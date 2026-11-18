"""Utilidades compartidas del backend.

Genera identificadores UUIDv4 como texto y timestamps UTC en ISO 8601 con sufijo Z,
tal como lo definen ARCHITECTURE.md y DATABASE.md.
"""

import uuid
from datetime import UTC, datetime


def new_uuid() -> str:
    """Genera un UUIDv4 como texto canónico de 36 caracteres."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Devuelve el instante actual en UTC como ISO 8601 con sufijo Z."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")