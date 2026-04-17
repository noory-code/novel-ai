# Validation: solera-write-story (v3)

> Unique validation rules for the solera-write-story skill after the v3 open.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section in template", type: section_exists, target: assets/story.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/story.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Five workflow steps", type: count_check, target: assets/story.md, pattern: "### Step \\d+", min: 5, max: 5}
  - {id: S-004, name: "story template exists", type: file_exists, paths: [assets/story.md]}
  - {id: S-005, name: "retrospective template exists", type: file_exists, paths: [assets/retrospective.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-040, name: "Action Item decomposition reference", type: content_contains, target: SKILL.md, patterns: ["solera-execute-action-item", "Action Items"]}
  - {id: C-002, name: "US/TS distinction", type: content_contains, target: assets/story.md, patterns: ["User Story", "Technical Story"]}
  - {id: C-003, name: "Quality Criteria section", type: section_exists, target: assets/story.md, section: "## Quality Criteria"}
  - {id: C-004, name: "Story ID Rules", type: section_exists, target: assets/story.md, section: "## Story ID Rules"}
  - {id: C-005, name: "Status transition included", type: content_contains, target: assets/story.md, patterns: ["Status →"]}
  - {id: C-006, name: "Folder Structure section", type: section_exists, target: assets/story.md, section: "## Folder Structure"}
  - {id: C-007, name: "Acceptance Criteria pattern", type: content_contains, target: assets/story.md, patterns: ["## Acceptance Criteria"]}
  - {id: C-008, name: "Retrospective reference", type: content_contains, target: assets/story.md, patterns: ["RETROSPECTIVE.md", "retrospective.md"]}
  - {id: C-009, name: "Squash merge", type: content_contains, target: assets/story.md, patterns: ["Squash"]}
  - {id: C-010, name: "Action Items columns", type: content_contains, target: assets/story.md, patterns: ["Skill", "Agent", "Phase", "depends_on"]}

  - {id: C-011, name: "v3 Input Artifacts section", type: content_contains, target: assets/story.md, patterns: ["Input Artifacts"]}
  - {id: C-012, name: "v3 Output Artifacts section", type: content_contains, target: assets/story.md, patterns: ["Output Artifacts"]}
  - {id: C-013, name: "v3 contributes_to frontmatter", type: content_contains, target: assets/story.md, patterns: ["contributes_to:"]}
  - {id: C-014, name: "v3 belongs_to frontmatter", type: content_contains, target: assets/story.md, patterns: ["belongs_to:"]}

  - {id: C-020, name: "v3 Prerequisites: Concept + Milestone", type: content_contains, target: SKILL.md, patterns: ["concepts/_index.md", "contributes_to", "concept.align"]}
  - {id: C-021, name: "v3 Wrap-up includes Current Shape update", type: content_contains, target: SKILL.md, patterns: ["Current Shape", "Contributions"]}
  - {id: C-022, name: "v3 commit format uses primary_concept", type: content_contains, target: SKILL.md, patterns: ["primary_concept", "contributes_to[0]"]}
  - {id: C-023, name: "v3 Skills Used table", type: section_exists, target: SKILL.md, section: "## Skills Used"}
  - {id: C-024, name: "Skill scan step", type: content_contains, target: SKILL.md, patterns: ["Scan available skills", ".claude/skills/*/SKILL.md"]}
  - {id: C-025, name: "retro requires Concept Contribution Summary", type: content_contains, target: assets/retrospective.md, patterns: ["Concept Contribution Summary"]}

  - {id: C-030, name: "Removed v2 hierarchy references", type: content_not_contains, target: SKILL.md, patterns: ["_epic.md", "_goal.md", "solera-write-epic", "solera-write-goal", "epics/"]}
  - {id: C-031, name: "Removed v2 hierarchy references in template", type: content_not_contains, target: assets/story.md, patterns: ["_epic.md", "_goal.md", "epics/"]}
```
