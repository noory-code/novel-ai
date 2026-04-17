# Validation: solera-write-milestone (v3)

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-003, name: "Gate check execution section", type: section_exists, target: SKILL.md, section: "## Gate check execution"}
  - {id: S-004, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-005, name: "Templates present", type: file_exists, paths: [assets/milestone-template.md, assets/_index-template.md]}
  - {id: S-006, name: "Template has Workflow section", type: section_exists, target: assets/milestone-template.md, section: "## Workflow"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Three modes documented", type: content_contains, target: SKILL.md, patterns: ["create", "update", "mark-released"]}
  - {id: C-011, name: "Moment 2 framing", type: content_contains, target: SKILL.md, patterns: ["Moment 2", "Milestone Agreement"]}
  - {id: C-012, name: "Agreement Cycle is non-negotiable", type: content_contains, target: SKILL.md, patterns: ["non-negotiable", "analysis round"]}
  - {id: C-013, name: "Never agree on first round silently", type: content_contains, target: SKILL.md, patterns: ["Never mark as agreed on the first round"]}
  - {id: C-014, name: "skip analysis requires minimum", type: content_contains, target: SKILL.md, patterns: ["skip analysis", "minimal one-line"]}
  - {id: C-015, name: "milestone.agree gate check point", type: content_contains, target: SKILL.md, patterns: ["milestone.agree"]}

  - {id: C-020, name: "Template required sections", type: content_contains, target: assets/milestone-template.md, patterns: ["# Scope", "# AI Analysis", "# Agreement Log", "# Exit Criteria"]}
  - {id: C-021, name: "Four statuses defined", type: content_contains, target: SKILL.md, patterns: ["proposed", "agreed", "in-progress", "released"]}
```
