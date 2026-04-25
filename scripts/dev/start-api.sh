#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
VENV_DIR="$ROOT_DIR/.venv"

cd "$ROOT_DIR"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.12)"
  elif [[ -x "$HOME/.local/bin/python3.12" ]]; then
    PYTHON_BIN="$HOME/.local/bin/python3.12"
  else
    PYTHON_BIN="$(command -v python3)"
  fi

  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -r "$API_DIR/requirements.txt"
PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/python" -m uvicorn apps.api.main:app --host 0.0.0.0 --port 18081 --reload
