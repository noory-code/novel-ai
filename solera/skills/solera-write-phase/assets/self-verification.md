# Validation: solera-write-phase

> This file defines the unique validation rules for the solera-write-phase skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section", type: section_exists, target: assets/phase-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/phase-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4 stages", type: count_check, target: assets/phase-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "phase-template exists", type: file_exists, paths: [assets/phase-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Goal repeat block", type: content_contains, target: assets/phase-template.md, patterns: ["solera-write-goal invoke", "<!-- /repeat -->"]}
  - {id: C-002, name: "retro.md exists", type: file_exists, paths: [assets/retro.md]}
  - {id: C-003, name: "retro ref exists", type: content_contains, target: assets/phase-template.md, patterns: ["retro.md"]}
  - {id: C-004, name: "Status transition included", type: content_contains, target: assets/phase-template.md, patterns: ["Status →"]}
  - {id: C-005, name: "roadmap prerequisite", type: content_contains, target: SKILL.md, patterns: ["roadmap.md"]}
  - {id: C-006, name: "Phase folder structure", type: section_exists, target: SKILL.md, section: "## Folder Structure"}
  - {id: C-007, name: "Input table", type: content_contains, target: SKILL.md, patterns: ["project_path"]}
  - {id: C-008, name: "Wrap-up artifacts check", type: content_contains, target: assets/phase-template.md, patterns: ["artifacts/"]}
  - {id: C-009, name: "SUMMARY.md mention", type: content_contains, target: assets/phase-template.md, patterns: ["SUMMARY.md"]}
```
