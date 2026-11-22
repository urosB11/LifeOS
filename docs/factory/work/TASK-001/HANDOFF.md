# Handoff: TASK-001 — Espacio de trabajo de Tareas

**Fecha:** 2026-11-21
**De:** Developer — Mimo (reasignación del PO: "trabaja vos en las tareas restantes")
**Para:** Reviewer — Mimo / Product Owner
**Entrega:** SPEC `docs/factory/work/TASK-001/SPEC.md`
**Estado:** REVIEW

## Qué se hizo

La vista de Tareas dejó de ser "una tabla genérica con un formulario
permanente" y pasó a ser un **espacio de trabajo**: la captura es una acción
compacta (panel desplegable), las filas son escaneables (estado, prioridad,
fecha, proyecto) y las acciones frecuentes están separadas de la eliminación.

Sin endpoints nuevos, sin migraciones, sin dependencias: se reutilizan
`GET/POST/PATCH/DELETE /tasks`, `POST /tasks/{id}/complete` y
`POST /tasks/{id}/reopen`, y el `showConfirm` ya existente.

### Alcance funcional cubierto (SPEC §Alcance funcional)

| Ítem | Implementación |
|---|---|
| 1. Crear con acción compacta y formulario desplegable | Botón "+ Nueva tarea" con `aria-expanded` / `aria-controls="task-panel"`; el panel está **oculto por defecto** (`hidden`) y se despliega al pulsar |
| 2. Editar con PATCH | Título, descripción, prioridad, vencimiento y proyecto; el panel se abre precargado con los valores actuales |
| 3. Completar/reabrir y eliminar con confirmación | Botón de estado alterna `complete`/`reopen`; eliminar pide confirmación explícita (`showConfirm`) |
| 4. Filtros por estado y proyecto | Se conservan los dos filtros, ahora con etiquetas accesibles (`aria-label`) |
| 5. Contadores de pendientes/completadas | Barra de contadores con totales reales + cuántas tareas son visibles con el filtro aplicado |
| 6. Vencimientos sin depender solo del color | Chips textuales: "Vencida el 2026-11-18", "Vence hoy", "Vence el 2026-11-25", "Sin fecha" |
| 7. Acceso al proyecto | Enlace `chip--link` al proyecto (`#/projects/{id}`) |
| 8. Conservar formularios ante errores y prevenir doble submit | Borrador en estado + error junto al formulario + foco al campo + guardia `form.pending` y botón deshabilitado |

### Detalles de implementación

- **Contadores globales, lista filtrada.** Con un filtro activo se consulta
  además el conjunto completo (`GET /tasks`) para no mostrar "0 completadas"
  cuando el filtro esconde las completadas. La barra muestra
  `N pendientes · N completadas · N vencidas · Filtro aplicado · N tareas
  visibles`.
- **Editar permite limpiar campos.** En alta solo se envían los campos con
  valor; en edición (PATCH) los campos opcionales vacíos se envían como
  `null`, de modo que se puede quitar prioridad, vencimiento, proyecto o
  descripción (antes quedaban pegados al valor anterior).
- **Proyectos ordenados por nombre** en los desplegables (la API no garantiza
  orden y un desplegable predecible es más escaneable).
- **Aviso de filtro activo.** Si la tarea recién guardada no aparece en la
  lista porque un filtro la esconde, se informa ("No aparece en la lista
  porque hay un filtro aplicado.") en lugar de dar la impresión de que no se
  guardó.
- **Acción destructiva atenuada.** "Eliminar" usa contorno de peligro en vez
  de relleno sólido, para que la acción frecuente (Editar) no compita
  visualmente con ella. La confirmación sigue siendo obligatoria.
- **Teclado.** Enter en el título envía el formulario; ESC cierra el panel y
  devuelve el foco al botón "+ Nueva tarea". El listener de ESC vive en el
  panel (no en `document`), para no acumular listeners globales en cada
  navegación; además no interfiere con el ESC del modal de confirmación.
- **Responsive.** En ≤768px la fila pasa a tipo tarjeta: las acciones bajan a
  su propia línea y el formulario del panel queda en una sola columna
  alineada a la izquierda.

### Componentes compartidos reutilizados

`.chip` (antes `.home-chip`) y `.check-toggle` (antes `.home-task__check`)
pasaron a ser clases genéricas compartidas por Home y Tareas, en lugar de
duplicar estilos. Home se actualizó para usar las nuevas clases sin cambio
de comportamiento.

## Qué se verificó

Pruebas automatizadas (sin cambios de backend):

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa | `.venv\Scripts\pytest.exe -q` (desde `backend/`) | ✅ **140 passed** (1 warning) |
| Lint | `.venv\Scripts\ruff.exe check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check` sobre `tasks.js`, `home.js`, `settings.js`, `projects.js`, `habit-entry.js`, `app.js` | ✅ OK |
| Whitespace | `git diff --check` | ✅ Sin errores |

QA interactiva y visual (Edge headless vía CDP, sin dependencias nuevas)
contra Uvicorn en `127.0.0.1:8000` con `LIFEOS_DATA_DIR` temporal y base
creada con Alembic. **0 hallazgos.**

| Criterio de aceptación | Resultado |
|---|---|
| Crear y editar tareas desde la vista | ✅ Crear: la tarea aparece con prioridad "Alta", vencimiento "Vence el 2026-11-24", proyecto y descripción; la API confirma los 4 campos. Editar: el panel se abre precargado (título, prioridad, vencimiento, proyecto, descripción) y el PATCH actualiza la fila y la API |
| Guardar y mostrar campos opcionales | ✅ Descripción visible en la fila; vacío → `null` en la API; quitarla deja la fila con "Sin fecha" y sin badge de prioridad |
| Mantener filtros al actualizar | ✅ Los filtros se conservan al guardar; con filtro activo se avisa que la tarea no es visible |
| Diferenciar vencida, pendiente y completada | ✅ "Vencida el 2026-11-18" (texto, no solo color), "Vence hoy", badge "Pendiente"/"Completada" y fila tachada al completar |
| Errores no borran formularios | ✅ Con el POST bloqueado por red: el título "Tarea que debe sobrevivir al error" **se conservó**, el panel siguió abierto, el error se mostró junto al formulario ("Error de conexión. Inténtalo de nuevo."), el foco volvió al campo y el botón se rehabilitó |
| Acciones destructivas confirmadas | ✅ Modal "Eliminar tarea" con el nombre de la tarea; "Cancelar" no borra (verificado en la API), "Eliminar" sí (verificado en la API) |
| Responsive, teclado y estados completos | ✅ 1440×900 / 768×1024 / 390×844 sin scroll horizontal (`scrollWidth == clientWidth`), filas sin desborde con texto largo, acciones en su propia línea en móvil; Enter crea, ESC cierra y devuelve el foco; estados de carga, vacío, error y confirmación |
| Compatibilidad con tareas creadas desde Proyectos y Home | ✅ La tarea creada desde la captura de Home y la creada en el detalle de Proyectos aparecen en Tareas, con su prioridad y su proyecto |

Otros verificados en la QA:

- **Doble submit:** triple clic en "Guardar tarea" → **1 sola tarea** creada.
- **Completar/reabrir:** el estado alterna correctamente y los contadores se
  actualizan ("8 pendientes 3 completadas 1 vencida").
- **Filtro por proyecto:** muestra solo tareas del proyecto; el filtro por
  estado "completadas" muestra 2 y "pendientes" 8, coherente con la semilla.
- **Orden de proyectos:** el desplegable de proyecto aparece ordenado por
  nombre.
- **Sin errores de consola** relevantes (se descartan solo los `ERR_FAILED`
  provocados por la simulación de red y el favicon).

Artefactos: `C:\Users\uriel\AppData\Local\Temp\opencode\task001_shots\`
(`report_task001.json` + capturas por viewport, panel abierto en tema
claro/oscuro, tablet y móvil).

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/assets/js/tasks.js` | Reescrito: panel desplegable accesible, alta/edición (POST/PATCH) con borrador persistente, completar/reabrir, eliminar con confirmación, filtros conservados, contadores globales + visibles, chips de vencimiento textuales, enlace al proyecto, estados completos y teclado |
| `frontend/assets/css/app.css` | Nuevo bloque "Espacio de trabajo de Tareas" (`.task-panel*`, `.tasks-summary*`, `.task-row*`, `.chip--link`, `.task-row__delete`); `.home-chip*` → `.chip*` y `.home-task__check` → `.check-toggle` como componentes compartidos; reglas de tarjeta en móvil y panel en una columna |
| `frontend/assets/js/home.js` | Solo ajuste de clases compartidas (`.chip*`, `.check-toggle`); sin cambio de comportamiento |
| `docs/factory/work/TASK-001/HANDOFF.md` | Nuevo — este documento |
| `docs/factory/work/WORK_QUEUE.md` | TASK-001 → REVIEW |

## Limitaciones y riesgos

- QA propia del Developer: las capturas son estáticas y no sustituyen una
  revisión manual en navegador real ni con lector de pantalla.
- El contador de vencidas usa la fecha local del navegador (igual que Home);
  una tarea vencida "según la zona horaria del cliente" puede diferir de la
  del servidor en tareas justo alrededor de medianoche.
- El filtro de proyecto usa el `project_id` que expone el endpoint actual;
  no hay filtro por texto (fuera de alcance según el SPEC).
- La lista no pagina: se muestran todas las tareas que devuelve la API
  (límite 100 en el backend). Con muchas tareas habría que pensar en
  paginación, que no está en el alcance de TASK-001.
- Sin cambios de backend: si en el futuro se quiere búsqueda global o
  subtareas, el SPEC las excluye explícitamente.

## Contexto para la siguiente tarea

- Rama `product/lifeos-evolution`; el commit se publica en
  `origin/product/lifeos-evolution` (sin merge ni push a `main`).
- Siguiente en la cola: **UX-REVIEW-001** (revisión de UX, sin código) y
  después el cierre de Fase 9.
- Sigue pendiente de decisión del PO el **overflow horizontal móvil** de
  STAB-001 (`.main{margin:0 auto}`), que afecta a 5 pantallas; Home y
  Tareas no sufren ese defecto (390px sin overflow), pero Proyectos,
  Hábitos y Notas sí.
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
