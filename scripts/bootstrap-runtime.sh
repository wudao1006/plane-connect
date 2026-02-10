#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/bin/python" ]; then
  exit 0
fi

echo "Runtime .venv not found. Bootstrapping runtime environment..."

if command -v uv >/dev/null 2>&1; then
  uv venv .venv
  uv pip install --python .venv/bin/python -r requirements.txt
  exit 0
fi

echo "Error: uv is required to bootstrap runtime when bundled .venv is missing."
echo "Install uv first: https://docs.astral.sh/uv/"
exit 1
