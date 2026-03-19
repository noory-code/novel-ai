---
name: solera-manage-workflow
user-invocable: true
description: Know what to work on next — track progress, pick up where you left off, or close out a completed item.
metadata:
  version: "5.0.0"
  category: workflow
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [what should I work on, mark work complete, show current progress, update progress, write a retrospective, next task]
  uses: [solera-write-identity, solera-write-phase, solera-write-goal, solera-write-epic, solera-write-story, solera-execute-action-item, solera-publish-artifacts]
---

# Workflow Manage (Supervisor)

> The workflow manager **reads and executes — it does not define**.
> The `## Workflow` section of each work item template is the SSOT.

## Common Rules

- [conventions.md](assets/conventions.md) (hierarchy, Git branches, folder structure, status values)
- [lifecycle.md](assets/lifecycle.md) (Workflow pattern description)

## Prerequisites

- `[project]/progress.md` exists; if not, initialize it (ref: [assets/progress.md](assets/progress.md))

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
3. Execute each step of the Workflow in order **(BLOCKING: execute each step sequentially)**
4. If document writing is required, invoke write-* skills **(BLOCKING: proceed to next step after skill completes)**
5. Update progress.md

### complete — Complete work item

1. Read the target work item
2. Execute the latter steps of `## Workflow` (completion check, status change, etc.) **(BLOCKING: execute sequentially)**
3. If the item is an Epic or Goal, write RETRO.md
4. Update progress.md
5. Decide the next work item

### check — Check current status

1. Read progress.md
2. Return the current Phase, Goal, Epic, and Story

### next — Decide next work

1. Story complete and Epic has remaining Stories → start the next Story **(BLOCKING)**
2. Epic complete and Goal has remaining Epics → write an Epic retrospective, then start the next Epic **(BLOCKING)**
3. Goal complete → write a Goal retrospective, confirm artifacts/ is empty (promoted during Goal Create and Epic Wrap-ups)
4. Otherwise → continue current work

## Responsibilities

| Role | Skill |
|------|-------|
| **Document writing** | solera-write-identity, solera-write-phase, solera-write-goal, solera-write-epic, solera-write-story, solera-execute-action-item |
| **Execution supervision** | solera-manage-workflow |
| **Artifact promotion** | solera-publish-artifacts (invoked at Goal Create and Epic Wrap-up) |

## Supervision Principles

- Reads the work item's `## Workflow` as the SSOT
- Does not define procedures directly — follows procedures defined in the template
- Delegates document writing to write-* skills
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

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| progress.md missing | `{project}/progress.md` file not found | Initialize from [assets/progress.md](assets/progress.md) template | Continue after file creation |
| work_item file missing | Specified _goal.md/_epic.md/_story.md not found | Display error message, request file path verification | Skill halted, resume after correct path is provided |
| Workflow section missing | Work item has no `## Workflow` section | Apply default workflow pattern (ref: lifecycle.md) | Continue (using default pattern) |
| write-* skill invocation failed | Sub-skill invocation error | Display failed skill name, request manual execution | Step halted, resume after manual resolution |
| Status mismatch | Story is ✅ but Epic is 🔄 | Display mismatched items, request status sync | Halted before next work decision, resume after manual sync |
| No next work | All work complete, next invoked | Display "All work complete" message | Skill completes normally |
| RETRO.md writing failed | Retrospective writing error on Epic/Goal completion | Verify template path, request manual writing | Complete step halted, resume after manual writing |
| progress.md update failed | File write permission error | Verify permissions, instruct `chmod 644 progress.md` | Skill halted, retry after permission fix |

## Completion Checklist

- [ ] Read the Workflow section of the work item?
- [ ] Executed Workflow steps in order?
- [ ] Updated progress.md?
- [ ] Wrote a retrospective upon completion? (Epic/Goal)
- [ ] Decided the next work item?
