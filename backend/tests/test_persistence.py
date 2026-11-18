"""Prueba de persistencia entre reinicios (Fase 6, criterio de aceptación 11).

"Los datos y relaciones persisten tras cerrar y reiniciar." Se simula un
cierre (dispose del engine) y un reinicio (engine nuevo sobre el mismo
archivo) con datos sintéticos en una base temporal.
"""

from contextlib import contextmanager

from app.db.session import Base, SessionLocal, get_db
from app.modules.dashboard.models import UserPreference
from app.modules.projects.models import Project
from app.modules.tasks.models import Task
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker


def test_data_persists_across_engine_restart(tmp_path):
    """Datos, relaciones y preferencias sobreviven a un cierre/reinicio."""
    db_file = tmp_path / "restart.db"
    url = f"sqlite:///{db_file}"

    # Primer inicio: esquema + datos sintéticos
    engine1 = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    session_factory1 = sessionmaker(bind=engine1, autocommit=False, autoflush=False)
    with session_factory1() as db:
        project = Project(name="Proyecto persistente", status="active")
        db.add(project)
        db.flush()
        db.add(
            Task(
                title="Tarea persistente",
                project_id=project.id,
                status="pending",
                priority="normal",
            )
        )
        db.add(UserPreference(key="theme", value="dark"))
        db.commit()
        project_id = project.id

    # Cierre de la aplicación
    engine1.dispose()

    # Reinicio: engine y sesión nuevos sobre el mismo archivo
    engine2 = create_engine(url, connect_args={"check_same_thread": False})
    session_factory2 = sessionmaker(bind=engine2, autocommit=False, autoflush=False)
    with session_factory2() as db:
        projects = db.execute(select(Project)).scalars().all()
        assert len(projects) == 1
        assert projects[0].id == project_id
        assert projects[0].name == "Proyecto persistente"

        tasks = db.execute(select(Task)).scalars().all()
        assert len(tasks) == 1
        assert tasks[0].project_id == project_id
        assert tasks[0].title == "Tarea persistente"

        preference = db.get(UserPreference, "theme")
        assert preference is not None
        assert preference.value == "dark"
    engine2.dispose()


def test_get_db_commits_on_success():
    """get_db confirma la transacción cuando la ruta termina bien.

    Regresión de Fase 6: sin commit, Session.close() descartaba cada
    escritura y la API reportaba éxito sin persistir nada.
    """
    from app.db.activity import ActivityEvent

    ctx = contextmanager(get_db)
    with ctx() as db:
        db.add(Project(name="Debe persistir", status="active"))

    with SessionLocal() as db:
        names = [p.name for p in db.execute(select(Project)).scalars().all()]
        assert "Debe persistir" in names

    # Limpieza de la base global temporal
    with SessionLocal() as db:
        db.execute(delete(Project).where(Project.name == "Debe persistir"))
        db.execute(delete(ActivityEvent))
        db.commit()


def test_get_db_rolls_back_on_error():
    """Si la ruta falla, get_db revierte: no quedan escrituras parciales."""
    ctx = contextmanager(get_db)
    try:
        with ctx() as db:
            db.add(Project(name="No debe persistir", status="active"))
            raise RuntimeError("fallo simulado de la ruta")
    except RuntimeError:
        pass
    else:
        raise AssertionError("debió propagarse el error de la ruta")

    with SessionLocal() as db:
        names = [p.name for p in db.execute(select(Project)).scalars().all()]
        assert "No debe persistir" not in names


def test_api_writes_persist_with_real_session():
    """Un POST real con get_db (sin override de tests) queda en la base.

    Usa la sesión real de la aplicación contra la base global temporal
    (aislada por conftest), sin la sesión compartida del fixture `client`.
    """
    from app.db.activity import ActivityEvent
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="http://127.0.0.1:8000") as test_client:
        response = test_client.post(
            "/api/v1/projects",
            json={"name": "Persistencia real", "status": "active"},
        )
        assert response.status_code == 201, response.text
        project_id = response.json()["id"]

    # Sesión nueva (como sería otro proceso u otro request): el dato está.
    with SessionLocal() as db:
        stored = db.get(Project, project_id)
        assert stored is not None
        assert stored.name == "Persistencia real"

    # Limpieza de la base global temporal
    with SessionLocal() as db:
        db.execute(delete(ActivityEvent).where(ActivityEvent.entity_id == project_id))
        db.execute(delete(Project).where(Project.id == project_id))
        db.commit()
