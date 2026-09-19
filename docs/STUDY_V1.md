# CHI poster V1: controlled teaching-task study

> Research tooling is preserved but temporarily frozen. Product UI at `/` is the current priority; this protocol is retained at `/research` without further study-workflow development.

**CHI V1 is an instructor/TA-only controlled teaching-task study. Student presence is outside the V1 experimental scope.** This is a protected research constraint. Recruit instructors, teaching assistants, or experienced classroom presenters. Each session has exactly one participant and one researcher/facilitator. Students are not participants, and no student actors—physical or simulated as a study prerequisite—are required.

The participant teaches individually in a controlled room. Researcher-triggered events concern their own presentation/AV workflow. Keep Q&A, Discussion, Student Presentation, Side Conversation, student tracking/voice lift and multi-person fusion as reusable extensions, outside required V1 scope.

## Common materials and procedure

Use the same room, one PTZ camera, slide deck, short embedded video with program audio, alternate application, demonstration object, task prompts and facilitator cues in all three conditions. Before recruitment, freeze the materials/version and media duration in the study protocol. A practical rehearsal uses three teaching slides, one 20-second embedded clip, a single object demonstrated at the whiteboard/demo area, and one alternate application window. Supply these materials locally; the prototype does not bundle a deck/video or control presentation software. Do not improvise content or AV difficulty by condition.

Camera intents are presenter, demo_zone and wide. An instructor alias remains for backward compatibility; student camera targets are not needed. Multiple cameras remain an architectural extension. Recording transport is always participant controlled.

Facilitator explains controls, gives equivalent practice, assigns the counterbalanced condition, and advances tasks when the participant is ready. Do not announce an injected error. Complete a post-condition questionnaire before the next condition. Use a pseudonymous participant ID and record the chosen material version in facilitator notes.

| Step | Participant task | Researcher sensor cue |
| --- | --- | --- |
| 1 | Begin teaching session; check AV setup | v1_pre_class |
| 2 | Open/start slides | v1_lecture |
| 3 | Speak while presenting several slides | v1_lecture |
| 4 | Move away from lectern while teaching | v1_presenter_moves |
| 5 | Move into whiteboard/demo area | v1_whiteboard |
| 6 | Perform brief demonstration | v1_demonstration |
| 7 | Return to slides | v1_lecture |
| 8 | Play embedded video with program audio | v1_media_playback |
| 9 | Pause/stop video; resume presentation | v1_lecture |
| 10 | Change to another presentation/application source | v1_source_change |
| 11 | Return to normal lecture presentation | v1_lecture |
| 12 | Continue presenting; check slides remain visible | Standardized wrong display source in AI conditions |
| 13 | Restore or maintain intended AV setup using available controls | No new sensor trial: preserves error/recommendation for correction |
| 14 | End teaching session; stop any recording | v1_post_class |

The versioned task data is `config/study/chi_v1.yaml`. Participant prompts and physical tasks are identical across conditions. Step 12 injects a camera-feed display recommendation in Assistive, or executes that policy-permitted wrong source in Autonomous. Manual performs the same presentation/check/recovery task without an invented AI action. This planned difference must be acknowledged when analyzing failure recovery: compare Assistive/Autonomous error responses directly, and treat Manual as the manual-workflow baseline. Do not silently add automated AV errors to Manual.

## Conditions and counterbalancing

- **Manual:** participant performs AV actions. No AI recommendations/execution.
- **Assistive:** AI contextualizes observations and proposes changes; participant accepts/dismisses and can make manual corrections.
- **Autonomous:** AI executes policy-permitted changes; participant may undo, restrict a capability, or take control.

Assign participants evenly to the six permutations of Manual/Assistive/Autonomous, as returned by `/api/study/protocol`. Record `counterbalance_index` (0–5) and `condition_position` (0–2); reuse the same group for a participant's three conditions. The facilitator allocates groups; the software does not implement recruitment allocation or prevent a researcher from deliberately choosing a different group. Assigned condition remains logged separately when Take Control changes current authority to Manual. Reset restrictions/device baseline at the next assigned condition. The same 14 tasks run in every order.

## Shared perception and runtime

Priorities: known instructor/presenter tracking and zone, speech activity, local Whisper transcription, presentation/source state, media playback, demo/whiteboard evidence and temporal transitions. Primary activity states are PRE_CLASS, LECTURE (presentation), DEMONSTRATION, MEDIA_PLAYBACK, TRANSITION, POST_CLASS, UNKNOWN.

All sources use the existing ObservationFrame pipeline and StateEstimator. Session phase, source and transition cues are normalized SceneObservation fields. An explicitly assigned single presenter plus speech/scene evidence can support lecture/demo inference without DoA. Geometric ActiveSpeakerFusion remains available for later multi-person work, but no DoA calibration or student identity is needed for V1. V1 scenario fixtures contain one presenter, no student tracks, null DoA, and uncalibrated geometry. These are evidence fixtures, not direct semantic-state assignments.

XVF3800 remains canonical: processed microphone audio, device AEC, speech activity, and Whisper/STT input are the priorities. DoA is optional context; `audio.doa_enabled: false` skips its polling, and a DoA read failure does not disable successful speech-energy observations. Speech-energy threshold calibration is still required for real energy-based speech detection; acoustic triangulation/camera-azimuth calibration is not. Simulation development requires neither. The live transcript/scene producer and physical PTZ output remain integration work; no physical hardware verification is claimed.

## Failures and participant presentation

Required fixtures: `v1_wrong_camera` (demo target while presenting at the normal position), `v1_wrong_display` (camera feed instead of slides), `v1_wrong_audio` (media mode during spoken lecture), `v1_wrong_recording` (wide instead of slides/presenter composition). Standard script uses the display failure at the same point in each relevant AI condition. Use other variants only under a pre-specified protocol, not ad hoc substitutions.

Failures pass through the unchanged agent/delegation/action boundaries. `experiment_injection` logs retain labels; participant tasks, recommendations and UI do not identify them as injected. Researcher controls remain hidden in study participant view. Internal labels/API access are local researcher tools, not an authentication boundary. No student controls/avatars appear in the primary UI. Extended multi-person scenarios remain in the development API, and are rejected during an active V1 study or in the study runtime.

## Running and recording

Start `python -m backend --profile study` with the project virtual environment, plus `npm run dev` in frontend. Participant: http://localhost:5173/research?view=participant. Facilitator: http://localhost:5173/research. Set participant ID, counterbalance group and condition position; Start assigned condition, then Begin next teaching task. Participant/facilitator explicitly marks completion before advancing. Completion is reported, not automatically inferred from sensors. The API also accepts partial/aborted outcome and notes.

API sequence:

1. `GET /api/study/protocol` — safe task prompts and six condition orders.
2. `POST /api/study/start` with `{"counterbalance_index":0,"condition_position":0}`.
3. `POST /api/study/next` — schedules that task's normalized scenario through the existing pipeline.
4. `POST /api/study/complete` with `{"outcome":"completed","notes":""}`; repeat steps 3–4 for 14 tasks.
5. `POST /api/study/feedback` with scores and all four delegation preferences.

Built-in scripted playback requires simulation-basic, simulation-ai or study. Hardware/hybrid share observation contracts but require a future live facilitator driver. Trial tapes/replay are unchanged. To use actual Qwen in study configure `AGENT_BACKEND=ollama` and `OLLAMA_STRICT=true`; otherwise study defaults to deterministic Fake. Per-capability `POST /api/authority/restrict` takes capability camera/display/audio/recording and boolean restricted. Restrictions clear pending recommendations and deny subsequent AI changes in that capability; manual control remains available.

## Measures and operational definitions

JSONL events include pseudonymous participant ID, current authority, assigned condition, study run ID, task ID and condition position:

- Manual actions: participant_manual_action.
- AI recommendations and acceptance/dismissal: recommendation_created, recommendation_applied, recommendation_dismissed.
- Autonomous actions: device_action_executed with current condition autonomous; policy denials and failures remain logged.
- Overrides/undo/Take Control: participant_override with mode undo/manual. Assigned condition is retained.
- Authority restrictions: authority_restriction per capability.
- Response latency: agent_response_latency for model inference; recommendation response from creation to Apply/Dismiss; first participant response after the latest recommendation or autonomous device action carries response_latency_ms. Use injection/action timestamps for failure-specific analysis. These are engineering/event measures, not a validated psychological response-time instrument.
- Task completion: study_task_started/completed, reported outcome and elapsed milliseconds. Task elapsed time includes cue/model time; it is not solely correction time.
- Perceived control, trust, workload: explicit post-condition 1–7 ratings (1 very low, 7 very high), plus optional notes. These are single-item ratings, not NASA-TLX or a validated multi-item scale.
- Post-condition delegation preference: separate required camera, display, audio, recording choices (manual/assistive/autonomous). Never collapse these to one global preference.

The feedback UI requires every rating/preference. No subjective score is inferred or fabricated. Logs and recordings remain private/untracked. A formal study still needs the finalized protocol/materials and questionnaire choice; these implementation defaults are for controlled rehearsal and data capture.
