---
name: solera-manage-workflow
user-invocable: true
description: Supervisor skill — know what to work on next, read each work item's Workflow section, drive it to completion.
metadata:
  version: "6.0.0"
  category: workflow
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [what should I work on, show current progress, update progress, next task, next work, resume work]
  uses: [solera-write-identity, solera-write-concept, solera-write-milestone, solera-write-story, solera-execute-action-item, solera-release, solera-publish-artifacts]
---

# Manage Workflow (Supervisor)

> The workflow manager **reads and executes — it does not define**.
> The `## Workflow` section of each work item template is the SSOT.
> In v3 the supervisor understands three axes: **Living** (Concepts), **Time-bound** (Milestones, Stories, Action Items), and **Immutable** (Releases).

## Common Rules

- [conventions.md](assets/conventions.md) — hierarchy, folder structure, branches, status values
- [lifecycle.md](assets/lifecycle.md) — Workflow pattern description

## Prerequisites

- `{project_path}/progress.md` exists; if not, initialize from [assets/progress.md](assets/progress.md).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **action** | N | Action type | start \| complete \| check \| next |
| **work_item** | N | Target work item path | `stories/US-001-google-login/_story.md` |

## Output

| Action | Output | Path |
|--------|--------|------|
| start / complete | progress.md update | `{project_path}/progress.md` |
| complete (Story) | RETROSPECTIVE.md written | `{story_path}/RETROSPECTIVE.md` |
| next | Next work item decided | — |
| check | Current state report | — |

## Procedure

> This skill's own Procedure below describes **how the supervisor drives other work items' `## Workflow` sections**. It is meta-procedure, not domain procedure. Domain procedures live in the target work item's template (Concept / Milestone / Story / Action Item).

### start — Start work item

1. Read the target work item (`_story.md` or `{milestone_id}.md` or `{concept_id}.md`).
2. Extract the `## Workflow` section.
3. Execute each step in order **(BLOCKING: sequential)**.
4. If document writing is required, invoke the appropriate write-* skill **(BLOCKING: wait for completion)**.
5. Update `progress.md`.

### complete — Complete work item

1. Read the target work item.
2. Execute the Wrap-up step(s) of `## Workflow` (gate checks, status change, etc.).
3. For a Story: confirm RETROSPECTIVE.md written with Concept Contribution Summary, confirm each contributed Concept's Current Shape was updated with human approval.
4. Update `progress.md`.
5. Decide next work item.

### check — Check current status

1. Read `progress.md`.
2. Read `concepts/_index.md` and `milestones/_index.md` (if they exist) for the Living / Time-bound view.
3. Return: active Concepts, active Milestone (if any), current Story + Action Item.

### next — Decide next work

The supervisor is state-aware. Branch on current state:

1. **ACT in progress** → resume that ACT via `solera-execute-action-item`.
2. **Story in progress, ACTs remaining** → start the next incomplete ACT.
3. **Story all ACTs complete, Wrap-up pending** → drive Story Wrap-up (RETROSPECTIVE + Concept Current Shape updates).
4. **Story complete, Milestone has more Stories pending** → suggest the next Story (do not auto-pick; the human decides).
5. **Milestone Exit Criteria all met** → advise `solera-write-milestone --mode=mark-released`, then `solera-release`.
6. **No active Milestone but Concepts exist** → advise `solera-write-milestone` to agree on next scope.
7. **No Concepts yet** → advise `solera-write-concept` to draw the first one.
8. **No Identity yet** → advise `solera-write-identity`.

> **Do NOT suggest handoff, session end, or session switch at any point.** Handoff is user-initiated only (via `solera-handoff`).

## Responsibilities

| Role | Skill |
|------|-------|
| **Identity writing** | solera-write-identity |
| **Concept drawing / updating** | solera-write-concept |
| **Milestone agreement / release marking** | solera-write-milestone |
| **Story planning + execution** | solera-write-story, solera-execute-action-item |
| **Release snapshotting** | solera-release |
| **Execution supervision** | solera-manage-workflow (this skill) |
| **Artifact promotion** | solera-publish-artifacts (invoked at Story Wrap-up) |

## Supervision Principles

- Reads the work item's `## Workflow` as the SSOT.
- Does not define procedures directly — follows the procedures defined in the template.
- Delegates document writing to write-* skills.
- Delegates development work to frontend-*, dev-* skills.
- **Never suggests handoff** after completing a work item — proceeds to the next item or asks the user what to do next.
- **State-aware but not opinionated** — when multiple valid next steps exist, the supervisor surfaces the options and lets the human choose.

## Human–AI Protocol

| AI does | AI does not |
|---------|-------------|
| Read progress.md and the relevant Workflow section | Decide what to work on when multiple Stories are open |
| Drive each Workflow step in order | Skip Wrap-up steps (gate checks, Concept Current Shape updates) |
| Surface state-based options at decision points | Auto-start the next Story without human signal |
| Delegate writing / development to specialized skills | Invent procedures not declared in templates |

## Templates

- [assets/progress.md](assets/progress.md) — progress.md template (v3 format)
- [assets/retro.md](assets/retro.md) — retrospective base
- [assets/status.md](assets/status.md) — status convention

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| progress.md missing | File not found | Initialize from template | Continue after creation |
| Work item file missing | Named path has no file | Report; request correct path | Halted |
| Workflow section missing | No `## Workflow` in template | Report template bug; apply default 4-phase pattern from lifecycle.md | Continue (degraded) |
| write-* invocation failed | Sub-skill error | Report; request manual execution | Halted |
| Status mismatch | Story ✅ but parent Milestone not updated | Report and sync | Halted before next decision |
| Concept Current Shape never updated | Wrap-up skipped the loop | Halt until updates are drafted and approved | Blocking |
| Gate failure | workflow_gate check blocks | Report failing check | Blocking |
| No next work | All Milestones released, no Concepts pending | Report "no active work; draw a new Concept or agree a new Milestone" | Completes normally |

## Completion Checklist

- [ ] Read the Workflow section of the work item
- [ ] Executed Workflow steps in order
- [ ] Updated progress.md
- [ ] (Story) Wrote RETROSPECTIVE with Concept Contribution Summary
- [ ] (Story) Each contributed Concept's Current Shape updated with human approval
- [ ] Decided the next work item or surfaced options
