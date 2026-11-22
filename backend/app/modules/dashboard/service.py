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
        default_column_span=4,
        default_row_span=1,
    ),
    WidgetCatalogItem(
        widget_id="active_projects",
        label="Proyectos activos",
        description="Listado de proyectos con estado activo",
        default_visible=True,
        default_position=2,
        default_column_span=4,
        default_row_span=1,
    ),
    WidgetCatalogItem(
        widget_id="quick_add_task",
        label="Nueva tarea",
        description="Acceso rápido para crear una tarea",
        default_visible=True,
        default_position=1,
        default_column_span=2,
        default_row_span=1,
    ),
    WidgetCatalogItem(
        widget_id="quick_add_note",
        label="Nueva nota",
        description="Acceso rápido para crear una nota",
        default_visible=True,
        default_position=1,
        default_column_span=2,
        default_row_span=1,
    ),
    WidgetCatalogItem(
        widget_id="habits_today",
        label="Hábitos de hoy",
        description="Hábitos programados para hoy con su estado de registro",
        default_visible=True,
        default_position=3,
        default_column_span=2,
        default_row_span=1,
    ),
    WidgetCatalogItem(
        widget_id="habits_week",
        label="Semana de hábitos",
        description="Programación y registros de la semana por hábito",
        default_visible=True,
        default_position=4,
        default_column_span=6,
        default_row_span=1,
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
                    "column_span": pref.column_span if pref else item.default_column_span,
                    "row_span": pref.row_span if pref else item.default_row_span,
                    "config_json": pref.config_json if pref else None,
                }
            )
        # Ordenar por posición
        result.sort(key=lambda w: w["position"])
        return result

    def save_widget_preferences(
        self, preferences: list[dict[str, Any]]
    ) -> list[dict]:
        """Guarda visibilidad, orden y spans lógicos de los widgets."""
        current = {pref.widget_id: pref for pref in self.widget_repo.list()}
        catalog = {item.widget_id: item for item in WIDGET_CATALOG}
        requested = {pref["widget_id"]: dict(pref) for pref in preferences}
        capture_ids = ("quick_add_task", "quick_add_note")
        capture_prefs = [
            requested[widget_id]
            for widget_id in capture_ids
            if widget_id in requested
        ]
        if capture_prefs:
            existing_positions = [
                current[widget_id].position
                for widget_id in capture_ids
                if widget_id in current
            ]
            default_positions = [
                catalog[widget_id].default_position for widget_id in capture_ids
            ]
            position_values = [
                pref["position"]
                for pref in capture_prefs
                if pref.get("position") is not None
            ]
            column_values = [
                pref["column_span"]
                for pref in capture_prefs
                if pref.get("column_span") is not None
            ]
            row_values = [
                pref["row_span"]
                for pref in capture_prefs
                if pref.get("row_span") is not None
            ]
            existing_capture = next(
                (current[widget_id] for widget_id in capture_ids if widget_id in current),
                None,
            )
            shared_position = min(
                position_values
                or existing_positions
                or default_positions
            )
            shared_column_span = (
                column_values[0]
                if column_values
                else existing_capture.column_span
                if existing_capture
                else catalog[capture_ids[0]].default_column_span
            )
            shared_row_span = (
                row_values[0]
                if row_values
                else existing_capture.row_span
                if existing_capture
                else catalog[capture_ids[0]].default_row_span
            )
            for widget_id in capture_ids:
                requested.setdefault(widget_id, {"widget_id": widget_id})
                requested[widget_id].update(
                    position=shared_position,
                    column_span=shared_column_span,
                    row_span=shared_row_span,
                )

        saved = {}
        for pref in requested.values():
            widget_id = pref["widget_id"]
            existing = current.get(widget_id)
            default = catalog[widget_id]
            is_visible = (
                pref["is_visible"]
                if pref.get("is_visible") is not None
                else existing.is_visible if existing else default.default_visible
            )
            position = (
                pref["position"]
                if pref.get("position") is not None
                else existing.position if existing else default.default_position
            )
            column_span = (
                pref["column_span"]
                if pref.get("column_span") is not None
                else existing.column_span if existing else default.default_column_span
            )
            row_span = (
                pref["row_span"]
                if pref.get("row_span") is not None
                else existing.row_span if existing else default.default_row_span
            )
            db_obj = self.widget_repo.upsert(
                widget_id, is_visible, position, column_span, row_span
            )
            current[widget_id] = db_obj
            saved[widget_id] = db_obj
        record_event(
            self.db,
            event_type="dashboard.widgets_updated",
            entity_type="dashboard",
            entity_id="widgets",
            metadata={"count": len(preferences)},
        )
        return [
            {
                "widget_id": saved[pref["widget_id"]].widget_id,
                "is_visible": saved[pref["widget_id"]].is_visible,
                "position": saved[pref["widget_id"]].position,
                "column_span": saved[pref["widget_id"]].column_span,
                "row_span": saved[pref["widget_id"]].row_span,
                "config_json": saved[pref["widget_id"]].config_json,
                "updated_at": saved[pref["widget_id"]].updated_at,
            }
            for pref in preferences
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