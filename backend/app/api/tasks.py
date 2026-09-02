from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskOut, TaskUpdate
from app.ws.manager import manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(status: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Task).order_by(Task.created_at.desc())
    if status:
        query = query.where(Task.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=TaskOut)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(status="pending", **body.model_dump(exclude_none=True))
    db.add(task)
    await db.commit()
    await db.refresh(task)
    out = TaskOut.model_validate(task)
    await manager.broadcast("task", out.model_dump())
    return out


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: UUID, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    out = TaskOut.model_validate(task)
    await manager.broadcast("task_updated", out.model_dump())
    return out
