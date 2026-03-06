---
name: execute-action-item
description: Implement one Action Item end-to-end: write the code, run tests, and commit — one focused change at a time.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [start an Action Item, execute Action Item, implement and commit, work on ACT-NNN, ACT-NNN]
  uses: []
---

# Writing Action Item

> An Action Item is the smallest workflow unit. 1 Action Item = 1 commit.

## Prerequisites

- `_story.md` exists; if not, invoke writing-story
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
| Development skills (frontend-*, dev-*, design-*, etc.) | Actual coding and documentation work | Execute |

> Development skill selection: match task content keywords with skill-orchestration triggers

## Procedure

1. **Setup**
   - [ ] Confirm `_story.md` exists; if not, invoke writing-story
   - [ ] Confirm all prerequisite ACTs in depends_on are complete
   - [ ] Read the Action Item file — ref: [assets/action-item.md](assets/action-item.md)
   - [ ] Confirm the objective and task checklist
   - [ ] Check for previous ACT retrospectives: `Glob action-items/ACT-*.md` — if any completed ACTs exist, read their `## Retrospective` section and apply any "AI Improvements" noted there
   - [ ] Status → 🔄

2. **Write tests** (if code changes are required)
   - [ ] Design test cases based on acceptance criteria
   - [ ] Write Unit/Widget test code (Red — will fail since implementation is not yet done)

3. **Development**
   - [ ] Match task keywords to a development skill and invoke it
   - [ ] Perform the actual coding or documentation work
   - [ ] Complete all items in the task checklist

4. **Test verification**
   - [ ] Build passes
   - [ ] Tests pass (Green)
   - [ ] Confirm all files listed in output_paths exist

5. **Wrap-up**
   - [ ] Record the list of changed files in the Action Item file's results section
   - [ ] Commit (1 Action Item = 1 commit, following the message format)
   - [ ] Write `## Retrospective` section in the Action Item file — ref: [assets/retro.md](assets/retro.md)
     - Did well / Did poorly / Improvements / Instruction issues
   - [ ] Status → ✅
   - [ ] Decide the next Action Item or process Story completion

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
- [ ] (Wrap-up) Retrospective written in Action Item file
- [ ] (Wrap-up) Status ✅
- [ ] (Wrap-up) Next Action Item or Story completion confirmed
