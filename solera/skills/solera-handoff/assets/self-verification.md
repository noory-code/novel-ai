# Self-Verification

> Automated validation TCs (Test Cases) for skill definition

## TC001: Input section exists
```yaml
type: section_exists
section: "## Input"
```

## TC002: Output section exists
```yaml
type: section_exists
section: "## Output"
```

## TC003: Procedure section exists
```yaml
type: section_exists
section: "## Procedure"
```

## TC004: Completion Checklist exists
```yaml
type: section_exists
section: "## Completion Checklist"
```

## TC005: metadata.triggers has 2 or more items
```yaml
type: pattern_match
pattern: "triggers: \\[[^\\]]+,[^\\]]+\\]"
description: "triggers array requires at least 2 keywords"
```

## TC006: uses field exists (composite type)
```yaml
type: pattern_match
pattern: "uses: \\[.*\\]"
description: "composite type requires uses field"
```

## TC007: No AI-First banned phrases
```yaml
type: content_not_contains
forbidden_words: ["as appropriate", "if needed", "depending on the situation", "as you see fit", "handle accordingly", "depending on the case"]
description: "AI-First banned phrases must not be used"
```

## TC008: Procedure steps exist
```yaml
type: content_contains
required_patterns: ["### Step 1", "### Step 2", "### Step 3", "### Step 4"]
description: "Steps 1–4 exist in the Procedure section"
```

## TC009: assets file references
```yaml
type: cross_reference
referenced_files: ["assets/handoff-template.md", "assets/self-verification.md"]
description: "Confirm referenced assets files actually exist"
```
