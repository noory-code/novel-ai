# Validation: solera-write-story

> This file defines the unique validation rules for the solera-write-story skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow section", type: section_exists, target: assets/story.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/story.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4 stages", type: count_check, target: assets/story.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "story template exists", type: file_exists, paths: [assets/story.md]}
  - {id: S-005, name: "retro template exists", type: file_exists, paths: [assets/retro.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Action Item repeat block", type: content_contains, target: assets/story.md, patterns: ["solera-execute-action-item invoke", "<!-- /repeat -->"]}
  - {id: C-002, name: "US/TS distinction", type: content_contains, target: assets/story.md, patterns: ["User Story", "Technical Story"]}
  - {id: C-003, name: "Quality Criteria section", type: section_exists, target: assets/story.md, section: "## Quality Criteria"}
  - {id: C-004, name: "Story ID Rules", type: section_exists, target: assets/story.md, section: "## Story ID Rules"}
  - {id: C-005, name: "Status transition included", type: content_contains, target: assets/story.md, patterns: ["Status →"]}
  - {id: C-006, name: "Folder Structure section", type: section_exists, target: assets/story.md, section: "## Folder Structure"}
  - {id: C-007, name: "Acceptance criteria pattern", type: content_contains, target: assets/story.md, patterns: ["## Acceptance Criteria"]}
  - {id: C-008, name: "Retrospective write reference", type: content_contains, target: assets/story.md, patterns: ["Write retrospective", "RETRO.md"]}
  - {id: C-009, name: "Squash merge", type: content_contains, target: assets/story.md, patterns: ["Squash merge"]}
  - {id: C-010, name: "Action Items agent column", type: content_contains, target: assets/story.md, patterns: ["Agent", "Phase", "depends_on"]}
  - {id: C-011, name: "retro template reference", type: content_contains, target: assets/story.md, patterns: ["retro.md"]}
  - {id: C-012, name: "Prerequisite Epic context", type: content_contains, target: SKILL.md, patterns: ["_epic.md", "published/identity/mission.md"]}
  - {id: C-013, name: "Wrap-up procedure exists", type: content_contains, target: SKILL.md, patterns: ["Wrap-up", "RETRO.md", "Squash merge"]}
  - {id: C-014, name: "Skills used table", type: section_exists, target: SKILL.md, section: "## Skills Used"}
```
