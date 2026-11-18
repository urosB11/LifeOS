"""Rutas API de configuración de usuario."""

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.modules.dashboard.repository import UserPreferenceRepository
from app.modules.dashboard.service import UserPreferenceService

router = APIRouter(prefix="/settings", tags=["settings"])


def _service(db = Depends(get_db)) -> UserPreferenceService:
    return UserPreferenceService(
        pref_repo=UserPreferenceRepository(db),
        db=db,
    )


@router.get("/preferences", response_model=list[dict])
def list_preferences(service: UserPreferenceService = Depends(_service)):
    """Lista todas las preferencias de usuario."""
    return service.list_all()


@router.put("/preferences/{key}", response_model=dict)
def set_preference(
    key: str,
    value: dict,
    service: UserPreferenceService = Depends(_service),
):
    """Establece una preferencia de usuario (tema, zona horaria, etc.)."""
    val = value.get("value", "")
    service.set(key, val)
    return {"key": key, "value": val}


@router.get("/theme", response_model=dict)
def get_theme(service: UserPreferenceService = Depends(_service)):
    """Obtiene el tema actual (system, light, dark)."""
    theme = service.get("theme")
    return {"theme": theme or "system"}


@router.put("/theme", response_model=dict)
def set_theme(
    body: dict,
    service: UserPreferenceService = Depends(_service),
):
    """Establece el tema (system, light, dark)."""
    theme = body.get("theme", "")
    if theme not in ("system", "light", "dark"):
        raise HTTPException(status_code=400, detail="Tema inválido")
    service.set("theme", theme)
    return {"theme": theme}


@router.get("/timezone", response_model=dict)
def get_timezone(service: UserPreferenceService = Depends(_service)):
    """Obtiene la zona horaria actual."""
    tz = service.get("timezone")
    return {"timezone": tz or "America/Argentina/Cordoba"}


@router.put("/timezone", response_model=dict)
def set_timezone(
    body: dict,
    service: UserPreferenceService = Depends(_service),
):
    """Establece la zona horaria."""
    tz = body.get("timezone", "")
    if not tz:
        raise HTTPException(status_code=400, detail="Zona horaria inválida")
    service.set("timezone", tz)
    return {"timezone": tz}