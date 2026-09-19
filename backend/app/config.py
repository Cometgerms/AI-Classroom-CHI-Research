from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    agent_backend: str = "fake"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_fallback_model: str = ""
    ollama_strict: bool = False
    ollama_timeout_seconds: float = 120.0
    study_log_path: str = "data/study_events.jsonl"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

from .runtime_config import load_config
from dotenv import dotenv_values
from pathlib import Path
import os

# Legacy .env remains supported; real environment wins, then layered local config.
_env = {**dotenv_values(Path(__file__).resolve().parents[1]/'.env'), **os.environ}
runtime_config = load_config(environ=_env)
settings = Settings(study_log_path=_env.get('STUDY_LOG_PATH') or str(Path(__file__).resolve().parents[1]/'data/study_events.jsonl'),
                    agent_backend=runtime_config['agent']['backend'],
                    ollama_model=runtime_config['agent']['model'],
                    ollama_base_url=runtime_config['agent']['base_url'],
                    ollama_strict=runtime_config['agent']['strict'] or str(_env.get('OLLAMA_STRICT','false')).lower()=='true')
