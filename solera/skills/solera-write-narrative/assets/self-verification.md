# Validation: solera-write-narrative

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/narrative-template.md, assets/_index-template.md]}
  - {id: S-006, name: "Template has Workflow section", type: section_exists, target: assets/narrative-template.md, section: "## Workflow"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Four modes documented", type: content_contains, target: SKILL.md, patterns: ["create", "update", "deprecate", "archive"]}
  - {id: C-011, name: "Living Axis framing", type: content_contains, target: SKILL.md, patterns: ["Living Axis", "upstream of Concepts"]}
  - {id: C-012, name: "Distinguishes Narrative from Time-bound Story", type: content_contains, target: SKILL.md, patterns: ["Narrative is not that", "Time-bound", "narratives/", "stories/"]}
  - {id: C-013, name: "Three forms supported", type: content_contains, target: SKILL.md, patterns: ["user_story", "jtbd", "scenario"]}
  - {id: C-014, name: "Acceptance Cues are NOT acceptance criteria", type: content_contains, target: SKILL.md, patterns: ["NOT acceptance criteria", "Not acceptance criteria"]}
  - {id: C-015, name: "AI does not invent narrative content", type: content_contains, target: SKILL.md, patterns: ["AI must not invent", "must not invent"]}
  - {id: C-016, name: "Propose as Concept goes through Service canvas (stub guard)", type: content_contains, target: SKILL.md, patterns: ["Propose as Concept", "stub", "needs human review"]}
  - {id: C-017, name: "Never auto-finalize a Concept from this skill", type: content_contains, target: SKILL.md, patterns: ["Never auto-finalize a new Concept", "never auto-finalize"]}
  - {id: C-018, name: "about is required, 1+ Personas", type: content_contains, target: SKILL.md, patterns: ["about", "1+", "required"]}
  - {id: C-019, name: "Template has core sections", type: content_contains, target: assets/narrative-template.md, patterns: ["# Statement", "# Context", "# Acceptance Cues", "# Related"]}
  - {id: C-020, name: "Frontmatter declares kind: narrative + form + about", type: content_contains, target: assets/narrative-template.md, patterns: ["kind: narrative", "form:", "about:"]}

  - {id: C-021, name: "Index template structure", type: content_contains, target: assets/_index-template.md, patterns: ["## Active", "## Deprecated"]}
```
