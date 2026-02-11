#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(pwd -P)"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 如果在 skill 目录内执行（例如 `cd ~/.claude/skills/plane-sync && ...`），
# 且存在 OLDPWD，则优先把 OLDPWD 视为调用方项目目录。
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

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 PROJECT_ID [--my-tasks] [--template brief] [--limit 10] ..."
  exit 1
fi

HAS_OUTPUT=0
HAS_PROJECT_DIR=0
for ARG in "$@"; do
  case "$ARG" in
    --output|--output=*)
      HAS_OUTPUT=1
      ;;
    --project-dir|--project-dir=*)
      HAS_PROJECT_DIR=1
      ;;
  esac
done

ARGS=("$@")
if [ "$HAS_PROJECT_DIR" -eq 0 ]; then
  ARGS+=(--project-dir "$CALLER_DIR")
fi

if [ "$HAS_OUTPUT" -eq 0 ]; then
  ARGS+=(--output "$CALLER_DIR/plane.md")
fi

exec .venv/bin/python - "${ARGS[@]}" <<'PY'
import shlex
import sys
from plane_skills.plane_sync_skill import plane_sync_skill

args = sys.argv[1:]
args_string = shlex.join(args)
plane_sync_skill(args_string=args_string)
PY
