# UX-WIDGETS-002 — Handoff

**Estado:** REVIEW · **Fecha:** 2026-11-22 · **Rama:** `product/lifeos-evolution`

## Entrega

- Home tiene un modo explícito **Personalizar** con un borrador local de orden y visibilidad.
- Los widgets se arrastran desde un asa; también se pueden mover arriba/abajo con botones que funcionan con teclado. No se permite cambiar de zona.
- Las seis preferencias se pueden activar u ocultar. `quick_add_task` y `quick_add_note` comparten una tarjeta movible, pero mantienen visibilidad independiente.
- Guardar envía un único `PUT /dashboard/widgets`; cancelar descarta el borrador. Un error conserva los cambios y ofrece reintento.
- Settings elimina su editor de orden/visibilidad duplicado y enlaza a Home.
- El estado sin widgets visibles conserva las preferencias editables sin mostrar una acción duplicada que pueda reiniciar el borrador.

## Persistencia de posiciones

Se conserva el catálogo de seis IDs y el contrato existente. Al guardar se envía, por cada ID, únicamente `widget_id`, `is_visible` y `position`.

Las posiciones son enteros consecutivos de `0` a `5`: primero se numeran los grupos visibles en el orden fijo de zonas `main`, `side`, `full`, respetando el orden visible dentro de cada zona; después se agregan los widgets ocultos en su orden previo estable. El grupo Captura rápida ocupa una sola ubicación y serializa sus dos IDs juntos, manteniendo su orden relativo y visibilidades independientes. Nunca se persiste ni se altera la zona.

## Archivos

- `frontend/assets/js/home.js`
- `frontend/assets/css/app.css`
- `frontend/assets/js/settings.js`
- `docs/factory/work/WORK_QUEUE.md`

No se modificaron backend, modelo, esquema, migraciones, endpoints ni dependencias.

## Verificación

- `backend\.venv\Scripts\python.exe -m pytest`: **141 passed**, un warning de deprecación de Starlette.
- Desde `backend\`: `.venv\Scripts\python.exe -m ruff check app tests`: **All checks passed**.
- `node --check` para `home.js` y `settings.js`: correcto.
- `git diff --check`: correcto.
- QA interactiva en el servidor aislado `127.0.0.1:8001`: reordenamiento, rechazo entre zonas, controles de teclado y foco, guardar/cancelar, persistencia tras recargar, error 503/reintento y combinaciones de visibilidad de Captura rápida.
- En 1440×900, 768×1024 y 390×844, en tema claro y oscuro, no hubo overflow horizontal. Los controles de mover/asa miden 46×46 CSS px; `touch-action: none` se limita al asa y `prefers-reduced-motion` se respeta.
- Con todas las secciones ocultas, el panel permite reactivarlas y no presenta un segundo botón que reinicie el borrador.
- Settings se comprobó sin controles numéricos ni editor duplicado.

## Pendiente y límites de QA

- QA visual y funcional propia completada; revisión independiente y aceptación del PO pendientes. Mantener el estado REVIEW.
- No se hizo prueba táctil física; se verificaron los targets y las reglas Pointer Events/touch-action en navegador.
- La prueba de navegador usó datos aislados; no se usó ni modificó la base personal.
