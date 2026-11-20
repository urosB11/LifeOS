# Handoff: STAB-001 — QA manual Fase 8

**Fecha:** 2026-11-20
**De:** Developer (ejecución de QA propia)
**Para:** Reviewer — Mimo / Product Owner
**Entrega:** Validación manual de Fase 8 (PRJ-001, PRJ-002, HAB-001)

## Qué se hizo

Ejecución de QA manual de STAB-001 contra la rama `main` (commit 27791fc, que incluye Fase 8 base, PRJ-001, PRJ-002 y HAB-001). Se levantó el servidor Uvicorn en `127.0.0.1:8001` con `LIFEOS_DATA_DIR` temporal y base de datos inicializada mediante Alembic `upgrade head`.

## Qué se verificó

| Flujo | Resultado |
|---|---|
| Health check | ✅ `{"status":"ok","database":"sqlite"}` |
| Crear proyecto (PRJ-001) | ✅ 201, métricas expuestas: task_count=0, completed_count=0, overdue_count=0, next_due_date=null |
| Crear tarea desde proyecto (PRJ-002) | ✅ 201, project_id asociado correctamente, métricas actualizadas (task_count=1) |
| Completar/reabrir proyecto | ✅ Transiciones de estado funcionan, métricas se mantienen |
| Error de API (nombre vacío) | ✅ 422 con detalle de validación |
| Proyecto inexistente | ✅ 404 |
| Proyecto sin tareas | ✅ task_count=0, next_due_date=null (frontend muestra "Sin tareas") |
| Calendario de hábitos (HAB-001) | ✅ Hábito creado, calendario devuelve 30 días para noviembre 2026 |
| Frontend servido | ✅ index (200), projects.js (200, 26708 bytes), habits.js (200, 36720 bytes), app.js (200, 7668 bytes) |
| Tasks endpoint | ✅ 200, lista de tareas |
| Notes endpoint | ✅ 200, 0 notas |
| Settings endpoints | ✅ preferences/theme/timezone disponibles |
| Pruebas automatizadas | ✅ 139/139 pytest, ruff OK, node --check OK |

## Qué queda pendiente

- Revisión visual en navegador real en los tres viewports definidos en el SPEC: Desktop (1440×900), Tablet (768×1024), Móvil (390×844)
- Revisión independiente por Reviewer (Mimo) — si no está disponible, declarar QA propia
- Verificación de flujos de UI que requieren interacción de navegador (abrir/cerrar modales, foco de teclado, navegación móvil, overflow horizontal)

## Comandos ejecutados

```
git fetch origin
git checkout -b product/lifeos-evolution origin/product/lifeos-evolution
# Servidor temporal:
uvicorn app.main:app --host 127.0.0.1 --port 8001 (con LIFEOS_DATA_DIR temporal, LIFEOS_ALLOWED_HOSTS)
alembic upgrade head
# Pruebas:
.venv\Scripts\pytest -q          → 139 passed
.venv\Scripts\ruff check app tests → All checks passed
node --check frontend/assets/js/projects.js habits.js app.js → JS OK
# Smoke test con Python urllib contra http://127.0.0.1:8001/api/v1
```

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| docs/factory/work/WORK_QUEUE.md | STAB-001 cambiado de READY a REVIEW, notas actualizadas |
| docs/factory/work/STAB-001/HANDOFF.md | Nuevo — este documento de handoff |

## Decisiones tomadas

- STAB-001 es "solo revisión, no código" per SPEC.md: no se implementaron cambios de código.
- Se ejecutó QA propia del Developer ya que el Reviewer (Mimo) no está disponible en este momento. Esto debe declararse al entregar.
- Todas las verificaciones se hicieron contra una base de datos temporal (LIFEOS_DATA_DIR), nunca contra la base personal.

## Contexto para la siguiente tarea

- La siguiente tarea en la cola es BUG-001 (conservar formulario ante error), que depende de STAB-001 y BUG-001 (auto-dependencia para reproducir).
- HOME-001 depende de STAB-001 y BUG-001.
- La rama de trabajo es `product/lifeos-evolution`. No hacer push ni merge a main.

## Estado de la cola de trabajo

- STAB-001: REVIEW (pendiente de aceptación por PO)
- BUG-001: READY (siguiente en la cola)
- HOME-001: READY (bloqueada por STAB-001 y BUG-001)
