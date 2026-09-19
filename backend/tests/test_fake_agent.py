import pytest
from app.agent.fake import FakeAgent
from app.models import RoomState, ActivityState

@pytest.mark.asyncio
async def test_qna_agent_actions():
    s=RoomState()
    s.activity.state=ActivityState.Q_AND_A
    s.observations.active_speaker="student_3"
    d=await FakeAgent().decide(s)
    assert any(a.tool=="camera_focus" and a.args["target"]=="student_3" for a in d.actions)
    assert any(a.tool=="student_voice_lift" for a in d.actions)
