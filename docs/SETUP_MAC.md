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
