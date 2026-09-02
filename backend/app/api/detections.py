from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Alert, DetectionEvent
from app.schemas import AlertOut, DetectionIn, DetectionOut
from app.services.alerts_engine import classify_severity, find_duplicate_alert
from app.ws.manager import manager

router = APIRouter(prefix="/api/detections", tags=["detections"])


@router.post("/{drone_id}", response_model=DetectionOut)
async def ingest_detection(drone_id: str, body: DetectionIn, db: AsyncSession = Depends(get_db)):
    """Ingest one AI detection event (Section 4.2/4.3).

    Called by edge-inference/simulate_drone.py in dev, or by
    edge-inference/detect.py from a real Jetson Nano in production -- the
    payload shape is identical either way (config.AI_SOURCE just changes
    who's calling).
    """
    detection = DetectionEvent(drone_id=drone_id, **body.model_dump(exclude_none=True))
    db.add(detection)
    await db.commit()
    await db.refresh(detection)

    detection_out = DetectionOut.model_validate(detection)
    await manager.broadcast("detection", detection_out.model_dump())

    # Alerts engine: dedup against recent same-type/same-area open alerts,
    # otherwise raise a new one.
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
