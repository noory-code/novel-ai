---
name: distill-help
user-invocable: true
description: Explain what Distill is, list all available skills, and guide the first step.
metadata:
  version: "1.0.0"
  category: meta
  type: reference
  style: guide
  triggers: [what is distill, distill help, distill commands, how to use distill, distill get started]
  uses: []
---

# /distill-help

> Extract and recall reusable knowledge from Claude Code conversations.

## Overview

Distill captures decisions, patterns, and solutions from your Claude sessions and makes them searchable across projects. Knowledge is stored in three scopes — global (`~/.distill/`), workspace (git root), and project — so the right context is always available without polluting unrelated projects.

After setup, Distill automatically extracts knowledge at session end via a hook. After 20 chunks accumulate, crystallize runs automatically to generate rules and skills.

## Available Skills

| Skill | What it does |
|-------|-------------|
| `/distill-init` | One-step onboarding: create config, scan environment |
| `/distill-recall` | Hybrid semantic + keyword search across all stored knowledge |
| `/distill-learn` | Extract knowledge from a conversation transcript |
| `/distill-ingest` | Extract knowledge from markdown/text files or directories |
| `/distill-profile` | Show knowledge statistics, environment summary, hook status |
| `/distill-digest` | Analyze for duplicates and stale entries |
| `/distill-memory` | Manage entries: promote, demote, delete, or crystallize into rules |

## Quick Start

**First time — say:**

> Initialize distill for this project.

**Search your knowledge — say:**

> Recall how I handle authentication in this project.

**Manually crystallize into rules — say:**

> Crystallize my distill knowledge into rules.

## How Knowledge Becomes Rules

1. **Extraction**: Hooks automatically extract knowledge at session end
2. **Accumulation**: Chunks stored in SQLite with confidence scores
3. **Crystallize** (auto after 20 chunks, or manual via `/distill-memory`):
   - High confidence + broadly applicable → **rule** (`.claude/rules/distill-*.md`)
   - Procedural, 3+ steps, has trigger → **skill** (`.claude/skills/distill-*/SKILL.md`)
   - Low confidence or niche → stays in **store** (searchable via `/distill-recall`)
