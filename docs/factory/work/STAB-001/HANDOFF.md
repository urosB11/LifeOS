# Handoff: STAB-001 — QA manual Fase 8

**Fecha:** 2026-11-20
**De:** Developer (ejecución de QA propia)
**Para:** Reviewer — Mimo / Product Owner
**Entrega:** Validación manual de Fase 8 (PRJ-001, PRJ-002, HAB-001)

## Qué se hizo

Ejecución de QA manual de STAB-001 contra la rama `main` (commit 27791fc, que incluye Fase 8 base, PRJ-001, PRJ-002 y HAB-001). Se levantó el servidor Uvicorn en `127.0.0.1:8001` con `LIFEOS_DATA_DIR` temporal y base de datos inicializada mediante Alembic `upgrade head`.

## Qué se verificó

| Flujo | Resultado |
|---|---|
| Health check | ✅ `{"status":"ok","database":"sqlite"}` |
| Crear proyecto (PRJ-001) | ✅ 201, métricas expuestas: task_count=0, completed_count=0, overdue_count=0, next_due_date=null |
| Crear tarea desde proyecto (PRJ-002) | ✅ 201, project_id asociado correctamente, métricas actualizadas (task_count=1) |
| Completar/reabrir proyecto | ✅ Transiciones de estado funcionan, métricas se mantienen |
| Error de API (nombre vacío) | ✅ 422 con detalle de validación |
| Proyecto inexistente | ✅ 404 |
| Proyecto sin tareas | ✅ task_count=0, next_due_date=null (frontend muestra "Sin tareas") |
| Calendario de hábitos (HAB-001) | ✅ Hábito creado, calendario devuelve 30 días para noviembre 2026 |
| Frontend servido | ✅ index (200), projects.js (200, 26708 bytes), habits.js (200, 36720 bytes), app.js (200, 7668 bytes) |
| Tasks endpoint | ✅ 200, lista de tareas |
| Notes endpoint | ✅ 200, 0 notas |
| Settings endpoints | ✅ preferences/theme/timezone disponibles |
| Pruebas automatizadas | ✅ 139/139 pytest, ruff OK, node --check OK |

## Qué queda pendiente

- Revisión visual en navegador real en los tres viewports definidos en el SPEC: Desktop (1440×900), Tablet (768×1024), Móvil (390×844)
- Revisión independiente por Reviewer (Mimo) — si no está disponible, declarar QA propia
- Verificación de flujos de UI que requieren interacción de navegador (abrir/cerrar modales, foco de teclado, navegación móvil, overflow horizontal)

## Comandos ejecutados

```
git fetch origin
git checkout -b product/lifeos-evolution origin/product/lifeos-evolution
# Servidor temporal:
uvicorn app.main:app --host 127.0.0.1 --port 8001 (con LIFEOS_DATA_DIR temporal, LIFEOS_ALLOWED_HOSTS)
alembic upgrade head
# Pruebas:
.venv\Scripts\pytest -q          → 139 passed
.venv\Scripts\ruff check app tests → All checks passed
node --check frontend/assets/js/projects.js habits.js app.js → JS OK
# Smoke test con Python urllib contra http://127.0.0.1:8001/api/v1
```

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| docs/factory/work/WORK_QUEUE.md | STAB-001 cambiado de READY a REVIEW, notas actualizadas |
| docs/factory/work/STAB-001/HANDOFF.md | Nuevo — este documento de handoff |

## Decisiones tomadas

- STAB-001 es "solo revisión, no código" per SPEC.md: no se implementaron cambios de código.
- Se ejecutó QA propia del Developer ya que el Reviewer (Mimo) no está disponible en este momento. Esto debe declararse al entregar.
- Todas las verificaciones se hicieron contra una base de datos temporal (LIFEOS_DATA_DIR), nunca contra la base personal.

## Contexto para la siguiente tarea

- La siguiente tarea en la cola es BUG-001 (conservar formulario ante error), que depende de STAB-001 y BUG-001 (auto-dependencia para reproducir).
- HOME-001 depende de STAB-001 y BUG-001.
- La rama de trabajo es `product/lifeos-evolution`. No hacer push ni merge a main.

## Estado de la cola de trabajo

- STAB-001: REVIEW (pendiente de aceptación por PO)
- BUG-001: READY (siguiente en la cola)
- HOME-001: READY (bloqueada por STAB-001 y BUG-001)

---

# Revisión independiente — Reviewer (Mimo)

**Fecha:** 2026-11-21 · **Veredicto: REJECT** (la validación de Fase 8 no pasa; ver hallazgos)

## Qué se hizo

Revisión independiente sobre la QA del Developer. Navegador real: Edge headless vía Chrome DevTools Protocol (sin dependencias nuevas), servidor Uvicorn en `127.0.0.1:8001` con `LIFEOS_DATA_DIR` temporal (nunca la base personal) y `alembic upgrade head`. Datos semilla: 2 proyectos (uno con tareas, uno vacío), 1 hábito, 1 nota. Matriz completa: 8 pantallas × 3 viewports (1440×900, 768×1024, 390×844) = 24 capturas, más flujos de interacción (formulario, errores, modal, foco, teclado, calendario, navegación móvil, estados vacíos/404).

## Hallazgos por severidad

### ALTA

1. **[NUEVA — no está en la cola] Overflow horizontal en móvil (390×844) en 5 pantallas:** `#/projects` (scrollWidth 711 vs 390), `#/projects/:id` (509), `#/tasks` (703), `#/habits` (551), `#/notes` (541). Desktop y tablet sin overflow. Causa raíz identificada empíricamente: `.main { margin: 0 auto }` (app.css:170) es hijo de `.app-content` (`display:flex; flex-direction:column`); los márgenes `auto` en el eje cruzado desactivan el stretch, por lo que `main` se dimensiona por su contenido (≈711px, el ancho mínimo de la tabla de proyectos) en vez del ancho del contenedor (390px). Al no estar `main` constreñido, `.table-wrap` (`overflow-x:auto`) recibe un ancho igual al de la tabla y su scroll interno no se activa. Verificado en vivo: con `margin:0` → 390px; `align-self:stretch` solo no basta (los `auto` tienen prioridad). **Recomendación:** crear tarea de cola para corregirlo (no incluido en BUG-001 ni PRJ-UI-001).
2. **[CONFIRMADA — ya en cola como BUG-001, P0] Campos del formulario se limpian tras error de validación.** Reproducción: detalle de proyecto → "+ Nueva tarea" → descripción y prioridad cargadas → título vacío → "Crear tarea". El formulario permanece abierto y muestra el mensaje de error ("El título de la tarea no puede estar vacío."), pero `description` y `priority` quedan vacías. Coincide con el análisis de código: `createTask()` llama a `renderDetail()` que regenera el `innerHTML` sin enlazar valores al estado.

### MEDIA

3. **[CONFIRMADA — ya en cola como PRJ-UI-001, P1] Las tareas existentes desaparecen del DOM con el formulario abierto** (0 filas de tabla). La cabecera "Tareas (3)" y el resumen 1 completadas · 2 pendientes · 1 vencida sí permanecen visibles. Es exactamente el problema que PRJ-UI-001 debe corregir.
4. **[NUEVA] El foco no se restaura al cerrar el modal con ESC.** El modal se abre correctamente y el foco entra en él (`document.activeElement` dentro del modal), ESC lo cierra, pero después `activeElement` queda en `BODY` (no vuelve al botón que lo abrió).
5. **[OBSERVACIÓN] Celdas del calendario de hábitos de 28px** (medido en desktop, `.cal-day`). Consistente con el objetivo "calendario compacto" de HAB-001; el SPEC de STAB-001 no fija tamaño objetivo, por lo que no lo clasifico como defecto.

### BAJA

6. `GET /favicon.ico` → 404 en consola (solo en la primera carga de Home). No afecta funcionalidad.

## Verificaciones independientes (no me limité a leer el reporte de Nemo)

| Verificación | Resultado |
|---|---|
| `pytest -q` | ✅ 139 passed (1 warning, 161.88s) |
| `ruff check app tests` | ✅ All checks passed |
| `node --check` (7 archivos JS) | ✅ OK |
| Handoff de Nemo vs mi ejecución | ✅ Coincide en health, CRUD, 422/404, métricas, calendario, frontend servido |

## Flujos verificados OK (positivos)

- Formulario de tarea: abrir, cancelar, reabrir ✅
- Crear tarea válida: toast "Tarea creada", formulario se cierra, contadores actualizados (`Tareas (4)`, 1/4), sin duplicados ✅
- Modal de eliminación: abre, el foco entra al modal, ESC lo cierra ✅
- Teclado: Tab navega por la navegación y formularios; foco visible (`:focus-visible` con outline) ✅
- Calendario: cambio de mes (noviembre→diciembre), selector de hábito y leyenda presentes ✅
- Navegación móvil: listado → detalle → volver ✅
- Estados: proyecto vacío ("Sin tareas" + CTA) y proyecto inexistente ("Proyecto no encontrado") ✅
- Sin errores de consola funcionales (además del favicon) ✅

## Limitaciones declaradas

- QA visual ejecutada en Edge **headless** vía CDP (no hay navegador gráfico interactivo en este entorno). Es un navegador real de motor Chromium, pero la revisión "a ojo" de animaciones/paletas se hizo sobre capturas PNG estáticas.
- La primera ejecución del script de QA tuvo dos fallos propios (timeout de CDP y selector mal formado) que produjeron un falso positivo de BUG-001; fue corregida y re-ejecutada. El hallazgo 2 arriba proviene de la ejecución corregida.

## Veredicto

**REJECT** para la validación de Fase 8: 1 hallazgo ALTA nuevo no contemplado en la cola (overflow móvil) más 2 defectos ALTA/P0 ya confirmados (BUG-001, PRJ-UI-001). La funcionalidad de fondo (API, métricas, flujos) está sólida; el rechazo se debe a los defectos de UI. STAB-001 queda en REVIEW hasta aceptación del PO. **Se recomienda al PO:** agregar tarea para el overflow móvil y decidir si BUG-001/PRJ-UI-001 se liberan para ejecución.
