// Life OS — vista de Tareas (Fase 8C)
//
// Listado, filtros, prioridades, vencimientos, formularios y estados.
// Usa los componentes compartidos de 8A.

import { showToast, showConfirm } from "./app.js";

export async function renderTasksView(container, apiBase) {
  let projects = [];

  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Tareas</h1>
        <p class="subtitle">Gesti&oacute;n de tus tareas y pendientes</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3 style="margin-top:0;">Nueva tarea</h3>
      <div class="form-row" style="margin-top:12px;">
        <div class="form-group" style="flex:2; min-width:260px;">
          <label for="task-title">T&iacute;tulo</label>
          <input type="text" id="task-title" placeholder="T&iacute;tulo de la tarea" required>
        </div>
        <div class="form-group" style="flex:1; min-width:180px;">
          <label for="task-project">Proyecto (opcional)</label>
          <select id="task-project"><option value="">Ninguno</option></select>
        </div>
        <div class="form-group" style="flex:1; min-width:140px;">
          <label for="task-priority">Prioridad</label>
          <select id="task-priority">
            <option value="">Ninguna</option>
            <option value="low">Baja</option>
            <option value="normal">Normal</option>
            <option value="high">Alta</option>
          </select>
        </div>
        <div class="form-group" style="flex:1; min-width:140px;">
          <label for="task-due">Vencimiento</label>
          <input type="date" id="task-due">
        </div>
        <div class="form-group" style="flex:0; min-width:auto; align-self:flex-end;">
          <button class="btn btn--primary" id="task-create-btn">Crear tarea</button>
        </div>
      </div>
    </div>

    <div class="filters-bar" style="margin-bottom: 16px;">
      <span class="text-secondary" style="font-size:0.9375rem;">Filtrar:</span>
      <select id="task-filter-status" aria-label="Filtrar por estado">
        <option value="">Todos los estados</option>
        <option value="pending">Pendientes</option>
        <option value="completed">Completadas</option>
      </select>
      <select id="task-filter-project" aria-label="Filtrar por proyecto">
        <option value="">Todos los proyectos</option>
      </select>
    </div>

    <div id="tasks-list" class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando tareas&hellip;</p>
    </div>
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
    try {
      const res = await fetch(`${apiBase}/projects`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
    } catch (error) {
      // Silenciar: los proyectos se cargan en segundo plano
    }
  }

  let currentTasks = [];

  async function load() {
    listEl.innerHTML = `
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando&hellip;</p>
    `;
    try {
      const params = new URLSearchParams();
      if (filterStatus.value) params.set("status", filterStatus.value);
      if (filterProject.value) params.set("project_id", filterProject.value);

      const res = await fetch(`${apiBase}/tasks?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const tasks = await res.json();
      currentTasks = tasks;

      if (tasks.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state__icon" aria-hidden="true">&#10003;</div>
          <p class="empty-state__title">No hay tareas</p>
          <p class="empty-state__text">No hay tareas que coincidan con el filtro actual.</p>
        `;
        return;
      }

      const projectMap = {};
      projects.forEach(p => { projectMap[p.id] = p.name; });

      listEl.innerHTML = `
        <div class="table-wrap">
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
                <td>${projectMap[t.project_id] ? escapeHtml(projectMap[t.project_id]) : "&mdash;"}</td>
                <td><span class="badge badge--${t.status === "completed" ? "success" : "status"}">${t.status === "completed" ? "Completada" : "Pendiente"}</span></td>
                <td>${t.priority ? `<span class="badge badge--priority-${t.priority}">${priorityLabel(t.priority)}</span>` : "&mdash;"}</td>
                <td>${t.due_date ? `<span class="${isOverdue(t.due_date, t.status) ? "text-danger" : ""}">${t.due_date}</span>` : "&mdash;"}</td>
                <td>
                  <div class="btn-group">
                    <button class="btn btn--secondary btn--sm" onclick="appTasks.toggleStatus('${t.id}', '${t.status}')">
                      ${t.status === "pending" ? "Completar" : "Reabrir"}
                    </button>
                    <button class="btn btn--danger btn--sm" onclick="appTasks.deleteTask('${t.id}')">
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
        </div>
      `;
    } catch (error) {
      listEl.innerHTML = `
        <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
        <p class="empty-state__title">Error al cargar</p>
        <p class="empty-state__text">No se pudieron cargar las tareas. Verifica que el servicio est&eacute; activo.</p>
        <button class="btn btn--secondary" onclick="appTasks.reload()">Reintentar</button>
      `;
    }
  }

  function priorityLabel(priority) {
    if (priority === "high") return "Alta";
    if (priority === "normal") return "Normal";
    if (priority === "low") return "Baja";
    return priority;
  }

  function isOverdue(dueDate, status) {
    if (status === "completed") return false;
    const today = new Date().toISOString().slice(0, 10);
    return dueDate < today;
  }

  createBtn.addEventListener("click", async () => {
    const title = titleInput.value.trim();
    if (!title) {
      showToast("El título de la tarea no puede estar vacío", "warning");
      titleInput.focus();
      return;
    }

    const body = { title };
    const projectId = projectSelect.value;
    if (projectId) body.project_id = projectId;
    const priority = prioritySelect.value;
    if (priority) body.priority = priority;
    const due = dueInput.value;
    if (due) body.due_date = due;

    createBtn.disabled = true;
    createBtn.textContent = "Creando…";
    try {
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
        showToast("Tarea creada", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error al crear tarea", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    } finally {
      createBtn.disabled = false;
      createBtn.textContent = "Crear tarea";
    }
  });

  filterStatus.addEventListener("change", load);
  filterProject.addEventListener("change", load);

  window.appTasks = {
    async toggleStatus(id, currentStatus) {
      try {
        const endpoint = currentStatus === "pending" ? "/complete" : "/reopen";
        const res = await fetch(`${apiBase}/tasks/${id}${endpoint}`, {
          method: "POST",
        });

        if (res.ok) {
          showToast("Estado actualizado", "success");
          await load();
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al cambiar estado", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    },

    async deleteTask(id) {
      const task = currentTasks.find(t => t.id === id);
      const title = task ? task.title : "";
      const confirmed = await showConfirm({
        title: "Eliminar tarea",
        text: `¿Eliminar la tarea "${title}"?`,
        confirmLabel: "Eliminar",
        danger: true,
      });
      if (!confirmed) return;

      try {
        const res = await fetch(`${apiBase}/tasks/${id}`, {
          method: "DELETE",
        });

        if (res.ok || res.status === 204) {
          showToast("Tarea eliminada", "success");
          await load();
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al eliminar tarea", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    },

    reload() {
      load();
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
