# Mashbill contributor guide

Read the repository-level [`CLAUDE.md`](../../CLAUDE.md) first. Its language,
versioning, independence, portability, and verification rules all apply here.

## Scope

Mashbill is the headless Novel design engine. It owns structured project data,
canvas and node operations, local publication, an MCP stdio surface, and an HTTP
API. The commercial Novel user interface is a separate product and is not part
of this package.

Project data lives under `.noory/novel/`. Legacy `.noory/plot/` and `.plot/`
layouts are migration inputs only.

## Canon

- Public product essence: [`docs/VISION.md`](./docs/VISION.md), a packaged mirror
  of the repository's canonical `docs/VISION.md`.
- Current public concepts and behavior:
  [`noory-code/novel-ai/docs`](https://github.com/noory-code/novel-ai/tree/main/docs).
- Implementation decisions: [`docs/DECISIONS.md`](./docs/DECISIONS.md).
- Package architecture: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).
- Wire and node-format implementation notes: [`docs/node-format/`](./docs/node-format/).

When a package document points to the public repository docs, the public docs
are the semantic source of truth. Package documents may describe implementation
mechanics but must not redefine shared concepts.

## Runtime modes

```bash
# MCP stdio only: used by Claude Code, Codex, and Gemini CLI manifests
uv run python -m mashbill --mcp-stdio

# Combined MCP/HTTP development process
uv run python -m mashbill

# HTTP-only entry point
uv run mashbill-http
```

The stdio plugin mode must never bind the HTTP port. Host manifests must launch
with `--mcp-stdio` and resolve the package through the host's plugin-root
variable.

## Change rules

- Preserve the headless boundary: do not add private app paths, local fixtures,
  browser-only verification agents, or dependencies on a sibling repository.
- Keep every other Novel AI package independent. Integration with Solera uses
  format F files; Proof links are stable identifiers; Distill remains separate.
- Prefer the narrow mutation surface. `update_node` is the clobber-safe path for
  one node; `update_canvas` intentionally replaces a complete canvas document.
- File formats and migrations require round-trip and compatibility tests.
- MCP tool additions require a pinned tool-catalog test and direct behavior tests.
- Public plugin changes require a version bump and dated `CHANGELOG.md` entry.

## Verification

```bash
uv sync
uv run ruff format --check mashbill tests hooks
uv run ruff check mashbill tests hooks
uv run mypy mashbill tests
uv run pytest
```

Run `python3 ../../scripts/validate_repository.py` from this directory, or
`python3 scripts/validate_repository.py` from the repository root, after any
manifest, marketplace, package-path, or public-documentation change.
