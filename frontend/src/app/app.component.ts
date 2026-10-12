import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { interval, Subscription, startWith, switchMap } from 'rxjs';

interface Ticket { id: number; code: string; patient: string; service: string; status: string; desk: number | null; }
interface State { waiting: Ticket[]; desks: { number: number; ticket: Ticket | null }[]; stats: { today: number; served: number }; }

@Component({ selector: 'app-root', standalone: true, imports: [CommonModule, FormsModule], templateUrl: './app.component.html' })
export class AppComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  private poll?: Subscription;
  state: State = { waiting: [], desks: [], stats: { today: 0, served: 0 } };
  patient = '';
  today = new Date();
  service = 'Consulta general';
  busy = false;
  sound = false;
  notice = '';
  private lastCalls = new Set<number>();
  private audio?: AudioContext;

  ngOnInit() { this.poll = interval(2500).pipe(startWith(0), switchMap(() => this.http.get<State>('/api/state'))).subscribe(s => { this.state = s; for (const desk of s.desks) if (desk.ticket && !this.lastCalls.has(desk.ticket.id)) { this.lastCalls.add(desk.ticket.id); if (this.sound) this.chime(); } }); }
  ngOnDestroy() { this.poll?.unsubscribe(); this.audio?.close(); }
  addTicket() { if (!this.patient.trim() || this.busy) return; this.busy = true; this.http.post('/api/tickets', { patient: this.patient.trim(), service: this.service }).subscribe({ next: () => { this.patient = ''; this.message('Turno creado y agregado a la fila.'); this.refresh(); }, error: e => this.message(e.error?.error || 'No se pudo crear el turno.'), complete: () => this.busy = false }); }
  call(desk: number) { this.http.post<Ticket>(`/api/desks/${desk}/call`, {}).subscribe({ next: t => { this.lastCalls.add(t.id); this.message(`${t.code} · ${t.patient} llamado al consultorio ${desk}.`); this.refresh(); if (this.sound) this.chime(); }, error: e => this.message(e.error?.error || 'No se pudo llamar el turno.') }); }
  finish(ticket: Ticket) { this.http.post(`/api/tickets/${ticket.id}/finish`, {}).subscribe({ next: () => { this.message(`${ticket.code} marcado como atendido.`); this.refresh(); }, error: () => this.message('No se pudo cerrar la atención.') }); }
  toggleSound() { this.sound = !this.sound; if (this.sound) { this.audio = new AudioContext(); this.chime(); } }
  private chime() { if (!this.audio) this.audio = new AudioContext(); if (this.audio.state === 'suspended') void this.audio.resume(); const ctx = this.audio; [659, 784, 988].forEach((f, i) => { const osc = ctx.createOscillator(), gain = ctx.createGain(), at = ctx.currentTime + i * .13; osc.type = 'sine'; osc.frequency.value = f; gain.gain.setValueAtTime(.0001, at); gain.gain.exponentialRampToValueAtTime(.12, at + .025); gain.gain.exponentialRampToValueAtTime(.0001, at + .32); osc.connect(gain).connect(ctx.destination); osc.start(at); osc.stop(at + .34); }); }
  private refresh() { this.http.get<State>('/api/state').subscribe(s => this.state = s); }
  private message(text: string) { this.notice = text; setTimeout(() => this.notice = '', 3600); }
}
