"""Deterministic baseline using estimator state; shares the audited scenario rules."""
from .fake import FakeAgent

class RuleAgent(FakeAgent):
    async def decide(self, state):
        decision = await super().decide(state)
        decision.rationale = f"RuleAgent policy for {state.activity.state.value}"
        return decision
