---
name: writing-phase
description: Phase document writing. Distributes Initiative Goals by quarter → tracks Goal execution. Triggers - "Phase definition", "Phase start", "quarterly planning".
metadata:
  version: "2.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Phase definition, Phase start, quarterly planning]
  uses: [writing-goal]
---

# Writing Phase

> Writes Phase README.md and tracks Goal execution.

## Prerequisites

- `workspace/initiative/[year]/roadmap.md` exists → if not, request from user

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **phase_id** | Y | Phase ID | 2026-P1-foundation |
| **year** | Y | Initiative year | 2026 |
| **project_path** | Y | Project workspace root | banas/workspace |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Phase README | `{project_path}/phase/{phase_id}/README.md` |
| Create | Goal folder structure | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/` |
| Wrap-up | Phase summary | `{project_path}/phase/{phase_id}/SUMMARY.md` |
| Wrap-up | Phase retrospective | `{project_path}/phase/{phase_id}/RETRO.md` |
| Wrap-up | progress.md update | `{project_path}/progress.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-goal` | Elaborate each Goal and decompose into Epics | Execute |
| `catalog-transition` | Move artifacts → catalog on Goal completion | Execute (within Goal) |

## Procedure

1. **Verify roadmap**
   - [ ] Read `{project_path}/initiative/{year}/roadmap.md`
   - [ ] Extract Goals list for this Phase from the Phase planning table
   - [ ] No Goals → confirm with user

2. **Create Phase folder**
   - [ ] Create `{project_path}/phase/{phase_id}/`
   - [ ] Create `{project_path}/phase/{phase_id}/goals/`

3. **Write README.md** → ref: [assets/phase-template.md](assets/phase-template.md)
   - [ ] Overview table (period, objectives)
   - [ ] Goals table (Goals extracted from roadmap)
   - [ ] Completion criteria (key criteria per Goal)
   - [ ] Workflow section (template as-is)

4. **Create Goal folder structure**
   - [ ] Create `goals/{goal_id}-{name}/` for each Goal
   - [ ] Prepare to invoke writing-goal

5. **Phase Wrap-up**
   - [ ] Confirm all Goal statuses ✅
   - [ ] Confirm catalog-transition completed for each Goal (moved to `workspace/catalog/`)
   - [ ] Write SUMMARY.md (overall Goal outcomes, catalog artifact list, handoff notes for next Phase)
   - [ ] Write RETRO.md → ref: [assets/retro.md](assets/retro.md)
   - [ ] README.md status → ✅, update progress
   - [ ] Update progress.md

## Folder Structure

```
{project_path}/phase/{phase_id}/
├── README.md
├── SUMMARY.md      # Created at Wrap-up (template TBD)
├── RETRO.md        # Created at Wrap-up
└── goals/
    ├── {goal_id}-{name}/
    │   ├── _goal.md
    │   ├── artifacts/    # During Goal → moved via catalog-transition
    │   └── epics/
    └── ...
```

## Completion Checklist

- [ ] README.md created
- [ ] Goals table includes all Goals from roadmap
- [ ] Folder structure created for each Goal
- [ ] writing-goal transition prepared
- [ ] (Wrap-up) All Goal catalog-transitions confirmed complete
- [ ] (Wrap-up) SUMMARY.md written
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) progress.md updated
