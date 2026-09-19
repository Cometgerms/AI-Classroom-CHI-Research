from dataclasses import dataclass
from .models import Action, Condition

@dataclass
class PolicyDecision:
    result: str  # allow, recommend, deny
    reason: str

CAPABILITY_BY_TOOL = {
    "camera_focus": "camera",
    "display_set_source": "display",
    "audio_set_mode": "audio",
    "student_voice_lift": "audio",
    "recording_start": "recording",
    "recording_stop": "recording",
    "recording_set_layout": "recording",
}

class DelegationPolicy:
    def evaluate(self, condition: Condition, action: Action) -> PolicyDecision:
        if action.tool in {"recording_start", "recording_stop"}:
            return PolicyDecision("deny", "Recording transport is participant-only")
        capability = CAPABILITY_BY_TOOL[action.tool]
        # Hard safety examples can live here later. M1 keeps the rules visible.
        if action.tool == "student_voice_lift" and action.args.get("enabled") not in (True, False):
            return PolicyDecision("deny", "Invalid voice-lift argument")

        if condition == Condition.MANUAL:
            return PolicyDecision("deny", f"{capability} is human-controlled in Manual condition")
        if condition == Condition.ASSISTIVE:
            return PolicyDecision("recommend", f"AI may recommend {capability} changes but cannot execute")
        return PolicyDecision("allow", f"Autonomous condition permits validated {capability} action")

policy = DelegationPolicy()
