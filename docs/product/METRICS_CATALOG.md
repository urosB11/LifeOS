# Catálogo de métricas — LifeOS

**Versión:** 0.1 · **Fecha:** 20 de noviembre de 2026

## Contrato obligatorio

Cada métrica documenta nombre, pregunta, fórmula, unidad, fuente, ámbito, período, zona horaria, faltantes y limitaciones.

## Métricas actuales

| ID | Nombre | Fórmula / criterio | Fuente | Lectura válida |
|---|---|---|---|---|
| TASK-PENDING | Tareas pendientes | COUNT(status=pending) | tasks | Estado actual |
| TASK-COMPLETED | Tareas completadas | COUNT(status=completed) | tasks | Estado actual |
| TASK-OVERDUE | Tareas vencidas | pending con due_date anterior a hoy local | tasks + timezone | Vencidas hoy |
| PROJECT-ACTIVE | Proyectos activos | COUNT(status=active) | projects | Estado actual |
| PROJECT-TASK-RATIO | Progreso de tareas | completed_count / task_count × 100 | tasks por project_id | Ejecución de tareas, no resultado |
| PROJECT-OVERDUE | Tareas vencidas por proyecto | pending con due_date anterior a hoy local | tasks por project_id | Deuda operativa |
| PROJECT-NEXT-DUE | Próximo vencimiento | menor due_date >= hoy entre tasks pending | tasks por project_id | Próxima fecha registrada |
| HABIT-STREAK | Racha actual | Días programados consecutivos completados que terminan hoy | habits + habit_entries | Consistencia de un hábito |
| HABIT-WEEKLY | Cumplimiento semanal | completed / días programados × 100 | habits + habit_entries | Semana local |
| HABIT-MONTHLY | Cumplimiento mensual | completed / días programados × 100 | habits + habit_entries | Mes local |

Si el denominador es cero, mostrar "Sin datos" o "Sin tareas", no 0 %.

## Métricas futuras

| ID propuesto | Qué mediría | Datos necesarios | Estado |
|---|---|---|---|
| PROJECT-DELIVERABLE-PROGRESS | Entregables aceptados | Hitos, pesos, criterios y aceptación | Diseño pendiente |
| PROJECT-PLAN-VARIANCE | Diferencia plan/real | Fechas previstas, reales y baseline | Diseño pendiente |
| PROJECT-VELOCITY | Transiciones de tareas por período | Historial con project_id al momento del evento | No confiable hoy |
| PROJECT-HEALTH | Riesgo respecto del plan | Fechas, avance esperado, hitos vencidos y reglas acordadas | Sin fórmula |
| GOAL-ATTAINMENT | Progreso de un objetivo medible | Baseline, target, unidad y registros | Objetivos no implementados |
| LIFE-AREA-OVERVIEW | Evolución por área | Áreas, objetivos y métricas válidas | Futuro |

## Restricciones analíticas

- No llamar "salud" a un conteo de tareas vencidas.
- No mostrar velocidad histórica usando solo el estado actual.
- No sumar porcentajes de proyectos para producir un índice global sin ponderación explícita.
- No comparar semanas de distinta duración o zonas horarias sin declararlo.
- No tratar una tarea reabierta como finalización neta sin definir semántica de eventos.
- No mostrar predicciones o scores opacos en el MVP.
- No usar datos sintéticos fuera de pruebas.

## Requisitos para series temporales

Antes de habilitar gráficos históricos:
1. definir evento de transición con estado anterior, nuevo, timestamp y project_id en el momento;
2. decidir cómo tratar tareas movidas, reabiertas y eliminadas;
3. asegurar escritura atómica;
4. probar reconstrucción con secuencias conocidas;
5. definir zona horaria y granularidad;
6. documentar exportación y límites.