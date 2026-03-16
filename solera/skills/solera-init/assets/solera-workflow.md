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

## Team Customization

> Add your team's process rules here. Solera provides the work item structure — this section
> defines **how your team works within that structure**. AI reads these rules on every task.

### Workflow Gates

> Define prerequisites that must be met before entering a specific phase.
> Format: `[work-item-level].[step]: [condition]`

```yaml
# examples:
# epic.concept: design artifact must exist in artifacts/design/ before writing Concept
# story.execute: test plan must be approved before starting Action Items
```

### Artifact Conventions

> Override how specific artifact types are produced or stored.

```yaml
# examples:
# artifact.erd: use Miro link instead of file (add link to domain.md)
# artifact.design: Figma link required in _epic.md before Concept step
```

### Commit & Branch Conventions

> Extend or override the default git rules above.

```yaml
# examples:
# commit_prefix: "[JIRA-{id}]"   # prepend Jira ticket to every commit message
# branch_prefix: "team/"         # add team prefix to all branches
```

### Technology Stack

> Inform AI of the tech stack so it generates correct code and architecture.

```yaml
# examples:
# backend: "Spring Boot 3, Kotlin, JPA"
# frontend: "Next.js 14, TypeScript, Tailwind CSS"
# database: "PostgreSQL 16"
# infra: "AWS ECS, RDS, S3"
```

### Custom Rules

> Any other team-specific constraints not covered above.

```
# examples:
# - All PRs require at least 2 approvals before merge
# - API changes must include OpenAPI spec update as a separate Action Item
# - No direct commits to epics/* branches — always go through Story branch
```
