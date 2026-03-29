# Template: Action Item

Defines the decomposition unit of a Story, which corresponds to a single commit.

## ACT-NNN-[name].md

```markdown
# ACT-NNN: [title]

> Story: [US|TS]-NNN
> Status: ⏳ Pending / 🔄 In Progress / ✅ Complete / ❌ Cancelled
> Skill: [skill name or -]
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

## Retrospective (record after completion)

### Did Well

- [effective decisions or execution]

### Did Poorly

- [mistakes, inefficiencies, unnecessary repetition]

### Improvements

- [specific behaviors to change in the next Action Item]

### Instruction Issues

- [omissions or ambiguities found in skills/rules]
```

## Workflow

### Step 0. Setup
- [ ] Confirm `_story.md` exists in the Story folder; if missing, invoke solera-write-story
- [ ] Status → 🔄
- [ ] Confirm the goal and task content checklist

### Step 1. Execute
- [ ] Read the `Skill:` field from the Action Item metadata
  - If a skill is specified (not `-`): invoke it via `Skill(name="{skill_name}")`
  - If `-`: identify required skills from task content keywords and invoke manually
- [ ] Perform actual coding/documentation work
- [ ] Confirm all task content checklist items complete

### Step 2. Wrap-up
- [ ] Build/tests pass (if applicable)
- [ ] Record changed file list
- [ ] Commit (1 Action Item = 1 commit, follow message format)
- [ ] Write retrospective to RETROSPECTIVE.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] Determine the next Action Item or process Story completion

## Folder Structure

```
{epic_path}/[US|TS]-NNN-[name]/
├── _story.md
├── ACT-001-[name].md
├── ACT-002-[name].md
└── ACT-003-[name].md
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
| Creating a branch per Action Item | An Action Item is a **commit only** — no branch |
| Bundling multiple Action Items in one commit | One Action Item = one commit |
