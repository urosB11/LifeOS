// Life OS — vista Home (dashboard configurable) — Fase 8B
//
// Centro de control adaptativo: resumen con métricas, grilla responsive de
// widgets y configuración en modal. Persistencia de preferencias sin cambios
// en el backend.

import { showToast } from "./app.js";
import {
  HABIT_DAY_SYMBOLS,
  deriveHabitDayState,
  formatLongDate,
  habitLegendHtml,
  habitStateLabel,
  openHabitEntryEditor,
} from "./habit-entry.js";

export async function renderHomeView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Home</h1>
        <p class="subtitle">Resumen de tu día y accesos r&aacute;pidos</p>
      </div>
      <button class="btn btn--secondary" id="widgets-edit-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;">
          <circle cx="8" cy="8" r="2"/>
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.3 3.3l1.4 1.4M11.3 11.3l1.4 1.4M12.7 3.3l-1.4 1.4M4.7 11.3l-1.4 1.4"/>
        </svg>
        Configurar widgets
      </button>
    </div>

    <div id="dashboard-summary" class="summary-cards" style="margin-bottom: 24px;"></div>

    <div id="dashboard-grid" class="dashboard-grid"></div>
  `;

  const summaryEl = container.querySelector("#dashboard-summary");
  const gridEl = container.querySelector("#dashboard-grid");
  const editBtn = container.querySelector("#widgets-edit-btn");

  let widgets = [];
  // Últimos datos del resumen: permiten actualizar "Hábitos hoy" tras
  // registrar un hábito sin recargar todo el dashboard (HAB-002).
  let lastSummary = null;
  let lastNotesCount = 0;
  // Última semana cargada: alimenta el editor de celdas del widget.
  let currentWeek = null;

  // --- Carga de datos -------------------------------------------------------
  async function load() {
    try {
      // Cargar resumen y widgets en paralelo
      const [sumRes, wRes] = await Promise.all([
        fetch(`${apiBase}/dashboard/summary`),
        fetch(`${apiBase}/dashboard/widgets`),
      ]);

      if (!sumRes.ok) throw new Error(`HTTP ${sumRes.status}`);
      const summary = await sumRes.json();
      lastSummary = summary;

      // Métricas adicionales desde endpoints existentes (sin duplicar módulos)
      let notesCount = 0;
      let habitsToday = { total: 0, completed: 0 };
      try {
        const [notesRes, habitsRes] = await Promise.all([
          fetch(`${apiBase}/notes`),
          fetch(`${apiBase}/habits/today`),
        ]);
        if (notesRes.ok) {
          const notes = await notesRes.json();
          notesCount = Array.isArray(notes) ? notes.length : 0;
        }
        if (habitsRes.ok) {
          const items = await habitsRes.json();
          habitsToday.total = items.length;
          habitsToday.completed = items.filter(
            (i) => i.entry && i.entry.status === "completed"
          ).length;
        }
      } catch (_) {
        // Métricas adicionales son best-effort
      }

      lastNotesCount = notesCount;
      renderSummary(summary, notesCount, habitsToday);

      if (!wRes.ok) throw new Error(`HTTP ${wRes.status}`);
      widgets = await wRes.json();
      renderWidgets();
    } catch (error) {
      summaryEl.innerHTML = "";
      gridEl.innerHTML = `
        <div class="widget-card">
          <p class="empty-state">No se pudo cargar el dashboard. Verifica que el servicio est&eacute; activo.</p>
        </div>
      `;
    }
  }

  // --- Resumen --------------------------------------------------------------
  function renderSummary(summary, notesCount, habitsToday) {
    const overdueClass = summary.tasks.overdue > 0 ? "text-danger" : "";
    summaryEl.innerHTML = `
      <div class="summary-card">
        <div class="summary-value">${summary.tasks.pending}</div>
        <div class="summary-label">Tareas pendientes</div>
      </div>
      <div class="summary-card">
        <div class="summary-value text-success">${summary.tasks.completed}</div>
        <div class="summary-label">Tareas completadas</div>
      </div>
      <div class="summary-card">
        <div class="summary-value ${overdueClass}">${summary.tasks.overdue}</div>
        <div class="summary-label">Tareas vencidas</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${summary.projects.active}</div>
        <div class="summary-label">Proyectos activos</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${notesCount}</div>
        <div class="summary-label">Notas</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${habitsToday.completed}/${habitsToday.total}</div>
        <div class="summary-label">H&aacute;bitos hoy</div>
      </div>
    `;
  }

  // --- Widgets --------------------------------------------------------------
  function renderWidgets() {
    const visible = widgets.filter((w) => w.is_visible).sort((a, b) => a.position - b.position);

    if (visible.length === 0) {
      gridEl.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#9881;</div>
          <p class="empty-state__title">No hay widgets visibles</p>
          <p class="empty-state__text">Activa algunos en la configuraci&oacute;n.</p>
          <button class="btn btn--primary" id="widgets-empty-config">Configurar widgets</button>
        </div>
      `;
      const emptyBtn = gridEl.querySelector("#widgets-empty-config");
      if (emptyBtn) emptyBtn.addEventListener("click", openConfig);
      return;
    }

    gridEl.innerHTML = `
      <div class="widgets-grid">
        ${visible.map((w) => renderWidget(w)).join("")}
      </div>
    `;

    visible.forEach((w) => loadWidgetContent(w));
  }

  function renderWidget(w) {
    return `
      <div class="widget-card" id="widget-${w.widget_id}">
        <div class="widget-header">
          <span class="widget-title">${w.label}</span>
          <span class="widget-position">${w.position + 1}</span>
        </div>
        <div class="widget-content" id="widget-content-${w.widget_id}">
          Cargando&hellip;
        </div>
      </div>
    `;
  }

  async function loadWidgetContent(w) {
    const contentEl = container.querySelector(`#widget-content-${w.widget_id}`);
    try {
      if (w.widget_id === "upcoming_tasks") {
        const res = await fetch(`${apiBase}/tasks?status=pending`);
        const tasks = await res.json();
        contentEl.innerHTML = renderUpcomingTasks(tasks);
      } else if (w.widget_id === "active_projects") {
        const res = await fetch(`${apiBase}/projects?status=active`);
        const projects = await res.json();
        contentEl.innerHTML = renderActiveProjects(projects);
      } else if (w.widget_id === "quick_add_task") {
        contentEl.innerHTML = renderQuickAddTask();
        bindQuickAddTask();
      } else if (w.widget_id === "quick_add_note") {
        contentEl.innerHTML = renderQuickAddNote();
        bindQuickAddNote();
      } else if (w.widget_id === "habits_today") {
        const res = await fetch(`${apiBase}/habits/today`);
        const items = await res.json();
        contentEl.innerHTML = renderHabitsToday(items);
      } else if (w.widget_id === "habits_week") {
        const res = await fetch(`${apiBase}/habits/week`);
        const week = await res.json();
        contentEl.innerHTML = renderHabitsWeek(week);
      }
    } catch (e) {
      contentEl.innerHTML = `<p class="empty-state">Error cargando contenido.</p>`;
    }
  }

  // --- Renderers de widgets -------------------------------------------------
  function renderUpcomingTasks(tasks) {
    if (tasks.length === 0) return `<p class="empty-state">No hay tareas pendientes.</p>`;
    const items = tasks
      .slice(0, 5)
      .map(
        (t) => `
      <div class="task-item">
        <strong>${escapeHtml(t.title)}</strong>
        ${t.due_date ? `<span class="badge badge--status">Vence: ${t.due_date}</span>` : ""}
        ${t.priority ? `<span class="badge badge--priority-${t.priority}">${t.priority}</span>` : ""}
      </div>
    `
      )
      .join("");
    return `<div class="widget-list">${items}${tasks.length > 5 ? `<p class="text-secondary" style="font-size:0.875rem;">+ ${tasks.length - 5} m&aacute;s</p>` : ""}</div>`;
  }

  function renderActiveProjects(projects) {
    if (projects.length === 0) return `<p class="empty-state">No hay proyectos activos.</p>`;
    const items = projects
      .slice(0, 5)
      .map(
        (p) => `
      <div class="task-item">
        <strong>${escapeHtml(p.name)}</strong>
        <span class="badge badge--status">${p.status}</span>
      </div>
    `
      )
      .join("");
    return `<div class="widget-list">${items}${projects.length > 5 ? `<p class="text-secondary" style="font-size:0.875rem;">+ ${projects.length - 5} m&aacute;s</p>` : ""}</div>`;
  }

  function renderQuickAddTask() {
    return `
      <div class="quick-add">
        <input type="text" id="quick-task-title" aria-label="T&iacute;tulo de la nueva tarea" placeholder="T&iacute;tulo de la nueva tarea">
        <button class="btn btn--primary btn--sm" id="quick-task-create">Crear</button>
      </div>
    `;
  }

  function renderQuickAddNote() {
    return `
      <div class="quick-add">
        <input type="text" id="quick-note-title" aria-label="T&iacute;tulo de la nueva nota" placeholder="T&iacute;tulo de la nueva nota">
        <button class="btn btn--primary btn--sm" id="quick-note-create">Crear</button>
      </div>
    `;
  }

  function renderHabitsToday(items) {
    const link = `<p style="margin-top:10px;"><a href="#/habits">Ver todos los h&aacute;bitos &rarr;</a></p>`;
    if (!items.length) {
      return `<p class="empty-state">No hay h&aacute;bitos programados hoy.</p>${link}`;
    }
    const badge = (entry) => {
      if (!entry) return `<span class="badge habit-badge--partial">Pendiente</span>`;
      if (entry.status === "completed") return `<span class="badge habit-badge--done">Cumplido</span>`;
      if (entry.status === "skipped") return `<span class="badge habit-badge--skipped">Omitido</span>`;
      return `<span class="badge habit-badge--partial">Registrado</span>`;
    };
    const rows = items
      .slice(0, 6)
      .map(
        (item) => `
      <div class="task-item">
        <strong>${escapeHtml(item.habit.name)}</strong>
        ${badge(item.entry)}
      </div>
    `
      )
      .join("");
    const more = items.length > 6
      ? `<p class="text-secondary" style="font-size:0.875rem;">+ ${items.length - 6} m&aacute;s</p>`
      : "";
    return `<div class="widget-list">${rows}${more}</div>${link}`;
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
    const link = `<p style="margin-top:10px;"><a href="#/habits">Abrir h&aacute;bitos &rarr;</a></p>`;
    if (!week.items.length) {
      return `<p class="empty-state">No hay h&aacute;bitos activos.</p>${link}`;
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

  // Refresca semana, widget de hoy y el resumen afectado tras editar un
  // registro, sin recargar toda la aplicación (HAB-002 §1).
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
    const weekEl = container.querySelector("#widget-content-habits_week");
    if (weekEl) weekEl.innerHTML = renderHabitsWeek(week);
    const todayEl = container.querySelector("#widget-content-habits_today");
    if (todayEl) todayEl.innerHTML = renderHabitsToday(items);
    if (lastSummary) {
      renderSummary(lastSummary, lastNotesCount, {
        total: items.length,
        completed: items.filter(
          (i) => i.entry && i.entry.status === "completed"
        ).length,
      });
    }
  }

  // --- Quick add handlers ---------------------------------------------------
  function bindQuickAddTask() {
    const btn = container.querySelector("#quick-task-create");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      const input = container.querySelector("#quick-task-title");
      const title = input.value.trim();
      if (!title) return;
      const res = await fetch(`${apiBase}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        input.value = "";
        showToast("Tarea creada", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error creando tarea", "error");
      }
    });
  }

  function bindQuickAddNote() {
    const btn = container.querySelector("#quick-note-create");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      const input = container.querySelector("#quick-note-title");
      const title = input.value.trim();
      if (!title) return;
      const res = await fetch(`${apiBase}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content: "" }),
      });
      if (res.ok) {
        input.value = "";
        showToast("Nota creada", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error creando nota", "error");
      }
    });
  }

  // --- Configuración de widgets (modal) -------------------------------------
  function openConfig() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="config-title">
        <h2 class="modal__title" id="config-title">Configurar widgets</h2>
        <p class="modal__text">Selecciona qu&eacute; widgets mostrar y su orden.</p>
        <div id="widgets-config" style="margin-bottom: 16px;"></div>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="widgets-cancel-btn">Cancelar</button>
          <button class="btn btn--primary" id="widgets-save-btn">Guardar preferencias</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const configEl = overlay.querySelector("#widgets-config");
    const saveBtn = overlay.querySelector("#widgets-save-btn");
    const cancelBtn = overlay.querySelector("#widgets-cancel-btn");

    // Renderizar filas de configuración
    const sorted = [...widgets].sort((a, b) => a.position - b.position);
    configEl.innerHTML = sorted
      .map(
        (w, idx) => `
      <div class="widget-config-row" data-widget="${w.widget_id}">
        <label>
          <input type="checkbox" ${w.is_visible ? "checked" : ""}>
          ${w.label}
        </label>
        <div class="widget-config-controls">
          <button class="btn btn--secondary btn--sm" data-move="up" data-idx="${idx}" ${idx === 0 ? "disabled" : ""}>&uarr;</button>
          <button class="btn btn--secondary btn--sm" data-move="down" data-idx="${idx}" ${idx === sorted.length - 1 ? "disabled" : ""}>&darr;</button>
        </div>
      </div>
    `
      )
      .join("");

    // Mover widgets arriba/abajo
    configEl.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-move]");
      if (!btn) return;
      const idx = parseInt(btn.dataset.idx, 10);
      const dir = btn.dataset.move === "up" ? -1 : 1;
      const targetIdx = idx + dir;
      if (targetIdx < 0 || targetIdx >= sorted.length) return;
      [sorted[idx], sorted[targetIdx]] = [sorted[targetIdx], sorted[idx]];
      // Re-render
      configEl.innerHTML = sorted
        .map(
          (w, i) => `
        <div class="widget-config-row" data-widget="${w.widget_id}">
          <label>
            <input type="checkbox" ${w.is_visible ? "checked" : ""}>
            ${w.label}
          </label>
          <div class="widget-config-controls">
            <button class="btn btn--secondary btn--sm" data-move="up" data-idx="${i}" ${i === 0 ? "disabled" : ""}>&uarr;</button>
            <button class="btn btn--secondary btn--sm" data-move="down" data-idx="${i}" ${i === sorted.length - 1 ? "disabled" : ""}>&darr;</button>
          </div>
        </div>
      `
        )
        .join("");
    });

    // Guardar
    saveBtn.addEventListener("click", async () => {
      const prefs = [];
      const rows = configEl.querySelectorAll(".widget-config-row");
      rows.forEach((row, idx) => {
        const widgetId = row.getAttribute("data-widget");
        const checkbox = row.querySelector("input[type=checkbox]");
        prefs.push({
          widget_id: widgetId,
          is_visible: checkbox.checked,
          position: idx,
        });
      });

      const res = await fetch(`${apiBase}/dashboard/widgets`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });

      if (res.ok) {
        overlay.remove();
        showToast("Preferencias guardadas", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error guardando preferencias", "error");
      }
    });

    // Cancelar
    cancelBtn.addEventListener("click", () => overlay.remove());
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    // Escape para cerrar
    const onKey = (e) => {
      if (e.key === "Escape") {
        overlay.remove();
        document.removeEventListener("keydown", onKey);
      }
    };
    document.addEventListener("keydown", onKey);

    // Focus en el primer checkbox
    const firstCheckbox = configEl.querySelector("input[type=checkbox]");
    if (firstCheckbox) firstCheckbox.focus();
  }

  editBtn.addEventListener("click", openConfig);

  // Edición de celdas de la semana (delegación: el contenido se re-renderiza).
  gridEl.addEventListener("click", (event) => {
    const cell = event.target.closest('[data-action="wk-edit"]');
    if (!cell || !gridEl.contains(cell)) return;
    if (!currentWeek) return;
    const item = currentWeek.items.find((i) => i.habit.id === cell.dataset.id);
    if (!item) return;
    const day = item.days.find((d) => d.date === cell.dataset.date);
    if (!day) return;
    openHabitEntryEditor({
      apiBase,
      habit: item.habit,
      date: day.date,
      entry: day.entry_status
        ? { status: day.entry_status, value: day.entry_value }
        : null,
      today: currentWeek.today,
      onSaved: refreshHabitsViews,
      getFallbackFocus: () => container.querySelector("#widget-habits_week"),
      returnFocusTo: cell,
    });
  });

  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  // Escapa también comillas: los valores usados en atributos (aria-label,
  // title) deben seguir siendo seguros con nombres de usuario.
  return div.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
