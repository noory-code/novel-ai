# Template: Story

Defines the decomposition unit of an Epic, covering both User Stories and Technical Stories.

## _story.md (User Story)

```markdown
# US-NNN: [title]

> Epic: [parent Epic name]
> Status: ⏳ Pending / 🔄 In Progress / ✅ Complete / ❌ Cancelled

## User Story

**As a** [persona],
**I want** [action],
**So that** [purpose].

## Acceptance Criteria

- [ ] [criterion 1]
- [ ] [criterion 2]

## Action Items

| ID | Action Item | Skill | Agent | Phase | depends_on | Status | Commit |
|----|-------------|-------|-------|-------|------------|--------|--------|
| ACT-001 | [Action Item title] | [skill name or -] | [agent name or -] | 1 | - | ⏳ Pending | - |
| ACT-002 | [Action Item title] | [skill name or -] | [agent name or -] | 1 | - | ⏳ Pending | - |
| ACT-003 | [Action Item title] | [skill name or -] | [agent name or -] | 2 | ACT-001,ACT-002 | ⏳ Pending | - |

**Progress**: 0/N Action Items complete
```

## _story.md (Technical Story)

```markdown
# TS-NNN: [title]

> Epic: [parent Epic name]
> Status: ⏳ Pending / 🔄 In Progress / ✅ Complete / ❌ Cancelled

## Technical Goal

[The technical problem/goal this task resolves]

## Spec

| Item | Details |
|------|---------|
| **Impact Scope** | [which systems are affected] |
| **Dependencies** | [prerequisite tasks/libraries] |

## Acceptance Criteria

- [ ] [criterion 1]
- [ ] [criterion 2]

## Action Items

| ID | Action Item | Skill | Agent | Phase | depends_on | Status | Commit |
|----|-------------|-------|-------|-------|------------|--------|--------|
| ACT-001 | [Action Item title] | [skill name or -] | [agent name or -] | 1 | - | ⏳ Pending | - |

**Progress**: 0/N Action Items complete
```

## Workflow

### Step 0. Setup
- [ ] Confirm `epics/*/_epic.md` exists; if missing, invoke solera-write-epic
- [ ] Status → 🔄

### Step 1. Create (performed on Epic branch)
- [ ] Determine Story type (US / TS)
- [ ] Define acceptance criteria
- [ ] Scan available skills: `Glob .claude/skills/*/SKILL.md` and `Glob .claude/plugins/*/skills/*/SKILL.md`
- [ ] Write `_story.md` with the story/technical goal, acceptance criteria, and Action Items table
- [ ] Create Action Item files (required) as `ACT-NNN-[name].md` in the Story folder
- [ ] Assign responsible Agent per Action Item (when using agent team)
- [ ] Assign Skill per Action Item: match task content against scanned skill triggers; set `-` if no match
- [ ] Define dependencies between Action Items (depends_on)
- [ ] Allocate phases (Action Items that can run in parallel belong to the same Phase)
- [ ] Create `epic-[name]/story-[ID]-[name]` branch (from Epic branch)

### Step 2. Execute
<!-- Execute Action Items in Phase N in parallel. Next Phase starts after previous Phase is complete -->
<!-- Repeat the block below for each Action Item in the Action Items table -->
#### Action Item: ACT-NNN — {title}
- [ ] solera-execute-action-item invoke or development skill invoke
- [ ] Perform work and commit
<!-- /repeat -->
- [ ] Confirm all acceptance criteria are met
- [ ] Confirm all Action Items complete

### Step 3. Wrap-up
- [ ] Build/tests pass
- [ ] Write retrospective to RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] Status → ✅
- [ ] Squash merge into Epic branch
- [ ] Determine the next Story or process Epic completion

## Folder Structure

```
{epic_path}/[US|TS]-NNN-[name]/
├── _story.md
├── ACT-001-[name].md
├── ACT-002-[name].md
└── ACT-003-[name].md
```

## Story ID Rules

| Prefix | Type | Example |
|--------|------|---------|
| `US-` | User Story | US-001, US-002 |
| `TS-` | Technical Story | TS-001, TS-002 |

> **Note**: Story IDs are unique only **within an Epic**.
> `login/US-001` ≠ `profile/US-001`

## Quality Criteria

- [ ] Does the User Story follow the As a / I want / So that format?
- [ ] Does the Technical Story have a technical goal?
- [ ] Are acceptance criteria defined?
- [ ] Have all Action Items been assigned an ID?
- [ ] Is progress displayed?
- [ ] Are Skill, Agent, Phase, and depends_on defined for each Action Item?
- [ ] Can Action Items in the same Phase run in parallel without output conflicts?
