import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .models import ConditionRequest, ManualActionRequest, ParticipantRequest, OverrideRequest, Condition
from .state_store import store
from .study_logger import logger
from .scenarios import SCENARIOS, apply_scenario
from .devices import executor
from .delegation import CAPABILITY_BY_TOOL
from .orchestrator import orchestrator

app = FastAPI(title="Agentic Classroom Milestone 1", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"ok": True, "agent_backend": settings.agent_backend, "model": settings.ollama_model}

@app.get("/api/state")
async def get_state():
    return {"state": await store.snapshot(), "recommendation": store.pending}

@app.get("/api/config")
async def config():
    return {"agent_backend": settings.agent_backend, "ollama_model": settings.ollama_model, "scenarios": list(SCENARIOS) + ["reset"]}

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

@app.post("/api/scenario/{name}")
async def scenario(name: str):
    if name not in SCENARIOS and name != "reset":
        raise HTTPException(404, "Unknown scenario")
    async with store.control_lock:
        store.pending = None
        state = await store.mutate(lambda s: apply_scenario(s, name))
    logger.log("scenario_injected", scenario=name, resulting_activity=state.activity.model_dump())
    result = await orchestrator.evaluate()
    return {"state": await store.snapshot(), **result}

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
