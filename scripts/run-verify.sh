#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(pwd -P)"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CALLER_DIR="${PLANE_CALLER_CWD:-$CURRENT_DIR}"
if [ "$CALLER_DIR" = "$ROOT_DIR" ] && [ -n "${OLDPWD:-}" ] && [ -d "${OLDPWD:-}" ]; then
  CANDIDATE_DIR="$(cd "$OLDPWD" 2>/dev/null && pwd -P || true)"
  if [ -n "$CANDIDATE_DIR" ] && [ "$CANDIDATE_DIR" != "$ROOT_DIR" ]; then
    CALLER_DIR="$CANDIDATE_DIR"
  fi
fi

cd "$ROOT_DIR"
export PLANE_CALLER_CWD="$CALLER_DIR"

./scripts/bootstrap-runtime.sh

exec .venv/bin/python verify_setup.py --project-dir "$CALLER_DIR"
