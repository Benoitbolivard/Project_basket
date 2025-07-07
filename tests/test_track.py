import json
from pathlib import Path

from vision import track


def test_tracker(tmp_path: Path) -> None:
    dets = [
        {
            "ts": 0.0,
            "detections": [
                {"class": "player", "bbox": [0.0, 0.0, 1.0, 1.0]},
                {"class": "player", "bbox": [10.0, 0.0, 1.0, 1.0]},
            ],
        },
        {
            "ts": 1.0,
            "detections": [
                {"class": "player", "bbox": [0.1, 0.0, 1.0, 1.0]},
                {"class": "player", "bbox": [10.1, 0.0, 1.0, 1.0]},
            ],
        },
        {
            "ts": 2.0,
            "detections": [
                {"class": "player", "bbox": [0.2, 0.0, 1.0, 1.0]},
                {"class": "player", "bbox": [10.2, 0.0, 1.0, 1.0]},
            ],
        },
    ]

    det_file = tmp_path / "dets.json"
    with open(det_file, "w", encoding="utf-8") as f:
        json.dump(dets, f)

    out_file = tmp_path / "tracks.json"

    track.main(["--detections", str(det_file), "--output", str(out_file)])

    with open(out_file, "r", encoding="utf-8") as f:
        tracks = json.load(f)

    ids = {t["track_id"] for t in tracks}
    assert len(ids) >= 2
