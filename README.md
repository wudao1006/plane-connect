# Plane Sync Skill

Plane Sync is a lightweight Claude Skill for syncing Plane project tasks and producing AI-friendly Markdown reports.

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
