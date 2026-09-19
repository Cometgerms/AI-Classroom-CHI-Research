#!/usr/bin/env bash
set -euo pipefail
MODEL="${1:-qwen3:8b}"
if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed. Download it from https://ollama.com/download"
  exit 1
fi
echo "Pulling $MODEL ..."
ollama pull "$MODEL"
echo "Testing local model..."
ollama run "$MODEL" "Reply with exactly: AGENT READY"
