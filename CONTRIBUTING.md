# Contributing to novel-ai

Thank you for helping improve Novel's open plugin stack. Contributions from every country,
background, and experience level are welcome.

## Before You Start

- Search existing issues before opening a new one.
- Use an issue to discuss changes that alter data formats, package boundaries, or public behavior.
- Keep changes inside one package unless the change is explicitly a cross-package contract update.
- Do not add imports between `mashbill`, `solera`, `proof`, and `distill`. Their integration is by
  plain files and stable identifiers.

## Development Setup

Each package is an independent Python project:

```bash
cd <package>
uv sync
uv run pytest
uv run mypy <package-or-src>/ tests/
uv run ruff check <package-or-src>/ tests/
```

Read [CLAUDE.md](CLAUDE.md) and any package-local instructions before editing. Mashbill contributors
must also read [`mashbill/CLAUDE.md`](mashbill/CLAUDE.md).

## Pull Requests

- Write code, comments, commits, issues, and pull requests in English.
- Keep each commit focused on one purpose and use `type(scope): description` messages.
- Add or update tests for behavioral changes.
- Update the affected package's version SSOTs and `CHANGELOG.md` for every plugin change.
- State the commands you ran and their results in the pull request description.
- Do not include generated caches, runtime data, credentials, or local editor settings.

Korean text is allowed only where it is the subject of localization behavior, such as the Korean
glossary and localized product copy. Historical decision records remain in their original language
to preserve provenance; new design documentation is English.

## Reporting Problems

Use a GitHub issue for reproducible bugs and feature proposals. Do not disclose a vulnerability in
a public issue; follow [SECURITY.md](SECURITY.md) instead.
