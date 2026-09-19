"""Supported runtime composition, normalized replay and controlled study injection."""
import asyncio
from dataclasses import asdict
from uuid import uuid4
from pydantic import BaseModel, Field
from .observations import ObservationFrame, SceneObservation
from .pipeline import ObservationPipeline
from .simulation import load_scenario, frames
from .services.audio.factory import create_audio_frontend
from .services.vision.observation import create_camera_perception, SimCameraPerception
from .runtime_config import audio_backend
from .devices import executor
from .models import Action, ActivityState, Condition, DeviceState
from .state_store import store
from .study_logger import logger
from .orchestrator import orchestrator

class Recording(BaseModel):
    version: int = 1
    calibration: dict
    condition: Condition
    initial_devices: DeviceState = Field(default_factory=DeviceState)
    frames: list[ObservationFrame] = Field(min_length=1,max_length=30001)
    injection: dict | None = None
    device_failure: str | None = None

class ClassroomRuntime:
    def __init__(self,config):
        self.config=config
        self.audio=create_audio_frontend(config)
        self.camera=create_camera_perception(config)
        self.pipeline=ObservationPipeline(config)
        self.scene=SceneObservation()
        self.lock=asyncio.Lock();self.task=None;self.latest=None;self.recording=None;self.running=False
        self.error=None;self.inference=None
    async def start(self):
        executor.configure(self.config['hardware'])
        await self.camera.start()
        await self.audio.start()
        if self.config['runtime']['profile'] in ('simulation-basic','simulation-ai','study'):
            await self.run_scenario(self.config['scenario']['default'])
        else:
            self.running=True
            self.task=asyncio.create_task(self.collect())
    async def stop(self):
        self.running=False
        self.audio.running=False
        if self.task: await self.task
        if self.inference:
            self.inference.cancel()
            await asyncio.gather(self.inference,return_exceptions=True)
        await self.audio.stop();await self.camera.stop()
    async def collect(self):
        try:
            async for audio in self.audio.observations():
                if not self.running: break
                vision=await self.camera.observe(audio.timestamp)
                frame=ObservationFrame(timestamp=audio.timestamp,audio=audio,vision=vision,scene=self.scene)
                self.latest=frame
                changed=await self.pipeline.consume(frame)
                if changed and store.state.activity.state not in (ActivityState.UNKNOWN,ActivityState.TRANSITION):
                    if self.inference and not self.inference.done(): self.inference.cancel()
                    self.inference=asyncio.create_task(self.evaluate_live())
        except Exception as exc:
            self.error=str(exc);logger.log('runtime_unavailable',error=self.error)
    async def evaluate_live(self):
        try: await orchestrator.evaluate()
        except Exception as exc:
            self.error=str(exc);logger.log('agent_unavailable',error=self.error)
    async def snapshot(self):
        return {'status':asdict(await self.audio.status()),'observation':self.latest.model_dump(mode='json') if self.latest else None,
                'error':self.error,'adapters':self.config['hardware'],
                'outputs':{name:{'backend':backend,'available':backend=='simulation' and name not in executor.failed}
                           for name,backend in executor.backends.items()}}
    async def run_scenario(self,name,realtime=False):
        if self.config['runtime']['profile'] not in ('simulation-basic','simulation-ai','study'):
            raise ValueError('Use normalized observations in hybrid/hardware; scenario playback is a simulation runtime')
        data=load_scenario(name)
        recording=Recording(calibration=data['calibration'],condition=store.state.condition,initial_devices=store.state.devices.model_copy(deep=True),frames=list(frames(data)),
                            injection=data.get('injection'),device_failure=data.get('device_failure'))
        return await self.replay(recording,realtime)
    async def replay(self,recording,realtime=False):
        if self.config['runtime']['profile'] not in ('simulation-basic','simulation-ai','study'):
            raise ValueError('Replay requires a simulation profile')
        if recording.version!=1: raise ValueError('Unsupported recording version')
        # Validate the entire tape before mutating any state.
        if any(a.timestamp>b.timestamp for a,b in zip(recording.frames,recording.frames[1:])):
            raise ValueError('Replay clocks must be monotonic')
        transform=self.injection_transform(recording.injection)
        pipeline=ObservationPipeline(self.config,recording.calibration)
        async with self.lock:
            executor.failed.clear()
            async with store.control_lock:
                store.pending=None
                store.history=[]
                await store.mutate(lambda state: setattr(state,'devices',recording.initial_devices.model_copy(deep=True)))
            run_id=str(uuid4())
            logger.log('runtime_run_started',run_id=run_id,recording=recording.model_dump(mode='json'))
            self.pipeline=pipeline;self.recording=recording
            if recording.device_failure:
                executor.failed.add(recording.device_failure)
                logger.log('experiment_injection',run_id=run_id,kind='device_failure',subsystem=recording.device_failure)
            previous=None
            for frame in recording.frames:
                if realtime and previous is not None: await asyncio.sleep(frame.timestamp-previous)
                previous=frame.timestamp;self.latest=frame
                self.audio.publish(frame.audio)
                self.camera.publish(frame.vision)
                await self.pipeline.consume(frame)
            if recording.injection: logger.log('experiment_injection',run_id=run_id,**recording.injection)
            # Authority is deliberately the current study condition, never restored from the tape.
            result=await orchestrator.evaluate(transform)
            logger.log('runtime_run_completed',run_id=run_id,condition=store.state.condition.value,state=store.state.model_dump(mode='json'))
            return {'state':await store.snapshot(),**result}
    @staticmethod
    def injection_transform(spec):
        if not spec: return None
        kind=spec.get('kind')
        if kind=='wrong_qna':
            actions=[Action(tool='camera_focus',args={'target':'student_3'},reason='Focus the audience speaker'),
                     Action(tool='student_voice_lift',args={'enabled':True},reason='Support the question')]
        elif kind=='action': actions=[Action(tool=spec['tool'],args=spec['args'],reason='Adjust the classroom presentation')]
        else: raise ValueError('Unknown experiment injection')
        def transform(decision):
            result=decision.model_copy(deep=True)
            result.actions=actions
            result.rationale='Adjust the classroom AV to support the current activity.'
            if kind=='wrong_qna': result.activity_state=ActivityState.Q_AND_A
            return result
        return transform
