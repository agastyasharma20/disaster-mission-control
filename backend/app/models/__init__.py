import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import GUID


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DroneTelemetry(Base):
    __tablename__ = "drone_telemetry"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    drone_id: Mapped[str] = mapped_column(String, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    altitude_m: Mapped[float] = mapped_column(Float)
    heading_deg: Mapped[float] = mapped_column(Float)
    battery_pct: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    drone_id: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String, index=True)  # person|fire|smoke|flood_water|vehicle|collapsed_structure
    confidence: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    snapshot_url: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    detection_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("detection_events.id"), nullable=True
    )
    drone_id: Mapped[str] = mapped_column(String, index=True)
    object_type: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String, index=True)  # critical|high|medium|low
    status: Mapped[str] = mapped_column(String, default="open", index=True)  # open|acknowledged|resolved
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String)  # drop|rescue
    target_lat: Mapped[float] = mapped_column(Float)
    target_lon: Mapped[float] = mapped_column(Float)
    assigned_team: Mapped[str | None] = mapped_column(String, nullable=True)
    priority: Mapped[str] = mapped_column(String, default="medium")  # critical|high|medium|low
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    # pending|dispatched|in_progress|completed|failed
    linked_alert_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("alerts.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String)
    # Stored as a JSON-serialisable list of [lat, lon] pairs for simplicity.
    # A real PostGIS geometry column is a straightforward upgrade (see README)
    # once zone editing needs spatial queries.
    boundary: Mapped[str] = mapped_column(String)  # JSON string: [[lat,lon], ...]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=_uuid)
    text: Mapped[str] = mapped_column(String)
    zone: Mapped[str | None] = mapped_column(String, nullable=True)
    made_by: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
