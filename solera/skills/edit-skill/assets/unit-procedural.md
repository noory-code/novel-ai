# Template: Unit + Procedural

> Single-technology procedural workflow. Examples: flutter-freezed (class generation workflow).

## Frontmatter

```yaml
---
name: skill-name
description: What this skill creates or performs
metadata:
  version: "1.0.0"
  category: flutter | backend | infra | ...
  type: unit
  style: procedural
  triggers: [trigger keywords]
---
```

## Body Structure

### Input

- **param_name** (required): description
- **param_name** (optional, default: default_value): description

### Output

- `generated/file/path` — description

### Procedure

1. **Prepare**
   - [ ] verification step

2. **Core work**
   - [ ] action step

3. **Code generation** (if applicable)
   - [ ] run build tools

### Code Generation

```bash
dart run build_runner build --delete-conflicting-outputs
```

### Completion Checklist

- [ ] File created
- [ ] Build successful
- [ ] Tests passing

### Common Mistakes

| Wrong | Right |
|---|---|
| example | example |
