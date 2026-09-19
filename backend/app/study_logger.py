import json
from pathlib import Path
from .config import settings
from .models import EventRecord

class StudyLogger:
    def __init__(self):
        self.path = Path(settings.study_log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, **payload):
        record = EventRecord(event=event, payload=payload)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        return record

    def recent(self, limit: int = 100):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in lines[-limit:] if x.strip()]

logger = StudyLogger()
