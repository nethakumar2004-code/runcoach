import pytest

from app.models.training_plan import TrainingLevel, TrainingPlan, TrainingWorkout, WorkoutType
from conftest import signup


@pytest.fixture()
def plan_ids(db):
    plan = TrainingPlan(name="5K", goal="Finish a 5K", duration_weeks=4, level=TrainingLevel.BEGINNER)
    db.add(plan)
    db.flush()
    workout = TrainingWorkout(
        training_plan_id=plan.id, week_number=1, day_number=1,
        workout_type=WorkoutType.EASY, description="Easy 3 km",
    )
    db.add(workout)
    db.commit()
    return plan.id, workout.id


def test_plan_detail_includes_workouts(client, plan_ids):
    plan_id, _ = plan_ids
    assert len(client.get(f"/training-plans/{plan_id}").json()["workouts"]) == 1


def test_plan_list_filters_by_level(client, plan_ids):
    assert len(client.get("/training-plans/?level=beginner").json()) == 1
    assert client.get("/training-plans/?level=advanced").json() == []
    assert client.get("/training-plans/?level=nonsense").status_code == 400


def test_full_training_plan_flow(client, plan_ids):
    plan_id, workout_id = plan_ids
    headers = signup(client)

    assert client.post(f"/training-plans/enroll/{plan_id}", headers=headers).status_code == 200

    current = client.get("/training-plans/my/current", headers=headers)
    assert current.status_code == 200, current.text
    assert current.json()["training_plan"]["name"] == "5K"

    progress = client.get("/training-plans/my/progress", headers=headers)
    assert progress.status_code == 200
    assert progress.json()["total_weeks"] == 4

    week = client.get("/training-plans/my/week/1", headers=headers)
    assert week.status_code == 200
    assert week.json()["completed_count"] == 0

    done = client.post(f"/training-plans/workouts/{workout_id}/complete", headers=headers, json={"effort_rating": 4})
    assert done.status_code == 200, done.text
    assert done.json()["workout"]["id"] == workout_id

    again = client.post(f"/training-plans/workouts/{workout_id}/complete", headers=headers, json={})
    assert again.status_code == 400

    assert client.get("/training-plans/my/week/1", headers=headers).json()["completed_count"] == 1

    moved = client.put("/training-plans/my/week?week_number=2", headers=headers)
    assert moved.status_code == 200
    assert moved.json()["current_week"] == 2
    assert client.put("/training-plans/my/week?week_number=9", headers=headers).status_code == 400


def test_no_active_plan_is_404_not_500(client):
    headers = signup(client)
    for path in ("/training-plans/my/current", "/training-plans/my/progress", "/training-plans/my/week/1"):
        assert client.get(path, headers=headers).status_code == 404, path


def test_invalid_effort_rating_rejected(client, plan_ids):
    plan_id, workout_id = plan_ids
    headers = signup(client)
    client.post(f"/training-plans/enroll/{plan_id}", headers=headers)
    response = client.post(f"/training-plans/workouts/{workout_id}/complete", headers=headers, json={"effort_rating": 50})
    assert response.status_code == 422
