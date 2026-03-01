# Contributing to Distill

## Development Setup

```bash
cd distill
uv sync
uv run pytest          # run all tests
uv run mypy src/       # type check
uv run ruff check src/ tests/  # lint
uv run ruff format src/ tests/ # format
```

## Commit Format

```
type(scope): description
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples:
```
feat(distill): add workspace scope to recall()
fix(metadata): use parameterized queries to prevent SQL injection
test(crystallize): add rule deduplication tests
```

- Commit messages must be in **English**
- Each commit must pass build + tests on its own
- Each commit contains exactly one purpose

## Pull Request Process

1. Fork the repository and create a branch from `main`
2. Make your changes with tests
3. Ensure all checks pass:
   ```bash
   uv run pytest
   uv run mypy src/
   uv run ruff check src/ tests/
   ```
4. Open a pull request with a clear description of the change

## Architecture

- `tools/` — thin MCP wrappers (no business logic)
- `store/` — SQLite persistence (metadata + vector)
- `extractor/` — knowledge extraction pipeline
- `store/scope.py` — 3-tier scope: global → workspace → project

See [docs/architecture.md](docs/architecture.md) for the full picture.

## Code Conventions

- Python 3.11+, `pathlib.Path` everywhere (never `os.path`)
- Type hints on all functions; mypy strict mode
- Line length: 100 chars (ruff)
- Pydantic v2 for all data models

## Testing

- Add tests for any new functionality in `tests/`
- Tests must pass with `uv run pytest`
- 309 tests currently passing — do not regress

## Reporting Issues

Please open an issue at https://github.com/noory-code/noory-ai/issues
