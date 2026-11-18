"""Servicio de Analytics básico.

Calcula métricas deterministas desde datos operativos. No almacena agregados
duplicados ni usa event sourcing: activity_events es historial complementario,
no fuente de verdad (ARCHITECTURE.md sección 8, DATABASE.md sección 8).
"""

from __future__ import annotations

from typing import Any

from app.core.clock import local_today
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository


class AnalyticsService:
    """Indicadores básicos de tareas y proyectos."""

    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        db,
    ):
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.db = db

    def get_summary(self) -> dict[str, Any]:
        """Resumen de métricas básicas (FR-AN-01 a 03)."""
        pending = self.task_repo.count(status="pending")
        completed = self.task_repo.count(status="completed")
        overdue = self.task_repo.count_overdue()
        active_projects = self.project_repo.count_by_status("active")

        return {
            "format_version": 1,
            "calculated_at_local": local_today(self.db).isoformat(),
            "tasks": {
                "pending": pending,
                "completed": completed,
                "overdue": overdue,
            },
            "projects": {
                "active": active_projects,
            },
        }
