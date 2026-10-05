from datetime import date, timedelta

from app.models.run import CompletedRun
from app.services.achievements import calculate_streaks
from conftest import days_ago, post_run, signup


def earned_names(client, headers):
    profile = client.get("/achievements/profile", headers=headers).json()
    return {b["achievement"]["name"] for b in profile["badge_progress"] if b["is_earned"]}


def test_saving_a_run_returns_200_and_saves_it_once(client, db):
    headers = signup(client)
    response = post_run(client, headers)
    assert response.status_code == 200, response.text
    assert db.query(CompletedRun).count() == 1


def test_run_without_rpe_counts_the_same_load_everywhere(client):
    headers = signup(client)
    saved = post_run(client, headers, rpe=None).json()
    assert saved["training_load"] == 125.0  # 25 min x default RPE 5

    assert client.get("/dashboard", headers=headers).json()["total_load_7d"] == 125.0
    assert client.get("/runs/", headers=headers).json()[0]["training_load"] == 125.0
    assert client.get("/weekly_loads", headers=headers).json()["days"][0]["load"] == 125.0


def test_run_response_has_real_rolling_loads(client):
    headers = signup(client)
    post_run(client, headers, start_datetime=days_ago(10))
    response = post_run(client, headers, start_datetime=days_ago(1)).json()
    assert response["load_7_day"] == 125.0
    assert response["load_28_day"] == 250.0


def test_acwr_needs_four_weeks_of_history(client):
    headers = signup(client)
    post_run(client, headers)
    assert client.get("/dashboard", headers=headers).json()["acwr"] is None

    post_run(client, headers, start_datetime=days_ago(30))
    post_run(client, headers, start_datetime=days_ago(20))
    assert client.get("/dashboard", headers=headers).json()["acwr"] is not None


def test_impossible_runs_are_rejected(client):
    headers = signup(client)
    assert post_run(client, headers, rpe=99).status_code == 422
    assert post_run(client, headers, distance_km=0).status_code == 422
    assert post_run(client, headers, duration_sec=0).status_code == 422
    too_fast = post_run(client, headers, distance_km=5, duration_sec=300)  # 1:00/km
    assert too_fast.status_code == 422
    assert "Unrealistic pace" in too_fast.json()["detail"]


def test_tiny_run_cannot_unlock_speed_badges(client):
    headers = signup(client)
    assert post_run(client, headers, distance_km=0.02, duration_sec=1).status_code == 200
    earned = earned_names(client, headers)
    assert "Speed Demon" not in earned and "Lightning Fast" not in earned


def test_real_fast_run_unlocks_speed_badge(client):
    headers = signup(client)
    post_run(client, headers, distance_km=5, duration_sec=5 * 230)  # 3:50/km
    assert "Speed Demon" in earned_names(client, headers)


def test_achievements_awarded_when_run_is_saved(client):
    headers = signup(client)
    response = post_run(client, headers).json()
    assert "First Steps" in response["new_achievements"]
    assert "5K Hero" in response["new_achievements"]


def test_streak_badges_unlock(client):
    headers = signup(client)
    for day in (2, 1, 0):
        post_run(client, headers, start_datetime=days_ago(day, hour=0))
    profile = client.get("/achievements/profile", headers=headers).json()
    assert profile["stats"]["current_streak_days"] == 3
    assert "Consistent Runner" in earned_names(client, headers)


def test_more_than_ten_badges_all_show_as_earned(client):
    headers = signup(client)
    # 11 days in a row of 5 km at 3:25/km, then a 50 km run: 12-day streak, 105 km total
    for day in range(11, 0, -1):
        post_run(client, headers, start_datetime=days_ago(day), distance_km=5, duration_sec=5 * 205)
    post_run(client, headers, start_datetime=days_ago(0, hour=0), distance_km=50, duration_sec=4 * 3600)
    profile = client.get("/achievements/profile", headers=headers).json()
    total_earned = len(client.get("/achievements/achievements", headers=headers).json())
    assert total_earned > 10
    assert sum(b["is_earned"] for b in profile["badge_progress"]) == total_earned


def test_calculate_streaks():
    today = date(2026, 1, 10)
    assert calculate_streaks([], today) == (0, 0)
    assert calculate_streaks([today - timedelta(days=i) for i in range(3)], today) == (3, 3)
    # Ran yesterday but not yet today: streak still alive
    assert calculate_streaks([today - timedelta(days=1), today - timedelta(days=2)], today) == (2, 2)
    # Last run 3 days ago: streak broken, longest kept
    assert calculate_streaks([today - timedelta(days=d) for d in (3, 4, 5, 6)], today) == (0, 4)


def test_start_time_with_offset_is_stored_as_utc(client, db):
    headers = signup(client)
    post_run(client, headers, start_datetime="2026-01-05T12:30:00+05:30")
    assert db.query(CompletedRun).one().start_datetime.isoformat() == "2026-01-05T07:00:00"


def test_analytics_handles_runs_without_saved_load(client, db):
    headers = signup(client)
    post_run(client, headers, start_datetime=days_ago(3))
    post_run(client, headers, start_datetime=days_ago(10))
    db.query(CompletedRun).update({CompletedRun.training_load: None})
    db.commit()
    assert client.get("/analytics/advanced", headers=headers).status_code == 200


def test_race_predictions_use_riegel(client):
    headers = signup(client)
    post_run(client, headers, distance_km=5, duration_sec=1500)  # 25:00 5K
    predictions = {p["distance"]: p["predicted_time"] for p in client.get("/analytics/advanced", headers=headers).json()["race_predictions"]}
    assert predictions["5K"] == "25:00"
    assert predictions["10K"] == "52:07"  # 1500 x 2^1.06


def test_short_run_is_not_a_5k_record(client):
    headers = signup(client)
    post_run(client, headers, distance_km=4.5, duration_sec=1350)
    records = client.get("/analytics/advanced", headers=headers).json()["personal_records"]
    assert records["fastest_5k"] is None


def test_runs_list_supports_paging(client):
    headers = signup(client)
    for day in range(3):
        post_run(client, headers, start_datetime=days_ago(day + 1))
    assert len(client.get("/runs/?limit=2", headers=headers).json()) == 2
    assert len(client.get("/runs/?skip=2&limit=2", headers=headers).json()) == 1


def test_real_phone_data_is_accepted(client, db):
    """iOS sends speed -1 m/s when unknown; no HR strap gives 0 bpm; RPE 0 means not set."""
    headers = signup(client)
    point = {"lat": 51.5, "lng": -0.1, "timestamp": days_ago(1), "speed": -3.6}
    response = post_run(client, headers, gps_route=[point, point], avg_hr=0, rpe=0, max_speed_kmh=-3.6, weight_kg=0)
    assert response.status_code == 200, response.text
    assert response.json()["training_load"] == 125.0  # RPE 0 treated as unset -> default 5

    run = db.query(CompletedRun).one()
    assert run.gps_route[0]["speed"] is None
    assert run.avg_hr is None and run.max_speed_kmh is None


def test_previously_stored_odd_data_still_loads(client, db):
    headers = signup(client)
    run_id = post_run(client, headers).json()["run_id"]
    run = db.query(CompletedRun).filter(CompletedRun.id == run_id).one()
    run.gps_route = [{"lat": 51.5, "lng": -0.1, "timestamp": "2026-01-01T07:00:00", "elevation": None, "speed": -3.6}]
    run.hr_data = [{"bpm": 300, "timestamp": "2026-01-01T07:00:00", "zone": "max"}]
    db.commit()
    assert client.get(f"/runs/{run_id}", headers=headers).status_code == 200
