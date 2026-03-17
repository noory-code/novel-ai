---
name: init
description: One-step Distill onboarding for a new project.
metadata:
  version: "1.0.0"
  category: setup
  type: unit
  style: tool
  triggers: [distill init, initialize distill, setup distill, distill onboarding]
  uses: [mcp__distill__init]
---

# /distill:init

One-step onboarding: creates config, scans environment, and reports directories to ingest.

## Usage

```
/distill:init
```

## MCP Tool

Call `mcp__distill__init` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | string | None | Override scope: `global`, `workspace`, or `project` |

## What it does

1. Creates `.distill/config.json` if missing
2. Scans `.claude/` for existing rules, skills, and agents
3. Reports any directories configured in `sources.dirs` for follow-up ingest

## After init

Run `/distill:ingest <path>` for each reported directory to populate the knowledge store.
