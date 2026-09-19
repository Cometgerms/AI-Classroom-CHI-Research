# Current state — 2026-09-19

**Simulation is a supported product/research runtime.** Developers do not need physical AV hardware. Profiles: simulation-basic, simulation-ai, hybrid, hardware and study. Manual / Assistive / Autonomous authority is independent of profile. Start with [simulation reference](SIMULATION.md), [Mac setup](SETUP_MAC.md), or [Windows setup](SETUP_WINDOWS.md).

**Works:** normalized sensor timelines and replay → geometric speaker fusion → sustained state estimator → Fake/Rule/strict local Qwen → delegation/safety → simulated AV. Fifteen data-driven scenarios include all requested ordinary events and controlled wrong-Q&A/camera/display/audio plus device failure. Injection metadata is logged internally and omitted from participant presentation. Study UI hides researcher controls/debug information; ?researcher=1 shows them. Core startup needs no hardware packages or Ollama.

**Adapters:** XVF3800 remains canonical V1 audio, with separate UAC and read-only telemetry. Real/sim audio and camera use identical contracts. Hybrid independently selects sensing and output subsystems; live observations feed the shared pipeline. Real camera capture is lazy and explicitly configured. Physical PJLink/PTZ/OBS/audio output are unavailable placeholders, never successful simulated substitutes. Physical threshold/geometry defaults remain uncalibrated.

**Models:** actual Qwen3:8b/Ollama 0.33.2 on M1 Max/64 GiB passed strict simulation-ai full-loop smoke in all three authority conditions. Existing whisper.cpp Metal/small.en, optional YOLO/VLM and prior XVF audit remain intact. No accessible XVF was found; no physical camera capture/AV verification was performed. Windows/CUDA remain unverified locally.

**Replay:** versioned normalized trial tapes include initial simulated devices, virtual calibration and controlled injections. Replay preserves current participant/authority for comparisons. GET/POST /api/replay and scripts/replay_trial.py support export/recovery from persistent JSONL. Full arbitrary participant-session action reenactment is not implemented. Qwen replay re-infers; Fake is deterministic.

**Verification:** **95 passed, 1 hardware-optional deselected**; frontend build passed (dependency directive warnings); study participant/researcher browser checks passed; strict actual Qwen three-condition smoke passed twice; doctor Simulation basic/AI READY, XVF hybrid/Full hardware NOT READY. Three-OS CI configured, not remotely run. Source syntax, tape extraction and whitespace checks passed.

**Limits:** single in-memory session; one evaluation per scenario trial; individual-action undo; no client recommendation-ID binding; researcher toggle is local presentation, not authentication. Hybrid still needs upstream scene semantics/STT, physical calibration and hardware validation. No physical projector/PTZ integration was started.

**Next:** extend scripted trial/Qwen regression coverage, then validate calibrated XVF/camera hybrid data through the shared pipeline. Preserve hardware-free CI and simulation as permanent supported modes.

**Latest handoff:** [2026-09-19_1535_supported-simulation-runtime.md](HANDOFFS/2026-09-19_1535_supported-simulation-runtime.md). Earlier handoffs are immutable. This work and the earlier XVF refactor remain uncommitted.
