# Local model bootstrap — 2026-09-19, America/New_York (EDT)

## Goal

Inspect the complete existing prototype before editing; establish shared-agent documentation; install and verify local models while preserving Manual/Assistive/Autonomous and deterministic simulation. No real AV integration.

## Completed

- Read all initial source/config/docs, including .env.example and LICENSE. Recorded pre-change discrepancies in INITIAL_AUDIT. Preserved existing modified README and untracked source; no commits or destructive cleanup.
- Created AGENTS, architecture/current-state/model/platform docs, append-only decisions, immutable handoff convention, model manifest and ignore rules.
- Installed exact Qwen3 8B and Qwen3-VL 2B Instruct tags into existing Ollama; verified actual inference, including JSON and tools. Retained FakeAgent unchanged. Added RuleAgent selection and kept OllamaAgent on the same RoomAgent interface. Removed default silent qwen3:4b substitution; explicit fallback setting remains available.
- Closed action argument validation, denied AI recording transport, guarded in-flight inference against authority/state changes, cleared stale recommendations, guarded Apply with Assistive authority, limited Undo restoration to devices.
- Built whisper.cpp with Metal and downloaded small.en. Installed isolated Silero/Ultralytics stack and nano weights. Added optional STT/VAD/person/tracker/pose/sound/semantic vision services, temporal estimator contract and isolated digital crop director. None opens microphones/cameras or connects hardware.
- Added cross-platform bootstrap/wrappers, stack inference check, strict live RoomAgent/API check, allowlisted environment report, lightweight benchmark and version snapshots. Added missing Vite CSS type declaration and npm lockfile. Corrected README's unsupported replay/hidden-console claims.

## Files Changed

AGENTS.md; .gitignore; README.md; docs/{INITIAL_AUDIT,ARCHITECTURE,CURRENT_STATE,DECISIONS,MODELS,SETUP_MAC,SETUP_WINDOWS}.md; docs/HANDOFFS/README.md; config/{models.yaml,perception-requirements.txt,perception-macos.lock.txt}; backend/requirements*.txt; backend/.env.example; backend/app/{models,safety,delegation,devices,state_store,orchestrator,main,config}.py; backend/app/agent/{ollama,factory,rule}.py; backend/app/services/; backend/tests/test_invariants.py; scripts/{ai_common,bootstrap_models,check_ai_stack,check_room_agent,environment_report,benchmark_ai_stack}.py; platform bootstrap wrappers; frontend/package-lock.json; frontend/src/vite-env.d.ts; artifacts/*.json.

## Models / Dependencies

- Existing Ollama 0.33.2 retained, not reinstalled. Existing llama3.1:latest untouched.
- qwen3:8b digest 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41, 5.225 GB.
- qwen3-vl:2b-instruct digest ea422f1e73652a95479954d8572d3c8c6022f628ce2d38a1a04aae1b7f2d5300, 1.890 GB.
- whisper.cpp 1.9.4-dev commit 5670d5c0bbcb148feabef84400a07cfca9aa3b30, Metal build, small.en. Weights SHA-256 and bytes in manifest.
- Isolated backend Python 3.12.13 venv and separate perception venv. Ultralytics 8.4.155, Silero 6.2.2, Torch 2.9.1, ONNX Runtime 1.30.0, lap 0.5.13. Full package snapshots checked in, weights ignored.
- Homebrew Node 22.23.2 and CMake installed (with brew dependencies). npm packages installed with generated lockfile.
- ODAS skipped after upstream CMake inspection: mandatory ALSA/PulseAudio make native Mac setup nontrivial. Build route documented for Linux/WSL2.

## Commands Run

- Initial `python3 -m pytest backend/tests`: failed because system Python lacked pytest.
- `python3.12 -m venv backend/.venv`; pip install backend requirements + pytest-asyncio; baseline `cd backend && .venv/bin/python -m pytest -q`.
- `ollama --version`; `ollama list`; `ollama pull qwen3:8b`; `ollama pull qwen3-vl:2b-instruct`.
- `brew install node@22 cmake`; frontend `npm install`, `npm run build`.
- Optional venv pip install Ultralytics/Silero/lap, then onnxruntime after first VAD failure.
- Clone whisper.cpp, CMake configure with GGML_METAL=ON, build, download small.en into models/whisper.
- `scripts/bootstrap_models.py --secondary --perception` twice; second run reused all weights.
- `scripts/check_ai_stack.py`; `scripts/check_room_agent.py`; `scripts/environment_report.py` with backend Python and Node on PATH.
- `scripts/benchmark_ai_stack.py --image artifacts/private/vision-proxy.jpg` (public Ultralytics bus image). Final numbers use this frame for VLM too.
- Launched uvicorn and Vite on temporary ports 18000/15173; both HTTP 200; stopped both after check. No persistent app server intentionally left running.

## Tests

- Baseline: 4 passed after installing dependencies; no baseline application failures.
- Final backend: **22 passed**, including three-condition API behavior, no unapproved Assistive execution, stale slow-inference rejection after Take Control, validation, participant-only recording, Fake fallback, safe Undo, estimator sustain, digital crop fallback and malformed Ollama response rejection.
- Strict real Ollama integration: Manual/Assistive/Autonomous all PASS; fallback disabled; report artifacts/room_agent_integration.json.
- Stack: Ollama, both Qwen tags, whisper.cpp, small.en transcription, Silero silence AND started/active/ended speech events, Ultralytics and both YOLO models PASS. ODAS SKIPPED.
- Frontend production build PASS after adding vite/client CSS types; nonblocking lucide-react 'use client' bundler warnings.
- Backend and frontend launch/HTTP smoke PASS. No manual browser interaction or Windows execution claimed.
- Compilation PASS with AppleDouble sidecars excluded. Broad compileall initially failed on `._*.py` metadata (null bytes), not application sources.
- `git diff --check` clean; ignored model binaries/venvs/vendor/cache media are absent from git's candidate file list.
- Setup failures resolved: initial Whisper download path absent (created directory), missing ONNX Runtime, CSS side-effect declaration.

## Current Runtime State

Ollama remains running as before. All requested local models are downloaded and tested on M1 Max/64 GiB. Backend runs from backend/.venv, fake by default; run scripts create .env from example if missing. `AGENT_BACKEND=ollama` enables local Qwen; `rule` selects deterministic rules. Frontend runs using Node 22 (Homebrew keg-only path must be exported). Optional inference runs from .venv-perception; it is not loaded by simulator startup. Refer to exact launch commands in SETUP_MAC/SETUP_WINDOWS.

## Known Issues

Single process/session; no replay endpoint; researcher console initially visible; Undo is one tool, not a whole AI action batch. Approval endpoint acts on current pending recommendation without a client-supplied ID. No continuous perception ingestion, audio/vision association, room calibration, physical AV adapters, independent device acknowledgements, or real ODAS. Temporal estimator and digital crop code are isolated foundations, not deployed sensing. Windows/CUDA unverified. VLM/YOLO smoke fixtures do not establish classroom accuracy.

External filesystem generates AppleDouble metadata, causing pip invalid-distribution and vendor-git index warnings; imports/build/tests passed. Prefer APFS for environments if this becomes disruptive. No personal identifiers or absolute paths in committed reports.

## Decisions Made

See four dated entries in DECISIONS.md: preserve study baseline; deterministic validation and stale-inference invalidation; isolate optional stack and exact requested models; defer ODAS native port and physical camera control. These decisions do not alter the three study conditions.

## Next Recommended Actions

1. On Windows, run SETUP_WINDOWS and generate machine-specific check/benchmark/environment artifacts; verify CUDA explicitly.
2. Add a timestamped observation replay fixture and ingestion path feeding the estimator, with VAD-gated STT and explicit ambiguity-triggered VLM. Preserve existing controlled scenario injection.
3. Before participant sessions, tighten recommendation-ID binding, UI error display/research console visibility, and decide whether study protocol requires batch undo and durable replay.
4. Calibrate zones/identity and validate digital camera framing before any physical AV integration.

## Do Not Assume

Downloaded tags are mutable; compare recorded digests. Mac lockfiles are not Windows CUDA lockfiles. Benchmark is one run, model-unloaded cold start with OS caches retained: ~18.74 tokens/s, 1.48 s first token, 1.67 s tool call; VLM 2.81 s on proxy image; Whisper RTF .056; YOLO CPU 26.8 FPS. These are not study outcomes. No Windows measurements, classroom accuracy evaluation, Core ML install, live microphone/camera, or physical AV verification occurred. Do not change scenario labels to match model output or silently replace models.
