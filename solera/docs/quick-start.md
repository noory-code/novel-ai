# Quick Start (v3)

This guide walks through your first Solera v3 project from empty directory to a released snapshot. It uses a concrete example — a task management app called `task-app` — and shows exactly what you say to Claude at each step.

For the philosophy behind the three-axis model, see [work-item-structure.md](./work-item-structure.md) and [architecture.md](./architecture.md).

## Prerequisites

- Claude Code with the Solera plugin installed
- A git repository initialized at your project root

Install the plugin if you haven't yet:

```bash
claude plugin install /path/to/solera
```

If you have a **v2 project** to upgrade, stop here and read [migrate-v2-to-v3.md](./migrate-v2-to-v3.md). `solera-init` refuses to overlay v3 on v2 data.

---

## Step 1 — Initialize the workspace

Say to Claude:

> Initialize Solera for this project. We're building a task management app called task-app.

Solera creates:

```
task-app/
└── .solera/                               # v4 dotfolder root
    ├── progress.md                        # v3 three-axis format
    ├── identity/
    ├── personas/
    │   └── _index.md
    ├── journeys/
    │   └── _index.md
    ├── narratives/
    │   └── _index.md
    ├── concepts/
    │   └── _index.md
    ├── milestones/
    │   └── _index.md
    ├── stories/
    ├── releases/
    │   └── _index.md
    ├── team-process.md                    # populated via kickoff interview
    └── catalog/
        └── published/
```

It also installs `.claude/rules/solera-workflow.md` and conducts a short kickoff interview to populate `team-process.md` (stages, gates, tech stack, architecture rules). You can edit `team-process.md` directly later; nothing is locked.

**Verify:**

```
task-app/.solera/progress.md            ← exists
task-app/.solera/concepts/              ← exists
task-app/.solera/personas/              ← exists
task-app/.solera/journeys/              ← exists
task-app/.solera/narratives/            ← exists
task-app/.solera/milestones/            ← exists
task-app/.solera/stories/               ← exists
task-app/.solera/releases/              ← exists
task-app/.solera/team-process.md        ← exists
```

---

## Step 2 — Define identity

Say to Claude:

> Write the identity for this project.

Solera asks about mission, target users, and core values, then writes:

```
task-app/.solera/identity/
├── mission.md
├── core-values.md
└── vision_1.md
```

Identity is written once. You can revise a file by hand later; it doesn't have its own update skill.

---

## Step 3 — Draw your first Concept

This is Moment 1. You draw the big-picture area of the project. AI never invents the Intent on your behalf.

Say to Claude:

> Draw a Concept called `task-lifecycle`.

Claude asks for the **Intent** (one or two sentences that rarely change):

> "What does this Concept mean in this project? One or two sentences — a north star that should rarely change."

You answer, for example: "A task exists from capture through completion and is always in exactly one clear state."

Claude then surfaces observations (it scans identity, existing Concepts, any published artifacts — all empty right now) and asks for **Current Design** (the ideal shape you're drawing right now):

You answer: "States: inbox → active → done or archived. A task always has a title and optional due date. No multi-user yet."

Claude writes:

```markdown
---
id: task-lifecycle
name: Task Lifecycle
status: active
created: 2026-04-16
---

# Intent
A task exists from capture through completion and is always in exactly one clear state.

# Current Design
States: inbox → active → done or archived. A task always has a title and optional due date. No multi-user yet.

# Current Shape
(no Stories have contributed yet)

# Horizon
(not set yet)

# Health
(no signals yet)

# Contributions
| Story | What it left behind | Date |
|-------|---------------------|------|

# Related Artifacts

## Workflow
(template embedded)
```

Claude also updates `concepts/_index.md` so `task-lifecycle` appears under `## Active`.

Draw a second Concept the same way, say `quick-capture` — the idea that capturing a task should take no more than one second.

---

## Step 4 — Agree on a Milestone (Moment 2)

This is the critical human–AI agreement moment. You propose scope; Claude pushes back with an analysis; loop until agreed.

Say to Claude:

> Write a Milestone called `mvp` that includes `task-lifecycle` to the "inbox/active/done" depth and `quick-capture` to the "1-second float button" depth. Target date end of Q2 2026.

Claude runs the agreement cycle. **Round 1** — Claude reads the current state of each Concept and emits an analysis:

```
Analysis for mvp:

task-lifecycle:
  maturity: far — Current Shape empty.
  design_gaps: "archived" state not yet in Current Design but implied by Intent.
  artifact_readiness: no persona or journey yet.
  health_flags: (no concerns)

quick-capture:
  maturity: far — Current Shape empty.
  design_gaps: "1-second" is not measurable — needs an acceptance definition.
  artifact_readiness: no persona.
  health_flags: (no concerns)

Cross-concept concerns:
  dependencies: quick-capture assumes task-lifecycle's inbox state works.
  contradictions: (no concerns)

Scope sanity:
  too_ambitious: (no concerns)
  missing: a "task-list-view" Concept might be needed for MVP — users need to see captured tasks.
  stretch: (no concerns)
```

You respond — either revise scope, accept with notes, or agree. Say:

> Good point on task-list-view — draw it as a new Concept first. Then redo the milestone with the three Concepts.

Claude goes back to `solera-write-concept` for `task-list-view`, then resumes the Milestone cycle. **Round 2** runs with three Concepts; you agree.

The file is written:

```markdown
---
id: mvp
name: MVP
status: agreed
target_date: 2026-06-30
created: 2026-04-16
---

# Scope
- task-lifecycle: inbox/active/done states working end-to-end
- quick-capture: float button + one-keystroke save
- task-list-view: scrollable list of all active tasks

# AI Analysis
(Round 2 content)

# Agreement Log
- Round 1 (2026-04-16): human proposed 2 Concepts; AI flagged task-list-view missing; human revised.
- Round 2 (2026-04-16): three-Concept scope; no new concerns; human agreed.

# Exit Criteria
- task-lifecycle: Current Shape reflects all three states working.
- quick-capture: Current Shape reflects 1-second measured capture flow.
- task-list-view: Current Shape reflects scrollable list of active tasks.

# Accepted Risks
(none)

## Workflow
(template embedded)
```

---

## Step 5 — Plan and execute a Story (Moment 3)

Say to Claude:

> Write Story US-001 `capture-flow` contributing to `quick-capture` and `task-lifecycle`, belonging to `mvp`.

Solera creates:

```
stories/US-001-capture-flow/
└── _story.md             (frontmatter: contributes_to, belongs_to; status 🔄)
```

And branches:

```bash
git checkout -b story/US-001-capture-flow
```

Claude asks for acceptance criteria and Input Artifacts (design references, specs, prior code paths), writes the User Story, and decomposes into Action Items. If `team-process.md` has `execution_order.groups` defined, Claude respects layer ordering (Domain → Data → Presentation, for example).

The Action Items table ends up like:

```markdown
## Action Items

| ID      | Action Item              | Skill         | Agent         | Phase | depends_on | Status | Commit |
|---------|--------------------------|---------------|---------------|-------|------------|--------|--------|
| ACT-001 | Add Task entity + tests  | dev-flutter   | domain        | 1     | -          | ⏳     | -      |
| ACT-002 | CaptureUseCase           | dev-flutter   | domain        | 1     | ACT-001    | ⏳     | -      |
| ACT-003 | Local repo + persistence | dev-flutter   | data          | 2     | ACT-002    | ⏳     | -      |
| ACT-004 | Float button + form      | dev-flutter   | presentation  | 3     | ACT-003    | ⏳     | -      |
```

Claude creates one `ACT-NNN-{name}.md` per row. Then Execute each ACT:

> Execute ACT-001.

For each ACT, Claude writes code, runs tests, and commits with the v3 format:

```
[quick-capture][US-001][ACT-001] Add Task entity + tests

- Task entity with id, title, createdAt, state fields
- Unit tests for state transitions
```

Notice the scope tag `[quick-capture]` — Claude picked `contributes_to[0]`. Since this Story contributes to two Concepts, the commit body includes:

```
- contributes also to: task-lifecycle
```

After each ACT completion, Claude appends to `_story.md`'s `# Output Artifacts`:

```markdown
# Output Artifacts

- ACT-001 commit abc1234: `lib/domain/task/task.dart`, `test/domain/task/task_test.dart`
- ACT-002 commit def5678: `lib/domain/task/capture_use_case.dart`
...
```

---

## Step 6 — Story Wrap-up (결과 확정)

After all four ACTs are ✅, say:

> Wrap up the Story.

Claude runs `story.wrap_up` gate checks, writes `RETROSPECTIVE.md` with the **Concept Contribution Summary** required in v3:

```markdown
## Concept Contribution Summary

### Quick Capture
**What this Story left behind**: Float button + form + local persistence. Sub-second save observed in tests.
**Proposed Current Shape update**: "Float button writes to local store in <1s. No sync yet."
**Approved Current Shape**: (human edits and approves)
**Drift note**: (none)

### Task Lifecycle
**What this Story left behind**: Task entity exists with state enum (inbox/active/done/archived). Only inbox → active transition exercised.
**Proposed Current Shape update**: "Task entity with state enum; inbox → active transition working."
**Approved Current Shape**: (human edits and approves)
**Drift note**: (none)
```

For each contributed Concept, Claude proposes a **Current Shape** update and **blocks** until you approve. On approval, the Concept file is updated and a row appears in `# Contributions`:

```markdown
# Contributions
| Story               | What it left behind                              | Date       |
|---------------------|--------------------------------------------------|------------|
| US-001-capture-flow | Float button + form + local persistence          | 2026-04-18 |
```

Then `solera-publish-artifacts` runs as a hook — if the Story produced any design artifacts under `stories/US-001-capture-flow/artifacts/`, they move to `catalog/published/{type}/` and each contributed Concept's `# Related Artifacts` gains a wikilink. (This Story's a pure-code Story, so zero artifacts move — the skill exits cleanly.)

Finally Claude squash-merges the Story branch into trunk:

```bash
git checkout dev
git merge --squash story/US-001-capture-flow
git commit -m "[quick-capture][US-001] capture-flow"
```

---

## Step 7 — Run more Stories, reach the Milestone

Repeat Step 5–6 for additional Stories until every Milestone Exit Criterion is met. Claude's `solera-manage-workflow` can help you see what's next:

> What should I work on?

Claude checks `progress.md`, the Milestone, and active Concepts, and surfaces options — never auto-picks when multiple are valid.

---

## Step 8 — Mark the Milestone released

When all Exit Criteria are met:

> Mark milestone mvp as released.

Claude reads each Exit Criterion, compares to the current Concept state, and either sets `status: released` or halts with a list of still-open criteria.

---

## Step 9 — Cut the Release (Moment 4)

This freezes the current Concept state as an immutable snapshot.

> Cut release v0.1-mvp and create a git tag.

Solera runs `solera-release`:

1. Validates the milestone is `released`.
2. Gathers Stories whose `contributes_to` intersects the milestone's scope (completed by now).
3. Creates `releases/v0.1-mvp/concepts-snapshot/` and copies each in-scope Concept file, prepending a ❄️ marker.
4. Writes `stories-manifest.md`.
5. Drafts `README.md` and **blocks** for your approval. You edit the overview, accept the Follow-up Candidates list, confirm.
6. Writes `.released` marker and (optionally) runs `git tag -a v0.1-mvp`.

Result:

```
.solera/releases/
├── _index.md                             (updated)
└── v0.1-mvp/
    ├── .released
    ├── README.md                         (human-approved)
    ├── concepts-snapshot/
    │   ├── _index.md
    │   ├── task-lifecycle.md             # with ❄️ marker
    │   ├── quick-capture.md
    │   └── task-list-view.md
    └── stories-manifest.md
```

The original `concepts/*.md` files are untouched — the living axis keeps evolving. The snapshot is the only fixed record of "what MVP was."

---

## Step 10 — Continue to the next Milestone

Back to Step 4. Propose the next Milestone's scope. Claude's analysis this time has more context — Concepts have Current Shape content, Contributions history, Related Artifacts. The agreement cycle will be richer.

Releases accumulate under `releases/`. Each is a frozen historical record. Together with git history and the Contributions log on each Concept, they give you a complete timeline of how the project evolved.

---

## What's next

- [architecture.md](./architecture.md) — How skills chain, the Workflow-as-SSOT rule, and why the supervisor has no state machine.
- [team-workflow.md](./team-workflow.md) — Running Solera with 2–5 contributors; branch ownership, parallel Stories, `/solera-handoff`.
- [migrate-v2-to-v3.md](./migrate-v2-to-v3.md) — Upgrading a v2 project with `solera-migrate-v2`.
