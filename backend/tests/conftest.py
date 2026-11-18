"""Pytest configuration for Life OS backend tests.

Uses a temporary SQLite database so the user's personal database is never
touched (AGENTS.md section 5, DATABASE.md section 11).
"""

import os
import tempfile

import pytest
from app.db.session import Base, _enable_foreign_keys
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker


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