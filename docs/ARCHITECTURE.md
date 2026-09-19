# Architecture

The study compares Level 0 Manual (no AI recommendations/execution), Level 1 Assistive (explicit participant approval), and Level 2 Autonomous (permitted AI execution with Undo and Take Control). All conditions share state, devices, intent schemas, and UI.

Required pipeline:

Observations → specialist perception → structured observations → temporal estimator → room state → local semantic agent → delegation policy → deterministic intent validation → device adapters → AV system → verification → updated room state.

## Implemented runtime

- `backend/app/main.py`: FastAPI REST endpoints and state WebSocket. One process, one session; bind to localhost. Frontend React/Vite polls at 750 ms. Researcher console is toggleable and initially visible, not access-controlled.
- `models.py`: session/activity/observation/device/health state and validated intent actions. `state_store.py`: process-global locked state, revision, pending recommendation, 50-action history. Inference happens outside the control lock; results are discarded if another evaluation or state/authority change supersedes them. Short simulated commits are serialized with condition changes and approvals.
- `scenarios.py`: deterministic labels AND observations, including an explicit wrong-Q&A manipulation. This path deliberately bypasses the optional temporal estimator to preserve controlled study scenarios.
- `agent/`: RoomAgent → FakeAgent, RuleAgent, OllamaAgent. RuleAgent reuses the audited deterministic activity rules. Ollama uses Qwen3 tool calling; args pass the same Action validator. `services/agent` re-exports the existing interface rather than moving it. Model failures fall back to FakeAgent unless strict mode; reason is present in decision logs. No automatic different-model fallback by default.
- `delegation.py`: authority decision; AI cannot start/stop recording. `safety.py`: closed arguments/enums, strict boolean, simulation target IDs, no raw commands. `devices.py`: validated deterministic state updates and simulated readback logged as verification. Only participant endpoints may request recording transport.
- Assistive recommendations are cleared on changed scenario, condition, participant, manual action, evaluation, or override. Apply requires Assistive authority. Undo restores only device state for the last individual action; it does not undo a whole AI batch. Take Control selects global Manual authority.
- `study_logger.py`: JSONL events; recent-event endpoint. No replay implementation. Logs and all model weights are ignored by git.

## Optional services (isolated, not wired into the UI event loop)

- STT: `SpeechToText.transcribe(Path)` → text; whisper.cpp subprocess with explicit CLI/model paths, WAV validation, timeout, no shell. It is not a model-visible tool.
- VAD: `VoiceActivityDetector.process(frame)` → speech_started/active/ended; Silero, 512 mono float samples at 16 kHz, silence-end hysteresis. Silence yields no agent request; no automatic STT/agent scheduler yet.
- Vision: `PersonDetector`, `PersonTracker`, `PoseEstimator`; lazy Ultralytics imports. Structured IDs/boxes/confidence; room zone remains unknown until calibration. Pose only exports a raised-hand cue. SemanticVision accepts one image only when the caller marks evidence ambiguous; no continuous VLM.
- Estimator: timestamp-driven sustained media/Q&A candidate rules. This contract is tested; real ingestion, speaker association and calibration remain next milestone.
- Sound localization: simulated tracker plus explicit ODAS stub. No microphone accessed.
- Camera: M1 camera remains a symbolic simulated target. Optional DigitalCameraDirector maps trusted normalized tracked boxes to smoothed crops; missing track returns wide. It is not wired into devices. Physical PTZ is deferred; no LLM-coordinate path exists.

## Limits

Single-process in-memory state is unsuitable for concurrent study sessions or multiple uvicorn workers. Hardware verification currently means simulator readback, not an independent device acknowledgement. Camera IDs are the six simulated students, instructor, and named zones. Approval binds to the current pending recommendation; the API does not yet accept a recommendation ID from the UI. UI error handling, research-console hiding, durable replay, batch undo, and actual sensor orchestration remain documented follow-ups.
