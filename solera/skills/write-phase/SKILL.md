---
name: write-phase
description: Plan a quarter — distribute Goals across a Phase and track which ones are in progress or complete.
metadata:
  version: "3.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [define a Phase, start a Phase, plan the quarter, set up quarterly goals, write Phase README]
  uses: [write-goal]
---

# Writing Phase

> Writes the Phase README.md and tracks Goal execution.

## Prerequisites

- `workspace/initiative/[year]/roadmap.md` exists; if not, request it from the user

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
| `writing-goal` | Elaborate each Goal and decompose it into Epics | Execute |
| `catalog-transition` | Move artifacts to the catalog upon Goal completion | Execute (within Goal) |

## Procedure

1. **Verify roadmap**
   - [ ] Read `{project_path}/initiative/{year}/roadmap.md`
   - [ ] Extract the Goals list for this Phase from the Phase planning table
   - [ ] If no Goals are found, confirm with the user

2. **Create Phase folder**
   - [ ] Create `{project_path}/phase/{phase_id}/`
   - [ ] Create `{project_path}/phase/{phase_id}/goals/`

3. **Write README.md** — ref: [assets/phase-template.md](assets/phase-template.md)
   - [ ] Overview table (period, objectives)
   - [ ] Goals table (Goals extracted from roadmap)
   - [ ] Completion criteria (key criteria for each Goal)
   - [ ] Workflow section (template as-is)

4. **Create Goal folder structure**
   - [ ] Create `goals/{goal_id}-{name}/` for each Goal
   - [ ] Prepare to invoke writing-goal

5. **Phase Wrap-up**
   - [ ] Confirm all Goal statuses ✅
   - [ ] Confirm catalog-transition completed for each Goal (moved to `workspace/catalog/`)
   - [ ] Write SUMMARY.md (overall Goal outcomes, catalog artifact list, handoff notes for the next Phase)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set README.md status to ✅ and update progress
   - [ ] Update progress.md

## Folder Structure

```
{project_path}/phase/{phase_id}/
├── README.md
├── SUMMARY.md      # Created at Wrap-up (see phase-template.md Step 3)
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
- [ ] Goals table includes all Goals from the roadmap
- [ ] Folder structure created for each Goal
- [ ] writing-goal transition prepared
- [ ] (Wrap-up) All Goal catalog-transitions confirmed complete
- [ ] (Wrap-up) SUMMARY.md written
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) progress.md updated
