import pytest


def _detection(object_type: str, lat: float = 22.7196, lon: float = 75.8577, confidence: float = 0.9):
    return {"object_type": object_type, "confidence": confidence, "lat": lat, "lon": lon}


@pytest.mark.asyncio
async def test_fire_detection_raises_critical_alert(client):
    resp = await client.post("/api/detections/drone-01", json=_detection("fire"))
    assert resp.status_code == 200

    alerts = (await client.get("/api/alerts")).json()
    assert len(alerts) == 1
    assert alerts[0]["object_type"] == "fire"
    assert alerts[0]["severity"] == "critical"
    assert alerts[0]["status"] == "open"


@pytest.mark.asyncio
async def test_unmapped_object_type_defaults_to_low_severity(client):
    await client.post("/api/detections/drone-01", json=_detection("debris"))
    alerts = (await client.get("/api/alerts")).json()
    assert alerts[0]["severity"] == "low"


@pytest.mark.asyncio
async def test_repeated_nearby_detection_is_deduped_into_one_alert(client):
    await client.post("/api/detections/drone-01", json=_detection("person", lat=22.7196, lon=75.8577))
    # Same object type, same drone, ~11m away, well inside the 50m dedup radius.
    await client.post("/api/detections/drone-01", json=_detection("person", lat=22.71969, lon=75.8577))

    alerts = (await client.get("/api/alerts")).json()
    assert len(alerts) == 1


@pytest.mark.asyncio
async def test_detection_far_away_creates_a_separate_alert(client):
    await client.post("/api/detections/drone-01", json=_detection("person", lat=22.7196, lon=75.8577))
    # ~1.1km away -- well outside the dedup radius.
    await client.post("/api/detections/drone-01", json=_detection("person", lat=22.7296, lon=75.8577))

    alerts = (await client.get("/api/alerts")).json()
    assert len(alerts) == 2


@pytest.mark.asyncio
async def test_different_drone_does_not_dedup(client):
    await client.post("/api/detections/drone-01", json=_detection("person"))
    await client.post("/api/detections/drone-02", json=_detection("person"))

    alerts = (await client.get("/api/alerts")).json()
    assert len(alerts) == 2


@pytest.mark.asyncio
async def test_alerts_filterable_by_severity(client):
    await client.post("/api/detections/drone-01", json=_detection("fire"))
    await client.post("/api/detections/drone-01", json=_detection("vehicle", lat=22.73, lon=75.9))

    critical = (await client.get("/api/alerts", params={"severity": "critical"})).json()
    assert len(critical) == 1
    assert critical[0]["object_type"] == "fire"


@pytest.mark.asyncio
async def test_acknowledge_alert(client):
    await client.post("/api/detections/drone-01", json=_detection("fire"))
    alert_id = (await client.get("/api/alerts")).json()[0]["id"]

    resp = await client.patch(f"/api/alerts/{alert_id}", json={"status": "acknowledged"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_acknowledge_unknown_alert_404s(client):
    resp = await client.patch(
        "/api/alerts/00000000-0000-0000-0000-000000000000", json={"status": "acknowledged"}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_acknowledge_malformed_alert_id_422s(client):
    resp = await client.patch("/api/alerts/not-a-uuid", json={"status": "acknowledged"})
    assert resp.status_code == 422
