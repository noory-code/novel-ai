---
name: handoff
description: Context transfer between sessions - update HANDOFF.md
metadata:
  version: "1.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [handoff, session end, save context, work handover]
  uses: [workflow-manage]
---

# Handoff

> Create/update HANDOFF.md for context transfer between sessions

## Input

None (auto-detects current session state)

## Output

| File | Location | Purpose |
|------|----------|---------|
| HANDOFF.md | Project root | Context transfer between sessions (temporary state) |

## Procedure

### Step 1: Understand current session work

Collect the following information to understand the current session's work:

1. **Check Git status**:
   ```bash
   git status --short
   git diff --stat
   git log --oneline -5
   ```

2. **Check Todo list**: Current session's todo list state

3. **Read progress.md**: Check current Phase/Goal/Epic/Story via the [workflow-manage](../workflow-manage/SKILL.md) skill

### Step 2: Read HANDOFF.md

1. Attempt to read `HANDOFF.md`
2. If file does not exist, create a new one referencing [assets/handoff-template.md](assets/handoff-template.md)

### Step 3: Update sections

Update the following sections based on information collected in Step 1:

| Section | Content | Source |
|---------|---------|--------|
| **Current work** | 1-2 line summary of work in progress | progress.md + todo list |
| **Completed items** | List of work completed this session | git diff + todo (completed) |
| **Next steps** | Work to do in the next session | todo (pending) + user input |
| **Key decisions** | Major decisions and their reasons | git log + user input |
| **Reference files** | Paths of key changed files | git diff --name-only |
| **Notes** | Special items the next session should know | user input |

### Step 4: Save with timestamp

1. Add `> Last updated: YYYY-MM-DD HH:MM:SS` at the top of the file
2. Save HANDOFF.md

## Error Handling

| Failure point | Condition | Recovery procedure |
|---------------|-----------|-------------------|
| HANDOFF.md read failure | File does not exist | Create new at project root (reference template) |
| Cannot determine current work | git diff/log is empty | Ask user "Please tell me what you did this session" |
| HANDOFF.md write failure | Permission error | Run `chmod 644 HANDOFF.md` and retry |

## When to Use

- Before interrupting work
- Before reaching context window limit
- Mid-save during complex work

## progress.md vs HANDOFF.md

> See [assets/handoff-template.md](assets/handoff-template.md) for the difference between the two files

## References

| File | Content |
|------|---------|
| [assets/handoff-template.md](assets/handoff-template.md) | HANDOFF.md format + difference from progress.md |
| [assets/self-verification.md](assets/self-verification.md) | Automated skill verification TCs |

## Completion Checklist

- [ ] Understood current work via git status/diff/log?
- [ ] Confirmed current Phase/Goal/Epic from progress.md?
- [ ] Read or created HANDOFF.md?
- [ ] Updated 6 sections (current work, completed items, next steps, decisions, reference files, notes)?
- [ ] Added timestamp?
- [ ] Saved HANDOFF.md?
