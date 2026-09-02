from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Alert
from app.schemas import AlertOut, AlertUpdate
from app.ws.manager import manager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    severity: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Alert).order_by(Alert.created_at.desc())
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(alert_id: UUID, body: AlertUpdate, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = body.status
    await db.commit()
    await db.refresh(alert)
    out = AlertOut.model_validate(alert)
    await manager.broadcast("alert_updated", out.model_dump())
    return out
