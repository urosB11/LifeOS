# Handoff: UX-HOME-002 — Claridad de Home y captura contextual

- **Fecha:** 2026-11-22
- **Developer:** Mimo
- **Estado:** REVIEW
- **Spec:** `docs/factory/work/UX-HOME-002/SPEC.md`

## Entrega

- Atención y Hoy ahora son colecciones disjuntas por ID. Atención conserva su
  prioridad de vencidas y de hoy; Hoy mantiene su orden de relevancia. Los
  límites siguen siendo 5 y 8, y los contadores “más” corresponden a cada
  colección.
- Una consulta fallida de tareas muestra un mensaje y reintento; una consulta
  correcta sin resultados muestra el estado vacío. Los demás bloques se
  mantienen visibles ante un fallo aislado.
- Los proyectos con `task_count=0` muestran “Sin tareas”, sin progreso 0/0.
- Captura rápida muestra un editor a la vez. El selector solo aparece si ambos
  widgets están visibles; cambiar de modo conserva borradores independientes.
  La captura de notas admite contenido y conserva los campos ante errores.
- Se evita acumular listeners al volver a renderizar Home, lo que podía enviar
  varias solicitudes de creación desde una sola acción.
- Se corrigió `get_timezone()`: el repositorio devuelve el modelo de
  preferencia, cuyo valor debe leerse explícitamente. Home calcula su fecha con
  la zona configurada vía `Intl`; el reloj backend y el calendario semanal
  también respetan esa preferencia.

## Verificación

- `.\.venv\Scripts\python.exe -m pytest -q` (desde `backend`): **141 passed**,
  1 warning deprecado de Starlette.
- `.\.venv\Scripts\ruff.exe check app tests` (desde `backend`): OK.
- `node --check` para todos los JS de `frontend/assets/js`: OK.
- `git diff --check`: OK.
- Smoke en servidor aislado: `/` y `/api/v1/health` respondieron HTTP 200.
- QA interactiva con datos sintéticos: tareas vencidas, de hoy, futuras, alta
  prioridad, sin fecha y completadas; límites 5/8 y contadores 9/8; sin
  intersección Atención/Hoy; error frente a lista vacía y reintento; proyecto
  sin tareas; modos y visibilidad independiente de widgets; borradores al
  cambiar de modo; error y creación de nota con contenido; envío doble y
  render repetido producen una sola creación.
- Zona horaria probada con `Pacific/Kiritimati` (fecha local 2026-11-23),
  `Etc/GMT+12` (2026-11-22) y valor inválido (fallback a Córdoba).
- Home en 1440×900, 768×1024 y 390×844, tema oscuro y claro: sin overflow
  horizontal. Capturas revisadas en móvil en ambos temas.

## Aislamiento y límites

- Smoke y datos manuales usaron
  `%LOCALAPPDATA%\\Temp\\lifeos_responsive002`; no se usó la base personal.
- Se eliminaron solo los fixtures sintéticos creados para esta QA y se
  restauraron las preferencias de zona horaria y widgets.
- No se añadieron endpoints, dependencias, tablas ni migraciones.
- QA propia; revisión independiente y aceptación del PO pendientes. Estado
  `REVIEW`, no `DONE`.

## Comandos

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app tests
```

Desde la raíz:

```powershell
Get-ChildItem frontend\assets\js\*.js | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
git diff --check
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8001/
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8001/api/v1/health
```

## Archivos

- `frontend/assets/js/home.js`
- `frontend/assets/css/app.css`
- `backend/app/core/clock.py`
- `backend/tests/test_settings.py`
- `docs/factory/work/WORK_QUEUE.md`
- `docs/factory/work/UX-HOME-002/HANDOFF.md`
