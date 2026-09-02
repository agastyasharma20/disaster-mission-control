import pytest


@pytest.mark.asyncio
async def test_create_and_list_task(client):
    resp = await client.post(
        "/api/tasks",
        json={"type": "drop", "target_lat": 22.72, "target_lon": 75.86, "priority": "high"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending"
    assert body["type"] == "drop"

    tasks = (await client.get("/api/tasks")).json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_task_status_lifecycle(client):
    created = (
        await client.post(
            "/api/tasks", json={"type": "rescue", "target_lat": 0.0, "target_lon": 0.0}
        )
    ).json()

    for next_status in ["dispatched", "in_progress", "completed"]:
        resp = await client.patch(f"/api/tasks/{created['id']}", json={"status": next_status})
        assert resp.status_code == 200
        assert resp.json()["status"] == next_status


@pytest.mark.asyncio
async def test_list_tasks_filterable_by_status(client):
    await client.post("/api/tasks", json={"type": "drop", "target_lat": 0.0, "target_lon": 0.0})
    second = (
        await client.post("/api/tasks", json={"type": "rescue", "target_lat": 1.0, "target_lon": 1.0})
    ).json()
    await client.patch(f"/api/tasks/{second['id']}", json={"status": "dispatched"})

    pending = (await client.get("/api/tasks", params={"status": "pending"})).json()
    assert len(pending) == 1
    assert pending[0]["type"] == "drop"


@pytest.mark.asyncio
async def test_task_linked_to_alert(client):
    await client.post(
        "/api/detections/drone-01",
        json={"object_type": "fire", "confidence": 0.9, "lat": 22.72, "lon": 75.86},
    )
    alert = (await client.get("/api/alerts")).json()[0]

    task = (
        await client.post(
            "/api/tasks",
            json={
                "type": "rescue",
                "target_lat": alert["lat"],
                "target_lon": alert["lon"],
                "priority": alert["severity"],
                "linked_alert_id": alert["id"],
            },
        )
    ).json()
    assert task["linked_alert_id"] == alert["id"]


@pytest.mark.asyncio
async def test_update_unknown_task_404s(client):
    resp = await client.patch(
        "/api/tasks/00000000-0000-0000-0000-000000000000", json={"status": "dispatched"}
    )
    assert resp.status_code == 404
