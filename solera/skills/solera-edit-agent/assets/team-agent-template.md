# Template: Team Agent (Persistent)

## {agent-name}.md

```markdown
# {agent-name}

> {One-line role description within the team}

## Role

{Team role details — responsibility scope within the team}

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

- [ ] Role is described in one line
- [ ] Tools list is minimal
- [ ] Instructions use explicit `condition → action` format
- [ ] Team Protocol section present (Messaging, Task Management, Shutdown)
- [ ] Shutdown handling covers both cases (in-progress and idle)
