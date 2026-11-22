"""Rutas API de Dashboard y widgets."""

from fastapi import APIRouter, Depends, HTTPException

from app.db.session import get_db
from app.modules.dashboard.repository import (
    UserPreferenceRepository,
    WidgetPreferenceRepository,
)
from app.modules.dashboard.schemas import WidgetPreferenceUpdate
from app.modules.dashboard.service import WIDGET_CATALOG, DashboardService, UserPreferenceService
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _dashboard_service(db = Depends(get_db)) -> DashboardService:
    return DashboardService(
        widget_repo=WidgetPreferenceRepository(db),
        project_repo=ProjectRepository(db),
        task_repo=TaskRepository(db),
        db=db,
    )


def _user_pref_service(db = Depends(get_db)) -> UserPreferenceService:
    return UserPreferenceService(
        pref_repo=UserPreferenceRepository(db),
        db=db,
    )


@router.get("/widgets", response_model=list[dict])
def list_widgets(service: DashboardService = Depends(_dashboard_service)):
    """Catálogo de widgets con preferencias de visibilidad y orden."""
    return service.get_widget_catalog()


@router.put("/widgets", response_model=list[dict])
def save_widgets(
    preferences: list[WidgetPreferenceUpdate],
    service: DashboardService = Depends(_dashboard_service),
):
    """Guarda visibilidad, orden y tamaño de los widgets del dashboard."""
    widget_ids = [preference.widget_id for preference in preferences]
    if len(widget_ids) != len(set(widget_ids)):
        raise HTTPException(status_code=422, detail="No se permiten widgets duplicados.")
    known_ids = {item.widget_id for item in WIDGET_CATALOG}
    unknown_ids = sorted(set(widget_ids) - known_ids)
    if unknown_ids:
        raise HTTPException(
            status_code=422,
            detail=f"Widgets desconocidos: {', '.join(unknown_ids)}.",
        )
    payload = [
        preference.model_dump(exclude_unset=True) for preference in preferences
    ]
    capture = [
        item
        for item in payload
        if item["widget_id"] in {"quick_add_task", "quick_add_note"}
    ]
    has_layout = any(
        "column_span" in item or "row_span" in item for item in capture
    )
    if len(capture) == 2 and has_layout:
        for field in ("position", "column_span", "row_span"):
            values = [item[field] for item in capture if field in item]
            if len(values) == 2 and values[0] != values[1]:
                raise HTTPException(
                    status_code=422,
                    detail="Captura rápida comparte orden y tamaño.",
                )
    return service.save_widget_preferences(payload)


@router.get("/summary", response_model=dict)
def get_summary(service: DashboardService = Depends(_dashboard_service)):
    """Resumen de Home: métricas básicas de tareas y proyectos."""
    return service.get_summary()