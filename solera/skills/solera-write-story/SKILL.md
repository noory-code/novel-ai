---
name: solera-write-story
user-invocable: true
description: Write a Story with clear acceptance criteria, then break it into atomic Action Items — each one a single commit.
metadata:
  version: "9.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write a Story, plan a Story, start a Story, break Story into Action Items, define acceptance criteria]
  uses: [solera-execute-action-item]
---

# Writing Story

> Writes _story.md and decomposes the Story into Action Items.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `solera-write-identity` with Skill tool
- `_epic.md` exists
  - If not: check `{epic_path}/_epic.md` with Glob tool → invoke `solera-write-epic` with Skill tool
- The corresponding Story must be assigned in the Stories table of _epic.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1 |
| **goal_name** | Y | Parent Goal name | search-liquor |
| **epic_name** | Y | Parent Epic name | 01-auth |
| **epic_type** | N | Feature \| Enabler (default: Feature) | Enabler |
| **story_id** | Y | Story ID | US-001 |
| **story_name** | Y | Story name | login-form |
| **story_type** | N | US (User Story) \| TS (Technical Story) (default: US) | TS |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | _story.md | `{epic_path}/{story_id}-{story_name}/_story.md` | Final |
| Create | ACT-NNN-{name}.md | `{epic_path}/{story_id}-{story_name}/ACT-NNN-{name}.md` | Final |
| Wrap-up | RETRO.md | `{epic_path}/{story_id}-{story_name}/RETRO.md` | Final |

> `{epic_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}-{goal_name}/epics/{epic_name}`

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `solera-execute-action-item` | Execute each Action Item (1 ACT = 1 commit) | Execute |

## Procedure

1. **Setup**
   - [ ] Confirm `{epic_path}/_epic.md` exists with Glob tool
     - If not: invoke Skill tool `skill="solera-write-epic"` **(BLOCKING: resume after Epic creation completes)**
   - [ ] Check for previous Story retrospectives: `Glob {epic_path}/*/RETRO.md` — if any exist, read the most recent one and apply any "AI Improvements" noted there
   - [ ] Create `epics-{epic_name}/story-{story_id}-{story_name}` branch (from Epic branch)
   - [ ] Read `{project_path}/workspace/team-process.md` if it exists
     - Extract `workflow_gates` section for gate checks in Steps 4–5
   - [ ] Create `{epic_path}/{story_id}-{story_name}/` folder
   - [ ] Status → 🔄

2. **Determine Story type and define acceptance criteria**
   - [ ] Decide US (User Story) vs TS (Technical Story)
   - [ ] Define verifiable acceptance criteria
   - [ ] Clarify the definition of done

3. **Write _story.md and decompose Action Items**
   - [ ] **Scan available skills**: Run `Glob .claude/skills/*/SKILL.md` and `Glob .claude/plugins/*/skills/*/SKILL.md` to collect installed skill names and their trigger phrases
   - [ ] Write _story.md — ref: [assets/story.md](assets/story.md)
     - US: As a / I want / So that
     - TS: Technical objective + spec
   - [ ] Include acceptance criteria
   - [ ] Write the Action Items table (apply 1 Action Item = 1 commit principle)
   - [ ] Assign an Agent for each Action Item (when using agent teams)
   - [ ] **Assign a Skill for each Action Item**: Match the Action Item's task content against the scanned skill triggers. Set the `Skill` column to the matched skill name. If no skill matches, set to `-` (manual execution)
   - [ ] **Layer-aware decomposition** (when `execution_order.groups` is non-empty in team-process.md):
     - Read `execution_order.groups` from team-process.md
     - For each Action Item, determine its layer group by matching the assigned Skill name, Agent name, or task keywords against group keyword lists
     - If an Action Item's layer cannot be determined: assign it to the earliest group (conservative default)
     - Assign phases respecting group order: group[0] ACTs → earliest phases, group[N] ACTs → later phases
     - ACTs within the same group may share a phase (parallel OK)
   - [ ] Define depends_on to prevent output conflicts
   - [ ] Distribute across phases (same phase = can run in parallel)
   - [ ] **Phase ordering validation** (when `execution_order.groups` is non-empty in team-process.md):
     - For each Action Item in the table, resolve which group it belongs to (by Skill name, Agent name, or task keywords)
     - Validate: if group[i] appears before group[j] in `execution_order.groups`, then every ACT in group[i] must have phase ≤ every ACT in group[j]
     - If violation found: reassign phases to satisfy the ordering constraint, preserving parallelism within the same group
     - Log the reassignment: "Phase reassigned: ACT-NNN moved from phase X to Y (execution_order: {group} must precede {group})"
   - [ ] **MUST: Immediately after writing _story.md, create one file per Action Item.**
     - Parse every row in the Action Items table
     - For each row: create `ACT-NNN-{name}.md` in the Story folder using the template in [assets/action-item.md](../solera-execute-action-item/assets/action-item.md)
     - Do NOT proceed to Step 4 until all files exist
   - [ ] Verify all Action Item files exist: `Glob {story_path}/ACT-*.md` — count must match the table row count

4. **Execute**
   - [ ] **Gate check**: If `workflow_gates.story.execute` is set:
     - If `checks` array is present — iterate each check:
       - `glob_exists`: Run `Glob {params.pattern}` — PASS if ≥1 match
       - `act_complete`: Read _story.md Action Items table — PASS if all listed ACT IDs have status ✅
       - `command_passes`: Run command via Bash `{params.run}` — PASS if exit code = 0
       - `grep_absent`: Run `Grep {params.pattern}` with glob `{params.glob}` — PASS if 0 matches
     - If ANY check FAILS:
       → Display: "Gate `story.execute` blocked — check failed: {check.type} with params {check.params}"
       → **(BLOCKING: skill pauses until all checks pass)**
     - If `checks` array is absent (backward compat): evaluate `condition` text
       → If condition is not met: display the required condition to user
       → **(BLOCKING: skill pauses until condition is fulfilled)**
   - [ ] Extract incomplete (⏳ or no status) Action Items from the Action Items table in `_story.md`
   - [ ] Execute each Action Item in phase order **(BLOCKING: wait for each Action Item to complete, execute sequentially)**:
     ```python
     Skill(name="solera-execute-action-item", args={
       "project_path": "{project_path}",
       "year": "{year}",
       "phase_id": "{phase_id}",
       "goal_id": "{goal_id}",
       "goal_name": "{goal_name}",
       "epic_name": "{epic_name}",
       "epic_type": "{epic_type}",
       "story_id": "{story_id}",
       "story_name": "{story_name}",
       "action_item_id": "ACT-NNN",
       "action_item_name": "{name}"
     })
     → Confirm ACT-NNN.md committed + status ✅ before proceeding to next Action Item
     ```
   - [ ] Confirm all acceptance criteria are met
   - [ ] Proceed to Step 5 after confirming all Action Item statuses ✅

5. **Wrap-up**
   - [ ] **Gate check**: If `workflow_gates.story.wrap_up` is set:
     - If `checks` array is present — iterate each check:
       - `glob_exists`: Run `Glob {params.pattern}` — PASS if ≥1 match
       - `act_complete`: Read _story.md Action Items table — PASS if all listed ACT IDs have status ✅
       - `command_passes`: Run command via Bash `{params.run}` — PASS if exit code = 0
       - `grep_absent`: Run `Grep {params.pattern}` with glob `{params.glob}` — PASS if 0 matches
     - If ANY check FAILS:
       → Display: "Gate `story.wrap_up` blocked — check failed: {check.type} with params {check.params}"
       → **(BLOCKING: skill pauses until all checks pass)**
     - If `checks` array is absent (backward compat): evaluate `condition` text
       → If condition is not met: display the required condition to user
       → **(BLOCKING: skill pauses until condition is fulfilled)**
   - [ ] Confirm all tests pass (if code changes were made)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set _story.md status to ✅
   - [ ] Squash merge to the Epic branch

## Folder Structure

```
{epic_path}/{story_id}-{story_name}/
├── _story.md
├── RETRO.md              # Created at Wrap-up
├── ACT-001-{name}.md
├── ACT-002-{name}.md
└── ACT-003-{name}.md
```

## Commit Message Format

```
[epic-name][US-NNN][ACT-NNN] title

- change description
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md missing | `published/identity/mission.md` not found | Verify with Glob, then invoke `solera-write-identity` via Skill tool | Resume this skill after identity creation |
| _epic.md missing | `{epic_path}/_epic.md` not found | Verify with Glob, then invoke `solera-write-epic` via Skill tool | Resume this skill after Epic creation |
| Story unassigned | No Story entry in the _epic.md Stories table | Display error message, request _epic.md update | Skill halted, resume after manual fix |
| Branch creation failed | git error (conflict, permissions, etc.) | Display git error message, request manual resolution | Skill halted, resume after resolution |
| Action Item files not created | File creation missed in Step 3 | Verify with Glob, display missing file list and recreate | Block Step 4 entry until all files are confirmed created |
| Action Item count mismatch | Table row count does not match file count | Display difference, request table or file correction | Block Step 4 entry, resume after manual fix |
| Circular dependency | Circular structure in depends_on | Display circular dependency path, request table correction | Execute step halted, resume after manual fix |
| solera-execute-action-item failed | Sub-skill invocation failed | Record the failed Action Item, notify user | Skip the Action Item and continue, or halt |
| Squash merge failed | git conflict or permission error | Display conflicting file list, request manual resolution | Wrap-up halted, resume after manual resolution |

## Examples

### Example: Full User Story execution flow

#### Skill invocation

```python
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
```

#### Files created at each step

**1. After Setup**
```
epics/01-search-ui/US-001-search-input/
└── _story.md              (draft, status: 🔄)
```

**2. After Story writing and Action Items decomposition**
```markdown
# _story.md

## Story
As a **user**
I want **to enter a liquor name in the search bar and search**
So that **I can quickly find the liquor information I want**

## Acceptance Criteria
- [ ] Search bar is displayed on screen
- [ ] Real-time input validation
- [ ] Execute search with Enter key

## Action Items

| ID | Name | Skill | Phase | Depends On | Agent | Status |
|----|------|-------|-------|------------|-------|--------|
| ACT-001 | create-component | dev-flutter | 1 | - | FE | ⏳ |
| ACT-002 | add-validation | dev-flutter | 1 | - | FE | ⏳ |
| ACT-003 | write-tests | dev-flutter | 2 | ACT-001,ACT-002 | QA | ⏳ |
```

**3. After Action Item file creation**
```
epics/01-search-ui/US-001-search-input/
├── _story.md
├── ACT-001-create-component.md
├── ACT-002-add-validation.md
└── ACT-003-write-tests.md
```

**4. Execute intermediate state (ACT-001, ACT-002 complete)**
```
epics/01-search-ui/US-001-search-input/
├── _story.md             (ACT-001: ✅, ACT-002: ✅, ACT-003: 🔄)
├── ACT-001-create-component.md   (commit: abc1234, status: ✅)
├── ACT-002-add-validation.md     (commit: def5678, status: ✅)
└── ACT-003-write-tests.md        (status: 🔄)

git log --oneline:
def5678 [01-search-ui][US-001][ACT-002] Add search input validation
abc1234 [01-search-ui][US-001][ACT-001] Create search component
```

**5. After Wrap-up (all Action Items ✅)**
```
epics/01-search-ui/US-001-search-input/
├── _story.md             (status: ✅)
├── RETRO.md
├── ACT-001-create-component.md   (✅)
├── ACT-002-add-validation.md     (✅)
└── ACT-003-write-tests.md        (✅)

git log --oneline:
9876543 [01-search-ui][US-001][ACT-003] Add search component tests
def5678 [01-search-ui][US-001][ACT-002] Add search input validation
abc1234 [01-search-ui][US-001][ACT-001] Create search component
```

#### Sub-skills invoked during execution

```python
# Execute Action Item ACT-001
Skill(name="solera-execute-action-item", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui",
  "epic_type": "Feature",
  "story_id": "US-001",
  "story_name": "search-input",
  "action_item_id": "ACT-001",
  "action_item_name": "create-component"
})
# → Write code, commit, ACT-001.md status ✅

# Repeat for ACT-002, ACT-003 (in Phase order)
```

#### Final output state

- `_story.md` status: ✅
- All Action Item statuses: ✅
- `RETRO.md` exists
- 3 commits created in total (1 ACT = 1 commit)
- Squash merged to Epic branch

## Completion Checklist

- [ ] _story.md written
- [ ] Acceptance criteria are verifiable
- [ ] All ACT-NNN-{name}.md files exist on disk (verified with Glob tool — count matches Action Items table)
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Execute) solera-execute-action-item invoked for all Action Items
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _story.md status ✅
- [ ] (Wrap-up) Squash merged to Epic branch
