"""Central settings, read from environment variables (or backend/.env)."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BACKEND_DIR / ".env")


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def default_database_url() -> str:
    # Absolute path, so the same database is used no matter which folder the server is started from
    return f"sqlite:///{(BACKEND_DIR / 'dev.db').as_posix()}"


def _load_secret_key() -> str:
    key = os.getenv("SECRET_KEY")
    if key:
        return key
    # No key configured: generate one once and keep it in a git-ignored file,
    # so tokens survive restarts but the key never lives in the source code.
    key_file = BACKEND_DIR / ".secret_key"
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_urlsafe(64)
    key_file.write_text(key)
    return key


DATABASE_URL = os.getenv("DATABASE_URL") or default_database_url()
SECRET_KEY = _load_secret_key()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(30 * 24 * 60)))

# Enables the "dev-token" login bypass and the /training-plans debug endpoints. Never turn on in production.
DEV_MODE = _flag("RUNCOACH_DEV_MODE")

# Comma-separated emails allowed to create training plans
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

_weather_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
OPENWEATHER_API_KEY = _weather_key if _weather_key and _weather_key != "your_api_key_here" else None
