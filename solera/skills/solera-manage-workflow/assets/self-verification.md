# Validation: solera-manage-workflow (v3)

> Unique validation rules for this skill.

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
      - assets/retrospective.md
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
      - "handle accordingly"

  - id: C-002
    name: "Core v3 keywords present"
    type: content_contains
    target: SKILL.md
    patterns:
      - "Workflow"
      - "progress.md"
      - "Concept"
      - "Milestone"
      - "Release"
      - "Living"
      - "Time-bound"
      - "Immutable"

  - id: C-003
    name: "Procedure actions defined"
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
      - "solera-write-concept"
      - "solera-write-milestone"
      - "solera-write-story"
      - "solera-execute-action-item"
      - "solera-release"

  - id: C-005
    name: "Responsibilities section exists"
    type: section_exists
    target: SKILL.md
    section: "## Responsibilities"

  - id: C-006
    name: "Supervision Principles section exists"
    type: section_exists
    target: SKILL.md
    section: "## Supervision Principles"

  - id: C-007
    name: "Removed v2 hierarchy references"
    type: content_not_contains
    target: SKILL.md
    patterns:
      - "solera-write-phase"
      - "solera-write-goal"
      - "solera-write-epic"
      - "epics/"
      - "phase/"
```
