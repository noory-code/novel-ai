# Validation: writing-goal

> This file defines the unique validation rules for the writing-goal skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section", type: section_exists, target: assets/goal-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/goal-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4 stages", type: count_check, target: assets/goal-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "goal-template exists", type: file_exists, paths: [assets/goal-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Epic repeat block", type: content_contains, target: assets/goal-template.md, patterns: ["writing-epic invoke", "<!-- /repeat -->"]}
  - {id: C-002, name: "Goal type section", type: section_exists, target: assets/goal-template.md, section: "## Goal Types"}
  - {id: C-003, name: "Output templates", type: file_exists, paths: [assets/goal-template.md, assets/persona.md, assets/service-map.md]}
  - {id: C-004, name: "retro.md exists", type: file_exists, paths: [assets/retro.md]}
  - {id: C-005, name: "retro ref exists", type: content_contains, target: assets/goal-template.md, patterns: ["retro.md"]}
  - {id: C-006, name: "Status transition included", type: content_contains, target: assets/goal-template.md, patterns: ["Status →"]}
  - {id: C-007, name: "catalog-transition reference", type: content_contains, target: assets/goal-template.md, patterns: ["catalog-transition"]}
  - {id: C-008, name: "Enabler branch", type: content_contains, target: assets/goal-template.md, patterns: ["Enabler"]}
  - {id: C-009, name: "Input table", type: content_contains, target: SKILL.md, patterns: ["project_path"]}
  - {id: C-010, name: "Wrap-up procedure", type: content_contains, target: SKILL.md, patterns: ["Wrap-up"]}
  - {id: C-011, name: "Skills used table", type: section_exists, target: SKILL.md, section: "## Skills Used"}
  - {id: C-012, name: "persona-relationship reference", type: content_contains, target: SKILL.md, patterns: ["persona-relationship"]}
```
