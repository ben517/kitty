#!/usr/bin/env bash
# Start the FastAPI server
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use Nix loader with explicit library paths for numpy/chromadb native libs
LOADER="/nix/store/pf5avvvl4ssd6kylcvg2g23hcjp71h19-glibc-2.39-52/lib64/ld-linux-x86-64.so.2"
LIB_PATH="/nix/store/90yn7340r8yab8kxpb0p7y0c9j3snjam-gcc-13.2.0-lib/lib:/nix/store/03h8f1wmpb86s9v8xd0lcb7jnp7nwm6l-idx-env-fhs/usr/lib"

exec "$LOADER" --library-path "$LIB_PATH" "$SCRIPT_DIR/venv/bin/python" -m uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    "$@"
