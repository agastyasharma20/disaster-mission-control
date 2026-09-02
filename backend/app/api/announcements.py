from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Announcement
from app.schemas import AnnouncementCreate, AnnouncementOut
from app.ws.manager import manager

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

# Section 4.6: v1 is a manual log. Wiring this to real TTS + PA hardware is a
# stretch goal (Section 11) -- swap the POST handler's side effect for a
# hardware call without touching the schema or the dashboard.


@router.get("", response_model=list[AnnouncementOut])
async def list_announcements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Announcement).order_by(Announcement.timestamp.desc()))
    return result.scalars().all()


@router.post("", response_model=AnnouncementOut)
async def create_announcement(body: AnnouncementCreate, db: AsyncSession = Depends(get_db)):
    row = Announcement(**body.model_dump(exclude_none=True))
    db.add(row)
    await db.commit()
    await db.refresh(row)
    out = AnnouncementOut.model_validate(row)
    await manager.broadcast("announcement", out.model_dump())
    return out
