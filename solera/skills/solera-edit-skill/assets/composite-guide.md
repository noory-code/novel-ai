# Template: Composite + Guide

> Multi-skill combination reference document. Examples: UI-Flow guide, Clean Architecture guide.

## Frontmatter

```yaml
---
name: skill-name
description: What skills this combines and when to use it
metadata:
  version: "1.0.0"
  category: flutter | design | ...
  type: composite
  style: guide
  triggers: [trigger keywords]
  uses: [skill-1, skill-2, skill-3]  # required for composite
---
```

## Body Structure

### Skills Used

| Skill | Purpose |
|---|---|
| `skill-1` | purpose1 |
| `skill-2` | purpose2 |

### Integration Overview

```
skill-1 → skill-2 → skill-3
```

### Quick Reference

#### Pattern 1: {pattern name}

```dart
// combining skill-1 and skill-2
```

#### Pattern 2: {pattern name}

```dart
// combining skill-2 and skill-3
```

### Dependency Direction

```
A → B → C
(dependency arrow direction)
```

### Rules

| Item | Rule |
|---|---|
| **Skill combination** | rule1 |
| **Order** | rule2 |

### Common Mistakes

| Wrong | Right |
|---|---|
| wrong combination | correct combination |

### Related Skills

| Skill | Purpose |
|---|---|
| `related-skill-1` | related purpose |
