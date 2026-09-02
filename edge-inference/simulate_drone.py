"""
Fake drone: publishes a realistic flight path + battery drain as telemetry,
and occasionally a fake AI detection, straight to the backend REST API.

This is what Section 12 means by getting a trivial end-to-end flow working
before real AI hardware exists: point the dashboard at this script and the
whole loop (telemetry -> map, detection -> alert -> task board) is demoable
with zero drone/Jetson hardware.

Usage:
    python simulate_drone.py
    BACKEND_URL=http://localhost:8000 DRONE_ID=drone-01 python simulate_drone.py

Swap this for edge-inference/detect.py (config.ai_source = "jetson") once
real hardware is available -- both post to the same endpoints.
"""
import math
import os
import random
import time
from datetime import datetime, timezone

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DRONE_ID = os.environ.get("DRONE_ID", "drone-01")
TICK_SECONDS = float(os.environ.get("TICK_SECONDS", "2"))

# Simulated disaster zone center + a circular patrol radius (degrees ~ meters
# at this scale don't matter for a demo).
CENTER_LAT = float(os.environ.get("CENTER_LAT", "22.7196"))  # Indore, MP
CENTER_LON = float(os.environ.get("CENTER_LON", "75.8577"))
RADIUS_DEG = 0.01
ALTITUDE_M = 120.0

DETECTION_TYPES = [
    "person",
    "fire",
    "smoke",
    "flood_water",
    "vehicle",
    "collapsed_structure",
]
DETECTION_CHANCE = 0.25  # per tick


def fly_step(t: float) -> tuple[float, float, float]:
    """Circular patrol path. Returns (lat, lon, heading_deg)."""
    angle = t * 0.15  # angular speed
    lat = CENTER_LAT + RADIUS_DEG * math.sin(angle)
    lon = CENTER_LON + RADIUS_DEG * math.cos(angle)
    heading = (math.degrees(angle) + 90) % 360
    return lat, lon, heading


def post(path: str, payload: dict) -> None:
    try:
        resp = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[simulate_drone] POST {path} failed: {exc}")


def main() -> None:
    print(f"[simulate_drone] {DRONE_ID} -> {BACKEND_URL} (Ctrl+C to stop)")
    battery = 100.0
    t = 0.0
    while True:
        lat, lon, heading = fly_step(t)
        battery = max(0.0, battery - 0.05)

        post(
            f"/api/telemetry/{DRONE_ID}",
            {
                "lat": lat,
                "lon": lon,
                "altitude_m": ALTITUDE_M + random.uniform(-2, 2),
                "heading_deg": heading,
                "battery_pct": battery,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        if random.random() < DETECTION_CHANCE:
            object_type = random.choice(DETECTION_TYPES)
            post(
                f"/api/detections/{DRONE_ID}",
                {
                    "object_type": object_type,
                    "confidence": round(random.uniform(0.55, 0.98), 2),
                    "lat": lat + random.uniform(-0.0005, 0.0005),
                    "lon": lon + random.uniform(-0.0005, 0.0005),
                    "snapshot_url": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            print(f"[simulate_drone] detection: {object_type}")

        if battery <= 0:
            print("[simulate_drone] battery depleted, restarting patrol at 100%")
            battery = 100.0

        t += TICK_SECONDS
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
