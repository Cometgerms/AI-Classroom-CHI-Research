"""Geometric audio/vision association. No LLM and no depth inferred from azimuth."""
from dataclasses import dataclass
import math
def wrap(degrees): return (degrees+180)%360-180

@dataclass(frozen=True)
class PersonTrack:
    track_id: str
    image_x: float # normalized box center, 0 left to 1 right
    timestamp: float
    role: str = 'unknown' # supplied by calibration/researcher, never inferred from azimuth
    confidence: float = 1.0

@dataclass(frozen=True)
class ActiveSpeakerObservation:
    track_id: str | None = None
    role: str | None = None
    confidence: float = 0
    doa_error_deg: float | None = None

class CameraCalibration:
    def __init__(self, points, calibrated=False, type='piecewise_linear'):
        if type!='piecewise_linear': raise ValueError('Unsupported camera calibration')
        self.points=[(p['image_x'],p['azimuth_deg']) for p in points]
        if len(self.points)<2 or any(not all(math.isfinite(v) for v in p) for p in self.points):
            raise ValueError('Need finite calibration points')
        if self.points[0][0]!=0 or self.points[-1][0]!=1 or any(b[0]<=a[0] for a,b in zip(self.points,self.points[1:])):
            raise ValueError('Calibration x must increase strictly from 0 to 1')
        self.calibrated=calibrated

    def azimuth(self, image_x):
        if not self.calibrated: return None
        if not math.isfinite(image_x) or not 0<=image_x<=1: return None
        for (x0,a0),(x1,a1) in zip(self.points,self.points[1:]):
            if x0<=image_x<=x1:
                return wrap(a0+(a1-a0)*(image_x-x0)/(x1-x0))
        return None

class ActiveSpeakerFusion:
    def __init__(self, calibration, angular_tolerance_deg=20, ambiguity_margin_deg=5,
                 onset_ms=200, max_track_age_ms=500, smoothing=.35):
        if not 0<smoothing<=1 or angular_tolerance_deg<=0 or min(ambiguity_margin_deg,onset_ms,max_track_age_ms)<0:
            raise ValueError('Invalid fusion configuration')
        self.calibration=calibration
        self.tolerance,self.margin=angular_tolerance_deg,ambiguity_margin_deg
        self.onset,self.max_age=onset_ms/1000,max_track_age_ms/1000
        self.alpha=smoothing
        self.reset()

    def reset(self): self.candidate=self.since=self.angle=self.last=None

    def process(self, audio, tracks):
        now=audio.timestamp
        if self.last is not None and now<self.last: raise ValueError('Audio time must be monotonic')
        if (not audio.audio_device_available or not audio.activity_calibrated or not audio.speech_active
                or audio.doa_degrees is None or not math.isfinite(audio.doa_degrees)
                or not self.calibration.calibrated):
            self.reset();return ActiveSpeakerObservation()
        if self.last is not None and now-self.last>self.max_age: self.reset()
        self.last=now
        self.angle=audio.doa_degrees if self.angle is None else wrap(self.angle+self.alpha*wrap(audio.doa_degrees-self.angle))
        matches=[]
        ids=[t.track_id for t in tracks]
        if len(set(ids))!=len(ids): self.reset();return ActiveSpeakerObservation()
        for track in tracks:
            if not 0<=now-track.timestamp<=self.max_age or not 0<track.confidence<=1: continue
            azimuth=self.calibration.azimuth(track.image_x)
            if azimuth is None: continue
            error=abs(wrap(azimuth-self.angle))
            if error<=self.tolerance: matches.append((error,track))
        matches.sort(key=lambda item:item[0])
        if not matches or (len(matches)>1 and matches[1][0]-matches[0][0]<self.margin):
            self.candidate=self.since=None
            return ActiveSpeakerObservation()
        error,track=matches[0]
        if self.candidate!=track.track_id: self.candidate,self.since=track.track_id,now
        if now-self.since<self.onset-1e-9: return ActiveSpeakerObservation()
        # Association score, not a calibrated probability or firmware confidence.
        confidence=track.confidence*max(0,1-error/self.tolerance)
        return ActiveSpeakerObservation(track.track_id,track.role,confidence,error)
