"""Servicio de Analytics básico.

Calcula métricas deterministas desde datos operativos. No almacena agregados
duplicados ni usa event sourcing: activity_events es historial complementario,
no fuente de verdad (ARCHITECTURE.md sección 8, DATABASE.md sección 8).
"""

from __future__ import annotations

from typing import Any

from app.core.clock import local_today
from app.modules.habits import scheduling
from app.modules.habits.repository import HabitEntryRepository, HabitRepository
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository


class AnalyticsService:
    """Indicadores básicos de tareas, proyectos y hábitos."""

    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        habit_repo: HabitRepository,
        entry_repo: HabitEntryRepository,
        db,
    ):
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.habit_repo = habit_repo
        self.entry_repo = entry_repo
        self.db = db

    def _habits_summary(self) -> dict[str, Any]:
        """Hábitos del día local: solo estados guardados, sin recalcular."""
        today = local_today(self.db)
        active = self.habit_repo.list(status="active")
        scheduled = [h for h in active if scheduling.is_scheduled(h, today)]
        entries = self.entry_repo.get_for_date(
            [h.id for h in scheduled], today.isoformat()
        )
        completed = sum(1 for e in entries.values() if e.status == "completed")
        skipped = sum(1 for e in entries.values() if e.status == "skipped")
        return {
            "active": len(active),
            "scheduled_today": len(scheduled),
            "completed_today": completed,
            "skipped_today": skipped,
            "pending_today": len(scheduled) - completed - skipped,
        }

    def get_summary(self) -> dict[str, Any]:
        """Resumen de métricas básicas (FR-AN-01 a 03 y métricas de hábitos)."""
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
            "habits": self._habits_summary(),
        }
