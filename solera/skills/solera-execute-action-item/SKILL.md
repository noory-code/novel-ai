---
name: solera-execute-action-item
user-invocable: true
description: Implement one Action Item end-to-end: write the code, run tests, and commit — one focused change at a time.
metadata:
  version: "7.1.0"
  category: writing
  type: unit
  style: procedural
  triggers: [start an Action Item, execute Action Item, implement and commit, work on ACT-NNN, ACT-NNN]
  uses: []
---

# Writing Action Item

> An Action Item is the smallest workflow unit. 1 Action Item = 1 commit.

## Prerequisites

- `_story.md` exists; if not, invoke solera-write-story
- The corresponding ACT must be assigned in the Action Items table of _story.md
- All prerequisite ACTs listed in depends_on must be ✅ complete

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
| **story_id** | Y | Parent Story ID | US-001 |
| **story_name** | Y | Parent Story name | login-form |
| **action_item_id** | Y | Action Item ID | ACT-001 |
| **action_item_name** | Y | Action Item name | setup-project |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Execute | Code/document changes | Files declared in output_paths | Final |
| Wrap-up | git commit | `[epic-name][story_id][ACT-NNN] title` | Final |
| Wrap-up | ACT status ✅ | Status update within `ACT-NNN-{name}.md` | Final |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `Skill:` field value from ACT file | Primary — auto-invoked when specified | Development |
| Development skills (frontend-*, dev-*, design-*, etc.) | Fallback — keyword-matched when `Skill:` is `-` | Development |

## Skill Resolution

1. Read the `Skill:` metadata field from the Action Item file
2. If the field contains a skill name (not `-`): invoke `Skill(name="{skill_name}")` directly
3. If the field is `-` or missing: fall back to matching task content keywords against available skill triggers

## Procedure

1. **Setup**
   - [ ] Confirm `_story.md` exists; if not, invoke solera-write-story
   - [ ] Confirm all prerequisite ACTs in depends_on are complete
   - [ ] Read the Action Item file — ref: [assets/action-item.md](assets/action-item.md)
   - [ ] Confirm the objective and task checklist
   - [ ] Check for previous ACT retrospectives: `Glob {story_path}/ACT-*.md` — if any completed ACTs exist, read their `## Retrospective` section and apply any "AI Improvements" noted there
   - [ ] Status → 🔄

2. **Write tests** (if code changes are required)
   - [ ] Design test cases based on acceptance criteria
   - [ ] Write Unit/Widget test code (Red — will fail since implementation is not yet done)

3. **Development**
   - [ ] Resolve skill per Skill Resolution above
   - [ ] Invoke the resolved skill (or perform manual coding if no skill available)
   - [ ] Complete all items in the task checklist

4. **Test verification**
   - [ ] Build passes
   - [ ] Tests pass (Green)
   - [ ] Confirm all files listed in output_paths exist
   - [ ] **Architecture check** (when `architecture_rules.rules` is non-empty in team-process.md):
     - Read `architecture_rules.rules` from `{project_path}/workspace/team-process.md`
     - For each rule in `rules`:
       - Collect files matching `rule.scope` using Glob
       - Intersect with this Action Item's changed files (output_paths + `git diff --name-only`)
       - For each intersected file, run `Grep {pattern}` for each pattern in `rule.forbidden_imports`
       - If ANY match found:
         → Display: "Architecture violation in `{file}`: matched `{pattern}` — {rule.message}"
         → **(BLOCKING: skill pauses until violation is resolved)**
     - If `architecture_rules` section is absent or `rules` is empty: skip this check

5. **Wrap-up**
   - [ ] Record the list of changed files in the Action Item file's results section
   - [ ] Commit (1 Action Item = 1 commit, following the message format)
   - [ ] Write `## Retrospective` section in the Action Item file — ref: [assets/retro.md](assets/retro.md)
     - Did well / Did poorly / Improvements / Instruction issues
   - [ ] **System improvement** (when `## Retrospective` contains "AI Improvements" or "Instruction System Issues"):
     - For each improvement entry, classify into one of:
       - `skill_change`: A skill's checklist, forbidden list, or procedure needs updating
         → Edit the relevant SKILL.md immediately (add checklist item, forbidden pattern, etc.)
       - `rule_change`: A rule file (`.claude/rules/*.md`) needs updating
         → Edit the relevant rule file immediately
       - `framework_change`: Requires a code-level fix beyond skill/rule scope
         → Record as a new Technical Story (TS) in the parent Epic's backlog
     - Apply `skill_change` and `rule_change` within this same commit
     - Log each applied change: "System improvement applied: {file} — {description}"
   - [ ] Status → ✅
   - [ ] Decide the next Action Item or process Story completion

## Folder Structure

```
{epic_path}/{story_id}-{story_name}/
├── _story.md
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
| _story.md missing | `_story.md` file not found | Invoke `solera-write-story` skill | Resume this skill after Story creation |
| Action Item unassigned | No ACT entry in _story.md Action Items table | Display error message, request _story.md update | Skill halted, resume after manual fix |
| Dependencies incomplete | Prerequisite ACTs in depends_on are not ✅ | Display incomplete ACT list, request completion of prior work | Skill halted, resume after prior work completes |
| Action Item file missing | `ACT-NNN-{name}.md` not found | Create file using template reference | Continue after file creation |
| Build failed | Build command failed in Step 4 | Display build error, request code fix | Test verification step halted, re-run after fix |
| Test failed | Test failure in Step 4 | Display failed test list, request code fix | Test verification step halted, re-run after fix |
| output_paths files missing | Declared files were not actually created | Display missing file list, request file creation | Test verification step halted, re-run after file creation |
| Architecture violation | Forbidden import pattern found in changed files | Display violation details (file, pattern, rule message), request code fix | Test verification step halted, re-run after fix |
| Commit failed | git commit error (pre-commit hook failure, etc.) | Display git error message, request manual resolution | Wrap-up halted, retry commit after resolution |
| Development skill matching failed | No suitable development skill found via keywords | Request manual implementation from user, or request skill recommendation | Development step halted, resume after manual work or skill assignment |

## Completion Checklist

- [ ] Action Item objective achieved
- [ ] Task checklist complete
- [ ] Results (changed files, commit) recorded
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Wrap-up) Retrospective written in Action Item file
- [ ] (Wrap-up) Status ✅
- [ ] (Wrap-up) Next Action Item or Story completion confirmed
