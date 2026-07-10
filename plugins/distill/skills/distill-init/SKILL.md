---
name: distill-init
user-invocable: true
description: One-step Distill onboarding for a new project.
metadata:
  version: "1.9.0"
  category: setup
  type: unit
  style: tool
  triggers: [distill init, initialize distill, setup distill, distill onboarding]
  uses: [mcp__distill__init]
---

# /distill-init

One-step onboarding: creates config, scans the local environment, and reports configured sources.

## Usage

```
/distill-init
```

## MCP Tool

Call `mcp__distill__init` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | string | None | Override scope: `global`, `workspace`, or `project` |

## What it does

1. Creates `.noory/distill/config.json` for a project or workspace, or the
   global config under `~/.distill/`, if missing.
2. Scans any existing Claude-compatible rules, skills, and agents.
3. Reports directories configured in `sources.dirs`.

## After init

On Claude Code, use `distill-ingest` for reported directories. On Codex or
Gemini CLI, read the source, extract reusable chunks with the current model,
and call Distill MCP `store`.
