// Life OS — vista de Tareas (Fase 8C + TASK-001)
//
// Espacio de trabajo de tareas: acción compacta para capturar, edición con
// PATCH, filtros existentes, contadores y una lista de filas escaneables
// (prioridad, fecha y estado) con las acciones frecuentes separadas de la
// eliminación. Reutiliza GET/POST/PATCH/DELETE y complete/reopen actuales:
// sin cambios de endpoints, modelo ni migraciones.

import { showToast, showConfirm } from "./app.js";

export async function renderTasksView(container, apiBase) {
  let projects = [];
  let currentTasks = [];

  // Estado del formulario (crear o editar). El borrador vive fuera del DOM
  // para que un error o un re-render no destruya lo escrito (TASK-001 §8).
  const form = {
    mode: "create", // "create" | "edit"
    taskId: null,
    pending: false,
    error: "",
    draft: { title: "", description: "", project_id: "", priority: "", due_date: "" },
  };

  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Tareas</h1>
        <p class="subtitle">Captura, prioriza y revisa tus pendientes</p>
      </div>
      <button class="btn btn--primary" id="task-new-btn" aria-expanded="false" aria-controls="task-panel">
        + Nueva tarea
      </button>
    </div>

    <div class="task-panel" id="task-panel" hidden>
      <form id="task-form" novalidate>
        <h2 class="task-panel__title" id="task-form-title">Nueva tarea</h2>
        <div class="form-row">
          <div class="form-group">
            <label for="task-title">T&iacute;tulo <span class="text-secondary" style="font-weight:normal;">(obligatorio)</span></label>
            <input type="text" id="task-title" placeholder="T&iacute;tulo de la tarea" required maxlength="200">
          </div>
          <div class="form-group">
            <label for="task-project">Proyecto (opcional)</label>
            <select id="task-project"><option value="">Ninguno</option></select>
          </div>
          <div class="form-group">
            <label for="task-priority">Prioridad</label>
            <select id="task-priority">
              <option value="">Ninguna</option>
              <option value="low">Baja</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
            </select>
          </div>
          <div class="form-group">
            <label for="task-due">Vencimiento (opcional)</label>
            <input type="date" id="task-due">
          </div>
        </div>
        <div class="form-group">
          <label for="task-description">Descripci&oacute;n (opcional)</label>
          <input type="text" id="task-description" placeholder="Descripci&oacute;n" maxlength="2000">
        </div>
        <div class="btn-group">
          <button type="submit" class="btn btn--primary" id="task-save-btn">Guardar tarea</button>
          <button type="button" class="btn btn--secondary" id="task-cancel-btn">Cancelar</button>
          <span class="task-panel__error" id="task-error" role="alert" tabindex="-1"></span>
        </div>
      </form>
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

    <div class="tasks-summary" id="tasks-summary" aria-live="polite"></div>

    <div id="tasks-list">
      <div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
        <p class="empty-state__title">Cargando tareas&hellip;</p>
      </div>
    </div>
  `;

  const listEl = container.querySelector("#tasks-list");
  const summaryEl = container.querySelector("#tasks-summary");
  const panelEl = container.querySelector("#task-panel");
  const formEl = container.querySelector("#task-form");
  const formTitleEl = container.querySelector("#task-form-title");
  const titleInput = container.querySelector("#task-title");
  const descriptionInput = container.querySelector("#task-description");
  const projectSelect = container.querySelector("#task-project");
  const prioritySelect = container.querySelector("#task-priority");
  const dueInput = container.querySelector("#task-due");
  const saveBtn = container.querySelector("#task-save-btn");
  const cancelBtn = container.querySelector("#task-cancel-btn");
  const errorEl = container.querySelector("#task-error");
  const newBtn = container.querySelector("#task-new-btn");
  const filterStatus = container.querySelector("#task-filter-status");
  const filterProject = container.querySelector("#task-filter-project");

  // --- Utilidades -----------------------------------------------------------
  function todayISO() {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  function isOverdue(dueDate, status) {
    if (!dueDate || status === "completed") return false;
    return dueDate < todayISO();
  }

  function isDueToday(dueDate, status) {
    if (!dueDate || status === "completed") return false;
    return dueDate === todayISO();
  }

  function priorityLabel(priority) {
    if (priority === "high") return "Alta";
    if (priority === "normal") return "Normal";
    if (priority === "low") return "Baja";
    return "";
  }

  function projectName(projectId) {
    const p = projects.find((x) => x.id === projectId);
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

  // --- Carga ----------------------------------------------------------------
  async function loadProjects() {
    try {
      const res = await fetch(`${apiBase}/projects`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      projects = await res.json();
      // Orden alfabético: la API no garantiza orden, y un desplegable
      // predecible es más escaneable para elegir proyecto (filtro o alta).
      projects = [...projects].sort((a, b) => a.name.localeCompare(b.name, "es"));

      const currentProject = projectSelect.value;
      const currentFilter = filterProject.value;
      projectSelect.innerHTML = '<option value="">Ninguno</option>';
      filterProject.innerHTML = '<option value="">Todos los proyectos</option>';
      projects.forEach((p) => {
        const opt1 = document.createElement("option");
        opt1.value = p.id;
        opt1.textContent = p.name;
        projectSelect.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = p.id;
        opt2.textContent = p.name;
        filterProject.appendChild(opt2);
      });
      // Conserva la selección previa (crear/editar o filtro).
      if (currentProject) projectSelect.value = currentProject;
      if (currentFilter) filterProject.value = currentFilter;
    } catch (error) {
      // Silenciar: los proyectos se cargan en segundo plano
    }
  }

  async function load() {
    listEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
        <p class="empty-state__title">Cargando&hellip;</p>
      </div>
    `;
    summaryEl.innerHTML = "";
    try {
      const params = new URLSearchParams();
      if (filterStatus.value) params.set("status", filterStatus.value);
      if (filterProject.value) params.set("project_id", filterProject.value);

      const res = await fetch(`${apiBase}/tasks?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const tasks = await res.json();
      currentTasks = tasks;

      // Los contadores describen el total real; la lista muestra la vista
      // filtrada. Con filtro activo se consulta el conjunto completo para no
      // reportar "0 completadas" cuando el filtro esconde las completadas.
      let totals = tasks;
      const filtered = Boolean(filterStatus.value || filterProject.value);
      if (filtered) {
        try {
          const allRes = await fetch(`${apiBase}/tasks`);
          if (allRes.ok) totals = await allRes.json();
        } catch (error) {
          totals = tasks;
        }
      }

      renderSummary(totals, tasks, filtered);

      if (tasks.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#10003;</div>
            <p class="empty-state__title">No hay tareas</p>
            <p class="empty-state__text">No hay tareas que coincidan con el filtro actual.</p>
            <button class="btn btn--primary btn--sm" id="tasks-empty-create">Crear una tarea</button>
          </div>
        `;
        const emptyBtn = listEl.querySelector("#tasks-empty-create");
        if (emptyBtn) emptyBtn.addEventListener("click", openCreatePanel);
        return tasks;
      }

      listEl.innerHTML = `<ul class="task-list">${tasks.map(taskRow).join("")}</ul>`;
      return tasks;
    } catch (error) {
      summaryEl.innerHTML = "";
      listEl.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
          <p class="empty-state__title">Error al cargar</p>
          <p class="empty-state__text">No se pudieron cargar las tareas. Verifica que el servicio est&eacute; activo.</p>
          <button class="btn btn--secondary" id="tasks-retry">Reintentar</button>
        </div>
      `;
      const retryBtn = listEl.querySelector("#tasks-retry");
      if (retryBtn) retryBtn.addEventListener("click", load);
      return null;
    }
  }

  // Contadores: `totals` = todas las tareas, `visible` = la lista filtrada.
  function renderSummary(totals, visible, filtered) {
    const pending = totals.filter((t) => t.status === "pending").length;
    const completed = totals.length - pending;
    const overdue = totals.filter((t) => isOverdue(t.due_date, t.status)).length;
    summaryEl.innerHTML = `
      <span class="tasks-summary__item"><strong>${pending}</strong> ${pending === 1 ? "pendiente" : "pendientes"}</span>
      <span class="tasks-summary__item"><strong>${completed}</strong> ${completed === 1 ? "completada" : "completadas"}</span>
      ${overdue > 0 ? `<span class="tasks-summary__item tasks-summary__item--danger"><strong>${overdue}</strong> ${overdue === 1 ? "vencida" : "vencidas"}</span>` : ""}
      ${
        filtered
          ? `<span class="tasks-summary__filter">Filtro aplicado · ${visible.length} ${visible.length === 1 ? "tarea visible" : "tareas visibles"}</span>`
          : ""
      }
    `;
  }

  function taskRow(task) {
    const completed = task.status === "completed";
    const overdue = isOverdue(task.due_date, task.status);
    const dueToday = isDueToday(task.due_date, task.status);
    const project = projectName(task.project_id);

    let dueChip = `<span class="chip chip--muted">Sin fecha</span>`;
    if (overdue) dueChip = `<span class="chip chip--danger">Vencida el ${task.due_date}</span>`;
    else if (dueToday) dueChip = `<span class="chip chip--warning">Vence hoy</span>`;
    else if (task.due_date) dueChip = `<span class="chip">Vence el ${task.due_date}</span>`;

    return `
      <li class="task-row${completed ? " task-row--completed" : ""}" id="task-row-${task.id}">
        <button type="button" class="check-toggle" data-action="toggle-status" data-id="${task.id}"
                data-status="${task.status}"
                aria-label="${completed ? "Reabrir" : "Completar"} ${escapeHtml(task.title)}"
                title="${completed ? "Reabrir" : "Completar"}">&#10003;</button>
        <div class="task-row__body">
          <span class="task-row__title">${escapeHtml(task.title)}</span>
          <span class="task-row__meta">
            <span class="badge badge--${completed ? "success" : "status"}">${completed ? "Completada" : "Pendiente"}</span>
            ${task.priority ? `<span class="badge badge--priority-${task.priority}">${priorityLabel(task.priority)}</span>` : ""}
            ${dueChip}
            ${
              project
                ? `<a class="chip chip--link" href="#/projects/${task.project_id}">${escapeHtml(project)}</a>`
                : ""
            }
          </span>
          ${task.description ? `<span class="task-row__description">${escapeHtml(task.description)}</span>` : ""}
        </div>
        <div class="task-row__actions">
          <button type="button" class="btn btn--secondary btn--sm" data-action="edit-task" data-id="${task.id}">Editar</button>
          <button type="button" class="btn btn--secondary btn--sm task-row__delete" data-action="delete-task" data-id="${task.id}">Eliminar</button>
        </div>
      </li>
    `;
  }

  // --- Formulario (crear / editar) ------------------------------------------
  function captureDraft() {
    if (titleInput) form.draft.title = titleInput.value;
    if (descriptionInput) form.draft.description = descriptionInput.value;
    if (projectSelect) form.draft.project_id = projectSelect.value;
    if (prioritySelect) form.draft.priority = prioritySelect.value;
    if (dueInput) form.draft.due_date = dueInput.value;
  }

  function renderForm() {
    formTitleEl.textContent = form.mode === "edit" ? "Editar tarea" : "Nueva tarea";
    titleInput.value = form.draft.title;
    descriptionInput.value = form.draft.description;
    projectSelect.value = form.draft.project_id;
    prioritySelect.value = form.draft.priority;
    dueInput.value = form.draft.due_date;
    errorEl.textContent = form.error;
    saveBtn.textContent = form.pending
      ? "Guardando…"
      : form.mode === "edit"
      ? "Guardar cambios"
      : "Guardar tarea";
    saveBtn.disabled = form.pending;
  }

  function openCreatePanel() {
    form.mode = "create";
    form.taskId = null;
    form.error = "";
    form.draft = { title: "", description: "", project_id: "", priority: "", due_date: "" };
    panelEl.hidden = false;
    newBtn.setAttribute("aria-expanded", "true");
    newBtn.textContent = "Cerrar";
    renderForm();
    titleInput.focus();
  }

  function openEditPanel(taskId) {
    const task = currentTasks.find((t) => t.id === taskId);
    if (!task) return;
    form.mode = "edit";
    form.taskId = taskId;
    form.error = "";
    form.draft = {
      title: task.title || "",
      description: task.description || "",
      project_id: task.project_id || "",
      priority: task.priority || "",
      due_date: task.due_date || "",
    };
    panelEl.hidden = false;
    newBtn.setAttribute("aria-expanded", "true");
    newBtn.textContent = "Cerrar";
    renderForm();
    titleInput.focus();
  }

  function closePanel() {
    form.mode = "create";
    form.taskId = null;
    form.error = "";
    form.draft = { title: "", description: "", project_id: "", priority: "", due_date: "" };
    panelEl.hidden = true;
    newBtn.setAttribute("aria-expanded", "false");
    newBtn.textContent = "+ Nueva tarea";
    renderForm();
    newBtn.focus();
  }

  async function submitForm() {
    if (form.pending) return;
    captureDraft();
    const title = form.draft.title.trim();
    if (!title) {
      form.error = "El título de la tarea no puede estar vacío.";
      renderForm();
      titleInput.focus();
      return;
    }

    const editing = form.mode === "edit";
    const taskId = form.taskId;

    // En alta solo se envían los campos con valor; en edición (PATCH) se
    // envían también los vacíos como `null` para poder quitar un campo
    // opcional (prioridad, vencimiento, proyecto o descripción).
    const body = { title };
    if (editing) {
      body.description = form.draft.description.trim() || null;
      body.project_id = form.draft.project_id || null;
      body.priority = form.draft.priority || null;
      body.due_date = form.draft.due_date || null;
    } else {
      if (form.draft.description.trim()) body.description = form.draft.description.trim();
      if (form.draft.project_id) body.project_id = form.draft.project_id;
      if (form.draft.priority) body.priority = form.draft.priority;
      if (form.draft.due_date) body.due_date = form.draft.due_date;
    }

    form.pending = true;
    form.error = "";
    renderForm();

    try {
      const res = await fetch(
        editing ? `${apiBase}/tasks/${taskId}` : `${apiBase}/tasks`,
        {
          method: editing ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (res.ok) {
        const saved = await res.json().catch(() => null);
        form.pending = false;
        const wasEditing = editing;
        // Cierra el panel y limpia el borrador antes de recargar.
        form.mode = "create";
        form.taskId = null;
        form.error = "";
        form.draft = { title: "", description: "", project_id: "", priority: "", due_date: "" };
        panelEl.hidden = true;
        newBtn.setAttribute("aria-expanded", "false");
        newBtn.textContent = "+ Nueva tarea";
        renderForm();
        showToast(wasEditing ? "Tarea actualizada" : "Tarea creada", "success");
        const visible = await load();
        // Si un filtro activo esconde la tarea recién guardada, se avisa en
        // lugar de dejar la impresión de que no se guardó.
        if (
          saved &&
          visible &&
          !visible.some((t) => t.id === saved.id) &&
          (filterStatus.value || filterProject.value)
        ) {
          showToast("No aparece en la lista porque hay un filtro aplicado.", "info");
        }
      } else {
        form.pending = false;
        const err = await res.json().catch(() => ({}));
        form.error = formatApiDetail(err.detail, editing ? "No se pudo actualizar la tarea." : "No se pudo crear la tarea.");
        renderForm();
        titleInput.focus();
      }
    } catch (error) {
      form.pending = false;
      form.error = "Error de conexión. Inténtalo de nuevo.";
      renderForm();
      titleInput.focus();
    }
  }

  // --- Acciones sobre la lista ----------------------------------------------
  async function toggleStatus(id, status, button) {
    if (button && button.disabled) return;
    if (button) button.disabled = true;
    try {
      const endpoint = status === "pending" ? "/complete" : "/reopen";
      const res = await fetch(`${apiBase}/tasks/${id}${endpoint}`, { method: "POST" });
      if (res.ok) {
        showToast(status === "pending" ? "Tarea completada" : "Tarea reabierta", "success");
        await load();
      } else {
        if (button) button.disabled = false;
        const err = await res.json().catch(() => ({}));
        showToast(formatApiDetail(err.detail, "No se pudo cambiar el estado"), "error");
      }
    } catch (error) {
      if (button) button.disabled = false;
      showToast("Error de conexión", "error");
    }
  }

  async function deleteTask(id) {
    const task = currentTasks.find((t) => t.id === id);
    const title = task ? task.title : "";
    const confirmed = await showConfirm({
      title: "Eliminar tarea",
      text: `¿Eliminar la tarea "${escapeHtml(title)}"?`,
      confirmLabel: "Eliminar",
      danger: true,
    });
    if (!confirmed) return;

    try {
      const res = await fetch(`${apiBase}/tasks/${id}`, { method: "DELETE" });
      if (res.ok || res.status === 204) {
        showToast("Tarea eliminada", "success");
        await load();
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(formatApiDetail(err.detail, "No se pudo eliminar la tarea"), "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    }
  }

  // --- Eventos --------------------------------------------------------------
  newBtn.addEventListener("click", () => {
    if (panelEl.hidden) {
      openCreatePanel();
    } else {
      closePanel();
    }
  });

  cancelBtn.addEventListener("click", closePanel);

  formEl.addEventListener("submit", (event) => {
    event.preventDefault();
    submitForm();
  });

  // El borrador se actualiza en vivo: un re-render no pierde lo escrito.
  formEl.addEventListener("input", captureDraft);
  formEl.addEventListener("change", captureDraft);

  // ESC cierra el panel y devuelve el foco al botón. El listener vive en el
  // panel (se descarta con el DOM al cambiar de vista) para no acumular
  // listeners globales en cada navegación.
  panelEl.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panelEl.hidden) {
      // Si hay un modal abierto (p. ej. confirmar eliminación), ESC solo debe
      // cerrar ese modal.
      if (document.querySelector(".modal-overlay")) return;
      event.stopPropagation();
      closePanel();
    }
  });

  listEl.addEventListener("click", async (event) => {
    const toggleBtn = event.target.closest('[data-action="toggle-status"]');
    if (toggleBtn) {
      await toggleStatus(toggleBtn.dataset.id, toggleBtn.dataset.status, toggleBtn);
      return;
    }
    const editBtn = event.target.closest('[data-action="edit-task"]');
    if (editBtn) {
      openEditPanel(editBtn.dataset.id);
      return;
    }
    const deleteBtn = event.target.closest('[data-action="delete-task"]');
    if (deleteBtn) {
      await deleteTask(deleteBtn.dataset.id);
    }
  });

  filterStatus.addEventListener("change", load);
  filterProject.addEventListener("change", load);

  await loadProjects();
  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  // Escapa también comillas para los valores usados en atributos.
  const amp = String.fromCharCode(38);
  return div.innerHTML.replace(/"/g, `${amp}quot;`).replace(/'/g, `${amp}#39;`);
}
