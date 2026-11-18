// Life OS — vista de Proyectos

export async function renderProjectsView(container, apiBase) {
  container.innerHTML = `
    <div class="form-row" style="margin-bottom: 16px;">
      <div class="form-group" style="flex: 2; min-width: 260px;">
        <label>Nuevo proyecto</label>
        <input type="text" id="proj-name" placeholder="Nombre del proyecto">
      </div>
      <div class="form-group" style="flex: 1; min-width: 200px;">
        <label>Descripci&oacute;n</label>
        <input type="text" id="proj-desc" placeholder="Descripci&oacute;n opcional">
      </div>
      <button class="btn btn--primary" id="proj-create-btn">Crear</button>
    </div>

    <h2 style="margin-top: 24px;">Proyectos</h2>
    <div id="projects-list" class="empty-state">Cargando proyectos...</div>
  `;

  const listEl = container.querySelector("#projects-list");
  const nameInput = container.querySelector("#proj-name");
  const descInput = container.querySelector("#proj-desc");
  const createBtn = container.querySelector("#proj-create-btn");

  async function load() {
    const res = await fetch(`${apiBase}/projects`);
    const projects = await res.json();

    if (projects.length === 0) {
      listEl.innerHTML = `<p class="empty-state">A&uacute;n no hay proyectos. Crea uno arriba.</p>`;
      return;
    }

    listEl.innerHTML = `
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
              <td>${escapeHtml(p.description || "&mdash;")}</td>
              <td><span class="badge badge--status">${p.status}</span></td>
              <td>
                <div class="btn-group">
                  <button class="btn btn--secondary btn--sm" onclick="appProjects.toggleStatus('${p.id}', '${p.status}')">
                    ${p.status === "active" ? p.status === "completed" ? "Reabrir" : "Completar" : p.status === "archived" ? "Restaurar" : "Archivar"}
                  </button>
                  <button class="btn btn--danger btn--sm" onclick="appProjects.deleteProject('${p.id}', '${escapeHtml(p.name)}')">
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
    const name = nameInput.value.trim();
    if (!name) return;
    const body = { name };
    if (descInput.value.trim()) body.description = descInput.value.trim();

    const res = await fetch(`${apiBase}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (res.ok) {
      nameInput.value = "";
      descInput.value = "";
      await load();
    } else {
      const err = await res.json();
      alert(err.detail || "Error al crear proyecto");
    }
  });

  window.appProjects = {
    async toggleStatus(id, currentStatus) {
      let endpoint;
      if (currentStatus === "active") endpoint = "/complete";
      else if (currentStatus === "completed") endpoint = "/reopen";
      else if (currentStatus === "archived") endpoint = "/restore";
      else return;

      const res = await fetch(`${apiBase}/projects/${id}${endpoint}`, {
        method: "POST",
      });

      if (res.ok) await load();
      else {
        const err = await res.json();
        alert(err.detail || "Error al cambiar estado");
      }
    },

    async deleteProject(id, name) {
      if (!confirm(`¿Eliminar el proyecto "${name}"? Esta acci&oacute;n no se puede deshacer si hay tareas vinculadas.`)) return;

      const res = await fetch(`${apiBase}/projects/${id}`, {
        method: "DELETE",
      });

      if (res.ok || res.status === 204) {
        await load();
      } else {
        const err = await res.json();
        alert(err.detail || "Error al eliminar proyecto");
      }
    },
  };

  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}