---
name: solera-edit-skill
user-invocable: true
description: Add, refine, or audit a skill — guides Claude from a blank template to a production-ready SKILL.md.
metadata:
  version: "2.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [create a skill, edit a skill, improve a skill, review a skill, add a new skill, skill template]
  uses: []
---

# Edit Skill

> Creates, reviews, or improves a skill file in `.claude/skills/`.
> Run this to scaffold a new skill, audit an existing one, or apply improvements.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **action** | Y | `create` \| `review` \| `improve` | `create` |
| **skill_name** | N | Name for the new skill (required when `action=create`) | `flutter-auth` |
| **skill_path** | N | Path to existing skill (required when `action=review` or `action=improve`) | `.claude/skills/my-skill` |
| **target_path** | N | Where to create the skill (default: `.claude/skills/`) | `.claude/skills/` |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | SKILL.md | `.claude/skills/{skill_name}/SKILL.md` |
| Create | Asset files (optional) | `.claude/skills/{skill_name}/assets/*.md` |

## Procedure

Branch on `action`:

### CREATE (steps 1–4)

1. **Determine skill type**
   - [ ] Decide type: `unit` | `composite`
   - [ ] Decide style: `guide` | `procedural`
   - [ ] If `composite`: list the component skills in `uses`

2. **Select template** — ref: [assets/unit-guide.md](assets/unit-guide.md) | [assets/unit-procedural.md](assets/unit-procedural.md) | [assets/composite-guide.md](assets/composite-guide.md) | [assets/composite-procedural.md](assets/composite-procedural.md)
   - [ ] Choose the template that matches the chosen type + style

3. **Write SKILL.md content**
   - [ ] Fill frontmatter: `name`, `description`, `version`, `category`, `type`, `style`, `triggers`, `uses`
   - [ ] Write all required sections for the chosen type/style
   - [ ] Keep under 200 lines; extract overflow content to `assets/`

4. **Validate**
   - [ ] `composite` without `uses` → ERROR: add `uses` list before proceeding
   - [ ] `procedural` without a procedure section → ERROR: add procedure before proceeding
   - [ ] Over 200 lines → split content into `assets/` and link from SKILL.md

### REVIEW (steps 5–6)

5. **Analyze existing skill**
   - [ ] SKILL.md file is present
   - [ ] `metadata.type` exists (`unit` | `composite`)
   - [ ] `metadata.style` exists (`guide` | `procedural`)
   - [ ] If `type=composite` → `metadata.uses` exists and is non-empty
   - [ ] If `style=guide` → Quick Reference section exists
   - [ ] If `style=procedural` → Procedure section exists
   - [ ] Line count ≤ 200

6. **Generate review report**
   - Summarize findings: list each failed check with a concrete recommendation

### IMPROVE (steps 7–8)

7. **Run review** (invoke steps 5–6)
   - Obtain the review report from step 6

8. **Apply improvements**
   - [ ] Apply each recommendation from the review report
   - [ ] Re-validate: line count ≤ 200 and all required sections present

## Folder Structure

```
{skill_name}/
├── SKILL.md        # required
├── assets/         # templates and reference docs (flat — no subdirectories)
├── references/     # external reference docs (flat — no subdirectories)
└── scripts/        # validation scripts
```

> No subdirectories inside `assets/` or `references/` — flat structure only.

## Completion Checklist

- [ ] SKILL.md created and valid
- [ ] Line count ≤ 200
- [ ] Input and output clearly defined
- [ ] Type and style declared in frontmatter
