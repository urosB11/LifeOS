# WORK_QUEUE — Cola central de trabajo

**Actualizada:** 20 de noviembre de 2026. Coordinator mantiene; PO prioriza.

## Estados
READY = especificada y autorizada; PLANNING = solo diseño; IN_PROGRESS = ejecución; REVIEW = revisión/aceptación; APPROVED = aceptada; DONE = cerrada; BLOCKED = decisión/dependencia; CANCELLED = cancelada.

## Completadas en main
- FACTORY-001: estructura factory.
- UX-001: auditoría inicial (informe presentado; no todos los artefactos originales versionados).
- PRJ-001: métricas y detalle, commit afaf6cde2e72d00d72d317711d0c2d3fb442270e.
- PRJ-002: crear tareas desde proyecto, mismo commit.
- HAB-001: calendario compacto, commit 27791fc8a157a8733f5bb322a7f19c845a251995.

## Fase 9 — READY
### STAB-001 — QA manual Fase 8
Prioridad P0 · Reviewer Mimo · Spec STAB-001/SPEC.md · Solo revisión, no código.

### BUG-001 — Conservar formulario ante error
Prioridad P0 · Developer Nemo · Spec BUG-001/SPEC.md · Reproducir antes de corregir.

### HOME-001 — Home como centro de operaciones
Prioridad P0 · Developer Nemo · Depende de STAB-001/BUG-001 · Spec HOME-001/SPEC.md.

### TASK-001 — Espacio de trabajo de Tareas
Prioridad P1 · Developer Nemo · Secuencial después de HOME-001 · Spec TASK-001/SPEC.md.

## Revisión
### UX-REVIEW-001
PLANNING · Reviewer Mimo · Después de HOME-001 y TASK-001.

## Diseño futuro — no autoriza código
### PRJ-PLAN-001
PLANNING · Diseño de hitos, entregables, planificación y progreso real · Spec PRJ-PLAN-001/DESIGN_TASK.md.

### ANALYTICS-001
PLANNING · Catálogo, historial y semántica temporal · Depende de PRJ-PLAN-001 · Spec ANALYTICS-001/DESIGN_TASK.md.

## Regla
Cada tarea entrega pruebas reales y handoff. No push ni merge. PO acepta el cierre.