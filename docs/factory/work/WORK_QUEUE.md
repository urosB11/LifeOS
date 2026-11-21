# WORK_QUEUE — Cola central de trabajo

**Actualizada:** 21 de noviembre de 2026. Coordinator mantiene; PO prioriza.

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
Prioridad P0 · Reviewer Mimo · Spec STAB-001/SPEC.md · Solo revisión, no código. **Estado: REVIEW — veredicto de Mimo: REJECT** (2026-11-21). QA de Nemo verificado independientemente (139/139 pytest, ruff OK, node --check OK) + revisión visual Edge headless/CDP en 1440×900, 768×1024, 390×844. Hallazgos: ALTA overflow horizontal móvil en 5 pantallas (causa: `.main{margin:0 auto}` en flex column de `.app-content` — **no contemplado en la cola, requiere tarea nueva**); ALTA confirmada BUG-001 (campos perdidos tras error); MEDIA confirmada PRJ-UI-001 (tareas fuera del DOM con formulario abierto); MEDIA foco no restaurado al cerrar modal con ESC; BAJA favicon 404. Detalle en STAB-001/HANDOFF.md. Pendiente: aceptación del PO.

### BUG-001 — Conservar formulario ante error
Prioridad P0 · Developer Nemo · Spec BUG-001/SPEC.md · Reproducir antes de corregir.

### HAB-002 — Semana interactiva y calendarios por hábito
Prioridad P1 · Developer Mimo (asignación explícita del PO) · Reviewer Nemo · Depende de STAB-001 para liberar a Mimo de la revisión independiente · Spec HAB-002/SPEC.md. **Estado: REVIEW** (Mimo, 2026-11-21) — implementación completa y QA propia ejecutada (140/140 pytest, ruff y node --check OK, QA visual en 3 viewports sin hallazgos ALTA); pendiente revisión independiente de Nemo. Handoff: `docs/factory/work/HAB-002/HANDOFF.md`.

### PRJ-UI-001 — Mantener las tareas visibles al abrir el formulario
Prioridad P1 · Developer Mimo (asignación explícita del PO) · Reviewer Nemo · Después de BUG-001 para evitar solapamiento en projects.js · Spec PRJ-UI-001/SPEC.md.

### HOME-001 — Home como centro de operaciones
Prioridad P0 · Developer Nemo · Depende de STAB-001/BUG-001 y de HAB-002 por solapamiento en home.js · Spec HOME-001/SPEC.md.

### TASK-001 — Espacio de trabajo de Tareas
Prioridad P1 · Developer Nemo · Secuencial después de HOME-001 · Spec TASK-001/SPEC.md.

## Revisión
### UX-REVIEW-001
PLANNING · Reviewer Mimo · Después de HOME-001 y TASK-001.

## Diseño futuro — no autoriza código
### PRJ-PLAN-001
PLANNING · Diseño de hitos, entregables, planificación y progreso real · Spec PRJ-PLAN-001/DESIGN_TASK.md.

### PRJ-WORKSPACE-001 — Proyecto como espacio de trabajo
PLANNING · Diseño de arquitectura funcional e información del proyecto (resumen, tareas, notas, documentos/recursos y seguimiento) · Spec PRJ-WORKSPACE-001/DESIGN_TASK.md · No implementar.

### ANALYTICS-001
PLANNING · Catálogo, historial y semántica temporal · Depende de PRJ-PLAN-001 · Spec ANALYTICS-001/DESIGN_TASK.md.

## Regla
Cada tarea entrega pruebas reales y handoff. Todo commit de implementación debe hacerse push a la rama remota de trabajo asignada y verificarse; no hacer merge ni push a main. PO acepta el cierre.