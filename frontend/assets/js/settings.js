// Life OS — vista de Configuración

export async function renderSettingsView(container, apiBase) {
  container.innerHTML = `
    <h1>Configuraci&oacute;n</h1>
    <p class="subtitle">Preferencias de la aplicaci&oacute;n</p>

    <div class="card" style="margin-bottom: 24px;">
      <h3>Apariencia</h3>
      <div class="form-group" style="margin-bottom: 16px;">
        <label for="setting-theme">Tema</label>
        <select id="setting-theme">
          <option value="system">Sistema</option>
          <option value="light">Claro</option>
          <option value="dark">Oscuro</option>
        </select>
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-top:4px;">El tema oscuro se aplica a toda la interfaz.</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
      <h3>Zona horaria</h3>
      <div class="form-group" style="margin-bottom: 16px;">
        <label for="setting-timezone">Zona horaria</label>
        <input type="text" id="setting-timezone" placeholder="Ej. America/Argentina/Cordoba">
        <p style="font-size:0.875rem;color:var(--text-secondary);margin-top:4px;">Se usa para mostrar fechas y determinar tareas vencidas.</p>
      </div>
    </div>

    <div class="card">
      <h3>Preferencias del dashboard</h3>
      <p class="subtitle">Administra la visibilidad y el orden de los widgets de Home.</p>
      <div id="dashboard-widgets-config" style="margin-top: 12px;"></div>
      <button class="btn btn--primary" id="settings-save-widgets" style="margin-top: 12px;">Guardar widgets</button>
    </div>
  `;

  const themeSelect = container.querySelector("#setting-theme");
  const timezoneInput = container.querySelector("#setting-timezone");
  const widgetsConfigEl = container.querySelector("#dashboard-widgets-config");
  const saveWidgetsBtn = container.querySelector("#settings-save-widgets");

  let widgets = [];

  async function load() {
    // Tema
    const themeRes = await fetch(`${apiBase}/settings/theme`);
    const themeData = await themeRes.json();
    themeSelect.value = themeData.theme || "system";

    // Zona horaria
    const tzRes = await fetch(`${apiBase}/settings/timezone`);
    const tzData = await tzRes.json();
    timezoneInput.value = tzData.timezone || "America/Argentina/Cordoba";

    // Widgets
    const wRes = await fetch(`${apiBase}/dashboard/widgets`);
    widgets = await wRes.json();
    renderWidgetsConfig();
  }

  function renderWidgetsConfig() {
    const sorted = [...widgets].sort((a, b) => a.position - b.position);
    widgetsConfigEl.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Widget</th><th>Visible</th><th>Orden</th></tr>
        </thead>
        <tbody>
          ${sorted.map((w, idx) => `
            <tr>
              <td><strong>${w.label}</strong><br><small style="color:var(--text-secondary);">${w.description}</small></td>
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
    `;
  }

  themeSelect.addEventListener("change", async () => {
    const res = await fetch(`${apiBase}/settings/theme`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: themeSelect.value }),
    });
    if (res.ok) {
      applyTheme(themeSelect.value);
    } else {
      const err = await res.json();
      alert(err.detail || "Error guardando tema");
    }
  });

  timezoneInput.addEventListener("change", async () => {
    const res = await fetch(`${apiBase}/settings/timezone`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ timezone: timezoneInput.value }),
    });
    if (!res.ok) {
      const err = await res.json();
      alert(err.detail || "Error guardando zona horaria");
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
      // Obtener el widget_id del checkbox
      const widgetId = checkbox.getAttribute("data-widget");
      prefs.push({
        widget_id: widgetId,
        is_visible: checkbox.checked,
        position: parseInt(positionInput.value) || 0,
      });
    });

    const res = await fetch(`${apiBase}/dashboard/widgets`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    });

    if (res.ok) {
      await load();
      alert("Preferencias guardadas");
    } else {
      const err = await res.json();
      alert(err.detail || "Error guardando widgets");
    }
  });

  await load();
}

let currentTheme = "system";

function applyTheme(theme) {
  currentTheme = theme || "system";
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const useDark = currentTheme === "dark" || (currentTheme === "system" && prefersDark);
  document.body.classList.toggle("theme-dark", useDark);
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

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}