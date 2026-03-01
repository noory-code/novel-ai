# Template: Task Agent (One-shot)

## {agent-name}.md

```markdown
# {agent-name}

> {One-line role description}

## Role

{Role details — what this agent does}

## Tools

- Read
- Glob
- Grep
{add tools needed for the role}

## Instructions

### Procedure

1. {Step 1}
2. {Step 2}
3. {Step 3}

### Reference Docs

- {path to relevant document}

### Rules

- {condition} → {action}
- {condition} → {action}

## Usage

```yaml
subagent_type: "{agent-name}"
prompt: "{example prompt}"
```
```

## Quality Criteria

- [ ] Role is described in one line
- [ ] Tools list is minimal (only what the role requires)
- [ ] Instructions use explicit `condition → action` format, not prose
- [ ] Usage example included
