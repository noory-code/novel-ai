# Validation: solera-write-epic

> This file defines the unique validation rules for the solera-write-epic skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section", type: section_exists, target: assets/epic-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/epic-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4 stages", type: count_check, target: assets/epic-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "epic-template exists", type: file_exists, paths: [assets/epic-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Story repeat block", type: content_contains, target: assets/epic-template.md, patterns: ["solera-write-story invoke", "<!-- /repeat -->"]}
  - {id: C-002, name: "Output templates", type: file_exists, paths: [assets/epic-template.md, assets/use-case.md, assets/entity.md, assets/concept.md]}
  - {id: C-003, name: "retro.md exists", type: file_exists, paths: [assets/retro.md]}
  - {id: C-004, name: "retro ref exists", type: content_contains, target: assets/epic-template.md, patterns: ["retro.md"]}
  - {id: C-005, name: "Status transition included", type: content_contains, target: assets/epic-template.md, patterns: ["Status →"]}
  - {id: C-006, name: "Use Case output", type: content_contains, target: assets/epic-template.md, patterns: ["use-case"]}
  - {id: C-007, name: "Entity output", type: content_contains, target: assets/epic-template.md, patterns: ["entities"]}
  - {id: C-008, name: "Prerequisite Goal context", type: content_contains, target: SKILL.md, patterns: ["_goal.md", "published/identity/mission.md"]}
  - {id: C-009, name: "Wrap-up procedure exists", type: content_contains, target: SKILL.md, patterns: ["Wrap-up", "RETROSPECTIVE.md", "solera-create-pr"]}
  - {id: C-010, name: "Skills used table", type: section_exists, target: SKILL.md, section: "## Skills Used"}
  - {id: C-011, name: "solera-publish-artifacts in Wrap-up", type: content_contains, target: assets/epic-template.md, patterns: ["solera-publish-artifacts"]}
```
