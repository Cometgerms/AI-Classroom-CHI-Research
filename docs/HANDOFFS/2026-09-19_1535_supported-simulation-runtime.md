# Supported simulation runtime — 2026-09-19 15:35 ET

Immutable handoff. Builds on the uncommitted XVF3800 refactor; preserves its files, pinned model choices, calibration defaults and earlier handoff. No physical projector/PTZ integration or git commit was performed.

## Implemented

- Five explicit profiles: simulation-basic (core-only Fake), simulation-ai (strict real local Qwen), hybrid (independent selectors), hardware (real selections with honest unavailable outputs), study (controlled sensor trials and hidden participant diagnostics). Legacy aliases preserved.
- Shared AudioObservation, PersonTrack, VisionObservation, SceneObservation and validated ObservationFrame. RealCameraPerception lazily loads optional OpenCV/YOLO; simulation camera/audio publish the identical contracts. Live hybrid sensing feeds the same pipeline with nonblocking model inference.
- Data-driven YAML timelines under config/scenarios. All twelve requested scenarios plus wrong-camera/display/audio variants. Speech, DoA, tracks, floor evidence, transcript and presentation events pass through geometric ActiveSpeakerFusion and sustained StateEstimator. Student question verifies LECTURE → TRANSITION → Q&A. Physical calibration remains false/null; virtual scenario calibration is explicit.
- One agent evaluation per completed trial; optional realtime scheduling. Direct semantic assignment remains only a named debug endpoint, disabled in study. Same policy/safety/agent interface for every runtime. Manual/Assistive/Autonomous remain independent.
- Controlled model errors transform decisions before delegation; experiment_injection events contain the internal labels. Participant UI has no injection cues or researcher controls. Researcher console explicitly available with ?researcher=1. This is localhost presentation separation, not authentication.
- DeviceRouter selects each AV subsystem independently. Simulated adapters mutate/read back state. PJLink/PTZ/OBS/real audio output are unavailable placeholders that never fabricate success. Device-failure scenarios report action failure without changing the failed device.
- GET/POST /api/replay exports/replays versioned normalized trial tapes with initial simulated-device baseline, calibration, condition metadata and injections. Current participant/authority are preserved. JSONL persists tapes, observations and decision/action events; scripts/replay_trial.py extracts/replays them after restart.
- Doctor independently reports Simulation basic, Simulation AI, XVF hybrid, Full hardware. README, architecture, both setup guides, AGENTS and append-only decisions updated. Detailed API/config notes: docs/SIMULATION.md.

## Real AI versus simulation

Simulation-ai uses actual Qwen3:8b through the existing OllamaAgent; strict mode forbids Fake fallback. Fusion, temporal estimation, action validation and delegation are real application code. Sensor observations, room geometry and AV readback are intentionally simulated. Simulation-basic and study default to deterministic Fake; study can configure Ollama. Whisper/YOLO/VLM are not required to replay already-normalized observations. No live microphone/camera capture or physical AV success was claimed.

## Verification

- Backend: **95 passed, 1 hardware-optional test deselected** (`cd backend && .venv/bin/python -m pytest -q`). Includes isolated startup with sounddevice/usb/cv2/torch/ultralytics/Silero/libusb imports blocked, both basic and unavailable hardware profiles; normalized contracts/fusion/transitions, every ordinary scenario, all three authorities, all profile/condition combinations, hybrid selection, logged injections, replay baseline/authority, malformed-tape rejection and participant config/debug restrictions.
- Strict real Qwen end-to-end smoke passed Manual, Assistive and Autonomous twice through sensor scenario → fusion → estimator → RoomAgent → delegation → simulated device. Evidence: artifacts/simulation_ai_smoke.json. No fallback. Requires external Ollama; not CI.
- Frontend `npm run build` passed; existing lucide-react module-directive warnings only. Browser-checked study participant/researcher views and controlled wrong-Q&A recommendation; participant view omitted internal labels and evidence.
- Doctor: Simulation basic READY, Simulation AI READY; XVF hybrid NOT READY, Full hardware NOT READY. No accessible XVF; physical output adapters deliberately absent. Core Python lacks optional Torch/YOLO; optional perception environment from earlier session remains available.
- JSONL tape extraction CLI passed; Python source syntax and git diff whitespace checks passed. Core CI configured for Linux/macOS/Windows; remote CI/Windows execution not performed here.

## Exact macOS startup (repo root)

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend --profile simulation-basic
```

Separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. For Qwen, install/start Ollama, run `ollama pull qwen3:8b`, stop the basic backend and run:

```bash
backend/.venv/bin/python -m backend --profile simulation-ai
# Separate terminal, verification:
backend/.venv/bin/python scripts/check_simulation_ai.py
```

For participant study, replace profile with study. Researcher URL: http://localhost:5173/?researcher=1. No .env is required; clear conflicting AGENT_BACKEND overrides if present. If Homebrew Node is keg-only: `export PATH="/opt/homebrew/opt/node@22/bin:$PATH"`.

## Exact Windows startup (repo root, PowerShell)

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
& backend/.venv/Scripts/python.exe -m backend --profile simulation-basic
```

Separate terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

For Qwen, install/start Ollama, `ollama pull qwen3:8b`, stop the basic backend, then from root:

```powershell
& backend/.venv/Scripts/python.exe -m backend --profile simulation-ai
# Separate terminal:
& backend/.venv/Scripts/python.exe scripts/check_simulation_ai.py
```

Study and hybrid profile names are identical across platforms. Optional hardware dependencies are in platform setup docs, not required for these commands.

## Known limits and next step

One process/session; individual-action undo and no recommendation-ID binding. Trial replay does not yet re-enact arbitrary interleaved participant actions across a whole session, although those events are logged. Qwen replay re-infers and is not bit-exact. A scenario evaluates once after its timeline; use successive trials or /api/observations for multiple decision points. Scene semantics/STT still require an upstream producer in live hybrid mode. Real camera code and XVF calibration remain unverified with physical devices. No automatic reconnect for UAC. Local participant/researcher presentation is not an authorization boundary.

Recommended next step: extend controlled-study scripts and representative strict-Qwen trial regression checks, then validate calibrated real XVF/camera observations using hybrid without changing the observation pipeline. Preserve simulation CI as a permanent requirement. Physical AV integration must retain honest capability/failure reporting and follow successful simulation-ai verification.
