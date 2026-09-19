# Coding-agent instructions

- CURRENT PRIORITY: product-first instructor interaction. `/` is Agentic Classroom; `/research` preserves existing research tools; `/dev` contains advanced diagnostics. Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.
- Do not improve counterbalancing, questionnaires, session workflow or experiment scripting in this milestone. Keep research routes, logs, replay, models and injection code intact unless compatibility requires a change.
- Product labels are AI Mode Off / Assist / Auto, independent of hardware profile. Use a clean instructor view model; no participant IDs, scenario names, trial metadata, confidence values or internal backend names in normal UI.
- Primary local development uses simulation-ai with real Qwen; simulation-basic remains the hardware/model-free CI/onboarding option. Keep manual controls and Take Control independent of AI availability. Never imply real recording/video/hardware success from simulated state.
- VideoEngine is the only recording/program boundary (SimVideoEngine / OBSVideoEngine). Physical protocols remain deferred; selected but unavailable engines report disconnected. Keep room display independent of recording/program.

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
- Never invent microphone orientation, speech-energy thresholds, DoA confidence, camera calibration, or hardware test success. Physical AV success must be verified; DoA/camera-azimuth calibration must not block instructor-only V1 study development.

- Simulation is a permanent supported product/research runtime. Developers must be able to run simulation-basic with core requirements only and no hardware or Ollama. Preserve strict real-agent simulation-ai.
- Runtime profiles and study authority are independent. Real/simulated/replay observations use the same contracts, fusion, estimator, agent and policy; no simulation branches in downstream inference.
- Ordinary scenarios schedule sensor evidence in config/scenarios/*.yaml. Semantic state assignment is debug-only. Preserve normalized trial replay, internally logged experiment injections and participant UI concealment.
- Do not begin physical projector/PTZ integration before the simulation-ai observation → state → agent → delegation → simulated-device loop passes scripts/check_simulation_ai.py reliably; hardware verification/calibration is still required separately.

- PROTECTED CHI V1 RESEARCH CONSTRAINT: one instructor/TA/experienced-presenter participant and one facilitator per session; no students or student actors. See docs/STUDY_V1.md and config/study/chi_v1.yaml.
- V1 primary activities: PRE_CLASS, LECTURE/PRESENTATION, DEMONSTRATION, MEDIA_PLAYBACK, TRANSITION, POST_CLASS, UNKNOWN. Keep multi-person states reusable but outside required V1 scope.
- Prioritize presenter tracking/zone, speech, local STT, source/media state and demo context. XVF processed audio/AEC/speech/STT remain canonical; DoA/fusion/calibration are optional context, never V1 study prerequisites. One PTZ with presenter/demo_zone/wide intents is sufficient.
- Preserve the same teaching tasks across counterbalanced authority conditions. Use instructor-workflow failures and hide injection labels from participant UI. Record per-capability delegation preferences separately.
