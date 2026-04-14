# Validation: solera-migrate-v2 (v3)

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure (7 steps, all BLOCKING on approval)"}
  - {id: S-003, name: "Resume Semantics section", type: section_exists, target: SKILL.md, section: "## Resume Semantics"}
  - {id: S-004, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-005, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-006, name: "Migration notes template present", type: file_exists, paths: [assets/migration-notes-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit"]}

  - {id: C-010, name: "Seven steps numbered", type: content_contains, target: SKILL.md, patterns: ["### Step 1 — Freeze", "### Step 2 — Skeleton", "### Step 3", "### Step 4", "### Step 5", "### Step 6", "### Step 7"]}
  - {id: C-011, name: "Non-destructive principle", type: content_contains, target: SKILL.md, patterns: ["Non-destructive", "_v2-archive"]}
  - {id: C-012, name: "Blocking on judgment", type: content_contains, target: SKILL.md, patterns: ["Blocking on judgment", "BLOCKING"]}
  - {id: C-013, name: "Git-aware moves", type: content_contains, target: SKILL.md, patterns: ["git mv", "preserves git history"]}
  - {id: C-014, name: "Clean working tree required", type: content_contains, target: SKILL.md, patterns: ["Working tree must be clean"]}
  - {id: C-015, name: "Three ID strategies offered", type: content_contains, target: SKILL.md, patterns: ["Renumber", "Prefix by Epic", "Keep and suffix"]}
  - {id: C-016, name: "contributes_to confidence ratings", type: content_contains, target: SKILL.md, patterns: ["Confidence: high", "confidence: LOW", "needs human review"]}
  - {id: C-017, name: "Concept renamed to domain-model", type: content_contains, target: SKILL.md, patterns: ["catalog/published/domain-model"]}
  - {id: C-018, name: "pre-v3 synthetic milestone required", type: content_contains, target: SKILL.md, patterns: ["pre-v3", "synthetic", "required"]}
  - {id: C-019, name: "Batch Concept authoring (no per-invoke)", type: content_contains, target: SKILL.md, patterns: ["Batch-processing constraint", "grounding every sentence"]}

  - {id: C-020, name: "No Workflow section (rationale stated)", type: content_contains, target: SKILL.md, patterns: ["one-shot transition skill", "no template-level Workflow"]}

  - {id: C-021, name: "Step 2 Identity copy policy present", type: content_contains, target: SKILL.md, patterns: ["Identity copy policy", "mission.md", "core-values.md", "vision_", "tone-and-manner"]}
  - {id: C-022, name: "Journey subdir handling under identity", type: content_contains, target: SKILL.md, patterns: ["journeys/", "catalog/published/journey/"]}
  - {id: C-023, name: "Unknown catalog type BLOCKING prompt", type: content_contains, target: SKILL.md, patterns: ["unknown catalog type", "_unclassified/{type}/"]}
  - {id: C-024, name: "Standard vs non-standard identity classification", type: content_contains, target: SKILL.md, patterns: ["v3 standard identity", "Non-standard identity files"]}
```
