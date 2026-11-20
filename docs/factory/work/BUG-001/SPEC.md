# BUG-001 — Conservar el formulario de creación de tarea ante error

**Prioridad:** P0 · **Responsable:** Developer — Nemo · **Estado:** READY

## Hallazgo a verificar

En el flujo de creación de tarea desde el detalle del proyecto, comprobar si renderDetail reconstruye los controles durante el envío y tras un error HTTP sin restaurar los valores introducidos. La implementación actual parece reconstruir el formulario sin conservar su estado.

Reproducir antes de modificar.

## Comportamiento esperado

- Si la API devuelve error o falla la conexión, mantener título, descripción, prioridad y vencimiento.
- Mostrar el error junto al formulario.
- Mantener el formulario abierto y enfocar el primer campo inválido o el mensaje.
- Evitar doble envío mientras la petición está pendiente.
- Si se crea correctamente, cerrar el formulario, limpiar campos, actualizar tareas y métricas y confirmar.

## Restricciones

No cambiar endpoint, modelo, migraciones ni dependencias. No modificar otros formularios salvo defecto reproducido y corrección aislada.

## Criterios

1. Error HTTP conserva los valores.
2. Error de red conserva los valores.
3. Entrada inválida señala el campo sin perder los demás.
4. Doble click no crea dos tareas.
5. Éxito crea una sola tarea con el project_id correcto.
6. Funciona con teclado y móvil.

## Pruebas

Agregar pruebas frontend si la estrategia lo permite; en su defecto documentar pasos de reproducción. Ejecutar node --check, pytest y Ruff según archivos afectados.