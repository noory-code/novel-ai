# Validation: solera-write-persona

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-004, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/persona-template.md, assets/_index-template.md]}
  - {id: S-006, name: "Template has Workflow section", type: section_exists, target: assets/persona-template.md, section: "## Workflow"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Four modes documented", type: content_contains, target: SKILL.md, patterns: ["create", "update", "deprecate", "archive"]}
  - {id: C-011, name: "Living Axis framing", type: content_contains, target: SKILL.md, patterns: ["Living Axis", "upstream of Concepts"]}
  - {id: C-012, name: "AI does not invent who the user is", type: content_contains, target: SKILL.md, patterns: ["AI must not invent", "Invent who the user is", "can't invent who your user is"]}
  - {id: C-013, name: "Template has six core fields", type: content_contains, target: assets/persona-template.md, patterns: ["# Identity", "# Goals", "# Pains", "# Triggers", "# Quotes", "# Related"]}
  - {id: C-014, name: "Frontmatter declares kind: persona", type: content_contains, target: assets/persona-template.md, patterns: ["kind: persona"]}

  - {id: C-020, name: "Index template structure", type: content_contains, target: assets/_index-template.md, patterns: ["## Active", "## Deprecated"]}
```
