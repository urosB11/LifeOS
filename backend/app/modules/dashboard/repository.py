"""Repositorios de preferencias de widgets y usuario."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dashboard.models import UserPreference, WidgetPreference


class WidgetPreferenceRepository:
    """Acceso a datos de preferencias de widgets."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, widget_id: str) -> WidgetPreference | None:
        return self.db.get(WidgetPreference, widget_id)

    def list(self) -> list[WidgetPreference]:
        stmt = select(WidgetPreference).order_by(WidgetPreference.position)
        return list(self.db.execute(stmt).scalars().all())

    def upsert(
        self,
        widget_id: str,
        is_visible: bool,
        position: int,
        column_span: int,
        row_span: int,
    ) -> WidgetPreference:
        existing = self.get(widget_id)
        if existing:
            existing.is_visible = is_visible
            existing.position = position
            existing.column_span = column_span
            existing.row_span = row_span
            from app.core.utils import utc_now

            existing.updated_at = utc_now()
            self.db.add(existing)
            self.db.flush()
            self.db.refresh(existing)
            return existing
        db_obj = WidgetPreference(
            widget_id=widget_id,
            is_visible=is_visible,
            position=position,
            column_span=column_span,
            row_span=row_span,
        )
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj


class UserPreferenceRepository:
    """Acceso a datos de preferencias de usuario."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> UserPreference | None:
        return self.db.get(UserPreference, key)

    def list(self) -> list[UserPreference]:
        stmt = select(UserPreference).order_by(UserPreference.key)
        return list(self.db.execute(stmt).scalars().all())

    def upsert(self, key: str, value: str) -> UserPreference:
        existing = self.get(key)
        if existing:
            existing.value = value
            from app.core.utils import utc_now

            existing.updated_at = utc_now()
            self.db.add(existing)
            self.db.flush()
            self.db.refresh(existing)
            return existing
        db_obj = UserPreference(key=key, value=value)
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj