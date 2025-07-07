from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment
from sklearn.metrics.pairwise import cosine_distances


@dataclass
class Detection:
    bbox: List[float]
    class_name: str
    feature: np.ndarray


@dataclass
class Track:
    track_id: int
    kf: KalmanFilter
    class_name: str
    features: List[np.ndarray] = field(default_factory=list)
    time_since_update: int = 0

    def predict(self) -> None:
        self.kf.predict()
        self.time_since_update += 1

    def update(self, det: Detection) -> None:
        self.time_since_update = 0
        self.features.append(det.feature)
        self.kf.update(self._bbox_to_z(det.bbox))

    @staticmethod
    def _bbox_to_z(bbox: List[float]) -> np.ndarray:
        x, y, w, h = bbox
        return np.array([x + w / 2, y + h / 2, w, h])

    def to_bbox(self) -> List[float]:
        cx, cy, w, h = self.kf.x[:4].reshape(-1)
        return [float(cx - w / 2), float(cy - h / 2), float(w), float(h)]


class Tracker:
    def __init__(self, max_age: int = 30, dist_thresh: float = 0.5) -> None:
        self.tracks: List[Track] = []
        self.next_id = 1
        self.max_age = max_age
        self.dist_thresh = dist_thresh

    @staticmethod
    def _create_kf(bbox: List[float]) -> KalmanFilter:
        kf = KalmanFilter(dim_x=8, dim_z=4)
        dt = 1.0
        kf.F = np.eye(8)
        for i in range(4):
            kf.F[i, i + 4] = dt
        kf.H = np.eye(4, 8)
        kf.P[4:, 4:] *= 1000.0
        kf.P *= 10.0
        kf.R[2:, 2:] *= 10.0
        x, y, w, h = bbox
        kf.x[:4] = np.array([x + w / 2, y + h / 2, w, h]).reshape(4, 1)
        return kf

    @staticmethod
    def _det_feature(det: dict) -> np.ndarray:
        if "feature" in det:
            return np.asarray(det["feature"], dtype=float)
        arr = np.asarray(det["bbox"], dtype=float)
        norm = np.linalg.norm(arr)
        return arr / (norm + 1e-6)

    def _init_track(self, det: dict) -> Track:
        feature = self._det_feature(det)
        kf = self._create_kf(det["bbox"])
        track = Track(
            track_id=self.next_id,
            kf=kf,
            class_name=det["class"],
            features=[feature],
        )
        self.next_id += 1
        self.tracks.append(track)
        return track

    def step(self, detections: List[dict], ts: float) -> List[dict]:
        for t in self.tracks:
            t.predict()

        detections_list = [
            Detection(d["bbox"], d["class"], self._det_feature(d)) for d in detections
        ]
        if not self.tracks:
            for det in detections_list:
                self._init_track(
                    {"bbox": det.bbox, "class": det.class_name, "feature": det.feature}
                )
            return [
                {
                    "ts": ts,
                    "track_id": t.track_id,
                    "class": t.class_name,
                    "bbox": t.to_bbox(),
                }
                for t in self.tracks
            ]

        cost = np.zeros((len(self.tracks), len(detections_list)), dtype=float)
        for i, track in enumerate(self.tracks):
            track_feat = track.features[-1].reshape(1, -1)
            det_feats = np.stack([d.feature for d in detections_list])
            cost[i] = cosine_distances(track_feat, det_feats)[0]

        row_ind, col_ind = linear_sum_assignment(cost)
        matched_tracks = set()
        matched_dets = set()
        for r, c in zip(row_ind, col_ind):
            if cost[r, c] > self.dist_thresh:
                continue
            track = self.tracks[r]
            det = detections_list[c]
            track.update(det)
            matched_tracks.add(r)
            matched_dets.add(c)

        for idx, track in enumerate(self.tracks):
            if idx not in matched_tracks:
                track.time_since_update += 1

        for i, det in enumerate(detections_list):
            if i not in matched_dets:
                self._init_track(
                    {"bbox": det.bbox, "class": det.class_name, "feature": det.feature}
                )

        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        outputs = [
            {
                "ts": ts,
                "track_id": t.track_id,
                "class": t.class_name,
                "bbox": t.to_bbox(),
            }
            for t in self.tracks
            if t.time_since_update == 0
        ]
        return outputs


def run(detections_path: str, output_path: str) -> None:
    with open(detections_path, "r", encoding="utf-8") as f:
        frames = json.load(f)

    tracker = Tracker()
    results: List[dict] = []
    for frame in frames:
        ts = frame["ts"]
        detections = frame.get("detections", [])
        results.extend(tracker.step(detections, ts))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run DeepSORT tracking")
    parser.add_argument("--detections", required=True, help="Input detections JSON")
    parser.add_argument("--output", required=True, help="Output tracks JSON")
    args = parser.parse_args(argv)

    run(args.detections, args.output)


if __name__ == "__main__":
    main()
