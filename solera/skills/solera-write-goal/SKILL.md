---
name: solera-write-goal
user-invocable: true
description: Define what success looks like for a Goal — map the service, identify personas, sketch the journey, and break it into Epics.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write a Goal, start a Goal, plan a Goal, break Goal into Epics, elaborate on a Goal]
  uses: [solera-write-identity, solera-write-epic, solera-publish-artifacts]
---

# Writing Goal

> Writes the _goal.md file and decomposes the Goal into Epics.

## Prerequisites

- `published/identity/mission.md` exists; if not, invoke solera-write-identity
- The corresponding Goal must be assigned in the Phase README
  - If not: invoke `solera-write-phase` with Skill tool passing:
    `project_path={project_path}, phase_id={phase_id}, year={first 4 chars of phase_id, e.g. "2026-P1-foundation" → "2026"}`

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal name | search-liquor |
| **goal_type** | N | Feature \| Enabler (default: Feature) | Enabler |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | _goal.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/_goal.md` | Final |
| Create | Service Map (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/service-map/index.md` | Intermediate |
| Create | Persona (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/*.md` | Intermediate |
| Create | Persona Relationship (Feature, 2+ personas) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/relationship.md` | Intermediate |
| Execute | Epic document | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/epics/{NN}-{name}/_epic.md` | Final |
| Wrap-up | RETRO.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/RETRO.md` | Final |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `solera-write-identity` | Create identity if it does not exist | Setup |
| `solera-write-epic` | Elaborate each Epic and decompose it into Stories | Execute |
| `solera-publish-artifacts` | Promote Goal-level artifacts (service-map, persona, journey) to published/ | Create (after Step 4) |

## Procedure

1. **Setup**
   - [ ] Confirm `published/identity/mission.md` exists; if not, invoke solera-write-identity **(BLOCKING: this skill pauses until identity creation completes)**
   - [ ] Confirm `{project_path}/phase/{phase_id}/README.md` exists with Glob tool
     - If not: `Skill(name="solera-write-phase", args={"project_path": "{project_path}", "year": "{year}", "phase_id": "{phase_id}"})` **(BLOCKING: resumes after Phase creation completes)**
   - [ ] Confirm Goal information from the Phase README (period, objectives)
   - [ ] Create `goals/{goal_id}-{name}/` folder
   - [ ] Create `goals/{goal_id}-{name}/artifacts/` folder

2. **Confirm Goal type**
   - For Features, proceed in order from Step 3
   - For Enablers, skip Step 3 and write the Journey as Steps only (briefly) in Step 4

3. **Create Service Map and Personas** (Feature only)
   - [ ] Write the Service Map — ref: [assets/service-map.md](assets/service-map.md)
   - [ ] Write Persona profile, goals, and Pain Points — ref: [assets/persona.md](assets/persona.md)
   - [ ] If there are 2 or more Personas, create persona-relationship.md — ref: [assets/persona-relationship.md](assets/persona-relationship.md)

4. **Journey, Epic decomposition, and _goal.md**
   - [ ] Read `{project_path}/workspace/team-process.md` if it exists — check `workflow_gates` for this Goal's prerequisites
   - [ ] If any `workflow_gates.*` condition is set and not met:
     → Display the unmet gate conditions to user
     → **(BLOCKING: skill pauses until all relevant conditions are fulfilled)**
   - [ ] **Add** a Journey for each relevant Persona for this Goal (for Enablers, write Steps only, briefly)
     - File naming: `artifacts/journey/{goal_id}-{persona_name}.md`
     - **Never modify existing journey files** — each Goal adds new journey files (OCP: open for extension, closed for modification)
     - If a prior journey exists for the same persona, the new file extends it with additional steps
   - [ ] Map Journey steps to Epics and assign numbers (01, 02, ...)
   - [ ] Write _goal.md — ref: [assets/goal-template.md](assets/goal-template.md)
   - [ ] Invoke solera-publish-artifacts to promote Goal-level artifacts (service-map, persona, journey) to published/ **(BLOCKING: promotion must complete before Execute)**

5. **Execute**
   - [ ] Invoke solera-write-epic for each Epic (Setup → Create → Execute → Wrap-up) **(BLOCKING: wait for each Epic to complete; execute sequentially)**
   - [ ] Invoke solera-create-pr upon Epic completion to create a PR to the parent branch **(BLOCKING: PR must be created before proceeding to next Epic)**
   - [ ] Confirm all Epics are complete

6. **Goal Wrap-up**
   - [ ] Confirm all Epic statuses ✅
   - [ ] Confirm artifacts/ is empty (all artifacts promoted during Create and Epic Wrap-up steps)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set _goal.md status to ✅

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

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md missing | `published/identity/mission.md` not found | Invoke `solera-write-identity` via Skill tool | Resume this skill after identity creation |
| Phase README missing | `phase/{phase_id}/README.md` not found | Invoke `solera-write-phase` (pass project_path, phase_id, year) | Resume after Phase creation |
| Goal not assigned | Goal info missing from Phase README | Display error, request Phase README update | Skill halted, resume after manual fix |
| goal_type unclear | Cannot determine Feature/Enabler | Default to Feature, ask user to confirm | Adjust if user overrides |
| Folder creation failed | Permission error or path issue | Display error, ask user to check permissions | Skill halted, return error state |
| solera-write-epic failed | Sub-skill invocation failed | Log failed Epic, notify user | Skip that Epic and continue, or halt |
| solera-publish-artifacts failed (Create) | Goal-level artifact promotion failed | List failed files, request manual move | Create step halted, resume after manual fix |
| artifacts/ not empty (Wrap-up) | Unpromoted files remain from Epics | List remaining files, request manual check | Show warning, continue |

## Examples

### Example: Full Feature Goal execution

#### Skill invocation

```python
Skill(name="solera-write-goal", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "goal_type": "Feature"
})
```

#### Files generated per step

**1. After Setup**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (draft, status: 🔄)
└── artifacts/            (empty folder)
```

**2. After Service Map & Personas**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md
└── artifacts/
    ├── service-map/
    │   └── index.md
    └── persona/
        ├── bartender.md
        ├── liquor-enthusiast.md
        └── relationship.md
```

**3. After Epic decomposition (_goal.md updated)**
```markdown
# _goal.md

...
## Epics

| ID | Name | Journey Step | Status |
|----|------|--------------|--------|
| 01 | search-ui | Search input | ⏳ |
| 02 | filter-logic | Apply filters | ⏳ |
| 03 | result-display | View results | ⏳ |
```

**4. After Create (Goal-level artifacts promoted immediately)**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (status: 🔄)
├── artifacts/            (service-map, persona → moved to published/)
└── epics/                (still empty)

published/
├── service-map/index.md           (← promoted from artifacts)
└── persona/
    ├── bartender.md               (← promoted from artifacts)
    └── liquor-enthusiast.md       (← promoted from artifacts)
```

**5. Mid-Execute (Epic 01 complete, Epic-level artifacts also promoted)**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (Epic 01: ✅, Epic 02: 🔄, Epic 03: ⏳)
├── artifacts/            (Epic 01 artifacts → moved to published/)
└── epics/
    ├── 01-search-ui/
    │   ├── _epic.md      (status: ✅)
    │   ├── RETRO.md
    │   └── US-001-search-input/...
    └── 02-filter-logic/
        ├── _epic.md      (status: 🔄)
        └── US-001-filter-setup/...

published/
├── service-map/...       (promoted at Goal Create)
├── persona/...           (promoted at Goal Create)
├── use-case/...          (promoted at Epic 01 Wrap-up)
└── concept/...           (promoted at Epic 01 Wrap-up)
```

**6. After Wrap-up (all Epics ✅, artifacts/ empty)**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (status: ✅)
├── RETRO.md
├── artifacts/            (empty — all promoted)
└── epics/
    ├── 01-search-ui/...  (✅)
    ├── 02-filter-logic/...(✅)
    └── 03-result-display/...(✅)
```

#### Sub-skills invoked during execution

```python
# After Goal Create — promote Goal-level artifacts immediately
Skill(name="solera-publish-artifacts", args={
  "project_path": "/Users/myname/workspace/myapp",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor"
})
# → service-map, persona, journey → published/

# Write Epic 01
Skill(name="solera-write-epic", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui"
})
# → creates _epic.md, decomposes Stories, all Stories completed → ✅

# Create PR for Epic 01
Skill(name="solera-create-pr")
# → PR from Epic branch to Goal branch

# Repeat for Epic 02, 03...
# (solera-publish-artifacts promotes Epic-level artifacts at each Epic Wrap-up)
```

#### Final output state

- `_goal.md` status: ✅
- All Epic statuses: ✅
- `RETRO.md` exists
- `artifacts/` folder empty (promoted incrementally at Goal Create + each Epic Wrap-up)

## Completion Checklist

- [ ] _goal.md created
- [ ] If Feature: Service Map and Personas created
- [ ] If Feature with 2 or more Personas: persona-relationship.md created
- [ ] Preliminary Journey written
- [ ] Epic decomposition complete
- [ ] (Create) solera-publish-artifacts invoked for Goal-level artifacts
- [ ] (Execute) solera-write-epic invoked for all Epics
- [ ] (Wrap-up) artifacts/ is empty
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _goal.md status ✅
