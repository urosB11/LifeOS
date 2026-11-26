# Handoff: RESPONSIVE-002 — Corregir overflow horizontal móvil

- **Fecha:** 2026-11-22
- **De:** Developer — Mimo
- **Para:** Reviewer independiente / Product Owner
- **Estado:** REVIEW

## Qué se hizo

- Se limitó el ancho de `.main` al contenedor flex con `width: 100%` y `min-width: 0`, manteniendo el ancho máximo y centrado existentes.
- Se limitó el ancho intrínseco de los `select` dentro de `.filters-bar`; una opción larga del filtro de proyecto hacía desbordar Tareas aun después de corregir `.main`.
- Se actualizó el comentario del calendario para reflejar que el límite general del contenido ahora vive en `.main`.
- No se añadió `overflow-x: hidden`, no se recortó contenido, no se cambió `--text-muted` ni se alteraron datos/API.

## Qué se verificó

- Reproducción del defecto con los límites de ancho de `.main` desactivados temporalmente en el navegador: a 390 px, `scrollWidth` llegó a 725 px en Projects, 621 px en Habits y 586 px en Notes; a 768 px llegó a 973 px en Projects, 868 px en Habits y 834 px en Notes.
- Después del cambio, siete rutas (`Home`, `Projects`, detalle de proyecto, `Tasks`, `Habits`, `Notes`, `Settings`) en 1440×900, 768×1024 y 390×844, en temas oscuro y claro: `documentElement.scrollWidth <= clientWidth` en las 42 combinaciones.
- Se usaron datos sintéticos en una base aislada bajo `%LOCALAPPDATA%\\Temp\\lifeos_responsive002`. Las tablas que exceden el ancho disponible mantienen scroll horizontal local en `.table-wrap`; la página no se desplaza horizontalmente.
- Navegación de las siete rutas a 390 px sin errores de consola ni errores de página.
- `pytest`: 140 passed, 1 warning deprecado en Starlette.
- Ruff: OK.
- `node --check` para los JS de `frontend/assets/js`: OK.
- Smoke test temporal: Home y `/api/v1/health` responden HTTP 200.
- `git diff --check`: OK.

## Qué queda pendiente

- Revisión independiente y aceptación del PO.
- UX-HOME-002 queda como siguiente entrega READY, dependiente de esta verificación.
- Los cambios locales previos de UX-01 en `home.js`/`app.css`, `contexto_lifeos.txt` y `docs/factory/work/UX-01/`, `UX-02/`, `UX-03/` se preservaron y no forman parte de esta entrega.

## Comandos ejecutados

Desde `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app tests
```

Desde la raíz:

```powershell
Get-ChildItem frontend\assets\js\*.js | ForEach-Object { node --check $_.FullName }
git diff --check
```

Smoke/browser:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8001/
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8001/api/v1/health
```

El servidor de QA se ligó a `127.0.0.1:8001`, con `LIFEOS_DATA_DIR` temporal y `LIFEOS_ALLOWED_HOSTS` limitado a ese host local. No se usó la base personal.

## Archivos de esta entrega

| Archivo | Cambios |
|---------|---------|
| `frontend/assets/css/app.css` | Ancho del contenedor principal; comentario del calendario |
| `frontend/assets/css/components.css` | Límite para selects largos de filtros |
| `docs/factory/work/WORK_QUEUE.md` | Estado y evidencia de QA |
| `docs/factory/work/RESPONSIVE-002/HANDOFF.md` | Este handoff |

## Decisiones tomadas

- Se corrigió el ancho en el contenedor común, no mediante excepciones por módulo.
- Las tablas conservan su scroll horizontal interno cuando las columnas no caben; solo se elimina el scroll horizontal de página.
- El filtro mantiene la etiqueta completa en su lista desplegable; el control se limita visualmente al ancho de su contenedor.

## Estado de la cola de trabajo

RESPONSIVE-002 queda en **REVIEW** hasta aceptación del PO. UX-HOME-002 sigue READY y solo debe comenzar después de verificar esta entrega. La revisión UX independiente continúa pendiente.
