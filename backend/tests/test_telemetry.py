import pytest


@pytest.mark.asyncio
async def test_post_and_get_latest_telemetry(client):
    payload = {
        "lat": 22.7196,
        "lon": 75.8577,
        "altitude_m": 120.0,
        "heading_deg": 45.0,
        "battery_pct": 87.5,
    }

    resp = await client.post("/api/telemetry/drone-01", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["drone_id"] == "drone-01"
    assert body["lat"] == payload["lat"]
    assert "id" in body and "timestamp" in body

    latest = await client.get("/api/telemetry/drone-01/latest")
    assert latest.status_code == 200
    assert latest.json()["battery_pct"] == 87.5


@pytest.mark.asyncio
async def test_latest_telemetry_returns_most_recent(client):
    # Explicit, clearly-ordered timestamps: two POSTs issued back-to-back can
    # otherwise land within the same clock tick (SQLite's DATETIME storage
    # in particular has coarser precision than a tight loop needs), which
    # would make "most recent" ambiguous rather than actually wrong.
    base = {"lat": 0.0, "lon": 0.0, "altitude_m": 100.0, "heading_deg": 0.0}

    await client.post(
        "/api/telemetry/drone-02",
        json={**base, "battery_pct": 90.0, "timestamp": "2026-01-01T00:00:00Z"},
    )
    await client.post(
        "/api/telemetry/drone-02",
        json={**base, "battery_pct": 42.0, "timestamp": "2026-01-01T00:00:05Z"},
    )

    latest = await client.get("/api/telemetry/drone-02/latest")
    assert latest.json()["battery_pct"] == 42.0


@pytest.mark.asyncio
async def test_latest_telemetry_for_unknown_drone_is_null(client):
    resp = await client.get("/api/telemetry/no-such-drone/latest")
    assert resp.status_code == 200
    assert resp.json() is None
