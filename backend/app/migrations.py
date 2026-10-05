"""Bring the database schema up to date with Alembic (runs on server startup)."""
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.config import BACKEND_DIR
from app.db import Base, engine

logger = logging.getLogger(__name__)

# The first migration: the schema as it was before Alembic was added
BASELINE_REVISION = "9691de8e55d1"
BASELINE_TABLES = {
    "achievements", "activity_comments", "activity_feed", "activity_likes", "challenge_participants",
    "challenges", "completed_runs", "friendships", "goals", "kudos", "planned_workouts", "training_plans",
    "training_workouts", "user_achievements", "user_stats", "user_training_plans", "user_workout_completions",
    "users", "weather_alerts", "weather_data",
}


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.attributes["configure_logger"] = False
    return cfg


def run_migrations() -> None:
    cfg = alembic_config()
    tables = set(inspect(engine).get_table_names())

    if "alembic_version" not in tables and "users" in tables:
        # A database created before migrations existed (like the original dev.db).
        # Fill in any missing baseline tables (only those - later tables belong to later migrations),
        # then record it as being at the baseline so Alembic doesn't recreate what's already there.
        logger.info("Existing database without migration history: marking it as baseline %s", BASELINE_REVISION)
        baseline = [t for name, t in Base.metadata.tables.items() if name in BASELINE_TABLES]
        Base.metadata.create_all(bind=engine, tables=baseline)
        command.stamp(cfg, BASELINE_REVISION)

    command.upgrade(cfg, "head")
