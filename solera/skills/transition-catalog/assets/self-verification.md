# Validation: transition-catalog

> This file defines the unique validation rules for the transition-catalog skill.

## Structural

```yaml
structural:
  - id: S-001
    name: "Prerequisites section exists"
    type: section_exists
    target: SKILL.md
    section: "## Prerequisites"

  - id: S-002
    name: "Procedure section exists"
    type: section_exists
    target: SKILL.md
    section: "## Procedure"

  - id: S-003
    name: "Completion Checklist exists"
    type: section_exists
    target: SKILL.md
    section: "## Completion Checklist"

  - id: S-004
    name: "Version format section exists"
    type: section_exists
    target: SKILL.md
    section: "## Version Format"

  - id: S-005
    name: "Move mapping section exists"
    type: section_exists
    target: SKILL.md
    section: "## Move Mapping"
```

## Semantic

```yaml
semantic:
  - id: C-001
    name: "No AI-First banned phrases"
    type: content_not_contains
    target: SKILL.md
    patterns:
      - "as appropriate"
      - "if needed"
      - "depending on the situation"
      - "as you see fit"

  - id: C-002
    name: "Core keywords present"
    type: content_contains
    target: SKILL.md
    patterns:
      - "catalog"
      - "artifacts"
      - "applied version"
      - "Goal"

  - id: C-003
    name: "Version pattern defined"
    type: content_contains
    target: SKILL.md
    patterns:
      - "[Phase]-[Goal number]"
      - "H1-G01"

  - id: C-004
    name: "Procedure step checklist"
    type: count_check
    target: SKILL.md
    pattern: "- \\[ \\]"
    min: 5
    max: 999
```
