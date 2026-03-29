---
name: solera-write-epic
user-invocable: true
description: Scope an Epic — write use cases, define the concept, and decompose into Stories ready to implement.
metadata:
  version: "5.0.1"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write an Epic, plan an Epic, start an Epic, break Epic into Stories, define Epic scope, draft concept]
  uses: [solera-write-story, solera-publish-artifacts, solera-create-pr]
---

# Writing Epic

> Writes _epic.md and decomposes the Epic into Stories.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `solera-write-identity` with Skill tool
- `_goal.md` exists
  - If not: check `{goal_path}/_goal.md` with Glob tool → invoke `solera-write-goal` with Skill tool passing:
    `goal_id={goal_id}, goal_name={goal_id}, project_path={project_path}, phase_id={phase_id}`
    (ask user to confirm `goal_name` if it differs from `goal_id`)
  - If `phase_id` is unknown: ask the user before proceeding
  - New project: run `solera-write-identity` first to establish `identity/` and `initiative/{year}/goals.md`
- The corresponding Epic must be assigned in _goal.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1 |
| **goal_name** | Y | Parent Goal name | search-liquor |
| **epic_name** | Y | Epic name | 01-auth |
| **epic_type** | N | Feature \| Enabler (default: Feature) | Enabler |

## Output

| Step | Output | Nature | Path |
|------|--------|--------|------|
| Setup | _epic.md | Final | `{goal_path}/epics/{epic_name}/_epic.md` |
| UseCase | UC-NNN.md (Feature only) | Intermediate (artifacts) | `{goal_path}/artifacts/use-case/UC-NNN-{name}.md` |
| Concept | domain.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/domain.md` |
| Concept | entities/*.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/entities/{entity}.md` |
| Story | _story.md | Final | `{goal_path}/epics/{epic_name}/{US\|TS}-NNN-{name}/_story.md` |
| Wrap-up | RETROSPECTIVE.md | Final | `{goal_path}/epics/{epic_name}/RETROSPECTIVE.md` |

> `{goal_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}`
> artifacts = intermediate outputs. Promoted to published/ via solera-publish-artifacts at Epic Wrap-up.

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `solera-write-story` | Elaborate each Story and decompose it into Action Items | Execute |
| `solera-publish-artifacts` | Promote Epic-level artifacts (use-case, concept) to published/ | Wrap-up |
| `solera-create-pr` | Create a PR upon Story/Epic completion | Execute, Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `{goal_path}/_goal.md` exists with Glob tool
     - If not: `Skill(name="solera-write-goal", args={"project_path": "{project_path}", "year": "{year}", "phase_id": "{phase_id}", "goal_id": "{goal_id}", "goal_name": "{goal_name}", "goal_type": "{goal_type or default Feature}"})`
       (ask user to confirm `goal_name` if it differs from `goal_id`) **(BLOCKING: resume after Goal creation completes)**
   - [ ] Create `epics/{epic_name}` branch (from Goal branch)
   - [ ] Read `{project_path}/workspace/team-process.md` if it exists
     - Extract `workflow_gates` section for gate checks in Steps 2–3
   - [ ] Create `{goal_path}/epics/{epic_name}/` folder
   - [ ] Create _epic.md draft — ref: [assets/epic-template.md](assets/epic-template.md)
   - [ ] Status → 🔄

2. **Create Use Case** (Feature only, skip for Enabler)
   - [ ] **Gate check**: If `workflow_gates.epic.use_case` is set and condition is not met:
     → Display the required condition to user
     → **(BLOCKING: skill pauses until condition is fulfilled)**
   - [ ] Define the Actor (person or system)
   - [ ] Define the Goal (measurable objective)
   - [ ] Write the basic flow (step by step)
   - [ ] Write alternative and exception flows
   - [ ] Ref: [assets/use-case.md](assets/use-case.md)

3. **Create Concept**
   - [ ] **Gate check**: If `workflow_gates.epic.concept` is set and condition is not met:
     → Display the required condition to user
     → **(BLOCKING: skill pauses until condition is fulfilled)**
   - [ ] Derive core concepts, then write or update domain.md — ref: [assets/concept.md](assets/concept.md)
   - [ ] Write a detailed description for each Entity — ref: [assets/entity.md](assets/entity.md)
   - [ ] Add a relationship diagram (Mermaid classDiagram)
   - domain.md rule: the first Epic creates it; subsequent Epics **update** it rather than overwrite it
   - concept.md = full version template, entity.md = quick reference skeleton

4. **Story decomposition and complete _epic.md**
   - [ ] Map Use Cases to Stories (Feature) or technical tasks to Stories (Enabler)
   - [ ] Assign Story IDs (US: User Story, TS: Technical Story)
   - [ ] Estimate the expected commit count for each Story
   - [ ] Complete the Stories table in _epic.md and define completion criteria

5. **Execute**
   - [ ] Extract incomplete (⏳ or no status) Stories from the Stories table in `_epic.md`
   - [ ] Execute each Story in order **(BLOCKING: wait for each Story to complete, execute sequentially)**:
     ```python
     Skill(name="solera-write-story", args={
       "project_path": "{project_path}",
       "year": "{year}",
       "phase_id": "{phase_id}",
       "goal_id": "{goal_id}",
       "goal_name": "{goal_name}",
       "epic_name": "{epic_name}",
       "epic_type": "{epic_type}",
       "story_id": "{US|TS-NNN}",
       "story_name": "{name}",
       "story_type": "{US|TS}"
     })
     → Confirm _story.md created + status ✅ before proceeding to next Story
     ```
   - [ ] Merge to the Epic branch upon Story completion
   - [ ] Proceed to Step 6 after confirming all Story statuses ✅

6. **Wrap-up**
   - [ ] Confirm all Story statuses ✅ (return to Step 5 if any are incomplete)
   - [ ] Invoke solera-publish-artifacts to promote Epic-level artifacts (use-case, concept) to published/ **(BLOCKING: proceed to next step after promotion completes)**
   - [ ] Write RETROSPECTIVE.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set _epic.md status to ✅
   - [ ] `Skill(name="solera-create-pr")` **(BLOCKING: skill ends after PR creation completes)** → create PR to parent branch (Goal)

## Folder Structure

```
{goal_path}/
├── artifacts/                # Intermediate outputs
│   ├── use-case/UC-NNN-{name}.md
│   └── concept/
│       ├── domain.md
│       └── entities/{entity}.md
└── epics/{epic_name}/
    ├── _epic.md
    ├── RETROSPECTIVE.md              # Created at Wrap-up
    └── {US|TS}-NNN-{name}/
        └── _story.md
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md missing | `published/identity/mission.md` not found | Verify with Glob, then invoke `solera-write-identity` via Skill tool | Resume this skill after identity creation |
| _goal.md missing | `{goal_path}/_goal.md` not found | Verify with Glob, then invoke `solera-write-goal` via Skill tool (pass project_path, year, phase_id, goal_id, goal_name, goal_type; confirm goal_name with user) | Resume this skill after Goal creation |
| phase_id unknown | phase_id parameter not provided | Request phase_id input from user | Halted until parameter is provided |
| Epic unassigned | No Epic entry in _goal.md | Display error message, request _goal.md update | Skill halted, resume after manual fix |
| Branch creation failed | git error (conflict, permissions, etc.) | Display git error message, request manual resolution | Skill halted, resume after resolution |
| domain.md update conflict | Conflict between existing domain.md and new content | Highlight areas requiring merge, request manual merge from user | Concept step halted, resume after manual merge |
| solera-write-story failed | Sub-skill invocation failed | Record the failed Story, notify user | Skip the Story and continue, or halt |
| solera-publish-artifacts failed | Epic-level artifact promotion failed | Display failed file list, request manual move | Wrap-up halted, resume after manual resolution |
| solera-create-pr failed | PR creation failed | Display PR creation error, request manual PR creation | Wrap-up halted, complete after manual PR creation |

## Examples

### Example: Full Feature Epic execution flow

#### Skill invocation

```python
Skill(name="solera-write-epic", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui",
  "epic_type": "Feature"
})
```

#### Files created at each step

**1. After Setup**
```
goals/G1-search-liquor/epics/01-search-ui/
└── _epic.md              (draft, status: 🔄)
```

**2. After Use Case creation**
```
goals/G1-search-liquor/
├── artifacts/
│   └── use-case/
│       ├── UC-001-basic-search.md
│       └── UC-002-filter-search.md
└── epics/01-search-ui/
    └── _epic.md
```

**3. After Concept creation**
```
goals/G1-search-liquor/
├── artifacts/
│   ├── use-case/...
│   └── concept/
│       ├── domain.md
│       └── entities/
│           ├── search-query.md
│           ├── filter.md
│           └── result-set.md
└── epics/01-search-ui/
    └── _epic.md
```

**4. After Story decomposition (_epic.md updated)**
```markdown
# _epic.md

...
## Stories

| ID | Name | UC | Commits | Status |
|----|------|----|---------|--------|
| US-001 | search-input | UC-001 | 3 | ⏳ |
| US-002 | filter-ui | UC-002 | 2 | ⏳ |
| TS-001 | api-integration | - | 4 | ⏳ |
```

**5. Execute intermediate state (Story US-001 complete)**
```
goals/G1-search-liquor/epics/01-search-ui/
├── _epic.md              (US-001: ✅, US-002: 🔄, TS-001: ⏳)
├── US-001-search-input/
│   ├── _story.md         (status: ✅)
│   ├── RETROSPECTIVE.md
│   ├── ACT-001-create-component.md
│   ├── ACT-002-add-validation.md
│   └── ACT-003-write-tests.md
└── US-002-filter-ui/
    ├── _story.md         (status: 🔄)
    └── ACT-001-filter-component.md
```

**6. After Wrap-up (all Stories ✅)**
```
goals/G1-search-liquor/epics/01-search-ui/
├── _epic.md              (status: ✅)
├── RETROSPECTIVE.md
├── US-001-search-input/...   (✅)
├── US-002-filter-ui/...      (✅)
└── TS-001-api-integration/...  (✅)
```

#### Sub-skills invoked during execution

```python
# Write Story US-001
Skill(name="solera-write-story", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui",
  "epic_type": "Feature",
  "story_id": "US-001",
  "story_name": "search-input",
  "story_type": "US"
})
# → Create _story.md, decompose Action Items, all ACTs executed then ✅

# Repeat for Story US-002, TS-001...

# After Epic completion, promote Epic-level artifacts
Skill(name="solera-publish-artifacts", args={
  "project_path": "/Users/myname/workspace/myapp",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor"
})
# → use-case, concept → published/

# Create PR
Skill(name="solera-create-pr")
# → PR from Epic branch to Goal branch
```

#### Final output state

- `_epic.md` status: ✅
- All Story statuses: ✅
- `RETROSPECTIVE.md` exists
- PR created to Goal branch

## Completion Checklist

- [ ] _epic.md created
- [ ] If Feature: Use Case written
- [ ] Concept (domain.md, entities) written or updated
- [ ] Story decomposition complete
- [ ] (Execute) solera-write-story invoked for all Stories
- [ ] (Wrap-up) solera-publish-artifacts invoked for Epic-level artifacts
- [ ] (Wrap-up) RETROSPECTIVE.md written
- [ ] (Wrap-up) _epic.md status ✅
- [ ] (Wrap-up) solera-create-pr invoked
