"""Optional timestamp-driven estimator. Scripted study labels bypass this explicitly."""
from dataclasses import dataclass
from ..models import ActivityState

@dataclass(frozen=True)
class ActivityObservation:
    timestamp: float
    program_audio: bool = False
    hdmi_playback: bool = False
    instructor_speaking: bool = False
    audience_speaking: bool = False
    instructor_yielded: bool = False

class TemporalStateEstimator:
    def __init__(self, sustain_seconds=2.0):
        self.sustain_seconds = sustain_seconds
        self.candidate = ActivityState.UNKNOWN
        self.since = self.last = None

    def process(self, observation: ActivityObservation) -> ActivityState:
        o = observation
        if self.last is not None and o.timestamp < self.last:
            raise ValueError('Observation timestamps must be monotonic')
        self.last = o.timestamp
        candidate = ActivityState.UNKNOWN
        if o.program_audio and o.hdmi_playback and not o.instructor_speaking:
            candidate = ActivityState.MEDIA_PLAYBACK
        elif o.audience_speaking and o.instructor_yielded and not o.instructor_speaking:
            candidate = ActivityState.Q_AND_A
        if candidate != self.candidate or self.since is None:
            self.candidate, self.since = candidate, o.timestamp
        return candidate if o.timestamp - self.since >= self.sustain_seconds else ActivityState.UNKNOWN
