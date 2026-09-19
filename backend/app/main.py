import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings, runtime_config
from contextlib import asynccontextmanager
from .runtime import ClassroomRuntime, Recording
from .observations import ObservationFrame, SceneObservation
from .simulation import catalog
from fastapi.responses import JSONResponse
from .models import ConditionRequest, ManualActionRequest, ParticipantRequest, OverrideRequest, Condition
from .state_store import store
from .study_logger import logger
from .scenarios import SCENARIOS, apply_scenario
from .devices import executor, DeviceUnavailable
from .delegation import CAPABILITY_BY_TOOL
from .orchestrator import orchestrator

@asynccontextmanager
async def lifespan(app):
    app.state.audio_runtime = ClassroomRuntime(runtime_config)
    await app.state.audio_runtime.start()
    try:
        yield
    finally:
        await app.state.audio_runtime.stop()

app = FastAPI(title="Agentic Classroom Milestone 1", version="0.2.0", lifespan=lifespan)

@app.get('/api/audio')
async def audio_status():
    runtime = getattr(app.state, 'audio_runtime', None)
    if runtime is None:
        return {'status': 'not_started'}
    return await runtime.snapshot()

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"ok": True, "agent_backend": settings.agent_backend, "model": settings.ollama_model}

@app.get("/api/state")
async def get_state():
    return {"state": await store.snapshot(), "recommendation": store.pending}

@app.get("/api/config")
async def config(researcher: bool = False):
    participant=runtime_config['runtime'].get('participant_view',False) and not researcher
    return {"runtime":runtime_config['runtime']['label'],"profile":runtime_config['runtime']['profile'],
            "participant_view":participant,"agent_backend": settings.agent_backend, "ollama_model": settings.ollama_model,
            "scenarios": [] if participant else catalog()}

@app.post("/api/participant")
async def participant(req: ParticipantRequest):
    async with store.control_lock:
        store.pending = None
        state = await store.mutate(lambda s: setattr(s, "participant_id", req.participant_id))
        logger.log("participant_set", participant_id=req.participant_id)
        return state

@app.post("/api/condition")
async def condition(req: ConditionRequest):
    async with store.control_lock:
        store.pending = None
        state = await store.mutate(lambda s: setattr(s, "condition", req.condition))
        logger.log("condition_changed", condition=req.condition.value, participant_id=state.participant_id)
        return state

def classroom_runtime():
    if not hasattr(app.state,'audio_runtime'):
        app.state.audio_runtime=ClassroomRuntime(runtime_config)
    return app.state.audio_runtime

@app.exception_handler(DeviceUnavailable)
async def device_unavailable(request,exc):
    return JSONResponse(status_code=503,content={'detail':str(exc)})

@app.post("/api/scenario/{name}")
async def scenario(name: str, realtime: bool = False):
    try: return await classroom_runtime().run_scenario(name,realtime)
    except KeyError: raise HTTPException(404,'Unknown scenario')
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.get('/api/replay')
async def export_recording():
    return classroom_runtime().recording

@app.post('/api/replay')
async def replay(recording: Recording, realtime: bool = False):
    try: return await classroom_runtime().replay(recording,realtime)
    except ValueError as exc: raise HTTPException(422,str(exc))

@app.post('/api/observations')
async def normalized_observation(frame: ObservationFrame):
    runtime=classroom_runtime()
    if runtime.task or runtime.lock.locked(): raise HTTPException(409,'Live acquisition or trial playback owns the observation clock')
    await runtime.pipeline.consume(frame)
    return await orchestrator.evaluate()

@app.post('/api/scene')
async def scene_observation(scene: SceneObservation):
    classroom_runtime().scene=scene
    return scene

@app.post('/api/simulation/sensors')
async def simulated_sensor_input(frame: ObservationFrame):
    runtime=classroom_runtime()
    from .services.audio.simulation import SimAudioFrontEnd
    from .services.vision.observation import SimCameraPerception
    selected=[]
    if isinstance(runtime.audio,SimAudioFrontEnd):
        runtime.audio.publish(frame.audio);selected.append('audio')
    if isinstance(runtime.camera,SimCameraPerception):
        runtime.camera.publish(frame.vision);selected.append('camera')
    runtime.scene=frame.scene
    return {'updated_simulated_adapters':selected}

@app.post('/api/debug/scenario/{name}')
async def debug_scenario(name: str):
    if runtime_config['runtime'].get('participant_view'): raise HTTPException(403,'Debug injection disabled in study')
    if name not in SCENARIOS and name!='reset': raise HTTPException(404,'Unknown scenario')
    async with store.control_lock:
        store.pending=None
        await store.mutate(lambda s: apply_scenario(s,name))
    logger.log('debug_semantic_injection',scenario=name)
    return await orchestrator.evaluate()

@app.post("/api/agent/evaluate")
async def evaluate():
    return await orchestrator.evaluate()

@app.post("/api/manual/action")
async def manual_action(req: ManualActionRequest):
    async with store.control_lock:
        store.pending = None
        state = await executor.execute(req.action)
        logger.log("participant_manual_action", action=req.action.model_dump(), participant_id=state.participant_id, condition=state.condition.value)
        return state

@app.post("/api/recommendation/apply")
async def recommendation_apply():
    async with store.control_lock:
        if (await store.snapshot()).condition != Condition.ASSISTIVE:
            raise HTTPException(409, "Approval requires Assistive condition")
        rec = store.pending
        if not rec:
            raise HTTPException(404, "No pending recommendation")
        actions = rec.decision.actions
        store.pending = None
        for a in actions:
            await executor.execute(a)
        state = await store.snapshot()
        logger.log("recommendation_applied", recommendation_id=rec.id, actions=[a.model_dump() for a in actions], participant_id=state.participant_id)
        await store.broadcast()
        return state

@app.post("/api/recommendation/dismiss")
async def recommendation_dismiss():
    async with store.control_lock:
        store.revision += 1
        rec = store.pending
        if not rec:
            raise HTTPException(404, "No pending recommendation")
        store.pending = None
        state = await store.snapshot()
        logger.log("recommendation_dismissed", recommendation_id=rec.id, participant_id=state.participant_id)
        await store.broadcast()
        return state

@app.post("/api/override")
async def override(req: OverrideRequest):
    async with store.control_lock:
        store.revision += 1
        store.pending = None
        state = await store.undo() if req.mode == "undo" else await store.snapshot()
        if req.mode == "manual":
            # M1 uses global condition for the 3-level study. Fine-grained capability authority comes in Milestone 1.5/2.
            state = await store.mutate(lambda s: setattr(s, "condition", Condition.MANUAL))
        logger.log("participant_override", capability=req.capability, mode=req.mode, participant_id=state.participant_id)
        return state

@app.get("/api/logs/recent")
async def logs(limit: int = 100):
    return logger.recent(limit)

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    q = asyncio.Queue(maxsize=10)
    store.subscribers.add(q)
    try:
        await websocket.send_json((await store.snapshot()).model_dump(mode="json"))
        while True:
            payload = await q.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        store.subscribers.discard(q)
