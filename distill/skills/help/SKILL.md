---
name: help
description: Explain what Distill is, list all available commands, and guide the first step.
metadata:
  version: "1.0.0"
  category: meta
  type: reference
  style: guide
  triggers: [what is distill, distill help, distill commands, how to use distill, distill get started]
  uses: []
---

# Distill Help

> Extract and recall reusable knowledge from Claude Code conversations.

## Overview

Distill captures decisions, patterns, and solutions from your Claude sessions and makes them searchable across projects. Knowledge is stored in three scopes — global (`~/.distill/`), workspace (git root), and project — so the right context is always available without polluting unrelated projects.

After setup, Distill automatically extracts knowledge at session end via a hook. No manual action needed.

## Commands

| Command | What it does |
|---------|-------------|
| `/distill init` | One-step onboarding: create config, install skills and hooks |
| `/distill recall <query>` | Semantic search across all stored knowledge |
| `/distill learn <path> <session_id>` | Extract knowledge from a transcript file |
| `/distill ingest <path>` | Extract knowledge from a markdown or text file |
| `/distill crystallize` | Consolidate stored chunks into rule/skill/agent files |
| `/distill profile` | Show knowledge statistics (entry count, scope breakdown) |

## Quick Start

**First time — say:**

> Initialize distill for this project.

Distill runs `init`, creates `.distill/config.json`, and installs the session-end hook. From this point, knowledge is extracted automatically after every session.

**Search your knowledge — say:**

> Recall how I handle authentication in this project.

**After accumulating entries — say:**

> Crystallize my distill knowledge into rules.
