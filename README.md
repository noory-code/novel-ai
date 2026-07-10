# novel-ai

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

The open plugin stack used by Novel. Each package is independently installable, while the four
packages form one coherent workflow through plain files and stable identifiers.

| Plugin | Responsibility | Project data |
|---|---|---|
| [Mashbill](mashbill/) | Visual thinking canvas and Novel artifact publisher | `.noory/novel/` |
| [Solera](solera/) | Work planning, deterministic gates, and execution order | `.noory/solera/` |
| [Proof](proof/) | Append-only decisions referenced by stable ID | `.noory/proof/` |
| [Distill](distill/) | Durable knowledge extraction and recall | `.noory/distill/`, `~/.distill/` |

The packages do not share Python imports. Mashbill publishes artifacts, Solera consumes them by
value, Proof records decisions by ID, and Distill preserves reusable knowledge across sessions.

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

## Development

Each package has its own environment and lockfile:

```bash
cd mashbill  # or solera, proof, distill
uv sync
uv run pytest
```

Read [CLAUDE.md](CLAUDE.md) for repository-wide rules and each package's README for its commands and
runtime contract.

External contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the
[Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md).

## History

This repository was extracted from [`noory-code/noory-ai`](https://github.com/noory-code/noory-ai)
with the commit history of all four package directories preserved. The original repository retains
this project as the `novel-ai/` submodule.

## License

MIT. See [LICENSE](LICENSE) and package-level license metadata.
