from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db():
    """Create tables if they don't exist. Fine for a minor-project demo;
    swap for Alembic migrations if this ever goes to production."""
    from app import models  # noqa: F401 -- ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
