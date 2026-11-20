# TASK-001 — Mejorar el espacio de trabajo de Tareas

**Prioridad:** P1 · **Responsable:** Developer — Nemo · **Revisión:** Mimo · **Estado:** READY después de HOME-001

## Problema

La vista de Tareas resuelve CRUD básico, pero la experiencia está dominada por un formulario siempre visible y una tabla genérica. Se necesita capturar, priorizar, revisar y modificar acciones con menos fricción.

## Objetivo

Mejorar la organización de tareas y las acciones frecuentes sin crear un sistema de gestión nuevo ni modificar el modelo de datos.

## Alcance funcional

1. Crear tarea mediante acción compacta y formulario desplegable/modal accesible.
2. Editar tarea existente usando PATCH actual: título, descripción, prioridad, vencimiento y proyecto.
3. Mantener completar/reabrir y eliminar con confirmación.
4. Mantener filtros existentes por estado y proyecto.
5. Añadir contadores o grupos claros para pendientes y completadas.
6. Destacar vencimientos sin depender solo del color.
7. Acceder al proyecto asociado cuando la navegación actual lo permita.
8. Conservar formularios ante errores y prevenir doble submit.

## Presentación

- Lista compacta y legible; en móvil puede convertirse en filas tipo tarjeta.
- Prioridad, fecha y estado escaneables.
- Acciones frecuentes separadas de eliminar.
- No construir Kanban, drag-and-drop ni tabla con demasiadas columnas.
- El formulario no ocupa permanentemente media pantalla.
- Reutilizar tema y componentes compartidos.

## Datos y límites

- Reutilizar GET/POST/PATCH/DELETE y complete/reopen actuales.
- No modificar entidades, migraciones ni endpoints salvo limitación real documentada.
- No implementar búsqueda global, dependencias, asignaciones multiusuario, subtareas ni time tracking.

## Criterios de aceptación

- Crear y editar tareas desde la vista.
- Guardar y mostrar campos opcionales.
- Mantener filtros al actualizar cuando corresponda.
- Diferenciar vencida, pendiente y completada.
- Errores no borran formularios.
- Acciones destructivas confirmadas.
- Responsive, teclado y estados completos.
- Compatibilidad con tareas creadas desde Proyectos y Home.

## Pruebas

CRUD de campos, tarea con/sin proyecto, cambio de fecha/prioridad, completar/reabrir, error de red, doble envío, filtros, textos largos, desktop/tablet/móvil y teclado. Entregar informe y dejar REVIEW.