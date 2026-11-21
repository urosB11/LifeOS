# Handoff: BUG-001 — Conservar el formulario de creación de tarea ante error

**Fecha:** 2026-11-21
**De:** Developer — Mimo (reasignación del PO: "trabaja vos en las tareas restantes")
**Para:** Reviewer — Nemo / Product Owner
**Entrega:** SPEC `docs/factory/work/BUG-001/SPEC.md`
**Estado:** REVIEW

## Qué se hizo

Reproducción del defecto y corrección en `frontend/assets/js/projects.js`
(detalle de proyecto). **Sin cambios de endpoint, modelo, migraciones ni
dependencias.**

### Reproducción (código anterior)

`createTask()` leía los campos del DOM y acto seguido ejecutaba
`creatingTask = true; renderDetail();`. `renderDetail()` reemplaza
`contentEl.innerHTML` por completo, así que el formulario se reconstruía
**vacío** antes de la petición y se reconstruía **vacío** otra vez después
del error. Resultado: título, descripción, prioridad y vencimiento se
perdía con cualquier error HTTP o de conexión.

### Corrección

1. **Borrador en estado** (`taskDraft = { title, desc, priority, due }`).
   `captureTaskDraft()` lee el formulario vivo antes de cada re-render y
   `renderDetail()` restaura los valores en los campos
   (`value="${escapeHtml(taskDraft.title)}"`, `<option selected>` para la
   prioridad). El borrador sobrevive a re-renders por error, por recarga del
   proyecto y por el propio `creatingTask`.
2. **Error junto al formulario**: `<span id="task-error" role="alert"
   tabindex="-1">` dentro del grupo de botones, con el detalle de la API
   formateado (`formatApiDetail`: string, objeto o lista de errores 422).
   Los mensajes se guardan en texto plano y se escapan al renderizar.
3. **Foco**: tras un error 400/422 el foco va al primer campo inválido
   (`#task-title`, con `aria-invalid` + `aria-describedby`); en otros casos
   (red caída, 500) al mensaje de error (`focusTaskError()`).
4. **Doble envío**: bandera `creatingTask` (guarda síncrona antes del
   `await`), botón `type="submit"` con `disabled` y etiqueta
   "Guardando…" mientras la petición está pendiente. Clic y Enter pasan por
   el mismo flujo (`submit` del formulario), sin doble handler.
5. **Éxito**: el formulario se cierra, el borrador se limpia, `load()`
   refresca tareas y métricas del proyecto, y se muestra el toast
   "Tarea creada".
6. **Cancelar**: quita solo el formulario y devuelve el foco al botón
   "+ Nueva tarea".

## Qué se verificó

Pruebas automatizadas (sin cambios de backend; la suite completa cubre la
regresión):

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa | `.venv\Scripts\pytest.exe -q` (desde `backend/`) | ✅ **140 passed** |
| Lint | `.venv\Scripts\ruff.exe check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check frontend/assets/js/projects.js` | ✅ OK |

QA interactiva (Edge headless vía CDP, sin dependencias nuevas) contra
Uvicorn en `127.0.0.1:8000` con `LIFEOS_DATA_DIR` temporal y base creada
con Alembic. El error de red se simuló interceptando el `POST
/api/v1/tasks` con el dominio `Fetch` de CDP (`Fetch.failRequest`), que
provoca un fallo de conexión real en el `fetch` del navegador.

| Criterio de aceptación | Resultado |
|---|---|
| Mantener título, descripción, prioridad y vencimiento ante error | ✅ Tras el error de red: `title="Tarea que debe sobrevivir"`, `desc="Descripción con acentos: auditoría, números y detalle"`, `priority="high"`, `due="2026-12-31"` |
| Mostrar el error junto al formulario | ✅ `#task-error` visible, `role="alert"`, texto "Error de conexión. Verifica que el servicio esté activo e inténtalo de nuevo." |
| Mantener el formulario abierto | ✅ `#task-form` sigue en el DOM tras el error |
| Enfocar el primer campo inválido o el mensaje | ✅ Foco en `#task-error` (error de red) y en `#task-title` con `aria-invalid` (error de validación) |
| Evitar doble envío | ✅ 3 clics consecutivos sobre "Crear tarea" → **1 sola tarea creada** (3 → 4); botón deshabilitado mientras la petición está pendiente |
| Éxito: cerrar, limpiar, actualizar y confirmar | ✅ Formulario cerrado, borrador limpiado, lista 3 → 4 filas, contador "Tareas (4)", toast "Tarea creada" |
| Enter envía | ✅ Enter en el campo título creó la tarea (4 → 5 filas) y cerró el formulario |

Artefactos: `C:\Users\uriel\AppData\Local\Temp\opencode\bug001_shots\`
(`report_bug001_prjui.json` + capturas por viewport).

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/assets/js/projects.js` | Borrador persistente del formulario, error junto al formulario, foco, doble envío, submit único por Enter, helpers `emptyTaskDraft`, `formatApiDetail`, `captureTaskDraft`, `focusTaskError` |
| `docs/factory/work/BUG-001/HANDOFF.md` | Nuevo — este documento |
| `docs/factory/work/WORK_QUEUE.md` | BUG-001 → REVIEW |

## Limitaciones y riesgos

- El único error de consola observado en la QA es
  `net::ERR_FAILED ... /api/v1/tasks`, provocado **por la propia
  intercepción de red del test**, no por la aplicación.
- La corrección es del flujo del **detalle de proyecto**. El SPEC acota el
  alcance a ese formulario ("No modificar otros formularios salvo defecto
  reproducido y corrección aislada"); no se tocó el formulario de Tareas ni
  el de Home, que tienen su propia tarea (TASK-001 / HOME-001).
- Sin cambios de backend: el contrato de `POST /api/v1/tasks` se usa tal
  cual.

## Contexto para la siguiente tarea

- Rama `product/lifeos-evolution`; el commit se publica en
  `origin/product/lifeos-evolution` (sin merge ni push a `main`).
- PRJ-UI-001 comparte archivo (`projects.js`) y se entrega en el mismo
  commit; ver `docs/factory/work/PRJ-UI-001/HANDOFF.md`.
- Revisión independiente pendiente de Nemo (o del PO).
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
