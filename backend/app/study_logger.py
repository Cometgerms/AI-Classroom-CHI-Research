import json
from pathlib import Path
from .config import settings
from .models import EventRecord

class StudyLogger:
    def __init__(self):
        self.interaction_anchor=None
        self.path = Path(settings.study_log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, **payload):
        from .state_store import store
        progress=store.state.study
        context={'participant_id':store.state.participant_id,'condition':store.state.condition.value}
        if progress:
            context.update(study_run_id=progress.run_id,protocol=progress.protocol,task_id=progress.task_id,
                           assigned_condition=progress.assigned_condition.value,condition_position=progress.condition_position)
        from datetime import datetime, timezone
        scope=(store.state.participant_id,progress.run_id if progress else None)
        timestamp=datetime.now(timezone.utc)
        if event=='recommendation_created' or (event=='device_action_executed' and store.state.condition.value=='autonomous'):
            self.interaction_anchor=(scope,timestamp)
        if event in ('participant_manual_action','participant_override','authority_restriction','recommendation_applied','recommendation_dismissed'):
            if self.interaction_anchor and self.interaction_anchor[0]==scope:
                context['response_latency_ms']=max(0,(timestamp-self.interaction_anchor[1]).total_seconds()*1000)
                self.interaction_anchor=None
        record = EventRecord(event=event, payload={**context,**payload})
        with self.path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        return record

    def recent(self, limit: int = 100):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(x) for x in lines[-limit:] if x.strip()]

logger = StudyLogger()
