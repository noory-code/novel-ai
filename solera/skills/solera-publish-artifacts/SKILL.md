---
name: solera-publish-artifacts
description: Mark a Goal as done — move all artifacts to the published catalog and update cross-references.
metadata:
  version: "4.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [transition to catalog, archive completed Goal, publish Goal artifacts, wrap up Goal, Goal completion cleanup]
  uses: []
---

# Catalog Transition

## Prerequisites

This skill is invoked at two points:
1. **After Goal Create** — promotes Goal-level artifacts (service-map, persona, journey)
2. **At Epic Wrap-up** — promotes Epic-level artifacts (use-case, concept)

- The calling work item (Goal Create or Epic) must be complete
- Only artifacts present in `artifacts/` at the time of invocation are moved

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal name | search-liquor |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| File move | Transitioned artifacts | `workspace/catalog/published/{type}/` | Final |
| Version record | Version tag | `[Phase]-[Goal number]` in document header | Final |

## Procedure

1. **Confirm transition targets**
   - [ ] Compute goal_path: `{project_path}/phase/{phase_id}/goals/{goal_id}-{goal_name}`
   - [ ] Scan `{goal_path}/artifacts/`
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
| `[Phase]-[Goal number]` | 2026-P1-G01, 2026-P1-G02, 2026-P2-G01 |

**Document header example**:
```markdown
# Journey: alba-first-search

> Persona: ALBA
> Applied version: 2026-P1-G01
> Last updated: 2026-01-15
```

## Move Mapping

| Artifact | Destination |
|----------|------------|
| service-map | `workspace/catalog/published/service-map/` |
| persona | `workspace/catalog/published/persona/` |
| journey | `workspace/catalog/published/journey/` |
| use-case | `workspace/catalog/published/use-case/` |
| concept | `workspace/catalog/published/concept/` |
| erd | `workspace/catalog/published/schema/` |
| dto | `workspace/catalog/published/dto/` |
| api-spec | `workspace/catalog/published/api/` |

## Obsidian Frontmatter

> **Note:** This section is for teams using Obsidian as a knowledge base. If you are not using Obsidian, skip the frontmatter fields — the file move in step 3 is the only required action.

```yaml
---
title: [document title]
type: [journey|persona|service|concept|schema|use-case]
tags:
  - status/completed    # changed to completed status
  - relates-to/[related document]
created: YYYY-MM-DD
updated: YYYY-MM-DD      # updated to transition date
applied-version: [Phase]-[Goal number]  # e.g., 2026-P1-G01
---
```

## Example

### Skill invocation

```python
Skill(name="solera-publish-artifacts", args={
  "project_path": "/Users/myname/workspace/myapp",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor"
})
```

### Before (artifacts/)

```
{project_path}/phase/2026-P1-foundation/goals/G1-liquor-search/artifacts/
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

### After (workspace/catalog/published/)

```
{project_path}/workspace/catalog/published/
├── service-map/
│   └── index.md           # Applied version: 2026-P1-G01
├── persona/
│   ├── bana.md            # Applied version: 2026-P1-G01
│   └── relationship.md    # Applied version: 2026-P1-G01
├── journey/
│   └── first-search.md    # Applied version: 2026-P1-G01
├── use-case/
│   └── UC-001-search-liquor.md  # Applied version: 2026-P1-G01
└── concept/
    └── liquor.md          # Applied version: 2026-P1-G01
```

## Notes

- Only move types defined in the move mapping table to `workspace/catalog/published/` (files not in the mapping table remain in artifacts)
- If the same file already exists in the destination, replace it with the higher version
- To review a previous version, use `git log --follow -- {file-path}` to view history
- Invoked incrementally: after Goal Create (Goal-level artifacts) and at each Epic Wrap-up (Epic-level artifacts), not in bulk at Goal completion

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (9 cases) |

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| Invocation timing mismatch | Invoked outside of Goal Create or Epic Wrap-up | Display current state, guide to correct invocation timing | Skill halted, re-invoke at correct timing |
| artifacts folder missing | `{goal_path}/artifacts/` not found | Display warning message, treat as no transition targets | Skill complete (no transition needed) |
| Files outside mapping table | Artifact types not in the mapping table exist | Display excluded file list, leave in artifacts | Continue (move only mapped files) |
| catalog directory missing | `workspace/catalog/published/` not found | Create directory with `mkdir -p` | Continue after directory creation |
| File move failed | Permission error or path issue | Display failed file list, request permission check | Skill halted, resume after manual resolution |
| Link update failed | Relative path conversion error | Display links requiring fix, request manual correction | Verification step halted, resume after manual fix |
| Frontmatter parsing failed | YAML format error | Skip the file and display warning | Continue (frontmatter update is optional) |
| artifacts folder not empty | Unmapped files remain | Display remaining file list, ask if intentional | Skill complete (with verification warning) |

## Completion Checklist

- [ ] Transition targets confirmed
- [ ] Version record added
- [ ] File move complete
- [ ] Links updated
- [ ] Obsidian frontmatter optimized
- [ ] Verification complete (links working, artifacts empty)
