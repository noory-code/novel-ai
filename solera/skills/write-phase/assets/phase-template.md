# Template: Phase README.md

## README.md

```markdown
# Phase: [phase-id]

> Initiative: [year]
> Status: ⏳ Pending

## Overview

| Item | Details |
|------|---------|
| **Period** | [YYYY-MM ~ YYYY-MM] |
| **Objective** | [One-line summary of Phase objective] |

## Goals

| Goal | Type | Status | Progress | Folder |
|------|------|--------|----------|--------|
| [goal-id]: [name] | [Feature|Enabler] | ⏳ Pending | 0/N | [→](./goals/[goal-id]-[name]/) |

**Phase Progress**: 0/N Goals complete

## Completion Criteria

- [ ] [completion criteria per goal]
```

## Workflow

### Step 0. Setup
- [ ] Confirm `workspace/initiative/[year]/roadmap.md` exists
- [ ] Review Goals assigned to this Phase in roadmap.md
- [ ] Create `workspace/phase/[phase-id]/` folder
- [ ] Create `workspace/phase/[phase-id]/goals/` folder
- [ ] Status → 🔄

### Step 1. Create
- [ ] Write Phase README.md (overview, Goals table, completion criteria)
- [ ] Create each Goal folder structure (`goals/[goal-id]-[name]/`)

### Step 2. Execute
<!-- Repeat the block below for each Goal in the Goals table -->
#### Goal: {goal-id}-{name}
- [ ] write-goal invoke
- [ ] Elaborate Goal and decompose Epics
- [ ] Complete all Epics
<!-- /repeat -->
- [ ] Confirm all Goals complete

### Step 3. Wrap-up
- [ ] Confirm all Goal statuses are ✅
- [ ] Confirm transition-catalog complete for each Goal (moved to `workspace/catalog/`)
- [ ] Write SUMMARY.md covering overall Goal outcomes, the catalog artifact list, and handoff notes for the next Phase
- [ ] Write RETRO.md (ref: [retro.md](retro.md))
- [ ] Set README.md status → ✅ and update progress
- [ ] Update progress.md
- [ ] Determine next Phase
