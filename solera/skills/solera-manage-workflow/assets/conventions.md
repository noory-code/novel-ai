# Conventions (v3)

Project-wide rules referenced by all Solera skills.

## Axes

Solera organizes a project on three axes:

| Axis | Characteristic | Items |
|------|----------------|-------|
| **Living** | Never ends, evolves continuously | Identity, Concepts |
| **Time-bound** | Has a start and end | Milestone, Story, Action Item |
| **Immutable** | Frozen snapshot, write-once | Release |

## Human vs AI Role

| Role | Owned items | Primary responsibility |
|------|-------------|------------------------|
| **Human** | Identity, Concepts, Milestone agreement, Release approval | Direction, Intent, scope agreement, final say |
| **AI** | Story, Action Item; drafts for Milestone analysis / Release notes | Decomposition, implementation, proposals |

Both collaborate at **Milestone Agreement** (Moment 2) and **Story Wrap-up** (결과 확정 of Moment 3).

## Folder Structure

```
{project}/
├── progress.md                       # current state on all three axes
├── HANDOFF.md                        # transient session state
└── workspace/
    ├── identity/                     # mission, values, vision
    ├── concepts/                     # Living Axis — one file per Concept
    │   ├── _index.md
    │   └── {concept_id}.md
    ├── milestones/                   # Time-bound — agreements
    │   ├── _index.md
    │   └── {milestone_id}.md
    ├── stories/                      # Time-bound — flattened
    │   └── {story_id}-{story_name}/
    │       ├── _story.md
    │       ├── ACT-NNN-{name}.md
    │       └── RETROSPECTIVE.md
    ├── releases/                     # Immutable snapshots
    │   ├── _index.md
    │   └── {release_tag}/
    │       ├── .released
    │       ├── README.md
    │       ├── concepts-snapshot/
    │       └── stories-manifest.md
    ├── team-process.md               # team conventions (gates, layers, architecture rules)
    └── catalog/
        └── published/                # promoted design artifacts
            ├── persona/
            ├── service-map/
            ├── journey/
            ├── use-case/
            └── domain-model/
```

## Git Branches

| Level | Branch | Branched From |
|-------|--------|---------------|
| **Story** | `story/{story_id}-{story_name}` | trunk (`main` / `dev`) |

> Action Item is a **commit only** — no branch.
> Epic branches no longer exist in v3.

## Status Values

| Icon | Status | Meaning |
|------|--------|---------|
| ⏳ | Pending | Not yet started |
| 🔄 | In Progress | Work in progress |
| ✅ | Complete | Work complete |
| ⏸️ | On Hold | Temporarily paused |
| ❌ | Cancelled | Abandoned |

## Concept / Milestone Status

Concepts and Milestones use a different status scheme aligned with their axis:

| Item | Status values |
|------|---------------|
| Concept | `active` / `deprecated` / `archived` |
| Milestone | `proposed` / `agreed` / `in-progress` / `released` |
| Release | always immutable once written (no status field beyond `.released` marker) |
