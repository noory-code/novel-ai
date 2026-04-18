# Template: Rule

## {rule-name}.md

```markdown
---
name: {rule-name}
description: {1-2 sentences — when should Claude consult this rule? List 2-3 concrete trigger phrases or file patterns.}
version: "1.0.0"
applies_to:
  - "{file glob or area — e.g. src/**/*.ts, api design, commit messages}"
---

# Rule: {Rule Name}

> **Scope**: {When does this rule apply — specific trigger condition, not "as appropriate"}

## Checklist

- [ ] {Verifiable item 1}
- [ ] {Verifiable item 2}
- [ ] {Verifiable item 3}

## Good / Bad Examples

| Bad | Good |
|---|---|
| {concrete wrong example} | {concrete right example} |
| {concrete wrong example} | {concrete right example} |
```

## Quality Criteria

- [ ] Frontmatter includes `name`, `description`, `version`, `applies_to`
- [ ] `description` names 2-3 concrete triggers (phrases or file patterns) — not "when appropriate"
- [ ] `applies_to` is a glob or bounded area, not "everywhere"
- [ ] Scope line is explicit (not "when appropriate" or "if needed")
- [ ] Each checklist item can be verified independently
- [ ] Good/Bad examples are specific and concrete (not generic)
- [ ] Line count ≤ 200
