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

La base de datos SQLite se crea automáticamente en la ubicación definida por `DATABASE.md` (Windows: `%LOCALAPPDATA%\LifeOS\lifeos.db`). Se puede sobrescribir con la variable de entorno `LIFEOS_DATA_DIR` o `LIFEOS_DATABASE_URL`.

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

## Alcance de esta versión (Fase 1)

- Servidor FastAPI/Uvicorn en `127.0.0.1:8000`
- Endpoint `/api/v1/health`
- Frontend estático servido desde el mismo origen
- Configuración SQLAlchemy/Alembic con `PRAGMA foreign_keys = ON`
- Base de datos vacía (las tablas de dominio se crean en fases posteriores mediante migraciones Alembic)
- Pruebas con pytest + HTTPX
- Linting con Ruff

## Seguridad

- No exponer el servidor fuera de `127.0.0.1`.
- No cambiar `LIFEOS_HOST` a `0.0.0.0` ni abrir puertos en el firewall.
- La base de datos y los backups quedan fuera del repositorio (ver `.gitignore`).