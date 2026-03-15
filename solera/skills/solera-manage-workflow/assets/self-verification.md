# Validation: solera-manage-workflow

> This file defines the unique validation rules for the solera-manage-workflow skill.

## Structural

```yaml
structural:
  - id: S-001
    name: "Common Rules section exists"
    type: section_exists
    target: SKILL.md
    section: "## Common Rules"

  - id: S-002
    name: "Prerequisites section exists"
    type: section_exists
    target: SKILL.md
    section: "## Prerequisites"

  - id: S-003
    name: "Procedure section exists"
    type: section_exists
    target: SKILL.md
    section: "## Procedure"

  - id: S-004
    name: "Completion Checklist exists"
    type: section_exists
    target: SKILL.md
    section: "## Completion Checklist"

  - id: S-005
    name: "assets files exist"
    type: file_exists
    paths:
      - assets/conventions.md
      - assets/lifecycle.md
      - assets/progress.md
      - assets/retro.md
      - assets/status.md
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
      - "Workflow"
      - "progress.md"
      - "RETRO.md"
      - "work item"

  - id: C-003
    name: "Procedure steps defined"
    type: content_contains
    target: SKILL.md
    patterns:
      - "### start"
      - "### complete"
      - "### check"
      - "### next"

  - id: C-004
    name: "Skill delegation specified"
    type: content_contains
    target: SKILL.md
    patterns:
      - "solera-write-*"
      - "invoke"

  - id: C-005
    name: "Role assignment table exists"
    type: section_exists
    target: SKILL.md
    section: "## Role Assignment"

  - id: C-006
    name: "Supervision principle exists"
    type: section_exists
    target: SKILL.md
    section: "## Supervision Principle"
```
