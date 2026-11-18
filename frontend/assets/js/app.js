// Life OS — aplicación principal (enrutamiento basado en hash, JavaScript nativo)

import { renderProjectsView } from "./projects.js";
import { renderTasksView } from "./tasks.js";
import { renderNotesView } from "./notes.js";
import { renderHabitsView } from "./habits.js";
import { renderHomeView } from "./home.js";
import { renderSettingsView } from "./settings.js";

const API_BASE = "/api/v1";
const statusEl = document.getElementById("status");
const viewEl = document.getElementById("app-view");
const navLinks = document.querySelectorAll(".nav__link");

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    await response.json();
    statusEl.textContent = "Servicio activo";
    statusEl.style.color = "#267568";
  } catch (error) {
    statusEl.textContent = "Servicio no disponible";
    statusEl.style.color = "#9B3A3A";
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
  setActiveNav(hash === "#/home" ? "#/" : hash);

  if (hash === "#/" || hash === "" || hash === "#/home") {
    // Home abre el dashboard con widgets (Fase 4); el stub anterior dejaba
    // el dashboard inalcanzable desde la navegación.
    await renderHomeView(viewEl, API_BASE);
  } else if (hash === "#/projects") {
    await renderProjectsView(viewEl, API_BASE);
  } else if (hash === "#/tasks") {
    await renderTasksView(viewEl, API_BASE);
  } else if (hash === "#/notes") {
    await renderNotesView(viewEl, API_BASE);
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
