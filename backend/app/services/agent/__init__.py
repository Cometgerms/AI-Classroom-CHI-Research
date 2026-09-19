"""Compatibility facade; canonical implementations remain in app.agent."""
from ...agent.base import RoomAgent
from ...agent.fake import FakeAgent
from ...agent.rule import RuleAgent
from ...agent.ollama import OllamaAgent
