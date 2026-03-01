---
name: meta-command
description: Create, review, or improve a slash command file in `.claude/commands/`.
metadata:
  version: "1.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [create command, review command, improve command, new command, slash command]
  uses: []
---

# Meta Command

> Creates, reviews, or improves a slash command file in `.claude/commands/`.

## Command vs Skill

| | Command | Skill |
|---|---|---|
| Invocation | User types `/commit` | AI selects automatically |
| Name style | Short (`/handoff`) | Descriptive (`writing-goal`) |
| Trigger | Explicit user input | Keyword/context match |

## Input

| Parameter | Required | Description | Example |
|---|---|---|---|
| action | Y | `create` \| `review` \| `improve` | create |
| command_name | N | Name without leading slash (required when action=create) | handoff |
| command_path | N | Path to existing command (required when action=review or improve) | .claude/commands/handoff.md |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Command definition file | `.claude/commands/{command_name}.md` |
| Create | CLAUDE.md Commands table | Updated `## Commands` section |

## Procedure

### CREATE

1. **Gather requirements**
   - [ ] Choose a short, verb-based name (e.g., `/commit`, `/handoff`, `/review`)
   - [ ] Define explicit trigger condition: "when user types /[name]"
   - [ ] Define Process steps

2. **Write command file** — ref: [assets/command-template.md](assets/command-template.md)
   - [ ] Keep under 200 lines
   - [ ] `description` frontmatter field present
   - [ ] Trigger condition stated explicitly
   - [ ] Process checklist included

3. **Update CLAUDE.md**
   - [ ] Add row to `## Commands` table (or create section if absent)

4. **Validate**
   - [ ] Command name is short and action-oriented
   - [ ] No ambiguous instructions (no "handle accordingly", "as appropriate")

### REVIEW

5. **Analyze existing command**
   - [ ] Line count ≤ 200
   - [ ] `description` frontmatter field present
   - [ ] Process section is complete
   - [ ] Command registered in CLAUDE.md

6. **Generate review report**
   - Summarize findings and recommendations

### IMPROVE

7. **Run review** (invoke steps 5–6)
   - Obtain review report

8. **Apply improvements**
   - [ ] Apply review findings
   - [ ] Re-validate all criteria

## Completion Checklist

- [ ] `.claude/commands/{command_name}.md` created
- [ ] Line count ≤ 200
- [ ] `description` frontmatter present
- [ ] Process checklist included
- [ ] CLAUDE.md Commands table updated
