# Local model inventory — verified 2026-09-19

Machine: Apple M1 Max, 64 GiB unified memory. Ollama CLI and server **0.33.2** were already installed. Existing llama3.1:latest was left untouched. Exact digests, byte sizes, weight SHA-256 values, sources and per-component install status are in [config/models.yaml](../config/models.yaml) (JSON syntax, valid YAML 1.2). Nothing was substituted for the requested tags.

| Role | Model / runtime | Verified version | Local status |
|---|---|---|---|
| Room reasoning | qwen3:8b / Ollama | digest 500a1f067a9f…; 5,225,388,164 bytes | Chat, JSON, tool calling, all three conditions through RoomAgent/API passed |
| Semantic vision | qwen3-vl:2b-instruct / Ollama | digest ea422f1e7365…; 1,889,519,783 bytes | Image ingestion and structured UNKNOWN classification on blank image passed |
| STT | small.en / whisper.cpp | 1.9.4-dev, commit 5670d5c0bbcb148feabef84400a07cfca9aa3b30 | Built with Metal; upstream 11-second JFK clip transcribed |
| VAD | Silero | silero-vad 6.2.2, onnxruntime 1.30.0 | Independent inference verified; package contains model resources |
| Detection/tracking | yolo26n.pt / Ultralytics | 8.4.155; weights from assets v8.4.0 | Detection and tracking inference verified on CPU |
| Pose | yolo26n-pose.pt / Ultralytics | 8.4.155; weights from assets v8.4.0 | Pose inference verified on blank fixture (empty result is expected) |
| Source localization | ODAS (C library, no ML model) | Not installed | SKIPPED: native Mac build requires platform work |

Qwen3-VL is escalation-only, never continuous video. The [Ollama model page](https://ollama.com/library/qwen3-vl) specifies minimum 0.12.7; bootstrap enforces that when secondary models are requested. Successful inference also verifies compatibility with the installed runtime. Actual classroom visual accuracy is unmeasured.

## Dependencies and licenses

- Qwen3 and Qwen3-VL: Apache-2.0 model licenses; source [Qwen3 8B](https://huggingface.co/Qwen/Qwen3-8B), [Qwen3-VL 2B Instruct](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct). Ollama: MIT.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) and Whisper weights: MIT. small.en selected; base.en allowed but not downloaded. Metal verified; Core ML optional, not installed. Windows CUDA build documented, not verified here.
- [Silero VAD](https://github.com/snakers4/silero-vad): MIT. Torch 2.9.1 locally; VAD does not require STT. Initial test exposed missing onnxruntime; added explicitly and verified.
- [Ultralytics YOLO26](https://docs.ultralytics.com/models/yolo26/): AGPL-3.0 or Enterprise license. This dependency's terms differ from the repository's Apache-2.0 license; academic use is not a blanket license exemption. Reassess distribution/deployment terms if project scope changes. No legal determination is made here.
- [ODAS](https://github.com/introlab/odas): MIT, C source with FFTW/ALSA/libconfig/PulseAudio dependencies. No downloaded neural weights.

Backend dependency snapshot: `backend/requirements-macos.lock.txt`. Optional perception snapshot: `config/perception-macos.lock.txt`; portable top-level requirements: `config/perception-requirements.txt`. Frontend uses `package-lock.json` / `npm ci`. Installed Node 22.23.2 and CMake via Homebrew; Python 3.12.13 was already available. System Python 3.14 is not used for the backend or perception venv. Windows must resolve appropriate CUDA Torch wheels separately, not reuse the Mac full lock.

## Checks and performance

Run `scripts/check_ai_stack.py` with perception Python for real inference checks; optional failures are nonfatal to its exit status and never imported by simulator startup. `scripts/check_room_agent.py` uses actual Qwen3 with strict mode through the API. Test artifacts distinguish PASS/FAIL/SKIPPED; do not interpret installed weights alone as accuracy validation.

Single-run engineering measurements on this Mac, recorded in `artifacts/benchmark_darwin_arm64.json`: Qwen3 cold request 3.51 s (model load 1.35 s), first token 1.48 s, 18.74 tokens/s, tool call 1.67 s; VLM one-frame classification 2.81 s; Whisper real-time factor 0.056 including load; YOLO CPU ~26.8 FPS after warmup. VLM/YOLO input was [Ultralytics' bus image](https://raw.githubusercontent.com/ultralytics/assets/main/im/bus.jpg), a people-detection proxy, not a representative classroom capture. Cold means unloaded model, not cleared OS caches. No Windows numbers exist yet. These are not study results or latency guarantees.

Reports contain allowlisted hardware/version facts, no hostname, username or personal paths. Model weights live in Ollama's own cache and ignored repository `models/`; whisper.cpp source/build in ignored `vendor/`. Private fixture media are ignored. Exact Windows and Mac commands are in the platform guides.
