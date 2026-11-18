"""Database session and engine configuration.

Creates a synchronous SQLAlchemy engine for SQLite and enforces
PRAGMA foreign_keys = ON on every connection (DATABASE.md section 6).
"""

import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()

# Ensure the data directory exists before opening the SQLite database
# (DATABASE.md section 11: the app creates the directory if missing).
# For sqlite:/// URLs, the file path follows the scheme prefix.
_db_prefix = "sqlite:///"
if settings.database_url.startswith(_db_prefix):
    _db_path = settings.database_url[len(_db_prefix):]
    _db_dir = os.path.dirname(_db_path)
    if _db_dir and not os.path.exists(_db_dir):
        os.makedirs(_db_dir, exist_ok=True)

# Synchronous engine for SQLite. check_same_thread=False allows the connection
# to be used across FastAPI dependency calls in the same thread.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record):  # noqa: ARG001
    """Activate PRAGMA foreign_keys = ON on every new DBAPI connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_db() -> Session:
    """Yield a database session and settle the request transaction.

    This dependency is the transaction boundary for API requests (DATABASE.md
    section 6: domain change and activity event confirmed together):

    - commit when the route finishes successfully, so writes actually persist;
    - rollback when the route raises, so a failed request leaves no partial
      data behind;
    - close the session either way.

    Without the commit, Session.close() discarded every write and the API
    appeared to succeed while nothing persisted (found in Fase 6 acceptance).
    """
    db = SessionLocal()
    try:
        yield db
    except BaseException:
        db.rollback()
        raise
    else:
        db.commit()
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined on Base.metadata.

    Used only for development/testing convenience. In production, schema changes
    are managed exclusively through Alembic migrations (DATABASE.md section 10).
    """
    # Ensure foreign keys are pragma-on for the connection used to create tables.
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))
        Base.metadata.create_all(bind=connection)