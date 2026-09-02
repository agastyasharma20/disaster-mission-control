from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TelemetryIn(BaseModel):
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    battery_pct: float
    timestamp: datetime | None = None


class TelemetryOut(TelemetryIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    drone_id: str
    timestamp: datetime


class DetectionIn(BaseModel):
    object_type: str
    confidence: float
    lat: float
    lon: float
    snapshot_url: str | None = None
    timestamp: datetime | None = None


class DetectionOut(DetectionIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    drone_id: str
    timestamp: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    detection_id: UUID | None
    drone_id: str
    object_type: str
    severity: str
    status: str
    lat: float
    lon: float
    created_at: datetime


class AlertUpdate(BaseModel):
    status: str  # open|acknowledged|resolved


class TaskCreate(BaseModel):
    type: str  # drop|rescue
    target_lat: float
    target_lon: float
    assigned_team: str | None = None
    priority: str = "medium"
    linked_alert_id: UUID | None = None


class TaskUpdate(BaseModel):
    status: str | None = None
    assigned_team: str | None = None
    priority: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: str
    target_lat: float
    target_lon: float
    assigned_team: str | None
    priority: str
    status: str
    linked_alert_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ZoneCreate(BaseModel):
    name: str
    boundary: list[list[float]]  # [[lat, lon], ...]


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    boundary: list[list[float]]
    created_at: datetime


class AnnouncementCreate(BaseModel):
    text: str
    zone: str | None = None
    made_by: str | None = None


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    text: str
    zone: str | None
    made_by: str | None
    timestamp: datetime
