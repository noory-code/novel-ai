# Conventions

This file defines the project-wide rules referenced by all skills.

## Work Item Hierarchy

```
Identity > Initiative > Phase > Goal > Epic > Story > Action Item
           (annual)    (quarter) (goal) (task) (daily) (commit)
```

| Role | Hierarchy | Responsibility |
|------|-----------|----------------|
| **Human** | Identity~Phase | Strategic decisions, approval |
| **AI** | Goal~Action Item | Decomposition, document generation, implementation |

## Git Branches

| Hierarchy | Branch Name | Branch From |
|-----------|-------------|-------------|
| **Epic** | `epics/[name]` | Parent branch |
| **Story** | `epics-[name]/story-[ID]-[name]` | Epic branch |

> Action Item = commit only (no branch)

## Folder Structure

```
[project]/
├── progress.md
└── workspace/
    ├── identity/
    ├── initiative/[year]/
    ├── phase/[phase]/
    │   └── goals/[goal]/
    │       ├── _goal.md
    │       ├── artifacts/
    │       └── epics/
    └── catalog/
```

## Status Values

| Icon | Status | Description |
|------|--------|-------------|
| ⏳ | Pending | Not yet started |
| 🔄 | In Progress | Work in progress |
| ✅ | Complete | Work complete |
| ⏸️ | On Hold | Temporarily paused |
