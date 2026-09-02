from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DroneTelemetry
from app.schemas import TelemetryIn, TelemetryOut
from app.ws.manager import manager

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


@router.post("/{drone_id}", response_model=TelemetryOut)
async def ingest_telemetry(drone_id: str, body: TelemetryIn, db: AsyncSession = Depends(get_db)):
    row = DroneTelemetry(drone_id=drone_id, **body.model_dump(exclude_none=True))
    db.add(row)
    await db.commit()
    await db.refresh(row)

    out = TelemetryOut.model_validate(row)
    await manager.broadcast("telemetry", out.model_dump())
    return out


@router.get("/{drone_id}/latest", response_model=TelemetryOut | None)
async def latest_telemetry(drone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DroneTelemetry)
        .where(DroneTelemetry.drone_id == drone_id)
        .order_by(DroneTelemetry.timestamp.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return TelemetryOut.model_validate(row) if row else None
