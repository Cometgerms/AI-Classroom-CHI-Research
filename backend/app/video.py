"""Video-engine boundary. No vendor protocol leaks into application or agent code."""
from typing import Protocol
from .models import Action
from .state_store import store

class VideoEngineUnavailable(RuntimeError): pass

class VideoEngine(Protocol):
    async def set_layout(self,layout: str): ...
    async def start_recording(self): ...
    async def stop_recording(self): ...
    async def get_status(self) -> dict: ...
    async def preview(self) -> dict: ...

class SimVideoEngine:
    async def _execute(self,action):
        from .devices import SimDeviceExecutor
        return await SimDeviceExecutor().execute(action)
    async def set_layout(self,layout):
        return await self._execute(Action(tool='recording_set_layout',args={'layout':layout}))
    async def start_recording(self): return await self._execute(Action(tool='recording_start'))
    async def stop_recording(self): return await self._execute(Action(tool='recording_stop'))
    async def get_status(self):
        state=await store.snapshot()
        return {'status':'ready','simulated':True,'recording':state.devices.recording,
                'startedAt':state.devices.recording_started_at,'layout':state.devices.recording_layout}
    async def preview(self):
        return {'kind':'illustration','label':'Composition preview','description':'Illustrated preview · no live video feed'}

class OBSVideoEngine:
    """Reserved V1 engine adapter: honest unavailable until OBS transport is implemented.

    Implement the protocol here in the next hardware milestone. No fake acknowledgements,
    guessed connection status or simulated preview when OBS has been selected.
    """
    async def set_layout(self,layout): raise VideoEngineUnavailable('Video engine disconnected. Display control is still available.')
    async def start_recording(self): raise VideoEngineUnavailable('Video engine disconnected. Recording did not start.')
    async def stop_recording(self): raise VideoEngineUnavailable('Video engine disconnected. Recording status is unknown.')
    async def get_status(self):
        return {'status':'disconnected','simulated':False,'recording':None,'startedAt':None,'layout':None}
    async def preview(self):
        return {'kind':'unavailable','label':'Preview unavailable','description':'Connect the video engine to see the program.'}
