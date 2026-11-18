"""Repositorio de Hábitos (Fase 7)."""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.utils import utc_now
from app.modules.habits.models import Habit, HabitEntry
from app.modules.habits.schemas import HabitCreate, HabitUpdate


class HabitRepository:
    """Acceso a datos de la entidad Habit."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, habit_id: str) -> Habit | None:
        return self.db.get(Habit, habit_id)

    def list(
        self,
        status: str | None = None,
        category: str | None = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[Habit]:
        stmt = select(Habit)
        if status is not None:
            stmt = stmt.where(Habit.status == status)
        if category is not None:
            stmt = stmt.where(Habit.category == category)
        # Orden personalizable: position y luego fecha de creación como desempate
        stmt = stmt.order_by(Habit.position.asc(), Habit.created_at.asc())
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_entries_by_habit(self, habit_id: str) -> int:
        stmt = select(func.count(HabitEntry.id)).where(HabitEntry.habit_id == habit_id)
        return self.db.execute(stmt).scalar_one()

    def next_position(self) -> int:
        """Siguiente posición final del orden personalizado."""
        stmt = select(func.max(Habit.position))
        current = self.db.execute(stmt).scalar_one()
        return 0 if current is None else current + 1

    def create(self, habit_in: HabitCreate, position: int | None = None) -> Habit:
        db_obj = Habit(
            name=habit_in.name,
            description=habit_in.description,
            category=habit_in.category,
            color=habit_in.color,
            frequency_type=habit_in.frequency_type,
            frequency_days=(
                None if habit_in.frequency_days is None
                else json.dumps(habit_in.frequency_days)
            ),
            start_date=habit_in.start_date,
            target_value=habit_in.target_value,
            target_unit=habit_in.target_unit,
            position=position if position is not None else habit_in.position,
        )
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Habit, habit_in: HabitUpdate) -> Habit:
        data = habit_in.model_dump(exclude_unset=True)
        if "frequency_days" in data:
            days = data.pop("frequency_days")
            data["frequency_days"] = None if days is None else json.dumps(days)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def set_status(self, db_obj: Habit, status: str) -> Habit:
        db_obj.status = status
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Habit) -> None:
        self.db.delete(db_obj)
        self.db.flush()


class HabitEntryRepository:
    """Acceso a datos de la entidad HabitEntry (registros diarios)."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_date(self, habit_id: str, entry_date: str) -> HabitEntry | None:
        stmt = select(HabitEntry).where(
            HabitEntry.habit_id == habit_id,
            HabitEntry.entry_date == entry_date,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_habit(
        self,
        habit_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 400,
    ) -> list[HabitEntry]:
        stmt = select(HabitEntry).where(HabitEntry.habit_id == habit_id)
        if from_date is not None:
            stmt = stmt.where(HabitEntry.entry_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(HabitEntry.entry_date <= to_date)
        stmt = stmt.order_by(HabitEntry.entry_date.asc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_for_date(self, habit_ids: list[str], entry_date: str) -> dict[str, HabitEntry]:
        """Entradas de varios hábitos para una fecha (para la vista de hoy)."""
        if not habit_ids:
            return {}
        stmt = select(HabitEntry).where(
            HabitEntry.habit_id.in_(habit_ids),
            HabitEntry.entry_date == entry_date,
        )
        entries = self.db.execute(stmt).scalars().all()
        return {e.habit_id: e for e in entries}

    def create(
        self,
        habit_id: str,
        entry_date: str,
        value: float | None,
        status: str,
        note: str | None,
    ) -> HabitEntry:
        db_obj = HabitEntry(
            habit_id=habit_id,
            entry_date=entry_date,
            value=value,
            status=status,
            note=note,
        )
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: HabitEntry,
        value: float | None,
        value_set: bool,
        status: str,
        note: str | None,
        note_set: bool,
    ) -> HabitEntry:
        if value_set:
            db_obj.value = value
        db_obj.status = status
        if note_set:
            db_obj.note = note
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: HabitEntry) -> None:
        self.db.delete(db_obj)
        self.db.flush()
