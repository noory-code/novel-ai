---
name: solera-edit-agent
user-invocable: true
description: Define or improve an agent — specifies role, tools, and boundaries so Claude acts as a focused specialist.
metadata:
  version: "2.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [create an agent, edit an agent, improve an agent, review an agent, define a subagent]
  uses: []
---

# Edit Agent

## Agent Definition Fields

| Field | Required | Description |
|---|---|---|
| Role | Y | One-line agent role |
| Tools | Y | Allowed tools list |
| Instructions | Y | System prompt (AI-First style) |
| Domain | N | Paths to reference skills/docs |
| Mode | N | task / team / both |
| Usage | N | Invocation example |

## Input

| Parameter | Required | Description | Example |
|---|---|---|---|
| action | Y | create \| review \| improve | create |
| agent_name | N | Name in hyphen-case (required when action=create) | code-reviewer |
| agent_path | N | Path to existing agent (required when action=review or improve) | .claude/agents/code-reviewer.md |
| agent_mode | N | task \| team \| both (default: task) | task |

## Output

| Step | Output | Path |
|---|---|---|
| Create | Agent definition file | `.claude/agents/{agent_name}.md` |
| Create | CLAUDE.md Agents table | Updated `## Agents` section |

## Procedure

### CREATE

**Step 1: Gather requirements**

- [ ] Define role in one line
- [ ] Identify required tools (only what's needed for the role)
- [ ] Determine domain knowledge scope
- [ ] Decide agent_mode: task | team | both
- [ ] List reference skills/docs

**Step 2: Design by mode**

- task: choose subagent_type (Explore | Plan | Bash | general-purpose), design one-shot prompt
- team: define persistent role, SendMessage protocol, include shutdown_response handling
- both: include both task and team sections

**Step 3: Write agent file** — ref: [assets/task-agent-template.md](assets/task-agent-template.md) | [assets/team-agent-template.md](assets/team-agent-template.md)

- [ ] Name in hyphen-case
- [ ] All required sections present (Role, Tools, Instructions)
- [ ] team mode → include shutdown protocol

**Step 4: Update CLAUDE.md**

- [ ] Add row to `## Agents` table (or create section if absent)

**Step 5: Validate**

- [ ] Tools list is minimal (only what the role requires)
- [ ] Instructions use explicit conditions, not "handle appropriately"
- [ ] team mode has shutdown protocol

### REVIEW

**Step 6: Analyze existing agent**

- [ ] Required sections present (Role, Tools, Instructions)
- [ ] Role matches tools (no unnecessary tool access)
- [ ] Instructions follow AI-First principle (explicit conditions → actions)
- [ ] team mode → shutdown protocol present
- [ ] Prompt quality: specific conditions and actions

**Step 7: Generate review report**

- Summarize findings and recommendations

### IMPROVE

**Step 8: Run review (invoke steps 6-7)**

- Obtain review report

**Step 9: Apply improvements**

- [ ] Apply review findings
- [ ] Re-validate required sections

## Common Mistakes

| Wrong | Right |
|---|---|
| Allowing all tools | List only tools the role actually needs |
| "Handle it appropriately" | Explicit: `if {condition} → {action}` |
| team agent without shutdown | Include shutdown_response handling |
| Agent name in CamelCase | Use hyphen-case |
| Multiple responsibilities per agent | One role per agent (SoC) |

## Completion Checklist

- [ ] `.claude/agents/{agent_name}.md` created
- [ ] Required sections present (Role, Tools, Instructions)
- [ ] CLAUDE.md Agents table updated
- [ ] team mode → shutdown protocol included
