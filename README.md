# novel-ai

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The open plugin stack used by Novel. Each package is independently installable, while the four
packages form one coherent workflow through plain files and stable identifiers.

| Plugin | Responsibility | Project data |
|---|---|---|
| [Mashbill](plugins/mashbill/) | Structured service design and Novel artifact publication | `.noory/novel/` |
| [Solera](plugins/solera/) | Work planning, deterministic gates, and execution order | `.noory/solera/` |
| [Proof](plugins/proof/) | Append-only decisions referenced by stable ID | `.noory/proof/` |
| [Distill](plugins/distill/) | Durable knowledge extraction and recall | `.noory/distill/`, `~/.distill/` |

The packages do not share Python imports. Mashbill publishes artifacts, Solera consumes them by
value, Proof records decisions by ID, and Distill preserves reusable knowledge across sessions.
Claude Code and Codex install them as independent plugins; Gemini CLI installs one suite extension
that starts the same four packages as separate MCP servers. See
[Host support and distribution](docs/HOST_SUPPORT.md) for the architecture and capability matrix.

## Install with Claude Code

```text
/plugin marketplace add noory-code/novel-ai
/plugin install mashbill@novel-ai
/plugin install solera@novel-ai
/plugin install proof@novel-ai
/plugin install distill@novel-ai
```

Install only the plugins needed by a project. Mashbill and Solera work independently; Proof and
Distill remain useful standalone.

## Install with Codex

```bash
codex plugin marketplace add noory-code/novel-ai --ref main
codex plugin add mashbill@novel-ai
codex plugin add solera@novel-ai
codex plugin add proof@novel-ai
codex plugin add distill@novel-ai
```

## Install with Gemini CLI

```bash
gemini extensions install https://github.com/noory-code/novel-ai
```

Gemini installs one extension and registers four isolated stdio MCP servers. The
separation keeps failures and dependencies local to each domain package.

## Development

Each package has its own environment and lockfile:

```bash
cd plugins/mashbill  # or plugins/solera, plugins/proof, plugins/distill
uv sync
uv run pytest
```

Read [CLAUDE.md](CLAUDE.md) for repository-wide rules and each package's README for its commands and
runtime contract.

The canonical public design documentation starts at [docs/index.md](docs/index.md). If you used
these plugins from their former `noory-ai/` paths, see [docs/MIGRATION.md](docs/MIGRATION.md).

External contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md).

## History

This repository was extracted from [`noory-code/noory-ai`](https://github.com/noory-code/noory-ai)
with the commit history of all four package directories preserved. The original repository retains
this project as the `novel-ai/` submodule.

## License

MIT. See [LICENSE](LICENSE) and package-level license metadata.
