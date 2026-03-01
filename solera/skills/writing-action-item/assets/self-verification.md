# Validation: writing-action-item

> This file defines the unique validation rules for the writing-action-item skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section", type: section_exists, target: assets/action-item.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/action-item.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 3 stages", type: count_check, target: assets/action-item.md, pattern: "### Step \\d+", min: 3, max: 3}
  - {id: S-004, name: "action-item template exists", type: file_exists, paths: [assets/action-item.md]}
  - {id: S-005, name: "retro template exists", type: file_exists, paths: [assets/retro.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "1 AI = 1 commit", type: content_contains, target: SKILL.md, patterns: ["1 Action Item = 1 commit"]}
  - {id: C-002, name: "Commit message format", type: content_contains, target: assets/action-item.md, patterns: ["[epic-name]"]}
  - {id: C-003, name: "Status transition included", type: content_contains, target: assets/action-item.md, patterns: ["Status →"]}
  - {id: C-004, name: "Cautions section", type: section_exists, target: assets/action-item.md, section: "## Cautions"}
  - {id: C-005, name: "Folder Structure section", type: section_exists, target: assets/action-item.md, section: "## Folder Structure"}
  - {id: C-006, name: "Commit Message Format section", type: section_exists, target: assets/action-item.md, section: "## Commit Message Format"}
  - {id: C-007, name: "Retrospective write reference", type: content_contains, target: assets/action-item.md, patterns: ["Write retrospective", "RETRO.md"]}
  - {id: C-008, name: "Agent assignment metadata", type: content_contains, target: assets/action-item.md, patterns: ["Agent:", "Phase:", "depends_on:"]}
  - {id: C-009, name: "output_paths metadata", type: content_contains, target: assets/action-item.md, patterns: ["output_paths"]}
  - {id: C-010, name: "Prerequisite Story context", type: content_contains, target: SKILL.md, patterns: ["_story.md", "depends_on"]}
  - {id: C-011, name: "Skills used table", type: section_exists, target: SKILL.md, section: "## Skills Used"}
```
