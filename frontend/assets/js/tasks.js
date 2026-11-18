// Life OS — vista de Tareas

export async function renderTasksView(container, apiBase) {
  let projects = [];

  container.innerHTML = `
    <div class="form-row" style="margin-bottom: 16px;">
      <div class="form-group" style="flex: 2; min-width: 260px;">
        <label>T&iacute;tulo</label>
        <input type="text" id="task-title" placeholder="T&iacute;tulo de la tarea">
      </div>
      <div class="form-group" style="flex: 1; min-width: 180px;">
        <label>Proyecto (opcional)</label>
        <select id="task-project"><option value="">Ninguno</option></select>
      </div>
      <div class="form-group" style="flex: 1; min-width: 140px;">
        <label>Prioridad</label>
        <select id="task-priority">
          <option value="">Ninguna</option>
          <option value="low">Baja</option>
          <option value="normal">Normal</option>
          <option value="high">Alta</option>
        </select>
      </div>
      <div class="form-group" style="flex: 1; min-width: 140px;">
        <label>Vencimiento</label>
        <input type="date" id="task-due">
      </div>
      <button class="btn btn--primary" id="task-create-btn">Crear</button>
    </div>

    <div style="margin-bottom: 12px; display:flex; gap: 8px; flex-wrap: wrap;">
      <label style="font-size:0.9375rem; color:var(--text-secondary);">Filtrar:</label>
      <select id="task-filter-status" style="padding:6px 10px; border:1px solid var(--border); border-radius:var(--radius); background:var(--surface);">
        <option value="">Todos los estados</option>
        <option value="pending">Pendientes</option>
        <option value="completed">Completadas</option>
      </select>
      <select id="task-filter-project" style="padding:6px 10px; border:1px solid var(--border); border-radius:var(--radius); background:var(--surface);">
        <option value="">Todos los proyectos</option>
      </select>
    </div>

    <h2 style="margin-top: 0;">Tareas</h2>
    <div id="tasks-list" class="empty-state">Cargando tareas...</div>
  `;

  const listEl = container.querySelector("#tasks-list");
  const titleInput = container.querySelector("#task-title");
  const projectSelect = container.querySelector("#task-project");
  const prioritySelect = container.querySelector("#task-priority");
  const dueInput = container.querySelector("#task-due");
  const createBtn = container.querySelector("#task-create-btn");
  const filterStatus = container.querySelector("#task-filter-status");
  const filterProject = container.querySelector("#task-filter-project");

  async function loadProjects() {
    const res = await fetch(`${apiBase}/projects`);
    projects = await res.json();

    projectSelect.innerHTML = '<option value="">Ninguno</option>';
    filterProject.innerHTML = '<option value="">Todos los proyectos</option>';
    projects.forEach(p => {
      const opt1 = document.createElement("option");
      opt1.value = p.id;
      opt1.textContent = p.name;
      projectSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = p.id;
      opt2.textContent = p.name;
      filterProject.appendChild(opt2);
    });
  }

  async function load() {
    const params = new URLSearchParams();
    if (filterStatus.value) params.set("status", filterStatus.value);
    if (filterProject.value) params.set("project_id", filterProject.value);

    const res = await fetch(`${apiBase}/tasks?${params}`);
    const tasks = await res.json();

    if (tasks.length === 0) {
      listEl.innerHTML = `<p class="empty-state">No hay tareas que coincidan con el filtro.</p>`;
      return;
    }

    const projectMap = {};
    projects.forEach(p => { projectMap[p.id] = p.name; });

    listEl.innerHTML = `
      <table class="table">
        <thead>
          <tr>
            <th>T&iacute;tulo</th>
            <th>Proyecto</th>
            <th>Estado</th>
            <th>Prioridad</th>
            <th>Vencimiento</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${tasks.map(t => `
            <tr id="task-row-${t.id}">
              <td><strong>${escapeHtml(t.title)}</strong></td>
              <td>${escapeHtml(projectMap[t.project_id] || "&mdash;")}</td>
              <td><span class="badge badge--status">${t.status}</span></td>
              <td>${t.priority ? `<span class="badge badge--priority-${t.priority}">${t.priority}</span>` : "&mdash;"}</td>
              <td>${t.due_date || "&mdash;"}</td>
              <td>
                <div class="btn-group">
                  <button class="btn btn--secondary btn--sm" onclick="appTasks.toggleStatus('${t.id}', '${t.status}')">
                    ${t.status === "pending" ? "Completar" : "Reabrir"}
                  </button>
                  <button class="btn btn--danger btn--sm" onclick="appTasks.deleteTask('${t.id}', '${escapeHtml(t.title)}')">
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  }

  createBtn.addEventListener("click", async () => {
    const title = titleInput.value.trim();
    if (!title) return;

    const body = { title };
    const projectId = projectSelect.value;
    if (projectId) body.project_id = projectId;
    const priority = prioritySelect.value;
    if (priority) body.priority = priority;
    const due = dueInput.value;
    if (due) body.due_date = due;

    const res = await fetch(`${apiBase}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      titleInput.value = "";
      projectSelect.value = "";
      prioritySelect.value = "";
      dueInput.value = "";
      await load();
    } else {
      const err = await res.json();
      alert(err.detail || "Error al crear tarea");
    }
  });

  filterStatus.addEventListener("change", load);
  filterProject.addEventListener("change", load);

  window.appTasks = {
    async toggleStatus(id, currentStatus) {
      const endpoint = currentStatus === "pending" ? "/complete" : "/reopen";
      const res = await fetch(`${apiBase}/tasks/${id}${endpoint}`, {
        method: "POST",
      });

      if (res.ok) await load();
      else {
        const err = await res.json();
        alert(err.detail || "Error al cambiar estado");
      }
    },

    async deleteTask(id, title) {
      if (!confirm(`¿Eliminar la tarea "${title}"?`)) return;

      const res = await fetch(`${apiBase}/tasks/${id}`, {
        method: "DELETE",
      });

      if (res.ok || res.status === 204) {
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error al eliminar tarea");
      }
    },
  };

  await loadProjects();
  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}