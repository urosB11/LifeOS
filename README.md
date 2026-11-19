# Life OS

Life OS es un centro de operaciones personal, modular y local. Esta carpeta contiene la línea base aprobada de producto, arquitectura, datos, seguridad y desarrollo asistido con OpenCode.

## Estado actual

- **Fases 1 a 6 completadas:** fundaciones ejecutables, proyectos y tareas, notas y etiquetas, Home/dashboard/Settings, exportación JSON + backup/restauración + métricas básicas, y estabilización/aceptación del MVP (aceptación de extremo a extremo, persistencia, accesibilidad/responsive).
- **Fase 7 (Habit Tracker — Life OS 0.2) completada:** módulo de hábitos con estados, registros diarios, métricas deterministas, vistas Hábitos + Home, widgets de hábitos y verificación ampliada (`backend/verify_acceptance.py`, 23 checks).
- **Código funcional:** backend FastAPI + frontend HTML/CSS/JavaScript nativo ejecutables en `127.0.0.1:8000`; 134 pruebas automatizadas.
- **Context7:** plugin de proyecto configurado en `opencode.json`; falta autenticarlo localmente (`opencode mcp auth context7`).
- **Skills:** cuatro skills locales incluidas; falta instalar `frontend-design` de Anthropic y `fastapi` oficial en el proyecto (`scripts/setup-opencode.ps1`).

## Cómo ejecutar

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/`. Detalle completo en `backend/README.md`; uso diario en `GUIA_USUARIO.md`; recuperación de datos en `RECUPERACION.md`.

## Documentos

- `VISION.md`: propósito y evolución del producto.
- `REQUIREMENTS.md`: funcionalidades y criterios de aceptación del MVP.
- `ARCHITECTURE.md`: tecnologías, capas y estructura.
- `DATABASE.md`: tablas, relaciones, eventos y políticas de integridad.
- `SECURITY.md`: modelo de confianza y controles.
- `ROADMAP.md`: fases y entregables.
- `AGENTS.md`: reglas de trabajo para OpenCode y otros agentes.
- `GUIA_USUARIO.md`: guía de uso de la aplicación.
- `RECUPERACION.md`: respaldo, restauración y recuperación de datos.
- `CHANGELOG.md`: historial de cambios.
- `OPENCODE_SETUP.md`: preparación del entorno y herramientas.
- `OPENCODE_FIRST_TASK.md`: primer encargo para iniciar Fase 1.

## Tecnología inicial

Python 3.11+, FastAPI, SQLite, SQLAlchemy 2.x, Alembic, Uvicorn, pytest, HTTPX, Ruff y frontend HTML/CSS/JavaScript nativo. No se necesita Node para ejecutar Life OS; Node se usa únicamente para herramientas de desarrollo como el CLI `skills`.

## Principios

- Local-first; sin IA ni servicios externos en el runtime del MVP.
- Base de datos fuera del repositorio.
- No exponer el servidor fuera de `127.0.0.1`.
- Cada cambio se prueba con una base temporal.
- Ninguna skill ni agente puede modificar el alcance o la política de seguridad por iniciativa propia.

Lee `OPENCODE_SETUP.md`, ejecuta la preparación local y autentica Context7 antes de comenzar con OpenCode.
