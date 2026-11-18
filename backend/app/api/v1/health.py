"""Health check endpoint.

Returns the basic status of the process and database connectivity.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

router = APIRouter()


@router.get("/health", summary="Estado del servicio y base de datos")
def health(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Health check.

    Verifies that the API process is running and that a simple query against
    SQLite succeeds. Returns 200 when healthy.
    """
    # Verify database connectivity with a trivial query.
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "database": "sqlite",
        "database_url": settings.database_url,
    }