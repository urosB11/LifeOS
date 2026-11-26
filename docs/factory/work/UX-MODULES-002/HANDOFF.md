# UX-MODULES-002 — Handoff

**Estado:** REVIEW · **Fecha:** 2026-11-22 · **Rama:** `product/lifeos-evolution`

## Entrega

- Projects muestra `+ Nuevo proyecto` con el panel cerrado por defecto. Abrir, cancelar o pulsar Escape mantiene visible la lista y restaura el foco; un error conserva el borrador y permite reintentar.
- Notes hace progresivas la creación de notas y etiquetas. Búsqueda, filtro y listas continúan disponibles mientras se usa el formulario.
- Las notas existentes se editan en un diálogo con Guardar y Cancelar. El guardado modifica título y contenido mediante el PATCH existente; las etiquetas y demás relaciones no se reescriben.
- Errores HTTP 422 conservan el borrador de edición; la creación conserva título, contenido y etiqueta elegida ante un error del POST.
- El contenido se representa como texto, incluidas cadenas que parecen HTML. Enter en el textarea agrega una línea y no envía el formulario.
- Los botones de acciones compactas de Projects y Notes miden al menos 44 CSS px.

## Archivos

- `frontend/assets/js/projects.js`
- `frontend/assets/js/notes.js`
- `frontend/assets/css/app.css`
- `docs/factory/work/WORK_QUEUE.md`

No hubo cambios de backend, API, modelos, seguridad, migraciones ni dependencias.

## Verificación

- Desde `backend\`: `.venv\Scripts\python.exe -m pytest` — **141 passed**, 1 warning de deprecación de Starlette.
- Desde `backend\`: `.venv\Scripts\python.exe -m ruff check app tests` — **All checks passed**.
- `node --check frontend\assets\js\projects.js` y `node --check frontend\assets\js\notes.js` — correctos.
- `git diff --check` — correcto.
- Smoke API en el servidor aislado `127.0.0.1:8001`: health, notas y proyectos respondieron correctamente. La base está bajo `LIFEOS_DATA_DIR` temporal; no se usó la base personal.
- QA interactiva: paneles cerrados por defecto, listas visibles, Escape y foco restaurado; POST fallido conserva el borrador, reintento crea sin duplicar; edición PATCH de título y contenido, error 422 con borrador conservado y reintento exitoso; filtro por etiqueta, relación preservada después de editar, confirmación al descartar/eliminar, trampa de foco y texto no ejecutable.
- Matriz Projects y Notes en 1440×900, 768×1024 y 390×844, en tema claro y oscuro: sin overflow horizontal de página; las tablas mantienen desplazamiento interno cuando corresponde. Los botones de acción compactos de Projects se ajustaron a 44 px y se volvieron a verificar.

## Pendiente y límites de QA

- QA propia completada; revisión independiente y aceptación del PO pendientes. Mantener el estado REVIEW.
- No se hizo prueba táctil física.
- La etiqueta sintética de QA permanece en la base temporal porque no existe una operación de borrado de etiquetas; las notas sintéticas creadas para las pruebas se eliminaron. No afecta datos personales.
