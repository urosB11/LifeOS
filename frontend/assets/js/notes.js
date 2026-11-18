// Life OS — vista de Notas y Etiquetas

export async function renderNotesView(container, apiBase) {
  let tags = [];

  container.innerHTML = `
    <div class="form-row" style="margin-bottom: 16px;">
      <div class="form-group" style="flex: 2; min-width: 260px;">
        <label for="note-title">T&iacute;tulo</label>
        <input type="text" id="note-title" placeholder="T&iacute;tulo de la nota">
      </div>
      <div class="form-group" style="flex: 1; min-width: 200px;">
        <label for="note-tag">Etiqueta (opcional)</label>
        <select id="note-tag"><option value="">Ninguna</option></select>
      </div>
      <button class="btn btn--primary" id="note-create-btn">Crear nota</button>
    </div>

    <div class="form-group" style="margin-bottom: 16px;">
      <label for="note-content">Contenido</label>
      <textarea id="note-content" rows="4" placeholder="Escriba aqu&iacute; el contenido de la nota..."></textarea>
    </div>

    <div style="margin-bottom: 12px; display:flex; gap: 8px; flex-wrap: wrap; align-items:center;">
      <span style="font-size:0.9375rem; color:var(--text-secondary); margin-right:8px;">Filtrar por etiqueta:</span>
      <select id="note-filter-tag" aria-label="Filtrar por etiqueta" style="padding:6px 10px; border:1px solid var(--border); border-radius:var(--radius); background:var(--surface);">
        <option value="">Todas las etiquetas</option>
      </select>
      <input type="text" id="note-filter-search" aria-label="Buscar en t&iacute;tulo y contenido" placeholder="Buscar en t&iacute;tulo y contenido" style="padding:6px 10px; border:1px solid var(--border); border-radius:var(--radius); background:var(--surface); flex:1; min-width:200px;">
    </div>

    <h2 style="margin-top: 0;">Notas</h2>
    <div id="notes-list" class="empty-state">Cargando notas...</div>

    <h3 style="margin-top: 32px;">Etiquetas</h3>
    <div class="form-row" style="margin-bottom: 16px;">
      <div class="form-group" style="flex: 1; min-width: 200px;">
        <label for="tag-name">Nueva etiqueta</label>
        <input type="text" id="tag-name" placeholder="Nombre de la etiqueta">
      </div>
      <button class="btn btn--primary" id="tag-create-btn">Crear etiqueta</button>
    </div>
    <div id="tags-list" class="empty-state">Cargando etiquetas...</div>
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
    const res = await fetch(`${apiBase}/notes/tags`);
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
  }

  let currentNotes = [];

  async function loadNotes() {
    const params = new URLSearchParams();
    if (filterTagSelect.value) params.set("tag", filterTagSelect.value);
    if (filterSearchInput.value.trim()) params.set("search", filterSearchInput.value.trim());

    const res = await fetch(`${apiBase}/notes?${params}`);
    const notes = await res.json();
    currentNotes = notes;

    if (notes.length === 0) {
      notesListEl.innerHTML = `<p class="empty-state">No hay notas que coincidan con el filtro.</p>`;
      return;
    }

    // Cargar tags para mostrar nombres
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
            // Recortar primero y escapar después: escapar y luego recortar
            // corta entidades HTML a la mitad.
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
  }

  async function renderTagsList() {
    if (tags.length === 0) {
      tagsListEl.innerHTML = `<p class="empty-state">A&uacute;n no hay etiquetas.</p>`;
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
              <td>—</td>
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
    if (!title) return;

    const body = { title, content: contentInput.value || "" };
    const tagId = tagSelect.value;
    if (tagId) {
      // Crear nota primero, luego asignar etiqueta
    }

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

      await loadNotes();
    } else {
      const err = await res.json();
      alert(err.detail || "Error al crear nota");
    }
  });

  tagCreateBtn.addEventListener("click", async () => {
    const name = tagNameInput.value.trim();
    if (!name) return;

    const res = await fetch(`${apiBase}/notes/tags`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    if (res.ok) {
      tagNameInput.value = "";
      await loadTags();
    } else {
      const err = await res.json();
      alert(err.detail || "Error al crear etiqueta");
    }
  });

  filterTagSelect.addEventListener("change", loadNotes);
  filterSearchInput.addEventListener("input", loadNotes);

  window.appNotes = {
    async viewNote(noteId) {
      const res = await fetch(`${apiBase}/notes/${noteId}`);
      if (!res.ok) return;
      const note = await res.json();
      // alert muestra texto plano: usar nombres de etiqueta, no HTML
      const tagNames = (note.tag_links || [])
        .map(lt => lt.tag && lt.tag.name)
        .filter(Boolean)
        .join(", ") || "—";
      alert(
        `Título: ${note.title}\n\nContenido:\n${note.content}\n\nEtiquetas: ${tagNames}`
      );
    },

    async viewTagNotes(tagId) {
      const res = await fetch(`${apiBase}/notes/tags/${tagId}/notes`);
      if (!res.ok) return;
      const notes = await res.json();
      const names = notes.map(n => n.title).join("\n") || "(ninguna)";
      alert(`Notas con esta etiqueta:\n\n${names}`);
    },

    async deleteNote(id) {
      const note = currentNotes.find(n => n.id === id);
      const title = note ? note.title : "";
      if (!confirm(`¿Eliminar la nota "${title}"?`)) return;
      const res = await fetch(`${apiBase}/notes/${id}`, { method: "DELETE" });
      if (res.ok || res.status === 204) {
        await loadNotes();
      } else {
        const err = await res.json();
        alert(err.detail || "Error al eliminar nota");
      }
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