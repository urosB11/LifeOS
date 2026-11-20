// Life OS — vista de Proyectos (Fase 8C)
//
// Listado, creación, edición inline, estados y acciones. Usa los componentes
// compartidos de 8A (section-header, badges, empty-state, toast, confirm).

import { showToast, showConfirm } from "./app.js";

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

  // Acciones disponibles por estado (FR-PROJ-04 / FR-PROJ-06)
  function projectActions(status) {
    if (status === "active") {
      return [["complete", "Completar"], ["archive", "Archivar"]];
    }
    if (status === "completed") {
      return [["reopen", "Reabrir"], ["archive", "Archivar"]];
    }
    return [["restore", "Restaurar"]]; // archived
  }

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
              <th>Descripci&oacute;n</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${projects.map(p => `
              <tr id="proj-row-${p.id}">
                <td><strong>${escapeHtml(p.name)}</strong></td>
                <td>${p.description ? escapeHtml(p.description) : "&mdash;"}</td>
                <td><span class="badge badge--${statusBadgeClass(p.status)}">${statusLabel(p.status)}</span></td>
                <td>
                  <div class="btn-group">
                    ${projectActions(p.status).map(([action, label]) => `
                      <button class="btn btn--secondary btn--sm" onclick="appProjects.runAction('${p.id}', '${action}')">${label}</button>
                    `).join("")}
                    <button class="btn btn--danger btn--sm" onclick="appProjects.deleteProject('${p.id}')">Eliminar</button>
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
        <p class="empty-state__text">No se pudieron cargar los proyectos. Verifica que el servicio est&eacute; activo.</p>
        <button class="btn btn--secondary" onclick="appProjects.reload()">Reintentar</button>
      `;
    }
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
        text: `¿Eliminar el proyecto "${name}"? Esta acción no se puede deshacer si hay tareas vinculadas.`,
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

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
