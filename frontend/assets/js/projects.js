// Life OS — vista de Proyectos (Fase 8C + Rediseño Etapa 1)
//
// Listado con métricas de seguimiento, vista de detalle con tareas
// asociadas, edición y transiciones de estado. Usa componentes de 8A.

import { showToast, showConfirm } from "./app.js";

// --- Utilidades compartidas -------------------------------------------------

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// BUG-001: el borrador del formulario de tarea vive en estado para que un
// re-render (por error HTTP, error de red o recarga) no destruya lo escrito.
function emptyTaskDraft() {
  return { title: "", desc: "", priority: "", due: "" };
}

// Normaliza el detalle de error de la API (string, objeto o lista de 422).
function formatApiDetail(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && item.msg ? item.msg : null))
      .filter(Boolean);
    if (messages.length) return messages.join(" · ");
  }
  return fallback;
}

function statusBadgeClass(status) {
  if (status === "active") return "status";
  if (status === "completed") return "success";
  return "neutral";
}

function statusLabel(status) {
  if (status === "active") return "Activo";
  if (status === "completed") return "Completado";
  return "Archivado";
}

function projectActions(status) {
  if (status === "active") {
    return [["complete", "Completar"], ["archive", "Archivar"]];
  }
  if (status === "completed") {
    return [["reopen", "Reabrir"], ["archive", "Archivar"]];
  }
  return [["restore", "Restaurar"]];
}

function progressPercent(completed, total) {
  if (total === 0) return null;
  return Math.round((completed / total) * 100);
}

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function isOverdue(dueDate) {
  return dueDate < todayISO();
}

function isFutureDue(dueDate) {
  return dueDate >= todayISO();
}

// --- Vista de listado -------------------------------------------------------

export async function renderProjectsView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Proyectos</h1>
        <p class="subtitle">Gesti&oacute;n de tus proyectos activos</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3 style="margin-top:0;">Nuevo proyecto</h3>
      <div class="form-row" style="margin-top:12px;">
        <div class="form-group" style="flex:2; min-width:260px;">
          <label for="proj-name">Nombre</label>
          <input type="text" id="proj-name" placeholder="Nombre del proyecto" required>
        </div>
        <div class="form-group" style="flex:1; min-width:200px;">
          <label for="proj-desc">Descripci&oacute;n (opcional)</label>
          <input type="text" id="proj-desc" placeholder="Descripci&oacute;n">
        </div>
        <div class="form-group" style="flex:0; min-width:auto; align-self:flex-end;">
          <button class="btn btn--primary" id="proj-create-btn">Crear proyecto</button>
        </div>
      </div>
    </div>

    <div id="projects-list" class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#128194;</div>
      <p class="empty-state__title">Cargando proyectos&hellip;</p>
    </div>
  `;

  const listEl = container.querySelector("#projects-list");
  const nameInput = container.querySelector("#proj-name");
  const descInput = container.querySelector("#proj-desc");
  const createBtn = container.querySelector("#proj-create-btn");

  let currentProjects = [];

  async function load() {
    listEl.innerHTML = `
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando&hellip;</p>
    `;
    try {
      const res = await fetch(`${apiBase}/projects`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const projects = await res.json();
      currentProjects = projects;

      if (projects.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state__icon" aria-hidden="true">&#128194;</div>
          <p class="empty-state__title">A&uacute;n no hay proyectos</p>
          <p class="empty-state__text">Crea el primero con el formulario de arriba.</p>
        `;
        return;
      }

      listEl.innerHTML = `
        <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Estado</th>
              <th>Avance</th>
              <th>Vencidas</th>
              <th>Pr&oacute;ximo vencimiento</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${projects.map(p => {
              const pct = progressPercent(p.completed_count, p.task_count);
              const hasTasks = p.task_count > 0;
              return `
              <tr id="proj-row-${p.id}">
                <td>
                  <a href="#/projects/${p.id}" style="font-weight:600; color:var(--accent); text-decoration:none;">
                    ${escapeHtml(p.name)}
                  </a>
                </td>
                <td><span class="badge badge--${statusBadgeClass(p.status)}">${statusLabel(p.status)}</span></td>
                <td>
                  ${hasTasks ? `
                    <div style="display:flex; align-items:center; gap:8px;">
                      <span style="font-size:0.875rem; white-space:nowrap;">${p.completed_count}/${p.task_count}</span>
                      <div class="progress" style="min-width:60px; flex:1;" role="progressbar"
                           aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}"
                           aria-label="Avance de ${escapeHtml(p.name)}">
                        <div class="progress__bar" style="width:${pct}%"></div>
                      </div>
                      <span style="font-size:0.875rem; min-width:32px; text-align:right;">${pct}%</span>
                    </div>
                  ` : `<span class="text-secondary">Sin tareas</span>`}
                </td>
                <td>
                  ${p.overdue_count > 0
                    ? `<span class="text-danger" style="font-weight:600;">${p.overdue_count}</span>`
                    : `<span class="text-secondary">0</span>`}
                </td>
                <td>
                  ${p.next_due_date
                    ? (isFutureDue(p.next_due_date)
                      ? `<span>${p.next_due_date}</span>`
                      : `<span class="text-danger">${p.next_due_date}</span>`)
                    : `<span class="text-secondary">&mdash;</span>`}
                </td>
                <td>
                  <div class="btn-group">
                    ${projectActions(p.status).map(([action, label]) => `
                      <button class="btn btn--secondary btn--sm" onclick="appProjects.runAction('${p.id}', '${action}')">${label}</button>
                    `).join("")}
                  </div>
                  <button class="btn btn--danger btn--sm" style="margin-top:4px;" onclick="appProjects.deleteProject('${p.id}')">Eliminar</button>
                </td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
        </div>
      `;
    } catch (error) {
      listEl.innerHTML = `
        <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
        <p class="empty-state__title">Error al cargar</p>
        <p class="empty-state__text">No se pudieron cargar los proyectos. Verifica que el servicio est&eacute; activo.</p>
        <button class="btn btn--secondary" onclick="appProjects.reload()">Reintentar</button>
      `;
    }
  }

  createBtn.addEventListener("click", async () => {
    const name = nameInput.value.trim();
    if (!name) {
      showToast("El nombre del proyecto no puede estar vacío", "warning");
      nameInput.focus();
      return;
    }
    const body = { name };
    if (descInput.value.trim()) body.description = descInput.value.trim();

    createBtn.disabled = true;
    createBtn.textContent = "Creando…";
    try {
      const res = await fetch(`${apiBase}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        nameInput.value = "";
        descInput.value = "";
        showToast("Proyecto creado", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error al crear proyecto", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    } finally {
      createBtn.disabled = false;
      createBtn.textContent = "Crear proyecto";
    }
  });

  window.appProjects = {
    async runAction(id, action) {
      try {
        const res = await fetch(`${apiBase}/projects/${id}/${action}`, {
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

    async deleteProject(id) {
      const project = currentProjects.find(p => p.id === id);
      const name = project ? project.name : "";
      const confirmed = await showConfirm({
        title: "Eliminar proyecto",
        text: `&iquest;Eliminar el proyecto "${escapeHtml(name)}"? Esta acci&oacute;n lo elimina permanentemente (solo si no tiene tareas asociadas).`,
        confirmLabel: "Eliminar",
        danger: true,
      });
      if (!confirmed) return;

      try {
        const res = await fetch(`${apiBase}/projects/${id}`, {
          method: "DELETE",
        });

        if (res.ok || res.status === 204) {
          showToast("Proyecto eliminado", "success");
          await load();
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al eliminar proyecto", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    },

    reload() {
      load();
    },
  };

  await load();
}

// --- Vista de detalle -------------------------------------------------------

export async function renderProjectDetailView(container, apiBase, projectId) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <a href="#/projects" class="btn btn--secondary btn--sm" style="margin-bottom:8px; display:inline-flex;">
          &larr; Volver al listado
        </a>
        <h1 id="detail-title">Cargando&hellip;</h1>
        <p class="subtitle" id="detail-subtitle"></p>
      </div>
      <div class="btn-group" id="detail-header-actions"></div>
    </div>

    <div id="detail-content">
      <div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
        <p class="empty-state__title">Cargando proyecto&hellip;</p>
      </div>
    </div>
  `;

  const titleEl = container.querySelector("#detail-title");
  const subtitleEl = container.querySelector("#detail-subtitle");
  const headerActionsEl = container.querySelector("#detail-header-actions");
  const contentEl = container.querySelector("#detail-content");

  let project = null;
  let tasks = [];
  let taskFormOpen = false;
  let creatingTask = false;
  let taskError = "";
  // Campo al que debe ir el foco tras un error ("title" o "" = mensaje).
  let taskErrorField = "";
  // BUG-001: borrador persistente del formulario de tarea.
  let taskDraft = emptyTaskDraft();

  // Lee el formulario vivo antes de cualquier re-render para no perder lo escrito.
  function captureTaskDraft() {
    const titleEl = container.querySelector("#task-title");
    const descEl = container.querySelector("#task-desc");
    const priorityEl = container.querySelector("#task-priority");
    const dueEl = container.querySelector("#task-due");
    if (titleEl) taskDraft.title = titleEl.value;
    if (descEl) taskDraft.desc = descEl.value;
    if (priorityEl) taskDraft.priority = priorityEl.value;
    if (dueEl) taskDraft.due = dueEl.value;
  }

  // Tras un error: foco en el primer campo inválido o en el mensaje.
  function focusTaskError() {
    const target =
      taskErrorField === "title"
        ? container.querySelector("#task-title")
        : container.querySelector("#task-error");
    if (!target) return;
    if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
    target.focus();
  }

  async function load() {
    try {
      const res = await fetch(`${apiBase}/projects/${projectId}`);
      if (!res.ok) {
        if (res.status === 404) {
          titleEl.textContent = "Proyecto no encontrado";
          contentEl.innerHTML = `
            <div class="empty-state">
              <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
              <p class="empty-state__title">Proyecto no encontrado</p>
              <p class="empty-state__text">El proyecto que buscas no existe o fue eliminado.</p>
              <a href="#/projects" class="btn btn--secondary">Volver al listado</a>
            </div>
          `;
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      project = await res.json();

      titleEl.textContent = project.name;
      subtitleEl.textContent = `Estado: ${statusLabel(project.status)}`;
      headerActionsEl.innerHTML = `
        <button class="btn btn--secondary btn--sm" onclick="appProjectsDetail.editProject()">Editar</button>
      `;

      // Cargar tareas del proyecto
      try {
        const tasksRes = await fetch(`${apiBase}/tasks?project_id=${projectId}`);
        if (tasksRes.ok) {
          tasks = await tasksRes.json();
        }
      } catch (e) {
        tasks = [];
      }

      renderDetail();
    } catch (error) {
      titleEl.textContent = "Error";
      contentEl.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
          <p class="empty-state__title">Error al cargar</p>
          <p class="empty-state__text">No se pudo cargar el proyecto. Verifica que el servicio est&eacute; activo.</p>
          <button class="btn btn--secondary" onclick="appProjectsDetail.reload()">Reintentar</button>
        </div>
      `;
    }
  }

  function renderDetail() {
    // Conserva lo escrito en el formulario antes de reconstruir el DOM.
    captureTaskDraft();
    const pct = progressPercent(project.completed_count, project.task_count);
    const hasTasks = project.task_count > 0;
    const pendingTasks = tasks.filter(t => t.status === "pending");
    const completedTasks = tasks.filter(t => t.status === "completed");
    const overdueTasks = pendingTasks.filter(t => t.due_date && isOverdue(t.due_date));

    contentEl.innerHTML = `
      <div class="card" style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;">
          <div>
            <h2 style="margin-top:0; margin-bottom:4px;">${escapeHtml(project.name)}</h2>
            <span class="badge badge--${statusBadgeClass(project.status)}">${statusLabel(project.status)}</span>
          </div>
          <div class="btn-group" id="state-actions">
            ${projectActions(project.status).map(([action, label]) => `
              <button class="btn btn--secondary btn--sm" onclick="appProjectsDetail.runAction('${action}')">${label}</button>
            `).join("")}
          </div>
        </div>

        ${project.description ? `
          <p style="margin-top:12px; color:var(--text-secondary);">${escapeHtml(project.description)}</p>
        ` : ""}

        <div style="margin-top:16px; display:flex; gap:24px; flex-wrap:wrap;">
          <div>
            <div style="font-size:0.875rem; color:var(--text-secondary);">Avance</div>
            ${hasTasks ? `
              <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
                <span style="font-weight:600;">${project.completed_count}/${project.task_count}</span>
                <div class="progress" style="min-width:100px; flex:1;" role="progressbar"
                     aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}"
                     aria-label="Avance del proyecto">
                  <div class="progress__bar" style="width:${pct}%"></div>
                </div>
                <span style="font-weight:600;">${pct}%</span>
              </div>
            ` : `<span class="text-secondary">Sin tareas</span>`}
          </div>
          <div>
            <div style="font-size:0.875rem; color:var(--text-secondary);">Tareas vencidas</div>
            <div style="margin-top:4px; font-weight:600; ${project.overdue_count > 0 ? 'color:var(--danger);' : ''}">
              ${project.overdue_count}
            </div>
          </div>
          <div>
            <div style="font-size:0.875rem; color:var(--text-secondary);">Pr&oacute;ximo vencimiento</div>
            <div style="margin-top:4px; ${project.next_due_date && isFutureDue(project.next_due_date) ? '' : 'color:var(--danger);'}">
              ${project.next_due_date || "&mdash;"}
            </div>
          </div>
          <div>
            <div style="font-size:0.875rem; color:var(--text-secondary);">Creado</div>
            <div style="margin-top:4px; font-size:0.875rem;">${project.created_at.slice(0, 10)}</div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px;">
        <h3 style="margin-top:0;">Editar proyecto</h3>
        <div class="form-row" style="margin-top:12px;">
          <div class="form-group" style="flex:2; min-width:260px;">
            <label for="edit-name">Nombre</label>
            <input type="text" id="edit-name" value="${escapeHtml(project.name)}" required>
          </div>
          <div class="form-group" style="flex:1; min-width:200px;">
            <label for="edit-desc">Descripci&oacute;n</label>
            <input type="text" id="edit-desc" value="${escapeHtml(project.description || '')}">
          </div>
          <div class="form-group" style="flex:0; min-width:auto; align-self:flex-end;">
            <button class="btn btn--primary" id="edit-save-btn">Guardar cambios</button>
          </div>
        </div>
      </div>

      <div class="card" style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
          <h3 style="margin:0;">Tareas (${tasks.length})</h3>
          <span class="text-secondary" style="font-size:0.875rem;">
            ${completedTasks.length} completadas &middot; ${pendingTasks.length} pendientes${overdueTasks.length > 0 ? ` &middot; <span class="text-danger">${overdueTasks.length} vencidas</span>` : ""}
          </span>
          <button class="btn btn--primary btn--sm" onclick="appProjectsDetail.toggleTaskForm()" id="task-new-btn"
                  aria-expanded="${taskFormOpen ? "true" : "false"}" aria-controls="task-form">
            ${taskFormOpen ? "Cerrar formulario" : "+ Nueva tarea"}
          </button>
        </div>

        ${taskFormOpen ? `
          <form id="task-form" style="margin-top:12px; display:flex; flex-direction:column; gap:10px;" novalidate
                aria-label="Nueva tarea en ${escapeHtml(project.name)}">
            <div class="form-row" style="display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end;">
              <div class="form-group" style="flex:2; min-width:240px;">
                <label for="task-title">T&iacute;tulo <span class="text-secondary" style="font-weight:normal;">(obligatorio)</span></label>
                <input type="text" id="task-title" value="${escapeHtml(taskDraft.title)}" placeholder="T&iacute;tulo de la tarea" required maxlength="200"
                       ${taskErrorField === "title" ? 'aria-invalid="true" aria-describedby="task-error"' : ""}>
              </div>
              <div class="form-group" style="flex:1; min-width:180px;">
                <label for="task-desc">Descripci&oacute;n (opcional)</label>
                <input type="text" id="task-desc" value="${escapeHtml(taskDraft.desc)}" placeholder="Descripci&oacute;n" maxlength="2000">
              </div>
              <div class="form-group" style="flex:0; min-width:140px;">
                <label for="task-priority">Prioridad</label>
                <select id="task-priority">
                  <option value="" ${taskDraft.priority === "" ? "selected" : ""}>Sin prioridad</option>
                  <option value="high" ${taskDraft.priority === "high" ? "selected" : ""}>Alta</option>
                  <option value="normal" ${taskDraft.priority === "normal" ? "selected" : ""}>Normal</option>
                  <option value="low" ${taskDraft.priority === "low" ? "selected" : ""}>Baja</option>
                </select>
              </div>
              <div class="form-group" style="flex:1; min-width:160px;">
                <label for="task-due">Vencimiento (opcional)</label>
                <input type="date" id="task-due" value="${escapeHtml(taskDraft.due)}">
              </div>
            </div>
            <div class="btn-group" style="margin-top:4px;">
              <button type="submit" class="btn btn--primary" id="task-save-btn" ${creatingTask ? "disabled" : ""}>${creatingTask ? "Guardando&hellip;" : "Crear tarea"}</button>
              <button type="button" class="btn btn--secondary" onclick="appProjectsDetail.cancelTaskForm()">Cancelar</button>
              <span id="task-error" role="alert" tabindex="-1" style="color:var(--danger); font-size:0.875rem; margin-left:8px;">${taskError ? escapeHtml(taskError) : ""}</span>
            </div>
          </form>
        ` : ""}

        ${tasks.length === 0 ? `
          <div class="empty-state" style="padding:20px;">
            <div class="empty-state__icon" aria-hidden="true">&#10003;</div>
            <p class="empty-state__title">Sin tareas</p>
            <p class="empty-state__text">${taskFormOpen ? "Este proyecto todav&iacute;a no tiene tareas. Complet&aacute; el formulario de arriba para crear la primera." : "Este proyecto no tiene tareas asociadas."}</p>
            ${taskFormOpen ? "" : `<button class="btn btn--primary btn--sm" onclick="appProjectsDetail.toggleTaskForm()" style="margin-top:12px;">Crear primera tarea</button>`}
          </div>
        ` : `
          <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>T&iacute;tulo</th>
                <th>Estado</th>
                <th>Prioridad</th>
                <th>Vencimiento</th>
              </tr>
            </thead>
            <tbody>
              ${tasks.map(t => `
                <tr>
                  <td><strong>${escapeHtml(t.title)}</strong></td>
                  <td><span class="badge badge--${t.status === "completed" ? "success" : "status"}">${t.status === "completed" ? "Completada" : "Pendiente"}</span></td>
                  <td>${t.priority ? `<span class="badge badge--priority-${t.priority}">${t.priority === "high" ? "Alta" : t.priority === "normal" ? "Normal" : "Baja"}</span>` : "&mdash;"}</td>
                  <td>${t.due_date ? (isOverdue(t.due_date) && t.status === "pending" ? `<span class="text-danger">${t.due_date}</span>` : t.due_date) : "&mdash;"}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
          </div>
        `}
      </div>

      <div class="card" style="margin-top:24px; border-color:var(--danger);">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <h3 style="margin-top:0; margin-bottom:4px; color:var(--danger);">Zona de peligro</h3>
            <p class="text-secondary" style="margin:0; font-size:0.875rem;">
              Eliminar un proyecto es permanente. Si tiene tareas, no se podr&aacute; eliminar.
            </p>
          </div>
          <button class="btn btn--danger" onclick="appProjectsDetail.deleteProject()">Eliminar proyecto</button>
        </div>
      </div>
    `;

    // Guardar cambios
    container.querySelector("#edit-save-btn").addEventListener("click", async () => {
      const name = container.querySelector("#edit-name").value.trim();
      const desc = container.querySelector("#edit-desc").value.trim();
      if (!name) {
        showToast("El nombre no puede estar vacío", "warning");
        return;
      }
      const body = { name };
      if (desc) body.description = desc;

      try {
        const res = await fetch(`${apiBase}/projects/${projectId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (res.ok) {
          showToast("Proyecto actualizado", "success");
          await load();
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al actualizar", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    });

    // El botón es type="submit": clic y Enter disparan el mismo flujo y la
    // bandera `creatingTask` evita el doble envío.
    const taskForm = container.querySelector("#task-form");
    if (taskForm) {
      taskForm.addEventListener("submit", (e) => {
        e.preventDefault();
        appProjectsDetail.createTask();
      });
    }
  }

  window.appProjectsDetail = {
    async runAction(action) {
      try {
        const res = await fetch(`${apiBase}/projects/${projectId}/${action}`, {
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

    async deleteProject() {
      const confirmed = await showConfirm({
        title: "Eliminar proyecto",
        text: `&iquest;Eliminar el proyecto "${escapeHtml(project.name)}"? Esta acci&oacute;n lo elimina permanentemente (solo si no tiene tareas asociadas).`,
        confirmLabel: "Eliminar",
        danger: true,
      });
      if (!confirmed) return;

      try {
        const res = await fetch(`${apiBase}/projects/${projectId}`, {
          method: "DELETE",
        });
        if (res.ok || res.status === 204) {
          showToast("Proyecto eliminado", "success");
          window.location.hash = "#/projects";
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al eliminar proyecto", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    },

    editProject() {
      const el = container.querySelector("#edit-name");
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
        el.focus();
      }
    },

    reload() {
      load();
    },

    toggleTaskForm() {
      const willOpen = !taskFormOpen;
      taskFormOpen = willOpen;
      taskError = "";
      taskErrorField = "";
      if (!willOpen) taskDraft = emptyTaskDraft();
      renderDetail();
      if (willOpen) {
        const titleEl = container.querySelector("#task-title");
        if (titleEl) titleEl.focus();
      } else {
        const btn = container.querySelector("#task-new-btn");
        if (btn) btn.focus();
      }
    },

    // Cancelar quita solo el formulario: la lista de tareas permanece visible
    // en el mismo contexto (PRJ-UI-001).
    cancelTaskForm() {
      taskFormOpen = false;
      taskError = "";
      taskErrorField = "";
      taskDraft = emptyTaskDraft();
      renderDetail();
      const btn = container.querySelector("#task-new-btn");
      if (btn) btn.focus();
    },

    async createTask() {
      if (creatingTask) return;
      // Lee el formulario vivo: el borrador sobrevive a cualquier re-render.
      captureTaskDraft();
      const title = taskDraft.title.trim();
      const desc = taskDraft.desc.trim();
      const priority = taskDraft.priority;
      const due = taskDraft.due;

      if (!title) {
        taskError = "El título de la tarea no puede estar vacío.";
        taskErrorField = "title";
        renderDetail();
        focusTaskError();
        return;
      }

      const body = { project_id: projectId, title };
      if (desc) body.description = desc;
      if (priority) body.priority = priority;
      if (due) body.due_date = due;

      creatingTask = true;
      taskError = "";
      taskErrorField = "";
      renderDetail();

      try {
        const res = await fetch(`${apiBase}/tasks`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (res.ok) {
          creatingTask = false;
          taskFormOpen = false;
          taskError = "";
          taskErrorField = "";
          taskDraft = emptyTaskDraft();
          showToast("Tarea creada", "success");
          await load();
        } else {
          creatingTask = false;
          const err = await res.json().catch(() => ({}));
          taskError = formatApiDetail(err.detail, `Error al crear tarea (HTTP ${res.status})`);
          // 400/422: el foco va al primer campo inválido; el resto, al mensaje.
          taskErrorField = res.status === 400 || res.status === 422 ? "title" : "";
          renderDetail();
          focusTaskError();
        }
      } catch (error) {
        creatingTask = false;
        taskError = "Error de conexión. Verifica que el servicio esté activo e inténtalo de nuevo.";
        taskErrorField = "";
        renderDetail();
        focusTaskError();
      }
    },
  };

  await load();
}
