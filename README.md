# Plane Sync Skill

Plane Sync is a lightweight Claude Skill for syncing Plane project tasks and producing AI-friendly Markdown reports.

## Installing This Skill

This repository follows the same distribution pattern used by public skill repositories:
- one skill folder with `SKILL.md` metadata
- optional `agents/*.yml` UI metadata
- reusable scripts/resources in the same repository

### Codex (manual install)

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.codex/skills/plane-sync
```

### Claude Code (manual install)

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.claude/skills/plane-sync
```

After installation, restart the client so the new skill is discovered.

For an AI-oriented install guide (copy/paste prompts + commands), see `AI_DOWNLOAD.md`.

## Portable Bundle (with `.venv`)

If you want a package that includes the virtual environment:

```bash
./scripts/build-portable-bundle.sh
```

This creates `dist/plane-sync-portable-<timestamp>.tar.gz`.

After extracting:

```bash
cp .env.example .env
./scripts/run-verify.sh
./scripts/run-sync.sh OPINION --template brief --limit 10
```

`run-verify.sh` and `run-sync.sh` can also auto-bootstrap `.venv` from source clone mode (using `uv`) when `.venv` is missing.

## Core capabilities

- Sync issues from a Plane project
- Filter by assignee, priority, and status
- Generate reports with templates: `ai-context`, `brief`, `standup`, `development`
- Save report to a local markdown file (default: `plane.md`)

## Project structure

```text
SKILL.md                 # Claude Skill definition
agents/plane.yml         # Skill UI metadata
plane_skills/            # Core implementation
plane_skills/templates/  # Report templates
verify_setup.py          # Environment and structure checks
```

## Setup

Preferred (works even when `pip` is unavailable):

```bash
uv run --with requests --with python-dotenv --with tqdm --with colorama python3 verify_setup.py
```

Alternative (if `pip` is available):

```bash
pip install -r requirements.txt
cp .env.example .env
```

Configure `.env`:

```bash
PLANE_BASE_URL="https://your-plane-instance.com"
PLANE_API_KEY="plane_api_your_api_key_here"
PLANE_WORKSPACE="your-workspace-slug"
MY_EMAIL="your-email@company.com"
```

Or run interactive first-time auth setup:

```bash
python3 -m plane_skills.config_manager --init-auth
```

For AI/CI (non-interactive) setup:

```bash
python3 -m plane_skills.config_manager \
  --init-auth \
  --non-interactive \
  --base-url "https://your-plane-instance.com" \
  --api-key "plane_api_your_api_key_here" \
  --workspace "your-workspace-slug" \
  --email "your-email@company.com"
```

## Usage

In Claude Code:

```bash
/plane-sync MOBILE
/plane-sync MOBILE --my-tasks
/plane-sync MOBILE --priority high,urgent --status todo,in-progress
/plane-sync MOBILE --template standup --limit 15 --output standup.md
```

## Python API

```python
from plane_skills import plane_sync_skill

plane_sync_skill(
    project_id="MOBILE",
    my_tasks=True,
    template="ai-context",
    output="plane.md",
)
```

## Verification

```bash
python3 verify_setup.py
python3 /home/wudao/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```
