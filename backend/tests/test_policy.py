from app.delegation import policy
from app.models import Action, Condition

def test_manual_denies_agent_execution():
    d = policy.evaluate(Condition.MANUAL, Action(tool="camera_focus", args={"target":"student"}))
    assert d.result == "deny"

def test_assistive_recommends():
    d = policy.evaluate(Condition.ASSISTIVE, Action(tool="camera_focus", args={"target":"student"}))
    assert d.result == "recommend"

def test_autonomous_allows():
    d = policy.evaluate(Condition.AUTONOMOUS, Action(tool="camera_focus", args={"target":"student"}))
    assert d.result == "allow"
