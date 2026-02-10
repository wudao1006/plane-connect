# AI Download Guide

This document is for AI assistants (and teammates) to install `plane-sync` quickly from GitHub.

Repository:

```text
https://github.com/wudao1006/plane-connect.git
```

## 1) Codex Install

### Option A: Manual (works everywhere)

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.codex/skills/plane-sync
```

### Option B: With skill-installer (if available)

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo wudao1006/plane-connect \
  --path .
```

If `--path .` is not supported in your installer version, use Option A.

## 2) Claude Code Install

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/wudao1006/plane-connect.git ~/.claude/skills/plane-sync
```

Restart Claude Code after installation.

## 3) First-Time Auth (interactive)

Run inside the installed skill directory:

```bash
python3 -m plane_skills.config_manager --init-auth
```

This writes `.env` with:
- `PLANE_BASE_URL`
- `PLANE_API_KEY`
- `PLANE_WORKSPACE`
- `MY_EMAIL`

## 4) Verify

```bash
python3 verify_setup.py
```

## 5) Use

In Claude Code:

```bash
/plane-sync OPINION
/plane-sync OPINION --my-tasks
/plane-sync OPINION --template standup --limit 15
```

## AI Prompt Template

Use this prompt with an AI coding agent:

```text
Install the plane-sync skill from https://github.com/wudao1006/plane-connect.git
to ~/.claude/skills/plane-sync (or ~/.codex/skills/plane-sync), run interactive auth
setup, then verify with python3 verify_setup.py.
```
