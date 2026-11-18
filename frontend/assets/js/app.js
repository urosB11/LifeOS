// Life OS — frontend JavaScript nativo (módulo ES, sin build step)

const statusEl = document.getElementById("status");
const messageEl = document.getElementById("message");

async function checkHealth() {
  try {
    const response = await fetch("/api/v1/health");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    statusEl.textContent = "Servicio activo";
    statusEl.style.color = "#267568";
    messageEl.textContent = `Life OS ${data.version} — base de datos: ${data.database}. Todo operativo.`;
  } catch (error) {
    statusEl.textContent = "Servicio no disponible";
    statusEl.style.color = "#9B3A3A";
    messageEl.textContent = `No se pudo conectar con la API: ${error.message}`;
  }
}

checkHealth();