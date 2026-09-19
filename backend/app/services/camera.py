"""Camera director consumes trusted tracking coordinates, never model coordinates."""
from dataclasses import dataclass
from typing import Protocol

class CameraDirector(Protocol):
    def focus(self, target: str, tracks: dict[str, tuple[float,float,float,float]]) -> tuple[float,float,float,float]: ...

@dataclass
class DigitalCameraDirector:
    """Normalized digital crop target with smoothing; caller applies it to a frame.

    Not wired into M1. Missing tracking safely falls back to the whole frame.
    """
    smoothing: float = 0.25
    crop: tuple[float,float,float,float] = (0,0,1,1)

    def focus(self, target, tracks):
        import math
        box = tracks.get(target) if target != 'wide' else None
        if box is None:
            self.crop=(0,0,1,1)
            return self.crop
        if len(box)!=4 or not all(math.isfinite(v) and 0<=v<=1 for v in box) or box[0]>=box[2] or box[1]>=box[3]:
            raise ValueError('Invalid normalized tracking box')
        if not 0 < self.smoothing <= 1:
            raise ValueError('Smoothing must be in (0, 1]')
        x1,y1,x2,y2=box
        pad=.1
        desired=(max(0,x1-pad),max(0,y1-pad),min(1,x2+pad),min(1,y2+pad))
        self.crop=tuple(a+(b-a)*self.smoothing for a,b in zip(self.crop,desired))
        return self.crop

    def apply(self, frame):
        height,width=frame.shape[:2]
        x1,y1,x2,y2=self.crop
        return frame[int(y1*height):max(int(y1*height)+1,int(y2*height)),int(x1*width):max(int(x1*width)+1,int(x2*width))]
