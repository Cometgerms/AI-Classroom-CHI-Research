from uuid import uuid4
from datetime import datetime, timezone
from .agent.factory import get_agent
from .delegation import policy
from .devices import executor, DeviceUnavailable
from .models import Condition, Recommendation, RoomState
from .state_store import store
from .study_logger import logger

class Orchestrator:
    async def evaluate(self, decision_transform=None):
        async with store.control_lock:
            state = await store.snapshot()
            store.revision += 1  # Supersede any older inference on the same state.
            revision = store.revision
            store.pending = None
        if not state.ai_enabled or state.condition == Condition.MANUAL:
            logger.log("agent_skipped", reason="manual_or_disabled", condition=state.condition.value)
            return {"decision": None, "recommendation": None, "executed": []}

        decision = await get_agent().decide(state)
        if decision_transform is not None:
            decision = decision_transform(decision)
        async with store.control_lock:
            if store.revision != revision:
                logger.log("agent_decision_discarded", reason="state_changed_during_inference")
                return {"decision": None, "recommendation": None, "executed": []}
            logger.log("agent_decision", condition=state.condition.value, decision=decision.model_dump())

            executed=[]
            failures=[]
            recommend=[]
            for action in decision.actions:
                p = policy.evaluate(state.condition, action)
                logger.log("policy_decision", action=action.model_dump(), result=p.result, reason=p.reason)
                if p.result == "allow":
                    try:
                        await executor.execute(action)
                        executed.append(action)
                    except DeviceUnavailable as exc:
                        failures.append({"tool":action.tool,"error":str(exc)})
                elif p.result == "recommend":
                    recommend.append(action)

            recommendation=None
            if recommend:
                rd = decision.model_copy(deep=True)
                rd.actions = recommend
                recommendation = Recommendation(
                    id=str(uuid4()),
                    created_at=datetime.now(timezone.utc).isoformat(),
                    decision=rd,
                )
                store.pending = recommendation
                logger.log("recommendation_created", recommendation=recommendation.model_dump())
                await store.broadcast()

            return {
                "decision": decision,
                "recommendation": recommendation,
                "executed": executed,
                "failures": failures,
            }

orchestrator = Orchestrator()
