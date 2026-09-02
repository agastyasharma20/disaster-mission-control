import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Alert, DetectionEvent

# Section 4.3: severity rules. Anything not listed defaults to "low".
SEVERITY_RULES: dict[str, str] = {
    "fire": "critical",
    "smoke": "high",
    "person": "high",
    "collapsed_structure": "high",
    "flood_water": "medium",
    "vehicle": "medium",
}


def classify_severity(object_type: str) -> str:
    return SEVERITY_RULES.get(object_type, "low")


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Equirectangular approximation -- good enough at disaster-zone scale
    (a few km) and avoids pulling in a geo library for the demo."""
    r = 6371000.0
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    y = math.radians(lat2 - lat1)
    return math.sqrt(x * x + y * y) * r


async def find_duplicate_alert(db: AsyncSession, detection: DetectionEvent) -> Alert | None:
    """Collapse repeated detections of the same object into one alert if a
    same-type, same-drone alert already exists nearby and recently (Section 4.3)."""
    window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.dedup_window_seconds)
    result = await db.execute(
        select(Alert)
        .where(
            Alert.drone_id == detection.drone_id,
            Alert.object_type == detection.object_type,
            Alert.status == "open",
            Alert.created_at >= window_start,
        )
        .order_by(Alert.created_at.desc())
    )
    for candidate in result.scalars():
        if _distance_m(candidate.lat, candidate.lon, detection.lat, detection.lon) <= settings.dedup_radius_m:
            return candidate
    return None
