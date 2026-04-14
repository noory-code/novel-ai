---
name: solera-init
user-invocable: true
description: Set up Solera v3 in a project — install rules, create the three-axis workspace, and run the team kickoff interview.
metadata:
  version: "3.0.0"
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
```

## Completion Checklist

- [ ] Rule file installed at `.claude/rules/solera-workflow.md`
- [ ] v3 workspace folder structure created (`identity/`, `concepts/`, `milestones/`, `stories/`, `releases/`, `catalog/published/`)
- [ ] Three `_index.md` seed files present
- [ ] `progress.md` initialized with v3 three-axis format
- [ ] Kickoff interview completed (Steps A–G)
- [ ] `team-process.md` written with v3 gate keys (no `epic.*` gates)
- [ ] User informed of next step: "Run `solera-write-identity` to establish project identity, then `solera-write-concept` to draw your first Concept."
