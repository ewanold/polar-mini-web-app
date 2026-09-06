#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/src/frontend"
CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export UV_PROJECT_ENVIRONMENT="${POLAR_APP_VENV:-$CACHE_HOME/polar-web-app/backend-venv}"
POLAR_FRONTEND_WORKSPACE="${POLAR_FRONTEND_WORKSPACE:-$CACHE_HOME/polar-web-app/frontend-dev}"

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
  printf 'error: uv is required for backend development\n' >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  printf 'error: npm is required for frontend development\n' >&2
  exit 1
fi
if ! command -v rsync >/dev/null 2>&1; then
  printf 'error: rsync is required to mirror frontend source from a noexec project mount\n' >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/database" "$(dirname "$UV_PROJECT_ENVIRONMENT")"
export POLAR_APP_DATABASE_PATH="${POLAR_APP_DATABASE_PATH:-$ROOT_DIR/database/polar-app.sqlite3}"
export POLAR_APP_HOST="${POLAR_APP_HOST:-127.0.0.1}"
export POLAR_APP_PORT="${POLAR_APP_PORT:-8000}"

mkdir -p "$POLAR_FRONTEND_WORKSPACE"
rsync -a --delete --exclude node_modules --exclude dist \
  "$FRONTEND_DIR/" "$POLAR_FRONTEND_WORKSPACE/"
npm ci --prefix "$POLAR_FRONTEND_WORKSPACE" --no-audit --no-fund

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  kill "${BACKEND_PID:-}" "${FRONTEND_PID:-}" "${SYNC_PID:-}" 2>/dev/null || true
  wait "${BACKEND_PID:-}" "${FRONTEND_PID:-}" "${SYNC_PID:-}" 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT INT TERM

(
  while true; do
    rsync -a --delete --exclude node_modules --exclude dist \
      "$FRONTEND_DIR/" "$POLAR_FRONTEND_WORKSPACE/"
    sleep 1
  done
) &
SYNC_PID=$!

(
  cd "$ROOT_DIR/src/backend"
  "$UV_BIN" run alembic upgrade head
  exec "$UV_BIN" run uvicorn polar_app.main:app --reload --host "$POLAR_APP_HOST" --port "$POLAR_APP_PORT"
) &
BACKEND_PID=$!

npm run dev --prefix "$POLAR_FRONTEND_WORKSPACE" -- --host "${POLAR_FRONTEND_HOST:-127.0.0.1}" &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
