"""CHI V1 protocol and task bookkeeping; sensing/agents still use the shared runtime."""
import asyncio
from datetime import datetime, timezone
from itertools import permutations
from uuid import uuid4
import yaml
from .runtime_config import ROOT
from .models import Condition, StudyProgress, DeviceState
from .state_store import store
from .study_logger import logger

PROTOCOL=yaml.safe_load((ROOT/'config/study/chi_v1.yaml').read_text())
assert (PROTOCOL['participant_count'],PROTOCOL['facilitator_count'],PROTOCOL['student_count'],PROTOCOL['student_actors_required'])==(1,1,0,False)
CONDITION_ORDERS=list(permutations(Condition))
lock=asyncio.Lock()

def now(): return datetime.now(timezone.utc).isoformat()
def elapsed(start): return max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(start)).total_seconds()*1000) if start else None

def public_protocol():
    return {key:value for key,value in PROTOCOL.items() if key!='tasks'} | {
        'tasks':[{'id':task['id'],'instruction':task['instruction']} for task in PROTOCOL['tasks']],
        'condition_orders':[[condition.value for condition in order] for order in CONDITION_ORDERS]}

async def start(req):
    async with lock,store.control_lock:
        if store.state.study and not store.state.study.finished:
            raise ValueError('Finish the current condition before starting another')
        order=CONDITION_ORDERS[req.counterbalance_index]
        progress=StudyProgress(run_id=str(uuid4()),assigned_condition=order[req.condition_position],
                               condition_order=list(order),condition_position=req.condition_position)
        store.pending=None;store.history=[]
        def update(state):
            state.study=progress;state.condition=progress.assigned_condition
            state.restricted_capabilities=[];state.devices=DeviceState(camera_target='presenter')
        await store.mutate(update)
        logger.log('study_condition_started',counterbalance_index=req.counterbalance_index,condition_position=req.condition_position,
                   order=[c.value for c in order],protocol=PROTOCOL['protocol'])
        return await store.snapshot()

async def advance(runtime):
    async with lock:
        async with store.control_lock:
            progress=store.state.study
            if not progress or progress.finished: raise ValueError('Start a study condition first')
            if progress.task_index>=0 and not progress.completed: raise ValueError('Record task completion before advancing')
            index=progress.task_index+1
            if index>=len(PROTOCOL['tasks']): raise ValueError('All tasks are complete')
            task=PROTOCOL['tasks'][index]
            def update(state):
                state.study.task_index=index;state.study.task_id=task['id'];state.study.instruction=task['instruction']
                state.study.started_at=now();state.study.completed=False
            await store.mutate(update)
            logger.log('study_task_started',task_id=task['id'],task_number=index+1)
        if task['scenario']:
            # Sensor timeline and experiment injections use the same runtime as ordinary development.
            await runtime.run_scenario(task['scenario'])
        return await store.snapshot()

async def complete(req):
    async with lock,store.control_lock:
        progress=store.state.study
        if not progress or progress.task_index<0 or progress.completed: raise ValueError('No active unfinished task')
        logger.log('study_task_completed',outcome=req.outcome,notes=req.notes,response_latency_ms=elapsed(progress.started_at))
        def update(state):
            state.study.completed=True
            state.study.finished=state.study.task_index==len(PROTOCOL['tasks'])-1
        await store.mutate(update)
        if store.state.study.finished: logger.log('study_condition_completed')
        return await store.snapshot()

async def feedback(req):
    async with store.control_lock:
        if not store.state.study or not store.state.study.finished: raise ValueError('Complete the condition before feedback')
        logger.log('study_condition_feedback',**req.model_dump(mode='json'))
        return {'recorded':True}
