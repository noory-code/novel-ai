---
name: solera-help
description: Explain what Solera is, list all available skills, and guide the first step.
metadata:
  version: "1.0.0"
  category: meta
  type: reference
  style: guide
  triggers: [what is solera, solera help, solera skills, how to use solera, solera get started, solera 뭐야, solera 사용법, solera 어떻게 써, solera 스킬 목록, solera 도움말]
  uses: []
---

# Solera Help

> Layered workflow execution — Phase → Goal → Epic → Story → Action Item.

## Overview

Solera turns natural-language project intent into deterministic, AI-executable work items. Every level of the hierarchy owns its own procedure file, so Claude executes without guessing — from a quarterly Phase down to a single git commit.

Each session ends with an auto-updated `HANDOFF.md`, so the next contributor (or the same developer tomorrow) can resume with zero coordination.

## Skills

### Writing (composition)

| Skill | Trigger phrase | Produces |
|-------|---------------|----------|
| `solera-write-identity` | "Define service identity", "write mission statement" | `identity/mission.md`, `core-values.md`, `vision_1.md`, `initiative/{year}/goals.md` |
| `solera-write-phase` | "Plan the quarter", "define a Phase" | `phase/{id}/README.md`, Goal folder structure |
| `solera-write-goal` | "Write a Goal", "break Goal into Epics" | `_goal.md`, service map, personas |
| `solera-write-epic` | "Write an Epic", "plan an Epic" | `_epic.md`, use cases, domain concepts |
| `solera-write-story` | "Write a Story", "break Story into Action Items" | `_story.md`, `ACT-NNN-{name}.md` files |
| `solera-execute-action-item` | "Start an Action Item", "ACT-NNN" | Code/doc changes + one git commit |

### Workflow

| Skill | Trigger phrase | Produces |
|-------|---------------|----------|
| `solera-manage-workflow` | "What should I work on", "show current progress" | `progress.md` updates; reads and executes each work item's Workflow |
| `solera-create-pr` | "Open a PR", "merge the Epic" | GitHub PR via `gh pr create`, squash merge, branch deletion |
| `solera-transition-catalog` | "Wrap up Goal", "archive completed Goal" | Artifacts moved from `artifacts/` to `published/` |
| `solera-handoff` | "End session", or automatic on session end | `HANDOFF.md` with full session context |

### Meta (system skills)

| Skill | Trigger phrase | Produces |
|-------|---------------|----------|
| `solera-init` | "Set up solera", "initialize solera" | `.claude/rules/solera-workflow.md`, workspace structure, `progress.md` |
| `solera-help` | "Help", "list skills", "what can solera do" | Skill overview and quick-start guidance |
| `solera-edit-skill` | "Create a skill", "edit a skill" | `.claude/skills/{name}/SKILL.md` |
| `solera-edit-rule` | "Create a rule", "add a coding rule" | `.claude/rules/{name}.md` |
| `solera-edit-command` | "Create a command", "add a slash command" | `.claude/commands/{name}.md` |
| `solera-edit-agent` | "Create an agent", "define a subagent" | `.claude/agents/{name}.md` |

## Quick Start

**First time using Solera — say:**

> Initialize Solera for this project.

This installs the workflow rule and creates the workspace structure.

**Then define your service identity:**

**Already have a Phase — continue with:**

> Write Goal G1 for Phase 2026-P1-foundation. The goal is `task-management`.

**Resume after a break:**

> Resume where we left off.

Solera reads `HANDOFF.md` and continues from the exact step it stopped at.
