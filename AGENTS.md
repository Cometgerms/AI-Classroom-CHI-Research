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
- XVF3800 is the V1 canonical audio front end. Use AudioFrontEnd/AudioObservation; keep processed UAC audio separate from read-only control telemetry. No normal-path ODAS or Silero; both are optional research adapters.
- Preserve Mac/Windows parity: shared Qwen3:8b and whisper.cpp small.en, common PortAudio/Python adapters. Platform configuration selects acceleration only. Keep machine paths/device indices in ignored config/local.yaml; match devices by name and reject ambiguity.
- Never invent microphone orientation, speech-energy thresholds, DoA confidence, camera calibration, or hardware test success. No physical projector/PTZ integration until audio refactor/calibration is verified.

- Simulation is a permanent supported product/research runtime. Developers must be able to run simulation-basic with core requirements only and no hardware or Ollama. Preserve strict real-agent simulation-ai.
- Runtime profiles and study authority are independent. Real/simulated/replay observations use the same contracts, fusion, estimator, agent and policy; no simulation branches in downstream inference.
- Ordinary scenarios schedule sensor evidence in config/scenarios/*.yaml. Semantic state assignment is debug-only. Preserve normalized trial replay, internally logged experiment injections and participant UI concealment.
- Do not begin physical projector/PTZ integration before the simulation-ai observation → state → agent → delegation → simulated-device loop passes scripts/check_simulation_ai.py reliably; hardware verification/calibration is still required separately.
