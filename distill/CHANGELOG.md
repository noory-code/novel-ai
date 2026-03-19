# Changelog

All notable changes are documented here, organized by development phase.

---

## [1.7.4] — 2026-03-20

### Fixed
- `distill-digest`: fix cross-reference `/distill:memory` → `/distill-memory`
- `distill-memory`: fix cross-reference `/distill:digest` → `/distill-digest`

---

## [1.7.3] — 2026-03-20

### Added
- `user-invocable: true` frontmatter to all 8 skills for explicit /command invocation

---

## [1.7.2] — 2026-03-18

### Fixed
- `README.md`: remove broken link to non-existent `docs/tools.md`
- `README.md`: fix duplicate sentence in FAQ debug instructions
- `docs/development.md`: add missing `store.py` to tools directory tree
- `docs/configuration.md`: correct `auto_crystallize_threshold` default from `0` to `20` (matches `config.py`)

---

## [1.7.1] — 2026-03-18

### Fixed
- **Cross-platform hooks**: replaced hardcoded `.venv/bin/python` with platform-aware path (Windows `Scripts/` vs Unix `bin/`)
- **Cross-platform temp paths**: replaced hardcoded `/tmp/` with `tempfile.gettempdir()`
- **Cross-platform file locking**: replaced Unix-only `fcntl` with platform-aware locking (`msvcrt` on Windows)
- **Hook registration**: added missing `hooks` field in `plugin.json` so PreCompact/SessionEnd hooks are actually loaded

---

## [1.7.0] — 2026-03-18

### Changed
- **Skill rename**: `/distill:recall` → `/distill-recall` (all 7 skills renamed to `distill-*` format)
- **Auto-crystallize enabled by default**: threshold changed from 0 (disabled) to 20 — after 20 chunks accumulate, crystallize runs automatically to generate rules/skills

### Fixed
- **prompts.md SSOT sync**: added missing "agent" delivery classification to match prompts.py

### Removed
- **`/distill` umbrella skill**: replaced by individual `/distill-*` skills
- **`/help` skill**: renamed to `/distill-help` with updated skill list and crystallize workflow docs

---

## [1.6.0] — 2026-03-18

### Added
- **Individual skills**: 7 new slash commands — `/distill:recall`, `/distill:profile`, `/distill:digest`, `/distill:learn`, `/distill:ingest`, `/distill:memory`, `/distill:init`
- Each skill documents parameters, examples, and follow-up workflows

---

## [1.5.1] — 2026-03-17

### Fixed
- Broken `docs/troubleshooting.md` link in README FAQ
- Wrong git clone URL (`wooxist/distill` → `noory-code/noory-ai`) in docs and source
- Outdated version in PRIVACY.md (v1.4.0 → v1.5.0)
- Missing `lock.py` and `helpers.py` in CLAUDE.md architecture diagram
- Incorrect tool count in docs/development.md (7 → 9)
- Outdated test count in CLAUDE.md (316 → 332) and docs/development.md (311 → 332)
- Inaccurate proposal count in README (194 → 192)

---

## [1.5.0] — 2026-03-17

### Added
- **Hybrid search**: `recall()` now combines vector KNN and FTS5 keyword search via Reciprocal Rank Fusion (RRF), improving recall for exact keyword matches that vector search alone may miss
- **Combined relevance ranking**: results ranked by weighted formula (50% search score + 35% confidence + 15% access frequency) instead of confidence-only sorting
- **Hook concurrency control**: file-lock (`fcntl.flock`) prevents multiple hook processes from stacking up when PreCompact and SessionEnd fire in rapid succession
- **Hook status file**: `~/.distill/hook-status.json` provides observability into hook execution (pid, duration, result, errors)
- **Hook status in profile**: `profile()` now shows last hook run details (event, result, duration, error)
- 23 new tests for hybrid search, relevance scoring, lock behavior, status file I/O, and profile hook display

### Changed
- `recall()` output now shows `relevance:` (combined score) instead of `confidence:`
- SQLite `busy_timeout` increased from 5s to 30s for safer concurrent access between MCP server and hook processes

---

## [1.4.0] — 2026-03-17

### Added
- `PRIVACY.md` — privacy policy for marketplace submission
- "How It Works" section in README — explains the extraction and recall flow
- "FAQ" section in README — answers common questions about API keys, debugging, conflicts, offline use, and data storage

### Changed
- `plugin.json`: updated description for marketplace (explains value proposition and "no API key" clearly)
- `help` skill: removed Korean trigger phrases — English-only triggers for marketplace compatibility

---

## [1.3.3] — 2026-03-08

### Fixed
- `hooks.json`: use distill venv python (`${CLAUDE_PLUGIN_ROOT}/../.venv/bin/python3`)
  instead of system `python3` — system python (Xcode) cannot find distill module

---

## [1.3.2] — 2026-03-08

### Fixed
- `hooks.json`: use `python3` instead of `python` in hook commands —
  macOS does not provide `python` binary, only `python3`

---

## [1.3.1] — 2026-03-07

### Fixed
- `distill_hook.py`: replace `uv run` with direct `.venv/bin/python` in MCP config,
  eliminating the uv wrapper process spawned on every PreCompact/SessionEnd hook call

**309 tests passing**

---

## [1.2.0] — 2026-03-01

### Changed
- `init()` no longer installs skills into `.claude/skills/` — skills are provided by the plugin directly
- `init()` no longer registers hooks into `~/.claude/settings.local.json` — hooks are provided by the plugin directly
- `init()` now only creates config and scans environment

**309 tests passing**

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
