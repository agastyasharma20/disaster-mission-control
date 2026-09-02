from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import DetectionIn, DetectionOut
from app.services.ingestion import ingest_detection

router = APIRouter(prefix="/api/detections", tags=["detections"])


@router.post("/{drone_id}", response_model=DetectionOut)
async def post_detection(drone_id: str, body: DetectionIn, db: AsyncSession = Depends(get_db)):
    """Ingest one AI detection event (Section 4.2/4.3).

    Called by edge-inference/simulate_drone.py in dev, or by
    edge-inference/detect.py from a real Jetson Nano in production -- the
    payload shape is identical either way (config.AI_SOURCE just changes
    who's calling). The MQTT path (app/mqtt_client.py) writes through the
    same app.services.ingestion.ingest_detection() this calls.
    """
    return await ingest_detection(db, drone_id, body)
