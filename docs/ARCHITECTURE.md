# Product-first instructor application

**Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.** The researcher console is preserved but product UI/functionality is now the primary implementation priority. The instructor-only CHI V1 constraint below remains protected.

`/` serves InstructorApp; `/devices`, `/settings` and `/dev` use the same normalized product view model. The existing ResearchApp and its stylesheet are lazy-loaded only at `/research`. Query parameters on the main route do not enable research tools. Backend study routes, models, replay, logging and injections remain unchanged except necessary shared-device compatibility.

`product.py` projects RoomState into InstructorAppState without internal/research metadata. AI modes Off/Assist/Auto map to existing authority, independently of hardware profiles. Async model availability/evaluation keeps manual operations and Take Control responsive. Product approvals bind to ID and expire after 45 seconds. `product_events.py` provides a bounded device-only history and precondition-checked latest-action undo; recording transport is never implicitly undone.

`DeviceRouter` delegates recording/program semantics through VideoEngine. SimVideoEngine provides honest simulated state/illustrated preview; OBSVideoEngine is a disconnected boundary awaiting transport/readback. No OBS calls in frontend or orchestration. Room display remains separate. Shared typed intents now include camera follow, display blank and audio mute. Product defaults persist in ignored config/local.product.json; advanced hardware setup remains explicit future adapter work.

See [product behavior and startup](PRODUCT.md) for API and limitations. Physical protocols and research workflow are not this milestone's implementation target.

---

# Supported simulation runtime (2026-09-19)

**CHI V1 is an instructor/TA-only controlled teaching-task study. Student presence is outside the V1 experimental scope.** One participant and one facilitator; no student actors. See [protected V1 protocol and teaching-task script](STUDY_V1.md).

Simulation is a permanent product/research runtime; no hardware ownership is needed to contribute. [Runtime reference](SIMULATION.md) defines profiles, APIs, scenario schema, replay and known limits.

```text
YAML timeline / normalized replay / real audio + real or simulated camera
  → ObservationFrame(AudioObservation, VisionObservation(PersonTrack), SceneObservation)
  → optional ActiveSpeakerFusion / known-presenter evidence → sustained StateEstimator → RoomState
  → Fake / Rule / strict Ollama RoomAgent → optional logged experiment injection
  → delegation + typed safety validation → independently selected device adapters
  → simulated readback or honest unavailable failure → study logger
```

No simulation branches exist in fusion, estimation or agent reasoning. Simulated calibration is explicitly supplied by the scenario, never substituted for measured physical calibration. Direct state-label injection is debug-only and disabled in study. Scenarios evaluate the agent once after the sensor timeline; live acquisition and submitted frames can trigger repeated decisions. Runtime and Manual/Assistive/Autonomous authority are independent.

DeviceRouter selects camera_control, projector, audio_output and recorder independently. Physical output adapters are explicit unavailable placeholders until implementation/verification; they do not mutate device state. Real camera and XVF share normalized types with their simulation adapters. Hybrid's asynchronous inference cannot block observation collection.

Study UI hides technical diagnostics and injection metadata by default. Researcher view is a local presentation switch, not an authentication boundary. Replay is normalized trial replay with device baseline and current authority; complete participant session action re-enactment remains future work.

## Protected V1 scope and shared evidence

V1 uses one presenter participant and one facilitator, no students/actors, and one PTZ with presenter/demo_zone/wide semantic intents. Required activities are PRE_CLASS, LECTURE/PRESENTATION, DEMONSTRATION, MEDIA_PLAYBACK, TRANSITION, POST_CLASS and UNKNOWN. Q&A, Discussion, Student Presentation and Side Conversation remain supported extensions, not V1 study requirements.

SceneObservation now includes session_phase, transitioning and presentation_source. The existing pipeline accepts an explicitly assigned single presenter track plus speech/scene evidence without DoA or calibrated camera-azimuth geometry. Optional geometric fusion still supports multi-person research; neither the agent nor estimator has a separate simulation/instructor-only implementation. XVF's optional DoA read is isolated from energy/speech availability. Processed audio, AEC and Whisper/STT remain the V1 priorities.

`study.py` handles protocol/task bookkeeping only; `runtime.py` still produces and consumes normalized trials. `config/study/chi_v1.yaml` defines 14 common teaching prompts. Six permutations counterbalance condition order. Store assigned condition separately from effective authority, so Take Control does not relabel the assigned experimental condition. Per-capability restrictions deny AI actions, preserving manual controls.

`study_logger.py` attaches participant/run/task/current-and-assigned-condition context. Task outcomes, response latencies and explicit post-condition ratings/preferences supplement existing action/recommendation/override events. Participant-safe task prompts contain no scenario names or injection metadata. Full protocol and metric definitions: [STUDY_V1.md](STUDY_V1.md).

## Implementation detail

The study compares Level 0 Manual (no AI recommendations/execution), Level 1 Assistive (explicit participant approval), and Level 2 Autonomous (permitted AI execution with Undo and Take Control). All conditions share state, devices, intent schemas, and UI.

Required pipeline:

Observations → specialist perception → structured observations → temporal estimator → room state → local semantic agent → delegation policy → deterministic intent validation → device adapters → AV system → verification → updated room state.

## Implemented runtime

- `backend/app/main.py`: FastAPI REST endpoints and state WebSocket. One process, one session; bind to localhost. Frontend React/Vite polls at 750 ms. Researcher console is toggleable outside participant study view; local presentation is not access-controlled.
- `models.py`: session/activity/observation/device/health state and validated intent actions. `state_store.py`: process-global locked state, revision, pending recommendation, 50-action history. Inference happens outside the control lock; results are discarded if another evaluation or state/authority change supersedes them. Short simulated commits are serialized with condition changes and approvals.
- `simulation.py` loads normalized YAML timelines; `runtime.py` handles trials/replay and logged decision injections. Legacy `scenarios.py` is debug-only.
- `agent/`: RoomAgent → FakeAgent, RuleAgent, OllamaAgent. RuleAgent reuses the audited deterministic activity rules. Ollama uses Qwen3 tool calling; args pass the same Action validator. `services/agent` re-exports the existing interface rather than moving it. Model failures fall back to FakeAgent unless strict mode; reason is present in decision logs. No automatic different-model fallback by default.
- `delegation.py`: authority decision; AI cannot start/stop recording. `safety.py`: closed arguments/enums, strict boolean, simulation target IDs, no raw commands. `devices.py`: validated deterministic state updates and simulated readback logged as verification. Only participant endpoints may request recording transport.
- Assistive recommendations are cleared on changed scenario, condition, participant, manual action, evaluation, or override. Apply requires Assistive authority. Undo restores only device state for the last individual action; it does not undo a whole AI batch. Take Control selects global Manual authority.
- `study_logger.py`: JSONL events; recent-event endpoint. Normalized trial recording/replay is implemented. Logs and all model weights are ignored by git.

## Host perception and research services (outside controlled scenario injection)

- STT: `SpeechToText.transcribe(Path)` → text; whisper.cpp subprocess with explicit CLI/model paths, WAV validation, timeout, no shell. It is not a model-visible tool.
- Optional research VAD: `VoiceActivityDetector.process(frame)` → speech_started/active/ended; Silero, 512 mono float samples at 16 kHz, silence-end hysteresis. Silence yields no agent request; no automatic STT/agent scheduler yet.
- Vision: `PersonDetector`, `PersonTracker`, `PoseEstimator`; lazy Ultralytics imports. Structured IDs/boxes/confidence; room zone remains unknown until calibration. Pose only exports a raised-hand cue. SemanticVision accepts one image only when the caller marks evidence ambiguous; no continuous VLM.
- Estimator: timestamp-driven sustained media/Q&A candidate rules. This contract is tested; the shared room estimator uses geometric speaker fusion and normalized live/scenario input. Physical calibration remains required.
- Optional research localization: simulated SoundSourceTracker plus explicit ODAS stub. Normal V1 uses AudioFrontEnd/XVF DoA instead.
- Camera: M1 camera remains a symbolic simulated target. Optional DigitalCameraDirector maps trusted normalized tracked boxes to smoothed crops; missing track returns wide. It is not wired into devices. Physical PTZ is deferred; no LLM-coordinate path exists.

## Limits

Single-process in-memory state is unsuitable for concurrent study sessions or multiple uvicorn workers. Hardware verification currently means simulator readback, not an independent device acknowledgement. Camera IDs are the six simulated students, instructor, and named zones. Approval binds to the current pending recommendation; the API does not yet accept a recommendation ID from the UI. Full-session participant action re-enactment, batch undo, approval-ID binding and physical verification remain follow-ups.

## Canonical V1 audio revision — 2026-09-19

**XVF3800 is the V1 canonical audio front end.** It supplies device-side AEC/beamforming/noise suppression/AGC/limiting, azimuth and speech energy. ODAS and Silero remain optional research alternatives, not normal-path requirements. Generic abstractions remain intact.

```text
XVF3800 or SimAudioFrontEnd
  ├─ processed UAC audio → common SpeechToText (whisper.cpp small.en) → transcript
  ├─ selected-beam energy → calibrated temporal speech activity
  └─ selected-beam DoA ───────┐
Camera → PersonTracker → calibrated image-x→azimuth mapping
                             ↓
                       ActiveSpeakerFusion
                             ↓
                    active person / assigned role
                             ↓
               temporal state estimator → room agent
                             ↓
              delegation → deterministic validator → adapters
```

This is the canonical integration pipeline, not a claim of verified live hardware. Audio adapter lifecycle, normalized observation collection, geometric fusion and the UAC-to-STT bridge are implemented; real camera ingestion and normalized semantic state projection are connected but unverified with physical devices. Scene semantics still need an upstream producer. Scenarios infer activities from sensor evidence. FastAPI `/api/audio` exposes current frame and adapter availability. Unchanged live evidence does not invalidate agent decisions. Raw four-beam telemetry is adapter-only.

Layered configuration and developer profiles separate platform/hardware from authority. Core code contains no CoreAudio/WASAPI objects, absolute machine paths, shared device indices, or LLM USB/DSP access. See [audio contracts/calibration](AUDIO_FRONTEND.md) for exact lifecycle, coordinate, threshold and readiness semantics. Current hardware combination: real XVF audio plus simulated AV outputs, or entirely simulated. Unsupported real AV adapters fail explicitly; their config selectors are future extension points.
