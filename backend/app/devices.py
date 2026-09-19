from .safety import validate_action
from datetime import datetime, timezone
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
                if s.devices.camera_target not in ("presenter","instructor"):
                    s.devices.camera_mode="fixed"
            elif t == "camera_set_follow":
                s.devices.camera_mode = "follow" if a["enabled"] else "fixed"
                if a["enabled"]: s.devices.camera_target="presenter"
            elif t == "display_set_source":
                s.devices.display_source = str(a.get("source", "presentation"))
            elif t == "audio_set_mode":
                s.devices.audio_mode = str(a.get("mode", "lecture"))
            elif t == "student_voice_lift":
                s.devices.student_voice_lift = bool(a.get("enabled", False))
            elif t == "recording_start":
                if not s.devices.recording:
                    s.devices.recording_started_at=datetime.now(timezone.utc).isoformat()
                s.devices.recording = True
            elif t == "recording_stop":
                s.devices.recording = False
                s.devices.recording_started_at=None
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
        from .video import SimVideoEngine, OBSVideoEngine
        self.video=SimVideoEngine() if hardware['recorder']=='simulation' else OBSVideoEngine()
        self.failed=set()
    async def execute(self, action, actor="instructor"):
        validate_action(action)
        before=await store.snapshot()
        subsystem={'camera_focus':'camera_control','camera_set_follow':'camera_control','display_set_source':'projector','audio_set_mode':'audio_output','student_voice_lift':'audio_output'}.get(action.tool,'recorder')
        if subsystem in self.failed:
            logger.log('device_action_failed',subsystem=subsystem,reason='experiment injection')
            raise DeviceUnavailable(f'{subsystem} unavailable')
        if subsystem=='recorder':
            from .video import VideoEngineUnavailable
            try:
                if action.tool=='recording_start': result=await self.video.start_recording()
                elif action.tool=='recording_stop': result=await self.video.stop_recording()
                else: result=await self.video.set_layout(action.args['layout'])
            except VideoEngineUnavailable as exc: raise DeviceUnavailable(str(exc)) from exc
        else: result=await self.adapters[subsystem].execute(action)
        from .product_events import record_action
        record_action(action,before.devices,result.devices,actor,self.backends[subsystem]=='simulation')
        return result

executor = DeviceRouter()
