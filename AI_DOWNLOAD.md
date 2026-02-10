# AI Download Guide

This guide is optimized for AI agents and headless environments.

Repository:

```text
https://github.com/wudao1006/plane-connect.git
```

## Preferred: Download Portable Package (includes `.venv`)

```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
curl -L -o plane-sync-portable.tar.gz \
  https://github.com/wudao1006/plane-connect/raw/main/portable/plane-sync-portable-linux-x86_64.tar.gz
tar -xzf plane-sync-portable.tar.gz
mv plane-connect plane-sync
cd plane-sync
```

Then run:

```bash
cp .env.example .env
./scripts/run-verify.sh
./scripts/run-sync.sh OPINION --template brief --limit 10
```

## Alternative: Source Clone (auto-bootstrap)

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.claude/skills/plane-sync
cd ~/.claude/skills/plane-sync
```

### Codex

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.codex/skills/plane-sync
cd ~/.codex/skills/plane-sync
```

Source mode no longer requires manual pip setup:
`./scripts/run-verify.sh` and `./scripts/run-sync.sh` auto-bootstrap `.venv` via `uv` when missing.

## Configure Auth

### Option A: Non-interactive (recommended for AI/CI)

```bash
python3 -m plane_skills.config_manager \
  --init-auth \
  --non-interactive \
  --base-url "https://your-plane-instance.com" \
  --api-key "plane_api_your_api_key_here" \
  --workspace "your-workspace-slug" \
  --email "your-email@company.com"
```

### Option B: Interactive (for human terminal only)

```bash
python3 -m plane_skills.config_manager --init-auth
```

## Dependency Strategy

No manual dependency install is required when using:
- portable package (bundled `.venv`)
- or source mode with `./scripts/run-verify.sh` / `./scripts/run-sync.sh`

## Use the Skill

```bash
/plane-sync OPINION
/plane-sync OPINION --my-tasks
/plane-sync OPINION --template standup --limit 15
```

## Troubleshooting for AI Agents

1. `pip: command not found`
- Do not run `pip install ...`.
- Use `./scripts/run-verify.sh` (auto-bootstrap) or portable package mode.

2. `EOFError` during `--init-auth`
- You are in non-interactive shell; use `--non-interactive` with explicit flags.

3. `project not found`
- Verify `PLANE_WORKSPACE` and project identifier (e.g. `OPINION`).

4. API auth/network errors
- Check `PLANE_BASE_URL`, `PLANE_API_KEY`, network, and permissions.

5. Running bundled `.venv` fails on another machine
- Use source clone mode (auto-bootstrap), or rebuild portable package on target OS/architecture.

## AI Prompt Template

```text
Install plane-sync from https://github.com/wudao1006/plane-connect.git to ~/.claude/skills/plane-sync,
run non-interactive auth setup with my Plane credentials, then run:
./scripts/run-verify.sh
./scripts/run-sync.sh OPINION --template brief --limit 10
```
