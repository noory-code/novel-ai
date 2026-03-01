---
name: workflow-manage
description: Workflow supervisor. Reads and executes the Workflow of a work item.
metadata:
  version: "4.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [start work, complete work, current work, next work, progress update, write retrospective]
  uses: [writing-phase, writing-goal, writing-epic, writing-story, writing-action-item, catalog-transition]
---

# Workflow Manage (Supervisor)

> The workflow manager **reads and executes — it does not define**.
> The `## Workflow` section of each work item template is the SSOT.

## Common Rules

- [conventions.md](assets/conventions.md) (hierarchy, Git branches, folder structure, status values)
- [lifecycle.md](assets/lifecycle.md) (Workflow pattern description)

## Prerequisites

- `[project]/progress.md` exists → if not, initialize (ref: [assets/progress.md](assets/progress.md))

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **action** | N | Action type | start \| complete \| check \| next |
| **work_item** | N | Target work item path | _goal.md, _epic.md, _story.md |

## Output

| Action | Output | Path |
|--------|--------|------|
| start / complete | progress.md update | `{project}/progress.md` |
| complete (Epic/Goal) | RETRO.md written | `{path}/RETRO.md` |
| next | Next work item decided | — |

## Procedure

### start — Start work item

1. Read the target work item (_goal.md | _epic.md | _story.md)
2. Extract the `## Workflow` section
3. Execute each step of the Workflow in order
4. If document writing is required, invoke writing-* skills
5. Update progress.md

### complete — Complete work item

1. Read the target work item
2. Execute the latter steps of `## Workflow` (completion check, status change, etc.)
3. If Epic/Goal, write RETRO.md
4. Update progress.md
5. Decide next work

### check — Check current status

1. Read progress.md
2. Return current Phase, Goal, Epic, Story

### next — Decide next work

1. Story complete + Epic has remaining Stories → start next Story
2. Epic complete + Goal has remaining Epics → Epic retrospective → start next Epic
3. Goal complete → Goal retrospective → invoke catalog-transition
4. Otherwise → continue current work

## Responsibilities

| Role | Skill |
|------|-------|
| **Document writing** | writing-identity, writing-phase, writing-goal, writing-epic, writing-story, writing-action-item |
| **Execution supervision** | workflow-manage (this skill) |
| **Completion handling** | catalog-transition |

## Supervision Principles

- Reads the work item's `## Workflow` as SSOT
- Does not define procedures directly — follows procedures defined in the template
- Delegates document writing to writing-* skills
- Delegates development work to frontend-*, dev-* skills

## Templates

- [assets/progress.md](assets/progress.md)
- [assets/retro.md](assets/retro.md)
- [assets/status.md](assets/status.md)

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (9 cases) |

## Completion Checklist

- [ ] Read the Workflow section of the work item?
- [ ] Executed Workflow steps in order?
- [ ] Updated progress.md?
- [ ] Wrote a retrospective upon completion? (Epic/Goal)
- [ ] Decided the next work item?
