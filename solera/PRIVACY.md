# Privacy Policy

**Solera** is a Claude Code plugin that operates entirely on your local machine.

## Data Collection

Solera does **not** collect, transmit, or store any data on external servers. All data created by Solera (workspace files, progress tracking, team process definitions, handoff documents) remains in your local project directory.

## What Solera Creates Locally

| File | Purpose | Location |
|------|---------|----------|
| `team-process.md` | Team workflow configuration | `{project}/workspace/` |
| `progress.md` | Current work item position | `{project}/` |
| `HANDOFF.md` | Session context for continuity | `{project}/` |
| `_goal.md`, `_epic.md`, `_story.md` | Work item definitions | `{project}/phase/...` |
| Artifact files | Use cases, personas, journeys, concepts | `{project}/phase/.../artifacts/` |

## Third-Party Services

Solera does not integrate with or send data to any third-party services. The only external interaction is through **Git** and **GitHub CLI** (`gh`), which are invoked using your existing local credentials and configuration. Solera does not access, store, or manage these credentials.

## Data Sharing

No data is shared with Anthropic, the plugin author, or any other party. Your project data never leaves your machine through Solera.

## Changes to This Policy

Updates to this privacy policy will be documented in the [CHANGELOG](./CHANGELOG.md) and reflected in the plugin version number.

## Contact

For questions about this privacy policy, open an issue at [github.com/noory-code/noory-ai](https://github.com/noory-code/noory-ai/issues).

---

*Last updated: 2026-03-18 | Solera v2.10.0*
