# Validation: solera-create-pr

> This file defines the unique validation rules for the solera-create-pr skill.

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
  - {id: C-005, name: "Target branch resolution", type: content_contains, target: SKILL.md, patterns: ["Target Branch Resolution", "default_pr_base"]}
  - {id: C-006, name: "Artifact promotion check", type: content_contains, target: SKILL.md, patterns: ["Artifact promotion check", "solera-publish-artifacts"]}
  - {id: C-007, name: "target_branch optional", type: content_contains, target: SKILL.md, patterns: ["target_branch | N"]}
```
