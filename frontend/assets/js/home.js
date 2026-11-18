// Life OS — vista Home (dashboard configurable)

export async function renderHomeView(container, apiBase) {
  container.innerHTML = `
    <h1>Home</h1>
    <p class="subtitle">Resumen de tu día y accesos rápidos</p>

    <div id="dashboard-summary" class="summary-cards" style="margin-bottom: 24px;"></div>

    <div id="dashboard-controls" class="card" style="margin-bottom: 24px; display:none;">
      <h3>Configurar widgets</h3>
      <p class="subtitle">Selecciona qué widgets mostrar y su orden.</p>
      <div id="widgets-config" style="margin-top: 12px;"></div>
      <button class="btn btn--primary" id="widgets-save-btn" style="margin-top: 12px;">Guardar preferencias</button>
      <button class="btn btn--secondary" id="widgets-cancel-btn" style="margin-top: 12px; margin-left: 8px;">Cancelar</button>
    </div>

    <div id="dashboard-grid" class="dashboard-grid"></div>

    <button class="btn btn--secondary" id="widgets-edit-btn" style="margin-top: 16px;">Editar widgets</button>
  `;

  const summaryEl = container.querySelector("#dashboard-summary");
  const gridEl = container.querySelector("#dashboard-grid");
  const controlsEl = container.querySelector("#dashboard-controls");
  const configEl = container.querySelector("#widgets-config");
  const saveBtn = container.querySelector("#widgets-save-btn");
  const cancelBtn = container.querySelector("#widgets-cancel-btn");
  const editBtn = container.querySelector("#widgets-edit-btn");

  let widgets = [];
  let editing = false;

  async function load() {
    // Cargar resumen
    const sumRes = await fetch(`${apiBase}/dashboard/summary`);
    const summary = await sumRes.json();

    summaryEl.innerHTML = `
      <div class="summary-card">
        <div class="summary-value">${summary.tasks.pending}</div>
        <div class="summary-label">Tareas pendientes</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${summary.tasks.completed}</div>
        <div class="summary-label">Tareas completadas</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${summary.tasks.overdue}</div>
        <div class="summary-label">Tareas vencidas</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${summary.projects.active}</div>
        <div class="summary-label">Proyectos activos</div>
      </div>
    `;

    // Cargar widgets
    const wRes = await fetch(`${apiBase}/dashboard/widgets`);
    widgets = await wRes.json();
    renderWidgets();
    renderConfig();
  }

  function renderWidgets() {
    const visible = widgets.filter(w => w.is_visible).sort((a, b) => a.position - b.position);

    if (visible.length === 0) {
      gridEl.innerHTML = `<p class="empty-state">No hay widgets visibles. Activa algunos en la configuraci&oacute;n.</p>`;
      return;
    }

    gridEl.innerHTML = `
      <div class="widgets-grid">
        ${visible.map(w => renderWidget(w)).join("")}
      </div>
    `;

    // Cargar contenido de cada widget dinámicamente
    visible.forEach(w => loadWidgetContent(w));
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
      } else if (w.widget_id === "quick_add_note") {
        contentEl.innerHTML = renderQuickAddNote();
      }
    } catch (e) {
      contentEl.innerHTML = `<p class="empty-state">Error cargando contenido.</p>`;
    }
  }

  function renderUpcomingTasks(tasks) {
    if (tasks.length === 0) return `<p class="empty-state">No hay tareas pendientes.</p>`;
    const items = tasks.slice(0, 5).map(t => `
      <div class="task-item">
        <strong>${escapeHtml(t.title)}</strong>
        ${t.due_date ? `<span class="badge badge--status">Vence: ${t.due_date}</span>` : ""}
        ${t.priority ? `<span class="badge badge--priority-${t.priority}">${t.priority}</span>` : ""}
      </div>
    `).join("");
    return `<div class="widget-list">${items}${tasks.length > 5 ? `<p style="font-size:0.875rem;color:var(--text-secondary);">+ ${tasks.length - 5} m&aacute;s</p>` : ""}</div>`;
  }

  function renderActiveProjects(projects) {
    if (projects.length === 0) return `<p class="empty-state">No hay proyectos activos.</p>`;
    const items = projects.slice(0, 5).map(p => `
      <div class="task-item">
        <strong>${escapeHtml(p.name)}</strong>
        <span class="badge badge--status">${p.status}</span>
      </div>
    `).join("");
    return `<div class="widget-list">${items}${projects.length > 5 ? `<p style="font-size:0.875rem;color:var(--text-secondary);">+ ${projects.length - 5} m&aacute;s</p>` : ""}</div>`;
  }

  function renderQuickAddTask() {
    return `
      <div class="quick-add">
        <input type="text" id="quick-task-title" placeholder="T&iacute;tulo de la nueva tarea">
        <button class="btn btn--primary btn--sm" id="quick-task-create">Crear tarea</button>
      </div>
    `;
  }

  function renderQuickAddNote() {
    return `
      <div class="quick-add">
        <input type="text" id="quick-note-title" placeholder="T&iacute;tulo de la nueva nota">
        <button class="btn btn--primary btn--sm" id="quick-note-create">Crear nota</button>
      </div>
    `;
  }

  function renderConfig() {
    const sorted = [...widgets].sort((a, b) => a.position - b.position);
    configEl.innerHTML = sorted.map((w, idx) => `
      <div class="widget-config-row" data-widget="${w.widget_id}">
        <label>
          <input type="checkbox" ${w.is_visible ? "checked" : ""}>
          ${w.label}
        </label>
        <div class="widget-config-controls">
          <button class="btn btn--secondary btn--sm" onclick="appHome.moveWidget('${w.widget_id}', -1)" ${idx === 0 ? "disabled" : ""}>&uarr;</button>
          <button class="btn btn--secondary btn--sm" onclick="appHome.moveWidget('${w.widget_id}', 1)" ${idx === sorted.length - 1 ? "disabled" : ""}>&darr;</button>
        </div>
      </div>
    `).join("");
  }

  // Event listeners
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
      editing = false;
      controlsEl.style.display = "none";
      await load();
    } else {
      const err = await res.json();
      alert(err.detail || "Error guardando preferencias");
    }
  });

  cancelBtn.addEventListener("click", () => {
    editing = false;
    controlsEl.style.display = "none";
  });

  editBtn.addEventListener("click", () => {
    editing = true;
    controlsEl.style.display = "block";
    renderConfig();
  });

  // Quick add task
  container.addEventListener("click", async (e) => {
    if (e.target && e.target.id === "quick-task-create") {
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
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error creando tarea");
      }
    }
    if (e.target && e.target.id === "quick-note-create") {
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
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error creando nota");
      }
    }
  });

  window.appHome = {
    moveWidget(widgetId, direction) {
      const idx = widgets.findIndex(w => w.widget_id === widgetId);
      if (idx === -1) return;
      const targetIdx = idx + direction;
      if (targetIdx < 0 || targetIdx >= widgets.length) return;
      [widgets[idx], widgets[targetIdx]] = [widgets[targetIdx], widgets[idx]];
      widgets[idx].position = idx;
      widgets[targetIdx].position = targetIdx;
      renderConfig();
    },
  };

  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}