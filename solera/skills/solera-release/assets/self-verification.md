# Validation: solera-release (v3)

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/release-notes-template.md, assets/stories-manifest-template.md, assets/_index-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit"]}

  - {id: C-010, name: "Moment 4 framing", type: content_contains, target: SKILL.md, patterns: ["Moment 4", "immutable", "past stays the past"]}
  - {id: C-011, name: "Requires milestone released status", type: content_contains, target: SKILL.md, patterns: ["status: released", "mark-released"]}
  - {id: C-012, name: "Immutability marker and refusal to overwrite", type: content_contains, target: SKILL.md, patterns: [".released", "Refuse to overwrite", "never modifies"]}
  - {id: C-013, name: "Snowflake marker on snapshot copies", type: content_contains, target: SKILL.md, patterns: ["❄️", "Snapshotted for release"]}
  - {id: C-014, name: "Human approval on README", type: content_contains, target: SKILL.md, patterns: ["BLOCKING", "human confirmation", "human has the final word"]}
  - {id: C-015, name: "Incomplete Story warning", type: content_contains, target: SKILL.md, patterns: ["belongs to this milestone but is not complete", "require human confirmation"]}

  - {id: C-020, name: "No Workflow section (rationale stated)", type: content_contains, target: SKILL.md, patterns: ["not a work item", "no Workflow section"]}

  - {id: C-030, name: "Removed v2 phase/goal tag references", type: content_not_contains, target: SKILL.md, patterns: ["[Phase]-[Goal number]", "H1-G01", "phase_id", "goal_id"]}
```
