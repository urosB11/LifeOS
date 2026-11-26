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
    <p id="settings-load-error" class="home-error__text" role="alert" hidden>
      No se pudieron cargar las preferencias de configuraci&oacute;n.
    </p>

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
      <h3 style="margin-top:0;">Secciones de Home</h3>
      <p class="subtitle">La visibilidad y el orden se personalizan desde Home.</p>
      <a class="btn btn--secondary" href="#/">Ir a Home</a>
    </div>
  `;

  const themeSelect = container.querySelector("#setting-theme");
  const timezoneInput = container.querySelector("#setting-timezone");
  const loadErrorEl = container.querySelector("#settings-load-error");

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

    } catch (error) {
      loadErrorEl.hidden = false;
    }
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
