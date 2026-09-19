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

## 2026-09-19 — XVF3800 will be the V1 audio front end

Decision: XVF3800 is the V1 canonical audio front end. AudioFrontEnd (real/simulation) supersedes a SoundSourceTracker-centric normal path. Keep generic VAD/localization adapters for optional research.
Why: the four-microphone device supplies AEC, adaptive multi-beam beamforming, dereverberation/noise suppression, AGC, limiter, DoA, speech-energy information, USB Audio Class audio and USB host control. Do not duplicate those functions on the host unnecessarily.
Alternatives considered: normal-path ODAS plus Silero, raw multichannel host DSP, native platform-specific room logic.
Consequences: ODAS and Silero are not required or installed by default. Host-side whisper.cpp small.en and YOLO person tracking remain V1 capabilities; VLM/pose are optional. Speech energy requires experimentally calibrated threshold and onset/release hysteresis. Auto-selected beam supplies primary direction, orientation offset/inversion remain local. Camera-calibrated geometric fusion associates azimuth with tracks without LLM calculations or assumed depth. UAC streaming and read-only USB telemetry use separate adapters. Simulation and hybrid modes share observations and study authority; platform layers choose acceleration, not different reasoning/STT models. Python host-control is pinned; hardware success must be measured, never inferred from package presence.

## 2026-09-19 — Config layers and sensor/study separation

Decision: use default → platform → named profile → local → environment precedence. Shared model is Qwen3:8b; shared agent default Ollama, explicit simulation profile FakeAgent. Legacy backend/.env remains an override for compatibility. Polling/fusion status lives at /api/audio, outside the scenario state mutation loop.
Why: both development machines need one application and locally calibrated hardware choices; 10 Hz sensor updates must not repeatedly invalidate slow inference or overwrite controlled study manipulations.
Alternatives considered: separate platform apps, hard-coded device indices, direct per-poll scenario mutation.
Consequences: environment overrides can intentionally override a profile; document and remove stale .env entries locally. Fusion consumes normalized tracks but live camera producer/event-to-state projection remains a separately testable next step. Real camera/projector/recorder choices currently fail as unsupported; real XVF audio + simulated AV is supported. New CI matrix checks core on Linux/macOS/Windows without requiring hardware or ML accelerators.

## 2026-09-19 — Explicit simulation launch overrides local hardware mode

Decision: refine the preceding configuration-order entry: default → platform → local → explicit launch profile → environment. This supersedes only that entry's profile/local precedence.
Why: `--profile simulation` must select simulated adapters even when a developer keeps a hybrid local.yaml. An explicitly requested launch profile is an operational choice; environment remains the highest override.
Alternatives considered: preserving local-over-profile precedence and requiring extra environment variables to escape hardware mode.
Consequences: local calibration and device matching remain effective; explicit simulation selects FakeAgent/simulated audio. Environment variables can still override intentionally. Config unit tests cover this case.

## 2026-09-19 — Supported simulation runtime and normalized trials

Simulation-basic, simulation-ai, hybrid, hardware and study are runtime profiles, independent of Manual/Assistive/Autonomous authority. Simulation is a permanent research/product mode; hardware ownership is never required for contribution. Simulation-ai uses strict local Qwen, real fusion/estimation and unchanged delegation against simulated sensors/devices.

Versioned YAML timelines generate normalized AudioObservation/VisionObservation/SceneObservation frames. Same fusion/estimator applies to real sensing, simulation and replay; virtual calibration is explicit and does not certify real geometry. Scenarios evaluate once after their timeline; live streams evaluate stable changes. Direct semantic labels are debug-only. Controlled errors transform decisions before authority policy and are logged separately without participant UI markers.

Replay records trial sensor inputs, initial simulated devices, calibration and injection metadata. Replaying preserves current participant/authority to support comparisons; full participant-session command reenactment is not yet implemented. Study participant view hides technical controls; researcher query is local presentation, not access control. Physical PJLink/PTZ/OBS/audio output remain honest unavailable adapters. Strict Qwen full-loop smoke passed all three conditions before any physical AV integration work.

## 2026-09-19 — Protected instructor-only CHI poster V1 scope

CHI V1 is an instructor/TA-only controlled teaching-task study. Student presence is outside the V1 experimental scope. Each session has one instructor/TA/experienced-presenter participant and one researcher/facilitator, with no student actors. This supersedes earlier student-oriented study examples and any implication that DoA calibration or multi-person fusion is required for V1.

Keep the existing normalized observation pipeline, estimator, agent, policy and adapters. Add PRE_CLASS/POST_CLASS and known-presenter evidence without acoustic localization; retain all multi-person states and scenarios as deferred extensions. XVF priorities are processed microphone audio, AEC, speech activity and local Whisper input. One PTZ with presenter/demo_zone/wide intents is sufficient. No DoA calibration work may block study development.

The controlled 14-step teaching script is identical across six counterbalanced condition orders. Wrong display at step 12 is the standardized AI-condition failure; manual receives the same physical teaching/check/recovery prompts but no fabricated AI action. Wrong camera/audio/recording fixtures are available for pre-specified variants. This planned difference must be explicit in failure-recovery analysis.

Add task/completion/latency logging, per-capability authority restrictions and post-condition ratings/preferences. Preserve assigned condition separately from effective authority after Take Control. Single-item 1–7 control/trust/workload ratings are implementation defaults, not claims of validated questionnaires. Old handoffs remain immutable; the new handoff supersedes their V1 scope.

## 2026-09-19 — Product-first instructor application; research tooling frozen

Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed. The researcher console is preserved but product UI/functionality is now the primary implementation priority. This changes implementation priority, not the protected instructor-only CHI V1 research scope.

The main `/` route is Agentic Classroom with AI Mode Off/Assist/Auto, independent of hardware runtime. Existing researcher code and CSS move intact to the lazy-loaded `/research` route; study routes/models/logs/replay/injections remain. Product consumes `/api/instructor/state`, a clean view model without trial metadata. `/devices`, `/settings` and `/dev` separate operation, configuration and diagnostics. Primary local development is simulation-ai with strict Qwen; core-only simulation-basic remains supported.

Add deterministic follow/blank/mute controls, explicit recording/timer/layout, bounded action feed, safe latest-action undo, ID/expiry-bound product recommendations and AI-independent Take Control. VideoEngine abstracts simulated recording/program from a future OBS transport. OBS selection currently reports disconnected; no physical protocol was implemented to finish UI. Program preview is explicitly an illustration; simulated recording does not create a file. Room display remains independent of recording/program availability.

Settings persist local defaults only; unsupported hardware calibration/mapping/destination controls are described honestly. No separate simulator UI, cloud dependencies, research-workflow enhancements, or changes to the three experimental definitions.
