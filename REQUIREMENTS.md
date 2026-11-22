# Life OS — Requisitos funcionales y no funcionales del MVP 0.1

**Estado:** línea base de requisitos para implementación
**Versión:** 0.3
**Fecha:** 22 de noviembre de 2026
**Relacionado con:** `VISION.md`, `ARCHITECTURE.md`, `DATABASE.md` y `SECURITY.md`

> Este documento define qué debe hacer el MVP. Las decisiones funcionales que afectan a esta versión están cerradas aquí; las tecnologías y límites técnicos se desarrollan en `ARCHITECTURE.md`.

## 1. Objetivo

Entregar una aplicación web local, responsive y de un solo usuario que permita gestionar tareas, proyectos y notas desde un dashboard configurable. La aplicación debe conservar los datos entre sesiones, permitir exportarlos y respaldarlos, y seguir siendo útil sin conexión a Internet ni inteligencia artificial.

## 2. Usuario y contexto de uso

- Usuario inicial: una persona que utiliza Life OS para organizar su propia información.
- Entorno inicial: computadora personal con navegador moderno.
- Plataforma de desarrollo inicial: Windows 10/11; el código debe evitar dependencias innecesarias del sistema operativo.
- Conectividad: las funciones principales no requieren Internet.
- IA: no forma parte del MVP.
- Hardware: se priorizan procesos livianos y un número reducido de dependencias.

## 3. Alcance funcional

### 3.1 Aplicación y navegación

**FR-APP-01 — Inicio local.** La aplicación se inicia en el equipo del usuario siguiendo el README y se abre en el navegador.

**FR-APP-02 — Navegación principal.** Debe ofrecer acceso claro a Home, Tasks, Projects, Notes, Hábitos y Settings.

**FR-APP-03 — Diseño responsive.** La interfaz se adapta a escritorio, tablet y móvil sin perder acceso a las funciones principales.

**FR-APP-04 — Estados de interfaz.** Las vistas contemplan carga, estado vacío, error, confirmación y éxito con mensajes comprensibles.

### 3.2 Home y widgets

**FR-HOME-01 — Dashboard.** Home presenta un resumen de tareas y proyectos y accesos rápidos.

**FR-HOME-02 — Catálogo inicial.** El catálogo interno contiene estos widgets:

1. `upcoming_tasks`: tareas pendientes ordenadas por prioridad y vencimiento.
2. `active_projects`: proyectos activos.
3. `quick_add_task`: acceso rápido para crear una tarea.
4. `quick_add_note`: acceso rápido para crear una nota.
5. `habits_today`: hábitos activos programados para hoy con su estado de registro.
6. `habits_week`: programación y registros de la semana local por hábito.

**FR-HOME-03 — Visibilidad.** El usuario puede mostrar u ocultar cualquiera de los widgets disponibles.

**FR-HOME-04 — Orden y distribución.** El usuario puede reordenar y redimensionar los widgets desde Home mediante un modo explícito de personalización. El arrastre y el ajuste desde asas dedicadas tienen alternativas accesibles por teclado y táctil. Un grid responsive evita solapamientos; el orden y las dimensiones lógicas se conservan al reiniciar la aplicación.

**FR-HOME-05 — Persistencia.** La visibilidad, el orden y el tamaño de los widgets se conservan después de cerrar y reiniciar la aplicación.

**FR-HOME-06 — Fuente única.** Los widgets leen los datos de los módulos correspondientes; no mantienen copias operativas propias.

### 3.3 Tareas

**FR-TASK-01 — Crear.** El usuario crea una tarea con título obligatorio y descripción, prioridad, fecha de vencimiento y proyecto asociado opcionales.

**FR-TASK-02 — Consultar.** Puede ver una lista de tareas y abrir el detalle de cada una.

**FR-TASK-03 — Editar.** Puede modificar título, descripción, prioridad, vencimiento y proyecto.

**FR-TASK-04 — Completar y reabrir.** Puede marcar una tarea como completada y volver a abrirla.

**FR-TASK-05 — Eliminar.** Puede eliminar una tarea después de una confirmación explícita. Las notas vinculadas se conservan y pierden únicamente el vínculo con esa tarea.

**FR-TASK-06 — Estado.** Los estados son `pending` y `completed`.

**FR-TASK-07 — Prioridad.** La prioridad es opcional. Sus valores son `low`, `normal` y `high`; `NULL` representa que no se asignó prioridad.

**FR-TASK-08 — Vencimiento.** La fecha de vencimiento es opcional y representa un día de calendario local, no un instante UTC.

**FR-TASK-09 — Filtros y orden.** Se puede filtrar por estado, prioridad y proyecto, y ordenar por vencimiento, prioridad, fecha de creación o título. El orden inicial es: pendientes antes que completadas; prioridad alta antes que normal y baja; fecha de vencimiento más próxima primero; sin fecha después de las fechadas; creación más reciente como desempate.

### 3.4 Proyectos

**FR-PROJ-01 — Crear.** El usuario crea un proyecto con nombre obligatorio y descripción opcional.

**FR-PROJ-02 — Consultar.** Puede ver una lista y el detalle de cada proyecto.

**FR-PROJ-03 — Editar.** Puede modificar nombre y descripción.

**FR-PROJ-04 — Estados.** Los estados son `active`, `completed` y `archived`. Un proyecto completado puede volver a activo; un proyecto archivado puede restaurarse a activo.

**FR-PROJ-05 — Relación con tareas.** Puede asociar tareas a un proyecto y consultar las tareas asociadas.

**FR-PROJ-06 — Archivado y eliminación.** Archivar es la operación preferida y no elimina datos. La eliminación física requiere confirmación y solo se permite cuando el proyecto no tiene tareas asociadas. Las notas vinculadas conservan su contenido y pierden únicamente el vínculo con el proyecto eliminado. No se borran tareas en cascada.

### 3.5 Notas y etiquetas

**FR-NOTE-01 — Crear.** El usuario crea una nota con título y contenido de texto.

**FR-NOTE-02 — Consultar.** Puede listar notas y abrir su detalle.

**FR-NOTE-03 — Editar.** Puede modificar título y contenido.

**FR-NOTE-04 — Eliminar.** Puede eliminar una nota previa confirmación. Se eliminan sus relaciones y asignaciones a etiquetas; las etiquetas compartidas no se borran por ello.

**FR-NOTE-05 — Fechas.** Cada nota registra creación y última modificación.

**FR-NOTE-06 — Búsqueda.** La lista de notas permite buscar texto en título y contenido mediante búsqueda simple por coincidencia parcial. No se requiere un motor de búsqueda full-text ni búsqueda semántica.

**FR-NOTE-07 — Vínculos opcionales.** Una nota puede estar independiente o relacionarse con cero o varios proyectos y cero o varias tareas. Desde la nota se accede a los elementos vinculados; desde un proyecto o una tarea se pueden consultar sus notas.

**FR-NOTE-08 — Etiquetas.** El usuario puede crear etiquetas reutilizables, asignar varias a una nota, quitar asignaciones y filtrar notas por una etiqueta. Las notas y las etiquetas pueden existir sin relaciones. El MVP no requiere edición/renombrado de etiquetas ni filtros combinados por múltiples etiquetas.

**FR-NOTE-09 — Normalización.** Los nombres de etiquetas se normalizan quitando espacios externos, colapsando espacios repetidos y comparando sin distinguir mayúsculas/minúsculas. Se conserva un nombre visible elegido al crear la etiqueta; no se permiten duplicados equivalentes.

**FR-NOTE-10 — Conservación de notas.** Eliminar una tarea o un proyecto no elimina las notas relacionadas. Solo se quitan los vínculos afectados.

**FR-NOTE-11 — Contenido seguro.** El contenido se almacena y presenta como texto; no se ejecuta HTML ni JavaScript introducido en una nota. El formato Markdown enriquecido queda fuera del MVP.

### 3.6 Persistencia, exportación y respaldo

**FR-DATA-01 — Persistencia.** Tareas, proyectos, notas, etiquetas, relaciones, hábitos y sus registros, preferencias y eventos se guardan localmente.

**FR-DATA-02 — Reinicio.** Cerrar y reiniciar la aplicación no provoca pérdida de datos.

**FR-DATA-03 — Exportación.** El usuario puede exportar los datos funcionales en JSON versionado y documentado, incluyendo relaciones, etiquetas, hábitos y preferencias. El formato no depende de detalles internos del ORM.

**FR-DATA-04 — Backup.** Debe existir un procedimiento verificable para generar una copia de seguridad consistente de SQLite.

**FR-DATA-05 — Restauración.** Debe existir un procedimiento documentado de restauración de una copia SQLite. Antes de sustituir la base activa se realiza un backup previo y se verifica la integridad de la copia restaurada. La restauración de JSON desde la interfaz no forma parte del MVP.

**FR-DATA-06 — Integridad.** Todas las relaciones se validan en backend y base de datos; no se permiten referencias huérfanas. Los errores de una operación no deben dejar cambios parciales ni eventos desincronizados.

### 3.7 Configuración

**FR-SET-01 — Preferencias.** El usuario puede elegir tema claro, oscuro o del sistema y configurar la zona horaria. La visibilidad y el orden de los widgets se administran desde Home, que es la única interfaz de personalización del dashboard. Settings puede ofrecer un acceso directo a esa interfaz, pero no un segundo editor ni campos numéricos de posición.

**FR-SET-02 — Zona horaria.** Se utiliza `America/Argentina/Cordoba` inicialmente. La zona horaria queda configurable, pero las fechas de vencimiento se conservan como fechas de calendario.

**FR-SET-03 — Configuración técnica.** Las rutas, el puerto y los parámetros técnicos se configuran fuera de las tablas de dominio. No se guardan secretos en preferencias de usuario.

### 3.8 Estadísticas básicas

**FR-AN-01 — Resumen de tareas.** Home puede mostrar cantidad de tareas pendientes, completadas y vencidas.

**FR-AN-02 — Resumen de proyectos.** Home puede mostrar la cantidad de proyectos activos.

**FR-AN-03 — Progreso por proyecto.** El detalle de un proyecto puede mostrar tareas completadas sobre el total de tareas asociadas. Si no tiene tareas, se muestra “Sin tareas”, no 0 %.

**FR-AN-04 — Definición de métricas.** Toda métrica debe tener fórmula, fuente y período claros. Las cifras se calculan de forma determinista, sin IA.

**FR-AN-05 — Resumen de hábitos.** El resumen analítico incluye hábitos activos, programados hoy, completados hoy, omitidos hoy y pendientes hoy, usando solo los estados guardados en base.

### 3.9 Hábitos (Fase 7)

**FR-HAB-01 — Crear.** El usuario crea un hábito con nombre obligatorio y descripción, categoría, color (hex `#RGB` o `#RRGGBB`), fecha de inicio y frecuencia opcionales.

**FR-HAB-02 — Modalidades.** Un hábito es binario (cumplimiento sí/no) o cuantificable con `target_value` y `target_unit` opcionales; la unidad requiere cantidad objetivo.

**FR-HAB-03 — Frecuencias.** Solo `daily` y `weekly_days` con días 0=lunes … 6=domingo; sin duplicados ni fuera de rango. No se implementa motor de recurrencias en el MVP.

**FR-HAB-04 — Consultar.** Se listan los hábitos con filtro por estado y categoría, orden por posición, y se abre el detalle de cada uno.

**FR-HAB-05 — Editar.** Puede modificar nombre, descripción, categoría, color, frecuencia, objetivo y posición; la validación cruzada (por ejemplo `weekly_days` con al menos un día) usa el estado fusionado del hábito.

**FR-HAB-06 — Estados.** Los estados son `active`, `paused` y `archived`. Pausar requiere activo, reactivar requiere pausado, archivar parte de activo o pausado y restaurar requiere archivado; las transiciones son idempotentes y las inválidas responden conflicto.

**FR-HAB-07 — Archivar y eliminar.** Archivar es la operación preferida y conserva los registros. La eliminación física solo se permite sin registros; con registros responde conflicto (409).

**FR-HAB-08 — Registro diario.** El usuario registra un día del hábito (por defecto el día local actual). No se permiten días futuros, días no programados ni días anteriores a la fecha de inicio; hay un único registro por hábito y día, que se corrige con PATCH o se elimina (el día vuelve a no registrado).

**FR-HAB-09 — Estados de registro.** Los registros son `pending`, `completed` y `skipped`; `status` es la única fuente de verdad del cumplimiento y ninguna métrica lo recalcula. Al escribir un valor en un hábito cuantificable se deriva `completed` si `value >= target_value`.

**FR-HAB-10 — Vista de hoy.** La vista de Hábitos muestra los hábitos activos programados para el día local con su registro, permitiendo marcar, omitir, guardar cantidad y deshacer.

**FR-HAB-11 — Calendario.** Cada hábito muestra un calendario mensual con la programación y el estado de registro por día; la regla de días programados vive en backend y la interfaz solo lo representa.

**FR-HAB-12 — Métricas.** Racha actual, mejor racha, cumplimiento semanal/mensual y consistencia, con las fórmulas de `DATABASE.md` sección 8.1: solo los días programados entran en los denominadores y un denominador cero muestra “Sin datos”, no 0 %.

**FR-HAB-13 — Widgets.** `habits_today` y `habits_week` están en el catálogo, visibles por defecto y leen los endpoints existentes sin duplicar reglas ni datos.

**FR-HAB-14 — Exportación.** `habits` y `habit_entries` se incluyen en la exportación JSON y en el respaldo SQLite, con IDs y relaciones conservados.

**FR-HAB-15 — Límites.** Sin notificaciones, gamificación excesiva, IA ni sincronización: el seguimiento es manual y offline; los eventos de actividad no incluyen nombres ni contenido de hábitos.

## 4. Requisitos no funcionales

- **NFR-01 Portabilidad:** no depender de servicios pagos o propietarios para las funciones esenciales.
- **NFR-02 Propiedad de datos:** datos almacenados localmente, exportables y respaldables.
- **NFR-03 Modularidad:** separación entre frontend, API, servicios de aplicación y persistencia.
- **NFR-04 Simplicidad:** monolito modular; sin microservicios, Kubernetes, colas distribuidas ni framework frontend en el MVP.
- **NFR-05 Seguridad local:** bind exclusivo a `127.0.0.1` por defecto; no exponer el servicio a LAN o Internet.
- **NFR-06 Secretos:** no versionar credenciales, tokens, bases de usuario ni archivos `.env`.
- **NFR-07 Privacidad:** la aplicación no transmite datos del usuario a servicios externos en el MVP.
- **NFR-08 Usabilidad:** flujos claros, confirmaciones y mensajes comprensibles.
- **NFR-09 Mantenibilidad:** estructura consistente, instrucciones de ejecución y pruebas automatizadas.
- **NFR-10 Rendimiento:** funcionamiento razonable en hardware modesto; sin procesos pesados persistentes.
- **NFR-11 Pruebas:** pruebas para CRUD, relaciones, integridad, persistencia, backup/exportación y métricas básicas.
- **NFR-12 Accesibilidad:** navegación por teclado, foco visible, etiquetas semánticas, contraste legible y estados no comunicados solo por color.
- **NFR-13 Offline:** las funciones esenciales siguen operando sin Internet; la consulta de documentación de desarrollo con Context7 no es una dependencia de ejecución de Life OS.

## 5. Criterios de aceptación del MVP

El MVP se acepta cuando se demuestre que:

1. La aplicación se inicia desde instrucciones documentadas y abre Home.
2. Se crean, editan, completan, reabren y eliminan tareas.
3. Se crean y editan proyectos; se cambian sus estados y se vinculan tareas.
4. No se puede borrar físicamente un proyecto que tenga tareas; archivar no elimina información.
5. Se crean, consultan, editan y eliminan notas.
6. Una nota puede estar sin vínculos o relacionada con varios proyectos y tareas; los vínculos se ven desde ambos lados.
7. Se crean y reutilizan etiquetas; se evitan duplicados por mayúsculas y espacios; se filtran notas por etiqueta.
8. Al eliminar una tarea o proyecto, las notas permanecen y solo se quitan sus vínculos.
9. El dashboard permite mostrar, ocultar y reordenar widgets; conserva preferencias al reiniciar.
10. Los widgets reflejan los datos reales de los módulos.
11. Los datos y relaciones persisten tras cerrar y reiniciar.
12. La exportación JSON incluye las entidades y relaciones documentadas.
13. El backup SQLite puede crearse y restaurarse en un entorno de prueba.
14. Las métricas básicas coinciden con conjuntos de prueba conocidos y sus fórmulas documentadas.
15. Los flujos principales funcionan sin Internet ni IA.
16. Las vistas principales son utilizables en escritorio y móvil.
17. Las pruebas críticas pasan y no hay defectos conocidos de pérdida/corrupción de datos o exposición de red.
18. Se crean, editan, pausan, reactivan, archivan y restauran hábitos; no se elimina físicamente un hábito con registros.
19. Solo se registran días programados y no futuros; corregir un registro no duplica el historial.
20. Las métricas de hábitos (rachas, cumplimiento y consistencia) coinciden con conjuntos sintéticos conocidos y con las fórmulas documentadas.

## 6. Fuera de alcance (versión 0.2)

- Módulos completos Work, Business, Finance y Mind.
- Centro avanzado de Analytics transversal, comparaciones históricas, objetivos y reporting avanzado.
- Calendario sincronizado con terceros y gestor completo de conocimiento.
- IA conversacional, memoria semántica y agentes autónomos.
- Integraciones Gmail, Calendar, Telegram, GitHub u otros servicios.
- Sincronización cloud, acceso remoto, multiusuario y colaboración.
- App Center con instalación dinámica de plugins de terceros.
- Aplicaciones móviles nativas o empaquetado desktop.
- Adjuntos, imágenes, rich text y Markdown enriquecido dentro de notas.
- Importación/restauración de JSON desde la interfaz.
- Notificaciones externas, rachas con recompensas ni gamificación de hábitos.

## 7. Decisiones de línea base

Las siguientes decisiones quedan cerradas para el MVP y se desarrollan en los documentos técnicos:

- Frontend nativo HTML/CSS/JavaScript, sin framework ni proceso de build.
- Backend Python + FastAPI.
- Persistencia SQLite mediante SQLAlchemy 2.x y migraciones Alembic.
- SQLAlchemy síncrono para mantener simple la interacción con SQLite.
- Pruebas con pytest y HTTPX; Ruff para chequeos de estilo si queda configurado.
- API `/api/v1`, frontend servido por FastAPI en el mismo origen.
- UUIDv4 en texto para entidades; timestamps UTC y vencimientos como fechas locales.
- Proyectos archivables; eliminación física restringida cuando tienen tareas.
- Notas muchos-a-muchos con proyectos y tareas, y etiquetas reutilizables.
- Exportación JSON; backup/restauración de SQLite mediante procedimiento local documentado.

## 8. Gestión de cambios

Un requisito nuevo debe indicar el problema que resuelve, su beneficio, su impacto en datos, seguridad, arquitectura y mantenimiento, y criterios de aceptación. Las skills o sugerencias de los agentes no amplían por sí solas el alcance.

---

**Regla para OpenCode:** comenzar por la fase autorizada en `ROADMAP.md`, trabajar en incrementos pequeños y no implementar módulos excluidos sin instrucción explícita.
