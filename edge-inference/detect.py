"""
Real edge inference path (Section 4.2): runs a YOLO model on a video source
and POSTs detection events to the backend, same shape as simulate_drone.py.

Intended to run on the Jetson Nano (export the model to ONNX/TensorRT for
speed there -- see Ultralytics' `model.export(format="engine")`), but also
runs fine on a dev laptop against a webcam or a sample disaster-footage clip
for testing before real hardware is available.

The stock YOLOv8n weights only know COCO classes -- "person", "car", "truck"
etc. Section 4.2's `fire` / `smoke` / `flood_water` / `collapsed_structure`
classes need a fine-tuned model; COCO_CLASS_MAP below is the seam where you
plug in weights trained on a disaster-scene dataset. Until then this maps the
closest stock classes so the pipeline is exercisable end-to-end.

Usage:
    python detect.py --source 0                     # webcam
    python detect.py --source sample_disaster.mp4    # video file
    python detect.py --source rtsp://<drone-ip>/stream --model best.pt
"""
import argparse
import os
import time
from datetime import datetime, timezone

import cv2
import requests
from ultralytics import YOLO

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DRONE_ID = os.environ.get("DRONE_ID", "drone-01")
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.5"))

# Stock COCO class -> Section 4.2 disaster-response class. Replace with a
# fine-tuned model's own class names once one is trained.
COCO_CLASS_MAP = {
    "person": "person",
    "car": "vehicle",
    "truck": "vehicle",
    "bus": "vehicle",
    "motorcycle": "vehicle",
}


def publish(object_type: str, confidence: float, lat: float, lon: float) -> None:
    payload = {
        "object_type": object_type,
        "confidence": round(confidence, 2),
        "lat": lat,
        "lon": lon,
        "snapshot_url": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/api/detections/{DRONE_ID}", json=payload, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[detect] failed to publish detection: {exc}")


def current_position() -> tuple[float, float]:
    """Placeholder: in production, read the drone's live GPS (e.g. from the
    same telemetry stream the flight controller publishes) instead of a
    fixed point."""
    return float(os.environ.get("CENTER_LAT", "22.7196")), float(os.environ.get("CENTER_LON", "75.8577"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0", help="Video source: webcam index, file path, or RTSP URL")
    parser.add_argument("--model", default="yolov8n.pt", help="Path to YOLO weights (stock or fine-tuned)")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    model = YOLO(args.model)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise SystemExit(f"Could not open video source: {source}")

    print(f"[detect] running {args.model} on {source} -> {BACKEND_URL}")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            results = model.predict(frame, verbose=False)[0]
            lat, lon = current_position()

            for box in results.boxes:
                confidence = float(box.conf[0])
                if confidence < CONFIDENCE_THRESHOLD:
                    continue
                class_name = model.names[int(box.cls[0])]
                mapped = COCO_CLASS_MAP.get(class_name)
                if mapped is None:
                    continue
                publish(mapped, confidence, lat, lon)

            time.sleep(0.1)  # throttle; tune per Jetson Nano's real FPS
    finally:
        cap.release()


if __name__ == "__main__":
    main()
