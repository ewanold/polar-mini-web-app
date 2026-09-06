#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATIC_INDEX="$ROOT_DIR/src/backend/src/polar_app/static/index.html"

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

if [[ ! -f "$STATIC_INDEX" ]]; then
  printf 'error: compiled frontend assets are missing; run ./scripts/build.sh first\n' >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/database" "$ROOT_DIR/database/backups" "$ROOT_DIR/database/logs"

CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export UV_PROJECT_ENVIRONMENT="${POLAR_APP_VENV:-$CACHE_HOME/polar-web-app/backend-venv}"
mkdir -p "$(dirname "$UV_PROJECT_ENVIRONMENT")"

export POLAR_APP_DATABASE_PATH="${POLAR_APP_DATABASE_PATH:-$ROOT_DIR/database/polar-app.sqlite3}"
export POLAR_APP_HOST="${POLAR_APP_HOST:-127.0.0.1}"
export POLAR_APP_PORT="${POLAR_APP_PORT:-8000}"

cd "$ROOT_DIR/src/backend"
"$UV_BIN" run alembic upgrade head
exec "$UV_BIN" run uvicorn polar_app.main:app \
  --host "$POLAR_APP_HOST" \
  --port "$POLAR_APP_PORT" \
  --workers 1
