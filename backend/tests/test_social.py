import json

from conftest import days_ago, post_run, signup


def make_friends(client, a_headers, b_headers, b_email):
    client.post("/social/friends/request", headers=a_headers, json={"email": b_email})
    request_id = client.get("/social/friends", headers=b_headers).json()["pending_requests"][0]["id"]
    assert client.post(f"/social/friends/{request_id}/accept", headers=b_headers).status_code == 200


def test_friends_list_has_no_duplicates(client):
    a = signup(client, email="a@example.com")
    b = signup(client, email="b@example.com")
    for i in range(3):  # extra users used to multiply every friend in the list
        signup(client, email=f"extra{i}@example.com")
    make_friends(client, a, b, "b@example.com")

    friends = client.get("/social/friends", headers=a).json()["friends"]
    assert len(friends) == 1
    assert friends[0]["friend_email"] == "b@example.com"


def test_runs_and_achievements_appear_in_friends_feed(client):
    a = signup(client, email="a@example.com")
    b = signup(client, email="b@example.com")
    make_friends(client, a, b, "b@example.com")
    post_run(client, a)

    feed = client.get("/social/feed", headers=b).json()
    types = {item["activity_type"] for item in feed}
    assert "run_completed" in types and "achievement_earned" in types
    run_item = next(item for item in feed if item["activity_type"] == "run_completed")
    assert json.loads(run_item["activity_data"])["distance_km"] == 5.0


def test_strangers_cannot_see_or_like_activities(client):
    a = signup(client, email="a@example.com")
    stranger = signup(client, email="s@example.com")
    post_run(client, a)
    activity_id = client.get("/social/feed", headers=a).json()[0]["id"]

    assert client.get("/social/feed", headers=stranger).json() == []
    assert client.post(f"/social/activities/{activity_id}/like", headers=stranger).status_code == 404


def test_likes_and_comments(client):
    a = signup(client, email="a@example.com")
    b = signup(client, email="b@example.com")
    make_friends(client, a, b, "b@example.com")
    post_run(client, a)
    activity_id = client.get("/social/feed", headers=b).json()[0]["id"]

    assert client.post(f"/social/activities/{activity_id}/like", headers=b).json()["liked"] is True
    comment = client.post(f"/social/activities/{activity_id}/comments", headers=b, json={"comment_text": "Nice run!"})
    assert comment.status_code == 200

    item = next(i for i in client.get("/social/feed", headers=a).json() if i["id"] == activity_id)
    assert item["likes_count"] == 1 and item["comments_count"] == 1
    assert client.get(f"/social/activities/{activity_id}/comments", headers=a).json()[0]["comment_text"] == "Nice run!"


def test_kudos(client):
    a = signup(client, email="a@example.com")
    b = signup(client, email="b@example.com")
    make_friends(client, a, b, "b@example.com")
    run_id = post_run(client, a).json()["run_id"]

    assert client.post(f"/social/runs/{run_id}/kudos", headers=a).status_code == 400  # not your own run
    given = client.post(f"/social/runs/{run_id}/kudos", headers=b).json()
    assert given == {"run_id": run_id, "given": True, "kudos_count": 1}
    assert client.get("/social/stats", headers=a).json()["kudos_received"] == 1
    assert client.get(f"/social/runs/{run_id}/kudos", headers=a).json()[0]["giver_id"]


def test_challenge_progress_updates_after_runs(client):
    a = signup(client)
    challenge = client.post("/social/challenges", headers=a, json={
        "name": "10 km week", "challenge_type": "distance", "target_value": 10,
        "start_date": days_ago(3), "end_date": days_ago(-7),
    })
    assert challenge.status_code == 200, challenge.text

    post_run(client, a, start_datetime=days_ago(1))
    mine = client.get("/social/challenges", headers=a).json()[0]
    assert mine["user_progress"] == 5 and mine["user_completed"] is False

    post_run(client, a, start_datetime=days_ago(0, hour=0))
    mine = client.get("/social/challenges", headers=a).json()[0]
    assert mine["user_progress"] == 10 and mine["user_completed"] is True


def test_challenge_validation(client):
    response = client.post("/social/challenges", headers=signup(client), json={
        "name": "bad", "challenge_type": "jumping", "target_value": -1,
        "start_date": days_ago(0), "end_date": days_ago(5),
    })
    assert response.status_code == 422


def test_leaderboard_uses_weighted_pace(client):
    a = signup(client)
    post_run(client, a, start_datetime=days_ago(0, hour=0), distance_km=1, duration_sec=240)    # 4:00/km
    post_run(client, a, start_datetime=days_ago(0, hour=0), distance_km=9, duration_sec=9 * 360)  # 6:00/km
    entry = client.get("/social/leaderboard/weekly", headers=a).json()["entries"][0]
    assert entry["total_distance"] == 10
    assert round(entry["avg_pace"]) == 348  # total time / total distance, not the mean of 240 and 360
