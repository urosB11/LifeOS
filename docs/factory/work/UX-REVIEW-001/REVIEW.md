# UX-REVIEW-001 — Revisión de UX de HOME-001 y TASK-001

**Fecha:** 2026-11-21
**Revisor:** Mimo (rol Reviewer de la cola)
**Alcance:** revisión de las entregas **HOME-001** (`1511611`) y **TASK-001**
(`6218ea6`) — Home y Tareas, en tema oscuro y claro, en 1440×900, 768×1024 y
390×844.
**Tipo de tarea:** revisión (documentación). No se implementa funcionalidad
nueva.
**Estado:** REVIEW — veredicto de Mimo: **APROBADO CON CORRECCIONES
APLICADAS** (detalle abajo). Pendiente de revisión independiente (Nemo) y
aceptación del PO.

> **Transparencia sobre la independencia.** El PO reasignó la ejecución de
> HOME-001 y TASK-001 a Mimo ("trabaja vos en las tareas restantes"), por lo
> que **la persona que implementó y la que revisó es la misma**. Este informe
> es, por tanto, **QA propia y no una revisión independiente**. La revisión
> independiente por Nemo sigue pendiente en la cola. Las correcciones que se
> listan abajo se aplicaron sobre las propias entregas del revisor, lo que
> aumenta el riesgo de sesgo: por eso se dejan documentadas con mediciones
> reproducibles (script y artefactos) para que Nemo pueda contrastarlas.

## Método

Auditoría objetiva sobre la aplicación en ejecución (Uvicorn en
`127.0.0.1:8000` con `LIFEOS_DATA_DIR` temporal y base creada con Alembic),
con Edge headless vía CDP, sin dependencias nuevas:

1. **Contraste calculado** en el navegador (no estimado): se toma el color
   real del texto, se sube por el árbol hasta el primer fondo efectivo y se
   calcula la razón WCAG 2.x. Se contrasta contra el mínimo de **4.5:1**
   para texto normal y **3:1** para texto grande (≥24px, o ≥18.66px en
   negrita). Se auditaron 20 selectores en Home y 15 en Tareas, en los dos
   temas.
2. **Foco con teclado real**: 26 pulsaciones de `Tab` por vista, leyendo el
   `outline` computado en cada parada (`:focus-visible`).
3. **Trampa de foco del modal** de widgets: `Tab` real dentro del modal y
   seguimiento del `document.activeElement`.
4. **Roles y nombres accesibles**: todos los `button`, `a[href]`,
   `input`, `select` y `textarea` de cada vista; jerarquía de encabezados;
   regiones `aria-live`; `role="alert"`; `lang`; landmarks.
5. **Comportamiento** ya cubierto por las QA funcionales de HOME-001 y
   TASK-001 (estados, formularios, filtros, errores, responsive), que se
   re-ejecutaron tras las correcciones (0 hallazgos).

Artefactos: `C:\Users\uriel\AppData\Local\Temp\opencode\uxreview001\`
(`report_uxreview001.json`, `report_uxreview001b.json`).

## Resumen

| Severidad | Hallazgos | Estado |
|---|---:|---|
| ALTA | 0 | — |
| MEDIA | 4 | 3 corregidos, 1 pendiente de decisión del PO |
| BAJA | 3 | 3 corregidos |

**Veredicto:** las dos entregas cumplen los criterios de aceptación de sus
SPEC y la puerta de salida de Fase 9 en cuanto a comportamiento, jerarquía,
estados, teclado y responsive. Los defectos detectados son de **contraste y
foco del modal**, ambos con corrección local y verificable; no hay hallazgos
bloqueantes.

## Hallazgos

### MEDIA-1 — Contraste insuficiente en texto secundario (WCAG 2.1 AA 1.4.3)

**Medición (antes):** razones calculadas sobre los colores reales en el
navegador.

| Elemento | Texto | Tema oscuro | Tema claro | Mínimo |
|---|---|---:|---:|---:|
| `.chip--muted` | "Sin fecha" | **2.73** | **2.32** | 4.5 |
| `.home-more` | "3 tareas más en la lista completa" | **3.44** | **2.59** | 4.5 |
| `.home-project__label` | "Ejecución de tareas" | **3.44** | **2.59** | 4.5 |
| `.chip--warning` | "Vence hoy" | 6.61 | **3.57** | 4.5 |
| `.badge--priority-normal` | "Normal" | 6.61 | **3.57** | 4.5 |
| `.badge--status` | "Pendiente" | **4.26** | 4.74 | 4.5 |
| `.chip` | "Migración de informes" | 5.02 | **4.43** | 4.5 |

**Causa:** las clases nuevas de HOME-001/TASK-001 usaron `--text-muted`
(2.73–3.44 en oscuro, 2.32–2.59 en claro) y combinaciones de tokens de
`vars.css` que no alcanzan 4.5:1 sobre su fondo sutil (`--warning` sobre
`--warning-subtle` en claro: 3.57; `--accent` sobre `--accent-subtle` en
oscuro: 4.26).

**Impacto:** texto de 12–13px con bajo contraste; dificultad de lectura en
pantallas pequeñas y para baja visión. No es un problema de información: el
estado nunca depende solo del color ("Vencida", "Vence hoy", "Sin fecha",
"Pendiente", "Completada" son texto), por lo que el contenido se mantiene
comprensible; el defecto es de legibilidad.

**Corrección aplicada (local, sin cambiar la identidad visual):**

- `.chip--muted`, `.home-more`, `.home-project__label`: `--text-muted` →
  `--text-secondary`.
- `.chip`: fondo `--surface-hover` → `--surface-raised` (en claro, el texto
  secundario sobre `--surface-hover` quedaba en 4.43).
- `.chip--warning` y `.badge--priority-normal`: nuevo token **`--warning-text`**
  (oscuro `#D8C070`, claro `#7A6206`) para el color de texto, dejando
  `--warning` intacto para bordes y acentos. Es un token **nuevo**, no una
  alteración de los existentes.
- `.badge--status`: `--accent` → `--accent-hover` (4.26 → 5.2 en oscuro;
  en claro sube de 4.74 a 6.3). Beneficia también a las etiquetas de Notas.

**Medición (después):** **0 fallos de contraste** en los 35 selectores
auditados, en los dos temas y las dos vistas.

---

### MEDIA-2 — El modal de widgets no atrapa el foco (teclado)

**Medición:** con `Tab` real dentro del modal, el foco escapaba al shell de
la aplicación: **7 salidas del modal** ("Life OS × Home Proyectos Tareas…",
"Home", "Proyectos", "Tareas", "Notas", "Hábitos", "Configuración") tras
"Guardar preferencias". El modal de confirmación de `app.js`
(`showConfirm`, Fase 8D) sí implementa la trampa; el de widgets, no.

**Impacto:** una persona que navega con teclado o lector de pantalla pierde
el contexto del modal y creye que la aplicación ha cambiado de pantalla.

**Corrección aplicada:** `openConfig()` en `frontend/assets/js/home.js` ahora
atrapa `Tab`/`Shift+Tab` dentro del modal con el mismo patrón que
`showConfirm`. **Verificación:** 24 pulsaciones de `Tab` → **0 salidas del
modal**.

---

### MEDIA-3 — El foco no se restaura al cerrar el modal de widgets

**Medición:** tras cerrar con `ESC` o con "Cancelar", `document.activeElement`
quedaba en `<body>` (el usuario pierde el lugar en la página).

**Impacto:** al reabrir el modal o seguir tabulando, el usuario vuelve al
principio del documento en lugar de a "Configurar widgets". Es el mismo
defecto que STAB-001 había detectado para el modal de confirmación y que ya
estaba corregido allí.

**Corrección aplicada:** `close()` común en `openConfig()` que quita el
overlay, **retira el listener de teclado** y restaura el foco al elemento
que lo tenía antes de abrir. **Verificación:** `focoDespuesDeEsc` y
`focoDespuesDeCancelar` = `widgets-edit-btn` (antes: `BODY`).

---

### MEDIA-4 — El listener de `keydown` (ESC) se acumulaba al cerrar sin ESC

**Medición:** el listener de `document` solo se eliminaba cuando se pulsaba
`ESC`; al cerrar con "Cancelar" o clic fuera, quedaba registrado (una
acumulación por cada apertura). Sin errores en consola observados
(`errores: []`), pero es una fuga preventable.

**Impacto:** bajo; listeners acumulados sobre `document` en una app local de
una sola página.

**Corrección aplicada:** eliminada junto con el resto en `close()` (MEDIA-3).

---

### BAJA-1 — SVG decorativo sin `aria-hidden` / `focusable`

**Medición:** 1 SVG dentro del ámbito de las vistas revisadas (el icono del
botón "Configurar widgets" en Home); sin `aria-hidden` ni `focusable`.
Tareas: 0 SVG en el ámbito de la vista.

**Corrección aplicada:** `aria-hidden="true" focusable="false"` en el icono.

---

### BAJA-2 — Home no tiene región `aria-live` para los datos que cambian

**Medición:** Tareas tiene `aria-live="polite"` en `#tasks-summary` y
`role="alert"` en `#task-error`; Home no tenía ninguna región viva: ni la
frase contextual (`#home-context`) ni el resumen de hábitos de hoy se
anuncian al actualizarse.

**Corrección aplicada:** `aria-live="polite"` en `#home-context` y en el
resumen "X de Y cumplidos" (en los dos renderizados: inicial y refresco
dirigido de HAB-002).

---

### BAJA-3 — La marca de "completar" solo se veía al pasar el mouse

**Medición:** `.check-toggle` usaba `color: transparent`; el ✓ solo aparecía
en `:hover`. El círculo vacío no comunica la acción disponible y el
completado es una acción frecuente en Home ("Hoy") y en Tareas.

**Corrección aplicada:** el ✓ se muestra siempre en `--text-secondary` y pasa
a `--accent` al pasar el mouse; el estado completado conserva su fondo
`--success`.

---

### Pendiente de decisión del PO (no corregido)

| # | Tema | Detalle |
|---|---|---|
| P-1 | **Token `--text-muted`** | El token global (`#6B7570` oscuro / `#9AA39E` claro) no alcanza 4.5:1 sobre `--surface` ni `--surface-hover` (2.59–3.44). Las clases nuevas ya no lo usan, pero sigue presente en otras vistas (Hábitos, Proyectos, Notas, Configuración). Ajustarlo cambiaría elSecondary texto de toda la app: es una decisión de diseño global, fuera del alcance de esta revisión. Recomendación: darkest `--text-muted` a `#7E8883` (oscuro) / `#7B8580` (claro) y medir el impacto visual en las 5 pantallas. |
| P-2 | **Overflow horizontal móvil (STAB-001)** | Ya identificado en STAB-001: `.main{margin:0 auto}` provoca scroll horizontal en 5 pantallas a 390px (Proyectos, Hábitos y Notas entre ellas). Home y Tareas ya no lo sufren. No hay tarea en la cola que lo cubra: requiere decisión del PO. |

## Verificaciones positivas

- **Foco visible en todo el recorrido de teclado:** 26 paradas de `Tab` en
  Home y 26 en Tareas, **todas** con anillo `2px solid var(--accent)`. El
  anillo global `:focus-visible` (app.css) cubre también enlaces y botones
  nuevos.
- **Nombres accesibles:** 0 controles sin nombre en las dos vistas (botones
  de completar con `aria-label="Completar <título>"`, enlaces de proyecto con
  texto, selects de filtro con `aria-label`).
- **Semántica:** `lang="es"`, un único `<h1>` por vista, jerarquía
  H1 → H2 coherente (Home: Atención, Hoy, Proyectos en marcha, Captura
  rápida, Hábitos de hoy), landmark `<main>` presente, `role="progressbar"`
  con `aria-valuenow`/`aria-valuemax`/`aria-label` en las barras de proyecto,
  `role="alert"` en los errores de bloque.
- **Estados completos:** carga, vacío, error por bloque (con "Reintentar"),
  éxito (toasts) y confirmación en ambas vistas.
- **El estado nunca depende solo del color:** "Vencida", "Vence hoy",
  "Sin fecha", "Pendiente", "Completada", "Alta/Normal/Baja" son texto.
- **Responsive:** sin scroll horizontal ni desbordes de fila en 1440×900,
  768×1024 y 390×844 en ambas vistas; filas de tarea tipo tarjeta en móvil.
- **Movimiento:** transiciones de 100–200ms y `prefers-reduced-motion`
  respetado globalmente (`* { transition: none !important; animation: none
  !important; }`).
- **Sin dependencias externas:** sin fuentes remotas, sin CDN, sin
  servicios de terceros; todo el CSS y JS es local y nativo.
- **Notas como texto:** el contenido de notas y tareas se inyecta escapado
  (`escapeHtml`), nunca como HTML ejecutable.
- **Sin lógica de negocio duplicada:** las vistas consumen los endpoints
  existentes; el estado de hábito se deriva con el módulo compartido
  `habit-entry.js`.

## Re-ejecución tras las correcciones

| Comprobación | Resultado |
|---|---|
| `pytest -q` (backend, DB temporal) | ✅ **140 passed** (1 warning) |
| `ruff check app tests` | ✅ All checks passed |
| `node --check` (home.js, tasks.js, settings.js) | ✅ OK |
| `git diff --check` | ✅ Sin errores |
| QA funcional HOME-001 (Edge/CDP, 3 viewports, 2 temas) | ✅ **0 hallazgos** |
| QA funcional TASK-001 (Edge/CDP, 3 viewports, 2 temas) | ✅ **0 hallazgos** |
| Auditoría de contraste (35 selectores × 2 temas × 2 vistas) | ✅ **0 fallos** (antes: 9) |
| Trampa de foco del modal (24 `Tab`) | ✅ **0 salidas** (antes: 7) |
| Restauración de foco al cerrar el modal | ✅ `widgets-edit-btn` (antes: `BODY`) |

## Limitaciones de esta revisión

- Las capturas y mediciones son automatizadas (Edge headless vía CDP): no
  sustituyen una revisión manual en navegador real ni con lector de pantalla
  (NVDA/JAWS/VoiceOver).
- No se ejecutó axe-core ni Lighthouse: las reglas de contraste se midieron
  directamente, pero no se emite una declaración de conformidad WCAG
  completa.
- No se verificó el contraste de los estados hover/active/focus de cada
  componente, solo el estado normal.
- El revisor es el mismo agente que implementó HOME-001 y TASK-001 (ver
  nota de transparencia): la independencia queda pendiente de Nemo.

## Contexto

- Rama `product/lifeos-evolution`. Las correcciones de esta revisión se
  publican en un commit propio, después de las entregas de HOME-001
  (`1511611`) y TASK-001 (`6218ea6`).
- Cierra la Fase 9 en cuanto a tareas READY: STAB-001, BUG-001, HAB-002,
  PRJ-UI-001, HOME-001, TASK-001 y UX-REVIEW-001 quedan en REVIEW.
- PRJ-WORKSPACE-001, PRJ-PLAN-001 y ANALYTICS-001 siguen en PLANNING
  (solo diseño, sin código).
- `contexto_lifeos.txt` no trackeado en el repo: no versionar ni borrar.
