---
name: writing-story
description: Story document writing → Action Item decomposition. 1 Action Item = 1 commit.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Story elaboration, Story start, decompose into Action Items, commit unit]
  uses: [writing-action-item]
---

# Writing Story

> Writes _story.md and decomposes into Action Items.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `writing-identity` with Skill tool
- `_epic.md` exists
  - If not: check `{epic_path}/_epic.md` with Glob tool → invoke `writing-epic` with Skill tool
- The corresponding Story must be assigned in the Stories table of _epic.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1-search-liquor |
| **epic_name** | Y | Parent Epic name | 01-auth |
| **story_id** | Y | Story ID | US-001 |
| **story_name** | Y | Story name | login-form |
| **story_type** | N | US (User Story) \| TS (Technical Story) (default: US) | TS |

## Output

| Step | Output | Nature | Path |
|------|--------|--------|------|
| Create | _story.md | Final | `{epic_path}/stories/{story_id}/_story.md` |
| Create | ACT-NNN-{name}.md | Final | `{epic_path}/stories/{story_id}/action-items/ACT-NNN-{name}.md` |
| Wrap-up | RETRO.md | Final | `{epic_path}/stories/{story_id}/RETRO.md` |

> `{epic_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}/epics/{epic_name}`

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-action-item` | Execute each Action Item (1 ACT = 1 commit) | Execute |
| `workflow-pr` | PR to Epic branch upon Story completion | Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `{epic_path}/_epic.md` exists with Glob tool
     - If not: invoke Skill tool `skill="writing-epic"` → resume this Step after completion
   - [ ] Create `story-{story_id}-{story_name}` branch (from Epic branch)
   - [ ] Create `{epic_path}/stories/{story_id}/` folder
   - [ ] Status → 🔄

2. **Determine Story type + define acceptance criteria**
   - [ ] Decide US (User Story) vs TS (Technical Story)
   - [ ] Define verifiable acceptance criteria
   - [ ] Clarify definition of done

3. **Write _story.md + decompose Action Items**
   - [ ] Write _story.md → ref: [assets/story.md](assets/story.md)
     - US: As a / I want / So that
     - TS: Technical objective + spec
   - [ ] Include acceptance criteria
   - [ ] Write Action Items table
   - [ ] Create file per Action Item (`action-items/ACT-NNN-{name}.md`)
   - [ ] 1 Action Item = 1 commit principle
   - [ ] Assign Agent per Action Item (when using agent teams)
   - [ ] Define depends_on → prevent output conflicts
   - [ ] Phase distribution (same Phase = can run in parallel)

4. **Execute**
   - [ ] Extract incomplete (⏳ or no status) Action Items from Action Items table in `_story.md`
   - [ ] Execute each Action Item in Phase order (do not proceed to next Step until all Action Items are complete):
     ```
     Skill tool call: skill="writing-action-item"
       args: action_item_id=ACT-NNN, action_item_name={name}, story_id={story_id},
             epic_name={epic_name}, goal_id={goal_id}, phase_id={phase_id},
             project_path={project_path}
     → Confirm ACT-NNN.md committed + status ✅ before proceeding to next Action Item
     ```
   - [ ] Confirm all acceptance criteria met
   - [ ] Proceed to Step 5 after confirming all Action Item statuses ✅

5. **Wrap-up**
   - [ ] Confirm all tests pass (if code changes)
   - [ ] Write RETRO.md → ref: [assets/retro.md](assets/retro.md)
   - [ ] _story.md status → ✅
   - [ ] Squash merge to Epic branch
   - [ ] Skill tool call: `skill="workflow-pr"` (Story → Epic branch)

## Folder Structure

```
{epic_path}/stories/{story_id}/
├── _story.md
├── RETRO.md              # Created at Wrap-up
└── action-items/
    └── ACT-NNN-{name}.md
```

## Commit Message Format

```
[epic-name][US-NNN][ACT-NNN] title

- change description
```

## Completion Checklist

- [ ] _story.md written
- [ ] Acceptance criteria verifiable
- [ ] Action Item files created
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Execute) writing-action-item invoked for all Action Items
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _story.md status ✅
- [ ] (Wrap-up) Squash merged to Epic branch
