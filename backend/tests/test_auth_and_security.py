import hashlib

from app import config
from app.models.user import User
from app.models.weather import WeatherData
from conftest import post_run, signup


def test_server_starts_on_a_fresh_database(client):
    # Used to crash: the Goal / PlannedWorkout models used a Postgres-only UUID type
    assert client.get("/runs/ping").json() == {"status": "ok"}


def test_default_database_path_does_not_depend_on_working_directory():
    url = config.default_database_url()
    assert url.startswith("sqlite:///")
    assert url.endswith("/backend/dev.db")


def test_dev_token_rejected_unless_dev_mode(client, monkeypatch):
    dev_headers = {"Authorization": "Bearer dev-token"}
    assert client.get("/auth/me", headers=dev_headers).status_code == 401

    monkeypatch.setattr(config, "DEV_MODE", True)
    assert client.get("/auth/me", headers=dev_headers).status_code == 200


def test_passwords_are_stored_with_bcrypt(client, db):
    signup(client, email="a@example.com")
    user = db.query(User).filter(User.email == "a@example.com").one()
    assert user.password_hash.startswith("$2")


def test_legacy_sha256_account_can_log_in_and_is_upgraded(client, db):
    db.add(User(email="old@example.com", name="Old", password_hash=hashlib.sha256(b"oldpassword").hexdigest()))
    db.commit()

    response = client.post("/auth/login", json={"email": "old@example.com", "password": "oldpassword"})
    assert response.status_code == 200

    db.expire_all()
    assert db.query(User).filter(User.email == "old@example.com").one().password_hash.startswith("$2")
    assert client.post("/auth/login", json={"email": "old@example.com", "password": "wrong"}).status_code == 401


def test_login_is_case_insensitive(client):
    signup(client, email="Mixed@Example.com")
    assert client.post("/auth/login", json={"email": "mixed@example.com", "password": "password123"}).status_code == 200


def test_short_password_rejected_with_readable_message(client):
    response = client.post("/auth/signup", json={"email": "b@example.com", "password": "a", "name": "B"})
    assert response.status_code == 422
    assert "at least 8 characters" in response.json()["detail"]


def test_me_works_for_user_without_name(client, db):
    headers = signup(client, email="c@example.com")
    user = db.query(User).filter(User.email == "c@example.com").one()
    user.name = None
    db.commit()
    assert client.get("/auth/me", headers=headers).status_code == 200


def test_only_admins_can_create_training_plans(client):
    plan = {"name": "x", "goal": "x", "duration_weeks": 1, "level": "beginner", "workouts": []}
    assert client.post("/training-plans/", headers=signup(client), json=plan).status_code == 403

    admin = signup(client, email="admin@example.com")
    response = client.post("/training-plans/", headers=admin, json={
        **plan,
        "workouts": [{"week_number": 1, "day_number": 1, "workout_type": "easy", "description": "Easy 3k"}],
    })
    assert response.status_code == 200, response.text
    assert len(response.json()["workouts"]) == 1


def test_debug_endpoints_hidden_outside_dev_mode(client):
    assert client.get("/training-plans/test/week/1/1").status_code == 404
    assert client.get("/training-plans/debug/user-status", headers=signup(client)).status_code == 404


def test_weather_history_only_shows_your_own_runs(client, db):
    owner = signup(client, email="owner@example.com")
    other = signup(client, email="other@example.com")
    run_id = post_run(client, owner).json()["run_id"]
    db.add(WeatherData(
        run_id=run_id, latitude=51.5, longitude=-0.1, temperature=10, feels_like=9, humidity=50,
        wind_speed=1, wind_direction=1, weather_condition="Clear", weather_description="clear",
        weather_icon="01d", location_name="Owner's street",
    ))
    db.commit()

    assert client.get("/weather/history", headers=owner).json()["total_records"] == 1
    assert client.get("/weather/history", headers=other).json()["total_records"] == 0


def test_weather_without_api_key_is_clearly_marked_and_not_stored(client, db):
    response = client.get("/weather/current?lat=51.5&lon=-0.1", headers=signup(client))
    assert response.status_code == 200
    body = response.json()
    assert body["is_mock"] is True
    assert "Sample" in body["weather"]["location_name"]
    assert db.query(WeatherData).count() == 0


def test_weather_api_failure_returns_503_not_fake_data(client, monkeypatch):
    import requests
    from app.routers import weather

    def broken(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(config, "OPENWEATHER_API_KEY", "real-key")
    monkeypatch.setattr(weather.requests, "get", broken)
    assert client.get("/weather/current?lat=51.5&lon=-0.1", headers=signup(client)).status_code == 503


def test_unknown_weather_alert_type_rejected(client):
    headers = signup(client)
    bad = client.post("/weather/alerts", headers=headers, json={"alert_type": "rain", "condition": "above", "threshold_value": 1})
    assert bad.status_code == 422
    ok = client.post("/weather/alerts", headers=headers, json={"alert_type": "wind", "condition": "above", "threshold_value": 1})
    assert ok.status_code == 200
    assert ok.json()["alert_type"] == "wind_speed"


def test_internal_errors_do_not_leak_details(client, monkeypatch):
    from app.routers import dashboard

    def explode(*args, **kwargs):
        raise RuntimeError("secret database detail")

    monkeypatch.setattr(dashboard, "rolling_loads", explode)
    response = client.get("/dashboard", headers=signup(client))
    assert response.status_code == 500
    assert "secret" not in response.text


def test_change_password(client):
    headers = signup(client, email="d@example.com")
    url = "/auth/change-password"
    assert client.post(url, headers=headers, json={"current_password": "wrong", "new_password": "newpassword1"}).status_code == 400
    assert client.post(url, headers=headers, json={"current_password": "password123", "new_password": "short"}).status_code == 422
    assert client.post(url, headers=headers, json={"current_password": "password123", "new_password": "newpassword1"}).status_code == 200
    assert client.post("/auth/login", json={"email": "d@example.com", "password": "password123"}).status_code == 401
    assert client.post("/auth/login", json={"email": "d@example.com", "password": "newpassword1"}).status_code == 200
