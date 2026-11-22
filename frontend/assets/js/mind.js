// Life OS — vista principal de Mind: Spaces, Inbox y detalle de Space (MIND-002)
//
// El Canvas tiene su propio módulo (mind-canvas.js). Aquí viven el listado de
// Spaces, la captura rápida al Inbox y el detalle de cada Space.

import { showToast, showConfirm } from "./app.js";
import {
  apiJson,
  emptyState,
  errorState,
  escapeHtml,
  formatDate,
  loadingState,
  showFormModal,
} from "./mind-common.js";

/** Captura rápida compartida por las vistas de Mind (SPEC §5). */
export function mountQuickCapture(host, apiBase, onSaved) {
  host.innerHTML = `
    <form class="mind-capture" id="mind-capture-form" novalidate>
      <div class="form-group">
        <label for="mind-capture-content">Captura rápida para el Inbox</label>
        <textarea id="mind-capture-content" rows="2" maxlength="100000"
          placeholder="Escribí la idea, la tarea suelta o el dato que querés guardar…" required></textarea>
      </div>
      <div class="mind-capture__row">
        <div class="form-group">
          <label for="mind-capture-title">Título (opcional)</label>
          <input type="text" id="mind-capture-title" maxlength="200" placeholder="Si lo omitís, se usa la primera línea">
        </div>
        <button class="btn btn--primary" type="submit" id="mind-capture-btn">Guardar en Inbox</button>
      </div>
      <p class="mind-capture__status" id="mind-capture-status" role="status" aria-live="polite"></p>
    </form>
  `;

  const form = host.querySelector("#mind-capture-form");
  const contentEl = host.querySelector("#mind-capture-content");
  const titleEl = host.querySelector("#mind-capture-title");
  const btn = host.querySelector("#mind-capture-btn");
  const statusEl = host.querySelector("#mind-capture-status");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const content = contentEl.value.trim();
    if (!content) {
      statusEl.textContent = "La captura no puede estar vacía.";
      showToast("La captura no puede estar vacía", "warning");
      contentEl.focus();
      return;
    }
    btn.disabled = true;
    btn.textContent = "Guardando…";
    statusEl.textContent = "";
    try {
      const note = await apiJson(`${apiBase}/mind/inbox/captures`, {
        method: "POST",
        body: { title: titleEl.value.trim() || null, content },
      });
      // Solo se limpia el borrador cuando el guardado fue exitoso.
      contentEl.value = "";
      titleEl.value = "";
      statusEl.textContent = "Captura guardada en el Inbox.";
      showToast("Captura guardada en el Inbox", "success");
      if (onSaved) onSaved(note);
    } catch (err) {
      // El borrador se conserva para no perder lo escrito.
      statusEl.textContent = `No se pudo guardar: ${err.message}`;
      showToast(err.message || "Error al guardar la captura", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Guardar en Inbox";
    }
  });
}

// --- Vista principal -------------------------------------------------------

export async function renderMindHomeView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Mind</h1>
        <p class="subtitle">Capturá ideas y organizá tu trabajo en espacios visuales</p>
      </div>
    </div>

    <div class="card mind-card-block" id="mind-capture-host"></div>

    <div class="mind-grid">
      <section class="card mind-panel" aria-labelledby="mind-inbox-title">
        <h2 class="mind-panel__title" id="mind-inbox-title">Inbox</h2>
        <div id="mind-inbox-summary" class="empty-state">${loadingState("Cargando Inbox…")}</div>
      </section>

      <section class="card mind-panel" aria-labelledby="mind-spaces-title">
        <div class="mind-panel__head">
          <h2 class="mind-panel__title" id="mind-spaces-title">Spaces</h2>
          <label class="mind-toggle">
            <input type="checkbox" id="mind-show-archived">
            Mostrar archivados
          </label>
        </div>
        <div id="mind-spaces-list" class="empty-state">${loadingState("Cargando Spaces…")}</div>
      </section>
    </div>

    <section class="card mind-card-block" aria-labelledby="mind-new-space-title">
      <h2 class="mind-panel__title" id="mind-new-space-title">Nuevo Space</h2>
      <form id="mind-new-space" novalidate>
        <div class="form-row">
          <div class="form-group">
            <label for="mind-space-name">Nombre</label>
            <input type="text" id="mind-space-name" maxlength="200" placeholder="Ej.: Investigación" required>
          </div>
          <div class="form-group">
            <label for="mind-space-description">Descripción (opcional)</label>
            <input type="text" id="mind-space-description" maxlength="2000" placeholder="Para qué sirve este espacio">
          </div>
        </div>
        <button class="btn btn--primary" type="submit" id="mind-space-create">Crear Space</button>
        <p class="mind-capture__status" id="mind-space-status" role="status" aria-live="polite"></p>
      </form>
    </section>
  `;

  const spacesListEl = container.querySelector("#mind-spaces-list");
  const inboxSummaryEl = container.querySelector("#mind-inbox-summary");
  const archivedToggle = container.querySelector("#mind-show-archived");
  const newSpaceForm = container.querySelector("#mind-new-space");
  const spaceNameEl = container.querySelector("#mind-space-name");
  const spaceDescriptionEl = container.querySelector("#mind-space-description");
  const spaceCreateBtn = container.querySelector("#mind-space-create");
  const spaceStatusEl = container.querySelector("#mind-space-status");

  mountQuickCapture(container.querySelector("#mind-capture-host"), apiBase, () => {
    loadInboxSummary();
  });

  async function loadInboxSummary() {
    inboxSummaryEl.innerHTML = loadingState("Cargando Inbox…");
    try {
      const inbox = await apiJson(`${apiBase}/mind/inbox`);
      const count = inbox.captures.length;
      inboxSummaryEl.innerHTML = `
        <p class="text-secondary" style="margin:0 0 12px;">
          ${count === 1 ? "1 captura esperando" : `${count} capturas esperando`}
        </p>
        <a class="btn btn--primary" href="#/mind/inbox">Abrir Inbox</a>
      `;
    } catch (err) {
      inboxSummaryEl.innerHTML = errorState(
        "Error al cargar el Inbox",
        err.message || "No se pudo consultar el Inbox.",
        "mind-inbox-retry"
      );
      const retry = container.querySelector("#mind-inbox-retry");
      if (retry) retry.addEventListener("click", loadInboxSummary);
    }
  }

  async function loadSpaces() {
    spacesListEl.innerHTML = loadingState("Cargando Spaces…");
    const includeArchived = archivedToggle.checked;
    try {
      const spaces = await apiJson(
        `${apiBase}/mind/spaces?include_archived=${includeArchived}`
      );
      const userSpaces = spaces.filter((s) => !s.is_inbox);
      if (!userSpaces.length) {
        spacesListEl.innerHTML = emptyState(
          "Todavía no hay Spaces",
          "Creá tu primer espacio de trabajo abajo: un Canvas, un proyecto o un estudio."
        );
        return;
      }
      spacesListEl.classList.remove("empty-state");
      spacesListEl.innerHTML = `
        <ul class="mind-space-list">
          ${userSpaces.map((s) => _spaceItem(s)).join("")}
        </ul>
      `;
    } catch (err) {
      spacesListEl.innerHTML = errorState(
        "Error al cargar los Spaces",
        err.message || "No se pudieron cargar los Spaces.",
        "mind-spaces-retry"
      );
      const retry = container.querySelector("#mind-spaces-retry");
      if (retry) retry.addEventListener("click", loadSpaces);
    }
  }

  archivedToggle.addEventListener("change", loadSpaces);

  newSpaceForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = spaceNameEl.value.trim();
    if (!name) {
      spaceStatusEl.textContent = "El nombre del Space no puede estar vacío.";
      showToast("El nombre del Space no puede estar vacío", "warning");
      spaceNameEl.focus();
      return;
    }
    spaceCreateBtn.disabled = true;
    spaceCreateBtn.textContent = "Creando…";
    try {
      await apiJson(`${apiBase}/mind/spaces`, {
        method: "POST",
        body: { name, description: spaceDescriptionEl.value.trim() || null },
      });
      spaceNameEl.value = "";
      spaceDescriptionEl.value = "";
      spaceStatusEl.textContent = "Space creado.";
      showToast("Space creado", "success");
      await loadSpaces();
    } catch (err) {
      spaceStatusEl.textContent = `No se pudo crear: ${err.message}`;
      showToast(err.message || "Error al crear el Space", "error");
    } finally {
      spaceCreateBtn.disabled = false;
      spaceCreateBtn.textContent = "Crear Space";
    }
  });

  await loadInboxSummary();
  await loadSpaces();
}

function _spaceItem(space) {
  const canvases = space.canvas_count === 1 ? "1 Canvas" : `${space.canvas_count} Canvases`;
  return `
    <li class="mind-space">
      <div class="mind-space__main">
        <h3 class="mind-space__name">
          <a href="#/mind/spaces/${space.id}">${escapeHtml(space.name)}</a>
        </h3>
        ${space.description ? `<p class="text-secondary mind-space__desc">${escapeHtml(space.description)}</p>` : ""}
        <p class="mind-space__meta">${canvases}</p>
      </div>
      ${space.status === "archived" ? '<span class="badge badge--status">Archivado</span>' : ""}
    </li>
  `;
}

// --- Vista Inbox -----------------------------------------------------------

export async function renderMindInboxView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Inbox</h1>
        <p class="subtitle">Capturas transversales de Mind</p>
      </div>
      <a class="btn btn--secondary" href="#/mind">Volver a Mind</a>
    </div>

    <div class="card mind-card-block" id="mind-capture-host"></div>

    <section class="card mind-card-block" aria-labelledby="mind-captures-title">
      <h2 class="mind-panel__title" id="mind-captures-title">Capturas</h2>
      <div id="mind-captures-list" class="empty-state">${loadingState("Cargando capturas…")}</div>
    </section>
  `;

  const listEl = container.querySelector("#mind-captures-list");

  mountQuickCapture(container.querySelector("#mind-capture-host"), apiBase, () => {
    loadCaptures();
  });

  async function loadCaptures() {
    listEl.innerHTML = loadingState("Cargando capturas…");
    try {
      const inbox = await apiJson(`${apiBase}/mind/inbox`);
      const captures = inbox.captures;
      if (!captures.length) {
        listEl.innerHTML = emptyState(
          "El Inbox está vacío",
          "Usá la captura rápida de arriba para guardar tu primera idea."
        );
        return;
      }
      listEl.classList.remove("empty-state");
      listEl.innerHTML = `
        <ul class="mind-capture-list">
          ${captures
            .map(
              (note) => `
            <li class="mind-capture-item">
              <div class="mind-capture-item__main">
                <h3 class="mind-capture-item__title">${escapeHtml(note.title)}</h3>
                <p class="mind-capture-item__preview">${escapeHtml(
                  note.content.substring(0, 160)
                )}${note.content.length > 160 ? "…" : ""}</p>
                <p class="mind-space__meta">${formatDate(note.updated_at)}</p>
              </div>
              <div class="btn-group">
                <button class="btn btn--secondary btn--sm" data-action="edit" data-id="${note.id}">Editar</button>
                <button class="btn btn--danger btn--sm" data-action="delete" data-id="${note.id}">Eliminar</button>
              </div>
            </li>
          `
            )
            .join("")}
        </ul>
      `;
    } catch (err) {
      listEl.innerHTML = errorState(
        "Error al cargar las capturas",
        err.message || "No se pudieron cargar las capturas.",
        "mind-captures-retry"
      );
      const retry = container.querySelector("#mind-captures-retry");
      if (retry) retry.addEventListener("click", loadCaptures);
    }
  }

  listEl.addEventListener("click", async (e) => {
    const button = e.target.closest("[data-action]");
    if (!button) return;
    const noteId = button.dataset.id;

    if (button.dataset.action === "edit") {
      const inbox = await apiJson(`${apiBase}/mind/inbox`);
      const note = inbox.captures.find((c) => c.id === noteId);
      if (!note) return;
      const result = await showFormModal({
        title: "Editar captura",
        fields: [
          { name: "title", label: "Título", value: note.title, maxlength: 200 },
          {
            name: "content",
            label: "Contenido",
            type: "textarea",
            value: note.content,
            rows: 6,
            required: true,
            maxlength: 100000,
          },
        ],
        submitLabel: "Guardar",
      });
      if (!result.ok) return;
      try {
        // El contenido se edita con el API canónico de Notas (fuente de verdad).
        await apiJson(`${apiBase}/notes/${noteId}`, {
          method: "PATCH",
          body: { title: result.values.title.trim(), content: result.values.content },
        });
        showToast("Captura actualizada", "success");
        await loadCaptures();
      } catch (err) {
        showToast(err.message || "Error al actualizar la captura", "error");
      }
      return;
    }

    if (button.dataset.action === "delete") {
      const confirmed = await showConfirm({
        title: "Eliminar captura",
        text: "¿Eliminar esta captura? La idea se borra de Mind y de tus Notes.",
        confirmLabel: "Eliminar",
        danger: true,
      });
      if (!confirmed) return;
      try {
        await apiJson(`${apiBase}/notes/${noteId}`, { method: "DELETE" });
        showToast("Captura eliminada", "success");
        await loadCaptures();
      } catch (err) {
        showToast(err.message || "Error al eliminar la captura", "error");
      }
    }
  });

  await loadCaptures();
}

// --- Vista de Space --------------------------------------------------------

export async function renderMindSpaceView(container, apiBase, spaceId) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1 id="mind-space-title">Space</h1>
        <p class="subtitle" id="mind-space-description"></p>
      </div>
      <a class="btn btn--secondary" href="#/mind">Volver a Mind</a>
    </div>
    <div id="mind-space-body" class="empty-state">${loadingState("Cargando Space…")}</div>
  `;

  const titleEl = container.querySelector("#mind-space-title");
  const descriptionEl = container.querySelector("#mind-space-description");
  const bodyEl = container.querySelector("#mind-space-body");

  let space = null;
  let showArchived = false;

  async function loadSpace() {
    try {
      space = await apiJson(`${apiBase}/mind/spaces/${spaceId}`);
    } catch (err) {
      bodyEl.innerHTML = errorState(
        "Error al cargar el Space",
        err.message || "No se pudo cargar el Space.",
        "mind-space-retry"
      );
      const retry = container.querySelector("#mind-space-retry");
      if (retry) retry.addEventListener("click", loadSpace);
      return;
    }
    titleEl.textContent = space.name;
    descriptionEl.textContent = space.description || "Sin descripción";
    await loadCanvases();
  }

  async function loadCanvases() {
    bodyEl.classList.remove("empty-state");
    bodyEl.innerHTML = loadingState("Cargando Canvases…");
    try {
      const canvases = await apiJson(
        `${apiBase}/mind/spaces/${spaceId}/canvases?include_archived=${showArchived}`
      );
      bodyEl.innerHTML = `
        <section class="card mind-card-block" aria-labelledby="mind-canvases-title">
          <div class="mind-panel__head">
            <h2 class="mind-panel__title" id="mind-canvases-title">Canvases</h2>
            <div class="mind-panel__actions">
              <label class="mind-toggle">
                <input type="checkbox" id="mind-canvases-archived" ${showArchived ? "checked" : ""}>
                Mostrar archivados
              </label>
              <button class="btn btn--secondary btn--sm" id="mind-space-rename">Renombrar Space</button>
              ${
                space.status === "archived"
                  ? '<button class="btn btn--secondary btn--sm" id="mind-space-restore">Restaurar Space</button>'
                  : '<button class="btn btn--secondary btn--sm" id="mind-space-archive">Archivar Space</button>'
              }
            </div>
          </div>
          <div id="mind-canvases-list">
            ${
              canvases.length
                ? `<ul class="mind-space-list">
                    ${canvases.map(_canvasItem).join("")}
                  </ul>`
                : emptyState(
                    "Sin Canvases",
                    "Creá el primer Canvas para empezar a colocar ideas en el espacio."
                  )
            }
          </div>
          <form id="mind-new-canvas" class="mind-inline-form" novalidate>
            <div class="form-row">
              <div class="form-group">
                <label for="mind-canvas-title">Título del Canvas</label>
                <input type="text" id="mind-canvas-title" maxlength="200" placeholder="Ej.: Mapa de ideas" required>
              </div>
              <div class="form-group">
                <label for="mind-canvas-description">Descripción (opcional)</label>
                <input type="text" id="mind-canvas-description" maxlength="2000" placeholder="De qué trata este Canvas">
              </div>
            </div>
            <button class="btn btn--primary" type="submit" id="mind-canvas-create">Crear Canvas</button>
            <p class="mind-capture__status" id="mind-canvas-status" role="status" aria-live="polite"></p>
          </form>
        </section>
      `;
      bindCanvasEvents();
    } catch (err) {
      bodyEl.innerHTML = errorState(
        "Error al cargar los Canvases",
        err.message || "No se pudieron cargar los Canvases.",
        "mind-canvases-retry"
      );
      const retry = container.querySelector("#mind-canvases-retry");
      if (retry) retry.addEventListener("click", loadCanvases);
    }
  }

  function bindCanvasEvents() {
    const archivedToggle = bodyEl.querySelector("#mind-canvases-archived");
    archivedToggle.addEventListener("change", () => {
      showArchived = archivedToggle.checked;
      loadCanvases();
    });

    const renameBtn = bodyEl.querySelector("#mind-space-rename");
    renameBtn.addEventListener("click", async () => {
      const result = await showFormModal({
        title: "Renombrar Space",
        fields: [
          { name: "name", label: "Nombre", value: space.name, required: true, maxlength: 200 },
          {
            name: "description",
            label: "Descripción",
            value: space.description || "",
            maxlength: 2000,
          },
        ],
      });
      if (!result.ok) return;
      try {
        await apiJson(`${apiBase}/mind/spaces/${spaceId}`, {
          method: "PATCH",
          body: {
            name: result.values.name.trim(),
            description: result.values.description.trim() || null,
          },
        });
        showToast("Space actualizado", "success");
        await loadSpace();
      } catch (err) {
        showToast(err.message || "Error al actualizar el Space", "error");
      }
    });

    const archiveBtn = bodyEl.querySelector("#mind-space-archive");
    if (archiveBtn) {
      archiveBtn.addEventListener("click", async () => {
        const confirmed = await showConfirm({
          title: "Archivar Space",
          text: "El Space deja de aparecer en la lista, pero conserva sus Canvases y contenido.",
          confirmLabel: "Archivar",
        });
        if (!confirmed) return;
        try {
          await apiJson(`${apiBase}/mind/spaces/${spaceId}/archive`, { method: "POST" });
          showToast("Space archivado", "success");
          await loadSpace();
        } catch (err) {
          showToast(err.message || "Error al archivar el Space", "error");
        }
      });
    }

    const restoreBtn = bodyEl.querySelector("#mind-space-restore");
    if (restoreBtn) {
      restoreBtn.addEventListener("click", async () => {
        try {
          await apiJson(`${apiBase}/mind/spaces/${spaceId}/restore`, { method: "POST" });
          showToast("Space restaurado", "success");
          await loadSpace();
        } catch (err) {
          showToast(err.message || "Error al restaurar el Space", "error");
        }
      });
    }

    bodyEl.querySelector("#mind-canvases-list").addEventListener("click", async (e) => {
      const button = e.target.closest("[data-action]");
      if (!button) return;
      const canvasId = button.dataset.id;
      const canvas = canvases.find((c) => c.id === canvasId);

      if (button.dataset.action === "rename") {
        const result = await showFormModal({
          title: "Renombrar Canvas",
          fields: [
            { name: "title", label: "Título", value: canvas.title, required: true, maxlength: 200 },
            {
              name: "description",
              label: "Descripción",
              value: canvas.description || "",
              maxlength: 2000,
            },
          ],
        });
        if (!result.ok) return;
        try {
          await apiJson(`${apiBase}/mind/canvases/${canvasId}`, {
            method: "PATCH",
            body: {
              title: result.values.title.trim(),
              description: result.values.description.trim() || null,
            },
          });
          showToast("Canvas actualizado", "success");
          await loadCanvases();
        } catch (err) {
          showToast(err.message || "Error al actualizar el Canvas", "error");
        }
        return;
      }

      if (button.dataset.action === "archive" || button.dataset.action === "restore") {
        const archiving = button.dataset.action === "archive";
        if (archiving) {
          const confirmed = await showConfirm({
            title: "Archivar Canvas",
            text: "El Canvas deja de aparecer en la lista, pero conserva sus Cards.",
            confirmLabel: "Archivar",
          });
          if (!confirmed) return;
        }
        try {
          await apiJson(
            `${apiBase}/mind/canvases/${canvasId}/${archiving ? "archive" : "restore"}`,
            { method: "POST" }
          );
          showToast(archiving ? "Canvas archivado" : "Canvas restaurado", "success");
          await loadCanvases();
        } catch (err) {
          showToast(err.message || "Error al cambiar el estado del Canvas", "error");
        }
      }
    });

    const canvasForm = bodyEl.querySelector("#mind-new-canvas");
    const canvasTitleEl = bodyEl.querySelector("#mind-canvas-title");
    const canvasDescEl = bodyEl.querySelector("#mind-canvas-description");
    const canvasCreateBtn = bodyEl.querySelector("#mind-canvas-create");
    const canvasStatusEl = bodyEl.querySelector("#mind-canvas-status");

    canvasForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = canvasTitleEl.value.trim();
      if (!title) {
        canvasStatusEl.textContent = "El título del Canvas no puede estar vacío.";
        showToast("El título del Canvas no puede estar vacío", "warning");
        canvasTitleEl.focus();
        return;
      }
      canvasCreateBtn.disabled = true;
      canvasCreateBtn.textContent = "Creando…";
      try {
        const canvas = await apiJson(`${apiBase}/mind/spaces/${spaceId}/canvases`, {
          method: "POST",
          body: { title, description: canvasDescEl.value.trim() || null },
        });
        canvasTitleEl.value = "";
        canvasDescEl.value = "";
        canvasStatusEl.textContent = "Canvas creado.";
        showToast("Canvas creado", "success");
        await loadCanvases();
        location.hash = `#/mind/canvases/${canvas.id}`;
      } catch (err) {
        canvasStatusEl.textContent = `No se pudo crear: ${err.message}`;
        showToast(err.message || "Error al crear el Canvas", "error");
      } finally {
        canvasCreateBtn.disabled = false;
        canvasCreateBtn.textContent = "Crear Canvas";
      }
    });
  }

  await loadSpace();
}

function _canvasItem(canvas) {
  return `
    <li class="mind-space">
      <div class="mind-space__main">
        <h3 class="mind-space__name">
          <a href="#/mind/canvases/${canvas.id}">${escapeHtml(canvas.title)}</a>
        </h3>
        ${canvas.description ? `<p class="text-secondary mind-space__desc">${escapeHtml(canvas.description)}</p>` : ""}
        <p class="mind-space__meta">Actualizado ${formatDate(canvas.updated_at)}</p>
      </div>
      <div class="btn-group">
        <a class="btn btn--secondary btn--sm" href="#/mind/canvases/${canvas.id}">Abrir</a>
        <button class="btn btn--secondary btn--sm" data-action="rename" data-id="${canvas.id}">Renombrar</button>
        ${
          canvas.status === "archived"
            ? `<button class="btn btn--secondary btn--sm" data-action="restore" data-id="${canvas.id}">Restaurar</button>`
            : `<button class="btn btn--secondary btn--sm" data-action="archive" data-id="${canvas.id}">Archivar</button>`
        }
      </div>
    </li>
  `;
}
