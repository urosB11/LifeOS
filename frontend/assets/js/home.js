// Life OS — vista Home (dashboard configurable) — Fase 8B + HOME-001 + UX-01
//
// Centro de operaciones diario: qué requiere atención, qué puedo avanzar
// hoy, qué proyectos están en marcha, cómo vienen los hábitos y cómo
// capturar una tarea o una nota.
//
// El catálogo de widgets se conserva intacto (ids y visibilidad). El orden
// global y los spans lógicos de grid definen su colocación responsive.
//
// UX-01 añade: fecha con la zona horaria configurada, estados por bloque
// (carga/error/vacío con reintento individual), fallback del catálogo si
// falla GET /dashboard/widgets y captura con selector Tarea/Nota.

import { showToast } from "./app.js";
import {
  HABIT_DAY_SYMBOLS,
  deriveHabitDayState,
  formatLongDate,
  habitLegendHtml,
  habitStateBadge,
  habitStateLabel,
  openHabitEntryEditor,
} from "./habit-entry.js";

const CAPTURE_WIDGET_IDS = ["quick_add_task", "quick_add_note"];

const MAX_ATTENTION = 5;
const MAX_TODAY = 8;
const MAX_PROJECTS = 6;
const MAX_HABITS = 6;
const homeViewControllers = new WeakMap();
// Una tarea cuenta como relevante para hoy si está vencida, vence hoy, vence
// dentro de una semana, tiene prioridad alta o no tiene fecha.
const RELEVANT_WINDOW_DAYS = 7;

// Espejo del catálogo del backend (WIDGET_CATALOG en
// backend/app/modules/dashboard/service.py). Solo se usa como disposición
// conocida cuando GET /dashboard/widgets falla: Home nunca queda en blanco
// (UX-01 §5) y el aviso ofrece reintento. No sustituye las preferencias
// reales: mientras falle, guardar preferencias queda bloqueado.
const DEFAULT_WIDGETS = [
  { widget_id: "upcoming_tasks", label: "Tareas próximas", is_visible: true, position: 0, column_span: 4, row_span: 1 },
  { widget_id: "quick_add_task", label: "Nueva tarea", is_visible: true, position: 1, column_span: 2, row_span: 1 },
  { widget_id: "quick_add_note", label: "Nueva nota", is_visible: true, position: 1, column_span: 2, row_span: 1 },
  { widget_id: "active_projects", label: "Proyectos activos", is_visible: true, position: 2, column_span: 4, row_span: 1 },
  { widget_id: "habits_today", label: "Hábitos de hoy", is_visible: true, position: 3, column_span: 2, row_span: 1 },
  { widget_id: "habits_week", label: "Semana de hábitos", is_visible: true, position: 4, column_span: 6, row_span: 1 },
];

// Mismo default que app/core/clock.py (DEFAULT_TIMEZONE): si la zona
// configurada no existe, backend y frontend resuelven a la misma fecha.
const DEFAULT_TIMEZONE = "America/Argentina/Cordoba";

export async function renderHomeView(container, apiBase) {
  homeViewControllers.get(container)?.abort();
  const eventController = new AbortController();
  homeViewControllers.set(container, eventController);

  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Home</h1>
        <p class="subtitle" id="home-date">&nbsp;</p>
        <p class="home-context" id="home-context"></p>
      </div>
      <button class="btn btn--secondary" id="widgets-edit-btn" aria-pressed="false">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;" aria-hidden="true" focusable="false">
          <circle cx="8" cy="8" r="2"/>
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.3 3.3l1.4 1.4M11.3 11.3l1.4 1.4M12.7 3.3l-1.4 1.4M4.7 11.3l-1.4 1.4"/>
        </svg>
        <span id="widgets-edit-label">Personalizar</span>
      </button>
    </div>

    <div class="home-prefs-notice" id="home-prefs-notice" role="alert" hidden>
      <span class="home-prefs-notice__text" id="home-prefs-notice-text"></span>
      <button class="btn btn--secondary btn--sm" data-action="retry-widgets">Reintentar</button>
    </div>

    <div id="home-customize-panel"></div>

    <div class="home-layout" id="home-grid" data-home-grid></div>
  `;

  const dateEl = container.querySelector("#home-date");
  const contextEl = container.querySelector("#home-context");
  const homeGridEl = container.querySelector("#home-grid");
  const editBtn = container.querySelector("#widgets-edit-btn");
  const editLabel = container.querySelector("#widgets-edit-label");
  const customizePanel = container.querySelector("#home-customize-panel");
  editBtn.disabled = true;

  let widgets = [];
  let widgetsLoading = true;
  // true mientras GET /dashboard/widgets falle: se usan DEFAULT_WIDGETS y
  // se anuncia el fallo con reintento; guardar preferencias queda bloqueado
  // para no sobrescribir las preferencias reales con los defaults.
  let prefsFailed = false;
  // Zona horaria configurada en Settings (UX-01 §2/§3.1): "pending" hasta
  // resolver GET /settings/timezone; "ok" con valor validado; "failed" si la
  // petición falla (la fecha cae a la local del navegador).
  const tzInfo = { state: "pending", value: null };
  // Datos por bloque (UX-01 §5): undefined = cargando · null = no se pudo
  // cargar (error del bloque, distinto de vacío) · array = datos.
  const data = {};
  // Última semana cargada: alimenta el editor de celdas del widget.
  let currentWeek = null;
  // Borradores de la captura rápida: sobreviven a los re-renders por error.
  const drafts = {
    task: { title: "", project_id: "" },
    note: { title: "", content: "" },
  };
  let captureMode = "task";
  const captureErrors = { task: "", note: "" };
  const capturePending = { task: false, note: false };
  let customizingWidgets = false;
  let widgetDraft = null;
  let widgetSaveState = "idle";
  let widgetSaveError = "";
  let widgetAnnouncement = "";
  let dragState = null;
  let resizeState = null;

  // --- Utilidades -----------------------------------------------------------
  function todayISO() {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  function addDays(iso, days) {
    const d = new Date(`${iso}T00:00:00`);
    d.setDate(d.getDate() + days);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  // Valida la zona horaria como hace _valid_zone() en app/core/clock.py:
  // un valor inválido resuelve al default, igual que en el backend.
  function isValidTimezone(tz) {
    if (!tz) return false;
    try {
      new Intl.DateTimeFormat("en-CA", { timeZone: tz });
      return true;
    } catch (error) {
      return false;
    }
  }

  // Fecha YYYY-MM-DD en la zona horaria indicada, vía Intl (sin dependencias).
  function isoInTz(date, timeZone) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(date);
    const pick = (type) => (parts.find((p) => p.type === type) || {}).value || "";
    return `${pick("year")}-${pick("month")}-${pick("day")}`;
  }

  // Hoy para toda la vista (fecha del encabezado, frase contextual y
  // selección de tareas): usar la zona configurada directamente; /habits/week
  // alimenta su propio calendario y no es la fuente de la fecha de Home.
  function homeToday() {
    if (tzInfo.state === "ok") return isoInTz(new Date(), tzInfo.value);
    return todayISO();
  }

  // Orden explícito de "Hoy": vencidas, vencen hoy, prioridad alta, próxima
  // fecha y, al final, las que no tienen fecha.
  function todayRank(task, today) {
    if (task.due_date && task.due_date < today) return 0;
    if (task.due_date === today) return 1;
    if (task.priority === "high") return 2;
    if (task.due_date) return 3;
    return 4;
  }

  function isRelevantToday(task, today) {
    if (!task.due_date) return true;
    if (task.due_date <= today) return true;
    if (task.due_date <= addDays(today, RELEVANT_WINDOW_DAYS)) return true;
    return task.priority === "high";
  }

  function priorityLabel(priority) {
    if (priority === "high") return "Alta";
    if (priority === "normal") return "Normal";
    if (priority === "low") return "Baja";
    return "";
  }

  function projectName(projectId) {
    if (!projectId) return "";
    const p = (data.projects || []).find((x) => x.id === projectId);
    return p ? p.name : "";
  }

  function formatApiDetail(detail, fallback) {
    if (!detail) return fallback;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail.map((item) => (item && item.msg ? item.msg : null)).filter(Boolean);
      if (messages.length) return messages.join(" · ");
    }
    return fallback;
  }

  function projectProgress(project) {
    if (!project.task_count) return null;
    return Math.round((project.completed_count / project.task_count) * 100);
  }

  // --- Carga de datos (UX-01 §5: bloques independientes) --------------------
  const BLOCK_URLS = {
    tasks: `${apiBase}/tasks?status=pending`,
    projects: `${apiBase}/projects?status=active`,
    habits: `${apiBase}/habits/today`,
    week: `${apiBase}/habits/week`,
  };

  async function loadWidgets() {
    widgetsLoading = true;
    try {
      const res = await fetch(`${apiBase}/dashboard/widgets`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      widgets = await res.json();
      prefsFailed = false;
    } catch (error) {
      // Disposición predeterminada conocida: Home nunca queda en blanco
      // (UX-01 §5) y el aviso ofrece reintento.
      widgets = DEFAULT_WIDGETS.map((w) => ({ ...w }));
      prefsFailed = true;
    } finally {
      widgetsLoading = false;
    }
  }

  // Carga (o recarga) un bloque. Con `showLoading` el bloque pasa por su
  // estado de carga; sin él se conserva el contenido actual mientras llega
  // la respuesta (recarga silenciosa).
  async function loadBlock(block, showLoading = false) {
    if (showLoading) {
      data[block] = undefined;
      renderAll();
    }
    try {
      const res = await fetch(BLOCK_URLS[block]);
      data[block] = res.ok ? await res.json() : null;
    } catch (error) {
      data[block] = null;
    }
    renderAll();
  }

  const BLOCK_WIDGET_IDS = {
    tasks: "upcoming_tasks",
    projects: "active_projects",
    habits: "habits_today",
    week: "habits_week",
  };

  // Reintento de un solo bloque (UX-01 §5): el error sigue distinguiéndose
  // del vacío y el resto de Home permanece visible.
  async function retryBlock(block) {
    if (!BLOCK_URLS[block]) return;
    await loadBlock(block, true);
    focusBlockAfterRetry(block, data[block] !== null);
  }

  // El foco vuelve al botón de reintento si el bloque sigue en error, o pasa
  // al primer control del bloque si cargó; sin esto el teclado queda en body
  // porque el botón que disparó el reintento desapareció con el re-render.
  function focusBlockAfterRetry(block, ok) {
    if (!ok) {
      const retry = container.querySelector(
        `[data-action="retry-block"][data-block="${block}"]`
      );
      if (retry) {
        retry.focus();
        return;
      }
    }
    const card = container.querySelector(`#widget-${BLOCK_WIDGET_IDS[block]}`);
    if (!card) return;
    const first = card.querySelector("button:not([disabled]), a[href]");
    if (first) {
      first.focus();
    } else if (typeof card.focus === "function") {
      card.focus();
    }
  }

  // Reintento del catálogo de preferencias (UX-01 §5): si vuelve a fallar
  // se conservan los defaults y el aviso; si carga, el aviso desaparece.
  async function retryWidgets() {
    await loadWidgets();
    renderAll();
    if (prefsFailed) {
      showToast("No se pudieron cargar las preferencias.", "error");
      const retry = container.querySelector('[data-action="retry-widgets"]');
      if (retry) retry.focus();
    } else {
      // Siguiente acción natural una vez restauradas las preferencias.
      editBtn.focus();
    }
  }

  // Zona horaria configurada en Settings (UX-01 §2/§3.1). Espeja
  // get_timezone() de app/core/clock.py: valor guardado si es una zona IANA
  // válida; si no, el default; si la petición falla, la fecha del encabezado
  // cae a la local del navegador (homeToday()).
  async function loadTimezone() {
    try {
      const res = await fetch(`${apiBase}/settings/timezone`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const body = await res.json();
      const tz = body && body.timezone;
      tzInfo.value = isValidTimezone(tz) ? tz : DEFAULT_TIMEZONE;
      tzInfo.state = "ok";
    } catch (error) {
      tzInfo.state = "failed";
      tzInfo.value = null;
    }
  }

  async function load() {
    try {
      if (!widgets.length) renderGlobalLoading();
      // 1) Disposición y zona horaria en paralelo con los bloques de datos.
      await Promise.all([loadWidgets(), loadTimezone()]);
      renderAll();
      // 2) Datos: cada bloque se pinta cuando su propia respuesta llega;
      //    un bloque lento o caído no bloquea al resto (UX-01 §5).
      await Promise.all(Object.keys(BLOCK_URLS).map((block) => loadBlock(block)));
    } catch (error) {
      renderGlobalError();
    }
  }

  function renderGlobalLoading() {
    homeGridEl.innerHTML = `<div class="widget-card"><p class="empty-state">Cargando Home&hellip;</p></div>`;
  }

  // Solo ante una excepción inesperada de render: los fallos de API se
  // resuelven por bloque y el catálogo tiene fallback (UX-01 §5).
  function renderGlobalError() {
    homeGridEl.innerHTML = `
      <div class="widget-card">
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
          <p class="empty-state__title">No se pudo cargar Home</p>
          <p class="empty-state__text">Verifica que el servicio est&eacute; activo e intent&aacute; de nuevo.</p>
          <button class="btn btn--primary" data-action="reload-home">Reintentar</button>
        </div>
      </div>
    `;
  }

  // --- Estructura -----------------------------------------------------------
  function activeWidgetPreferences() {
    return customizingWidgets && widgetDraft ? widgetDraft : widgets;
  }

  function visibleWidgets(source = activeWidgetPreferences()) {
    return source.filter((w) => w.is_visible).sort((a, b) => a.position - b.position);
  }

  function widgetGroups(source, visibleOnly = false) {
    const ordered = source
      .filter((widget) => !visibleOnly || widget.is_visible)
      .slice()
      .sort((a, b) => a.position - b.position || a.widget_id.localeCompare(b.widget_id));
    const groups = [];
    let captureAdded = false;
    for (const widget of ordered) {
      if (CAPTURE_WIDGET_IDS.includes(widget.widget_id)) {
        if (captureAdded) continue;
        captureAdded = true;
        const captureWidgets = source
          .filter((item) => CAPTURE_WIDGET_IDS.includes(item.widget_id))
          .sort((a, b) => a.position - b.position);
        const visibleCapture = captureWidgets.filter((item) => item.is_visible);
        if (visibleOnly && !visibleCapture.length) continue;
        groups.push({
          id: "quick_add",
          widgetIds: captureWidgets.map((item) => item.widget_id),
          label: "Captura rápida",
          columnSpan: captureWidgets[0]?.column_span || 2,
          rowSpan: captureWidgets[0]?.row_span || 1,
        });
      } else {
        groups.push({
          id: widget.widget_id,
          widgetIds: [widget.widget_id],
          label: widget.label,
          columnSpan: widget.column_span,
          rowSpan: widget.row_span,
        });
      }
    }
    return groups;
  }

  function visibleWidgetGroups(source = activeWidgetPreferences()) {
    return widgetGroups(source, true);
  }

  function decorateWidgetCard(markup, group) {
    return markup.replace(/<div class="widget-card"([^>]*)>/, (_match, attrs) => {
      const cleanAttrs = attrs.replace(/\s+tabindex="-1"/g, "");
      const cardAttrs = `class="widget-card home-widget-card" data-widget-group="${group.id}" data-widget-ids="${group.widgetIds.join(" ")}" data-column-span="${group.columnSpan}" data-row-span="${group.rowSpan}" tabindex="-1"`;
      return `<div ${cardAttrs}${cleanAttrs}>${widgetEditorMarkup(group.id, group.label)}`;
    });
  }

  function widgetEditorMarkup(groupId, label) {
    if (!customizingWidgets) return "";
    const groups = visibleWidgetGroups();
    const index = groups.findIndex((group) => group.id === groupId);
    const disabled = widgetSaveState === "saving";
    return `
      <div class="home-widget-editor">
        <button type="button" class="home-widget-handle" data-action="widget-drag-handle"
                data-widget-group="${groupId}" aria-label="Mover ${escapeHtml(label)}"
                ${disabled || groups.length < 2 ? "disabled" : ""}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor" aria-hidden="true">
            <circle cx="6" cy="4" r="1.25"/><circle cx="12" cy="4" r="1.25"/>
            <circle cx="6" cy="9" r="1.25"/><circle cx="12" cy="9" r="1.25"/>
            <circle cx="6" cy="14" r="1.25"/><circle cx="12" cy="14" r="1.25"/>
          </svg>
        </button>
        <div class="home-widget-editor__moves">
          <button type="button" class="home-widget-move" id="widget-move-${groupId}-up"
                  data-action="move-widget" data-widget-group="${groupId}" data-direction="up"
                  aria-label="Mover ${escapeHtml(label)} arriba" ${disabled || index <= 0 ? "disabled" : ""}>↑</button>
          <button type="button" class="home-widget-move" id="widget-move-${groupId}-down"
                  data-action="move-widget" data-widget-group="${groupId}" data-direction="down"
                  aria-label="Mover ${escapeHtml(label)} abajo" ${disabled || index === groups.length - 1 ? "disabled" : ""}>↓</button>
          <button type="button" class="home-widget-resize" data-action="widget-resize-handle"
                  data-widget-group="${groupId}" aria-label="Cambiar tamaño de ${escapeHtml(label)}"
                  ${disabled ? "disabled" : ""}>↘</button>
        </div>
      </div>
    `;
  }

  function normalizeWidgetDraftByOrder() {
    if (!widgetDraft) return;
    const positions = new Map();
    widgetGroups(widgetDraft).forEach((group, index) => {
      group.widgetIds.forEach((id) => positions.set(id, index));
    });
    widgetDraft = widgetDraft.map((widget) => ({ ...widget, position: positions.get(widget.widget_id) }));
  }

  function normalizeWidgetDraftFromDom() {
    if (!widgetDraft) return;
    const groups = widgetGroups(widgetDraft);
    const groupById = new Map(groups.map((group) => [group.id, group]));
    const orderedGroups = [];
    for (const card of homeGridEl.querySelectorAll(".home-widget-card")) {
      const group = groupById.get(card.dataset.widgetGroup);
      if (group && !orderedGroups.includes(group)) orderedGroups.push(group);
    }
    for (const group of groups) {
      if (!orderedGroups.includes(group)) orderedGroups.push(group);
    }
    const positions = new Map();
    orderedGroups.forEach((group, index) => {
      group.widgetIds.forEach((id) => positions.set(id, index));
    });
    widgetDraft = widgetDraft.map((widget) => ({
      ...widget,
      position: positions.get(widget.widget_id),
    }));
  }

  function widgetDraftIsDirty() {
    if (!widgetDraft) return false;
    const savedById = new Map(widgets.map((widget) => [widget.widget_id, widget]));
    return widgetDraft.some((widget) => {
      const saved = savedById.get(widget.widget_id);
      return !saved || saved.position !== widget.position
        || saved.is_visible !== widget.is_visible
        || saved.column_span !== widget.column_span
        || saved.row_span !== widget.row_span;
    });
  }

  function renderCustomizePanel() {
    if (!customizingWidgets || !widgetDraft) {
      customizePanel.innerHTML = "";
      return;
    }
    const sorted = widgetDraft.slice().sort((a, b) => a.position - b.position);
    const isSaving = widgetSaveState === "saving";
    customizePanel.innerHTML = `
      <section class="home-customize-panel" aria-labelledby="home-customize-title">
        <div class="home-customize-panel__intro">
          <h2 id="home-customize-title">Personalizar secciones</h2>
          <p>Usa las flechas para mover. Arrastra ↘ o usa sus flechas para cambiar el tamaño.</p>
        </div>
        <fieldset class="home-customize-visibility">
          <legend>Secciones visibles o disponibles</legend>
          <div class="home-customize-visibility__list">
            ${sorted
              .map(
                (widget) => `
                  <label class="home-customize-toggle" for="widget-visibility-${widget.widget_id}">
                    <input type="checkbox" id="widget-visibility-${widget.widget_id}"
                           data-action="widget-visibility" data-widget-id="${widget.widget_id}"
                           aria-label="${escapeHtml(widget.label)} visible"
                           ${widget.is_visible ? "checked" : ""} ${isSaving ? "disabled" : ""}>
                    <span class="home-customize-toggle__name">${escapeHtml(widget.label)}</span>
                    <span class="home-customize-toggle__zone">${widget.column_span} × ${widget.row_span} en pantalla amplia</span>
                    <span class="home-customize-toggle__state">${widget.is_visible ? "Visible" : "Oculta"}</span>
                  </label>
                `
              )
              .join("")}
          </div>
        </fieldset>
        <div class="home-customize-panel__footer">
          <div class="home-customize-panel__messages">
            <p class="home-customize-error" role="alert">${widgetSaveError ? escapeHtml(widgetSaveError) : ""}</p>
            <p class="home-customize-status" id="home-widget-status" role="status" aria-live="polite" aria-atomic="true">${escapeHtml(widgetAnnouncement || (widgetSaveState === "saved" ? "Preferencias guardadas." : ""))}</p>
          </div>
          <div class="home-customize-panel__actions">
            <button type="button" class="btn btn--secondary" data-action="cancel-customization" ${isSaving ? "disabled" : ""}>Cancelar</button>
            <button type="button" class="btn btn--primary" id="home-widget-save"
                    data-action="save-customization" ${isSaving || !widgetDraftIsDirty() ? "disabled" : ""}>
              ${isSaving ? "Guardando…" : widgetSaveError ? "Reintentar" : "Guardar cambios"}
            </button>
          </div>
        </div>
      </section>
    `;
  }

  // Guarda lo escrito en la captura antes de re-renderizar: un re-render
  // (error, reintento o respuesta tardía) no debe destruir lo que se esté
  // escribiendo (UX-01 §4: borrador preservado).
  function syncDraftsFromDom() {
    const titleEl = container.querySelector("#home-task-title");
    const projectEl = container.querySelector("#home-task-project");
    const noteTitleEl = container.querySelector("#home-note-title");
    const noteContentEl = container.querySelector("#home-note-content");
    if (titleEl) drafts.task.title = titleEl.value;
    if (projectEl) drafts.task.project_id = projectEl.value;
    if (noteTitleEl) drafts.note.title = noteTitleEl.value;
    if (noteContentEl) drafts.note.content = noteContentEl.value;
  }

  // Conserva el foco (y la selección del cursor) a través de un re-render:
  // sin esto cada pintura devuelve el foco al body y el teclado pierde el
  // lugar (UX-01 §6).
  function captureFocus() {
    const active = document.activeElement;
    if (!active || active === document.body || !container.contains(active)) {
      return () => {};
    }
    let key = null;
    if (active.id) {
      key = `#${active.id}`;
    } else if (active.dataset && active.dataset.action) {
      key = `[data-action="${active.dataset.action}"]`;
      if (active.dataset.id) key += `[data-id="${active.dataset.id}"]`;
      if (active.dataset.block) key += `[data-block="${active.dataset.block}"]`;
    }
    if (!key) return () => {};
    const start = typeof active.selectionStart === "number" ? active.selectionStart : null;
    const end = typeof active.selectionEnd === "number" ? active.selectionEnd : null;
    return () => {
      const next = container.querySelector(key);
      if (!next || typeof next.focus !== "function") return;
      next.focus();
      if (start !== null && typeof next.setSelectionRange === "function") {
        try {
          next.setSelectionRange(start, end);
        } catch (error) {
          // Tipos de input sin selección (p. ej. numéricos).
        }
      }
    };
  }

  // Aviso de preferencias no cargadas (UX-01 §5): el texto solo cambia en
  // transición; reasignar el mismo contenido en cada pintura re-anunciaría
  // el alerta.
  function renderPrefsNotice() {
    const notice = container.querySelector("#home-prefs-notice");
    if (!notice) return;
    const textEl = notice.querySelector("#home-prefs-notice-text");
    if (prefsFailed && notice.hidden) {
      textEl.textContent =
        "No se pudieron cargar las preferencias de Home. Se muestra la disposición predeterminada.";
      notice.hidden = false;
    } else if (!prefsFailed && !notice.hidden) {
      notice.hidden = true;
      textEl.textContent = "";
    }
  }

  function renderAll() {
    const restoreFocus = captureFocus();
    syncDraftsFromDom();
    renderHeader();
    renderPrefsNotice();
    renderCustomizePanel();
    editBtn.setAttribute("aria-pressed", String(customizingWidgets));
    editLabel.textContent = customizingWidgets ? "Guardar y finalizar" : "Personalizar";
    editBtn.disabled = widgetsLoading || prefsFailed || widgetSaveState === "saving";

    const visible = visibleWidgets();
    if (visible.length === 0) {
      homeGridEl.innerHTML = `
        <div class="widget-card">
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#9881;</div>
            <p class="empty-state__title">No hay secciones visibles</p>
            <p class="empty-state__text">Activa alguna secci&oacute;n desde el panel Personalizar para volver a ver tu d&iacute;a.</p>
            ${customizingWidgets ? "" : '<button class="btn btn--primary" data-action="begin-customization">Personalizar</button>'}
          </div>
        </div>
      `;
      restoreFocus();
      return;
    }

    homeGridEl.innerHTML = visibleWidgetGroups()
      .map(renderWidgetGroup)
      .join("");
    restoreFocus();
  }

  function renderHeader() {
    // La fecha mostrada deriva del mismo "hoy" que usan la frase contextual
    // y la selección de tareas: zona horaria configurada, no la del
    // navegador (UX-01 §2/§3.1).
    const today = homeToday();
    const dateText = new Date(`${today}T00:00:00`).toLocaleDateString("es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    dateEl.textContent = dateText.charAt(0).toUpperCase() + dateText.slice(1);

    if (data.tasks === null) {
      contextEl.replaceChildren(document.createTextNode("No se pudieron cargar las tareas."));
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "btn btn--secondary btn--sm home-context__retry";
      retry.dataset.action = "retry-block";
      retry.dataset.block = "tasks";
      retry.textContent = "Reintentar";
      contextEl.append(" ", retry);
      return;
    }
    if (!Array.isArray(data.tasks)) {
      contextEl.textContent = "";
      return;
    }
    const tasks = data.tasks;
    const overdue = tasks.filter((t) => t.due_date && t.due_date < today).length;
    const dueToday = tasks.filter((t) => t.due_date === today).length;
    const pending = tasks.length;

    let phrase;
    if (overdue > 0 && dueToday > 0) {
      phrase = `${overdue} ${overdue === 1 ? "tarea vencida" : "tareas vencidas"} y ${dueToday} ${
        dueToday === 1 ? "vence" : "vencen"
      } hoy.`;
    } else if (overdue > 0) {
      phrase = `${overdue} ${overdue === 1 ? "tarea vencida" : "tareas vencidas"}.`;
    } else if (dueToday > 0) {
      phrase = `${dueToday} ${dueToday === 1 ? "tarea vence" : "tareas vencen"} hoy.`;
    } else if (pending > 0) {
      phrase = `Nada vence hoy. ${pending} ${pending === 1 ? "tarea pendiente" : "tareas pendientes"} en total.`;
    } else {
      phrase = "No hay tareas pendientes.";
    }
    contextEl.textContent = phrase;
  }

  function renderWidgetGroup(group) {
    if (group.id === "upcoming_tasks") {
      return decorateWidgetCard(renderTasksCard(), group);
    }
    if (group.id === "active_projects") {
      return decorateWidgetCard(renderProjectsCard(), group);
    }
    if (group.id === "habits_today") {
      return decorateWidgetCard(renderHabitsCard(), group);
    }
    if (group.id === "habits_week") {
      return decorateWidgetCard(renderWeekCard(), group);
    }
    if (group.id === "quick_add") return renderCaptureSection(visibleWidgets());
    return "";
  }

  // --- Bloque: Atención + Hoy ------------------------------------------------
  function renderTasksCard() {
    if (data.tasks === undefined) {
      return loadingBlock("upcoming_tasks", "Tareas", "Cargando tareas&hellip;");
    }
    if (data.tasks === null) {
      return `
        <div class="widget-card" id="widget-upcoming_tasks" tabindex="-1">
          <div class="widget-header"><span class="widget-title">Tareas</span></div>
          <div class="widget-content" id="widget-content-upcoming_tasks">
            ${errorBlock("No se pudieron cargar las tareas.", "tasks")}
          </div>
        </div>
      `;
    }

    const today = homeToday();
    const tasks = data.tasks;
    const overdue = tasks.filter((t) => t.due_date && t.due_date < today);
    const dueToday = tasks.filter((t) => t.due_date === today);
    const attention = [
      ...overdue.map((task) => ({ task, kind: "overdue" })),
      ...dueToday.map((task) => ({ task, kind: "today" })),
    ]
      .sort((a, b) => {
        if (a.kind !== b.kind) return a.kind === "overdue" ? -1 : 1;
        const pa = a.task.priority === "high" ? 0 : 1;
        const pb = b.task.priority === "high" ? 0 : 1;
        if (pa !== pb) return pa - pb;
        return a.task.title.localeCompare(b.task.title, "es");
      });

    const attentionIds = new Set(attention.map(({ task }) => task.id));
    const todayTasks = tasks
      .filter((task) => isRelevantToday(task, today) && !attentionIds.has(task.id))
      .sort((a, b) => {
        const ra = todayRank(a, today);
        const rb = todayRank(b, today);
        if (ra !== rb) return ra - rb;
        const da = a.due_date || "9999-12-31";
        const db = b.due_date || "9999-12-31";
        if (da !== db) return da.localeCompare(db);
        return a.title.localeCompare(b.title);
      });

    const attentionHtml = attention.length
      ? `
        <section class="home-attention" aria-labelledby="home-attention-title">
          <div class="home-attention__head">
            <h2 class="home-section__title" id="home-attention-title">Atenci&oacute;n</h2>
            <span class="home-attention__count">${attention.length}</span>
          </div>
          <ul class="home-attention__list">
            ${attention
              .slice(0, MAX_ATTENTION)
              .map(
                ({ task, kind }) => `
              <li class="home-attention__item home-attention__item--${kind}">
                <span class="home-attention__label">${kind === "overdue" ? "Vencida" : "Vence hoy"}</span>
                <span class="home-attention__title">${escapeHtml(task.title)}</span>
                <span class="home-attention__meta">
                  ${task.priority ? `<span class="badge badge--priority-${task.priority}">${priorityLabel(task.priority)}</span>` : ""}
                  ${kind === "overdue" ? `<span class="home-attention__date">${task.due_date}</span>` : ""}
                  ${projectName(task.project_id) ? `<span class="home-attention__project">${escapeHtml(projectName(task.project_id))}</span>` : ""}
                </span>
              </li>
            `
              )
              .join("")}
          </ul>
          ${
            attention.length > MAX_ATTENTION
              ? `<p class="home-more">${attention.length - MAX_ATTENTION} m&aacute;s en Atenci&oacute;n · <a href="#/tasks">Ver todas las tareas</a></p>`
              : ""
          }
        </section>
      `
      : `
        <section class="home-attention" aria-labelledby="home-attention-title">
          <div class="home-attention__head">
            <h2 class="home-section__title" id="home-attention-title">Atenci&oacute;n</h2>
          </div>
          <p class="home-calm">Nada requiere atenci&oacute;n hoy: no hay tareas vencidas ni con vencimiento hoy.</p>
        </section>
      `;

    const todayHtml = `
      <section class="home-today" aria-labelledby="home-today-title">
        <div class="home-section__head">
          <h2 class="home-section__title" id="home-today-title">Hoy</h2>
          <a class="home-section__link" href="#/tasks">Ver todas las tareas</a>
        </div>
        ${
          todayTasks.length
            ? `<ul class="home-task-list">
                ${todayTasks.slice(0, MAX_TODAY).map((task) => taskRow(task, today)).join("")}
              </ul>
              ${
                todayTasks.length > MAX_TODAY
                  ? `<p class="home-more">${todayTasks.length - MAX_TODAY} ${todayTasks.length - MAX_TODAY === 1 ? "tarea m&aacute;s" : "tareas m&aacute;s"} en la lista completa</p>`
                  : ""
              }`
            : `<p class="home-calm">No hay tareas relevantes para hoy.</p>`
        }
      </section>
    `;

    return `
      <div class="widget-card" id="widget-upcoming_tasks" tabindex="-1">
        <div class="widget-content" id="widget-content-upcoming_tasks">
          ${attentionHtml}
          ${todayHtml}
        </div>
      </div>
    `;
  }

  function taskRow(task, today) {
    const project = projectName(task.project_id);
    let dueChip = "";
    if (!task.due_date) {
      dueChip = `<span class="chip chip--muted">Sin fecha</span>`;
    } else if (task.due_date < today) {
      dueChip = `<span class="chip chip--danger">Vencida el ${task.due_date}</span>`;
    } else if (task.due_date === today) {
      dueChip = `<span class="chip chip--warning">Vence hoy</span>`;
    } else {
      dueChip = `<span class="chip">Vence el ${task.due_date}</span>`;
    }
    return `
      <li class="home-task">
        <button type="button" class="check-toggle" data-action="complete-task" data-id="${task.id}"
                aria-label="Completar ${escapeHtml(task.title)}" title="Completar">&#10003;</button>
        <div class="home-task__body">
          <span class="home-task__title">${escapeHtml(task.title)}</span>
          <span class="home-task__chips">
            ${project ? `<span class="chip">${escapeHtml(project)}</span>` : ""}
            ${task.priority ? `<span class="badge badge--priority-${task.priority}">${priorityLabel(task.priority)}</span>` : ""}
            ${dueChip}
          </span>
        </div>
      </li>
    `;
  }

  // --- Bloque: Proyectos en marcha -------------------------------------------
  function renderProjectsCard() {
    if (data.projects === undefined) {
      return loadingBlock("active_projects", "Proyectos en marcha", "Cargando proyectos&hellip;");
    }
    if (data.projects === null) {
      return `
        <div class="widget-card" id="widget-active_projects" tabindex="-1">
          <div class="widget-header"><span class="widget-title">Proyectos en marcha</span></div>
          <div class="widget-content" id="widget-content-active_projects">
            ${errorBlock("No se pudieron cargar los proyectos.", "projects")}
          </div>
        </div>
      `;
    }
    const projects = data.projects;
    return `
      <div class="widget-card" id="widget-active_projects" tabindex="-1">
        <div class="widget-content" id="widget-content-active_projects">
          <section class="home-projects" aria-labelledby="home-projects-title">
            <div class="home-section__head">
              <h2 class="home-section__title" id="home-projects-title">Proyectos en marcha</h2>
              <a class="home-section__link" href="#/projects">Ver proyectos</a>
            </div>
            ${
              projects.length
                ? `<ul class="home-project-list">
                    ${projects.slice(0, MAX_PROJECTS).map(projectRow).join("")}
                  </ul>
                  ${projects.length > MAX_PROJECTS ? `<p class="home-more">${projects.length - MAX_PROJECTS} proyectos m&aacute;s activos</p>` : ""}`
                : `<p class="home-calm">No hay proyectos activos.</p>`
            }
          </section>
        </div>
      </div>
    `;
  }

  function projectRow(project) {
    const hasTasks = project.task_count > 0;
    const pct = projectProgress(project);
    const meta = [];
    if (project.overdue_count > 0) {
      meta.push(
        `<span class="chip chip--danger">${project.overdue_count} ${
          project.overdue_count === 1 ? "tarea vencida" : "tareas vencidas"
        }</span>`
      );
    }
    if (project.next_due_date) {
      meta.push(`<span class="chip">Pr&oacute;ximo vencimiento: ${project.next_due_date}</span>`);
    }
    return `
      <li class="home-project">
        <div class="home-project__head">
          <a class="home-project__name" href="#/projects/${project.id}">${escapeHtml(project.name)}</a>
          <span class="home-project__count">
            ${hasTasks ? `${project.completed_count}/${project.task_count}` : "Sin tareas"}
          </span>
        </div>
        ${
          hasTasks
            ? `<div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="${project.task_count}"
                 aria-valuenow="${project.completed_count}"
                 aria-label="Ejecuci&oacute;n de tareas de ${escapeHtml(project.name)}: ${project.completed_count} de ${project.task_count}">
                <div class="progress__bar" style="width:${pct}%"></div>
              </div>
              <div class="home-project__meta">
                <span class="home-project__label">Ejecuci&oacute;n de tareas</span>
                ${meta.join("")}
              </div>`
            : ""
        }
      </li>
    `;
  }

  // --- Bloque: Hábitos de hoy ------------------------------------------------
  function habitTodayState(item) {
    if (!item.entry) return "wait";
    if (item.entry.status === "completed") return "done";
    if (item.entry.status === "skipped") return "skipped";
    if (item.entry.status === "pending") return "partial";
    return "wait";
  }

  function renderHabitsCard() {
    if (data.habits === undefined) {
      return loadingBlock("habits_today", "H&aacute;bitos de hoy", "Cargando h&aacute;bitos&hellip;");
    }
    if (data.habits === null) {
      return `
        <div class="widget-card" id="widget-habits_today" tabindex="-1">
          <div class="widget-header"><span class="widget-title">H&aacute;bitos de hoy</span></div>
          <div class="widget-content" id="widget-content-habits_today">
            ${errorBlock("No se pudieron cargar los h&aacute;bitos de hoy.", "habits")}
          </div>
        </div>
      `;
    }
    const items = data.habits;
    const done = items.filter((i) => habitTodayState(i) === "done").length;
    return `
      <div class="widget-card" id="widget-habits_today" tabindex="-1">
        <div class="widget-content" id="widget-content-habits_today">
          <section class="home-habits" aria-labelledby="home-habits-title">
            <div class="home-section__head">
              <h2 class="home-section__title" id="home-habits-title">H&aacute;bitos de hoy</h2>
              <span class="home-section__summary" aria-live="polite">${done} de ${items.length} cumplidos</span>
            </div>
            ${
              items.length
                ? `<ul class="home-habit-list">
                    ${items
                      .slice(0, MAX_HABITS)
                      .map((item) => {
                        const state = habitTodayState(item);
                        return `
                        <li class="home-habit">
                          <span class="home-habit__name">${escapeHtml(item.habit.name)}</span>
                          <span class="badge badge--${habitStateBadge(state)}">${habitStateLabel(state)}</span>
                        </li>
                      `;
                      })
                      .join("")}
                  </ul>
                  ${items.length > MAX_HABITS ? `<p class="home-more">${items.length - MAX_HABITS} h&aacute;bitos m&aacute;s</p>` : ""}`
                : `<p class="home-calm">No hay h&aacute;bitos programados para hoy.</p>`
            }
            <p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>
          </section>
        </div>
      </div>
    `;
  }

  // --- Bloque: Captura rápida -----------------------------------------------
  function renderCaptureSection(sideWidgets) {
    const showTask = sideWidgets.some((w) => w.widget_id === "quick_add_task");
    const showNote = sideWidgets.some((w) => w.widget_id === "quick_add_note");
    if (!showTask && !showNote) return "";
    const capturePreference = activeWidgetPreferences().find((widget) =>
      CAPTURE_WIDGET_IDS.includes(widget.widget_id)
    );
    captureMode = showTask && showNote ? captureMode : showTask ? "task" : "note";
    const showModeSelector = showTask && showNote;
    const projects = data.projects || [];
    const markup = `
      <div class="widget-card" id="widget-quick_add">
        <div class="widget-content" id="widget-content-quick_add">
          <section class="home-capture" aria-labelledby="home-capture-title">
            <h2 class="home-section__title" id="home-capture-title">Captura r&aacute;pida</h2>
            ${
              showModeSelector
                ? `<div class="home-capture__modes" role="group" aria-label="Tipo de captura">
                    <button type="button" class="btn btn--secondary btn--sm" id="home-capture-mode-task"
                            data-action="capture-mode" data-mode="task" aria-pressed="${captureMode === "task"}">Tarea</button>
                    <button type="button" class="btn btn--secondary btn--sm" id="home-capture-mode-note"
                            data-action="capture-mode" data-mode="note" aria-pressed="${captureMode === "note"}">Nota</button>
                  </div>`
                : ""
            }
            ${
              showTask && captureMode === "task"
                ? `
              <form class="home-capture__form" data-capture="task" novalidate>
                <label class="home-capture__label" for="home-task-title">Nueva tarea</label>
                <input type="text" id="home-task-title" value="${escapeHtml(drafts.task.title)}"
                       placeholder="T&iacute;tulo de la tarea" required maxlength="200">
                <select id="home-task-project" aria-label="Proyecto (opcional)">
                  <option value="">Sin proyecto</option>
                  ${projects
                    .map(
                      (p) =>
                        `<option value="${p.id}" ${drafts.task.project_id === p.id ? "selected" : ""}>${escapeHtml(p.name)}</option>`
                    )
                    .join("")}
                </select>
                <button type="submit" class="btn btn--primary btn--sm" ${capturePending.task ? "disabled" : ""}>
                  ${capturePending.task ? "Guardando&hellip;" : "Crear tarea"}
                </button>
                <p class="home-capture__error" role="alert">${captureErrors.task ? escapeHtml(captureErrors.task) : ""}</p>
              </form>`
                : ""
            }
            ${
              showNote && captureMode === "note"
                ? `
              <form class="home-capture__form" data-capture="note" novalidate>
                <label class="home-capture__label" for="home-note-title">Nueva nota</label>
                <input type="text" id="home-note-title" value="${escapeHtml(drafts.note.title)}"
                       placeholder="T&iacute;tulo de la nota" required maxlength="200">
                <label class="home-capture__label" for="home-note-content">Contenido</label>
                <textarea id="home-note-content" rows="3" maxlength="100000"
                          placeholder="Contenido de la nota (opcional)">${escapeHtml(drafts.note.content)}</textarea>
                <button type="submit" class="btn btn--secondary btn--sm" ${capturePending.note ? "disabled" : ""}>
                  ${capturePending.note ? "Guardando&hellip;" : "Crear nota"}
                </button>
                <p class="home-capture__error" role="alert">${captureErrors.note ? escapeHtml(captureErrors.note) : ""}</p>
              </form>`
                : ""
            }
          </section>
        </div>
      </div>
    `;
    return decorateWidgetCard(markup, {
      id: "quick_add",
      widgetIds: CAPTURE_WIDGET_IDS,
      label: "Captura rápida",
      columnSpan: capturePreference?.column_span || 2,
      rowSpan: capturePreference?.row_span || 1,
    });
  }

  // --- Bloque: Semana de hábitos (HAB-002) -----------------------------------
  function renderWeekCard() {
    if (data.week === undefined) {
      return loadingBlock("habits_week", "Semana de h&aacute;bitos", "Cargando la semana&hellip;");
    }
    if (data.week === null) {
      return `
        <div class="widget-card" id="widget-habits_week" tabindex="-1">
          <div class="widget-header"><span class="widget-title">Semana de h&aacute;bitos</span></div>
          <div class="widget-content" id="widget-content-habits_week">
            ${errorBlock("No se pudo cargar la semana de h&aacute;bitos.", "week")}
          </div>
        </div>
      `;
    }
    return `
      <div class="widget-card" id="widget-habits_week" tabindex="-1">
        <div class="widget-header"><span class="widget-title">Semana de h&aacute;bitos</span></div>
        <div class="widget-content" id="widget-content-habits_week">
          ${renderHabitsWeek(data.week)}
        </div>
      </div>
    `;
  }

  function weekCell(habit, day, today) {
    const state = deriveHabitDayState(day, today);
    const label = `${habit.name}, ${formatLongDate(day.date)}: ${habitStateLabel(state)}`;
    const symbol = HABIT_DAY_SYMBOLS[state];
    const editable = state !== "off" && state !== "future";
    if (editable) {
      // Días programados <= hoy: editables desde Home (HAB-002 §1).
      return `<button type="button" class="wk-cell hstate--${state}" role="gridcell"
              data-action="wk-edit" data-id="${habit.id}" data-date="${day.date}"
              aria-label="${escapeHtml(label)}. Editar registro">${symbol}</button>`;
    }
    // No programado: espacio de alineación sin casillero, borde, fondo,
    // símbolo ni color. Futuro: celda gris sin interacción.
    return `<span class="wk-cell hstate--${state}" role="gridcell"
            aria-label="${escapeHtml(label)}">${symbol}</span>`;
  }

  function renderHabitsWeek(week) {
    currentWeek = week;
    const link = `<p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>`;
    if (!week.items.length) {
      return `<p class="home-calm">No hay h&aacute;bitos activos esta semana.</p>${link}`;
    }
    const names = ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"];
    const head = week.items[0].days
      .map((d) => {
        const weekday = new Date(`${d.date}T00:00:00`).getDay();
        const isToday = d.date === week.today;
        return `<span class="wk-head${isToday ? " wk-head--today" : ""}" role="columnheader">
            <span aria-hidden="true">${names[weekday]}</span>
            <span aria-hidden="true">${d.date.slice(8, 10)}</span>
            <span class="sr-only">${escapeHtml(formatLongDate(d.date))}${isToday ? " (hoy)" : ""}</span>
          </span>`;
      })
      .join("");
    const rows = week.items
      .map(
        (item) => `
      <div class="wk-row" role="row">
        <span class="wk-name" role="rowheader"
              title="${escapeHtml(item.habit.name)}">${escapeHtml(item.habit.name)}</span>
        ${item.days
          .map((d) => weekCell(item.habit, d, week.today))
          .join("")}
      </div>
    `
      )
      .join("");
    return `
      <div class="wk-matrix" role="grid"
           aria-label="Semana de h&aacute;bitos: ${week.week_start} al ${week.week_end}">
        <div class="wk-row wk-row--head" role="row">
          <span class="wk-name wk-name--head" role="columnheader">
            <span class="sr-only">H&aacute;bito</span>
          </span>
          ${head}
        </div>
        ${rows}
      </div>
      <ul class="wk-legend">${habitLegendHtml("wk")}</ul>
      ${link}`;
  }

  // Estado de carga de un bloque: no bloquea el resto de Home (UX-01 §5).
  function loadingBlock(widgetId, title, message) {
    return `
      <div class="widget-card" id="widget-${widgetId}" tabindex="-1">
        <div class="widget-header"><span class="widget-title">${title}</span></div>
        <div class="widget-content" id="widget-content-${widgetId}">
          <p class="home-loading">${message}</p>
        </div>
      </div>
    `;
  }

  // Error de un bloque: distinto del estado vacío, con reintento propio
  // (UX-01 §5). `tabindex="-1"` permite devolver el foco al fallar/suceder
  // el reintento sin perder al teclado.
  function errorBlock(message, block) {
    return `
      <div class="home-error" role="alert">
        <p class="home-error__text">${escapeHtml(message)}</p>
        <button class="btn btn--secondary btn--sm" data-action="retry-block" data-block="${block}">Reintentar</button>
      </div>
    `;
  }

  // --- Refresco dirigido tras editar un hábito (HAB-002) --------------------
  async function refreshHabitsViews() {
    const [weekRes, todayRes] = await Promise.all([
      fetch(`${apiBase}/habits/week`),
      fetch(`${apiBase}/habits/today`),
    ]);
    if (!weekRes.ok || !todayRes.ok) {
      throw new Error("No se pudo actualizar la vista de hábitos");
    }
    const week = await weekRes.json();
    const items = await todayRes.json();
    data.week = week;
    data.habits = items;
    const weekEl = container.querySelector("#widget-content-habits_week");
    if (weekEl) weekEl.innerHTML = renderHabitsWeek(week);
    const todayEl = container.querySelector("#widget-content-habits_today");
    if (todayEl) todayEl.innerHTML = renderHabitsTodayInner(items);
  }

  function renderHabitsTodayInner(items) {
    const done = items.filter((i) => habitTodayState(i) === "done").length;
    const list = items.length
      ? `<ul class="home-habit-list">
          ${items
            .slice(0, MAX_HABITS)
            .map((item) => {
              const state = habitTodayState(item);
              return `
              <li class="home-habit">
                <span class="home-habit__name">${escapeHtml(item.habit.name)}</span>
                <span class="badge badge--${habitStateBadge(state)}">${habitStateLabel(state)}</span>
              </li>
            `;
            })
            .join("")}
        </ul>`
      : `<p class="home-calm">No hay h&aacute;bitos programados para hoy.</p>`;
    return `
      <section class="home-habits" aria-labelledby="home-habits-title">
        <div class="home-section__head">
          <h2 class="home-section__title" id="home-habits-title">H&aacute;bitos de hoy</h2>
          <span class="home-section__summary" aria-live="polite">${done} de ${items.length} cumplidos</span>
        </div>
        ${list}
        <p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>
      </section>
    `;
  }

  // --- Acciones -------------------------------------------------------------
  async function completeTask(taskId, button) {
    if (button.disabled) return;
    button.disabled = true;
    try {
      const res = await fetch(`${apiBase}/tasks/${taskId}/complete`, { method: "POST" });
      if (res.ok) {
        showToast("Tarea completada", "success");
        await load();
      } else {
        button.disabled = false;
        const err = await res.json().catch(() => ({}));
        showToast(formatApiDetail(err.detail, "No se pudo completar la tarea"), "error");
      }
    } catch (error) {
      button.disabled = false;
      showToast("Error de conexión", "error");
    }
  }

  async function submitQuickTask() {
    if (capturePending.task) return;
    const titleEl = container.querySelector("#home-task-title");
    const projectEl = container.querySelector("#home-task-project");
    if (titleEl) drafts.task.title = titleEl.value;
    if (projectEl) drafts.task.project_id = projectEl.value;
    const title = drafts.task.title.trim();
    if (!title) {
      captureErrors.task = "Escribe un título para la tarea.";
      renderAll();
      focusCapture("task");
      return;
    }
    capturePending.task = true;
    captureErrors.task = "";
    renderAll();
    try {
      const body = { title };
      if (drafts.task.project_id) body.project_id = drafts.task.project_id;
      const res = await fetch(`${apiBase}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        capturePending.task = false;
        drafts.task = { title: "", project_id: "" };
        // Limpia también el DOM: syncDraftsFromDom() re-leería el valor
        // viejo durante el re-render y resucitaría el borrador.
        const titleInput = container.querySelector("#home-task-title");
        const projectSelect = container.querySelector("#home-task-project");
        if (titleInput) titleInput.value = "";
        if (projectSelect) projectSelect.value = "";
        // Listo para la siguiente captura; el foco sobrevive a los
        // re-renders posteriores por su id.
        focusCapture("task");
        showToast("Tarea creada", "success");
        const refreshes = [loadBlock("tasks")];
        if (body.project_id) refreshes.push(loadBlock("projects"));
        await Promise.all(refreshes);
      } else {
        capturePending.task = false;
        const err = await res.json().catch(() => ({}));
        captureErrors.task = formatApiDetail(err.detail, "No se pudo crear la tarea.");
        renderAll();
        focusCapture("task");
      }
    } catch (error) {
      capturePending.task = false;
      captureErrors.task = "Error de conexión. Inténtalo de nuevo.";
      renderAll();
      focusCapture("task");
    }
  }

  async function submitQuickNote() {
    if (capturePending.note) return;
    const titleEl = container.querySelector("#home-note-title");
    const contentEl = container.querySelector("#home-note-content");
    if (titleEl) drafts.note.title = titleEl.value;
    if (contentEl) drafts.note.content = contentEl.value;
    const title = drafts.note.title.trim();
    if (!title) {
      captureErrors.note = "Escribe un título para la nota.";
      renderAll();
      focusCapture("note");
      return;
    }
    capturePending.note = true;
    captureErrors.note = "";
    renderAll();
    try {
      const res = await fetch(`${apiBase}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content: drafts.note.content }),
      });
      if (res.ok) {
        capturePending.note = false;
        drafts.note = { title: "", content: "" };
        // Limpia también el DOM para que syncDraftsFromDom() no resucite el
        // borrador durante el re-render, y deja el foco listo para la
        // siguiente captura.
        const noteInput = container.querySelector("#home-note-title");
        const noteContent = container.querySelector("#home-note-content");
        if (noteInput) noteInput.value = "";
        if (noteContent) noteContent.value = "";
        focusCapture("note");
        showToast("Nota creada", "success");
      } else {
        capturePending.note = false;
        const err = await res.json().catch(() => ({}));
        captureErrors.note = formatApiDetail(err.detail, "No se pudo crear la nota.");
        renderAll();
        focusCapture("note");
      }
    } catch (error) {
      capturePending.note = false;
      captureErrors.note = "Error de conexión. Inténtalo de nuevo.";
      renderAll();
      focusCapture("note");
    }
  }

  function focusCapture(kind) {
    const id = kind === "task" ? "#home-task-title" : "#home-note-title";
    const el = container.querySelector(id);
    if (el) el.focus();
  }

  container.addEventListener("pointerdown", startWidgetDrag, { signal: eventController.signal });
  container.addEventListener("pointerdown", startWidgetResize, { signal: eventController.signal });
  container.addEventListener("pointermove", (event) => {
    moveWidgetDrag(event);
    moveWidgetResize(event);
  }, { signal: eventController.signal });
  container.addEventListener("pointerup", (event) => {
    finishWidgetDrag(event, true);
    finishWidgetResize(event, true);
  }, {
    signal: eventController.signal,
  });
  container.addEventListener("pointercancel", (event) => {
    finishWidgetDrag(event, false);
    finishWidgetResize(event, false);
  }, {
    signal: eventController.signal,
  });

  container.addEventListener("keydown", (event) => {
    const handle = event.target.closest('[data-action="widget-resize-handle"]');
    if (!handle || !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    event.preventDefault();
    resizeWidgetGroup(
      handle.dataset.widgetGroup,
      event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0,
      event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0
    );
  }, { signal: eventController.signal });

  // Delegación de eventos: el contenido se re-renderiza con frecuencia.
  container.addEventListener("click", async (event) => {
    const captureModeBtn = event.target.closest('[data-action="capture-mode"]');
    if (captureModeBtn) {
      syncDraftsFromDom();
      captureMode = captureModeBtn.dataset.mode;
      renderAll();
      return;
    }

    const completeBtn = event.target.closest('[data-action="complete-task"]');
    if (completeBtn) {
      await completeTask(completeBtn.dataset.id, completeBtn);
      return;
    }

    const reloadBtn = event.target.closest('[data-action="reload-home"]');
    if (reloadBtn) {
      await load();
      return;
    }

    const retryBlockBtn = event.target.closest('[data-action="retry-block"]');
    if (retryBlockBtn) {
      await retryBlock(retryBlockBtn.dataset.block);
      return;
    }

    const retryWidgetsBtn = event.target.closest('[data-action="retry-widgets"]');
    if (retryWidgetsBtn) {
      await retryWidgets();
      return;
    }

    const beginCustomizeBtn = event.target.closest('[data-action="begin-customization"]');
    if (beginCustomizeBtn) {
      beginCustomization();
      return;
    }

    const moveWidgetBtn = event.target.closest('[data-action="move-widget"]');
    if (moveWidgetBtn) {
      moveWidgetGroup(moveWidgetBtn.dataset.widgetGroup, moveWidgetBtn.dataset.direction);
      return;
    }

    const saveCustomizeBtn = event.target.closest('[data-action="save-customization"]');
    if (saveCustomizeBtn) {
      await saveWidgetPreferences();
      return;
    }

    const cancelCustomizeBtn = event.target.closest('[data-action="cancel-customization"]');
    if (cancelCustomizeBtn) {
      cancelCustomization();
      return;
    }

    const cell = event.target.closest('[data-action="wk-edit"]');
    if (cell) {
      if (!currentWeek) return;
      const item = currentWeek.items.find((i) => i.habit.id === cell.dataset.id);
      if (!item) return;
      const day = item.days.find((d) => d.date === cell.dataset.date);
      if (!day) return;
      openHabitEntryEditor({
        apiBase,
        habit: item.habit,
        date: day.date,
        entry: day.entry_status ? { status: day.entry_status, value: day.entry_value } : null,
        today: currentWeek.today,
        onSaved: refreshHabitsViews,
        getFallbackFocus: () => container.querySelector("#widget-habits_week"),
        returnFocusTo: cell,
      });
    }
  }, { signal: eventController.signal });

  container.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-capture]");
    if (!form) return;
    event.preventDefault();
    if (form.dataset.capture === "task") {
      await submitQuickTask();
    } else if (form.dataset.capture === "note") {
      await submitQuickNote();
    }
  }, { signal: eventController.signal });

  container.addEventListener("change", (event) => {
    const visibilityToggle = event.target.closest('[data-action="widget-visibility"]');
    if (!visibilityToggle || !widgetDraft || widgetSaveState === "saving") return;
    const widget = widgetDraft.find((item) => item.widget_id === visibilityToggle.dataset.widgetId);
    if (!widget) return;
    widget.is_visible = visibilityToggle.checked;
    normalizeWidgetDraftByOrder();
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = `${widget.label}: ${widget.is_visible ? "visible" : "oculta"}.`;
    renderAll();
  }, { signal: eventController.signal });

  function beginCustomization() {
    if (widgetsLoading || prefsFailed) {
      showToast("No se pudieron cargar las preferencias. Reintent&aacute; primero.", "error");
      const retry = container.querySelector('[data-action="retry-widgets"]');
      if (retry) retry.focus();
      return;
    }
    widgetDraft = widgets.map((widget) => ({ ...widget }));
    customizingWidgets = true;
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = "";
    renderAll();
    const firstToggle = container.querySelector('[data-action="widget-visibility"]');
    const firstMove = container.querySelector('[data-action="move-widget"]:not([disabled])');
    (firstToggle || firstMove || customizePanel).focus();
  }

  function cancelCustomization() {
    if (widgetSaveState === "saving") return;
    widgetDraft = null;
    customizingWidgets = false;
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = "";
    renderAll();
    editBtn.focus();
  }

  function announceWidget(message) {
    if (widgetAnnouncement === message) return;
    widgetAnnouncement = message;
    const status = container.querySelector("#home-widget-status");
    if (status) status.textContent = message;
  }

  function focusWidgetGroup(groupId) {
    const card = container.querySelector(`.home-widget-card[data-widget-group="${groupId}"]`);
    if (card) card.focus();
  }

  function focusWidgetResize(groupId) {
    const handle = container.querySelector(
      `[data-action="widget-resize-handle"][data-widget-group="${groupId}"]`
    );
    if (handle) handle.focus();
  }

  function moveWidgetGroup(groupId, direction) {
    if (!widgetDraft || widgetSaveState === "saving" || !["up", "down"].includes(direction)) return;
    const card = container.querySelector(`.home-widget-card[data-widget-group="${groupId}"]`);
    if (!card) return;
    const cards = Array.from(homeGridEl.querySelectorAll(".home-widget-card"));
    const index = cards.indexOf(card);
    const target = cards[index + (direction === "up" ? -1 : 1)];
    if (!target) return;
    if (direction === "up") homeGridEl.insertBefore(card, target);
    else homeGridEl.insertBefore(target, card);
    normalizeWidgetDraftFromDom();
    const groups = visibleWidgetGroups();
    const nextIndex = groups.findIndex((group) => group.id === groupId);
    const label = groups[nextIndex]?.label || groupId;
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = `${label} movido a la posición ${nextIndex + 1} de ${groups.length}.`;
    renderAll();
    focusWidgetGroup(groupId);
  }

  function resizeWidgetGroup(groupId, columnDelta, rowDelta) {
    if (!widgetDraft || widgetSaveState === "saving") return;
    const group = widgetGroups(widgetDraft).find((item) => item.id === groupId);
    if (!group) return;
    const columnSpan = Math.max(2, Math.min(6, group.columnSpan + columnDelta));
    const rowSpan = Math.max(1, Math.min(3, group.rowSpan + rowDelta));
    if (columnSpan === group.columnSpan && rowSpan === group.rowSpan) return;
    for (const widget of widgetDraft) {
      if (group.widgetIds.includes(widget.widget_id)) {
        widget.column_span = columnSpan;
        widget.row_span = rowSpan;
      }
    }
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = `${group.label}: tamaño ${columnSpan} por ${rowSpan}.`;
    renderAll();
    focusWidgetResize(groupId);
  }

  function clearDropHighlights() {
    homeGridEl.classList.remove("home-drop-forbidden");
    container.querySelectorAll(".home-widget-card--drop-target").forEach((card) => {
      card.classList.remove("home-widget-card--drop-target");
    });
  }

  function updateDragTarget(event) {
    const state = dragState;
    if (!state || !state.started) return;
    clearDropHighlights();
    // El placeholder ocupa una celda del grid con el mismo tamaño de la
    // tarjeta arrastrada: al insertarse desplaza el resto de tarjetas. Por eso
    // el destino se resuelve sobre la geometría capturada al iniciar el
    // arrastre; así la sección cae donde señala la previsualización y no al
    // final de la cuadrícula.
    const pointerX = event.clientX + window.scrollX;
    const pointerY = event.clientY + window.scrollY;
    const targetCard = [...state.layout.entries()].find(([card, rect]) => {
      if (card === state.source) return false;
      return pointerX >= rect.left && pointerX <= rect.right
        && pointerY >= rect.top && pointerY <= rect.bottom;
    });

    if (!targetCard) {
      // Sin tarjeta bajo el puntero: si además está fuera de la cuadrícula,
      // soltar allí no es válido; si está en una zona vacía, se conserva la
      // previsualización ya mostrada.
      const gridRect = homeGridEl.getBoundingClientRect();
      const insideGrid = event.clientX >= gridRect.left && event.clientX <= gridRect.right
        && event.clientY >= gridRect.top && event.clientY <= gridRect.bottom;
      if (!insideGrid) {
        state.invalid = true;
        homeGridEl.classList.add("home-drop-forbidden");
        announceWidget("Suelta la sección dentro de la cuadrícula.");
        return;
      }
      state.invalid = false;
      return;
    }

    state.invalid = false;
    const [card, rect] = targetCard;
    card.classList.add("home-widget-card--drop-target");
    const verticalMidpoint = rect.top + rect.height / 2;
    const before = pointerY < verticalMidpoint
      || (pointerY < rect.bottom && pointerX < rect.left + rect.width / 2);
    homeGridEl.insertBefore(state.placeholder, before ? card : card.nextSibling);
    announceWidget("Suelta la sección para cambiar su posición.");
  }

  function startWidgetDrag(event) {
    const handle = event.target.closest('[data-action="widget-drag-handle"]');
    if (!handle || handle.disabled || !customizingWidgets || widgetSaveState === "saving" || event.button !== 0) return;
    const source = handle.closest(".home-widget-card");
    if (!source) return;
    const placeholder = document.createElement("div");
    placeholder.className = "home-widget-drop-placeholder";
    placeholder.setAttribute("aria-hidden", "true");
    placeholder.textContent = "Soltar aquí";
    placeholder.dataset.columnSpan = source.dataset.columnSpan;
    placeholder.dataset.rowSpan = source.dataset.rowSpan;
    dragState = {
      handle,
      pointerId: event.pointerId,
      source,
      placeholder,
      startX: event.clientX,
      startY: event.clientY,
      started: false,
      invalid: false,
      initialOrder: Array.from(homeGridEl.querySelectorAll(".home-widget-card"))
        .map((card) => card.dataset.widgetGroup),
      // Geometría de las tarjetas en coordenadas de documento, capturada antes
      // de insertar el placeholder. El placeholder es un elemento más del grid
      // y desplaza el resto de tarjetas, así que resolver el destino con las
      // medidas en vivo desfasaría el puntero respecto a lo que se ve.
      layout: new Map(
        Array.from(homeGridEl.querySelectorAll(".home-widget-card")).map((card) => {
          const rect = card.getBoundingClientRect();
          return [card, {
            left: rect.left + window.scrollX,
            top: rect.top + window.scrollY,
            right: rect.right + window.scrollX,
            bottom: rect.bottom + window.scrollY,
            width: rect.width,
            height: rect.height,
          }];
        })
      ),
    };
    handle.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveWidgetDrag(event) {
    const state = dragState;
    if (!state || state.pointerId !== event.pointerId) return;
    if (!state.started) {
      const distance = Math.hypot(event.clientX - state.startX, event.clientY - state.startY);
      if (distance < 5) return;
      state.started = true;
      state.source.classList.add("home-widget-card--dragging");
      homeGridEl.insertBefore(state.placeholder, state.source);
      const group = visibleWidgetGroups().find(
        (item) => item.id === state.source.dataset.widgetGroup
      );
      announceWidget(`Arrastrando ${group ? group.label : "sección"}.`);
    }
    event.preventDefault();
    const edgeSize = 64;
    if (event.clientY > window.innerHeight - edgeSize) window.scrollBy(0, 18);
    else if (event.clientY < edgeSize) window.scrollBy(0, -18);
    updateDragTarget(event);
  }

  function finishWidgetDrag(event, commit) {
    const state = dragState;
    if (!state || state.pointerId !== event.pointerId) return;
    if (commit && state.started) updateDragTarget(event);
    dragState = null;
    clearDropHighlights();
    state.source.classList.remove("home-widget-card--dragging");
    if (state.handle.hasPointerCapture(state.pointerId)) {
      state.handle.releasePointerCapture(state.pointerId);
    }
    if (!state.started) return;

    const releaseTarget = document.elementFromPoint(event.clientX, event.clientY);
    const validDrop = commit
      && !state.invalid
      && homeGridEl.contains(releaseTarget)
      && state.placeholder.parentElement === homeGridEl;
    if (!validDrop) {
      state.placeholder.remove();
      announceWidget("Movimiento cancelado. La sección conserva su posición.");
      return;
    }
    homeGridEl.insertBefore(state.source, state.placeholder);
    state.placeholder.remove();
    const nextOrder = Array.from(homeGridEl.querySelectorAll(".home-widget-card"))
      .map((card) => card.dataset.widgetGroup);
    if (nextOrder.join("|") === state.initialOrder.join("|")) {
      announceWidget("La sección conserva su posición.");
      return;
    }
    normalizeWidgetDraftFromDom();
    const groups = visibleWidgetGroups();
    const index = groups.findIndex((group) => group.id === state.source.dataset.widgetGroup);
    const group = groups[index];
    widgetSaveState = "idle";
    widgetSaveError = "";
    widgetAnnouncement = `${group.label} movido a la posición ${index + 1} de ${groups.length}.`;
    renderAll();
    focusWidgetGroup(group.id);
  }

  function gridMetrics() {
    const styles = getComputedStyle(homeGridEl);
    const columns = styles.gridTemplateColumns.split(" ").length;
    const gap = Number.parseFloat(styles.columnGap) || 0;
    const cellWidth = (homeGridEl.clientWidth - gap * (columns - 1)) / columns + gap;
    const rowHeight = Number.parseFloat(styles.gridAutoRows) || 112;
    const rowStep = rowHeight + (Number.parseFloat(styles.rowGap) || gap);
    return { cellWidth, rowStep };
  }

  function startWidgetResize(event) {
    const handle = event.target.closest('[data-action="widget-resize-handle"]');
    if (!handle || handle.disabled || !customizingWidgets || widgetSaveState === "saving" || event.button !== 0) return;
    const source = handle.closest(".home-widget-card");
    if (!source) return;
    const metrics = gridMetrics();
    resizeState = {
      handle,
      pointerId: event.pointerId,
      source,
      groupId: source.dataset.widgetGroup,
      startX: event.clientX,
      startY: event.clientY,
      startColumnSpan: Number(source.dataset.columnSpan),
      startRowSpan: Number(source.dataset.rowSpan),
      cellWidth: metrics.cellWidth,
      rowStep: metrics.rowStep,
      started: false,
    };
    handle.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveWidgetResize(event) {
    const state = resizeState;
    if (!state || state.pointerId !== event.pointerId) return;
    const columnDelta = Math.round((event.clientX - state.startX) / state.cellWidth);
    const rowDelta = Math.round((event.clientY - state.startY) / state.rowStep);
    const columnSpan = Math.max(2, Math.min(6, state.startColumnSpan + columnDelta));
    const rowSpan = Math.max(1, Math.min(3, state.startRowSpan + rowDelta));
    if (columnSpan === Number(state.source.dataset.columnSpan)
      && rowSpan === Number(state.source.dataset.rowSpan)) return;
    state.started = true;
    state.source.classList.add("home-widget-card--resizing");
    for (const widget of widgetDraft || []) {
      if (state.source.dataset.widgetIds.split(" ").includes(widget.widget_id)) {
        widget.column_span = columnSpan;
        widget.row_span = rowSpan;
      }
    }
    state.source.dataset.columnSpan = String(columnSpan);
    state.source.dataset.rowSpan = String(rowSpan);
    widgetSaveState = "idle";
    widgetSaveError = "";
    const group = widgetGroups(widgetDraft).find((item) => item.id === state.groupId);
    widgetAnnouncement = `${group?.label || "Sección"}: tamaño ${columnSpan} por ${rowSpan}.`;
    renderCustomizePanel();
    announceWidget(widgetAnnouncement);
    event.preventDefault();
  }

  function finishWidgetResize(event, commit) {
    const state = resizeState;
    if (!state || state.pointerId !== event.pointerId) return;
    resizeState = null;
    state.source.classList.remove("home-widget-card--resizing");
    if (state.handle.hasPointerCapture(state.pointerId)) {
      state.handle.releasePointerCapture(state.pointerId);
    }
    if (!state.started) return;
    if (!commit) {
      for (const widget of widgetDraft || []) {
        if (state.source.dataset.widgetIds.split(" ").includes(widget.widget_id)) {
          widget.column_span = state.startColumnSpan;
          widget.row_span = state.startRowSpan;
        }
      }
      renderAll();
      focusWidgetResize(state.groupId);
      announceWidget("Cambio de tamaño cancelado.");
      return;
    }
    const group = widgetGroups(widgetDraft).find((item) => item.id === state.groupId);
    widgetAnnouncement = `${group.label}: tamaño ${group.columnSpan} por ${group.rowSpan}.`;
    renderAll();
    focusWidgetResize(state.groupId);
  }

  async function saveWidgetPreferences(exitAfterSave = false) {
    if (!customizingWidgets || !widgetDraft || prefsFailed || widgetSaveState === "saving") return;
    if (!widgetDraftIsDirty()) {
      if (exitAfterSave) cancelCustomization();
      else announceWidget("No hay cambios pendientes.");
      return;
    }
    normalizeWidgetDraftByOrder();
    widgetSaveState = "saving";
    widgetSaveError = "";
    widgetAnnouncement = "Guardando preferencias.";
    renderAll();
    try {
      const res = await fetch(`${apiBase}/dashboard/widgets`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(widgetDraft.map(({
          widget_id,
          is_visible,
          position,
          column_span,
          row_span,
        }) => ({
          widget_id,
          is_visible,
          position,
          column_span,
          row_span,
        }))),
      });
      const saved = await res.json();
      if (!res.ok) {
        throw new Error(formatApiDetail(saved.detail, "No se pudieron guardar las preferencias."));
      }
      if (!Array.isArray(saved) || saved.length !== widgets.length) {
        throw new Error("La respuesta del servidor no contiene el catálogo completo de widgets.");
      }
      const savedById = new Map(saved.map((widget) => [widget.widget_id, widget]));
      if (widgets.some((widget) => !savedById.has(widget.widget_id))) {
        throw new Error("La respuesta del servidor no coincide con el catálogo de widgets.");
      }
      widgets = widgets.map((widget) => ({ ...widget, ...savedById.get(widget.widget_id) }));
      widgetDraft = widgets.map((widget) => ({ ...widget }));
      widgetSaveState = "saved";
      widgetAnnouncement = "Preferencias guardadas.";
      renderAll();
      if (exitAfterSave) {
        customizingWidgets = false;
        widgetDraft = null;
        widgetSaveState = "idle";
        widgetAnnouncement = "";
        renderAll();
        editBtn.focus();
        showToast("Preferencias guardadas", "success");
      }
    } catch (error) {
      widgetSaveState = "error";
      widgetSaveError = error.message || "No se pudieron guardar las preferencias.";
      widgetAnnouncement = "";
      renderAll();
      const saveBtn = container.querySelector("#home-widget-save");
      if (saveBtn) saveBtn.focus();
    }
  }

  function toggleCustomization() {
    if (!customizingWidgets) {
      beginCustomization();
      return;
    }
    saveWidgetPreferences(true);
  }

  editBtn.addEventListener("click", toggleCustomization, { signal: eventController.signal });

  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  // Escapa también comillas: los valores usados en atributos (aria-label,
  // title) deben seguir siendo seguros con nombres de usuario.
  const amp = String.fromCharCode(38);
  return div.innerHTML
    .replace(/"/g, `${amp}quot;`)
    .replace(/'/g, `${amp}#39;`);
}
