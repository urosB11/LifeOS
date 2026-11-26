# UX-WIDGETS-003 — Grid flexible y redimensionable para Home

**Prioridad:** P1 · **Responsable:** Developer — Mimo · **Estado:** REVIEW
**Autorización:** Product Owner, 2026-11-22 · **Rama:** product/lifeos-evolution
**Dependencia:** UX-WIDGETS-002 (base existente; esta tarea amplía explícitamente sus límites).

## Alcance aclarado

La superficie son los seis widgets actuales de Home. Projects y Notes no se convierten en widgets ni se modifican en esta tarea.

El PO autorizó expresamente extender el modelo/API y crear una migración para conservar el tamaño y el orden del grid. Esta tarea supersede para Home los límites de UX-WIDGETS-002 que excluían tamaño y movimiento entre zonas. No habilita cambios en otros módulos.

## Decisión de layout

- Reemplazar las tres zonas fijas por un grid CSS único de seis columnas en escritorio, cuatro en tablet y una en móvil.
- Cada tarjeta ocupa posiciones auto-colocadas por CSS Grid. `position` define el orden global y `column_span`/`row_span` sus dimensiones lógicas; no se persisten coordenadas en píxeles ni hay posiciones superpuestas.
- Valores permitidos: `column_span` de 2 a 6 y `row_span` de 1 a 3. En tablet el ancho visible se limita a cuatro columnas; en móvil todas las tarjetas ocupan el ancho disponible. Los tamaños guardados reaparecen al volver a un viewport amplio.
- Los tamaños son mínimos de grid, no alturas fijas: el contenido puede ampliar una fila y nunca se recorta para forzar una dimensión.
- El layout inicial prioriza una composición emparejada por filas: tareas 4×1 junto a Captura rápida 2×1; proyectos 4×1 junto a hábitos de hoy 2×1; semana de hábitos a 6×1. El contenido puede ampliar las filas de forma natural.
- Captura rápida continúa siendo una tarjeta visual: `quick_add_task` y `quick_add_note` conservan visibilidad independiente y comparten orden y tamaño.

## Persistencia y compatibilidad

- Extender `widget_preferences` con `column_span` y `row_span`; reutilizar `position`, `is_visible`, el catálogo de IDs y `GET/PUT /api/v1/dashboard/widgets`.
- Migración Alembic aditiva con valores por defecto seguros y transformación determinista del orden anterior por zonas: se intercalan los widgets de `main` con los del `side`, considerando Captura rápida como un grupo, y se colocan al final los widgets `full`. Se conserva el orden relativo previo dentro de cada zona y la visibilidad.
- La API valida límites enteros, mantiene compatibilidad con PUT anteriores que omitan spans y devuelve ambos campos al listar/guardar.
- Actualizar la versión de exportación JSON y conservar las nuevas columnas en exportación y backup.
- No guardar layout en `config_json` ni en `localStorage`; no agregar endpoints ni dependencias.

## Interacción

- En modo normal no hay controles de movimiento o tamaño permanentes.
- En Personalizar, se arrastra una tarjeta desde un asa explícita para cambiar su orden; una previsualización indica el destino.
- El tamaño cambia desde un asa de redimensión con Pointer Events. Solo las asas capturan puntero/touch; botones, inputs, formularios y contenido interno conservan su comportamiento.
- El movimiento y el tamaño son un borrador local hasta Guardar. Cancelar descarta ambos; un error de guardado conserva el borrador y permite reintentar.
- Mantener botones accesibles arriba/abajo. El asa de redimensión permite ajuste con flechas; anunciar los cambios con una región viva.
- Usar targets de al menos 44×44 CSS px, foco visible, estados de arrastre/redimensión, `touch-action: none` solo en las asas y respetar `prefers-reduced-motion`.

## Boceto visual

Escritorio, 6 columnas:

```text
+--------------------------------------+------------------+
| Tareas próximas (4)                  | Captura rápida(2)|
+--------------------------------------+------------------+
| Proyectos activos (4)                | Hábitos de hoy(2)|
+---------------------------------------------------------+
| Semana de hábitos (6)                                   |
+---------------------------------------------------------+
```

Tablet reduce el grid a cuatro columnas y adapta los spans; móvil usa una sola columna, conserva el orden y presenta cada widget a ancho completo.

## Criterios de aceptación

1. Los seis widgets pueden cambiar de orden mediante arrastre en el modo Personalizar.
2. Los widgets pueden redimensionarse en pasos de columnas/filas sin recortar contenido.
3. El guardado persiste orden y dimensiones tras reload y reinicio; Cancelar revierte ambos.
4. El arrastre/redimensionamiento desde asas no activa controles internos ni interfiere con el scroll fuera de ellas.
5. Captura rápida se mueve/redimensiona como una unidad y mantiene la visibilidad independiente de sus acciones.
6. Alternativas de teclado para mover y redimensionar conservan foco y anuncian el resultado.
7. El layout se adapta a 1440×900, 768×1024 y 390×844, sin overflow horizontal, en temas claro y oscuro.
8. La migración preserva las preferencias existentes, incluyendo visibilidad y orden relativo por zonas.
9. GET/PUT y exportación devuelven/persisten los spans; entradas fuera de rango responden 422 sin escrituras parciales.
10. No hay regresiones de captura, completar tareas, registros de hábitos, enlaces ni personalización de visibilidad.

## QA

- Migración desde `0005_habits` y pruebas de API con `LIFEOS_DATA_DIR` temporal verificado.
- Drag de mouse, drag con pointer en móvil, redimensionamiento en ambos ejes, keyboard, Cancelar/Guardar/error/reintento/reload.
- Interacciones internas de los widgets y doble submit donde corresponda.
- Matriz de los tres viewports y dos temas.
- `pytest`, Ruff, `node --check`, smoke API, exportación, `git diff --check` y revisión del diff.

## Entrega

Documentar decisión, archivos, migración, serialización de spans, resultados reales y límites de QA en HANDOFF.md. Actualizar DATABASE.md y las guías afectadas. Commit y push a product/lifeos-evolution; dejar REVIEW, no DONE.
