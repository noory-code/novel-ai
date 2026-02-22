# Development

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
git clone https://github.com/wooxist/distill.git
cd distill
uv sync
```

## Run

```bash
uv run python -m distill      # Start MCP server
```

## Test

```bash
uv run pytest                 # Run all tests (311 tests)
uv run pytest -v              # Verbose output
uv run pytest tests/test_config.py  # Single test file
```

Tests use `pytest` with `pytest-asyncio` for async test support.

## Project Structure

```
src/distill/
├── server.py                # FastMCP server entry point + 7 tool registrations
├── config.py                # Config loader (DistillConfig, SourcesConfig, OutputsConfig)
├── tools/                   # 7 MCP tool implementations
│   ├── init.py              # One-step onboarding
│   ├── recall.py            # Knowledge search (vector + FTS5 hybrid)
│   ├── learn.py             # Extraction + auto-crystallize
│   ├── profile.py           # Statistics
│   ├── digest.py            # Duplicate detection
│   ├── memory.py            # Promote/demote/delete/crystallize
│   ├── ingest.py            # Markdown/text dir → knowledge store
│   └── helpers.py           # Shared utilities (for_each_scope)
├── extractor/               # Knowledge extraction pipeline
│   ├── parser.py            # .jsonl transcript parsing
│   ├── prompts.py           # LLM prompts (extraction + crystallize)
│   ├── extractor.py         # Orchestration + MCP sampling call
│   ├── crystallize.py       # Rule/skill/agent file generation via MCP sampling
│   ├── rules_reader.py      # Read existing distill-*.md rules
│   └── sampling_error.py    # MCP sampling error wrapping
├── store/                   # Storage layer
│   ├── types.py             # KnowledgeEntry, KnowledgeInput, KnowledgeSource
│   ├── scope.py             # Path resolution + walk-up root detection (project/workspace/global)
│   ├── metadata.py          # SQLite CRUD + FTS5 + meta key-value
│   └── vector.py            # Vector embeddings (fastembed + sqlite-vec)
├── scanner/                 # .claude/ environment scanner
│   ├── scanner.py           # scan_environment() → EnvironmentInventory
│   └── types.py             # EnvironmentItem, EnvironmentInventory, UserConflict
└── hooks/
    └── distill_hook.py      # PreCompact/SessionEnd handler
shared/
└── prompts.md               # Prompt SSOT (must sync with prompts.py)
tests/
├── test_config.py           # Config loading tests
├── test_extractor.py        # callLlm + parseExtractionResponse tests
├── test_extract_knowledge.py # extractKnowledge integration tests
├── test_crystallize.py      # parseCrystallizeResponse + crystallize tests
├── test_parser.py           # Transcript parsing tests
├── test_rules_reader.py     # Rules reader tests
├── test_metadata.py         # SQLite CRUD tests
├── test_vector.py           # FTS5 + vector search tests
├── test_scanner.py          # Environment scanner tests
├── test_distill_hook.py     # PreCompact/SessionEnd hook tests
├── test_tools_*.py          # Tool-level tests (recall, learn, profile, digest, memory)
├── test_ingest.py           # ingest tool tests
└── test_init.py             # init tool tests
```

## Code Style

- Python type hints on all functions (PEP 484)
- Pydantic models for config and data validation
- `from __future__ import annotations` for forward references
- No wildcard imports
- Async functions use `async def` + `await`

## Commit Convention

```
type(scope): message
```

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructuring |
| `docs` | Documentation |
| `test` | Tests |
| `chore` | Config, dependencies |

Examples:
- `feat(tools): add tag filtering to recall`
- `fix(extractor): handle empty transcript`
- `docs: update configuration guide`

## Pull Request Guidelines

1. Tests must pass (`uv run pytest` with zero failures)
2. One purpose per PR
3. Update docs if behavior changes
4. Sync `shared/prompts.md` if `src/distill/extractor/prompts.py` changes
