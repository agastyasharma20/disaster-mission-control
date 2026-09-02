import pytest

from app.models import Alert, DetectionEvent
from app.services.alerts_engine import classify_severity, find_duplicate_alert


@pytest.mark.parametrize(
    "object_type,expected",
    [
        ("fire", "critical"),
        ("smoke", "high"),
        ("person", "high"),
        ("collapsed_structure", "high"),
        ("flood_water", "medium"),
        ("vehicle", "medium"),
        ("something_unlisted", "low"),
    ],
)
def test_classify_severity(object_type, expected):
    assert classify_severity(object_type) == expected


@pytest.mark.asyncio
async def test_find_duplicate_alert_matches_nearby_open_alert(db_session):
    existing = Alert(
        drone_id="drone-01",
        object_type="person",
        severity="high",
        status="open",
        lat=22.7196,
        lon=75.8577,
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)

    nearby_detection = DetectionEvent(
        drone_id="drone-01",
        object_type="person",
        confidence=0.8,
        lat=22.71965,  # ~5m away
        lon=75.8577,
    )

    duplicate = await find_duplicate_alert(db_session, nearby_detection)
    assert duplicate is not None
    assert duplicate.id == existing.id


@pytest.mark.asyncio
async def test_find_duplicate_alert_ignores_far_away_alert(db_session):
    existing = Alert(
        drone_id="drone-01",
        object_type="person",
        severity="high",
        status="open",
        lat=22.7196,
        lon=75.8577,
    )
    db_session.add(existing)
    await db_session.commit()

    far_detection = DetectionEvent(
        drone_id="drone-01",
        object_type="person",
        confidence=0.8,
        lat=22.73,  # >1km away
        lon=75.8577,
    )

    assert await find_duplicate_alert(db_session, far_detection) is None


@pytest.mark.asyncio
async def test_find_duplicate_alert_ignores_resolved_alert(db_session):
    resolved = Alert(
        drone_id="drone-01",
        object_type="person",
        severity="high",
        status="resolved",
        lat=22.7196,
        lon=75.8577,
    )
    db_session.add(resolved)
    await db_session.commit()

    same_spot = DetectionEvent(
        drone_id="drone-01", object_type="person", confidence=0.8, lat=22.7196, lon=75.8577
    )

    assert await find_duplicate_alert(db_session, same_spot) is None
