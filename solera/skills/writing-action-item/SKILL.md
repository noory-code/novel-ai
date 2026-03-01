---
name: writing-action-item
description: Action Item execution. 1 Action Item = 1 commit.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Action Item start, Action Item execute, commit work, ACT-NNN]
  uses: []
---

# Writing Action Item

> An Action Item is the smallest workflow unit. 1 Action Item = 1 commit.

## Prerequisites

- `_story.md` exists → if not, invoke writing-story
- The corresponding ACT must be assigned in the Action Items table of _story.md
- All prerequisite ACTs listed in depends_on must be ✅ complete

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **epic_name** | Y | Parent Epic name | 01-auth |
| **story_id** | Y | Parent Story ID | US-001 |
| **action_item_id** | Y | Action Item ID | ACT-001 |
| **action_item_name** | Y | Action Item name | setup-project |

## Output

| Step | Output | Path |
|------|--------|------|
| Execute | Code/document changes | Files declared in output_paths |
| Wrap-up | git commit | `[epic-name][story_id][ACT-NNN] title` |
| Wrap-up | ACT status ✅ | Status update within `action-items/ACT-NNN-{name}.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| Development skills (frontend-*, dev-*, design-*, etc.) | Actual coding/documentation work | Execute |

> Development skill selection: match task content keywords with skill-orchestration triggers

## Procedure

1. **Setup**
   - [ ] Confirm `_story.md` exists → if not, invoke writing-story
   - [ ] Confirm prerequisite ACTs in depends_on are complete
   - [ ] Read Action Item file → ref: [assets/action-item.md](assets/action-item.md)
   - [ ] Confirm objective + task checklist
   - [ ] Status → 🔄

2. **Write tests** (if code changes)
   - [ ] Design test cases based on acceptance criteria
   - [ ] Write Unit/Widget test code (Red — will fail since implementation not yet done)

3. **Development**
   - [ ] Match task keywords → development skill → invoke
   - [ ] Perform actual coding/documentation work
   - [ ] Complete all items in task checklist

4. **Test verification**
   - [ ] Build passes
   - [ ] Tests pass (Green)
   - [ ] Confirm output_paths files exist

5. **Wrap-up**
   - [ ] Record list of changed files (Action Item file results section)
   - [ ] Commit (1 Action Item = 1 commit, follow message format)
   - [ ] Status → ✅
   - [ ] Decide next Action Item or process Story completion

## Folder Structure

```
{epic_path}/stories/{story_id}/action-items/
└── ACT-NNN-{name}.md
```

## Commit Message Format

```
[epic-name][US-NNN][ACT-NNN] title

- change description
```

## Completion Checklist

- [ ] Action Item objective achieved
- [ ] Task checklist complete
- [ ] Results (changed files, commit) recorded
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Wrap-up) Status ✅
- [ ] (Wrap-up) Next Action Item or Story completion confirmed
