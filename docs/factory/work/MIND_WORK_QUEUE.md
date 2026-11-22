# Mind — Work Queue

**Actualizada:** 22 de noviembre de 2026  
**Fuente de orden:** `docs/product/MIND_ROADMAP.md`  
**Responsable de priorización y aceptación:** Product Owner

## Estados

- **READY:** SPEC revisada y habilitada para que el PO asigne ejecución.
- **PLANNING:** alcance futuro; no comenzar código.
- **IN_PROGRESS:** trabajo en curso.
- **REVIEW:** implementación entregada; falta aceptación del PO.
- **APPROVED/DONE:** aceptación explícita del PO.
- **BLOCKED:** falta una decisión o dependencia.

## Cola

| ID | Entrega | Prioridad | Dependencias | Responsable | Estado |
|---|---|---:|---|---|---|
| MIND-001 | Diseño y planificación consolidada | P0 | Visión + auditoría técnica | Product/Architecture | REVIEW — roadmap 0.2 consolidado |
| MIND-002 | Primer núcleo funcional: Spaces, Inbox y Canvas con Cards simples | P0 | MIND-001 | Mimo / Developer | REVIEW — implementación entregada (2026-11-22); pendiente aceptación del PO |
| MIND-003 | Canvas interactivo y relaciones visuales | P1 | MIND-002 | Mimo / Developer | PLANNING |
| MIND-004 | Cards ricas y documentos por bloques | P1 | MIND-003 | Product/Architecture + Mimo | PLANNING |
| MIND-005 | Knowledge, búsqueda, reutilización y relaciones semánticas | P1 | MIND-004 | Mimo / Developer | PLANNING |
| MIND-006 | Integración con Projects, Tasks y Habits | P1 | MIND-005 | Mimo / Developer | PLANNING |
| MIND-007 | Flujos de estudio e investigación | P1 | MIND-005 | Product/UX + Mimo | PLANNING |
| MIND-008 | Medios, archivos y bloques avanzados | P2 | MIND-004 | Product/Architecture + Mimo | PLANNING |
| MIND-009 | Consolidación de calidad y escala | P1 | MIND-006, MIND-007, MIND-008 | Mimo + Reviewer | PLANNING |
| MIND-010 | Orbe v1: mini-chat contextual por Card | P3 | MIND-009 + autorización de IA | IA/Developer | FUTURO |
| MIND-011 | Orbes: artefactos, propuestas y operaciones aprobadas | P3 | MIND-010 + autorización específica | IA/Developer | FUTURO |
| MIND-012 | Orbes: voz y continuidad avanzada | P3 | MIND-011 + autorización específica | IA/Developer | FUTURO |

## Reglas operativas

1. No adelantar Orbes para “probar IA” antes de consolidar el producto funcional.
2. Toda entrega debe ser vertical y producir un resultado visible y persistente.
3. No crear tablas, endpoints o módulos preparatorios sin caso de uso de la entrega READY.
4. No duplicar Notes, Tasks, Projects ni Habits.
5. Antes de MIND-004, decidir el modelo canónico de documentos ricos, preservando Notes existentes.
6. Las tareas MIND-003 en adelante no comienzan hasta contar con SPEC y dependencias aceptadas.
7. Preservar el worktree y los cambios de Evolution. Mind se implementa en un worktree independiente.
8. Cada entrega se prueba con DB temporal, revisión del diff y QA visual; se publica en la rama asignada a Mind y queda en REVIEW.
