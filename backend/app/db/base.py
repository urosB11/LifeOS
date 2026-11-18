"""SQLAlchemy declarative base for domain models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Domain models (projects, tasks, notes, tags, etc.) inherit from this class.
    Tables are created through Alembic migrations, not via create_all(), in line
    with DATABASE.md section 10.
    """


__all__ = ["Base"]