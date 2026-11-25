// Life OS — geometría de las conexiones del Canvas (MIND-003)
//
// Ocho puntos de anclaje por Card (centro superior, esquinas superiores
// izquierda/derecha, centro izquierdo/derecha, esquinas inferiores
// izquierda/derecha y centro inferior) y selección automática del par
// conveniente en ambos extremos según la posición relativa entre tarjetas.
//
// La línea se calcula sobre el rectángulo de la Card: termina exactamente en
// el perímetro y no atraviesa ninguna de las dos Cards (se verifica
// geométricamente con el método de slab sobre ambos rectángulos). Funciones
// puras, sin DOM: se prueban con `node --test`.

export const DEFAULT_CARD_WIDTH = 240;
export const DEFAULT_CARD_HEIGHT = 160;

// Índices de anclaje, en el sentido de las agujas del reloj desde el centro:
// 0 centro superior, 1 esquina superior derecha, 2 centro derecho,
// 3 esquina inferior derecha, 4 centro inferior, 5 esquina inferior izquierda,
// 6 centro izquierdo, 7 esquina superior izquierda.
export const ANCHOR = Object.freeze({
  TOP: 0,
  TOP_RIGHT: 1,
  RIGHT: 2,
  BOTTOM_RIGHT: 3,
  BOTTOM: 4,
  BOTTOM_LEFT: 5,
  LEFT: 6,
  TOP_LEFT: 7,
});

// Posición relativa de cada anclaje dentro del rectángulo de la Card.
const ANCHOR_FACTORS = Object.freeze([
  [0.5, 0], // 0: centro superior
  [1, 0], // 1: esquina superior derecha
  [1, 0.5], // 2: centro derecho
  [1, 1], // 3: esquina inferior derecha
  [0.5, 1], // 4: centro inferior
  [0, 1], // 5: esquina inferior izquierda
  [0, 0.5], // 6: centro izquierdo
  [0, 0], // 7: esquina superior izquierda
]);

// Modos de cabecera de Card según su ancho (controles inline vs. menú).
export const HEADER_FULL_MIN_WIDTH = 600;
export const HEADER_MINI_MIN_WIDTH = 300;

const EPSILON = 1e-9;

function sizeOf(node) {
  const width =
    Number.isFinite(node.width) && node.width > 0
      ? node.width
      : DEFAULT_CARD_WIDTH;
  const height =
    Number.isFinite(node.height) && node.height > 0
      ? node.height
      : DEFAULT_CARD_HEIGHT;
  return { width, height };
}

/** Rectángulo en coordenadas de mundo de una Card. */
export function cardRect(node) {
  const { width, height } = sizeOf(node);
  return {
    left: node.x,
    top: node.y,
    right: node.x + width,
    bottom: node.y + height,
    width,
    height,
  };
}

/** Centro geométrico de una Card. */
export function cardCenter(node) {
  const rect = cardRect(node);
  return {
    x: (rect.left + rect.right) / 2,
    y: (rect.top + rect.bottom) / 2,
  };
}

/**
 * Punto exacto del perímetro para uno de los 8 anclajes.
 * Las esquinas devuelven la esquina real; los centros, el punto medio del borde.
 */
export function anchorPoint(node, index) {
  const rect = cardRect(node);
  const factors = ANCHOR_FACTORS[index] || ANCHOR_FACTORS[0];
  return {
    x: rect.left + rect.width * factors[0],
    y: rect.top + rect.height * factors[1],
  };
}

/** Ángulo (desde el centro de la Card) de uno de los 8 anclajes. */
export function anchorAngle(node, index) {
  const center = cardCenter(node);
  const point = anchorPoint(node, index);
  return Math.atan2(point.y - center.y, point.x - center.x);
}

function angleDiff(a, b) {
  let diff = a - b;
  while (diff <= -Math.PI) diff += 2 * Math.PI;
  while (diff > Math.PI) diff -= 2 * Math.PI;
  return Math.abs(diff);
}

/**
 * ¿El segmento p→q atraviesa el interior de la Card?
 *
 * Se prueba sobre el rectángulo reducido `epsilon` px para que los extremos,
 * que caen exactamente sobre el perímetro, no cuenten como cruce.
 */
export function segmentHitsCard(p, q, node, epsilon = 1) {
  const rect = cardRect(node);
  const minX = rect.left + epsilon;
  const maxX = rect.right - epsilon;
  const minY = rect.top + epsilon;
  const maxY = rect.bottom - epsilon;
  if (minX >= maxX || minY >= maxY) return false;

  const dx = q.x - p.x;
  const dy = q.y - p.y;
  let t0 = 0;
  let t1 = 1;

  const clip = (origin, delta, min, max) => {
    if (Math.abs(delta) < EPSILON) return origin >= min && origin <= max;
    let a = (min - origin) / delta;
    let b = (max - origin) / delta;
    if (a > b) {
      const swap = a;
      a = b;
      b = swap;
    }
    if (a > t0) t0 = a;
    if (b < t1) t1 = b;
    return t0 <= t1;
  };

  if (!clip(p.x, dx, minX, maxX)) return false;
  if (!clip(p.y, dy, minY, maxY)) return false;
  return t0 <= t1;
}

/**
 * Punto en el perímetro por el que sale el rayo desde el centro de la Card
 * hacia `toward`. Respaldo geométrico: para rectángulos que no se solapan,
 * el segmento entre ambos rayos nunca atraviesa ninguna de las dos Cards.
 */
export function rayExitPoint(node, toward) {
  const center = cardCenter(node);
  const rect = cardRect(node);
  const dx = toward.x - center.x;
  const dy = toward.y - center.y;
  if (Math.abs(dx) < EPSILON && Math.abs(dy) < EPSILON) {
    return { x: center.x, y: rect.top };
  }
  let t = Infinity;
  if (Math.abs(dx) >= EPSILON) {
    t = Math.min(t, ((dx > 0 ? rect.right : rect.left) - center.x) / dx);
  }
  if (Math.abs(dy) >= EPSILON) {
    t = Math.min(t, ((dy > 0 ? rect.bottom : rect.top) - center.y) / dy);
  }
  return { x: center.x + dx * t, y: center.y + dy * t };
}

function nearestAnchorIndex(node, point) {
  const center = cardCenter(node);
  const direction = Math.atan2(point.y - center.y, point.x - center.x);
  let best = 0;
  let bestDiff = Infinity;
  for (let index = 0; index < 8; index++) {
    const diff = angleDiff(anchorAngle(node, index), direction);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = index;
    }
  }
  return best;
}

/**
 * Elige el par de anclajes (origen y destino) más conveniente para unir dos
 * Cards, minimizando la desviación angular en ambos extremos y garantizando
 * que el segmento no atraviese ninguna de las dos.
 *
 * Devuelve:
 * - sourceAnchor / targetAnchor: índice 0-7 de cada extremo.
 * - sourcePoint / targetPoint: punto exacto sobre el perímetro.
 * - fallback: true si se usó el respaldo por rayo entre centros (solo posible
 *   cuando las dos Cards se solapan, caso degenerado).
 */
export function pickEdgeAnchors(source, target) {
  const from = cardCenter(source);
  const to = cardCenter(target);
  const theta = Math.atan2(to.y - from.y, to.x - from.x);

  const candidates = [];
  for (let s = 0; s < 8; s++) {
    const sourceAngle = anchorAngle(source, s);
    for (let t = 0; t < 8; t++) {
      const targetAngle = anchorAngle(target, t);
      candidates.push({
        s,
        t,
        cost:
          angleDiff(sourceAngle, theta) +
          angleDiff(targetAngle, theta + Math.PI),
      });
    }
  }
  candidates.sort((a, b) => a.cost - b.cost);

  for (const candidate of candidates) {
    const sourcePoint = anchorPoint(source, candidate.s);
    const targetPoint = anchorPoint(target, candidate.t);
    if (
      !segmentHitsCard(sourcePoint, targetPoint, source) &&
      !segmentHitsCard(sourcePoint, targetPoint, target)
    ) {
      return {
        sourceAnchor: candidate.s,
        targetAnchor: candidate.t,
        sourcePoint,
        targetPoint,
        fallback: false,
      };
    }
  }

  // Respaldo geométrico (solo con Cards solapadas): rayo entre centros.
  const sourcePoint = rayExitPoint(source, to);
  const targetPoint = rayExitPoint(target, from);
  return {
    sourceAnchor: nearestAnchorIndex(source, sourcePoint),
    targetAnchor: nearestAnchorIndex(target, targetPoint),
    sourcePoint,
    targetPoint,
    fallback: true,
  };
}

/**
 * Modo de controles de cabecera según el ancho de la Card:
 * - "full": los 5 controles en línea.
 * - "mini": Editar + Conectar en línea y el resto en el menú.
 * - "menu": todo en el menú contextual (tarjetas pequeñas).
 */
export function cardHeaderMode(width) {
  if (width >= HEADER_FULL_MIN_WIDTH) return "full";
  if (width >= HEADER_MINI_MIN_WIDTH) return "mini";
  return "menu";
}