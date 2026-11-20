# Fase 9 — Plan de ejecución: experiencia diaria

**Estado:** autorizada dentro de las tareas READY.  
**Rama:** product/lifeos-evolution  
**Objetivo:** mejorar el uso cotidiano sin migraciones ni cambios de arquitectura.

## Resultado buscado

La aplicación debe dejar de sentirse como una colección de pantallas CRUD y comenzar a comportarse como un centro de operaciones personal. El usuario debe identificar qué requiere atención, decidir qué hacer, trabajar dentro del contexto de un proyecto y registrar actividad sin fricción.

## Secuencia

| Orden | ID | Tipo | Dependencia | Estado |
|---:|---|---|---|---|
| 1 | STAB-001 | QA manual / revisión | Ninguna | READY |
| 2 | BUG-001 | Corrección localizada | Reproducir defecto | READY |
| 3 | HOME-001 | UX + implementación | STAB-001 y BUG-001 | READY |
| 4 | TASK-001 | UX + implementación | HOME-001 | READY |
| 5 | UX-REVIEW-001 | Revisión independiente | HOME-001 y TASK-001 | PLANNING |
| 6 | PRJ-PLAN-001 | Diseño de dominio | Ninguna | PLANNING |
| 7 | ANALYTICS-001 | Diseño analítico | PRJ-PLAN-001 | PLANNING |

## Límites

Incluido: Home, Tareas, corrección de formularios, responsive, pruebas y revisión manual.

Excluido: objetivos/áreas/hitos como entidades; Analytics histórico; IA; integraciones; cloud; sincronización; nuevas librerías; migraciones.

## Puerta de salida

- Home comunica prioridades y acciones, no solo totales.
- Tareas ofrece creación, edición, filtros y estados claros.
- Formularios no pierden datos ante errores.
- Vistas funcionan en los tres tamaños definidos.
- Se preservan funciones y preferencias actuales.
- Tests, smoke test, revisión de diff y manual QA documentados.
- Reviewer presenta informe cuando esté disponible.
- El Product Owner acepta el cierre final.