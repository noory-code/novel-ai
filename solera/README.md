# Solera

**A slim harness for AI-driven work.**

Solera plans work into a **tree of WorkItems**, runs deterministic **gates** on
the leaves, and orders the steps an external AI agent executes. It **supervises
rather than builds**: the agent (Claude Code, Codex) does the work; Solera plans
it, hands it over one leaf at a time, and verifies each before moving on.

It works **standalone** over a plain-file `.noory/solera/` workspace, with or
without [Novel](https://github.com/noory-code/noory-ai/tree/main/plot).

## The loop

```mermaid
flowchart LR
  Plan[plan + add: build the tree] --> Next[next: take the next leaf]
  Next --> Work[agent builds it]
  Work --> Gate[complete: run the gate]
  Gate -->|pass| Next
  Gate -->|fail| Stop[stop, escalate to a human]
```

- **WorkItem** — any rung of the tree: `initiative` / `epic` / `story` /
  `action` (`level` is a free label, so depth and taxonomy are not fixed).
- **Leaf** — a WorkItem with a **gate** and no children: one chunk an agent
  finishes in a single context. **Container** — a WorkItem with children and no
  gate: it rolls up their status. Size is an *altitude*, not a number.
- **Gate** — deterministic verification (a test, a build, a content check). Not
  an LLM step — the harness must be able to trust the verdict.
- **Retrospective / Feedback** — neutral, ID-tagged notes a human folds back into
  the design.

## Install (Claude Code)

```
/plugin install solera
```

Then use the skills: **solera-plan**, **solera-run**, **solera-retro**,
**solera-feedback** (start with **solera-help**).

## CLI

The skills drive a small CLI. Run it from the project directory; `.noory/solera/`
lives under it and gates run there:

```bash
solera --root "$PWD" plan "Ship the feature." --level story
solera --root "$PWD" add STORY-001 "Add the endpoint" --gate "pytest -q tests/test_api.py"
solera --root "$PWD" next        # mark the next leaf doing, print its instruction
#   ... agent does the work ...
solera --root "$PWD" complete    # run the gate; pass -> done + rollup, fail -> stop
solera --root "$PWD" status      # pointer + tree-integrity audit
solera --root "$PWD" retro STORY-001 "The plan under-sized the migration step."
solera --root "$PWD" feedback FB-001 "Blocked: the spec is ambiguous about auth."
```

## Design

- **Standalone first.** Solera never imports mashbill and never path-references it.
  When the two connect, they share a neutral format and stable ids *by value*,
  never a code dependency (guarded by `tests/test_independence.py`).
- **Files are the state.** WorkItems, the progress pointer, and notes are
  Markdown with YAML frontmatter under `.noory/solera/`. Identity lives in the
  path; parsers fail fast on a malformed file.
- **Deterministic where it matters.** Planning helpers, the gate-runner, and the
  audit are plain code, not LLM steps, so the harness's mechanics are trustworthy.

Artifact-home rules are in [`docs/ARTIFACT_HOMES.md`](docs/ARTIFACT_HOMES.md).

## Development

```bash
cd solera
uv sync
uv run pytest      # tests
uv run mypy solera/ tests/
uv run ruff check solera/ tests/
```

MIT licensed.
