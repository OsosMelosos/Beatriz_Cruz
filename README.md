# TurnoLab

Sistema de gestión de turnos para una recepción clínica. Interfaz Angular y API Python (Flask) con SQLite.

## Requisitos
- Python 3.10+
- Node.js 22.12+ y npm (Angular 22)

## Iniciar
1. API: `cd backend`, crea un entorno virtual, instala `pip install -r requirements.txt` y ejecuta `python app.py`.
2. Interfaz: en otra terminal, `cd frontend`, ejecuta `npm install` y `npm start`.
3. Abre `http://localhost:4200`. La API corre en `http://localhost:5000`.

La pantalla muestra cuatro consultorios. Genera turnos, llama al siguiente paciente desde cada consultorio y marca la atención como terminada. La campanilla se activa desde el control de sonido (los navegadores requieren interacción para permitir audio).

