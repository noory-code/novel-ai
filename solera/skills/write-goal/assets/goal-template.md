# Template: _goal.md

## _goal.md

```markdown
# Goal: [name]

> Phase: [phase]
> Status: ⏳ Pending

## Journey (rough)

| Journey | Persona | Steps |
|---------|---------|-------|
| [name] | [persona] | Step1 → Step2 → Step3 |

## Epics

| Epic | Journey | Status |
|------|---------|--------|
| 01-[name] | [journey] | ⏳ |

## Completion Criteria

- [ ] All Epics complete
```

## Workflow

### Step 0. Setup
- [ ] Confirm `published/identity/mission.md` exists; if missing, invoke write-identity
- [ ] Create `goals/[goal-id]-[name]/` folder
- [ ] Create `goals/[goal-id]-[name]/artifacts/` folder
- [ ] Status → 🔄

### Step 1. Create
- [ ] Generate Service Map and Persona (Feature only; skip for Enabler)
- [ ] Write Journey (rough): define the steps sequence for each Persona
- [ ] Decompose Epics: map to Journeys and assign numbers (01, 02, ...)
- [ ] Write `_goal.md` with the Journey table, Epics table, and completion criteria

### Step 2. Execute
<!-- Repeat the block below for each Epic in the Epics table -->
#### Epic: {number}-{name}
- [ ] write-epic invoke (Setup → Create → Execute → Wrap-up)
- [ ] create-pr invoke (PR to parent branch)
<!-- /repeat -->
- [ ] Confirm all Epics complete

### Step 3. Wrap-up
- [ ] Write retrospective to RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] transition-catalog invoke (artifacts/ → published/)

## Goal Types

| Type | Output | Examples |
|------|--------|---------|
| **Feature** | Service Map, Persona, and Journey leading to Epics | liquor-search, profile |
| **Enabler** | Epic only (Persona/Journey can be skipped) | infrastructure, DB design |
