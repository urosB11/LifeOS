// Life OS — vista Hábitos (Fase 8C)
//
// Registro rápido del día, calendario de consistencia y gestión de hábitos.
// Las reglas de días programados viven en el backend (/habits/{id}/calendar);
// esta vista solo pinta y envía acciones. Usa componentes de 8A.

import { showToast, showConfirm } from "./app.js";

const MONTHS = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];
const WEEKDAYS_SHORT = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"];
const WEEKDAYS_LONG = [
  "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
];
const COLOR_PRESETS = [
  { value: "", label: "Sin color" },
  { value: "#267568", label: "Verde azulado" },
  { value: "#2E5E8C", label: "Azul" },
  { value: "#6B4E71", label: "Ciruela" },
  { value: "#9C5A3C", label: "Terracota" },
  { value: "#4A5568", label: "Pizarra" },
];

// Escapa texto y comillas: el contenido del usuario siempre entra como texto.
function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function frequencyLabel(habit) {
  if (habit.frequency_type === "daily") return "Todos los días";
  const days = habit.frequency_days || [];
  if (!days.length) return "Sin días";
  if (days.length === 7) return "Todos los días";
  return days.map((d) => WEEKDAYS_LONG[d] ?? `día ${d}`).join(", ");
}

function targetLabel(habit) {
  if (habit.target_value === null || habit.target_value === undefined) return "";
  const unit = habit.target_unit ? ` ${habit.target_unit}` : "";
  return `Meta: ${habit.target_value}${unit}`;
}

export async function renderHabitsView(container, apiBase) {
  container.innerHTML = `
    <div id="habits-view">
      <div class="section-header">
        <div>
          <h1>Hábitos</h1>
          <p class="subtitle">Tu seguimiento diario</p>
        </div>
        <button class="btn btn--primary" id="habit-new-btn" data-action="new">Nuevo hábito</button>
      </div>

      <div id="habits-alert" role="alert" hidden
           style="margin-top:12px; padding:10px 14px; border:1px solid var(--danger);
                  border-radius:var(--radius); color:var(--danger);"></div>

      <form id="habit-form" class="card" hidden style="margin-top:16px;" novalidate>
        <h3 id="habit-form-title" style="margin-top:0;">Nuevo hábito</h3>
        <div class="form-row" style="margin-top:12px;">
          <div class="form-group" style="flex:2; min-width:240px;">
            <label for="hf-name">Nombre</label>
            <input type="text" id="hf-name" maxlength="200" required>
          </div>
          <div class="form-group" style="flex:1; min-width:180px;">
            <label for="hf-category">Categoría (opcional)</label>
            <input type="text" id="hf-category" maxlength="100" list="hf-category-list">
            <datalist id="hf-category-list"></datalist>
          </div>
          <div class="form-group" style="flex:1; min-width:150px;">
            <label for="hf-color">Color</label>
            <select id="hf-color">
              ${COLOR_PRESETS.map((c) => `<option value="${c.value}">${c.label}</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:2; min-width:240px;">
            <label for="hf-description">Descripción (opcional)</label>
            <input type="text" id="hf-description" maxlength="2000">
          </div>
          <div class="form-group" style="flex:1; min-width:160px;">
            <label for="hf-start">Fecha de inicio</label>
            <input type="date" id="hf-start" required>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1; min-width:200px;">
            <label for="hf-frequency">Frecuencia</label>
            <select id="hf-frequency">
              <option value="daily">Todos los días</option>
              <option value="weekly_days">Días específicos</option>
            </select>
          </div>
          <div class="form-group" style="flex:1; min-width:160px;">
            <label for="hf-target">Cantidad objetivo (opcional)</label>
            <input type="number" id="hf-target" min="0" step="any" placeholder="Ej. 5">
          </div>
          <div class="form-group" style="flex:1; min-width:140px;">
            <label for="hf-unit">Unidad</label>
            <input type="text" id="hf-unit" maxlength="30" placeholder="Ej. km, páginas">
          </div>
        </div>
        <fieldset id="hf-days-field" hidden
                  style="border:1px solid var(--border); border-radius:var(--radius);
                         padding:12px; margin-top:4px;">
          <legend style="font-size:0.875rem; padding:0 6px;">Días de la semana</legend>
          <div style="display:flex; gap:14px; flex-wrap:wrap;">
            ${WEEKDAYS_LONG.map((label, i) => `
              <label style="display:flex; align-items:center; gap:6px; font-size:0.9375rem;">
                <input type="checkbox" class="hf-day" value="${i}"> ${label}
              </label>`).join("")}
          </div>
        </fieldset>
        <div class="btn-group" style="margin-top:16px;">
          <button type="submit" class="btn btn--primary" id="hf-submit">Guardar hábito</button>
          <button type="button" class="btn btn--secondary" data-action="cancel-form">Cancelar</button>
        </div>
      </form>

      <div id="habits-summary" class="summary-cards" style="margin-top:20px;"></div>

      <h2 style="margin-top:24px;">Hoy</h2>
      <div id="habits-today" class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
        <p class="empty-state__title">Cargando&hellip;</p>
      </div>

      <section class="card" style="margin-top:24px;">
        <h3 style="margin-top:0;">Métricas</h3>
        <p class="subtitle" style="margin-bottom:12px;">
          Rachas y cumplimiento sobre días programados (fórmulas en la documentación).
        </p>
        <div id="habits-stats">
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
            <p class="empty-state__title">Cargando&hellip;</p>
          </div>
        </div>
      </section>

      <section class="card habits-calendar" style="margin-top:24px;">
        <div class="cal-header">
          <div class="cal-header__title">
            <h3 style="margin:0;">Calendario</h3>
            <label class="sr-only" for="cal-habit">Hábito del calendario</label>
            <select id="cal-habit" style="max-width:220px;"></select>
          </div>
          <div class="cal-nav">
            <button type="button" class="btn btn--secondary btn--sm" id="cal-prev"
                    data-action="cal-prev" aria-label="Mes anterior">&#8249;</button>
            <span id="cal-month" aria-live="polite" style="min-width:150px; text-align:center;"></span>
            <button type="button" class="btn btn--secondary btn--sm" id="cal-next"
                    data-action="cal-next" aria-label="Mes siguiente">&#8250;</button>
          </div>
        </div>
        <div id="calendar-grid">
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
            <p class="empty-state__title">Cargando&hellip;</p>
          </div>
        </div>
        <ul class="cal-legend">
          <li><span class="cal-swatch cal-day--done"></span>Cumplido</li>
          <li><span class="cal-swatch cal-day--partial"></span>Registrado sin completar</li>
          <li><span class="cal-swatch cal-day--skipped"></span>Omitido</li>
          <li><span class="cal-swatch cal-day--missed"></span>Pendiente de registrar</li>
          <li><span class="cal-swatch cal-day--off"></span>No programado</li>
        </ul>
      </section>

      <h2 style="margin-top:28px;">Todos los hábitos</h2>
      <div class="filters-bar" style="margin-bottom:12px;">
        <label class="sr-only" for="filter-category">Filtrar por categoría</label>
        <select id="filter-category">
          <option value="">Todas las categorías</option>
        </select>
        <label class="sr-only" for="filter-status">Filtrar por estado</label>
        <select id="filter-status">
          <option value="">Todos los estados</option>
          <option value="active">Activos</option>
          <option value="paused">Pausados</option>
          <option value="archived">Archivados</option>
        </select>
      </div>
      <div id="habits-manage" class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
        <p class="empty-state__title">Cargando&hellip;</p>
      </div>
    </div>
  `;

  const view = container.querySelector("#habits-view");
  const alertEl = view.querySelector("#habits-alert");
  const summaryEl = view.querySelector("#habits-summary");
  const todayEl = view.querySelector("#habits-today");
  const statsEl = view.querySelector("#habits-stats");
  const manageEl = view.querySelector("#habits-manage");
  const calendarGridEl = view.querySelector("#calendar-grid");
  const calHabitEl = view.querySelector("#cal-habit");
  const calMonthEl = view.querySelector("#cal-month");
  const formEl = view.querySelector("#habit-form");
  const freqEl = view.querySelector("#hf-frequency");
  const daysFieldEl = view.querySelector("#hf-days-field");
  const filterCategoryEl = view.querySelector("#filter-category");
  const filterStatusEl = view.querySelector("#filter-status");

  let habits = [];
  let todayItems = [];
  let editingId = null;
  const calendar = { habitId: null, year: null, month: null };

  // --- Utilidades --------------------------------------------------------

  function showError(message) {
    alertEl.textContent = message;
    alertEl.hidden = !message;
  }

  async function api(path, options = {}) {
    const res = await fetch(`${apiBase}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body.detail) detail = typeof body.detail === "string" ? body.detail : detail;
      } catch (e) { /* sin cuerpo JSON */ }
      throw new Error(detail);
    }
    return res.status === 204 ? null : res.json();
  }

  function habitById(id) {
    return habits.find((h) => h.id === id);
  }

  // --- Resumen y hoy ------------------------------------------------------

  function renderSummary() {
    const done = todayItems.filter(
      (i) => i.entry && i.entry.status === "completed"
    ).length;
    const skipped = todayItems.filter(
      (i) => i.entry && i.entry.status === "skipped"
    ).length;
    const pending = todayItems.length - done - skipped;
    summaryEl.innerHTML = `
      <div class="summary-card">
        <div class="summary-value text-success">${done}</div>
        <div class="summary-label">Cumplidos hoy</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">${pending}</div>
        <div class="summary-label">Pendientes</div>
      </div>
      <div class="summary-card">
        <div class="summary-value text-secondary">${skipped}</div>
        <div class="summary-label">Omitidos</div>
      </div>
    `;
  }

  function progressHtml(item) {
    const habit = item.habit;
    if (habit.target_value === null || habit.target_value === undefined) return "";
    const value = item.entry ? item.entry.value : null;
    const pct =
      value === null || value === undefined
        ? 0
        : Math.max(0, Math.min(100, (value / habit.target_value) * 100));
    const unit = habit.target_unit ? ` ${habit.target_unit}` : "";
    const shown = value === null || value === undefined ? "—" : value;
    return `
      <div class="habit-row__progress">
        <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100"
             aria-valuenow="${Math.round(pct)}"
             aria-label="Progreso de ${esc(habit.name)}">
          <div class="progress__bar" style="width:${pct}%"></div>
        </div>
        <span class="progress__text">${shown} / ${habit.target_value}${esc(unit)}</span>
      </div>`;
  }

  function renderToday() {
    if (!todayItems.length) {
      todayEl.className = "empty-state";
      todayEl.innerHTML = habits.length
        ? `<div class="empty-state__icon" aria-hidden="true">&#10003;</div>
           <p class="empty-state__title">Sin hábitos hoy</p>
           <p class="empty-state__text">No hay hábitos programados para hoy.</p>`
        : `<div class="empty-state__icon" aria-hidden="true">&#127991;</div>
           <p class="empty-state__title">Aún no hay hábitos</p>
           <p class="empty-state__text">Crea el primero con el botón "Nuevo hábito".</p>`;
      return;
    }
    todayEl.className = "habits-today";
    todayEl.innerHTML = todayItems
      .map((item) => {
        const habit = item.habit;
        const entry = item.entry;
        const state = entry ? entry.status : null;
        let badge = "";
        if (state === "completed") badge = `<span class="badge habit-badge--done">Cumplido</span>`;
        else if (state === "skipped") badge = `<span class="badge habit-badge--skipped">Omitido</span>`;
        else if (state === "pending") badge = `<span class="badge habit-badge--partial">Registrado</span>`;

        const meta = [frequencyLabel(habit), targetLabel(habit)]
          .filter(Boolean).map((t) => `<span>${esc(t)}</span>`).join(" · ");

        const isQuant = habit.target_value !== null && habit.target_value !== undefined;
        let actions = "";
        if (isQuant) {
          const value = entry && entry.value !== null && entry.value !== undefined ? entry.value : "";
          actions = `
            <label class="sr-only" for="hv-${habit.id}">Cantidad para ${esc(habit.name)}</label>
            <input type="number" class="habit-value-input" id="hv-${habit.id}"
                   min="0" step="any" value="${value}"
                   placeholder="${habit.target_value}${habit.target_unit ? " " + esc(habit.target_unit) : ""}">
            <button type="button" class="btn btn--primary btn--sm" data-action="save-value"
                    data-id="${habit.id}">Guardar</button>`;
          if (state !== "skipped") {
            actions += `
              <button type="button" class="btn btn--secondary btn--sm" data-action="skip"
                      data-id="${habit.id}">Omitir</button>`;
          }
        } else if (!entry) {
          actions = `
            <button type="button" class="btn btn--primary btn--sm" data-action="mark"
                    data-id="${habit.id}">Marcar hecho</button>
            <button type="button" class="btn btn--secondary btn--sm" data-action="skip"
                    data-id="${habit.id}">Omitir</button>`;
        }
        if (entry) {
          actions += `
            <button type="button" class="btn btn--secondary btn--sm" data-action="undo"
                    data-id="${habit.id}">Deshacer</button>`;
        }

        return `
          <div class="habit-row${state === "completed" ? " habit-row--done" : ""}" data-id="${habit.id}">
            <span class="habit-dot ${dotClass(habit.color)}" aria-hidden="true"></span>
            <div class="habit-row__main">
              <span class="habit-row__name">${esc(habit.name)}</span>
              <span class="habit-row__meta">${meta || ""}</span>
            </div>
            ${badge}
            ${progressHtml(item)}
            <div class="habit-row__actions">${actions}</div>
          </div>`;
      })
      .join("");
  }

  function dotClass(color) {
    const preset = COLOR_PRESETS.find((c) => c.value === color);
    if (!preset || !color) return "habit-dot--none";
    const index = COLOR_PRESETS.indexOf(preset);
    return `habit-dot--${index}`;
  }

  // --- Métricas -----------------------------------------------------------

  function pctText(value) {
    if (value === null || value === undefined) {
      return `<span class="text-secondary">Sin datos</span>`;
    }
    return `${value}%`;
  }

  function streakText(value) {
    return `${value} ${value === 1 ? "día" : "días"}`;
  }

  function renderStats(list) {
    if (!list || !list.length) {
      statsEl.innerHTML = `<div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#128202;</div>
        <p class="empty-state__title">Sin métricas</p>
        <p class="empty-state__text">Aún no hay métricas que mostrar.</p>
      </div>`;
      return;
    }
    statsEl.innerHTML = `
      <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Hábito</th>
            <th>Racha actual</th>
            <th>Mejor racha</th>
            <th>Semana</th>
            <th>Mes</th>
            <th>Consistencia</th>
          </tr>
        </thead>
        <tbody>
          ${list.map((s) => `
            <tr>
              <td>
                <span class="habit-dot ${dotClass(s.color)}" aria-hidden="true"></span>
                ${esc(s.name)}
              </td>
              <td>${streakText(s.current_streak)}</td>
              <td>${streakText(s.best_streak)}</td>
              <td>${pctText(s.weekly_compliance)}</td>
              <td>${pctText(s.monthly_compliance)}</td>
              <td>${pctText(s.consistency_month)}</td>
            </tr>`).join("")}
        </tbody>
      </table>
      </div>
      <p class="subtitle" style="margin-top:10px;">
        Cumplimiento = días completados sobre días programados del período.
        Consistencia incluye los días omitidos como registrados.
      </p>`;
  }

  // --- Calendario ---------------------------------------------------------

  function renderCalendarSelect() {
    const options = habits
      .filter((h) => h.status !== "archived")
      .map((h) => `<option value="${h.id}">${esc(h.name)}</option>`)
      .join("");
    calHabitEl.innerHTML = options || `<option value="">Sin hábitos</option>`;
    if (calendar.habitId && habitById(calendar.habitId)) {
      calHabitEl.value = calendar.habitId;
    } else if (habits.length) {
      const first = habits.find((h) => h.status !== "archived") || habits[0];
      calendar.habitId = first.id;
      calHabitEl.value = first.id;
    }
  }

  async function renderCalendar() {
    if (!calendar.habitId) {
      calendarGridEl.innerHTML = `<div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#128197;</div>
        <p class="empty-state__title">Sin hábitos</p>
        <p class="empty-state__text">Crea un hábito para ver su calendario.</p>
      </div>`;
      calMonthEl.textContent = "";
      return;
    }
    const monthStr = `${calendar.year}-${String(calendar.month + 1).padStart(2, "0")}`;
    calMonthEl.textContent = `${MONTHS[calendar.month]} ${calendar.year}`;
    calendarGridEl.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
      <p class="empty-state__title">Cargando&hellip;</p>
    </div>`;
    try {
      const data = await api(`/habits/${calendar.habitId}/calendar?month=${monthStr}`);
      drawCalendar(data);
    } catch (error) {
      calendarGridEl.innerHTML = `<div class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
        <p class="empty-state__title">Error</p>
        <p class="empty-state__text">No se pudo cargar el calendario. ${esc(error.message)}</p>
      </div>`;
    }
  }

  function drawCalendar(data) {
    const first = new Date(`${data.days[0].date}T00:00:00`);
    const lead = (first.getDay() + 6) % 7; // lunes = 0
    const monthLabel = MONTHS[Number(data.month.slice(5, 7)) - 1];
    const stateText = {
      completed: "cumplido",
      pending: "registrado sin completar",
      skipped: "omitido",
    };

    let cells = "";
    for (let i = 0; i < lead; i += 1) {
      cells += `<div class="cal-day cal-day--empty" aria-hidden="true"></div>`;
    }
    for (const day of data.days) {
      const dayNum = Number(day.date.slice(8, 10));
      const future = day.date > data.today;
      let cls = "";
      let text = "";
      if (!day.scheduled) {
        cls = "cal-day--off";
        text = "no programado";
      } else if (day.entry_status) {
        cls = `cal-day--${day.entry_status === "completed" ? "done" : day.entry_status === "skipped" ? "skipped" : "partial"}`;
        text = stateText[day.entry_status];
      } else if (future) {
        cls = "cal-day--future";
        text = "programado";
      } else {
        cls = "cal-day--missed";
        text = "pendiente de registrar";
      }
      const isToday = day.date === data.today;
      cells += `
        <div class="cal-day ${cls}${isToday ? " cal-day--today" : ""}"
             role="gridcell"
             aria-label="${dayNum} de ${monthLabel}: ${text}">
          <span aria-hidden="true">${dayNum}</span>
        </div>`;
    }
    calendarGridEl.innerHTML = `
      <div class="cal" role="grid" aria-label="Calendario de ${monthLabel}">
        <div class="cal__weekdays" role="row">
          ${WEEKDAYS_SHORT.map((d) => `<span role="columnheader">${d}</span>`).join("")}
        </div>
        <div class="cal__days">${cells}</div>
      </div>`;
  }

  // --- Gestión -----------------------------------------------------------

  function renderManage() {
    const category = filterCategoryEl.value;
    const status = filterStatusEl.value;
    let rows = habits;
    if (category) rows = rows.filter((h) => h.category === category);
    if (status) rows = rows.filter((h) => h.status === status);

    if (!habits.length) {
      manageEl.className = "empty-state";
      manageEl.innerHTML = `<div class="empty-state__icon" aria-hidden="true">&#127991;</div>
        <p class="empty-state__title">Sin hábitos</p>
        <p class="empty-state__text">Crea tu primer hábito para empezar a seguirlo.</p>`;
      return;
    }
    if (!rows.length) {
      manageEl.className = "empty-state";
      manageEl.innerHTML = `<div class="empty-state__icon" aria-hidden="true">&#128269;</div>
        <p class="empty-state__title">Sin resultados</p>
        <p class="empty-state__text">Ningún hábito coincide con el filtro.</p>`;
      return;
    }
    manageEl.className = "habits-manage";
    manageEl.innerHTML = `
      <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Hábito</th>
            <th>Frecuencia</th>
            <th>Categoría</th>
            <th>Meta</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((h) => {
            const statusBadge =
              h.status === "active" ? "Activo" :
              h.status === "paused" ? "Pausado" : "Archivado";
            const statusBadgeClass =
              h.status === "active" ? "status" :
              h.status === "paused" ? "warning" : "neutral";
            const statusAction =
              h.status === "active"
                ? `<button type="button" class="btn btn--secondary btn--sm" data-action="pause" data-id="${h.id}">Pausar</button>
                   <button type="button" class="btn btn--secondary btn--sm" data-action="archive" data-id="${h.id}">Archivar</button>`
                : h.status === "paused"
                ? `<button type="button" class="btn btn--secondary btn--sm" data-action="resume" data-id="${h.id}">Reactivar</button>
                   <button type="button" class="btn btn--secondary btn--sm" data-action="archive" data-id="${h.id}">Archivar</button>`
                : `<button type="button" class="btn btn--secondary btn--sm" data-action="restore" data-id="${h.id}">Restaurar</button>`;
            return `
              <tr>
                <td>
                  <span class="habit-dot ${dotClass(h.color)}" aria-hidden="true"></span>
                  <strong>${esc(h.name)}</strong>
                </td>
                <td>${esc(frequencyLabel(h))}</td>
                <td>${h.category ? esc(h.category) : "&mdash;"}</td>
                <td>${h.target_value !== null && h.target_value !== undefined ? esc(targetLabel(h)) : "&mdash;"}</td>
                <td><span class="badge badge--${statusBadgeClass}">${statusBadge}</span></td>
                <td>
                  <div class="btn-group">
                    <button type="button" class="btn btn--secondary btn--sm" data-action="move-up"
                            data-id="${h.id}" aria-label="Mover arriba ${esc(h.name)}">↑</button>
                    <button type="button" class="btn btn--secondary btn--sm" data-action="move-down"
                            data-id="${h.id}" aria-label="Mover abajo ${esc(h.name)}">↓</button>
                    <button type="button" class="btn btn--secondary btn--sm" data-action="edit"
                            data-id="${h.id}">Editar</button>
                    ${statusAction}
                    <button type="button" class="btn btn--danger btn--sm" data-action="delete"
                            data-id="${h.id}">Eliminar</button>
                  </div>
                </td>
              </tr>`;
          }).join("")}
        </tbody>
      </table>
      </div>`;
  }

  function renderFilters() {
    const categories = [...new Set(habits.map((h) => h.category).filter(Boolean))];
    const current = filterCategoryEl.value;
    filterCategoryEl.innerHTML =
      `<option value="">Todas las categorías</option>` +
      categories.map((c) => `<option value="${esc(c)}">${esc(c)}</option>`).join("");
    if (categories.includes(current)) filterCategoryEl.value = current;

    const datalist = view.querySelector("#hf-category-list");
    datalist.innerHTML = categories.map((c) => `<option value="${esc(c)}"></option>`).join("");
  }

  // --- Formulario ---------------------------------------------------------

  function openForm(habit = null) {
    editingId = habit ? habit.id : null;
    view.querySelector("#habit-form-title").textContent =
      habit ? "Editar hábito" : "Nuevo hábito";
    view.querySelector("#hf-name").value = habit ? habit.name : "";
    view.querySelector("#hf-description").value = habit && habit.description ? habit.description : "";
    view.querySelector("#hf-category").value = habit && habit.category ? habit.category : "";
    view.querySelector("#hf-color").value = habit && habit.color ? habit.color : "";
    view.querySelector("#hf-start").value = habit ? habit.start_date : "";
    view.querySelector("#hf-target").value =
      habit && habit.target_value !== null && habit.target_value !== undefined ? habit.target_value : "";
    view.querySelector("#hf-unit").value = habit && habit.target_unit ? habit.target_unit : "";
    freqEl.value = habit ? habit.frequency_type : "daily";
    const days = habit && habit.frequency_days ? habit.frequency_days : [];
    view.querySelectorAll(".hf-day").forEach((cb) => {
      cb.checked = days.includes(Number(cb.value));
    });
    daysFieldEl.hidden = freqEl.value !== "weekly_days";
    showError("");
    formEl.hidden = false;
    view.querySelector("#hf-name").focus();
  }

  function closeForm() {
    formEl.hidden = true;
    editingId = null;
  }

  async function submitForm(event) {
    event.preventDefault();
    const name = view.querySelector("#hf-name").value.trim();
    const start = view.querySelector("#hf-start").value;
    const frequencyType = freqEl.value;
    const frequencyDays = [...view.querySelectorAll(".hf-day:checked")]
      .map((cb) => Number(cb.value));
    const targetRaw = view.querySelector("#hf-target").value;
    const targetValue = targetRaw === "" ? null : Number(targetRaw);
    const targetUnit = view.querySelector("#hf-unit").value.trim() || null;

    if (!name) return showError("El nombre del hábito no puede estar vacío.");
    if (!start) return showError("Indica la fecha de inicio.");
    if (frequencyType === "weekly_days" && !frequencyDays.length) {
      return showError("Selecciona al menos un día de la semana.");
    }
    if (targetUnit && targetValue === null) {
      return showError("La unidad necesita una cantidad objetivo.");
    }

    const payload = {
      name,
      description: view.querySelector("#hf-description").value.trim() || null,
      category: view.querySelector("#hf-category").value.trim() || null,
      color: view.querySelector("#hf-color").value || null,
      frequency_type: frequencyType,
      frequency_days: frequencyType === "weekly_days" ? frequencyDays : null,
      start_date: start,
      target_value: targetValue,
      target_unit: targetUnit,
    };
    if (targetValue !== null && (!Number.isFinite(targetValue) || targetValue <= 0)) {
      return showError("La cantidad objetivo debe ser un número mayor que cero.");
    }

    try {
      if (editingId) {
        await api(`/habits/${editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
        showToast("Hábito actualizado", "success");
      } else {
        await api("/habits", { method: "POST", body: JSON.stringify(payload) });
        showToast("Hábito creado", "success");
      }
      closeForm();
      await refresh();
    } catch (error) {
      showError(`No se pudo guardar: ${error.message}`);
    }
  }

  // --- Acciones ------------------------------------------------------------

  async function withError(fn) {
    showError("");
    try {
      await fn();
      await refresh();
    } catch (error) {
      showError(error.message);
    }
  }

  async function refresh() {
    const [todayRes, habitsRes, statsRes] = await Promise.all([
      api("/habits/today").catch(() => []),
      api("/habits").catch(() => null),
      api("/habits/stats").catch(() => []),
    ]);
    todayItems = todayRes;
    if (habitsRes) habits = habitsRes;
    renderSummary();
    renderToday();
    renderStats(statsRes);
    renderFilters();
    renderManage();
    renderCalendarSelect();
    await renderCalendar();
  }

  async function handleAction(action, id) {
    switch (action) {
      case "new":
        openForm(null);
        return;
      case "cancel-form":
        closeForm();
        return;
      case "cal-prev": {
        calendar.month -= 1;
        if (calendar.month < 0) { calendar.month = 11; calendar.year -= 1; }
        await renderCalendar();
        return;
      }
      case "cal-next": {
        calendar.month += 1;
        if (calendar.month > 11) { calendar.month = 0; calendar.year += 1; }
        await renderCalendar();
        return;
      }
      case "mark":
        await withError(async () => {
          await api(`/habits/${id}/entries`, { method: "POST", body: "{}" });
          showToast("Hábito marcado como cumplido", "success");
        });
        return;
      case "skip": {
        const item = todayItems.find((i) => i.habit.id === id);
        const body = JSON.stringify({ status: "skipped" });
        await withError(async () => {
          if (item && item.entry) {
            await api(`/habits/${id}/entries/${item.entry.entry_date}`, {
              method: "PATCH", body,
            });
          } else {
            await api(`/habits/${id}/entries`, { method: "POST", body });
          }
          showToast("Hábito omitido", "success");
        });
        return;
      }
      case "undo": {
        const item = todayItems.find((i) => i.habit.id === id);
        if (!item || !item.entry) return;
        await withError(async () => {
          await api(`/habits/${id}/entries/${item.entry.entry_date}`, { method: "DELETE" });
          showToast("Registro deshecho", "success");
        });
        return;
      }
      case "save-value": {
        const input = view.querySelector(`#hv-${id}`);
        const raw = input ? input.value : "";
        if (raw === "") return showError("Ingresa una cantidad para guardar.");
        const item = todayItems.find((i) => i.habit.id === id);
        const body = JSON.stringify({ value: Number(raw) });
        await withError(async () => {
          if (item && item.entry) {
            await api(`/habits/${id}/entries/${item.entry.entry_date}`, {
              method: "PATCH", body,
            });
          } else {
            await api(`/habits/${id}/entries`, { method: "POST", body });
          }
          showToast("Cantidad guardada", "success");
        });
        return;
      }
      case "edit":
        openForm(habitById(id));
        return;
      case "pause":
        await withError(async () => {
          await api(`/habits/${id}/pause`, { method: "POST" });
          showToast("Hábito pausado", "success");
        });
        return;
      case "resume":
        await withError(async () => {
          await api(`/habits/${id}/resume`, { method: "POST" });
          showToast("Hábito reactivado", "success");
        });
        return;
      case "archive":
        await withError(async () => {
          await api(`/habits/${id}/archive`, { method: "POST" });
          showToast("Hábito archivado", "success");
        });
        return;
      case "restore":
        await withError(async () => {
          await api(`/habits/${id}/restore`, { method: "POST" });
          showToast("Hábito restaurado", "success");
        });
        return;
      case "delete": {
        const habit = habitById(id);
        if (!habit) return;
        const confirmed = await showConfirm({
          title: "Eliminar hábito",
          text: `¿Eliminar el hábito "${habit.name}"? Si tiene registros no se podrá eliminar; deberás archivarlo.`,
          confirmLabel: "Eliminar",
          danger: true,
        });
        if (!confirmed) return;
        await withError(async () => {
          await api(`/habits/${id}`, { method: "DELETE" });
          showToast("Hábito eliminado", "success");
        });
        return;
      }
      case "move-up":
      case "move-down": {
        const ordered = habits
          .filter((h) => h.status !== "archived")
          .slice()
          .sort((a, b) => a.position - b.position || a.created_at.localeCompare(b.created_at));
        const index = ordered.findIndex((h) => h.id === id);
        const other = action === "move-up" ? index - 1 : index + 1;
        if (index < 0 || other < 0 || other >= ordered.length) return;
        const a = ordered[index];
        const b = ordered[other];
        await withError(async () => {
          await api(`/habits/${a.id}`, { method: "PATCH", body: JSON.stringify({ position: b.position }) });
          await api(`/habits/${b.id}`, { method: "PATCH", body: JSON.stringify({ position: a.position }) });
        });
        return;
      }
      default:
    }
  }

  // --- Listeners (sobre nodos creados por este render) ---------------------

  view.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target || !view.contains(target)) return;
    handleAction(target.dataset.action, target.dataset.id);
  });

  formEl.addEventListener("submit", submitForm);

  freqEl.addEventListener("change", () => {
    daysFieldEl.hidden = freqEl.value !== "weekly_days";
  });

  calHabitEl.addEventListener("change", () => {
    calendar.habitId = calHabitEl.value || null;
    renderCalendar();
  });

  filterCategoryEl.addEventListener("change", renderManage);
  filterStatusEl.addEventListener("change", renderManage);

  // Estado inicial del calendario: mes local actual
  const now = new Date();
  calendar.year = now.getFullYear();
  calendar.month = now.getMonth();

  try {
    await refresh();
  } catch (error) {
    showError(`No se pudieron cargar los hábitos: ${error.message}`);
    todayEl.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
      <p class="empty-state__title">Error al cargar</p>
      <p class="empty-state__text">No se pudo cargar la información. Verifica que el servicio esté activo.</p>
    </div>`;
    statsEl.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
      <p class="empty-state__title">Error al cargar</p>
    </div>`;
    manageEl.innerHTML = `<div class="empty-state">
      <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
      <p class="empty-state__title">Error al cargar</p>
    </div>`;
  }
}
