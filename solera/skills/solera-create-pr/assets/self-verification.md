# Validation: solera-create-pr (v3)

> Unique validation rules for this skill.

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
  - {id: C-002, name: "Review procedure", type: content_contains, target: SKILL.md, patterns: ["Handle review", "review"]}
  - {id: C-003, name: "Merge procedure", type: content_contains, target: SKILL.md, patterns: ["squash merge", "Squash"]}
  - {id: C-004, name: "Branch deletion", type: content_contains, target: SKILL.md, patterns: ["Story branch is deleted", "branch deletion"]}
  - {id: C-005, name: "Target branch resolution", type: content_contains, target: SKILL.md, patterns: ["Target Branch Resolution", "default_pr_base"]}

  - {id: C-010, name: "v3 Story as PR unit", type: content_contains, target: SKILL.md, patterns: ["story_branch", "story/{story_id}-{story_name}"]}
  - {id: C-011, name: "v3 PR title with primary_concept", type: content_contains, target: SKILL.md, patterns: ["[{primary_concept}][{story_id}]"]}
  - {id: C-012, name: "v3 Wrap-up verification before PR", type: content_contains, target: SKILL.md, patterns: ["Concept Contribution Summary", "contributes_to", "# Contributions"]}
  - {id: C-013, name: "v3 RETROSPECTIVE required", type: content_contains, target: SKILL.md, patterns: ["RETROSPECTIVE.md"]}

  - {id: C-020, name: "Removed v2 Epic PR references", type: content_not_contains, target: SKILL.md, patterns: ["[Epic]", "epic_branch", "epic_name", "solera-publish-artifacts before creating the PR"]}
  - {id: C-021, name: "Removed v2 refs in template", type: content_not_contains, target: assets/pr-template.md, patterns: ["Epic:", "Goal:"]}
```
