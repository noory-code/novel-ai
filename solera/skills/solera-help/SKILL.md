---
name: solera-help
user-invocable: true
description: Explain what Solera is, list all available skills, and guide the first step.
metadata:
  version: "3.1.0"
  category: meta
  type: unit
  style: guide
  triggers: [what is solera, solera help, solera skills, how to use solera, solera get started]
  uses: []
---

# Solera Help (v4)

> Three-axis project workflow — **Living** (Identity, Personas, Journeys, Narratives, Concepts), **Time-bound** (Milestones, Stories, Action Items), **Immutable** (Releases).

## Overview

Solera turns natural-language project intent into deterministic, AI-executable work. Humans draw Concepts (the living map) and agree on Milestones. AI decomposes Stories into Action Items, runs each as a single commit, and proposes updates to the Living map at wrap-up — subject to human approval. Achieved Milestones are frozen into immutable Releases.

Core flow: **계획 → 일 → 결과 확정.**
Core collaboration: four moments — Setup → Concept Drawing → Milestone Agreement → Work → Milestone Reached.

Run `/solera-handoff` before ending a session to update `HANDOFF.md`, so the next contributor (or the same developer tomorrow) can resume with zero coordination.

## Skills

### Living Axis — human-led drawing

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-write-identity` | "Define service identity", "write mission statement" | `identity/mission.md`, `core-values.md`, `vision_1.md` |
| `solera-write-persona` | "Draw a persona", "add a persona", "update persona" | `personas/{id}.md` (Identity, Goals, Pains, Triggers, Quotes, Channels, Related); `personas/_index.md` |
| `solera-write-journey` | "Draw a journey", "add a user journey", "update journey" | `journeys/{id}.md` (Trigger, Steps table, Outcome, Related — `walks` one Persona); `journeys/_index.md` |
| `solera-write-narrative` | "Write a narrative", "write a user story", "JTBD", "propose concept from narrative" | `narratives/{id}.md` (Statement, Context, Acceptance Cues — `about` 1+ Personas, optional `in_journey`, optional `proposes` Concepts); `narratives/_index.md` |
| `solera-write-concept` | "Draw a concept", "update concept", "deprecate concept" | `concepts/{id}.md` (Intent, Current Design, Current Shape, Health, Contributions); `concepts/_index.md` |

### Time-bound Axis — human–AI agreement, AI execution

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-write-milestone` | "Agree on milestone scope", "write a milestone" | `milestones/{id}.md` with Scope, AI Analysis, Agreement Log, Exit Criteria |
| `solera-write-story` | "Write a Story", "break Story into Action Items" | `stories/{id}-{name}/_story.md`, `ACT-NNN-{name}.md`, `RETROSPECTIVE.md` |
| `solera-execute-action-item` | "Start an Action Item", "ACT-NNN" | Code/doc changes + one git commit per ACT |

### Immutable Axis — freeze reached Milestones

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-release` | "Cut a release", "freeze milestone" | `releases/{tag}/README.md`, `concepts-snapshot/`, `stories-manifest.md`, `.released` marker |

### Workflow

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-manage-workflow` | "What should I work on", "show current progress" | `progress.md` updates; reads and drives each work item's `## Workflow` |
| `solera-create-pr` | "Open a PR", "merge the Story" | GitHub PR via `gh pr create`, squash merge, branch deletion |
| `solera-publish-artifacts` | "Publish Story artifacts" | persona / service-map / journey / use-case / domain-model promoted to `catalog/published/`; Concept Related Artifacts updated |
| `solera-handoff` | "Run handoff", "save handoff" | `HANDOFF.md` with full session context |

### Migration

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-migrate-v2` | "Migrate v2 to v3", "upgrade solera workspace" | `_v2-archive/` freeze, v3 skeleton, Concept drafts, Story flattening, `releases/v2-final/` |

### Meta (system skills)

| Skill | Trigger phrase | Produces |
|-------|----------------|----------|
| `solera-init` | "Set up solera", "initialize solera" | `.claude/rules/solera-workflow.md`, `.solera/` workspace structure, `progress.md` |
| `solera-help` | "Help", "list skills", "what can solera do" | Skill overview and quick-start guidance |
| `solera-edit-skill` | "Create a skill", "edit a skill" | `.claude/skills/{name}/SKILL.md` |
| `solera-edit-rule` | "Create a rule", "add a coding rule" | `.claude/rules/{name}.md` |
| `solera-edit-command` | "Create a command", "add a slash command" | `.claude/commands/{name}.md` |
| `solera-edit-agent` | "Create an agent", "define a subagent" | `.claude/agents/{name}.md` |

## Quick Start

**First time using Solera — say:**

> Initialize Solera for this project.

This installs the workflow rule and creates the `.solera/` workspace structure (`identity/`, `personas/`, `journeys/`, `narratives/`, `concepts/`, `milestones/`, `stories/`, `releases/`, `catalog/published/`).

**Then establish identity:**

> Write the identity for this project.

**Draw who the service is for (Living Axis — upstream of Concepts):**

> Draw a Persona called `small-cafe-owner`.
> Draw a Journey `first-time-checkout` walked by `small-cafe-owner`.
> Write a Narrative about `small-cafe-owner` in journey `first-time-checkout`.

Personas, Journeys, and Narratives pressure Concept design. AI proposes observations but never invents who the user is, what they walk through, or what they want — those are the human's drawings.

**Draw the first Concept:**

> Draw a Concept called `authentication`.

Solera asks for the Intent (you provide it — AI never invents it) and Current Design, surfaces observations from existing artifacts, and writes `concepts/authentication.md`.

**Agree on next scope:**

> Write a Milestone `mvp` covering authentication, onboarding, and liquor-search.

AI reads each Concept's current state and produces an analysis round; you revise; loop until agreed.

**Start work:**

> Write Story US-001 `google-login` contributing to authentication, belonging to mvp.

Solera decomposes to Action Items, runs them as commits, and at Wrap-up proposes Current Shape updates to each contributed Concept for your approval.

**Freeze the Release when ready:**

> Mark mvp as released, then cut release v0.1-mvp.

**Resume after a break:**

> Resume where we left off.

Solera reads `HANDOFF.md` and continues from the exact step it stopped at.

## Upgrading from v2?

If you have an existing v2 project (with `workspace/phase/`, `workspace/initiative/`, `_goal.md`, `_epic.md`), run:

> Migrate this v2 project to v3.

Solera invokes `solera-migrate-v2`, which freezes v2 data to `_v2-archive/`, scaffolds v3, proposes Concepts from v2 Goals/Epics, and moves completed Stories with `contributes_to` tags — every step blocking for your approval.
