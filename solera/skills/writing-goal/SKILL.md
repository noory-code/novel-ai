---
name: writing-goal
description: Goal document writing. Creates Service Map, Persona, Journey (rough) → decomposes into Epics.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Goal elaboration, Goal start, decompose into Epics]
  uses: [writing-identity, writing-epic, catalog-transition]
---

# Writing Goal

> Writes _goal.md and decomposes into Epics.

## Prerequisites

- `published/identity/mission.md` exists → if not, invoke writing-identity
- The corresponding Goal must be assigned in the Phase README → if not, invoke writing-phase

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal name | search-liquor |
| **goal_type** | N | Feature \| Enabler (default: Feature) | Enabler |
| **project_path** | Y | Project workspace root | banas/workspace |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | _goal.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/_goal.md` |
| Create | Service Map (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/service-map/index.md` |
| Create | Persona (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/*.md` |
| Create | Persona Relationship (Feature, 2+ personas) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/relationship.md` |
| Execute | Epic document | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/epics/{NN}-{name}/_epic.md` |
| Wrap-up | RETRO.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/RETRO.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-identity` | Create identity if it does not exist | Setup |
| `writing-epic` | Elaborate each Epic and decompose into Stories | Execute |
| `catalog-transition` | Move artifacts/ → published/ | Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `published/identity/mission.md` exists → if not, invoke writing-identity
   - [ ] Confirm Goal information from Phase README (period, objectives)
   - [ ] Create `goals/{goal_id}-{name}/` folder
   - [ ] Create `goals/{goal_id}-{name}/artifacts/` folder

2. **Confirm Goal type**
   - Feature → proceed in order from step 3
   - Enabler → skip step 3, write Journey as Steps only (briefly) in step 4

3. **Create Service Map, Persona** (Feature only)
   - [ ] Write Service Map → ref: [assets/service-map.md](assets/service-map.md)
   - [ ] Persona profile, goals, Pain Points → ref: [assets/persona.md](assets/persona.md)
   - [ ] If 2 or more personas, create persona-relationship.md → ref: [assets/persona-relationship.md](assets/persona-relationship.md)

4. **Journey + Epic decomposition + write _goal.md**
   - [ ] Define Journey per Persona (Enabler: write Steps only briefly)
   - [ ] Map Journey → Epic, assign numbers (01, 02, ...)
   - [ ] Write _goal.md → ref: [assets/goal-template.md](assets/goal-template.md)

5. **Execute**
   - [ ] Invoke writing-epic for each Epic (Setup → Create → Execute → Wrap-up)
   - [ ] Invoke workflow-pr upon Epic completion → PR to parent branch
   - [ ] Confirm all Epics complete

6. **Goal Wrap-up**
   - [ ] Confirm all Epic statuses ✅
   - [ ] Write RETRO.md → ref: [assets/retro.md](assets/retro.md)
   - [ ] Invoke catalog-transition (artifacts/ → published/)
   - [ ] _goal.md status → ✅

## Folder Structure

```
{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/
├── _goal.md
├── RETRO.md          # Created at Wrap-up
├── artifacts/
│   ├── service-map/index.md    # Feature only
│   └── persona/*.md            # Feature only
└── epics/{NN}-{name}/
    └── _epic.md
```

## Completion Checklist

- [ ] _goal.md created
- [ ] If Feature: Service Map, Persona created
- [ ] If Feature + 2 or more Personas: persona-relationship.md created
- [ ] Journey (rough) written
- [ ] Epic decomposition complete
- [ ] (Execute) writing-epic invoked for all Epics
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) catalog-transition complete
- [ ] (Wrap-up) _goal.md status ✅
