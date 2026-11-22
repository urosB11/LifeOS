# UX-MODULES-002 — Formularios progresivos y edición de notas

**Prioridad:** P1 · **Responsable:** Developer — Mimo · **Estado:** READY  
**Dependencia:** UX-WIDGETS-002 · **Rama:** product/lifeos-evolution.

## Problema

Projects y Notes muestran formularios de creación permanentemente, aun cuando el usuario está consultando listas. Notes permite abrir una nota en una vista de lectura y eliminarla, pero no editarla en la interfaz, aunque FR-NOTE-03 exige editar título y contenido y el backend ya dispone de PATCH.

Tasks ya tiene un panel compacto de creación/edición y Habits ofrece acciones directas de registro. No se deben rehacer módulos que ya resuelven el patrón.

## Objetivo

Reducir la ocupación permanente de pantalla, mantener el contexto de lista y completar la edición de notas usando contratos existentes.

## Projects — alta progresiva

- El listado inicia con una acción primaria “+ Nuevo proyecto”; el formulario permanece cerrado.
- Al abrir, mostrar panel compacto con nombre obligatorio y descripción opcional.
- La lista de proyectos permanece visible en el DOM mientras el panel está abierto.
- Guardar crea una vez, refresca la lista y devuelve foco/contexto de forma coherente.
- Cancelar/Escape cierra y restaura el foco al disparador.
- Error HTTP, validación o red conserva borrador, muestra el mensaje junto al panel y permite reintentar.
- No cambiar estados, reglas de archivado, eliminación, notas vinculadas ni navegación de detalle.
- No rehacer el formulario de edición del detalle salvo defecto reproducible.

## Notes — alta progresiva y edición real

### Alta
- La vista de lista inicia con acción “+ Nueva nota”; el editor no ocupa permanentemente la pantalla.
- Abrir editor con título obligatorio y contenido de texto; etiqueta opcional si el patrón actual lo soporta.
- Lista, búsqueda y filtro por etiqueta permanecen visibles mientras se crea.
- Cancelar/Escape cierra el panel y restaura el foco.
- Ante error, conservar título, contenido y etiqueta seleccionada.
- No renderizar HTML ni habilitar Markdown enriquecido; el contenido sigue siendo texto seguro.

### Edición
- Incorporar acción Editar para una nota existente desde su tarjeta/detalle.
- Cargar title y content actuales; guardar mediante PATCH /notes/{id} (o ruta existente equivalente comprobada).
- Guardar/Cancelar explícitos. Enter no debe insertar un submit accidental si se está escribiendo contenido multilínea.
- Escape cancela únicamente cuando no hay una operación pendiente; pedir confirmación solo si descartar borrador modificado podría perder trabajo.
- Conservar vínculos proyecto/tarea y etiquetas existentes al editar título/contenido. No reescribir relaciones si el usuario no las modificó.
- Actualizar la tarjeta/lista y updated_at tras guardar.
- Si falla el PATCH, mantener el editor y todo el borrador; mostrar error y permitir reintento.
- Restaurar el foco a la acción Editar al cerrar; modal/panel con semántica y trampa de foco si corresponde.

### Etiquetas

- El formulario “Nueva etiqueta” puede comenzar colapsado detrás de una acción secundaria.
- La lista de etiquetas y el filtro por etiqueta permanecen accesibles.
- No agregar renombrado ni borrado de etiquetas; preservar el modelo compartido.

## Patrones comunes

- Usar el patrón probado de TASK-001: trigger con aria-expanded/aria-controls, panel hidden por defecto, Escape, foco restaurado, guardia contra doble envío, estado pending y borrador separado del DOM cuando hay re-render.
- Acciones principales visibles; acciones secundarias ocasionales pueden quedar en “Más acciones” con nombre accesible.
- Eliminar mantiene confirmación explícita y aspecto visual secundario.
- No guardar al perder foco sin que el usuario lo haya solicitado.

## No incluir

Reescritura de Tasks; rediseño integral de Habits; editor rich text/Markdown; nuevas etiquetas/relaciones de dominio; búsqueda semántica; nuevos endpoints; nuevas dependencias; migraciones; cambios de seguridad.

## Criterios de aceptación

1. Project create form oculto por defecto; lista siempre visible.
2. Cancelar/Escape devuelve foco; no se pierde borrador en error.
3. Notes create form oculto por defecto; lista/búsqueda/filtro visibles.
4. Una nota existente permite editar title y content con PATCH.
5. La edición conserva etiquetas y vínculos no modificados.
6. Error de red/422 conserva el borrador.
7. Doble submit no duplica registros ni eventos.
8. Etiquetas pueden crearse sin mantener formulario abierto permanentemente.
9. Acción eliminar continúa confirmada.
10. Teclado, foco, tamaños táctiles y responsive verificados en ambos temas.
11. No hay cambio de API/modelo/seguridad.

## Pruebas

Proyectos: abrir/cerrar, Escape, crear, error POST, doble clic, lista visible, textos largos y cancelación. Notes: crear con título/contenido, nota con contenido vacío si está permitido, editar ambas propiedades, cancelación, error 422/red, preservar tags/links, evitar doble PATCH, cerrar modal y restaurar foco. Verificar texto escapado/no HTML. Viewports 1440×900, 768×1024, 390×844; themes dark/light; pytest, Ruff, node --check y smoke temporal.

## Entrega

Informe de pruebas, archivos, comportamiento y cualquier limitación. Commit y push a product/lifeos-evolution. Estado REVIEW, no DONE.
