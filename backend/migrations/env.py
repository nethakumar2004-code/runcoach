from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import config as app_config
from app import models  # noqa: F401  registers every table on Base.metadata
from app.db import Base

config = context.config

# The database URL always comes from the app settings (DATABASE_URL / backend/.env), never alembic.ini
config.set_main_option("sqlalchemy.url", app_config.DATABASE_URL)

# When migrations run inside the server, keep the server's logging setup
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Databases created before migrations existed declared these id columns as Postgres UUID.
# SQLite stores them as plain text either way, so don't report them as a change to migrate.
LEGACY_UUID_COLUMNS = {
    ("goals", "id"), ("goals", "user_id"),
    ("planned_workouts", "id"), ("planned_workouts", "user_id"), ("planned_workouts", "goal_id"),
}


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    if (metadata_column.table.name, metadata_column.name) in LEGACY_UUID_COLUMNS:
        return False
    return None  # default comparison for everything else


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        compare_type=compare_type,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite can't ALTER most columns; batch mode rebuilds the table instead
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
            render_as_batch=True,  # SQLite can't ALTER most columns; batch mode rebuilds the table instead
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
