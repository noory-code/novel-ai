---
name: solera-write-story
user-invocable: true
description: Write a Story that contributes to one or more Concepts, decompose it into atomic Action Items, and execute each as a single commit.
metadata:
  version: "10.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write a Story, plan a Story, start a Story, break Story into Action Items, define acceptance criteria]
  uses: [solera-execute-action-item]
---

# Writing Story

> A Story is the unit of executable work.
> Every Story **contributes to at least one Concept** and may belong to a Milestone.
> Each Action Item inside a Story is one commit.

## Philosophy

Stories live on the **Time-bound Axis** — they end. But their effect is not lost when they end: a Story's completion updates the Current Shape of the Concepts it contributed to. This is how Solera keeps the Living Axis alive without losing the record of what actually happened.

Two artifact lanes inside a Story:
- **Input Artifacts** — materials the Story needs to start (design links, specs, references). The human provides these up front.
- **Output Artifacts** — what the Story produces (PRs, Figma outputs, docs). Filled in during execution; finalized at Wrap-up.

At Wrap-up the AI proposes updates to each contributed Concept's Current Shape; the human approves.

## Prerequisites

- `{project_path}/workspace/concepts/_index.md` exists with at least one active Concept.
- Each Concept in `contributes_to` must exist at `concepts/{id}.md` with `status: active`.
- If `belongs_to` is provided: the Milestone file exists with `status: agreed` or `in-progress`.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **story_id** | Y | Prefix + number; globally unique within `stories/` | US-001, TS-014 |
| **story_name** | Y | Kebab-case short name | google-login |
| **story_type** | N | `US` (User Story) \| `TS` (Technical Story). Default: US. | TS |
| **contributes_to** | Y | List of Concept IDs this Story advances (≥1) | [authentication, onboarding] |
| **belongs_to** | N | Milestone ID this Story is running toward | mvp |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | `_story.md` | `{project_path}/workspace/stories/{story_id}-{story_name}/_story.md` | Final |
| Create | `ACT-NNN-{name}.md` (one per Action Item) | `{story_path}/ACT-NNN-{name}.md` | Final |
| Wrap-up | `RETROSPECTIVE.md` | `{story_path}/RETROSPECTIVE.md` | Final |
| Wrap-up | Concept Current Shape updates | `concepts/{id}.md` (each contributed) | Final |
| Wrap-up | Concept Contributions row | `concepts/{id}.md` | Final |

> `{story_path}` = `{project_path}/workspace/stories/{story_id}-{story_name}`

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `solera-execute-action-item` | Execute each Action Item (1 ACT = 1 commit) | Execute |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/workspace/concepts/_index.md` exists; stop otherwise and advise `solera-write-concept`.
- [ ] **Gate `concept.align` check** (blocking):
  - Built-in validation (always runs): `contributes_to` is present and non-empty; for each `concept_id` in `contributes_to`, Glob `concepts/{concept_id}.md` must exist and have `status: active`. On failure: halt with a clear error listing missing IDs.
  - Additional `checks[]` from team-process.md (if configured): run each entry as described in **Gate check execution** below. Halt on any failure.
- [ ] If `belongs_to` is provided: read `milestones/{belongs_to}.md`; status must be `agreed` or `in-progress`. Halt otherwise.
- [ ] Check for previous Story retrospectives: `Glob stories/*/RETROSPECTIVE.md` — if any exist, read the most recent and apply any "AI Improvements" noted there.
- [ ] Read `{project_path}/workspace/team-process.md` if it exists; extract `workflow_gates` for Steps 4–5 and `execution_order.groups` / `architecture_rules` for Step 3.
- [ ] Create branch `story/{story_id}-{story_name}` from the current base branch (usually `main` or `dev`).
- [ ] Create `{story_path}/` folder.
- [ ] Status → 🔄.

### 2. Define the Story

- [ ] Determine Story type (US / TS).
- [ ] Write the story body:
  - **US** — As a {persona} / I want {action} / So that {outcome}.
  - **TS** — Technical Goal + Spec table.
- [ ] Define verifiable acceptance criteria.
- [ ] Collect **Input Artifacts**: design links, specs, references. Ask the human if any are missing but expected (e.g., "this Story mentions UI, is there a Figma link?").
- [ ] **Output Artifacts** section is initialized with placeholders — filled during Execute.

### 3. Decompose into Action Items

- [ ] **Scan available skills**: `Glob .claude/skills/*/SKILL.md` and `Glob .claude/plugins/*/skills/*/SKILL.md` to collect installed skill names and trigger phrases.
- [ ] Write the Action Items table (ref: [assets/story.md](assets/story.md)):
  - 1 Action Item = 1 commit.
  - Each row: `ID, Action Item, Skill, Agent, Phase, depends_on, Status, Commit`.
- [ ] **Assign Skill per Action Item**: match task content against scanned skill triggers. If no match, set `-` (manual execution).
- [ ] **Assign Agent per Action Item** if agent teams are used; else `-`.
- [ ] **Layer-aware decomposition** (when `execution_order.groups` is non-empty in team-process.md):
  - For each ACT, determine its layer group by matching its Skill name / Agent name / task keywords against group keyword lists.
  - Unresolvable → assign to earliest group (conservative default).
  - Assign Phases respecting group order; ACTs in the same group may share a Phase.
- [ ] Define `depends_on` to prevent output conflicts.
- [ ] **Phase-ordering validation** (same trigger): verify group[i]'s max Phase ≤ group[j]'s min Phase whenever group[i] precedes group[j]; reassign Phases if violated and log each reassignment.
- [ ] **MUST: immediately after writing _story.md, create one file per Action Item.** Parse every table row; create `ACT-NNN-{name}.md` using [../solera-execute-action-item/assets/action-item.md](../solera-execute-action-item/assets/action-item.md). Block entry to Step 4 until Glob `{story_path}/ACT-*.md` count matches table row count.

### 4. Execute

- [ ] **Gate check `story.execute`** (if defined in team-process.md): run each configured check per **Gate check execution** below; halt on any failure.
- [ ] Extract incomplete Action Items (⏳ or no status) from the Action Items table.
- [ ] Execute each ACT in Phase order via Skill tool (blocking, sequential):
  ```python
  Skill(name="solera-execute-action-item", args={
    "project_path": "{project_path}",
    "story_id": "{story_id}",
    "story_name": "{story_name}",
    "action_item_id": "ACT-NNN",
    "action_item_name": "{name}"
  })
  ```
  After each ACT: confirm status ✅ and commit present before proceeding.
- [ ] After each ACT completion, the Action Item's output paths (PR URL, commit hash, new doc paths, etc.) are captured — `solera-execute-action-item` appends them to the Story's `# Output Artifacts` section.
- [ ] Confirm all acceptance criteria met.
- [ ] Confirm all ACT statuses ✅.

### 5. Wrap-up

- [ ] **Gate check `story.wrap_up`** (if defined in team-process.md): same check types as `story.execute`; halt on failure.
- [ ] Confirm tests pass (if code changes were made).
- [ ] Write `RETROSPECTIVE.md` — ref: [assets/retro.md](assets/retro.md). Must include the **"Concept Contribution Summary"** section (see that asset).
- [ ] **Concept Current Shape update loop** — for each `concept_id` in `contributes_to`:
  - Read the current `concepts/{id}.md`.
  - AI drafts a proposed revision of `# Current Shape` reflecting what this Story actually produced, based on Output Artifacts and the acceptance criteria that were met.
  - Show the existing Current Shape and the proposed revision side-by-side to the human.
  - **BLOCKING**: human approves, edits, or rejects. On approval, write the updated Current Shape.
  - Append a row to `# Contributions` in the Concept file:
    ```
    | {story_id}-{story_name} | {1-line summary of what the Story left behind} | {YYYY-MM-DD} |
    ```
- [ ] Set `_story.md` Status → ✅.
- [ ] Squash-merge the `story/{story_id}-{story_name}` branch into the base branch (usually `main`/`dev`). Do not force-push; if the merge fails, report and pause.

## Gate check execution

All `workflow_gates.*.checks[]` entries in `team-process.md` share the same execution model. For each check object, dispatch by `type`:

| `type` | What it does | `params` |
|---|---|---|
| `glob_exists` | Run `Glob {pattern}` — PASS if ≥1 match | `{ pattern: "path/glob" }` |
| `act_complete` | Read `_story.md` Action Items table — PASS if every listed ACT ID has status ✅ | `{ ids: [ACT-001, ACT-002] }` |
| `command_passes` | Run command via Bash — PASS if exit code = 0 | `{ run: "npm test" }` |
| `grep_absent` | Run `Grep {pattern}` restricted to `{glob}` — PASS if 0 matches | `{ pattern: "TODO\|FIXME", glob: "src/**/*.ts" }` |
| `concept_exists` | For each `concept_id` in params (or `contributes_to` if params empty), Glob `concepts/{id}.md`; PASS if all exist with `status: active` | `{ ids: [authentication, onboarding] }` or `{}` (defaults to this Story's `contributes_to`) |
| `milestone_status` | Read `milestones/{id}.md`; PASS if its `status` matches `equals` | `{ id: "mvp", equals: "agreed" }` |

Rules:
- A gate with `checks: []` or no `checks` key falls back to text evaluation of the `condition` field.
- ALL checks must pass for a gate to pass. Any failure → halt with the failing check's `type` and `params` in the error message.
- Unknown `type` values → halt with `"unknown gate check type: {type}"` (do not silently skip).

## Commit Message Format

```
[{primary_concept}][{story_id}][ACT-NNN] title

- change description
```

Where `{primary_concept}` is the first entry in `contributes_to`. This keeps commit history searchable by Concept.

## Human–AI Protocol

This skill operates across **Moment 3 (Work)** and participates in **결과 확정** at Wrap-up. Rules:

| AI does | AI does not |
|---------|-------------|
| Propose Action Item decomposition | Invent acceptance criteria the human didn't ask for |
| Match Action Items to skills and agents | Silently skip Concept Current Shape update at Wrap-up |
| Draft Current Shape revisions for each contributed Concept | Overwrite an existing Current Shape without human approval |
| Capture Output Artifacts automatically during Execute | Drop or reshape human-provided Input Artifacts |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Missing Concept | `contributes_to` names a non-existent Concept | Halt; list missing IDs | Skill halts |
| Inactive Concept | Concept exists but `status: deprecated`/`archived` | Halt; ask the human to revise scope or revive | Skill halts |
| Milestone not agreed | `belongs_to` milestone is `proposed` or `released` | Halt; ask the human to resolve | Skill halts |
| Gate failure | `concept.align` / `story.execute` / `story.wrap_up` | Report failing checks | Blocking |
| ACT count mismatch | Table rows ≠ ACT files | List difference; halt Step 4 | Blocking until fixed |
| Circular dependency | `depends_on` cycle | Display cycle path; halt Step 4 | Blocking until fixed |
| Current Shape reject | Human rejects AI's draft at Wrap-up | Accept human's alternative or loop | Continue after resolution |
| Squash merge failure | git conflict / permission | Report; pause Wrap-up | Resume after manual fix |

## Completion Checklist

- [ ] `_story.md` written with `contributes_to` (≥1) and optional `belongs_to`
- [ ] Acceptance criteria verifiable
- [ ] All `ACT-NNN-{name}.md` files present (Glob-verified count matches table)
- [ ] Input Artifacts captured up front; Output Artifacts captured during Execute
- [ ] 1 Action Item = 1 commit principle observed
- [ ] All gate checks passed
- [ ] `RETROSPECTIVE.md` written with "Concept Contribution Summary" section
- [ ] Each contributed Concept's `# Current Shape` updated (human-approved) and `# Contributions` row appended
- [ ] `_story.md` status ✅
- [ ] `story/{id}` branch squash-merged into base

## Examples

### Example: executing STORY-001-google-login on banas

Invocation:
```python
Skill(name="solera-write-story", args={
  "project_path": "banas",
  "story_id": "US-001",
  "story_name": "google-login",
  "story_type": "US",
  "contributes_to": ["authentication"],
  "belongs_to": "mvp"
})
```

After Setup:
```
stories/US-001-google-login/
└── _story.md  (draft, status: 🔄)

# branch: story/US-001-google-login
```

After Step 3 (decomposition):
```
stories/US-001-google-login/
├── _story.md
├── ACT-001-google-provider-config.md
├── ACT-002-login-screen.md
└── ACT-003-callback-handler.md
```

Commit messages follow:
```
[authentication][US-001][ACT-001] Configure Google provider
[authentication][US-001][ACT-002] Add login screen
[authentication][US-001][ACT-003] Wire callback handler
```

After Wrap-up:
- `concepts/authentication.md` updated — Current Shape now reflects Google login end-to-end; Contributions table gains one row.
- `RETROSPECTIVE.md` written with Concept Contribution Summary.
- `story/US-001-google-login` squash-merged.
