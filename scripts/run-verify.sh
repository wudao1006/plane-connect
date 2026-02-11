#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(pwd -P)"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLED_SKILL=0
case "$ROOT_DIR" in
  "$HOME/.claude/skills/"*|"$HOME/.codex/skills/"*)
    INSTALLED_SKILL=1
    ;;
esac

discover_caller_dir() {
  local candidate=""

  if [ -n "${PLANE_CALLER_CWD:-}" ] && [ -d "${PLANE_CALLER_CWD:-}" ]; then
    candidate="$(cd "$PLANE_CALLER_CWD" 2>/dev/null && pwd -P || true)"
  fi

  if [ -z "$candidate" ] && [ -d "$CURRENT_DIR" ]; then
    candidate="$CURRENT_DIR"
  fi

  if [ "$INSTALLED_SKILL" -eq 1 ] && [ "$candidate" = "$ROOT_DIR" ] && [ -n "${OLDPWD:-}" ] && [ -d "${OLDPWD:-}" ]; then
    local oldpwd_real
    oldpwd_real="$(cd "$OLDPWD" 2>/dev/null && pwd -P || true)"
    if [ -n "$oldpwd_real" ] && [ "$oldpwd_real" != "$ROOT_DIR" ]; then
      candidate="$oldpwd_real"
    fi
  fi

  if [ "$INSTALLED_SKILL" -eq 1 ] && [ "$candidate" = "$ROOT_DIR" ] && [ -d /proc ]; then
    local pid="$PPID"
    local depth=0
    while [ "$pid" -gt 1 ] && [ "$depth" -lt 8 ]; do
      if [ -r "/proc/$pid/cwd" ]; then
        local proc_cwd
        proc_cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
        if [ -n "$proc_cwd" ] && [ "$proc_cwd" != "$ROOT_DIR" ] && [ -d "$proc_cwd" ]; then
          candidate="$proc_cwd"
          break
        fi
      fi
      if [ -r "/proc/$pid/stat" ]; then
        pid="$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null || echo 1)"
      else
        break
      fi
      depth=$((depth + 1))
    done
  fi

  echo "$candidate"
}

CALLER_DIR="$(discover_caller_dir)"
if [ -z "$CALLER_DIR" ] || [ ! -d "$CALLER_DIR" ]; then
  CALLER_DIR="$CURRENT_DIR"
fi

cd "$ROOT_DIR"
export PLANE_CALLER_CWD="$CALLER_DIR"

./scripts/bootstrap-runtime.sh

exec .venv/bin/python verify_setup.py --project-dir "$ROOT_DIR"
