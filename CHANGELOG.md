# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/). Las versiones siguen [SemVer](https://semver.org/lang/es/) mientras el producto evolucione.

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
