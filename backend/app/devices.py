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

class DeviceUnavailable(RuntimeError): pass

class UnavailableDevice:
    def __init__(self, backend): self.backend=backend
    async def execute(self, action):
        logger.log('device_action_failed', adapter=self.backend, action=action.model_dump(), reason='Adapter not implemented or configured')
        raise DeviceUnavailable(f'{self.backend} adapter unavailable; no device state changed')

class DeviceRouter:
    def __init__(self): self.configure({name:'simulation' for name in ('camera_control','projector','audio_output','recorder')})
    def configure(self, hardware):
        self.backends={name:hardware[name] for name in ('camera_control','projector','audio_output','recorder')}
        self.adapters={name:SimDeviceExecutor() if backend=='simulation' else UnavailableDevice(backend) for name,backend in self.backends.items()}
        self.failed=set()
    async def execute(self, action):
        validate_action(action)
        subsystem={'camera_focus':'camera_control','display_set_source':'projector','audio_set_mode':'audio_output','student_voice_lift':'audio_output'}.get(action.tool,'recorder')
        if subsystem in self.failed:
            logger.log('device_action_failed',subsystem=subsystem,reason='experiment injection')
            raise DeviceUnavailable(f'{subsystem} unavailable')
        return await self.adapters[subsystem].execute(action)

executor = DeviceRouter()
