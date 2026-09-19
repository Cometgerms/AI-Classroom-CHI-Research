import asyncio
import json
from dataclasses import replace
import pytest
from httpx import ASGITransport,AsyncClient
from app.models import RoomState,Condition,Action
from app.state_store import store
from app.config import settings
from app.study_logger import logger
from app.runtime_config import load_config
from app.runtime import ClassroomRuntime
from app.simulation import load_scenario,frames
from app.pipeline import ObservationPipeline
from app.devices import executor
from app import study
from app.main import app

@pytest.fixture(autouse=True)
def clean(tmp_path,monkeypatch):
    store.state=RoomState();store.pending=None;store.history=[];store.revision=0
    store.control_lock=asyncio.Lock();store.lock=asyncio.Lock()
    monkeypatch.setattr(study,'lock',asyncio.Lock())
    monkeypatch.setattr(settings,'agent_backend','fake')
    monkeypatch.setattr(logger,'path',tmp_path/'events.jsonl')
    config=load_config(profile='simulation-basic',environ={})
    executor.configure(config['hardware'])
    monkeypatch.setattr(app.state,'audio_runtime',ClassroomRuntime(config),raising=False)

def test_protected_protocol_and_balanced_orders():
    p=study.PROTOCOL
    assert (p['participant_count'],p['facilitator_count'],p['student_count'],p['student_actors_required'])==(1,1,0,False)
    assert p['camera_targets']==['presenter','demo_zone','wide']
    assert len(p['tasks'])==14
    assert len(set(study.CONDITION_ORDERS))==6
    for pos in range(3):
        assert all(sum(order[pos]==c for order in study.CONDITION_ORDERS)==2 for c in Condition)
    assert 'scenario' not in study.public_protocol()['tasks'][11]
    for task in p['tasks']:
        if not task['scenario']: continue
        data=load_scenario(task['scenario'])
        assert not data['calibration']['calibrated']
        for frame in frames(data):
            assert len(frame.vision.tracks)==1
            assert all(t.role=='instructor' for t in frame.vision.tracks)
            assert frame.audio.doa_degrees is None
            assert not frame.scene.audience_speaking

@pytest.mark.asyncio
@pytest.mark.parametrize('name,expected',[('pre_class','PRE_CLASS'),('lecture','LECTURE'),('presenter_moves','LECTURE'),('whiteboard','DEMONSTRATION'),('demonstration','DEMONSTRATION'),('media_playback','MEDIA_PLAYBACK'),('source_change','LECTURE'),('transition','TRANSITION'),('post_class','POST_CLASS')])
async def test_presenter_estimation_without_doa_for_any_source(name,expected):
    config=load_config(environ={})
    pipeline=ObservationPipeline(config)
    for f in frames(load_scenario('v1_'+name)):
        # Identical real-source observations work; no runtime/simulation estimator branch.
        f.audio=replace(f.audio,source='xvf3800');f.vision=replace(f.vision,source='camera')
        await pipeline.consume(f)
    assert store.state.activity.state.value==expected

@pytest.mark.asyncio
@pytest.mark.parametrize('condition_index',[0,1,2])
async def test_complete_same_script_all_conditions(condition_index):
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/api/study/start',json={'counterbalance_index':0,'condition_position':condition_index})).status_code==200
        assigned=store.state.condition
        for index,task in enumerate(study.PROTOCOL['tasks']):
            response=await client.post('/api/study/next')
            assert response.status_code==200,response.text
            assert store.state.study.task_id==task['id']
            if index==11:
                if assigned==Condition.MANUAL: assert store.pending is None and not store.history
                elif assigned==Condition.ASSISTIVE:
                    assert store.pending.decision.actions[0].args=={'source':'camera'}
                    assert (await client.post('/api/recommendation/dismiss')).status_code==200
                else:
                    assert store.state.devices.display_source=='camera'
                    assert (await client.post('/api/override',json={'mode':'undo'})).status_code==200
                    assert store.state.devices.display_source!='camera'
            elif store.pending:
                assert (await client.post('/api/recommendation/apply')).status_code==200
            assert (await client.post('/api/study/complete',json={'outcome':'completed'})).status_code==200
        assert store.state.study.finished
        assert store.state.activity.state.value=='POST_CLASS'
        feedback={'perceived_control':5,'trust':4,'workload':3,'delegation_preferences':{'camera':'autonomous','display':'assistive','audio':'manual','recording':'manual'}}
        assert (await client.post('/api/study/feedback',json=feedback)).status_code==200
        rows=[json.loads(line) for line in logger.path.read_text().splitlines()]
        completions=[r for r in rows if r['event']=='study_task_completed']
        assert len(completions)==14 and all(r['payload']['response_latency_ms']>=0 for r in completions)
        assert all(r['payload']['assigned_condition']==assigned.value for r in completions)
        assert any(r['event']=='study_condition_feedback' for r in rows)
        assert all('controlled' not in r['payload'].get('instruction','') for r in rows)

@pytest.mark.asyncio
async def test_restriction_and_take_control_preserve_assigned_condition():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        await client.post('/api/study/start',json={'counterbalance_index':0,'condition_position':2})
        await client.post('/api/authority/restrict',json={'capability':'camera'})
        await client.post('/api/scenario/v1_demonstration')
        assert store.state.devices.camera_target=='presenter'
        await client.post('/api/override',json={'mode':'manual'})
        assert store.state.condition==Condition.MANUAL
        assert store.state.study.assigned_condition==Condition.AUTONOMOUS
        assert (await client.post('/api/scenario/student_question')).status_code==422

@pytest.mark.asyncio
@pytest.mark.parametrize('name,tool',[('camera','camera_focus'),('display','display_set_source'),('audio','audio_set_mode'),('recording','recording_set_layout')])
async def test_instructor_failure_variants(name,tool):
    store.state.condition=Condition.ASSISTIVE
    result=await app.state.audio_runtime.run_scenario('v1_wrong_'+name)
    assert result['recommendation'].decision.actions[0].tool==tool
    visible=json.dumps({'state':store.state.model_dump(mode='json'),'recommendation':store.pending.model_dump(mode='json')})
    assert 'injection' not in visible.lower() and 'v1_wrong' not in visible
    assert 'experiment_injection' in logger.path.read_text()

@pytest.mark.asyncio
async def test_optional_doa_failure_does_not_disable_speech():
    from app.services.audio.xvf3800.frontend import XVF3800AudioFrontEnd
    config=load_config(environ={})['audio'];config['speech_activity'].update(energy_threshold=.1,onset_ms=0)
    class Control:
        def get_doa(self): raise RuntimeError('DoA unavailable')
        def get_speech_energy(self): return [1.,1.,1.,1.]
    class Audio:
        def available(self): return True
    front=XVF3800AudioFrontEnd(Control(),Audio(),config)
    result=await front.poll()
    assert result.speech_active and result.audio_device_available and result.doa_degrees is None
    assert 'Optional DoA' in result.error

@pytest.mark.asyncio
async def test_study_scope_and_assignment_cannot_be_bypassed_by_replay():
    from app.runtime import Recording
    from app.models import StudyStartRequest
    await study.start(StudyStartRequest(counterbalance_index=0,condition_position=1))
    data=load_scenario('student_question')
    tape=Recording(calibration=data['calibration'],condition=Condition.ASSISTIVE,frames=list(frames(data)))
    with pytest.raises(ValueError,match='Multi-person replay'):
        await app.state.audio_runtime.replay(tape)
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
        assert (await client.post('/api/condition',json={'condition':'autonomous'})).status_code==409
        assert (await client.post('/api/study/feedback',json={'perceived_control':9})).status_code==422
    assert store.state.condition==Condition.ASSISTIVE
