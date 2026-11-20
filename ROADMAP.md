# Life OS — Roadmap de producto y ejecución

**Versión:** 0.3 · **Fecha:** 20 de noviembre de 2026

> Define orden y puertas de calidad, no fechas. READY autoriza solo la tarea especificada. PLANNING autoriza diseño, no código.

## 1. Dirección
Construir un centro de operaciones personal que el usuario quiera abrir diariamente. Primero experiencia y datos confiables; después planificación y análisis; finalmente agentes e integraciones.

## 2. Estado verificado en main
HEAD: 27791fc8a157a8733f5bb322a7f19c845a251995.

| Entrega | Estado | Evidencia |
|---|---|---|
| Fases 1–6 | Implementadas | Núcleo MVP según README/CHANGELOG |
| Fase 7 Habit Tracker | Implementada | Módulo, registros, métricas y widgets |
| Fase 8A–8D UX/UI | Comprometida | e3a4443250b319cf5fcd7cd0e082c4eecfc3ec5d |
| PRJ-001/002 | Comprometidas | Métricas, detalle y creación de tareas; afaf6cde2e72d00d72d317711d0c2d3fb442270e |
| HAB-001 | Comprometida | Calendario 300px/celdas 28px; 27791fc8a157a8733f5bb322a7f19c845a251995 |

Los commits reportan 139 tests, Ruff, node --check y smoke satisfactorios. No se reejecutaron aquí. QA visual manual sigue pendiente; tests no equivalen a aceptación UX.

## 3. Reglas
Trabajar en product/lifeos-evolution; inspeccionar git status/diff; preservar cambios locales; tests con DB temporal; no migraciones, dependencias, integraciones, cloud ni cambios de arquitectura en Fase 9; métricas con fórmula y fuente; no push ni merge.

## 4. Fases anteriores
Fases 1–7 y rediseño base Fase 8 están comprometidos en main. No reabrir salvo regresión o defecto reproducible. PRJ-001, PRJ-002 y HAB-001 están en main. QA visual manual pendiente.

## 5. Fase 9 — Experiencia diaria (autorizada)
Orden: STAB-001 QA; BUG-001 resiliencia de formulario si se reproduce; HOME-001 Home como centro de operaciones; TASK-001 espacio de trabajo de tareas; UX-REVIEW-001 revisión independiente. Cada tarea tiene SPEC en docs/factory/work/.

Criterios: Home responde qué requiere atención y qué hacer hoy; tareas contextuales; métricas reales; formularios resilientes; responsive real; conservar widgets y preferencias; tests, smoke, diff y QA documentados.

## 6. Fase 10 — Planificación (solo diseño)
Definir Área→Objetivo→Proyecto→Hito/entregable→Tarea, fechas planificadas, criterios de aceptación, pesos, relaciones, eventos, migraciones, API, exportación y backup. No crear modelos/migraciones/endpoints hasta aprobación expresa.

## 7. Fase 11 — Analytics (diseño)
Catálogo, semántica de eventos, períodos y reconstrucción. No inferir velocidad desde completed_at: se limpia al reabrir; los eventos actuales no guardan project_id al momento de la transición.

## 8. Fases futuras
Fase 12 Work/Business/Finance según necesidad real. Fase 13 AI Orchestrator con lectura, borradores, preview, aprobación, herramientas tipadas y auditoría. Fase 14 integraciones y acceso remoto solo con modelo de amenazas, autenticación, autorización, HTTPS, secretos y backup.

## 9. Priorización
1 pérdida/corrupción; 2 seguridad; 3 integridad; 4 flujos bloqueados; 5 accesibilidad/responsive; 6 jerarquía/usabilidad; 7 estética menor.

## 10. Definition of Done
Criterios identificables, alcance respetado, pruebas reales, diff revisado, documentación, archivos listados, limitaciones y revisión independiente. Dejar REVIEW hasta aceptación del PO.

## 11. Regla de autonomía
El Developer puede ejecutar tareas READY de Fase 9. Si requiere migración, dependencia, cambio de arquitectura, seguridad, IA, integración o decisión fuera de especificación, bloquear solo esa parte y continuar con tareas independientes.