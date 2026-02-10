#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install uv first: https://docs.astral.sh/uv/"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment (.venv)"
  uv venv .venv
else
  echo "[1/4] Reusing existing virtual environment (.venv)"
fi

echo "[2/4] Installing dependencies into .venv"
uv pip install --python .venv/bin/python -r requirements.txt

echo "[3/4] Building portable archive"
mkdir -p dist
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="dist/plane-sync-portable-${STAMP}.tar.gz"

tar -czf "$ARCHIVE" \
  --exclude=".git" \
  --exclude=".claude" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".env" \
  --exclude="dist" \
  .

echo "[4/4] Bundle ready"
echo "Archive: $ARCHIVE"
du -sh "$ARCHIVE"
sha256sum "$ARCHIVE"

cat <<'EOF'

Usage after extracting:
  1) cd plane-connect
  2) cp .env.example .env  # fill your Plane credentials
  3) ./scripts/run-verify.sh
  4) ./scripts/run-sync.sh OPINION --template brief --limit 10
EOF
