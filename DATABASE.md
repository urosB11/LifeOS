# Life OS — Diseño de base de datos

**Estado:** línea base de datos del MVP 0.1, Fase 7 (Hábitos) y MIND-002 (Mind core)
**Versión:** 0.5
**Fecha:** 22 de noviembre de 2026
**Relacionado con:** `VISION.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `SECURITY.md`, `docs/factory/work/MIND-002/SPEC.md`

> Este documento define el modelo lógico del MVP. La implementación SQL concreta se realizará con SQLAlchemy 2.x y migraciones Alembic. Las tablas de dominio son la fuente de verdad; `activity_events` conserva historial complementario, no reemplaza el estado actual.

## 1. Objetivo

Conservar tareas, proyectos, notas, etiquetas, hábitos, sus registros diarios, preferencias y eventos con integridad referencial, respaldo y exportación documentada. El modelo debe ser suficiente para la primera versión y permitir agregar módulos futuros sin crear anticipadamente tablas vacías.

## 2. Entidades

| Tabla | Propósito |
|---|---|
| `projects` | Proyectos y su ciclo de vida. |
| `tasks` | Tareas, con proyecto opcional. |
| `notes` | Notas de texto independientes o vinculadas. |
| `note_project_links` | Relación muchos-a-muchos nota/proyecto. |
| `note_task_links` | Relación muchos-a-muchos nota/tarea. |
| `tags` | Catálogo compartido de etiquetas. |
| `note_tags` | Asignaciones muchos-a-muchos nota/etiqueta. |
| `widget_preferences` | Visibilidad y orden de widgets. |
| `user_preferences` | Preferencias básicas de la instalación. |
| `activity_events` | Historial de cambios relevantes. |
| `habits` | Hábitos con frecuencia, estado y objetivo opcional (Fase 7). |
| `habit_entries` | Registro diario de un hábito por fecha (Fase 7). |
| `mind_spaces` | Contextos de trabajo de Mind y el Inbox único (MIND-002). |
| `mind_canvases` | Superficies visuales dentro de un Space (MIND-002). |
| `mind_space_notes` | Membresía de una Note en un Space (capturas del Inbox). |
| `mind_canvas_nodes` | Instancia visual de una Note sobre un Canvas (posición y tamaño). |

No crear tablas para Work, Business, Finance, integraciones o agentes hasta que sus requisitos estén definidos. Mind (MIND-002) cubre Spaces, Inbox, Canvases y Cards simples con su propio modelo; las relaciones semánticas, los documentos por bloques y los Orbes siguen sin tablas hasta que exista su SPEC.

## 3. Convenciones

### 3.1 Identificadores

Usar UUIDv4 como identificador de las entidades de dominio, almacenado como texto canónico de 36 caracteres (`TEXT`). Python genera los UUID mediante su biblioteca estándar. Los IDs son estables para exportación/importación futura y no dependen del orden de inserción.

Las tablas de unión usan claves primarias compuestas cuando corresponde. `widget_preferences.widget_id` y `user_preferences.key` son claves naturales estables.

### 3.2 Fechas y horas

- Instantes: UTC en ISO 8601 normalizado, con `Z` final.
- Fechas de vencimiento: `YYYY-MM-DD` de calendario local, sin conversión UTC.
- Zona horaria inicial de presentación: `America/Argentina/Cordoba`, configurable.
- Usar `created_at`, `updated_at`, `completed_at` y `archived_at` cuando correspondan.
- Los timestamps deben generarse en backend, no confiarse al reloj del navegador.

### 3.3 Valores controlados

- Task status: `pending`, `completed`.
- Task priority: `low`, `normal`, `high` o `NULL` si no se asignó.
- Project status: `active`, `completed`, `archived`.
- Habit status: `active`, `paused`, `archived`.
- Habit frequency type: `daily`, `weekly_days`.
- Habit entry status: `pending`, `completed`, `skipped`.
- Mind space status: `active`, `archived`.
- Mind canvas status: `active`, `archived`.
- Guardar valores estables en inglés en la base; localizar etiquetas solo en interfaz.
- No almacenar valores calculables salvo que sean necesarios para preservar un evento histórico.

## 4. Relaciones

```text
projects 1 ───────── N tasks

notes N ──────────── N projects  (note_project_links)
notes N ──────────── N tasks     (note_task_links)
notes N ──────────── N tags      (note_tags)

habits 1 ─────────── N habit_entries

mind_spaces 1 ─────── N mind_canvases
mind_spaces N ──────── N notes      (mind_space_notes)
mind_canvases N ────── N notes      (mind_canvas_nodes)

widget_preferences  (catálogo de widgets definido en código)
user_preferences    (preferencias simples)
activity_events     (historial complementario)
```

Una nota puede tener cero vínculos y cero etiquetas. No se fuerza una clasificación. Una nota puede asociarse con varios proyectos y varias tareas, evitando duplicar contenido. Un hábito puede tener cero registros (aún no se registró ningún día). En Mind, una misma Note puede ser miembro de varios Spaces y representarse en varios Canvases: el contenido canónico nunca se duplica.

## 5. Tablas

Los tipos son lógicos; la migración definirá las columnas SQLAlchemy y las restricciones concretas.

### 5.1 `projects`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `name` | TEXT | Obligatorio, no vacío después de normalizar espacios. |
| `description` | TEXT | Opcional. |
| `status` | TEXT | `active`, `completed` o `archived`; default `active`. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |
| `completed_at` | TEXT | Nullable; momento en que pasó a completado. |
| `archived_at` | TEXT | Nullable; momento en que se archivó. |

Al reabrir un proyecto completado se vuelve a `active` y se limpia `completed_at`. Al archivar se establece `archived_at`; al restaurar se vuelve a `active` y se limpia `archived_at`.

### 5.2 `tasks`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `project_id` | TEXT | FK nullable a `projects.id`, `ON DELETE RESTRICT`. |
| `title` | TEXT | Obligatorio, no vacío. |
| `description` | TEXT | Opcional. |
| `status` | TEXT | `pending` o `completed`; default `pending`. |
| `priority` | TEXT | Nullable; `low`, `normal`, `high`. |
| `due_date` | TEXT | Nullable; `YYYY-MM-DD`. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |
| `completed_at` | TEXT | Nullable. |

Completar establece `completed_at`; reabrir limpia el valor actual, sin borrar el evento histórico. Una tarea asociada a un proyecto completado puede seguir consultándose y editándose; completar o reabrir una tarea no cambia automáticamente el estado del proyecto.

### 5.3 `notes`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `title` | TEXT | Obligatorio, no vacío. |
| `content` | TEXT | Texto plano; puede estar vacío. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Las notas no tienen una FK directa a proyectos o tareas. Sus relaciones se almacenan en tablas de unión. La búsqueda inicial es por coincidencia parcial en título y contenido, sin FTS ni búsqueda semántica.

### 5.4 `note_project_links`

| Campo | Tipo | Regla |
|---|---|---|
| `note_id` | TEXT | FK a `notes.id`, parte de PK compuesta. |
| `project_id` | TEXT | FK a `projects.id`, parte de PK compuesta. |
| `created_at` | TEXT | Instante UTC obligatorio. |

PK compuesta (`note_id`, `project_id`) para evitar duplicados. La eliminación de una nota o proyecto elimina la fila de vínculo mediante cascada, pero nunca elimina el contenido de la otra entidad.

### 5.5 `note_task_links`

| Campo | Tipo | Regla |
|---|---|---|
| `note_id` | TEXT | FK a `notes.id`, parte de PK compuesta. |
| `task_id` | TEXT | FK a `tasks.id`, parte de PK compuesta. |
| `created_at` | TEXT | Instante UTC obligatorio. |

PK compuesta (`note_id`, `task_id`). La eliminación de una nota o tarea elimina únicamente la fila de vínculo. La nota permanece si se elimina la tarea.

### 5.6 `tags`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `name` | TEXT | Nombre visible obligatorio. |
| `normalized_name` | TEXT | Nombre normalizado, UNIQUE. |
| `created_at` | TEXT | Instante UTC obligatorio. |

Normalización: eliminar espacios externos, colapsar secuencias de espacios, normalizar Unicode y aplicar `casefold` para comparar sin distinguir mayúsculas/minúsculas. Se conserva en `name` la primera forma visible introducida. En el MVP no se requiere renombrar ni eliminar etiquetas desde la interfaz; pueden reutilizarse en distintas notas.

### 5.7 `note_tags`

| Campo | Tipo | Regla |
|---|---|---|
| `note_id` | TEXT | FK a `notes.id`, parte de PK compuesta. |
| `tag_id` | TEXT | FK a `tags.id`, parte de PK compuesta. |
| `created_at` | TEXT | Instante UTC obligatorio. |

PK compuesta (`note_id`, `tag_id`). Eliminar una nota elimina sus asignaciones, no el registro compartido de la etiqueta. Quitar una etiqueta de una nota no elimina ni la nota ni la etiqueta.

### 5.8 `widget_preferences`

| Campo | Tipo | Regla |
|---|---|---|
| `widget_id` | TEXT | PK; ID estable del catálogo en código. |
| `is_visible` | INTEGER/BOOLEAN | Obligatorio. |
| `position` | INTEGER | Obligatorio, no negativo. |
| `config_json` | TEXT | Nullable; solo opciones validadas del widget. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

IDs del catálogo MVP: `upcoming_tasks`, `active_projects`, `quick_add_task`, `quick_add_note`. El orden inicial sigue ese orden. Si no existe preferencia guardada, se utilizan los defaults del catálogo.

### 5.9 `user_preferences`

| Campo | Tipo | Regla |
|---|---|---|
| `key` | TEXT | PK. |
| `value` | TEXT | Valor serializado y documentado. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Preferencias iniciales posibles: `timezone` y `theme` (`system`, `light`, `dark`). No guardar contraseñas, tokens, claves API ni rutas a secretos.

### 5.10 `activity_events`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `event_type` | TEXT | Tipo estable y documentado. |
| `entity_type` | TEXT | `task`, `project`, `note`, `tag` o `habit` cuando corresponda. |
| `entity_id` | TEXT | ID de la entidad; referencia polimórfica. |
| `occurred_at` | TEXT | Instante UTC obligatorio. |
| `metadata_json` | TEXT | Opcional; metadatos pequeños, validados y no sensibles. |
| `schema_version` | INTEGER | Versión del formato de metadatos. |

Eventos mínimos:

- `task.created`, `task.updated`, `task.completed`, `task.reopened`, `task.deleted`;
- `project.created`, `project.updated`, `project.completed`, `project.reopened`, `project.archived`, `project.restored`, `project.deleted`;
- `note.created`, `note.updated`, `note.deleted`;
- `tag.created`;
- `habit.created`, `habit.updated`, `habit.status_changed`, `habit.entry_created`, `habit.entry_updated`.

Los cambios de vínculos o etiquetas actualizan `notes.updated_at` y generan `note.updated`; los metadatos indican el tipo de cambio, nunca el cuerpo de la nota, título privado u otro contenido sensible. El evento y el cambio de dominio se confirman en una misma transacción. Los eventos son append-only desde la aplicación.

`entity_type` + `entity_id` es una referencia polimórfica y no puede implementarse como FK convencional. La lógica de aplicación valida la entidad al crear el evento. Los eventos de eliminación conservan la referencia histórica.

### 5.11 `habits`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `name` | TEXT | Obligatorio, no vacío después de normalizar espacios. |
| `description` | TEXT | Opcional. |
| `category` | TEXT | Opcional; clasificación libre (ej. "Salud"). |
| `color` | TEXT | Nullable; color del sistema (hex o token) para la tarjeta. |
| `frequency_type` | TEXT | `daily` o `weekly_days`; default `daily`. |
| `frequency_days` | TEXT | Nullable; JSON con la lista de días `0-6` (0=lunes … 6=domingo) solo para `weekly_days`. `NULL` en `daily`. |
| `start_date` | TEXT | `YYYY-MM-DD` local obligatorio; días anteriores no son programados. |
| `target_value` | REAL | Nullable; objetivo numérico (hábito cuantificable). `NULL` = binario. |
| `target_unit` | TEXT | Nullable; unidad del objetivo ("km", "paginas", "min"). |
| `status` | TEXT | `active`, `paused` o `archived`; default `active`. |
| `position` | INTEGER | Orden personalizable, no negativo. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

`frequency_days` es JSON porque SQLite no tiene arrays; la validación de formato y de rango 0-6 ocurre en backend. Los hábitos no se eliminan físicamente mientras tengan registros (se archivan); eliminar un hábito sin registros requiere confirmación, igual que proyectos. El progreso del día se determina por los días programados según la frecuencia vigente **y** `start_date`: no se recalculan los días ya pasados cuando cambia la frecuencia.

### 5.12 `habit_entries`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `habit_id` | TEXT | FK a `habits.id`, `ON DELETE RESTRICT`. |
| `entry_date` | TEXT | `YYYY-MM-DD` local obligatorio. |
| `value` | REAL | Nullable; cantidad registrada (hábitos cuantificables). |
| `status` | TEXT | `pending`, `completed` o `skipped`; default `pending`. |
| `note` | TEXT | Nullable; texto breve del registro. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Restricción `UNIQUE(habit_id, entry_date)`: un solo registro por hábito y fecha. `status` es la única fuente de verdad del cumplimiento; `value` es dato y no recalcula el estado almacenado (se deriva el estado únicamente al escribir). Semántica de un día para un hábito:

- **programado**: aplica ese día según `frequency_type`, `frequency_days` y `start_date`;
- **no programado**: no aplica; no cuenta como pendiente;
- **no registrado**: programado sin fila en `habit_entries`; cuenta como pendiente;
- **omitido**: fila con `status = skipped`.

Los registros existentes se conservan con su fecha y estado aunque después cambie la frecuencia o la configuración del hábito.

### 5.13 `mind_spaces`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `name` | TEXT | Obligatorio, no vacío después de normalizar espacios. |
| `description` | TEXT | Opcional. |
| `is_inbox` | INTEGER | Boolean; `1` marca el Inbox único de la instalación. |
| `status` | TEXT | `active` o `archived`; default `active`. |
| `archived_at` | TEXT | Nullable; instante del archivado. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Restricción `UNIQUE` parcial sobre `is_inbox` con predicado `is_inbox = 1`: la base admite como máximo un Inbox. La existencia se garantiza en el servicio (`ensure_inbox`, idempotente y transaccional) en el bootstrap de cada petición de Mind. El Inbox no se renombra, archiva ni elimina desde la interfaz; archivarlo está prohibido también en el servicio.

### 5.14 `mind_canvases`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `space_id` | TEXT | FK a `mind_spaces.id`, `ON DELETE CASCADE`. |
| `title` | TEXT | Obligatorio, no vacío después de normalizar espacios. |
| `description` | TEXT | Opcional. |
| `status` | TEXT | `active` o `archived`; default `active`. |
| `archived_at` | TEXT | Nullable; instante del archivado. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Un Canvas archivado conserva sus nodos y el contenido de las Notes referenciadas. No existe borrado físico de Canvases en MIND-002: el archivado es la operación preferida.

### 5.15 `mind_space_notes`

| Campo | Tipo | Regla |
|---|---|---|
| `space_id` | TEXT | PK (compuesta), FK a `mind_spaces.id`, `ON DELETE CASCADE`. |
| `note_id` | TEXT | PK (compuesta), FK a `notes.id`, `ON DELETE CASCADE`. |
| `created_at` | TEXT | Instante UTC obligatorio. |

Membresía Note↔Space. Las capturas del Inbox son Notes con una fila en esta tabla. Eliminar la Note elimina su membresía y sus referencias visuales; eliminar o mover un Space nunca borra Notes.

### 5.16 `mind_canvas_nodes`

| Campo | Tipo | Regla |
|---|---|---|
| `id` | TEXT | PK UUIDv4. |
| `canvas_id` | TEXT | FK a `mind_canvases.id`, `ON DELETE CASCADE`. |
| `note_id` | TEXT | FK a `notes.id`, `ON DELETE CASCADE`. |
| `x` | REAL | Coordenada X en el mundo; independiente del viewport y del zoom. |
| `y` | REAL | Coordenada Y en el mundo; independiente del viewport y del zoom. |
| `width` | REAL | Nullable; tamaño inicial. `NULL` = tamaño por defecto. |
| `height` | REAL | Nullable; tamaño inicial. `NULL` = tamaño por defecto. |
| `z_index` | INTEGER | Orden visual, no negativo. |
| `created_at` | TEXT | Instante UTC obligatorio. |
| `updated_at` | TEXT | Instante UTC obligatorio. |

Restricción `UNIQUE(canvas_id, note_id)`: una Note tiene como máximo una representación por Canvas, pero puede representarse en varios Canvases. El nodo guarda solo la instancia visual; el texto vive en `notes`. Quitar un nodo no elimina la Note; eliminar la Note elimina sus nodos (`ON DELETE CASCADE`).

## 6. Integridad y eliminación

- `tasks.project_id` usa `ON DELETE RESTRICT`: no se puede eliminar físicamente un proyecto que conserve tareas.
- Archivar un proyecto es la operación preferida; no elimina ni desvincula tareas ni notas.
- Si un proyecto no tiene tareas, puede eliminarse con confirmación. Sus filas en `note_project_links` se eliminan, y las notas quedan intactas.
- Eliminar una tarea requiere confirmación; sus filas en `note_task_links` se eliminan, y las notas quedan intactas.
- Eliminar una nota elimina sus filas en `note_project_links`, `note_task_links` y `note_tags`; no elimina etiquetas compartidas.
- `habit_entries.habit_id` usa `ON DELETE RESTRICT`: no se puede eliminar físicamente un hábito que conserve registros; archivar es la operación preferida.
- `mind_spaces.is_inbox` tiene un índice único parcial: la BD no admite un segundo Inbox.
- `mind_canvases.space_id`, `mind_space_notes.space_id` y `mind_space_notes.note_id` usan `ON DELETE CASCADE`; `mind_canvas_nodes.canvas_id` y `mind_canvas_nodes.note_id` también.
- Eliminar una Note elimina sus membresías en Spaces y sus representaciones visuales: no quedan referencias Mind huérfanas.
- Archivar un Space o un Canvas no elimina contenido canónico ni Canvases; restaurarlos es la operación inversa.
- Eliminar o mover un Space nunca borra Notes.
- No hay cascadas desde Projects a Tasks ni desde Habits a HabitEntries.
- Activar `PRAGMA foreign_keys = ON` por cada conexión SQLite.
- Las operaciones relacionadas y el evento correspondiente forman una única transacción.

## 7. Índices

Crear índices para consultas reales del MVP:

- `tasks(status)`, `tasks(due_date)`, `tasks(project_id)`;
- `projects(status)`;
- `notes(updated_at)`;
- `note_project_links(project_id)`, `note_task_links(task_id)`;
- `tags(normalized_name)` UNIQUE;
- `note_tags(tag_id)`;
- `habits(status)`, `habits(start_date)`, `habits(position)`;
- `habit_entries(habit_id, entry_date)` y `habit_entries(entry_date)`;
- `habit_entries UNIQUE(habit_id, entry_date)` (restricción, no índice adicional);
- `mind_spaces(status)`;
- `mind_spaces UNIQUE` parcial sobre `is_inbox` con predicado `is_inbox = 1`;
- `mind_canvases(space_id)`, `mind_canvases(status)`;
- `mind_space_notes(note_id)` (la PK compuesta ya cubre `space_id`);
- `mind_canvas_nodes(canvas_id)`, `mind_canvas_nodes(note_id)`;
- `mind_canvas_nodes UNIQUE(canvas_id, note_id)` (restricción, no índice adicional);
- `activity_events(entity_type, entity_id, occurred_at)`;
- `activity_events(event_type, occurred_at)`.

La migración debe evitar índices duplicados ya creados por restricciones o claves primarias.

## 8. Métricas básicas

Las métricas del MVP se calculan en consultas; no se guardan agregados duplicados.

| Métrica | Fórmula / regla | Fuente |
|---|---|---|
| Pendientes | Conteo de tasks con `status = pending`. | `tasks` |
| Completadas | Conteo de tasks con `status = completed`. | `tasks` |
| Vencidas | Tareas `pending` con `due_date` anterior a la fecha local actual. | `tasks` + zona horaria |
| Proyectos activos | Conteo de projects con `status = active`. | `projects` |
| Avance de proyecto | `completed tasks / all tasks * 100`; si total es cero, mostrar “Sin tareas”. | `tasks` |

Son indicadores del estado actual, no análisis de rendimiento histórico. `activity_events` prepara informes temporales futuros. No presentar métricas de finanzas u otras áreas hasta que sus módulos existan y sus fórmulas estén definidas.

### 8.1 Métricas de hábitos (Fase 7)

Se calculan en consultas desde `habits` + `habit_entries`; no se guardan agregados. El período se determina con la zona horaria del usuario (fechas de calendario local) y **solo cuentan los días programados** como denominador:

| Métrica | Fórmula / regla | Denominador y tratamiento de faltantes |
|---|---|---|
| Racha actual | Mayor cantidad de días consecutivos con `status = completed` que termina en el día local actual. | Si hoy no está completado (y es programado), la racha es 0. Días no programados no interrumpen la racha. |
| Mejor racha | Mayor cantidad de días consecutivos con `status = completed` en todo el historial. | Igual tratamiento de días no programados. |
| Cumplimiento semanal | `entradas completed en la semana / días programados en la semana * 100`. | Semana = lunes a domingo local. Días programados sin entrada cuentan en el denominador y no en el numerador. |
| Cumplimiento mensual | `entradas completed en el mes / días programados en el mes * 100`. | Mes calendario local. Mismo tratamiento. |
| Consistencia | `entradas (completed + skipped) / días programados * 100` en el período. | Incluye omitidos como registrados; los no registrados restan. |
| Progreso vs objetivo | `value / target_value` por día; se considera completado al registrar `value >= target_value`. | Solo hábitos con `target_value`; si no hay objetivo, se usa `status` directamente. |

Si el denominador es cero (sin días programados en el período), mostrar “Sin datos” y no 0 %. Los días no programados no entran en ningún denominador. `status = completed` de la entrada es siempre la fuente de verdad; ninguna métrica lo recalcula.

## 9. Exportación, backup y restauración

### 9.1 Exportación JSON

La exportación incluye `format_version`, `exported_at`, `projects`, `tasks`, `notes`, `note_project_links`, `note_task_links`, `tags`, `note_tags`, `habits`, `habit_entries`, `mind_spaces`, `mind_canvases`, `mind_space_notes`, `mind_canvas_nodes`, `widget_preferences`, `user_preferences` y `activity_events`. Se define de manera independiente del ORM y conserva IDs y relaciones.

No se implementa importación de JSON desde la interfaz en el MVP.

### 9.2 Backup SQLite

Generar la copia con la API de backup de SQLite (`sqlite3.Connection.backup`) o mecanismo equivalente que garantice una copia consistente, no mediante copia directa del archivo mientras hay escrituras activas. Guardar fuera del repositorio.

### 9.3 Restauración

Antes de restaurar, crear una copia adicional de la base actual. Validar que el backup se abre y pasa `PRAGMA integrity_check`; detener el servidor; reemplazar la base mediante procedimiento controlado; iniciar la aplicación y comprobar migraciones e integridad. La restauración debe documentarse y probarse con una base temporal.

## 10. Migraciones

SQLAlchemy 2.x gestiona modelos y sesiones; Alembic gestiona cambios versionados de esquema. Cada cambio de esquema requiere migración, pruebas sobre base temporal y actualización de este documento. No usar `create_all()` como sustituto de migraciones en entornos con datos existentes.

## 11. Ubicación de la base

- Windows: `%LOCALAPPDATA%\LifeOS\lifeos.db`.
- Linux: `$XDG_DATA_HOME/life-os/lifeos.db` o `~/.local/share/life-os/lifeos.db`.
- macOS: `~/Library/Application Support/LifeOS/lifeos.db`.
- `LIFEOS_DATA_DIR` permite definir una ubicación alternativa.
- `data/`, `backups/`, `*.db`, `*.sqlite*` y exportaciones reales quedan fuera de Git.

La aplicación crea el directorio si no existe e informa errores de permisos o espacio.

## 12. Pruebas mínimas

1. CRUD de tareas, proyectos, notas y etiquetas.
2. Valores de estado y prioridad rechazando valores desconocidos.
3. Vínculos múltiples y ausencia de duplicados en tablas de relación.
4. Eliminación restringida de proyecto con tareas.
5. Conservación de notas al eliminar proyectos/tareas.
6. Limpieza de relaciones al eliminar nota, proyecto o tarea.
7. Normalización de etiquetas y prevención de duplicados Unicode/case-insensitive.
8. Persistencia de widgets y preferencias.
9. Atomicidad entre cambios de dominio y eventos.
10. Fórmulas analíticas con datos sintéticos conocidos.
11. Exportación JSON conservando IDs y relaciones.
12. Backup y restauración en entorno de prueba.
13. Migración desde base vacía y desde una versión previa de prueba.
14. CRUD de hábitos y transiciones `active`/`paused`/`archived`.
15. Único registro por hábito y fecha; corrección de registros; conservación del historial ante cambios de frecuencia.
16. Rachas, cumplimiento y consistencia con datos sintéticos conocidos (fórmulas de la sección 8.1).
17. Inbox único: la BD rechaza un segundo `is_inbox = 1` y el servicio lo crea de forma idempotente.
18. Spaces y Canvases: crear, renombrar, archivar y restaurar sin perder Canvases ni contenido.
19. Cards: crear, editar por el API canónico de Notes, mover (posición persistida) y quitar sin borrar la Note.
20. Eliminar una Note elimina sus membresías y nodos, sin dejar referencias Mind huérfanas.
21. Exportación JSON, backup y restauración con los datos de Mind, conservando IDs y referencias.

## 13. Decisiones cerradas y límites

No quedan decisiones de modelo bloqueantes para iniciar el MVP. Se adoptan UUIDv4 texto, prioridades `low/normal/high` opcionales, proyectos `active/completed/archived`, archivado preferido y borrado restringido, notas muchos-a-muchos con proyectos y tareas, etiquetas reutilizables sin renombrado en el MVP, widgets iniciales definidos arriba y JSON como formato de exportación. La restauración de backup SQLite es documentada; la importación desde JSON queda fuera de alcance.

Cualquier cambio de este modelo requiere actualizar las pruebas, la migración y la documentación relacionada antes de implementarlo.

### 13.1 Decisiones de Mind (MIND-002)

- El contenido canónico de una Card es una Note: Mind no duplica ni copia texto.
- La instancia visual (posición, tamaño y orden) vive en `mind_canvas_nodes`; quitar el nodo no borra la Note.
- El Inbox es un Space reservado con `is_inbox = 1` y un índice único parcial que garantiza su unicidad en la base.
- Las coordenadas de las Cards son del mundo, no del viewport: el mismo Canvas se abre igual en distintas pantallas.
- No hay borrado físico de Spaces ni Canvases en esta entrega: el archivado es la operación preferida y reversible.
- No existen tablas de conexiones entre Cards, relaciones semánticas ni documentos por bloques: corresponden a MIND-003 y MIND-004.
