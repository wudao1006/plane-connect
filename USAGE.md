# Plane Sync Usage

## Command

```bash
/plane-sync PROJECT_ID [options]
```

## First-time Interactive Auth

```bash
python3 -m plane_skills.config_manager --init-auth
```

This wizard writes project `.env` with `PLANE_BASE_URL`, `PLANE_API_KEY`, `PLANE_WORKSPACE`, and `MY_EMAIL`.

## Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--my-tasks` | boolean | `false` | Sync only tasks assigned to current user |
| `--assignee` | string | - | Filter by assignee email or display name |
| `--priority` | string | - | Comma-separated: `urgent,high,medium,low` |
| `--status` | string | - | Comma-separated status names |
| `--limit` | integer | `20` | Max number of tasks to include (`1-100`) |
| `--template` | string | `ai-context` | `ai-context`, `brief`, `standup`, `development` |
| `--output` | string | `plane.md` | Output markdown filename |
| `--refresh-users` | boolean | `false` | Refresh cached user mapping |

## Examples

```bash
/plane-sync MOBILE
/plane-sync MOBILE --my-tasks
/plane-sync MOBILE --assignee user@company.com --status todo,in-progress
/plane-sync MOBILE --priority high,urgent --limit 10 --template brief
/plane-sync MOBILE --template standup --output standup.md
```

## Python API

```python
from plane_skills import plane_sync_skill, sync_my_tasks, sync_high_priority_tasks

# Full API
plane_sync_skill(
    project_id="MOBILE",
    assignee="user@company.com",
    priority="high,urgent",
    status="todo,in-progress",
    limit=15,
    template="ai-context",
    output="plane.md",
)

# Helper APIs
sync_my_tasks("MOBILE")
sync_high_priority_tasks("MOBILE")
```

## Troubleshooting

1. `配置验证失败`:
   - Check `.env` required values: `PLANE_BASE_URL`, `PLANE_API_KEY`, `PLANE_WORKSPACE`.
2. `项目不存在`:
   - Verify `PROJECT_ID` identifier in Plane.
3. `--my-tasks` has no result:
   - Ensure `MY_EMAIL` is set and matches Plane account.
4. Dependency errors:
   - Run `pip install -r requirements.txt`.

## Self-check

```bash
python3 verify_setup.py
```
