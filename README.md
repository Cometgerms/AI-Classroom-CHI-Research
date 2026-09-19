# Agentic Classroom

A local-first classroom-control application for instructors. See what the room is doing, choose **AI Mode: Off / Assist / Auto**, and change camera, display, audio or recording without interrupting teaching.

**Research tooling is preserved but temporarily frozen while the instructor-facing product interaction is developed.** The protected CHI V1 scope remains instructor/TA-only: one participant, one facilitator, no students or student actors.

## Start the product

Primary development on the M1 Max uses real local Qwen with simulated physical devices:

```bash
# Repository root; Python 3.12, Node 22+, Ollama installed/running
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
ollama pull qwen3:8b
backend/.venv/bin/python -m backend --profile simulation-ai
```

Separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Clear conflicting legacy AGENT_BACKEND overrides if present. The convenience backend launch scripts default to simulation-ai. For development/CI without Ollama or hardware, explicitly select `--profile simulation-basic`.

Windows PowerShell uses `py -3.12 -m venv backend/.venv` and `& backend/.venv/Scripts/python.exe -m backend --profile simulation-ai`; the frontend commands are identical. Full setup: [Mac](docs/SETUP_MAC.md), [Windows](docs/SETUP_WINDOWS.md).

## Instructor interaction

- **Off:** you control the room. **Assist:** approve or ignore a suggestion. **Auto:** validated routine changes happen automatically; Undo and Take Control remain available.
- Camera: Presenter, Demo area, Wide, Follow presenter.
- Room display: Instructor laptop, Room PC, Camera/program, Blank.
- Audio: Presentation, Media, Mute.
- Recording: explicit start/stop and elapsed timer, with a separate program layout.
- Recent actions: concise device changes with AI/you indicators and safe latest-action undo.
- Devices and Settings: availability, local defaults and separate advanced diagnostics.

Program preview is an explicitly labelled illustration until a live video engine is connected. Simulated recording does not save video. Take Control never implicitly stops recording or resets the display. Manual controls do not depend on Qwen availability. Disconnected physical adapters never fabricate success.

Routes: `/` classroom, `/devices`, `/settings`, `/dev` diagnostics. Existing study/research tools are retained separately at `/research`; they are not exposed by query flags on the main dashboard. [Product behavior, settings and limitations](docs/PRODUCT.md).

## Shared architecture

Normalized real/simulated/replay observations → shared state engine → RoomAgent → delegation/safety → semantic device adapters. AI/hardware modes remain independent across simulation-basic, simulation-ai, hybrid and hardware. A `VideoEngine` interface owns composition, recording and preview: SimVideoEngine works now; OBSVideoEngine honestly reports disconnected until its transport/readback is implemented. Physical protocols are the next milestone, not a prerequisite for this UI.

XVF3800 remains the canonical audio front end. DoA, student tracking and multi-person fusion are not prerequisites for instructor-only V1. Simulation remains a supported product mode with no hardware ownership requirement. Research models/routes/logging/replay/scenarios/injections are preserved.

## Verification and documentation

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm run build)
backend/.venv/bin/python scripts/doctor.py --profile simulation-ai
backend/.venv/bin/python scripts/check_simulation_ai.py
```

[Current state](docs/CURRENT_STATE.md) · [Architecture](docs/ARCHITECTURE.md) · [Decisions](docs/DECISIONS.md) · [Handoffs](docs/HANDOFFS/) · [Models](docs/MODELS.md) · [Simulation/replay](docs/SIMULATION.md) · [Preserved study protocol](docs/STUDY_V1.md).

Start coding-agent work with [AGENTS.md](AGENTS.md). Keep local settings, weights, recordings and private logs out of Git.
