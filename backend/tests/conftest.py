"""Pytest configuration for Life OS backend tests.

Uses a temporary SQLite database so the user's personal database is never
touched (AGENTS.md section 5, DATABASE.md section 11).
"""

import atexit
import os
import shutil
import tempfile

# AGENTS.md section 5: tests must NEVER touch the personal database.
# LIFEOS_DATA_DIR must be set BEFORE importing any app module, because the
# global engine and the cached settings read it at import time. The backup
# and restore endpoints use the app-global engine, so without this isolation
# they would read and write %LOCALAPPDATA%\\LifeOS\\lifeos.db during test runs.
_TEST_DATA_DIR = tempfile.mkdtemp(prefix="lifeos_test_data_")
os.environ["LIFEOS_DATA_DIR"] = _TEST_DATA_DIR
atexit.register(shutil.rmtree, _TEST_DATA_DIR, ignore_errors=True)

import pytest  # noqa: E402
from app.db.session import Base, _enable_foreign_keys, engine  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _global_engine_schema():
    """Create the schema on the app-global engine (isolated temp database).

    The backup/restore endpoints operate on the app-global engine, so that
    engine needs a real schema outside the per-test fixture database.
    """
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture(scope="session")
def tmp_db_path():
    """Create a temporary SQLite database file for the test session."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def db(tmp_db_path):
    """Create a fresh database schema for each test function using a temp DB."""
    database_url = f"sqlite:///{tmp_db_path}"
    test_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    event.listen(test_engine, "connect", _enable_foreign_keys)
    test_session_local = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        class_=Session,
    )

    # Ensure foreign keys pragma and create schema.
    with test_engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))
        Base.metadata.create_all(bind=connection)

    connection = test_engine.connect()
    transaction = connection.begin()
    session = test_session_local(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def client(db):
    """FastAPI TestClient wired to the temporary database session."""

    def override_get_db():
        yield db

    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://127.0.0.1:8000") as test_client:
        yield test_client
    app.dependency_overrides.clear()