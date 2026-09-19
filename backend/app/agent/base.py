from abc import ABC, abstractmethod
from ..models import AgentDecision, RoomState

class RoomAgent(ABC):
    @abstractmethod
    async def decide(self, state: RoomState) -> AgentDecision:
        raise NotImplementedError
