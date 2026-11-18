"""Servicio de Dashboard y configuración de usuario.

Proporciona el catálogo de widgets con preferencias, el resumen de Home
y las preferencias de usuario (tema, zona horaria).
"""

from __future__ import annotations

from typing import Any

from app.db.activity import record_event
from app.modules.dashboard.repository import (
    UserPreferenceRepository,
    WidgetPreferenceRepository,
)
from app.modules.dashboard.schemas import WidgetCatalogItem
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository

# Catálogo estático de widgets del MVP (ARCHITECTURE.md sección 6, FR-HOME-02)
WIDGET_CATALOG: list[WidgetCatalogItem] = [
    WidgetCatalogItem(
        widget_id="upcoming_tasks",
        label="Tareas próximas",
        description="Tareas pendientes ordenadas por prioridad y vencimiento",
        default_visible=True,
        default_position=0,
    ),
    WidgetCatalogItem(
        widget_id="active_projects",
        label="Proyectos activos",
        description="Listado de proyectos con estado activo",
        default_visible=True,
        default_position=1,
    ),
    WidgetCatalogItem(
        widget_id="quick_add_task",
        label="Nueva tarea",
        description="Acceso rápido para crear una tarea",
        default_visible=True,
        default_position=2,
    ),
    WidgetCatalogItem(
        widget_id="quick_add_note",
        label="Nueva nota",
        description="Acceso rápido para crear una nota",
        default_visible=True,
        default_position=3,
    ),
]


class DashboardService:
    """Casos de uso del dashboard y widgets."""

    def __init__(
        self,
        widget_repo: WidgetPreferenceRepository,
        project_repo: ProjectRepository,
        task_repo: TaskRepository,
        db,
    ):
        self.widget_repo = widget_repo
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.db = db

    def get_widget_catalog(self) -> list[dict[str, Any]]:
        """Devuelve el catálogo de widgets con sus preferencias guardadas.

        Si no existe preferencia guardada, se usan los defaults del catálogo.
        """
        prefs = {p.widget_id: p for p in self.widget_repo.list()}
        result = []
        for item in WIDGET_CATALOG:
            pref = prefs.get(item.widget_id)
            result.append(
                {
                    "widget_id": item.widget_id,
                    "label": item.label,
                    "description": item.description,
                    "is_visible": pref.is_visible if pref else item.default_visible,
                    "position": pref.position if pref else item.default_position,
                    "config_json": pref.config_json if pref else None,
                }
            )
        # Ordenar por posición
        result.sort(key=lambda w: w["position"])
        return result

    def save_widget_preferences(
        self, preferences: list[dict[str, Any]]
    ) -> list[dict]:
        """Guarda visibilidad y orden de los widgets."""
        saved = []
        for pref in preferences:
            widget_id = pref["widget_id"]
            is_visible = bool(pref.get("is_visible", True))
            position = int(pref.get("position", 0))
            db_obj = self.widget_repo.upsert(widget_id, is_visible, position)
            saved.append(db_obj)
        record_event(
            self.db,
            event_type="dashboard.widgets_updated",
            entity_type="dashboard",
            entity_id="widgets",
            metadata={"count": len(preferences)},
        )
        return [
            {
                "widget_id": s.widget_id,
                "is_visible": s.is_visible,
                "position": s.position,
                "config_json": s.config_json,
                "updated_at": s.updated_at,
            }
            for s in saved
        ]

    def get_summary(self) -> dict[str, Any]:
        """Resumen de Home: métricas básicas de tareas y proyectos (FR-AN-01 a 03)."""
        pending = self.task_repo.count(status="pending")
        completed = self.task_repo.count(status="completed")
        overdue = self.task_repo.count_overdue()
        active_projects = self.project_repo.count_by_status("active")

        return {
            "tasks": {
                "pending": pending,
                "completed": completed,
                "overdue": overdue,
            },
            "projects": {
                "active": active_projects,
            },
        }


class UserPreferenceService:
    """Casos de uso de preferencias de usuario (tema, zona horaria)."""

    def __init__(self, pref_repo: UserPreferenceRepository, db):
        self.pref_repo = pref_repo
        self.db = db

    def get(self, key: str) -> str | None:
        pref = self.pref_repo.get(key)
        return pref.value if pref else None

    def set(self, key: str, value: str) -> str:
        self.pref_repo.upsert(key, value)
        record_event(
            self.db,
            event_type="user.preference_updated",
            entity_type="user_preference",
            entity_id=key,
            metadata={"key": key},
        )
        return value

    def list_all(self) -> list[dict[str, str]]:
        prefs = self.pref_repo.list()
        return [{"key": p.key, "value": p.value} for p in prefs]