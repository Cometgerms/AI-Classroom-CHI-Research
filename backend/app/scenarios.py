from .models import ActivityState, ObservationState, RoomState

SCENARIOS = {
    "lecture": dict(
        activity=ActivityState.LECTURE, confidence=.97,
        obs=dict(instructor_speaking=True, student_speaking=False, active_speaker="instructor", speaker_location="front", transcript="Today we will look at this example.", presentation_active=True, program_audio=False, presenter_zone="front", evidence=["instructor dominant", "slides active"]),
    ),
    "student_question": dict(
        activity=ActivityState.Q_AND_A, confidence=.94,
        obs=dict(instructor_speaking=False, student_speaking=True, active_speaker="student_3", speaker_location="row_3_left", transcript="Could you explain that last example again?", presentation_active=True, program_audio=False, presenter_zone="front", evidence=["audience speaker sustained", "instructor yielded floor", "question language"]),
    ),
    "media_playback": dict(
        activity=ActivityState.MEDIA_PLAYBACK, confidence=.96,
        obs=dict(instructor_speaking=False, student_speaking=False, active_speaker="program", speaker_location="program", transcript="", presentation_active=True, program_audio=True, presenter_zone="front", evidence=["program audio active", "video motion", "instructor silent"]),
    ),
    "demonstration": dict(
        activity=ActivityState.DEMONSTRATION, confidence=.91,
        obs=dict(instructor_speaking=True, student_speaking=False, active_speaker="instructor", speaker_location="demo_zone", transcript="Listen to what happens when I change this parameter.", presentation_active=True, program_audio=False, presenter_zone="demo_zone", evidence=["presenter moved to demo zone", "physical demonstration"]),
    ),
    "side_conversation": dict(
        activity=ActivityState.SIDE_CONVERSATION, confidence=.88,
        obs=dict(instructor_speaking=True, student_speaking=True, active_speaker="instructor", speaker_location="row_5_right", transcript="", presentation_active=True, program_audio=False, presenter_zone="front", evidence=["brief student speech", "instructor continues", "not class-wide"]),
    ),
    "discussion": dict(
        activity=ActivityState.DISCUSSION, confidence=.89,
        obs=dict(instructor_speaking=False, student_speaking=True, active_speaker="student_2", speaker_location="center", transcript="I think there is another way to interpret it.", presentation_active=True, program_audio=False, presenter_zone="seated", evidence=["multi-person turn-taking", "instructor not dominant"]),
    ),
    "controlled_wrong_qna": dict(
        activity=ActivityState.Q_AND_A, confidence=.86,
        obs=dict(instructor_speaking=True, student_speaking=True, active_speaker="student_4", speaker_location="row_4_right", transcript="", presentation_active=True, program_audio=False, presenter_zone="front", evidence=["CONTROLLED FAILURE: side conversation misclassified as Q&A"]),
    ),
}

def apply_scenario(state: RoomState, name: str):
    if name == "reset":
        fresh = RoomState(participant_id=state.participant_id, condition=state.condition)
        state.session = fresh.session
        state.activity = fresh.activity
        state.observations = fresh.observations
        state.devices = fresh.devices
        state.health = fresh.health
        state.last_scenario = "lecture"
        return
    cfg = SCENARIOS[name]
    previous = state.activity.state
    state.activity.state = cfg["activity"]
    state.activity.previous = previous
    state.activity.confidence = cfg["confidence"]
    state.activity.evidence = list(cfg["obs"]["evidence"])
    state.observations = ObservationState(**cfg["obs"])
    state.last_scenario = name
