# Validation: create-pr

> This file defines the unique validation rules for the create-pr skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
  - {id: S-002, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-003, name: "PR template exists", type: file_exists, paths: [assets/pr-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "gh pr create command", type: content_contains, target: SKILL.md, patterns: ["gh pr create"]}
  - {id: C-002, name: "Review procedure", type: content_contains, target: SKILL.md, patterns: ["review"]}
  - {id: C-003, name: "Merge procedure", type: content_contains, target: SKILL.md, patterns: ["merge"]}
  - {id: C-004, name: "Branch deletion", type: content_contains, target: SKILL.md, patterns: ["delete branch"]}
```
