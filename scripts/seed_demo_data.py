"""
One-shot seed script: POSTs a sample disaster-zone boundary to a running
backend so the map isn't empty before the simulated drone starts sending
telemetry. Safe to re-run (just creates another zone row each time).

Usage:
    python scripts/seed_demo_data.py
    BACKEND_URL=http://localhost:8000 python scripts/seed_demo_data.py
"""
import os

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# A rough polygon around the same Indore-centered patrol area
# edge-inference/simulate_drone.py flies, standing in for a real
# disaster-zone boundary drawn by an operator.
DEMO_ZONE = {
    "name": "Zone A — Primary Search Area",
    "boundary": [
        [22.7296, 75.8477],
        [22.7296, 75.8677],
        [22.7096, 75.8677],
        [22.7096, 75.8477],
        [22.7296, 75.8477],
    ],
}


def main() -> None:
    resp = requests.post(f"{BACKEND_URL}/api/zones", json=DEMO_ZONE, timeout=10)
    resp.raise_for_status()
    zone = resp.json()
    print(f"[seed] created zone '{zone['name']}' ({zone['id']})")


if __name__ == "__main__":
    main()
