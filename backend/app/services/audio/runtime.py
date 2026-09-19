"""Audio collection boundary. Polling never holds the room authority lock or invokes an LLM."""
import asyncio
from dataclasses import asdict
from .factory import create_audio_frontend
from ..active_speaker import ActiveSpeakerFusion, CameraCalibration

class AudioRuntime:
    def __init__(self,config):
        self.frontend=create_audio_frontend(config)
        self.fusion=ActiveSpeakerFusion(CameraCalibration(**config['camera']['calibration']),**config['fusion'])
        self.latest=None
        self.active_speaker=None
        self.tracks=[]
        self.task=None

    async def start(self):
        await self.frontend.start()
        self.task=asyncio.create_task(self.collect())

    async def collect(self):
        async for observation in self.frontend.observations():
            self.latest=observation
            self.active_speaker=self.fusion.process(observation,self.tracks)

    def update_people(self, people, frame_width, timestamp, roles=None):
        """Bridge existing PersonTracker output to calibrated fusion, without framework objects."""
        from ..active_speaker import PersonTrack
        if frame_width <= 0: raise ValueError('Expected positive frame width')
        roles = roles or {}
        self.tracks = [PersonTrack(str(p.track_id), (p.bounding_box[0]+p.bounding_box[2])/(2*frame_width),
                                   timestamp, roles.get(str(p.track_id), 'unknown'), p.confidence)
                       for p in people if p.track_id is not None]

    def update_tracks(self,tracks):
        self.tracks=list(tracks)

    async def stop(self):
        # Do not close libusb while a bounded background read is still using it.
        self.frontend.running=False
        if self.task: await self.task
        await self.frontend.stop()

    async def snapshot(self):
        return {'status':asdict(await self.frontend.status()),
                'observation':asdict(self.latest) if self.latest else None,
                'active_speaker':asdict(self.active_speaker) if self.active_speaker else None}
