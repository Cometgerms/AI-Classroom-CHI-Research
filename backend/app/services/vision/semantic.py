"""Explicit one-frame ambiguity escalation. Never called by a continuous video loop."""
import base64
import json
import httpx
from pydantic import BaseModel, Field
from ...models import ActivityState

class VisualActivity(BaseModel):
    activity: ActivityState
    confidence: float = Field(ge=0,le=1)

class SemanticVision:
    def __init__(self, base_url='http://localhost:11434', model='qwen3-vl:2b-instruct'):
        self.base_url,self.model=base_url.rstrip('/'),model

    async def classify(self, image: bytes, *, ambiguous: bool) -> VisualActivity | None:
        if not ambiguous:
            return None
        async with httpx.AsyncClient(timeout=120) as client:
            response=await client.post(self.base_url+'/api/chat',json={
                'model':self.model,'stream':False,'format':VisualActivity.model_json_schema(),
                'messages':[{'role':'user','content':'Classify classroom activity. Use UNKNOWN when evidence is insufficient.',
                    'images':[base64.b64encode(image).decode()]}]})
            response.raise_for_status()
        return VisualActivity.model_validate_json(response.json()['message']['content'])
