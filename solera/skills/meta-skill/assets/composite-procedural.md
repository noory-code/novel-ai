# Template: Composite + Procedural

> Multi-skill procedural workflow. Examples: writing-goal, writing-epic.

## Frontmatter

```yaml
---
name: skill-name
description: What workflow this defines
metadata:
  version: "1.0.0"
  category: planning | flutter | ...
  type: composite
  style: procedural
  triggers: [trigger keywords]
  uses: [skill-1, skill-2]  # required for composite
---
```

## Body Structure

### Prerequisites

- prerequisite list
- If missing → invoke the relevant skill before proceeding

### Input

- **param_name** (required): description
- **param_name** (optional, default: default_value): description

### Output

- `path/pattern` — description
- `path/pattern` — ref: [template](assets/template.md)

### Skills Used

| Skill | Purpose |
|---|---|
| `skill-1` | purpose1 |
| `skill-2` | purpose2 |

### Procedure

1. **Prepare and analyze**
   - [ ] verification step

2. **Use skill-1** (invoke: skill-1)
   - [ ] when condition

3. **Use skill-2** (invoke: skill-2)
   - [ ] when condition

4. **Validate**
   - [ ] validation step

### Completion Checklist

- [ ] All steps complete
- [ ] Output files created
- [ ] Validation passed

### Common Mistakes

| Wrong | Right |
|---|---|
| Missing `uses` field | `composite` type requires a non-empty `uses` list |
| Ignoring skill dependencies | Explicitly link input/output between skills in the procedure |
