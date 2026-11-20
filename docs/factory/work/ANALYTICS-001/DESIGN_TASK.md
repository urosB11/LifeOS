# ANALYTICS-001 — Diseño de Analytics e historial confiable

**Prioridad:** P1 · **Estado:** PLANNING · **Solo diseño; no implementar**

## Objetivo

Diseñar Analytics transversal con métricas trazables, períodos comparables e historial suficiente, sin crear gráficas antes de resolver la semántica de datos.

## Trabajo

1. Inventariar métricas actuales en DATABASE.md, AnalyticsService y módulos.
2. Clasificarlas como estado actual, actividad de período, tendencia, ejecución o resultado.
3. Crear diccionario usando docs/product/METRICS_CATALOG.md.
4. Evaluar limitaciones de activity_events:
   - task.completed y task.reopened no guardan project_id en metadatos;
   - completed_at se limpia al reabrir;
   - reasignar una tarea cambia project_id actual frente a histórico.
5. Proponer evento de transición con estado anterior/nuevo, project_id en el momento, timestamp UTC y metadatos mínimos.
6. Definir períodos, zona horaria, semanas/meses, faltantes, reaperturas y tareas eliminadas.
7. Definir cuándo consultar tablas actuales y cuándo reconstruir eventos.
8. Proponer informes iniciales y criterios de visualización.

## Entregable

Catálogo priorizado, fórmulas, contratos de consulta, propuesta de eventos, pruebas con secuencias temporales, limitaciones y etapas de implementación.

No agregar tablas, snapshots, endpoints, migraciones, librerías ni dashboards. No introducir event sourcing completo ni agregados duplicados sin justificar.