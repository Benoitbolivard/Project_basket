from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
from loguru import logger
from tqdm import tqdm
from ultralytics import YOLO


def run(video: Path, output: Path, device: str = "cpu") -> Path:
    logger.info("Loading YOLO model on {}", device)
    model = YOLO("yolov8n.pt")

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise FileNotFoundError(video)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    results = []
    pbar = tqdm(total=total, desc="Detecting", unit="frame")
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ts = frame_idx / fps
        prediction = model(frame, device=device)[0]
        for box in prediction.boxes:
            results.append(
                {
                    "ts": round(ts, 2),
                    "class": model.names[int(box.cls)],
                    "bbox": [float(x) for x in box.xywh[0].tolist()],
                    "conf": round(float(box.conf[0]), 2),
                }
            )
        frame_idx += 1
        pbar.update(1)
    pbar.close()
    cap.release()

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        json.dump(results, f)
    logger.info("Wrote {} detections to {}", len(results), output)
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="YOLO basketball detection")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args(argv)
    run(args.video, args.output, args.device)


if __name__ == "__main__":
    main()
