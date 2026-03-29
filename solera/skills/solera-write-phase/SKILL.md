---
name: solera-write-phase
user-invocable: true
description: Plan a quarter — distribute Goals across a Phase and track which ones are in progress or complete.
metadata:
  version: "3.0.1"
  category: writing
  type: composite
  style: procedural
  triggers: [define a Phase, start a Phase, plan the quarter, set up quarterly goals, write Phase README]
  uses: [solera-write-goal]
---

# Writing Phase

> Writes the Phase README.md and tracks Goal execution.

## Prerequisites

- `workspace/initiative/[year]/roadmap.md` exists; if not, request it from the user

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Phase ID | 2026-P1-foundation |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Phase README | `{project_path}/phase/{phase_id}/README.md` |
| Create | Goal folder structure | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/` |
| Wrap-up | Phase summary | `{project_path}/phase/{phase_id}/SUMMARY.md` |
| Wrap-up | Phase retrospective | `{project_path}/phase/{phase_id}/RETROSPECTIVE.md` |
| Wrap-up | progress.md update | `{project_path}/progress.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `solera-write-goal` | Elaborate each Goal and decompose it into Epics | Execute |
| `solera-publish-artifacts` | Promote artifacts incrementally (at Goal Create and Epic Wrap-up) | Execute (within Goal/Epic) |

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
   - [ ] Prepare to invoke solera-write-goal

5. **Phase Wrap-up**
   - [ ] Confirm all Goal statuses ✅
   - [ ] Confirm artifacts/ is empty for each Goal (promoted incrementally during Goal Create and Epic Wrap-ups)
   - [ ] Write SUMMARY.md (overall Goal outcomes, catalog artifact list, handoff notes for the next Phase)
   - [ ] Write RETROSPECTIVE.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set README.md status to ✅ and update progress
   - [ ] Update progress.md

## Folder Structure

```
{project_path}/phase/{phase_id}/
├── README.md
├── SUMMARY.md      # Created at Wrap-up (see phase-template.md Step 3)
├── RETROSPECTIVE.md        # Created at Wrap-up
└── goals/
    ├── {goal_id}-{name}/
    │   ├── _goal.md
    │   ├── artifacts/    # Promoted incrementally at Goal Create and Epic Wrap-up
    │   └── epics/
    └── ...
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| roadmap.md missing | `initiative/{year}/roadmap.md` file not found | Request roadmap.md from user | Skill halted until file is provided |
| Goals list empty | No Phase plan found in roadmap.md | Request confirmation from user | Continue or halt after user confirmation |
| phase_id format error | phase_id does not match the rule (e.g., YYYY-PX-name) | Display error message with correct format example | Skill halted, request correct phase_id input |
| Folder creation failed | Permission error or path issue | Display error message, request permission check | Skill halted, return error state |
| solera-write-goal failed | Sub-skill invocation failed | Record the failed Goal, notify user | Skip the Goal and continue, or halt |
| artifacts/ not empty | Goal artifacts not fully promoted | Display remaining file list, request manual verification | Display warning and continue |

## Completion Checklist

- [ ] README.md created
- [ ] Goals table includes all Goals from the roadmap
- [ ] Folder structure created for each Goal
- [ ] solera-write-goal invoked for all Goals
- [ ] (Wrap-up) All Goal artifacts/ directories are empty
- [ ] (Wrap-up) SUMMARY.md written
- [ ] (Wrap-up) RETROSPECTIVE.md written
- [ ] (Wrap-up) progress.md updated
