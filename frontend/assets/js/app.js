// Life OS — aplicación principal (enrutamiento basado en hash, JavaScript nativo)

import { renderProjectsView, renderProjectDetailView } from "./projects.js";
import { renderTasksView } from "./tasks.js";
import { renderNotesView } from "./notes.js";
import { renderHabitsView } from "./habits.js";
import { renderHomeView } from "./home.js";
import { renderSettingsView } from "./settings.js";
import {
  renderMindHomeView,
  renderMindInboxView,
  renderMindSpaceView,
} from "./mind.js";
import { renderMindCanvasView } from "./mind-canvas.js";

const API_BASE = "/api/v1";
const statusEl = document.getElementById("status");
const statusMobileEl = document.getElementById("status-mobile");
const viewEl = document.getElementById("app-view");
const navLinks = document.querySelectorAll(".nav__link");

// --- Sidebar (Fase 8B) ------------------------------------------------------
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebar-overlay");
const menuBtn = document.getElementById("menu-btn");
const sidebarClose = document.getElementById("sidebar-close");

function openSidebar() {
  sidebar.classList.add("open");
  sidebarOverlay.classList.add("visible");
  menuBtn.setAttribute("aria-expanded", "true");
  document.body.style.overflow = "hidden";
}

function closeSidebar() {
  sidebar.classList.remove("open");
  sidebarOverlay.classList.remove("visible");
  menuBtn.setAttribute("aria-expanded", "false");
  document.body.style.overflow = "";
}

menuBtn.addEventListener("click", () => {
  if (sidebar.classList.contains("open")) {
    closeSidebar();
  } else {
    openSidebar();
  }
});

sidebarClose.addEventListener("click", closeSidebar);
sidebarOverlay.addEventListener("click", closeSidebar);

// Cerrar sidebar al navegar (en móvil)
navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    if (window.innerWidth <= 768) closeSidebar();
  });
});

// Cerrar sidebar con Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && sidebar.classList.contains("open")) {
    closeSidebar();
  }
});

// --- Toast (Fase 8A) -------------------------------------------------------
let toastContainer = null;

function ensureToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    toastContainer.setAttribute("role", "status");
    toastContainer.setAttribute("aria-live", "polite");
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

export function showToast(message, type = "info", duration = 4000) {
  const container = ensureToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast__close" aria-label="Cerrar">&times;</button>
  `;
  const closeBtn = toast.querySelector(".toast__close");
  closeBtn.addEventListener("click", () => toast.remove());
  container.appendChild(toast);
  if (duration > 0) {
    setTimeout(() => {
      if (toast.parentNode) toast.remove();
    }, duration);
  }
}

// --- Confirmación modal (Fase 8A + 8D: focus trap) --------------------------
export function showConfirm({ title, text, confirmLabel = "Confirmar", cancelLabel = "Cancelar", danger = false }) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h2 class="modal__title" id="modal-title">${title}</h2>
        <p class="modal__text">${text}</p>
        <div class="modal__actions">
          <button class="btn btn--secondary" data-action="cancel">${cancelLabel}</button>
          <button class="btn ${danger ? "btn--danger" : "btn--primary"}" data-action="confirm">${confirmLabel}</button>
        </div>
      </div>
    `;
    const previouslyFocused = document.activeElement;
    function close(result) {
      overlay.remove();
      document.removeEventListener("keydown", onKey, true);
      if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
      resolve(result);
    }
    function onKey(e) {
      if (e.key === "Escape") {
        e.preventDefault();
        close(false);
        return;
      }
      // Focus trap: mantener el foco dentro del modal
      if (e.key === "Tab") {
        const focusable = overlay.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
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
      if (e.target === overlay) close(false);
      const action = e.target.closest("[data-action]")?.dataset.action;
      if (action === "confirm") close(true);
      if (action === "cancel") close(false);
    });
    document.addEventListener("keydown", onKey, true);
    document.body.appendChild(overlay);
    overlay.querySelector('[data-action="confirm"]').focus();
  });
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await response.json();
    if (statusEl) {
      statusEl.textContent = "Servicio activo";
      statusEl.style.color = "var(--success)";
    }
    if (statusMobileEl) {
      statusMobileEl.textContent = "Servicio activo";
      statusMobileEl.style.color = "var(--success)";
    }
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = "Servicio no disponible";
      statusEl.style.color = "var(--danger)";
    }
    if (statusMobileEl) {
      statusMobileEl.textContent = "Servicio no disponible";
      statusMobileEl.style.color = "var(--danger)";
    }
  }
}

function setActiveNav(path) {
  navLinks.forEach((link) => {
    const active = link.getAttribute("href") === path;
    link.classList.toggle("active", active);
    if (active) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

async function route() {
  const hash = location.hash || "#/";
  // "#/home" es un alias legible de "#/" (el dashboard real)
  // "#/projects/:id" mantiene activo el enlace de Proyectos
  // "#/mind/..." mantiene activo el enlace de Mind
  let navHash = hash;
  if (hash.startsWith("#/projects/")) {
    navHash = "#/projects";
  } else if (hash.startsWith("#/mind")) {
    navHash = "#/mind";
  }
  setActiveNav(navHash === "#/home" ? "#/" : navHash);

  if (hash === "#/" || hash === "" || hash === "#/home") {
    // Home abre el dashboard con widgets (Fase 4); el stub anterior dejaba
    // el dashboard inalcanzable desde la navegación.
    await renderHomeView(viewEl, API_BASE);
  } else if (hash === "#/projects") {
    await renderProjectsView(viewEl, API_BASE);
  } else if (hash.startsWith("#/projects/")) {
    const projectId = hash.replace("#/projects/", "");
    await renderProjectDetailView(viewEl, API_BASE, projectId);
  } else if (hash === "#/tasks") {
    await renderTasksView(viewEl, API_BASE);
  } else if (hash === "#/notes") {
    await renderNotesView(viewEl, API_BASE);
  } else if (hash === "#/mind") {
    await renderMindHomeView(viewEl, API_BASE);
  } else if (hash === "#/mind/inbox") {
    await renderMindInboxView(viewEl, API_BASE);
  } else if (hash.startsWith("#/mind/spaces/")) {
    const spaceId = hash.replace("#/mind/spaces/", "");
    await renderMindSpaceView(viewEl, API_BASE, spaceId);
  } else if (hash.startsWith("#/mind/canvases/")) {
    const canvasId = hash.replace("#/mind/canvases/", "");
    await renderMindCanvasView(viewEl, API_BASE, canvasId);
  } else if (hash === "#/habits") {
    await renderHabitsView(viewEl, API_BASE);
  } else if (hash === "#/settings") {
    await renderSettingsView(viewEl, API_BASE);
  } else {
    viewEl.innerHTML = `<p class="empty-state">Vista no encontrada.</p>`;
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("load", () => {
  checkHealth();
  route();
});
