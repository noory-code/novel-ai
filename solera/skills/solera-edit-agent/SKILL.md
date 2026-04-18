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

Every agent file is a Markdown document with **required YAML frontmatter** followed by the system prompt body.

### Required frontmatter

| Field | Required | Values | Purpose |
|---|---|---|---|
| `name` | Y | hyphen-case identifier | File identity; matches filename |
| `description` | Y | Starts with `"Use this agent when ..."`, includes ≥2 `<example>` blocks (Context / user / assistant / commentary) | Drives auto-triggering by Claude |
| `model` | Y | `inherit` (default) \| `sonnet` \| `opus` \| `haiku` | Which model runs the agent |
| `color` | Y | `blue` \| `cyan` \| `green` \| `yellow` \| `magenta` \| `red` | Visual identification in the UI |
| `tools` | Y | Minimal array of allowed tool names (e.g. `[Read, Grep]`) | Least-privilege tool whitelist |

### Body fields

| Field | Required | Description |
|---|---|---|
| Role | Y | One-line agent role (below the frontmatter) |
| Instructions | Y | System prompt (AI-First style — explicit `condition → action`) |
| Domain | N | Paths to reference skills/docs |
| Mode | N | task / team / both (drives which template to use) |
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

**Step 3: Write frontmatter (required)** — every agent file MUST start with YAML frontmatter

- [ ] `name`: hyphen-case, matches filename
- [ ] `description`: starts with `"Use this agent when ..."`, includes ≥2 `<example>` blocks (Context / user / assistant / commentary). Concrete trigger phrases, not "as needed".
- [ ] `model`: `inherit` (default) unless the role needs otherwise
- [ ] `color`: a distinct color so the agent is visually identifiable (blue/cyan/green/yellow/magenta/red)
- [ ] `tools`: minimal whitelist — only what this role actually uses. Never "all tools".

**Step 4: Write agent body** — ref: [assets/task-agent-template.md](assets/task-agent-template.md) | [assets/team-agent-template.md](assets/team-agent-template.md)

- [ ] Role section (one line)
- [ ] Instructions with explicit `condition → action` rules
- [ ] team mode → include Team Protocol section with shutdown handling

**Step 5: Update CLAUDE.md**

- [ ] Add row to `## Agents` table (or create section if absent)

**Step 6: Validate**

- [ ] Frontmatter has all 5 required fields with valid values
- [ ] `tools` list is minimal (only what the role requires)
- [ ] Instructions use explicit conditions, not "handle appropriately"
- [ ] team mode has shutdown protocol

### REVIEW

**Step 7: Analyze existing agent**

- [ ] Frontmatter present with `name`, `description`, `model`, `color`, `tools`
- [ ] `description` includes `<example>` blocks (triggering examples)
- [ ] `tools` is minimal (no unnecessary tool access)
- [ ] Instructions follow AI-First principle (explicit conditions → actions)
- [ ] team mode → shutdown protocol present
- [ ] Prompt quality: specific conditions and actions

**Step 8: Generate review report**

- Summarize findings and recommendations

### IMPROVE

**Step 9: Run review (invoke steps 7-8)**

- Obtain review report

**Step 10: Apply improvements**

- [ ] Apply review findings
- [ ] Re-validate frontmatter and body

## Common Mistakes

| Wrong | Right |
|---|---|
| Skipping frontmatter (just writing Markdown body) | Every agent file starts with YAML frontmatter (`name`, `description`, `model`, `color`, `tools`) |
| `description: "Reviews code"` (one generic line) | `description: "Use this agent when ..."` + 2+ `<example>` blocks |
| `tools: []` or no `tools` field (inherits all) | Explicit minimal whitelist — only what the role needs |
| Allowing all tools | List only tools the role actually needs |
| Invalid `color` value (e.g. `purple`, `orange`) | Use one of: blue, cyan, green, yellow, magenta, red |
| "Handle it appropriately" | Explicit: `if {condition} → {action}` |
| team agent without shutdown | Include shutdown_response handling |
| Agent name in CamelCase | Use hyphen-case |
| Multiple responsibilities per agent | One role per agent (SoC) |

## Completion Checklist

- [ ] `.claude/agents/{agent_name}.md` created
- [ ] Frontmatter present with all 5 required fields (`name`, `description`, `model`, `color`, `tools`)
- [ ] `description` starts with `"Use this agent when ..."` and includes ≥2 `<example>` blocks
- [ ] `tools` is a minimal whitelist
- [ ] Role and Instructions sections present in body
- [ ] CLAUDE.md Agents table updated
- [ ] team mode → shutdown protocol included
