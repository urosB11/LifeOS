// Life OS — utilidades compartidas de Mind (MIND-002)
// Sin dependencias externas: fetch, DOM y componentes de 8A.

export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text === null || text === undefined ? "" : String(text);
  return div.innerHTML;
}

/** Fetch JSON con errores normalizados (lanza Error con .status). */
export async function apiJson(
  url,
  { method = "GET", body = null, headers = {} } = {}
) {
  const init = { method, headers: { ...headers } };
  if (body !== null) {
    const hasContentType = Object.keys(init.headers).some(
      (name) => name.toLowerCase() === "content-type"
    );
    if (!hasContentType) init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(url, init);
  const raw = await res.text();
  let data = null;
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = null;
    }
  }
  if (!res.ok) {
    const detail = data && (data.detail || data.message);
    const error = new Error(
      typeof detail === "string" ? detail : `Error ${res.status} al solicitar Mind`
    );
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

export function formatDate(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return (
    date.toLocaleDateString("es", { day: "2-digit", month: "short", year: "numeric" }) +
    " " +
    date.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })
  );
}

/** Estados estándar: carga, vacío y error con reintento. */
export function loadingState(message = "Cargando…") {
  return `
    <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
    <p class="empty-state__title">${escapeHtml(message)}</p>
  `;
}

export function emptyState(title, text, actionHtml = "") {
  return `
    <div class="empty-state__icon" aria-hidden="true">&#128221;</div>
    <p class="empty-state__title">${escapeHtml(title)}</p>
    ${text ? `<p class="empty-state__text">${escapeHtml(text)}</p>` : ""}
    ${actionHtml}
  `;
}

export function errorState(title, text, retryId) {
  return `
    <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
    <p class="empty-state__title">${escapeHtml(title)}</p>
    <p class="empty-state__text">${escapeHtml(text)}</p>
    <button class="btn btn--secondary" type="button" id="${retryId}">Reintentar</button>
  `;
}

/**
 * Modal de formulario reutilizable (renombrar, editar, crear).
 * Resuelve { ok: true, values } al guardar o { ok: false } al cancelar.
 */
export function showFormModal({
  title,
  fields,
  submitLabel = "Guardar",
  cancelLabel = "Cancelar",
  danger = false,
  hint = "",
}) {
  return new Promise((resolve) => {
    const previouslyFocused = document.activeElement;
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";

    const body = fields
      .map((field) => {
        const id = `mind-modal-${field.name}`;
        const attrs = [
          field.required ? "required" : "",
          field.maxlength ? `maxlength="${field.maxlength}"` : "",
        ]
          .filter(Boolean)
          .join(" ");
        const common = `id="${id}" name="${field.name}" ${attrs} placeholder="${escapeHtml(
          field.placeholder || ""
        )}"`;
        const control =
          field.type === "textarea"
            ? `<textarea ${common} rows="${field.rows || 4}">${escapeHtml(
                field.value || ""
              )}</textarea>`
            : `<input type="text" ${common} value="${escapeHtml(field.value || "")}">`;
        return `
          <div class="form-group">
            <label for="${id}">${escapeHtml(field.label)}</label>
            ${control}
          </div>
        `;
      })
      .join("");

    overlay.innerHTML = `
      <div class="modal" style="max-width:560px;" role="dialog" aria-modal="true" aria-labelledby="mind-modal-title">
        <h2 class="modal__title" id="mind-modal-title">${escapeHtml(title)}</h2>
        ${hint ? `<p class="text-secondary" style="font-size:0.875rem;">${escapeHtml(hint)}</p>` : ""}
        <form id="mind-modal-form" novalidate>${body}</form>
        <div class="modal__actions">
          <button class="btn btn--secondary" type="button" data-action="cancel">${escapeHtml(
            cancelLabel
          )}</button>
          <button class="btn ${danger ? "btn--danger" : "btn--primary"}" type="submit" form="mind-modal-form">${escapeHtml(
            submitLabel
          )}</button>
        </div>
      </div>
    `;

    function close(result) {
      overlay.remove();
      document.removeEventListener("keydown", onKey, true);
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
      resolve(result);
    }

    function onKey(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        close({ ok: false });
        return;
      }
      if (e.key === "Tab") {
        const focusable = overlay.querySelectorAll(
          "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close({ ok: false });
      if (e.target.closest('[data-action="cancel"]')) close({ ok: false });
    });

    overlay.querySelector("#mind-modal-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const values = {};
      fields.forEach((field) => {
        const el = overlay.querySelector(`[name="${field.name}"]`);
        values[field.name] = el ? el.value : "";
      });
      close({ ok: true, values });
    });

    document.addEventListener("keydown", onKey, true);
    document.body.appendChild(overlay);
    const firstField = overlay.querySelector("input, textarea");
    if (firstField) firstField.focus();
  });
}
