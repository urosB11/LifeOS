# UX-WIDGETS-003 — Handoff

**Estado:** REVIEW — QA propia; pendiente de revisión independiente y aceptación del PO.
**Rama:** `product/lifeos-evolution`
**Base:** `a3b5a083ea35fe59665a3b38bc25b19f3f096e99`
**Alcance:** personalización de los seis widgets de Home. Projects y Notes no se modificaron.

## Entrega

- Se reemplazaron las zonas fijas de Home por un grid de seis columnas en escritorio, cuatro en tablet y una en móvil. El orden global y spans lógicos de columnas/filas se editan en Personalizar y persisten en la API existente.
- El arrastre usa un asa explícita; el redimensionamiento ofrece asa pointer y alternativa de teclado. Los cambios permanecen como borrador hasta Guardar; Cancelar descarta ambos tipos de cambio.
- Captura rápida conserva su tarjeta compartida con visibilidad separada de Tarea y Nota. El backend sincroniza orden y spans aunque una actualización antigua o parcial incluya solo una de las preferencias del grupo.
- La migración aditiva `0006_home_widget_grid` asigna spans iniciales, conserva visibilidad y orden por zonas y define un orden de downgrade estable para Tarea antes de Nota.
- La exportación JSON se actualizó para incluir el nuevo esquema. No se añadieron dependencias ni endpoints.

## Decisiones técnicas

- `position`, `column_span` y `row_span` guardan unidades lógicas, no coordenadas en píxeles. CSS Grid auto-coloca las tarjetas y el contenido puede ampliar filas naturalmente.
- Los spans permitidos son 2–6 columnas y 1–3 filas. En tablet el span visible se limita a cuatro columnas; en móvil cada tarjeta ocupa la columna disponible sin modificar el valor persistido.
- Las preferencias se guardan mediante `PUT /api/v1/dashboard/widgets`; `config_json` y `localStorage` no se usan para el layout.
- El catálogo inicial usa filas de una unidad para evitar altura vacía en tarjetas cortas; cada widget puede redimensionarse hasta tres filas.

## Archivos

- `frontend/assets/js/home.js`
- `frontend/assets/css/app.css`
- `backend/app/api/v1/dashboard.py`
- `backend/app/modules/dashboard/models.py`
- `backend/app/modules/dashboard/repository.py`
- `backend/app/modules/dashboard/schemas.py`
- `backend/app/modules/dashboard/service.py`
- `backend/app/modules/data_service.py`
- `backend/migrations/versions/0006_home_widget_grid.py`
- `backend/tests/test_dashboard.py`
- `backend/tests/test_export.py`
- `backend/verify_migrations.py`
- `ARCHITECTURE.md`, `DATABASE.md`, `REQUIREMENTS.md`, `ROADMAP.md`
- `docs/product/UX_DIRECTION.md`, `docs/product/UX_INTERACTION_MODEL.md`
- `docs/factory/decisions/ADR-003-home-widget-grid-layout.md`, `docs/factory/decisions/log.md`
- `docs/factory/work/WORK_QUEUE.md`, `docs/factory/work/UX-WIDGETS-003/SPEC.md`

## Validación

- Backend: `pytest -q`: 144 pasaron con una advertencia deprecada de Starlette; Dashboard/exportación focalizados: 8 pasaron.
- Aislamiento: pytest usa `LIFEOS_DATA_DIR` temporal (configurado en `backend/tests/conftest.py`); la verificación de migraciones usó `C:\Users\uriel\AppData\Local\Temp\lifeos_mig_a2z4qwe1`; el navegador usó `C:\Users\uriel\AppData\Local\Temp\lifeos_widgets_003_6df249ab651f4fd8b99fce4469af6d41\lifeos.db`. Ninguna prueba escribió en la base personal.
- Migraciones: `backend/verify_migrations.py`; upgrade desde 0005, preservación de preferencias, downgrade a 0005 y re-upgrade; integridad y FK verificadas.
- Ruff en los archivos backend afectados: sin errores. El chequeo de todo `backend` mantiene hallazgos previos en archivos no modificados.
- `node --check frontend/assets/js/home.js` y `node --check frontend/assets/js/app.js`: correctos.
- `git diff --check`: correcto.
- QA de navegador en base temporal aislada y servidor local `127.0.0.1:8002`: drag y resize con mouse y con touch emulado mediante Chrome DevTools; resize con teclado; Guardar, recarga y persistencia; Cancelar; control interno de Captura rápida durante Personalizar. Las preferencias de QA se restauraron a defaults.
- En los viewports configurados 1440×900, 768×1024 y 390×844: 6/4/1 columnas, sin overflow horizontal, en temas claro y oscuro. Las asas de mover/redimensionar miden 46×46 CSS px en móvil.

## Límites y pendientes

- No se probó en un dispositivo táctil físico. La revisión independiente debe completar esa verificación.
- QA propia no equivale a aprobación. Mantener el estado REVIEW hasta revisión independiente y aceptación del PO.
