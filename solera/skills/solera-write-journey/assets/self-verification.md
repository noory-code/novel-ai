# Validation: solera-write-journey

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/journey-template.md, assets/_index-template.md]}
  - {id: S-006, name: "Template has Workflow section", type: section_exists, target: assets/journey-template.md, section: "## Workflow"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Four modes documented", type: content_contains, target: SKILL.md, patterns: ["create", "update", "deprecate", "archive"]}
  - {id: C-011, name: "Living Axis framing", type: content_contains, target: SKILL.md, patterns: ["Living Axis", "upstream of Concepts"]}
  - {id: C-012, name: "walks relation is single-Persona, required", type: content_contains, target: SKILL.md, patterns: ["walks", "exactly one", "split"]}
  - {id: C-013, name: "Steps stay in the table (no separate files)", type: content_contains, target: SKILL.md, patterns: ["Steps stay", "table", "not as separate files"]}
  - {id: C-014, name: "AI does not invent journey content", type: content_contains, target: SKILL.md, patterns: ["AI must not invent", "must not invent"]}
  - {id: C-015, name: "Template has core sections", type: content_contains, target: assets/journey-template.md, patterns: ["# Trigger", "# Steps", "# Outcome", "# Related"]}
  - {id: C-016, name: "Template steps table has six columns", type: content_contains, target: assets/journey-template.md, patterns: ["| # | Stage | Step | Touchpoint | Emotion | Pain |"]}
  - {id: C-017, name: "Frontmatter declares kind: journey + walks", type: content_contains, target: assets/journey-template.md, patterns: ["kind: journey", "walks: {persona_id}"]}

  - {id: C-020, name: "Index template structure", type: content_contains, target: assets/_index-template.md, patterns: ["## Active", "## Deprecated"]}
```
