# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/). Las versiones siguen [SemVer](https://semver.org/lang/es/) mientras el producto evolucione. Ambas entradas sin etiqueta `[Unreleased]` esperan release: la de Fase 7 (Life OS 0.2) sobre la de Fase 6.

## [Unreleased] — Fase 7: Habit Tracker (Life OS 0.2)

### Added

- **Módulo de hábitos:** tablas `habits` y `habit_entries` (migración `0005_habits`) con `UNIQUE(habit_id, entry_date)`, índices de consulta y `ON DELETE RESTRICT`; modalidades binaria y cuantificable (`target_value`/`target_unit`) con colores hex y categorías.
- **Frecuencias:** `daily` y `weekly_days` (0=lunes … 6=domingo, JSON en `frequency_days`) validadas en backend sobre el estado fusionado del hábito; sin motor de recurrencias.
- **API `/api/v1/habits`:** CRUD con filtros de estado/categoría y posición autoasignada; transiciones `pause`/`resume`/`archive`/`restore` idempotentes (inválidas → 409); borrado físico solo sin registros (409 con registros).
- **Registros diarios:** `POST/GET /habits/{id}/entries` con un registro por día, días futuros/no programados rechazados, corrección por `DELETE` de registro y `PATCH` por fecha sin duplicar historial; `GET /habits/today`, `GET /habits/week` y `GET /habits/{id}/calendar` con la regla de días programados en backend.
- **Métricas (DATABASE.md §8.1):** `GET /habits/stats` con racha actual, mejor racha, cumplimiento semanal/mensual y consistencia; denominadores solo con días programados y `null` → "Sin datos" cuando el denominador es cero.
- **Vista Hábitos:** registro rápido del día (hecho/omitir/cantidad/deshacer), resumen del día, tabla de métricas, calendario mensual por hábito, gestión con filtros y reordenamiento; navegación `#/habits`.
- **Widgets:** `habits_today` y `habits_week` en el catálogo (visibles por defecto) con celdas semanales por estado y leyenda; `habits` en `/analytics/summary` (activos, programados/completados/omitidos/pendientes hoy).
- **Exportación/backup:** `habits` y `habit_entries` incluidos en el JSON versionado y verificados en el respaldo.
- **Pruebas y verificación:** `tests/test_habits.py` (CRUD, validaciones, transiciones, registros, calendario, semana y métricas con datos sintéticos), tests de widgets/analytics/export actualizados; `verify_acceptance.py` ampliado a 23 checks (Fase 7 incluida) y `verify_migrations.py` con 13 tablas.

### Changed

- Catálogo de widgets de 4 a 6 entradas (`REQUIREMENTS.md` FR-HOME-02) y navegación principal con "Hábitos" (FR-APP-02).
- `AnalyticsService` ahora resume también hábitos del día local usando solo estados guardados.
- `DATABASE.md` v0.4: entidades, eventos `habit.*`, métricas §8.1, exportación §9.1 y pruebas 14–16.
- Requisitos FR-HAB-01..15 y criterios 18–20; roadmap con la Fase 7; guía de usuario con la sección Hábitos.

## [Unreleased] — Fase 6: Estabilización y aceptación del MVP 0.1

### Fixed

- **Persistencia de escrituras (crítico):** `get_db` ahora confirma la transacción al terminar cada ruta y revierte si falla. Antes, `Session.close()` descartaba todas las escrituras: la API reportaba éxito pero nada se guardaba (detectado en la aceptación de Fase 6).
- **Migraciones:** `migrations/env.py` ejecutaba un `PRAGMA` antes de `context.configure()`, lo que dejaba la conexión "en transacción" y Alembic no registraba `alembic_version` ni confirmaba las migraciones 0002–0004 en una base nueva. Las claves foráneas ya se habilitan en el evento `connect`.
- **Tests aislados de la base personal:** `conftest.py` fija `LIFEOS_DATA_DIR` a un directorio temporal antes de importar la app; antes, los tests de backup leían la base personal y dejaban copias en `%LOCALAPPDATA%\LifeOS\backups\`.
- **Home:** la navegación "Home" abre el dashboard con widgets; antes mostraba un placeholder y el dashboard quedaba inalcanzable desde la UI.
- **Widgets quick-add:** los handlers se vinculan a sus elementos; antes se acumulaban en el contenedor persistente y un clic podía crear registros duplicados tras navegar.
- **Proyectos:** acciones por estado correctas (*Completar*/*Reabrir*/*Archivar*/*Restaurar*); antes el botón de un proyecto completado decía "Archivar" pero ejecutaba reapertura.
- **Contenido como texto:** los botones de eliminar pasan solo UUIDs (el título se resuelve en el cliente); antes, comillas en títulos rompían el HTML/JS del botón.
- **Restore:** `engine.dispose()` después de reemplazar la base, para que las conexiones del pool no lean el archivo viejo.

### Added

- `GET /api/v1/notes?project_id=` y `?task_id=`: consultar las notas de un proyecto o tarea (FR-NOTE-07, criterio 6: vínculos visibles desde ambos lados).
- Tests de regresión: commit/rollback de `get_db`, persistencia con la sesión real, persistencia tras reinicio y roundtrip de `POST /api/v1/restore` (81 pruebas).
- `backend/verify_migrations.py`: verificación de instalación limpia (vacío → head → downgrade → re-upgrade con integridad y FK).
- `backend/verify_acceptance.py`: aceptación de extremo a extremo contra un servidor real (instalación, frontend, seguridad, flujos, cierre, reinicio, persistencia).
- Documentación: `GUIA_USUARIO.md`, `RECUPERACION.md`, `CHANGELOG.md`; actualización de `README.md`, `backend/README.md` y esta entrada.

### Changed

- Accesibilidad: labels asociados (`for`/`id`), `aria-label` en filtros y entradas rápidas, `aria-current="page"` en la navegación activa.
- Tema "Sistema" ahora sigue `prefers-color-scheme` del SO en tiempo real.
- Estado de error intencional en el dashboard si el servicio no responde.
- Tablas con contenedor de scroll horizontal en pantallas angostas.
- Corrección de entidades mal escapadas en vistas (`&mdash;` doblemente escapado, texto `&iacute;` en diálogos).

## [0.1.0] — Fases 1 a 5

### Added

- **Fase 1:** esqueleto FastAPI en `127.0.0.1:8000`, frontend estático en el mismo origen, `/api/v1/health` con validación de `Host`, SQLAlchemy + Alembic, pytest/HTTPX y Ruff.
- **Fase 2:** CRUD de proyectos y tareas con prioridad, vencimiento, estados, archivado, borrado restringido y eventos en la misma transacción.
- **Fase 3:** notas de texto con búsqueda, vínculos muchos-a-muchos con proyectos/tareas, etiquetas normalizadas sin duplicados y conservación de notas al borrar entidades.
- **Fase 4:** navegación Home/Proyectos/Tareas/Notas/Configuración, dashboard con cuatro widgets configurables (visibilidad y orden persistidos), tema claro/oscuro/sistema, zona horaria IANA y estados de carga/vacío/error.
- **Fase 5:** exportación JSON versionada con relaciones, backup SQLite consistente (`sqlite3.Connection.backup`), restauración con validación `integrity_check` y copia de seguridad previa, métricas básicas con fórmulas documentadas y reloj local con `zoneinfo`/`tzdata`.
