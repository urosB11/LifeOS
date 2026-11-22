// Life OS — vista Home (dashboard configurable) — Fase 8B + HOME-001
//
// Centro de operaciones diario: qué requiere atención, qué conviene hacer
// hoy, qué proyectos están en marcha, cómo vienen los hábitos y cómo
// capturar una tarea o una nota.
//
// El catálogo de widgets se conserva intacto (ids, orden, visibilidad y
// preferencias): cada widget del catálogo alimenta una sección de la nueva
// estructura. La visibilidad oculta la sección; el orden define el orden
// dentro de cada columna. No se agregan endpoints ni dependencias.

import { showToast } from "./app.js";
import {
  HABIT_DAY_SYMBOLS,
  deriveHabitDayState,
  formatLongDate,
  habitLegendHtml,
  habitStateBadge,
  habitStateLabel,
  openHabitEntryEditor,
} from "./habit-entry.js";

// Rol de cada widget del catálogo dentro de la nueva estructura:
// "main" = columna amplia · "side" = columna secundaria · "full" = ancho completo.
const WIDGET_ROLES = {
  upcoming_tasks: "main",
  active_projects: "main",
  habits_today: "side",
  quick_add_task: "side",
  quick_add_note: "side",
  habits_week: "full",
};

const MAX_ATTENTION = 5;
const MAX_TODAY = 8;
const MAX_PROJECTS = 6;
const MAX_HABITS = 6;
// Una tarea cuenta como relevante para hoy si está vencida, vence hoy, vence
// dentro de una semana, tiene prioridad alta o no tiene fecha.
const RELEVANT_WINDOW_DAYS = 7;

export async function renderHomeView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Home</h1>
        <p class="subtitle" id="home-date">&nbsp;</p>
        <p class="home-context" id="home-context"></p>
      </div>
      <button class="btn btn--secondary" id="widgets-edit-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right:6px;">
          <circle cx="8" cy="8" r="2"/>
          <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.3 3.3l1.4 1.4M11.3 11.3l1.4 1.4M12.7 3.3l-1.4 1.4M4.7 11.3l-1.4 1.4"/>
        </svg>
        Configurar widgets
      </button>
    </div>

    <div class="home-layout">
      <div class="home-col home-col--main" id="home-main"></div>
      <div class="home-col home-col--side" id="home-side"></div>
      <div class="home-col home-col--full" id="home-full"></div>
    </div>
  `;

  const dateEl = container.querySelector("#home-date");
  const contextEl = container.querySelector("#home-context");
  const mainEl = container.querySelector("#home-main");
  const sideEl = container.querySelector("#home-side");
  const fullEl = container.querySelector("#home-full");
  const editBtn = container.querySelector("#widgets-edit-btn");

  let widgets = [];
  // Datos de la vista. `null` en un bloque significa "no se pudo cargar"
  // (se muestra el error del bloque); un array vacío significa "sin datos".
  const data = { tasks: null, projects: null, habits: null, week: null };
  // Última semana cargada: alimenta el editor de celdas del widget.
  let currentWeek = null;
  // Borradores de la captura rápida: sobreviven a los re-renders por error.
  const drafts = {
    task: { title: "", project_id: "" },
    note: { title: "" },
  };
  const captureErrors = { task: "", note: "" };
  const capturePending = { task: false, note: false };

  // --- Utilidades -----------------------------------------------------------
  function todayISO() {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  function addDays(iso, days) {
    const d = new Date(`${iso}T00:00:00`);
    d.setDate(d.getDate() + days);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  // Orden explícito de "Hoy": vencidas, vencen hoy, prioridad alta, próxima
  // fecha y, al final, las que no tienen fecha.
  function todayRank(task, today) {
    if (task.due_date && task.due_date < today) return 0;
    if (task.due_date === today) return 1;
    if (task.priority === "high") return 2;
    if (task.due_date) return 3;
    return 4;
  }

  function isRelevantToday(task, today) {
    if (!task.due_date) return true;
    if (task.due_date <= today) return true;
    if (task.due_date <= addDays(today, RELEVANT_WINDOW_DAYS)) return true;
    return task.priority === "high";
  }

  function priorityLabel(priority) {
    if (priority === "high") return "Alta";
    if (priority === "normal") return "Normal";
    if (priority === "low") return "Baja";
    return "";
  }

  function projectName(projectId) {
    if (!projectId) return "";
    const p = (data.projects || []).find((x) => x.id === projectId);
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

  function projectProgress(project) {
    if (!project.task_count) return 0;
    return Math.round((project.completed_count / project.task_count) * 100);
  }

  // --- Carga de datos -------------------------------------------------------
  async function load() {
    mainEl.innerHTML = `<div class="widget-card"><p class="empty-state">Cargando&hellip;</p></div>`;
    sideEl.innerHTML = "";
    fullEl.innerHTML = "";
    try {
      const [wRes, tasksRes, projectsRes, habitsRes, weekRes] = await Promise.all([
        fetch(`${apiBase}/dashboard/widgets`),
        fetch(`${apiBase}/tasks?status=pending`),
        fetch(`${apiBase}/projects?status=active`),
        fetch(`${apiBase}/habits/today`),
        fetch(`${apiBase}/habits/week`),
      ]);

      if (!wRes.ok) throw new Error(`HTTP ${wRes.status}`);
      widgets = await wRes.json();

      // Cada bloque tolera su propio fallo: un error aislado no vacía Home.
      data.tasks = tasksRes.ok ? await tasksRes.json() : null;
      data.projects = projectsRes.ok ? await projectsRes.json() : null;
      data.habits = habitsRes.ok ? await habitsRes.json() : null;
      data.week = weekRes.ok ? await weekRes.json() : null;

      renderAll();
    } catch (error) {
      mainEl.innerHTML = `
        <div class="widget-card">
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
            <p class="empty-state__title">No se pudo cargar Home</p>
            <p class="empty-state__text">Verifica que el servicio est&eacute; activo e intent&aacute; de nuevo.</p>
          </div>
        </div>
      `;
      sideEl.innerHTML = "";
      fullEl.innerHTML = "";
    }
  }

  // --- Estructura -----------------------------------------------------------
  function visibleWidgets() {
    return widgets.filter((w) => w.is_visible).sort((a, b) => a.position - b.position);
  }

  function renderAll() {
    renderHeader();

    const visible = visibleWidgets();
    if (visible.length === 0) {
      mainEl.innerHTML = `
        <div class="widget-card">
          <div class="empty-state">
            <div class="empty-state__icon" aria-hidden="true">&#9881;</div>
            <p class="empty-state__title">No hay secciones visibles</p>
            <p class="empty-state__text">Activa alg&uacute;n widget en la configuraci&oacute;n para ver tu d&iacute;a.</p>
            <button class="btn btn--primary" id="widgets-empty-config">Configurar widgets</button>
          </div>
        </div>
      `;
      const emptyBtn = mainEl.querySelector("#widgets-empty-config");
      if (emptyBtn) emptyBtn.addEventListener("click", openConfig);
      sideEl.innerHTML = "";
      fullEl.innerHTML = "";
      return;
    }

    const byRole = { main: [], side: [], full: [] };
    visible.forEach((w) => {
      const role = WIDGET_ROLES[w.widget_id] || "main";
      byRole[role].push(w);
    });

    mainEl.innerHTML = byRole.main.map(renderMainWidget).join("");

    // La captura rápida agrupa los dos widgets de acceso rápido en una
    // sección; se renderiza una sola vez, en la posición del primero.
    let captureRendered = false;
    sideEl.innerHTML = byRole.side
      .map((w) => {
        if (w.widget_id === "quick_add_task" || w.widget_id === "quick_add_note") {
          if (captureRendered) return "";
          captureRendered = true;
          return renderCaptureSection(byRole.side);
        }
        return renderSideWidget(w);
      })
      .join("");

    fullEl.innerHTML = byRole.full.map(renderFullWidget).join("");
  }

  function renderHeader() {
    const today = todayISO();
    const dateText = new Date().toLocaleDateString("es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
    dateEl.textContent = dateText.charAt(0).toUpperCase() + dateText.slice(1);

    const tasks = data.tasks || [];
    const overdue = tasks.filter((t) => t.due_date && t.due_date < today).length;
    const dueToday = tasks.filter((t) => t.due_date === today).length;
    const pending = tasks.length;

    let phrase;
    if (overdue > 0 && dueToday > 0) {
      phrase = `${overdue} ${overdue === 1 ? "tarea vencida" : "tareas vencidas"} y ${dueToday} ${
        dueToday === 1 ? "vence" : "vencen"
      } hoy.`;
    } else if (overdue > 0) {
      phrase = `${overdue} ${overdue === 1 ? "tarea vencida" : "tareas vencidas"}.`;
    } else if (dueToday > 0) {
      phrase = `${dueToday} ${dueToday === 1 ? "tarea vence" : "tareas vencen"} hoy.`;
    } else if (pending > 0) {
      phrase = `Nada vence hoy. ${pending} ${pending === 1 ? "tarea pendiente" : "tareas pendientes"} en total.`;
    } else {
      phrase = "No hay tareas pendientes.";
    }
    contextEl.textContent = phrase;
  }

  function renderMainWidget(w) {
    if (w.widget_id === "upcoming_tasks") return renderTasksCard();
    if (w.widget_id === "active_projects") return renderProjectsCard();
    return "";
  }

  function renderSideWidget(w) {
    if (w.widget_id === "habits_today") return renderHabitsCard();
    return "";
  }

  function renderFullWidget(w) {
    if (w.widget_id === "habits_week") return renderWeekCard();
    return "";
  }

  // --- Bloque: Atención + Hoy ------------------------------------------------
  function renderTasksCard() {
    if (data.tasks === null) {
      return `
        <div class="widget-card" id="widget-upcoming_tasks">
          <div class="widget-header"><span class="widget-title">Tareas</span></div>
          <div class="widget-content" id="widget-content-upcoming_tasks">
            ${errorBlock("No se pudieron cargar las tareas.")}
          </div>
        </div>
      `;
    }

    const today = todayISO();
    const tasks = data.tasks;
    const overdue = tasks.filter((t) => t.due_date && t.due_date < today);
    const dueToday = tasks.filter((t) => t.due_date === today);
    const attention = [...overdue.map((t) => ({ task: t, kind: "overdue" })), ...dueToday.map((t) => ({ task: t, kind: "today" }))]
      .sort((a, b) => {
        if (a.kind !== b.kind) return a.kind === "overdue" ? -1 : 1;
        const pa = a.task.priority === "high" ? 0 : 1;
        const pb = b.task.priority === "high" ? 0 : 1;
        if (pa !== pb) return pa - pb;
        return (a.task.due_date || "").localeCompare(b.task.due_date || "");
      });

    const relevant = tasks
      .filter((t) => isRelevantToday(t, today))
      .sort((a, b) => {
        const ra = todayRank(a, today);
        const rb = todayRank(b, today);
        if (ra !== rb) return ra - rb;
        const da = a.due_date || "9999-12-31";
        const db = b.due_date || "9999-12-31";
        if (da !== db) return da.localeCompare(db);
        return a.title.localeCompare(b.title);
      });

    const attentionHtml = attention.length
      ? `
        <section class="home-attention" aria-labelledby="home-attention-title">
          <div class="home-attention__head">
            <h2 class="home-section__title" id="home-attention-title">Atenci&oacute;n</h2>
            <span class="home-attention__count">${attention.length}</span>
          </div>
          <ul class="home-attention__list">
            ${attention
              .slice(0, MAX_ATTENTION)
              .map(
                ({ task, kind }) => `
              <li class="home-attention__item home-attention__item--${kind}">
                <span class="home-attention__label">${kind === "overdue" ? "Vencida" : "Vence hoy"}</span>
                <span class="home-attention__title">${escapeHtml(task.title)}</span>
                <span class="home-attention__meta">
                  ${task.priority ? `<span class="badge badge--priority-${task.priority}">${priorityLabel(task.priority)}</span>` : ""}
                  ${kind === "overdue" ? `<span class="home-attention__date">${task.due_date}</span>` : ""}
                  ${projectName(task.project_id) ? `<span class="home-attention__project">${escapeHtml(projectName(task.project_id))}</span>` : ""}
                </span>
              </li>
            `
              )
              .join("")}
          </ul>
          ${attention.length > MAX_ATTENTION ? `<p class="home-more">${attention.length - MAX_ATTENTION} m&aacute;s en Atenci&oacute;n</p>` : ""}
        </section>
      `
      : `
        <section class="home-attention" aria-labelledby="home-attention-title">
          <div class="home-attention__head">
            <h2 class="home-section__title" id="home-attention-title">Atenci&oacute;n</h2>
          </div>
          <p class="home-calm">Nada requiere atenci&oacute;n hoy: no hay tareas vencidas ni con vencimiento hoy.</p>
        </section>
      `;

    const todayHtml = `
      <section class="home-today" aria-labelledby="home-today-title">
        <div class="home-section__head">
          <h2 class="home-section__title" id="home-today-title">Hoy</h2>
          <a class="home-section__link" href="#/tasks">Ver todas las tareas</a>
        </div>
        ${
          relevant.length
            ? `<ul class="home-task-list">
                ${relevant.slice(0, MAX_TODAY).map((t) => taskRow(t, today)).join("")}
              </ul>
              ${
                relevant.length > MAX_TODAY
                  ? `<p class="home-more">${relevant.length - MAX_TODAY} ${relevant.length - MAX_TODAY === 1 ? "tarea m&aacute;s" : "tareas m&aacute;s"} en la lista completa</p>`
                  : ""
              }`
            : `<p class="home-calm">No hay tareas relevantes para hoy.</p>`
        }
      </section>
    `;

    return `
      <div class="widget-card" id="widget-upcoming_tasks">
        <div class="widget-content" id="widget-content-upcoming_tasks">
          ${attentionHtml}
          ${todayHtml}
        </div>
      </div>
    `;
  }

  function taskRow(task, today) {
    const project = projectName(task.project_id);
    let dueChip = "";
    if (!task.due_date) {
      dueChip = `<span class="chip chip--muted">Sin fecha</span>`;
    } else if (task.due_date < today) {
      dueChip = `<span class="chip chip--danger">Vencida el ${task.due_date}</span>`;
    } else if (task.due_date === today) {
      dueChip = `<span class="chip chip--warning">Vence hoy</span>`;
    } else {
      dueChip = `<span class="chip">Vence el ${task.due_date}</span>`;
    }
    return `
      <li class="home-task">
        <button type="button" class="check-toggle" data-action="complete-task" data-id="${task.id}"
                aria-label="Completar ${escapeHtml(task.title)}" title="Completar">&#10003;</button>
        <div class="home-task__body">
          <span class="home-task__title">${escapeHtml(task.title)}</span>
          <span class="home-task__chips">
            ${project ? `<span class="chip">${escapeHtml(project)}</span>` : ""}
            ${task.priority ? `<span class="badge badge--priority-${task.priority}">${priorityLabel(task.priority)}</span>` : ""}
            ${dueChip}
          </span>
        </div>
      </li>
    `;
  }

  // --- Bloque: Proyectos en marcha -------------------------------------------
  function renderProjectsCard() {
    if (data.projects === null) {
      return `
        <div class="widget-card" id="widget-active_projects">
          <div class="widget-header"><span class="widget-title">Proyectos en marcha</span></div>
          <div class="widget-content" id="widget-content-active_projects">
            ${errorBlock("No se pudieron cargar los proyectos.")}
          </div>
        </div>
      `;
    }
    const projects = data.projects;
    return `
      <div class="widget-card" id="widget-active_projects">
        <div class="widget-content" id="widget-content-active_projects">
          <section class="home-projects" aria-labelledby="home-projects-title">
            <div class="home-section__head">
              <h2 class="home-section__title" id="home-projects-title">Proyectos en marcha</h2>
              <a class="home-section__link" href="#/projects">Ver proyectos</a>
            </div>
            ${
              projects.length
                ? `<ul class="home-project-list">
                    ${projects.slice(0, MAX_PROJECTS).map(projectRow).join("")}
                  </ul>
                  ${projects.length > MAX_PROJECTS ? `<p class="home-more">${projects.length - MAX_PROJECTS} proyectos m&aacute;s activos</p>` : ""}`
                : `<p class="home-calm">No hay proyectos activos.</p>`
            }
          </section>
        </div>
      </div>
    `;
  }

  function projectRow(project) {
    const pct = projectProgress(project);
    const meta = [];
    if (project.overdue_count > 0) {
      meta.push(
        `<span class="chip chip--danger">${project.overdue_count} ${
          project.overdue_count === 1 ? "tarea vencida" : "tareas vencidas"
        }</span>`
      );
    }
    if (project.next_due_date) {
      meta.push(`<span class="chip">Pr&oacute;ximo vencimiento: ${project.next_due_date}</span>`);
    }
    return `
      <li class="home-project">
        <div class="home-project__head">
          <a class="home-project__name" href="#/projects/${project.id}">${escapeHtml(project.name)}</a>
          <span class="home-project__count">${project.completed_count}/${project.task_count}</span>
        </div>
        <div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="${project.task_count}"
             aria-valuenow="${project.completed_count}"
             aria-label="Ejecuci&oacute;n de tareas de ${escapeHtml(project.name)}: ${project.completed_count} de ${project.task_count}">
          <div class="progress__bar" style="width:${pct}%"></div>
        </div>
        <div class="home-project__meta">
          <span class="home-project__label">Ejecuci&oacute;n de tareas</span>
          ${meta.join("")}
        </div>
      </li>
    `;
  }

  // --- Bloque: Hábitos de hoy ------------------------------------------------
  function habitTodayState(item) {
    if (!item.entry) return "wait";
    if (item.entry.status === "completed") return "done";
    if (item.entry.status === "skipped") return "skipped";
    if (item.entry.status === "pending") return "partial";
    return "wait";
  }

  function renderHabitsCard() {
    if (data.habits === null) {
      return `
        <div class="widget-card" id="widget-habits_today">
          <div class="widget-header"><span class="widget-title">H&aacute;bitos de hoy</span></div>
          <div class="widget-content" id="widget-content-habits_today">
            ${errorBlock("No se pudieron cargar los h&aacute;bitos de hoy.")}
          </div>
        </div>
      `;
    }
    const items = data.habits;
    const done = items.filter((i) => habitTodayState(i) === "done").length;
    return `
      <div class="widget-card" id="widget-habits_today">
        <div class="widget-content" id="widget-content-habits_today">
          <section class="home-habits" aria-labelledby="home-habits-title">
            <div class="home-section__head">
              <h2 class="home-section__title" id="home-habits-title">H&aacute;bitos de hoy</h2>
              <span class="home-section__summary">${done} de ${items.length} cumplidos</span>
            </div>
            ${
              items.length
                ? `<ul class="home-habit-list">
                    ${items
                      .slice(0, MAX_HABITS)
                      .map((item) => {
                        const state = habitTodayState(item);
                        return `
                        <li class="home-habit">
                          <span class="home-habit__name">${escapeHtml(item.habit.name)}</span>
                          <span class="badge badge--${habitStateBadge(state)}">${habitStateLabel(state)}</span>
                        </li>
                      `;
                      })
                      .join("")}
                  </ul>
                  ${items.length > MAX_HABITS ? `<p class="home-more">${items.length - MAX_HABITS} h&aacute;bitos m&aacute;s</p>` : ""}`
                : `<p class="home-calm">No hay h&aacute;bitos programados para hoy.</p>`
            }
            <p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>
          </section>
        </div>
      </div>
    `;
  }

  // --- Bloque: Captura rápida -----------------------------------------------
  function renderCaptureSection(sideWidgets) {
    const showTask = sideWidgets.some((w) => w.widget_id === "quick_add_task");
    const showNote = sideWidgets.some((w) => w.widget_id === "quick_add_note");
    if (!showTask && !showNote) return "";
    const projects = data.projects || [];
    return `
      <div class="widget-card" id="widget-quick_add">
        <div class="widget-content" id="widget-content-quick_add">
          <section class="home-capture" aria-labelledby="home-capture-title">
            <h2 class="home-section__title" id="home-capture-title">Captura r&aacute;pida</h2>
            ${
              showTask
                ? `
              <form class="home-capture__form" data-capture="task" novalidate>
                <label class="home-capture__label" for="home-task-title">Nueva tarea</label>
                <input type="text" id="home-task-title" value="${escapeHtml(drafts.task.title)}"
                       placeholder="T&iacute;tulo de la tarea" required maxlength="200">
                <select id="home-task-project" aria-label="Proyecto (opcional)">
                  <option value="">Sin proyecto</option>
                  ${projects
                    .map(
                      (p) =>
                        `<option value="${p.id}" ${drafts.task.project_id === p.id ? "selected" : ""}>${escapeHtml(p.name)}</option>`
                    )
                    .join("")}
                </select>
                <button type="submit" class="btn btn--primary btn--sm" ${capturePending.task ? "disabled" : ""}>
                  ${capturePending.task ? "Guardando&hellip;" : "Crear tarea"}
                </button>
                <p class="home-capture__error" role="alert">${captureErrors.task ? escapeHtml(captureErrors.task) : ""}</p>
              </form>`
                : ""
            }
            ${
              showNote
                ? `
              <form class="home-capture__form" data-capture="note" novalidate>
                <label class="home-capture__label" for="home-note-title">Nueva nota</label>
                <input type="text" id="home-note-title" value="${escapeHtml(drafts.note.title)}"
                       placeholder="T&iacute;tulo de la nota" required maxlength="200">
                <button type="submit" class="btn btn--secondary btn--sm" ${capturePending.note ? "disabled" : ""}>
                  ${capturePending.note ? "Guardando&hellip;" : "Crear nota"}
                </button>
                <p class="home-capture__error" role="alert">${captureErrors.note ? escapeHtml(captureErrors.note) : ""}</p>
              </form>`
                : ""
            }
          </section>
        </div>
      </div>
    `;
  }

  // --- Bloque: Semana de hábitos (HAB-002) -----------------------------------
  function renderWeekCard() {
    if (data.week === null) {
      return `
        <div class="widget-card" id="widget-habits_week">
          <div class="widget-header"><span class="widget-title">Semana de h&aacute;bitos</span></div>
          <div class="widget-content" id="widget-content-habits_week">
            ${errorBlock("No se pudo cargar la semana de h&aacute;bitos.")}
          </div>
        </div>
      `;
    }
    return `
      <div class="widget-card" id="widget-habits_week">
        <div class="widget-header"><span class="widget-title">Semana de h&aacute;bitos</span></div>
        <div class="widget-content" id="widget-content-habits_week">
          ${renderHabitsWeek(data.week)}
        </div>
      </div>
    `;
  }

  function weekCell(habit, day, today) {
    const state = deriveHabitDayState(day, today);
    const label = `${habit.name}, ${formatLongDate(day.date)}: ${habitStateLabel(state)}`;
    const symbol = HABIT_DAY_SYMBOLS[state];
    const editable = state !== "off" && state !== "future";
    if (editable) {
      // Días programados <= hoy: editables desde Home (HAB-002 §1).
      return `<button type="button" class="wk-cell hstate--${state}" role="gridcell"
              data-action="wk-edit" data-id="${habit.id}" data-date="${day.date}"
              aria-label="${escapeHtml(label)}. Editar registro">${symbol}</button>`;
    }
    // No programado: espacio de alineación sin casillero, borde, fondo,
    // símbolo ni color. Futuro: celda gris sin interacción.
    return `<span class="wk-cell hstate--${state}" role="gridcell"
            aria-label="${escapeHtml(label)}">${symbol}</span>`;
  }

  function renderHabitsWeek(week) {
    currentWeek = week;
    const link = `<p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>`;
    if (!week.items.length) {
      return `<p class="home-calm">No hay h&aacute;bitos activos esta semana.</p>${link}`;
    }
    const names = ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"];
    const head = week.items[0].days
      .map((d) => {
        const weekday = new Date(`${d.date}T00:00:00`).getDay();
        const isToday = d.date === week.today;
        return `<span class="wk-head${isToday ? " wk-head--today" : ""}" role="columnheader">
            <span aria-hidden="true">${names[weekday]}</span>
            <span aria-hidden="true">${d.date.slice(8, 10)}</span>
            <span class="sr-only">${escapeHtml(formatLongDate(d.date))}${isToday ? " (hoy)" : ""}</span>
          </span>`;
      })
      .join("");
    const rows = week.items
      .map(
        (item) => `
      <div class="wk-row" role="row">
        <span class="wk-name" role="rowheader"
              title="${escapeHtml(item.habit.name)}">${escapeHtml(item.habit.name)}</span>
        ${item.days
          .map((d) => weekCell(item.habit, d, week.today))
          .join("")}
      </div>
    `
      )
      .join("");
    return `
      <div class="wk-matrix" role="grid"
           aria-label="Semana de h&aacute;bitos: ${week.week_start} al ${week.week_end}">
        <div class="wk-row wk-row--head" role="row">
          <span class="wk-name wk-name--head" role="columnheader">
            <span class="sr-only">H&aacute;bito</span>
          </span>
          ${head}
        </div>
        ${rows}
      </div>
      <ul class="wk-legend">${habitLegendHtml("wk")}</ul>
      ${link}`;
  }

  function errorBlock(message) {
    return `
      <div class="home-error" role="alert">
        <p class="home-error__text">${escapeHtml(message)}</p>
        <button class="btn btn--secondary btn--sm" data-action="reload-home">Reintentar</button>
      </div>
    `;
  }

  // --- Refresco dirigido tras editar un hábito (HAB-002) --------------------
  async function refreshHabitsViews() {
    const [weekRes, todayRes] = await Promise.all([
      fetch(`${apiBase}/habits/week`),
      fetch(`${apiBase}/habits/today`),
    ]);
    if (!weekRes.ok || !todayRes.ok) {
      throw new Error("No se pudo actualizar la vista de hábitos");
    }
    const week = await weekRes.json();
    const items = await todayRes.json();
    data.week = week;
    data.habits = items;
    const weekEl = container.querySelector("#widget-content-habits_week");
    if (weekEl) weekEl.innerHTML = renderHabitsWeek(week);
    const todayEl = container.querySelector("#widget-content-habits_today");
    if (todayEl) todayEl.innerHTML = renderHabitsTodayInner(items);
  }

  function renderHabitsTodayInner(items) {
    const done = items.filter((i) => habitTodayState(i) === "done").length;
    const list = items.length
      ? `<ul class="home-habit-list">
          ${items
            .slice(0, MAX_HABITS)
            .map((item) => {
              const state = habitTodayState(item);
              return `
              <li class="home-habit">
                <span class="home-habit__name">${escapeHtml(item.habit.name)}</span>
                <span class="badge badge--${habitStateBadge(state)}">${habitStateLabel(state)}</span>
              </li>
            `;
            })
            .join("")}
        </ul>`
      : `<p class="home-calm">No hay h&aacute;bitos programados para hoy.</p>`;
    return `
      <section class="home-habits" aria-labelledby="home-habits-title">
        <div class="home-section__head">
          <h2 class="home-section__title" id="home-habits-title">H&aacute;bitos de hoy</h2>
          <span class="home-section__summary">${done} de ${items.length} cumplidos</span>
        </div>
        ${list}
        <p class="home-section__foot"><a class="home-section__link" href="#/habits">Abrir h&aacute;bitos</a></p>
      </section>
    `;
  }

  // --- Acciones -------------------------------------------------------------
  async function completeTask(taskId, button) {
    if (button.disabled) return;
    button.disabled = true;
    try {
      const res = await fetch(`${apiBase}/tasks/${taskId}/complete`, { method: "POST" });
      if (res.ok) {
        showToast("Tarea completada", "success");
        await load();
      } else {
        button.disabled = false;
        const err = await res.json().catch(() => ({}));
        showToast(formatApiDetail(err.detail, "No se pudo completar la tarea"), "error");
      }
    } catch (error) {
      button.disabled = false;
      showToast("Error de conexión", "error");
    }
  }

  async function submitQuickTask() {
    if (capturePending.task) return;
    const titleEl = container.querySelector("#home-task-title");
    const projectEl = container.querySelector("#home-task-project");
    if (titleEl) drafts.task.title = titleEl.value;
    if (projectEl) drafts.task.project_id = projectEl.value;
    const title = drafts.task.title.trim();
    if (!title) {
      captureErrors.task = "Escribe un título para la tarea.";
      renderAll();
      focusCapture("task");
      return;
    }
    capturePending.task = true;
    captureErrors.task = "";
    renderAll();
    try {
      const body = { title };
      if (drafts.task.project_id) body.project_id = drafts.task.project_id;
      const res = await fetch(`${apiBase}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        capturePending.task = false;
        drafts.task = { title: "", project_id: "" };
        showToast("Tarea creada", "success");
        await load();
      } else {
        capturePending.task = false;
        const err = await res.json().catch(() => ({}));
        captureErrors.task = formatApiDetail(err.detail, "No se pudo crear la tarea.");
        renderAll();
        focusCapture("task");
      }
    } catch (error) {
      capturePending.task = false;
      captureErrors.task = "Error de conexión. Inténtalo de nuevo.";
      renderAll();
      focusCapture("task");
    }
  }

  async function submitQuickNote() {
    if (capturePending.note) return;
    const titleEl = container.querySelector("#home-note-title");
    if (titleEl) drafts.note.title = titleEl.value;
    const title = drafts.note.title.trim();
    if (!title) {
      captureErrors.note = "Escribe un título para la nota.";
      renderAll();
      focusCapture("note");
      return;
    }
    capturePending.note = true;
    captureErrors.note = "";
    renderAll();
    try {
      const res = await fetch(`${apiBase}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content: "" }),
      });
      if (res.ok) {
        capturePending.note = false;
        drafts.note = { title: "" };
        showToast("Nota creada", "success");
        await load();
      } else {
        capturePending.note = false;
        const err = await res.json().catch(() => ({}));
        captureErrors.note = formatApiDetail(err.detail, "No se pudo crear la nota.");
        renderAll();
        focusCapture("note");
      }
    } catch (error) {
      capturePending.note = false;
      captureErrors.note = "Error de conexión. Inténtalo de nuevo.";
      renderAll();
      focusCapture("note");
    }
  }

  function focusCapture(kind) {
    const id = kind === "task" ? "#home-task-title" : "#home-note-title";
    const el = container.querySelector(id);
    if (el) el.focus();
  }

  // Delegación de eventos: el contenido se re-renderiza con frecuencia.
  container.addEventListener("click", async (event) => {
    const completeBtn = event.target.closest('[data-action="complete-task"]');
    if (completeBtn) {
      await completeTask(completeBtn.dataset.id, completeBtn);
      return;
    }

    const reloadBtn = event.target.closest('[data-action="reload-home"]');
    if (reloadBtn) {
      await load();
      return;
    }

    const cell = event.target.closest('[data-action="wk-edit"]');
    if (cell) {
      if (!currentWeek) return;
      const item = currentWeek.items.find((i) => i.habit.id === cell.dataset.id);
      if (!item) return;
      const day = item.days.find((d) => d.date === cell.dataset.date);
      if (!day) return;
      openHabitEntryEditor({
        apiBase,
        habit: item.habit,
        date: day.date,
        entry: day.entry_status ? { status: day.entry_status, value: day.entry_value } : null,
        today: currentWeek.today,
        onSaved: refreshHabitsViews,
        getFallbackFocus: () => container.querySelector("#widget-habits_week"),
        returnFocusTo: cell,
      });
    }
  });

  container.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-capture]");
    if (!form) return;
    event.preventDefault();
    if (form.dataset.capture === "task") {
      await submitQuickTask();
    } else if (form.dataset.capture === "note") {
      await submitQuickNote();
    }
  });

  // --- Configuración de widgets (modal) -------------------------------------
  function openConfig() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="config-title">
        <h2 class="modal__title" id="config-title">Configurar widgets</h2>
        <p class="modal__text">Selecciona qu&eacute; secciones mostrar y su orden.</p>
        <div id="widgets-config" style="margin-bottom: 16px;"></div>
        <div class="modal__actions">
          <button class="btn btn--secondary" id="widgets-cancel-btn">Cancelar</button>
          <button class="btn btn--primary" id="widgets-save-btn">Guardar preferencias</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const configEl = overlay.querySelector("#widgets-config");
    const saveBtn = overlay.querySelector("#widgets-save-btn");
    const cancelBtn = overlay.querySelector("#widgets-cancel-btn");

    // Renderizar filas de configuración
    const sorted = [...widgets].sort((a, b) => a.position - b.position);
    configEl.innerHTML = sorted
      .map(
        (w, idx) => `
      <div class="widget-config-row" data-widget="${w.widget_id}">
        <label>
          <input type="checkbox" ${w.is_visible ? "checked" : ""}>
          ${w.label}
        </label>
        <div class="widget-config-controls">
          <button class="btn btn--secondary btn--sm" data-move="up" data-idx="${idx}" ${idx === 0 ? "disabled" : ""}>&uarr;</button>
          <button class="btn btn--secondary btn--sm" data-move="down" data-idx="${idx}" ${idx === sorted.length - 1 ? "disabled" : ""}>&darr;</button>
        </div>
      </div>
    `
      )
      .join("");

    // Mover widgets arriba/abajo
    configEl.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-move]");
      if (!btn) return;
      const idx = parseInt(btn.dataset.idx, 10);
      const dir = btn.dataset.move === "up" ? -1 : 1;
      const targetIdx = idx + dir;
      if (targetIdx < 0 || targetIdx >= sorted.length) return;
      [sorted[idx], sorted[targetIdx]] = [sorted[targetIdx], sorted[idx]];
      // Re-render
      configEl.innerHTML = sorted
        .map(
          (w, i) => `
        <div class="widget-config-row" data-widget="${w.widget_id}">
          <label>
            <input type="checkbox" ${w.is_visible ? "checked" : ""}>
            ${w.label}
          </label>
          <div class="widget-config-controls">
            <button class="btn btn--secondary btn--sm" data-move="up" data-idx="${i}" ${i === 0 ? "disabled" : ""}>&uarr;</button>
            <button class="btn btn--secondary btn--sm" data-move="down" data-idx="${i}" ${i === sorted.length - 1 ? "disabled" : ""}>&darr;</button>
          </div>
        </div>
      `
        )
        .join("");
    });

    // Guardar
    saveBtn.addEventListener("click", async () => {
      const prefs = [];
      const rows = configEl.querySelectorAll(".widget-config-row");
      rows.forEach((row, idx) => {
        const widgetId = row.getAttribute("data-widget");
        const checkbox = row.querySelector("input[type=checkbox]");
        prefs.push({
          widget_id: widgetId,
          is_visible: checkbox.checked,
          position: idx,
        });
      });

      const res = await fetch(`${apiBase}/dashboard/widgets`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });

      if (res.ok) {
        overlay.remove();
        showToast("Preferencias guardadas", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error guardando preferencias", "error");
      }
    });

    // Cancelar
    cancelBtn.addEventListener("click", () => overlay.remove());
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    // Escape para cerrar
    const onKey = (e) => {
      if (e.key === "Escape") {
        overlay.remove();
        document.removeEventListener("keydown", onKey);
      }
    };
    document.addEventListener("keydown", onKey);

    // Focus en el primer checkbox
    const firstCheckbox = configEl.querySelector("input[type=checkbox]");
    if (firstCheckbox) firstCheckbox.focus();
  }

  editBtn.addEventListener("click", openConfig);

  await load();
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  // Escapa también comillas: los valores usados en atributos (aria-label,
  // title) deben seguir siendo seguros con nombres de usuario.
  const amp = String.fromCharCode(38);
  return div.innerHTML
    .replace(/"/g, `${amp}quot;`)
    .replace(/'/g, `${amp}#39;`);
}
