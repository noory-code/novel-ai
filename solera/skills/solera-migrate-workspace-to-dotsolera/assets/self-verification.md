# Validation: solera-migrate-workspace-to-dotsolera

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "Philosophy section", type: section_exists, target: SKILL.md, section: "## Philosophy"}
  - {id: S-002, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure (5 steps, one BLOCKING gate)"}
  - {id: S-003, name: "Resume Semantics section", type: section_exists, target: SKILL.md, section: "## Resume Semantics"}
  - {id: S-004, name: "Human-AI Protocol section", type: section_exists, target: SKILL.md, section: "## Human–AI Protocol"}
  - {id: S-005, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}

  - {id: C-010, name: "Five steps numbered", type: content_contains, target: SKILL.md, patterns: ["### Step 1 — Preflight", "### Step 2 — BLOCKING confirmation", "### Step 3 — Move", "### Step 4 — `.gitignore` patch", "### Step 5 — Commit"]}

  - {id: C-011, name: "Idempotency rule", type: content_contains, target: SKILL.md, patterns: ["Idempotent re-runs", "already migrated"]}
  - {id: C-012, name: "Single BLOCKING gate", type: content_contains, target: SKILL.md, patterns: ["BLOCKING", "Apply this migration?"]}
  - {id: C-013, name: "Git-aware moves", type: content_contains, target: SKILL.md, patterns: ["git mv", "preserves git history", "preserves all subdirs"]}
  - {id: C-014, name: "Clean working tree required", type: content_contains, target: SKILL.md, patterns: ["Working tree must be clean"]}
  - {id: C-015, name: "Single commit constraint", type: content_contains, target: SKILL.md, patterns: ["one commit", "single commit", "Single commit only"]}
  - {id: C-016, name: "Resume by commit trailer", type: content_contains, target: SKILL.md, patterns: ["Solera-Migrate-Step: workspace-to-dotsolera"]}
  - {id: C-017, name: "Top-level state files handled", type: content_contains, target: SKILL.md, patterns: ["progress.md", "HANDOFF.md"]}
  - {id: C-018, name: ".gitignore patch policy", type: content_contains, target: SKILL.md, patterns: ["patches existing", "do not introduce new ignore rules"]}
  - {id: C-019, name: "Both directories present is conflict", type: content_contains, target: SKILL.md, patterns: ["Both .solera/ and workspace/ exist", "remove the wrong one"]}

  - {id: C-020, name: "No Workflow section (rationale stated)", type: content_contains, target: SKILL.md, patterns: ["one-shot transition skill", "no template-level Workflow"]}

  - {id: C-021, name: "Backward-compat note for Solera v1.x", type: content_contains, target: SKILL.md, patterns: ["Solera v1.x falls back", "removed in a future minor"]}
```
