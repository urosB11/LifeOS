# UX-WIDGETS-002 — Personalización visual y reordenamiento de widgets

**Prioridad:** P1 · **Responsable:** Developer — Mimo · **Estado:** READY  
**Dependencia:** UX-HOME-002 · **Rama:** product/lifeos-evolution.

## Problema confirmado en el código

Home ya tiene un modal con flechas de orden, pero no permite arrastrar las tarjetas reales. El layout asigna los widgets a zonas fijas mediante roles main, side y full; el orden solo tiene efecto dentro de cada zona. Settings contiene además una tabla duplicada con un input numérico por widget.

El modelo widget_preferences y GET/PUT /dashboard/widgets persisten widget_id, is_visible y position. No persisten una zona/columna. El código asigna la zona por widget_id mediante WIDGET_ROLES.

## Objetivo

Permitir organizar visualmente los widgets directamente desde Home, sin números de orden, manteniendo el modelo actual, IDs, visibilidad y funcionamiento accesible.

## Decisión de alcance (aprobada para esta tarea)

- Reordenar únicamente dentro de la zona funcional actual: main, side o full.
- No mover widgets de una zona a otra.
- No agregar columna zone, migración, endpoint, modelo ni atajo en config_json.
- El usuario entra en un modo explícito Personalizar; la página normal permanece limpia.
- La zona full contiene actualmente un solo widget, por lo que no debe mostrar un asa o affordance de arrastre sin utilidad.

## Modelo de interacción

### Modo normal
- Las tarjetas no muestran asas permanentes ni controles de orden.
- Home mantiene su jerarquía y comportamiento de lectura.

### Modo Personalizar
- Un control claro “Personalizar” activa el modo; el control cambia a estado accesible “Finalizar personalización” o equivalente.
- Las tarjetas que se pueden reordenar muestran un asa explícita; solo el asa inicia el drag, nunca el cuerpo completo.
- Se muestra un placeholder de destino y una señal visual de inserción.
- Solo se acepta el drop dentro de la misma zona. Un destino de otra zona se indica como no permitido; no mover ni cambiar el rol.
- Los widgets ocultos siguen siendo configurables en una sección “Secciones disponibles/ocultas” con toggles de visibilidad. Al activarlos vuelven a su zona original.
- No es necesario mostrar un drag handle cuando una zona no tiene al menos dos unidades movibles.

### Captura rápida como grupo

quick_add_task y quick_add_note se renderizan como una sola tarjeta visual de Captura rápida. Al menos uno puede estar visible. Para orden:
- El grupo se mueve como una única unidad.
- La visibilidad de cada acción sigue siendo independiente.
- Si solo una acción está visible, la tarjeta conserva la posición del grupo.
- Reordenar el grupo no modifica el orden relativo interno ni la visibilidad de sus dos IDs.
- El sistema nunca debe duplicar la tarjeta por haber dos preferencias visibles.

### Guardar y cancelar
- El orden y los toggles durante Personalizar viven en un borrador local; no hacer requests mientras se arrastra.
- Guardar serializa el catálogo completo de seis IDs con is_visible y position, manteniendo los roles y grupos. Envía un único PUT a /dashboard/widgets.
- Cancelar descarta el borrador local y restaura lo guardado.
- Si falla el PUT, mantener el borrador visible, no cerrar el modo ni perder cambios; ofrecer reintento.
- Evitar doble submit; indicar estado Guardando/Guardado/Error.
- Tras guardar, actualizar Home sin perder foco/contexto.
- Restablecer defaults puede ser una acción secundaria con confirmación si sobrescribe preferencias.

### Interacción accesible

- Proveer mover arriba/abajo como alternativa funcional al drag.
- La operación debe poder hacerse con teclado sin mouse ni touch.
- Conservar el foco en el widget movido y anunciar nombre y nueva posición mediante región aria-live.
- Targets táctiles de al menos 44×44 CSS px.
- No depender de hover.
- Para Pointer Events, limitar touch-action:none al asa; el resto de la tarjeta mantiene scroll natural. No exigir arrastre desde una superficie que interfiere con el scroll.
- Respetar prefers-reduced-motion y no reconstruir toda la grilla repetidamente durante pointermove.

## Settings

- Eliminar el input numérico de position y la tabla duplicada de orden.
- Settings puede mostrar una frase explicativa y un acceso a Home para personalizar widgets.
- No duplicar el toggle de visibilidad ni mantener dos fuentes de verdad.
- Usar la ruta actual de Home ya definida por la aplicación; no inventar una ruta nueva.

## Persistencia y orden

- Reutilizar GET/PUT /dashboard/widgets.
- Reutilizar position para almacenar el orden de presentación compatible con las tres zonas actuales.
- Normalizar las posiciones en una secuencia estable y determinista al guardar; mantener el orden relativo de widgets ocultos y el grupo Captura rápida.
- No escribir posiciones durante cada frame ni generar un evento por cada movimiento.
- El API guarda la preferencia final con el mecanismo existente; sin cambios de backend.

## No incluir

Mover entre zonas/columnas; free-form canvas; redimensionar widgets; múltiples layouts/perfiles; drag de tareas; nuevas librerías; migraciones; endpoints; refactor genérico de layout; nueva configuración JSON.

## Criterios de aceptación

1. El modo normal no muestra controles de personalización permanentes.
2. En modo Personalizar, se pueden arrastrar widgets movibles dentro de su zona.
3. No es posible soltar en otra zona.
4. Existe alternativa por botones/teclado y funciona sin puntero.
5. Captura rápida se mueve como grupo y mantiene visibilidad independiente por acción.
6. Los toggles de visibilidad funcionan para los seis IDs.
7. Guardar persiste el orden/visibilidad tras reload y reinicio.
8. Cancelar revierte cambios no guardados.
9. Error de guardado preserva el borrador y permite reintentar.
10. Settings ya no tiene input numérico ni editor duplicado.
11. IDs y respuesta API siguen siendo compatibles con código existente.
12. Sin migraciones, endpoints ni dependencias nuevas.
13. Teclado, táctil, foco, aria-live, reduced motion y temas dark/light verificados.

## Pruebas

- Dos widgets main; hábitos y grupo Captura en side; único widget full.
- Ambos quick capture visibles, solo task visible, solo note visible, ambos ocultos.
- Drag antes/después de widget, intento entre zonas, mover por botones/teclado.
- Guardar/cancelar/reload/error/reintento/doble click.
- Verificar orden en API y UI con posiciones normalizadas.
- Settings sin número ni editor; navegación a Home.
- Viewports 1440×900, 768×1024, 390×844; pointer/mouse, teclado y touch.
- pytest, Ruff, node --check, smoke temporal y diff check.

## Entrega

Documentar modelo exacto de serialización de position, archivos tocados, pruebas y limitaciones. Commit y push a product/lifeos-evolution. Estado REVIEW, no DONE.
