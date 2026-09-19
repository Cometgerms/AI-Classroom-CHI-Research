# Agentic Classroom — Milestone 1

**XVF3800 is the V1 canonical audio front end.** Start without hardware using `backend/.venv/bin/python -m backend --profile simulation-basic` (Windows: `backend/.venv/Scripts/python.exe`). See [audio architecture](docs/AUDIO_FRONTEND.md), [Mac setup](docs/SETUP_MAC.md), and [Windows setup](docs/SETUP_WINDOWS.md).

A local-first simulated classroom AV control system for the CHI user study.

## What Milestone 1 includes

- Four simulated AV subsystems: **camera, display, audio, recording**
- Three experimental conditions: **Manual, Assistive, Autonomous**
- Parallel room state: session, activity, device state, system health
- Data-driven normalized sensor timelines and controlled study errors
- `FakeAgent` for deterministic development and study rehearsal
- `OllamaAgent` for a real local Qwen agent
- Delegation policy layer between AI decisions and device execution
- Participant UI + Researcher Console; study hides technical controls by default
- JSONL study logging
- Normalized trial recording/replay and persistent JSONL event logs
- Hardware adapters intentionally abstracted so simulated devices can later be replaced by PJLink / ONVIF / OBS / audio implementations without changing the agent

## Recommended local model

Default: `qwen3:8b` via Ollama (Q4_K_M, ~5.2 GB download).
No alternate model is selected unless explicitly configured.

The model is **not** allowed to emit raw hardware commands. It can only select registered intent-level tools such as `camera_focus`, `display_set_source`, `audio_set_mode`, and `recording_set_layout`.

## Start without hardware

Simulation is a supported product/research mode, not a temporary placeholder. Every developer can contribute without owning physical AV hardware. See [simulation profiles, scenarios and replay](docs/SIMULATION.md).

From the repository root on macOS:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend --profile simulation-basic
```

Windows PowerShell:

```powershell
py -3.12 -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python.exe -m backend --profile simulation-basic
```

In another terminal: `cd frontend`, `npm ci`, `npm run dev` (Node 22+). Open `http://localhost:5173`. API documentation: `http://localhost:8000/docs`.

For real Qwen with simulated sensors/devices, install Ollama, run `ollama pull qwen3:8b`, then use `--profile simulation-ai`. No Fake fallback in this profile. Clear incompatible AGENT_BACKEND overrides from backend/.env or the environment. For controlled participant presentation use `--profile study`; append `?researcher=1` to the UI URL for researcher controls.

Profiles: **simulation-basic**, **simulation-ai**, **hybrid**, **hardware**, **study**. Runtime profile and study authority are independent. Hybrid independently selects each adapter through configuration; absent/unimplemented hardware returns unavailable rather than successful simulated readback.

## Study conditions

### Manual
The AI does not recommend or execute AV actions. The participant operates the four subsystems directly.

### Assistive
The agent interprets the classroom state and returns recommendations. The participant must **Apply** or **Dismiss** them.

### Autonomous
The same agent decisions are executed automatically after the delegation/safety layer validates them. The participant can **Undo** or **Take Control**.

The sensing/state inputs are identical between conditions. Only authority changes.

## Included scenarios

- `lecture`
- `student_question`
- `media_playback`
- `demonstration`
- `side_conversation`
- `discussion`
- `controlled_wrong_qna` — intentionally mislabels a side conversation as Q&A for the study failure condition
- `reset`

## Architecture

```text
Simulated / future real sensors
          │
          ▼
    Structured Room State
          │
          ▼
    FakeAgent / OllamaAgent
          │ intent-level actions
          ▼
      Delegation Policy
          │
          ▼
 Deterministic Device Adapters
   camera/display/audio/recording
          │
          ▼
   Simulated devices (M1)
   Real APIs later (PJLink/ONVIF/OBS/...)
```

## Important study design property

Do **not** build separate apps for the three conditions. They use the same backend, state, simulator, agent interface, UI shell, and device adapters. The experimental condition only changes the authority policy.

## Milestone 1 acceptance test

1. Start backend + frontend.
2. Select `Manual`, inject `student_question`: nothing should happen automatically.
3. Select `Assistive`, inject `student_question`: a recommendation should appear; Apply changes camera/audio/layout, Dismiss does not.
4. Select `Autonomous`, inject `student_question`: allowed actions should execute immediately and be logged.
5. Inject `controlled_wrong_qna`, then press Undo / Take Control.
6. Restart with `--profile simulation-ai` and confirm the same UI works with Qwen3 8B.
7. Inspect `backend/data/study_events.jsonl` and verify the complete event trace exists.

## Next milestone

Extend normalized trial regression coverage and verify calibrated live XVF/camera observations through the shared estimator. ODAS and Silero are optional research adapters, not the normal V1 path.

## Local stack and agent handoffs

Start with [AGENTS.md](AGENTS.md), [current state](docs/CURRENT_STATE.md), and [architecture](docs/ARCHITECTURE.md).
Exact setup: [Apple Silicon](docs/SETUP_MAC.md) or [Windows/NVIDIA](docs/SETUP_WINDOWS.md).
Model versions, licenses and verification: [MODELS](docs/MODELS.md), [manifest](config/models.yaml).

```bash
python scripts/bootstrap_models.py --secondary
python scripts/check_ai_stack.py
python scripts/environment_report.py
python scripts/benchmark_ai_stack.py --image path/to/frame.jpg
```

Run perception checks using the optional perception environment. Missing optional components are reported without disabling the simulator. `AGENT_BACKEND=rule` selects the deterministic rule baseline. The explicit simulation profile uses FakeAgent; the no-profile configuration also defaults to simulation-basic. Test with `cd backend && python -m pytest -q`; the dedicated `python scripts/check_room_agent.py` requires real Ollama and disables fallback.

See [initial audit](docs/INITIAL_AUDIT.md) for original discrepancies, [decisions](docs/DECISIONS.md) for changes, and [handoffs](docs/HANDOFFS/) for session records. No real AV devices are connected.

## Cross-platform audio profiles

Configuration order is shared defaults → platform → ignored `config/local.yaml` → explicit launch profile → environment overrides. Copy `config/local.example.yaml` for local hardware settings; never commit device indices or personal paths. Profiles: `simulation-basic`, `simulation-ai`, `hybrid`, `hardware`, `study`. Legacy simulation/mac-local/windows-local/hardware-xvf names remain compatibility aliases. Study authority remains independent of hardware/platform. Real XVF audio can be mixed with simulated camera/display/recording; other real AV adapters remain deferred.

```bash
python scripts/bootstrap_xvf3800.py
python scripts/doctor.py --profile hardware-xvf
python -m backend --profile hardware-xvf
```

Install hardware dependencies only when needed (see platform guides). `/api/audio` reports normalized observations and availability. Unknown speech thresholds and uncalibrated geometry are explicitly reported. Without XVF hardware use simulation; no default ODAS or Silero installation is needed.
