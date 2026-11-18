# Life OS — Diseño de base de datos

**Estado:** línea base de datos aprobada para el MVP 0.1
**Versión:** 0.3
**Fecha:** 17 de noviembre de 2026
**Relacionado con:** `VISION.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md` y `SECURITY.md`

> Este documento define el modelo lógico del MVP. La implementación SQL concreta se realizará con SQLAlchemy 2.x y migraciones Alembic. Las tablas de dominio son la fuente de verdad; `activity_events` conserva historial complementario, no reemplaza el estado actual.

## 1. Objetivo

Conservar tareas, proyectos, notas, etiquetas, preferencias y eventos con integridad referencial, respaldo y exportación documentada. El modelo debe ser suficiente para la primera versión y permitir agregar módulos futuros sin crear anticipadamente tablas vacías.

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

No crear tablas para Work, Business, Finance, Mind, integraciones o agentes hasta que sus requisitos estén definidos.

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
- Guardar valores estables en inglés en la base; localizar etiquetas solo en interfaz.
- No almacenar valores calculables salvo que sean necesarios para preservar un evento histórico.

## 4. Relaciones

```text
projects 1 ───────── N tasks

notes N ──────────── N projects  (note_project_links)
notes N ──────────── N tasks     (note_task_links)
notes N ──────────── N tags      (note_tags)

widget_preferences  (catálogo de widgets definido en código)
user_preferences    (preferencias simples)
activity_events     (historial complementario)
```

Una nota puede tener cero vínculos y cero etiquetas. No se fuerza una clasificación. Una nota puede asociarse con varios proyectos y varias tareas, evitando duplicar contenido.

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
| `entity_type` | TEXT | `task`, `project`, `note` o `tag` cuando corresponda. |
| `entity_id` | TEXT | ID de la entidad; referencia polimórfica. |
| `occurred_at` | TEXT | Instante UTC obligatorio. |
| `metadata_json` | TEXT | Opcional; metadatos pequeños, validados y no sensibles. |
| `schema_version` | INTEGER | Versión del formato de metadatos. |

Eventos mínimos:

- `task.created`, `task.updated`, `task.completed`, `task.reopened`, `task.deleted`;
- `project.created`, `project.updated`, `project.completed`, `project.reopened`, `project.archived`, `project.restored`, `project.deleted`;
- `note.created`, `note.updated`, `note.deleted`;
- `tag.created`.

Los cambios de vínculos o etiquetas actualizan `notes.updated_at` y generan `note.updated`; los metadatos indican el tipo de cambio, nunca el cuerpo de la nota, título privado u otro contenido sensible. El evento y el cambio de dominio se confirman en una misma transacción. Los eventos son append-only desde la aplicación.

`entity_type` + `entity_id` es una referencia polimórfica y no puede implementarse como FK convencional. La lógica de aplicación valida la entidad al crear el evento. Los eventos de eliminación conservan la referencia histórica.

## 6. Integridad y eliminación

- `tasks.project_id` usa `ON DELETE RESTRICT`: no se puede eliminar físicamente un proyecto que conserve tareas.
- Archivar un proyecto es la operación preferida; no elimina ni desvincula tareas ni notas.
- Si un proyecto no tiene tareas, puede eliminarse con confirmación. Sus filas en `note_project_links` se eliminan, y las notas quedan intactas.
- Eliminar una tarea requiere confirmación; sus filas en `note_task_links` se eliminan, y las notas quedan intactas.
- Eliminar una nota elimina sus filas en `note_project_links`, `note_task_links` y `note_tags`; no elimina etiquetas compartidas.
- No hay cascadas desde Projects a Tasks.
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

Son indicadores del estado actual, no análisis de rendimiento histórico. `activity_events` prepara informes temporales futuros. No presentar métricas de hábitos, finanzas o productividad hasta que esos módulos existan y sus fórmulas estén definidas.

## 9. Exportación, backup y restauración

### 9.1 Exportación JSON

La exportación incluye `format_version`, `exported_at`, `projects`, `tasks`, `notes`, `note_project_links`, `note_task_links`, `tags`, `note_tags`, `widget_preferences`, `user_preferences` y `activity_events`. Se define de manera independiente del ORM y conserva IDs y relaciones.

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

## 13. Decisiones cerradas y límites

No quedan decisiones de modelo bloqueantes para iniciar el MVP. Se adoptan UUIDv4 texto, prioridades `low/normal/high` opcionales, proyectos `active/completed/archived`, archivado preferido y borrado restringido, notas muchos-a-muchos con proyectos y tareas, etiquetas reutilizables sin renombrado en el MVP, widgets iniciales definidos arriba y JSON como formato de exportación. La restauración de backup SQLite es documentada; la importación desde JSON queda fuera de alcance.

Cualquier cambio de este modelo requiere actualizar las pruebas, la migración y la documentación relacionada antes de implementarlo.
