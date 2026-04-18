# System Prompt Design for Solera Agents

> Reference for writing the Markdown **body** of an agent file (what appears under the YAML frontmatter). The body becomes the agent's system prompt at runtime.
>
> This doc distills the official plugin-dev `agent-development/references/system-prompt-design.md` and layers Solera's two extra rules: **AI-First** (no banned phrases) and **explicit `condition → action`** (no prose judgments). If you want the full catalogue of patterns, read the official reference directly.

## Core Structure (all agents)

Write in **second person**, addressing the agent. Every Solera agent system prompt has these six sections in this order:

```markdown
You are {specific role} specializing in {specific domain}.

## Core Responsibilities
1. {primary responsibility — the reason this agent exists}
2. {secondary responsibility}
3. {additional as needed}

## Process
1. {concrete step 1}
2. {concrete step 2}
3. {continue with clear, verifiable steps}

## Quality Standards
- {standard 1 with specifics — how to tell done-well from done-poorly}
- {standard 2}
- {standard 3}

## Output Format
{what the agent returns, as a concrete template}

## Edge Cases
- {case 1} → {specific action}
- {case 2} → {specific action}
```

Order matters: **role → responsibilities → process → quality → output → edges**. If a reader skips to any section the information they need is where they expect it.

## Solera Rules (mandatory)

These apply on top of the official structure.

### Rule 1 — Banned phrases (AI-First)

The following phrases are **forbidden** in agent system prompts:

- `"as appropriate"`
- `"if needed"`
- `"depending on the situation"`
- `"as you see fit"`
- `"handle accordingly"`

Each forces the reader (Claude) to make an unconstrained judgment. Replace with an explicit trigger:

| Banned | Replace with |
|---|---|
| "Handle errors appropriately" | "On `PermissionError` → report `{path}` and stop. On other exceptions → write the exception message and continue." |
| "Review the PR if needed" | "Review the PR when `diff_size > 200 lines` OR `PR title contains 'WIP'`." |
| "Use the right tool as appropriate" | "Use Grep for content search, Glob for path matching, Read only when you already know the path." |

### Rule 2 — `condition → action` format in Process and Edge Cases

Instead of prose:

> When you find a security issue, evaluate its severity and decide whether to block or warn.

Write:

> - `exposed_secret_detected` → block; report file:line; stop agent
> - `deprecated_crypto_api` → warn; continue; include in final report
> - `other finding` → continue; include in final report

This is mechanical to execute and testable by humans at review time.

## Three Solera-common patterns

### Pattern A — Analysis agent

For code review, security scan, documentation audit, etc. The agent reads, never writes.

```markdown
You are a {domain} analyzer specializing in {specific analysis type}.

## Core Responsibilities
1. Read {specific inputs} thoroughly
2. Identify {concrete issue categories}
3. Produce a prioritized report — do not modify files

## Process
1. **Gather**: Glob/Read the files matching `{scope pattern}`
2. **Scan**: For each file, check against these rules:
   - `{rule 1}` → record `{finding type}`
   - `{rule 2}` → record `{finding type}`
3. **Group**: Cluster findings by file then by severity
4. **Prioritize**: critical > major > minor, stable order within each
5. **Report**: Format per Output Format below

## Quality Standards
- Every finding includes `file:line`
- Severity is one of: `critical` | `major` | `minor`
- Recommendations are specific ("replace X with Y"), not vague ("consider improving X")

## Output Format
## Summary
{2-3 sentence overview}

## Critical
- `{file:line}` — {issue} — {recommendation}

## Major
...

## Minor
...

## Edge Cases
- `0 files matched scope` → output "No files in scope. Done." and stop
- `file binary or unreadable` → skip; list in a "Skipped" appendix
```

**Solera-specific variants**: prefer `Read`/`Glob`/`Grep` tools only; avoid `Write`/`Edit`. In frontmatter `tools: [Read, Glob, Grep]`.

### Pattern B — Generation agent

For creating content (code, tests, docs). Writes files; may read first.

```markdown
You are a {domain} generator specializing in {specific output type}.

## Core Responsibilities
1. Understand the user's intent from the input prompt
2. Generate {specific output} following the project's conventions
3. Validate the generated output is syntactically and semantically correct

## Process
1. **Parse input**: Extract {key parameters}
2. **Read conventions**: Read CLAUDE.md and {relevant rule files}
3. **Generate**: Produce {output artifact} following {template}
4. **Validate**:
   - `syntax_check_fails` → revise; re-validate
   - `convention_check_fails` → revise; re-validate
   - `max 3 revision attempts` → halt; report failure mode
5. **Write**: Save to `{output_path}`

## Quality Standards
- Output matches project conventions (indent, naming, imports)
- No TODO/FIXME left behind
- Tests (if generated) cover the golden path and one edge case

## Output Format
- Absolute path of written file
- One-line summary of what was generated

## Edge Cases
- `target path already exists` → do not overwrite; ask user via AskUserQuestion
- `missing prerequisite input` → halt with list of what's missing
```

**Solera-specific variants**: `tools: [Read, Write, Grep, Glob]`. If bash is needed for validation (`pytest`, `tsc`), add `Bash`.

### Pattern C — Orchestrator (team) agent

For agents that delegate to sub-agents. See the Team Protocol section in `assets/team-agent-template.md`.

```markdown
You are a {domain} team lead coordinating {specialist agents}.

## Core Responsibilities
1. Decompose the request into sub-tasks
2. Delegate each sub-task to the appropriate specialist via Agent tool
3. Synthesize the specialists' outputs into a single result

## Process
1. **Plan**: Produce a task breakdown with one specialist per task
2. **Dispatch**: For each task, invoke `Agent(subagent_type="{specialist}", prompt=...)`
3. **Collect**: Wait for all specialist results
4. **Synthesize**: Merge into the Output Format

## Quality Standards
- Each sub-task is independently verifiable
- No sub-task overlaps with another (MECE)
- Specialists receive enough context to act without asking back

## Output Format
{team-level result}

## Edge Cases
- `specialist returns an error` → retry once with clarified prompt; if still fails, report the sub-task as failed
- `sub-tasks become interdependent mid-flight` → halt; report the emerging dependency and re-plan
```

## Length Budget

| Range | Verdict |
|---|---|
| < 20 chars | Missing — reject |
| 20-300 chars | Underspecified — add process steps, quality standards, edge cases |
| 500-3000 chars | **Sweet spot** — complete without bloat |
| 3000-10,000 chars | Acceptable if multi-pattern or covers many edge cases |
| > 10,000 chars | Split into multiple agents (SRP) |

## Common Mistakes

| Anti-pattern | Fix |
|---|---|
| First-person ("I will analyze...") | Second-person ("You analyze...") |
| Missing Edge Cases section | Add at least 2 `condition → action` entries |
| Output Format as prose ("return a nice summary") | Output Format as a concrete template |
| Process steps without explicit decisions | Each step either executes or branches on a named condition |
| Quality Standards that say "high quality" | Specific rules — how to tell done-well from done-poorly |
| Banned phrase leak | Replace with explicit trigger (see Rule 1 table) |

## How this doc relates to the rest

- **Frontmatter design** — see SKILL.md "Agent Definition Fields" section and `references/description-examples.md`
- **Template selection (task vs team)** — see SKILL.md Procedure Step 4
- **Full pattern catalogue (6+ patterns)** — read the official `plugin-dev/skills/agent-development/references/system-prompt-design.md`
