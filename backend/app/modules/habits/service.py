"""Servicio de Hábitos (Fase 7).

Implementa reglas de negocio y registra eventos de actividad en la misma
transacción que el cambio de dominio (DATABASE.md sección 6).
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from app.core.clock import local_today
from app.db.activity import record_event
from app.modules.habits import metrics, scheduling
from app.modules.habits.repository import HabitEntryRepository, HabitRepository
from app.modules.habits.schemas import (
    EntryCreate,
    EntryOut,
    EntryUpdate,
    HabitCreate,
    HabitOut,
    HabitStats,
    HabitUpdate,
    TodayItem,
    WeekDay,
    WeekItem,
    WeekView,
    validate_date_format,
    validate_habit_config,
)


class ConflictError(ValueError):
    """Estado en conflicto con la regla de negocio (respuesta 409)."""


class NotFoundError(LookupError):
    """Recurso inexistente con mensaje específico (respuesta 404)."""


class HabitService:
    """Casos de uso de hábitos y sus registros diarios."""

    def __init__(
        self,
        habit_repo: HabitRepository,
        entry_repo: HabitEntryRepository,
        db,
    ):
        self.habit_repo = habit_repo
        self.entry_repo = entry_repo
        self.db = db

    def _merged_config(self, habit, habit_in: HabitUpdate):
        """Estado de configuración resultante de aplicar una actualización parcial."""
        data = habit_in.model_dump(exclude_unset=True)
        frequency_type = data.get("frequency_type", habit.frequency_type)
        frequency_days = data.get(
            "frequency_days",
            json.loads(habit.frequency_days) if habit.frequency_days else None,
        )
        target_value = data.get("target_value", habit.target_value)
        target_unit = data.get("target_unit", habit.target_unit)
        return frequency_type, frequency_days, target_value, target_unit

    def create(self, habit_in: HabitCreate) -> HabitOut:
        # Reglas cruzadas sobre el payload completo (frecuencia/objetivo)
        validate_habit_config(
            habit_in.frequency_type,
            habit_in.frequency_days,
            habit_in.target_value,
            habit_in.target_unit,
        )
        # Si no se indicó posición explícita, se coloca al final del orden
        position = (
            habit_in.position
            if "position" in habit_in.model_fields_set
            else self.habit_repo.next_position()
        )
        habit = self.habit_repo.create(habit_in, position=position)
        record_event(
            self.db,
            event_type="habit.created",
            entity_type="habit",
            entity_id=habit.id,
            metadata={"status": habit.status, "frequency_type": habit.frequency_type},
        )
        return HabitOut.model_validate(habit)

    def get(self, habit_id: str) -> HabitOut | None:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            return None
        return HabitOut.model_validate(habit)

    def list(
        self, status: str | None = None, category: str | None = None
    ) -> list[HabitOut]:
        habits = self.habit_repo.list(status=status, category=category)
        return [HabitOut.model_validate(h) for h in habits]

    def update(self, habit_id: str, habit_in: HabitUpdate) -> HabitOut | None:
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            return None
        validate_habit_config(*self._merged_config(habit, habit_in))
        updated = self.habit_repo.update(habit, habit_in)
        record_event(
            self.db,
            event_type="habit.updated",
            entity_type="habit",
            entity_id=habit_id,
            metadata={"fields": list(habit_in.model_dump(exclude_unset=True).keys())},
        )
        return HabitOut.model_validate(updated)

    def _transition(
        self, habit_id: str, current_ok: set[str], new_status: str
    ) -> HabitOut:
        """Aplica una transición de estado validada.

        LookupError => no encontrado (404); ValueError => transición inválida
        (409); si ya está en el estado objetivo es un no-op idempotente.
        """
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise NotFoundError("Hábito no encontrado")
        if habit.status == new_status:
            return HabitOut.model_validate(habit)
        if habit.status not in current_ok:
            raise ValueError(
                f"No se puede pasar de '{habit.status}' a '{new_status}'"
            )
        old_status = habit.status
        updated = self.habit_repo.set_status(habit, new_status)
        record_event(
            self.db,
            event_type="habit.status_changed",
            entity_type="habit",
            entity_id=habit_id,
            metadata={"from": old_status, "to": new_status},
        )
        return HabitOut.model_validate(updated)

    def pause(self, habit_id: str) -> HabitOut:
        return self._transition(habit_id, {"active"}, "paused")

    def resume(self, habit_id: str) -> HabitOut:
        return self._transition(habit_id, {"paused"}, "active")

    def archive(self, habit_id: str) -> HabitOut:
        # Archivar desde cualquier estado (como projects)
        return self._transition(habit_id, {"active", "paused"}, "archived")

    def restore(self, habit_id: str) -> HabitOut:
        return self._transition(habit_id, {"archived"}, "active")

    def delete(self, habit_id: str) -> bool:
        """Elimina físicamente un hábito solo si no tiene registros.

        Reglas (DATABASE.md sección 6): archivar es la operación preferida;
        `habit_entries.habit_id` es ON DELETE RESTRICT.
        """
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            return False
        if self.habit_repo.count_entries_by_habit(habit_id) > 0:
            return False
        self.habit_repo.delete(habit)
        record_event(
            self.db,
            event_type="habit.deleted",
            entity_type="habit",
            entity_id=habit_id,
        )
        return True

    # --- Registros diarios (entries) ----------------------------------------

    def _resolve_create_status(
        self, habit, value: float | None, explicit: str | None
    ) -> str:
        """Estado de un registro nuevo (derivation solo al escribir)."""
        if explicit is not None:
            return explicit
        if value is None:
            # Registro rápido sin valor: cumplido (toggle binario)
            return "completed"
        if habit.target_value is not None:
            return "completed" if value >= habit.target_value else "pending"
        return "completed"

    def create_entry(self, habit_id: str, entry_in: EntryCreate) -> EntryOut:
        """Registra un día; si ya existe el registro, se corrige con PATCH."""
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise NotFoundError("Hábito no encontrado")

        today = local_today(self.db)
        entry_date = (
            date.fromisoformat(entry_in.entry_date)
            if entry_in.entry_date
            else today
        )
        if entry_date > today:
            raise ValueError("No se pueden registrar días futuros")
        if not scheduling.is_scheduled(habit, entry_date):
            raise ValueError("El día indicado no está programado para este hábito")
        if entry_in.value is not None and habit.target_value is None:
            raise ValueError(
                "Este hábito es binario: registra el cumplimiento sin value"
            )
        if self.entry_repo.get_by_date(habit_id, entry_date.isoformat()):
            raise ConflictError(
                "Ya existe un registro para ese día; usa PATCH para corregirlo"
            )

        status_value = self._resolve_create_status(
            habit, entry_in.value, entry_in.status
        )
        entry = self.entry_repo.create(
            habit_id=habit_id,
            entry_date=entry_date.isoformat(),
            value=entry_in.value,
            status=status_value,
            note=entry_in.note,
        )
        record_event(
            self.db,
            event_type="habit.entry_created",
            entity_type="habit",
            entity_id=habit_id,
            metadata={"entry_date": entry.entry_date, "status": entry.status},
        )
        return EntryOut.model_validate(entry)

    def update_entry(
        self, habit_id: str, entry_date: str, entry_in: EntryUpdate
    ) -> EntryOut:
        """Corrige el registro de una fecha; no duplica el historial."""
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise NotFoundError("Hábito no encontrado")
        entry = self.entry_repo.get_by_date(habit_id, entry_date)
        if entry is None:
            raise NotFoundError("Registro no encontrado")

        data = entry_in.model_dump(exclude_unset=True)
        if "value" in data and data["value"] is not None and habit.target_value is None:
            raise ValueError(
                "Este hábito es binario: registra el cumplimiento sin value"
            )
        if data.get("status") is not None:
            status_value = data["status"]
        elif data.get("value") is not None:
            # Re-derivar solo al escribir un valor nuevo
            status_value = self._resolve_create_status(habit, data["value"], None)
        else:
            status_value = entry.status

        updated = self.entry_repo.update(
            entry,
            value=data.get("value"),
            value_set="value" in data,
            status=status_value,
            note=data.get("note"),
            note_set="note" in data,
        )
        record_event(
            self.db,
            event_type="habit.entry_updated",
            entity_type="habit",
            entity_id=habit_id,
            metadata={"entry_date": entry_date, "status": updated.status},
        )
        return EntryOut.model_validate(updated)

    def delete_entry(self, habit_id: str, entry_date: str) -> bool:
        """Borra un registro: el día vuelve a 'no registrado'."""
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            return False
        entry = self.entry_repo.get_by_date(habit_id, entry_date)
        if entry is None:
            return False
        self.entry_repo.delete(entry)
        record_event(
            self.db,
            event_type="habit.entry_deleted",
            entity_type="habit",
            entity_id=habit_id,
            metadata={"entry_date": entry_date},
        )
        return True

    def list_entries(
        self,
        habit_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[EntryOut]:
        """Historial de registros de un hábito en un rango opcional."""
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise NotFoundError("Hábito no encontrado")
        if from_date is not None:
            validate_date_format(from_date, "from")
            from_date = date.fromisoformat(from_date)
        if to_date is not None:
            validate_date_format(to_date, "to")
            to_date = date.fromisoformat(to_date)
        if from_date and to_date and from_date > to_date:
            raise ValueError("El rango 'from' posterior a 'to'")
        entries = self.entry_repo.list_for_habit(
            habit_id,
            from_date=from_date.isoformat() if from_date else None,
            to_date=to_date.isoformat() if to_date else None,
        )
        return [EntryOut.model_validate(e) for e in entries]

    def calendar(self, habit_id: str, month: str) -> dict:
        """Días de un mes (YYYY-MM) con programación y estado de registro.

        Centraliza la regla de días programados en backend; la UI solo colorea.
        """
        habit = self.habit_repo.get(habit_id)
        if habit is None:
            raise NotFoundError("Hábito no encontrado")
        try:
            year_str, month_str = month.split("-")
            year, mon = int(year_str), int(month_str)
            first = date(year, mon, 1)
        except (ValueError, AttributeError) as exc:
            raise ValueError("month debe tener el formato YYYY-MM") from exc
        last = (
            date(year + (1 if mon == 12 else 0), (mon % 12) + 1, 1)
            - timedelta(days=1)
        )
        entries = self.entry_repo.list_for_habit(
            habit_id, from_date=first.isoformat(), to_date=last.isoformat()
        )
        entry_map = {e.entry_date: e.status for e in entries}
        today = local_today(self.db)

        days: list[dict] = []
        current = first
        while current <= last:
            iso = current.isoformat()
            days.append(
                {
                    "date": iso,
                    "scheduled": scheduling.is_scheduled(habit, current),
                    "entry_status": entry_map.get(iso),
                }
            )
            current = date.fromordinal(current.toordinal() + 1)
        return {
            "month": f"{year:04d}-{mon:02d}",
            "today": today.isoformat(),
            "days": days,
        }

    def today(self) -> list[TodayItem]:
        """Hábitos activos programados para el día local actual con su registro."""
        today = local_today(self.db)
        active = self.habit_repo.list(status="active")
        scheduled = [h for h in active if scheduling.is_scheduled(h, today)]
        entries = self.entry_repo.get_for_date(
            [h.id for h in scheduled], today.isoformat()
        )
        return [
            TodayItem(
                habit=HabitOut.model_validate(h),
                entry=(
                    EntryOut.model_validate(entries[h.id])
                    if h.id in entries
                    else None
                ),
            )
            for h in scheduled
        ]

    # --- Métricas (DATABASE.md sección 8.1) --------------------------------

    def week(self) -> WeekView:
        """Semana local en curso (lunes-domingo) con programación y registro.

        Alimenta el widget habits_week; la regla de días vive en backend.
        Solo hábitos activos: los pausados no se registran y los archivados
        no pertenecen a la vista operativa (la vista de métricas sí los incluye
        si se piden por id).
        """
        today = local_today(self.db)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        habits = self.habit_repo.list(status="active")

        items: list[WeekItem] = []
        for habit in habits:
            entries = self.entry_repo.list_for_habit(
                habit.id,
                from_date=week_start.isoformat(),
                to_date=week_end.isoformat(),
                limit=7,
            )
            entry_map = {e.entry_date: e.status for e in entries}
            days = []
            for offset in range(7):
                day = week_start + timedelta(days=offset)
                iso = day.isoformat()
                days.append(
                    WeekDay(
                        date=iso,
                        scheduled=scheduling.is_scheduled(habit, day),
                        entry_status=entry_map.get(iso),
                    )
                )
            items.append(WeekItem(habit=HabitOut.model_validate(habit), days=days))
        return WeekView(
            week_start=week_start.isoformat(),
            week_end=week_end.isoformat(),
            today=today.isoformat(),
            items=items,
        )

    def _stats_for(self, habit, today) -> HabitStats:
        """Métricas de un hábito calculadas desde sus registros (sin agregados)."""
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        entries = self.entry_repo.list_for_habit(
            habit.id,
            from_date=habit.start_date,
            to_date=today.isoformat(),
            limit=5000,
        )
        statuses = {
            date.fromisoformat(e.entry_date): e.status for e in entries
        }
        completed = {d for d, s in statuses.items() if s == "completed"}

        sched_week, done_week, _ = metrics.period_counts(
            habit, week_start, today, today, statuses
        )
        sched_month, done_month, recorded_month = metrics.period_counts(
            habit, month_start, today, today, statuses
        )

        return HabitStats(
            habit_id=habit.id,
            name=habit.name,
            color=habit.color,
            status=habit.status,
            target_value=habit.target_value,
            target_unit=habit.target_unit,
            today=today.isoformat(),
            week_start=week_start.isoformat(),
            month=month_start.isoformat(),
            current_streak=metrics.current_streak(habit, completed, today),
            best_streak=metrics.best_streak(habit, completed, today),
            scheduled_week=sched_week,
            completed_week=done_week,
            weekly_compliance=metrics.ratio(done_week, sched_week),
            scheduled_month=sched_month,
            completed_month=done_month,
            monthly_compliance=metrics.ratio(done_month, sched_month),
            consistency_month=metrics.ratio(recorded_month, sched_month),
        )

    def stats(self, habit_id: str | None = None) -> list[HabitStats]:
        """Métricas de un hábito (habit_id) o de todos los no archivados."""
        today = local_today(self.db)
        if habit_id is not None:
            habit = self.habit_repo.get(habit_id)
            if habit is None:
                raise NotFoundError("Hábito no encontrado")
            return [self._stats_for(habit, today)]
        habits = [h for h in self.habit_repo.list() if h.status != "archived"]
        return [self._stats_for(h, today) for h in habits]
