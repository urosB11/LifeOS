# HOME-001 — Rediseño de Home como centro de operaciones

**Prioridad:** P0 · **Responsable:** Developer — Nemo · **Revisión:** Mimo · **Estado:** READY

## Problema

Home muestra seis métricas de igual jerarquía y una grilla de widgets. La información existe, pero la pantalla no ayuda suficientemente a decidir qué hacer. La prominencia visual no refleja urgencia ni utilidad.

## Objetivo

Convertir Home en una vista diaria que responda:
1. qué requiere atención;
2. qué conviene hacer hoy;
3. qué proyectos están en marcha;
4. cómo vienen los hábitos;
5. cómo registrar una tarea o nota.

## Estructura propuesta

### Encabezado
- Título Home y fecha local.
- Frase contextual breve y neutral.
- Acción secundaria para configurar widgets.
- Sin mensajes motivacionales ni saludos artificiales.

### Atención
- Mostrar tareas vencidas y tareas que vencen hoy si existen.
- Distinguir urgencia por fecha y prioridad.
- Si no hay elementos urgentes, mostrar estado tranquilo y útil.
- Tareas sin fecha no son vencidas.

### Hoy
- Lista de tareas pendientes relevantes.
- Orden: vencidas, vencen hoy, prioridad alta, próxima fecha; sin fecha al final.
- Mostrar proyecto, prioridad y vencimiento cuando existan.
- Acceso a Tareas y acción de completar si endpoint actual lo permite.

### Proyectos en marcha
- Proyectos activos relevantes.
- Usar task_count, completed_count, overdue_count y next_due_date de la API.
- Etiquetar la barra como progreso/ejecución de tareas.
- No llamar "salud del proyecto" a estos indicadores.

### Hábitos de hoy
- Hábitos programados hoy y estado guardado.
- Resumen compacto y acceso a Hábitos.
- No mostrar métricas sin definición.

### Captura rápida
- Crear tarea y nota desde Home.
- La tarea puede asociarse a un proyecto existente.
- Formularios compactos; título obligatorio, campos restantes opcionales.
- Conservar entradas ante error y evitar doble submit.
- Actualizar secciones tras guardar.

## Jerarquía visual

- No mantener seis tarjetas métricas iguales como estructura dominante.
- Priorizar atención y acciones de hoy sobre totales.
- Desktop: área amplia para Atención/Hoy y columna secundaria para Hábitos/Captura; proyectos en filas compactas.
- Tablet/móvil: reorganizar en una columna.
- Mantener tema oscuro y claro.
- Reutilizar tokens y componentes compartidos.

## Datos y contratos

Consultar primero:
- /api/v1/dashboard/summary
- /api/v1/dashboard/widgets
- /api/v1/tasks
- /api/v1/projects
- /api/v1/habits/today
- /api/v1/notes

No agregar endpoint ni dependencia sin demostrar que los existentes no alcanzan.

## Compatibilidad

- Preservar IDs de widgets, orden, visibilidad y preferencias.
- No dejar Home vacío por defecto.
- No eliminar widgets existentes ni cambiar catálogo sin especificación.

## No incluir

Gráficas históricas, velocidad, predicciones, IA, objetivos, entregables, calendario sincronizado ni datos sintéticos.

## Criterios de aceptación

- Se identifican tareas vencidas y de hoy en primera mirada.
- Las acciones están ordenadas con reglas explícitas.
- Proyectos muestran métricas reales y claramente etiquetadas.
- Hábitos muestra estado guardado del día local.
- Crear tareas/notas no duplica registros.
- Errores no destruyen entradas.
- Preferencias de widgets siguen funcionando.
- Loading, empty, error y success resueltos.
- Responsive y teclado en desktop, tablet y móvil.
- Sin dependencias ni migraciones.

## Pruebas

Datos sintéticos conocidos de vencidas/hoy/sin fecha/completadas; proyectos vacíos y con tareas; hábitos con diferentes estados; widgets visibles/ocultos; error HTTP; doble click y Enter. Ejecutar node --check, Ruff, pytest, smoke y revisión visual.

Entregar informe y dejar REVIEW, no DONE.