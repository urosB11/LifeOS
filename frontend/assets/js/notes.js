// Life OS — vista de Notas y Etiquetas (Fase 8C)
//
// Listado, editor, etiquetas, relaciones y acciones. Usa los componentes
// compartidos de 8A.

import { showToast, showConfirm } from "./app.js";

export async function renderNotesView(container, apiBase) {
  let tags = [];

  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Notas</h1>
        <p class="subtitle">Tus notas y etiquetas</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3 style="margin-top:0;">Nueva nota</h3>
      <div class="form-row" style="margin-top:12px;">
        <div class="form-group" style="flex:2; min-width:260px;">
          <label for="note-title">T&iacute;tulo</label>
          <input type="text" id="note-title" placeholder="T&iacute;tulo de la nota" required>
        </div>
        <div class="form-group" style="flex:1; min-width:200px;">
          <label for="note-tag">Etiqueta (opcional)</label>
          <select id="note-tag"><option value="">Ninguna</option></select>
        </div>
      </div>
      <div class="form-group">
        <label for="note-content">Contenido</label>
        <textarea id="note-content" rows="4" placeholder="Escriba aqu&iacute; el contenido de la nota..."></textarea>
      </div>
      <button class="btn btn--primary" id="note-create-btn">Crear nota</button>
    </div>

    <div class="filters-bar" style="margin-bottom: 16px;">
      <span class="text-secondary" style="font-size:0.9375rem;">Filtrar por etiqueta:</span>
      <select id="note-filter-tag" aria-label="Filtrar por etiqueta">
        <option value="">Todas las etiquetas</option>
      </select>
      <input type="text" id="note-filter-search" aria-label="Buscar en t&iacute;tulo y contenido" placeholder="Buscar en t&iacute;tulo y contenido">
    </div>

    <div id="notes-list" class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando notas&hellip;</p>
    </div>

    <h2 style="margin-top: 32px;">Etiquetas</h2>
    <div class="card" style="margin-bottom: 16px;">
      <h3 style="margin-top:0;">Nueva etiqueta</h3>
      <div class="form-row" style="margin-top:12px;">
        <div class="form-group" style="flex:1; min-width:200px;">
          <label for="tag-name">Nombre de la etiqueta</label>
          <input type="text" id="tag-name" placeholder="Nombre de la etiqueta">
        </div>
        <div class="form-group" style="flex:0; min-width:auto; align-self:flex-end;">
          <button class="btn btn--primary" id="tag-create-btn">Crear etiqueta</button>
        </div>
      </div>
    </div>
    <div id="tags-list" class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando etiquetas&hellip;</p>
    </div>
  `;

  const notesListEl = container.querySelector("#notes-list");
  const tagsListEl = container.querySelector("#tags-list");
  const titleInput = container.querySelector("#note-title");
  const contentInput = container.querySelector("#note-content");
  const tagSelect = container.querySelector("#note-tag");
  const createBtn = container.querySelector("#note-create-btn");
  const filterTagSelect = container.querySelector("#note-filter-tag");
  const filterSearchInput = container.querySelector("#note-filter-search");
  const tagNameInput = container.querySelector("#tag-name");
  const tagCreateBtn = container.querySelector("#tag-create-btn");

  async function loadTags() {
    try {
      const res = await fetch(`${apiBase}/notes/tags`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      tags = await res.json();

      tagSelect.innerHTML = '<option value="">Ninguna</option>';
      filterTagSelect.innerHTML = '<option value="">Todas las etiquetas</option>';
      tags.forEach(t => {
        const opt1 = document.createElement("option");
        opt1.value = t.id;
        opt1.textContent = t.name;
        tagSelect.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = t.id;
        opt2.textContent = t.name;
        filterTagSelect.appendChild(opt2);
      });

      renderTagsList();
    } catch (error) {
      tagsListEl.innerHTML = `
        <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
        <p class="empty-state__title">Error al cargar etiquetas</p>
      `;
    }
  }

  let currentNotes = [];

  async function loadNotes() {
    notesListEl.innerHTML = `
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando&hellip;</p>
    `;
    try {
      const params = new URLSearchParams();
      if (filterTagSelect.value) params.set("tag", filterTagSelect.value);
      if (filterSearchInput.value.trim()) params.set("search", filterSearchInput.value.trim());

      const res = await fetch(`${apiBase}/notes?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const notes = await res.json();
      currentNotes = notes;

      if (notes.length === 0) {
        notesListEl.innerHTML = `
          <div class="empty-state__icon" aria-hidden="true">&#128221;</div>
          <p class="empty-state__title">No hay notas</p>
          <p class="empty-state__text">No hay notas que coincidan con el filtro actual.</p>
        `;
        return;
      }

      const tagMap = {};
      tags.forEach(t => { tagMap[t.id] = t.name; });

      notesListEl.innerHTML = `
        <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>T&iacute;tulo</th>
              <th>Contenido</th>
              <th>Etiquetas</th>
              <th>Modificada</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            ${notes.map(n => {
              const noteTags = (n.tag_links || []).map(lt => lt.tag && lt.tag.name).filter(Boolean);
              const preview = n.content ? escapeHtml(n.content.substring(0, 80)) : "&mdash;";
              const truncated = n.content && n.content.length > 80 ? "…" : "";
              return `
                <tr id="note-row-${n.id}">
                  <td><strong>${escapeHtml(n.title)}</strong></td>
                  <td>${preview}${truncated}</td>
                  <td>${noteTags.length ? noteTags.map(t => `<span class="badge badge--status">${escapeHtml(t)}</span>`).join(" ") : "&mdash;"}</td>
                  <td>${n.updated_at}</td>
                  <td>
                    <div class="btn-group">
                      <button class="btn btn--secondary btn--sm" onclick="appNotes.viewNote('${n.id}')">Ver</button>
                      <button class="btn btn--danger btn--sm" onclick="appNotes.deleteNote('${n.id}')">Eliminar</button>
                    </div>
                  </td>
                </tr>
              `;
            }).join("")}
          </tbody>
        </table>
        </div>
      `;
    } catch (error) {
      notesListEl.innerHTML = `
        <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
        <p class="empty-state__title">Error al cargar</p>
        <p class="empty-state__text">No se pudieron cargar las notas. Verifica que el servicio est&eacute; activo.</p>
        <button class="btn btn--secondary" onclick="appNotes.reload()">Reintentar</button>
      `;
    }
  }

  async function renderTagsList() {
    if (tags.length === 0) {
      tagsListEl.innerHTML = `
        <div class="empty-state__icon" aria-hidden="true">&#127991;</div>
        <p class="empty-state__title">No hay etiquetas</p>
        <p class="empty-state__text">Crea la primera etiqueta con el formulario de arriba.</p>
      `;
      return;
    }
    tagsListEl.innerHTML = `
      <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>Nombre</th><th>Notas</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          ${tags.map(t => `
            <tr>
              <td><strong>${escapeHtml(t.name)}</strong></td>
              <td>&mdash;</td>
              <td><button class="btn btn--secondary btn--sm" onclick="appNotes.viewTagNotes('${t.id}')">Ver notas</button></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      </div>
    `;
  }

  createBtn.addEventListener("click", async () => {
    const title = titleInput.value.trim();
    if (!title) {
      showToast("El título de la nota no puede estar vacío", "warning");
      titleInput.focus();
      return;
    }

    const body = { title, content: contentInput.value || "" };
    const tagId = tagSelect.value;

    createBtn.disabled = true;
    createBtn.textContent = "Creando…";
    try {
      const res = await fetch(`${apiBase}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const note = await res.json();
        titleInput.value = "";
        contentInput.value = "";
        tagSelect.value = "";

        if (tagId) {
          await fetch(`${apiBase}/notes/${note.id}/tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: tagId }),
          });
        }

        showToast("Nota creada", "success");
        await loadNotes();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error al crear nota", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    } finally {
      createBtn.disabled = false;
      createBtn.textContent = "Crear nota";
    }
  });

  tagCreateBtn.addEventListener("click", async () => {
    const name = tagNameInput.value.trim();
    if (!name) {
      showToast("El nombre de la etiqueta no puede estar vacío", "warning");
      tagNameInput.focus();
      return;
    }

    tagCreateBtn.disabled = true;
    tagCreateBtn.textContent = "Creando…";
    try {
      const res = await fetch(`${apiBase}/notes/tags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });

      if (res.ok) {
        tagNameInput.value = "";
        showToast("Etiqueta creada", "success");
        await loadTags();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error al crear etiqueta", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    } finally {
      tagCreateBtn.disabled = false;
      tagCreateBtn.textContent = "Crear etiqueta";
    }
  });

  filterTagSelect.addEventListener("change", loadNotes);
  filterSearchInput.addEventListener("input", loadNotes);

  window.appNotes = {
    async viewNote(noteId) {
      try {
        const res = await fetch(`${apiBase}/notes/${noteId}`);
        if (!res.ok) return;
        const note = await res.json();
        const tagNames = (note.tag_links || [])
          .map(lt => lt.tag && lt.tag.name)
          .filter(Boolean)
          .join(", ") || "—";

        // Usar modal de 8A para mostrar la nota
        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
          <div class="modal" style="max-width:600px;" role="dialog" aria-modal="true" aria-labelledby="note-view-title">
            <h2 class="modal__title" id="note-view-title">${escapeHtml(note.title)}</h2>
            <div style="margin:16px 0; padding:16px; background:var(--bg); border:1px solid var(--border); border-radius:var(--radius); max-height:50vh; overflow-y:auto;">
              <p style="white-space:pre-wrap; margin:0; font-size:0.9375rem;">${escapeHtml(note.content)}</p>
            </div>
            <p class="text-secondary" style="font-size:0.875rem; margin-bottom:16px;">Etiquetas: ${escapeHtml(tagNames)}</p>
            <div class="modal__actions">
              <button class="btn btn--secondary" data-action="close">Cerrar</button>
            </div>
          </div>
        `;
        document.body.appendChild(overlay);

        const close = () => overlay.remove();
        overlay.addEventListener("click", (e) => {
          if (e.target === overlay) close();
          if (e.target.closest('[data-action="close"]')) close();
        });
        const onKey = (e) => {
          if (e.key === "Escape") {
            close();
            document.removeEventListener("keydown", onKey);
          }
        };
        document.addEventListener("keydown", onKey);
        overlay.querySelector('[data-action="close"]').focus();
      } catch (error) {
        showToast("Error al cargar la nota", "error");
      }
    },

    async viewTagNotes(tagId) {
      try {
        const res = await fetch(`${apiBase}/notes/tags/${tagId}/notes`);
        if (!res.ok) return;
        const notes = await res.json();
        const tag = tags.find(t => t.id === tagId);
        const tagName = tag ? tag.name : "etiqueta";

        if (notes.length === 0) {
          showToast(`No hay notas con la etiqueta "${tagName}"`, "info");
          return;
        }

        const overlay = document.createElement("div");
        overlay.className = "modal-overlay";
        overlay.innerHTML = `
          <div class="modal" style="max-width:500px;" role="dialog" aria-modal="true" aria-labelledby="tag-notes-title">
            <h2 class="modal__title" id="tag-notes-title">Notas: ${escapeHtml(tagName)}</h2>
            <div style="margin:16px 0; max-height:50vh; overflow-y:auto;">
              ${notes.map(n => `
                <div style="padding:8px 0; border-bottom:1px solid var(--border);">
                  <strong>${escapeHtml(n.title)}</strong>
                </div>
              `).join("")}
            </div>
            <div class="modal__actions">
              <button class="btn btn--secondary" data-action="close">Cerrar</button>
            </div>
          </div>
        `;
        document.body.appendChild(overlay);

        const close = () => overlay.remove();
        overlay.addEventListener("click", (e) => {
          if (e.target === overlay) close();
          if (e.target.closest('[data-action="close"]')) close();
        });
        const onKey = (e) => {
          if (e.key === "Escape") {
            close();
            document.removeEventListener("keydown", onKey);
          }
        };
        document.addEventListener("keydown", onKey);
        overlay.querySelector('[data-action="close"]').focus();
      } catch (error) {
        showToast("Error al cargar las notas", "error");
      }
    },

    async deleteNote(id) {
      const note = currentNotes.find(n => n.id === id);
      const title = note ? note.title : "";
      const confirmed = await showConfirm({
        title: "Eliminar nota",
        text: `¿Eliminar la nota "${title}"?`,
        confirmLabel: "Eliminar",
        danger: true,
      });
      if (!confirmed) return;

      try {
        const res = await fetch(`${apiBase}/notes/${id}`, { method: "DELETE" });
        if (res.ok || res.status === 204) {
          showToast("Nota eliminada", "success");
          await loadNotes();
        } else {
          const err = await res.json();
          showToast(err.detail || "Error al eliminar nota", "error");
        }
      } catch (error) {
        showToast("Error de conexión", "error");
      }
    },

    reload() {
      loadNotes();
    },
  };

  await loadTags();
  await loadNotes();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
