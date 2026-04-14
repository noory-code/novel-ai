# Template: Story

Defines the decomposition unit that contributes to Concepts. Covers both User Stories and Technical Stories.

Every Story **must** declare which Concepts it contributes to. It **may** declare which Milestone it belongs to.

## _story.md (User Story)

```markdown
---
story_id: US-NNN
story_name: {kebab-case name}
story_type: US
status: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Cancelled
contributes_to: [concept_id_1, concept_id_2]
belongs_to: {milestone_id or omitted}
created: {YYYY-MM-DD}
---

# US-NNN: {title}

> contributes to: {concept names, comma-separated}
> belongs to: {milestone name or —}
> Status: 🔄 In Progress

## User Story

**As a** {persona}
**I want** {action}
**So that** {outcome}

## Acceptance Criteria

- [ ] {criterion 1}
- [ ] {criterion 2}

## Input Artifacts

<!-- Materials needed to start this Story. Filled in at Step 2.
     Keep only lines that actually exist; remove unused placeholders. -->

- Design: {Figma / Pen URL or internal path}
- Spec: {Notion / docs link or internal path}
- Reference: {prior Story / existing code path}

## Output Artifacts

<!-- What this Story produces. AI appends entries during Execute; final list is fixed at Wrap-up. -->

(none yet — populated during Execute)

## Action Items

| ID | Action Item | Skill | Agent | Phase | depends_on | Status | Commit |
|----|-------------|-------|-------|-------|------------|--------|--------|
| ACT-001 | {Action Item title} | {skill name or -} | {agent name or -} | 1 | - | ⏳ Pending | - |
| ACT-002 | {Action Item title} | {skill name or -} | {agent name or -} | 1 | - | ⏳ Pending | - |
| ACT-003 | {Action Item title} | {skill name or -} | {agent name or -} | 2 | ACT-001,ACT-002 | ⏳ Pending | - |

**Progress**: 0/N Action Items complete
```

## _story.md (Technical Story)

```markdown
---
story_id: TS-NNN
story_name: {kebab-case name}
story_type: TS
status: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Cancelled
contributes_to: [concept_id_1]
belongs_to: {milestone_id or omitted}
created: {YYYY-MM-DD}
---

# TS-NNN: {title}

> contributes to: {concept names}
> belongs to: {milestone name or —}
> Status: 🔄 In Progress

## Technical Goal

{The technical problem this Story resolves and why it advances the contributed Concept(s).}

## Spec

| Item | Details |
|------|---------|
| **Impact Scope** | {which systems are affected} |
| **Dependencies** | {prerequisite Stories / libraries} |

## Acceptance Criteria

- [ ] {criterion 1}
- [ ] {criterion 2}

## Input Artifacts

- Reference: {architecture doc / prior code path}
- Spec: {design doc link}

## Output Artifacts

(none yet — populated during Execute)

## Action Items

| ID | Action Item | Skill | Agent | Phase | depends_on | Status | Commit |
|----|-------------|-------|-------|-------|------------|--------|--------|
| ACT-001 | {Action Item title} | {skill name or -} | {agent name or -} | 1 | - | ⏳ Pending | - |

**Progress**: 0/N Action Items complete
```

## Workflow

### Step 0. Setup
- [ ] Confirm each `contributes_to` Concept exists at `concepts/{id}.md` with `status: active` (gate `concept.align`)
- [ ] If `belongs_to` is set: milestone status must be `agreed` or `in-progress`
- [ ] Read previous retrospectives (apply AI Improvements)
- [ ] Read `team-process.md` (workflow_gates, execution_order, architecture_rules)
- [ ] Create branch `story/{story_id}-{story_name}` from base
- [ ] Create Story folder; status → 🔄

### Step 1. Define
- [ ] Determine Story type (US / TS)
- [ ] Write story body + acceptance criteria
- [ ] Collect **Input Artifacts** (human provides up front)

### Step 2. Decompose
- [ ] Scan available skills
- [ ] Write Action Items table (1 ACT = 1 commit)
- [ ] Assign Skill / Agent / Phase / depends_on per ACT
- [ ] Layer-aware decomposition when `execution_order.groups` is defined
- [ ] Validate Phase ordering against group order
- [ ] Create one `ACT-NNN-{name}.md` per row; block Step 3 until count matches

### Step 3. Execute
- [ ] Gate check `story.execute`
- [ ] Invoke `solera-execute-action-item` per ACT in Phase order (blocking, sequential)
- [ ] Output Artifacts appended by each ACT completion
- [ ] Confirm acceptance criteria + all ACTs ✅

### Step 4. Wrap-up
- [ ] Gate check `story.wrap_up`
- [ ] Write `RETROSPECTIVE.md` (must include "Concept Contribution Summary")
- [ ] For each contributed Concept:
  - AI drafts Current Shape revision → human approves/edits
  - Append row to `# Contributions`
- [ ] Status → ✅
- [ ] Squash-merge to base branch

## Folder Structure

```
{project_path}/workspace/stories/{story_id}-{story_name}/
├── _story.md
├── RETROSPECTIVE.md                  # created at Wrap-up
├── ACT-001-{name}.md
├── ACT-002-{name}.md
└── ACT-003-{name}.md
```

## Story ID Rules

| Prefix | Type | Example |
|--------|------|---------|
| `US-` | User Story | US-001, US-002 |
| `TS-` | Technical Story | TS-001, TS-002 |

> **v3 change**: Story IDs are unique **globally within `stories/`**, not scoped to an Epic (Epic no longer exists).
> Use numeric ranges per contributor if needed to avoid collisions.

## Commit Message Format

```
[{primary_concept}][{story_id}][ACT-NNN] title
```

Where `{primary_concept}` is `contributes_to[0]`.

## Quality Criteria

- [ ] `contributes_to` is present and non-empty
- [ ] Every `contributes_to` Concept exists and is active
- [ ] If `belongs_to` is set, milestone is agreed/in-progress
- [ ] User Story follows As a / I want / So that format (or TS has technical goal)
- [ ] Acceptance criteria are verifiable
- [ ] Every Action Item has ID, Skill, Agent, Phase, depends_on
- [ ] ACTs in the same Phase can run in parallel without output conflicts
- [ ] Input Artifacts captured at creation; Output Artifacts captured during Execute
- [ ] Concept Current Shape updates proposed and approved at Wrap-up
