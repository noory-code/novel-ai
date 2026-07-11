# Contribution Rules

## Commit

```yaml
format: "type(scope): message"
types: [feat, fix, refactor, docs, test, chore]
```

Examples:
- `feat(tools): add tag filtering to recall`
- `fix(extractor): handle empty transcript`
- `docs: update configuration guide`

## Test Check

Tests must pass before commit:

```bash
uv run pytest
```

## Code Style

- Python type hints on all functions (PEP 484)
- Pydantic models for config and data validation
- `from __future__ import annotations` for forward references
- No wildcard imports

## Prompt Changes

Extraction prompt SSOT: `shared/prompts.md`
Inline prompts in `src/distill/extractor/prompts.py` must stay in sync.
