# Template: Action Item

Defines the decomposition unit of a Story = the commit unit.

## ACT-NNN-[name].md

```markdown
# ACT-NNN: [title]

> Story: [US|TS]-NNN
> Status: ⏳ Pending / 🔄 In Progress / ✅ Complete / ❌ Cancelled
> Agent: [fullstack-db | fullstack-domain | fullstack-data | fullstack-presentation | -]
> Phase: [N]
> depends_on: [ACT-NNN, ...] or -
> output_paths: [expected output file paths]

## Goal

[What this Action Item aims to achieve]

## Task Content

- [ ] [task 1]
- [ ] [task 2]

---

## Result (record after completion)

### Changed Files

- `path/to/file.dart` - [change description]

### Commit

- `abc1234` [epic-name][US-NNN][ACT-NNN] title
```

## Workflow

### Step 0. Setup
- [ ] Confirm `stories/[US|TS]-NNN/_story.md` exists → invoke writing-story if missing
- [ ] Status → 🔄
- [ ] Confirm goal + task content checklist

### Step 1. Execute
- [ ] Identify required skills → invoke development skills (frontend-*, dev-*, design-*, etc.)
- [ ] Perform actual coding/documentation work
- [ ] Confirm all task content checklist items complete

### Step 2. Wrap-up
- [ ] Build/tests pass (if applicable)
- [ ] Record changed file list
- [ ] Commit (1 Action Item = 1 commit, follow message format)
- [ ] Write retrospective → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] Determine next Action Item or process Story completion

## Folder Structure

```
stories/[US|TS]-NNN/action-items/
└── ACT-NNN-[name].md
```

## Commit Message Format

```
[epic-name][US-NNN][ACT-NNN] title

- change description 1
- change description 2
```

**Examples:**
```
[define-concept][TS-001][ACT-001] Define domain concepts
[design-schema][TS-001][ACT-002] Write ERD
```

## Cautions

| Wrong | Correct |
|-------|---------|
| Create a branch per Action Item | Action Item = **commit only** |
| Multiple Action Items in one commit | 1 Action Item = 1 commit |
