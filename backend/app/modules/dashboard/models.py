"""Modelos de preferencias de widgets y usuario."""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utc_now
from app.db.base import Base


class WidgetPreference(Base):
    """Preferencia de visibilidad, orden y tamaño de un widget del dashboard.

    Los tamaños son spans lógicos de grid, no coordenadas en píxeles.
    """

    __tablename__ = "widget_preferences"

    widget_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    column_span: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    row_span: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WidgetPreference(widget_id={self.widget_id}, position={self.position})>"


class UserPreference(Base):
    """Preferencia simple de la instalación (clave/valor).

    Posibles claves: timezone, theme. No guardar secretos.
    """

    __tablename__ = "user_preferences"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserPreference(key={self.key}, value={self.value})>"