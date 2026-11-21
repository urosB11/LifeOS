// Life OS — estados y edición de registros de hábitos (HAB-002)
//
// Semántica de los 7 estados del día compartida entre Home (matriz de
// semana) y Habit Tracker (calendarios): se deriva de programación, fecha
// local y registro; no agrega estados persistidos. La edición usa solo los
// endpoints existentes de entries (POST/PATCH/DELETE).

import { showToast } from "./app.js";

// Orden exacto de la tabla del SPEC (HAB-002 §1).
export const HABIT_DAY_STATES = [
  "done",
  "partial",
  "wait",
  "missed",
  "skipped",
  "future",
  "off",
];

const STATE_LABELS = {
  done: "Cumplido",
  partial: "Parcial",
  wait: "Pendiente de registrar",
  missed: "No cumplido",
  skipped: "Omitido",
  future: "En espera",
  off: "No programado",
};

const STATE_BADGES = {
  done: "success",
  partial: "info",
  wait: "warning",
  missed: "danger",
  skipped: "warning",
  future: "neutral",
  off: "neutral",
};

// Glifos de la matriz de Home; el calendario muestra el número del día.
export const HABIT_DAY_SYMBOLS = {
  done: "\u2713",
  partial: "\u25D0",
  wait: "\u25CB",
  missed: "\u00D7",
  skipped: "\u2013",
  future: "",
  off: "",
};

/** Deriva el estado visual de un día (7 condiciones del SPEC). */
export function deriveHabitDayState(day, today) {
  if (!day.scheduled) return "off";
  if (day.entry_status === "completed") return "done";
  if (day.entry_status === "pending") return "partial";
  if (day.entry_status === "skipped") return "skipped";
  if (day.date > today) return "future";
  if (day.date === today) return "wait";
  return "missed";
}

/** Etiqueta visible exacta de un estado. */
export function habitStateLabel(state) {
  return STATE_LABELS[state] || "";
}

/** Clase de badge (components.css) para un estado. */
export function habitStateBadge(state) {
  return STATE_BADGES[state] || "neutral";
}

/**
 * Leyenda generada desde los mismos estados que pintan las celdas, para que
 * coincida exactamente. `kind` es "cal" (calendario) o "wk" (matriz Home).
 */
export function habitLegendHtml(kind) {
  return HABIT_DAY_STATES.map((state) => {
    const swatch =
      state === "off"
        ? `${kind}-swatch lg-swatch--empty`
        : `${kind}-swatch hstate--${state}`;
    return `<li><span class="${swatch}" aria-hidden="true"></span>${STATE_LABELS[state]}</li>`;
  }).join("");
}

/** Fecha larga en español ("lunes 16 de noviembre de 2026"). */
export function formatLongDate(iso) {
  const parsed = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Fecha local actual en ISO (solo como respaldo si el llamador no pasa today). */
function localTodayIso() {
  const now = new Date();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${mm}-${dd}`;
}

function esc(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function request(apiBase, path, options = {}) {
  const res = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) {
        detail = typeof body.detail === "string" ? body.detail : detail;
      }
    } catch (_) {
      // Sin cuerpo JSON
    }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

/**
 * Editor compacto de un registro diario (modal accesible por teclado).
 *
 * - Hábito binario: marcar cumplido, marcar omitido o quitar el registro.
 * - Hábito cuantificable: ingresar/corregir cantidad (backend deriva el
 *   estado según la meta) y quitar el registro.
 * - Errores se muestran dentro del modal sin perder el contexto; el guardado
 *   evita doble envío deshabilitando los controles durante la petición.
 *
 * @param {object} options
 * @param {string} options.apiBase - Base de la API (p. ej. /api/v1).
 * @param {object} options.habit - Hábito (HabitOut) con target_value/unit.
 * @param {string} options.date - Fecha YYYY-MM-DD (<= hoy, programada).
 * @param {{status: string|null, value: number|null}|null} options.entry
 *   Registro actual del día o null si no existe.
 * @param {string} [options.today] - Hoy ISO (si no se pasa, fecha local).
 * @param {() => Promise<void>} [options.onSaved] - Refresco tras guardar.
 * @param {() => HTMLElement} [options.getFallbackFocus] - Fallback de foco
 *   si el disparador fue reemplazado por el refresco.
 * @param {HTMLElement} [options.returnFocusTo] - Disparador explícito: con
 *   clics sintéticos el `document.activeElement` puede ser el `body`.
 */
export function openHabitEntryEditor({
  apiBase,
  habit,
  date,
  entry = null,
  today = null,
  onSaved = null,
  getFallbackFocus = null,
  returnFocusTo = null,
}) {
  const returnFocus = returnFocusTo || document.activeElement;
  const entryExists = Boolean(entry && entry.status);
  const quantifiable =
    habit.target_value !== null && habit.target_value !== undefined;
  const effectiveToday = today || localTodayIso();
  const stateKey = deriveHabitDayState(
    {
      date,
      scheduled: true,
      entry_status: entry ? entry.status : null,
      entry_value: entry ? entry.value : null,
    },
    effectiveToday
  );
  const unit = habit.target_unit ? ` ${habit.target_unit}` : "";
  const targetHint = quantifiable
    ? `Meta: ${habit.target_value}${unit}`
    : "";

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="he-title">
      <h2 class="modal__title" id="he-title">${entryExists ? "Corregir registro" : "Registrar día"}</h2>
      <p class="modal__text">
        <strong>${esc(habit.name)}</strong><br>
        ${esc(formatLongDate(date))}<br>
        Estado actual:
        <span class="badge badge--${habitStateBadge(stateKey)}">${habitStateLabel(stateKey)}</span>
      </p>
      ${
        quantifiable
          ? `
      <div class="form-group">
        <label for="he-value">Cantidad${unit ? ` (${esc(unit.trim())})` : ""}</label>
        <input id="he-value" type="number" min="0" step="any" inputmode="decimal"
               value="${
                 entry && entry.value !== null && entry.value !== undefined
                   ? entry.value
                   : ""
               }">
        <p style="margin:6px 0 0; font-size:0.8125rem; color:var(--text-secondary);">
          ${esc(targetHint)}
        </p>
      </div>`
          : ""
      }
      <p class="form-error" id="he-error" role="alert" hidden></p>
      <div class="modal__actions">
        ${
          quantifiable
            ? `<button type="button" class="btn btn--primary" data-he="save">Guardar</button>`
            : `<button type="button" class="btn btn--primary" data-he="completed"${
                entry && entry.status === "completed" ? " disabled" : ""
              }>Marcar cumplido</button>
               <button type="button" class="btn btn--secondary" data-he="skipped"${
                 entry && entry.status === "skipped" ? " disabled" : ""
               }>Marcar omitido</button>`
        }
        ${
          entryExists
            ? `<button type="button" class="btn btn--danger" data-he="delete">Quitar registro</button>`
            : ""
        }
        <button type="button" class="btn btn--ghost" data-he="cancel">Cancelar</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  const modalEl = overlay.querySelector(".modal");
  const errorEl = overlay.querySelector("#he-error");
  const allButtons = [...overlay.querySelectorAll("button[data-he]")];
  const initialDisabled = new Map(allButtons.map((b) => [b, b.disabled]));
  let busy = false;

  function setError(message) {
    errorEl.textContent = message || "";
    errorEl.hidden = !message;
  }

  function setBusy(next) {
    busy = next;
    allButtons.forEach((button) => {
      button.disabled = next || initialDisabled.get(button);
    });
  }

  async function finish(message) {
    showToast(message, "success");
    try {
      if (onSaved) await onSaved();
    } catch (_) {
      showToast(
        "El registro se guardó, pero no se pudo actualizar la vista.",
        "error"
      );
    }
    close();
  }

  async function persist(payload) {
    if (entryExists) {
      await request(apiBase, `/habits/${habit.id}/entries/${date}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    } else {
      await request(apiBase, `/habits/${habit.id}/entries`, {
        method: "POST",
        body: JSON.stringify({ entry_date: date, ...payload }),
      });
    }
  }

  async function run(payload, message) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await persist(payload);
      await finish(message);
    } catch (error) {
      setError(`No se pudo guardar: ${error.message}`);
      setBusy(false);
    }
  }

  async function removeEntry() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await request(apiBase, `/habits/${habit.id}/entries/${date}`, {
        method: "DELETE",
      });
      await finish("Registro eliminado");
    } catch (error) {
      setError(`No se pudo quitar el registro: ${error.message}`);
      setBusy(false);
    }
  }

  function saveValue() {
    const input = overlay.querySelector("#he-value");
    const raw = input ? input.value.trim() : "";
    if (raw === "") {
      setError("Ingresa una cantidad para guardar.");
      return;
    }
    const numeric = Number(raw);
    if (!Number.isFinite(numeric) || numeric < 0) {
      setError("La cantidad debe ser un número mayor o igual a cero.");
      return;
    }
    run({ value: numeric }, "Cantidad guardada");
  }

  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      // Clic fuera del modal: cancelar (si no hay una petición en curso).
      if (!busy) close();
      return;
    }
    const button = event.target.closest("button[data-he]");
    if (!button || !overlay.contains(button)) return;
    switch (button.dataset.he) {
      case "cancel":
        if (!busy) close();
        break;
      case "save":
        saveValue();
        break;
      case "delete":
        removeEntry();
        break;
      case "completed":
        run({ status: "completed" }, "Día marcado como cumplido");
        break;
      case "skipped":
        run({ status: "skipped" }, "Día marcado como omitido");
        break;
      default:
    }
  });

  function onKeydown(event) {
    if (event.key === "Escape") {
      if (!busy) {
        event.preventDefault();
        close();
      }
      return;
    }
    if (event.key !== "Tab") return;
    const focusables = [
      ...modalEl.querySelectorAll(
        'button:not([disabled]), input:not([disabled]), [href], select, textarea'
      ),
    ].filter((el) => !el.disabled);
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function close() {
    document.removeEventListener("keydown", onKeydown);
    overlay.remove();
    const fallback = getFallbackFocus ? getFallbackFocus() : null;
    // Prioriza el disparador (celda) y cae al contenedor del widget cuando el
    // refresco ya lo reemplazó; nunca deja el foco en el body.
    const target =
      returnFocus && returnFocus !== document.body && returnFocus.isConnected
        ? returnFocus
        : fallback && fallback !== document.body && fallback.isConnected
        ? fallback
        : null;
    if (target) {
      if (!target.hasAttribute("tabindex")) target.tabIndex = -1;
      try {
        target.focus();
      } catch (_) {
        // Elemento no enfocable: se ignora.
      }
    }
  }

  document.addEventListener("keydown", onKeydown);

  const firstControl = overlay.querySelector(
    "input:not([disabled]), button:not([disabled])"
  );
  if (firstControl) firstControl.focus();
}
