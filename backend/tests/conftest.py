import os
import tempfile
from pathlib import Path

# Settings must be in place before the app is imported (load_dotenv never overrides these)
_TEST_DB = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["RUNCOACH_DEV_MODE"] = "0"
os.environ["OPENWEATHER_API_KEY"] = ""
os.environ["ADMIN_EMAILS"] = "admin@example.com"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app, raise_server_exceptions=False) as test_client:  # runs startup: tables + achievements
        yield test_client


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def signup(client, email="runner@example.com", name="Runner", password="password123"):
    response = client.post("/auth/signup", json={"email": email, "password": password, "name": name})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def post_run(client, headers, **overrides):
    run = {"start_datetime": days_ago(1), "distance_km": 5.0, "duration_sec": 1500, "rpe": 5}
    run.update(overrides)
    return client.post("/runs/", headers=headers, json=run)


def days_ago(days, hour=7):
    """ISO timestamp for `days` days ago at the given UTC hour."""
    from datetime import timedelta
    from app.timeutils import utcnow
    moment = (utcnow() - timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return moment.isoformat() + "Z"
