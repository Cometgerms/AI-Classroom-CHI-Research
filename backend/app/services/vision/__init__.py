"""Lazy optional perception; no framework tensors leave this module."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class PersonObservation:
    track_id: int | None
    bounding_box: tuple[float, float, float, float]
    zone: str
    confidence: float

@dataclass(frozen=True)
class PoseObservation:
    bounding_box: tuple[float, float, float, float]
    confidence: float
    raised_hand: bool

class PersonDetector(Protocol):
    def detect(self, frame) -> list[PersonObservation]: ...

class PersonTracker(Protocol):
    def track(self, frame) -> list[PersonObservation]: ...

class PoseEstimator(Protocol):
    def estimate(self, frame) -> list[PoseObservation]: ...

class UltralyticsPeople:
    def __init__(self, weights, device='cpu'):
        from ultralytics import YOLO
        self.model, self.device = YOLO(str(weights)), device

    def _run(self, frame, tracking):
        if tracking:
            results = self.model.track(frame, classes=[0], persist=True, device=self.device, verbose=False)
        else:
            results = self.model.predict(frame, classes=[0], device=self.device, verbose=False)
        observations = []
        for result in results:
            for box in result.boxes:
                observations.append(PersonObservation(
                    int(box.id.item()) if box.id is not None else None,
                    tuple(box.xyxy[0].tolist()), 'unknown', float(box.conf.item())))
        # Zones require classroom calibration; never infer a room zone from pixels alone.
        return observations

    def detect(self, frame):
        return self._run(frame, False)

    def track(self, frame):
        return self._run(frame, True)

class UltralyticsPose:
    def __init__(self, weights, device='cpu'):
        from ultralytics import YOLO
        self.model, self.device = YOLO(str(weights)), device

    def estimate(self, frame):
        observations = []
        for result in self.model.predict(frame, device=self.device, verbose=False):
            if result.keypoints is None:
                continue
            for box, points in zip(result.boxes, result.keypoints.data.tolist()):
                raised = any(points[w][2] > .5 and points[s][2] > .5 and points[w][1] < points[s][1]
                             for w, s in ((9, 5), (10, 6)))
                observations.append(PoseObservation(tuple(box.xyxy[0].tolist()), float(box.conf.item()), raised))
        return observations
