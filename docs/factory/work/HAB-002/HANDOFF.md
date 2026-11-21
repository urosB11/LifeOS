# Handoff: HAB-002 — Semana interactiva y calendarios por hábito

**Fecha:** 2026-11-21
**De:** Developer — Mimo (asignación explícita del PO)
**Para:** Reviewer — Nemo / Product Owner
**Entrega:** SPEC `docs/factory/work/HAB-002/SPEC.md`
**Estado:** REVIEW

## Qué se hizo

Home y Habit Tracker ahora permiten registrar y corregir hábitos con la misma
semántica visual, sin selector de un único hábito y sin scroll horizontal en la
matriz semanal.

- **Backend (aditivo, sin migración):** `GET /api/v1/habits/week` y
  `GET /api/v1/habits/{id}/calendar?month=YYYY-MM` ahora incluyen
  `entry_value` (float o null) junto a `entry_status`. Permite editar la
  cantidad desde la UI reutilizando los endpoints existentes de `entries`
  (POST/PATCH/DELETE), tal como habilita el SPEC §3. No se agregan rutas,
  estados persistidos ni columnas.
- **Módulo compartido nuevo** `frontend/assets/js/habit-entry.js`:
  - `deriveHabitDayState(day, today)` deriva los 7 estados de la tabla del SPEC
    (cumplido, parcial, pendiente de registrar, no cumplido, omitido, en espera,
    no programado) a partir de programación, fecha local y registro.
  - `habitLegendHtml(kind)` genera la leyenda desde la misma lista de estados
    que pintan las celdas (Home y Habit Tracker coinciden por construcción).
  - `openHabitEntryEditor(...)` modal compacto y accesible por teclado para
    marcar cumplido / omitido / quitar registro (binario) o corregir la cantidad
    (cuantificable). El backend deriva el estado según la meta; la UI no
    inventa estados.
- **Home (`home.js`):** el widget "Semana de hábitos" pasa de tabla con scroll
  horizontal a matriz CSS Grid (nombre + 7 columnas alineadas). Clic en una
  celda programada de hoy o anterior abre el editor; las futuras son grises y
  no interactivas; las no programadas quedan realmente vacías (sin casillero,
  borde, fondo, símbolo ni color). Tras guardar se refrescan la semana, el
  widget "Hábitos de hoy" y la tarjeta "Hábitos hoy" del resumen, sin recargar
  la aplicación.
- **Habit Tracker (`habits.js`):** se elimina `#cal-habit`. Se muestra un
  calendario por cada hábito no archivado (activos y pausados, con su color y
  badge "Pausado") en una grilla responsive de varias columnas, todos
  sincronizados en un único mes con un solo control anterior/siguiente y una
  sola leyenda. Las celdas pasadas también son editables.
- **CSS (`app.css`):** clases de estado compartidas `.hstate--*` (una sola
  definición para ambas vistas), matriz `.wk-matrix`/`.wk-row`/`.wk-cell`,
  grilla `.cal-grid`/`.cal-card`, y tope `max-width` de la tarjeta de
  calendarios para que la vista no contribuya al overflow de página.

## Qué se verificó

Pruebas automatizadas (backend, base temporal):

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa | `.venv\Scripts\pytest -q` (desde `backend/`) | ✅ **140 passed** (139 previos + 1 nuevo `test_week_and_calendar_expose_entry_value`) |
| Lint | `.venv\Scripts\ruff check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check` sobre `habit-entry.js`, `home.js`, `habits.js`, `app.js` | ✅ OK (sin salida) |
| Migraciones | `alembic upgrade head` | ✅ `0005_habits (head)`; **sin migraciones nuevas** en este cambio |

Cobertura del test nuevo (`backend/tests/test_habits.py`):
`entry_value` en semana y calendario; registro histórico por debajo de la meta
→ `pending`; corrección con PATCH (supera la meta → `completed`) reflejada en el
calendario; DELETE → `entry_status`/`entry_value` en `None`; hábito binario con
`entry_value` en `None`; y aserción de que los `status` persistidos siguen
limitados a `{pending, completed, skipped}` (sin `missed`/`future`).

QA visual e interactiva (Edge headless vía CDP, sin dependencias nuevas),
servidor Uvicorn en `127.0.0.1:8000` con `LIFEOS_DATA_DIR` temporal y base
creada con Alembic:

| Criterio de aceptación | Resultado |
|---|---|
| CA1 — 7 días sin scroll horizontal (1440/768/390) | ✅ `.wk-matrix` y `#widget-content-habits_week`: `scrollWidth == clientWidth` (300/300 escritorio y tableta, 298/298 móvil) |
| CA2 — usable con teclado y etiquetas por fecha y hábito | ✅ `role="grid"` + `rowheader`/`columnheader`/`gridcell`; etiquetas `"Beber agua, lunes, 16 de noviembre de 2026: No cumplido. Editar registro"`; Enter abre el editor, ESC lo cierra y **el foco vuelve a la celda**; el foco entra al modal al abrirlo |
| CA3 — 7 estados distinguibles, "no programado" vacío | ✅ Conteo en la matriz: cumplido 1, parcial 1, pendiente 1, no cumplido 10, omitido 1, en espera 2, no programado 5; las 5 celdas "no programado" verificadas con fondo transparente, borde transparente y sin texto |
| CA4 — día pasado sin registro = "No cumplido" y editable | ✅ Clic en la celda abre el editor con estado "No cumplido" |
| CA5 — crear/modificar/quitar con y sin meta | ✅ Binario: "Marcar cumplido" → celda a `hstate--done`; Cuantificable: `#he-value` precargado con 3 (meta 8 km) → guardar 9 → celda a `hstate--done` (estado derivado por backend) |
| CA6 — fecha futura sin interacción ni escritura | ✅ 0 celdas futuras interactivas en la matriz y en los calendarios (son `<span>`/`<div>`, no botones) |
| CA7 — un calendario por activo/pausado | ✅ 4 tarjetas (3 activos + "Leer" pausado con badge); el archivado no aparece; 4 calendarios = 4 tarjetas |
| CA8 — cambiar mes actualiza todos | ✅ "noviembre 2026" → "diciembre 2026" con los 4 calendarios re-renderizados (aria-label de cada uno con el nuevo mes) y vuelta al mes anterior |
| CA9 — sin overflow horizontal introducido | ✅ Sección de calendarios: `delta 0px` al ocultar (técnica de ocultamiento por hijo de `#habits-view`); grilla 324px ≤ 366px útiles en 390. Home: `scrollWidth == clientWidth` en los 3 viewports |
| CA10 — modo claro/oscuro, estados de carga/vacío/error | ✅ Capturas en tema oscuro y claro; se conservan los estados de carga, vacío y error existentes |

Hallazgos de la ronda de QA (0 ALTA):

- **OBSERVACIÓN — overflow horizontal de página en `#/habits` a 390×844**
  (`scrollWidth` 612 vs `clientWidth` 390). **Preexistente, no introducido por
  HAB-002**: el driver es `#habits-manage` (tabla de gestión, +55px al ocultarla);
  la sección de calendarios de HAB-002 aporta **0px** al ancho. La causa raíz es
  el defecto `.main{margin:0 auto}` reportado en STAB-001 (5 pantallas), que ya
  está en la cola como tarea nueva pendiente de decisión del PO. Baseline
  STAB-001 con 1 hábito: 551px; con 5 hábitos la tabla de gestión crece.
- **MEDIA — `GET /favicon.ico` → 404**: preexistente (STAB-001, hallazgo #6,
  severidad baja), fuera del alcance de HAB-002.

Correcciones aplicadas durante la QA:

1. El foco no se restauraba al cerrar el editor (con clics sintéticos
   `document.activeElement` es el `body`): el editor ahora acepta
   `returnFocusTo` explícito y cae al contenedor del widget cuando el refresco
   reemplazó la celda.
2. La grilla multi-hábito era el driver del overflow móvil: la tarjeta de
   calendarios queda acotada a `calc(100vw - 2 * var(--spacing))`.

## Comandos ejecutados

```powershell
# Pruebas backend (desde backend/)
$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\pytest.exe -q          → 140 passed
.venv\Scripts\ruff.exe check app tests                              → All checks passed

# Sintaxis frontend (desde la raíz del repo)
node --check frontend/assets/js/habit-entry.js frontend/assets/js/home.js `
                frontend/assets/js/habits.js frontend/assets/js/app.js   → OK

# Servidor QA (base temporal, nunca la personal)
$env:LIFEOS_DATA_DIR="C:\Users\uriel\AppData\Local\Temp\opencode\lifeos_hab002_mimo"
.venv\Scripts\python.exe -m alembic upgrade head                   → 0005_habits (head)
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
# (Host header: el middleware exige LIFEOS_ALLOWED_HOSTS; el puerto 8000 ya está permitido por defecto)

# Smoke + seed y QA visual (scripts temporales, fuera del repo)
python C:\Users\uriel\AppData\Local\Temp\opencode\hab002_seed.py     → SEED_OK
node   C:\Users\uriel\AppData\Local\Temp\opencode\hab002_qa.mjs      → {"OBSERVACION":1,"MEDIA":1}
node   C:\Users\uriel\AppData\Local\Temp\opencode\hab002_shots2.mjs  → 6 capturas dirigidas
```

Capturas y reporte: `C:\Users\uriel\AppData\Local\Temp\opencode\hab002_shots\`
(`report_hab002.json` + 12 capturas: 3 viewports × Home/Hábitos, editor abierto,
y capturas dirigidas de la matriz y los calendarios en claro y oscuro).

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `backend/app/modules/habits/schemas.py` | `WeekDay.entry_value` opcional (aditivo) |
| `backend/app/modules/habits/service.py` | `week()` y `calendar()` devuelven `entry_value` |
| `backend/tests/test_habits.py` | Nuevo `test_week_and_calendar_expose_entry_value` (valores, PATCH/DELETE histórico, binario, estados persistidos) |
| `frontend/assets/js/habit-entry.js` | **Nuevo** — estados compartidos, leyenda y editor compacto accesible |
| `frontend/assets/js/home.js` | Matriz de semana, celdas editables, refresco dirigido de semana/hoy/resumen, foco, `escapeHtml` con comillas |
| `frontend/assets/js/habits.js` | Calendarios por hábito con mes compartido, eliminación de `#cal-habit`, edición desde el calendario, foco |
| `frontend/assets/css/app.css` | Estados `.hstate--*` compartidos, matriz de semana, grilla de calendarios, ajustes móviles, tope de ancho |
| `docs/factory/work/WORK_QUEUE.md` | HAB-002 → REVIEW |
| `docs/factory/work/HAB-002/HANDOFF.md` | Nuevo — este documento |

## Decisiones tomadas

- **Sin migración y sin estados persistidos nuevos.** "No cumplido" y "en
  espera" son estados derivados en la UI; los `status` persistidos siguen
  siendo `completed`, `pending`, `skipped`.
- **Un único módulo de estados** (`habit-entry.js`) para que Home y Habit
  Tracker no puedan divergir; la leyenda se genera desde esa misma lista.
- **`entry_value` como campo aditivo** en semana y calendario (SPEC §3 lo
  autoriza) en lugar de una ruta nueva o un N+1 de entradas.
- **Las celdas no programadas quedan vacías**, incluso en el calendario: se
  conserva el número del día como contenido, pero sin casillero, fondo ni
  color de estado (la semántica de estado es la del SPEC).
- **El overflow móvil residual no se corrigió aquí**: su causa raíz
  (`.main{margin:0 auto}`) afecta a 5 pantallas y fue reportado en STAB-001
  como tarea nueva pendiente de decisión del PO; tocarlo en HAB-002 superaría
  el alcance autorizado. Se contuvo el ancho de la sección nueva para no
  agravarlo.
- La revisión visual se hizo con Edge headless vía CDP (Node, sin dependencias
  nuevas), como en STAB-001.

## Limitaciones y riesgos

- QA propia del Developer: las capturas son estáticas y no sustituyen una
  revisión manual en navegador real ni con lector de pantalla.
- El favicon 404 y el overflow móvil preexistente quedan pendientes (fuera de
  alcance, ya reportados).
- El resaltado de "hoy" en el calendario se aplica también sobre celdas no
  programadas (solo contorno, sin color de estado); el `aria-label` de cada
  celda indica el estado real ("No programado").

## Contexto para la siguiente tarea

- La rama de trabajo es `product/lifeos-evolution`. El commit de este trabajo
  se publica en `origin/product/lifeos-evolution`; no hacer merge ni push a
  `main` (requiere autorización del PO).
- Siguiente tarea en la cola: **PRJ-UI-001** (mantener las tareas visibles al
  abrir el formulario), con coordinación con BUG-001 (Nemo). PRJ-WORKSPACE-001
  permanece en PLANNING (solo diseño).
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
