# Current state — 2026-09-19

**Works:** FastAPI/React simulator with unchanged FakeAgent, selectable RuleAgent/OllamaAgent, strict intent validation and stale-inference rejection. Manual disables AI; Assistive requires Apply; Autonomous executes permitted actions with Undo/Take Control. Same state/tools/devices/UI across conditions.

**Simulated:** all AV devices, scenario observations/activity, controlled wrong-Q&A, device readback. Optional temporal estimator and digital crop director are tested but not wired into the UI pipeline.

**Real:** local model inference only. M1 Max/64 GiB, Ollama 0.33.2; qwen3:8b and qwen3-vl:2b-instruct downloaded/verified. whisper.cpp 1.9.4-dev Metal + small.en, Silero 6.2.2, Ultralytics 8.4.155 + yolo26n/yolo26n-pose verified in isolated environment. No real AV or sensor capture. ODAS skipped due native platform dependencies.

**Known issues:** one in-memory session/process, no replay, individual-action undo, console visible by default, approval lacks client recommendation-ID binding, no calibrated perception ingestion. Windows/CUDA not yet verified. External-drive AppleDouble metadata produces tooling warnings; see setup guide. Smoke/benchmark fixtures do not prove classroom accuracy.

**Next milestone:** Windows stack verification, then timestamped observation replay feeding the estimator and VAD-gated STT, preserving deterministic study scenarios.

**Last verified:** baseline 4 tests; final **22 passed**. Frontend build and both server launch checks passed. Strict real Ollama API checks passed all three conditions. All installed stack components passed inference; ODAS SKIPPED. Bootstrap repeat passed without re-download. Reports/benchmarks in artifacts; exact launch/install commands in SETUP_MAC.md and SETUP_WINDOWS.md. Ollama running; temporary app servers stopped.

**Latest handoff:** [2026-09-19_1432_local-model-bootstrap.md](HANDOFFS/2026-09-19_1432_local-model-bootstrap.md). Model versions/digests in MODELS.md and config/models.yaml.
