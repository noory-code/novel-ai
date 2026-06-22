# Changelog

## [7.6.0] — 2026-06-23

### Added

- **`solera import <vs_dir> --label <label>` CLI** — the pipeline's entry step is
  now driven from the command line. It copies a published Plot release (a
  format-F `vS` service bundle plus the `vP` snapshot it is `based_on`) into
  `specs/{label}/`, the same `import_release` the library already exposed.
  Surfaced by a Plot↔Solera dogfood: every other stage (`plan` / `add` /
  `next` / `complete` / `repin`) had a CLI, but importing a release was
  library-only — the `repin` tests even stubbed it on disk. The user wires in
  the path Plot published; Solera never reaches into Plot (format-f.md §6 /
  04-pipeline). Bad path / unsupported `format_f_version` / duplicate label
  fail cleanly (`error:`, exit 1). Suite 111 green, mypy + ruff clean.

## [7.5.0] — 2026-06-22

### Added

- **`solera repin <old> <new>` CLI** (INT-f) — the re-pin flow is now driven from
  the command line, not just library functions. It loads two imported releases'
  `elements` (`specs/{label}/service/manifest.json`), runs the ID-diff, and
  prints which work items go **stale** (realize a `changed` slug → reopen
  candidate) vs **escalate** (realize a `removed` slug → orphaned, a human
  decides). Read-only by default; `--apply` reopens the stale set
  (`status → todo`). Escalated items are never auto-reopened — the
  human-in-the-loop gate (04-pipeline). New: `intake.load_imported_elements`.
  Suite 109 green, mypy + ruff clean.

## [7.4.0] — 2026-06-22

### Added

- **`realizes` link + re-pin flow** (INT-f) — completes the Plot↔Solera loop on
  the Solera side:
  - `WorkItem.realizes: list[str]` — the format F slug(s) an item builds (e.g.
    `feature/login`), connected *by value* (no Plot import). Back-compatible:
    older item files without it parse as `[]`. CLI: `add --realizes <slug>`
    (repeatable).
  - `repin.propose_repin(ws, old, new)` — read-only: maps an ID-diff onto the
    work items that realize the changed (→ stale) / removed (→ escalate) slugs;
    unchanged slugs' work is left alone (progress preserved).
  - `repin.reopen_items(ws, ids)` — the status mutation, applied only after a
    human approves the proposal (human-in-the-loop gate, 04-pipeline).
  Suite 105 green, mypy + ruff clean.

## [7.3.1] — 2026-06-22

### Added

- **format F version guard** (INT-1c) — `intake.import_release` now rejects a
  bundle whose `format_f_version` is not `SUPPORTED_FORMAT_F_VERSION`, so a Plot
  that bumps the format without Solera following fails loudly instead of
  mis-reading the contract. Pinned in lock-step with Plot's
  `format_f.FORMAT_F_VERSION` (cross-repo contract guard, both sides tested).

## [7.3.0] — 2026-06-22

### Added

- **format F intake — the Solera "read" half of the Plot↔Solera contract**
  (INT-3). New `solera/intake.py` reads **format F** (a neutral published-bundle
  format, `repos-plot/docs/specs/format-f.md`) without importing Plot or
  path-referencing its tree (R8 — `test_independence.py` still green):
  - `import_release(ws, source_vs_dir, label)` copies a frozen `vS` service
    bundle + its `based_on` `vP` slice into `specs/{label}/` (immutable →
    immutable), so a story's `source: specs/{label}` points only inside Solera's
    own folder — Solera runs with or without Plot.
  - `diff_releases(old, new)` — the deterministic ID-diff (changed / removed /
    added) that drives re-pinning on a re-publish. Pure function, never an LLM.
  - `Workspace.specs_dir` added.
  Tests synthesize bundles by hand to prove the independence. Suite 100 green.

## [7.2.0] — 2026-06-21

Minor — hooks (D2-6): the automation layer that keeps the loop from drifting.

### Added

- **SessionStart hook** (`hooks/session_start.py`) — orients a new session in the
  active workspace: surfaces the in-progress leaf (its goal and gate) and the next
  command to additionalContext, so a session never starts blind to where the loop
  left off. No-op outside a Solera workspace.
- **Stop hook** (`hooks/stop.py`) — if a leaf is left `doing` at session end,
  prints a reminder to run `solera complete` (or write feedback). Advisory only —
  it never blocks the stop, so it cannot trap the loop.

Both are pure-stdlib, cross-platform, and read the workspace files directly (no
import of the solera package, so they run even when nothing is installed).

## [7.1.0] — 2026-06-21

Minor — decision-type leaves (D2-3).

### Added

- **`solera-decide` skill** — how to run a leaf that *decides* rather than
  *builds* (a tech stack, an architecture, a convention). The agent surfaces
  options and escalates; the **human** chooses and records the decision in
  [cairn](https://github.com/noory-code/noory-ai/tree/main/cairn); the leaf gates
  on `cairn check --about <topic>`. No new Solera code — a decision leaf is a
  normal WorkItem whose gate is a cairn command, so the two tools stay decoupled
  (no import; the link is a topic slug by value).

## [7.0.1] — 2026-06-21

Docs — artifact-home rule corrected. `docs/ARTIFACT_HOMES.md` (and the
`artifacts.py` docstring) split the old "design → Plot" line into **conceptual
design → Plot** and **technical design → the repository** (code-near), and add
**decisions → cairn** (the append-only decision log). Plot defines the *what*,
not the *how* or the tech stack; those live in the repo and cairn.

## [7.0.0] — 2026-06-21

Major — **recursive WorkItem tree**. Solera now plans work at any altitude
(initiative / epic / story / action), not just two levels. This resolves the
original "work-item size" question: size is an *altitude*; the leaf stays
one-context + one-gate, everything above is rollup.

Breaking: the `.noory/solera/` model changed. `Story` and `Action` are replaced
by a single `WorkItem`; storage is a flat `items/{id}.md` set with each item's
`children` list reconstructing the tree; `progress.md` now holds a single `item`
pointer; retrospectives live at `retros/{id}.md`; artifacts at `artifacts/{id}/`.

### Added / changed

- **`WorkItem`** — one node type. `level` is a free label so depth and taxonomy
  are not hard-coded. Invariant: a leaf has a gate and no children; a container
  has children and no gate; an item may have neither yet, never both.
- **Supervisor walks the tree** — `find_next_open` dives to the first open leaf
  (resuming a stuck `doing` leaf before any `todo`); `complete` rolls completion
  up the ancestors (a container is done when all its children are).
- **Planning at any level** — `create_item(level, goal, gate=…, parent=…)` with
  level-prefixed ids (INIT/EPIC/STORY/ACT-NNN).
- **Audit** checks tree integrity — missing children, multi-parent, cycles,
  dangling pointer.
- **CLI** — `plan --level …`, `add <parent> … --level … --gate …`; `complete`
  and `next` operate on the active leaf.

### Removed

- `Story`, `Action`, and their parsers/paths. `run_action_gate` → `run_item_gate`.

## [6.0.1] — 2026-06-21

Patch — one-active-Action invariant + operational spec.

### Fixed

- **`next` no longer skips a stuck Action.** When a gate fails, the Action holds
  in `doing`; previously `find_next_todo` looked only for `todo`, so the next
  `next` would silently start a later Action and abandon the stuck one.
  `find_next_open` now resumes a `doing` Action before starting any `todo` —
  one active Action at a time (`solera/supervisor.py`).

### Added

- **`docs/SPEC.md`** — how the slim core works, with mermaid diagrams (loop,
  Action state machine, file layout) and the invariants.
- End-to-end coverage of the blocked path (gate fails → feedback note → Action
  holds → `next` re-offers it) in `tests/test_scenario.py`.

## [6.0.0] — 2026-06-21

Major — **rebirth**. Solera is rebuilt from scratch as a slim **harness**:
it plans work and runs gates, but never builds anything itself. The old mindmap
canvas, three-axis model, four canvases, MCP server, React viewer, and VSCode
extension are removed. Breaking: the `.solera/` / canvas data model and the
`solera_mcp` server no longer exist.

### Added

- **File-convention core** (`solera/formats.py`, `solera/workspace.py`). A
  `.noory/solera/` workspace of plain Markdown files: Story and Action with YAML
  frontmatter, identity in the path (Story = directory, Action = file stem),
  fail-fast parsers (`FormatError`) with strict pydantic models.
- **Deterministic gate-runner** (`solera/gate.py`). One command, tokenised and
  run with `shell=False`; exit 0 passes, anything else fails, with stdout/stderr
  captured. Timeout / binary-not-found reported as `passed=False`, never raised.
- **Supervisor** (`solera/supervisor.py`). Finds the next open Action, hands the
  agent an instruction, runs the gate, advances on pass or stops (Action stuck in
  `doing`) for a human on fail. The `progress.md` pointer tracks the active Action.
- **Planning helpers** (`solera/planning.py`). Deterministic id allocation and
  Story/Action creation, so generated files always satisfy the format.
- **Retrospective + feedback notes** (`solera/formats.py`). Neutral ID-tagged
  notes; the `about` tag is optional so standalone Solera (no published spec)
  still produces valid notes.
- **Artifact homes** (`solera/artifacts.py`, `docs/ARTIFACT_HOMES.md`). One home
  per output; process artifacts stage under a Story tagged (about / from), not
  versioned; a light misplacement guard.
- **Workspace audit** (`solera/audit.py`). Cross-file referential-integrity guard.
- **CLI** (`solera/cli.py`) + **skills** (`solera-help`, `solera-plan`,
  `solera-run`, `solera-retro`, `solera-feedback`). The agent-facing surface:
  `python -m solera <command>`.
- **R8 independence guard** (`tests/test_independence.py`). No source file imports
  a Plot module or path-references the plot tree — the connection is by value only.

### Removed

- `solera_mcp/`, `viewer/`, `vscode-extension/`, the old `skills/`, `commands/`,
  `docs/`, and `tests/`. The MCP server is now a later Plot-integration concern,
  not part of the standalone core.

## [5.2.1] — 2026-06-15

Patch. R8 independence build guard.

### Added

- **R8 independence build guard** (`tests/test_r8_independence.py`). AST-checks
  every `solera_mcp/` module for imports of the Plot app (viewer / Tauri shell)
  or any sibling plugin, and bans `src-tauri` path literals. Mirrors
  `plot/tests/test_r8_independence.py` — the MIT-plugin / proprietary-app
  licence boundary is defended by this structural guard, not by file layout
  (noory-ai overhaul R8 / Track 2.2). Covers the Python MCP package; Solera's
  own React `viewer/` + `vscode-extension/` are separate build artefacts.

## [5.2.0] — 2026-06-11

Minor. R9 — Solera workspace data lives under `.noory/solera/` instead of
`.solera/` so every noory plugin (plot / distill / evonest / solera) shares
ONE `.noory/` dotfolder per project. Plot's canvas data and Solera's
workspace data can sit side-by-side without colliding. Completes Track 2.3
of the overhaul.

### Changed

- `solera_mcp.workspace.resolve_solera_root` resolves `.noory/solera/`
  first. A legacy `.solera/` migrates lazily on first read (one
  `shutil.move`, same volume). When both layouts exist (half-migrated /
  user-restored), the new root wins and the legacy dir is preserved for
  the user to reconcile — never merged blindly.
- The migration carries the user's `.gitignore` intent: a project that
  ignored `.solera/` keeps ignoring the data after the move
  (`# Solera workspace data (R9 location)\n.noory/solera/\n` appended).
  Projects that tracked their data on purpose get no ignore added (no
  invented policy). Same pattern as evonest v1.1.1.
- VSCode extension (`workspaceCheck.ts`) — adds an `r9` finding kind for
  projects already on `.noory/solera/`; legacy `.solera/` still reports
  as `v4` and the Python server auto-migrates it on first read.
- Viewer empty-state copy (`PlanCanvas.tsx`) + module docstrings updated.

### Notes

- v3 `workspace/` fallback unchanged (deprecated; same warning; same drop
  target).
- 133 server tests green; mypy + ruff clean; viewer + vscode-extension
  tsc clean. `tests/test_noory_migration.py` pins the contract
  (prefer-new, lazy-move, no-clobber, gitignore intent carry, no invented
  ignore, v3 untouched).

## [5.1.0] — 2026-04-19

Minor. The canvas becomes the primary authoring surface: click a field
on a Role / Persona / Journey / Narrative / Concept to edit it in place,
"+ add" popovers on Identity and each node spawn new entities without
leaving the canvas. Skills remain for bulk / scripted operations.

### Added

- **Unified CRUD HTTP surface** for every Living-axis entity:
  - `POST   /api/role` · `PATCH /api/role/{id}`
  - `POST   /api/persona` · `PATCH /api/persona/{id}`
  - `POST   /api/journey` · `PATCH /api/journey/{id}`
  - `POST   /api/narrative` · `PATCH /api/narrative/{id}`
  - `POST   /api/concept` · `PATCH /api/concept/{id}` (widened from
    parent-only)
  Each endpoint enforces a per-kind allowed-key list, validates
  cross-references (role exists, walks resolves to a Role,
  about_roles ≥ 1, parent chain has no cycles, Persona role matches
  journey.walks when used in walked_by, etc.), and writes via
  atomic helpers in `solera_mcp/writers.py`. Kebab-case `id` is
  required on POST; duplicates 409.
- **EditableText / EditableTextarea primitives** in
  `viewer/src/edit/`. Tiny `useInlineEdit` hook drives an
  idle / editing / saving / error state machine with optimistic-like
  UX: successful saves dismiss to idle, failed saves keep the draft
  and surface the server error so the human can retry. Enter commits
  on single-line, Cmd/Ctrl+Enter commits on textarea, Esc cancels,
  blur commits.
- **Actors canvas inline edit** (`canvases/ActorsLabels.tsx`):
  - Role: name + description editable in place; `+ add` popover
    creates sub-Role / Journey the role walks / Persona archetype /
    Narrative about this Role.
  - Persona: name + identity paragraph editable.
  - Journey: name + trigger + outcome editable; `+ narrative`
    popover attaches a new Narrative with in_journey set.
  - Narrative: statement editable.
  - Identity hub: `+ role` popover creates a top-level Role.
- **Plan canvas inline edit** (`canvases/PlanLabels.tsx`):
  - Concept: name + intent + the lens-dependent sub-text
    (current_design or current_shape depending on the active lens)
    editable in place.
  - Identity hub: `+ concept` popover creates top-level Concepts.
  - "+ concept" on every Concept node creates a child Concept.
- 10 new typed API client functions in `viewer/src/api.ts` —
  `patchRole` / `createRole` and siblings for every kind. Each has
  a TypeScript-typed Patch interface mirroring the server's
  allowed-key set so mistyped fields fail at compile time.

### Changed

- `patchConcept` now accepts every allowed Concept field
  (`name`, `status`, `intent`, `current_design`, `current_shape`,
  `horizon`, `parent`) instead of just `parent`.
- Dead code removed: `ActorsCanvas.tsx` dropped ~200 LOC of
  read-only `render{Kind}Label` renderers; `PlanCanvas.tsx`
  dropped the old `IdentityLabel` / `renderConceptLabel` / unused
  `truncate` helper.
- `PlanCanvas` and `ActorsCanvas` now accept `projectPath` +
  `onMutated` props; `App.tsx` wires `onMutated` to a graph
  re-fetch so successful inline edits update the view without a
  WebSocket round-trip.

### Tests

- `tests/test_writers.py` (13 Python cases): round-trip
  create + patch across every kind; preservation of untouched
  sections under patch; bullet-list and Steps table rewrites;
  frontmatter `parent: null` deletion.
- `tests/test_api_endpoints.py` (16 Python cases): happy paths
  for every POST + PATCH, cross-ref rejections (unknown role,
  missing walks, empty about_roles, self-parent), duplicate-id
  409, invalid-kebab 400, unknown-key 400.
- `tests/useInlineEdit.test.ts` (7 viewer cases): hook state
  transitions, custom-equality skip, rejected-save draft
  retention.
- `tests/EditableText.test.tsx` (5 viewer cases): click → edit,
  Enter commits, Esc cancels, error banner on reject, disabled
  blocks edit.

### Totals

188 tests green — 125 Python (+29) + 63 viewer (+14). mypy + ruff
clean. `npm run build` clean (bundle +~30kb for the edit
primitives + popovers).

### Known limitations / out of scope

- **Bullet-list and Steps-table inline editors** — Persona
  `goals` / `pains` / `triggers` / `quotes`, Narrative
  `acceptance_cues`, and the Journey Steps markdown table are
  still edited via skills only. Add/edit/remove UIs for these
  ship in a later minor.
- **Drag-and-drop reparent** — side-panel dropdown (ConceptPanel
  `ParentSelect`) remains the reparent surface. Drag still only
  moves node positions.
- **Multi-select / bulk edit** — a future cycle.

---

## [5.0.0] — 2026-04-19

Major version. Breaking schema change: `Role` is a new Living-axis
entity, `Persona` becomes its optional archetype, the Service canvas is
renamed to **Actors** and reshaped around an Identity-centric Role
tree. v4.x workspaces need the one-shot
`solera-migrate-v4-to-v5` skill to upgrade.

### Why

banas and similar projects kept using "Persona" for both *structural
user classes* (admin / fan / hero / 3rd-party) and *individual
archetypes* ("30대 성덕 Alice"). Those are two different levels of
description, and conflating them made the Service canvas semantics
ambiguous — there was no way to draw the structural shape of an
audience first and deepen individual verticals later. v5 gives each
its own entity.

### Added

- **`Role` entity** (Living axis). Fields: `id`, `name`, `status`,
  `description`, optional `context`, optional `parent` (sub-role
  chain), `integrity[]`. Full status grammar (active / deprecated /
  archived) identical to Concept. Stored under `.solera/roles/*.md`.
- **`solera-write-role` skill** (1.0.0) with four modes
  (create / update / deprecate / archive), parent cycle / self /
  archive validation, Moment 1 collaboration rule.
- **`solera-migrate-v4-to-v5` skill** (1.0.0) — BLOCKING, idempotent,
  per-Persona AskUserQuestion workflow that promotes Personas to
  Roles, splits `about:` into `about_roles` + `about_personas`,
  re-stamps `walks:` semantics, and writes
  `.solera/MIGRATION-v4-to-v5.md` with every decision.
- **`RolePanel`** in the viewer showing description / context / parent
  / sub-roles / personas / journeys / narratives + integrity banners
  for broken_parent_ref and inactive_parent_ref.
- **Integrity flags**: `missing_role`, `broken_role_ref`,
  `inactive_role_ref` (Persona); `broken_walks_ref`,
  `inactive_walks_ref` (Journey now resolves against Roles);
  `missing_about_roles`, `broken_about_role_ref`,
  `broken_about_persona_ref`, `legacy_about_field` (Narrative);
  `broken_parent_ref`, `inactive_parent_ref` (Role).

### Changed (BREAKING)

- **`Persona.role`** is now a required field. Every Persona must
  declare its parent Role. Missing `role:` surfaces as
  `missing_role` integrity flag; running
  `solera-migrate-v4-to-v5` is the supported path to populate it.
- **`Journey.walks`** semantically references a Role id (was
  Persona id in v4). A new `Journey.walked_by: list[str]` captures
  optional Persona archetypes for concrete cases.
- **`Narrative.about`** split into `Narrative.about_roles: list[str]`
  (1+ required) and `Narrative.about_personas: list[str]`
  (optional). Readers tolerate the legacy `about:` key by coercing
  it to `about_roles` and raising `legacy_about_field` — the
  migration skill clears this.
- **Service canvas → Actors canvas.** `ServiceCanvas.tsx` renamed to
  `ActorsCanvas.tsx`. `WorkspaceLens`: `"service"` →
  `"actors"`. Tab label reads **Actors**. Layout is Identity-
  centric: Roles form the first ring, sub-roles nest outward,
  Journeys sit one radius further, Narratives one radius beyond
  their Journey (or in their Role's wedge), Personas are small
  satellites next to their Role.
- **`solera-write-persona`** (2.0.0): `role:` parameter required in
  create; prerequisite flips from "≥1 Persona" to "≥1 Role".
- **`solera-write-journey`** (2.0.0): `walks` resolves against
  Roles; `walked_by` parameter added.
- **`solera-write-narrative`** (2.0.0): `about` split into
  `about_roles` / `about_personas`.
- **`solera-init`** (4.0.0): seeds `.solera/roles/` +
  `roles/_index.md`; v5 vs v4 vs v3 vs v2 detection with routing to
  the correct migration skill. Fresh-setup wording updated.
- **`solera-help`** (4.0.0): Living-axis table exposes
  `solera-write-role`; Quick Start walks through Role → Persona
  (optional) → Journey → Narrative → Concept.
- **`axes-and-status.md`**: Role added to the three-axis table,
  mermaid diagram updated with the new cross-axis relations
  (persona.role, journey.walks→Role, journey.walked_by,
  narrative.about_roles, narrative.about_personas), Role status
  grammar row, ownership column header renamed Actor to avoid the
  Role-entity collision.

### Migration

Run `/solera-migrate-v4-to-v5` inside any v4 workspace. The skill
makes a single atomic commit once the human approves the per-file
decisions. Existing `_v2-archive/` workspaces go v2 → v4 → v5 by
chaining `solera-migrate-v2` then `solera-migrate-v4-to-v5`.

### Tests

Total up to ~147: 96 Python (85 pre-Role + 11 new Role/integrity)
and 51 viewer (49 pre-Role + 2 new ActorsCanvas tests) green; mypy
and ruff clean; vite build clean.

### Known limitations (carried over)

- **VSCode AI-host MCP registration** still not wired up — deferred.
- **v5.1 editable canvas** (in-browser CRUD for Role / Persona /
  Journey / Narrative) is explicitly out of scope for v5.0 and ships
  next.

---

## [4.2.0] — 2026-04-19

### Changed (canvas redesign — resolves founding-principle violation)

- **Service canvas is now a Persona-centric radial mindmap.** The v4.0
  three-column swimlane (Persona | Journey | Narrative) violated the
  founding "UI must be mindmap graph" principle and was flagged in the
  v4.0.0 *Known limitations #2*. The new layout:
  - Each Persona is the hub of its own radial cluster.
  - Its Journeys radiate on the inner ring (radius 220) distributed
    evenly clockwise from 12 o'clock.
  - Its Narratives sit on the outer ring (radius 400). Anchored
    Narratives (`in_journey`) fan out around their Journey's angle;
    loose Narratives fill the angular midpoints between Journeys.
  - Multiple Personas → multiple clusters on a 3-per-row grid (900px
    spacing). Orphan Journeys + fully-loose Narratives get a dedicated
    row below the clusters so the integrity banners stay easy to find.
  - User drag positions persist via `layout.nodes` — identical contract
    to PlanCanvas, so the two canvases share one mental model.
- Service-canvas nodes dropped their hard-coded `sourcePosition` /
  `targetPosition` hints. React Flow now picks the best edge routing
  for the current angle, which is the only reasonable behavior when
  there's no "inbound side" in radial placement.
- Node widths trimmed 20–40px (Persona 260–300, Journey 280–320,
  Narrative 240–300) because radial wants slightly more compact cards
  to read as a ring rather than a list.

### Behavioural breaking (no API break)

- Any `map-layout.json` positions persisted under the old 3-column
  coordinate system will simply render at those coordinates — the user
  can drag to reorganize. No migration skill needed. New clusters
  without stored positions get the new radial layout by default.

### Known limitations (carried over)

- **VSCode AI-host MCP registration** is still not wired up — explicitly
  deferred. Claude Code plugin users are unaffected.
- The v4.0.0 *Known limitations #2* (ServiceCanvas swimlane) is now
  **RESOLVED** by this release.

### Verification

Visual verification via Playwright against a synthetic 3-Persona /
4-Journey / 5-Narrative workspace:
- Multi-Journey Persona renders the canonical radial mindmap shape.
- Single-Journey Personas render with one radial spoke (geometrically a
  chain — the mindmap shape emerges with density, as expected).

166 tests green (85 Python + 49 viewer + 32 extension). mypy + ruff
clean. Viewer build clean.

---

## [4.1.1] — 2026-04-19

### Refactored

Three source files exceeded the project's 500-LOC SoC warning. They have
now been decomposed by responsibility with the public surface preserved
via facade re-exports — no caller needs to change its imports.

- **`viewer/src/SidePanel.tsx`** (736 → 128 LOC): split into
  `panels/IdentityPanel`, `panels/ConceptPanel`, `panels/PersonaPanel`,
  `panels/JourneyPanel`, `panels/NarrativePanel`, and `panels/helpers`
  (shared Section / StatusChip / MetaRow / IntegrityBanner atoms).
  Largest remaining panel is `ConceptPanel.tsx` at 244 LOC (bundles
  `ParentSelect` / `SideToggle` with the Concept body because they only
  apply to Concepts).
- **`solera_mcp/graph.py`** (748 → 141 LOC): split into `models.py`
  (Pydantic + status literals), `parsing.py` (markdown/frontmatter/table
  helpers), `readers.py` (per-entity `read_*` functions, 420 LOC — the
  largest remaining file), `writers.py` (`update_concept_frontmatter`,
  `read_layout`, `write_layout`), and `integrity.py`
  (`annotate_cross_ref_integrity`). `graph.py` now owns only
  `build_graph` plus re-exports.
- **`solera_mcp/server.py`** (728 → 150 LOC): split into `workspace.py`
  (path / port helpers), `broadcast.py` (`BroadcastHub`),
  `api_endpoints.py` (basic HTTP handlers), `concept_propose.py` (the
  `POST /api/concept/propose-from-narrative` endpoint with its
  Moment-1 guardrails), `http_app.py` (Starlette composition), and
  `mcp_tools.py` (FastMCP + `get_map` + `open_map`). `server.py` keeps
  the uvicorn/asyncio entry points and re-exports the old names.

Some leading-underscore helpers were promoted to public names where
they're now imported across files (e.g. `_status_from_icon_or_text` →
`status_from_icon_or_text`, `_graph_for` → `graph_for`,
`_stub_concept_body` → `stub_concept_body`). No functional change.

### Tests

166 green, unchanged from v4.1.0 (85 Python + 49 viewer + 32 extension).
mypy + ruff clean. Viewer build clean.

### Known limitations (carried over)

- VSCode AI-host MCP registration is still not wired up — deferred.
- Service canvas is still a three-column swimlane, not a mindmap.
- The 500-LOC SoC warning is now resolved across all Python and viewer
  source files; the largest file is `solera_mcp/readers.py` at 420 LOC.

---

## [4.1.0] — 2026-04-19

### Added

- **Data-integrity flags on Living-axis entities.** `Journey.integrity` and
  `Narrative.integrity` are surfaced by the MCP graph parser whenever the
  underlying file is malformed: `missing_walks` (Journey without a `walks:`
  Persona id), `missing_about` (Narrative with an empty or absent `about:`
  list), and `broken_in_journey_ref` (Narrative pointing at a Journey that
  does not exist). Invalid references are preserved — not coerced to null —
  so the canvas can show the human what they typed.
- **Repair banners in the side panel.** Journey and Narrative views now show
  a red banner when any integrity flag is set, each with a copyable repair
  command (e.g. `/solera-write-journey mode=update journey_id=foo`) so the
  human can jump straight back to the correct skill.
- **Stronger orphan / integrity visuals on the Service canvas.** Nodes with
  integrity issues get a thick red border, rose background, and a header
  pill naming the concrete cause (`no walks`, `no about`, `unknown journey`)
  with a hover tooltip. Replaces the near-invisible small orange tag.
- **Next-step hints at skill completion.** `solera-write-persona`,
  `solera-write-journey`, and `solera-write-narrative` now print a concrete
  "Next:" line on `create`, pointing the human at the next skill in the
  Living-axis flow (or the Service canvas's "Propose as Concept" action for
  Narratives).
- **Plan-canvas empty state.** When `.solera/concepts/` is empty, the Plan
  canvas now shows an explicit prompt directing users to
  `solera-write-concept` or the Service canvas's Propose action — matching
  the Service canvas's existing empty state pattern.
- **Canvas loading / save / connection feedback.** A spinner + "Loading
  graph…" replaces the silent grey "loading…" text; the header now shows a
  pulsing socket-status dot (`connecting…` / `live` / `reconnecting…` /
  `offline`) and a transient save indicator (`saving…` → `saved` flash →
  idle).
- **WebSocket reconnection with exponential backoff.** `openGraphSocket`
  retries 1s → 2s → 4s → … up to 30s on abnormal disconnects and emits
  per-attempt status callbacks. Normal close codes (1000 / 1001) and
  explicit rejections (1003 / 1008) stop retrying.

### Changed

- **Separate `layout_changed` broadcast.** The MCP file watcher now
  classifies changes as `graph` (any `.md` or `concept-graph.json`) or
  `layout` (pure `map-layout.json` saves). The broadcast hub emits
  `{"event": "graph_changed"}` or `{"event": "layout_changed"}` accordingly;
  viewers only run a full graph re-fetch on the former, keeping canvas
  selection and side-panel state alive when the user drags a node.
- **Side-panel mutation feedback.** `ParentSelect` now shows an inline
  spinner while saving, retains the failed choice in a disabled state with a
  retry button on error, and marks the select with `aria-invalid` on
  failure. The "Propose as Concept" submit button gains a visible loading
  state (spinner + darker background + `aria-busy`).
- **WCAG AA contrast on tab labels and section titles.** Active-tab accents
  and `SectionTitle` tone classes moved from 500-shades (2.1:1–4.2:1 on
  white) to 700-shades (5.3:1–7.6:1). Inactive-tab text moved from
  `slate-500` (4.55:1) to `slate-700` (9.59:1). Markdown link color moved to
  `indigo-700`.
- **`solera-help`** (`3.1.0`): Living-axis table lists `solera-write-persona`
  / `-journey` / `-narrative`; Quick Start now walks users through drawing a
  Persona → Journey → Narrative before Concepts; all residual "v3" language
  removed.
- **`solera-init`**: description and title drop the "v3" marker; completion
  checklist points at the v4 gate keys explicitly.
- **`solera-write-persona`**: description no longer uses the unexplained
  phrase "service composer".

### Fixed

- Malformed Living-axis files no longer become silent orphans — they render
  prominently and point the human at the exact skill + flag to repair.

### Tests

166 tests green — 85 Python (added 5 integrity + 2 layout-event broadcast
tests), 49 viewer (added integrity-banner coverage), 32 extension unchanged.

### Known limitations (carried over from 4.0)

- VSCode AI-host MCP registration is still not wired up — deferred per the
  current roadmap.
- Service canvas is still a three-column swimlane, not a mindmap.
- `solera_mcp/graph.py`, `solera_mcp/server.py`, and `viewer/src/SidePanel.tsx`
  still exceed the project's 500-LOC SoC warning. Split planned for a later
  minor — the integrity and feedback work in this release intentionally
  kept surgical rather than restructuring.

---

## [4.0.0] — 2026-04-19

### Unified distribution (product consolidation)

Solera has always been one product. Previously the code shipped as three sibling directories — `solera/` (skills, v3.5.0), `solera-map/` (MCP + canvas viewer, v0.0.1), and `solera-map-vscode/` (VSCode extension, unpublished) — each with its own version line and manifest. That split was an implementation artifact, not a product boundary, and it forced users to install multiple pieces to get the whole thing.

v4.0 consolidates all three under a single `solera/` directory on a single version line:

- **Claude Code users**: `/plugin install solera` now brings skills + the MCP canvas server + viewer in one shot. No second install step.
- **VSCode users**: install **"Solera"** (publisher `noory-code`) from Marketplace — the extension bundles the same MCP server and React viewer and spawns them automatically. (See item #1 in the "Known limitations" section below regarding AI-host MCP registration.)
- **Data format** `.solera/` is shared. Switching between Claude Code and VSCode requires no data migration.

### Naming changes

- VSCode extension: `solera-map-vscode` → `solera`. Marketplace ID `noory-code.solera`. Command palette entry: **Solera: Open Canvas**.
- Python package: `solera-map` → `solera-mcp`. Module: `solera_map` → `solera_mcp`. Scripts: `solera-map` → `solera-mcp`, `solera-map-http` → `solera-mcp-http`.
- Configuration keys (VSCode): `soleraMap.command` → `solera.command`, `soleraMap.port` → `solera.port`.
- The internal name `solera-map` is retired. It was product-confusing ("a map OF solera? solera's map layer?") — the canvas is just Solera's UI, not a separate layer.

### Breaking

- **Workspace layout moved from `workspace/` to `.solera/`**. All Solera-managed data (identity, personas, journeys, narratives, concepts, milestones, stories, releases, catalog, team-process) now lives under a single dotfolder, hidden from default IDE / file-tree views (matching `.git/`, `.vscode/`, `.idea/` conventions). Top-level `progress.md` and `HANDOFF.md` move to `.solera/progress.md` and `.solera/HANDOFF.md`.
- Existing v3.x projects must run the new **`solera-migrate-workspace-to-dotsolera`** skill to migrate. Idempotent, git-tracked, single commit. Solera reads both layouts during the transition; the `workspace/` fallback will be dropped in a future minor.
- Former `solera-map` MCP-plugin users: uninstall `solera-map`; `/plugin install solera` now includes the MCP server. Same `.solera/` data — no data migration.
- `solera-init` now detects v4 (`.solera/`), v3 (`workspace/` with `concepts/` or `milestones/`), or v2 (`workspace/` with `initiative/` or `phase/`) and routes to the appropriate migration skill.
- `solera-migrate-v2` now produces v4 (`.solera/`) output directly — no need to chain through `solera-migrate-workspace-to-dotsolera` for v2 projects. Skill version bumps to `2.0.0`.
- v3 catalog `persona/` and `journey/` types are no longer first-class catalog entries. `solera-migrate-v2` parks any existing v2 catalog persona/journey artifacts under `_unclassified/persona-from-v3-catalog/` and `_unclassified/journey-from-v3-catalog/` for human re-homing via the new write skills.

### Added

- **Living-axis expansion** — three new entity types upstream of Concepts:
  - **Persona** (`solera-write-persona`) — who the service is for. Identity / Goals / Pains / Triggers / Quotes / Channels / Related cross-links. Status grammar `active`/`deprecated`/`archived`, identical to Concept.
  - **Journey** (`solera-write-journey`) — sequence of steps a Persona walks. Trigger / Steps (markdown table) / Outcome / Related. `walks` is required and points at exactly one active Persona.
  - **Narrative** (`solera-write-narrative`) — "As a / I want / so that" (or JTBD / scenario). Statement / Context / Acceptance Cues / Related. May `proposes:` Concepts. Distinct from Solera's existing Time-bound `Story` work item — Narratives are upstream of Concepts, not work units.
- All three follow the same Living-axis status grammar as Concept (`active`/`deprecated`/`archived`); see `axes-and-status.md`.
- **New cross-axis relations**: `walks` (Journey → Persona, required, exactly one), `about` (Narrative → Persona, 1+, required), `in_journey` (Narrative → Journey, 0..1, optional), `proposes` (Narrative → Concept, 0+, optional).
- **`solera-init` Step 3** seeds the new entity directories (`personas/`, `journeys/`, `narratives/`) and their `_index.md` files automatically. Six index files exist after `solera-init` (was three).
- **`solera-init` initial `progress.md`** lists Active Personas / Journeys / Narratives alongside Active Concepts.
- **New skill `solera-migrate-workspace-to-dotsolera`** — single-commit, idempotent, BLOCKING-confirmation migration for v3 projects to relocate `workspace/` and top-level `progress.md`/`HANDOFF.md` into `.solera/`.

### Changed

- **`solera-publish-artifacts`**: catalog destinations under `.solera/catalog/published/` no longer recognize `persona/` or `journey/` (those are first-class Living-axis files now). Existing v4 projects can still write design artifacts of other types (`service-map/`, `use-case/`, `domain-model/`, etc.) unchanged.
- **`solera-migrate-v2`**: Workflow rewritten for v4 destination. Adds `v2_source_path` (default `{project_path}/workspace`) and `solera_path` (default `{project_path}/.solera`) parameters; legacy `workspace_path` references in the skill's body are interpreted as `solera_path`. Step 7 final report points users to `solera-write-persona` / `solera-write-journey` / `solera-write-narrative` for re-homing v3 catalog artifacts.
- **`solera-handoff`** writes to `.solera/HANDOFF.md` instead of project-root `HANDOFF.md`.
- Plugin description and keywords updated to reference the new entity types.

### Canvases

Two real canvas components, four lenses:

- **Service** (new) — Personas, Journeys, Narratives. Upstream of Plan.
- **Plan** — Concept mindmap, bilateral layout around Identity.
- **Build** / **Live** — currently share the Plan canvas with lens-driven styling; dedicated components deferred to a later minor.

### Tests

158 automated tests ship with v4.0:

- **78 Python** (skill validation + graph + server unit + E2E subprocess over real TCP)
- **48 viewer** (ServiceCanvas layout + SidePanel + api.ts, vitest + jsdom)
- **32 extension unit** (csp + workspaceCheck + ServerProcess, vitest)
- **Integration scaffold** for VSCode extension via `@vscode/test-electron` (requires one-time Gatekeeper approval on macOS Sequoia+)

### Known limitations (honest)

1. **VSCode AI-host MCP registration is NOT wired up yet.** The extension spawns the MCP server and its Webview consumes it over HTTP, but `contributes.mcpServerDefinitionProviders` is not declared — so Copilot / Claude extension / Gemini inside VSCode cannot auto-discover this MCP. To be added in a patch release; earlier drafts of this CHANGELOG overstated the current state.

2. **Service canvas layout is swimlane, not mindmap.** The founding principle "UI must be mindmap graph" (human+AI co-draw for cognition) is honored by the Plan canvas but not the Service canvas (3-column layout: Persona | Journey | Narrative). Under review — may change in a later minor if the swimlane choice is judged to drift from product identity. **[Resolved in 4.2.0: Persona-centric radial.]**

3. **3 files exceed the project's 500-LOC SoC warning**: `solera_mcp/graph.py` (748), `solera_mcp/server.py` (720), `viewer/src/SidePanel.tsx` (736). Split planned for v4.1.

### Notes

The Living/Time-bound/Immutable axis model is unchanged — Personas, Journeys, and Narratives join Identity and Concepts on the existing Living axis, preserving the MECE-by-time-relationship structure. There is no new axis.

The Workflow-as-SSOT rule continues to apply: each new entity template carries a `## Workflow` section that the supervisor reads. The "Propose as Concept" canvas action creates a stub Concept whose `# Intent` is explicitly flagged "needs human review per solera-write-concept Moment 1 rule" — preserving the Moment 1 collaboration constraint. The AI never finalizes Concepts on the human's behalf.

---

## [3.5.0] — 2026-04-18

### Added

- **Concept hierarchy** — Concepts can now declare a `parent` (another active Concept they sit inside). Top-level Concepts represent the project's largest regions (products, shared foundations, surfaces); children nest without depth limit, so a product decision like "Community" can later hold "Reactions → Like", "Comments → Threaded", etc. Flat Concepts remain fully valid — the field is optional and backwards-compatible with every existing workspace.
- **`axes-and-status.md` → Cross-axis Relations** gains a `parent: Concept → Concept` row plus a dedicated subsection that specifies cycle/self-parent/archive rules (cycles rejected, self-parenting rejected, parent must be `active`, children become orphaned when parent archives).
- **`solera-write-concept` → Create mode** now resolves `parent` after Current Design: AI proposes a candidate from vocabulary overlap / explicit human reference / product-surface signals, human accepts or overrides (including explicit top-level). The Human–AI Protocol codifies: AI may propose `parent`, AI may not write it silently.
- **`solera-write-concept` → Update mode** adds `Parent` to the edit menu so a Concept can be re-homed (or promoted to top-level) without rewriting Intent. Setting parent to `null` removes the frontmatter line rather than persisting `parent: null`.
- **`solera-write-concept` → Wrap-up** rebuilds `concepts/_index.md` as an **indented tree** (2 spaces per depth) instead of a flat list, so the hierarchy is visible without opening the viewer. Orphaned children (parent missing / non-active) surface with a `⚠️ orphan` marker.
- **Concept template** (`concept-template.md`) includes a commented `parent` placeholder so hand-authored Concepts know the field exists.
- **New error handling** in `solera-write-concept`: unknown parent, inactive parent, self-parent, parent cycle — each halts with a specific message.

### Notes

This is a minor bump because the new field is optional and every existing workspace keeps parsing unchanged. The downstream `solera-map` plugin depends on this field for its Plan canvas tree rendering; prior to this release it was reading a field Solera didn't officially know about.

`solera-write-concept` skill version bumps to `1.1.0`.

---

## [3.4.20] — 2026-04-18

### Fixed

- **Defect 55 (surfaced during live banas migration Step 4)** — `_story.md` files without any YAML frontmatter. Nine banas v2 Stories (P2/G1/03-app-onboarding DS-001/002/003, US-001/002/003/004, TS-001-admin-user-management; P2/G1/04-clean-architecture TS-001/002) were authored without frontmatter at all. The previous Step 4 "patch frontmatter" rule assumed a frontmatter block already exists — frontmatterless files silently escaped patching, so the relocated Story had no `story_id`, `story_name`, `contributes_to`, or `belongs_to` in v3. Added an explicit branch:
  - No frontmatter present → **inject a new block** at the top with `title` (from first Markdown heading, else `{new_id}: {story_name}`), `story_id`, `story_name`, `contributes_to`, `belongs_to`, `status`, `created` (from earliest git commit date, else today).
  - Frontmatter present → existing add/replace behaviour.
  Also spelled out the full v2→v3 status mapping (`completed`/`in-progress`/`pending`/`on-hold`/`cancelled`) and added `value/`, `status/`, `origin/` to the list of v2-only tag prefixes to strip.

---

## [3.4.19] — 2026-04-18

### Fixed

- **Defect 52 (surfaced during live banas migration)** — Step 2.1 non-standard identity BLOCKING prompt only offered three destinations: `keep at workspace/identity/`, `_unclassified/`, or `skip`. In the real banas migration, `tone-and-manner.md` turned out to be a genuine brand-voice rule that belonged at `.claude/rules/tone-and-manner.md`, not inside any identity or catalog destination. The procedure had no way to promote an identity file into a rule / skill / other Claude Code artifact. Added **option (3) move to a custom target path** — user provides a `{project_path}`-relative path (e.g. `.claude/rules/tone-and-manner.md`), validated to end in `.md` and stay within the project. Makes identity classification flexible enough for real vaults that mixed identity, rules, and skills into one folder.

---

## [3.4.18] — 2026-04-18

### Notes

Marketplace refresh tag to close the **v3.4.1–v3.4.17 simulation hardening cycle**. No behavioural changes vs. v3.4.17 — this bump exists so downstream projects that were on v1.9.6 / v2.12.0 see a clearly higher patch number when running `/plugin update solera@noory-ai`, and so the "final" tag in this cycle is unambiguous before the real `solera-migrate-v2` run against a live v2 project.

Total simulation cycle summary (v3.3.0 baseline → v3.4.18):
- 35 thought-experiment iterations (25 general + 10 reading actual v2 project files).
- 51 defects identified; ~42 fixed; remaining intentionally noted as no-issue / YAGNI / preserved-by-archive.
- Step 6 (init) re-designed to direct-write (v3.4.0 structural refactor).
- `solera-migrate-v2` reshaped across Steps 1, 2.1, 2.2, 2.3, 3, 4, 7 — ready for real-project execution with safety branch and per-step commit trailers.

---

## [3.4.17] — 2026-04-18

### Fixed

- **Iteration 35 defect 51 — Step 7 progress.md v3 template SSOT link**. Reading banas' actual project-root progress.md (v2 format with Phase/Goal/Epic/Story 4-level table) made clear the rewrite needed a target-shape reference, not just a v2 input. The canonical v3 progress.md template already lives in `solera-init/SKILL.md` Step 3 (with `## Living Axis` / `## Time-bound Axis` / `## Immutable Axis` sections). Step 7 now explicitly points to it so AI does not re-invent the shape each migration.

---

## [3.4.16] — 2026-04-18

### Fixed

- **Iteration 31 defect 49 — Step 2.2 team-process.md gate patch converts v2 text-based `checks`**. Reading banas' actual `workspace/team-process.md` revealed that v2 projects store `workflow_gates.*.checks` as a **list of plain strings** (e.g. `- "Domain test 작성되어 있고 통과"`). v3 expects `checks[]` to be a list of `{type, params}` objects, and a v3 skill parsing the raw v2 list would either error or silently ignore the gate. Step 2.2 now converts v2 text-based checks: merge every string into the gate's `description`/`condition` field (joined with ` · `), remove the v2 `checks` key, and log a Manual Task in MIGRATION-NOTES.md to upgrade to typed checks later. v3 write-story's Gate execution already falls back to text evaluation of `condition` when `checks` is absent, so the gate remains enforceable after the downgrade.

- **Also clarified**: other team-process.md sections (`process_stages`, `tech_stack`, `conventions`, `tools`, `custom_rules`, project-specific keys like banas' `package_paths`) are preserved as-is — v3 skills either consume them or ignore them, but never reject the file for unknown keys.

---

## [3.4.15] — 2026-04-18

### Fixed

- **Iteration 30 defect 47 — Story discovery missed non-`US`/`TS` prefixes and intermediate-directory variance**. Real banas v2 uses `DS-001-profile-db/` (Design Stories — custom prefix) and mixes two directory shapes: `epics/02-build-auth/stories/TS-001/` (with intermediate `stories/` dir) AND `epics/01-user-auth/US-001-login-screen/` (no intermediate dir). The v3.4.8 regex matched only `US`/`TS` with a required `stories/` wrapper. Banas would have **silently dropped all DS Stories and every Story living directly under an Epic** — losing their ACT files too.
  - Regex relaxed to `^([A-Z]{1,4})-\d{3}(-.*)?$` (accepts any 1–4 letter prefix).
  - Discovery path glob handles both shapes (with and without `stories/`).
  - A **single BLOCKING prompt** per unknown prefix asks the human: keep as-is / convert to TS / convert to US / provide per-prefix mapping. Decision applies to all Stories with that prefix and is recorded in MIGRATION-NOTES.md.

---

## [3.4.14] — 2026-04-18

### Fixed

Iteration 29 read an actual v2 Story (`workspace/phase/2026-P1-foundation/goals/G0-infrastructure/epics/02-build-auth/stories/TS-001/_story.md`) and exposed two more Step 4 issues that only surface when the title is non-ASCII:

- **Defect 45 — ID leaks into slug when title starts with ID**. Banas titles are written as `"TS-001: 익명 인증 시스템"` — the ID prefix is included in the title string. The slug-derivation pipeline (whitespace → `-`, strip non-ASCII) would produce `ts-001` from that string, which a naive validity check accepts (valid kebab-case, 3-50 chars) even though it is just the ID repeated and carries zero semantic meaning. Step 4 now (a) strips `^{old_id}[:\s\-]*` from the title before slug derivation and (b) rejects any slug that equals the `{old_id}` lowercased, forcing the Story into the `pending_names` batch prompt.
- **Defect 46 — v2-only frontmatter fields leak into v3 Story files**. Banas stories carry `aliases: [TS-001, 스토리]` plus v2 Obsidian-style tags (`phase/p1-foundation`, `implements/g1-tech-foundation`, `vision/g1-tech-foundation`, `relates-to/persona-bana`). These have no v3 meaning. Step 4's frontmatter patch now removes them. `feature/*` tags are preserved because they form the audit trail for Step 3's clustering decisions.

---

## [3.4.13] — 2026-04-18

### Fixed

- **Iterations 26–27 defect 44 — batch resolve Story names before relocation**. Reading banas's actual `_epic.md` exposed that ID-only Stories with Korean/non-ASCII titles would each trigger a separate BLOCKING prompt — banas has 27+ Stories, most with Korean titles, which would mean 20+ consecutive BLOCKING prompts in the middle of Step 4. UX was unworkable. Added a **pre-pass**: derive `{story_name}` deterministically where possible (directory suffix or ASCII-decodable title), collect every unresolved Story into a `pending_names` list, then run a **single batch BLOCKING prompt** at the end with all Stories at once. The human pastes one name per line; blank lines fall back to ID-only with a MIGRATION-NOTES warning; invalid kebab-case rejects the whole batch with line-specific flags. Moves Step 4 from "N BLOCKING prompts per migration" to "at most one batch prompt per migration".

---

## [3.4.12] — 2026-04-18

### Fixed

- **Iteration 25 defect 42 — primary-feature derivation final fallback**. The v3.4.7 rule said "extract from directory suffix → else first `feature/*` tag" but gave no explicit behaviour when both fail (directory name has no extractable token AND the Epic has no `feature/*` tags at all). Banas does not trigger this because every Epic has both a sensible directory name and multiple tags, but an imported v2 vault without disciplined tagging could. Step 3 now runs a BLOCKING prompt per affected Epic asking the human for a one-word kebab-case primary feature (or `skip`), instead of silently dropping the Epic from Concept proposals.

---

## [3.4.11] — 2026-04-18

### Fixed

- **Iteration 24 defect 41 — Step 7 progress.md rewrite source**. The rewrite step assumed the v2 progress.md was inside `workspace/` and therefore archived by Step 1 at `_v2-archive/workspace-original/progress.md`. Real v2 projects (banas) keep progress.md at the project root, not inside workspace, which means Step 1 never archives it (Freeze only touches `workspace/` direct children) and Step 7 would have had nowhere to read the v2 content from. Added an explicit two-location lookup:
  1. Archived workspace copy (if it was inside `workspace/`).
  2. Project-root copy (if it lived outside `workspace/`) — used in place, overwritten by the v3 rewrite.
  3. Neither → start from scratch.
  
  The v3 rewrite is always written to `{project_path}/progress.md` (v3 convention) regardless of where the v2 copy lived.

Iterations 22 (Step 5 pre-v3 synthetic milestone) and 23 (Step 6 release v2-final) were walked through against banas with no defects surfacing — included here only to close the simulation log.

---

## [3.4.10] — 2026-04-18

### Fixed

Banas simulation surfaced two more Step 3 gaps:

- **Iteration 21 defect 38 — initiative scan missed `goals.md`**. Step 3's scan list for `_v2-archive/workspace-original/initiative/*/` only named `roadmap.md` and `README.md`. Real projects (banas) keep a third overview file `goals.md` at the same level, and the fixed-filename list missed it. Replaced with a glob over every `.md` directly inside each `initiative/*/` so future overview files (e.g. `north-star.md`, `priorities.md`) are picked up automatically.

- **Iteration 21 defect 40 — Goal-without-Epic handling**. Real projects have Goals that have not yet been decomposed into Epics (banas G3-vertical, G4-growth). The existing cluster heuristics operated on Epics only — such Goals would have been silently dropped from Concept proposals even though their `_goal.md` files were read during the scan phase. Added explicit handling: the Goal itself becomes a Concept candidate with primary feature from its frontmatter `feature/*` tag (or title fallback), marked `confidence: low` and `origin: goal-only` so the human sees why Epic-level evidence is absent.

Defect 39 (subdir-level loose files like `phase/README.md` not migrated to catalog) was evaluated and intentionally left alone — those files remain preserved in the archive, so there is no data loss; the human can promote them manually if needed.

---

## [3.4.9] — 2026-04-18

### Fixed

Banas simulation exposed that Step 3 and Step 4 were not wired to each other — Step 4 was re-inferring clustering signals that Step 3 had already decided, risking Stories landing on Concepts the human did not actually approve:

- **Iteration 19 defect 36 — Step 4 `contributes_to` inference now consumes Step 3 output.** The Epic's primary feature (derived in Step 3) maps to an approved Concept, and that Concept becomes the default `contributes_to`. Secondary features surface in the batch-report's rationale as additions the human can pick during sample review. Sibling `TS-*` Stories inherit the parent Epic's default unless their body says otherwise. Stories whose Epic primary feature had no approved Concept are tagged `contributes_to: []` and flagged.

- **Iteration 20 defect 37 — Step 4 "Prefix by Epic" ID strategy now uses `{epic_primary_feature}`**. Previously the strategy said `US-auth-001` as an example without defining how `auth` was chosen from a directory named `02-build-auth`. Rule: drop the numeric prefix and the verb (build/setup/app), keep the suffix which is the primary feature (`02-build-auth` → `auth`; `09-build-design-system` → `design-system`). Matches Step 3 clustering so Stories in the `authentication` Concept all share the `US-auth-*` ID prefix.

---

## [3.4.8] — 2026-04-18

### Fixed

- **Iteration 18 defect 35 — `solera-migrate-v2` Step 4 Story discovery + rename**. Real v2 projects (banas) mix two Story-directory shapes: `TS-003` (ID-only) and `TS-003-partner-role` (ID + name). The previous discovery pattern `US-NNN-*`/`TS-NNN-*` required a trailing dash + name, so ID-only directories would have been silently skipped — losing Stories from the migration without warning. The rename step also would have produced trailing-dash directory names (`TS-003-`) when name was empty. Fixes:
  - Discovery pattern is now the regex `^(US|TS)-\d{3}(-.*)?$`, matching both shapes.
  - Rename now derives `{story_name}` from the directory suffix when present, else infers a slug from `_story.md`'s title/heading, else runs a BLOCKING prompt asking the human for a 1–3-word kebab-case name.
  - Target path is always `{new_id}-{story_name}` — never `{new_id}-` with empty name.

---

## [3.4.7] — 2026-04-18

### Fixed

- **Iteration 17 defect 34 — `solera-migrate-v2` Step 3 multi-tag Epic handling**. Real v2 projects (banas) carry multiple `feature/*` tags per Epic (e.g. `02-build-auth` declares `feature/auth`, `feature/admin`, `feature/profile`, `feature/search`, `feature/social`). The existing Step 3 heuristic said "same `feature/*` tag → same Concept candidate" without saying which tag wins when an Epic has several — so clustering would be effectively random. Added an explicit three-step primary-feature derivation rule:
  1. Extract from the Epic directory name suffix (`02-build-auth` → `auth`, `09-build-design-system` → `design-system`) — deterministic.
  2. Fallback to the first `feature/*` tag, flagged in rationale.
  3. All other `feature/*` tags become `secondary_features` on the Epic entry — visible in candidate rationale but do not split the Epic.

  Critical for real-project clustering quality; without this rule, banas' 16+ multi-tag Epics would have produced incoherent Concept proposals.

---

## [3.4.6] — 2026-04-18

### Fixed

Walk-through simulation of `solera-migrate-v2` against an actual v2 project (banas — 4 phases, 5 goals, 16+ epics, 27 stories, a separate `published/` Obsidian vault with subtree content in `concept/liquor/` and `schema/liquor/`) exposed two migrate-v2 defects:

- **Iteration 16 defect 32 — subtree handling in Step 2.3**. The catalog merge assumed `{type}/` directories contain flat `.md` files. Real v2 Obsidian vaults often store nested content (`concept/liquor/foo.md`). Added an explicit rule: move the entire subtree via `git mv`, preserving nested structure; run collision detection per entry when the destination is not empty. Never flatten.
- **Iteration 16 defect 31 — journey collision in Step 2.1**. Journey files can exist in both `workspace/identity/journeys/` and `extra/*/identity/journeys/`. The Step 2.1 journey-move flow had no collision handling (Step 2.3's collision detection runs only inside the catalog-merge loop). Step 2.1 now explicitly defers to the Step 2.3 filename-collision BLOCKING prompt when a journey filename already exists at the destination.

---

## [3.4.5] — 2026-04-18

### Fixed

- **Iteration 10 defect** — the tooling catalog's `{project_slug}` row now spells out what to show the user when normalisation fails (e.g. a project name written in non-ASCII collapses to empty after stripping). Previously Step 6 just said "halt and ask"; the user could see a prompt without understanding why. The prompt text now explains that slugs feed file names and trigger phrases, so ASCII-only is required.

---

## [3.4.4] — 2026-04-18

### Fixed

- **Iteration 9 defect** — `solera-init` Step 6 interrupt-handling rule now covers both user-interrupt and `AskUserQuestion` tool errors: both route to `deferred` with reason `"interrupted during Step 6"` and continue. Prevents an unlikely-but-possible silent skip if the tool layer raises.

---

## [3.4.3] — 2026-04-18

### Fixed

- **Iteration 8 defect** — `solera-init` Step 6 now runs a catalog integrity check before prompting the user: if the tooling catalog defines the same candidate name twice (under any `project.type` section), Step 6 halts with a clear error. Prevents duplicate prompts and ambiguous decision records when the catalog is extended carelessly.

---

## [3.4.2] — 2026-04-18

### Fixed

- **Iteration 7 defect** — `solera-init` Step 6 assumed the tooling catalog file was always present. If `docs/reference/tooling-catalog.md` is missing, unreadable, or obviously truncated, Step 6 now halts with a clear error pointing to the file instead of silently falling back or skipping. Fail-fast on SSOT loss.

---

## [3.4.1] — 2026-04-18

### Fixed

- **Iteration 6 defect** — `solera-init` Step 6 procedure specified how to handle a verify-after-read failure but had no branch for the write step itself raising an exception (permission denied, disk full, invalid path). Added an explicit `catch → demote to declined with reason → continue` rule so a single candidate's write error never halts the whole Step 6 run.

---

## [3.4.0] — 2026-04-18

### Changed (structural — `solera-init` Step 6 / tooling catalog)

Five rounds of end-to-end thought experiments against the v3.3.0 Step 6 design surfaced 22 defects. The most severe — the Step 6 → `solera-edit-agent` proxy flow — was architecturally incorrect: it would have triggered a nested interactive interview every time, breaking init UX, and the catalog's frontmatter defaults had no path to reach the meta-skill's Input schema. v3.4.0 replaces the proxy flow with a **direct-write** design and rewrites both files to close the full defect set.

#### `docs/reference/tooling-catalog.md`

- **Pre-baked specs**. Each candidate now carries its full frontmatter, system-prompt body, CLAUDE.md row, Kind (`agent`|`skill`), Role (one-line), and recorded-evidence spec — everything Step 6 needs to write the file directly. `test-runner` is now **FULLY SPECIFIED** with a green/`[Read, Bash, Grep]` agent body including Core Responsibilities, Process, Quality Standards, Output Format, and Edge Cases. `pr-reviewer` and `{project_slug}-convention-guard` remain marked `(placeholder — coming soon)` — Step 6 proposes them but routes any decision to `deferred`.
- **Variable substitution rules table** clearly separates Step-6-substituted variables (`{project_name}`, `{project_slug}`, `{test_command}`, `{today}`) from runtime placeholders the agent/skill fills during execution (`{count}`, `{file:line}`, …). Runtime placeholders must be left verbatim.
- **`{project_name}` noise-word guard**: if the derived name is `src`, `workspace`, `repo`, `app`, `root`, or `workbench`, Step 6 halts and prompts the user for a real name. `{project_slug}` has an explicit 6-step normalisation (unicode-NFC → lowercase → replace `_`/whitespace with `-` → strip non-`[a-z0-9-]` → collapse consecutive `-` → strip edges) and must match `^[a-z][a-z0-9-]*[a-z0-9]$`, 3–50 chars.
- **Test command conflict resolution**: when multiple language evidence rows match (monorepo case), Step 6 MUST ask the user via AskUserQuestion which command to bake in. No silent priority-order pick.
- **Integrity rule**: only `(FULLY SPECIFIED)` entries are eligible for creation. `(placeholder — coming soon)` entries are always routed to `deferred` with reason `"catalog entry not yet fully specified"`.

#### `solera-init/SKILL.md` Step 6

- **Direct-write flow**: Step 6 no longer invokes `solera-edit-agent` / `solera-edit-skill`. It substitutes catalog variables and writes `.claude/agents/{name}.md` (or `.claude/skills/{name}/SKILL.md`) directly. The meta-skills remain for manual, interview-driven creation.
- **Idempotency on re-run**: if `team-process.md` already has a `tooling:` block, Step 6 asks the user `(1) skip Step 6` / `(2) only offer candidates not already listed` / `(3) restart from scratch`. Existing `created` entries are never silently rewritten.
- **Per-candidate prompt loop** with a primary AskUserQuestion (`create now` | `decline` | `defer`, with `create now` omitted for placeholder entries) and a follow-up AskUserQuestion for the reason on decline/defer. Interrupted prompts → `deferred` with reason `"interrupted during Step 6"`.
- **Pre-write guards**: `mkdir -p` the parent dir; check for target-path collision and offer skip / overwrite / write-as-new; record each outcome with a discriminating `note` on the `created` / `declined` entry.
- **CLAUDE.md fallback matrix**: no CLAUDE.md → create it with a minimal header + `## Agents` table; section absent → append section + header + row; section exists as a markdown table → replace row with same agent name, else append; section exists as non-table content → append a new table block below preserving existing content, and record a note.
- **Candidate status header parsing** pins to the exact regex `^### \d+\. .+ (agent|skill)  \((FULLY SPECIFIED|placeholder — coming soon)\)$`. Ambiguous/missing headers halt Step 6 with a clear error pointing to the catalog file.
- **Failure isolation**: any single candidate's failure (test-command unresolvable, file write failed, etc.) demotes that candidate to `declined` with a specific reason and continues to the next candidate — Step 6 never halts the whole run on one candidate.

### Metadata

- `solera-init` metadata.version `3.1.0` → `3.2.0`.
- Plugin version `3.3.1` → `3.4.0`.

### Why minor (not patch)

The catalog and Step 6 procedure are semantically re-designed from the v3.3.0 shape. Behaviour on user-facing invariants (no candidate created without explicit consent, decisions recorded in `team-process.md`) is preserved, but the internal contract between init and meta-skills changed. Treating this as a minor bump makes the shift visible to anyone tracking Solera's release notes.

---

## [3.3.1] — 2026-04-18

### Changed (docs only)

- **README.md** updated to reflect the v3.0.3–v3.3.0 releases:
  - `solera-publish-artifacts` row in the Skills table now notes it is not user-invocable and runs automatically at Story Wrap-up — clearer than the previous awkward `"(automatic hook)"` entry in the trigger column.
  - `solera-init` row now lists the full output set including `team-process.md` (kickoff interview result) and project-tailored agent/skill proposals (Step 6, v3.3.0), linking to `docs/reference/tooling-catalog.md`.
  - Reference section gained three entries:
    - `docs/reference/axes-and-status.md` (SSOT for three-axis model + status values, v3.0.3)
    - `docs/reference/self-verification-schema.md` (canonical schema for every skill's `assets/self-verification.md`, v3.0.3)
    - `docs/reference/tooling-catalog.md` (Step 6 candidates, v3.3.0)

No code, skill, or behaviour changes.

---

## [3.3.0] — 2026-04-18

### Added

- **`solera-init` Step 6 — Project-Tailored Tooling** (optional, BLOCKING). After the kickoff interview (Step 5) captures `project.type` and writes `team-process.md`, Step 6 proposes project-specific agent/skill candidates, lets the human multi-select via a BLOCKING prompt, and invokes the meta skills (`solera-edit-agent` / `solera-edit-skill`) to create the selected ones. No candidate is ever created without explicit user confirmation. Every proposal ends in exactly one of `created` / `declined` / `deferred`, recorded in `team-process.md` under a new `tooling:` block.

- **`docs/reference/tooling-catalog.md`** (SSOT for Step 6). Defines:
  - The **Evidence patterns** table (Glob patterns for Python / Node / TypeScript / Flutter / Go / Rust / Docker / CI / migrations / tests / architecture rules).
  - Three `project.type: software` candidates with full specs — **propose-when** rule, role description, meta-skill used, frontmatter defaults (`model`, `color`, `tools`):
    1. **`test-runner` agent** (green, `[Read, Bash, Grep]`) — maps detected lockfile to the right test command (`uv run pytest` / `npm test` / `flutter test` / `go test ./...` / `cargo test`).
    2. **`pr-reviewer` agent** (blue, `[Read, Grep, Glob, Bash]`) — codifies the project's review rubric as a reusable agent.
    3. **`{project}-convention-guard` skill** — wraps the project's `architecture_rules` + `custom_rules` into a pre-commit / pre-PR checklist skill.
  - Placeholder candidate sets for `marketing` / `design` / `content` / `other` (YAGNI — extended only when real usage warrants).
  - Extension rules so future candidates stay consistent.

### Changed

- `solera-init` metadata.version bumped `3.0.0` → `3.1.0` (minor — new user-facing feature).
- `team-process.md` template gains a `tooling:` block at the bottom with commented examples for `created` / `declined` / `deferred`.
- `solera-init` Completion Checklist gains an item covering Step 6.

### Notes

- **No existing workspace is affected** — Step 6 runs only during fresh `solera-init`. Existing projects can opt in by manually invoking `solera-edit-agent` or `solera-edit-skill` with the catalog as reference.
- **MVP scope**: only `project.type: software` ships with a non-empty candidate set today. This is deliberate. Extend `docs/reference/tooling-catalog.md` when real projects surface the need for marketing/design/content/other-type candidates.

---

## [3.2.0] — 2026-04-18

### Added

- **`solera-edit-agent` gets progressive-disclosure references.** Deep guidance no longer lives inline in SKILL.md — two new files in `skills/solera-edit-agent/references/` are loaded on demand:

  - **`references/system-prompt-design.md`** (217 lines) — the six-section structure (role → responsibilities → process → quality → output → edges), three Solera-common patterns (Analysis / Generation / Team-lead), a length budget, and a Solera-specific mistakes table. Distilled from the official `plugin-dev/skills/agent-development/references/system-prompt-design.md` with the two Solera layers added: **AI-First banned phrases** and **explicit `condition → action`** format for Process and Edge Cases.
  - **`references/description-examples.md`** (181 lines) — worked good/bad examples of the `description` frontmatter field for analysis, generation, and team-lead agents; an anti-pattern catalogue (generic one-liner, missing commentary, duplicated examples, over-broad triggers, banned phrases in the description itself); and a calibration checklist.

- SKILL.md Procedure Step 3 (frontmatter) now links to `references/description-examples.md`; Step 4 (body) links to `references/system-prompt-design.md`. A new `## References` section at the end of SKILL.md indexes both files with "when to load" guidance.

### Changed

- `solera-edit-agent` metadata.version bumped `2.1.0` → `2.2.0` (minor — new feature: on-demand reference docs).
- SKILL.md Completion Checklist gained a new item: "Body follows the six-section structure from references/system-prompt-design.md".

### Deferred (still)

- Progressive disclosure for the other three meta skills (`solera-edit-skill`, `-rule`, `-command`). SKILL.md sizes are still within the 200-line budget; duplicating the pattern now would be premature.
- Eval framework. Same reasoning as v3.1.0 — needs a design session on coexistence with `self-verification.md` first.

---

## [3.1.0] — 2026-04-18

### Fixed

- **`solera-help` advertised a non-existent handoff trigger**: the Workflow table at [skills/solera-help/SKILL.md:57](skills/solera-help/SKILL.md#L57) listed `"End session"` as an invocation phrase for `solera-handoff`, but v2.13.0 removed that trigger. Users following the help table could not invoke handoff. Replaced with `"Run handoff"`, which is in the skill's actual trigger list.
- **Inconsistent H1 titles across the four `solera-edit-*` skills** (`# Meta Skill`, `# Edit Rule`, `# Meta Command`, `# meta-subagent`). Standardised to `# Edit {Skill|Rule|Command|Agent}` matching the `name` field in each skill's frontmatter.
- **`solera-write-concept`**, **`solera-write-milestone`**, **`solera-release`** metadata.version bumped `1.0.0` → `1.0.1`. These SKILL.md files received SSOT markers in v3.0.3 ([994b2c6](https://github.com/noory-code/noory-ai/commit/994b2c6)) without a version bump; this corrects the metadata to match `solera-migrate-v2`'s precedent of bumping on any non-trivial SKILL.md edit.

### Changed

- **`solera-edit-*` meta skills upgraded toward the official skill-creator standard.** Gap analysis against `plugin-dev/skills/{skill,agent,command}-development` and the `skill-creator` skill found three concrete shortfalls, now addressed:

  1. **Rule and agent templates had no YAML frontmatter at all.** `assets/rule-template.md` and both `assets/{task,team}-agent-template.md` opened straight into Markdown body, so generated files could not be reliably loaded by Claude Code and lacked the description/trigger metadata other tooling relies on. Each template's inner code block now opens with the required frontmatter:
     - **Rule template**: `name`, `description` (must name 2-3 concrete triggers), `version`, `applies_to`.
     - **Agent templates (task & team)**: `name`, `description` with `"Use this agent when ..."` preamble and ≥2 `<example>` blocks (Context / user / assistant / commentary), `model` (`inherit`/`sonnet`/`opus`/`haiku`), `color` (6-colour whitelist), `tools` (minimal whitelist — never "all tools").
     - Associated Quality Criteria, Procedure steps, and Completion Checklists in the owning SKILL.md files were extended to enforce frontmatter presence.

  2. **All four edit-\* skill descriptions were generic**. Every description was a one-line `"Add/Define/Edit or {refine|improve} a {skill|rule|command|agent}"` — poor for Claude's auto-triggering. Each now opens with `"Use this skill when the user asks to ..."` followed by 4-5 concrete trigger phrases and the output contract (where the file lands, which frontmatter fields). Lengths went from ~80-90 chars to 349-458 chars.

  3. **`solera-edit-agent/SKILL.md` lacked an explicit frontmatter-writing step.** The Procedure now splits "Write agent" into "Step 3: frontmatter (required fields)" + "Step 4: body", renumbers downstream steps, and extends Common Mistakes and the Completion Checklist to cover frontmatter anti-patterns (skipping it, invalid `color` values, over-broad `tools`).

- **`solera-edit-skill`, `solera-edit-rule`, `solera-edit-command`, `solera-edit-agent`** metadata.version bumped `2.0.0` → `2.1.0`.

### Deferred

The gap analysis identified further improvements that are intentionally out of scope for this release:

- **Progressive disclosure** (moving deep reference content from SKILL.md into `references/`). Current SKILL.md files are still within the 200-line budget; restructuring now would risk link breakage without immediate benefit.
- **System prompt design guide** for `solera-edit-agent`. Requires a new reference document; the frontmatter fix took priority.
- **Eval framework** in the style of `skill-creator`. Solera already has `self-verification.md`; the two need a coherent design before adopting another layer.
- **Full argument/bash/plugin-context coverage** in `solera-edit-command`. Solera itself rarely authors slash commands, so the shortfall does not block current users.

### Notes

- No user-facing behaviour change for existing workspaces. `solera-edit-*` now produce richer files going forward.
- CHANGELOG entries for v2.7.0–v2.7.1 remain in Korean (preserved as historical record).

---

## [3.0.3] — 2026-04-17

### Fixed

- **`solera-migrate-v2` banned phrase leak**: Step 1 Procedure contained `"if needed"` — one of the five AI-First banned phrases its own self-verification rule (C-001) forbids. The ambiguous instruction is replaced with an explicit condition (`when the parent does not exist`).
- **Test suite validated v2 schema**: `tests/test_skill_validation.py` still required `phase_id`, `goal_id`, `epic_name`, and `_epic.md` prerequisites — parameters that v3.0.0 removed. The suite passed regardless of whether `solera-write-story` or `solera-execute-action-item` followed v3. Tests now pin the v3 contract (`story_id`, `contributes_to`, Concept-based prerequisites, `[primary_concept][story_id][ACT-NNN]` commit format) and actively guard against v2 regression by asserting forbidden parameters are absent.

### Changed

- **Three-axis and status SSOT centralised** in the new canonical reference `docs/reference/axes-and-status.md`. Four files that previously defined (or redefined) axis tables and status values now link to it: `docs/work-item-structure.md`, `skills/solera-manage-workflow/assets/conventions.md`, `skills/solera-init/assets/solera-workflow.md`, and the five core writing-skill SKILL.md files which gained a `<!-- SSOT: docs/reference/axes-and-status.md -->` marker. Renaming an axis or adding a status value is now a one-file edit.
- **Self-verification schema centralised** in `docs/reference/self-verification-schema.md`. The `## Structural` / `## Semantic` format with `id:`-addressable rules is declared canonical; `C-001` is reserved across all skills for the AI-First banned phrases check with `"handle accordingly"` added to the canonical pattern list. Every `skills/*/assets/self-verification.md` was aligned:
  - `solera-handoff/assets/self-verification.md` converted from the legacy TC### format to the canonical schema.
  - `solera-execute-action-item`, `solera-write-story`, and `solera-create-pr` gained the canonical `C-001` rule; their prior `C-001` content was renumbered to `C-040` to preserve meaning.
  - The six skills that already had `C-001` now include `"handle accordingly"`, matching the canonical list.
- **`solera-migrate-v2`** v1.2.0 → v1.3.0.
  - Resume Semantics now derives the last completed step **deterministically** from `Solera-Migrate-Step: N-name` commit trailers; filesystem signals are the fallback. Each of the seven step commits adds the trailer.
  - `"if needed"` (Step 1) replaced with an explicit precondition.
- **`retro.md` → `retrospective.md`** asset file rename across three skills (`solera-write-story`, `solera-manage-workflow`, `solera-execute-action-item`). Filename now matches the document it targets (`RETROSPECTIVE.md`). All cross-references updated.

### Notes

- This release is entirely maintenance — no user-facing behaviour changes. Existing workspaces do not need any action.
- The canonical references under `docs/reference/` are the single source of truth for axes, status values, and self-verification schema. Future edits to those concepts start there.

---

## [3.0.2] — 2026-04-16

### Fixed

- **`solera-migrate-v2` Step 1 archive policy**: previous versions used a name-based rule ("skip directories whose name matches a v3 name") to decide what to archive. This misfired on v2 projects where `workspace/identity/`, `workspace/catalog/`, or `workspace/team-process.md` already existed but contained v2 data — those paths would be skipped and v2 content would pollute the v3 skeleton. Step 1 now moves the **entire** `workspace/` contents into `_v2-archive/workspace-original/` regardless of name, and Step 2 copies selectively from the archive. Safer and unambiguous.
- **`solera-migrate-v2` concept → domain-model rename scope**: v1.1.0 only renamed `_v2-archive/catalog/published/concept/`, missing `_v2-archive/extra/*/concept/` and `_v2-archive/extra/*/published/concept/` (nested Obsidian vault layouts). Step 2.3 now enumerates all three source locations for the rename.
- **`solera-migrate-v2` loose files at vault roots**: v2 Obsidian vaults often contain `.md` files directly at the vault root (e.g., `README.md`, `app-structure.md`) that don't live inside a `{type}/` subdirectory. Previously these were silently left in `_v2-archive/` and lost during migration. Step 2.3 now scans for loose files at both the archived workspace root and every extra vault root, and runs a BLOCKING prompt per file (route to `_unclassified/misc/`, provide target, or skip).

### Changed

- **`solera-migrate-v2`** v1.1.0 → v1.2.0.
  - Step 1 "Freeze" now archives every direct child of `{workspace_path}/` into `_v2-archive/workspace-original/` — no name-based exceptions.
  - Step 2 all source paths updated from `_v2-archive/{child}/` to `_v2-archive/workspace-original/{child}/`.
  - Step 2.3 "Catalog merge" covers three source locations for the concept→domain-model rename and three source locations for type enumeration (workspace catalog, extra root, extra/published nested layout).
  - Step 2.3 adds the "Loose files at vault roots" subroutine with BLOCKING prompt.
  - Origin comments injected into migrated Stories (Step 4) now reference the `workspace-original/` path.

### Migration Notes

- Projects migrated with v3.0.0 or v3.0.1 and no surprises are unaffected — v3.0.2 only changes the migration skill.
- Projects that hit the name-conflict, missing-concept-rename, or lost-loose-file issues during a v3.0.0/v3.0.1 migration can re-run `solera-migrate-v2` after upgrading; Resume Semantics detects Step 2 completion via `catalog/published/` state and lets you replay from the correct step.

---

## [3.0.1] — 2026-04-16

### Fixed

- **`solera-migrate-v2` identity source discovery**: v2 Obsidian-style vaults sometimes keep identity files outside `workspace/identity/` (e.g., in a separate vault root like `{project_path}/published/identity/`). Step 2 now collects candidate identity files from both `_v2-archive/identity/` and `_v2-archive/extra/*/identity/`, classifies standard vs non-standard, and asks the human about non-standard files instead of silently keeping or dropping them. Issues a warning if no standard identity files are found in any source.
- **Catalog merge for unknown artifact types**: v2 projects may contain artifact folders not in the v3 mapping (e.g., `schema/`, `reference/`, custom folders). Step 2.3 now runs a BLOCKING one-shot prompt per unknown type, letting the human route it to `catalog/published/_unclassified/{type}/`, map it to an existing v3 type, or skip. Previously unknown types relied on ad-hoc judgment at execution time.
- **Journey detection**: If an archived identity dir contains a `journeys/` subdir, Step 2.1 now moves its contents to `catalog/published/journey/` instead of treating them as identity.

### Changed

- **`solera-publish-artifacts`** v5.0.0 → v5.1.0.
  - Move Mapping table adds `reference/ → catalog/published/reference/`.
  - New **fallback row**: unknown types go to `catalog/published/_unclassified/{type}/` (previously "left in place + logged"). Step 1 Discovery now asks a BLOCKING one-shot prompt per unknown type before routing to fallback.
  - Error Handling row for "Unknown artifact type" updated to describe the BLOCKING fallback flow.

- **`solera-migrate-v2`** v1.0.0 → v1.1.0.
  - Step 2 expanded into three subsections (2.1 Identity copy policy, 2.2 team-process.md, 2.3 Catalog merge) with explicit policies for identity classification and unknown catalog types.
  - Resume Semantics table adds a signal row for Step 2 completion (`catalog/published/` populated).

### Documentation

- `docs/migrate-v2-to-v3.md` "What happens to your v2 data" table expanded to describe the new non-standard identity and unknown catalog type flows.

### Migration Notes

- Projects migrated with v3.0.0 are unaffected — v3.0.1 only changes behavior of the migration skill itself, not the resulting v3 workspace layout.
- If you ran the v3.0.0 migration and ended up with missing identity files or dropped artifact folders, re-run `solera-migrate-v2` after v3.0.1 to resume from Step 2; the skill's Resume Semantics will skip already-completed steps.

---

## [3.0.0] — 2026-04-16

### ⚠️ BREAKING CHANGES

v3 is a full architectural rework. The v2 single-hierarchy model (Identity → Initiative → Phase → Goal → Epic → Story → Action Item) is replaced with a three-axis model:

- **Living** — Identity, Concepts (never end; evolve continuously)
- **Time-bound** — Milestones, Stories, Action Items (have a start and end)
- **Immutable** — Releases (frozen snapshots, write-once)

**v2 projects cannot be opened directly by v3.** Use `solera-migrate-v2` to migrate.

### Removed

- `solera-write-phase` — Phase layer eliminated
- `solera-write-goal` — Goal layer eliminated
- `solera-write-epic` — Epic layer eliminated
- `workspace/initiative/` and `workspace/phase/` directory conventions
- Epic branches (`epics/{name}`) and Story-under-Epic branches (`epics-{name}/story-{id}-{name}`)
- `[epic-name][US-NNN][ACT-NNN]` commit scope tag
- Artifact promotion at Goal Create + Epic Wrap-up (two hooks collapsed into one)

### Added

- **`solera-write-concept`** v1.0.0 — draw / update / deprecate / archive Concepts with human-led Intent and Current Design; AI proposes Current Shape updates at Story Wrap-up. Modes: `create` / `update` / `deprecate` / `archive`. BLOCKING on Intent entry — AI must never invent it.
- **`solera-write-milestone`** v1.0.0 — the Moment 2 skill. Human proposes scope; AI runs a mandatory analysis round (maturity, risks, dependencies, missing prerequisites, cross-concept contradictions); loop until agreed. Modes: `create` / `update` / `mark-released`. Analysis round is **non-negotiable** — even "skip analysis" requests produce at least a one-liner.
- **`solera-release`** v1.0.0 — Moment 4 skill. Freezes an achieved Milestone into `releases/{tag}/` with a `concepts-snapshot/` (verbatim Concept copies with ❄️ markers), a `stories-manifest.md`, and a human-approved `README.md`. Refuses to overwrite an existing release directory. Optional `git tag` creation.
- **`solera-migrate-v2`** v1.0.0 — 7-step assisted migration skill. Non-destructive freeze of v2 data to `_v2-archive/`, v3 skeleton creation, AI-proposed Concept candidates from v2 Goals/Epics (human approval required), Story flattening with `contributes_to` inference (sample-reviewed), `releases/v2-final/` as the first immutable snapshot.
- **Three-axis `progress.md` format** — Living / Time-bound / Immutable sections instead of Phase/Goal/Epic/Story/ACT pointers.
- **Concept Contribution Summary** — required section in every Story `RETROSPECTIVE.md`, with Drift note capability.
- **Input Artifacts / Output Artifacts** — two distinct sections on every Story. Input provided by human at Step 2; Output appended by `solera-execute-action-item` during Execute.
- **Gate `concept.align`** — checks `contributes_to` is present, each Concept exists and is `active`.
- **Gate `milestone.agree`** — fires at Milestone agreement boundary.
- **Check type `concept_exists`** — for each concept_id (or `contributes_to` if empty), Glob `concepts/{id}.md`; PASS if all exist with `status: active`.
- **Check type `milestone_status`** — read `milestones/{id}.md`; PASS if `status` matches `equals`.
- **Gate check execution** — dispatch table inlined into each gate-running skill (`solera-write-story`, `solera-execute-action-item`, `solera-write-milestone`) for the 6 check types.

### Changed

- **`solera-write-story`** v9.0.1 → v10.0.0. Parameters simplified: removed `year`, `phase_id`, `goal_id`, `goal_name`, `epic_name`, `epic_type`; added `contributes_to` (required ≥1) and `belongs_to` (optional). Path flattened from `phase/.../epics/.../stories/{id}` to `stories/{id}-{name}/`. Branch: `story/{id}-{name}` from trunk. Commit scope tag uses `contributes_to[0]` (the primary_concept). New Step 5 subroutine at Wrap-up: AI proposes Current Shape update for each contributed Concept; BLOCKING on human approval; Contributions row appended.
- **`solera-execute-action-item`** v7.2.0 → v8.0.0. Parameters simplified: removed `year`, `phase_id`, `goal_id`, `goal_name`, `epic_name`, `epic_type`. Commit scope tag reads `_story.md` frontmatter `contributes_to[0]`. New Wrap-up obligation: append each completed ACT to the parent Story's `# Output Artifacts` section (required for Story Wrap-up's Current Shape draft). System improvements (`skill_change` / `rule_change`) now commit as a separate follow-up commit (`chore(solera): apply improvements from …`) instead of amending the ACT commit — preserves Atomic Commits.
- **`solera-manage-workflow`** v5.1.0 → v6.0.0. `uses` list updated to v3 skills. New 8-branch `next` action surfaces options based on three-axis state (ACT in progress → Story has ACTs → Story Wrap-up pending → Milestone Stories pending → Milestone Exit Criteria met → no Milestone but Concepts → no Concepts → no Identity). Supervisor explicitly state-aware but not opinionated; auto-picks only when one path is obvious (resume).
- **`solera-init`** v2.1.0 → v3.0.0. Detects v2 projects (`workspace/initiative/`, `workspace/phase/`, `_goal.md`, `_epic.md`) and refuses to overlay v3 — advises `solera-migrate-v2` instead. Creates v3 skeleton: `identity/`, `concepts/`, `milestones/`, `stories/`, `releases/`, `catalog/published/` + three `_index.md` seeds. Kickoff interview C-4 gate mapping updated to v3 gate keys.
- **`solera-publish-artifacts`** v4.0.0 → v5.0.0. Rewritten as a **Story Wrap-up hook** (v2 had two hooks: Goal Create + Epic Wrap-up — collapsed to one). Discovery source is `stories/{story_id}/artifacts/`. Version tag is `{story_id}`. New responsibility: wire the promoted files into each contributed Concept's `# Related Artifacts` section. Collision handling is now BLOCKING with three explicit options (Overwrite / Rename new / Skip) — no automatic rename.
- **Artifact rename: `concept` → `domain-model`**. The v2 Epic-level "concept" artifact (domain entity modeling) is renamed to `domain-model` so the word "Concept" can be used for the living axis. `catalog/published/concept/` → `catalog/published/domain-model/`. The v2 template is archived at `docs/reference/domain-model-template.md`.
- **`solera-help`** v1.0.0 → v3.0.0 — full rewrite with v3 skill table grouped by axis.
- **`solera-write-identity`** — minor update: the handoff suggestion at the end of Identity creation now points to `solera-write-concept` instead of `solera-write-phase`/`solera-write-goal`.

### Documentation

- `docs/work-item-structure.md` — rewritten around the three axes and four moments.
- `docs/architecture.md` — rewritten. New sections: Three-Axis Wiring, Why no supervisor state machine.
- `docs/quick-start.md` — rewritten end-to-end for v3 (Identity → Concept → Milestone → Story → Release).
- `docs/team-workflow.md` — rewritten. Stories are now the sole branching unit; Concept-level coordination and drift-detection mechanics explained.
- `docs/migrate-v2-to-v3.md` — new. Migration guide for `solera-migrate-v2`.
- `docs/reference/domain-model-template.md` — new. v2 concept template archived for reference.
- `README.md` — rewritten. Three-axis diagram, four-moments summary, v2 migration pointer.

### Migration Notes

- **v2 projects**: run `solera-migrate-v2` from a clean git state. Every step blocks for your approval; automatic destruction is impossible. Reversible via `git reset` if mid-flight.
- **No automatic v2 → v3 fallback**: `solera-init` refuses to touch existing v2 data.
- **v2 maintenance**: stay on v2.14.0 if you need to maintain a v2 project without migrating. v3 will not add features backported to v2.

---

## [2.14.0] — 2026-04-09

### Added
- **Action Item level gates**: `workflow_gates` now supports `act.start` and `act.done`
  gate keys for per-commit dependency management and automated verification
- `solera-execute-action-item` v7.2.0: Setup step checks `act.start` gate before
  execution; Wrap-up step checks `act.done` gate after commit (same structured
  `checks[]` mechanism as Story-level gates)
- `solera-init` v2.1.0: kickoff interview and team-process template include
  `act.start` / `act.done` gate configuration

---

## [2.13.0] — 2026-04-06

### Fixed
- **Handoff no longer forced**: `solera-handoff` triggers narrowed to explicit requests
  only (`handoff`, `save handoff`, `run handoff`, `update HANDOFF`). Removed broad
  triggers like `end session`, `save work context`, `hand over to next session`
- **solera-workflow.md**: handoff routing changed from "End session, wrap up" to
  explicit-only invocation
- **Anti-pattern guard**: `solera-workflow.md` and `solera-manage-workflow` now
  explicitly prohibit suggesting handoff after task completion — handoff is
  user-initiated only

### Changed
- `solera-handoff` v2.0.0 → v2.1.0
- `solera-manage-workflow` v5.0.1 → v5.1.0

---

## [2.12.0] — 2026-03-30

### Added
- **System improvement step**: `solera-execute-action-item` Wrap-up now classifies
  retrospective improvements into `skill_change`, `rule_change`, or `framework_change`
  and applies skill/rule changes immediately within the same commit

### Changed
- **Rename RETRO.md → RETROSPECTIVE.md** across all skills, templates, docs, and tests
  — eliminates ambiguity with "retro" (retrospective vs. vintage)
- Affected skills patched: `solera-write-story` v9.0.1, `solera-write-epic` v5.0.1,
  `solera-write-goal` v5.0.1, `solera-write-phase` v3.0.1, `solera-manage-workflow` v5.0.1,
  `solera-execute-action-item` v7.1.0

---

## [2.11.0] — 2026-03-30

### Added
- **execution_order enforcement**: `solera-write-story` Step 3 validates ACT phase
  assignments against `execution_order.groups` from team-process.md — ensures
  layered architecture ordering (e.g., Domain before Data before Presentation)
- **Structured gate verification**: `workflow_gates` in team-process.md now supports
  a `checks[]` array with deterministic check types (`glob_exists`, `act_complete`,
  `command_passes`, `grep_absent`). `solera-write-story` Steps 4-5 iterate checks
  programmatically. Falls back to text-based evaluation when `checks` is absent.
- **Architecture boundary check**: `solera-execute-action-item` Step 4 enforces
  `architecture_rules` from team-process.md — greps for forbidden import patterns
  in changed files, blocks completion on violation
- **Layer-aware ACT decomposition**: `solera-write-story` Step 3 decomposes Action
  Items by architectural layer when `execution_order.groups` is defined, ensuring
  correct phase ordering from the start

### Changed
- **team-process.md template**: added `execution_order`, `architecture_rules` sections
  and extended `workflow_gates` to support structured `checks[]` array
- **solera-init interview**: added Step C-5 for automatable gate checks; added Step F
  questions for layered architecture ordering and boundary rules
- `solera-write-story` v8.0.0 → v9.0.0
- `solera-execute-action-item` v6.0.0 → v7.0.0

---

## [2.10.4] — 2026-03-20

### Fixed
- `solera-write-goal`: add missing `solera-create-pr` to `uses` array
- `solera-write-epic`: add missing `solera-create-pr` to `uses` array
- `solera-publish-artifacts`: fix description to reflect dual invocation (Goal Create + Epic Wrap-up)
- `solera-edit-rule`: normalize H1 from `# Skill: meta-rule` to `# Edit Rule`
- `solera-write-epic`: remove duplicate Directory Structure section

---

## [2.10.3] — 2026-03-20

### Added
- `user-invocable` frontmatter to all 16 skills (15 true, 1 false for solera-publish-artifacts)

---

## [2.10.2] — 2026-03-20

### Fixed
- `solera-create-pr`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-execute-action-item`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-init`: metadata `type: composite` → `type: unit` (no sub-skill invocations)

---

## [2.10.1] — 2026-03-18

### Fixed
- `solera-help`: metadata `type: reference` → `type: unit` (reference is not a valid type value)
- `solera-publish-artifacts`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-write-identity`: metadata `type: composite` → `type: unit` (no sub-skill invocations)

---

## [2.10.0] — 2026-03-18

### Removed
- **Handoff hook**: removed auto-HANDOFF.md generation — `git log` and `CLAUDE.md` provide sufficient context without extra API cost

---

## [2.9.2] — 2026-03-17

### Added
- **PRIVACY.md**: Privacy policy for marketplace submission — documents that Solera
  operates entirely locally with no data collection or external transmission

---

## [2.9.1] — 2026-03-17

### Added
- **LICENSE file**: MIT license added to plugin root for marketplace submission compliance

---

## [2.9.0] — 2026-03-16

### Changed (BREAKING)
- **Skill rename**: `solera-transition-catalog` → `solera-publish-artifacts` across all
  17 referencing files (SKILL.md, assets, docs, README). Directory renamed accordingly.

### Added
- **workflow_gates enforcement**: `solera-write-epic` and `solera-write-story` now read
  `team-process.md` and check gates before proceeding:
  - `epic.use_case` gate checked before Use Case step
  - `epic.concept` gate checked before Concept step
  - `story.execute` gate checked before Execute step
  - `story.wrap_up` gate checked before Wrap-up step
  - `solera-write-goal` also enforces unmet gates (blocking)
  - Previously gates were defined in team-process.md but never enforced (dead code)

### Fixed
- **Translate all remaining Korean to English**: Error Handling tables in 7 SKILL.md files,
  Examples sections in write-story and write-epic, 3 test files (test_skill_validation.py,
  test_handoff_hook.py, tests/README.md), and Korean trigger phrases removed from solera-help

---

## [2.8.1] — 2026-03-16

### Fixed
- **Translate all remaining Korean to English** across 3 files (58+ violations):
  - `solera-workflow.md`: Intent → Skill Routing table fully translated
  - `solera-write-identity`: persona interview questions (NN/G 6-field) + Error Handling table
  - `solera-write-goal`: BLOCKING comments, Error Handling table, and full Examples section

---

## [2.8.0] — 2026-03-16

### Changed (BREAKING)
- **`solera-init` SKILL.md fully rewritten in English** (v2.0.0)
  - All hardcoded Korean interview questions replaced with principle-based
    interview structure (Steps A–G), each mapped to a specific `team-process.md` field
  - Interview is now language-agnostic: AI asks in the user's language
- **`solera-init` Step 5 kickoff interview**: generalized from software-only to
  any project type (software / marketing / design / content / other)
  - Project type detected first; software projects get additional `tech_stack` fields
  - Stage list examples adapt to project type (software, marketing, design)
  - Every question traces to a specific output field (no orphan questions)

### Added
- **`assets/team-process-software.md`**: software development extension template
  (`tech_stack.backend`, `frontend`, `infra`) — merged into `team-process.md`
  when `project.type = "software"`
- **`team-process.md` base template**: redesigned as a universal project template
  with `project`, `workflow_gates`, `process_stages`, `conventions`, `tools`, `custom_rules`

---

## [2.7.2] — 2026-03-16

### Fixed
- **`solera-init` Step 5**: 나머지 4개 낮은 심각도 이슈 수정
  - UX vs UI 구분 설명 추가 — 체크리스트에 "(UX와 UI를 구분하지 않는다면 하나로 합쳐도 됨)" 안내
  - 백엔드/프론트 병렬 여부 질문 추가 — 둘 다 선택 시 "동시 진행인가요?" 확인
  - UI 디자인/엔티티 게이트 범위 명확화 — 프론트만 / 전체 개발 중 어느 쪽인지 질문
  - 배포 단계 심화 추가 — CI/CD, 배포 환경, 승인 절차 수집; 기술 스택 섹션에서 중복 방지
  - `workflow_gates` 템플릿 주석에 각 게이트의 적용 레벨(Epic/Story 범위) 명시

---

## [2.7.1] — 2026-03-16

### Fixed
- **`solera-init` Step 5 섹션 2**: 시뮬레이션 테스트에서 발견된 3개 이슈 수정
  - PR 승인 수 중복 수집 제거 — 코드 리뷰 단계(2-2)에서 수집한 값을 Section 4에서 재사용
  - `story.execute` 다중 게이트 조건 처리 추가 — 여러 gate=true 단계가 충돌 시
    백엔드/프론트 범위 확인 질문으로 AND 조건 분리 여부 결정
  - 초기 언급 단계가 최종 선택에서 누락된 경우 확인 질문 추가

---

## [2.7.0] — 2026-03-16

### Changed
- **`solera-init` Step 5 섹션 2**: "개발 프로세스" 인터뷰를 3단계 계층형 구조로 심화
  - 2-1: 팀이 실제로 사용하는 단계를 체크리스트 형식으로 선택
    (기획/UX/UI/엔티티/API/개발/테스트/리뷰/QA/배포)
  - 2-2: 선택된 단계에 대해서만 완료 기준, 툴, 담당자, 게이트 여부를 심화 질문
  - 2-3: AI가 수집한 답변으로 workflow_gates를 자동 도출 후 사용자 확인
- **`team-process.md` 템플릿**: `workflow_gates`에 4개 게이트 키 추가
  (`epic.use_case`, `epic.concept`, `story.execute`, `story.wrap_up`),
  `process_stages` 섹션 신규 추가 (단계별 name/tool/done_when/gate 구조)

---

## [2.6.0] — 2026-03-16

### Added
- **`solera-init`: Team Kickoff Interview** (Step 5) — conversational interview that
  collects service info, workflow gates, tech stack, and conventions, then generates
  `{project_path}/workspace/team-process.md`
- **`team-process.md` template** — YAML format with sections for service, workflow_gates,
  tech_stack, conventions, custom_rules; read by skills at Goal/Epic level

### Changed
- **`solera-workflow.md`** (installed rule) — rewritten as a slim Intent → Skill Routing
  table; removed procedural content; added pointer to `team-process.md`
- **`solera-write-identity`**: Step 1 expanded to Discovery Interview with NN/G 6-field
  persona model (role, skill level, context, goal, pain point, quote); personas are additive
- **`solera-write-goal`**: Journey step now creates new files per Goal (`{goal_id}-{persona}.md`)
  instead of overwriting — follows OCP (open for extension, closed for modification)

---

## [2.5.0] — 2026-03-16

### Added
- **Team Customization section** in `solera-workflow.md` template (installed by `solera-init`)
  - Teams can define workflow gates, artifact conventions, commit/branch conventions,
    tech stack, and custom rules on top of Solera's work item structure
  - Solera provides the skeleton; each team wraps it with their own process rules

---

## [2.4.0] — 2026-03-16

### Changed
- **Branch naming**: Epic branches changed from `epic-[name]` to `epics/[name]`.
  Story branches changed from `epic-[name]/story-[ID]-[name]` to
  `epics-[name]/story-[ID]-[name]` (avoids git file/directory conflict).
- Updated all branch references across skills, docs, and README

---

## [2.3.1] — 2026-03-16

### Fixed
- README.md: added missing `solera-init` and `solera-help` to Skills table
- solera-help SKILL.md: added self-reference to Meta skills listing

---

## [2.3.0] — 2026-03-16

### Changed (BREAKING)
- **Directory structure flattened**: Removed `stories/` and `action-items/`
  intermediate directories
  - Before: `epics/{name}/stories/US-001/action-items/ACT-001-xxx.md`
  - After: `epics/{name}/US-001-login-screen/ACT-001-xxx.md`
- Story folder naming now includes slug: `{story_id}-{story_name}/`
  (e.g., `US-001-login-screen/`) for readability
- Updated all path references across: write-story, write-epic, execute-action-item,
  manage-workflow, write-goal, architecture.md, quick-start.md

---

## [2.2.0] — 2026-03-16

### Added
- **solera-write-story**: Scan available project skills (`Glob .claude/skills/*/SKILL.md`
  and `.claude/plugins/*/skills/*/SKILL.md`) during Action Item decomposition
- **solera-write-story**: `Skill` column added to Action Items table — matches
  task content against scanned skill triggers
- **solera-execute-action-item**: `Skill Resolution` section — reads `Skill:`
  metadata from ACT file and auto-invokes the specified skill; falls back to
  keyword matching when set to `-`
- **action-item.md** template: `Skill:` metadata field added
- **story.md** template: `Skill` column added to Action Items tables (US & TS)

---

## [2.1.0] — 2026-03-16

### Added
- **solera-create-pr**: `target_branch` is now optional — resolved from
  `default_pr_base` in `.claude/rules/solera-workflow.md` Project Config,
  with fallback to user prompt
- **solera-create-pr**: Artifact promotion pre-check blocks PR creation when
  Epic-level artifacts (use-case, concept, erd, dto, api-spec) remain in
  `artifacts/` — instructs user to run `solera-transition-catalog` first
- **solera-workflow.md** template: added `## Project Config` section with
  `default_pr_base` setting (commented out by default)

---

## [2.0.0] — 2026-03-15

### Changed (BREAKING)
- All 16 skills renamed with `solera-` prefix to avoid name collisions with
  other plugins: `write-goal` → `solera-write-goal`, `create-pr` → `solera-create-pr`,
  `handoff` → `solera-handoff`, etc.
- Updated all internal references: SKILL.md files, asset templates, self-verification
  files, docs, README, tests, and handoff hook

---

## [1.11.0] — 2026-03-15

### Added
- `init` skill: sets up Solera in a new project — installs `.claude/rules/solera-workflow.md`
  (workflow rules, git branch conventions, artifact promotion, commit format) and creates
  the workspace folder structure with initial `progress.md`
- Updated `help` skill to list `init` and guide new users to run it first

---

## [1.10.0] — 2026-03-15

### Changed
- **Artifact promotion is now incremental** — `transition-catalog` is invoked at
  two points instead of once at Goal completion:
  1. After Goal Create: promotes Goal-level artifacts (service-map, persona, journey)
  2. At each Epic Wrap-up: promotes Epic-level artifacts (use-case, concept)
- Goal Wrap-up no longer calls `transition-catalog`; it only confirms `artifacts/`
  is empty
- `write-epic` now includes `transition-catalog` in its `uses` and Wrap-up procedure
- Updated all docs, templates, self-verification files, and error handling to reflect
  the incremental promotion model

---

## [1.9.7] — 2026-03-15

### Fixed
- Fix stale skill name references across all docs, SKILL.md, asset templates,
  and self-verification files. Align with v1.5.0 rename: `writing-*` → `write-*`,
  `writing-action-item` → `execute-action-item`, `workflow-manage` → `manage-workflow`,
  `workflow-pr` → `create-pr`, `catalog-transition` → `transition-catalog`.

---

## [1.9.6] — 2026-03-08

### Fixed
- `handoff_hook.py`: add project scope guard — only run in the plugin's
  home project (noory-ai), skip other projects like flutter-material-kit
  that have solera enabled. Prevents spurious handoff sessions in unrelated
  project session folders.

---

## [1.9.5] — 2026-03-08

### Fixed
- `handoff_hook.py`: replace ephemeral lockfile with TTL-based lock (120s).
  Previous lockfile was deleted in `finally`, allowing queued SessionEnd hooks
  to re-enter immediately after cleanup. Now the lock persists for 120s after
  creation, blocking all re-entrant calls during that window.

---

## [1.9.4] — 2026-03-08

### Fixed
- `handoff_hook.py`: replace env var guard with lockfile (`/tmp/solera-handoff-hook.lock`)
  Env vars are not propagated into hook subprocesses by Claude Code, so the previous
  `SOLERA_HANDOFF_RUNNING` guard had no effect. Lockfile approach reliably prevents
  concurrent re-entrant invocations.

---

## [1.9.3] — 2026-03-08

### Fixed
- `handoff_hook.py`: add `SOLERA_HANDOFF_RUNNING` env guard to prevent recursive
  SessionEnd invocations — `claude -p` subprocesses also trigger SessionEnd,
  causing HANDOFF.md to be overwritten repeatedly and processes to accumulate

---

## [1.9.2] — 2026-03-07

### Improved
- Standardized `| Step | Output | Path | Nature |` table format across all skills
- Added `execution_model` metadata and blocking/non-blocking clarification to write-goal, write-epic, write-story, manage-workflow
- Unified sub-skill invocation syntax to `Skill(name="...", args={...})` in write-epic, write-goal, write-story
- Added end-to-end `## Examples` sections to write-epic, write-goal, write-story
- `refactor`: aligned transition-catalog parameters with write-goal/epic/story pattern
- `refactor`: standardized hierarchical parameter naming across all skills
- `docs`: added `## Error Handling` section to all skills
- `test`: added automated skill parameter validation tests (9 cases)

---

## [1.9.1] — 2026-03-07

### Fixed
- `handoff_hook.py`: replace `Popen` + `start_new_session=True` with `subprocess.run(timeout=60)`
  `start_new_session` has no effect on macOS (setsid not supported), leaving orphan processes
  on every SessionEnd. Blocking run ensures clean process lifecycle.

---

## [1.4.0] - 2026-03-02

### Changed
- Renamed 13 skills to verb-first naming for clarity and intent:
  - `writing-*` → `write-*` (identity, phase, goal, epic, story)
  - `writing-action-item` → `execute-action-item`
  - `workflow-manage` → `manage-workflow`
  - `workflow-pr` → `create-pr`
  - `catalog-transition` → `transition-catalog`
  - `meta-skill` → `edit-skill`, `meta-rule` → `edit-rule`, `meta-command` → `edit-command`, `meta-subagent` → `edit-agent`
- Expanded triggers from 3–4 noun phrases to 5–6 natural English verb phrases per skill
- Rewrote all skill descriptions from internal-impl view to user-outcome view

## [1.3.0] - 2026-03-02

### Added
- `meta-skill` skill: create, review, or improve skill files in `.claude/skills/`; includes 4 type templates (unit-guide, unit-procedural, composite-guide, composite-procedural)
- `meta-rule` skill: create, review, or improve rule files in `.claude/rules/`
- `meta-command` skill: create, review, or improve slash command files in `.claude/commands/`
- `meta-subagent` skill: create, review, or improve agent definition files in `.claude/agents/`
- `docs/work-item-structure.md`: full hierarchy diagram (Identity → Action Item), folder layout, branch mapping, Human vs AI responsibility split

## [1.2.0] - 2026-03-02

### Added
- `writing-identity` skill: define service identity (Mission, Core Values, Vision, Goals rough list)

## [1.1.0] - 2026-03-02

### Added
- `docs/` folder with quick-start, architecture, and team-workflow guides
- README rewritten with Why Solera, Quick Start, comparison table, and team workflow section

### Changed
- plugin.json: version 1.1.0, expanded keywords

## [1.0.0] - 2026-03-01

### Added
- Initial release with 9 workflow skills
- Writing hierarchy: writing-phase, writing-goal, writing-epic, writing-story, writing-action-item
- Workflow management: workflow-manage, workflow-pr
- Context management: catalog-transition, handoff
- Stop hook: auto-runs handoff skill on session end
