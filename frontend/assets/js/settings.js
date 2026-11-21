// Life OS — vista de Configuración (Fase 8C)
//
// Preferencias, temas y configuración general. Usa componentes de 8A.

import { showToast } from "./app.js";

export async function renderSettingsView(container, apiBase) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1>Configuraci&oacute;n</h1>
        <p class="subtitle">Preferencias de la aplicaci&oacute;n</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3 style="margin-top:0;">Apariencia</h3>
      <div class="form-group" style="margin-bottom: 16px;">
        <label for="setting-theme">Tema</label>
        <select id="setting-theme">
          <option value="system">Sistema</option>
          <option value="light">Claro</option>
          <option value="dark">Oscuro</option>
        </select>
        <p class="text-secondary" style="font-size:0.875rem; margin-top:4px;">
          El tema oscuro se aplica a toda la interfaz.
        </p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3 style="margin-top:0;">Zona horaria</h3>
      <div class="form-group" style="margin-bottom: 16px;">
        <label for="setting-timezone">Zona horaria</label>
        <input type="text" id="setting-timezone" placeholder="Ej. America/Argentina/Cordoba">
        <p class="text-secondary" style="font-size:0.875rem; margin-top:4px;">
          Se usa para mostrar fechas y determinar tareas vencidas.
        </p>
      </div>
    </div>

    <div class="card">
      <h3 style="margin-top:0;">Preferencias del dashboard</h3>
      <p class="subtitle">Administra la visibilidad y el orden de los widgets de Home.</p>
      <div id="dashboard-widgets-config" style="margin-top: 12px;">
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#8987;</div>
          <p class="empty-state__title">Cargando&hellip;</p>
        </div>
      </div>
      <button class="btn btn--primary" id="settings-save-widgets" style="margin-top: 12px;">Guardar widgets</button>
    </div>
  `;

  const themeSelect = container.querySelector("#setting-theme");
  const timezoneInput = container.querySelector("#setting-timezone");
  const widgetsConfigEl = container.querySelector("#dashboard-widgets-config");
  const saveWidgetsBtn = container.querySelector("#settings-save-widgets");

  let widgets = [];

  async function load() {
    try {
      // Tema
      const themeRes = await fetch(`${apiBase}/settings/theme`);
      if (!themeRes.ok) throw new Error(`HTTP ${themeRes.status}`);
      const themeData = await themeRes.json();
      themeSelect.value = themeData.theme || "system";

      // Zona horaria
      const tzRes = await fetch(`${apiBase}/settings/timezone`);
      if (tzRes.ok) {
        const tzData = await tzRes.json();
        timezoneInput.value = tzData.timezone || "America/Argentina/Cordoba";
      }

      // Widgets
      const wRes = await fetch(`${apiBase}/dashboard/widgets`);
      if (!wRes.ok) throw new Error(`HTTP ${wRes.status}`);
      widgets = await wRes.json();
      renderWidgetsConfig();
    } catch (error) {
      widgetsConfigEl.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#9888;</div>
          <p class="empty-state__title">Error al cargar</p>
          <p class="empty-state__text">No se pudieron cargar las preferencias.</p>
        </div>
      `;
    }
  }

  function renderWidgetsConfig() {
    if (widgets.length === 0) {
      widgetsConfigEl.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon" aria-hidden="true">&#128193;</div>
          <p class="empty-state__title">Sin widgets</p>
          <p class="empty-state__text">No hay widgets configurables.</p>
        </div>
      `;
      return;
    }
    const sorted = [...widgets].sort((a, b) => a.position - b.position);
    widgetsConfigEl.innerHTML = `
      <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>Widget</th><th>Visible</th><th>Orden</th></tr>
        </thead>
        <tbody>
          ${sorted.map((w, idx) => `
            <tr>
              <td><strong>${w.label}</strong><br><small class="text-secondary">${w.description}</small></td>
              <td>
                <input type="checkbox" ${w.is_visible ? "checked" : ""} data-widget="${w.widget_id}">
              </td>
              <td>
                <input type="number" value="${w.position}" min="0" data-widget="${w.widget_id}" style="width:60px;">
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      </div>
    `;
  }

  themeSelect.addEventListener("change", async () => {
    try {
      const res = await fetch(`${apiBase}/settings/theme`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme: themeSelect.value }),
      });
      if (res.ok) {
        applyTheme(themeSelect.value);
        showToast("Tema actualizado", "success");
      } else {
        const err = await res.json();
        showToast(err.detail || "Error guardando tema", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    }
  });

  timezoneInput.addEventListener("change", async () => {
    try {
      const res = await fetch(`${apiBase}/settings/timezone`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timezone: timezoneInput.value }),
      });
      if (res.ok) {
        showToast("Zona horaria guardada", "success");
      } else {
        const err = await res.json();
        showToast(err.detail || "Error guardando zona horaria", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    }
  });

  saveWidgetsBtn.addEventListener("click", async () => {
    const prefs = [];
    const rows = widgetsConfigEl.querySelectorAll("tr");
    rows.forEach((row, idx) => {
      // Saltar header
      if (idx === 0) return;
      const checkbox = row.querySelector("input[type=checkbox]");
      const positionInput = row.querySelector("input[type=number]");
      const widgetId = checkbox.getAttribute("data-widget");
      prefs.push({
        widget_id: widgetId,
        is_visible: checkbox.checked,
        position: parseInt(positionInput.value) || 0,
      });
    });

    saveWidgetsBtn.disabled = true;
    saveWidgetsBtn.textContent = "Guardando…";
    try {
      const res = await fetch(`${apiBase}/dashboard/widgets`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prefs),
      });

      if (res.ok) {
        showToast("Preferencias guardadas", "success");
        await load();
      } else {
        const err = await res.json();
        showToast(err.detail || "Error guardando widgets", "error");
      }
    } catch (error) {
      showToast("Error de conexión", "error");
    } finally {
      saveWidgetsBtn.disabled = false;
      saveWidgetsBtn.textContent = "Guardar widgets";
    }
  });

  await load();
}

let currentTheme = "system";

function applyTheme(theme) {
  currentTheme = theme || "system";
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const useDark = currentTheme === "dark" || (currentTheme === "system" && prefersDark);
  // `:root` ya define la paleta oscura: para el tema claro hay que marcar
  // explícitamente `theme-light` en el body (si no, nunca se aplica).
  document.body.classList.toggle("theme-dark", useDark);
  document.body.classList.toggle("theme-light", currentTheme === "light");
}

// "Sistema" sigue la preferencia del SO en tiempo real
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (currentTheme === "system") applyTheme("system");
});

// Aplicar tema guardado al cargar el módulo
fetch("/api/v1/settings/theme")
  .then((r) => r.json())
  .then((data) => {
    applyTheme(data.theme || "system");
  })
  .catch(() => {
    // Si falla, se usa el tema por defecto (sistema)
  });

export { applyTheme };
