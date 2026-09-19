# Supported simulation — macOS

CHI V1 is an instructor/TA-only controlled teaching-task study: one participant and one facilitator, no students/actors. DoA calibration and student tracking are not prerequisites. See [study protocol](STUDY_V1.md).

Simulation is a permanent product/research mode. No physical AV hardware is needed to contribute. Python 3.12 and Node 22+ are sufficient for simulation-basic. From repository root:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend --profile simulation-basic
```

In a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. For real local Qwen, install/start Ollama and run `ollama pull qwen3:8b`; stop the backend and relaunch with `backend/.venv/bin/python -m backend --profile simulation-ai`. This profile is strict and never substitutes Fake. Clear conflicting AGENT_BACKEND entries from backend/.env/environment. For controlled study run `--profile study`; researcher UI is `http://localhost:5173/research`, preserved participant UI is /research?view=participant. Use `--profile hybrid` with independent adapter selections in ignored config/local.yaml. `--profile hardware` selects real devices and reports unavailable outputs honestly. Authority is selected separately in the researcher console.

```bash
backend/.venv/bin/python scripts/doctor.py --profile simulation-basic
backend/.venv/bin/python scripts/check_simulation_ai.py # requires Qwen/Ollama
(cd backend && .venv/bin/python -m pytest -q)
```

See [scenarios, contracts and replay](SIMULATION.md). The optional hardware/model instructions below do not apply to simulation-basic.

---

# XVF3800 V1 quick start — Apple Silicon

**XVF3800 is the V1 canonical audio front end.** ODAS/Silero are optional research adapters. These current instructions supplement the model/build details below. Run from repo root. No attached XVF was detected during this revision; live readings/capture need verification.

```bash
# Core, no microphone/camera/GPU dependencies:
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend --profile simulation-basic
# Or: bash scripts/run-backend-macos.sh simulation
```

For local perception development use one optional runtime with both core and hardware packages (existing .venv-perception may be reused):

```bash
python3.12 -m venv .venv-perception # skip if it already exists
.venv-perception/bin/python -m pip install -r backend/requirements.txt -r config/audio-requirements.txt -r config/perception-requirements.txt
.venv-perception/bin/python scripts/bootstrap_xvf3800.py
# Exit 2 means no accessible hardware/read failure; source acquisition can still succeed.
.venv-perception/bin/python scripts/bootstrap_models.py --perception
# Create local settings only if absent:
[ -f config/local.yaml ] || cp config/local.example.yaml config/local.yaml
.venv-perception/bin/python scripts/doctor.py --profile mac-local
.venv-perception/bin/python -m backend --profile mac-local
# Stop the backend before this explicit short microphone-capture test:
.venv-perception/bin/python scripts/capture_xvf_stt.py --seconds 3
.venv-perception/bin/python scripts/check_ai_stack.py --v1
.venv-perception/bin/python scripts/benchmark_xvf3800.py --hardware
(cd backend && .venv/bin/python -m pytest -q)
```

Example ignored local.yaml (threshold/calibration need measurements):

```yaml
runtime:
  platform: macos
  accelerator: auto
hardware:
  mode: hybrid
  audio: xvf3800
  camera: simulation
  projector: simulation
  recorder: simulation
audio:
  frontend: xvf3800
  device_match: reSpeaker 3800
  speech_activity:
    energy_threshold: null
    onset_ms: 150
    release_ms: 400
  xvf3800:
    azimuth_offset_deg: 0
    invert_azimuth: false
xvf3800:
  transport: usb
  host_control: auto
stt:
  backend: whisper_cpp
  acceleration: metal
vision:
  acceleration: mps
agent:
  backend: ollama
```

Explicit `--profile simulation-basic` overrides a hybrid local configuration. Environment overrides remain highest; clear stale AGENT_BACKEND or backend/.env values when debugging profile selection. `--profile hardware-xvf` is the equivalent generic hardware profile. Local config is gitignored, example config is shared; no indices/absolute paths need to be committed.

The preferred adapter imports the pinned official Python host and uses libusb-package's bundled libusb backend. If libusb cannot load, check wheel/architecture and install `brew install libusb` as a platform troubleshooting step; no personal dylib path is hard-coded. The official native alternative is `host_control/mac_arm64/`; retain its executable and all adjacent dylibs together if diagnosing it manually. The application does not invoke the native executable. Do not run the whole app with sudo to bypass errors.

macOS microphone permission belongs to the terminal/Python host application under System Settings → Privacy & Security → Microphone. Camera probing (`doctor --probe-camera`) may require Camera permission. Doctor otherwise enumerates only and does not record. Standard UAC audio and control telemetry are distinct: availability of one does not prove the other. No firmware flashing or parameter writes are performed.

Read [audio contracts/calibration](AUDIO_FRONTEND.md) and [official ReSpeaker guide](https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/). Discover the actual UAC profile; typical 16 kHz stereo and alternate 48 kHz firmware are not interchangeable assumptions. PortAudio host API filtering and a device-index override are local-only options if names are ambiguous. Calibrate energy/orientation/camera mapping before claiming active-speaker readiness.

Optional research VAD only: `.venv-perception/bin/python -m pip install -r config/research-vad-requirements.txt`, then set `audio.speech_activity_backend: silero` locally and run stack checks with `--research-vad`. This is never the default install path. ODAS remains a separate research experiment.

---

# Apple Silicon setup

Verified 2026-09-19: M1 Max, 64 GiB unified memory, macOS Darwin 25.5.0. Commands run from repository root unless specified. Python 3.12 avoids relying on optional ML wheel availability for system Python 3.14. Models/caches/vendor source are ignored by git.

## Core simulator and Ollama

Install Homebrew and Apple command-line tools if absent. Ollama was already installed/running here; version verified as 0.33.2. For another Mac use the [official installer](https://docs.ollama.com/macos) or Homebrew cask:

```bash
brew install python@3.12 node@22 cmake
# Only if Ollama is absent:
brew install --cask ollama
open -a Ollama
export PATH="/opt/homebrew/opt/node@22/bin:$PATH"
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-macos.lock.txt
python3.12 scripts/bootstrap_models.py --secondary
backend/.venv/bin/python scripts/check_room_agent.py
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm ci && npm run build)
# Separate terminals:
bash scripts/run-backend-macos.sh
bash scripts/run-ui-macos.sh
```

If using Intel Homebrew, adjust its prefix; this session only verified arm64. Keep `AGENT_BACKEND=fake` in backend/.env for deterministic study rehearsal; choose `ollama` or `rule` explicitly. Ollama is a separate loopback service; bootstrap checks its CLI/server and reports model download sizes before pulling missing tags. It never silently substitutes tags. `--secondary` adds Qwen3-VL. Rerunning skips existing tags.

## Optional perception

```bash
python3.12 -m venv .venv-perception
.venv-perception/bin/python -m pip install -r config/perception-requirements.txt
.venv-perception/bin/python scripts/bootstrap_models.py --secondary --perception
mkdir -p vendor models/whisper
# Clone once, then checkout the exact verified revision:
git clone https://github.com/ggml-org/whisper.cpp.git vendor/whisper.cpp
git -C vendor/whisper.cpp checkout 5670d5c0bbcb148feabef84400a07cfca9aa3b30
cmake -S vendor/whisper.cpp -B vendor/whisper.cpp/build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
cmake --build vendor/whisper.cpp/build --config Release -j 8
bash vendor/whisper.cpp/models/download-ggml-model.sh small.en models/whisper
.venv-perception/bin/python scripts/check_ai_stack.py
.venv-perception/bin/python scripts/environment_report.py
.venv-perception/bin/python scripts/benchmark_ai_stack.py --image path/to/representative-frame.jpg
```

Whisper adapter accepts mono 16 kHz 16-bit PCM WAV. Convert with `ffmpeg -i input.wav -ar 16000 -ac 1 -c:a pcm_s16le output.wav`. `WHISPER_CPP_BIN` and `WHISPER_MODEL` can override default paths. `base.en` is supported by the same adapter/download script but is not the selected model. `small.en` smoke check expects the default or an explicitly supplied compatible model.

Metal is enabled and tested. Core ML is optional and was not installed: upstream describes installing its conversion dependencies, running `models/generate-coreml-model.sh small.en` inside the whisper.cpp checkout, and rebuilding with `-DWHISPER_COREML=1`. Consult [upstream instructions](https://github.com/ggml-org/whisper.cpp#core-ml-support) before using that separate conversion environment; it is not needed for this setup.

No microphone or camera capture is started by any setup/check command. Benchmarks use an upstream speech sample and supplied image, not study recordings. The recorded YOLO benchmark used the Ultralytics bus image as a people-detection throughput proxy, not a classroom accuracy test.

## ODAS

Native build skipped after inspecting [upstream CMake](https://github.com/introlab/odas/blob/master/CMakeLists.txt): requires fftw3f, ALSA, libconfig and libpulse-simple. ALSA is a Linux dependency; this is not a straightforward native Mac build. A Linux machine/VM can use the Linux commands in SETUP_WINDOWS.md. Microphone-array geometry, multichannel routing and calibration remain unverified. The simulated tracker works without ODAS.

## Filesystem caveat

This checkout is on an external filesystem which creates AppleDouble `._*` metadata. These files are ignored. pip emitted invalid-distribution warnings for metadata sidecars, and the vendor git checkout emitted an index-sidecar warning; imports, compiler and tests nevertheless passed. Prefer an APFS development checkout/venvs if these warnings persist. No pre-existing user files were removed.

A broad `compileall` also sees AppleDouble sidecars; exclude them with `python -m compileall -q -x '/\._' backend/app scripts`. Normal imports and pytest ignore these metadata files.
