import asyncio
from datetime import datetime,timedelta,timezone
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient,ASGITransport
from app.main import app
from app.models import RoomState,Condition,Action,Recommendation,AgentDecision,ActivityState
from app.state_store import store
from app.devices import executor,DeviceUnavailable
from app.product import service,Preferences
from app.product_events import events
from app.runtime import ClassroomRuntime
from app.runtime_config import load_config
from app.config import settings
from app.study_logger import logger

@pytest.fixture(autouse=True)
def clean(tmp_path,monkeypatch):
    store.state=RoomState();store.pending=None;store.history=[];store.revision=0
    store.control_lock=asyncio.Lock();store.lock=asyncio.Lock();events.clear()
    cfg=load_config(profile='simulation-basic',environ={})
    executor.configure(cfg['hardware'])
    monkeypatch.setattr(app.state,'audio_runtime',ClassroomRuntime(cfg),raising=False)
    monkeypatch.setattr(settings,'agent_backend','fake')
    monkeypatch.setattr(logger,'path',tmp_path/'events.jsonl')
    monkeypatch.setattr('app.product.PREFERENCES_PATH',tmp_path/'preferences.json')
    monkeypatch.setattr(service,'preferences',Preferences())
    monkeypatch.setattr(service,'inference',None);monkeypatch.setattr(service,'busy',False)
    monkeypatch.setattr(service,'status','ready');monkeypatch.setattr(service,'error',None)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client: yield client
    if service.inference:
        service.inference.cancel();await asyncio.gather(service.inference,return_exceptions=True)

@pytest.mark.asyncio
async def test_product_view_has_no_research_metadata(client):
    data=(await client.get('/api/instructor/state')).json()
    text=json.dumps(data)
    for key in ('participant_id','study','scenario','confidence','observations','FakeAgent','condition'):
        assert key not in text
    assert data['aiMode']=='off'
    assert data['programState']['preview']['kind']=='illustration'
    store.state.activity.confidence=.3
    assert (await client.get('/api/instructor/state')).json()['currentActivity']=='Watching…'

@pytest.mark.asyncio
async def test_controls_and_explicit_recording_timer(client):
    for tool,args in [('camera_focus',{'target':'demo_zone'}),('camera_set_follow',{'enabled':True}),
                      ('display_set_source',{'source':'blank'}),('audio_set_mode',{'mode':'mute'}),('recording_start',{})]:
        assert (await client.post('/api/instructor/action',json={'tool':tool,'args':args})).status_code==200
    before=store.state.devices.recording_started_at
    assert before and store.state.devices.recording
    await client.post('/api/instructor/action',json={'tool':'recording_set_layout','args':{'layout':'demo_primary'}})
    assert store.state.devices.recording_started_at==before
    assert store.state.devices.recording
    await client.post('/api/instructor/take-control')
    assert store.state.condition==Condition.MANUAL and store.state.devices.recording
    assert store.state.devices.display_source=='blank'
    await client.post('/api/instructor/action',json={'tool':'recording_stop','args':{}})
    assert not store.state.devices.recording and store.state.devices.recording_started_at is None

@pytest.mark.asyncio
async def test_assist_recommendation_identity_expiration_and_ignore(client):
    await client.post('/api/instructor/mode',json={'mode':'assist'})
    await service.inference
    assert store.pending and not store.history
    rec=store.pending
    assert (await client.post('/api/instructor/recommendation/wrong/apply')).status_code==409
    assert (await client.post(f'/api/instructor/recommendation/{rec.id}/ignore')).status_code==200
    assert not store.pending and not store.history
    await client.post('/api/instructor/mode',json={'mode':'assist'});await service.inference
    store.pending.created_at=(datetime.now(timezone.utc)-timedelta(seconds=46)).isoformat()
    old=store.pending.id
    assert (await client.post(f'/api/instructor/recommendation/{old}/apply')).status_code==409
    assert not store.history

@pytest.mark.asyncio
async def test_auto_undo_does_not_stop_recording(client):
    await client.post('/api/instructor/action',json={'tool':'recording_start'})
    await client.post('/api/instructor/mode',json={'mode':'auto'});await service.inference
    ai_event=events[0]
    assert ai_event['actor']=='ai'
    assert (await client.post('/api/instructor/undo',json={'action_id':ai_event['id']})).status_code==200
    assert store.state.devices.recording
    assert (await client.post('/api/instructor/undo',json={'action_id':ai_event['id']})).status_code==409

@pytest.mark.asyncio
async def test_manual_control_invalidates_slow_ai_and_take_control_is_immediate(client,monkeypatch):
    from app.agent.fake import FakeAgent
    started=asyncio.Event();release=asyncio.Event()
    class Slow:
        async def decide(self,state):
            started.set();await release.wait();return await FakeAgent().decide(state)
    monkeypatch.setattr('app.orchestrator.get_agent',lambda:Slow())
    await client.post('/api/instructor/mode',json={'mode':'auto'});await started.wait()
    await client.post('/api/instructor/action',json={'tool':'display_set_source','args':{'source':'room_pc'}})
    assert (await client.post('/api/instructor/take-control')).status_code==200
    release.set();await asyncio.gather(service.inference,return_exceptions=True)
    assert store.state.condition==Condition.MANUAL and store.state.devices.display_source=='room_pc'
    assert not store.pending
    assert not any(e['actor']=='ai' for e in events)

@pytest.mark.asyncio
async def test_model_outage_keeps_manual_controls(client,monkeypatch):
    class Offline:
        async def decide(self,state): raise RuntimeError('offline')
    monkeypatch.setattr('app.orchestrator.get_agent',lambda:Offline())
    await client.post('/api/instructor/mode',json={'mode':'assist'});await service.inference
    assert service.error
    assert (await client.post('/api/instructor/action',json={'tool':'camera_focus','args':{'target':'wide'}})).status_code==200
    assert store.state.devices.camera_target=='wide'
    assert (await client.post('/api/instructor/take-control')).status_code==200

@pytest.mark.asyncio
async def test_obs_failure_does_not_break_display(client):
    from app.video import OBSVideoEngine
    hardware=load_config(profile='hybrid',environ={})['hardware'];hardware['recorder']='obs'
    executor.configure(hardware)
    assert isinstance(executor.video,OBSVideoEngine)
    assert (await client.post('/api/instructor/action',json={'tool':'recording_start'})).status_code==503
    assert not store.state.devices.recording
    assert (await client.post('/api/instructor/action',json={'tool':'display_set_source','args':{'source':'room_pc'}})).status_code==200
    data=(await client.get('/api/instructor/state')).json()
    assert data['recordingState']['recording'] is None
    assert data['programState']['preview']['kind']=='unavailable'
    assert data['currentDisplay']['available'] and data['roomStatus']=='degraded'

@pytest.mark.asyncio
async def test_preferences_validate_and_persist_without_recording(client):
    prefs=Preferences(default_mode='assist',default_framing='wide').model_dump()
    assert (await client.put('/api/instructor/settings',json=prefs)).status_code==200
    assert (await client.get('/api/instructor/settings')).json()==prefs
    assert not store.state.devices.recording
    assert (await client.put('/api/instructor/settings',json={**prefs,'default_mode':'admin'})).status_code==422

@pytest.mark.asyncio
async def test_camera_follow_and_undo_restore_composite_framing(client):
    store.state.devices.camera_target='presenter'
    await client.post('/api/instructor/action',json={'tool':'camera_focus','args':{'target':'demo_zone'}})
    assert store.state.devices.camera_mode=='fixed'
    event=events[0]
    await client.post('/api/instructor/undo',json={'action_id':event['id']})
    assert store.state.devices.camera_target=='presenter' and store.state.devices.camera_mode=='follow'

@pytest.mark.asyncio
async def test_approved_actions_and_restrictions(client):
    await client.post('/api/instructor/mode',json={'mode':'assist'});await service.inference
    rec=store.pending
    store.state.restricted_capabilities=['camera']
    assert (await client.post(f'/api/instructor/recommendation/{rec.id}/apply')).status_code==200
    assert store.state.devices.camera_target=='instructor'
    assert not store.pending

@pytest.mark.asyncio
async def test_sim_video_engine_semantics():
    from app.video import SimVideoEngine
    engine=SimVideoEngine()
    await engine.start_recording();await engine.set_layout('demo_primary')
    assert (await engine.get_status())['recording'] is True
    assert (await engine.get_status())['layout']=='demo_primary'
    assert (await engine.preview())['kind']=='illustration'
    await engine.stop_recording()
    assert (await engine.get_status())['recording'] is False
