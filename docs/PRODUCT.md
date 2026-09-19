# Agentic Classroom: instructor application

**The researcher console is preserved but product UI/functionality is now the primary implementation priority.** Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.

## Routes and use

- `/`: normal instructor dashboard. No research identifiers, scenario names, trial controls or raw model telemetry. Old `?researcher=1` does not change the main application.
- `/devices`: honest availability of sensing, AV outputs, video engine and local AI. Simulated inputs/outputs are explicitly identified here.
- `/settings`: AI, Camera, Audio, Display, Recording, Devices and Advanced. Default mode/model/framing/follow/layout preferences persist locally. Hardware calibration/mapping and recording destinations are described as technician/adapter setup, not fake editable integrations.
- `/dev`: technical diagnostics and development-only observation inputs, reachable via Settings → Advanced. Raw observation/profile/agent details belong here.
- `/research`: preserved researcher console and study workflow; `/research?view=participant` retains its participant presentation. The research UI and stylesheet are separate lazy-loaded modules. No new study workflow features are added in this milestone.

Off / Assist / Auto map to Manual / Assistive / Autonomous internally. Off is the safe startup default. Assist asks before applying; Auto executes policy-permitted actions and shows concise recent changes. Mode changes return immediately while inference runs asynchronously. Every AI result still passes the existing revision/policy/safety checks. Take Control clears pending recommendations, selects Off and cancels product inference; it does not reset display/audio or stop recording. A running research session shares the same room state and may lock non-Off mode changes; finish that session in research tools before product use.

Manual camera choices are Presenter, Demo area and Wide. Follow presenter returns to the presenter and enables follow; selecting Demo/Wide disables follow. Display choices are Instructor laptop, Room PC, Camera/program and Blank. Audio choices are Presentation, Media and Mute. Recording transport is explicit, with an elapsed timer; program layout is independent and may change while recording continues. No AI recording start/stop permission was introduced.

Program preview is currently an **illustrated composition**, not live video. Simulated recording writes no video file; this is stated next to the recording control. Room display source is shown independently from recording/program layout. An OBS failure does not disable direct display controls.

Assist recommendations are lightweight and expire after 45 seconds or when relevant state changes. Product Apply/Ignore binds to a recommendation ID and rejects stale submissions. Recent actions contain useful device changes, marked AI/approved/you, not raw research events. Undo operates only on the latest reversible simulated action with matching current values; camera undo restores framing and follow together. It never undoes recording transport. Physical compensation requires adapter verification in a later milestone. A later manual action prevents undoing an older AI command over that change.

## Backend boundaries

`/api/instructor/state` returns the normalized InstructorAppState model: room health, AI mode/availability, current activity, display, camera, audio, recording/program, concise recent actions, pending recommendation and device status. It deliberately does not expose study/internal state. The frontend uses this contract identically across simulation-basic, simulation-ai, hybrid and hardware.

`product.py` manages async product mode changes, cached local-model availability, validated manual actions, ID/expiry-bound approvals, safe undo, preferences and advanced diagnostics. The underlying RoomState, Orchestrator, delegation, typed safety and DeviceRouter remain shared with research/live/simulation. Local model health is probed every ten seconds; transient failures may take that long to appear. A successful tag probe is availability, not a claim that a particular inference will succeed. Inference errors show a concise message; manual controls remain available.

`video.py` defines `VideoEngine.set_layout/start_recording/stop_recording/get_status/preview`. SimVideoEngine uses validated simulated state changes and reports illustrated preview. OBSVideoEngine is an explicit disconnected implementation boundary; no physical OBS WebSocket protocol was added merely to complete the UI. Never show guessed OBS state or simulated success when OBS is selected. Future OBS operations belong in this class, not the frontend or orchestrator.

Product defaults are stored in ignored `config/local.product.json` (no credentials). Saving defaults does not operate hardware or start recording. Default mode/framing/follow/layout apply at next controller startup; local-model changes invalidate pending inference/recommendations immediately. Only simulated adapters receive framing/layout startup defaults today; real adapters remain honestly disconnected. Unconfigured mic selection, measured thresholds, demo calibration, I/O mapping and recording destinations remain technician/adapter work, with explicit explanations in Settings. No full first-run wizard yet.

Research event logging continues alongside the bounded in-memory product action feed. Research code/routes remain, and the instructor-only CHI V1 constraint is unchanged. No deployment/cloud dependency was added. The single-process prototype binds localhost; separate routes are presentation separation, not authentication or independent room sessions.

## Primary local development

From repository root on Mac:

```bash
# With Ollama running and qwen3:8b installed:
backend/.venv/bin/python -m backend --profile simulation-ai
# Separate terminal:
cd frontend
npm ci
npm run dev
```

Windows PowerShell:

```powershell
& backend/.venv/Scripts/python.exe -m backend --profile simulation-ai
# Separate terminal:
Set-Location frontend
npm ci
npm run dev
```

Clear conflicting legacy AGENT_BACKEND overrides or explicitly set it to ollama. The convenience launch scripts now default to simulation-ai. `--profile simulation-basic` still runs without Ollama or hardware; the UI labels deterministic responses as AI demo, not a connected local model. Profile/agent names are confined to diagnostics. Off/Assist/Auto are independent of adapter selection.

For a quick interaction check: manually set camera Wide, then choose Assist to obtain and accept a Qwen recommendation for presentation. Set Wide again and choose Auto to observe an action, Undo it, then Take Control. Change normalized context through `/dev` to exercise demo/media without exposing developer scenario controls on the main dashboard.

No physical AV or live-preview success is claimed. Recommended next milestone: implement the OBSVideoEngine transport/readback first, then XVF/PTZ/display adapters one at a time without changing the product interaction model.
