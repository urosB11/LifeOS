# Life OS — Roadmap de producto y ejecución

**Versión:** 0.4 · **Fecha:** 21 de noviembre de 2026

> Define orden y puertas de calidad, no fechas. READY autoriza solo la tarea especificada. PLANNING autoriza diseño, no código.

## 1. Dirección
Construir un centro de operaciones personal que el usuario quiera abrir diariamente. Primero experiencia y datos confiables; después planificación, conocimiento y análisis; finalmente agentes e integraciones.

## 2. Estado verificado en main
HEAD: 27791fc8a157a8733f5bb322a7f19c845a251995.

| Entrega | Estado | Evidencia |
|---|---|---|
| Fases 1–6 | Implementadas | Núcleo MVP según README/CHANGELOG |
| Fase 7 Habit Tracker | Implementada | Módulo, registros, métricas y widgets |
| Fase 8A–8D UX/UI | Comprometida | e3a4443250b319cf5fcd7cd0e082c4eecfc3ec5d |
| PRJ-001/002 | Comprometidas | Métricas, detalle y creación de tareas; afaf6cde2e72d00d72d317711d0c2d3fb442270e |
| HAB-001 | Comprometida | Calendario compacto; 27791fc8a157a8733f5bb322a7f19c845a251995 |

Los commits reportan 139 tests, Ruff, node --check y smoke satisfactorios. No se reejecutaron aquí. QA visual manual sigue pendiente; tests no equivalen a aceptación UX.

## 3. Reglas
Trabajar en la rama autorizada para cada tarea; inspeccionar git status/diff; preservar cambios locales; tests con DB temporal; no migraciones, dependencias, integraciones, cloud ni cambios de arquitectura en Fase 9; métricas con fórmula y fuente; no push ni merge sin autorización explícita.

## 4. Fases anteriores
Fases 1–7 y rediseño base Fase 8 están comprometidos en main. PRJ-001, PRJ-002 y HAB-001 están comprometidos. QA visual manual fue reportada en revisión separada y requiere aceptación del PO.

## 5. Fase 9 — Experiencia diaria
Orden de trabajo documentado en `docs/factory/work/WORK_QUEUE.md`: STAB-001 QA; BUG-001 resiliencia de formulario si se reproduce; HOME-001 Home como centro de operaciones; TASK-001 espacio de trabajo de tareas; UX-REVIEW-001 revisión independiente. No ampliar alcance durante su ejecución.

Criterios: Home responde qué requiere atención y qué hacer hoy; tareas contextuales; métricas reales; formularios resilientes; responsive real; conservar widgets y preferencias; tests, smoke, diff y QA documentados.

## 6. Fase 10 — Planificación
Definir Área→Objetivo→Proyecto→Hito/entregable→Tarea, fechas planificadas, criterios de aceptación, pesos, relaciones, eventos, migraciones, API, exportación y backup. No crear modelos/migraciones/endpoints hasta aprobación expresa.

## 7. Fase 11 — Analytics
Catálogo, semántica de eventos, períodos y reconstrucción. No inferir velocidad desde completed_at: se limpia al reabrir; los eventos actuales no guardan project_id al momento de la transición.

## 8. Fase 12 — Mind: fundación de conocimiento y Canvas (planificación)
Objetivo: construir un entorno útil para capturar, explorar y conectar conocimiento antes de incorporar IA operativa.

Etapas de diseño:
1. Cerrar modelo de producto: espacios, Inbox, notas/ideas/recursos, Canvas, nodos, conexiones y búsqueda.
2. Definir arquitectura de contenido canónico vs. representación visual; evitar duplicación.
3. Diseñar MVP verificable y contratos de interacción.
4. Evaluar persistencia, exportación, accesibilidad, responsive y rendimiento del Canvas.
5. Separar una especificación implementable de las capacidades futuras de IA.

Hipótesis de MVP a validar: crear un espacio/Canvas, capturar notas e ideas, ubicarlas libremente, conectarlas, reabrirlas y conservar su identidad fuera del Canvas. No construir Orbes con modelos reales en esta primera entrega.

## 9. Fase 13 — Work / Business / Finance
Definir según necesidades reales y reutilizar el modelo común sin anticipar módulos vacíos.

## 10. Fase 14 — AI Orchestrator y Orbes operativos
Después de que Mind y los contratos de dominio sean útiles sin IA: sesiones contextuales temporales/persistentes, contexto autorizado ampliable, proveedores intercambiables, agentes/roles, herramientas tipadas, artefactos, propuestas, permisos y auditoría. No comenzar por una arquitectura multiagente distribuida.

## 11. Fase 15 — Integraciones y acceso remoto seguro
Solo con modelo de amenazas, autenticación, autorización, HTTPS, secretos, backup y consentimiento explícito.

## 12. Priorización
1 pérdida/corrupción; 2 seguridad; 3 integridad; 4 flujos bloqueados; 5 accesibilidad/responsive; 6 jerarquía/usabilidad; 7 estética menor.

## 13. Definition of Done
Criterios identificables, alcance respetado, pruebas reales, diff revisado, documentación, archivos listados, limitaciones y revisión independiente. Dejar REVIEW hasta aceptación del PO.

## 14. Regla de autonomía
La autorización de una tarea READY no se extiende a otras fases. Si requiere migración, dependencia, cambio de arquitectura, seguridad, IA, integración o decisión fuera de especificación, bloquear esa parte y escalar.
