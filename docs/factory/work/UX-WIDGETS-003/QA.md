# UX-WIDGETS-003 — QA independiente del grid de Home

**Fecha:** 2026-11-22 · **Rama:** `product/lifeos-evolution` · **Base revisada:** `18e1d3c` + `04c7dcd`
**Alcance:** verificación objetiva de los criterios 1–10 de `UX-WIDGETS-003/SPEC.md` sobre la entrega publicada, con datos sintéticos y base de datos temporal.

> Nota de rol: esta verificación la realizó el mismo agente que implementations de UX-HOME-002/UX-WIDGETS-002/UX-MODULES-002 (Mimo). **No es una revisión independiente** en el sentido de UX-REVIEW-002, que sigue reservada a otro reviewer. Es QA adicional con evidencia reproducible.

## Entorno

- Servidor QA propio: `127.0.0.1:8016` con `LIFEOS_DATA_DIR=C:\Users\uriel\AppData\Local\Temp\opencode\lifeos_grid_qa` (aislada; nunca la base personal).
- Navegador: Edge headless por CDP (sin dependencias), perfiles temporales.
- Datos sintéticos: 2 proyectos (uno sin tareas), 8 tareas (vencidas, de hoy, próximas, sin fecha, completadas), 3 hábitos (uno cumplido, uno con cantidad, uno sin registro), 1 nota.
- Migración: la BD temporal se creó con `alembic upgrade head` (0006) y la migración se verificó por separado desde 0005.

## Resultado por criterio

| Criterio | Resultado | Evidencia |
|---|---|---|
| 1. Arrastre para cambiar orden | **Corregido en esta revisión** | Ver defecto D-01. Antes la tarjeta caía al final o se perdía la soltar; ahora cae junto a la tarjeta señalada. |
| 2. Redimensionar sin recortar | OK | `column_span` 2–6 y `row_span` 1–3; el contenido amplía la fila, no se recorta. |
| 3. Guardar/Cancelar y persistencia | OK | Guardar persiste; Cancelar revierte y no escribe; verificado tras recargar y tras reiniciar el navegador (orden y spans idénticos a la API). |
| 4. Las asas no capturan controles internos | OK | Arrastrar desde un enlace dentro de una tarjeta no mueve la tarjeta ni completa la tarea; `touch-action: none` solo en las asas (`auto` en las tarjetas). |
| 5. Captura rápida como unidad | OK | Ocultar la nota conserva la tarjeta con solo el formulario de tarea; con ambas ocultas desaparece la tarjeta. Visibilidad independiente verificada en la API. |
| 6. Alternativas de teclado | OK | Botones ↑/↓ mueven y anuncian la posición; el asa de redimensión responde a flechas, anuncia el tamaño y conserva el foco. |
| 7. Responsive y temas | OK | 6 columnas (1440×900), 4 (768×1024), 1 (390×844); sin overflow horizontal en claro ni oscuro. |
| 8. Migración preserva preferencias | OK | Desde 0005 con 6 preferencias: visibilidad intacta, orden intercalado main↔side con `full` al final, captura comparte posición; downgrade restaura el orden por zonas. |
| 9. API y exportación con spans | OK | GET devuelve spans; PUT persiste; fuera de rango, no entero, duplicado o desconocido → **422 sin escrituras parciales**; export `format_version` 2 y backup SQLite incluyen los spans. |
| 10. Sin regresiones | OK | Tareas, proyectos, hábitos, semana, captura y completar tarea siguen operativos; el POST de completar devolvió 200. |

## Defecto D-01 (ALTA) — el arrastre soltaba la sección en otro sitio

**Síntoma.** Al arrastrar una tarjeta hasta la franja superior de otra, la sección no quedaba donde se señalaba: caía **al final** de la cuadrícula o el movimiento se perdía ("La sección conserva su posición"). Casos reproducidos (orden inicial `active_projects, upcoming_tasks, quick_add, habits_today, habits_week`):

- `active_projects` → borde superior de `habits_week`: terminó en la posición 5 de 5 (al final) en lugar de justo antes.
- `active_projects` → centro de `quick_add`: terminó en la posición 5 de 5 (al final) en lugar de junto a Captura rápida.
- `habits_today` → borde superior de `active_projects`: terminó en la posición 5 de 5 en lugar de en la posición 1 o 2.

**Causa raíz.** `updateDragTarget()` resolvía el destino con `document.elementFromPoint(...).closest(".home-widget-card")`. El placeholder es un elemento más del grid con el mismo tamaño de la tarjeta arrastrada: al insertarse desplaza el resto de tarjetas y queda bajo el puntero, de modo que el elemento impactado era el placeholder (sin tarjeta ancestro) y el código caía en la rama que movía el placeholder al final de la cuadrícula. Además, las medidas en vivo cambiaban con cada desplazamiento, así que el puntero quedaba desfasado respecto a lo que se veía.

**Corrección aplicada** (`frontend/assets/js/home.js`):

1. Al iniciar el arrastre se captura la geometría de las tarjetas en coordenadas de documento, antes de insertar el placeholder.
2. El destino se resuelve con esa geometría estable, no con el elemento que hay bajo el puntero.
3. Si el puntero está en una zona sin tarjeta pero dentro de la cuadrícula, se conserva la previsualización ya mostrada en lugar de mandar la sección al final.

**Verificación tras la corrección** (misma matriz, `drag_fixed3.txt`): 6 de 8 escenarios cambian el orden y lo hacen **junto a la tarjeta señalada** (antes/según la mitad de la tarjeta apuntada); los 2 restantes no cambian porque la posición señalada ya era la actual. Se mantiene la previsualización (placeholder + destino marcado + anuncio "Suelta la sección para cambiar su posición").

## Ajuste A-01 (accesibilidad) — `aria-live` en la línea de contexto

`#home-context` conservaba `aria-live="polite"` y, tras UX-HOME-002, aloja además el botón **Reintentar** cuando falla la carga de tareas. Un control interactivo dentro de una región viva produce anuncios duplicados (el bloque ya declara `role="alert"`). Se retira el `aria-live` de `#home-context` (se conserva el `id`), aplicando la decisión pendiente de UX-01 §6 y el criterio de UX-01 §190 (`aria-live` solo para resultados de acciones).

## Desviación pendiente de decisión del PO (no corregida)

`UX-WIDGETS-003/SPEC.md` fija el layout inicial en **4×2 tareas, 2×1 captura, 4×2 proyectos, 2×2 hábitos de hoy y 6×2 semana**. La implementación usa **`row_span` 1 en los seis widgets** (migración `0006`, catálogo del backend y fallback del frontend son coherentes entre sí). El HANDOFF lo documenta como decisión técnica ("filas de una unidad para evitar altura vacía"), pero **contradice el boceto normativo del SPEC**. Se conserva tal cual: es una decisión de producto y corresponde al PO confirmarla o actualizar el SPEC.

## Límites de esta verificación

- No se probó en un dispositivo táctil físico; el arrastre se ejercitó con puntero de ratón vía CDP.
- Los errores de consola observados provienen de una extensión de Edge (`chrome-extension://…/editor/content.js`), no de la aplicación.
- Las capturas de pantalla quedan en `C:\Users\uriel\AppData\Local\Temp\opencode\uxwidgets003_shots`.
- UX-REVIEW-002 (revisión independiente por otro reviewer) sigue pendiente; esta entrega permanece en **REVIEW**, no DONE.

## Reproducción

```powershell
# Backend temporal
$env:LIFEOS_DATA_DIR="C:\Users\uriel\AppData\Local\Temp\opencode\lifeos_grid_qa"
cd backend; .\.venv\Scripts\alembic.exe upgrade head
$env:LIFEOS_ALLOWED_HOSTS="127.0.0.1:8016,localhost:8016"
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8016

# QA de navegador (CDP)
node C:\Users\uriel\AppData\Local\Temp\opencode\uxwidgets003_qa.mjs
node C:\Users\uriel\AppData\Local\Temp\opencode\probe_drag5.mjs

# Verificación de datos y migración
.\backend\.venv\Scripts\python.exe C:\Users\uriel\AppData\Local\Temp\opencode\mig6_check.py
.\backend\.venv\Scripts\python.exe C:\Users\uriel\AppData\Local\Temp\opencode\api_spans_check.py
```
