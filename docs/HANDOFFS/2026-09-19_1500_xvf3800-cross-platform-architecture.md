# XVF3800 cross-platform architecture — 2026-09-19, America/New_York (EDT)

## Goal

Make XVF3800 the canonical V1 audio front end; retain hardware-free simulation and common Mac/Windows code, shared models, and three study conditions. Refactor audio, configuration, diagnostics, tests and setup documentation without physical projector/PTZ work.

## Completed

- Read required docs/latest handoff and current audio/perception/configuration code; baseline 22 tests passed. Recorded conflicts before changes in XVF3800_AUDIT.md.
- Added AudioFrontEnd, normalized AudioObservation/AudioStatus, SimAudioFrontEnd, XVF3800AudioFrontEnd and read-only official Python control wrapper. Four beam directions/energies remain adapter diagnostics; normalized output selects auto beam. Radians → calibrated [-180,180) degrees with local offset/inversion; unknown confidence stays null.
- Split UAC capture (PortAudio/sounddevice) from USB control. Unique name/API matching and actual reported input profile discovery; no assumed 48 kHz, no committed device indices. Fresh bounded capture can feed SpeechToText via processed-channel selection and anti-aliased mono 16 kHz PCM16 conversion. Temporary WAV is removed.
- Added configurable threshold/onset/release classifier. Threshold null is explicitly uncalibrated, never guessed. Existing Silero and ODAS abstractions preserved as optional research paths; removed Silero from default perception requirements/checks. No normal ODAS runtime.
- Added locally calibrated image-x→azimuth mapping, circular smoothing and ActiveSpeakerFusion with temporal confirmation, angular tolerance, tie rejection and stale/no-speaker handling. Role comes from supplied track metadata. Bridge accepts existing normalized person tracking output; no LLM geometry.
- Added default/platform/local/profile/environment configuration, ignored local.yaml/example, profiles and cross-platform launcher. Explicit launch profiles override local choices; environment is highest. Shared Qwen3:8b, whisper.cpp small.en. Vision accelerator factory reports CPU fallback rather than changing model.
- FastAPI audio lifespan collects normalized observations and exposes /api/audio. Hardware sensing and study authority remain separate. Sensor polling does not continuously mutate study state or invoke LLMs; live calibrated camera ingestion and event-to-estimator integration remain next steps.
- Added pinned XVF bootstrap, doctor, explicit capture/STT smoke script, telemetry/synthetic state-action benchmark, marked hardware test and Linux/macOS/Windows core CI workflow.
- Updated AGENTS, architecture, decisions, models, README and platform setup docs. Full contract details in AUDIO_FRONTEND.md. This session did not commit or push changes.

## Files Changed

Important new files: backend/__main__.py; backend/app/runtime_config.py; backend/app/services/audio/**; backend/app/services/active_speaker.py; backend/app/services/vision/factory.py; backend/tests/test_audio_frontend.py; backend/pytest.ini; config/default.yaml; config/platform/*; config/profiles/*; config/local.example.yaml; config/audio-requirements.txt; config/audio-macos.lock.txt; config/research-vad-requirements.txt; scripts/{bootstrap_xvf3800,doctor,capture_xvf_stt,benchmark_xvf3800}.py; docs/{XVF3800_AUDIT,AUDIO_FRONTEND}.md; .github/workflows/tests.yml.

Updated: backend/app/{config,main}.py; backend/requirements.txt; config/{models.yaml,perception-requirements.txt}; scripts/{bootstrap_models,check_ai_stack}.py; run-backend Mac/Windows wrappers; .gitignore; AGENTS.md; README; architecture/decisions/models/platform docs; stack report and new doctor/benchmark reports.

## Models / Dependencies

XVF official upstream: https://github.com/respeaker/reSpeaker_XVF3800_USB_4MIC_ARRAY
Pinned host-control commit: **a652fe79da3a292b25decc0e1e7f267d29bb0284**. Official python_control/xvf_host.py downloaded under ignored vendor/xvf3800; SHA-256 pinned in control.py and checked on download/load. Persistent in-process read-only wrapper uses bundled libusb; no opaque vendor binaries committed and no firmware flash/write performed.

Installed sounddevice 0.5.6, PyUSB 1.3.1, libusb-package 1.0.30.0, NumPy 2.5.3, SciPy 1.18.1 with their dependencies; exact audio snapshot in config/audio-macos.lock.txt. Added core/audio packages to existing optional .venv-perception so it can run full local software/doctor in one interpreter. Backend venv also has audio packages for this session's conversion tests, but core requirements do not require them. PyYAML is now an explicit core dependency (already installed transitively before).

Existing Ollama 0.33.2, qwen3:8b, qwen3-vl:2b-instruct, whisper.cpp Metal/small.en, YOLO nano/pose remain available and unchanged. Existing optional Silero installation retained, no longer default. No new neural model downloads or ODAS installation.

## Commands Run

- Baseline and final: `cd backend && .venv/bin/python -m pytest -q`.
- Hardware deps: `backend/.venv/bin/python -m pip install -r config/audio-requirements.txt`.
- Full optional runtime: `.venv-perception/bin/python -m pip install -r backend/requirements.txt -r config/audio-requirements.txt`.
- `python scripts/bootstrap_xvf3800.py` (source PASS; VERSION/DoA/energy UNAVAILABLE, expected exit 2); repeated `--download-only` PASS without replacement.
- `.venv-perception/bin/python scripts/doctor.py --profile hardware-xvf`.
- `.venv-perception/bin/python scripts/check_ai_stack.py --v1`.
- `backend/.venv/bin/python scripts/benchmark_xvf3800.py --hardware`.
- `backend/.venv/bin/python scripts/check_room_agent.py` (strict real Qwen3).
- Launch smoke: `python -m backend --profile simulation --port 18000` and `--profile hardware-xvf --port 18001`; GET /api/audio HTTP 200 for both, temporary servers stopped.
- `python -m compileall -q -x '/\._' backend/app scripts backend/__main__.py`; `git diff --check`.

## Tests

**55 passed, 1 hardware test deselected** on macOS Python 3.12.13. Baseline 22 unchanged tests still pass. Tests cover DoA/energy parsing (Python/native output), malformed values, offset/inversion, onset/release, disconnect, simulated/real normalized contract, fusion smoothing/no-speaker/ties/staleness/circular angles, UAC 16/48 kHz discovery/ambiguity, STT conversion, config precedence, mocked platform parity, simulation without optional imports, read-only USB boundary, accelerator fallback and runtime lifecycle. Optional conversion test skips cleanly when NumPy/SciPy are absent.

Strict real Ollama three-condition API test: all PASS. V1 host inference: Ollama/Qwen3/Whisper/YOLO PASS, optional VLM/pose also PASS; Silero/ODAS SKIPPED by default. Compilation and whitespace checks PASS. New CI matrix is configured but has not executed remotely. Frontend source unchanged; no new UI build/browser test was necessary.

Doctor on full optional runtime: MPS PASS; CUDA unavailable (expected on Mac); Ollama/model/Whisper/YOLO PASS; one camera enumerated (capture not opened); **no matching XVF UAC or USB control device accessible**. Simulation and AI simulation prerequisites YES; XVF/full perception readiness NO. Reports persist no device names, paths or identifiers.

## Current Runtime State

Core: `backend/.venv/bin/python -m backend --profile simulation`. Full optional software: `.venv-perception/bin/python -m backend --profile mac-local` or hardware-xvf. Same web UI/API. /api/audio returns live normalized sensor state separately from controlled scenario state. Hardware profile starts gracefully when devices are absent and reports absence; it does not fabricate a simulated hardware success. Local config was NOT created; developers should copy/edit the example themselves.

No microphone recording or camera capture was performed. Only enumeration/read-only control probes were attempted; XVF absent. No automatic STT loop or live vision capture loop has been wired. Existing Ollama service remains; temporary app servers stopped.

## Known Issues

- Physical XVF VERSION, DoA, energy, UAC routing/capture, calibration and telemetry latency require an attached array. Firmware behavior and Windows drivers are unverified.
- Speech threshold null and calibration.calibrated false intentionally prevent ungrounded active-speaker claims. Do not invent defaults from one room's noise.
- Upstream Python control retries up to 100 times; with 100 ms transfer timeout, a stalled command can delay stop roughly 11 seconds. Polling is serialized; benchmark actual attached device before tuning. UAC reconnect currently needs profile restart.
- Full continuous camera→fusion→state-estimator ingestion is not yet wired; update_people/update_tracks provide the seam. /api/audio collection doesn't mutate scenario labels or continuously invalidate inference. Synthetic benchmark supplies explicit Q&A floor-yield context.
- Real camera/projector/recorder adapters are intentionally unsupported; XVF sensing + simulated AV output is the supported hybrid. Participant audio actions remain simulated AV modes, not XVF DSP writes.
- Prior single-process/session, individual-tool undo, recommendation-ID binding and replay/UI issues remain.
- External-drive AppleDouble warnings persist in pip; dependencies import/tests pass. All sidecars/caches/vendor content ignored.

## Decisions Made

Appended canonical hardware rationale and consequences, then config/sensor boundary decision. A follow-up entry explicitly supersedes initial profile-before-local precedence: **default → platform → local → explicit launch profile → environment**. This guarantees explicit simulation escapes a local hybrid configuration. Prior handoffs/decisions were not rewritten.

## Exact Windows Setup Commands

PowerShell from repo root, after Python 3.12 / Git / Node 22 / Ollama installation:

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
& backend/.venv/Scripts/python.exe -m backend --profile simulation
# Stop server, then optional full runtime (choose compatible CUDA Torch wheels first):
py -3.12 -m venv .venv-perception
& .venv-perception/Scripts/python.exe -m pip install -r backend/requirements.txt -r config/audio-requirements.txt -r config/perception-requirements.txt
& .venv-perception/Scripts/python.exe scripts/bootstrap_models.py --perception
& .venv-perception/Scripts/python.exe scripts/bootstrap_xvf3800.py
if (!(Test-Path config/local.yaml)) { Copy-Item config/local.example.yaml config/local.yaml }
& .venv-perception/Scripts/python.exe scripts/doctor.py --profile windows-local
& .venv-perception/Scripts/python.exe -m backend --profile windows-local
```

Whisper CUDA build/model commands and local config examples are in SETUP_WINDOWS.md. UAC and USB control can need different Windows drivers. Follow official Seeed Zadig/WinUSB guidance for the vendor-control interface; do not overwrite working audio interfaces indiscriminately. Microphone desktop-app permission is separate. The native win32 package is an optional manual diagnostic, not a dependency of shared room code. Simulation/non-hardware tests work without all of this.

## Next Recommended Actions

1. Attach XVF to the current Mac, run bootstrap/doctor, verify actual firmware/UAC profile and processed channel, then explicitly test capture_xvf_stt.
2. Measure speech energy under idle/speech/noise, set threshold and tune timing. Calibrate physical azimuth offset/inversion and camera mapping; confirm active-speaker matches with scripted multi-person fixtures.
3. Run Windows instructions, verify control driver alongside functioning UAC and actual CUDA inference; save separate sanitized reports/benchmarks. Run the new CI matrix.
4. Wire a calibrated camera track producer and debounced normalized event-to-estimator projection, preserving controlled scenarios/authority. Measure real total latency before any physical PTZ/projector work.

## Do Not Assume

A downloaded host package is not a connected device. No true hardware benchmark or live XVF inference passed. Reported ~1.95 ms state-change-to-action is a synthetic FakeAgent/simulated path, not classroom end-to-end latency. Do not equate positive energy to perfect VAD, attach a probability to DoA without evidence, or infer a person's full location from azimuth. Do not commit local calibration, device indices, names/serials, audio recordings or vendor binaries. Shared model names remain identical across platforms; a configured GPU preference is not proof of acceleration.
