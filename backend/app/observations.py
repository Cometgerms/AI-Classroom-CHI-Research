"""Validated, serializable sensor contract used by live adapters, scenarios and replay."""
from pydantic import BaseModel, Field, ConfigDict, model_validator
from .services.audio.models import AudioObservation
from .services.vision.observation import VisionObservation

class SceneObservation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    transcript: str = ''
    instructor_speaking: bool = False
    audience_speaking: bool = False
    instructor_yielded: bool = False
    presentation_active: bool = True
    hdmi_playback: bool = False
    program_audio: bool = False
    presenter_zone: str = 'front'
    object_visible: bool = False
    turn_count: int = Field(default=0,ge=0)
    student_at_front: bool = False

class ObservationFrame(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    timestamp: float = Field(ge=0)
    audio: AudioObservation
    vision: VisionObservation
    scene: SceneObservation = Field(default_factory=SceneObservation)

    @model_validator(mode='after')
    def check_clocks(self):
        import math
        if not all(math.isfinite(t) for t in (self.audio.timestamp,self.vision.timestamp)): raise ValueError('Invalid observation clock')
        if abs(self.audio.timestamp-self.timestamp)>1e-6 or abs(self.vision.timestamp-self.timestamp)>1e-6:
            raise ValueError('Observation clocks must match frame timestamp')
        if self.audio.doa_degrees is not None and not math.isfinite(self.audio.doa_degrees): raise ValueError('Invalid DoA')
        for t in self.vision.tracks:
            if not 0<=t.image_x<=1 or not 0<=t.confidence<=1 or not math.isfinite(t.timestamp):
                raise ValueError('Invalid person track')
        return self
