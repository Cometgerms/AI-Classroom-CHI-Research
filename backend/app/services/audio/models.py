from dataclasses import dataclass

@dataclass(frozen=True)
class AudioObservation:
    timestamp: float # monotonic seconds, same host clock as camera track timestamps
    speech_active: bool = False
    speech_energy: float | None = None
    doa_degrees: float | None = None # [-180, 180), calibrated room azimuth
    doa_confidence: float | None = None # firmware does not provide a calibrated confidence
    selected_beam: str | None = None
    audio_device_available: bool = False
    source: str = 'simulation'
    activity_calibrated: bool = False
    error: str | None = None

@dataclass(frozen=True)
class AudioStatus:
    running: bool
    audio_available: bool
    control_available: bool
    source: str
    error: str | None = None
