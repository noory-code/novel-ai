---
name: solera-handoff
user-invocable: true
description: Never lose context between sessions — capture current state, open threads, and next steps in HANDOFF.md.
metadata:
  version: "2.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [handoff, end session, save work context, hand over to next session, update HANDOFF]
  uses: [solera-manage-workflow]
---

# Handoff

> Creates or updates HANDOFF.md to transfer context between sessions.

## Input

None (auto-detects current session state)

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create/Update | HANDOFF.md | Project root | Transient |

## Procedure

### Step 1: Understand current session work

Collect the following information to understand the current session's work:

1. **Check Git status**:
   ```bash
   git status --short
   git diff --stat
   git log --oneline -5
   ```

2. **Check Todo list**: Review the current session's todo list state

3. **Read progress.md**: Check the current Phase/Goal/Epic/Story via the [solera-manage-workflow](../solera-manage-workflow/SKILL.md) skill

### Step 2: Read HANDOFF.md

1. Attempt to read `HANDOFF.md`
2. If the file does not exist, create a new one referencing [assets/handoff-template.md](assets/handoff-template.md)

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
| HANDOFF.md read failure | File does not exist | Create a new one at the project root (reference template) |
| Cannot determine current work | git diff/log is empty | Ask the user: "What did you accomplish this session?" |
| HANDOFF.md write failure | Permission error | Run `chmod 644 HANDOFF.md` and retry |

## When to Use

- Before interrupting work
- Before reaching the context window limit
- As a mid-session save during complex work

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
- [ ] Updated all 6 sections (current work, completed items, next steps, decisions, reference files, notes)?
- [ ] Added timestamp?
- [ ] Saved HANDOFF.md?
