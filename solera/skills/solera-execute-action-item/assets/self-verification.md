# Validation: solera-execute-action-item (v3)

> Unique validation rules for the solera-execute-action-item skill after the v3 open.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section in template", type: section_exists, target: assets/action-item.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/action-item.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Four workflow steps (0..3)", type: count_check, target: assets/action-item.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "action-item template exists", type: file_exists, paths: [assets/action-item.md]}
  - {id: S-005, name: "retrospective template exists", type: file_exists, paths: [assets/retrospective.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-040, name: "1 ACT = 1 commit principle", type: content_contains, target: SKILL.md, patterns: ["1 Action Item = 1 commit"]}
  - {id: C-002, name: "v3 commit scope tag uses primary_concept", type: content_contains, target: assets/action-item.md, patterns: ["[{primary_concept}]", "contributes_to"]}
  - {id: C-003, name: "Status transition included", type: content_contains, target: assets/action-item.md, patterns: ["Status →"]}
  - {id: C-004, name: "Cautions section", type: section_exists, target: assets/action-item.md, section: "## Cautions"}
  - {id: C-005, name: "Folder Structure section", type: section_exists, target: assets/action-item.md, section: "## Folder Structure"}
  - {id: C-006, name: "Commit Message Format section", type: section_exists, target: assets/action-item.md, section: "## Commit Message Format"}
  - {id: C-007, name: "Retrospective section", type: content_contains, target: assets/action-item.md, patterns: ["## Retrospective"]}
  - {id: C-008, name: "Metadata fields", type: content_contains, target: assets/action-item.md, patterns: ["Skill:", "Agent:", "Phase:", "depends_on:"]}
  - {id: C-009, name: "output_paths metadata", type: content_contains, target: assets/action-item.md, patterns: ["output_paths"]}
  - {id: C-010, name: "Prerequisite Story context", type: content_contains, target: SKILL.md, patterns: ["_story.md", "depends_on"]}
  - {id: C-011, name: "Skill Resolution section", type: section_exists, target: SKILL.md, section: "## Skill Resolution"}

  - {id: C-020, name: "v3 primary_concept derivation", type: content_contains, target: SKILL.md, patterns: ["primary_concept", "contributes_to[0]"]}
  - {id: C-021, name: "v3 Output Artifacts append on Story", type: content_contains, target: SKILL.md, patterns: ["Output Artifacts", "parent Story"]}
  - {id: C-022, name: "v3 Architecture check retained", type: content_contains, target: SKILL.md, patterns: ["architecture_rules", "forbidden_imports"]}
  - {id: C-023, name: "v3 act.start and act.done gates", type: content_contains, target: SKILL.md, patterns: ["act.start", "act.done"]}
  - {id: C-024, name: "Atomic Commits for system improvements", type: content_contains, target: SKILL.md, patterns: ["separate commit", "chore(solera)"]}

  - {id: C-030, name: "Removed v2 hierarchy references", type: content_not_contains, target: SKILL.md, patterns: ["_epic.md", "epic_name", "goal_id", "phase_id"]}
  - {id: C-031, name: "Removed v2 scope tag", type: content_not_contains, target: SKILL.md, patterns: ["[epic-name]"]}
  - {id: C-032, name: "Removed v2 refs in template", type: content_not_contains, target: assets/action-item.md, patterns: ["[epic-name]", "epic_path"]}
```
