"""Life OS FastAPI application.

Serves the frontend static files and the REST API under /api/v1 on the same
origin, avoiding CORS. The server binds only to 127.0.0.1:8000 by default
(SECURITY.md).
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import (
    analytics,
    backup,
    dashboard,
    export,
    health,
    notes,
    projects,
    tasks,
)
from app.api.v1 import settings as settings_api
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=None,  # Disable Swagger UI in MVP (no public API docs needed)
    redoc_url=None,
)

# --- API routes -----------------------------------------------------------
app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(tasks.router, prefix=settings.api_v1_prefix)
app.include_router(notes.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(settings_api.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(export.router, prefix=settings.api_v1_prefix)
app.include_router(backup.router, prefix=settings.api_v1_prefix)

# --- Frontend static files (same origin, no CORS) ------------------------
_frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if _frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_frontend_dir), html=True),
        name="frontend",
    )


# --- Security: validate Host header (SECURITY.md section 3) --------------
@app.middleware("http")
async def validate_host(request: Request, call_next):
    host = request.headers.get("host", "")
    if host and host not in settings.allowed_hosts:
        return JSONResponse(
            status_code=400,
            content={"detail": "Host no permitido"},
        )
    response = await call_next(request)
    return response


__all__ = ["app"]