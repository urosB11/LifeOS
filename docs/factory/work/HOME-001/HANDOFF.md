# Handoff: HOME-001 — Home como centro de operaciones

**Fecha:** 2026-11-21
**De:** Developer — Mimo (reasignación del PO: "trabaja vos en las tareas restantes")
**Para:** Reviewer — Mimo / Product Owner
**Entrega:** SPEC `docs/factory/work/HOME-001/SPEC.md`
**Estado:** REVIEW

## Qué se hizo

Home deja de ser una grilla de seis widgets con métricas iguales y pasa a
responder, en este orden: **qué requiere atención**, **qué conviene hacer
hoy**, **qué proyectos están en marcha**, **cómo vienen los hábitos** y
**cómo capturar una tarea o una nota**.

Sin endpoints nuevos, sin migraciones, sin dependencias: se reutilizan
`/dashboard/widgets`, `/dashboard/summary` (dejado de usar como estructura
dominante), `/tasks`, `/projects`, `/habits/today`, `/habits/week` y
`/notes`.

### Estructura nueva

| Zona | Secciones | Origen de datos |
|---|---|---|
| Columna amplia | **Atención** + **Hoy** | `GET /tasks?status=pending` |
| Columna amplia | **Proyectos en marcha** | `GET /projects?status=active` |
| Columna secundaria | **Hábitos de hoy** | `GET /habits/today` |
| Columna secundaria | **Captura rápida** (tarea y nota) | `POST /tasks`, `POST /notes` |
| Ancho completo | **Semana de hábitos** | `GET /habits/week` (HAB-002, sin cambios) |

- **Encabezado:** "Home", fecha local en español, frase contextual derivada
  de los datos ("2 tareas vencidas y 1 vence hoy.", "Nada vence hoy. 6
  tareas pendientes en total.") y la acción secundaria "Configurar widgets".
  Sin saludos ni frases motivacionales.
- **Atención:** solo tareas vencidas y las que vencen hoy, con etiqueta
  textual ("Vencida" / "Vence hoy"), prioridad y proyecto. Si no hay
  ninguna, muestra un estado tranquilo útil: "Nada requiere atención hoy: no
  hay tareas vencidas ni con vencimiento hoy."
- **Hoy:** lista de tareas pendientes relevantes con orden explícito
  (vencidas → vencen hoy → prioridad alta → próxima fecha → sin fecha al
  final). Cada fila muestra proyecto, prioridad y vencimiento, un botón para
  **completar** (`POST /tasks/{id}/complete`) y enlace a la vista Tareas.
  Criterio de relevancia: vencidas, las que vencen hoy, las que vencen en los
  próximos 7 días, las de prioridad alta y las que no tienen fecha.
- **Proyectos en marcha:** filas compactas con el nombre enlazado al
  proyecto, `completed_count/task_count`, una barra etiquetada
  **"Ejecución de tareas"** (con `role="progressbar"`, `aria-valuenow` =
  completadas y `aria-valuemax` = total), la cantidad de tareas vencidas y el
  próximo vencimiento. No se usa la palabra "salud".
- **Hábitos de hoy:** cada hábito programado con su estado guardado (Cumplido
  / Parcial / Pendiente de registrar / Omitido, con la semántica compartida
  de `habit-entry.js`) y el resumen "X de Y cumplidos".
- **Captura rápida:** formularios compactos con título obligatorio; la tarea
  admite proyecto, la nota no. Al guardar se actualizan todas las secciones.
- Se eliminaron las **seis tarjetas métricas iguales** que dominaban la
  pantalla (`.summary-card`: 0 en el DOM tras el rediseño).

### Compatibilidad con el catálogo de widgets

El catálogo (6 widgets, mismos ids, misma visibilidad por defecto) se
conserva intacto y sigue siendo el mecanismo de preferencias:

| Widget | Sección que alimenta | Rol |
|---|---|---|
| `upcoming_tasks` | Atención + Hoy | main |
| `active_projects` | Proyectos en marcha | main |
| `habits_today` | Hábitos de hoy | side |
| `quick_add_task` + `quick_add_note` | Captura rápida | side |
| `habits_week` | Semana de hábitos | full |

- **Visibilidad:** ocultar un widget oculta su sección y solo esa sección
  (verificado en la QA).
- **Orden:** el orden guardado define el orden dentro de cada columna
  (verificado: mover "Proyectos activos" arriba reordena la columna
  principal).
- El modal de configuración, el `PUT /dashboard/widgets` y los ids del DOM
  (`widget-<id>` / `widget-content-<id>`) se mantienen, incluido el contrato
  de HAB-002 (`#widget-content-habits_week`, `#widget-habits_week`).

### Corrección aislada descubierta en la QA

**Tema claro que nunca se aplicaba** (`frontend/assets/js/settings.js`):
`applyTheme()` solo alternaba la clase `theme-dark`, pero `:root` ya define
la paleta oscura, de modo que elegir "Claro" en Configuración no cambiaba
nada. Ahora se marca también `theme-light` en el body cuando el tema es
"light". Es una línea, sin cambios de contrato, y es necesaria para
cumplir el criterio "Mantener tema oscuro y claro" de HOME-001.

**Decisión documentada:** el valor "Sistema" sigue renderizando el tema
oscuro (la identidad principal del producto, según `vars.css`). No se cambió
ese comportamiento por defecto para no alterar la experiencia de los
usuarios; queda como pregunta abierta para el PO.

## Qué se verificó

Pruebas automatizadas (sin cambios de backend):

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa | `.venv\Scripts\pytest.exe -q` (desde `backend/`) | ✅ **140 passed** |
| Lint | `.venv\Scripts\ruff.exe check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check` sobre `home.js`, `settings.js`, `app.js`, `habit-entry.js`, `projects.js` | ✅ OK |

QA interactiva y visual (Edge headless vía CDP, sin dependencias nuevas)
contra Uvicorn en `127.0.0.1:8000` con `LIFEOS_DATA_DIR` temporal y base
creada con Alembic. **0 hallazgos.**

| Criterio de aceptación | Resultado |
|---|---|
| Tareas vencidas y de hoy identificables de entrada | ✅ Bloque "Atención" con 2 elementos: etiquetas "Vencida" y "Vence hoy", prioridad y proyecto visibles |
| Urgencia distinguida por fecha y prioridad | ✅ Etiqueta textual + badge de prioridad (no solo color) |
| Estado tranquilo si no hay urgentes | ✅ Tras mover todos los vencimientos: "Nada requiere atención hoy: no hay tareas vencidas ni con vencimiento hoy." (0 elementos en Atención) |
| Orden de "Hoy" con reglas explícitas | ✅ Verificado: `Auditar planilla Q3` (vencida) → `Cerrar conciliaciones` / `Revisar contratos pendientes` (hoy) → `Preparar comité del lunes` (alta) → `Ordenar archivo documental` (sin fecha). La tarea a 45 días quedó fuera y la completada no aparece |
| Proyectos con métricas reales y etiquetadas | ✅ "Migración de informes 2/3", barra rotulada "Ejecución de tareas" (`aria-valuenow=2`, `aria-valuemax=3`), "1 tarea vencida" y "Próximo vencimiento"; el proyecto sin tareas aparece con 0/0 |
| Hábitos con el estado guardado del día local | ✅ Beber agua = Cumplido, Caminar (3 de 8 km) = Parcial, Leer = Pendiente de registrar; resumen "1 de 3 cumplidos" |
| Crear tareas/notas sin duplicar registros | ✅ Triple clic en "Crear tarea" → **1 sola tarea** (6 → 7); la nota se creó una vez |
| Errores no destruyen entradas | ✅ Con el POST bloqueado por red: el título "Tarea capturada desde Home" **se conservó**, el error se mostró junto al formulario ("Error de conexión. Inténtalo de nuevo.") y el foco quedó en el campo |
| Preferencias de widgets siguen funcionando | ✅ El modal lista los 6 widgets del catálogo; ocultar "Tareas próximas" quita solo Atención/Hoy ( Proyectos/Hábitos/Semana siguen); restaurarlo las devuelve; mover "Proyectos activos" reordena la columna principal |
| Loading, empty, error y success | ✅ "Cargando…" inicial; estado vacío con acción "Configurar widgets" si no hay widgets visibles; estado tranquilo de Atención; error por bloque con botón "Reintentar"; toasts de éxito |
| Responsive y teclado | ✅ 1440×900 (2 columnas: 570px + 300px), 768×1024 y 390×844 (1 columna de 684px / 332px); sin scroll horizontal en las columnas ni en la página (`scrollWidth == clientWidth` en los 3); foco visible y formularios operables por teclado |
| Sin dependencias ni migraciones | ✅ Sin cambios de backend; `0005_habits (head)` sin migraciones nuevas |

Artefactos: `C:\Users\uriel\AppData\Local\Temp\opencode\home001_shots\`
(`report_home001.json` + capturas por viewport, tema claro/oscuro, estado
tranquilo, error de captura y modal de widgets).

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/assets/js/home.js` | Reescrito: estructura Atención/Hoy/Proyectos/Hábitos/Captura/Semana, reglas de orden y relevancia, acción de completar, captura rápida con borrador y sin doble envío, refresco dirigido de hábitos (HAB-002), modal de widgets conservado |
| `frontend/assets/css/app.css` | Nuevo bloque "Home como centro de operaciones": `.home-layout`, `.home-col`, `.home-context`, `.home-attention*`, `.home-task*`, `.home-chip*`, `.home-project*`, `.home-habit*`, `.home-capture*`, `.home-calm`, `.home-more`, `.home-error*`; grilla a una columna en ≤1023px |
| `frontend/assets/js/settings.js` | Corrección aislada: `applyTheme()` marca `theme-light` (el tema claro nunca se aplicaba) |
| `docs/factory/work/HOME-001/HANDOFF.md` | Nuevo — este documento |
| `docs/factory/work/WORK_QUEUE.md` | HOME-001 → REVIEW |

## Limitaciones y riesgos

- QA propia del Developer: las capturas son estáticas y no sustituyen una
  revisión manual en navegador real ni con lector de pantalla.
- La lista de "Hoy" se limita a 8 filas y "Proyectos en marcha" a 6, con
  enlace al listado completo; el resto se anuncia con un contador.
- El tema "Sistema" sigue resolviendo al tema oscuro (decisión
  conservative, ver arriba).
- El orden de las secciones se respeta **dentro de cada columna**: la
  asignación a columna (amplia / secundaria / ancho completo) es fija por
  rol, porque la jerarquía "Atención y Hoy primero" es el objetivo del
  rediseño. Es una interpretación del SPEC que conviene validar en review.
- Sin cambios de backend: si en el futuro el resumen necesita datos que los
  endpoints actuales no exponen, habría que documentar el límite (el SPEC
  lo prohíbe salvo demostración).

## Contexto para la siguiente tarea

- Rama `product/lifeos-evolution`; el commit se publica en
  `origin/product/lifeos-evolution` (sin merge ni push a `main`).
- Siguiente en la cola: **TASK-001** (P1, `tasks.js`) y después
  **UX-REVIEW-001** (revisión, sin código).
- Sigue pendiente de decisión del PO el **overflow horizontal móvil** de
  STAB-001 (`.main{margin:0 auto}`), que afecta a 5 pantallas; Home no
  sufre ese defecto (390px sin overflow), pero Proyectos, Hábitos, Tareas y
  Notas sí.
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
