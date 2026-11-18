# Life OS

Life OS es un centro de operaciones personal, modular y local. Esta carpeta contiene la línea base aprobada de producto, arquitectura, datos, seguridad y desarrollo asistido por OpenCode.

## Estado actual

- Planificación: Fase 0 cerrada.
- Próximo trabajo: Fase 1 — fundaciones ejecutables.
- Código funcional: todavía no implementado.
- Context7: plugin de proyecto configurado en `opencode.json`; falta autenticarlo localmente.
- Skills: cuatro skills locales incluidas; falta instalar `frontend-design` de Anthropic y `fastapi` oficial en el proyecto.

## Documentos

- `VISION.md`: propósito y evolución del producto.
- `REQUIREMENTS.md`: funcionalidades y criterios de aceptación del MVP.
- `ARCHITECTURE.md`: tecnologías, capas y estructura.
- `DATABASE.md`: tablas, relaciones, eventos y políticas de integridad.
- `SECURITY.md`: modelo de confianza y controles.
- `ROADMAP.md`: fases y entregables.
- `AGENTS.md`: reglas de trabajo para OpenCode y otros agentes.
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
