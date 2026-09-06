#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export UV_PROJECT_ENVIRONMENT="${POLAR_APP_VENV:-$CACHE_HOME/polar-web-app/backend-venv}"

if [[ -n "${UV_BIN:-}" ]]; then
  :
elif command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "$HOME/.hermes/bin/uv" ]]; then
  UV_BIN="$HOME/.hermes/bin/uv"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  UV_BIN="$HOME/.local/bin/uv"
else
  printf 'error: uv is required to rebuild aggregates\n' >&2
  exit 1
fi

cd "$ROOT_DIR/src/backend"
"$UV_BIN" run alembic upgrade head
exec "$UV_BIN" run python -m polar_app.cli rebuild-training-aggregates
