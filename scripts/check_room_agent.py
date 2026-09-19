"""Live Ollama integration through the same study API; no optional perception imports."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path
from ai_common import ROOT, save
sys.path.insert(0,str(ROOT/'backend'))
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.config import settings
from app.state_store import store
from app.study_logger import logger
from app.models import RoomState

async def main():
    settings.agent_backend='ollama'
    settings.ollama_strict=True
    settings.ollama_fallback_model=''
    results=[]
    with tempfile.TemporaryDirectory() as temp:
        logger.path=Path(temp)/'events.jsonl'
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
            for condition in ('manual','assistive','autonomous'):
                store.state=RoomState()
                store.pending=None
                store.history=[]
                await client.post('/api/condition',json={'condition':condition})
                before=store.state.devices.model_copy(deep=True)
                result=(await client.post('/api/scenario/student_question')).json()
                if condition=='manual':
                    assert result['decision'] is None and store.state.devices==before
                elif condition=='assistive':
                    assert store.state.devices==before and result['recommendation']
                    assert (await client.post('/api/recommendation/apply')).status_code==200
                    assert store.state.devices!=before
                else:
                    assert result['executed'] and store.state.devices!=before
                    await client.post('/api/override',json={'mode':'manual'})
                    assert store.state.condition.value=='manual'
                results.append({'condition':condition,'status':'PASS','backend':'ollama','model':settings.ollama_model})
                print(results[-1],flush=True)
    save('room_agent_integration.json',results)

if __name__=='__main__':
    asyncio.run(main())
