# Life OS

Life OS es un sistema operativo personal local-first: un centro de operaciones para conectar prioridades, proyectos, tareas, hábitos, notas y, progresivamente, objetivos e informes.

## Estado actual
- Fases 1–6: núcleo MVP 0.1 implementado.
- Fase 7: Habit Tracker 0.2 implementado.
- Fase 8: rediseño UX/UI comprometido en main.
- Proyectos: métricas, detalle, edición y creación contextual de tareas en main.
- Hábitos: calendario compacto en main.
- Los últimos commits reportan 139 pytest, Ruff, node --check y smoke satisfactorios; QA visual manual pendiente.
- Evolución documentada en product/lifeos-evolution.

## Ejecutar
~~~powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~
Abrir http://127.0.0.1:8000/. Ver backend/README.md, GUIA_USUARIO.md y RECUPERACION.md.

## Producto
VISION.md y ROADMAP.md: dirección y secuencia. REQUIREMENTS.md: requisitos vigentes. docs/product/: modelo conceptual, UX, métricas y agentes futuros.

## Técnico y operativo
ARCHITECTURE.md, DATABASE.md, SECURITY.md, AGENTS.md, docs/factory/AGENT_START_HERE.md, docs/factory/work/WORK_QUEUE.md y CHANGELOG.md.

## Principios
Local-first, datos fuera del repo, loopback, tests con DB temporal, métricas trazables, sin IA ni integraciones runtime sin aprobación.