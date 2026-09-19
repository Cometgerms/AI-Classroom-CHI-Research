import asyncio
import time
from dataclasses import replace
from .models import AudioObservation, AudioStatus

class SimAudioFrontEnd:
    def __init__(self, frames=None, poll_hz=10):
        self.frames=list(frames or [AudioObservation(0,audio_device_available=True,activity_calibrated=True)])
        self.poll_hz=poll_hz
        self.running=False

    def publish(self, observation: AudioObservation): self.frames=[observation]

    async def start(self): self.running=True
    async def stop(self): self.running=False
    async def status(self):
        return AudioStatus(self.running,self.running,self.running,'simulation')

    async def observations(self):
        index=0
        while self.running:
            yield replace(self.frames[index%len(self.frames)],timestamp=time.monotonic(),source='simulation')
            index+=1
            await asyncio.sleep(1/self.poll_hz)
