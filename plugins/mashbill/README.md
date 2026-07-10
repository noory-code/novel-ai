# Mashbill

Mashbill is the headless design engine behind Novel. It helps an AI and a human
structure a service's foundation, actors, services, features, entities, and
relationships as plain local data under `.noory/novel/`.

The package exposes the same core through MCP and HTTP. It does not bundle the
commercial Novel user interface.

## Host installation

Claude Code:

```bash
claude plugin marketplace add noory-code/novel-ai
claude plugin install mashbill@novel-ai
```

Codex:

```bash
codex plugin marketplace add noory-code/novel-ai --ref main
codex plugin add mashbill@novel-ai
```

Gemini CLI installs the complete repository extension, which registers Mashbill
as one of four independent MCP servers:

```bash
gemini extensions install https://github.com/noory-code/novel-ai
```

See the [host support matrix](../../docs/HOST_SUPPORT.md) for the exact package,
hook, and MCP capability boundaries.

## Local development

```bash
uv sync
uv run python -m mashbill --mcp-stdio
```

For HTTP development, run the combined process or the HTTP-only entry point:

```bash
uv run python -m mashbill
uv run mashbill-http
```

## Data and publication

- Active design data: `{project}/.noory/novel/`
- Legacy migration inputs: `{project}/.noory/plot/`, `{project}/.plot/`
- Published integration format: immutable format-F project snapshots and
  service releases
- Git behavior: edits are not auto-committed; explicit tag tools create named
  milestones

Mashbill publishes files that Solera imports by value. It never imports Solera,
Proof, Distill, or private Novel application code.

## Development checks

```bash
uv run pytest
uv run mypy mashbill tests
uv run ruff check mashbill tests hooks
uv run ruff format --check mashbill tests hooks
```

The public product canon starts at [`docs/index.md`](../../docs/index.md).
Package implementation decisions are recorded in
[`docs/DECISIONS.md`](docs/DECISIONS.md).
