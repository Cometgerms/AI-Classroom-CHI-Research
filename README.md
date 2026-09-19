# Agentic Classroom — Milestone 1

A local-first simulated classroom AV control system for the CHI user study.

## What Milestone 1 includes

- Four simulated AV subsystems: **camera, display, audio, recording**
- Three experimental conditions: **Manual, Assistive, Autonomous**
- Parallel room state: session, activity, device state, system health
- Scenario injection for controlled study events
- `FakeAgent` for deterministic development and study rehearsal
- `OllamaAgent` for a real local Qwen agent
- Delegation policy layer between AI decisions and device execution
- Participant UI + toggleable Researcher Console (visible by default)
- JSONL study logging
- Recent-event log endpoint (session replay is not implemented)
- Hardware adapters intentionally abstracted so simulated devices can later be replaced by PJLink / ONVIF / OBS / audio implementations without changing the agent

## Recommended local model

Default: `qwen3:8b` via Ollama (Q4_K_M, ~5.2 GB download).
No alternate model is selected unless explicitly configured.

The model is **not** allowed to emit raw hardware commands. It can only select registered intent-level tools such as `camera_focus`, `display_set_source`, `audio_set_mode`, and `recording_set_layout`.

## 1. Install Ollama and pull the model

Install Ollama from https://ollama.com/download, then:

```bash
ollama pull qwen3:8b
ollama run qwen3:8b
```

Press Ctrl-D / Ctrl-C after confirming the model responds. Ollama normally serves its local API at `http://localhost:11434`.

Also bootstrap the optional vision model with `python scripts/bootstrap_models.py --secondary`.

Helper scripts are included in `scripts/`.

## 2. Backend

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\\Scripts\\activate       # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` to inspect the API.

### Agent backend

In `backend/.env`:

```env
AGENT_BACKEND=fake
```

uses deterministic development behavior.

To use Qwen locally:

```env
AGENT_BACKEND=ollama
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434
```

The backend automatically falls back to the FakeAgent if Ollama is unavailable unless `OLLAMA_STRICT=true`.

## 3. Frontend

Requires Node 20+.

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

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
6. Switch `AGENT_BACKEND=ollama` and confirm the same UI works with Qwen3 8B.
7. Inspect `backend/data/study_events.jsonl` and verify the complete event trace exists.

## Next milestone

Replace simulated perception events with Silero/Whisper/ODAS/YOLO feeds while preserving the exact same room-state event schema.

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

Run perception checks using the optional perception environment. Missing optional components are reported without disabling the simulator. `AGENT_BACKEND=rule` selects the deterministic rule baseline. Fake remains the default. Test with `cd backend && python -m pytest -q`; the dedicated `python scripts/check_room_agent.py` requires real Ollama and disables fallback.

See [initial audit](docs/INITIAL_AUDIT.md) for original discrepancies, [decisions](docs/DECISIONS.md) for changes, and [handoffs](docs/HANDOFFS/) for session records. No real AV devices are connected.
