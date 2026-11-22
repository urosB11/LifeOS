# WORK_QUEUE — Cola central de trabajo

**Actualizada:** 22 de noviembre de 2026. Coordinator mantiene; PO prioriza.

## Estados
READY = especificada y autorizada; PLANNING = solo diseño; IN_PROGRESS = ejecución; REVIEW = revisión/aceptación; APPROVED = aceptada; DONE = cerrada; BLOCKED = decisión/dependencia; CANCELLED = cancelada.

## Completadas en main
- FACTORY-001: estructura factory.
- UX-001: auditoría inicial (informe presentado; no todos los artefactos originales versionados).
- PRJ-001: métricas y detalle, commit afaf6cde2e72d00d72d317711d0c2d3fb442270e.
- PRJ-002: crear tareas desde proyecto, mismo commit.
- HAB-001: calendario compacto, commit 27791fc8a157a8733f5bb322a7f19c845a251995.

## Fase 9 — entregas anteriores en REVIEW
### STAB-001 — QA manual Fase 8
Prioridad P0 · Reviewer Mimo · Spec STAB-001/SPEC.md · Solo revisión, no código. **Estado: REVIEW — veredicto de Mimo: REJECT** (2026-11-21). QA de Nemo verificado independientemente (139/139 pytest, ruff OK, node --check OK) + revisión visual Edge headless/CDP en 1440×900, 768×1024, 390×844. Hallazgos: ALTA overflow horizontal móvil en 5 pantallas (causa: `.main{margin:0 auto}` en flex column de `.app-content` — **no contemplado en la cola, requiere tarea nueva**); ALTA confirmada BUG-001 (campos perdidos tras error); MEDIA confirmada PRJ-UI-001 (tareas fuera del DOM con formulario abierto); MEDIA foco no restaurado al cerrar modal con ESC; BAJA favicon 404. Detalle en STAB-001/HANDOFF.md. Pendiente: aceptación del PO.

### BUG-001 — Conservar formulario ante error
Prioridad P0 · Developer Nemo (ejecución reasignada por el PO a Mimo) · Spec BUG-001/SPEC.md · **Estado: REVIEW** (2026-11-21) — reproducción confirmada y corregida en `projects.js`: borrador persistente del formulario, error junto al formulario (`role="alert"`), foco en el campo inválido o en el mensaje, sin doble envío. QA propia: 140/140 pytest, ruff y node --check OK, QA interactiva CDP sin hallazgos ALTA. Handoff: `docs/factory/work/BUG-001/HANDOFF.md`.

### HAB-002 — Semana interactiva y calendarios por hábito
Prioridad P1 · Developer Mimo (asignación explícita del PO) · Reviewer Nemo · Depende de STAB-001 para liberar a Mimo de la revisión independiente · Spec HAB-002/SPEC.md. **Estado: REVIEW** (Mimo, 2026-11-21) — implementación completa y QA propia ejecutada (140/140 pytest, ruff y node --check OK, QA visual en 3 viewports sin hallazgos ALTA); pendiente revisión independiente de Nemo. Handoff: `docs/factory/work/HAB-002/HANDOFF.md`.

### PRJ-UI-001 — Mantener las tareas visibles al abrir el formulario
Prioridad P1 · Developer Mimo (asignación explícita del PO) · Reviewer Nemo · Después de BUG-001 para evitar solapamiento en projects.js · Spec PRJ-UI-001/SPEC.md. **Estado: REVIEW** (2026-11-21) — la lista de tareas permanece en el DOM con el formulario abierto (formulario antes de la lista, contador/resumen visibles, vacío debajo del formulario); entregado en el mismo commit que BUG-001. Handoff: `docs/factory/work/PRJ-UI-001/HANDOFF.md`.

### HOME-001 — Home como centro de operaciones
Prioridad P0 · Developer Nemo (ejecución reasignada por el PO a Mimo) · Depende de STAB-001/BUG-001 y de HAB-002 por solapamiento en home.js · Spec HOME-001/SPEC.md. **Estado: REVIEW** (2026-11-21) — Home reescrito como centro de operaciones (Atención, Hoy, Proyectos en marcha, Hábitos de hoy, Captura rápida, Semana de hábitos); se eliminaron las seis tarjetas métricas iguales; catálogo de widgets conservado (ids, visibilidad y orden functioning, verificado). Incluye corrección aislada del tema claro, que nunca se aplicaba. QA propia: 140/140 pytest, ruff y node --check OK, QA interactiva/visual CDP en 3 viewports y 2 temas con 0 hallazgos. Handoff: `docs/factory/work/HOME-001/HANDOFF.md`.

### TASK-001 — Espacio de trabajo de Tareas
Prioridad P1 · Developer Nemo (ejecución reasignada por el PO a Mimo) · Secuencial después de HOME-001 · Spec TASK-001/SPEC.md. **Estado: REVIEW** (2026-11-21) — vista de Tareas rediseñada como espacio de trabajo: captura por acción compacta (panel desplegable oculto por defecto), edición con PATCH (incluye limpiar campos opcionales), completar/reabrir, eliminar con confirmación, filtros conservados con contadores globales + visibles, vencimientos con texto, enlace al proyecto y estados completos; en móvil las filas pasan a tipo tarjeta. QA propia: 140/140 pytest, ruff y node --check OK, QA interactiva/visual CDP en 3 viewports y 2 temas con 0 hallazgos. Handoff: `docs/factory/work/TASK-001/HANDOFF.md`.


## Fase 9.1 — Interacción directa y experiencia fluida

**Rama:** product/lifeos-evolution · **Developer:** Mimo · **Orden secuencial obligatorio.**  
La etapa aplica la dirección de VISION.md y docs/product/UX_DIRECTION.md: interfaz útil y contextual, no CRUD administrativo ni dashboard decorativo. Mantiene el stack y la fuente de verdad actuales.

### RESPONSIVE-002 — Corregir overflow horizontal móvil
Prioridad P0 · Developer Mimo · **Estado: REVIEW** (2026-11-22) · Spec: RESPONSIVE-002/SPEC.md · Sin dependencia.
Se confirmó que `.main` podía crecer a su ancho intrínseco dentro de `.app-content`; al fijar `width: 100%` y `min-width: 0`, Projects, detalle, Habits y Notes dejaron de ampliar la página. QA detectó además que el filtro de proyecto de Tareas heredaba el ancho de una opción larga; los `select` de `.filters-bar` ahora quedan limitados a su contenedor. Sin `overflow-x:hidden` ni recorte de contenido. Verificación browser en 1440×900, 768×1024 y 390×844, siete rutas y ambos temas: sin overflow de página; las tablas conservan scroll interno en `.table-wrap`. pytest 140/140, Ruff, node --check, smoke HTTP/API y `git diff --check` OK. Handoff: RESPONSIVE-002/HANDOFF.md. Pendiente revisión/aceptación del PO.

### UX-HOME-002 — Claridad de Home y captura contextual
Prioridad P1 · Developer Mimo · **Estado: REVIEW** (2026-11-22) · Depende de RESPONSIVE-002 · Spec: UX-HOME-002/SPEC.md.
Atención y Hoy son disjuntas por ID, conservan límites y contadores; los errores no se anuncian como listas vacías; proyectos sin tareas muestran “Sin tareas”; Captura rápida tiene modos Tarea/Nota, un solo formulario visible, borradores separados y contenido de nota. La zona horaria configurada gobierna Home y el reloj local del backend ahora lee correctamente la preferencia guardada. Sin cambios de API, modelo, migración ni dependencias. QA: 141 pytest, Ruff, node --check, smoke HTTP/API y matriz visual Home 1440×900, 768×1024, 390×844 en ambos temas sin overflow. Handoff: UX-HOME-002/HANDOFF.md. Pendiente revisión/aceptación del PO.

### UX-WIDGETS-002 — Personalización visual de widgets
Prioridad P1 · Developer Mimo · **Estado: REVIEW** (2026-11-22) · Depende de UX-HOME-002 · Spec: UX-WIDGETS-002/SPEC.md.
Home ahora ofrece personalización explícita con arrastre por asa, controles accesibles mover arriba/abajo, visibilidad independiente y guardar/cancelar; Settings ya no duplica el editor. Solo se reordenan widgets dentro de sus zonas actuales y Captura rápida se mueve como grupo. Sin cambios de API, modelo, migración ni dependencias. QA propia: 141 pytest, Ruff, node --check, persistencia/error/reintento, teclado y matriz visual en 1440×900, 768×1024 y 390×844 en ambos temas sin overflow. Handoff: UX-WIDGETS-002/HANDOFF.md. Pendiente revisión independiente y aceptación del PO.

### UX-MODULES-002 — Formularios progresivos y edición de notas
Prioridad P1 · Developer Mimo · **Estado: REVIEW** (2026-11-22) · Depende de UX-WIDGETS-002 · Spec: UX-MODULES-002/SPEC.md.
Projects y Notes abren los formularios de alta bajo demanda sin ocultar sus listas; el alta de etiquetas también es progresiva. Notes permite editar título y contenido con PATCH, conserva borradores ante error y deja intactas las relaciones no editadas. Los datos se mantienen como texto seguro. Sin cambios de API, modelo, migraciones ni dependencias. QA propia: pytest (141), Ruff, node --check, smoke API y flujos interactivos; matriz visual en 1440×900, 768×1024 y 390×844, ambos temas, sin overflow horizontal. Handoff: UX-MODULES-002/HANDOFF.md. Pendiente revisión independiente y aceptación del PO.

### UX-REVIEW-002 — Revisión UX independiente
Prioridad P1 · Reviewer distinto del Developer (Copilot UX preferente) · Estado: PLANNING · Spec: UX-REVIEW-002/SPEC.md.  
Se habilita cuando las cuatro entregas anteriores estén en REVIEW. Solo lectura, sin código, commits ni cambios. Verifica flujos, estados, accesibilidad, teclado, puntero/táctil, temas y tres viewports. Mimo no puede autoaprobar sus entregas.

**Secuencia para Mimo:** ejecutar RESPONSIVE-002 → UX-HOME-002 → UX-WIDGETS-002 → UX-MODULES-002. Una tarea por vez; commit y push verificado por tarea a product/lifeos-evolution; dejar REVIEW. Si la especificación no alcanza o una prueba contradice el modelo de producto, detener solo la parte afectada y elevar la decisión.

**Decisiones expresamente fuera de alcance:** mover widgets entre main/side/full; migrar o extender widget_preferences; cambiar config_json; cambiar el token global --text-muted; cambiar el comportamiento del tema “Sistema”; añadir librerías/frameworks/endpoints; reconstruir Home o el shell completo.


## Fase 9.2 — Distribución flexible de widgets

### UX-WIDGETS-003 — Grid redimensionable de Home
Prioridad P1 · Developer Mimo · **Estado: REVIEW** (2026-11-22; QA propia, pendiente revisión independiente y aceptación del PO) · Depende de UX-WIDGETS-002 · Spec: UX-WIDGETS-003/SPEC.md · ADR-003.
Home reemplaza las zonas fijas por un grid responsive con orden y spans persistidos. Incluye drag, resize, alternativas de teclado, migración de `widget_preferences` y actualización de exportación. Projects y Notes no se modifican. Sin dependencias nuevas. QA propia: pytest completo, Ruff en archivos backend afectados, `node --check`, migración temporal desde 0005 con downgrade/re-upgrade, persistencia tras reload, Cancel, drag/resize con mouse y touch emulados, resize por teclado, captura interna y matriz clara/oscura en 1440×900, 768×1024 y 390×844 sin overflow; asas verificadas ≥44×44 CSS px. La validación en dispositivo táctil físico queda pendiente de revisión independiente. Handoff: UX-WIDGETS-003/HANDOFF.md. No aceptar como DONE hasta revisión independiente y PO.

## Revisión
### UX-REVIEW-001
Reviewer Mimo · Después de HOME-001 y TASK-001. **Estado: REVIEW** (2026-11-21) — revisión de UX de Home y Tareas con auditoría objetiva (contraste calculado en el navegador, foco con teclado real, roles y nombres accesibles, trampa de foco del modal, estados y responsive en 3 viewports y 2 temas). Veredicto: **APROBADO CON CORRECCIONES APLICADAS** — 0 ALTA, 4 MEDIA (contraste AA, trampa de foco, restauración de foco y fuga del listener ESC en el modal de widgets) y 3 BAJA, todas corregidas y verificadas (0 fallos de contraste, 0 salidas del modal). Queda 1 pendiente de decisión del PO (token global `--text-muted`). **Nota:** la revisión la realizó el mismo agente que implementó HOME-001 y TASK-001 (reasignación del PO), por lo que es QA propia, no revisión independiente: sigue pendiente el contraste de Nemo. Informe: `docs/factory/work/UX-REVIEW-001/REVIEW.md`.

## Diseño futuro — no autoriza código
### PRJ-PLAN-001
PLANNING · Diseño de hitos, entregables, planificación y progreso real · Spec PRJ-PLAN-001/DESIGN_TASK.md.

### PRJ-WORKSPACE-001 — Proyecto como espacio de trabajo
PLANNING · Diseño de arquitectura funcional e información del proyecto (resumen, tareas, notas, documentos/recursos y seguimiento) · Spec PRJ-WORKSPACE-001/DESIGN_TASK.md · No implementar.

### ANALYTICS-001
PLANNING · Catálogo, historial y semántica temporal · Depende de PRJ-PLAN-001 · Spec ANALYTICS-001/DESIGN_TASK.md.

## Regla
Cada tarea entrega pruebas reales y handoff. Todo commit de implementación debe hacerse push a la rama remota de trabajo asignada y verificarse; no hacer merge ni push a main. PO acepta el cierre.