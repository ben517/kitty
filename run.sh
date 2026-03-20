#!/usr/bin/env bash
# Start the SOS Demo FastAPI server
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Fix native library paths for this Nix-based environment
export LD_LIBRARY_PATH="/nix/store/03h8f1wmpb86s9v8xd0lcb7jnp7nwm6l-idx-env-fhs/usr/lib:${LD_LIBRARY_PATH:-}"

exec "$SCRIPT_DIR/venv/bin/python" -m uvicorn app.main:app \
    --host "${SOS_HOST:-0.0.0.0}" \
    --port "${SOS_PORT:-8000}" \
    --reload "$@"
