import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Zone
from app.schemas import ZoneCreate, ZoneOut

router = APIRouter(prefix="/api/zones", tags=["zones"])


def _to_out(zone: Zone) -> ZoneOut:
    return ZoneOut(
        id=zone.id, name=zone.name, boundary=json.loads(zone.boundary), created_at=zone.created_at
    )


@router.get("", response_model=list[ZoneOut])
async def list_zones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone))
    return [_to_out(z) for z in result.scalars().all()]


@router.post("", response_model=ZoneOut)
async def create_zone(body: ZoneCreate, db: AsyncSession = Depends(get_db)):
    zone = Zone(name=body.name, boundary=json.dumps(body.boundary))
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return _to_out(zone)
