---
name: solera-init
user-invocable: true
description: Set up Solera v3 in a project — install rules, create the three-axis workspace, and run the team kickoff interview.
metadata:
  version: "3.2.0"
  category: meta
  type: unit
  style: procedural
  triggers: [set up solera, initialize solera, install solera, solera init]
  uses: []
---

# Solera Init (v3)

> Sets up Solera v3 in the current project:
> - installs the workflow rule,
> - creates the three-axis workspace (Living / Time-bound / Immutable),
> - and runs the team kickoff interview to populate `team-process.md`.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root (where `workspace/` will live) | . |

## Output

| Step | Output | Path |
|------|--------|------|
| Rules | Workflow rule | `.claude/rules/solera-workflow.md` |
| Folders | Workspace skeleton | `{project_path}/workspace/` |
| State | Progress file | `{project_path}/progress.md` |
| Interview | Team process definition | `{project_path}/workspace/team-process.md` |

## Procedure

### Step 1. Check existing setup

- [ ] Check if `.claude/rules/solera-workflow.md` already exists.
  - If exists: ask user whether to overwrite or skip.
- [ ] Check if `{project_path}/workspace/` already exists.
  - If exists: this is either a v2 project needing migration, or a partial v3 setup.
  - **v2 detection** — any of: `workspace/initiative/`, `workspace/phase/`, a `_goal.md` or `_epic.md` anywhere under `workspace/`.
  - If v2 detected: stop and advise `solera-migrate-v2`. Do NOT attempt to overlay v3 on top of v2 data.
  - If v3 partial (has `concepts/` or `milestones/`): skip folder creation, continue to rule installation.

### Step 2. Install rules

- [ ] Create `.claude/rules/` directory if not present.
- [ ] Write `.claude/rules/solera-workflow.md` — ref: [assets/solera-workflow.md](assets/solera-workflow.md). Copy content as-is (no substitution).

### Step 3. Create workspace structure

- [ ] Create the v3 folder layout:
  ```
  {project_path}/
  ├── progress.md
  └── workspace/
      ├── identity/
      ├── concepts/
      ├── milestones/
      ├── stories/
      ├── releases/
      └── catalog/
          └── published/
  ```
- [ ] Seed `concepts/_index.md` from [../solera-write-concept/assets/_index-template.md](../solera-write-concept/assets/_index-template.md).
- [ ] Seed `milestones/_index.md` from [../solera-write-milestone/assets/_index-template.md](../solera-write-milestone/assets/_index-template.md).
- [ ] Seed `releases/_index.md` from [../solera-release/assets/_index-template.md](../solera-release/assets/_index-template.md).
- [ ] Write initial `progress.md`:
  ```markdown
  # Progress

  > Last updated: {today}

  ## Living Axis
  **Active Concepts** (0): (none yet — run `solera-write-concept`)

  ## Time-bound Axis
  | Level | Current | Status |
  |-------|---------|--------|
  | Milestone | (none) | — |
  | Story | (none) | — |
  | Action Item | (none) | — |

  ## Immutable Axis
  **Latest Release**: (none yet)
  ```

### Step 4. Verify

- [ ] `.claude/rules/solera-workflow.md` exists and is non-empty.
- [ ] `{project_path}/workspace/` with all v3 subdirectories exists.
- [ ] `progress.md` exists.
- [ ] Three `_index.md` files exist (concepts, milestones, releases).

### Step 5. Team Kickoff Interview

Conduct a conversational interview to understand the team's work process.
**Ask all questions in the user's language.**
Every question maps to a specific field in `team-process.md`.
Save results to `{project_path}/workspace/team-process.md`.

If `project.type` is `software`, also merge fields from [assets/team-process-software.md](assets/team-process-software.md) into the output.

---

#### Step A — Detect project type → `project.type`

Ask what kind of project this is:
- `software` — product/app development
- `marketing` — campaigns, growth, promotion
- `design` — UX/UI, brand, visual design
- `content` — writing, media, editorial
- `other` — anything else

The answer determines which follow-up questions apply (Step F).

---

#### Step B — Project basics → `project.description`, `project.target_users`

- "What are you building or creating? One sentence." → `project.description`
- "Who are the primary users or audience?" → `project.target_users`
  → If vague: ask about role, context, or situation of use.

---

#### Step C — Work process → `process_stages[]`, `workflow_gates`

**C-1. Stage list** → `process_stages[].name`

Ask: "What stages does your team go through to deliver a feature or deliverable?"

If the answer is vague, offer an example list by project type:

Software example:
```
Planning → UX Design → UI Design → Entity Design → API Design
→ Backend Dev → Frontend Dev → Testing → Code Review → QA → Deploy
```

Marketing example:
```
Brief → Research → Concept → Content Creation → Review → Approval → Launch → Reporting
```

Design example:
```
Brief → Research → Concept → Wireframe → Visual Design → Review → Handoff
```

Confirm the final list. If a stage was mentioned earlier but dropped from the final list, ask whether it is truly out of scope.

**C-2. Stage details** → remaining `process_stages[]` fields

For each confirmed stage:
- "What is the done-criterion for {stage}?" → `done_when`
- "Is {stage} a gate — must it finish before the next stage begins?" → `gate: true/false`
- "Who owns {stage}?" → `owner` (optional)
- "What tool is used for {stage}?" → `tool` (optional)

If multiple gate-true stages could block the same Solera step, ask whether a stage blocks all work or only a specific part.

**C-3. Parallel stages** → `parallel: true`

If two stages can run simultaneously, mark them `parallel: true`.

**C-4. Gate derivation** → `workflow_gates`

Map `gate: true` stages to v3 Solera gate keys:

| Stage blocks... | Gate key |
|---|---|
| Milestone agreement (needs review/analysis before agreeing) | `milestone.agree` |
| Story creation (requires Concept alignment) | `concept.align` |
| Story development start | `story.execute` |
| Story completion (review/test) | `story.wrap_up` |
| Action Item execution start | `act.start` |
| Action Item completion (post-commit) | `act.done` |

After deriving, confirm with the user:
> "기반해서 다음 gate들을 설정할게요 — 맞나요?"

**C-5. Structured gate checks** → `workflow_gates.*.checks[]`

For each gate where `condition` is non-empty, ask:
- "이 gate를 자동으로 검증할 수 있나요? (파일 존재, 명령 실행, 특정 ACT 완료 등)"
  → If yes, map to `checks[]`:
    - File/path existence → `type: glob_exists`, `params: { pattern: "..." }`
    - ACT completion → `type: act_complete`, `params: { ids: [...] }`
    - Command/test pass → `type: command_passes`, `params: { run: "..." }`
    - Pattern must not appear → `type: grep_absent`, `params: { pattern: "...", glob: "..." }`
    - Concept existence check → `type: concept_exists`, `params: { ids: [...] }` (omit `ids` to read `contributes_to` from the calling Story)
    - Milestone status check → `type: milestone_status`, `params: { id: "...", equals: "agreed" }`
  → If no, leave `checks` absent (text-based fallback).

---

#### Step D — Collaboration conventions → `conventions.*`

- "How many approvals are required to merge/complete work?" → `review_approvals`
- "Any naming conventions for commits or tasks (e.g., ticket numbers)?" → `naming_prefix`
- "What is your iteration cycle?" → `iteration_cycle`

---

#### Step E — Tools → `tools.*`

- "What tools does your team use for project management, communication, and design?"
  → collect as key-value pairs: `project_tool`, `design_tool`, `communication`, etc.

---

#### Step F — Project-type specific fields

**Software only** → merges fields from [assets/team-process-software.md](assets/team-process-software.md):

- "What is your backend stack?" → `tech_stack.backend.*` (framework → ORM → auth → database)
- "What is your frontend stack?" → `tech_stack.frontend.*` (framework → state → styling)
- "What cloud/infra do you use?" → `tech_stack.infra.*` (cloud → container → CI/CD → environments)
- "Does your project follow a layered architecture (e.g., Clean Architecture, Hexagonal)?"
  → If yes: "In what order should layers be built?" → `execution_order.groups` (list of keyword lists per layer)
- "Any layer-boundary rules? (e.g., Domain must not import Presentation)"
  → If yes: map to `architecture_rules.rules[]` with `scope`, `forbidden_imports`, `message`.

---

#### Step G — Custom rules → `custom_rules[]`

- "Any other team-specific rules or constraints not covered above?"

---

### Step 6. Project-Tailored Tooling (BLOCKING, direct-write)

> Propose project-specific agent/skill candidates to the human, and — on per-candidate approval — **write the files directly** using the pre-baked specs in the catalog.
> Catalog SSOT: [../../docs/reference/tooling-catalog.md](../../docs/reference/tooling-catalog.md). Read it first for the full specs and integrity rules.
>
> **Important**: Step 6 does not invoke `solera-edit-agent` / `solera-edit-skill`. Those skills exist for manual, interview-driven creation. Step 6 is automated and copies catalog-specified content with variable substitution, nothing more.

- [ ] Read `project.type` from the freshly written `team-process.md`. Compute `{project_name}` and `{project_slug}` per the catalog's **Variable substitution rules** table (including the noise-word guard on `{project_name}` and the 3–50 char validity check on `{project_slug}` — halt and prompt the user if either check fails).
- [ ] **Idempotency check — re-run mode**: if `team-process.md` already contains a `tooling:` block with any non-empty list, ask AskUserQuestion:
  - `(1) skip Step 6 entirely` — default. Leave the existing `tooling:` block untouched and skip to Completion Checklist.
  - `(2) only offer candidates not already listed` — compute the skip-set = union of names in `tooling.created[].name ∪ tooling.declined[].name ∪ tooling.deferred[].name`. Continue Step 6 but drop any candidate whose name (after `{project_slug}` substitution) is in the skip-set. When merging, append to the existing lists — never remove or rewrite existing entries.
  - `(3) restart from scratch` — replace the existing `tooling:` block entirely. Warn that existing `created` entries are listed records of past creations and the files on disk are untouched by this choice.
- [ ] **If `project.type` has no candidates in the catalog** (currently anything except `software`):
  - Report: `"Tooling catalog does not yet list candidates for project.type={type}. Skipping Step 6 — invoke solera-edit-agent / solera-edit-skill manually when you identify concrete roles."`
  - Append an empty `tooling:` block to `team-process.md` (all three lists empty).
  - Skip to Completion Checklist.
- [ ] **Gather evidence** per the catalog's "Evidence patterns" table:
  - Use `Glob` for each pattern.
  - Use `Bash(command="git rev-list --count HEAD")` only when a candidate's Propose-when rule requires the commit count.
  - Record the matched patterns per-candidate — they feed the `evidence` field in the recorded decision.
- [ ] **Resolve the candidate set**: include every candidate whose "Propose when" condition holds against the gathered evidence. Drop the rest.
- [ ] **Filter by specification status**: for each included candidate, grep the catalog for a header line matching the exact pattern `^### \d+\. .+ (agent|skill)  \((FULLY SPECIFIED|placeholder — coming soon)\)$` that names the candidate:
  - `(FULLY SPECIFIED)` → eligible for creation.
  - `(placeholder — coming soon)` → keep for user review but non-creatable. The AskUserQuestion for it must omit the `create now` option; only `decline` and `defer` are offered; the default recommendation is `defer` with reason `"catalog entry not yet fully specified"`.
  - Header missing or ambiguous → halt Step 6 with the error `"Catalog section for {candidate_name} has no valid status header. Fix docs/reference/tooling-catalog.md before re-running."`
- [ ] **If the resolved set is empty**: report `"No tooling candidates matched evidence for project.type=software. Skipping Step 6."`, write an empty `tooling:` block, skip to Completion Checklist.
- [ ] **Per-candidate prompt loop** — for each candidate, sequentially:
  - Read the candidate's **Kind** (`agent` | `skill`) and **Role** from its catalog section.
  - Compute `candidate_evidence`: the subset of the gathered evidence globs that the candidate's Propose-when rule actually referenced. Record this subset for later (it goes into the `evidence` field on `created` entries).
  - **Primary AskUserQuestion**:
    - `header`: `"{candidate_name}"` (≤12 chars — truncate with `…` if longer)
    - `question`: `"Create {Kind} `{candidate_name}` — {Role}? Evidence: {candidate_evidence joined by ', '}."`
    - `options`:
      - `create now` (omit if placeholder)
      - `decline — not needed`
      - `defer — revisit later`
  - **Follow-up AskUserQuestion for reason** (only when answer is `decline` or `defer`):
    - `header`: `"Reason"`
    - `question`: `"Briefly, why {decline|defer}?"`
    - `options`: three common reasons from the catalog entry if provided, plus the inherent `Other` for free text. If the catalog entry lists no stock reasons, rely on `Other`.
  - Record the result in an in-memory `decisions` list before moving to the next candidate.
  - **If the user interrupts** (no answer received, e.g. `Esc`): record this candidate as `deferred` with reason `"interrupted during Step 6"` and continue to the next candidate. Never silently skip.
- [ ] **For each `create now` decision** (iterate `decisions` in order):
  1. Load the candidate's catalog entry. If the catalog requires `{test_command}` and it cannot be resolved from evidence, **demote this decision to `declined`** with reason `"test command could not be resolved from evidence"` and continue to the next candidate. (Do **not** halt the whole Step 6.)
  2. Substitute every `{variable}` in the catalog's Frontmatter + System prompt body per the catalog's "Variable substitution rules" table.
  3. Compute the final file path:
     - agent → `.claude/agents/{final_name}.md` where `{final_name}` is the catalog's Final name after `{project_slug}` substitution (e.g. `test-runner`, `billing-api-convention-guard`).
     - skill → `.claude/skills/{final_name}/SKILL.md` plus any declared assets.
  4. **Ensure the parent directory exists**: run `mkdir -p .claude/agents/` (for agents) or `mkdir -p .claude/skills/{final_name}/` (for skills) before writing. `.claude/` itself is guaranteed by Step 2 (`.claude/rules/` exists), but the `agents/` / `skills/` subdirectory is not.
  5. **If the target path already exists**: AskUserQuestion — `(1) skip this candidate` / `(2) overwrite` / `(3) write as {final_name}-new.md for human review`. Apply the choice and record the decision as:
     - `skip` → move this decision from `create now` to `declined` with `reason: "file already exists; user chose to keep existing"`. Do not write anything.
     - `overwrite` → write the file; record in `created` with `note: "overwrote existing file"`.
     - `write as {final_name}-new.md` → write to the `-new` path; record in `created` with `note: "written as {final_name}-new.md for human review (existing file untouched)"` and the actual path used.
  6. Write the file directly (frontmatter + body). Do **not** invoke any other Solera skill. **If the write raises any error** (permission denied, disk full, invalid path): catch it; demote this decision to `declined` with reason `"file write failed: {short error message}"`; record the path attempted; continue to the next candidate. Never halt the whole Step 6 on one candidate's write error.
  7. **For agent candidates**: append the catalog-specified CLAUDE.md row to `CLAUDE.md`.
     - If `{project_path}/CLAUDE.md` does not exist: create it with a minimal header `# CLAUDE.md\n\n## Agents\n\n| Agent | Purpose | Tools |\n|---|---|---|\n` plus the row.
     - If CLAUDE.md exists but has no `## Agents` section: append the section + header row + new row at the end of the file.
     - If `## Agents` exists and is a markdown table: check whether a row with the same agent name already exists. If it does → replace that row. If not → append the new row as the last row.
     - If `## Agents` exists but is **not** a markdown table (e.g. bullets or prose): do not rewrite the existing content. Append the table-formatted row as a new block immediately after the non-table content, preceded by a blank line and the standard header row (`| Agent | Purpose | Tools |` + separator). Record a `note: "CLAUDE.md ## Agents section was non-table; appended a new table block below existing content"` on the decision entry.
  8. Verify the file exists by reading it back; if the read fails, demote this decision to `declined` with reason `"file write failed — see skill output"` and continue to the next candidate. Do not halt Step 6.
- [ ] **Write the `tooling:` block to `team-process.md`** per the catalog's recording template. Every candidate appears in exactly one of `created` / `declined` / `deferred`. `created` entries include `source: docs/reference/tooling-catalog.md`.
- [ ] **Final report**: `"Step 6 complete. Created: N. Declined: M. Deferred: K. Files written: {list of paths}. Catalog: docs/reference/tooling-catalog.md."`

---

#### team-process.md template

Fill all collected values. Leave commented examples for empty optional fields.

```yaml
# team-process.md
# Generated by solera-init on {date}. Edit freely to update team conventions.
# Skills read this file at the start of Story and Action Item work.

project:
  name: "{project name}"
  type: ""              # software / marketing / design / content / other
  description: ""       # one-sentence description
  target_users:
    - ""                # brief: role + context

workflow_gates:
  # Solera skills check these before entering each step.
  # Each gate has `condition` (human-readable) and optional `checks[]` (machine-verifiable).
  # If `checks` is present: ALL checks must pass. If absent: AI evaluates `condition` as text.
  #
  # v3 Check types:
  #   - type: glob_exists       — params: { pattern: "path/glob" }
  #   - type: act_complete      — params: { ids: [ACT-001, ACT-002] }
  #   - type: command_passes    — params: { run: "flutter analyze" }
  #   - type: grep_absent       — params: { pattern: "TODO|FIXME", glob: "lib/**/*.dart" }
  #   - type: concept_exists    — params: { ids: [authentication] } (omit ids to use contributes_to)
  #   - type: milestone_status  — params: { id: "mvp", equals: "agreed" }
  #
  milestone.agree:
    condition: ""
  concept.align:
    condition: "Story's contributes_to references only active Concepts"
    checks:
      - type: concept_exists
        params: {}          # empty → read contributes_to from calling Story
  story.execute:
    condition: ""
  story.wrap_up:
    condition: ""
  act.start:
    condition: ""
  act.done:
    condition: ""

process_stages:
  # Team's actual stages in order. Generated from kickoff interview.
  # - name: ""
  #   done_when: ""     # what must be true before moving on
  #   gate: true        # must this finish before the next stage begins?
  #   owner: ""         # who owns this stage (optional)
  #   tool: ""          # tool used (optional)
  #   parallel: false   # can this run simultaneously with the next stage?
  stages: []

execution_order:
  # Layer/stage ordering for Action Item phase assignment.
  # Each group runs after the previous group completes.
  # Items within the same group can run in parallel.
  # groups:
  #   - [entity, usecase, domain-test]      # Phase 1: domain layer first
  #   - [datasource, repository-impl, dto]  # Phase 2: data layer
  #   - [flow, page, ui-state]              # Phase 3: presentation layer
  groups: []

architecture_rules:
  # Layer-boundary rules enforced during Action Item test verification.
  # Each rule defines a forbidden import pattern within a file scope.
  #
  # Example (Clean Architecture):
  #   - scope: "lib/domain/**/*.dart"
  #     forbidden_imports: ["package:.*/data/", "package:.*/presentation/"]
  #     message: "Domain must not import Data or Presentation"
  rules: []

conventions:
  review_approvals: 1   # number of approvals required
  naming_prefix: ""     # e.g. "[JIRA-{id}]"
  iteration_cycle: ""   # e.g. "2-week sprint" / "continuous"

tools:
  # project_tool: "Jira"
  # design_tool: "Figma"
  # communication: "Slack"

custom_rules:
  # - "..."

tooling:
  # Step 6 output — project-tailored agent/skill decisions.
  # See docs/reference/tooling-catalog.md for the candidate catalog.
  # Every Step 6 proposal ends in exactly one of these lists:
  created:
    # - name: test-runner
    #   kind: agent                # agent | skill
    #   created_at: "2026-04-18"
    #   evidence: [pyproject.toml, tests/]
  declined:
    # - name: pr-reviewer
    #   reason: "solo project, no PR workflow"
  deferred:
    # - name: convention-guard
    #   reason: "architecture_rules is empty today; revisit after writing them"
```

## Completion Checklist

- [ ] Rule file installed at `.claude/rules/solera-workflow.md`
- [ ] v3 workspace folder structure created (`identity/`, `concepts/`, `milestones/`, `stories/`, `releases/`, `catalog/published/`)
- [ ] Three `_index.md` seed files present
- [ ] `progress.md` initialized with v3 three-axis format
- [ ] Kickoff interview completed (Steps A–G)
- [ ] `team-process.md` written with v3 gate keys (no `epic.*` gates)
- [ ] Step 6 (Project-Tailored Tooling) completed: either skipped with a report, or ran to yield `tooling.created/.declined/.deferred` in `team-process.md`
- [ ] User informed of next step: "Run `solera-write-identity` to establish project identity, then `solera-write-concept` to draw your first Concept."
