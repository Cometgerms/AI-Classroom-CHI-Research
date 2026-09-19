# Instructor-only CHI V1 scope — 2026-09-19 16:08 ET

**CHI V1 is an instructor/TA-only controlled teaching-task study. Student presence is outside the V1 experimental scope.** Protected constraint: one instructor/TA/experienced-presenter participant and one facilitator; no students or student actors. This new immutable handoff supersedes earlier student-oriented V1 assumptions without editing historical handoffs. Baseline commit: 33504d0. This revision is uncommitted.

## Changes

- Protected scope in AGENTS, CURRENT_STATE, ARCHITECTURE, SIMULATION, README, audio/model/setup docs and new docs/STUDY_V1.md. Append-only decision records the scope change.
- PRE_CLASS and POST_CLASS activity states join Lecture/Presentation, Demonstration, Media Playback, Transition and Unknown as primary V1 states. Existing multi-person states/scenarios are preserved as extensions outside V1.
- Shared normalized SceneObservation adds session_phase, transitioning and presentation_source. The same pipeline infers presenter activity from one explicitly assigned presenter track and speech evidence without DoA or acoustic geometry calibration. Geometric fusion stays optional; no separate instructor-only estimator/agent/device architecture.
- XVF3800 still provides processed microphone audio/AEC, speech activity and Whisper input. Optional DoA polling can be disabled with audio.doa_enabled=false; DoA failure no longer disables successful energy/speech observations. Real speech-energy thresholds still need calibration. DoA/camera-azimuth work cannot block V1 study development.
- Thirteen v1_ scenario fixtures: pre/post class, lecture, movement, whiteboard, demonstration, media, source change, transition and four failures. Fixtures have one presenter, null DoA and uncalibrated geometry. Default development starts v1_lecture; study starts v1_pre_class. Existing student/Q&A scenarios remain available outside study.
- `config/study/chi_v1.yaml` defines the same 14 teaching tasks for all conditions. `study.py` and /api/study endpoints provide six counterbalanced orders, task start/completion and feedback. Researcher selects group and position; participant receives only ordinary task prompts. Source failure is standardized at step 12 in Assistive/Autonomous; step 13 preserves the faulty state/recommendation for recovery. Manual has the same teaching/check/recovery prompt, no invented AI action. This planned difference is explicit in the analysis guidance.
- Primary UI replaces student avatars/voice lift/Q&A controls with presenter/demo/wide, source/application, speech/video audio and recording layouts. Controlled wrong camera/display/audio/recording fixtures use instructor workflow. Injection labels stay in researcher tools/logs. Study/profile replay guards prevent multi-person trial playback during V1.
- Per-capability authority restrictions deny AI changes while preserving manual control. Take Control changes effective authority while retaining assigned condition in study metadata. Free condition switching is blocked during an active assigned study condition.
- Logs retain manual/recommendation/autonomous/override/undo/restriction events and add run/task/assigned-condition context, inference/response latency and reported task outcomes. Post-condition UI/API records separate 1–7 control/trust/workload ratings and Camera, Display/source, Audio, Recording delegation preferences. Scores are explicitly supplied, never inferred. Ratings are single-item defaults, not a validated workload/control/trust instrument.

## Verification

- Backend suite: 115 passed, 1 hardware-optional deselected. Covers all 14 tasks in each authority condition, counterbalance balance, one-presenter/no-DoA fixtures, real-source contract compatibility, V1 states, four failure variants/concealment, restrictions/Take Control, assigned-condition preservation, scope/replay guards, feedback validation and optional DoA failure. Legacy multi-person regression tests remain passing.
- Strict actual Qwen smoke now uses v1_demonstration; Manual, Assistive and Autonomous passed. Evidence: artifacts/simulation_ai_smoke.json. No DoA or students required.
- Frontend build passed; existing lucide module-directive warnings remain. Browser inspected updated controls, presenter-only room display, V1 scenario list and task/counterbalance controls.
- No physical camera, XVF, projector/PTZ or Windows verification claimed. No dependencies/models changed.

## Running

Current local frontend remains http://localhost:5173; backend refreshed in simulation-basic with the new V1 default. Both left running as requested previously. No study condition was started in the live user session during UI inspection.

From repository root on Mac:

```bash
backend/.venv/bin/python -m backend --profile study
# Separate terminal:
cd frontend
npm run dev
```

Windows PowerShell:

```powershell
& backend/.venv/Scripts/python.exe -m backend --profile study
# Separate terminal:
Set-Location frontend
npm run dev
```

Stop an existing backend before switching profiles. Participant URL: http://localhost:5173; facilitator: http://localhost:5173/?researcher=1. In researcher controls set pseudonymous participant ID, group 0–5 and condition position 0–2. Start assigned condition; Begin next teaching task; explicitly mark completion; complete all tasks and feedback. Keep group constant across the participant's conditions. Full installation instructions remain in platform guides. For actual Qwen use simulation-ai, or configure study with AGENT_BACKEND=ollama and OLLAMA_STRICT=true.

## Limits / recommended next step

Finalize and freeze the common slide deck, video duration, application, demonstration materials and questionnaire with the research protocol. The task runner cues sensor evidence; it does not operate slides/video applications. Task completion is reported, not automatically measured. Recruitment/group allocation remains facilitator-managed. Built-in scripted driver currently requires simulation/study, while live hybrid needs an upstream scene/STT producer and physical AV integration. Single-session localhost prototype; researcher visibility is not authentication. Replay remains trial-level, not full participant-session reenactment.

Next: rehearse the complete instructor-only protocol, refine timing and materials, validate event coding/ratings, and only then connect real processed audio/presenter tracking through the same normalized pipeline. Do not revive student actors, voice lift, Q&A or DoA calibration as V1 prerequisites.
