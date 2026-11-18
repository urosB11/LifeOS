"""Esquemas Pydantic para Hábitos (Fase 7)."""

from __future__ import annotations

import json
from datetime import date

from pydantic import BaseModel, Field, field_validator

HABIT_STATUSES = {"active", "paused", "archived"}
FREQUENCY_TYPES = {"daily", "weekly_days"}


def validate_date_format(value: str, field_label: str) -> str:
    """Valida `YYYY-MM-DD` real (fecha de calendario local)."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_label} debe ser una fecha YYYY-MM-DD válida: {value}"
        ) from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field_label} debe ser una fecha YYYY-MM-DD válida: {value}")
    return value


def validate_habit_config(
    frequency_type: str,
    frequency_days: list[int] | None,
    target_value: float | None,
    target_unit: str | None,
) -> None:
    """Valida la configuración combinada de un hábito.

    Se llama desde el servicio con el estado fusionado (creación o actualización
    parcial), de modo que las reglas cruzadas se evalúan sobre el resultado
    final, no sobre el payload parcial.
    """
    if frequency_type not in FREQUENCY_TYPES:
        raise ValueError(
            f"Frecuencia inválida: {frequency_type}. "
            f"Valores permitidos: {sorted(FREQUENCY_TYPES)}"
        )
    if frequency_type == "weekly_days":
        if not frequency_days:
            raise ValueError(
                "frequency_days es obligatorio con frecuencia 'weekly_days'"
            )
        invalid = [d for d in frequency_days if d not in range(0, 7)]
        if invalid:
            raise ValueError(
                f"frequency_days debe contener valores 0-6 (0=lunes): {invalid}"
            )
        if len(set(frequency_days)) != len(frequency_days):
            raise ValueError("frequency_days no debe repetir días")
    if target_unit and target_value is None:
        raise ValueError("target_unit requiere target_value")


class HabitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    frequency_type: str = Field(default="daily")
    frequency_days: list[int] | None = Field(default=None)
    start_date: str = Field(..., max_length=10)
    target_value: float | None = Field(default=None, gt=0)
    target_unit: str | None = Field(default=None, max_length=30)
    position: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El nombre del hábito no puede estar vacío")
        return value.strip()

    @field_validator("start_date")
    @classmethod
    def start_date_format(cls, value: str) -> str:
        return validate_date_format(value, "start_date")

    @field_validator("color")
    @classmethod
    def color_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        v = value.strip()
        if not (v.startswith("#") and len(v) in (4, 7) and
                all(c in "0123456789abcdefABCDEF" for c in v[1:])):
            raise ValueError(
                f"color debe ser un hexadecimal #RGB o #RRGGBB: {value}"
            )
        return v


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    """Actualización parcial; las reglas cruzadas se validan con el estado fusionado."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    frequency_type: str | None = None
    frequency_days: list[int] | None = None
    start_date: str | None = Field(default=None, max_length=10)
    target_value: float | None = Field(default=None, gt=0)
    target_unit: str | None = Field(default=None, max_length=30)
    position: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El nombre del hábito no puede estar vacío")
        return value.strip() if value else value

    @field_validator("start_date")
    @classmethod
    def start_date_format(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_date_format(value, "start_date")
        return value


class HabitOut(HabitBase):
    id: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @field_validator("frequency_days", mode="before")
    @classmethod
    def parse_frequency_days(cls, value):
        # La base guarda frequency_days como JSON (TEXT); se devuelve como lista.
        if isinstance(value, str):
            return json.loads(value)
        return value


# --- Registros diarios (entries) -----------------------------------------

ENTRY_STATUSES = {"pending", "completed", "skipped"}


def _validate_status(value: str | None) -> str | None:
    if value is not None and value not in ENTRY_STATUSES:
        raise ValueError(
            f"Estado de registro inválido: {value}. "
            f"Valores permitidos: {sorted(ENTRY_STATUSES)}"
        )
    return value


class EntryCreate(BaseModel):
    """Registro diario. `entry_date` omite el día local actual (backend)."""

    entry_date: str | None = Field(default=None, max_length=10)
    value: float | None = Field(default=None, ge=0)
    status: str | None = Field(default=None)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("entry_date")
    @classmethod
    def entry_date_format(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_date_format(value, "entry_date")
        return value

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str | None) -> str | None:
        return _validate_status(value)


class EntryUpdate(BaseModel):
    """Corrección de un registro existente (parcial)."""

    value: float | None = Field(default=None, ge=0)
    status: str | None = Field(default=None)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str | None) -> str | None:
        return _validate_status(value)


class EntryOut(BaseModel):
    id: str
    habit_id: str
    entry_date: str
    value: float | None = None
    status: str
    note: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TodayItem(BaseModel):
    """Hábito programado para hoy con su registro de hoy (o null)."""

    habit: HabitOut
    entry: EntryOut | None = None


# --- Métricas (DATABASE.md sección 8.1) ---------------------------------

class HabitStats(BaseModel):
    """Métricas de un hábito. Los cumplimientos son porcentaje 0-100 o
    None cuando el denominador es cero (la UI muestra 'Sin datos')."""

    habit_id: str
    name: str
    color: str | None = None
    status: str
    target_value: float | None = None
    target_unit: str | None = None
    today: str
    week_start: str
    month: str
    current_streak: int
    best_streak: int
    scheduled_week: int
    completed_week: int
    weekly_compliance: float | None
    scheduled_month: int
    completed_month: int
    monthly_compliance: float | None
    consistency_month: float | None


# --- Vista semanal (widget habits_week) ----------------------------------

class WeekDay(BaseModel):
    """Un día de la semana actual con su programación y registro."""

    date: str
    scheduled: bool
    entry_status: str | None = None


class WeekItem(BaseModel):
    """Hábito no archivado con los 7 días de la semana local (lunes-domingo)."""

    habit: HabitOut
    days: list[WeekDay]


class WeekView(BaseModel):
    week_start: str
    week_end: str
    today: str
    items: list[WeekItem]


__all__ = [
    "HABIT_STATUSES",
    "FREQUENCY_TYPES",
    "ENTRY_STATUSES",
    "HabitBase",
    "HabitCreate",
    "HabitUpdate",
    "HabitOut",
    "EntryCreate",
    "EntryUpdate",
    "EntryOut",
    "TodayItem",
    "HabitStats",
    "WeekDay",
    "WeekItem",
    "WeekView",
    "validate_habit_config",
]
