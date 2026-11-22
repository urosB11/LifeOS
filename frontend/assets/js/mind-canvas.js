// Life OS — workspace de Canvas de Mind (MIND-002)
//
// Lienzo libre con pan, zoom, Cards de texto y persistencia de posición.
// Las coordenadas se guardan en el mundo (independientes del viewport y del
// zoom), por lo que el mismo Canvas se abre igual en distintas pantallas.

import { showToast, showConfirm } from "./app.js";
import {
  apiJson,
  escapeHtml,
  errorState,
  loadingState,
  showFormModal,
} from "./mind-common.js";

const MIN_SCALE = 0.25;
const MAX_SCALE = 2.5;
const KEYBOARD_STEP = 8;
const KEYBOARD_STEP_BIG = 40;
const CARD_WIDTH = 240;
const CARD_HEIGHT = 160;

export async function renderMindCanvasView(container, apiBase, canvasId) {
  container.innerHTML = `
    <div class="section-header">
      <div>
        <h1 id="mind-canvas-title">Canvas</h1>
        <p class="subtitle" id="mind-canvas-description"></p>
      </div>
      <a class="btn btn--secondary" href="#/mind" id="mind-canvas-back">Volver a Mind</a>
    </div>
    <div id="mind-canvas-body" class="empty-state">${loadingState("Cargando Canvas…")}</div>
  `;

  const titleEl = container.querySelector("#mind-canvas-title");
  const descriptionEl = container.querySelector("#mind-canvas-description");
  const bodyEl = container.querySelector("#mind-canvas-body");

  let canvas = null;
  let nodes = [];
  let scale = 1;
  let tx = 40;
  let ty = 40;
  let panState = null;
  let dragState = null;
  let pinchState = null;
  let pendingSave = null;
  let saveTimer = null;

  const viewport = document.createElement("div");
  viewport.className = "mind-canvas__viewport";
  viewport.tabIndex = 0;
  viewport.setAttribute("role", "application");
  viewport.setAttribute(
    "aria-label",
    "Área de trabajo del Canvas. Con las flechas movés el lienzo, con + y - hacés zoom y con 0 volvés al 100 por ciento. Cada Card se puede mover con las flechas cuando tiene el foco."
  );

  const world = document.createElement("div");
  world.className = "mind-canvas__world";
  viewport.appendChild(world);

  let zoomLabel = null;

  const statusEl = document.createElement("p");
  statusEl.className = "mind-canvas__status";
  statusEl.setAttribute("role", "status");
  statusEl.setAttribute("aria-live", "polite");

  function setStatus(text, tone = "") {
    statusEl.className = `mind-canvas__status ${tone}`.trim();
    if (tone === "is-error") {
      statusEl.innerHTML = `${escapeHtml(
        text
      )} <button class="btn btn--secondary btn--sm" type="button" data-action="retry">Reintentar</button>`;
    } else {
      statusEl.textContent = text;
    }
  }

  function applyTransform() {
    world.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
    if (zoomLabel) zoomLabel.textContent = `${Math.round(scale * 100)}%`;
  }

  function clampScale(value) {
    return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));
  }

  function setScale(next, clientX, clientY) {
    const clamped = clampScale(next);
    if (clientX !== undefined && clientY !== undefined) {
      const rect = viewport.getBoundingClientRect();
      const sx = clientX - rect.left;
      const sy = clientY - rect.top;
      const wx = (sx - tx) / scale;
      const wy = (sy - ty) / scale;
      tx = sx - wx * clamped;
      ty = sy - wy * clamped;
    }
    scale = clamped;
    applyTransform();
  }

  function screenToWorld(clientX, clientY) {
    const rect = viewport.getBoundingClientRect();
    return {
      x: (clientX - rect.left - tx) / scale,
      y: (clientY - rect.top - ty) / scale,
    };
  }

  function fitToContent() {
    if (!nodes.length) {
      scale = 1;
      tx = 40;
      ty = 40;
      applyTransform();
      return;
    }
    const minX = Math.min(...nodes.map((n) => n.x));
    const minY = Math.min(...nodes.map((n) => n.y));
    const maxX = Math.max(...nodes.map((n) => n.x + (n.width || CARD_WIDTH)));
    const maxY = Math.max(...nodes.map((n) => n.y + (n.height || CARD_HEIGHT)));
    const rect = viewport.getBoundingClientRect();
    const padding = 48;
    const contentW = Math.max(1, maxX - minX);
    const contentH = Math.max(1, maxY - minY);
    // No se baja de 50%: por debajo el texto de las Cards deja de ser legible;
    // el resto del lienzo se alcanza desplazando el canvas.
    scale = clampScale(
      Math.max(
        0.5,
        Math.min((rect.width - padding * 2) / contentW, (rect.height - padding * 2) / contentH, 1)
      )
    );
    tx = (rect.width - contentW * scale) / 2 - minX * scale;
    ty = (rect.height - contentH * scale) / 2 - minY * scale;
    applyTransform();
  }

  // --- Guardado de posición -------------------------------------------------

  async function persistPosition(node, x, y, zIndex) {
    const body = { x, y };
    if (typeof zIndex === "number") body.z_index = zIndex;
    setStatus("Guardando posición…", "is-saving");
    try {
      await apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes/${node.id}`, {
        method: "PATCH",
        body,
      });
      node.x = x;
      node.y = y;
      node.savedX = x;
      node.savedY = y;
      if (typeof zIndex === "number") node.z_index = zIndex;
      pendingSave = null;
      setStatus("Posición guardada", "is-saved");
    } catch (err) {
      pendingSave = { node, x, y, zIndex };
      setStatus(`No se pudo guardar la posición: ${err.message}`, "is-error");
      showToast(err.message || "Error al guardar la posición", "error");
    }
  }

  function scheduleSave(node, x, y, zIndex) {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveTimer = null;
      persistPosition(node, x, y, zIndex);
    }, 400);
  }

  function retrySave() {
    if (!pendingSave) return;
    const { node, x, y, zIndex } = pendingSave;
    persistPosition(node, x, y, zIndex);
  }

  // --- Render de Cards ------------------------------------------------------

  function cardHtml(node) {
    const note = node.note || {};
    const style = `left:${node.x}px; top:${node.y}px; z-index:${node.z_index};`;
    const sizeStyle = node.width
      ? `width:${node.width}px;`
      : "";
    return `
      <article class="mind-card" tabindex="0" data-node-id="${node.id}" style="${style}${sizeStyle}"
        aria-label="Card: ${escapeHtml(note.title || "Sin título")}">
        <header class="mind-card__head" title="Arrastrá para mover la Card">
          <h3 class="mind-card__title">${escapeHtml(note.title || "Sin título")}</h3>
          <div class="mind-card__actions">
            <button class="btn btn--secondary btn--sm" type="button" data-action="edit">Editar</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="remove">Quitar</button>
          </div>
        </header>
        <div class="mind-card__body">${escapeHtml(note.content || "")}</div>
      </article>
    `;
  }

  function renderNodes() {
    world.innerHTML = nodes.map(cardHtml).join("");
    const empty = bodyEl.querySelector("#mind-canvas-empty");
    if (empty) {
      empty.hidden = nodes.length > 0;
    }
    applyTransform();
  }

  function nodeById(nodeId) {
    return nodes.find((n) => n.id === nodeId);
  }

  function cardElement(nodeId) {
    return world.querySelector(`.mind-card[data-node-id="${nodeId}"]`);
  }

  async function bringToFront(node) {
    const maxZ = nodes.reduce((acc, n) => Math.max(acc, n.z_index || 0), 0);
    if (node.z_index >= maxZ) return;
    const z = maxZ + 1;
    node.z_index = z;
    const el = cardElement(node.id);
    if (el) el.style.zIndex = String(z);
    try {
      await apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes/${node.id}`, {
        method: "PATCH",
        body: { z_index: z },
      });
    } catch {
      // El orden visual no es crítico: se reintenta en la próxima interacción.
    }
  }

  // --- Interacción: pan, zoom y drag ---------------------------------------

  viewport.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    if (pinchState) return;
    const card = e.target.closest(".mind-card");
    const head = e.target.closest(".mind-card__head");
    if (card && head && !e.target.closest("button")) {
      const node = nodeById(card.dataset.nodeId);
      if (!node) return;
      const el = card;
      dragState = {
        node,
        el,
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        originX: node.x,
        originY: node.y,
        moved: false,
      };
      el.classList.add("is-dragging");
      viewport.setPointerCapture(e.pointerId);
      e.preventDefault();
      return;
    }
    if (card) {
      const node = nodeById(card.dataset.nodeId);
      if (node) bringToFront(node);
      return;
    }
    panState = {
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      originTx: tx,
      originTy: ty,
    };
    viewport.setPointerCapture(e.pointerId);
    viewport.classList.add("is-panning");
  });

  viewport.addEventListener("pointermove", (e) => {
    if (pinchState) return;
    if (dragState && e.pointerId === dragState.pointerId) {
      const dx = (e.clientX - dragState.startX) / scale;
      const dy = (e.clientY - dragState.startY) / scale;
      const x = Math.round(dragState.originX + dx);
      const y = Math.round(dragState.originY + dy);
      dragState.moved = true;
      dragState.el.style.left = `${x}px`;
      dragState.el.style.top = `${y}px`;
      return;
    }
    if (panState && e.pointerId === panState.pointerId) {
      tx = panState.originTx + (e.clientX - panState.startX);
      ty = panState.originTy + (e.clientY - panState.startY);
      applyTransform();
    }
  });

  function endPointerInteraction(e, cancelled) {
    if (dragState && e.pointerId === dragState.pointerId) {
      const { node, el, moved, originX, originY } = dragState;
      el.classList.remove("is-dragging");
      if (cancelled) {
        // Escape: se descarta el movimiento incompleto.
        el.style.left = `${originX}px`;
        el.style.top = `${originY}px`;
      } else if (moved) {
        const x = parseFloat(el.style.left);
        const y = parseFloat(el.style.top);
        persistPosition(node, x, y);
      }
      dragState = null;
    }
    if (panState && e.pointerId === panState.pointerId) {
      panState = null;
      viewport.classList.remove("is-panning");
    }
  }

  viewport.addEventListener("pointerup", (e) => endPointerInteraction(e, false));
  viewport.addEventListener("pointercancel", (e) => endPointerInteraction(e, true));

  viewport.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      setScale(scale * factor, e.clientX, e.clientY);
    },
    { passive: false }
  );

  // Pellizco con dos dedos (táctil): zoom centrado en el punto medio.
  function touchDistance(a, b) {
    return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
  }
  function touchMid(a, b) {
    return { x: (a.clientX + b.clientX) / 2, y: (a.clientY + b.clientY) / 2 };
  }
  viewport.addEventListener(
    "touchstart",
    (e) => {
      if (e.touches.length !== 2) return;
      const [a, b] = e.touches;
      pinchState = { dist: touchDistance(a, b), scale, tx, ty };
      dragState = null;
      panState = null;
    },
    { passive: true }
  );
  viewport.addEventListener(
    "touchmove",
    (e) => {
      if (!pinchState || e.touches.length !== 2) return;
      e.preventDefault();
      const [a, b] = e.touches;
      const dist = touchDistance(a, b);
      const next = clampScale(pinchState.scale * (dist / pinchState.dist));
      const rect = viewport.getBoundingClientRect();
      const mid = touchMid(a, b);
      const sx = mid.x - rect.left;
      const sy = mid.y - rect.top;
      const wx = (sx - pinchState.tx) / pinchState.scale;
      const wy = (sy - pinchState.ty) / pinchState.scale;
      tx = sx - wx * next;
      ty = sy - wy * next;
      scale = next;
      applyTransform();
    },
    { passive: false }
  );
  viewport.addEventListener("touchend", () => {
    pinchState = null;
  });

  viewport.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && dragState) {
      // Escape cancela el drag sin guardar la posición.
      const { el, originX, originY } = dragState;
      el.style.left = `${originX}px`;
      el.style.top = `${originY}px`;
      el.classList.remove("is-dragging");
      dragState = null;
      setStatus("Movimiento cancelado", "");
      e.preventDefault();
      return;
    }
    const card = e.target.closest(".mind-card");
    if (card) {
      handleCardKeydown(e, card);
      return;
    }
    const panStep = e.shiftKey ? 120 : 40;
    switch (e.key) {
      case "ArrowLeft":
        tx += panStep;
        break;
      case "ArrowRight":
        tx -= panStep;
        break;
      case "ArrowUp":
        ty += panStep;
        break;
      case "ArrowDown":
        ty -= panStep;
        break;
      case "+":
      case "=":
        setScale(scale * 1.1);
        break;
      case "-":
      case "_":
        setScale(scale / 1.1);
        break;
      case "0":
        scale = 1;
        applyTransform();
        break;
      default:
        return;
    }
    e.preventDefault();
    applyTransform();
  });

  function handleCardKeydown(e, card) {
    const node = nodeById(card.dataset.nodeId);
    if (!node) return;
    const editingField = e.target.matches("input, textarea");
    if (editingField && e.key !== "Escape") {
      // Dentro del editor las flechas mueven el cursor, no la Card.
      return;
    }
    const step = e.shiftKey ? KEYBOARD_STEP_BIG : KEYBOARD_STEP;
    let dx = 0;
    let dy = 0;
    if (e.key === "ArrowLeft") dx = -step;
    else if (e.key === "ArrowRight") dx = step;
    else if (e.key === "ArrowUp") dy = -step;
    else if (e.key === "ArrowDown") dy = step;
    else if (e.key === "Enter" && !editingField) {
      e.preventDefault();
      openEditor(node);
      return;
    } else if (e.key === "Escape") {
      if (card.classList.contains("is-editing")) {
        closeEditor(node, card, true);
        e.preventDefault();
        return;
      }
      // Escape cancela un movimiento por teclado todavía no guardado.
      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }
      if (node.savedX !== undefined) {
        node.x = node.savedX;
        node.y = node.savedY;
        card.style.left = `${node.savedX}px`;
        card.style.top = `${node.savedY}px`;
        setStatus("Movimiento cancelado", "");
      }
      e.preventDefault();
      return;
    } else {
      return;
    }
    e.preventDefault();
    const x = node.x + dx;
    const y = node.y + dy;
    node.x = x;
    node.y = y;
    card.style.left = `${x}px`;
    card.style.top = `${y}px`;
    setStatus("Guardando posición…", "is-saving");
    scheduleSave(node, x, y);
  }

  // --- Edición del contenido de una Card -----------------------------------

  function openEditor(node) {
    const card = cardElement(node.id);
    if (!card || card.classList.contains("is-editing")) return;
    const note = node.note || {};
    card.classList.add("is-editing");
    card.querySelector(".mind-card__body").innerHTML = `
      <form class="mind-card__editor" data-node-id="${node.id}">
        <label class="mind-card__label" for="mind-card-title-${node.id}">Título</label>
        <input type="text" id="mind-card-title-${node.id}" class="mind-card__input" maxlength="200"
          value="${escapeHtml(note.title || "")}">
        <label class="mind-card__label" for="mind-card-content-${node.id}">Contenido</label>
        <textarea id="mind-card-content-${node.id}" class="mind-card__input" rows="5" maxlength="100000"
          required>${escapeHtml(note.content || "")}</textarea>
        <div class="btn-group">
          <button class="btn btn--primary btn--sm" type="submit">Guardar</button>
          <button class="btn btn--secondary btn--sm" type="button" data-action="cancel-edit">Cancelar</button>
          <button class="btn btn--danger btn--sm" type="button" data-action="delete-note">Eliminar nota</button>
        </div>
        <p class="mind-card__status" role="status" aria-live="polite"></p>
      </form>
    `;
    const input = card.querySelector(".mind-card__input");
    if (input) input.focus();
  }

  function closeEditor(node, card, discard) {
    card.classList.remove("is-editing");
    const body = card.querySelector(".mind-card__body");
    body.innerHTML = escapeHtml((node.note && node.note.content) || "");
    if (discard) {
      setStatus("Edición cancelada", "");
    }
  }

  world.addEventListener("submit", async (e) => {
    const form = e.target.closest(".mind-card__editor");
    if (!form) return;
    e.preventDefault();
    const node = nodeById(form.dataset.nodeId);
    if (!node) return;
    const card = cardElement(node.id);
    const titleEl = card.querySelector(".mind-card__input");
    const contentEl = card.querySelectorAll(".mind-card__input")[1];
    const statusEl = card.querySelector(".mind-card__status");
    const content = contentEl.value.trim();
    if (!content) {
      statusEl.textContent = "El contenido no puede estar vacío.";
      contentEl.focus();
      return;
    }
    try {
      await apiJson(`${apiBase}/notes/${node.note_id}`, {
        method: "PATCH",
        body: { title: titleEl.value.trim() || content.substring(0, 80), content },
      });
      node.note = {
        ...node.note,
        title: titleEl.value.trim() || content.substring(0, 80),
        content,
      };
      card.querySelector(".mind-card__title").textContent = node.note.title;
      closeEditor(node, card, false);
      setStatus("Card actualizada", "is-saved");
      showToast("Card actualizada", "success");
    } catch (err) {
      statusEl.textContent = `No se pudo guardar: ${err.message}`;
      showToast(err.message || "Error al guardar la Card", "error");
    }
  });

  world.addEventListener("click", async (e) => {
    const button = e.target.closest("button[data-action]");
    if (!button) return;
    const card = button.closest(".mind-card");
    const node = card ? nodeById(card.dataset.nodeId) : null;
    if (!node) return;

    if (button.dataset.action === "edit") {
      openEditor(node);
      return;
    }
    if (button.dataset.action === "cancel-edit") {
      closeEditor(node, card, true);
      return;
    }
    if (button.dataset.action === "remove") {
      const confirmed = await showConfirm({
        title: "Quitar del Canvas",
        text: "La Card sale del Canvas. La nota se conserva en tus Notes.",
        confirmLabel: "Quitar",
      });
      if (!confirmed) return;
      try {
        await apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes/${node.id}`, {
          method: "DELETE",
        });
        nodes = nodes.filter((n) => n.id !== node.id);
        renderNodes();
        setStatus("Card quitada del Canvas", "is-saved");
        showToast("Card quitada del Canvas", "success");
      } catch (err) {
        showToast(err.message || "Error al quitar la Card", "error");
      }
      return;
    }
    if (button.dataset.action === "delete-note") {
      const confirmed = await showConfirm({
        title: "Eliminar nota",
        text: "Se elimina la nota y su Card en todos los Canvases. No se puede deshacer.",
        confirmLabel: "Eliminar nota",
        danger: true,
      });
      if (!confirmed) return;
      try {
        await apiJson(`${apiBase}/notes/${node.note_id}`, { method: "DELETE" });
        nodes = nodes.filter((n) => n.id !== node.id);
        renderNodes();
        setStatus("Nota eliminada", "is-saved");
        showToast("Nota eliminada", "success");
      } catch (err) {
        showToast(err.message || "Error al eliminar la nota", "error");
      }
    }
  });

  // --- Creación de Cards ----------------------------------------------------

  async function createCard() {
    const result = await showFormModal({
      title: "Nueva Card",
      fields: [
        { name: "title", label: "Título (opcional)", maxlength: 200 },
        {
          name: "content",
          label: "Contenido",
          type: "textarea",
          rows: 5,
          required: true,
          maxlength: 100000,
          placeholder: "Escribí la idea o el texto de la Card…",
        },
      ],
      submitLabel: "Crear Card",
      hint: "La Card se guarda en el centro de lo que estás viendo.",
    });
    if (!result.ok) return;
    const content = result.values.content.trim();
    if (!content) {
      showToast("El contenido de la Card no puede estar vacío", "warning");
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const center = screenToWorld(rect.left + rect.width / 2, rect.top + rect.height / 2);
    try {
      const node = await apiJson(`${apiBase}/mind/canvases/${canvasId}/cards`, {
        method: "POST",
        body: {
          title: result.values.title.trim() || null,
          content,
          x: Math.round(center.x - CARD_WIDTH / 2),
          y: Math.round(center.y - CARD_HEIGHT / 2),
        },
      });
      nodes.push(node);
      renderNodes();
      setStatus("Card creada", "is-saved");
      showToast("Card creada", "success");
    } catch (err) {
      showToast(err.message || "Error al crear la Card", "error");
    }
  }

  // --- Carga inicial --------------------------------------------------------

  async function load() {
    try {
      canvas = await apiJson(`${apiBase}/mind/canvases/${canvasId}`);
      nodes = await apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes`);
    } catch (err) {
      bodyEl.innerHTML = errorState(
        "Error al cargar el Canvas",
        err.message || "No se pudo cargar el Canvas.",
        "mind-canvas-retry"
      );
      const retry = container.querySelector("#mind-canvas-retry");
      if (retry) retry.addEventListener("click", load);
      return;
    }

    titleEl.textContent = canvas.title;
    descriptionEl.textContent = canvas.description || "Canvas de Mind";
    nodes.forEach((node) => {
      node.savedX = node.x;
      node.savedY = node.y;
    });

    bodyEl.classList.remove("empty-state");
    bodyEl.innerHTML = `
      <section class="mind-canvas" aria-labelledby="mind-canvas-title">
        <div class="mind-canvas__toolbar">
          <div class="mind-canvas__toolbar-group">
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-out" aria-label="Alejar">−</button>
            <span class="mind-canvas__zoom" id="mind-canvas-zoom" aria-live="polite">100%</span>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-in" aria-label="Acercar">+</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-reset">100%</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-fit">Ajustar</button>
          </div>
          <button class="btn btn--primary btn--sm" type="button" id="mind-new-card">Nueva Card</button>
        </div>
        <div class="mind-canvas__frame"></div>
        <p class="mind-canvas__hint">
          Arrastrá el fondo para mover el lienzo · usá la cabecera de la Card para moverla ·
          rueda o +/− para el zoom · con la Card enfocada, las flechas la mueven
        </p>
        <div class="mind-canvas__empty" id="mind-canvas-empty" ${nodes.length ? "hidden" : ""}>
          <p class="empty-state__title">Este Canvas está vacío</p>
          <p class="empty-state__text">Creá la primera Card para empezar a organizar ideas.</p>
          <button class="btn btn--primary" type="button" id="mind-first-card">Crear la primera Card</button>
        </div>
      </section>
    `;

    // El viewport real vive dentro del marco para poder medir su tamaño.
    const frame = bodyEl.querySelector(".mind-canvas__frame");
    frame.appendChild(viewport);
    zoomLabel = bodyEl.querySelector("#mind-canvas-zoom");
    const emptyEl = bodyEl.querySelector("#mind-canvas-empty");
    emptyEl.hidden = nodes.length > 0;

    renderNodes();
    fitToContent();

    bodyEl.querySelector("#mind-zoom-in").addEventListener("click", () => setScale(scale * 1.2));
    bodyEl.querySelector("#mind-zoom-out").addEventListener("click", () => setScale(scale / 1.2));
    bodyEl.querySelector("#mind-zoom-reset").addEventListener("click", () => {
      scale = 1;
      applyTransform();
    });
    bodyEl.querySelector("#mind-zoom-fit").addEventListener("click", fitToContent);
    bodyEl.querySelector("#mind-new-card").addEventListener("click", createCard);
    bodyEl.querySelector("#mind-first-card").addEventListener("click", createCard);

    const statusHost = document.createElement("div");
    statusHost.className = "mind-canvas__status-host";
    statusHost.appendChild(statusEl);
    bodyEl.querySelector(".mind-canvas").appendChild(statusHost);

    statusEl.addEventListener("click", (e) => {
      if (e.target.closest("[data-action='retry']")) retrySave();
    });
  }

  await load();
}
