# Conventions (v3)

<!-- SSOT: ../../../docs/reference/axes-and-status.md — do not redefine axes, status, or ownership here -->

Project-wide rules referenced by all Solera skills. Axis definitions, ownership, and status values live in [axes-and-status.md](../../../docs/reference/axes-and-status.md). This file owns folder layout, branches, and operator quick cards only.

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

See [axes-and-status.md](../../../docs/reference/axes-and-status.md) for the authoritative tables and transition rules. Do not duplicate them here.
