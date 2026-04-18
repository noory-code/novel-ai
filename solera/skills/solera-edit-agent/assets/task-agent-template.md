# Template: Task Agent (One-shot)

## {agent-name}.md

```markdown
---
name: {agent-name}
description: Use this agent when {trigger condition in one sentence}. Examples:

<example>
Context: {short context}
user: "{exact user phrasing that should trigger the agent}"
assistant: "I'll use the {agent-name} agent to {action}."
<commentary>
{why this agent, not another}
</commentary>
</example>

<example>
Context: {second, different trigger context}
user: "{different phrasing}"
assistant: "{assistant response}"
<commentary>
{rationale}
</commentary>
</example>

model: inherit        # inherit | sonnet | opus | haiku
color: blue           # blue | cyan | green | yellow | magenta | red
tools: [Read, Glob, Grep]   # minimal whitelist — list only what the role needs
---

# {agent-name}

> {One-line role description}

## Role

{Role details — what this agent does}

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

- [ ] Frontmatter includes `name`, `description`, `model`, `color`, `tools`
- [ ] `description` starts with "Use this agent when..." and includes 2+ `<example>` blocks with Context/user/assistant/commentary
- [ ] `model` is one of: `inherit` (default), `sonnet`, `opus`, `haiku`
- [ ] `color` is one of: `blue`, `cyan`, `green`, `yellow`, `magenta`, `red`
- [ ] `tools` is a minimal list — only what the role requires (no "all tools")
- [ ] Role is described in one line
- [ ] Instructions use explicit `condition → action` format, not prose
- [ ] Usage example included
