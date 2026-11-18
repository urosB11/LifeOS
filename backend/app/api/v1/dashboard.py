"""Rutas API de Dashboard y widgets."""

from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.modules.dashboard.repository import (
    UserPreferenceRepository,
    WidgetPreferenceRepository,
)
from app.modules.dashboard.service import DashboardService, UserPreferenceService
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
    preferences: list[dict],
    service: DashboardService = Depends(_dashboard_service),
):
    """Guarda visibilidad y orden de los widgets del dashboard."""
    return service.save_widget_preferences(preferences)


@router.get("/summary", response_model=dict)
def get_summary(service: DashboardService = Depends(_dashboard_service)):
    """Resumen de Home: métricas básicas de tareas y proyectos."""
    return service.get_summary()