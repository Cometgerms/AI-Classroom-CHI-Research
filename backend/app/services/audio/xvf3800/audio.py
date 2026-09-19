"""PortAudio UAC capture; no CoreAudio/WASAPI objects escape this adapter."""
from dataclasses import dataclass
from pathlib import Path
import math
import wave
import queue
import time

@dataclass(frozen=True)
class AudioProfile:
    device_index: int # runtime enumeration only; never persisted to shared config/report
    sample_rate: int
    channels: int

def discover(config, sd=None):
    if sd is None: import sounddevice as sd
    devices=sd.query_devices()
    matches=[]
    for index, device in enumerate(devices):
        if device['max_input_channels']<1: continue
        if config.get('device_index') is not None:
            if index!=config['device_index']: continue
        elif config['device_match'].casefold() not in device['name'].casefold(): continue
        if config.get('host_api'):
            if sd.query_hostapis(device['hostapi'])['name'].casefold()!=config['host_api'].casefold(): continue
        matches.append((index,device))
    if len(matches)!=1:
        raise RuntimeError(f'Expected one UAC match, found {len(matches)}. Set audio.device_match/host_api (or device_index only in local.yaml).')
    index,device=matches[0]
    rate=config.get('sample_rate') or int(device['default_samplerate'])
    channels=config.get('channels') or min(2,device['max_input_channels'])
    if type(rate) is not int or rate<=0 or type(channels) is not int or not 1<=channels<=device['max_input_channels']:
        raise ValueError('Invalid UAC stream profile')
    sd.check_input_settings(device=index,samplerate=rate,channels=channels,dtype='float32')
    return AudioProfile(index,rate,channels)

class PortAudioCapture:
    def __init__(self, config):
        self.config=config
        self.stream=None
        self.profile=None
        self.queue=queue.Queue(maxsize=50)
        self.overflow=False

    def start(self):
        import sounddevice as sd
        self.profile=discover(self.config,sd)
        def callback(data, frames, timing, status):
            if status: self.overflow=True
            try: self.queue.put_nowait(data.copy())
            except queue.Full:
                try: self.queue.get_nowait()
                except queue.Empty: pass
                try: self.queue.put_nowait(data.copy())
                except queue.Full: pass
        self.stream=sd.InputStream(device=self.profile.device_index,samplerate=self.profile.sample_rate,
                                   channels=self.profile.channels,dtype='float32',blocksize=0,callback=callback)
        try: self.stream.start()
        except Exception:
            self.stream.close(); self.stream=None
            raise

    def stop(self):
        if self.stream is not None:
            try: self.stream.stop()
            finally: self.stream.close(); self.stream=None

    def capture(self, seconds):
        if self.stream is None: raise RuntimeError('UAC stream not started')
        if not 0<seconds<=30: raise ValueError('Capture duration must be 0–30 seconds')
        import numpy as np
        while not self.queue.empty():
            try: self.queue.get_nowait()
            except queue.Empty: break
        self.overflow=False
        count=round(seconds*self.profile.sample_rate)
        chunks=[]; total=0; deadline=time.monotonic()+seconds+2
        while total<count:
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError('UAC capture stalled or device disconnected')
            chunk=self.queue.get(timeout=remaining)
            chunks.append(chunk);total+=len(chunk)
        if self.overflow: raise RuntimeError('UAC input overflow; audio discarded')
        return np.concatenate(chunks)[:count],self.profile.sample_rate

    def available(self):
        return self.stream is not None and bool(self.stream.active)

def write_stt_wav(samples, sample_rate, destination, channel=0):
    """Select processed channel and anti-alias/resample actual UAC rate to Whisper's PCM16 mono."""
    import numpy as np
    from scipy.signal import resample_poly
    data=np.asarray(samples,dtype=np.float32)
    if data.ndim!=2 or type(channel) is not int or not 0<=channel<data.shape[1]:
        raise ValueError('Invalid processed audio channel')
    if sample_rate<=0 or not np.isfinite(data).all(): raise ValueError('Invalid audio data')
    mono=data[:,channel]
    if sample_rate!=16000:
        divisor=math.gcd(int(sample_rate),16000)
        mono=resample_poly(mono,16000//divisor,int(sample_rate)//divisor)
    pcm=(np.clip(mono,-1,1)*32767).astype('<i2')
    with wave.open(str(destination),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(pcm.tobytes())
    return Path(destination)
