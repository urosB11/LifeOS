# Life OS — Roadmap de producto y ejecución

**Versión:** 0.4 · **Fecha:** 22 de noviembre de 2026

> Define orden y puertas de calidad, no fechas. READY autoriza solo la tarea especificada; PLANNING autoriza diseño, no código.

## 1. Dirección

Construir un centro de operaciones personal que el usuario quiera abrir diariamente. LifeOS debe conectar el ciclo **intención → planificación → ejecución → evidencia → aprendizaje → ajuste**. Primero experiencia útil y datos confiables; después planificación y análisis; finalmente agentes e integraciones.

La interfaz no debe sentirse como una colección de CRUD ni como un dashboard decorativo. Debe ser calma, precisa, visualmente jerárquica, contextual y progresivamente reveladora. Ver docs/product/UX_DIRECTION.md y docs/product/UX_INTERACTION_MODEL.md.

## 2. Estado de referencia de main

HEAD de main documentado: 27791fc8a157a8733f5bb322a7f19c845a251995.

| Entrega | Estado en main | Evidencia |
|---|---|---|
| Fases 1–6 | Implementadas | Núcleo MVP |
| Fase 7 Habit Tracker | Implementada | Módulo, registros, métricas y widgets |
| Fase 8A–8D UX/UI | Comprometida | e3a4443250b319cf5fcd7cd0e082c4eecfc3ec5d |
| PRJ-001/002 | Comprometidas | afaf6cde2e72d00d72d317711d0c2d3fb442270e |
| HAB-001 | Comprometida | 27791fc8a157a8733f5bb322a7f19c845a251995 |

Estos cambios están en main. No se debe asumir que los cambios posteriores de la rama de evolución ya fueron integrados.

## 3. Estado de la rama de evolución

La rama product/lifeos-evolution contiene entregas posteriores de Fase 9. Al actualizar este roadmap, su HEAD remoto verificado fue 975bf80358d0b64ac36d7cc6428cfd8b66a4c1ef.

HOME-001, TASK-001, BUG-001, HAB-002, PRJ-UI-001, STAB-001 y UX-REVIEW-001 figuran en REVIEW en WORK_QUEUE.md. La revisión UX-REVIEW-001 fue realizada por el mismo agente que implementó Home y Tareas; no se considera independiente. La aceptación del PO y el contraste independiente siguen pendientes. No marcar esas entregas como DONE por esta actualización.

## 4. Reglas de rama y calidad

- Trabajar en product/lifeos-evolution, salvo asignación expresa del PO.
- Push obligatorio a la rama de trabajo asignada después de verificar pruebas y diff.
- Nunca push a main, merge, release o deploy sin aprobación explícita del PO.
- No force push ni reescritura destructiva de historia.
- Preservar cambios locales y archivos no trackeados.
- Tests siempre con DB temporal mediante LIFEOS_DATA_DIR.
- En Fase 9.1 no agregar dependencias, frameworks, endpoints ni migraciones.
- Una migración o cambio de arquitectura requiere especificación, DATABASE.md y aprobación separada.
- Métricas con fórmula, fuente, período y limitaciones; nunca inventar scores ni historia.

## 5. Fase 9 — Experiencia diaria

Las entregas originales STAB-001, BUG-001, HAB-002, PRJ-UI-001, HOME-001, TASK-001 y UX-REVIEW-001 están en REVIEW según WORK_QUEUE.md. La cola es la fuente de verdad para sus evidencias, bloqueos y aceptación. No se reabren salvo regresión o defecto reproducible.

## 6. Fase 9.1 — Interacción directa y experiencia fluida

**Objetivo:** reducir fricción sin rehacer la arquitectura ni sacrificar utilidad, trazabilidad o accesibilidad.

| Orden | ID | Resultado | Dependencia |
|---:|---|---|---|
| 1 | RESPONSIVE-002 | Resolver el overflow horizontal móvil ya registrado | Ninguna |
| 2 | UX-HOME-002 | Eliminar duplicaciones y estados engañosos; mejorar captura rápida | RESPONSIVE-002 |
| 3 | UX-WIDGETS-002 | Personalización visual en Home; drag dentro de zonas existentes | UX-HOME-002 |
| 4 | UX-MODULES-002 | Formularios progresivos y edición de notas | UX-WIDGETS-002 |
| 5 | UX-REVIEW-002 | Revisión UX independiente de la implementación | UX-HOME-002, UX-WIDGETS-002, UX-MODULES-002 y RESPONSIVE-002 |

### Resultado esperado

- Home ayuda a decidir y actuar; no repite tareas ni confunde error con ausencia de datos.
- La captura de tarea/nota tiene un único punto contextual y solo muestra un editor a la vez.
- El usuario reorganiza widgets arrastrándolos desde Home sin escribir posiciones numéricas.
- Settings deja de ofrecer un segundo editor para el orden de widgets.
- Projects y Notes muestran sus formularios de creación solo cuando se solicitan.
- Las notas existentes se pueden editar con el contrato API actual.
- Las vistas siguen siendo utilizables con mouse, teclado y táctil.

### Límites explícitos

- Mantener HTML/CSS/JavaScript nativo, FastAPI, SQLAlchemy síncrono, SQLite, Alembic y API /api/v1.
- No migraciones, nuevos endpoints ni nuevas dependencias.
- Drag & drop limitado a la zona funcional actual del widget (main, side o full). No permitir arrastrar entre zonas en esta entrega.
- Mantener IDs estables, visibilidad y preferencias actuales.
- No modificar el significado de proyectos, tareas, hábitos, notas o métricas.
- No alterar el token global --text-muted sin decisión del PO: el contraste quedó como pendiente en UX-REVIEW-001.
- Corregir overflow sin ocultarlo mediante overflow-x:hidden ni recortar contenido.

## 7. Fase 10 — Planificación (solo diseño)

Definir Área → Objetivo → Proyecto → Hito/entregable → Tarea, fechas planificadas, criterios de aceptación, pesos, relaciones, eventos, migraciones, API, exportación y backup. No crear modelos/migraciones/endpoints hasta aprobación expresa.

## 8. Fase 11 — Analytics (diseño)

Definir catálogo, historial, semántica temporal y reconstrucción. No inferir velocidad desde completed_at: se limpia al reabrir; los eventos actuales no guardan project_id al momento de la transición.

## 9. Fases futuras

Fase 12: Work/Business/Finance según necesidad real.  
Fase 13: AI Orchestrator con lectura, borradores, preview, aprobación, herramientas tipadas y auditoría.  
Fase 14: integraciones y acceso remoto solo con modelo de amenazas, autenticación, autorización, HTTPS, gestión de secretos y backup.

## 10. Priorización

1. Pérdida/corrupción de datos.
2. Seguridad.
3. Integridad y estados engañosos.
4. Flujos bloqueados.
5. Accesibilidad y responsive.
6. Jerarquía y usabilidad.
7. Estética menor.

## 11. Definition of Done

Criterios identificables, alcance respetado, pruebas reales, diff revisado, documentación afectada actualizada, archivos listados, limitaciones y revisión independiente. Dejar REVIEW hasta aceptación del PO.

## 12. Regla de autonomía

El Developer puede ejecutar únicamente tareas READY con SPEC. Si requiere migración, dependencia, cambio de arquitectura, seguridad, IA, integración o una decisión fuera de especificación, bloquear esa parte y consultar al PO. Las tareas dependientes no comienzan hasta que su dependencia esté verificada.
