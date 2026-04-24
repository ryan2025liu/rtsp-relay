#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

cd "$API_DIR"

python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 18081 --reload
