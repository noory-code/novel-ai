# Host support and distribution

Novel AI is one public repository with three official host entry points. The
repository is a marketplace for Claude Code and Codex, and one extension for
Gemini CLI. The four domain packages remain independently installable.

## Why one repository but four MCP servers

An installation bundle and a runtime process solve different problems. One
Gemini extension gives users one install and one update source; four stdio MCP
servers preserve the package boundaries already enforced by the source tree.

| Choice | Result |
|---|---|
| One repository | One public URL, release history, issue tracker, and Gemini install |
| Four plugins | Claude Code and Codex users install only the capabilities they need |
| Four MCP servers | Independent dependencies, startup failures, tool namespaces, and versions |
| Plain-file integration | Packages exchange published files and stable IDs, never sibling imports |

A single monolithic MCP would make every host start all dependencies, couple
unrelated failures, and erase the package independence boundary without adding
any user-facing benefit. It can be reconsidered only if a future host requires
exactly one server process per extension.

## Prerequisites

- Git
- `uv` available on `PATH`
- Python 3.11 through 3.13
- The selected host CLI

The extension and plugin manifests use `uv run --directory ...`, so first use
may create each selected package's environment from its committed lockfile.

## Claude Code

Claude Code's marketplace manifest is `.claude-plugin/marketplace.json`. Each
entry points at one self-contained directory under `plugins/`.

```bash
claude plugin marketplace add noory-code/novel-ai
claude plugin install mashbill@novel-ai
claude plugin install solera@novel-ai
claude plugin install proof@novel-ai
claude plugin install distill@novel-ai
```

The equivalent interactive commands begin with `/plugin`. Install only the
plugins the project uses. Claude Code receives each package's MCP server,
skills, and declared hooks. Distill's automatic session extraction is a
Claude-specific capability because its hook intentionally invokes `claude -p`.

## Codex

Codex's repository marketplace manifest is `.agents/plugins/marketplace.json`.
Each package has its own `.codex-plugin/plugin.json`.

```bash
codex plugin marketplace add noory-code/novel-ai --ref main
codex plugin add mashbill@novel-ai
codex plugin add solera@novel-ai
codex plugin add proof@novel-ai
codex plugin add distill@novel-ai
```

Mashbill and Solera hooks use the shared Claude-compatible hook protocol. Codex
discovers them, but the user must review and trust them once through `/hooks`
before Codex executes them. Proof has no hooks. Distill does not install its
Claude-specific automatic extraction hook on Codex; its MCP provides init,
recall, profile, digest, manual store, and entry management.

## Gemini CLI

Gemini CLI requires `gemini-extension.json` at the repository root. One install
registers all four stdio MCP servers and loads `GEMINI.md` as extension context.

```bash
gemini extensions install https://github.com/noory-code/novel-ai
```

For a local checkout under development:

```bash
gemini extensions link /absolute/path/to/novel-ai
```

Gemini installs the suite as one extension, but each MCP server remains a
separate subprocess. Gemini's `includeTools` allow-list limits Distill to tools
that do not require server-initiated MCP Sampling. Automatic transcript
extraction is therefore not claimed for Gemini; the model can extract reusable
knowledge itself and call `store`.

## Capability matrix

| Capability | Claude Code | Codex | Gemini CLI |
|---|---:|---:|---:|
| Mashbill MCP core | Yes | Yes | Yes |
| Solera MCP core | Yes | Yes | Yes |
| Proof MCP core | Yes | Yes | Yes |
| Distill local store and recall | Yes | Yes | Yes |
| Package skills | Yes | Yes | Extension context only |
| Mashbill/Solera hooks | Yes | Yes, after `/hooks` trust | No |
| Distill automatic transcript extraction | Yes | No | No |
| One-command suite install | Four selected plugins | Four selected plugins | Yes |

“No” means that the repository does not advertise or silently emulate a host
capability that the host does not provide. The underlying plain files remain
portable, so data created from one host is available to the others.

## Official references

- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Codex plugins](https://developers.openai.com/codex/plugins)
- [Codex MCP servers](https://developers.openai.com/codex/mcp)
- [Gemini CLI extension reference](https://geminicli.com/docs/extensions/reference/)
- [Gemini CLI extension releases](https://geminicli.com/docs/extensions/releasing/)
- [Gemini CLI MCP servers](https://geminicli.com/docs/tools/mcp-server/)
