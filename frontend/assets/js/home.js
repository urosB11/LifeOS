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
    try {
      // Cargar resumen
      const sumRes = await fetch(`${apiBase}/dashboard/summary`);
      if (!sumRes.ok) throw new Error(`HTTP ${sumRes.status}`);
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
      if (!wRes.ok) throw new Error(`HTTP ${wRes.status}`);
      widgets = await wRes.json();
      renderWidgets();
      renderConfig();
    } catch (error) {
      summaryEl.innerHTML = "";
      gridEl.innerHTML = `
        <div class="widget-card">
          <p class="empty-state">No se pudo cargar el dashboard. Verifica que el servicio est&eacute; activo.</p>
        </div>
      `;
    }
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
        <input type="text" id="quick-task-title" aria-label="T&iacute;tulo de la nueva tarea" placeholder="T&iacute;tulo de la nueva tarea">
        <button class="btn btn--primary btn--sm" id="quick-task-create">Crear tarea</button>
      </div>
    `;
  }

  function renderQuickAddNote() {
    return `
      <div class="quick-add">
        <input type="text" id="quick-note-title" aria-label="T&iacute;tulo de la nueva nota" placeholder="T&iacute;tulo de la nueva nota">
        <button class="btn btn--primary btn--sm" id="quick-note-create">Crear nota</button>
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
    const rows = items.slice(0, 6).map((item) => `
      <div class="task-item">
        <strong>${escapeHtml(item.habit.name)}</strong>
        ${badge(item.entry)}
      </div>
    `).join("");
    const more = items.length > 6
      ? `<p style="font-size:0.875rem;color:var(--text-secondary);">+ ${items.length - 6} m&aacute;s</p>`
      : "";
    return `<div class="widget-list">${rows}${more}</div>${link}`;
  }

  function weekCell(day, today) {
    if (!day.scheduled) {
      return `<span class="wk-cell wk-cell--off" title="No programado" aria-hidden="true">&middot;</span>`;
    }
    if (day.entry_status === "completed") {
      return `<span class="wk-cell wk-cell--done" title="Cumplido">&#10003;</span>`;
    }
    if (day.entry_status === "skipped") {
      return `<span class="wk-cell wk-cell--skip" title="Omitido">&ndash;</span>`;
    }
    if (day.entry_status === "pending") {
      return `<span class="wk-cell wk-cell--partial" title="Registrado sin completar">&bull;</span>`;
    }
    if (day.date > today) {
      return `<span class="wk-cell wk-cell--future" title="Programado, a&uacute;n sin registrar"></span>`;
    }
    return `<span class="wk-cell wk-cell--missed" title="Pendiente de registrar">&#9675;</span>`;
  }

  function renderHabitsWeek(week) {
    const link = `<p style="margin-top:10px;"><a href="#/habits">Abrir h&aacute;bitos &rarr;</a></p>`;
    if (!week.items.length) {
      return `<p class="empty-state">No hay h&aacute;bitos activos.</p>${link}`;
    }
    const head = week.items[0].days.map((d) => {
      const n = d.date.slice(8, 10);
      const names = ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"];
      const weekday = new Date(`${d.date}T00:00:00`).getDay();
      return `<th class="wk-th" scope="col" title="${d.date}">${names[weekday]} ${n}</th>`;
    }).join("");
    const rows = week.items.map((item) => `
      <tr>
        <th class="wk-name" scope="row">${escapeHtml(item.habit.name)}</th>
        ${item.days.map((d) => `<td class="wk-td">${weekCell(d, week.today)}</td>`).join("")}
      </tr>
    `).join("");
    return `
      <div class="table-wrap">
        <table class="wk-table">
          <thead><tr><th class="wk-name" scope="col"><span class="sr-only">H&aacute;bito</span></th>${head}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      <p class="wk-legend">&#10003; cumplido &middot; &bull; registrado sin completar &middot;
        &ndash; omitido &middot; &#9675; pendiente &middot; celda vac&iacute;a: programado a&uacute;n
        futuro &middot; gris: no programado</p>
      ${link}`;
  }

  // Los botones quick-add se vinculan a sus elementos recién creados. Antes
  // se adjuntaba un listener al contenedor persistente #app-view, que se
  // acumulaba con cada navegación a Home y creaba registros duplicados.
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
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error creando tarea");
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
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error creando nota");
      }
    });
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

  // Quick add: los handlers se vinculan en bindQuickAddTask/bindQuickAddNote
  // (uno por elemento creado); no agregar listeners al contenedor persistente.

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