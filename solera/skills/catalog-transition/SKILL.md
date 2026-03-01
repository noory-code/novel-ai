---
name: catalog-transition
description: Transitions artifacts to published upon Goal completion
metadata:
  version: "3.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [catalog transition, move artifacts, Goal completion cleanup]
  uses: []
---

# Catalog Transition

## Prerequisites

- Goal status is complete — all Stories must be complete
- All Epics are complete — cannot proceed if any are incomplete

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **goal_path** | Y | Path of the completed Goal | goals/G1-liquor-search |

## Output

| Step | Output | Path |
|------|--------|------|
| File move | Transitioned artifacts | `published/{type}/` |
| Version record | Version tag | `[Phase]-[Goal number]` in document header |

## Procedure

1. **Confirm transition targets**
   - [ ] Scan `goals/[goal]/artifacts/`
   - [ ] Select only files of types defined in the move mapping table (exclude any files not in the mapping table)

2. **Record version**
   - [ ] Add `Applied version: [Phase]-[Goal number]` to the header
   - [ ] Format: H1-G01, H1-G02, etc.

3. **Move files**
   - [ ] Move files according to the move mapping table

4. **Update links**
   - [ ] Fix paths in _goal.md and other artifacts

5. **Obsidian optimization**
   - [ ] Add the applied version to frontmatter
   - [ ] Change status/* tags to status/completed
   - [ ] Update the `updated` date

6. **Verification**
   - [ ] All files moved to published
   - [ ] Version information recorded
   - [ ] Links are working correctly
   - [ ] The artifacts folder is empty

---

## Version Format

| Pattern | Example |
|---------|---------|
| `[Phase]-[Goal number]` | H1-G01, H1-G02, H2-G01 |

**Document header example**:
```markdown
# Journey: alba-first-search

> Persona: ALBA
> Applied version: H1-G01
> Last updated: 2026-01-15
```

## Move Mapping

| Artifact | Destination |
|----------|------------|
| service-map | `published/service-map/` |
| persona | `published/persona/` |
| journey | `published/journey/` |
| use-case | `published/use-case/` |
| concept | `published/concept/` |
| erd | `published/schema/` |
| dto | `published/dto/` |
| api-spec | `published/api/` |

## Obsidian Frontmatter

```yaml
---
title: [document title]
type: [journey|persona|service|concept|schema|use-case]
tags:
  - status/completed    # changed to completed status
  - relates-to/[related document]
created: YYYY-MM-DD
updated: YYYY-MM-DD      # updated to transition date
applied-version: [Phase]-[Goal number]
---
```

## Example

### Before (artifacts/)

```
goals/G1-liquor-search/artifacts/
├── service-map/
│   └── index.md
├── persona/
│   ├── bana.md
│   └── relationship.md
├── journey/
│   └── first-search.md
├── use-case/
│   └── UC-001-search-liquor.md
└── concept/
    └── liquor.md
```

### After (published/)

```
published/
├── service-map/
│   └── index.md           # Applied version: H1-G01
├── persona/
│   ├── bana.md            # Applied version: H1-G01
│   └── relationship.md    # Applied version: H1-G01
├── journey/
│   └── first-search.md    # Applied version: H1-G01
├── use-case/
│   └── UC-001-search-liquor.md  # Applied version: H1-G01
└── concept/
    └── liquor.md          # Applied version: H1-G01
```

## Notes

- Only move types defined in the move mapping table to published (files not in the mapping table remain in artifacts)
- If the same file already exists in the destination, replace it with the higher version
- To review a previous version, use `git log --follow -- {file-path}` to view history
- Transition in bulk by Goal, not by Epic

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (9 cases) |

## Completion Checklist

- [ ] Transition targets confirmed
- [ ] Version record added
- [ ] File move complete
- [ ] Links updated
- [ ] Obsidian frontmatter optimized
- [ ] Verification complete (links working, artifacts empty)
