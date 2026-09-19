import asyncio
import json
import os
import subprocess
import sys
import pytest
from app.runtime_config import load_config, ROOT
from app.runtime import ClassroomRuntime, Recording
from app.simulation import load_scenario, frames, catalog
from app.pipeline import ObservationPipeline
from app.models import RoomState, Condition, ActivityState, Action
from app.devices import executor, DeviceUnavailable, UnavailableDevice
from app.state_store import store
from app.study_logger import logger
from app.config import settings
from app.observations import ObservationFrame
from app.services.audio.models import AudioObservation
from app.services.audio.factory import create_audio_frontend
from app.services.audio.simulation import SimAudioFrontEnd
from app.services.vision.observation import SimCameraPerception, RealCameraPerception, VisionObservation

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    store.state=RoomState();store.pending=None;store.history=[];store.revision=0
    store.lock=asyncio.Lock();store.control_lock=asyncio.Lock()
    monkeypatch.setattr(logger,'path',tmp_path/'events.jsonl')
    monkeypatch.setattr(settings,'agent_backend','fake')
    executor.configure(load_config(profile='simulation-basic',environ={})['hardware'])

@pytest.mark.asyncio
async def test_normalized_fusion_and_transition():
    config=load_config(environ={});data=load_scenario('student_question')
    pipeline=ObservationPipeline(config,data['calibration'])
    for frame in frames(data):
        assert isinstance(frame.audio,AudioObservation)
        assert isinstance(frame.vision,VisionObservation)
        assert ObservationFrame.model_validate_json(frame.model_dump_json())==frame
        await pipeline.consume(frame)
    lecture=pipeline.states.index('LECTURE')
    assert 'TRANSITION' in pipeline.states[lecture+1:]
    assert pipeline.states[-1]=='Q&A'
    assert store.state.observations.active_speaker=='student_3'

@pytest.mark.asyncio
@pytest.mark.parametrize('name,expected',[
 ('lecture_start','LECTURE'),('instructor_moves','LECTURE'),('demonstration','DEMONSTRATION'),
 ('student_question','Q&A'),('discussion','DISCUSSION'),('media_playback','MEDIA_PLAYBACK'),
 ('side_conversation','SIDE_CONVERSATION'),('student_presentation','STUDENT_PRESENTATION'),
 ('ambiguous_activity','UNKNOWN'),('sensor_dropout','UNKNOWN')])
async def test_sensor_scenarios(name,expected):
    runtime=ClassroomRuntime(load_config(environ={}))
    await runtime.run_scenario(name)
    assert store.state.activity.state.value==expected

@pytest.mark.asyncio
@pytest.mark.parametrize('profile',['simulation-basic','simulation-ai','study','hybrid','hardware'])
@pytest.mark.parametrize('condition',list(Condition))
async def test_profile_does_not_set_authority(profile,condition):
    store.state.condition=condition
    runtime=ClassroomRuntime(load_config(profile=profile,environ={}))
    assert store.state.condition==condition
    if profile=='simulation-ai': assert runtime.config['agent']['backend']=='ollama' and runtime.config['agent']['strict']

@pytest.mark.asyncio
async def test_injection_logged_without_participant_cues_and_replay():
    runtime=ClassroomRuntime(load_config(profile='study',environ={}))
    store.state.condition=Condition.ASSISTIVE
    result=await runtime.run_scenario('controlled_wrong_qna')
    assert result['recommendation'].decision.activity_state==ActivityState.Q_AND_A
    assert store.state.activity.state==ActivityState.SIDE_CONVERSATION
    assert 'experiment_injection' in logger.path.read_text()
    participant=json.dumps({'state':store.state.model_dump(mode='json'),'recommendation':store.pending.model_dump(mode='json')})
    assert 'injection' not in participant.lower() and 'controlled_wrong' not in participant
    tape=Recording.model_validate_json(runtime.recording.model_dump_json())
    first=store.pending.decision
    await runtime.replay(tape)
    assert store.pending.decision==first
    assert not store.history

@pytest.mark.asyncio
@pytest.mark.parametrize('name,tool',[('controlled_wrong_camera','camera_focus'),('controlled_wrong_display','display_set_source'),('controlled_wrong_audio','audio_set_mode')])
async def test_action_injections(name,tool):
    store.state.condition=Condition.AUTONOMOUS
    result=await ClassroomRuntime(load_config(environ={})).run_scenario(name)
    assert result['executed'][0].tool==tool
    assert 'experiment_injection' in logger.path.read_text()

@pytest.mark.asyncio
async def test_device_failure_never_fabricates_success():
    store.state.condition=Condition.AUTONOMOUS
    result=await ClassroomRuntime(load_config(environ={})).run_scenario('device_failure')
    assert result['failures'] and store.state.devices.camera_target=='instructor'
    executor.configure(load_config(profile='hardware',environ={})['hardware'])
    before=await store.snapshot()
    with pytest.raises(DeviceUnavailable): await executor.execute(Action(tool='display_set_source',args={'source':'camera'}))
    assert store.state.devices==before.devices

@pytest.mark.parametrize('audio,camera,projector,recorder',[
 ('xvf3800','simulation','simulation','simulation'),('simulation','real','pjlink','obs')])
def test_hybrid_adapter_selection(audio,camera,projector,recorder):
    env={f'CLASSROOM_HARDWARE__{k.upper()}':v for k,v in dict(audio=audio,camera=camera,projector=projector,recorder=recorder).items()}
    cfg=load_config(profile='hybrid',environ=env)
    runtime=ClassroomRuntime(cfg);executor.configure(cfg['hardware'])
    assert isinstance(runtime.audio,SimAudioFrontEnd)==(audio=='simulation')
    assert isinstance(runtime.camera,SimCameraPerception)==(camera=='simulation')
    assert isinstance(executor.adapters['projector'],UnavailableDevice)==(projector=='pjlink')

@pytest.mark.asyncio
async def test_real_camera_normalization_matches_simulation():
    from app.services.vision import PersonObservation
    cfg=load_config(environ={});cfg['camera']['roles']={'3':'student'}
    real=RealCameraPerception(cfg).normalize([PersonObservation(3,(70,0,90,20),'unknown',.9)],100,1)
    sim=SimCameraPerception();sim.publish(real)
    assert (await sim.observe(1)).tracks==real.tracks
    assert real.tracks[0].image_x==.8

@pytest.mark.asyncio
async def test_ai_uses_room_agent_interface(monkeypatch):
    from app.agent.ollama import OllamaAgent
    from app.agent.fake import FakeAgent
    monkeypatch.setattr(settings,'agent_backend','ollama')
    calls=[]
    async def decide(self,state):
        calls.append(state.activity.state)
        return await FakeAgent().decide(state)
    monkeypatch.setattr(OllamaAgent,'decide',decide)
    store.state.condition=Condition.AUTONOMOUS
    await ClassroomRuntime(load_config(profile='simulation-ai',environ={})).run_scenario('student_question')
    assert calls==[ActivityState.Q_AND_A]
    assert store.state.devices.camera_target=='student_3'

@pytest.mark.parametrize('profile',['simulation-basic','hardware'])
def test_start_without_hardware_or_ollama(tmp_path,profile):
    code='''
import sys, asyncio, importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0] in ('sounddevice','usb','cv2','torch','ultralytics','silero_vad','libusb_package'):
   raise ImportError('Hardware package deliberately blocked')
sys.meta_path.insert(0,Block())
from app.main import app, lifespan
from app.agent.ollama import OllamaAgent
async def fail(*args): raise AssertionError('Ollama must not run')
OllamaAgent.decide=fail
async def run():
 async with lifespan(app):
  runtime=app.state.audio_runtime
  if runtime.config['runtime']['profile']=='simulation-basic': assert runtime.pipeline.states[-1]=='LECTURE'
  else:
   assert runtime.camera.capture is None
   assert not (await runtime.audio.status()).audio_available
asyncio.run(run())
'''
    env={**os.environ,'PYTHONPATH':str(ROOT/'backend'),'CLASSROOM_PROFILE':profile,'AGENT_BACKEND':'fake','STUDY_LOG_PATH':str(tmp_path/'child.jsonl')}
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stderr

@pytest.mark.asyncio
async def test_replay_restores_device_baseline_but_preserves_authority():
    runtime=ClassroomRuntime(load_config(environ={}))
    store.state.condition=Condition.AUTONOMOUS
    await runtime.run_scenario('student_question')
    expected=store.state.devices.model_copy(deep=True)
    tape=runtime.recording
    store.state.devices.display_source='camera'
    await runtime.replay(tape)
    assert store.state.devices==expected
    store.state.condition=Condition.MANUAL
    await runtime.replay(tape)
    assert store.state.condition==Condition.MANUAL
    assert store.state.devices==tape.initial_devices

@pytest.mark.asyncio
async def test_invalid_tape_cannot_mutate_room():
    runtime=ClassroomRuntime(load_config(environ={}))
    await runtime.run_scenario('lecture_start')
    tape=runtime.recording.model_copy(deep=True)
    tape.frames.reverse()
    before=await store.snapshot()
    with pytest.raises(ValueError): await runtime.replay(tape)
    assert store.state==before

@pytest.mark.asyncio
async def test_study_config_hides_scenarios_and_debug(monkeypatch):
    from app.main import app,runtime_config
    from httpx import AsyncClient,ASGITransport
    monkeypatch.setitem(runtime_config,'runtime',{'profile':'study','label':'STUDY','participant_view':True})
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.get('/api/config')).json()['scenarios']==[]
        assert (await client.get('/api/config?researcher=true')).json()['scenarios']
        assert (await client.post('/api/debug/scenario/controlled_wrong_qna')).status_code==403
