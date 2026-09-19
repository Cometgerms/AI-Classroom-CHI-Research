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
