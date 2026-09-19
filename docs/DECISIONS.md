# Append-only architectural decisions

## 2026-09-19 — Preserve baseline and study conditions

Decision: keep existing FastAPI/React architecture, FakeAgent and scripted labels; expose RuleAgent as a separate selectable deterministic implementation sharing existing rules.
Why: reproducible experiments and UI work must not depend on inference or naturally occurring mistakes.
Alternatives considered: replacing FakeAgent, letting the LLM relabel every scenario.
Consequences: specialist services/estimator are independently testable but are not yet the source of live room state. Controlled failure remains explicit.

## 2026-09-19 — Validate all intents and invalidate stale inference

Decision: validate closed argument shapes in Action and again before simulated execution; deny AI recording transport; serialize device commits with authority changes; discard inference after state/revision changes. Undo restores only device fields.
Why: existing arbitrary args and pre-inference authority broke the intended safety boundary; whole-state undo could rewind observations.
Alternatives considered: prompt-only restrictions, holding a lock during inference, redesigning the entire state machine.
Consequences: unsupported intents are rejected; Take Control stays responsive during inference. Individual-action undo semantics are preserved; batch undo remains deferred. Physical async device execution will require cancellable transactions and independent acknowledgement before integration.

## 2026-09-19 — Isolate optional model stack

Decision: use Python 3.12 backend and separate perception venv; stdlib bootstrap reads JSON-form YAML 1.2 manifest. Preserve exact requested Qwen tags and remove the default alternate Qwen3 4B fallback. Fake fallback remains explicit in decision rationale; strict mode supports research checks.
Why: simulator startup cannot depend on heavy optional packages; repeated installs should be predictable and auditable.
Alternatives considered: all ML libraries in backend requirements, automatic substitution of models.
Consequences: perception checks must run with perception Python. Model digests and installed package snapshots are recorded; Windows resolves its own CUDA dependencies. Mutable Ollama tags require digest comparison on other machines.

## 2026-09-19 — ODAS and camera scope

Decision: skip native ODAS installation on this Mac after inspecting mandatory ALSA/PulseAudio requirements; document Linux/WSL2 route and provide simulated/stub tracker. Add an isolated digital crop director; retain symbolic camera simulation.
Why: platform porting and microphone geometry must not block the control study.
Alternatives considered: native ODAS port and physical PTZ integration now.
Consequences: no real source localization or physical AV control is claimed; digital cropping requires calibrated tracking input before wiring into UI.
