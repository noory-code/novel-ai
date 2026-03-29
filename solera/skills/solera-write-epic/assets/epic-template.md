# Template: _epic.md

## _epic.md

```markdown
# Epic: [name]

> Goal: [goal]
> Status: ⏳ Pending

## Overview
| Item | Details |
|------|---------|
| **Type** | Feature |
| **Journey** | [journey name] |

## User Value
**As a** [user],
**I want** [feature],
**So that** [value].

## Stories
| ID | Story | Status |
|----|-------|--------|
| US-001 | [title] | ⏳ |

## Completion Criteria
- [ ] All Stories complete
```

## Workflow

### Step 0. Setup
- [ ] Confirm `goals/*/_goal.md` exists; if missing, invoke solera-write-goal
- [ ] Create `epics/[name]` branch (from dev)
- [ ] Status → 🔄

### Step 1. Create
- [ ] Write Use Cases to `artifacts/use-case/UC-NNN-[name].md`
- [ ] Derive Concepts to `artifacts/concept/domain.md`
- [ ] Define Entities in `artifacts/concept/entities/*.md`
- [ ] Decompose Stories into `[US|TS]-NNN-[name]/_story.md`
- [ ] Write `_epic.md` with the Stories table and completion criteria

### Step 2. Execute
<!-- Repeat the block below for each Story in the Stories table -->
#### Story: {US|TS}-NNN — {title}
- [ ] solera-write-story invoke (Create → create branch → Execute → Wrap-up)
- [ ] Merge into Epic branch
<!-- /repeat -->
- [ ] Confirm all Stories complete

### Step 3. Wrap-up
- [ ] solera-publish-artifacts invoke (promote Epic-level artifacts: use-case, concept → published/)
- [ ] Write retrospective to RETROSPECTIVE.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] solera-create-pr invoke (create PR to parent branch and merge)
- [ ] Determine the next Epic or process Goal completion
