# Flujo: Feature (Nueva funcionalidad)

**Propósito:** Guía para implementar una funcionalidad de principio a fin.

## Estados

```
BACKLOG → PLANNING → IN_PROGRESS → REVIEW → APPROVED → DONE
```

## Pasos

### 1. BACKLOG
- Product Owner crea entrada en `work/WORK_QUEUE.md`.
- Define: nombre, descripción, rol responsable, dependencias, prioridad.

### 2. PLANNING
- Coordinator asigna rol Developer.
- Developer lee documentos relevantes (`REQUIREMENTS.md`, `ARCHITECTURE.md`, etc.).
- Developer describe: cambio mínimo, criterios de verificación, archivos a tocar.
- Si hay contradicción entre documentos → escalar al PO antes de implementar.

### 3. IN_PROGRESS
- Developer implementa porción vertical pequeña.
- Ejecuta pruebas específicas (`node --check`, `ruff`, `pytest`).
- Actualiza documentación afectada.
- No hace commit sin autorización.

### 4. REVIEW
- Coordinator solicita revisión a Reviewer.
- Reviewer usa `templates/pr-template.md`.
- Revisa: diff, accesibilidad, seguridad, cumplimiento de requisitos.
- Si hay hallazgos → vuelve a IN_PROGRESS.

### 5. APPROVED
- Coordinator entrega resultado al Product Owner.
- PO usa `templates/test-report.md` para decidir aceptación.
- Si hay cambios de alcance solicitados → PO decide.

### 6. DONE
- PO aprueba.
- Coordinator actualiza `work/WORK_QUEUE.md`.
- Developer hace commit y push (solo con autorización explícita).

## Handoff

Al finalizar, usar `templates/handoff-template.md` para transferir contexto a la siguiente tarea.
