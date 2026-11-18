"""Métricas de hábitos — funciones puras (Fase 7, DATABASE.md sección 8.1).

Todas las funciones reciben fechas de calendario local ya resueltas y
conjuntos de fechas con registro; no consultan la base. Convención de días
de la semana: 0=lunes … 6=domingo.

Reglas (DATABASE.md 8.1):
- solo los días programados entran en los denominadores;
- `status = completed` es la única fuente de verdad de cumplimiento;
- los días no programados no interrumpen ni suman en las rachas;
- denominador cero => la métrica es "Sin datos" (se devuelve None).
"""

from __future__ import annotations

from datetime import date, timedelta

from app.modules.habits import scheduling
from app.modules.habits.models import Habit


def _start(habit: Habit) -> date:
    return date.fromisoformat(habit.start_date)


def current_streak(habit: Habit, completed: set[date], today: date) -> int:
    """Racha actual: días programados consecutivos completados que terminan hoy.

    Si hoy es programado y no está completado, la racha es 0. Los días no
    programados no interrumpen la racha (DATABASE.md 8.1).
    """
    start = _start(habit)
    if today < start:
        return 0
    # Primer día programado desde hoy hacia atrás
    day = today
    while day >= start and not scheduling.is_scheduled(habit, day):
        day -= timedelta(days=1)
    if day < start or day not in completed:
        return 0
    streak = 0
    while day >= start:
        if not scheduling.is_scheduled(habit, day):
            day -= timedelta(days=1)
            continue
        if day not in completed:
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def best_streak(habit: Habit, completed: set[date], today: date) -> int:
    """Mejor racha del historial: máximo de días programados consecutivos
    completados. Los días no programados no interrumpen ni suman."""
    start = _start(habit)
    if today < start:
        return 0
    best = 0
    run = 0
    day = start
    while day <= today:
        if scheduling.is_scheduled(habit, day):
            if day in completed:
                run += 1
                best = max(best, run)
            else:
                run = 0
        day += timedelta(days=1)
    return best


def ratio(numerator: int, denominator: int) -> float | None:
    """Porcentaje 0-100 con una decimal; None si el denominador es cero
    (la UI muestra 'Sin datos', DATABASE.md 8.1)."""
    if denominator == 0:
        return None
    return round(numerator / denominator * 100, 1)


def period_counts(
    habit: Habit,
    first: date,
    last: date,
    today: date,
    statuses: dict[date, str],
) -> tuple[int, int, int]:
    """(días programados, completed, completed+skipped) entre first y last.

    - los días programados futuros (posteriores a hoy) no entran en el
      denominador: aún no es posible registrarlos;
    - 'consistencia' usa el segundo contador (completed + skipped) según
      DATABASE.md 8.1.
    """
    last = min(last, today)
    if last < first:
        return (0, 0, 0)
    scheduled = scheduling.scheduled_days(habit, first, last)
    done = sum(1 for d in scheduled if statuses.get(d) == "completed")
    recorded = sum(
        1 for d in scheduled if statuses.get(d) in ("completed", "skipped")
    )
    return (len(scheduled), done, recorded)
