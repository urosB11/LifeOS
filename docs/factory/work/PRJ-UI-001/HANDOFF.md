# Handoff: PRJ-UI-001 — Mantener las tareas visibles al abrir el formulario

**Fecha:** 2026-11-21
**De:** Developer — Mimo (reasignación del PO: "trabaja vos en las tareas restantes")
**Para:** Reviewer — Nemo / Product Owner
**Entrega:** SPEC `docs/factory/work/PRJ-UI-001/SPEC.md`
**Estado:** REVIEW

## Qué se hizo

En el detalle de proyecto, abrir "+ Nueva tarea" ya **no oculta la lista de
tareas**. El formulario se inserta debajo del encabezado de la sección
"Tareas" y antes de la lista; las tareas existentes se desplazan hacia abajo
de forma natural y siguen en el DOM.

Cambios en `frontend/assets/js/projects.js` (mismo archivo que BUG-001, sin
cambios de endpoint, modelo, migraciones ni dependencias):

- La sección Tareas pasó de un ternario que **reemplazaba** la tabla
  (`!taskFormOpen ? tabla : ""`) a dos bloques independientes: el formulario
  (si está abierto) y **siempre** la lista (tabla con tareas o estado
  vacío). La lista nunca se desmonta al abrir el formulario.
- El contador ("Tareas (N)") y el resumen ("N completadas · N pendientes ·
  N vencidas") viven en el encabezado de la sección, fuera del bloque
  condicional: siguen visibles con el formulario abierto.
- Estado vacío: cuando el proyecto no tiene tareas, el estado vacío se
  muestra **debajo del formulario** mientras está abierto (con un texto
  que indica que se use el formulario) y con su acción "Crear primera
  tarea" cuando está cerrado.
- Botón "+ Nueva tarea": pasa a "Cerrar formulario" con el formulario
  abierto, con `aria-expanded` y `aria-controls="task-form"`. Al abrir, el
  foco entra al formulario; al cerrar o cancelar, vuelve al botón.
- El formulario se labelló con `aria-label="Nueva tarea en <proyecto>"` y
  los campos conservan sus etiquetas y `maxlength`.

## Qué se verificó

Pruebas automatizadas (sin cambios de backend):

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa | `.venv\Scripts\pytest.exe -q` (desde `backend/`) | ✅ **140 passed** |
| Lint | `.venv\Scripts\ruff.exe check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check frontend/assets/js/projects.js` | ✅ OK |

QA interactiva (Edge headless vía CDP) con proyecto de 3 tareas y proyecto
sin tareas:

| Criterio de aceptación | Resultado |
|---|---|
| Mantener visible la lista al abrir el formulario | ✅ Con el formulario abierto: `tableInDom: true`, 3 filas ("Auditar planilla Q3", "Revisar contratos", "Publicar resumen") |
| Formulario debajo del encabezado y antes de la lista | ✅ `formTop: 764` < `tableTop: 899` (mismo orden en el DOM y en el layout) |
| No desaparecer, desmontarse ni reemplazarse | ✅ La tabla sigue montada; solo se reordena el contenido de la tarjeta |
| Mantener contador y resumen visibles | ✅ "Tareas (3)" y "1 completadas · 2 pendientes · 1 vencidas" visibles con el formulario abierto |
| Estado vacío debajo del formulario | ✅ Proyecto sin tareas: `emptyVisible: true`, `emptyBelowForm: true` |
| Cancelar quita solo el formulario | ✅ Tras cancelar: formulario ausente, estado vacío/lista presente, foco de vuelta en `#task-new-btn`, `aria-expanded="false"` |
| Responsive (1440/768/390) | ✅ La tarjeta no introduce scroll propio: escritorio 818/818, tableta 609/609 |

### Overlap móvil — comparación contra el código original

Medido a 390×844 sobre `#/projects/:id` con el mismo script contra la versión
publicada (`bfd3907`) y la nueva:

| Estado | Original | Nuevo |
|---|---|---|
| Formulario cerrado | `scrollWidth` 495 | `scrollWidth` 495 (idéntico) |
| Formulario abierto | `scrollWidth` 390 | `scrollWidth` 495 (igual al estado cerrado) |

**Conclusión:** el ensanche a 495px en 390px de viewport es **preexistente**
(ya estaba con el formulario cerrado, antes de este cambio) y lo provoca el
ancho intrínseco de la tabla de tareas dentro de `.main{margin:0 auto}`
(defecto raíz de STAB-001, pendiente de tarea nueva del PO). El original
medía 390px con el formulario abierto **solo porque eliminaba la tabla**,
que es justamente el defecto que PRJ-UI-001 corrige: el ancho no empeora
respecto del estado normal de la pantalla.

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/assets/js/projects.js` | Lista de tareas siempre montada, formulario antes de la lista, contador/resumen persistentes, estado vacío debajo del formulario, `aria-expanded`/`aria-controls`, foco al abrir/cancelar |
| `docs/factory/work/PRJ-UI-001/HANDOFF.md` | Nuevo — este documento |
| `docs/factory/work/WORK_QUEUE.md` | PRJ-UI-001 → REVIEW |

## Limitaciones y riesgos

- QA propia del Developer: las capturas son estáticas y no sustituyen una
  revisión manual en navegador real ni con lector de pantalla.
- El overflow horizontal móvil de esta pantalla (495px) es preexistente y
  no se corrigió aquí: su causa raíz (`.main{margin:0 auto}`) afecta a
  varias pantallas y requiere la tarea nueva pendiente de decisión del PO.
- Sin cambios de backend ni de contrato de API.

## Contexto para la siguiente tarea

- Rama `product/lifeos-evolution`; el commit se publica en
  `origin/product/lifeos-evolution` (sin merge ni push a `main`).
- Se entrega en el mismo commit que BUG-001 (mismo archivo, cambios
  entrelazados); ver `docs/factory/work/BUG-001/HANDOFF.md`.
- Siguiente en la cola: **HOME-001** (P0, `home.js`) y luego **TASK-001**
  (P1, `tasks.js`).
- Revisión independiente pendiente de Nemo (o del PO).
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
