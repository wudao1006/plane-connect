# AI Download Guide

This guide is optimized for AI agents and headless environments.

Repository:

```text
https://github.com/wudao1006/plane-connect.git
```

## Quick Install (Claude Code)

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.claude/skills/plane-sync
cd ~/.claude/skills/plane-sync
```

## Quick Install (Codex)

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.codex/skills/plane-sync
cd ~/.codex/skills/plane-sync
```

## Portable Package (includes `.venv`)

Build once on the source machine:

```bash
./scripts/build-portable-bundle.sh
```

Distribute:

```text
dist/plane-sync-portable-<timestamp>.tar.gz
```

On target machine:

```bash
tar -xzf plane-sync-portable-<timestamp>.tar.gz
cd plane-connect
cp .env.example .env
./scripts/run-verify.sh
./scripts/run-sync.sh OPINION --template brief --limit 10
```

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

### Preferred (no system pip required)

```bash
uv run --with requests --with python-dotenv --with tqdm --with colorama python3 verify_setup.py
```

### Alternative (if pip available)

```bash
python3 -m pip install -r requirements.txt
python3 verify_setup.py
```

## Use the Skill

```bash
/plane-sync OPINION
/plane-sync OPINION --my-tasks
/plane-sync OPINION --template standup --limit 15
```

## Troubleshooting for AI Agents

1. `pip: command not found`
- Use `uv run --with ... python3 verify_setup.py` (no pip required).

2. `EOFError` during `--init-auth`
- You are in non-interactive shell; use `--non-interactive` with explicit flags.

3. `project not found`
- Verify `PLANE_WORKSPACE` and project identifier (e.g. `OPINION`).

4. API auth/network errors
- Check `PLANE_BASE_URL`, `PLANE_API_KEY`, network, and permissions.

5. Running bundled `.venv` fails on another machine
- Rebuild bundle on the target OS/architecture (virtual environments are not fully cross-platform portable).

## AI Prompt Template

```text
Install plane-sync from https://github.com/wudao1006/plane-connect.git to ~/.claude/skills/plane-sync,
run non-interactive auth setup with my Plane credentials, then verify using:
uv run --with requests --with python-dotenv --with tqdm --with colorama python3 verify_setup.py
```
