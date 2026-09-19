#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d backend/.venv ]; then python3 -m venv backend/.venv; fi
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m backend --profile "${1:-simulation-ai}"
