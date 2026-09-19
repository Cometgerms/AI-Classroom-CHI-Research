"""VAD has no dependency on transcription or room-agent inference."""
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

@dataclass(frozen=True)
class SpeechEvent:
    kind: Literal['speech_started', 'speech_active', 'speech_ended']
    probability: float

class VoiceActivityDetector(Protocol):
    def process(self, audio_frame: Sequence[float]) -> list[SpeechEvent]: ...

class SileroVoiceActivityDetector:
    """512 normalized mono samples per frame at 16 kHz; 320 ms end hysteresis."""
    def __init__(self, threshold=0.5, end_frames=10):
        from silero_vad import load_silero_vad
        self.model = load_silero_vad()
        self.threshold, self.end_frames = threshold, end_frames
        self.active, self.silent = False, 0

    def process(self, audio_frame):
        import torch
        frame = torch.as_tensor(audio_frame, dtype=torch.float32)
        if frame.ndim != 1 or frame.numel() != 512:
            raise ValueError('VAD expects 512 mono samples at 16 kHz')
        if not torch.isfinite(frame).all() or frame.abs().max() > 1:
            raise ValueError('VAD samples must be finite and normalized to [-1, 1]')
        with torch.inference_mode():
            probability = float(self.model(frame, 16000).item())
        if probability >= self.threshold:
            kind = 'speech_active' if self.active else 'speech_started'
            self.active, self.silent = True, 0
            return [SpeechEvent(kind, probability)]
        self.silent += 1
        if self.active and self.silent >= self.end_frames:
            self.active = False
            return [SpeechEvent('speech_ended', probability)]
        return []
