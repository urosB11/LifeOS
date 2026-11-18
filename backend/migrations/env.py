from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, event, text
from alembic import context

# Alembic configuration object, provides access to values in alembic.ini.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support.
# Las tablas de dominio se gestionan con migraciones versionadas; target_metadata
# se deja None para no depender de autogenerate en esta fase.
target_metadata = None


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
        compare_type=True,
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

    with connectable.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys = ON"))

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()