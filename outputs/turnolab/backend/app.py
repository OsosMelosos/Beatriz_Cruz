from datetime import datetime
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB = Path(__file__).with_name("turnolab.db")


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            patient TEXT NOT NULL,
            service TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            desk INTEGER,
            created_at TEXT NOT NULL,
            called_at TEXT,
            finished_at TEXT
        )""")


def snapshot():
    with connect() as db:
        waiting = [dict(r) for r in db.execute(
            "SELECT * FROM tickets WHERE status='waiting' ORDER BY id")]
        desks = []
        for n in range(1, 5):
            row = db.execute("SELECT * FROM tickets WHERE desk=? AND status='serving'", (n,)).fetchone()
            desks.append({"number": n, "ticket": dict(row) if row else None})
        today = datetime.now().strftime("%Y-%m-%d")
        total = db.execute("SELECT COUNT(*) FROM tickets WHERE substr(created_at,1,10)=?", (today,)).fetchone()[0]
        served = db.execute("SELECT COUNT(*) FROM tickets WHERE status='done' AND substr(finished_at,1,10)=?", (today,)).fetchone()[0]
    return {"waiting": waiting, "desks": desks, "stats": {"today": total, "served": served}}


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "TurnoLab"})


@app.get("/api/state")
def state():
    return jsonify(snapshot())


@app.post("/api/tickets")
def create_ticket():
    body = request.get_json(silent=True) or {}
    patient = str(body.get("patient", "")).strip()
    service = str(body.get("service", "Consulta general")).strip()
    if not patient:
        return jsonify({"error": "Escribe el nombre del paciente."}), 400
    with connect() as db:
        seq = db.execute("SELECT COALESCE(MAX(id),0)+1 FROM tickets").fetchone()[0]
        code = f"TL-{seq:03d}"
        db.execute("INSERT INTO tickets(code,patient,service,created_at) VALUES(?,?,?,?)",
                   (code, patient[:80], service[:60], datetime.now().isoformat(timespec="seconds")))
        row = db.execute("SELECT * FROM tickets WHERE code=?", (code,)).fetchone()
    return jsonify(dict(row)), 201


@app.post("/api/desks/<int:desk>/call")
def call_next(desk):
    if desk not in range(1, 5):
        return jsonify({"error": "Consultorio inválido."}), 404
    with connect() as db:
        active = db.execute("SELECT id FROM tickets WHERE desk=? AND status='serving'", (desk,)).fetchone()
        if active:
            return jsonify({"error": "Termina la atención actual antes de llamar otro turno."}), 409
        row = db.execute("SELECT id FROM tickets WHERE status='waiting' ORDER BY id LIMIT 1").fetchone()
        if not row:
            return jsonify({"error": "No hay pacientes en espera."}), 404
        db.execute("UPDATE tickets SET status='serving', desk=?, called_at=? WHERE id=?",
                   (desk, datetime.now().isoformat(timespec="seconds"), row["id"]))
        ticket = db.execute("SELECT * FROM tickets WHERE id=?", (row["id"],)).fetchone()
    return jsonify(dict(ticket))


@app.post("/api/tickets/<int:ticket_id>/finish")
def finish(ticket_id):
    with connect() as db:
        cur = db.execute("UPDATE tickets SET status='done', finished_at=? WHERE id=? AND status='serving'",
                         (datetime.now().isoformat(timespec="seconds"), ticket_id))
        if not cur.rowcount:
            return jsonify({"error": "El turno ya no está en atención."}), 404
    return jsonify({"ok": True})


init_db()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
