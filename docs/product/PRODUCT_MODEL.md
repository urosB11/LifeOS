# Modelo de producto — LifeOS

**Versión:** 0.1 · **Fecha:** 20 de noviembre de 2026

## Propósito

Este documento establece el vocabulario funcional común. Evita que módulos y agentes usen "progreso", "objetivo", "proyecto" o "resultado" con significados distintos.

## Objetos del dominio

| Objeto | Qué representa | Regla principal | Situación |
|---|---|---|---|
| Área | Contexto amplio: personal, profesional, salud, aprendizaje, finanzas, etc. | Agrupa objetivos; no es una tarea | Conceptual |
| Objetivo | Resultado que se desea alcanzar | Debe poder describirse y, si corresponde, medirse | Futuro |
| Proyecto | Esfuerzo finito para obtener un resultado | Tiene alcance y estado; agrupa tareas | Actual |
| Hito / entregable | Resultado verificable que compone un proyecto | Tiene un criterio de aceptación observable | Futuro |
| Tarea | Acción concreta | Tiene estado y prioridad/vencimiento opcionales | Actual |
| Hábito | Práctica recurrente | Se mide en días programados y registros explícitos | Actual |
| Nota | Información, conocimiento o contexto | Puede existir sola o relacionarse con otros elementos | Actual |
| Evento | Cambio relevante | Es histórico; no reemplaza las tablas de dominio | Actual, básico |
| Métrica | Cálculo derivado | Tiene fórmula, fuente, período y limitaciones | Parcial |

## Relaciones objetivo

Área → Objetivo → Proyecto → Hito/entregable → Tarea.

Notas y hábitos podrán vincularse a objetivos en el futuro si la experiencia lo necesita. No implementar tablas vacías para anticipar conceptos sin flujo funcional.

## Distinciones de progreso

1. **Actividad:** acciones realizadas, por ejemplo tareas completadas.
2. **Ejecución:** estado de los elementos de trabajo.
3. **Entregables:** resultados parciales que cumplen criterios verificables.
4. **Resultado:** cambio que el objetivo buscaba producir.

El MVP mide parte de la ejecución. La métrica actual de proyectos —tareas completadas / tareas totales— debe llamarse "progreso de tareas" o "ejecución de tareas". No equivale al porcentaje del resultado.

## Reglas del ciclo de proyecto

- Un proyecto puede estar activo, completado o archivado.
- Archivar no significa completar el resultado.
- La finalización es explícita; no se infiere porque todas las tareas estén completadas.
- Reabrir debe conservar historial de transición.
- Un proyecto sin tareas no muestra 0 %.
- Las métricas se derivan de tareas y, en el futuro, de hitos/entregables, sin agregados duplicados.

## Reglas para incorporar objetos

Antes de crear una entidad:
1. describir el caso de uso y quién la crea;
2. especificar relaciones y cardinalidades;
3. definir estados y transiciones;
4. definir borrado y archivo;
5. definir eventos y trazabilidad;
6. definir exportación y backup;
7. definir métricas;
8. escribir pruebas límite;
9. justificar por qué no alcanza una entidad o relación existente.

No crear tablas para conceptos que solo aparecen en una visión futura.