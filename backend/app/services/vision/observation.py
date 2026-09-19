"""Shared vision contract for real cameras, simulation and replay."""
from dataclasses import dataclass
from typing import Protocol
from ..active_speaker import PersonTrack

@dataclass(frozen=True)
class VisionObservation:
    timestamp: float
    tracks: tuple[PersonTrack, ...] = ()
    camera_available: bool = True
    source: str = 'simulation'
    error: str | None = None

class CameraPerception(Protocol):
    async def start(self): ...
    async def stop(self): ...
    async def observe(self, timestamp: float) -> VisionObservation: ...

class SimCameraPerception:
    def __init__(self): self.current=VisionObservation(0); self.running=False
    async def start(self): self.running=True
    async def stop(self): self.running=False
    def publish(self, observation: VisionObservation): self.current=observation
    async def observe(self, timestamp):
        from dataclasses import replace
        return replace(self.current,timestamp=timestamp,tracks=tuple(replace(t,timestamp=timestamp) for t in self.current.tracks))

class RealCameraPerception:
    """Optional local OpenCV capture; explicit local camera selection required."""
    def __init__(self, config):
        self.config=config;self.capture=None;self.tracker=None;self.error=None
    async def start(self):
        import asyncio
        def open_camera():
            import cv2
            from .factory import create_person_tracker
            device=self.config['camera'].get('device')
            if device is None: raise RuntimeError('Set camera.device in ignored local.yaml after local enumeration')
            self.tracker,warning=create_person_tracker(self.config)
            self.capture=cv2.VideoCapture(device)
            if not self.capture.isOpened(): raise RuntimeError('Configured camera cannot be opened')
            self.error=warning
        try: await asyncio.to_thread(open_camera)
        except Exception as exc:
            self.error=str(exc)
            await self.stop()
    async def stop(self):
        if self.capture is not None: self.capture.release();self.capture=None
    def normalize(self, people, width, timestamp):
        roles=self.config['camera'].get('roles',{})
        tracks=tuple(PersonTrack(str(p.track_id),(p.bounding_box[0]+p.bounding_box[2])/(2*width),timestamp,
                                  roles.get(str(p.track_id),'unknown'),p.confidence)
                     for p in people if p.track_id is not None)
        return VisionObservation(timestamp,tracks,True,'camera')
    async def observe(self,timestamp):
        import asyncio
        if self.capture is None: return VisionObservation(timestamp,(),False,'camera',self.error)
        def read():
            ok,frame=self.capture.read()
            if not ok: raise RuntimeError('Camera disconnected or frame unavailable')
            return self.normalize(self.tracker.track(frame),frame.shape[1],timestamp)
        try: return await asyncio.to_thread(read)
        except Exception as exc: return VisionObservation(timestamp,(),False,'camera',str(exc))

def create_camera_perception(config):
    return SimCameraPerception() if config['hardware']['camera']=='simulation' else RealCameraPerception(config)
