# Coding-agent instructions

Read this file, docs/CURRENT_STATE.md, docs/ARCHITECTURE.md, docs/DECISIONS.md, docs/MODELS.md, and the newest docs/HANDOFFS entry before substantive work.

- Do not silently change architecture. Document uncertain assumptions and decisions.
- Preserve Level 0 Manual / Level 1 Assistive / Level 2 Autonomous. Same state, tools, adapters and UI; only authority changes.
- Keep simulated and real hardware behind the same interfaces.
- Never give an LLM unrestricted shell, HTTP, serial, PJLink, ONVIF or DSP access. Hardware actions must use typed intent tools and deterministic validators. No model-generated PTZ coordinates.
- Keep specialist observations → temporal estimator → structured room state → semantic agent → delegation → safety validation → adapters → verification.
- Preserve FakeAgent; optional models must not block simulator startup.
- Never commit model weights, downloaded binaries, caches, private recordings, study logs or personal machine identifiers.
- Record dependency/model versions and run tests before ending work.
- Each substantive session creates a new immutable docs/HANDOFFS/YYYY-MM-DD_HHMM_topic.md. Never erase another agent's handoff. Update CURRENT_STATE after writing it.
