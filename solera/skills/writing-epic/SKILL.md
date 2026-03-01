---
name: writing-epic
description: Epic document writing. Creates Use Case, Concept → decomposes into Stories.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Epic elaboration, Epic start, decompose into Stories, Use Case, Concept]
  uses: [writing-story]
---

# Writing Epic

> Writes _epic.md and decomposes into Stories.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `writing-identity` with Skill tool
- `_goal.md` exists
  - If not: check `{goal_path}/_goal.md` with Glob tool → invoke `writing-goal` with Skill tool
- The corresponding Epic must be assigned in _goal.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1-search-liquor |
| **epic_name** | Y | Epic name | 01-auth |
| **epic_type** | N | Feature \| Enabler (default: Feature) | Enabler |

## Output

| Step | Output | Nature | Path |
|------|--------|--------|------|
| Setup | _epic.md | Final | `{goal_path}/epics/{epic_name}/_epic.md` |
| UseCase | UC-NNN.md (Feature only) | Intermediate (artifacts) | `{goal_path}/artifacts/use-case/UC-NNN-{name}.md` |
| Concept | domain.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/domain.md` |
| Concept | entities/*.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/entities/{entity}.md` |
| Story | _story.md | Final | `{goal_path}/epics/{epic_name}/stories/{US\|TS}-NNN/_story.md` |
| Wrap-up | RETRO.md | Final | `{goal_path}/epics/{epic_name}/RETRO.md` |

> `{goal_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}`
> artifacts = intermediate outputs. Moved to published/ via catalog-transition upon Goal completion.

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-story` | Elaborate each Story and decompose into Action Items | Execute |
| `workflow-pr` | Create PR upon Story/Epic completion | Execute, Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `{goal_path}/_goal.md` exists with Glob tool
     - If not: invoke Skill tool `skill="writing-goal"` → resume this Step after completion
   - [ ] Create `epic-{epic_name}` branch (from Goal branch)
   - [ ] Create `{goal_path}/epics/{epic_name}/` folder
   - [ ] Create _epic.md draft → ref: [assets/epic-template.md](assets/epic-template.md)
   - [ ] Status → 🔄

2. **Create Use Case** (Feature only, skip for Enabler)
   - [ ] Define Actor (person/system)
   - [ ] Define Goal (measurable objective)
   - [ ] Write basic flow (step by step)
   - [ ] Write alternative/exception flows
   - [ ] → ref: [assets/use-case.md](assets/use-case.md)

3. **Create Concept**
   - [ ] Derive core concepts, write/update domain.md → ref: [assets/concept.md](assets/concept.md)
   - [ ] Write detailed description per Entity → ref: [assets/entity.md](assets/entity.md)
   - [ ] Relationship diagram (Mermaid classDiagram)
   - domain.md rule: first Epic creates it, subsequent Epics **update** (no overwriting)
   - concept.md = full version template, entity.md = quick reference skeleton

4. **Story decomposition + complete _epic.md**
   - [ ] Map Use Case → Story (Feature), technical tasks → Story (Enabler)
   - [ ] Assign Story IDs (US: User Story, TS: Technical Story)
   - [ ] Estimate expected commit count per Story
   - [ ] Complete Stories table in _epic.md, define completion criteria

5. **Execute**
   - [ ] Extract incomplete (⏳ or no status) Stories from Stories table in `_epic.md`
   - [ ] Execute each Story in order (do not proceed to next Step until all Stories are complete):
     ```
     Skill tool call: skill="writing-story"
       args: story_id={US|TS-NNN}, story_name={name}, epic_name={epic_name},
             goal_id={goal_id}, phase_id={phase_id}, project_path={project_path}
     → Confirm _story.md created + status ✅ before proceeding to next Story
     ```
   - [ ] Merge to Epic branch upon Story completion
   - [ ] Proceed to Step 6 after confirming all Story statuses ✅

6. **Wrap-up**
   - [ ] Confirm all Story statuses ✅ (return to Step 5 if any incomplete)
   - [ ] Write RETRO.md → ref: [assets/retro.md](assets/retro.md)
   - [ ] _epic.md status → ✅
   - [ ] Skill tool call: `skill="workflow-pr"` → create PR to parent branch (Goal)

## Folder Structure

```
{goal_path}/
├── artifacts/                # Intermediate outputs
│   ├── use-case/UC-NNN-{name}.md
│   └── concept/
│       ├── domain.md
│       └── entities/{entity}.md
└── epics/{epic_name}/
    ├── _epic.md
    ├── RETRO.md              # Created at Wrap-up
    └── stories/{US|TS}-NNN/
        └── _story.md
```

## Completion Checklist

- [ ] _epic.md created
- [ ] If Feature: Use Case written
- [ ] Concept (domain.md, entities) written/updated
- [ ] Story decomposition complete
- [ ] (Execute) writing-story invoked for all Stories
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _epic.md status ✅
- [ ] (Wrap-up) workflow-pr invoked
