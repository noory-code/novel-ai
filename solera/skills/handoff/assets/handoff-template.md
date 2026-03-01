# HANDOFF.md Template and Guide

## progress.md vs HANDOFF.md

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `progress.md` | Overall project progress status (Phase/Goal/Epic) | Per Epic |
| `HANDOFF.md` | Cross-session context handoff (transient state) | At session end |

> `progress.md` is for project management; `HANDOFF.md` is for AI session management

---

## HANDOFF.md Standard Format

```markdown
# HANDOFF.md
> Last updated: YYYY-MM-DD HH:MM:SS

## Current Work
[1-2 line summary of work in progress]

## Skill Status
- current_skill: [name of skill running, omit if none]
- current_step: [current Step, e.g. 5-Execute]

## Completed Items
- [x] completed task 1
- [x] completed task 2

## Next Steps
- [ ] next task 1
- [ ] next task 2

## Key Decisions
- Decision 1: [reason]

## Reference Files
- `path/to/file1.dart`

## Caveats
[Special notes the next session must be aware of]
```

---

## Section-by-Section Writing Guide

### Current Work
- Summarize concisely in 1–2 lines
- Specify the Epic or Story title and the current step
- Example: "Progressing through Epic 04-build-roles. Story TS-002 (role lookup system) implementation complete; TS-003 in preparation"

### Completed Items
- List the specific tasks completed in this session
- Use `[x]` for completed checkboxes
- Write entries to match the corresponding commit messages

### Next Steps
- Write clear TODOs so the next session can start immediately
- Use `[ ]` for incomplete checkboxes
- List in priority order

### Key Decisions
- Write in "what + why" format
- Include only decisions the next session needs in order to understand the context

### Reference Files
- Key file paths changed in this session
- Wrap paths in backticks (`)

### Caveats
- Errors, blockers, workarounds, and other special notes
- Information the next session must not miss
