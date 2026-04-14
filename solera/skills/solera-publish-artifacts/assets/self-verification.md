# Validation: solera-publish-artifacts (v3)

> Unique validation rules for this skill after the v3 open.

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
    name: "Version Tag section exists"
    type: section_exists
    target: SKILL.md
    section: "## Version Tag"

  - id: S-005
    name: "Move Mapping section exists"
    type: section_exists
    target: SKILL.md
    section: "## Move Mapping"

  - id: S-006
    name: "Related Artifacts Line Format section exists"
    type: section_exists
    target: SKILL.md
    section: "## Related Artifacts Line Format"
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
    name: "v3 core keywords present"
    type: content_contains
    target: SKILL.md
    patterns:
      - "Story Wrap-up"
      - "catalog/published"
      - "contributes_to"
      - "Related Artifacts"
      - "Applied version"

  - id: C-003
    name: "Version tag uses story_id"
    type: content_contains
    target: SKILL.md
    patterns:
      - "{story_id}"
      - "US-001"

  - id: C-004
    name: "Procedure step checklist"
    type: count_check
    target: SKILL.md
    pattern: "- \\[ \\]"
    min: 10
    max: 999

  - id: C-005
    name: "Move mapping includes v3 types + reference + fallback"
    type: content_contains
    target: SKILL.md
    patterns:
      - "domain-model"
      - "persona"
      - "service-map"
      - "journey"
      - "use-case"
      - "reference"
      - "_unclassified"

  - id: C-005b
    name: "Unknown type BLOCKING prompt at Discovery"
    type: content_contains
    target: SKILL.md
    patterns:
      - "unknown artifact type"
      - "_unclassified/{type}/"

  - id: C-006
    name: "Idempotency and collision handling documented"
    type: content_contains
    target: SKILL.md
    patterns:
      - "skipped (identical)"
      - "Overwrite"
      - "Rename new"
      - "Skip"

  - id: C-007
    name: "git mv preferred"
    type: content_contains
    target: SKILL.md
    patterns:
      - "git mv"

  - id: C-008
    name: "user-invocable is false"
    type: content_contains
    target: SKILL.md
    patterns:
      - "user-invocable: false"

  - id: C-010
    name: "Removed v2 Goal/Epic promotion references"
    type: content_not_contains
    target: SKILL.md
    patterns:
      - "Goal Create"
      - "Epic Wrap-up"
      - "[Phase]-[Goal number]"
      - "H1-G01"
      - "phase_id"
      - "goal_id"
```
