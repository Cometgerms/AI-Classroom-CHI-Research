"""Optional whisper.cpp CLI adapter. Input: local mono 16 kHz PCM WAV."""
from pathlib import Path
from typing import Protocol
import subprocess
import tempfile
import wave

class SpeechToText(Protocol):
    def transcribe(self, audio_path: Path) -> str: ...

class WhisperCppSpeechToText:
    def __init__(self, executable: Path, model: Path):
        self.executable, self.model = Path(executable).resolve(), Path(model).resolve()

    def transcribe(self, audio_path: Path) -> str:
        audio_path = Path(audio_path).resolve()
        with wave.open(str(audio_path), 'rb') as wav:
            if (wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) != (1, 16000, 2):
                raise ValueError('Expected mono 16 kHz 16-bit PCM WAV')
        if not self.executable.is_file() or not self.model.is_file():
            raise FileNotFoundError('Install whisper.cpp and small.en first')
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'transcript'
            subprocess.run([str(self.executable), '-m', str(self.model), '-f', str(audio_path),
                '-l', 'en', '-otxt', '-of', str(output), '-np'], check=True,
                capture_output=True, timeout=180)
            return output.with_suffix('.txt').read_text().strip()
