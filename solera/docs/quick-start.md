# Quick Start

This guide walks you through your first Solera project from an empty directory to a merged Epic. It uses a concrete example — a task management app called `task-app` — and shows exactly what you say to Claude at each step.

## Prerequisites

- Claude Code with the Solera plugin installed
- A git repository initialized at your project root

Install the plugin if you haven't yet:

```bash
claude plugin install /path/to/solera
```

---

## Step 1: Set up the workspace

You start a fresh project. Solera needs a workspace folder structure and an initiative roadmap before it can plan any work.

Say to Claude:

> Set up the Solera workspace for this project. The initiative is `task-app 2026`. We're building a task management app. Create the folder structure and write the initiative roadmap.

Solera creates:

```
task-app/
├── progress.md
└── workspace/
    ├── identity/
    └── initiative/
        └── 2026/
            └── roadmap.md
```

The `roadmap.md` captures your annual initiative goals — which quarters they belong to, and a one-line objective for each. Solera will reference this file every time it writes a Phase. If you already have a product vision, describe it when you ask; Solera will draft the roadmap from what you provide.

**Verify you're on track:**

```
task-app/workspace/initiative/2026/roadmap.md   ← exists
task-app/progress.md                             ← exists
```

---

## Step 2: Write a Phase

A Phase is a quarterly plan. It lists which Goals you'll pursue that quarter and tracks their completion.

Say to Claude:

> Write the Phase for Q1 2026. The phase ID is `2026-P1-foundation`. Our goal this quarter is to ship the core task management feature.

Solera reads `workspace/initiative/2026/roadmap.md`, extracts the Q1 goals, and creates:

```
task-app/workspace/phase/2026-P1-foundation/
├── README.md
└── goals/
```

`README.md` contains the phase overview table, a Goals table (with status icons), completion criteria, and a Workflow section that Solera will follow when you start work.

Example `README.md` header:

```markdown
# Phase: 2026-P1-foundation

> Initiative: 2026
> Status: 🔄 In Progress

## Overview

| Item       | Details                              |
|------------|--------------------------------------|
| **Period** | 2026-01 ~ 2026-03                    |
| **Objective** | Ship core task management feature |

## Goals

| Goal              | Type    | Status     | Progress | Folder |
|-------------------|---------|------------|----------|--------|
| G1: task-management | Feature | ⏳ Pending | 0/2      | [→](./goals/G1-task-management/) |
```

**Verify you're on track:**

```
task-app/workspace/phase/2026-P1-foundation/README.md   ← exists
task-app/workspace/phase/2026-P1-foundation/goals/      ← exists (empty)
```

---

## Step 3: Write a Goal and its first Epic

A Goal is a service-level objective — something a user or the system gains. For a Feature Goal, Solera creates a Service Map, Personas, and a Journey before decomposing into Epics.

Say to Claude:

> Write Goal G1 for Phase 2026-P1-foundation. The goal is `task-management`. Users need to create, organize, and complete tasks.

Solera works through the Goal procedure:

1. Creates the folder structure
2. Writes a Service Map (`artifacts/service-map/index.md`) describing how the task feature fits the product
3. Writes a Persona profile (`artifacts/persona/maya.md`) — for example, "Maya, a freelance designer managing client work"
4. Derives a Journey for Maya: `Browse tasks → Create task → Assign due date → Mark complete`
5. Maps Journey steps to Epics and writes `_goal.md`

Then Solera moves into the first Epic. Say:

> Start the first Epic: `01-task-crud`. This covers the core create/read/update/delete operations for tasks.

Solera creates the Epic branch and scaffolds the Epic:

```bash
git checkout -b epic-task-crud
```

It writes Use Cases (`artifacts/use-case/UC-001-create-task.md`), domain concepts (`artifacts/concept/domain.md`, `artifacts/concept/entities/task.md`), and then produces `_epic.md`.

**Workspace after this step:**

```
task-app/workspace/phase/2026-P1-foundation/goals/G1-task-management/
├── _goal.md
├── artifacts/
│   ├── service-map/
│   │   └── index.md
│   ├── persona/
│   │   └── maya.md
│   └── use-case/
│       └── UC-001-create-task.md
└── epics/
    └── 01-task-crud/
        └── _epic.md
```

`_goal.md` example:

```markdown
# Goal: task-management

> Phase: 2026-P1-foundation
> Status: 🔄 In Progress

## Journey (rough)

| Journey     | Persona | Steps                                          |
|-------------|---------|------------------------------------------------|
| task-flow   | Maya    | Browse → Create → Assign due date → Complete   |

## Epics

| Epic         | Journey   | Status     |
|--------------|-----------|------------|
| 01-task-crud | task-flow | 🔄 In Progress |

## Completion Criteria

- [ ] All Epics complete
```

`_epic.md` example:

```markdown
# Epic: 01-task-crud

> Goal: task-management
> Status: 🔄 In Progress

## User Value

**As a** freelance designer,
**I want** to create and manage tasks with due dates,
**So that** I never miss a client deadline.

## Stories

| ID     | Story               | Status     |
|--------|---------------------|------------|
| US-001 | create-task-form    | ⏳ Pending |
| US-002 | task-list-view      | ⏳ Pending |
| US-003 | mark-task-complete  | ⏳ Pending |
```

**Verify you're on track:**

```
_goal.md                               ← exists, status 🔄
epics/01-task-crud/_epic.md            ← exists, status 🔄
git branch                             → epic-task-crud (current)
```

---

## Step 4: Run the workflow — Stories and Action Items

Now you execute the Epic Story by Story. Each Story gets its own branch, and every unit of work inside it is a single commit.

### Write and execute a Story

Say to Claude:

> Start Story US-001: create-task-form.

Solera creates the Story branch:

```bash
git checkout -b epic-task-crud/story-US-001-create-task-form
```

It writes `_story.md` with the user story, acceptance criteria, and a table of Action Items:

```markdown
# US-001: create-task-form

> Epic: 01-task-crud
> Status: 🔄 In Progress

## User Story

**As a** Maya,
**I want** a form to create a new task with a title and due date,
**So that** I can capture work before I forget it.

## Acceptance Criteria

- [ ] Form renders with title input and due-date picker
- [ ] Submitting a valid form saves the task and clears the form
- [ ] Submitting with an empty title shows a validation error

## Action Items

| ID      | Action Item              | Agent | Phase | depends_on | Status     | Commit |
|---------|--------------------------|-------|-------|------------|------------|--------|
| ACT-001 | Add Task model           | -     | 1     | -          | ⏳ Pending | -      |
| ACT-002 | Add task creation API    | -     | 2     | ACT-001    | ⏳ Pending | -      |
| ACT-003 | Build TaskForm component | -     | 2     | ACT-001    | ⏳ Pending | -      |
| ACT-004 | Wire form to API         | -     | 3     | ACT-002, ACT-003 | ⏳ Pending | - |

**Progress**: 0/4 Action Items complete
```

### Execute Action Items

Each Action Item is one commit. Solera executes them in phase order (Phase 1 first, then Phase 2 actions in parallel if possible, then Phase 3).

Say to Claude:

> Execute ACT-001: Add Task model.

Solera writes the code, runs tests, and commits:

```
[task-crud][US-001][ACT-001] Add Task model

- Add Task entity with id, title, dueDate, completed fields
- Add task repository interface
```

After all four Action Items are committed, you have four commits on the Story branch. Say:

> Complete Story US-001.

Solera:
1. Confirms all acceptance criteria pass
2. Writes `RETRO.md` for the Story
3. Sets `_story.md` status to ✅
4. Squash-merges the Story branch into `epic-task-crud`

```bash
git checkout epic-task-crud
git merge --squash epic-task-crud/story-US-001-create-task-form
git commit -m "[task-crud][US-001] create-task-form"
```

Repeat this for US-002 and US-003. After each Story, Solera squash-merges to the Epic branch. `progress.md` is updated after every state change.

**Workspace after all Stories complete:**

```
epics/01-task-crud/
├── _epic.md                  (status ✅)
├── RETRO.md
├── US-001-create-task/
│   ├── _story.md             (status ✅)
│   ├── RETRO.md
│   ├── ACT-001-add-task-model.md
│   ├── ACT-002-add-task-api.md
│   ├── ACT-003-build-task-form.md
│   └── ACT-004-wire-form-to-api.md
├── US-002-edit-task/
│   └── ...
└── US-003-delete-task/
    └── ...
```

---

## Step 5: Complete the Epic — PR, merge, catalog transition

### Create the PR with solera-create-pr

Say to Claude:

> The Epic is done. Create a PR for epic-task-crud.

Solera runs `solera-create-pr`:

1. Confirms all Stories are ✅
2. Confirms build and tests pass on `epic-task-crud`
3. Creates the PR:

```bash
gh pr create \
  --base main \
  --head epic-task-crud \
  --title "[Epic] task-crud: core create/read/update/delete for tasks"
```

The PR body follows the `pr-template.md` format — Stories list, key changes summary, test results.

### Review and merge

After you (or a teammate) reviews and approves the PR, say:

> Merge the PR.

Solera executes the squash merge:

```bash
gh pr merge --squash epic-task-crud
```

The `epic-task-crud` branch is deleted after merge.

### Catalog transition happens incrementally

Artifacts are promoted to `workspace/catalog/published/` at two points — not in bulk at Goal completion:

1. **After Goal Create** — Goal-level artifacts (service-map, persona, journey) are promoted immediately, so the first Epic can reference them from `published/`
2. **At each Epic Wrap-up** — Epic-level artifacts (use-case, concept) are promoted before the PR is created

```
Goal Create promotes:                    Epic Wrap-up promotes:
service-map/index.md          →         use-case/UC-001-*.md          →
persona/maya.md                →         concept/domain.md             →
  to workspace/catalog/published/          to workspace/catalog/published/
```

Each moved file receives a version header:

```markdown
> Applied version: P1-G01
> Last updated: 2026-03-02
```

The `artifacts/` folder is now empty. A `RETRO.md` is written for the Goal. `_goal.md` status becomes ✅. `progress.md` reflects the completed Goal.

**Final workspace snapshot:**

```
task-app/
├── progress.md                              (Goal G1 complete)
├── HANDOFF.md                               (auto-updated on session end)
└── workspace/
    ├── initiative/2026/roadmap.md
    ├── phase/2026-P1-foundation/
    │   ├── README.md
    │   └── goals/G1-task-management/
    │       ├── _goal.md                     (status ✅)
    │       ├── RETRO.md
    │       ├── artifacts/                   (empty — transitioned)
    │       └── epics/01-task-crud/
    │           ├── _epic.md                 (status ✅)
    │           ├── RETRO.md
    │           └── US-001-create-task/...
    └── catalog/
        └── published/
            ├── service-map/index.md
            ├── persona/maya.md
            └── use-case/UC-001-create-task.md
```

---

## What's next

- **architecture.md** — How skills chain together, the role of each SKILL.md, and how solera-manage-workflow supervises execution without duplicating procedure definitions.
- **team-workflow.md** — Running Solera with multiple developers: branch ownership, parallel Story execution with agent assignments, and how `depends_on` prevents output conflicts.
