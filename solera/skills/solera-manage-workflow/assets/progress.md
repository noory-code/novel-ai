# Template: Progress (v3)

Document for tracking the project's current state on all three axes: Living (Concepts), Time-bound (Milestone, Story, ACT), and Immutable (latest Release).

## Location

```
{project_path}/.solera/progress.md
```

## Template

```markdown
# Progress

> Last updated: {YYYY-MM-DD HH:MM}

## Living Axis

**Active Personas** ({count}):
<!-- Extracted from personas/_index.md `## Active` section -->
- (none yet — run `solera-write-persona`)

**Active Journeys** ({count}):
<!-- Extracted from journeys/_index.md `## Active` section -->
- (none yet — run `solera-write-journey`)

**Active Narratives** ({count}):
<!-- Extracted from narratives/_index.md `## Active` section -->
- (none yet — run `solera-write-narrative`)

**Active Concepts** ({count}):
<!-- Extracted from concepts/_index.md `## Active` section -->
- Authentication
- Onboarding
- Liquor-search

## Time-bound Axis

| Level | Current | Status |
|-------|---------|--------|
| **Milestone** | mvp | Agreed (target 2026-06-30) |
| **Story** | US-001-google-login | 🔄 In Progress |
| **Action Item** | ACT-002-login-screen | 🔄 In Progress |

## Immutable Axis

**Latest Release**: (none yet)
<!-- Extracted from releases/_index.md `## Released` section -->

## Progress Summary

| Scope | Status |
|-------|--------|
| Concepts active | {N} |
| Active Milestone exit criteria met | {M}/{total} |
| Stories belonging to active Milestone | {complete}/{total} |
| Action Items in current Story | {complete}/{total} |
```

## Quality Criteria

- [ ] Last updated timestamp is accurate
- [ ] Active Concepts count matches `concepts/_index.md`
- [ ] Current Story / ACT match filesystem reality
- [ ] Latest Release entry matches `releases/_index.md`
- [ ] Status values use the 4-state convention (⏳ 🔄 ✅ ⏸️)
