# Backend — Life OS

Backend de Life OS: FastAPI + SQLAlchemy 2.x (síncrono) + SQLite + Alembic, sirviendo la API bajo `/api/v1` y el frontend estático en el mismo origen.

## Requisitos

- Python 3.11+
- No se requiere Node.js para ejecutar la aplicación.

## Instalación

Desde la carpeta `backend/`:

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activarlo
.venv\Scripts\Activate.ps1

# 3. Instalar dependencias (incluyendo las de desarrollo)
pip install -e ".[dev]"
```

## Ejecución

```powershell
# Desde la carpeta backend/
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

La aplicación escucha exclusivamente en `127.0.0.1:8000` (loopback). Abre el navegador en `http://127.0.0.1:8000/`.

La base de datos SQLite vive en la ubicación definida por `DATABASE.md` (Windows: `%LOCALAPPDATA%\LifeOS\lifeos.db`) y se puede sobrescribir con `LIFEOS_DATA_DIR` o `LIFEOS_DATABASE_URL`. **En el primer inicio** (o al actualizar el esquema) ejecuta antes las migraciones:

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
```

## Pruebas

```powershell
# Ejecutar todas las pruebas
.venv\Scripts\pytest -v

# Ejecutar con reporte de cobertura (si se desea)
.venv\Scripts\pytest -v --cov=app
```

Las pruebas usan una base de datos temporal (nunca la base personal del usuario).

## Linting

```powershell
.venv\Scripts\ruff check app tests
```

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `LIFEOS_HOST` | `127.0.0.1` | Host de enlace (solo loopback) |
| `LIFEOS_PORT` | `8000` | Puerto del servidor |
| `LIFEOS_DATA_DIR` | (ver DATABASE.md §11) | Directorio de datos de la aplicación |
| `LIFEOS_DATABASE_URL` | `sqlite:///<data_dir>/lifeos.db` | URL de SQLAlchemy para la base de datos |
| `LIFEOS_ALLOWED_HOSTS` | `127.0.0.1:8000,localhost:8000` | Hosts permitidos en el encabezado `Host` |

## Migraciones (Alembic)

Las tablas de dominio se crean y evolucionan con migraciones versionadas en `backend/migrations/`:

```powershell
# Base nueva: crear todo el esquema
.venv\Scripts\python.exe -m alembic upgrade head

# Ver revisiones aplicadas
.venv\Scripts\python.exe -m alembic current

# Última revisión disponible
.venv\Scripts\python.exe -m alembic heads
```

`alembic.ini` no fija la URL: `migrations/env.py` lee la misma configuración que la aplicación (`LIFEOS_DATABASE_URL` o `LIFEOS_DATA_DIR`), por lo que migrar y ejecutar usan la misma base (DATABASE.md §11).

## Scripts de verificación

| Script | Qué verifica |
|---|---|
| `verify_migrations.py` | Instalación limpia: base vacía → head, downgrade a `0001`, re-upgrade, `integrity_check` y `foreign_key_check`, con datos sintéticos en una base temporal. |
| `verify_acceptance.py` | Aceptación de extremo a extremo contra un servidor Uvicorn real: instalación limpia, primer inicio, frontend estático, rechazo de Host no permitido, flujos críticos, cierre, reinicio y persistencia. Usa un directorio temporal (`LIFEOS_DATA_DIR`), nunca la base personal. |

```powershell
.venv\Scripts\python.exe verify_migrations.py
.venv\Scripts\python.exe verify_acceptance.py
```

## Alcance de esta versión (Fases 1–6)

- Servidor FastAPI/Uvicorn en `127.0.0.1:8000` con frontend estático en el mismo origen.
- Módulos: proyectos, tareas, notas, etiquetas, dashboard configurable, preferencias (tema/zona horaria), métricas básicas (`/analytics/summary`).
- Exportación JSON versionada (`GET /api/v1/export`), backup SQLite (`GET/POST /api/v1/backup`) y restauración (`POST /api/v1/restore` con cuerpo raw `application/octet-stream`).
- Migraciones Alembic (4 revisiones: `0001`…`0004`).
- `GET /api/v1/health` con validación de header `Host`.
- Pruebas con pytest + HTTPX (81 pruebas) y linting con Ruff.
- Frontera de transacción: `get_db` confirma al terminar la ruta y revierte si falla (DATABASE.md §6).

## Seguridad

- No exponer el servidor fuera de `127.0.0.1`.
- No cambiar `LIFEOS_HOST` a `0.0.0.0` ni abrir puertos en el firewall.
- La base de datos y los backups quedan fuera del repositorio (ver `.gitignore`).
- Los tests fijan `LIFEOS_DATA_DIR` a un directorio temporal: nunca tocan la base personal (AGENTS.md §5).