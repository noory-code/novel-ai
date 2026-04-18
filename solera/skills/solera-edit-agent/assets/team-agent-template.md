# Template: Team Agent (Persistent)

## {agent-name}.md

```markdown
---
name: {agent-name}
description: Use this agent when {team-level trigger condition — e.g. a team lead is orchestrating parallel roles and this specialist is needed}. Examples:

<example>
Context: {what the team is doing when this specialist is spun up}
user: "{request to the team lead}"
assistant: "I'll bring in the {agent-name} agent to {role within the team}."
<commentary>
{why this specialist rather than handling inline}
</commentary>
</example>

<example>
Context: {second trigger context for the same role}
user: "{different phrasing}"
assistant: "{assistant response}"
<commentary>
{rationale}
</commentary>
</example>

model: inherit        # inherit | sonnet | opus | haiku
color: cyan           # blue | cyan | green | yellow | magenta | red
tools: [Read, Glob, Grep]   # minimal whitelist — only what the role needs
---

# {agent-name}

> {One-line role description within the team}

## Role

{Team role details — responsibility scope within the team}

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

## Team Protocol

### Messaging

- On task complete: report result to team lead via SendMessage
- On blocker: immediately notify team lead via SendMessage

### Task Management

- Use TaskList to check assigned tasks
- Use TaskUpdate to change status (in_progress → completed)
- After completion: claim next unassigned task

### Shutdown

- On shutdown_request received:
  - No task in progress → shutdown_response: approve: true
  - Task in progress → shutdown_response: approve: false + reason
```

## Quality Criteria

- [ ] Frontmatter includes `name`, `description`, `model`, `color`, `tools`
- [ ] `description` starts with "Use this agent when..." and includes 2+ `<example>` blocks (Context/user/assistant/commentary)
- [ ] `model` is one of: `inherit`, `sonnet`, `opus`, `haiku`
- [ ] `color` is one of: `blue`, `cyan`, `green`, `yellow`, `magenta`, `red` — team agents typically use a color distinct from the team lead
- [ ] `tools` is a minimal whitelist
- [ ] Role is described in one line
- [ ] Instructions use explicit `condition → action` format
- [ ] Team Protocol section present (Messaging, Task Management, Shutdown)
- [ ] Shutdown handling covers both cases (in-progress and idle)
