# Self-Verification Schema — Canonical Reference

> **SSOT.** Every `skills/*/assets/self-verification.md` in this plugin must follow the schema defined here.
> If you are writing or editing a self-verification file, read this document first. Format drift is not allowed.

## File Shape

```markdown
# Validation: {skill-name} (v3)

> Unique validation rules for this skill.

## Structural

```yaml
structural:
  - {id: S-001, name: "...", type: section_exists, target: SKILL.md, section: "## Input"}
  # ...
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md, patterns: [...]}
  # ...
```
```

Both sections are mandatory. Either may be empty (`structural: []`), but the YAML block and heading must be present.

## ID Convention

| Prefix | Meaning | Numeric range |
|--------|---------|---------------|
| `S-NNN` | Structural rule (sections, files exist) | 001–099 |
| `C-NNN` | Content / semantic rule (phrases, patterns, absences) | 001–999 |

- **C-001 is reserved** for the AI-First banned-phrases check. Every skill that has user-facing prose must include it. See the canonical pattern list below.
- Within a skill, IDs must be unique. Across skills they may overlap.
- When a rule is removed, leave its ID retired (do not renumber) so historical diffs stay readable.

## Supported Check Types

| `type` | Purpose | Required fields |
|--------|---------|-----------------|
| `section_exists` | A given `## Heading` exists in `target` | `target`, `section` |
| `file_exists` | Each path in `paths[]` exists on disk | `paths` |
| `content_contains` | All `patterns[]` appear in `target` | `target`, `patterns` |
| `content_not_contains` | None of `patterns[]` appear in `target` | `target`, `patterns` |
| `count_check` | `pattern` regex matches between `min` and `max` times in `target` | `target`, `pattern`, `min`, `max` |
| `pattern_match` | `pattern` regex matches `target` at least once | `target`, `pattern` |

`target` is a repo-relative path (e.g., `SKILL.md`, `assets/story.md`), resolved from the skill directory.

## AI-First Banned Phrases (C-001)

This is the canonical pattern list. Every skill's C-001 must use **exactly** this set:

```yaml
- {id: C-001, name: "No AI-First banned phrases", type: content_not_contains, target: SKILL.md,
   patterns: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly"]}
```

To add a new banned phrase:

1. Update this list here first.
2. Propagate to every `self-verification.md` in the same PR.
3. Run the all-skills grep to catch existing violations.

Skills that intentionally mention a banned phrase (e.g., `solera-edit-command`, `solera-edit-rule` explain what not to do) are exempt from C-001 — omit the rule rather than working around it.

## Compact vs Expanded YAML

Either style is acceptable inside the YAML block. Choose one per file for readability.

**Compact** (one line per rule — preferred when rules are short):
```yaml
- {id: S-001, name: "Procedure section", type: section_exists, target: SKILL.md, section: "## Procedure"}
```

**Expanded** (multi-line — preferred when `patterns[]` has 4+ entries):
```yaml
- id: C-005
  name: "Move mapping includes v3 types"
  type: content_contains
  target: SKILL.md
  patterns:
    - "domain-model"
    - "persona"
    - "service-map"
```

Both compile to the same rule record. Do not mix styles within a single rule.

## Forbidden Patterns

The following **must not** appear in any `self-verification.md`:

- Heading styles other than `## Structural` + `## Semantic` (no `## TC001`, no numbered-per-section).
- Free-form prose between YAML blocks — keep explanatory text in the file's short header (`> Unique validation rules for this skill.`).
- Rules without `id:` — every rule must be addressable for regression tests and grep.

## Downstream References

Files that must stay in sync with this schema:

- `skills/*/assets/self-verification.md` — every instance
- `tests/test_skill_validation.py` — parses `id:` field to identify specific rule regressions
