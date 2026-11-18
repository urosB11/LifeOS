"""Modelo de datos de Hábitos (Fase 7)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import new_uuid, utc_now
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.habits.models import HabitEntry


class Habit(Base):
    """Hábito con frecuencia, estado y objetivo cuantificable opcional.

    Reglas de negocio (DATABASE.md sección 5.11):
    - id es UUIDv4 como texto.
    - name es obligatorio y no vacío tras normalizar espacios.
    - frequency_type: 'daily' o 'weekly_days' (0=lunes … 6=domingo).
    - frequency_days es JSON con los días solo para 'weekly_days'; NULL en 'daily'.
    - start_date es YYYY-MM-DD de calendario local; los días anteriores no son
      programados.
    - target_value/target_unit definen un hábito cuantificable; NULL = binario.
    - status: 'active', 'paused' o 'archived'; default 'active'.
    - position es el orden personalizable (no negativo).
    """

    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    frequency_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="daily"
    )
    frequency_days: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, index=True
    )
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    entries: Mapped[list[HabitEntry]] = relationship(
        back_populates="habit", lazy="selectin"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Habit(id={self.id}, name={self.name!r}, status={self.status})>"


class HabitEntry(Base):
    """Registro diario de un hábito para una fecha de calendario local.

    Reglas de negocio (DATABASE.md sección 5.12):
    - UNIQUE(habit_id, entry_date): un solo registro por hábito y fecha.
    - status es la única fuente de verdad del cumplimiento:
      'pending' (registrado, sin completar), 'completed' o 'skipped' (omitido).
    - value guarda la cantidad medida (hábitos cuantificables); es dato y no
      recalcula el estado ya almacenado.
    - Un día programado sin fila se considera 'no registrado' (pendiente).
    - Los registros no se recalculan si cambia la frecuencia del hábito.
    """

    __tablename__ = "habit_entries"

    __table_args__ = (
        UniqueConstraint(
            "habit_id", "entry_date", name="uq_habit_entries_habit_id_entry_date"
        ),
        Index("ix_habit_entries_habit_id_entry_date", "habit_id", "entry_date"),
        Index("ix_habit_entries_entry_date", "entry_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    habit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("habits.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entry_date: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    habit: Mapped[Habit] = relationship(back_populates="entries")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<HabitEntry(id={self.id}, habit_id={self.habit_id}, "
            f"entry_date={self.entry_date}, status={self.status})>"
        )
