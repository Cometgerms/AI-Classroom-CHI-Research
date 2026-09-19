# Supported simulation — Windows

Simulation is a permanent product/research mode. No physical AV hardware is needed to contribute. Install Python 3.12 and Node 22+, then from repository root in PowerShell:

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
& backend/.venv/Scripts/python.exe -m backend --profile simulation-basic
```

In a separate PowerShell terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open http://localhost:5173. For real local Qwen, install/start Ollama and run `ollama pull qwen3:8b`; stop the backend and relaunch from root with `& backend/.venv/Scripts/python.exe -m backend --profile simulation-ai`. Clear conflicting AGENT_BACKEND entries from backend/.env/environment. This strict profile never substitutes Fake. `--profile study` defaults to participant presentation; `http://localhost:5173/?researcher=1` opens researcher controls. Use `--profile hybrid` with independent adapter selections in ignored config/local.yaml. `--profile hardware` reports unavailable physical outputs honestly. Study authority is independent of profiles.

```powershell
& backend/.venv/Scripts/python.exe scripts/doctor.py --profile simulation-basic
& backend/.venv/Scripts/python.exe scripts/check_simulation_ai.py # requires Qwen/Ollama
Push-Location backend
& .venv/Scripts/python.exe -m pytest -q
Pop-Location
```

See [scenarios, contracts and replay](SIMULATION.md). No WinUSB, microphone, camera, CUDA, Torch or Ollama is needed for simulation-basic. Windows execution remains unverified on this Mac; cross-platform CI is configured. Optional hardware/model setup follows.

---

# XVF3800 V1 quick start — Windows / NVIDIA

**XVF3800 is the V1 canonical audio front end.** The same application/UI runs on Windows; only platform adapters and acceleration differ. Windows hardware/driver/CUDA checks have not been run in this Mac session. ODAS/Silero are optional research adapters.

PowerShell, from repo root after installing Python 3.12, Node 22, Git and Ollama:

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
& backend/.venv/Scripts/python.exe -m backend --profile simulation-basic
# Or: & scripts/run-backend-windows.ps1 -Profile simulation
```

Optional full local development environment (select official CUDA Torch wheels as described below before installing vision requirements):

```powershell
py -3.12 -m venv .venv-perception
& .venv-perception/Scripts/python.exe -m pip install -r backend/requirements.txt -r config/audio-requirements.txt -r config/perception-requirements.txt
& .venv-perception/Scripts/python.exe scripts/bootstrap_xvf3800.py
# Exit 2 means hardware/read unavailable; simulation is still usable.
& .venv-perception/Scripts/python.exe scripts/bootstrap_models.py --perception
if (!(Test-Path config/local.yaml)) { Copy-Item config/local.example.yaml config/local.yaml }
& .venv-perception/Scripts/python.exe scripts/doctor.py --profile windows-local
& .venv-perception/Scripts/python.exe -m backend --profile windows-local
# Stop backend before this explicit microphone test; build Whisper first as below:
& .venv-perception/Scripts/python.exe scripts/capture_xvf_stt.py --seconds 3
& .venv-perception/Scripts/python.exe scripts/check_ai_stack.py --v1
& .venv-perception/Scripts/python.exe scripts/benchmark_xvf3800.py --hardware
Push-Location backend
& .venv/Scripts/python.exe -m pytest -q
Pop-Location
```

Example ignored local.yaml:

```yaml
runtime:
  platform: windows
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
  acceleration: cuda
vision:
  acceleration: cuda
agent:
  backend: ollama
```

The **UAC audio driver and USB control driver are separate**. Current [official Seeed instructions](https://wiki.seeedstudio.com/respeaker_xvf3800_introduction/#windows-usb-driver-setup) use Zadig: Options → List All Devices, identify the ReSpeaker, select WinUSB, install, reconnect. Confirm the vendor-control interface for your firmware/device layout; do not indiscriminately replace the working UAC audio interfaces. The host-control README's example reports control interface 3, but firmware layouts can differ. If telemetry works but the recording device disappears, revisit driver binding using the official guide. No automatic driver installation or firmware changes are performed by this project.

Our preferred path is pinned official Python/PyUSB with bundled libusb. The upstream `host_control/win32` native executable/DLL directory is an optional diagnostic alternative; keep its accompanying DLLs together. The shared room logic never invokes it. Enable microphone access for desktop apps in Windows privacy settings. PortAudio may list the same physical UAC device under several APIs; set `audio.host_api` to the exact enumerated API (e.g. `Windows WASAPI`) locally to resolve ambiguity. An index override is permitted only in local.yaml. Verify actual reported 16/48 kHz profile instead of assuming a rate.

Both platforms use the same Qwen3:8b model and whisper.cpp small.en. Acceleration selection is not evidence of GPU execution: run doctor/inference and compare actual benchmarks. `--profile simulation-basic` overrides local hybrid mode; environment remains highest. Core CI and simulation never require WinUSB, CUDA, microphones, cameras, or XVF hardware. Optional Silero install is separate via config/research-vad-requirements.txt; do not run ODAS in ordinary V1.

---

# Windows / NVIDIA setup

Target: Ryzen 9 + RTX 5070 Ti Laptop GPU. This machine was NOT available during the Mac session; do not assume identical versions, VRAM, CUDA or performance. Run in PowerShell from repository root. Install Git, Python 3.12, Node 22 LTS, and the [official Windows Ollama installer](https://docs.ollama.com/windows). Restart the terminal after installers update PATH, launch Ollama and check `ollama --version`.

## Core simulator (no CUDA Python stack required)

```powershell
py -3.12 -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
& backend/.venv/Scripts/python.exe scripts/bootstrap_models.py --secondary
& backend/.venv/Scripts/python.exe scripts/check_room_agent.py
Push-Location backend
& .venv/Scripts/python.exe -m pytest -q
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Pop-Location
Push-Location frontend
npm ci
npm run build
Pop-Location
# Separate terminals:
& scripts/run-backend-windows.ps1
& scripts/run-ui-windows.ps1
```

`AGENT_BACKEND=fake` remains default in backend/.env. Use `ollama` only when desired; `OLLAMA_STRICT=true` disables fallback for verification. No Qwen3 4B substitution is enabled. Bootstrap convenience wrapper: `& scripts/bootstrap_windows.ps1 --secondary`. Optional component failures never prevent the fake simulator from starting.

## Optional Python perception

```powershell
py -3.12 -m venv .venv-perception
# Install GPU-compatible torch/torchvision/torchaudio wheels using the current
# official PyTorch Windows + pip + CUDA selector before the following command.
& .venv-perception/Scripts/python.exe -m pip install -r config/perception-requirements.txt
& .venv-perception/Scripts/python.exe scripts/bootstrap_models.py --secondary --perception
& .venv-perception/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Use the [official PyTorch installation selector](https://pytorch.org/get-started/locally/) for a wheel compatible with the installed driver and Blackwell GPU. The Mac dependency snapshot is an audit record, not a Windows CUDA lock. The vision adapters default to CPU; explicitly select `device='cuda:0'` only after a real GPU inference test. VAD is CPU and independent of STT.

## whisper.cpp with CUDA

Install Visual Studio 2022 C++ build tools, CMake, and a CUDA Toolkit supporting this GPU/compiler. From a Developer PowerShell:

```powershell
New-Item -ItemType Directory -Force vendor, models/whisper | Out-Null
git clone https://github.com/ggml-org/whisper.cpp.git vendor/whisper.cpp
git -C vendor/whisper.cpp checkout 5670d5c0bbcb148feabef84400a07cfca9aa3b30
cmake -S vendor/whisper.cpp -B vendor/whisper.cpp/build -DGGML_CUDA=ON
cmake --build vendor/whisper.cpp/build --config Release -j 8
Invoke-WebRequest https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin -OutFile models/whisper/ggml-small.en.bin
$env:WHISPER_CPP_BIN = (Resolve-Path vendor/whisper.cpp/build/bin/Release/whisper-cli.exe).Path
$env:WHISPER_MODEL = (Resolve-Path models/whisper/ggml-small.en.bin).Path
& .venv-perception/Scripts/python.exe scripts/check_ai_stack.py
& .venv-perception/Scripts/python.exe scripts/environment_report.py
& .venv-perception/Scripts/python.exe scripts/benchmark_ai_stack.py --image path/to/representative-frame.jpg
```

For a single-config generator the executable may be directly under build/bin; adjust WHISPER_CPP_BIN. If CUDA build fails, document it and build a separate CPU directory with `-DGGML_CUDA=OFF`; do not silently claim GPU acceleration. Audio must be mono 16 kHz PCM16 WAV. Optional `base.en` uses the corresponding model URL and WHISPER_MODEL override. See [upstream CUDA instructions](https://github.com/ggml-org/whisper.cpp#nvidia-gpu-support).

## ODAS: Linux/WSL2 path, not verified native Windows

ODAS is a C program, not an ML weight. Upstream CMake requires Linux audio libraries. In Ubuntu/WSL2 or Linux:

```bash
sudo apt-get update
sudo apt-get install build-essential cmake git pkg-config libfftw3-dev libasound2-dev libconfig-dev libpulse-dev
git clone https://github.com/introlab/odas.git
cmake -S odas -B odas/build
cmake --build odas/build -j 8
```

This is a documented build path, not a verified live Windows microphone solution. Record the ODAS commit when built. WSL USB/multichannel audio routing and array geometry need separate work. Do not let ODAS block UI/control work.
