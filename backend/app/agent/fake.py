from .base import RoomAgent
from ..models import Action, ActivityState, AgentDecision, RoomState

class FakeAgent(RoomAgent):
    async def decide(self, state: RoomState) -> AgentDecision:
        a = state.activity.state
        actions: list[Action] = []
        if a == ActivityState.LECTURE:
            actions = [
                Action(tool="camera_focus", args={"target": "instructor"}, reason="Instructor is primary speaker", confidence=.97),
                Action(tool="audio_set_mode", args={"mode": "lecture"}, reason="Lecture activity", confidence=.96),
                Action(tool="student_voice_lift", args={"enabled": False}, reason="No audience voice lift needed in lecture", confidence=.96),
                Action(tool="recording_set_layout", args={"layout": "slides_plus_instructor"}, reason="Lecture composition", confidence=.94),
            ]
        elif a == ActivityState.Q_AND_A:
            actions = [
                Action(tool="camera_focus", args={"target": state.observations.active_speaker}, reason="Audience speaker has the floor", confidence=state.activity.confidence),
                Action(tool="student_voice_lift", args={"enabled": True}, reason="Make student question audible", confidence=state.activity.confidence),
                Action(tool="recording_set_layout", args={"layout": "q_and_a"}, reason="Q&A recording composition", confidence=state.activity.confidence),
            ]
        elif a == ActivityState.MEDIA_PLAYBACK:
            actions = [
                Action(tool="display_set_source", args={"source": "presentation"}, reason="Media is the primary content", confidence=.96),
                Action(tool="audio_set_mode", args={"mode": "media"}, reason="Program audio is active", confidence=.95),
                Action(tool="student_voice_lift", args={"enabled": False}, reason="Student voice lift is not needed during media playback", confidence=.95),
                Action(tool="recording_set_layout", args={"layout": "media_primary"}, reason="Prioritize program content", confidence=.93),
            ]
        elif a == ActivityState.DEMONSTRATION:
            actions = [
                Action(tool="camera_focus", args={"target": "demo_zone"}, reason="Instructor is demonstrating a physical object", confidence=.91),
                Action(tool="recording_set_layout", args={"layout": "demo_primary"}, reason="Demonstration should be primary", confidence=.89),
            ]
        elif a == ActivityState.DISCUSSION:
            actions = [
                Action(tool="camera_focus", args={"target": "wide"}, reason="Multiple speakers are participating", confidence=.89),
                Action(tool="audio_set_mode", args={"mode": "discussion"}, reason="Discussion requires group audio behavior", confidence=.87),
            ]
        elif a == ActivityState.SIDE_CONVERSATION:
            actions = []
        return AgentDecision(
            activity_state=a,
            activity_confidence=state.activity.confidence,
            rationale=f"FakeAgent policy for {a.value}",
            actions=actions,
        )
