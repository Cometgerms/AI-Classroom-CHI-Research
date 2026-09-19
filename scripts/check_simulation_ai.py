"""Strict local Qwen smoke: normalized observations → estimator → agent → authority → AV."""
import asyncio
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['CLASSROOM_PROFILE']='simulation-ai'
os.environ['AGENT_BACKEND']='ollama'
sys.path.insert(0,str(ROOT/'backend'))
from app.runtime import ClassroomRuntime
from app.config import runtime_config,settings
from app.state_store import store
from app.models import RoomState,Condition,ActivityState
from app.devices import executor
from app.study_logger import logger

async def main():
    logger.path=ROOT/'backend/data/simulation_ai_smoke.jsonl'
    settings.ollama_strict=True
    runtime=ClassroomRuntime(runtime_config)
    results=[]
    for condition in Condition:
        store.state=RoomState(condition=condition);store.pending=None;store.history=[]
        executor.configure(runtime_config['hardware'])
        result=await runtime.run_scenario('student_question')
        assert store.state.activity.state==ActivityState.Q_AND_A
        if condition==Condition.MANUAL:
            assert result['decision'] is None and not store.history
        else:
            assert result['decision'].actions
            assert 'fallback' not in result['decision'].rationale.lower()
            if condition==Condition.ASSISTIVE: assert store.pending and not store.history
            else: assert result['executed'] and not result['failures']
        results.append({'condition':condition.value,'status':'PASS','activity':store.state.activity.state.value,
                        'tools':[a.tool for a in result['decision'].actions] if result['decision'] else []})
        print(json.dumps(results[-1]),flush=True)
    report={'profile':'simulation-ai','agent':settings.ollama_model,'strict':True,'results':results}
    (ROOT/'artifacts/simulation_ai_smoke.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': asyncio.run(main())
