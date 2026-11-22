# UX-REVIEW-002 — Revisión independiente de Fase 9.1

**Prioridad:** P1 · **Responsable:** Reviewer distinto de Mimo (Copilot UX preferente) · **Estado:** PLANNING  
**Dependencias:** RESPONSIVE-002, UX-HOME-002, UX-WIDGETS-002 y UX-MODULES-002 en REVIEW.

## Objetivo

Evaluar que la experiencia implementada cumpla las especificaciones de producto y que los cambios realmente reduzcan fricción sin degradar accesibilidad, integridad, responsive o comprensión.

## Restricciones

- Solo lectura. No cambiar código, documentos, configuración, commits ni ramas.
- No aceptar una implementación por parecerse visualmente al diseño: ejecutar flujos y contrastar criterios.
- El reviewer no puede ser Mimo, que implementa las tareas.
- Si no dispone de navegador local real, debe declararlo y no afirmar QA visual.

## Alcance

- Home: listas Atención/Hoy disjuntas; datos fallidos vs vacíos; proyecto sin tareas; captura tarea/nota y borradores.
- Widgets: modo Personalizar, arrastre dentro de zonas, límites entre zonas, grupo Captura rápida, toggles, Guardar/Cancelar/error/reload, Settings sin editor numérico.
- Projects: panel progresivo, lista visible, error, cancelar y foco.
- Notes: creación progresiva, edición PATCH, preservación de tags/vínculos, error y borrador.
- Responsive: todas las vistas principales sin overflow horizontal accidental.
- Accesibilidad: navegación teclado completa, nombres/roles, foco visible/restaurado, alternativa al drag, aria-live, reduced motion y targets táctiles.
- Temas oscuro y claro.

## Matriz

- Desktop 1440×900
- Tablet 768×1024
- Móvil 390×844

Probar mouse/puntero, teclado y táctil real o emulado claramente identificado. Revisar consola, overflow, textos largos, loading, empty, error, success y confirmación.

## Entrega

Informe con:
1. ACCEPT / REJECT / BLOCKED por tarea.
2. Hallazgos con severidad, pasos reproducibles, viewport, navegador y evidencia.
3. Criterios cumplidos/no cumplidos.
4. Limitaciones de la prueba.
5. Defectos ya conocidos que permanecen fuera de alcance (por ejemplo --text-muted si aún no está resuelto).

No implementar arreglos. Dejar REVIEW y remitir veredicto al PO.
