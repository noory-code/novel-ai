# solera

> Layered workflow execution for Claude Code — Phase → Goal → Epic → Story → Action Item

Like the solera aging method, where layers of work blend and deepen over time into something complete.

## Skills

| Skill | Description |
|-------|-------------|
| `writing-phase` | Define a Phase and track Goals |
| `writing-goal` | Write a Goal — Service Map, Persona → break into Epics |
| `writing-epic` | Write an Epic — Use Case, Concept → break into Stories |
| `writing-story` | Write a Story → break into Action Items (1 = 1 commit) |
| `writing-action-item` | Execute an Action Item. Smallest workflow unit. |
| `workflow-manage` | Read and execute the Workflow defined in each work item |
| `workflow-pr` | Create PR when Epic is done → review → merge |
| `catalog-transition` | Move artifacts/ → published/ when Goal is complete |
| `handoff` | Update HANDOFF.md for cross-session context (auto-runs on Stop) |

## Hooks

| Event | Behavior |
|-------|----------|
| `Stop` | Automatically runs the handoff skill — updates HANDOFF.md with current session state |

## Installation

```bash
claude plugin install /path/to/solera
```

## Workflow hierarchy

```
Phase  (quarterly plan)
  └─ Goal  (service objective)
       └─ Epic  (feature scope)
            └─ Story  (user scenario, 1-2 days)
                 └─ Action Item  (1 commit)
```
