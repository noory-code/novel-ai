# Validation: solera-handoff (v3)

> Unique validation rules for this skill. Schema: [docs/reference/self-verification-schema.md](../../../docs/reference/self-verification-schema.md).

## Structural

```yaml
structural:
  - {id: S-001, name: "Input section", type: section_exists, target: SKILL.md, section: "## Input"}
  - {id: S-002, name: "Output section", type: section_exists, target: SKILL.md, section: "## Output"}
  - {id: S-003, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Handoff template exists", type: file_exists, paths: [assets/handoff-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md,
     patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-002, name: "triggers array has 2+ entries", type: pattern_match, target: SKILL.md,
     pattern: "triggers: \\[[^\\]]+,[^\\]]+\\]"}

  - {id: C-003, name: "composite skill declares uses", type: pattern_match, target: SKILL.md,
     pattern: "uses: \\[.*\\]"}

  - {id: C-010, name: "Auto-detects current state", type: content_contains, target: SKILL.md,
     patterns: ["auto-detects", "current session"]}

  - {id: C-011, name: "HANDOFF.md target declared", type: content_contains, target: SKILL.md,
     patterns: ["HANDOFF.md"]}

  - {id: C-020, name: "Removed v2 hierarchy references", type: content_not_contains, target: SKILL.md,
     patterns: ["_epic.md", "epic_name", "goal_id", "phase_id", "solera-write-epic"]}
```
