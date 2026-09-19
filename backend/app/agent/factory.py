from .rule import RuleAgent
from .fake import FakeAgent
from .ollama import OllamaAgent
from ..config import settings

def get_agent():
    if settings.agent_backend.lower() == "ollama":
        return OllamaAgent()
    if settings.agent_backend.lower() == "rule":
        return RuleAgent()
    return FakeAgent()
