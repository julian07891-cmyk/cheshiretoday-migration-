#!/usr/bin/env bash
set -e

# Ensure we run from the backend folder so `server:app` imports correctly
cd "$(dirname "$0")"

python3 -m uvicorn server:app --host 0.0.0.0 --port "${PORT:-8000}"
