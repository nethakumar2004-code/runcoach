import sqlite3

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app import models  # noqa: F401
from app.db import Base, engine


def test_migrations_match_the_models(client):
    """Fails if a model was changed without adding a migration.

    Fix: cd backend && alembic revision --autogenerate -m "describe the change", then review the file.
    """
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == [], f"Models and migrations differ - create a migration: {diff}"


def test_database_from_before_migrations_is_adopted(tmp_path, monkeypatch):
    """The original dev.db had tables but no migration history; startup must keep its data."""
    from app import migrations

    legacy_url = f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}"
    legacy_engine = create_engine(legacy_url)
    Base.metadata.create_all(bind=legacy_engine)
    with legacy_engine.begin() as connection:
        connection.exec_driver_sql("INSERT INTO users (id, email, password_hash) VALUES ('u1', 'old@example.com', 'x')")

    monkeypatch.setenv("DATABASE_URL", legacy_url)
    monkeypatch.setattr("app.config.DATABASE_URL", legacy_url)
    monkeypatch.setattr(migrations, "engine", legacy_engine)
    migrations.run_migrations()

    assert "alembic_version" in inspect(legacy_engine).get_table_names()
    db = sqlite3.connect(tmp_path / "legacy.db")
    assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 1
    head = ScriptDirectory.from_config(migrations.alembic_config()).get_current_head()
    assert db.execute("SELECT version_num FROM alembic_version").fetchone()[0] == head
