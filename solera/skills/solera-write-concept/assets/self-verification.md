# Validation: solera-write-concept (v3)

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/concept-template.md, assets/_index-template.md]}
  - {id: S-006, name: "Template has Workflow section", type: section_exists, target: assets/concept-template.md, section: "## Workflow"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Four modes documented", type: content_contains, target: SKILL.md, patterns: ["create", "update", "deprecate", "archive"]}
  - {id: C-011, name: "Living Axis framing", type: content_contains, target: SKILL.md, patterns: ["Living Axis", "Moment 1"]}
  - {id: C-012, name: "AI does not invent Intent", type: content_contains, target: SKILL.md, patterns: ["AI must not invent", "must not invent"]}
  - {id: C-013, name: "Human blocking on Intent", type: content_contains, target: SKILL.md, patterns: ["blocking", "Ask the human for the Intent"]}
  - {id: C-014, name: "just write it safeguard", type: content_contains, target: SKILL.md, patterns: ["just write it", "north star"]}
  - {id: C-015, name: "Template has six core sections", type: content_contains, target: assets/concept-template.md, patterns: ["# Intent", "# Current Design", "# Current Shape", "# Health", "# Contributions", "# Related Artifacts"]}

  - {id: C-020, name: "Index template structure", type: content_contains, target: assets/_index-template.md, patterns: ["## Active", "## Deprecated"]}
```
