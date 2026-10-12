import { bootstrapApplication } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { registerLocaleData } from '@angular/common';
import localeEsMX from '@angular/common/locales/es-MX';
import { AppComponent } from './app/app.component';

registerLocaleData(localeEsMX);
bootstrapApplication(AppComponent, { providers: [provideHttpClient()] }).catch(console.error);
