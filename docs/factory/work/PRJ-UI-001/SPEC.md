# PRJ-UI-001 — Mantener las tareas visibles al abrir el formulario

**Prioridad:** P1 · **Responsable:** Developer — Mimo (asignación explícita del PO) · **Reviewer independiente:** Nemo · **Estado:** READY

## Problema

En el detalle de un proyecto, al pulsar "+ Nueva tarea", `taskFormOpen` hace que `renderDetail()` oculte la tabla de tareas existentes. El usuario pierde de vista el trabajo que ya está dentro del proyecto mientras captura otra tarea.

## Comportamiento esperado

- Al abrir el formulario, mantener siempre visible la lista/tabla de tareas existentes.
- Insertar el formulario compacto debajo del encabezado de la sección Tareas y antes de la lista.
- Las tareas existentes deben desplazarse hacia abajo de forma natural; no desaparecer, desmontarse ni reemplazarse por el formulario.
- Mantener visible el contador de tareas y el resumen de completadas/pendientes/vencidas.
- Si no existen tareas, mostrar el estado vacío debajo del formulario mientras está abierto.
- Al cancelar, quitar solo el formulario; la lista permanece en el mismo contexto.
- Tras crear una tarea, cerrar el formulario, actualizar la lista y los contadores, y mostrar confirmación.
- No introducir un contenedor de lista con scroll independiente. El documento debe conservar su scroll normal.
- Evitar que el render del formulario desplace al usuario abruptamente al inicio o al final del detalle.

## Restricciones y coordinación

- Cambio localizado en `frontend/assets/js/projects.js` y estilos puntuales si fueran necesarios.
- No tocar modelos, base de datos, endpoints ni migraciones.
- No implementar todavía notas, documentos, adjuntos, hitos, métricas o tracker dentro de Proyectos.
- No duplicar ni revertir BUG-001: conservar la corrección de persistencia de valores del formulario ante error y coordinar el cambio sobre el mismo renderizado.
- Preservar el comportamiento de crear tarea asociada al `project_id` correcto.

## Criterios de aceptación

1. Al abrir "+ Nueva tarea", las tareas existentes siguen renderizadas y visibles debajo del formulario.
2. Con cero tareas, formulario y estado vacío se muestran sin contradicciones.
3. Cancelar conserva la lista y no cambia sus datos.
4. Crear una tarea agrega una fila y actualiza los contadores sin duplicar.
5. Errores de validación/API no ocultan la lista ni contradicen BUG-001.
6. La lista/formulario son usables en desktop, tablet y móvil sin overflow horizontal.
7. No se pierde navegación ni scroll del detalle.

## Pruebas requeridas

- Proyecto con 0, 1 y varias tareas; abrir/cerrar formulario.
- Verificar que las tareas existentes permanecen en DOM y a la vista.
- Crear tarea correctamente y simular error de API/red.
- Comprobar que no hay doble envío ni regresión de BUG-001.
- `node --check`, `pytest -q`, `ruff check app tests` y smoke con DB temporal según archivos afectados.
- QA visual 1440×900, 768×1024 y 390×844; teclado, foco y overflow.

## Entrega

Actualizar handoff y WORK_QUEUE, revisar el diff, crear commit descriptivo y hacer push obligatorio a `origin/product/lifeos-evolution`. Verificar que el commit está en remoto. No hacer merge ni push a main. Dejar en REVIEW; Nemo realiza revisión independiente.