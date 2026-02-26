# Changelog

All notable changes are documented here, organized by development phase.

---

## [1.1.0] — 2026-02-27

### Security
- **Command injection fix** (`distill_hook.py`): transcript path and session ID are now validated before being passed to subprocess; zombie process cleanup added
- **SQL injection fix** (`metadata.py`): all dynamic WHERE clauses replaced with parameterized queries
- **Path traversal fix** (`ingest.py`, `scanner.py`): file paths validated to stay within allowed directories; silent `OSError` now raises with context

### Fixed
- `MetadataStore` and `VectorStore` connection leaks on exception — `__exit__` now closes connections reliably
- 19 bare `except Exception: pass` sites replaced with `logger.warning(...)` across `digest.py`, `helpers.py`, `ingest.py`, `memory.py`, `store.py`
- JSONL parser now recovers per-line on corrupt input instead of failing the entire transcript
- `extractor.py` truncates at line boundaries, not arbitrary char offsets

### Changed
- `recall()` parameter renamed `type` → `knowledge_type` (avoids shadowing Python builtin); MCP tool updated accordingly
- `min_confidence` now exposed as MCP tool parameter on `recall()`
- Duplicate write logic in `crystallize.py` extracted to `_write_distill_file()` helper
- Scope detection walk-up logic deduplicated in `scope.py` and `helpers.py`

### Performance
- `VectorStore`: batch embedding via `index_many()`, batch commits, redundant WAL PRAGMA removed
- `learn.py`: single-commit batch insert instead of per-chunk commits
- Search join optimized to avoid Python-level N+1 queries

### Dependencies
- `fastembed` pinned to `>=0.7,<0.8` (aligns declared minimum with installed version)
- `ruff` updated to 0.15.2
- `Pillow` updated to 12.1.1 (security patches)

### Tests
- 55 new tests across `test_metadata.py`, `test_vector.py`, `test_parser.py`, `test_ingest.py`, `test_distill_hook.py`, `test_tools_recall.py`

**324 tests passing**

---

## [Phase 2.6] - 2026-02-19

### Added
- **Workspace scope** for monorepo support — 3-tier knowledge hierarchy: `project / workspace / global`
- `detect_workspace_root()` — walks up from CWD to find `.git` root (monorepo boundary)
- `detect_project_root()` — now walks up with PROJECT_MARKERS (`pyproject.toml`, `pubspec.yaml`, `package.json`, `CLAUDE.md`); no longer uses `.git` as project marker
- `workspace` as valid `KnowledgeScope` (`"global" | "project" | "workspace"`)
- `MetadataStore` / `VectorStore` accept `workspace_root` parameter
- `for_each_scope()` helper supports 3-tier iteration: global → workspace → project
- Stepwise `memory("promote")` / `memory("demote")`: moves one tier at a time (`project ↔ workspace ↔ global`)
- `load_config()` accepts `workspace_root` — config priority: project > workspace > global > defaults
- `VALID_SCOPES` in extractor now includes `"workspace"` (previously silently dropped)
- 24 new tests (`test_scope.py` + workspace cases in helpers/memory tests), total **269 tests**

### Fixed
- `extractor.py`: workspace-scoped chunks no longer silently dropped during LLM extraction
- `config.py`: workspace-level `.distill/config.json` now loaded and merged correctly

---

## [Phase 2.5] - 2026-02-18

### Added
- **Python rewrite** — FastMCP + fastembed + sqlite-vec + Pydantic v2 (replaces TypeScript)
- `SourcesConfig` — control knowledge sources (transcripts, rules, skills, agents, dirs)
- `OutputsConfig` — per-type thresholds for rules/skills/agents output
- `ingest(path)` tool — markdown/text directory → LLM extraction → SQLite (mtime-based cache)
- `init()` tool — one-step onboarding: create config, scan environment, ingest configured dirs
- Rule splitting — LLM decides split when `split_threshold_tokens` exceeded
- Agent generation — `outputs.agents.enabled` triggers agent files from 3+ related skills
- SessionStart hook — auto-learn pending extractions from previous session
- 241 tests passing

---

## [Phase 2] - 2026-02

### Added
- **User environment awareness** — `.claude/` scanner for rules, skills, agents inventory
- Full user rule context during extraction (Distill rules + user-authored rules)
- User conflict detection in crystallize — suggests (never auto-edits) user rule conflicts
- `profile()` environment summary — rule/skill/agent counts, token estimation, budget usage
- `UserConflict` type — surfaces conflicts without modifying user files
- 26 new tests (151 total)

---

## [Phase 1.5] - 2026-02

### Added
- **Knowledge routing** — three-tier delivery classification: rule / skill / store-only
- Skill file writer — `SKILL.md` format with `disable-model-invocation: true` frontmatter
- Agent file generation (opt-in via config)
- `downgrade` action in crystallize — demotes rules to store-only
- Config thresholds: `rule_confidence_threshold`, `rule_budget_max_files`

---

## [Phase 1] - 2026-01

### Added
- **Crystallize** — consolidate knowledge chunks into `distill-*.md` rule files via MCP sampling
- Config system — `.distill/config.json` with per-module model selection
- Auto-crystallize threshold — trigger crystallize after N new chunks
- `distill_meta` table — track `last_crystallize` timestamp
- Conflict detection during extraction — inject existing rules as context (single Haiku call)
- 65 tests covering all Phase 1 modules

---

## [MVP] - 2025-12

### Added
- MCP server with 5 tools: `learn`, `recall`, `profile`, `digest`, `memory`
- SQLite + FTS5 knowledge store (global/project dual scope)
- `.jsonl` transcript parser + truncation
- Bidirectional Decision Signal extraction (user↔AI corrections)
- PreCompact/SessionEnd auto-extraction hooks
- Semantic-based knowledge detection (no keyword matching)
- **No API key** — MCP Sampling routes through existing Claude subscription
