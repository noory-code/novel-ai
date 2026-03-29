---
name: solera-init
user-invocable: true
description: Set up Solera in a project — install rules, create the workspace structure, and run the team kickoff interview.
metadata:
  version: "2.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [set up solera, initialize solera, install solera, solera init]
  uses: []
---

# Solera Init

> Sets up Solera in the current project by installing rules, creating the workspace structure,
> and collecting the team's process through a kickoff interview.

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

- [ ] Check if `.claude/rules/solera-workflow.md` already exists
  - If exists: ask user whether to overwrite or skip
- [ ] Check if `{project_path}/workspace/` already exists
  - If exists: skip folder creation, proceed to rule installation

### Step 2. Install rules

- [ ] Create `.claude/rules/` directory (if not exists)
- [ ] Write `.claude/rules/solera-workflow.md` — ref: [assets/solera-workflow.md](assets/solera-workflow.md)
  - Copy the asset content as-is (no variable substitution needed)

### Step 3. Create workspace structure

- [ ] Create folder structure:
  ```
  {project_path}/
  ├── progress.md
  └── workspace/
      ├── identity/
      ├── initiative/
      └── catalog/
          └── published/
  ```
- [ ] Write initial `progress.md`:
  ```markdown
  # Progress

  > Phase: (none)
  > Goal: (none)
  > Epic: (none)
  > Story: (none)
  > Action Item: (none)
  ```

### Step 4. Verify

- [ ] `.claude/rules/solera-workflow.md` exists and is non-empty
- [ ] `{project_path}/workspace/` directory exists
- [ ] `{project_path}/progress.md` exists

### Step 5. Team Kickoff Interview

Conduct a conversational interview to understand the team's work process.
**Ask all questions in the user's language.**
Every question maps to a specific field in `team-process.md`.
Save results to `{project_path}/workspace/team-process.md`.

If `project.type` is `software`, also merge fields from
`assets/team-process-software.md` into the output file.

---

#### Step A — Detect project type → `project.type`

Ask what kind of project this is:
- `software` — product/app development
- `marketing` — campaigns, growth, promotion
- `design` — UX/UI, brand, visual design
- `content` — writing, media, editorial
- `other` — anything else

The answer determines which follow-up questions are relevant (Step F).

---

#### Step B — Project basics → `project.description`, `project.target_users`

- "What are you building or creating? One sentence."  → `project.description`
- "Who are the primary users or audience?"  → `project.target_users`
  → If vague: ask about role, context, or situation of use

---

#### Step C — Work process → `process_stages[]`, `workflow_gates`

**C-1. Stage list** → `process_stages[].name`

Ask: "What stages does your team go through to deliver a feature or deliverable?"

If the answer is vague, offer a stage list based on project type:

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

Confirm the final list.
If a stage was mentioned early but dropped from the final list:
→ "You mentioned [stage] earlier but didn't include it — is it out of scope for Solera tracking?"

**C-2. Stage details** → remaining `process_stages[]` fields

For each confirmed stage, ask:
- "What is the done-criteria for [stage]?" → `done_when`
- "Is [stage] a gate — must it finish before the next stage begins?" → `gate: true/false`
- "Who owns [stage]?" → `owner` (optional, skip if obvious)
- "What tool is used for [stage]?" → `tool` (optional, skip if not applicable)

If multiple stages have `gate: true` and both block the same Solera step:
→ "Does [stage A] block all work, or only a specific part (e.g. frontend only)?"

**C-3. Parallel stages** → `parallel: true` annotation

If two stages can run simultaneously:
→ "Do [stage A] and [stage B] run in parallel or in sequence?"
→ Mark parallel stages with `parallel: true`

**C-4. Gate derivation** → `workflow_gates`

Map `gate: true` stages to Solera gate keys:

| Stage blocks... | Gate key |
|---|---|
| Epic entry (planning/requirements) | `epic.use_case` |
| Concept step (design/spec artifact) | `epic.concept` |
| Story development start | `story.execute` |
| Story completion (review/test) | `story.wrap_up` |

After deriving gates, confirm with user:
"Based on what you described, I'll set these gates — does this look right?
 - epic.use_case: '{condition}'
 - epic.concept:  '{condition}'
 - story.execute: '{condition}'
 - story.wrap_up: '{condition}'
Please confirm or adjust."

**C-5. Structured gate checks** → `workflow_gates.*.checks[]`

For each gate where `condition` is non-empty, ask:
- "Can this gate be verified automatically? (e.g., a file must exist, a command must pass, specific ACTs must be complete)"
  → If yes: map answer to `checks[]` entries:
    - File/path existence → `type: glob_exists`, `params: { pattern: "..." }`
    - ACT completion → `type: act_complete`, `params: { ids: [...] }`
    - Command/test pass → `type: command_passes`, `params: { run: "..." }`
    - Pattern must not appear → `type: grep_absent`, `params: { pattern: "...", glob: "..." }`
  → If no: leave `checks` absent (text-based fallback)

---

#### Step D — Collaboration conventions → `conventions.*`

- "How many approvals are required to merge/complete work?" → `review_approvals`
  (reuse value from C-2 if already collected from a review stage)
- "Any naming conventions for commits or tasks (e.g. ticket numbers)?" → `naming_prefix`
- "What is your iteration cycle?" → `iteration_cycle`

---

#### Step E — Tools → `tools.*`

- "What tools does your team use for project management, communication, and design?"
  → collect as key-value pairs: `project_tool`, `design_tool`, `communication`, etc.

---

#### Step F — Project-type specific fields

**Software only** → merges `assets/team-process-software.md` fields:

- "What is your backend stack?" → `tech_stack.backend.*`
  → Ask layer by layer: framework → ORM → auth → database
  → If answer covers multiple fields at once, parse and map accordingly
- "What is your frontend stack?" → `tech_stack.frontend.*`
  → framework → state management → styling
- "What cloud/infra do you use?" → `tech_stack.infra.*`
  → cloud → container → CI/CD (reuse from deploy stage if already collected) → environments
- "Does your project follow a layered architecture (e.g., Clean Architecture, Hexagonal)?"
  → If yes: "In what order should layers be built? (e.g., Domain first, then Data, then Presentation)"
  → Map answer to `execution_order.groups` — each group is a list of keywords for that layer
  → Example: `groups: [[entity, usecase, domain-test], [datasource, repository-impl], [flow, page]]`
- "Are there any layer-boundary rules? (e.g., Domain must not import Presentation)"
  → If yes: map each rule to `architecture_rules.rules[]` with `scope`, `forbidden_imports`, `message`
  → If no: leave `rules: []`

---

#### Step G — Custom rules → `custom_rules[]`

- "Any other team-specific rules or constraints not covered above?"

---

#### team-process.md template

Fill all collected values. Leave commented examples for empty optional fields.
Ref: [assets/team-process-software.md](assets/team-process-software.md) for software extension.

```yaml
# team-process.md
# Generated by solera-init on {date}. Edit freely to update team conventions.
# Skills read this file at the start of Goal and Epic level work.

project:
  name: "{project name}"
  type: ""              # software / marketing / design / content / other
  description: ""       # one-sentence description
  target_users:
    - ""                # brief: role + context
    # - ""              # add more; use solera-write-identity for full persona profiles

workflow_gates:
  # Solera skills check these before entering each step.
  # Each gate has `condition` (human-readable) and optional `checks[]` (machine-verifiable).
  # If `checks` present: ALL checks must pass. If absent: AI evaluates `condition` as text.
  #
  # Check types:
  #   - type: glob_exists    — params: { pattern: "path/glob" }
  #   - type: act_complete   — params: { ids: [ACT-001, ACT-002] }
  #   - type: command_passes — params: { run: "flutter analyze" }
  #   - type: grep_absent    — params: { pattern: "TODO|FIXME", glob: "lib/**/*.dart" }
  #
  # Example:
  #   story.execute:
  #     condition: "Domain layer tests pass"
  #     checks:
  #       - type: command_passes
  #         params: { run: "flutter test packages/entities" }
  #       - type: act_complete
  #         params: { ids: [ACT-001, ACT-002] }
  epic.use_case:
    condition: ""
  epic.concept:
    condition: ""
  story.execute:
    condition: ""
  story.wrap_up:
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
  # Layer-boundary rules enforced during Action Item test verification (Step 4).
  # Each rule defines a forbidden import pattern within a file scope.
  #
  # Example (Clean Architecture):
  #   - scope: "lib/domain/**/*.dart"
  #     forbidden_imports: ["package:.*/data/", "package:.*/presentation/"]
  #     message: "Domain layer must not import Data or Presentation"
  #   - scope: "lib/presentation/**/*.dart"
  #     forbidden_imports: ["package:.*/data/"]
  #     message: "Presentation layer must not import Data directly"
  rules: []

conventions:
  review_approvals: 1   # number of approvals required
  naming_prefix: ""     # e.g. "[JIRA-{id}]" — prepended to every commit/task
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
- [ ] Workspace folder structure created
- [ ] `progress.md` initialized
- [ ] Kickoff interview completed (Steps A–G)
- [ ] `{project_path}/workspace/team-process.md` written with all collected values
- [ ] User informed of next step: "Run `solera-write-identity` to define your service identity and personas"
