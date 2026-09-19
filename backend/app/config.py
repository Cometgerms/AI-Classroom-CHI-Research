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

settings = Settings()
