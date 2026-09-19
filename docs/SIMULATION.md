# Supported simulation and replay

Simulation is a supported product and research runtime. Every developer can contribute without owning AV hardware. It remains supported when real adapters are added.

| Profile | Sensors / AV | Agent | Purpose |
| --- | --- | --- | --- |
| simulation-basic | All simulated | Fake (or Rule) | CI, onboarding, UI, deterministic scenarios |
| simulation-ai | All simulated | Strict local Qwen via Ollama | Full observation → state → agent → delegation → device loop |
| hybrid | Each adapter independently selected | Configured Fake/Rule/Ollama | Incremental real sensing and AV integration |
| hardware | XVF audio, real camera, physical AV selected | Configured agent | Honest capability checks; unsupported outputs fail |
| study | Controlled simulated observations and AV | Fake default, configurable Ollama | Reproducible experiment with participant view |

Manual, Assistive and Autonomous are independent study authority conditions, available with every profile. Manual skips AI; Assistive recommends; Autonomous executes permitted typed intents. AI may not start/stop recording. Participant control remains available. Simulation-ai never silently falls back to Fake. Missing Ollama leaves the UI/backend available in Manual; requesting AI reports an error.

Launch from repository root with `python -m backend --profile PROFILE` using the project's virtual environment. Simulation-basic needs only backend/requirements.txt. No microphone, camera, XVF, Torch, Ultralytics, Whisper or Ollama is required. Optional packages remain optional. Clear legacy AGENT_BACKEND overrides from backend/.env when using a profile that selects a different agent; incompatible overrides fail explicitly.

## Observation and scenario path

`AudioObservation`, `PersonTrack`, `VisionObservation`, and `ObservationFrame` are shared real/simulated/replay contracts. Frames validate clocks and geometry. `SceneObservation` carries normalized transcript, floor-taking, presentation, playback and object evidence. `ActiveSpeakerFusion` geometrically associates DoA and tracks; `StateEstimator` sustains evidence before changing activity. Neither branches on simulation. Physical calibration defaults remain uncalibrated; scenario YAML provides a separate explicit virtual-room calibration.

Versioned `config/scenarios/*.yaml` specifies a zero-based timeline, sample interval, duration, initial sensor evidence and scheduled partial updates. The loader carries evidence forward and emits normalized frames. No ordinary scenario specifies an activity label. Student question produces LECTURE → TRANSITION → Q&A from instructor silence/yield, speech, 54° DoA, student_3 at x=.8, and transcript/presentation evidence.

Catalog: lecture_start, instructor_moves, demonstration, student_question, discussion, media_playback, side_conversation, student_presentation, ambiguous_activity, sensor_dropout, device_failure, controlled_wrong_qna, controlled_wrong_camera, controlled_wrong_display, controlled_wrong_audio. The UI discovers the catalog from the backend.

`POST /api/scenario/student_question` plays virtual time deterministically. Add `?realtime=true` to honor scheduled delays. A scenario is one experimental trial: each frame passes through fusion/estimation, then the agent evaluates the final state once. This avoids repeated model calls or transitional recommendations within a trial. Use successive scenarios or normalized observation calls for multiple decision points. Concurrent scenario/replay runs serialize. Manual controls/Take Control can run during playback/inference; current authority and stale-inference guards apply.

`POST /api/observations` submits a validated normalized frame through the same pipeline and agent for external drivers. Do not move time backwards within a stream. `POST /api/scene` supplies scene evidence to live acquisition. Hybrid's live audio clock joins camera observations to the same pipeline, with asynchronous inference so model latency does not stop sensing. Scene semantics/STT still need an upstream producer; the runtime does not invent teacher roles, yielding or playback from hardware alone.

`POST /api/simulation/sensors` accepts an ObservationFrame and updates only selected simulated audio/camera adapters plus scene evidence, useful with hybrid. Real adapters are not overwritten. Simulated camera tracks are refreshed on the live audio clock. Hybrid physical fusion still requires measured camera/audio calibration.

## Controlled errors and participant presentation

Scenario metadata can specify `injection: {kind: wrong_qna}` or a validated action injection (`kind: action`, `tool`, `args`). Injection transforms the agent decision before the unchanged delegation policy. Manual still skips AI, Assistive still requires Apply. Wrong-Q&A retains the correctly estimated side conversation internally, while the injected decision acts as Q&A. `device_failure` marks a simulated adapter unavailable and never updates that device as if successful.

`experiment_injection` JSONL events record intentional errors. Recommendations use ordinary participant-facing reasons; normalized evidence and last_scenario carry no injection markers. Study's default UI hides agent/runtime diagnostics, evidence, scenario names and researcher controls. Open `http://localhost:5173/?researcher=1` for the local researcher console. This is presentation separation, not authentication; API/log access and query parameters are researcher-trusted on localhost. Do not expose this single-user prototype publicly.

Direct semantic injection remains explicitly debug-only at `/api/debug/scenario/{name}` and is disabled in study. Normal scenario playback never calls that code.

## Replay and logging

`GET /api/replay` exports the latest trial as versioned JSON: initial simulated device state, condition metadata, calibration, normalized frames and injection metadata. `POST /api/replay` replays it through the identical fusion/estimator/agent/delegation/device path. Replay restores the recorded simulated device baseline and clears old undo history, but preserves the current participant and authority condition so one tape can compare conditions/agents. It runs only in simulation/study profiles. Validate the whole tape before mutation; unordered clocks are rejected.

Example (Mac shell):

```bash
curl -X POST http://localhost:8000/api/scenario/student_question
curl http://localhost:8000/api/replay -o backend/data/question.json
curl -H 'Content-Type: application/json' --data-binary @backend/data/question.json http://localhost:8000/api/replay
```

To recover a persisted trial after a restart: `python scripts/replay_trial.py backend/data/study_events.jsonl --from-log --output backend/data/recovered.json`. Replay it with `python scripts/replay_trial.py backend/data/recovered.json` (or add `--realtime`).

JSONL contains `runtime_run_started` with the complete tape, per-frame `normalized_observation`, agent/policy/device events, participant actions, approvals/overrides, and `runtime_run_completed`. Keep logs/recordings private and untracked. Tapes reproduce sensor trials; arbitrary interleaved participant actions across an entire session are logged but not automatically re-executed. Qwen replay re-infers and may differ; deterministic Fake is appropriate for exact decision regression. Latest tape is in memory; JSONL persists all trial inputs across restarts.

## Hybrid selection and honest hardware status

Put machine-specific choices in ignored `config/local.yaml`, then select hybrid:

```yaml
hardware:
  audio: xvf3800
  camera: simulation
  projector: simulation
  recorder: simulation
  camera_control: simulation
  audio_output: simulation
```

Or choose `audio: simulation`, `camera: real`, `projector: pjlink`, `recorder: obs`. Real camera needs explicit `camera.device` and calibrated role mapping in `camera.roles`, plus optional perception packages. Selected PJLink/PTZ/OBS/real audio output adapters currently return unavailable errors, not fabricated success or silent simulation. No physical projector/PTZ implementation was started.

Doctor reports Simulation basic / Simulation AI / XVF hybrid / Full hardware independently. Hardware absence never reduces simulation readiness. Full hardware remains NOT READY until all real output adapters and hardware verification exist. Doctor checks prerequisites; `python scripts/check_simulation_ai.py` is the strict real-Qwen end-to-end smoke test (requires installed Ollama/model).
