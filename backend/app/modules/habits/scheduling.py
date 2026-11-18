"""Reglas de programación de días de los hábitos (Fase 7).

Determine qué días de calendario local están programados para un hábito según
su frecuencia y fecha de inicio. Convención de días: 0=lunes … 6=domingo,
igual que `date.weekday()` de Python (DATABASE.md sección 5.11).
"""

from __future__ import annotations

import json
from datetime import date

from app.modules.habits.models import Habit


def frequency_days(habit: Habit) -> list[int] | None:
    """Días programados de la semana parseados desde JSON, o None en `daily`."""
    if not habit.frequency_days:
        return None
    return json.loads(habit.frequency_days)


def start_date(habit: Habit) -> date:
    """Fecha de inicio del hábito como fecha de calendario local."""
    return date.fromisoformat(habit.start_date)


def is_scheduled(habit: Habit, day: date) -> bool:
    """True si `day` es un día programado para el hábito.

    - anteriores a `start_date` no son programados;
    - `daily`: programado todo día desde `start_date`;
    - `weekly_days`: programado si el número de semana está en la lista.
    """
    if day < start_date(habit):
        return False
    if habit.frequency_type == "daily":
        return True
    days = frequency_days(habit) or []
    return day.weekday() in days


def scheduled_days(habit: Habit, first: date, last: date) -> list[date]:
    """Lista ordenada de días programados entre `first` y `last` inclusive."""
    if last < first:
        return []
    days: list[date] = []
    current = first
    while current <= last:
        if is_scheduled(habit, current):
            days.append(current)
        current = date.fromordinal(current.toordinal() + 1)
    return days
