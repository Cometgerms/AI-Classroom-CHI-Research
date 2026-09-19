import asyncio
from copy import deepcopy
from .models import RoomState, Recommendation

class StateStore:
    def __init__(self):
        self.state = RoomState()
        self.pending: Recommendation | None = None
        self.history: list[RoomState] = []
        self.revision = 0
        self.control_lock = asyncio.Lock()
        self.lock = asyncio.Lock()
        self.subscribers: set[asyncio.Queue] = set()

    async def snapshot(self) -> RoomState:
        async with self.lock:
            return self.state.model_copy(deep=True)

    async def mutate(self, fn):
        async with self.lock:
            fn(self.state)
            self.revision += 1
            snap = self.state.model_copy(deep=True)
        await self.broadcast()
        return snap

    async def push_history(self):
        async with self.lock:
            self.history.append(self.state.model_copy(deep=True))
            if len(self.history) > 50:
                self.history = self.history[-50:]

    async def undo(self):
        async with self.lock:
            if not self.history:
                return self.state.model_copy(deep=True)
            previous = self.history.pop()
            # Preserve study identity/condition while undoing device action.
            self.state.devices = previous.devices.model_copy(deep=True)
            self.revision += 1
            snap = self.state.model_copy(deep=True)
        await self.broadcast()
        return snap

    async def broadcast(self):
        payload = self.state.model_dump(mode="json")
        for q in list(self.subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

store = StateStore()
