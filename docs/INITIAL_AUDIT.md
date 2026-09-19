# Repository audit — 2026-09-19 (before application edits)

Read all 30 source/config/documentation files, including hidden .env.example and Apache-2.0 LICENSE. There were no existing research documents, AGENTS.md, or lockfiles. README and the supplied handoff are the only study specifications. The checkout already contained a modified README and untracked backend/frontend/scripts; preserve them.

Backend: FastAPI, Pydantic state, process-global StateStore with asyncio lock, JSONL logger. Frontend: React/TypeScript/Vite, 750 ms polling, shared participant/researcher UI. Four device subsystems are entirely simulated. No real hardware/sensors. FakeAgent maps scripted activity to intents. OllamaAgent proposes five tool types and silently tries qwen3:4b before FakeAgent. Policy changes authority for Manual/Assistive/Autonomous. Scenarios inject both observations and pre-labelled activity, including controlled_wrong_qna. No temporal estimator or specialist services exist. Agent does not own activity estimation.

Discrepancies to address/document:
- Action tool names are restricted but args are arbitrary dictionaries; device adapter coerces values and lacks a deterministic argument validator.
- Recording start/stop prohibited only by the model prompt, not agent policy.
- Orchestrator uses pre-inference authority; Take Control/condition changes can race a slow inference. Pending recommendations survive override/scenario changes; Apply does not check current authority.
- Undo restores an entire old room state (not just devices) and only one individual tool, not a recommendation batch.
- README claims replay endpoint and hidden researcher console; only recent logs exist and researcher console starts visible.
- No RuleAgent, model manifest, bootstrap/check/benchmark/report, perception contracts, camera director, or durable handoffs.
- Missing pytest-asyncio dependency despite async test. Initial system Python test attempt failed: No module named pytest. Clean Python 3.12 venv baseline pending dependency installation.
- Frontend dependencies all use latest; Node absent from PATH. No baseline build yet.

Scope: preserve architecture and deterministic scenarios; establish optional isolated perception services and model bootstrap. Fix validation/authority invariants before real model verification. Real AV integration and continuous perception ingestion remain deferred.

Baseline after isolated dependency setup, before application edits: 4 passed (Python 3.12.13, pytest + pytest-asyncio). No baseline application failures.
