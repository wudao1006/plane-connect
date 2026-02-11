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

  # 1) 显式传入优先
  if [ -n "${PLANE_CALLER_CWD:-}" ] && [ -d "${PLANE_CALLER_CWD:-}" ]; then
    candidate="$(cd "$PLANE_CALLER_CWD" 2>/dev/null && pwd -P || true)"
  fi

  # 2) 当前目录
  if [ -z "$candidate" ] && [ -d "$CURRENT_DIR" ]; then
    candidate="$CURRENT_DIR"
  fi

  # 3) 上一个目录（仅安装模式下启用，适配 `cd skill && bash scripts/run-sync.sh`）
  if [ "$INSTALLED_SKILL" -eq 1 ] && [ "$candidate" = "$ROOT_DIR" ] && [ -n "${OLDPWD:-}" ] && [ -d "${OLDPWD:-}" ]; then
    local oldpwd_real
    oldpwd_real="$(cd "$OLDPWD" 2>/dev/null && pwd -P || true)"
    if [ -n "$oldpwd_real" ] && [ "$oldpwd_real" != "$ROOT_DIR" ]; then
      candidate="$oldpwd_real"
    fi
  fi

  # 4) 追踪父进程 cwd（仅安装模式下启用，适配 OLDPWD 丢失场景）
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

extract_env_value() {
  local file="$1"
  local key="$2"
  if [ ! -f "$file" ]; then
    return 0
  fi
  awk -F= -v key="$key" '
    $0 ~ "^[[:space:]]*"key"[[:space:]]*=" {
      v=$0
      sub("^[[:space:]]*"key"[[:space:]]*=[[:space:]]*", "", v)
      gsub(/^[\"\047]|[\"\047]$/, "", v)
      print v
      exit
    }
  ' "$file"
}

is_valid_env_dir() {
  local dir="$1"
  local env_file="$dir/.env"
  if [ ! -f "$env_file" ]; then
    return 1
  fi

  local base_url api_key workspace
  base_url="$(extract_env_value "$env_file" "PLANE_BASE_URL")"
  api_key="$(extract_env_value "$env_file" "PLANE_API_KEY")"
  workspace="$(extract_env_value "$env_file" "PLANE_WORKSPACE")"

  if [ -z "$base_url" ] || [ -z "$api_key" ] || [ -z "$workspace" ]; then
    return 1
  fi

  case "$base_url" in
    *plane.example.com*|*your-plane-instance*)
      return 1
      ;;
  esac

  case "$api_key" in
    *your_api_key_here*|*plane_api_xxx*|*demo_key*)
      return 1
      ;;
  esac

  case "$workspace" in
    *project-workspace*|*your-workspace-slug*)
      return 1
      ;;
  esac

  return 0
}

discover_config_dir() {
  local caller="$1"

  if is_valid_env_dir "$caller"; then
    echo "$caller"
    return
  fi

  if is_valid_env_dir "$ROOT_DIR"; then
    echo "$ROOT_DIR"
    return
  fi

  if [ -n "${PLANE_CONFIG_DIR:-}" ] && is_valid_env_dir "${PLANE_CONFIG_DIR:-}"; then
    echo "${PLANE_CONFIG_DIR:-}"
    return
  fi

  echo "$caller"
}

CALLER_DIR="$(discover_caller_dir)"
if [ -z "$CALLER_DIR" ] || [ ! -d "$CALLER_DIR" ]; then
  CALLER_DIR="$CURRENT_DIR"
fi
CONFIG_DIR="$(discover_config_dir "$CALLER_DIR")"

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
  ARGS+=(--project-dir "$CONFIG_DIR")
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
