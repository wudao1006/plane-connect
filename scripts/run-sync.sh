#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "Missing .venv. Run ./scripts/build-portable-bundle.sh first."
  exit 1
fi

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 PROJECT_ID [--my-tasks] [--template brief] [--limit 10] ..."
  exit 1
fi

exec .venv/bin/python - "$@" <<'PY'
import shlex
import sys
from plane_skills.plane_sync_skill import plane_sync_skill

args = sys.argv[1:]
args_string = shlex.join(args)
plane_sync_skill(args_string=args_string)
PY
