from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone

class Condition(str, Enum):
    MANUAL = "manual"
    ASSISTIVE = "assistive"
    AUTONOMOUS = "autonomous"

class SessionState(str, Enum):
    IDLE = "IDLE"
    PRE_CLASS = "PRE_CLASS"
    ACTIVE = "ACTIVE"
    BREAK = "BREAK"
    POST_CLASS = "POST_CLASS"

class ActivityState(str, Enum):
    PRE_CLASS = "PRE_CLASS"
    POST_CLASS = "POST_CLASS"
    LECTURE = "LECTURE"
    DEMONSTRATION = "DEMONSTRATION"
    MEDIA_PLAYBACK = "MEDIA_PLAYBACK"
    Q_AND_A = "Q&A"
    DISCUSSION = "DISCUSSION"
    STUDENT_PRESENTATION = "STUDENT_PRESENTATION"
    SIDE_CONVERSATION = "SIDE_CONVERSATION"
    TRANSITION = "TRANSITION"
    UNKNOWN = "UNKNOWN"

class HealthState(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    FAILSAFE = "FAILSAFE"

class ObservationState(BaseModel):
    instructor_speaking: bool = True
    student_speaking: bool = False
    active_speaker: str = "instructor"
    speaker_location: str = "front"
    transcript: str = ""
    presentation_active: bool = True
    program_audio: bool = False
    presenter_zone: str = "front"
    presentation_source: str = "presentation"
    evidence: list[str] = Field(default_factory=list)

class ActivityEstimate(BaseModel):
    state: ActivityState = ActivityState.LECTURE
    confidence: float = 0.95
    previous: ActivityState | None = None
    evidence: list[str] = Field(default_factory=list)

class DeviceState(BaseModel):
    camera_target: str = "instructor"
    camera_mode: str = "follow"
    display_power: bool = True
    display_source: str = "presentation"
    audio_mode: str = "lecture"
    student_voice_lift: bool = False
    recording: bool = False
    recording_started_at: str | None = None
    recording_layout: str = "slides_plus_instructor"

class StudyProgress(BaseModel):
    protocol: str = 'chi_v1_instructor'
    run_id: str
    assigned_condition: Condition
    condition_order: list[Condition]
    condition_position: int
    task_index: int = -1
    task_id: str | None = None
    instruction: str = ''
    started_at: str | None = None
    completed: bool = False
    finished: bool = False

class RoomState(BaseModel):
    participant_id: str = "P000"
    study: StudyProgress | None = None
    restricted_capabilities: list[Literal["camera", "display", "audio", "recording"]] = Field(default_factory=list)
    condition: Condition = Condition.MANUAL
    session: SessionState = SessionState.ACTIVE
    activity: ActivityEstimate = Field(default_factory=ActivityEstimate)
    observations: ObservationState = Field(default_factory=ObservationState)
    devices: DeviceState = Field(default_factory=DeviceState)
    health: HealthState = HealthState.NORMAL
    ai_enabled: bool = True
    last_scenario: str = "lecture"

class Action(BaseModel):
    tool: Literal[
        "camera_focus",
        "camera_set_follow",
        "display_set_source",
        "audio_set_mode",
        "student_voice_lift",
        "recording_start",
        "recording_stop",
        "recording_set_layout",
    ]
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    confidence: float = Field(default=1.0, ge=0, le=1)

    @model_validator(mode="after")
    def validate_intent(self):
        from .safety import validate_action
        validate_action(self)
        return self

class AgentDecision(BaseModel):
    activity_state: ActivityState
    activity_confidence: float = 0.0
    rationale: str = ""
    actions: list[Action] = Field(default_factory=list)

class Recommendation(BaseModel):
    id: str
    created_at: str
    decision: AgentDecision

class ManualActionRequest(BaseModel):
    action: Action

class ConditionRequest(BaseModel):
    condition: Condition

class ParticipantRequest(BaseModel):
    participant_id: str

class OverrideRequest(BaseModel):
    capability: Literal["camera", "display", "audio", "recording", "all"] = "all"
    mode: Literal["undo", "manual"] = "undo"

class EventRecord(BaseModel):
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event: str
    payload: dict[str, Any] = Field(default_factory=dict)

class RestrictionRequest(BaseModel):
    capability: Literal['camera','display','audio','recording']
    restricted: bool = True

class StudyStartRequest(BaseModel):
    counterbalance_index: int = Field(ge=0,le=5)
    condition_position: int = Field(ge=0,le=2)

class TaskCompletionRequest(BaseModel):
    outcome: Literal['completed','partial','aborted'] = 'completed'
    notes: str = Field(default='',max_length=2000)

class DelegationPreferences(BaseModel):
    camera: Condition
    display: Condition
    audio: Condition
    recording: Condition

class ConditionFeedback(BaseModel):
    perceived_control: int = Field(ge=1,le=7)
    trust: int = Field(ge=1,le=7)
    workload: int = Field(ge=1,le=7)
    delegation_preferences: DelegationPreferences
    notes: str = Field(default='',max_length=2000)
