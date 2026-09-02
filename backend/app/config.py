"""
Central configuration for the Disaster Mission Control backend.

AI_SOURCE is the swappable flag mentioned in the build proposal (Section 12):
- "simulated": detections arrive from edge-inference/simulate_drone.py (no real
  hardware needed).
- "jetson": detections arrive from a real Jetson Nano running edge-inference/detect.py
  against a live drone video feed.

The backend's API/DB/dashboard code does not change between the two -- both
paths POST to the same /api/detections/{drone_id} endpoint.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://mission:mission@localhost:5432/mission_control"
    ai_source: str = "simulated"  # "simulated" | "jetson"

    # Optional MQTT ingestion path (Section 5). Off by default -- REST is the
    # primary, always-on path used by edge-inference/*.py. See mqtt_client.py.
    mqtt_enabled: bool = False
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883

    # Alert dedup window: repeated detections of the same type from the same
    # drone within this radius/time are collapsed into one alert.
    dedup_window_seconds: int = 60
    dedup_radius_m: float = 50.0

    cors_origins: list[str] = ["*"]


settings = Settings()
