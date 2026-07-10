# Migration from `noory-ai`

Mashbill, Solera, Proof, and Distill moved from `noory-code/noory-ai` to the public
[`noory-code/novel-ai`](https://github.com/noory-code/novel-ai) repository on 2026-07-10. Their directory
history was preserved.

## Install source

Claude Code marketplace users should register the new repository once and install the required packages:

```text
/plugin marketplace add noory-code/novel-ai
/plugin install mashbill@novel-ai
/plugin install solera@novel-ai
/plugin install proof@novel-ai
/plugin install distill@novel-ai
```

Existing project data does not move. The plugins continue to use their documented `.noory/` locations.

## Source paths

| Former source path | Current source path |
|---|---|
| `noory-ai/mashbill/` | `novel-ai/plugins/mashbill/` |
| `noory-ai/solera/` | `novel-ai/plugins/solera/` |
| `noory-ai/proof/` | `novel-ai/plugins/proof/` |
| `noory-ai/distill/` | `novel-ai/plugins/distill/` |
| private workspace `docs/en/` mirrors | canonical public `novel-ai/docs/` |

The original `noory-ai` repository references this repository as its `novel-ai/` submodule. Development,
releases, issues, and pull requests for these four packages now belong here.

## Repository boundary

The commercial Novel application remains in a separate private repository. Public plugin code and contracts do
not require private source paths. Integration crosses that boundary by MCP/HTTP and committed neutral artifacts.
