# MIND-003 — Guía del PO para planificación y revisión

**Entrega:** Canvas interactivo y relaciones visuales  
**Estado:** PLANNING — esta guía no es una SPEC ni autoriza código.  
**Responsable de la SPEC:** Mimo  
**Revisiones previas:** Opus (producto/UX) y Sonnet (arquitectura), en modo read-only.  
**Rama de planificación:** `planning/mind-001`  
**Futura rama de implementación:** `product/mind-core` (worktree separado de Evolution).

## 1. Fuentes obligatorias

Leer antes de redactar o revisar:

1. `docs/product/HOME_MIND_PRODUCT_DIRECTION.md` — decisiones D1–D5 y límites Home/Mind.
2. `docs/product/research/HOME_MIND_UX_PROPOSAL.md` — estudio UX original.
3. `docs/product/MIND_PRODUCT_MODEL.md` y `docs/product/MIND_ROADMAP.md`.
4. `docs/factory/work/MIND-002/SPEC.md` y `HANDOFF.md` en `product/mind-core`.
5. Implementación real en `backend/app/modules/mind/`, `backend/app/api/v1/mind.py`, `frontend/assets/js/mind-canvas.js` y `frontend/assets/css/mind.css`.
6. `docs/factory/work/MIND_WORK_QUEUE.md` y `AGENTS.md`.

El estudio UX original es un insumo de producto, no una instrucción para contradecir el roadmap aprobado. Ante diferencias, prevalecen el modelo de producto y las decisiones D1–D5 de la sección enlazada arriba.

## 2. Resultado que debe producir MIND-003

Completar el Canvas como un entorno espacial útil y fiable. La SPEC debe definir una entrega vertical, acotada y persistente que cubra:

- conexiones visuales entre Cards;
- selección múltiple;
- redimensionamiento de Cards;
- orden visual / capas;
- accesibilidad por teclado y touch para selección, movimiento, conexión y resize;
- operaciones reversibles y undo/redo con comportamiento definido;
- persistencia backend de los cambios espaciales y recuperación tras recargar;
- acción explícita para añadir una Note existente del Inbox a un Canvas, reutilizando el contenido canónico y sin retirarlo del Inbox automáticamente;
- exportación, backup, restore e integridad referencial de cualquier dato nuevo;
- regresión de las capacidades MIND-002: Spaces, Inbox, Cards, drag, pan, zoom y teclado.

Agrupación/frames son **opcionales**: incluirlos solo si la revisión UX identifica un caso de uso claro y la auditoría técnica demuestra que no comprometen el alcance principal.

## 3. Distinciones de dominio que la SPEC debe respetar

- Una **conexión visual** une dos instancias de Cards en un Canvas. Pertenece al Canvas y no implica semántica global.
- Una **relación semántica** conecta contenidos canónicos independientemente de su ubicación. Queda para MIND-005.
- La Card/Node es una representación; la Note sigue siendo el contenido canónico.
- El backend actual ya dispone de `mind_canvas_nodes.width`, `height` y `z_index`, y el servicio `attach_note` permite representar una Note existente en un Canvas.
- La restricción actual permite una representación de una Note por Canvas y la misma Note en Canvas distintos. Verificar el comportamiento real antes de proponer cambios.
- MIND-002 ya ofrece movimiento, pan, zoom y alternativa por teclado. No rehacer esas capacidades; ampliar y probar sin regresiones.
- No crear una tabla de relaciones semánticas, biblioteca Knowledge, sistema nuevo de documentos, modelo duplicado de Notes ni integración con Tasks/Projects/Habits en MIND-003.

## 4. Trabajo de los agentes

### Opus — revisión de producto y UX (read-only)

Lee esta guía, la dirección Home–Mind, el estudio UX, el modelo de Mind, el roadmap y la SPEC/HANDOFF de MIND-002. Devuelve:

- contradicciones o decisiones aún ambiguas;
- flujo de usuario recomendado para crear/conectar/seleccionar/redimensionar;
- riesgo de complejidad y qué dejar fuera;
- criterios UX observables y escenarios de aceptación;
- evaluación de si frames/agrupación aportan valor ahora.

No modifica archivos, no redacta una SPEC alternativa completa y no escribe código.

### Sonnet — auditoría de arquitectura (read-only)

Inspecciona el código actual y devuelve:

- capacidades API/modelo ya disponibles y sus límites reales;
- diseño mínimo viable de conexiones visuales y restricciones de integridad;
- estrategia de selección, resize y z-order sin duplicar estado;
- opciones de undo/redo con persistencia y recuperación ante errores;
- impacto de export/backup/restore, eventos, pruebas y migraciones;
- conflictos conocidos de Alembic y prerequisitos de integración;
- estimación de complejidad y riesgos por subentrega.

No modifica archivos, no crea migraciones, no ejecuta cambios en DB y no empieza implementación.

### Mimo — SPEC y plan (sin código por ahora)

1. Verifica `git status`, rama, HEAD y worktrees antes de tocar nada. Identifica cualquier trabajo local no publicado que ya exista para MIND-003.
2. Preserva todos los cambios locales. No reset, clean, checkout destructivo, stash destructivo ni sobrescritura. Si hay trabajo sin publicar, intégralo conscientemente; no lo reemplaces por este documento.
3. Lee todas las fuentes obligatorias y obtiene los informes de Opus y Sonnet.
4. Consolida una única SPEC en `docs/factory/work/MIND-003/SPEC.md` y un HANDOFF/PLAN asociado.
5. La SPEC debe incluir: objetivo, flujo UX, alcance y exclusiones, modelo de datos, contrato API, estrategia de persistencia, undo/redo, accesibilidad, responsive, export/restore, migraciones, eventos, errores, pruebas, criterios de aceptación y riesgos.
6. Separa lo existente de lo nuevo. Para cada cambio de esquema/API explica por qué no alcanza lo ya implementado.
7. Actualiza la cola solo para reflejar el estado real. MIND-003 permanece PLANNING hasta aceptación del PO; no marcar READY ni empezar código.
8. Revisa el diff, deja commits pequeños y publica solo en `planning/mind-001`. No hacer push a `product/lifeos-evolution`, `product/mind-core` ni `main` durante la planificación.
9. Informa hash, push, archivos, decisiones tomadas, puntos abiertos y cualquier trabajo local previo que hayas preservado.

## 5. Bloqueos y límites para la futura implementación

- Antes de implementar, el PO debe aceptar la SPEC y mover MIND-003 a READY.
- La colisión Alembic entre `0006_mind` y `0006_home_widget_grid` no se resuelve durante la planificación. El handoff MIND-002 recomienda renumerar la migración Mind como `0007_mind`, pero requiere revisión de dependencias y decisión/alcance de integración. No editar migraciones por anticipado.
- Implementación en un worktree separado de Evolution. Nunca apuntar QA o migraciones a la DB personal; usar `LIFEOS_DATA_DIR` temporal.
- No fusionar toda `planning/mind-001` a la rama de producto: transferir solo documentos aprobados.
- No introducir frameworks, dependencias, librerías de Canvas ni servicios remotos sin aprobación.

## 6. Gate de aceptación PO

La entrega puede pasar a READY cuando:

- Opus y Sonnet hayan entregado revisión;
- los comentarios estén resueltos o registrados como decisiones explícitas;
- la SPEC sea coherente con el roadmap y con el código real;
- no haya ambigüedad sobre conexiones visuales vs. relaciones semánticas;
- undo/redo y persistencia tengan un diseño verificable;
- el alcance sea implementable sin tocar Home ni la base personal;
- existan criterios de aceptación y pruebas concretas.

**Hasta entonces: planificación solamente.**
