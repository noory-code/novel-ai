# Lifecycle (v3)

All work items that have their own procedure — Concept, Milestone, Story, Action Item — declare that procedure in a `## Workflow` section of their template.

## Core Principles

- **SSOT**: the `## Workflow` in each work item's template is the single authoritative source of procedure.
- **Supervisor reads and executes**: `solera-manage-workflow` does not define procedures; it drives the steps declared in the template.
- **Release has no Workflow** — it is an immutable output of `solera-release`, not a work item with a lifecycle of its own.

## Standard Workflow Pattern

Most Workflows use the 4-phase pattern:

```markdown
## Workflow

### Step 0. Setup
- [ ] Check prerequisites → invoke upstream skill if missing
- [ ] Initialize folder / branch / status if applicable

### Step 1. Create
- [ ] ... (handled by the write-* skill or by this skill's own logic)

### Step 2. Execute
- [ ] ... (perform the substantive work; delegate to child skills as needed)

### Step 3. Wrap-up
- [ ] Confirm completion / run gate checks
- [ ] Status → ✅ (or the item's completion state)
- [ ] Surface next-work decision to human
```

Action Items use a 3-phase pattern (Setup → Execute → Wrap-up — no Create step, because the file already exists by the time an ACT runs).

## Workflow Location by Work Item

| Work Item | Template with `## Workflow` | Phases |
|-----------|-----------------------------|--------|
| **Concept** | solera-write-concept/assets/concept-template.md | Setup → Create → Update / Deprecate / Archive → Wrap-up (mode-driven) |
| **Milestone** | solera-write-milestone/assets/milestone-template.md | Setup → Create (Agreement Cycle) → Update / Mark-released → Wrap-up (mode-driven) |
| **Story** | solera-write-story/assets/story.md | Setup → Define → Decompose → Execute → Wrap-up |
| **Action Item** | solera-execute-action-item/assets/action-item.md | Setup → Execute → Test verification → Wrap-up |

> Identity and Release do not have `## Workflow` sections:
> - Identity is a one-time human statement; no repeat lifecycle.
> - Release is an immutable output, not a lifecycle.

## Repeat Block Pattern

When a work item iterates over children (Story over Action Items; Milestone scope over Concepts), the template marks the loop with HTML comments:

```markdown
### Step 3. Execute
<!-- Repeat the block below for each Action Item in the Action Items table -->
#### Action Item: ACT-NNN — {title}
- [ ] Invoke solera-execute-action-item
- [ ] Confirm status ✅ before next ACT
<!-- /repeat -->
- [ ] Confirm all ACTs complete
```

- **Template**: define exactly one block between `<!-- repeat -->` and `<!-- /repeat -->`.
- **Actual document**: the write-* skill expands the block to match the real rows in the table when creating the work item, so each child appears as its own checkbox.
- **Progress tracking**: expanded checkboxes let the supervisor see per-child progress.

## Supervisor Role

`solera-manage-workflow`:

1. Reads `progress.md` and the two indexes (`concepts/_index.md`, `milestones/_index.md`) to locate the current state.
2. Reads the target work item's `## Workflow` section.
3. Executes each step in order.
4. Invokes write-* or development skills as declared.
5. Updates `progress.md` after state transitions.
6. At decision points with multiple valid next steps, **surfaces options to the human** rather than deciding alone.

The supervisor owns no domain logic. If a skill wants to add or change procedure, it edits its own template's `## Workflow` section — not this supervisor's code.
