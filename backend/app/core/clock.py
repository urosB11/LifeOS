"""Reloj local y zona horaria.

Centraliza el cálculo de la fecha local del usuario a partir de la preferencia
guardada en `user_preferences.timezone`. Las fechas de vencimiento y los
registros diarios son fechas de calendario local (`YYYY-MM-DD`), nunca
instantes UTC convertidos (DATABASE.md sección 3.2).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.utils import utc_now
from app.modules.dashboard.repository import UserPreferenceRepository

DEFAULT_TIMEZONE = "America/Argentina/Cordoba"


def _valid_zone(tz: str) -> ZoneInfo | None:
    """Devuelve un ZoneInfo válido para la cadena dada, o None si no existe."""
    try:
        return ZoneInfo(tz)
    except (ZoneInfoNotFoundError, Exception):
        return None


def get_timezone(db) -> str:
    """Devuelve la zona horaria configurada, validada con IANA.

    Si el valor guardado no es una zona válida, se usa la zona por defecto
    y no se sobrescribe la preferencia (el frontend la corregirá).
    """
    repo = UserPreferenceRepository(db)
    preference = repo.get("timezone")
    value = preference.value if preference else None
    if value and _valid_zone(value) is not None:
        return value
    # El default también debe ser válido; si no, caer a UTC.
    if _valid_zone(DEFAULT_TIMEZONE) is not None:
        return DEFAULT_TIMEZONE
    return "UTC"


def local_today(db) -> date:
    """Fecha de calendario local (`date`) según la zona horaria del usuario."""
    tz = get_timezone(db)
    zone = _valid_zone(tz)
    if zone is None:
        zone = ZoneInfo("UTC")
    return datetime.now(zone).date()


def now_utc() -> str:
    """Instante actual en UTC ISO 8601 con sufijo Z."""
    return utc_now()
