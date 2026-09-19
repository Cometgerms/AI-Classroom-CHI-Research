# Product-first instructor UI — 2026-09-19 16:42 ET

**The researcher console is preserved but product UI/functionality is now the primary implementation priority. Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.**

Continues from the uncommitted instructor-only V1 work on top of commit 33504d0. No commit made in this session. Prior immutable handoffs and the protected instructor/TA-only study scope remain intact.

## Delivered

- `/` now opens a new instructor application, with no trial/session/participant/scenario controls or raw confidence/evidence/backend names. Old `?researcher=1` does not enable research UI.
- Preserved prior researcher component/styles in frontend/src/research, lazily loaded at `/research`; participant presentation remains at `/research?view=participant`. Backend study routes, logging/replay, participant models, conditions, scenarios and injections remain. Only routing/shared-device compatibility changed; no new study workflow development.
- Polished responsive product dashboard: room/AI/recording status, Off/Assist/Auto, illustrated program composition, separate room-display source, readable current activity, camera/framing/follow, display Laptop/Room PC/Program/Blank, Presentation/Media/Mute audio, explicit recording start/stop/timer/layout. Simulated recording explicitly states that no video file is saved.
- Lightweight Assist suggestions with Apply/Ignore/Why and persistent footer affordances; compact Auto action history, latest-action Undo and always-visible Take Control. Take Control leaves recording/display/audio intact and does not wait for Qwen. Recommendations expire after 45 seconds or state invalidation and product approval binds to ID.
- Devices page reports sensing/output/video/local-AI availability honestly, identifying simulated devices. Settings offers persistent local defaults for mode/model/framing/follow/layout and explanatory hardware setup sections. Advanced diagnostics at `/dev` contains raw state/profile and development observation cues, not normal teaching controls.
- `/api/instructor/state` projects shared backend state into a typed InstructorAppState rather than returning research structures. Same frontend across simulation-basic, simulation-ai, hybrid and hardware. Async inference/probe isolates manual operation from model availability. Runtime axes remain independent.
- VideoEngine protocol with set_layout/start_recording/stop_recording/get_status/preview. SimVideoEngine works through validated simulated changes; OBSVideoEngine explicitly reports disconnected until its transport/readback is implemented. No scattered OBS calls or physical protocol implementation.
- New typed camera_set_follow plus blank/mute enum values. Selecting Demo/Wide disables follow; enabling follow selects presenter. Product Undo checks the latest action and current values, restoring camera framing/follow together without implicitly reversing recording transport. Research's existing generic Undo remains preserved.
- Bounded product action feed is separate from private research JSONL. Product events continue logging mode, approval, action and override events. Preferences persist in ignored config/local.product.json. AI mode defaults Off; primary developer launch scripts now select simulation-ai.

## Verification

- Backend: **126 passed, 1 hardware-optional deselected**. Existing study/simulation/audio tests remain passing. Product tests cover clean view model, manual controls/recording timer, ID/expiry approval, Ignore, Auto/Undo, slow inference cancellation, Qwen error/manual controls, OBS failure/display independence, settings validation/persistence, composite camera undo, restrictions and VideoEngine semantics.
- Frontend TypeScript + production build passed. Existing lucide module-directive warnings only. Research and instructor components/styles produce separate lazy bundles.
- Browser checked dashboard layout (including lower controls/history), real Qwen Assist recommendation + Apply, real Qwen Auto camera action + Undo, explicit simulated recording start/stop, Take Control while recording continued, Devices, Settings → Advanced → Diagnostics, preserved `/research`, and root with legacy researcher query still showing product only.
- Actual local Qwen3:8b / simulation-ai served browser walkthrough; no Fake fallback. Model/perception dependencies unchanged. No hardware or Windows execution claimed. Git whitespace check clean.

## Running / exact commands

The local frontend and backend are left running; primary backend is **simulation-ai**, physical devices simulated, real local Qwen available. Recording stopped and AI Off after browser verification. Main URL http://localhost:5173. Research is only at http://localhost:5173/research. Current user browser can refresh directly into the product.

Mac from repository root, with Ollama running and qwen3:8b installed:

```bash
backend/.venv/bin/python -m backend --profile simulation-ai
# If a legacy .env AGENT_BACKEND=fake conflicts:
AGENT_BACKEND=ollama backend/.venv/bin/python -m backend --profile simulation-ai
# Separate terminal:
cd frontend
npm ci
npm run dev
```

Windows PowerShell from repository root:

```powershell
& backend/.venv/Scripts/python.exe -m backend --profile simulation-ai
# If a legacy override conflicts, set $env:AGENT_BACKEND = "ollama" first.
# Separate terminal:
Set-Location frontend
npm ci
npm run dev
```

Stop an existing backend before switching profiles. Explicit simulation-basic remains the hardware/Ollama-free option; same product UI labels deterministic responses as AI demo. Hybrid selects each adapter via existing config; disconnected real outputs remain unavailable, not silently simulated.

## Limitations / next milestone

Program preview is an illustration, not live OBS/camera video. OBSVideoEngine is a defined disconnected adapter boundary, not implemented WebSocket transport. Simulated recording saves no file. Mic selection/threshold measurement, demo-zone physical calibration, I/O mapping and recording destination remain technician/adapter setup, explained honestly in Settings. No full setup wizard. UI responsive CSS exists; browser visual QA was at desktop size, not on physical touch hardware.

Local model probe checks availability every ten seconds; inference can still fail separately. One backend process/room; product and research share authority/state. A running research session can restrict non-Off product mode changes. Routes are separation of presentation, not access control. Product history/preferences are local; history is bounded/in-memory. Product Undo supports only latest reversible simulated changes and never recording transport; physical compensation requires future readback. Prior trial replay/session limits remain.

Next: refine instructor interaction from use, then implement OBSVideoEngine connection/status/preview/recording readback before replacing XVF/PTZ/PJLink/HDMI adapters one at a time. Preserve product interaction, shared normalized pipeline and honest unavailable states. Do not resume research UX work without a new priority decision.
