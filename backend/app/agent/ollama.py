import json
import httpx
from .base import RoomAgent
from .fake import FakeAgent
from ..config import settings
from ..models import Action, ActivityState, AgentDecision, RoomState

TOOLS = [
    {"type":"function","function":{"name":"camera_focus","description":"Frame a classroom target. Use only high-level targets; never camera coordinates.","parameters":{"type":"object","properties":{"target":{"type":"string","description":"instructor, wide, demo_zone, or active speaker/person id"}},"required":["target"]}}},
    {"type":"function","function":{"name":"display_set_source","description":"Select the primary classroom display source.","parameters":{"type":"object","properties":{"source":{"type":"string","enum":["presentation","room_pc","camera"]}},"required":["source"]}}},
    {"type":"function","function":{"name":"audio_set_mode","description":"Select a safe preconfigured audio mode; do not set raw gain.","parameters":{"type":"object","properties":{"mode":{"type":"string","enum":["lecture","media","discussion"]}},"required":["mode"]}}},
    {"type":"function","function":{"name":"student_voice_lift","description":"Request the safe student voice-lift mode on or off.","parameters":{"type":"object","properties":{"enabled":{"type":"boolean"}},"required":["enabled"]}}},
    {"type":"function","function":{"name":"recording_set_layout","description":"Choose recording composition; does not itself start or stop recording.","parameters":{"type":"object","properties":{"layout":{"type":"string","enum":["slides_plus_instructor","q_and_a","media_primary","demo_primary","wide"]}},"required":["layout"]}}},
]

SYSTEM = """You are the local supervisory AV agent for a university classroom research prototype.
You receive STRUCTURED room state, not raw camera/audio. Decide the smallest useful set of intent-level AV actions. /no_think
Rules:
- Never emit raw PJLink, ONVIF, shell, HTTP, gain, DSP, or camera-coordinate commands.
- Use only the provided tools.
- When study.protocol is chi_v1_instructor, one instructor/TA teaches with a facilitator; there are no students or student actors. Camera targets are presenter, demo_zone, wide. Never request student voice lift, student targeting, discussion audio or Q&A layout in this protocol.
- PRE_CLASS prepares teaching; POST_CLASS ends teaching. Recording transport remains participant-only.
- Respect observations.presentation_source and presenter_zone. DoA is optional; do not require student identification or localization.
- Prefer no action for SIDE_CONVERSATION, UNKNOWN, or ambiguous situations.
- Do not start or stop recording unless a future explicit policy/tool allows it.
- Camera framing is lower consequence than audio or recording.
- The backend delegation/safety layer is authoritative; you only propose intent.
- Avoid redundant actions that already match device state when possible.
"""

class OllamaAgent(RoomAgent):
    def __init__(self):
        self.fake = FakeAgent()

    async def _call(self, model: str, state: RoomState) -> AgentDecision:
        payload = {
            "model": model,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_ctx": 8192},
            "messages": [
                {"role":"system","content":SYSTEM},
                {"role":"user","content":"Current room state:\n" + state.model_dump_json(indent=2)},
            ],
            "tools": TOOLS,
        }
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            r = await client.post(settings.ollama_base_url.rstrip("/") + "/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message", {})
        calls = msg.get("tool_calls") or []
        actions=[]
        for c in calls:
            fn = c.get("function", {})
            name = fn.get("name")
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
            if name in {t["function"]["name"] for t in TOOLS}:
                actions.append(Action(tool=name, args=args, reason="Selected by local Ollama agent", confidence=state.activity.confidence))
        return AgentDecision(
            activity_state=state.activity.state,
            activity_confidence=state.activity.confidence,
            rationale=msg.get("content") or f"Local {model} tool decision",
            actions=actions,
        )

    async def decide(self, state: RoomState) -> AgentDecision:
        errors=[]
        for model in dict.fromkeys(filter(None, [settings.ollama_model, settings.ollama_fallback_model])):
            try:
                return await self._call(model, state)
            except Exception as e:
                errors.append(f"{model}: {e}")
        if settings.ollama_strict:
            raise RuntimeError("Ollama unavailable: " + " | ".join(errors))
        decision = await self.fake.decide(state)
        decision.rationale = "Ollama unavailable; FakeAgent fallback. " + " | ".join(errors)
        return decision
