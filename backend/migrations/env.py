from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, event, pool

from app.db import activity as _activity_models  # noqa: F401
from app.db.base import Base
from app.modules.dashboard import models as _dashboard_models  # noqa: F401
from app.modules.habits import models as _habit_models  # noqa: F401
from app.modules.mind import models as _mind_models  # noqa: F401
from app.modules.notes import models as _note_models  # noqa: F401
from app.modules.projects import models as _project_models  # noqa: F401
from app.modules.tasks import models as _task_models  # noqa: F401

# Alembic configuration object, provides access to values in alembic.ini.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata para `alembic check`. Las tablas de dominio siguen siendo
# gestionadas por migraciones versionadas; este metadata solo permite
# comparar el esquema aplicado con el ORM.
target_metadata = Base.metadata


def _get_database_url() -> str:
    """Obtiene la URL de base de datos de la configuración de la app.

    Así Alembic y la aplicación usan exactamente la misma base de datos
    (DATABASE.md sección 11).
    """
    from app.core.config import get_settings

    return get_settings().database_url


def _enable_foreign_keys(dbapi_connection, connection_record):
    """Activate PRAGMA foreign_keys = ON on every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite representa Boolean como INTEGER; la comparación de tipos
        # produciría un falso positivo para `widget_preferences.is_visible`.
        compare_type=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Usa la misma URL de base de datos que la aplicación para que las
    migraciones se apliquen sobre la base real, no sobre una relativa a alembic.ini.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    event.listen(connectable, "connect", _enable_foreign_keys)

    # IMPORTANTE: no ejecutar ninguna sentencia (ni PRAGMA ni SELECT) sobre la
    # conexión antes de context.configure(). Cualquier sentencia deja la
    # conexión "en transacción" a ojos de SQLAlchemy, Alembic detecta
    # _in_external_transaction=True y begin_transaction() queda como
    # nullcontext(): Alembic nunca confirma alembic_version ni el DDL
    # posterior al primer INSERT se pierde al cerrar la conexión
    # (upgrade head reportaba éxito sin registrar la versión).
    # Las claves foráneas ya se habilitan en el evento "connect" de arriba.
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite representa Boolean como INTEGER; la comparación de tipos
        # produciría un falso positivo para `widget_preferences.is_visible`.
        compare_type=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()