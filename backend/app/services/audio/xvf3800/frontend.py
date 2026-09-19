import asyncio
import tempfile
import time
from pathlib import Path
from ..activity import SpeechActivity
from ..models import AudioObservation, AudioStatus
from .parser import parse_doa, parse_energy
from .models import BeamTelemetry
from .audio import write_stt_wav

class XVF3800AudioFrontEnd:
    def __init__(self, control, audio, config):
        self.control,self.audio,self.config=control,audio,config
        self.activity=SpeechActivity(**config['speech_activity'])
        self.running=False
        self.control_available=False
        self.last_error=None
        self.diagnostics=None
        self.telemetry_latency_ms=None
        self._lock=asyncio.Lock()

    async def start(self):
        self.running=True
        try: await asyncio.to_thread(self.control.get_version); self.control_available=True
        except Exception as exc: self.last_error=str(exc)
        try: await asyncio.to_thread(self.audio.start)
        except Exception as exc: self.last_error=str(exc)

    async def stop(self):
        self.running=False
        async with self._lock:
            try: await asyncio.to_thread(self.audio.stop)
            finally: await asyncio.to_thread(self.control.close)
        self.control_available=False
        self.activity.reset()

    async def status(self):
        return AudioStatus(self.running,self.audio.available(),self.control_available,'xvf3800',self.last_error)

    async def poll(self):
        async with self._lock:
            start=time.monotonic()
            try:
                raw_energy=await asyncio.to_thread(self.control.get_speech_energy)
                orientation=self.config['xvf3800']
                doa=(None,None,None,None)
                doa_error=None
                if self.config.get('doa_enabled',True):
                    try:
                        raw_doa=await asyncio.to_thread(self.control.get_doa)
                        doa=parse_doa(raw_doa,orientation['azimuth_offset_deg'],orientation['invert_azimuth'])
                    except Exception as exc:
                        doa_error=f'Optional DoA unavailable: {exc}'
                energy=parse_energy(raw_energy)
                self.diagnostics=BeamTelemetry(doa,energy)
                timestamp=time.monotonic()
                active=self.activity.process(energy[3],timestamp)
                if self.config.get('speech_activity_backend')=='silero':
                    active=await self._silero_activity()
                self.control_available=True
                self.last_error=doa_error if self.audio.available() else 'UAC unavailable; telemetry only'
                calibrated=self.activity.threshold is not None or self.config.get('speech_activity_backend')=='silero'
                if not calibrated: self.last_error='Calibrate audio.speech_activity.energy_threshold before speech inference'
                return AudioObservation(timestamp,active,energy[3],doa[3],None,'auto_selected',
                                        self.audio.available(),'xvf3800',calibrated,self.last_error)
            except Exception as exc:
                self.activity.reset()
                self.control_available=False
                self.last_error=f'{type(exc).__name__}: {exc}'
                self.diagnostics=None
                await asyncio.to_thread(self.control.close)
                return AudioObservation(time.monotonic(),audio_device_available=self.audio.available(),
                                        source='xvf3800',error=self.last_error)
            finally:
                self.telemetry_latency_ms=(time.monotonic()-start)*1000

    async def _silero_activity(self):
        # Explicit optional research selection, never loaded in ordinary XVF operation.
        from ...vad import SileroVoiceActivityDetector
        import numpy as np
        from scipy.signal import resample_poly
        import math
        if not hasattr(self,'_vad'):
            self._vad=SileroVoiceActivityDetector()
            self._vad_buffer=np.array([],dtype=np.float32)
        samples,rate=await asyncio.to_thread(self.audio.capture,.064)
        channel=self.config['stt_channel']
        data=samples[:,channel]
        divisor=math.gcd(rate,16000)
        if rate!=16000: data=resample_poly(data,16000//divisor,rate//divisor)
        self._vad_buffer=np.concatenate([self._vad_buffer,data])
        while len(self._vad_buffer)>=512:
            self._vad.process(self._vad_buffer[:512])
            self._vad_buffer=self._vad_buffer[512:]
        return self._vad.active

    async def transcribe(self, stt, seconds=3):
        """Explicit capture consumer; normalized SpeechToText API, no recordings retained."""
        async with self._lock:
            samples,rate=await asyncio.to_thread(self.audio.capture,seconds)
        with tempfile.TemporaryDirectory() as directory:
            path=write_stt_wav(samples,rate,Path(directory)/'audio.wav',self.config['stt_channel'])
            return await asyncio.to_thread(stt.transcribe,path)

    async def observations(self):
        while self.running:
            start=time.monotonic()
            yield await self.poll()
            # Serialized reads, no subprocess spawning or overlapping polls. Slow cycles skip sleep.
            await asyncio.sleep(max(0,1/self.config['poll_hz']-(time.monotonic()-start)))
