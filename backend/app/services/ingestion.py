"""Shared write path for telemetry and detections.

Both the REST endpoints (app/api/telemetry.py, app/api/detections.py) and the
optional MQTT listener (app/mqtt_client.py) call these two functions -- one
DB-write + WebSocket-broadcast + alerts-engine path regardless of whether a
real drone is publishing over REST or MQTT (Section 5 of the proposal).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, DetectionEvent, DroneTelemetry
from app.schemas import AlertOut, DetectionIn, DetectionOut, TelemetryIn, TelemetryOut
from app.services.alerts_engine import classify_severity, find_duplicate_alert
from app.ws.manager import manager


async def ingest_telemetry(db: AsyncSession, drone_id: str, body: TelemetryIn) -> TelemetryOut:
    row = DroneTelemetry(drone_id=drone_id, **body.model_dump(exclude_none=True))
    db.add(row)
    await db.commit()
    await db.refresh(row)

    out = TelemetryOut.model_validate(row)
    await manager.broadcast("telemetry", out.model_dump())
    return out


async def ingest_detection(db: AsyncSession, drone_id: str, body: DetectionIn) -> DetectionOut:
    detection = DetectionEvent(drone_id=drone_id, **body.model_dump(exclude_none=True))
    db.add(detection)
    await db.commit()
    await db.refresh(detection)

    detection_out = DetectionOut.model_validate(detection)
    await manager.broadcast("detection", detection_out.model_dump())

    # Alerts engine: dedup against recent same-type/same-area open alerts,
    # otherwise raise a new one (Section 4.3).
    duplicate = await find_duplicate_alert(db, detection)
    if duplicate is None:
        alert = Alert(
            detection_id=detection.id,
            drone_id=detection.drone_id,
            object_type=detection.object_type,
            severity=classify_severity(detection.object_type),
            status="open",
            lat=detection.lat,
            lon=detection.lon,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        await manager.broadcast("alert", AlertOut.model_validate(alert).model_dump())

    return detection_out
