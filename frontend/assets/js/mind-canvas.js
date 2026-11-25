// Life OS — workspace de Canvas de Mind (MIND-002/003)
//
// Lienzo libre con pan, zoom, Cards de texto, conexiones y persistencia.
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
import {
  cardHeaderMode,
  pickEdgeAnchors,
  DEFAULT_CARD_WIDTH,
  DEFAULT_CARD_HEIGHT,
} from "./mind-geometry.js";

const MIN_SCALE = 0.25;
const MAX_SCALE = 2.5;
const KEYBOARD_STEP = 8;
const KEYBOARD_STEP_BIG = 40;
const CARD_WIDTH = DEFAULT_CARD_WIDTH;
const CARD_HEIGHT = DEFAULT_CARD_HEIGHT;
const MIN_CARD_WIDTH = 200;
const MIN_CARD_HEIGHT = 120;
const MAX_CARD_SIZE = 10000;

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
  let edges = [];
  let scale = 1;
  let tx = 40;
  let ty = 40;
  let panState = null;
  let dragState = null;
  let resizeState = null;
  let connectionDragState = null;
  let pinchState = null;
  let pendingSave = null;
  let saveTimer = null;
  let activeMenu = null; // { nodeId, menuEl, trigger, close }
  let connectingFrom = null;

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
      const actions =
        pendingSave && !pendingSave.saving
          ? ' <button class="btn btn--secondary btn--sm" type="button" data-action="retry">Reintentar</button><button class="btn btn--secondary btn--sm" type="button" data-action="cancel-pending">Cancelar cambios</button>'
          : "";
      statusEl.innerHTML = `${escapeHtml(text)}${actions}`;
    } else {
      statusEl.textContent = text;
    }
  }

  function applyTransform() {
    world.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
    if (zoomLabel) zoomLabel.textContent = `${Math.round(scale * 100)}%`;
    renderEdges();
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

  // --- Guardado de estado espacial ------------------------------------------

  async function persistSpatialAction(action, draft, key = crypto.randomUUID?.() || `mind-${Date.now()}-${Math.random().toString(36).slice(2)}`) {
    pendingSave = { action, draft, key, saving: true };
    setStatus("Guardando cambios…", "is-saving");
    try {
      const result = await apiJson(
        `${apiBase}/mind/canvases/${canvasId}/spatial-actions`,
        {
          method: "POST",
          body: action,
          headers: { "Idempotency-Key": key },
        }
      );
      draft.forEach(({ node, values }) => {
        Object.assign(node, values);
        node.savedX = node.x;
        node.savedY = node.y;
        node.savedWidth = node.width;
        node.savedHeight = node.height;
        node.savedZIndex = node.z_index;
      });
      pendingSave = null;
      if (action.action_type === "reorder") await refreshSpatialState();
      else renderNodes();
      updateHistoryControls();
      setStatus("Cambios guardados", "is-saved");
    } catch (err) {
      if (pendingSave) pendingSave.saving = false;
      setStatus(`Cambios pendientes: ${err.message}`, "is-error");
      showToast(err.message || "No se pudieron guardar los cambios", "error");
    }
  }

  function persistMove(drafts) {
    return persistSpatialAction(
      {
        action_type: "move",
        nodes: drafts.map(({ node, values }) => ({
          id: node.id,
          x: values.x,
          y: values.y,
        })),
      },
      drafts
    );
  }

  function retrySave() {
    if (!pendingSave) return;
    if (pendingSave.retry) {
      pendingSave.retry();
      return;
    }
    const { action, draft, key } = pendingSave;
    persistSpatialAction(action, draft, key);
  }

  async function cancelPendingSave() {
    if (!pendingSave) return;
    if (pendingSave.saving) return;
    try {
      await refreshSpatialState();
      pendingSave = null;
      connectingFrom = null;
      setStatus("Canvas sincronizado; cambios pendientes descartados", "");
    } catch (err) {
      setStatus(`No se pudo confirmar el estado actual: ${err.message}`, "is-error");
    }
  }

  async function runIdempotentRequest(
    url,
    { method, body = null },
    onSuccess,
    errorLabel,
    key = crypto.randomUUID?.() || `mind-${Date.now()}-${Math.random().toString(36).slice(2)}`
  ) {
    const retry = () =>
      runIdempotentRequest(url, { method, body }, onSuccess, errorLabel, key);
    pendingSave = { retry, saving: true };
    setStatus("Guardando cambios…", "is-saving");
    let result;
    try {
      result = await apiJson(url, {
        method,
        body,
        headers: { "Idempotency-Key": key },
      });
    } catch (err) {
      if (pendingSave) pendingSave.saving = false;
      setStatus(`No se pudo guardar ${errorLabel}: ${err.message}`, "is-error");
      return false;
    }
    pendingSave = null;
    await onSuccess(result);
    return true;
  }

  function scheduleSave(node, x, y) {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveTimer = null;
      persistMove([{ node, values: { x, y } }]);
    }, 400);
  }

  function updateHistoryControls() {
    const undo = bodyEl.querySelector("#mind-undo");
    const redo = bodyEl.querySelector("#mind-redo");
    const readOnly = canvas?.status === "archived";
    if (undo) undo.disabled = !history.can_undo || readOnly;
    if (redo) redo.disabled = !history.can_redo || readOnly;
  }

  // --- Menú de acciones de tarjeta ------------------------------------------

  function closeActiveMenu(restoreFocus = false) {
    if (!activeMenu) return;
    const { menuEl, trigger, close } = activeMenu;
    activeMenu = null;
    close();
    if (restoreFocus && trigger?.isConnected) trigger.focus();
    menuEl.remove();
  }

  function openCardMenu(node, trigger) {
    closeActiveMenu();
    const readOnly = canvas?.status === "archived";
    const disabled = readOnly ? "disabled" : "";

    const menu = document.createElement("div");
    menu.className = "mind-card__menu";
    menu.setAttribute("role", "menu");
    menu.setAttribute("aria-label", "Acciones de la Card");
    menu.innerHTML = `
      <button class="mind-card__menu-item" type="button" role="menuitem" data-action="edit">Editar</button>
      <button class="mind-card__menu-item" type="button" role="menuitem" data-action="connect" aria-label="Conectar ${escapeHtml(node.note?.title || "Card")} con otra Card" ${disabled}>Conectar con…</button>
      <button class="mind-card__menu-item" type="button" role="menuitem" data-action="front" ${disabled}>Traer al frente</button>
      <button class="mind-card__menu-item" type="button" role="menuitem" data-action="back" ${disabled}>Enviar atrás</button>
      <hr class="mind-card__menu-sep">
      <button class="mind-card__menu-item mind-card__menu-item--danger" type="button" role="menuitem" data-action="remove" ${disabled}>Quitar del Canvas</button>
    `;

    viewport.appendChild(menu);
    const triggerRect = trigger.getBoundingClientRect();
    const viewportRect = viewport.getBoundingClientRect();
    let left = triggerRect.left - viewportRect.left;
    let top = triggerRect.bottom - viewportRect.top + 4;
    const menuRect = menu.getBoundingClientRect();
    if (left + menuRect.width > viewportRect.width - 4) {
      left = viewportRect.width - menuRect.width - 4;
    }
    if (top + menuRect.height > viewportRect.height - 4) {
      top = triggerRect.top - viewportRect.top - menuRect.height - 4;
    }
    menu.style.left = `${Math.max(4, Math.round(left))}px`;
    menu.style.top = `${Math.max(4, Math.round(top))}px`;

    function onDocPointerDown(event) {
      if (
        menu.contains(event.target) ||
        event.target.closest?.("[data-action='menu']")
      ) {
        return;
      }
      closeActiveMenu();
    }

    menu.addEventListener("click", async (event) => {
      const item = event.target.closest("[data-action]");
      if (!item) return;
      const action = item.dataset.action;
      closeActiveMenu();
      if (action === "edit") {
        openEditor(node);
      } else if (action === "connect") {
        startConnect(node);
      } else if (action === "front" || action === "back") {
        await setOrder(node, action);
      } else if (action === "remove") {
        await removeNodeFromCanvas(node);
      }
    });

    function close() {
      document.removeEventListener("pointerdown", onDocPointerDown, true);
    }

    document.addEventListener("pointerdown", onDocPointerDown, true);
    trigger.setAttribute("aria-expanded", "true");
    activeMenu = {
      nodeId: node.id,
      menuEl: menu,
      trigger,
      close: () => {
        trigger.setAttribute("aria-expanded", "false");
        close();
      },
    };
    menu.querySelector(".mind-card__menu-item")?.focus();
  }

  function startConnect(node) {
    connectingFrom = node.id;
    renderNodes();
    setStatus(
      `Elegí una Card para conectar con “${node.note?.title || "Card"}”. Escape cancela.`,
      ""
    );
    cardElement(node.id)?.focus();
  }

  // --- Render de Cards ------------------------------------------------------

  function cardHtml(node) {
    const note = node.note || {};
    const readOnly = canvas?.status === "archived";
    const spatialDisabled = readOnly ? "disabled" : "";
    const width = node.width || CARD_WIDTH;
    const height = node.height || CARD_HEIGHT;
    const mode = cardHeaderMode(width);
    const style = `left:${node.x}px; top:${node.y}px; z-index:${node.z_index}; width:${width}px; height:${height}px;`;
    const connections = edges.filter(
      (edge) =>
        edge.source_node_id === node.id || edge.target_node_id === node.id
    );
    const connectLabel = `Conectar ${escapeHtml(note.title || "Card")} con otra Card`;
    const actionsHtml =
      mode === "full"
        ? `<div class="mind-card__actions">
            <button class="btn btn--secondary btn--sm" type="button" data-action="edit">Editar</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="connect" aria-label="${connectLabel}" ${spatialDisabled}>Conectar con…</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="front" ${spatialDisabled}>Traer al frente</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="back" ${spatialDisabled}>Enviar atrás</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="remove" ${spatialDisabled}>Quitar</button>
          </div>`
        : mode === "mini"
          ? `<div class="mind-card__actions">
            <button class="btn btn--secondary btn--sm" type="button" data-action="edit">Editar</button>
            <button class="btn btn--secondary btn--sm" type="button" data-action="connect" aria-label="${connectLabel}" ${spatialDisabled}>Conectar</button>
          </div>`
          : "";
    return `
      <article class="mind-card${selectedNodeIds.has(node.id) ? " is-selected" : ""}${connectingFrom && connectingFrom !== node.id ? " is-connection-target" : ""}${mode === "menu" ? " mind-card--menu" : ""}${mode === "mini" ? " mind-card--has-menu" : ""}"
        tabindex="0" data-node-id="${node.id}" style="${style}"
        aria-label="Card: ${escapeHtml(note.title || "Sin título")}${selectedNodeIds.has(node.id) ? ", seleccionada" : ""}">
        <header class="mind-card__head" title="Arrastrá para mover la Card">
          <h3 class="mind-card__title">${escapeHtml(note.title || "Sin título")}</h3>
          ${actionsHtml}
          <button class="mind-card__menu-trigger" type="button" data-action="menu"
            aria-haspopup="menu" aria-expanded="false" ${spatialDisabled}
            aria-label="Más acciones de la Card">⋯</button>
        </header>
        <div class="mind-card__body">${escapeHtml(note.content || "")}</div>
        <div class="mind-card__connections">
          <span class="mind-card__label">Conexiones (${connections.length})</span>
          ${
            connections.length
              ? `<ul>${connections
                  .map((edge) => {
                    const targetId =
                      edge.source_node_id === node.id
                        ? edge.target_node_id
                        : edge.source_node_id;
                    const target = nodeById(targetId);
                    return `<li><button class="mind-card__connection-link" type="button" data-action="focus-node" data-target-id="${targetId}">${escapeHtml(target?.note?.title || "Card")}</button><button class="mind-card__connection-remove" type="button" data-action="remove-edge" data-edge-id="${edge.id}" aria-label="Quitar conexión con ${escapeHtml(target?.note?.title || "Card")}" ${spatialDisabled}>Quitar</button></li>`;
                  })
                  .join("")}</ul>`
              : '<p class="mind-card__no-connections">Sin conexiones.</p>'
          }
        </div>
        <button class="mind-card__resize" type="button" data-action="resize-handle"
          ${spatialDisabled}
          aria-label="Redimensionar ${escapeHtml(note.title || "Card")}"
          title="Arrastrá o usá Alt+Flechas para cambiar el tamaño">⤡</button>
      </article>
    `;
  }

  function renderNodes() {
    const focusedCard = document.activeElement?.closest?.(".mind-card");
    const focusedNodeId = focusedCard?.dataset.nodeId;
    world.innerHTML = `${edgeSvgHtml()}${nodes
      .slice()
      .sort((a, b) => a.z_index - b.z_index)
      .map(cardHtml)
      .join("")}`;
    const empty = bodyEl.querySelector("#mind-canvas-empty");
    if (empty) {
      empty.hidden = nodes.length > 0;
    }
    if (focusedNodeId) cardElement(focusedNodeId)?.focus();
    applyTransform();
  }

  function edgeSvgHtml() {
    const lines = edges
      .map((edge) => {
        const source = nodeById(edge.source_node_id);
        const target = nodeById(edge.target_node_id);
        if (!source || !target) return "";
        const anchors = pickEdgeAnchors(source, target);
        return `<line class="mind-canvas__edge${selectedEdgeId === edge.id ? " is-selected" : ""}" data-edge-id="${edge.id}" x1="${anchors.sourcePoint.x}" y1="${anchors.sourcePoint.y}" x2="${anchors.targetPoint.x}" y2="${anchors.targetPoint.y}" />`;
      })
      .join("");
    return `<svg class="mind-canvas__edges" aria-hidden="true" focusable="false">${lines}</svg>`;
  }

  function renderEdges() {
    const svg = world.querySelector(".mind-canvas__edges");
    if (!svg) return;
    svg.innerHTML = edgeSvgHtml().replace(/^<svg[^>]*>|<\/svg>$/g, "");
    const removeButton = bodyEl.querySelector("#mind-remove-edge");
    if (removeButton) {
      removeButton.disabled =
        !selectedEdgeId ||
        !edges.some((edge) => edge.id === selectedEdgeId) ||
        canvas?.status === "archived";
    }
  }

  function nodeById(nodeId) {
    return nodes.find((n) => n.id === nodeId);
  }

  function cardElement(nodeId) {
    return world.querySelector(`.mind-card[data-node-id="${nodeId}"]`);
  }

  let selectedNodeIds = new Set();
  let selectedEdgeId = null;
  let selectionMode = false;
  let selectionRectState = null;

  function updateSelectionUI() {
    bodyEl.querySelector("#mind-selection-mode")?.classList.toggle(
      "is-active",
      selectionMode
    );
    const count = bodyEl.querySelector("#mind-selection-count");
    if (count) {
      count.textContent = selectedNodeIds.size
        ? `${selectedNodeIds.size} seleccionada${selectedNodeIds.size === 1 ? "" : "s"}`
        : "";
    }
    world.querySelectorAll(".mind-card").forEach((card) => {
      const selected = selectedNodeIds.has(card.dataset.nodeId);
      card.classList.toggle("is-selected", selected);
      card.setAttribute(
        "aria-label",
        `Card: ${card.querySelector(".mind-card__title")?.textContent || "Sin título"}${selected ? ", seleccionada" : ""}`
      );
    });
  }

  function toggleSelection(nodeId) {
    if (selectedNodeIds.has(nodeId)) selectedNodeIds.delete(nodeId);
    else selectedNodeIds.add(nodeId);
    updateSelectionUI();
    setStatus(
      selectedNodeIds.size
        ? `${selectedNodeIds.size} Card${selectedNodeIds.size === 1 ? "" : "s"} seleccionada${selectedNodeIds.size === 1 ? "" : "s"}`
        : "Selección vacía",
      ""
    );
  }

  async function setOrder(node, direction) {
    const ordered = nodes
      .slice()
      .sort((a, b) => a.z_index - b.z_index || a.id.localeCompare(b.id));
    const current = ordered.findIndex((item) => item.id === node.id);
    const target = direction === "front" ? ordered.length - 1 : 0;
    if (current === target) return;
    await persistSpatialAction(
      { action_type: "reorder", nodes: [{ id: node.id, z_index: target }] },
      [
        {
          node,
          values: { z_index: target },
        },
      ]
    );
  }

  async function createEdge(sourceId, targetId) {
    if (!sourceId || !targetId || sourceId === targetId) {
      connectingFrom = null;
      renderNodes();
      setStatus("Elegí otra Card para crear la conexión", "");
      return;
    }
    await runIdempotentRequest(
      `${apiBase}/mind/canvases/${canvasId}/edges`,
      {
        method: "POST",
        body: { source_node_id: sourceId, target_node_id: targetId },
      },
      async (edge) => {
        if (!edges.some((item) => item.id === edge.id)) edges.push(edge);
        connectingFrom = null;
        renderNodes();
        setStatus("Conexión creada", "is-saved");
        try {
          history = await apiJson(`${apiBase}/mind/canvases/${canvasId}/history`);
          updateHistoryControls();
        } catch (err) {
          setStatus(`Conexión creada; no se pudo actualizar el historial: ${err.message}`, "is-error");
        }
      },
      "la conexión"
    );
  }

  async function removeEdge(edgeId) {
    await runIdempotentRequest(
      `${apiBase}/mind/canvases/${canvasId}/edges/${edgeId}`,
      { method: "DELETE" },
      async () => {
        edges = edges.filter((edge) => edge.id !== edgeId);
        selectedEdgeId = null;
        renderNodes();
        setStatus("Conexión quitada", "is-saved");
        try {
          history = await apiJson(`${apiBase}/mind/canvases/${canvasId}/history`);
          updateHistoryControls();
        } catch (err) {
          setStatus(`Conexión quitada; no se pudo actualizar el historial: ${err.message}`, "is-error");
        }
      },
      "la conexión"
    );
  }

  async function showNotePicker() {
    let notes;
    try {
      notes = await apiJson(`${apiBase}/notes`);
    } catch (err) {
      setStatus(`No se pudieron cargar las Notes: ${err.message}`, "is-error");
      return null;
    }
    const available = notes;
    if (!available.length) {
      setStatus("No hay Notes disponibles para añadir a este Canvas", "");
      return null;
    }
    return new Promise((resolve) => {
      const previousFocus = document.activeElement;
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay mind-note-picker";
      overlay.innerHTML = `
        <section class="modal" role="dialog" aria-modal="true" aria-labelledby="mind-note-picker-title">
          <h2 class="modal__title" id="mind-note-picker-title">Añadir una Note</h2>
          <label for="mind-note-picker-search">Buscar por título o contenido</label>
          <input id="mind-note-picker-search" type="search" autocomplete="off">
          <ul class="mind-note-picker__list"></ul>
          <div class="modal__actions">
            <button class="btn btn--secondary" type="button" data-action="cancel">Cancelar</button>
          </div>
        </section>`;
      const search = overlay.querySelector("#mind-note-picker-search");
      const list = overlay.querySelector(".mind-note-picker__list");
      function renderOptions() {
        const query = search.value.trim().toLocaleLowerCase();
        const matches = available.filter((note) =>
          `${note.title || ""}\n${note.content || ""}`
            .toLocaleLowerCase()
            .includes(query)
        );
        list.innerHTML = matches.length
          ? matches
              .map(
                (note) => `
                  <li><button type="button" class="mind-note-picker__option" data-note-id="${note.id}">
                    <strong>${escapeHtml(note.title || "Sin título")}</strong>
                    <span>${escapeHtml((note.content || "").slice(0, 140))}</span>
                    ${nodes.some((node) => node.note_id === note.id) ? "<span>Ya está en este Canvas</span>" : ""}
                  </button></li>`
              )
              .join("")
          : '<li class="mind-note-picker__empty">No hay Notes que coincidan.</li>';
      }
      function close(note) {
        overlay.remove();
        document.removeEventListener("keydown", onKey, true);
        previousFocus?.focus?.();
        resolve(note || null);
      }
      function onKey(event) {
        if (event.key === "Escape") {
          event.preventDefault();
          close(null);
          return;
        }
        if (event.key === "Tab") {
          const focusable = overlay.querySelectorAll(
            "button, input, [tabindex]:not([tabindex='-1'])"
          );
          if (!focusable.length) return;
          if (event.shiftKey && document.activeElement === focusable[0]) {
            event.preventDefault();
            focusable[focusable.length - 1].focus();
          } else if (
            !event.shiftKey &&
            document.activeElement === focusable[focusable.length - 1]
          ) {
            event.preventDefault();
            focusable[0].focus();
          }
        }
      }
      search.addEventListener("input", renderOptions);
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay || event.target.closest("[data-action='cancel']")) {
          close(null);
          return;
        }
        const option = event.target.closest("[data-note-id]");
        if (option) close(available.find((note) => note.id === option.dataset.noteId));
      });
      renderOptions();
      document.addEventListener("keydown", onKey, true);
      document.body.appendChild(overlay);
      search.focus();
    });
  }

  async function addExistingNote() {
    const note = await showNotePicker();
    if (!note) return;
    const existing = nodes.find((node) => node.note_id === note.id);
    if (existing) {
      existingNodeFocus(existing.id);
      setStatus("La Note ya está en este Canvas", "");
      return;
    }
    const rect = viewport.getBoundingClientRect();
    const center = screenToWorld(
      rect.left + rect.width / 2,
      rect.top + rect.height / 2
    );
    await runIdempotentRequest(
      `${apiBase}/mind/canvases/${canvasId}/nodes`,
      {
        method: "POST",
        body: {
          note_id: note.id,
          x: Math.round(center.x - CARD_WIDTH / 2),
          y: Math.round(center.y - CARD_HEIGHT / 2),
        },
      },
      async (node) => {
        nodes.push(node);
        selectedNodeIds = new Set([node.id]);
        renderNodes();
        updateSelectionUI();
        setStatus("Note añadida al Canvas", "is-saved");
        try {
          history = await apiJson(`${apiBase}/mind/canvases/${canvasId}/history`);
          updateHistoryControls();
        } catch (err) {
          setStatus(`Note añadida; no se pudo actualizar el historial: ${err.message}`, "is-error");
        }
      },
      "la Note"
    );
  }

  function existingNodeFocus(nodeId) {
    const node = nodeById(nodeId);
    if (!node) return;
    selectedNodeIds = new Set([nodeId]);
    renderNodes();
    const el = cardElement(nodeId);
    el?.focus();
    tx = viewport.clientWidth / 2 - (node.x + (node.width || CARD_WIDTH) / 2) * scale;
    ty = viewport.clientHeight / 2 - (node.y + (node.height || CARD_HEIGHT) / 2) * scale;
    applyTransform();
  }

  async function refreshSpatialState() {
    const [nextNodes, nextEdges, nextHistory] = await Promise.all([
      apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes`),
      apiJson(`${apiBase}/mind/canvases/${canvasId}/edges`),
      apiJson(`${apiBase}/mind/canvases/${canvasId}/history`),
    ]);
    nodes = nextNodes;
    edges = nextEdges;
    history = nextHistory;
    if (!edges.some((edge) => edge.id === selectedEdgeId)) selectedEdgeId = null;
    selectedNodeIds = new Set(
      [...selectedNodeIds].filter((id) => nodes.some((node) => node.id === id))
    );
    renderNodes();
    updateHistoryControls();
    updateSelectionUI();
  }

  let history = { can_undo: false, can_redo: false };

  async function transitionHistory(undo, key = crypto.randomUUID?.() || `mind-${Date.now()}-${Math.random().toString(36).slice(2)}`) {
    const actionId = undo ? history.undo_action_id : history.redo_action_id;
    if (!actionId) return;
    const action = undo ? "undo" : "redo";
    const retry = () => transitionHistory(undo, key);
    pendingSave = { retry, saving: true };
    setStatus(undo ? "Deshaciendo…" : "Rehaciendo…", "is-saving");
    try {
      history = await apiJson(
        `${apiBase}/mind/canvases/${canvasId}/history/${action}`,
        {
          method: "POST",
          body: { expected_action_id: actionId },
          headers: { "Idempotency-Key": key },
        }
      );
      pendingSave = null;
      await refreshSpatialState();
      setStatus(undo ? "Acción deshecha" : "Acción rehecha", "is-saved");
    } catch (err) {
      if (pendingSave) pendingSave.saving = false;
      setStatus(`No se pudo ${undo ? "deshacer" : "rehacer"}: ${err.message}`, "is-error");
    }
  }

  function undoHistory() {
    transitionHistory(true);
  }

  function redoHistory() {
    transitionHistory(false);
  }

  async function removeNodeFromCanvas(node) {
    const confirmed = await showConfirm({
      title: "Quitar del Canvas",
      text: "La Card sale del Canvas. La nota se conserva en tus Notes.",
      confirmLabel: "Quitar",
    });
    if (!confirmed) return;
    await runIdempotentRequest(
      `${apiBase}/mind/canvases/${canvasId}/nodes/${node.id}`,
      { method: "DELETE" },
      async () => {
        nodes = nodes.filter((n) => n.id !== node.id);
        selectedNodeIds.delete(node.id);
        edges = edges.filter(
          (edge) =>
            edge.source_node_id !== node.id && edge.target_node_id !== node.id
        );
        if (!edges.some((edge) => edge.id === selectedEdgeId)) selectedEdgeId = null;
        renderNodes();
        updateSelectionUI();
        setStatus("Card quitada del Canvas", "is-saved");
        showToast("Card quitada del Canvas", "success");
        try {
          history = await apiJson(`${apiBase}/mind/canvases/${canvasId}/history`);
          updateHistoryControls();
        } catch (err) {
          setStatus(`Card quitada; no se pudo actualizar el historial: ${err.message}`, "is-error");
        }
      },
      "la Card"
    );
  }

  async function deleteNote(node) {
    let impact = { affected_canvases: 0, cleared_history_actions: 0 };
    try {
      impact = await apiJson(
        `${apiBase}/mind/notes/${node.note_id}/delete-impact`
      );
    } catch (err) {
      setStatus(`No se pudo consultar el impacto: ${err.message}`, "is-error");
      return;
    }
    const confirmed = await showConfirm({
      title: "Eliminar nota",
      text: `Se elimina la nota y sus Cards en todos los Canvases. También se limpiarán ${impact.cleared_history_actions} acciones de historial en ${impact.affected_canvases} Canvas. No se puede deshacer.`,
      confirmLabel: "Eliminar nota",
      danger: true,
    });
    if (!confirmed) return;
    try {
      await apiJson(`${apiBase}/notes/${node.note_id}`, { method: "DELETE" });
      nodes = nodes.filter((n) => n.id !== node.id);
      edges = edges.filter(
        (edge) =>
          edge.source_node_id !== node.id && edge.target_node_id !== node.id
      );
      selectedNodeIds.delete(node.id);
      renderNodes();
      await refreshSpatialState();
      setStatus("Nota eliminada", "is-saved");
      showToast("Nota eliminada", "success");
    } catch (err) {
      setStatus(`No se pudo eliminar la nota: ${err.message}`, "is-error");
    }
  }

  // --- Interacción: pan, zoom, drag, resize, conexión -----------------------

  viewport.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    if (pinchState) return;

    const menuTrigger = e.target.closest("[data-action='menu']");
    if (menuTrigger) {
      const card = menuTrigger.closest(".mind-card");
      if (card) {
        const node = nodeById(card.dataset.nodeId);
        if (node) openCardMenu(node, menuTrigger);
      }
      e.preventDefault();
      return;
    }

    const connectButton = e.target.closest("[data-action='connect']");
    if (connectButton) {
      const card = connectButton.closest(".mind-card");
      if (!card) return;
      connectionDragState = {
        sourceId: card.dataset.nodeId,
        pointerId: e.pointerId,
      };
      connectingFrom = card.dataset.nodeId;
      viewport.setPointerCapture(e.pointerId);
      e.preventDefault();
      return;
    }

    const card = e.target.closest(".mind-card");
    const head = e.target.closest(".mind-card__head");
    if (e.target.closest(".mind-canvas__edge")) return;
    const resizeHandle = e.target.closest("[data-action='resize-handle']");
    if (resizeHandle && card) {
      const node = nodeById(card.dataset.nodeId);
      if (!node) return;
      resizeState = {
        node,
        el: card,
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        originWidth: node.width || CARD_WIDTH,
        originHeight: node.height || CARD_HEIGHT,
        originalWidth: node.width,
        originalHeight: node.height,
        width: node.width || CARD_WIDTH,
        height: node.height || CARD_HEIGHT,
        moved: false,
      };
      viewport.setPointerCapture(e.pointerId);
      e.preventDefault();
      return;
    }
    if (card && (e.shiftKey || selectionMode)) return;
    if (card && head && !e.target.closest("button")) {
      const node = nodeById(card.dataset.nodeId);
      if (!node) return;
      if (!selectedNodeIds.has(node.id)) selectedNodeIds = new Set([node.id]);
      updateSelectionUI();
      const selected = nodes.filter((item) => selectedNodeIds.has(item.id));
      dragState = {
        entries: selected.map((item) => ({
          node: item,
          el: cardElement(item.id),
          originX: item.x,
          originY: item.y,
        })),
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        moved: false,
      };
      dragState.entries.forEach(({ el }) => el?.classList.add("is-dragging"));
      viewport.setPointerCapture(e.pointerId);
      e.preventDefault();
      return;
    }
    if (!card && (selectionMode || e.shiftKey)) {
      const start = screenToWorld(e.clientX, e.clientY);
      selectionRectState = {
        pointerId: e.pointerId,
        start,
        rect: document.createElement("div"),
      };
      selectionRectState.rect.className = "mind-canvas__selection-rect";
      world.appendChild(selectionRectState.rect);
      viewport.setPointerCapture(e.pointerId);
      e.preventDefault();
      return;
    }
    if (card) return;
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
    if (resizeState && e.pointerId === resizeState.pointerId) {
      const dx = (e.clientX - resizeState.startX) / scale;
      const dy = (e.clientY - resizeState.startY) / scale;
      resizeState.width = Math.max(
        MIN_CARD_WIDTH,
        Math.min(MAX_CARD_SIZE, Math.round(resizeState.originWidth + dx))
      );
      resizeState.height = Math.max(
        MIN_CARD_HEIGHT,
        Math.min(MAX_CARD_SIZE, Math.round(resizeState.originHeight + dy))
      );
      resizeState.moved = true;
      resizeState.node.width = resizeState.width;
      resizeState.node.height = resizeState.height;
      resizeState.el.style.width = `${resizeState.width}px`;
      resizeState.el.style.height = `${resizeState.height}px`;
      renderEdges();
      return;
    }
    if (dragState && e.pointerId === dragState.pointerId) {
      const dx = (e.clientX - dragState.startX) / scale;
      const dy = (e.clientY - dragState.startY) / scale;
      dragState.moved = true;
      dragState.entries.forEach(({ node, el, originX, originY }) => {
        node.x = Math.round(originX + dx);
        node.y = Math.round(originY + dy);
        if (el) {
          el.style.left = `${node.x}px`;
          el.style.top = `${node.y}px`;
        }
      });
      renderEdges();
      return;
    }
    if (selectionRectState && e.pointerId === selectionRectState.pointerId) {
      const current = screenToWorld(e.clientX, e.clientY);
      const left = Math.min(selectionRectState.start.x, current.x);
      const top = Math.min(selectionRectState.start.y, current.y);
      selectionRectState.rect.style.left = `${left}px`;
      selectionRectState.rect.style.top = `${top}px`;
      selectionRectState.rect.style.width = `${Math.abs(current.x - selectionRectState.start.x)}px`;
      selectionRectState.rect.style.height = `${Math.abs(current.y - selectionRectState.start.y)}px`;
      selectionRectState.current = current;
      return;
    }
    if (panState && e.pointerId === panState.pointerId) {
      tx = panState.originTx + (e.clientX - panState.startX);
      ty = panState.originTy + (e.clientY - panState.startY);
      applyTransform();
    }
  });

  function endPointerInteraction(e, cancelled) {
    if (connectionDragState && e.pointerId === connectionDragState.pointerId) {
      const { sourceId } = connectionDragState;
      connectionDragState = null;
      const target = !cancelled
        ? document
            .elementFromPoint(e.clientX, e.clientY)
            ?.closest(".mind-card")
        : null;
      if (target && target.dataset.nodeId !== sourceId) {
        suppressConnectClick = true;
        createEdge(sourceId, target.dataset.nodeId);
        window.setTimeout(() => {
          suppressConnectClick = false;
        }, 0);
      } else if (cancelled) {
        connectingFrom = null;
        renderNodes();
        setStatus("Conexión cancelada", "");
      } else {
        connectingFrom = sourceId;
        renderNodes();
      }
    }
    if (dragState && e.pointerId === dragState.pointerId) {
      const { entries, moved } = dragState;
      entries.forEach(({ el }) => el?.classList.remove("is-dragging"));
      if (cancelled) {
        entries.forEach(({ node, el, originX, originY }) => {
          node.x = originX;
          node.y = originY;
          if (el) {
            el.style.left = `${originX}px`;
            el.style.top = `${originY}px`;
          }
        });
      } else if (moved) {
        const drafts = entries.map(({ node }) => ({
          node,
          values: { x: node.x, y: node.y },
        }));
        entries.forEach(({ node, originX, originY }) => {
          node.x = originX;
          node.y = originY;
        });
        persistMove(drafts);
      }
      dragState = null;
    }
    if (resizeState && e.pointerId === resizeState.pointerId) {
      const {
        node,
        el,
        moved,
        originWidth,
        originHeight,
        originalWidth,
        originalHeight,
        width,
        height,
      } = resizeState;
      if (cancelled) {
        node.width = originalWidth;
        node.height = originalHeight;
        el.style.width = `${originWidth}px`;
        el.style.height = `${originHeight}px`;
      } else if (moved) {
        persistSpatialAction(
          {
            action_type: "resize",
            nodes: [{ id: node.id, width, height }],
          },
          [{ node, values: { width, height } }]
        );
      }
      resizeState = null;
    }
    if (selectionRectState && e.pointerId === selectionRectState.pointerId) {
      const state = selectionRectState;
      state.rect.remove();
      if (!cancelled && state.current) {
        const left = Math.min(state.start.x, state.current.x);
        const top = Math.min(state.start.y, state.current.y);
        const right = Math.max(state.start.x, state.current.x);
        const bottom = Math.max(state.start.y, state.current.y);
        selectedNodeIds = new Set(
          nodes
            .filter((node) => {
              const width = node.width || CARD_WIDTH;
              const height = node.height || CARD_HEIGHT;
              return (
                node.x < right &&
                node.x + width > left &&
                node.y < bottom &&
                node.y + height > top
              );
            })
            .map((node) => node.id)
        );
        updateSelectionUI();
        setStatus(`${selectedNodeIds.size} Card(s) seleccionada(s)`, "");
      }
      selectionRectState = null;
    }
    if (panState && e.pointerId === panState.pointerId) {
      panState = null;
      viewport.classList.remove("is-panning");
    }
  }

  viewport.addEventListener("pointerup", (e) => endPointerInteraction(e, false));
  viewport.addEventListener("pointercancel", (e) => endPointerInteraction(e, true));

  let suppressConnectClick = false;

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
      if (dragState || resizeState || selectionRectState || connectionDragState) {
        const pointerId =
          dragState?.pointerId ??
          resizeState?.pointerId ??
          selectionRectState?.pointerId ??
          connectionDragState?.pointerId;
        endPointerInteraction({ pointerId }, true);
      }
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
    const editingField = e.target.matches("input, textarea, select");
    if (e.key === "Escape" && editingField) {
      const card = e.target.closest(".mind-card");
      const node = card ? nodeById(card.dataset.nodeId) : null;
      if (card?.classList.contains("is-editing") && node) {
        closeEditor(node, card, true);
        e.preventDefault();
      }
      return;
    }
    if (!editingField && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "a") {
      selectedNodeIds = new Set(nodes.map((node) => node.id));
      updateSelectionUI();
      setStatus(`${selectedNodeIds.size} Cards seleccionadas`, "");
      e.preventDefault();
      return;
    }
    if (!editingField && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
      e.preventDefault();
      if (e.shiftKey) redoHistory();
      else undoHistory();
      return;
    }
    if (!editingField && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
      e.preventDefault();
      redoHistory();
      return;
    }
    if (e.key === "Escape") {
      if (connectionDragState) {
        connectionDragState = null;
        connectingFrom = null;
        renderNodes();
        setStatus("Conexión cancelada", "");
      } else if (connectingFrom) {
        connectingFrom = null;
        renderNodes();
        setStatus("Conexión cancelada", "");
      } else if (selectionRectState || dragState || resizeState) {
        endPointerInteraction(
          { pointerId: selectionRectState?.pointerId ?? dragState?.pointerId ?? resizeState?.pointerId },
          true
        );
        setStatus("Interacción cancelada", "");
      } else if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
        nodes.forEach((node) => {
          node.x = node.savedX ?? node.x;
          node.y = node.savedY ?? node.y;
          node.width = node.savedWidth;
          node.height = node.savedHeight;
        });
        renderNodes();
        setStatus("Movimiento cancelado", "");
      } else if (selectedNodeIds.size) {
        selectedNodeIds.clear();
        updateSelectionUI();
        setStatus("Selección vacía", "");
      } else if (pendingSave) {
        cancelPendingSave();
      }
      closeActiveMenu();
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
    const editingField = e.target.matches("input, textarea, select");
    if (!editingField && e.target !== card) return;
    if (editingField && e.key !== "Escape") {
      return;
    }
    if (!editingField && connectingFrom && ["Enter", " "].includes(e.key)) {
      e.preventDefault();
      createEdge(connectingFrom, node.id);
      return;
    }
    if (!editingField && e.key === " ") {
      toggleSelection(node.id);
      e.preventDefault();
      return;
    }
    if (!editingField && e.altKey && e.key.startsWith("Arrow")) {
      const step = e.shiftKey ? KEYBOARD_STEP_BIG : KEYBOARD_STEP;
      const width =
        (node.width || CARD_WIDTH) +
        (e.key === "ArrowRight" ? step : e.key === "ArrowLeft" ? -step : 0);
      const height =
        (node.height || CARD_HEIGHT) +
        (e.key === "ArrowDown" ? step : e.key === "ArrowUp" ? -step : 0);
      const nextWidth = Math.max(MIN_CARD_WIDTH, Math.min(MAX_CARD_SIZE, width));
      const nextHeight = Math.max(MIN_CARD_HEIGHT, Math.min(MAX_CARD_SIZE, height));
      node.width = nextWidth;
      node.height = nextHeight;
      card.style.width = `${nextWidth}px`;
      card.style.height = `${nextHeight}px`;
      renderEdges();
      persistSpatialAction(
        {
          action_type: "resize",
          nodes: [{ id: node.id, width: nextWidth, height: nextHeight }],
        },
        [{ node, values: { width: nextWidth, height: nextHeight } }]
      );
      e.preventDefault();
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
    const moving = selectedNodeIds.has(node.id)
      ? nodes.filter((item) => selectedNodeIds.has(item.id))
      : [node];
    const drafts = moving.map((item) => {
      item.x += dx;
      item.y += dy;
      const element = cardElement(item.id);
      if (element) {
        element.style.left = `${item.x}px`;
        element.style.top = `${item.y}px`;
      }
      return { node: item, values: { x: item.x, y: item.y } };
    });
    renderEdges();
    setStatus("Guardando posición…", "is-saving");
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveTimer = null;
      const values = drafts.map(({ node, values }) => ({ node, values: { ...values } }));
      persistMove(values);
    }, 400);
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
    const edgeLine = e.target.closest(".mind-canvas__edge");
    if (edgeLine) {
      selectedEdgeId = edgeLine.dataset.edgeId;
      renderEdges();
      const removeButton = bodyEl.querySelector("#mind-remove-edge");
      removeButton?.focus();
      return;
    }
    const button = e.target.closest("button[data-action]");
    const card = button?.closest(".mind-card") || e.target.closest(".mind-card");
    const node = card ? nodeById(card.dataset.nodeId) : null;
    if (!button) {
      if (!card || !node) return;
      if (connectingFrom) {
        createEdge(connectingFrom, node.id);
      } else if (e.shiftKey || selectionMode) {
        toggleSelection(node.id);
      } else {
        selectedNodeIds = new Set([node.id]);
        updateSelectionUI();
      }
      return;
    }
    if (!node) return;

    if (button.dataset.action === "edit") {
      openEditor(node);
      return;
    }
    if (button.dataset.action === "connect") {
      if (suppressConnectClick) return;
      connectingFrom = node.id;
      selectedNodeIds = new Set([node.id]);
      renderNodes();
      setStatus(`Elegí una Card para conectar con “${node.note?.title || "Card"}”. Escape cancela.`, "");
      cardElement(node.id)?.focus();
      return;
    }
    if (button.dataset.action === "menu") {
      openCardMenu(node, button);
      return;
    }
    if (button.dataset.action === "front" || button.dataset.action === "back") {
      await setOrder(node, button.dataset.action);
      return;
    }
    if (button.dataset.action === "resize-handle") {
      return;
    }
    if (button.dataset.action === "focus-node") {
      const targetNode = nodeById(button.dataset.targetId);
      const target = cardElement(button.dataset.targetId);
      if (target && targetNode) {
        target.focus();
        tx = viewport.clientWidth / 2 - (targetNode.x + (targetNode.width || CARD_WIDTH) / 2) * scale;
        ty = viewport.clientHeight / 2 - (targetNode.y + (targetNode.height || CARD_HEIGHT) / 2) * scale;
        applyTransform();
      }
      return;
    }
    if (button.dataset.action === "remove-edge") {
      await removeEdge(button.dataset.edgeId);
      return;
    }
    if (button.dataset.action === "cancel-edit") {
      closeEditor(node, card, true);
      return;
    }
    if (button.dataset.action === "remove") {
      await removeNodeFromCanvas(node);
      return;
    }
    if (button.dataset.action === "delete-note") {
      await deleteNote(node);
      return;
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
    await runIdempotentRequest(
      `${apiBase}/mind/canvases/${canvasId}/cards`,
      {
        method: "POST",
        body: {
          title: result.values.title.trim() || null,
          content,
          x: Math.round(center.x - CARD_WIDTH / 2),
          y: Math.round(center.y - CARD_HEIGHT / 2),
        },
      },
      async (node) => {
        nodes.push(node);
        selectedNodeIds = new Set([node.id]);
        renderNodes();
        updateSelectionUI();
        setStatus("Card creada", "is-saved");
        showToast("Card creada", "success");
        try {
          history = await apiJson(`${apiBase}/mind/canvases/${canvasId}/history`);
          updateHistoryControls();
        } catch (err) {
          setStatus(`Card creada; no se pudo actualizar el historial: ${err.message}`, "is-error");
        }
      },
      "la Card"
    );
  }

  // --- Carga inicial --------------------------------------------------------

  async function load() {
    try {
      [canvas, nodes, edges, history] = await Promise.all([
        apiJson(`${apiBase}/mind/canvases/${canvasId}`),
        apiJson(`${apiBase}/mind/canvases/${canvasId}/nodes`),
        apiJson(`${apiBase}/mind/canvases/${canvasId}/edges`),
        apiJson(`${apiBase}/mind/canvases/${canvasId}/history`),
      ]);
    } catch (err) {
      bodyEl.innerHTML = errorState(
        "No se pudo cargar el Canvas",
        err.message || "No se pudo cargar el Canvas.",
        "mind-canvas-retry"
      );
      const retry = container.querySelector("#mind-canvas-retry");
      if (retry) retry.addEventListener("click", load);
      return;
    }

    titleEl.textContent = canvas.title;
    descriptionEl.textContent = canvas.description || "";
    nodes.forEach((node) => {
      node.savedX = node.x;
      node.savedY = node.y;
      node.savedWidth = node.width;
      node.savedHeight = node.height;
      node.savedZIndex = node.z_index;
    });

    bodyEl.classList.remove("empty-state");
    bodyEl.innerHTML = `
      <section class="mind-canvas${canvas.status === "archived" ? " is-readonly" : ""}" aria-labelledby="mind-canvas-title">
        ${canvas.status === "archived" ? '<p class="mind-canvas__readonly" role="status">Canvas archivado: solo lectura. <button class="btn btn--secondary btn--sm" type="button" id="mind-canvas-restore">Restaurar Canvas</button></p>' : ""}
        <div class="mind-canvas__toolbar">
          <div class="mind-canvas__toolbar-group">
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-out" aria-label="Alejar">−</button>
            <span class="mind-canvas__zoom" id="mind-canvas-zoom" aria-live="polite">100%</span>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-in" aria-label="Acercar">+</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-reset">100%</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-zoom-fit">Ajustar</button>
          </div>
          <div class="mind-canvas__toolbar-group" aria-label="Acciones del Canvas">
            <button class="btn btn--secondary btn--sm" type="button" id="mind-selection-mode" aria-pressed="false" ${canvas.status === "archived" ? "disabled" : ""}>Seleccionar</button>
            <span id="mind-selection-count" class="mind-canvas__selection-count" aria-live="polite"></span>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-undo" ${history.can_undo && canvas.status !== "archived" ? "" : "disabled"}>Deshacer</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-redo" ${history.can_redo && canvas.status !== "archived" ? "" : "disabled"}>Rehacer</button>
            <button class="btn btn--secondary btn--sm" type="button" id="mind-add-note" ${canvas.status === "archived" ? "disabled" : ""}>Añadir Note</button>
            <button class="btn btn--danger btn--sm" type="button" id="mind-remove-edge" ${canvas.status === "archived" || !selectedEdgeId ? "disabled" : ""}>Quitar conexión seleccionada</button>
            <button class="btn btn--primary btn--sm" type="button" id="mind-new-card" ${canvas.status === "archived" ? "disabled" : ""}>Nueva Card</button>
          </div>
        </div>
        <div class="mind-canvas__frame"></div>
        <p class="mind-canvas__hint">
          Arrastrá el fondo para mover el lienzo · activá Seleccionar para marcar varias Cards ·
          usá la cabecera para moverlas · Alt+Flechas redimensiona · rueda o +/− para el zoom.
        </p>
        <div class="mind-canvas__empty" id="mind-canvas-empty" ${nodes.length ? "hidden" : ""}>
          <p class="empty-state__title">Este Canvas está vacío</p>
          <p class="empty-state__text">Creá una Card o añadí una Note para empezar.</p>
          <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
            <button class="btn btn--primary" type="button" data-action="new-card">Nueva Card</button>
            <button class="btn btn--secondary" type="button" data-action="add-note">Añadir Note</button>
          </div>
        </div>
      </section>
    `;

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
    bodyEl.querySelector("#mind-add-note").addEventListener("click", addExistingNote);
    bodyEl.querySelector("#mind-remove-edge").addEventListener("click", () => {
      if (selectedEdgeId) removeEdge(selectedEdgeId);
    });
    bodyEl.querySelector("#mind-undo").addEventListener("click", undoHistory);
    bodyEl.querySelector("#mind-redo").addEventListener("click", redoHistory);
    bodyEl.querySelector("#mind-canvas-restore")?.addEventListener("click", async () => {
      try {
        await apiJson(`${apiBase}/mind/canvases/${canvasId}/restore`, { method: "POST" });
        await load();
      } catch (err) {
        setStatus(`No se pudo restaurar el Canvas: ${err.message}`, "is-error");
      }
    });
    bodyEl.querySelector("#mind-selection-mode").addEventListener("click", (event) => {
      selectionMode = !selectionMode;
      event.currentTarget.classList.toggle("is-active", selectionMode);
      event.currentTarget.setAttribute("aria-pressed", selectionMode);
      if (!selectionMode) {
        selectedNodeIds.clear();
        updateSelectionUI();
      }
    });

    const statusHost = document.createElement("div");
    statusHost.className = "mind-canvas__status-host";
    statusHost.appendChild(statusEl);
    bodyEl.querySelector(".mind-canvas").appendChild(statusHost);

    emptyEl.addEventListener("click", (e) => {
      if (e.target.matches("[data-action='new-card']")) createCard();
      if (e.target.matches("[data-action='add-note']")) addExistingNote();
    });

    viewport.addEventListener("pointerdown", (e) => {
      if (!e.target.closest(".mind-card__menu") && !e.target.closest("[data-action='menu']")) {
        closeActiveMenu();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeActiveMenu();
    });
  }

  await load();
}