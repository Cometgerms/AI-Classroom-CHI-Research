from .safety import validate_action
from .models import Action, RoomState
from .state_store import store
from .study_logger import logger

class SimDeviceExecutor:
    async def execute(self, action: Action) -> RoomState:
        validate_action(action)
        await store.push_history()

        def apply(s: RoomState):
            t, a = action.tool, action.args
            if t == "camera_focus":
                s.devices.camera_target = str(a.get("target", "instructor"))
            elif t == "display_set_source":
                s.devices.display_source = str(a.get("source", "presentation"))
            elif t == "audio_set_mode":
                s.devices.audio_mode = str(a.get("mode", "lecture"))
            elif t == "student_voice_lift":
                s.devices.student_voice_lift = bool(a.get("enabled", False))
            elif t == "recording_start":
                s.devices.recording = True
            elif t == "recording_stop":
                s.devices.recording = False
            elif t == "recording_set_layout":
                s.devices.recording_layout = str(a.get("layout", "slides_plus_instructor"))
            else:
                raise ValueError(f"Unsupported tool: {t}")

        state = await store.mutate(apply)
        logger.log("device_action_executed", action=action.model_dump(), verified_state=state.devices.model_dump())
        return state

executor = SimDeviceExecutor()
