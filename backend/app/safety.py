"""Deterministic intent boundary, shared by AI and participant device paths."""
import re

ENUMS = {
    "display_set_source": ("source", {"presentation", "room_pc", "camera"}),
    "audio_set_mode": ("mode", {"lecture", "media", "discussion"}),
    "recording_set_layout": ("layout", {"slides_plus_instructor", "q_and_a", "media_primary", "demo_primary", "wide"}),
}

def validate_action(action):
    tool, args = action.tool, action.args
    if tool in ENUMS:
        key, allowed = ENUMS[tool]
        valid = set(args) == {key} and isinstance(args[key], str) and args[key] in allowed
    elif tool == "camera_focus":
        valid = set(args) == {"target"} and isinstance(args["target"], str) and bool(re.fullmatch(r"instructor|presenter|active_student|student|wide|demo_zone|student_[1-6]", args["target"]))
    elif tool == "student_voice_lift":
        valid = set(args) == {"enabled"} and type(args["enabled"]) is bool
    elif tool in {"recording_start", "recording_stop"}:
        valid = not args
    else:
        valid = False
    if not valid:
        raise ValueError(f"Invalid arguments for intent {tool}")
