---
name: plane-sync
description: Use when Claude Code needs to sync Plane project tasks, filter by assignee, priority, or status, and generate Markdown reports for planning, standup updates, or execution tracking.
---

# Plane Sync

## Overview

Use `plane-sync` to pull tasks from Plane and generate AI-friendly Markdown reports.
Run through `plane_skills/plane_sync_skill.py` with filters and templates.

## Quick Start

```bash
/plane-sync PROJECT_ID [options]
```

Examples:

```bash
/plane-sync MOBILE
/plane-sync MOBILE --my-tasks
/plane-sync MOBILE --priority high,urgent --status todo,in-progress
/plane-sync MOBILE --template standup --limit 15
```

## Parameters

Required:

- `PROJECT_ID`: Project identifier such as `MOBILE`, `WEB`, `API`

Optional:

| Option | Type | Default | Notes |
|---|---|---|---|
| `--my-tasks` | boolean | `false` | Keep only tasks assigned to current user |
| `--assignee` | string | - | Filter by assignee email or name |
| `--priority` | string | - | Comma-separated: `urgent,high,medium,low` |
| `--status` | string | - | Comma-separated status values |
| `--limit` | integer | `20` | Range: `1-100` |
| `--template` | string | `ai-context` | One of `ai-context`, `brief`, `standup`, `development` |
| `--output` | string | `plane.md` | Output markdown path |
| `--refresh-users` | boolean | `false` | Refresh cached user map |

## Templates

- `ai-context`: detailed AI analysis context
- `brief`: short summary
- `standup`: daily/standup report
- `development`: engineering-oriented report

Template files live in `plane_skills/templates/`.

## Workflow

1. Load `.env` and project config.
2. Fetch project and tasks from Plane API.
3. Apply assignee/priority/status filters.
4. Render markdown with selected template.
5. Save report to `--output`.

## Configuration

Set required environment variables in `.env`:

```bash
PLANE_BASE_URL="https://your-plane-instance.com"
PLANE_API_KEY="plane_api_xxx"
PLANE_WORKSPACE="workspace-slug"
MY_EMAIL="your-email@company.com"
```

## Common Mistakes

- Missing env vars: run `python3 verify_setup.py` and fix `.env`.
- Wrong project id: confirm the project key in Plane.
- Empty output: relax filters (`--status`, `--assignee`, `--priority`) and retry.
- Stale assignee names: add `--refresh-users`.

## Implementation Pointers

- Main entry: `plane_skills/plane_sync_skill.py`
- API client: `plane_skills/plane_client.py`
- Filters: `plane_skills/task_filter.py`
- Render engine: `plane_skills/template_engine.py`

For full usage and integration details, read `USAGE.md`.
