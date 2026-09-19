import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from app.main import app
from app.models import Action, RoomState, Condition, AgentDecision, ActivityState
from app.state_store import store
from app.study_logger import logger
from app.agent.fake import FakeAgent
from app.agent.ollama import OllamaAgent
from app.config import settings

@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    store.state = RoomState()
    store.pending = None
    store.history = []
    store.revision = 0
    store.lock = asyncio.Lock()
    store.control_lock = asyncio.Lock()
    monkeypatch.setattr(logger, 'path', tmp_path / 'events.jsonl')
    monkeypatch.setattr(settings, 'agent_backend', 'fake')

@pytest.mark.parametrize('tool,args', [
    ('camera_focus', {'target':'http://device','pan':30}),
    ('camera_focus', {'target':'student_999'}),
    ('audio_set_mode', {'mode':'raw_gain_100'}),
    ('student_voice_lift', {'enabled':'false'}),
    ('student_voice_lift', {'enabled':1}),
    ('recording_start', {'shell':'touch file'}),
    ('display_set_source', {}),
])
def test_invalid_intents_rejected(tool,args):
    with pytest.raises(ValidationError):
        Action(tool=tool,args=args)

@pytest.mark.asyncio
@pytest.mark.parametrize('condition', list(Condition))
async def test_condition_authority(condition):
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        await client.post('/api/condition',json={'condition':condition.value})
        before=(await store.snapshot()).devices
        response=await client.post('/api/scenario/student_question')
        assert response.status_code==200
        data=response.json()
        if condition==Condition.MANUAL:
            assert data['decision'] is None
            assert store.state.devices==before
        elif condition==Condition.ASSISTIVE:
            assert data['recommendation']
            assert store.state.devices==before
            assert (await client.post('/api/recommendation/apply')).status_code==200
            assert store.state.devices.camera_target=='student_3'
        else:
            assert data['executed']
            assert store.state.devices.camera_target=='student_3'
            await client.post('/api/override',json={'mode':'undo'})
            assert store.state.devices.recording_layout==before.recording_layout
            assert store.state.activity.state==ActivityState.Q_AND_A
            await client.post('/api/override',json={'mode':'manual'})
            assert store.state.condition==Condition.MANUAL

@pytest.mark.asyncio
async def test_take_control_discards_slow_decision(monkeypatch):
    from app.orchestrator import orchestrator
    started,release=asyncio.Event(),asyncio.Event()
    class SlowAgent:
        async def decide(self,state):
            started.set()
            await release.wait()
            return await FakeAgent().decide(state)
    monkeypatch.setattr('app.orchestrator.get_agent',lambda:SlowAgent())
    store.state.condition=Condition.AUTONOMOUS
    work=asyncio.create_task(orchestrator.evaluate())
    await started.wait()
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        await client.post('/api/override',json={'mode':'manual'})
    release.set()
    assert (await work)['executed']==[]
    assert store.history==[]

@pytest.mark.asyncio
async def test_stale_approval_and_dismiss():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        await client.post('/api/condition',json={'condition':'assistive'})
        await client.post('/api/scenario/student_question')
        before=store.state.devices.model_copy()
        await client.post('/api/recommendation/dismiss')
        assert store.state.devices==before
        await client.post('/api/scenario/student_question')
        await client.post('/api/override',json={'mode':'manual'})
        assert store.pending is None
        assert (await client.post('/api/recommendation/apply')).status_code==409
        assert store.state.devices==before

@pytest.mark.asyncio
async def test_outage_falls_back_without_optional_models(monkeypatch):
    monkeypatch.setattr(settings,'ollama_strict',False)
    async def fail(*args):
        raise ConnectionError('offline')
    monkeypatch.setattr(OllamaAgent,'_call',fail)
    decision=await OllamaAgent().decide(RoomState())
    assert 'FakeAgent fallback' in decision.rationale
    assert decision.actions

def test_recording_ai_policy_denied():
    from app.delegation import policy
    assert policy.evaluate(Condition.AUTONOMOUS,Action(tool='recording_start')).result=='deny'

def test_temporal_estimation_requires_sustained_evidence():
    from app.services.estimator import TemporalStateEstimator, ActivityObservation
    estimator=TemporalStateEstimator()
    assert estimator.process(ActivityObservation(0,program_audio=True,hdmi_playback=True))==ActivityState.UNKNOWN
    assert estimator.process(ActivityObservation(2,program_audio=True,hdmi_playback=True))==ActivityState.MEDIA_PLAYBACK
    assert estimator.process(ActivityObservation(3,instructor_speaking=True))==ActivityState.UNKNOWN

def test_camera_director_missing_target_widens_and_rejects_coordinates():
    from app.services.camera import DigitalCameraDirector
    director=DigitalCameraDirector()
    first=director.focus('instructor',{'instructor':(.2,.2,.4,.7)})
    assert first[0]>0 and first[2]<1
    assert director.focus('unknown',{})==(0,0,1,1)
    with pytest.raises(ValueError):
        director.focus('instructor',{'instructor':(-1,0,2,1)})

@pytest.mark.asyncio
async def test_mutated_intent_is_revalidated_before_device_execution():
    from app.devices import executor
    action=Action(tool='student_voice_lift',args={'enabled':False})
    action.args['enabled']='false'
    with pytest.raises(ValueError):
        await executor.execute(action)
    assert not store.history

@pytest.mark.asyncio
async def test_ollama_invalid_tool_args_do_not_reach_devices(monkeypatch):
    import httpx
    class Client:
        def __init__(self,*args,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,*args,**kwargs):
            return httpx.Response(200,request=httpx.Request('POST','http://local/api/chat'),json={
                'message':{'tool_calls':[{'function':{'name':'camera_focus','arguments':{'target':'instructor','pan':90}}}]}})
    monkeypatch.setattr('app.agent.ollama.httpx.AsyncClient',Client)
    monkeypatch.setattr(settings,'ollama_strict',True)
    with pytest.raises(RuntimeError):
        await OllamaAgent().decide(RoomState())
    assert not store.history
