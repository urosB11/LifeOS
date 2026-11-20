# PRJ-PLAN-001 — Diseño del modelo de planificación de proyectos

**Prioridad:** P1 · **Estado:** PLANNING · **Solo diseño; no implementar**

## Pregunta

¿Cómo debe representar LifeOS el progreso real de un proyecto y no confundir tareas completadas con resultados conseguidos?

## Trabajo

Comparar y recomendar un modelo funcional para:
- fechas planificadas de inicio y fin;
- hitos y entregables;
- criterios de aceptación verificables;
- peso relativo de entregables, si es necesario;
- relación de tareas con hitos;
- fechas reales de cumplimiento;
- historial de cambios;
- reglas de riesgo solo si existen datos suficientes.

## Principios

1. La métrica actual se mantiene como progreso de tareas.
2. Avance de resultado deriva de entregables aceptados o métrica de objetivo, no del número bruto de tareas.
3. Proyecto sin entregables no muestra un porcentaje de resultado inventado.
4. Pesos tienen significado y normalización explícitos.
5. Finalizar proyecto es una decisión explícita.
6. No definir salud/ritmo con umbrales arbitrarios.
7. Conservar historial suficiente para explicar transiciones.

## Alternativas

- Hitos con peso y criterios de aceptación.
- Entregables independientes con tareas relacionadas.
- Hitos como agrupadores de tareas, sin métrica ponderada.
- Fechas objetivo en proyecto y entregables.

Evaluar UX, integridad, consultas, exportación y migraciones.

## Entregable

Casos de uso, modelo conceptual/ERD, campos, cardinalidades, estados, reglas de progreso y fecha, eventos, contratos API, migración y compatibilidad, export/backup, riesgos y pruebas.

No modificar código, modelos, migraciones ni datos. Implementación requiere aprobación separada del PO.