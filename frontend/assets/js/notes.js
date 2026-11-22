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
      <button class="btn btn--primary" id="note-new-btn" aria-expanded="false" aria-controls="note-create-panel">
        + Nueva nota
      </button>
    </div>

    <section class="task-panel" id="note-create-panel" aria-labelledby="note-create-title" hidden>
      <form id="note-create-form" novalidate>
        <h2 class="task-panel__title" id="note-create-title">Nueva nota</h2>
        <div class="form-row">
          <div class="form-group">
            <label for="note-title">T&iacute;tulo <span class="text-secondary">(obligatorio)</span></label>
            <input type="text" id="note-title" placeholder="T&iacute;tulo de la nota" maxlength="200" required>
          </div>
          <div class="form-group">
            <label for="note-tag">Etiqueta (opcional)</label>
            <select id="note-tag"><option value="">Ninguna</option></select>
          </div>
        </div>
        <div class="form-group">
          <label for="note-content">Contenido</label>
          <textarea id="note-content" rows="4" maxlength="100000" placeholder="Escribe el contenido de la nota..."></textarea>
        </div>
        <div class="btn-group">
          <button type="submit" class="btn btn--primary" id="note-create-btn">Crear nota</button>
          <button type="button" class="btn btn--secondary" id="note-cancel-btn">Cancelar</button>
          <span class="task-panel__error" id="note-create-error" role="alert" tabindex="-1"></span>
        </div>
      </form>
    </section>

    <div class="filters-bar" style="margin-bottom: 16px;">
      <span class="text-secondary" style="font-size:0.9375rem;">Filtrar por etiqueta:</span>
      <select id="note-filter-tag" aria-label="Filtrar por etiqueta">
        <option value="">Todas las etiquetas</option>
      </select>
      <input type="text" id="note-filter-search" aria-label="Buscar en t&iacute;tulo y contenido" placeholder="Buscar en t&iacute;tulo y contenido">
    </div>

    <div id="notes-list" class="empty-state" tabindex="-1">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando notas&hellip;</p>
    </div>

    <div class="section-header notes-section-header">
      <h2>Etiquetas</h2>
      <button class="btn btn--secondary" id="tag-new-btn" aria-expanded="false" aria-controls="tag-create-panel">
        + Nueva etiqueta
      </button>
    </div>
    <section class="task-panel" id="tag-create-panel" aria-labelledby="tag-create-title" hidden>
      <form id="tag-create-form" novalidate>
        <h2 class="task-panel__title" id="tag-create-title">Nueva etiqueta</h2>
        <div class="form-row">
          <div class="form-group">
            <label for="tag-name">Nombre de la etiqueta</label>
            <input type="text" id="tag-name" placeholder="Nombre de la etiqueta" maxlength="100" required>
          </div>
        </div>
        <div class="btn-group">
          <button type="submit" class="btn btn--primary" id="tag-create-btn">Crear etiqueta</button>
          <button type="button" class="btn btn--secondary" id="tag-cancel-btn">Cancelar</button>
          <span class="task-panel__error" id="tag-create-error" role="alert" tabindex="-1"></span>
        </div>
      </form>
    </section>
    <div id="tags-list" class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando etiquetas&hellip;</p>
    </div>
  `;

  const notesListEl = container.querySelector("#notes-list");
  const tagsListEl = container.querySelector("#tags-list");
  const noteCreatePanel = container.querySelector("#note-create-panel");
  const noteCreateForm = container.querySelector("#note-create-form");
  const titleInput = container.querySelector("#note-title");
  const contentInput = container.querySelector("#note-content");
  const tagSelect = container.querySelector("#note-tag");
  const createBtn = container.querySelector("#note-create-btn");
  const noteCancelBtn = container.querySelector("#note-cancel-btn");
  const noteCreateError = container.querySelector("#note-create-error");
  const noteNewBtn = container.querySelector("#note-new-btn");
  const filterTagSelect = container.querySelector("#note-filter-tag");
  const filterSearchInput = container.querySelector("#note-filter-search");
  const tagCreatePanel = container.querySelector("#tag-create-panel");
  const tagCreateForm = container.querySelector("#tag-create-form");
  const tagNameInput = container.querySelector("#tag-name");
  const tagCreateBtn = container.querySelector("#tag-create-btn");
  const tagCancelBtn = container.querySelector("#tag-cancel-btn");
  const tagCreateError = container.querySelector("#tag-create-error");
  const tagNewBtn = container.querySelector("#tag-new-btn");

  const noteDraft = { title: "", content: "", tagId: "" };
  let noteCreatePending = false;
  let tagCreatePending = false;
  let noteDialog = null;

  function captureNoteDraft() {
    noteDraft.title = titleInput.value;
    noteDraft.content = contentInput.value;
    noteDraft.tagId = tagSelect.value;
  }

  function setNoteCreatePending(pending) {
    noteCreatePending = pending;
    titleInput.disabled = pending;
    contentInput.disabled = pending;
    tagSelect.disabled = pending;
    createBtn.disabled = pending;
    noteCancelBtn.disabled = pending;
    noteNewBtn.disabled = pending;
    createBtn.textContent = pending ? "Creando…" : "Crear nota";
  }

  function closeNoteCreatePanel() {
    if (noteCreatePending) return;
    noteCreatePanel.hidden = true;
    noteNewBtn.setAttribute("aria-expanded", "false");
    noteNewBtn.textContent = "+ Nueva nota";
    noteDraft.title = "";
    noteDraft.content = "";
    noteDraft.tagId = "";
    titleInput.value = "";
    contentInput.value = "";
    tagSelect.value = "";
    titleInput.removeAttribute("aria-invalid");
    noteCreateError.textContent = "";
    noteNewBtn.focus();
  }

  function openNoteCreatePanel() {
    noteDraft.title = "";
    noteDraft.content = "";
    noteDraft.tagId = "";
    titleInput.value = "";
    contentInput.value = "";
    tagSelect.value = "";
    titleInput.removeAttribute("aria-invalid");
    noteCreateError.textContent = "";
    noteCreatePanel.hidden = false;
    noteNewBtn.setAttribute("aria-expanded", "true");
    noteNewBtn.textContent = "Cerrar";
    titleInput.focus();
  }

  function setTagCreatePending(pending) {
    tagCreatePending = pending;
    tagNameInput.disabled = pending;
    tagCreateBtn.disabled = pending;
    tagCancelBtn.disabled = pending;
    tagNewBtn.disabled = pending;
    tagCreateBtn.textContent = pending ? "Creando…" : "Crear etiqueta";
  }

  function closeTagCreatePanel() {
    if (tagCreatePending) return;
    tagCreatePanel.hidden = true;
    tagNewBtn.setAttribute("aria-expanded", "false");
    tagNewBtn.textContent = "+ Nueva etiqueta";
    tagNameInput.value = "";
    tagNameInput.removeAttribute("aria-invalid");
    tagCreateError.textContent = "";
    tagNewBtn.focus();
  }

  function openTagCreatePanel() {
    tagNameInput.value = "";
    tagNameInput.removeAttribute("aria-invalid");
    tagCreateError.textContent = "";
    tagCreatePanel.hidden = false;
    tagNewBtn.setAttribute("aria-expanded", "true");
    tagNewBtn.textContent = "Cerrar";
    tagNameInput.focus();
  }

  async function loadTags() {
    try {
      const res = await fetch(`${apiBase}/notes/tags`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      tags = await res.json();

      const selectedTag = tagSelect.value;
      const selectedFilter = filterTagSelect.value;
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
      if (tags.some((tag) => tag.id === selectedTag)) tagSelect.value = selectedTag;
      if (tags.some((tag) => tag.id === selectedFilter)) filterTagSelect.value = selectedFilter;

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
                      <button type="button" class="btn btn--secondary btn--sm" data-action="edit-note" data-id="${n.id}">Editar</button>
                      <button type="button" class="btn btn--secondary btn--sm" data-action="view-note" data-id="${n.id}">Ver</button>
                      <button type="button" class="btn btn--danger btn--sm" data-action="delete-note" data-id="${n.id}">Eliminar</button>
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
        <p class="empty-state__text">Usa + Nueva etiqueta para crear la primera.</p>
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

  noteNewBtn.addEventListener("click", () => {
    if (noteCreatePanel.hidden) openNoteCreatePanel();
    else closeNoteCreatePanel();
  });
  noteCancelBtn.addEventListener("click", closeNoteCreatePanel);
  noteCreatePanel.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !noteCreatePanel.hidden && !noteCreatePending) {
      event.stopPropagation();
      closeNoteCreatePanel();
    }
  });
  noteCreateForm.addEventListener("input", () => {
    captureNoteDraft();
    noteCreateError.textContent = "";
    titleInput.removeAttribute("aria-invalid");
  });
  noteCreateForm.addEventListener("change", captureNoteDraft);
  noteCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (noteCreatePending) return;
    captureNoteDraft();
    const title = noteDraft.title.trim();
    if (!title) {
      noteCreateError.textContent = "El título de la nota no puede estar vacío.";
      titleInput.setAttribute("aria-invalid", "true");
      titleInput.focus();
      return;
    }

    const tagId = noteDraft.tagId;
    setNoteCreatePending(true);
    noteCreateError.textContent = "";
    titleInput.removeAttribute("aria-invalid");
    try {
      const res = await fetch(`${apiBase}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content: noteDraft.content || "" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(formatApiDetail(err.detail, "No se pudo crear la nota."));
      }

      const note = await res.json();
      let tagAssignmentError = "";
      if (tagId) {
        try {
          const tagRes = await fetch(`${apiBase}/notes/${note.id}/tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id: tagId }),
          });
          if (!tagRes.ok) {
            const err = await tagRes.json().catch(() => ({}));
            tagAssignmentError = formatApiDetail(err.detail, "No se pudo asignar la etiqueta.");
          }
        } catch (error) {
          tagAssignmentError = "No se pudo asignar la etiqueta.";
        }
      }

      setNoteCreatePending(false);
      closeNoteCreatePanel();
      await loadNotes();
      showToast(
        tagAssignmentError ? `Nota creada. ${tagAssignmentError}` : "Nota creada",
        tagAssignmentError ? "warning" : "success"
      );
    } catch (error) {
      noteCreateError.textContent = error.message || "Error de conexión. Inténtalo de nuevo.";
      noteCreateError.focus();
    } finally {
      setNoteCreatePending(false);
    }
  });

  tagNewBtn.addEventListener("click", () => {
    if (tagCreatePanel.hidden) openTagCreatePanel();
    else closeTagCreatePanel();
  });
  tagCancelBtn.addEventListener("click", closeTagCreatePanel);
  tagCreatePanel.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !tagCreatePanel.hidden && !tagCreatePending) {
      event.stopPropagation();
      closeTagCreatePanel();
    }
  });
  tagCreateForm.addEventListener("input", () => {
    tagCreateError.textContent = "";
    tagNameInput.removeAttribute("aria-invalid");
  });
  tagCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (tagCreatePending) return;
    const name = tagNameInput.value.trim();
    if (!name) {
      tagCreateError.textContent = "El nombre de la etiqueta no puede estar vacío.";
      tagNameInput.setAttribute("aria-invalid", "true");
      tagNameInput.focus();
      return;
    }

    setTagCreatePending(true);
    tagCreateError.textContent = "";
    tagNameInput.removeAttribute("aria-invalid");
    try {
      const res = await fetch(`${apiBase}/notes/tags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(formatApiDetail(err.detail, "No se pudo crear la etiqueta."));
      }
      setTagCreatePending(false);
      closeTagCreatePanel();
      await loadTags();
      showToast("Etiqueta creada", "success");
    } catch (error) {
      tagCreateError.textContent = error.message || "Error de conexión. Inténtalo de nuevo.";
      tagCreateError.focus();
    } finally {
      setTagCreatePending(false);
    }
  });

  filterTagSelect.addEventListener("change", loadNotes);
  filterSearchInput.addEventListener("input", loadNotes);

  function noteDialogIsDirty() {
    return noteDialog && (
      noteDialog.draft.title !== noteDialog.note.title ||
      noteDialog.draft.content !== noteDialog.note.content
    );
  }

  function renderNoteDialog(focusSelector) {
    if (!noteDialog) return;
    const note = noteDialog.note;
    const tagNames = (note.tag_links || [])
      .map((link) => link.tag && link.tag.name)
      .filter(Boolean)
      .join(", ") || "—";
    const editor = noteDialog.mode === "edit";
    noteDialog.overlay.innerHTML = `
      <div class="modal notes-modal" role="dialog" aria-modal="true" aria-labelledby="note-dialog-title">
        <h2 class="modal__title" id="note-dialog-title">${escapeHtml(editor ? "Editar nota" : note.title)}</h2>
        ${
          editor
            ? `
              <form id="note-edit-form" novalidate aria-busy="${noteDialog.pending}">
                <div class="form-group">
                  <label for="note-edit-title">T&iacute;tulo</label>
                  <input type="text" id="note-edit-title" maxlength="200" required
                         ${noteDialog.error && !noteDialog.draft.title.trim() ? 'aria-invalid="true"' : ""}>
                </div>
                <div class="form-group">
                  <label for="note-edit-content">Contenido</label>
                  <textarea id="note-edit-content" rows="10" maxlength="100000">${escapeHtml(noteDialog.draft.content)}</textarea>
                </div>
                <p class="notes-modal__error" role="alert" tabindex="-1">${escapeHtml(noteDialog.error)}</p>
                <div class="modal__actions notes-modal__actions">
                  <button type="submit" class="btn btn--primary" id="note-edit-save"
                          aria-disabled="${noteDialog.pending ? "true" : "false"}">
                    ${noteDialog.pending ? "Guardando…" : "Guardar cambios"}
                  </button>
                  <button type="button" class="btn btn--secondary" data-action="cancel-note-edit" ${noteDialog.pending ? "disabled" : ""}>
                    Cancelar
                  </button>
                </div>
              </form>
            `
            : `
              <div class="notes-modal__content">${note.content ? escapeHtml(note.content) : '<span class="text-secondary">Sin contenido.</span>'}</div>
              <p class="text-secondary notes-modal__tags">Etiquetas: ${escapeHtml(tagNames)}</p>
              <div class="modal__actions notes-modal__actions">
                <button type="button" class="btn btn--primary" data-action="edit-note-mode">Editar</button>
                <button type="button" class="btn btn--secondary" data-action="close-note-dialog">Cerrar</button>
              </div>
            `
        }
      </div>
    `;
    if (noteDialog.pending) {
      noteDialog.overlay.querySelectorAll("input, textarea").forEach((input) => {
        input.readOnly = true;
      });
    }
    const titleInput = noteDialog.overlay.querySelector("#note-edit-title");
    if (titleInput) titleInput.value = noteDialog.draft.title;
    const target = focusSelector && noteDialog.overlay.querySelector(focusSelector);
    if (target) target.focus();
  }

  function restoreNoteDialogFocus(noteId, action) {
    const trigger = Array.from(notesListEl.querySelectorAll(`[data-action="${action}"]`))
      .find((button) => button.dataset.id === noteId);
    (trigger || filterSearchInput).focus();
  }

  function closeNoteDialog() {
    if (!noteDialog) return;
    const { note, overlay, returnAction } = noteDialog;
    overlay.remove();
    noteDialog = null;
    restoreNoteDialogFocus(note.id, returnAction);
  }

  async function requestCloseNoteDialog() {
    if (!noteDialog || noteDialog.pending) return;
    if (noteDialog.mode === "edit" && noteDialogIsDirty()) {
      const confirmed = await showConfirm({
        title: "Descartar cambios",
        text: "Los cambios de esta nota todavía no se guardaron.",
        confirmLabel: "Descartar",
        danger: true,
      });
      if (!confirmed) return;
    }
    closeNoteDialog();
  }

  async function cancelNoteEdit() {
    if (!noteDialog || noteDialog.pending) return;
    if (noteDialogIsDirty()) {
      const confirmed = await showConfirm({
        title: "Descartar cambios",
        text: "Los cambios de esta nota todavía no se guardaron.",
        confirmLabel: "Descartar",
        danger: true,
      });
      if (!confirmed) return;
    }
    noteDialog.mode = "view";
    noteDialog.error = "";
    noteDialog.draft = { title: noteDialog.note.title, content: noteDialog.note.content || "" };
    renderNoteDialog('[data-action="edit-note-mode"]');
  }

  async function submitNoteEdit() {
    if (!noteDialog || noteDialog.pending) return;
    const titleInput = noteDialog.overlay.querySelector("#note-edit-title");
    const contentInput = noteDialog.overlay.querySelector("#note-edit-content");
    noteDialog.draft = { title: titleInput.value, content: contentInput.value };
    const title = noteDialog.draft.title.trim();
    if (!title) {
      noteDialog.error = "El título de la nota no puede estar vacío.";
      renderNoteDialog("#note-edit-title");
      noteDialog.overlay.querySelector("#note-edit-title").setAttribute("aria-invalid", "true");
      return;
    }

    noteDialog.pending = true;
    noteDialog.error = "";
    const saveBtn = noteDialog.overlay.querySelector("#note-edit-save");
    saveBtn.setAttribute("aria-disabled", "true");
    saveBtn.textContent = "Guardando…";
    noteDialog.overlay.querySelector("#note-edit-title").readOnly = true;
    noteDialog.overlay.querySelector("#note-edit-content").readOnly = true;
    noteDialog.overlay.querySelector('[data-action="cancel-note-edit"]').disabled = true;
    try {
      const res = await fetch(`${apiBase}/notes/${noteDialog.note.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content: noteDialog.draft.content }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(formatApiDetail(err.detail, "No se pudo actualizar la nota."));
      }

      const saved = await res.json();
      noteDialog.note = { ...noteDialog.note, ...saved };
      noteDialog.draft = { title: saved.title, content: saved.content || "" };
      noteDialog.mode = "view";
      noteDialog.pending = false;
      await loadNotes();
      showToast("Nota actualizada", "success");
      renderNoteDialog('[data-action="edit-note-mode"]');
    } catch (error) {
      noteDialog.pending = false;
      noteDialog.error = error.message || "Error de conexión. Inténtalo de nuevo.";
      renderNoteDialog("#note-edit-title");
      const errorEl = noteDialog.overlay.querySelector('[role="alert"]');
      if (errorEl) errorEl.focus();
    }
  }

  async function openNoteDialog(noteId, mode, triggerAction) {
    try {
      const res = await fetch(`${apiBase}/notes/${noteId}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(formatApiDetail(err.detail, "No se pudo cargar la nota."));
      }
      const note = await res.json();
      noteDialog = {
        note,
        mode,
        pending: false,
        error: "",
        draft: { title: note.title, content: note.content || "" },
        returnAction: triggerAction,
        overlay: document.createElement("div"),
      };
      noteDialog.overlay.className = "modal-overlay";
      noteDialog.overlay.addEventListener("click", async (event) => {
        if (event.target === noteDialog.overlay) {
          await requestCloseNoteDialog();
          return;
        }
        const action = event.target.closest("[data-action]")?.dataset.action;
        if (action === "edit-note-mode" && noteDialog && !noteDialog.pending) {
          noteDialog.mode = "edit";
          noteDialog.error = "";
          noteDialog.draft = { title: noteDialog.note.title, content: noteDialog.note.content || "" };
          renderNoteDialog("#note-edit-title");
        } else if (action === "cancel-note-edit") {
          await cancelNoteEdit();
        } else if (action === "close-note-dialog") {
          await requestCloseNoteDialog();
        }
      });
      noteDialog.overlay.addEventListener("input", (event) => {
        if (!noteDialog || noteDialog.mode !== "edit") return;
        if (event.target.id === "note-edit-title") noteDialog.draft.title = event.target.value;
        if (event.target.id === "note-edit-content") noteDialog.draft.content = event.target.value;
        noteDialog.error = "";
        event.target.removeAttribute("aria-invalid");
      });
      noteDialog.overlay.addEventListener("submit", (event) => {
        if (event.target.id !== "note-edit-form") return;
        event.preventDefault();
        submitNoteEdit();
      });
      noteDialog.overlay.addEventListener("keydown", async (event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          if (noteDialog && noteDialog.mode === "edit") await cancelNoteEdit();
          else await requestCloseNoteDialog();
          return;
        }
        if (event.key === "Tab") {
          const focusable = Array.from(noteDialog.overlay.querySelectorAll(
            'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])'
          ));
          if (!focusable.length) return;
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
          }
        }
      });
      document.body.appendChild(noteDialog.overlay);
      renderNoteDialog(mode === "edit" ? "#note-edit-title" : '[data-action="close-note-dialog"]');
    } catch (error) {
      showToast(error.message || "Error al cargar la nota", "error");
    }
  }

  notesListEl.addEventListener("click", async (event) => {
    const editBtn = event.target.closest('[data-action="edit-note"]');
    if (editBtn) {
      await openNoteDialog(editBtn.dataset.id, "edit", "edit-note");
      return;
    }
    const viewBtn = event.target.closest('[data-action="view-note"]');
    if (viewBtn) {
      await openNoteDialog(viewBtn.dataset.id, "view", "view-note");
      return;
    }
    const deleteBtn = event.target.closest('[data-action="delete-note"]');
    if (deleteBtn) await window.appNotes.deleteNote(deleteBtn.dataset.id);
  });

  window.appNotes = {
    async viewNote(noteId) {
      await openNoteDialog(noteId, "view", "view-note");
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

function formatApiDetail(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => (item && item.msg ? item.msg : null)).filter(Boolean);
    if (messages.length) return messages.join(" · ");
  }
  return fallback;
}
