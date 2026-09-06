#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${UV_BIN:-}" ]]; then
  if [[ ! -x "$UV_BIN" ]]; then
    printf 'error: configured UV_BIN is not executable: %s\n' "$UV_BIN" >&2
    exit 1
  fi
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "$HOME/.hermes/bin/uv" ]]; then
  UV_BIN="$HOME/.hermes/bin/uv"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  UV_BIN="$HOME/.local/bin/uv"
else
  printf 'error: uv is required; install it from https://docs.astral.sh/uv/\n' >&2
  exit 1
fi

CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export UV_PROJECT_ENVIRONMENT="${POLAR_APP_VENV:-$CACHE_HOME/polar-web-app/backend-venv}"
export POLAR_APP_DATABASE_PATH="${POLAR_APP_DATABASE_PATH:-$ROOT_DIR/database/polar-app.sqlite3}"

cd "$ROOT_DIR/src/backend"
"$UV_BIN" run python -m polar_app.backup "$@"
