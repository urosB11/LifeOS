"""Modelo y utilidades para eventos de actividad.

activity_events conserva historial complementario de cambios relevantes.
No es event sourcing: las tablas de dominio siguen siendo la fuente de verdad
(DATABASE.md sección 7). Los eventos se escriben en la misma transacción que
el cambio de dominio y nunca contienen cuerpos de notas ni contenido sensible.
"""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import new_uuid, utc_now
from app.db.base import Base


class ActivityEvent(Base):
    """Evento de actividad append-only."""

    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    occurred_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


def record_event(
    db,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    metadata: dict | None = None,
) -> ActivityEvent:
    """Registra un evento de actividad en la sesión actual (misma transacción)."""
    import json

    event = ActivityEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
        schema_version=1,
    )
    db.add(event)
    db.flush()
    return event