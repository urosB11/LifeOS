// Life OS — aplicación principal (enrutamiento basado en hash, JavaScript nativo)

import { renderProjectsView } from "./projects.js";
import { renderTasksView } from "./tasks.js";
import { renderNotesView } from "./notes.js";

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
    link.classList.toggle("active", link.getAttribute("href") === path);
  });
}

function renderHome() {
  viewEl.innerHTML = `
    <h1>Life OS</h1>
    <p class="subtitle">Centro de operaciones personal &mdash; MVP 0.1</p>
    <p>Selecciona Proyectos o Tareas en la navegaci&oacute;n para comenzar.</p>
  `;
}

async function route() {
  const hash = location.hash || "#/";
  setActiveNav(hash);

  if (hash === "#/" || hash === "") {
    renderHome();
  } else if (hash === "#/projects") {
    await renderProjectsView(viewEl, API_BASE);
  } else if (hash === "#/tasks") {
    await renderTasksView(viewEl, API_BASE);
  } else if (hash === "#/notes") {
    await renderNotesView(viewEl, API_BASE);
  } else {
    viewEl.innerHTML = `<p class="empty-state">Vista no encontrada.</p>`;
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("load", () => {
  checkHealth();
  route();
});