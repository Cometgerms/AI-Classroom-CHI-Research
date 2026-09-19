"""Instructor-facing API and view model. No research structures cross this boundary."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import httpx
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from .config import settings,runtime_config
from .runtime_config import ROOT
from .models import Action,Condition
from .state_store import store
from .devices import executor,DeviceUnavailable
from .delegation import CAPABILITY_BY_TOOL
from .orchestrator import orchestrator
from .study_logger import logger
from .product_events import events,public_events,action_label,TARGETS,SOURCES,AUDIO,LAYOUTS

router=APIRouter(prefix='/api/instructor')
MODES={'off':Condition.MANUAL,'assist':Condition.ASSISTIVE,'auto':Condition.AUTONOMOUS}
ACTIVITIES={'PRE_CLASS':'Ready','LECTURE':'Presentation','DEMONSTRATION':'Demonstration','MEDIA_PLAYBACK':'Media playback',
            'TRANSITION':'Transition','POST_CLASS':'Session ended'}
PREFERENCES_PATH=ROOT/'config/local.product.json'

class Preferences(BaseModel):
    model_config=ConfigDict(extra='forbid')
    default_mode: Literal['off','assist','auto']='off'
    local_model: str=Field(default='qwen3:8b',pattern=r'^[a-zA-Z0-9_.:/-]{1,100}$')
    default_framing: Literal['presenter','demo_zone','wide']='presenter'
    follow_presenter: bool=True
    default_layout: Literal['slides_plus_instructor','demo_primary','media_primary','wide']='slides_plus_instructor'

class ModeRequest(BaseModel):
    mode: Literal['off','assist','auto']
class UndoRequest(BaseModel):
    action_id: str

class ProductService:
    def __init__(self):
        self.preferences=Preferences()
        self.status='connecting';self.error=None;self.busy=False
        self.monitor=None;self.inference=None
    async def probe(self):
        if settings.agent_backend!='ollama': self.status='ready';return
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response=await client.get(settings.ollama_base_url.rstrip('/')+'/api/tags')
                response.raise_for_status()
            names={m['name'] for m in response.json()['models']}
            self.status='ready' if settings.ollama_model in names else 'disconnected'
        except Exception: self.status='disconnected'
    async def watch(self):
        while True:
            await self.probe()
            await asyncio.sleep(10)
    async def start(self):
        try: self.preferences=Preferences.model_validate_json(PREFERENCES_PATH.read_text())
        except FileNotFoundError: self.preferences=Preferences(local_model=settings.ollama_model)
        except Exception: self.error='Saved preferences could not be loaded. Using safe defaults.'
        settings.ollama_model=self.preferences.local_model
        self.monitor=asyncio.create_task(self.watch())
        if runtime_config['runtime']['profile']!='study':
            async with store.control_lock:
                await store.mutate(lambda state:setattr(state,'condition',MODES[self.preferences.default_mode]))
                # Simulated initial framing is explicit; never fabricate physical device state.
                for subsystem,action in [('camera_control',Action(tool='camera_focus',args={'target':self.preferences.default_framing})),
                    ('camera_control',Action(tool='camera_set_follow',args={'enabled':self.preferences.follow_presenter})),
                    ('recorder',Action(tool='recording_set_layout',args={'layout':self.preferences.default_layout}))]:
                    if executor.backends[subsystem]=='simulation': await executor.execute(action,actor='system')
            self.schedule()
    async def stop(self):
        tasks=[task for task in (self.monitor,self.inference) if task]
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    def schedule(self):
        if self.inference and not self.inference.done(): self.inference.cancel()
        self.busy=False
        if store.state.condition!=Condition.MANUAL:
            self.inference=asyncio.create_task(self.evaluate())
    async def evaluate(self):
        self.busy=True;self.error=None
        try: await orchestrator.evaluate()
        except asyncio.CancelledError: raise
        except Exception as exc:
            self.error='AI could not respond. Your room controls are still available.'
            logger.log('product_ai_unavailable',error=str(exc))
            await self.probe()
        finally: self.busy=False

service=ProductService()

def expire_recommendation():
    rec=store.pending
    if rec and (datetime.now(timezone.utc)-datetime.fromisoformat(rec.created_at)).total_seconds()>45:
        logger.log('recommendation_expired',recommendation_id=rec.id)
        store.pending=None

async def devices_view(runtime):
    hardware=runtime.config['hardware']
    audio=await runtime.audio.status()
    video=await executor.video.get_status()
    def output(name,label):
        simulated=executor.backends[name]=='simulation'
        status='ready' if simulated and name not in executor.failed else 'disconnected'
        return {'id':name,'label':label,'status':status,'detail':'Simulated device' if simulated else 'Adapter not connected'}
    camera_sim=hardware['camera']=='simulation'
    camera_ready=camera_sim or bool(getattr(runtime.camera,'capture',None))
    return [output('camera_control','Camera control'),
        {'id':'camera','label':'Room camera','status':'ready' if camera_ready else 'disconnected','detail':'Simulated input' if camera_sim else 'Local camera'},
        {'id':'audio','label':'Instructor microphone','status':'ready' if audio.audio_available else 'disconnected',
         'detail':'Simulated input' if audio.source=='simulation' else 'XVF3800'},
        output('audio_output','Room audio'),output('projector','Room display'),
        {'id':'input','label':'Presentation input','status':'ready' if hardware['projector']=='simulation' else 'disconnected',
         'detail':'Simulated input' if hardware['projector']=='simulation' else 'Input sensing not connected'},
        {'id':'recorder','label':'Video engine','status':'disconnected' if 'recorder' in executor.failed else video['status'],
         'detail':'Simulated engine' if video['simulated'] else 'OBS'},
        {'id':'ai','label':'Local AI','status':service.status,'detail':'Local processing' if settings.agent_backend=='ollama' else 'Demo responses'}]

@router.get('/state')
async def view():
    from .main import classroom_runtime
    runtime=classroom_runtime()
    async with store.control_lock:
        expire_recommendation()
        state=await store.snapshot();rec=store.pending
    device_states=await devices_view(runtime)
    video=await executor.video.get_status();preview=await executor.video.preview()
    if 'recorder' in executor.failed:
        video={**video,'status':'disconnected','recording':None,'startedAt':None,'layout':None}
        preview={'kind':'unavailable','label':'Preview unavailable','description':'Video engine disconnected.'}
    available={item['id']:item['status']=='ready' for item in device_states}
    activity=ACTIVITIES.get(state.activity.state.value,'Watching…') if state.activity.confidence>=.65 else 'Watching…'
    if state.activity.state.value=='TRANSITION': activity='Transition'
    if runtime.latest is None: activity='Watching…'
    pending=None
    if rec:
        pending={'id':rec.id,'title':f'Adjust the room for {activity.lower()}?',
                 'actions':[action_label(a) for a in rec.decision.actions],
                 'why':'These changes match the current classroom activity. You decide whether to apply them.'}
    return {'roomStatus':'ready' if all(d['status']=='ready' for d in device_states if d['id']!='ai') else 'degraded',
        'aiMode':next(k for k,v in MODES.items() if v==state.condition),
        'ai':{'status':service.status,'busy':service.busy,'message':service.error,
              'label':'Local AI' if settings.agent_backend=='ollama' else 'AI demo'},
        'currentActivity':activity,
        'currentDisplay':{'source':state.devices.display_source,'label':SOURCES.get(state.devices.display_source,'Unknown'),'available':available['projector']},
        'cameraState':{'target':state.devices.camera_target,'label':TARGETS.get(state.devices.camera_target,'Other framing'),
                       'follow':state.devices.camera_mode=='follow','available':available['camera_control'],'zone':state.observations.presenter_zone},
        'audioState':{'mode':state.devices.audio_mode,'label':AUDIO.get(state.devices.audio_mode,'Presentation'),
                      'available':available['audio_output'],'microphoneActive':available['audio'] and state.observations.instructor_speaking,
                      'programActive':state.observations.program_audio and state.devices.audio_mode!='mute'},
        'recordingState':video,
        'programState':{'layout':video['layout'],'label':LAYOUTS.get(video['layout'],'Unknown'),'preview':preview},
        'recentActions':public_events(),'pendingRecommendation':pending,'devices':device_states,
        'restrictions':state.restricted_capabilities}

@router.post('/mode')
async def mode(req:ModeRequest):
    async with store.control_lock:
        if store.state.study and not store.state.study.finished and req.mode!='off':
            raise HTTPException(409,'An existing session controls authority. Finish it in the research tools first.')
        store.pending=None
        await store.mutate(lambda state:setattr(state,'condition',MODES[req.mode]))
        logger.log('product_ai_mode_changed',mode=req.mode)
    service.schedule()
    return {'mode':req.mode}

@router.post('/take-control')
async def take_control():
    result=await mode(ModeRequest(mode='off'))
    logger.log('participant_override',mode='manual',capability='all')
    return result

@router.post('/action')
async def action(action:Action):
    async with store.control_lock:
        store.pending=None
        # Explicit human intervention invalidates any in-flight AI result, even on failure.
        store.revision+=1
        try: result=await executor.execute(action,actor='instructor')
        except DeviceUnavailable: raise HTTPException(503,'Device unavailable. No change was confirmed.')
        logger.log('participant_manual_action',action=action.model_dump())
    return {'ok':True}

@router.post('/recommendation/{recommendation_id}/{operation}')
async def recommendation(recommendation_id:str,operation:Literal['apply','ignore']):
    async with store.control_lock:
        expire_recommendation()
        rec=store.pending
        if not rec or rec.id!=recommendation_id or store.state.condition!=Condition.ASSISTIVE:
            raise HTTPException(409,'This suggestion is no longer current.')
        store.pending=None;store.revision+=1
        if operation=='apply':
            for proposed in rec.decision.actions:
                if CAPABILITY_BY_TOOL[proposed.tool] in store.state.restricted_capabilities: continue
                try: await executor.execute(proposed,actor='approved')
                except DeviceUnavailable:
                    logger.log('recommendation_failed',recommendation_id=rec.id)
                    raise HTTPException(503,'A device is unavailable. Check the current room state; some changes may have applied.')
        logger.log('recommendation_applied' if operation=='apply' else 'recommendation_dismissed',recommendation_id=rec.id,
                   response_latency_ms=(datetime.now(timezone.utc)-datetime.fromisoformat(rec.created_at)).total_seconds()*1000)
    return {'ok':True}

@router.post('/undo')
async def undo(req:UndoRequest):
    async with store.control_lock:
        if not events or events[0]['id']!=req.action_id or not events[0]['inverse']:
            raise HTTPException(409,'That change can no longer be undone safely.')
        event=events[0]
        expected=event.get('expected') or {event['field']:event['after']}
        if any(getattr(store.state.devices,key)!=value for key,value in expected.items()):
            raise HTTPException(409,'The room has changed since that action.')
        store.pending=None;store.revision+=1
        inverses=event.get('restore') or [event['inverse']]
        try:
            for inverse in inverses:
                await executor.execute(Action(**inverse,reason='Instructor undo'),actor='instructor')
        except DeviceUnavailable: raise HTTPException(503,'Device unavailable. Undo was not confirmed.')
        events[0]['label']='Undid '+event['label'].lower();events[0]['inverse']=None
        logger.log('participant_override',mode='undo',action_id=req.action_id)
    return {'ok':True}

@router.get('/settings')
async def preferences(): return service.preferences

@router.put('/settings')
async def save_preferences(req:Preferences):
    temp=PREFERENCES_PATH.with_suffix('.tmp')
    temp.write_text(req.model_dump_json(indent=2));temp.replace(PREFERENCES_PATH)
    service.preferences=req
    async with store.control_lock:
        settings.ollama_model=req.local_model
        store.pending=None;store.revision+=1
    await service.probe()
    return req

@router.get('/diagnostics')
async def diagnostics():
    from .main import classroom_runtime
    return {'profile':runtime_config['runtime']['profile'],'agent':settings.agent_backend,'model':settings.ollama_model,
            'state':await store.snapshot(),'runtime':await classroom_runtime().snapshot(),
            'video':await executor.video.get_status()}
