# Rule: Solera Workflow

> **Scope**: When working on any task in this project that uses the Solera plugin for work management.

## Work Item Hierarchy

```
Phase (quarter) → Goal (weeks) → Epic (days) → Story (hours) → Action Item (commit)
```

- Each work item has a `## Workflow` section — follow it as the SSOT for procedure
- All workflows follow: Setup → Create → Execute → Wrap-up

## Git Branch Rules

- [ ] Epic: `epics/[name]` branch from parent
- [ ] Story: `epics-[name]/story-[ID]-[name]` branch from Epic
- [ ] Action Item: commit only, no branch
- [ ] Commit format: `[epic-name][US|TS-NNN][ACT-NNN] description`

## Artifact Promotion

Artifacts are promoted incrementally via `solera-transition-catalog`, not in bulk:

- [ ] After Goal Create: service-map, persona, journey → `published/`
- [ ] At each Epic Wrap-up: use-case, concept → `published/`
- [ ] By Goal Wrap-up: `artifacts/` must be empty

## State Files

| File | Purpose | Lifespan |
|------|---------|----------|
| `progress.md` | Current Phase/Goal/Epic/Story/ACT position | Permanent |
| `HANDOFF.md` | Session context for next session | Overwritten each session |
| `RETRO.md` | Retrospective per work item | Permanent |

## Status Values

| Icon | Status |
|------|--------|
| ⏳ | Pending |
| 🔄 | In Progress |
| ✅ | Complete |
| ⏸️ | On Hold |

## Good / Bad Examples

| Bad | Good |
|---|---|
| Commit without `[epic][story][act]` prefix | `[auth][US-001][ACT-001] add login form` |
| Create artifact directly in `published/` | Create in `artifacts/`, promote via `solera-transition-catalog` |
| Skip `RETRO.md` at Wrap-up | Write retrospective at every level |
| Push code without completing all Action Items in a Story | Complete all ACTs, then merge Story branch |

## Project Config

> Optional settings. Skills read these values when present; omit any line to use defaults.

```yaml
# default_pr_base: dev          # Target branch for solera-create-pr (if omitted: ask user)
```
