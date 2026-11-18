"""Rutas API de Analytics básico."""

from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.modules.analytics.service import AnalyticsService
from app.modules.habits.repository import HabitEntryRepository, HabitRepository
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _service(db = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(
        task_repo=TaskRepository(db),
        project_repo=ProjectRepository(db),
        habit_repo=HabitRepository(db),
        entry_repo=HabitEntryRepository(db),
        db=db,
    )


@router.get("/summary", response_model=dict)
def get_summary(service: AnalyticsService = Depends(_service)):
    """Métricas básicas de tareas y proyectos (FR-AN-01 a 03)."""
    return service.get_summary()
