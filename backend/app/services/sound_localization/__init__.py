from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class SoundSource:
    track_id: str
    zone: str
    confidence: float

class SoundSourceTracker(Protocol):
    def process(self, audio_frame) -> list[SoundSource]: ...

class SimulatedSoundSourceTracker:
    def __init__(self, sources=()):
        self.sources = list(sources)

    def process(self, audio_frame=None):
        return list(self.sources)

class OdasSoundSourceTracker:
    def process(self, audio_frame):
        raise NotImplementedError('ODAS needs calibrated microphone geometry and a platform adapter; see setup docs')
