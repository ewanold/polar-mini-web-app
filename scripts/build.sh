#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/src/frontend"
STATIC_DIR="$ROOT_DIR/src/backend/src/polar_app/static"
CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
POLAR_FRONTEND_WORKSPACE="${POLAR_FRONTEND_WORKSPACE:-$CACHE_HOME/polar-web-app/frontend-build}"

if ! command -v npm >/dev/null 2>&1; then
  printf 'error: npm is required to build the frontend\n' >&2
  exit 1
fi
if [[ ! -f "$FRONTEND_DIR/package-lock.json" ]]; then
  printf 'error: frontend/package-lock.json is missing\n' >&2
  exit 1
fi

rm -rf "$POLAR_FRONTEND_WORKSPACE"
mkdir -p "$POLAR_FRONTEND_WORKSPACE"
cp -R "$FRONTEND_DIR/." "$POLAR_FRONTEND_WORKSPACE/"

npm ci --prefix "$POLAR_FRONTEND_WORKSPACE" --no-audit --no-fund
npm run build --prefix "$POLAR_FRONTEND_WORKSPACE"

rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"
cp -R "$POLAR_FRONTEND_WORKSPACE/dist/." "$STATIC_DIR/"

printf 'Frontend assets copied to %s\n' "$STATIC_DIR"
