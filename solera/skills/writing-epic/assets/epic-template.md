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
- [ ] Confirm `goals/*/_goal.md` exists → invoke writing-goal if missing
- [ ] Create `epic-[name]` branch (from dev)
- [ ] Status → 🔄

### Step 1. Create
- [ ] Write Use Cases → `artifacts/use-case/UC-NNN-[name].md`
- [ ] Derive Concepts → `artifacts/concept/domain.md`
- [ ] Define Entities → `artifacts/concept/entities/*.md`
- [ ] Decompose Stories → `stories/[US|TS]-NNN/_story.md`
- [ ] Write `_epic.md` → Stories table, completion criteria

### Step 2. Execute
<!-- Repeat the block below for each Story in the Stories table -->
#### Story: {US|TS}-NNN — {title}
- [ ] writing-story invoke (Create → create branch → Execute → Wrap-up)
- [ ] Merge into Epic branch
<!-- /repeat -->
- [ ] Confirm all Stories complete

### Step 3. Wrap-up
- [ ] Write retrospective → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] workflow-pr invoke → create PR to parent branch + merge
- [ ] Determine next Epic or process Goal completion
