# Changelog

All notable changes to Novel are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.135.0] — 2026-07-02

### Changed

- **The service landscape spans value exchanges, not internal layers.**
  Benchmark round 2 (Uber run): asked for the landscape, the coach mapped
  four internal layers of one marketplace (matching, safety, settlement) and
  surfaced a single value exchange. The services framing now pins what a
  service IS (one value-exchange surface — a distinct pair of sides trading
  value), states that layers of one exchange are not services, and has the
  coach ask what other exchanges the vision touches before drilling in.
  (D-2026-07-02-R, tenth sim iteration)

## [0.134.0] — 2026-07-02

### Changed

- **The coach draws core values out until the founder runs dry.** Benchmark
  round 2: J-values was the weakest axis in every run — the coach landed 2–3
  values and moved on while ground truths run 4–8. The foundation interview
  now treats every recurring fork as a candidate value and hunts the next
  fork after each one lands, never settling for the first two or three.
  (D-2026-07-02-Q, ninth sim iteration)

## [0.133.1] — 2026-07-02

### Fixed

- **Coach's pre-tool planning monologue no longer leaks into the chat.**
  Benchmark finding (B-9, 19 hits across every run): before calling canvas
  tools the model emits a short English planning block ("The user confirmed.
  Let me add it.") and the stream pipeline concatenated it with the post-tool
  reply — internals leaking through a channel the D-2026-07-02-D prompt rule
  can't reach. A ``tool_use`` block start now resets the accumulated turn
  text, so only text after the last tool call is the persisted reply (the
  viewer already reconciles its streamed text on ``turn_complete``).
  (D-2026-07-02-P)

## [0.133.0] — 2026-07-02

### Changed

- **Entity registration is the coach's own judgment.** Users can't name their
  data model ("찾을 수 없으니 자율적 판단이 필요"), and the entities canvas is
  the AI-maintained canvas by spec (D-2026-06-17-I) — so the coach now derives
  the entity map from the features and registers it autonomously, mentioning it
  in one light line instead of asking per-entity permission. Visible on the
  canvas for review/edit/delete = not silent; the confirm-first gate stays for
  foundation/services content. (D-2026-07-02-O)

## [0.132.0] — 2026-07-02

### Added

- **`set_node_references` MCP tool — the coach can wire reference slots.**
  Benchmark finding: every service's who-takes-part / what-values / what-tone
  slots stayed empty in every run. Ref fields are rightly protected from
  free-text writes, but NO tool could set them at all. The new tool assigns
  allow-listed ref fields per kind (service→actors/values/identities,
  step/feature→entities), validating every id on its home canvas; the write
  playbook now treats empty reference slots as an unfinished service.
  (D-2026-07-02-N)

## [0.131.0] — 2026-07-02

### Changed

- **The coach derives the entity map itself** — before leaving the services
  canvas it imagines the plausible data things the registered features must act
  on, even ones nobody named, and proposes the batch for confirmation
  ("엔티티는 상상해서라도 만들어보세요"). (D-2026-07-02-M)

### Fixed

- **Coach-registered features are now drillable.** Detail canvases only seeded
  through the app's endpoint flow, so features created by the coach had no
  기능 canvas at all ("기능 캔버스 뜨지 않네"). The MCP create path now seeds the
  feature's detail canvas exactly like the app path. (same decision)

## [0.130.0] — 2026-07-02

### Added

- **`near` placement on `create_node` — children land beside their parent.**
  Fifth sim-benchmark iteration (user: "캔버스는 잘 못그리네"): kind-clustering
  piled every feature of every service into one global column. `near=<parent id>`
  places the new node right of that anchor, stacking below earlier siblings
  (one column per anchor) and overriding the kind pile; the write playbook has
  the coach pass the parent when registering a child, in the same confirmed
  action as the connecting edge. Placement policy split to its own module.
  (D-2026-07-02-L)

## [0.129.0] — 2026-07-02

### Changed

- **Services coaching maps the landscape first.** Fourth sim-benchmark
  iteration: real products run on 5-6 value-exchange surfaces but the coach
  landed 2-3, sinking into the first service named. The framing now opens with
  a canvas-level map — candidate services derived from the mission and actors,
  confirmed, registered — then details each one. (D-2026-07-02-K)

## [0.128.0] — 2026-07-02

### Added

- **`create_edge` MCP tool — the coach can finally draw the line.** Third
  sim-benchmark iteration: 40/40 coach-registered features floated unconnected
  (0 service→feature edges across the batch) because the coach had a clobber-safe
  node append but only the whole-doc `update_canvas` for edges. `create_edge`
  mirrors `create_node`: endpoint validation, server-minted id + relation,
  single-edge append, whole-doc re-validation, atomic write, idempotent on
  retries. The write playbook now has the coach connect a registered node to its
  parent in the same confirmed action — one yes covers the node and its line.
  (D-2026-07-02-J)

## [0.127.0] — 2026-07-02

### Changed

- **The coach surfaces entities during design talk.** Second sim-benchmark
  iteration: entities were 0/8 across the batch — the surface-the-entity
  instruction lived only in the entities-scope framing that no design
  conversation runs under. The services framing now spots the data 'things'
  features handle and registers confirmed ones on the entities canvas (the
  write playbook explicitly allows that one cross-canvas create; still
  confirmation-gated). (D-2026-07-02-I)
- **The coach wraps up instead of leaving required items empty** — identity
  landed in only 3/8 runs; the pace playbook now has it draft a still-empty
  required item from everything that stands and ask for one quick confirm as
  the session winds down. (same decision)

## [0.126.0] — 2026-07-02

### Changed

- **The coach paces the whole canvas.** First finding of the coach-sim benchmark
  (Airbnb full-flow baseline): the coach was thorough but slow — 8 foundation
  turns never reached identity, 8 services turns never produced a feature. A new
  pace playbook in the canvas system prompt has it land an item once it's good
  enough and move on, derive later items from what already stands (identity from
  mission+values; service slots from foundation/actors), and budget the session
  across every concept the canvas needs. (D-2026-07-02-H)
- **Services coaching proposes features early** — 3–5 concrete features as soon
  as a service's problem/value stand, instead of after all five slots; reference
  slots fill by proposed matches along the way. (same decision)

## [0.125.2] — 2026-07-02

### Fixed

- **HTTP-only dev engines silently stripped the in-app coach of every canvas
  tool.** The chat CLI subprocess inherited the engine's own runtime toggles;
  the coach's mashbill MCP stdio server (spawned by the CLI) then saw
  `MASHBILL_NO_MCP=1` + the engine's busy `MASHBILL_PORT`, booted with "no
  transports to start", and exited — the coach could only talk, never write.
  Found by the coach-sim harness (a 6-turn run confirmed a mission and the
  canvas stayed empty; the session log showed the coach hunting for its tools
  six times). Both providers now spawn the CLI with those toggles stripped.
  Pinned by `test_spawn_env_strips_engine_runtime_toggles`.

## [0.125.1] — 2026-07-02

### Fixed

- A chat turn sent without a `selection` key (any API caller that isn't the
  viewer — found by the coach-sim harness) crashed the turn with a 500 in the
  context preamble. The preamble entry point now normalizes a missing/non-list
  selection to "nothing selected". Pinned by
  `test_turn_preamble_tolerates_missing_selection`.

## [0.125.0] — 2026-07-02

### Changed

- **The in-app coach no longer narrates its internal operations.** It stops saying
  "저장됐어요" and stops exposing internal field names (statement / body / …) to the
  user — the live canvas is the feedback, so the mechanics stay invisible and the coach
  speaks in the user's own words. Supersedes the "confirm the save out loud" line of the
  earlier write playbook. (D-2026-07-02-D)
- **The coach leads and fills a concept's full set through conversation.** It no longer
  declares a canvas "done" the moment one item exists or hands the wheel back with a bare
  "what next?" — it draws out a concept's several facets (a project's several core values,
  an identity's multiple voices) before moving on, so the user isn't forced to point out
  what's missing. Grounded in a dogfood transcript. (D-2026-07-02-E)

## [0.124.0] — 2026-07-02

### Changed

- **A newly created node now clusters with its own kind.** The coach's `create_node`
  auto-position places a new node with the existing same-kind cluster (left-aligned,
  just below the lowest sibling) instead of a fixed generic drop spot — so a new core
  value joins the others rather than scattering. Foundation auto-layout stays a manual
  button, unchanged. Fixes a dogfood report that new core values attached to the anchor
  "anywhere". (D-2026-07-02-C)

- **core_value node collapses to name (`label`) + `body`** — the separate
  `definition` field is removed across the engine model, viewer domain class, and
  inspector, finally implementing the long-pinned **D-2026-06-16-M** (the spec had
  said "name + body" for two weeks while the code still exposed three slots). The
  inspector now spells the two roles out: a one-line guide (name above, meaning
  below) + a body field labelled "meaning & tradeoff" with a worked placeholder —
  fixing the developer report that label / definition / body roles were unclear.
  Legacy `definition` folds into `body` on read as the lead paragraph (data-loss
  guard), so old projects lose nothing. Wire contract + `wire.gen.ts` regenerated.
  (D-2026-07-02-A)
- **In-app coach now proposes proactively.** Added a propose-playbook to the canvas
  system prompt: once it has enough, the coach drafts a concrete candidate and offers
  the higher-level angle the user hasn't reached, instead of only interviewing and
  waiting. Realises the "적극 토론 코치" spec (**D-2026-06-16-H**) that the prompt
  wasn't enforcing. The save gate is unchanged — proposing is talk; a write still
  needs an explicit yes. (D-2026-07-02-B)

### Removed

- `core_value.definition` field (engine + viewer + wire), folded into `body` on read.

## [0.123.0] — 2026-07-01

### Changed

- **Renamed the plugin directory `plot/` → `mashbill/`, the Claude Code plugin
  name `plot` → `mashbill` (+ homepage), and all 11 skills + the verifier agent
  `plot-*` → `mashbill-*`.** Completes the 2026-06-30 naming overhaul (the Python
  package was already `mashbill`; this pass renames the folder, plugin identity,
  dev/help skills, agent, and every cross-repo path/skill reference in the
  workspace and app repos). No behaviour change; engine imports + the open-core
  guard verified.
- Kept **unchanged by design** (non-exposed; renaming would break data/config or
  tool references): the MCP server key + `mcp__plot__` tool names, the
  `.noory/plot/` data directory, `PLOT_*` / `VITE_PLOT_*` env vars, and
  `plot:*` localStorage keys.

## [0.122.0] — 2026-06-30

### Changed

- **Renamed the engine package `plot_mcp` → `mashbill`** (project-wide naming
  overhaul: consumer app → "novel", open engine → "mashbill" = the whisky grain
  recipe, the open formula everything distils from). Import package
  `plot_mcp`→`mashbill`, distribution + console scripts `plot-mcp`/`plot-mcp-http`
  → `mashbill`/`mashbill-http`, sidecar binary `plot-mcp-*` → `mashbill-*`.
  Wire artifacts regenerated. `PLOT_*` env vars unchanged (brand layer, later).

## [0.121.0] — 2026-06-28

### Added

- **The coach can ADD a node, not just fill one** (`D-2026-06-27-B`) — new clobber-safe
  `create_node` MCP tool, mirroring `update_node`: it validates the kind is creatable on the
  canvas, mints the id and position server-side, applies only the kind's writable content
  fields, and appends one node via an atomic whole-canvas re-validate + write. Generalizes the
  former `create_master` into one creation SSOT. The write playbook gains a create branch —
  propose first, create only on an explicit yes. Guard: `tests/test_create_node.py`.

### Fixed

- **External canvas changes refresh the screen automatically again** (`D-2026-06-28-A`) — a
  coach write (or an edit from an external editor) landed on disk but the open canvas didn't
  update. The file-watcher's change descriptor still assumed the pre-`D-2026-06-21-AB` folder
  layout, so on the current flat layout it mislabeled every change (the project id carried the
  canvas kind; the canvas kind was dropped) and the viewer skipped the refetch. It now reads
  the flat layout and resolves the project id from `project.json`. This corrects the "reload
  already worked" premise of `D-2026-06-26-D`. The function had **zero tests** — now pinned by
  `tests/test_broadcast_describe.py`.

## [0.120.3] — 2026-06-27

### Changed

- **No need to select a node first for a unique kind** (`D-2026-06-27-A`) — asked
  "why must I pick the circle?". The coach now writes to the node you *mean*: the
  selected one, or, for a kind there's only one of (the mission, the identity), it
  finds it itself — no manual selection. It only asks "which one?" when several of
  the same kind exist (e.g. core values) and none is selected. Confirmation is
  unchanged: it still writes only after your explicit yes.

## [0.120.2] — 2026-06-27

### Fixed

- **Coach no longer forgets the conversation or fakes a save** (`D-2026-06-26-F`)
  — first real dogfood surfaced two trust-killers. (1) After an app restart the
  coach lost all memory and **re-asked questions already answered** ("who/what
  does it change" repeatedly), because the saved transcript was never re-fed to
  the fresh session; now a fresh session re-feeds the recent transcript so it
  continues from what's already agreed. (2) The coach **announced "saved ✓"
  while the node was actually empty** (even citing a fake file line); the guard
  now forbids claiming a save unless the write tool truly ran this turn, and
  forbids inventing file paths / "refresh to see it" (the canvas auto-updates).
  Guards: `test_chat_store` (transcript re-feed), `test_chat_system_prompt`.

## [0.120.1] — 2026-06-26

### Fixed

- **In-app coach now actually carries Novel's canvas tools** (`D-2026-06-26-E`) —
  the write tool added in 0.120.0 was unreachable in practice. The coach
  inherited its Novel tool connection from the user's global CLI config, which can
  point at a deleted / older app build — silently leaving the coach with **no**
  canvas tools (exactly the "in-app chat can't write to the canvas" failure).
  The coach is now spawned with the running build's own Novel server attached
  directly (`--mcp-config` + `--strict-mcp-config`), so it always has the canvas
  tools regardless of the global registration, and no longer sees the user's
  unrelated MCP servers. Guard: `test_claude_attaches_own_mashbill_strictly`.

## [0.120.0] — 2026-06-26

### Added

- **The in-app coach writes a confirmed value into the selected node**
  (`D-2026-06-26-D`) — closes the load-bearing gap where the coach could only
  *talk*: it proposed a mission / value / step and told the user to paste it,
  because nothing let it write. New MCP tool **`update_node`** patches one node's
  content (`label` + the kind's typed text) clobber-safely (read → merge writable
  fields → re-validate against the kind → atomic whole-canvas write; visual /
  structural / server fields are rejected; every other node + edge is untouched;
  an absent node id — including the project anchor, which is not a node — errors).
  The per-turn chat context now carries a `[Write target]` block (the ids the
  stateless in-app agent needs) and each selected node's **writable field names**
  (so a *blank* node still tells the coach what to fill — the "mission won't fill"
  case). A `WRITE_PLAYBOOK` in the canvas-scope system prompt tells the coach to
  save on an **explicit** confirmation, then confirm in one line what it saved —
  never before the yes, and ask when nothing / several nodes are selected. Writing
  *after* a confirmation is the completion of build-through-discussion
  (`D-2026-06-16-P`), not silent finalisation. Engine half this release; the file
  watcher already reloads the open canvas on the write. **Known limit:** a coach
  write reaches the viewer as an external change and clears its undo stack
  (recover via git / re-edit). Guards: `tests/test_update_node.py`,
  `tests/test_chat_selection_detail.py`, `tests/test_chat_system_prompt.py`.

## [0.119.0] — 2026-06-26

### Added

- **Chat conversations persist to disk** (`D-2026-06-26-B`) — every chat is now
  saved under the project at `.noory/plot/chat/<scope>.json`, one append-only log
  per scope, written **engine-side** (the user turn when a message is sent, the
  assistant turn on `turn_complete`). So conversations survive an engine/app
  restart, travel with the project, and restore on another machine — closing the
  gap where an in-memory chat was lost when the app restarted. Two new read
  endpoints, `GET /api/chat/conversations` (list, newest first) and
  `GET /api/chat/conversations/{scope}` (full log), back the viewer's
  conversation list + reopen. Engine half this release; the dock list/reopen UI
  pairs with it. **Known limit:** reopening restores the transcript for reading,
  not the live CLI session (continuing starts a fresh turn) — named follow-up.

## [0.118.0] — 2026-06-26

### Added

- **Per-service chat thread** (`D-2026-06-26-A`) — selecting a single service on
  the Services canvas now opens that service's own conversation (`service:<id>`),
  alongside the existing per-feature thread. A service is the value-level big
  picture; a feature is its flow design — different conversations, so they key
  different threads and get different coaching: the per-service thread inherits
  the Services Planning/value framing, the per-feature thread keeps its Execution
  flow framing. Drilling into a feature still keys `feature:<id>`; deselecting
  returns to the canvas-wide `services` thread. The chat tab shows the service's
  name. Engine: `service:<id>` accepted by `is_valid_scope`; framing,
  cross-canvas registry, and active-canvas map extended to the `service` base.
  Viewer: scope derivation in `lib/chatScope.ts` (pure, unit-tested), `ChatScope`
  type, and the per-service tab label.

### Changed

- SPEC conversation-scope section corrected the stale `service_detail` naming to
  the current `feature:<id>` wire scope (renamed in D-2026-06-20-J).

## [0.117.2] — 2026-06-24

### Changed

- **Coach output hygiene** — the in-app / MCP coaching system prompt gains two
  guideline principles (not scripted lines). The agent now keeps its read/ask
  machinery out of sight: it no longer narrates its tools, a read that didn't
  land, or "what I'm certain of" (the mechanism leak seen on the first Gate-3
  dogfood), and it frames an empty canvas as a fresh start rather than a gap to
  announce. Warmth is kept light — it leads with the one question instead of
  stacking reassurances. Content SSOT = `docs/concepts/ai-collaboration.md` §0.1
  (⑥⑦). See **D-2026-06-24-J**.

## [0.117.1] — 2026-06-24

Docs-only (engine binary unchanged) — logs a viewer-side fix + extension that
shipped in the `plot` repo. See **D-2026-06-24-G** follow-up.

### Fixed (viewer, plot repo)

- Service-inspector pick-OR-create was wired to the wrong canvas instance
  (FeatureDetailCanvas, not the main ServicesCanvas), so the inline "create"
  never appeared on the service inspector. Now wired to the main canvas.

### Added (viewer, plot repo)

- The Feature canvas's **actor anchor** (`ActorRefPicker`) gains the same inline
  "create a new actor" affordance (D-2026-06-19-C), via the masters endpoint —
  no more "create one on the Actors canvas first" dead-end. Viewer 1017 green.

## [0.117.0] — 2026-06-24

### Added

- **Node name-search** (**D-2026-06-24-I**) — new MCP tool
  `search_project_nodes(project_path, project_id, query)`: a case-insensitive
  label scan over **every** canvas (singletons + feature details), returning up
  to 20 `{id, kind, label, canvas}` hits. The "name" leg of the context
  entry-point chain (selection → map → **name** → semantic; D-2026-06-20-P §1.2),
  so the agent can jump to "the comment feature" even when it's on another
  canvas. The hallucination guard now names the tool. A plain label index, not
  vector search (the data is already a graph). Engine 648 green.
  `mashbill/node_search.py` + `tests/test_node_search.py` (6).

## [0.116.1] — 2026-06-24

### Changed

- **Context-provider seam landed** (**D-2026-06-24-H**, implements D-2026-06-17-L).
  The per-turn Layer-2 assembly (canvas map → cross-canvas registry → selected
  detail) is now one function `build_turn_preamble`; the chat endpoint shrinks to
  "build preamble + system prompt". Behavior-preserving — the current body is the
  CAG implementation; a future RAG / graph-traversal provider (D-2026-06-20-P)
  swaps this one function's internals without touching callers. Engine 642 green.

## [0.116.0] — 2026-06-24

Pick-OR-create reference masters (D-2026-06-24-G, wiring D-2026-06-19-C). The
Services inspector's reference chips can now create a missing actor / core_value
/ identity inline, instead of forcing the user to leave the flow and draw it on
the upstream canvas first.

### Added

- **`POST /api/projects/{id}/masters`** `{kind, label}` (kind ∈ actor /
  core_value / identity) — creates a **lightweight master** (name only, deepened
  later by its home-canvas coach) on its home canvas (actor → Actors, core_value
  / identity → Foundation), positioned so fresh ones don't stack, and returns its
  id. The engine owns the home-canvas + positioning (`mashbill/masters.py`) so
  the viewer never writes across the canvas boundary. `tests/test_masters.py` (8).

### Notes

- Viewer half (RefChips inline-create + threading + cache refresh) ships in the
  `plot` repo. Engine 639 green (8 new), mypy / ruff clean. Full click-loop
  verification in the debug `.app` is the user's hands (Gate 3).

## [0.115.0] — 2026-06-24

Chat quality, Phase 3 — the coaching playbooks (`docs/idea/chat/`, Lever 3). The
whole product is built through the chat coach, so the per-canvas coaching script
is the load-bearing content; this wires the already-decided interviews into the
system prompt and gives the external-agent path the same prompt as in-app.

### Changed

- **Per-canvas framing is now the full coaching playbook + a shared coach tone**
  (**D-2026-06-24-E**). Each canvas system prompt carries its actual interview —
  Foundation (mission / core-value / identity), Actors (three role families,
  actor≠persona), Services (5-slot JTBD + promotion test), Feature (happy-path-first
  flow + altitude guard), Entities (identity-not-name dedup) — prefixed by a gentle
  one-question-at-a-time tone + the pick-or-create reference principle. Content
  SSOT: `docs/concepts/ai-collaboration.md` §0–§2.
- **The external-agent MCP path now returns the same coaching system prompt as
  in-app** (**D-2026-06-24-F**). `get_viewer_context`'s `framing` is now
  `build_system_prompt(scope)` (guard + tone + playbook), not a bare one-liner —
  the primary (MCP-first) path is no longer context-poorer than the in-app panel.

### Notes

- Engine 631 green, mypy / ruff clean. Resolves the "Actors coaching set" and
  "MCP-path selection-awareness" design-undecided items.

## [0.114.0] — 2026-06-24

Chat quality, Phase 2 — the context envelope (`docs/idea/chat/`). Phase 1 fed the
agent the selected node + a read-the-canvas guard; Phase 2 gives it the rest of
the picture it's working within, bounded so a large project can't blow the window.

### Added

- **Active canvas map** (**D-2026-06-24-C**, Phase 2a). The chat message now
  leads with a compact map of **every** node on the active canvas (`kind "label"
  (id)`, selected ones marked), read engine-side, so the agent sees the whole
  current screen — not just the selection. Labels only (bodies stay in the
  selection block; deep reads are the agent's MCP-fetch job); capped at 60 nodes.
  Replaces the wire-label selection header when the canvas reads cleanly.
- **Cross-canvas registry** (**D-2026-06-24-D**, Phase 2b). On the `feature` and
  `services` scopes — where design work references actors / entities — the
  message lists the **existing** actors and entities (label + entity summary) so
  the agent references them instead of minting a duplicate (글 / 게시물 / 포스트
  as three entities). Capped at 40 each; other scopes skip it to spare the window.

### Notes

- Engine 623 green, mypy / ruff clean. In-app only; MCP-path parity is Phase 3.

## [0.113.0] — 2026-06-24

Chat quality, Phase 1 — feed the starving in-app agent (`docs/idea/chat/`). The
in-app `-p` agent hallucinates because it is context-starved, not because of the
`-p` mode; these two levers give it authority + the project's actual content.

### Added

- **Selected-node content injection** (**D-2026-06-24-B**, Lever 1a). The engine
  now reads the selected nodes' actual typed text (mission statement / body,
  core_value definition, …) and injects a `[Selected node details]` block into
  the chat message, so "polish this mission" reaches the agent **with the mission
  text** instead of inventing one. Read engine-side (`mashbill/chat_selection.py`)
  via `read_canvas`, keyed off the single project under the data root; the
  renderer is generic (non-empty, non-structural text fields) so new kinds need
  no per-kind branch. Fails safe — no project / missing canvas / absent id all
  yield nothing rather than a wrong detail. In-app only.

### Changed

- **Per-canvas framing is now an authoritative system prompt + hallucination
  guard** (**D-2026-06-24-A**, Lever 2). The Layer-3 framing moved out of the
  user message into a real system prompt, and a constant guard ("ground every
  claim in the given context; read the canvas with your mashbill MCP tools or ask;
  never invent project details; resolve 'this' to the selected node") now ships
  on every scope. claude delivers it via `--append-system-prompt`; codex (no
  such flag) prepends it to the message. The user message is now
  `context → selection detail → user text`. This is the cheapest, highest-leverage
  anti-hallucination lever. In-app only — MCP-path parity is a Phase-3 follow-up.

### Notes

- Engine 614 green, mypy / ruff clean. Verification of the actual hallucination
  drop needs a real CLI in the debug `.app` (Gate 3) + the Phase-0 adversarial
  set; the unit tests pin the structural causes (command assembly + content
  injection).

## [0.112.2] — 2026-06-23

### Fixed

- **In-app Codex chat no longer hangs with no response** (**D-2026-06-23-F**).
  The chat subprocess spawn set `stdout`/`stderr` but left `stdin` inherited, so
  the child got the engine sidecar's stdin (never at EOF). `codex exec` reads
  stdin for "additional input" even when the prompt is an arg ("Reading
  additional input from stdin..."), so it blocked forever → the turn produced no
  response. Spawn now passes `stdin=DEVNULL`, giving every provider an immediate
  EOF (the prompt is always an arg; no provider should read stdin). Independent
  of the v0.112.1 Claude flag bug — that one errored, this one silently hung.
  Verified `codex exec --json` itself returns fine + the parser already matches
  its event shape; the hang was purely the open stdin. Engine 599 green.

## [0.112.1] — 2026-06-23

### Fixed

- **In-app Claude chat no longer dies on an unknown CLI flag** (**D-2026-06-23-E**).
  The `claude -p` spawn passed `--exclude-dynamic-system-prompt-sections`, which
  is **not a real claude CLI flag** — it was assumed by D-2026-06-21-I and never
  verified. The installed CLI (2.1.17) rejected it with `error: unknown option`,
  so every Claude chat turn (any model, incl. Opus) failed before producing
  output. Removed the flag. Workspace grounding (the actual goal of D-2026-06-21-I)
  is unaffected: it rides on `--setting-sources local` + the
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY` spawn env; the removed flag was only a token
  nicety (keeping cwd/env/git out of the system prompt) the CLI can't do. All
  other spawn flags verified against `claude --help`. Engine 598 green.

## [0.112.0] — 2026-06-23

### Fixed

- **Service releases (`vS`) now anchor to the project mission** (**D-2026-06-23-D**).
  `publish_service` built `refs.anchors` from only `core_values` + `identity`, never
  the mission — so a mission change in a `vP+1` snapshot would propagate to no
  service at all, even though the mission is the project's single essence (VISION)
  that every service stands on. The manifest now always carries
  `anchors.mission = "mission"` (guarded by `"mission" in vP`, which the foundation
  invariant — ≥1 mission node — guarantees). Aligns the code with the format-f.md
  §3.2 example, which already showed the mission anchor. Surfaced by the mashbill↔Solera
  pipeline dogfood. `format_f_version` stays 1 (additive). Engine 598 green.

## [0.111.0] — 2026-06-23

### Fixed

- **Debug channel (`/api/debug`) restored under the auth seam** (**D-2026-06-23-C**).
  The `PLOT_AUTH_TOKEN` enforcement gated everything except `/api/health`, so the
  viewer's debug probe (a plain unauthenticated `fetch`) was 401'd and snapshots
  never landed — the WKWebView introspection bridge was dead. `/api/debug` is now
  in the auth open-paths set: it's dev-only (registered only under `PLOT_DEBUG=1`),
  in-memory, and localhost-bound, so the probe POST + the agent's GET work without
  the per-launch token. Harmless in release builds (the route isn't registered).
  Engine 597 green.

## [0.110.0] — 2026-06-23

### Changed

- **Codex reasoning effort is a separate control, not baked into the model id**
  (**D-2026-06-23-B**, reverses D-2026-06-22-C). `parse_codex_models` now emits
  ONE bare entry per model (`id` = slug) carrying its `supported_reasoning_levels`
  as a separate `ModelOption.efforts` list, instead of expanding into combined
  `<slug>:<effort>` entries. The viewer picks model + effort independently and
  recombines them into the `<slug>:<effort>` form `CodexProvider` already splits
  — so `CodexProvider` is unchanged. Engine 596 green, mypy strict + ruff clean.

## [0.109.0] — 2026-06-23

### Removed

- **Gemini (agy) chat provider temporarily removed** (**D-2026-06-23-A**), re-add
  in October — untestable for now (user direction). Dropped from the engine:
  `ProviderName` literal + `_PROVIDERS` entry (`mcp_registration`), the
  `chat_providers/gemini.py` driver, `GeminiProvider` wiring (`chat_session`),
  the `agy models` catalogue branch + `parse_agy_models` (`chat_models`), and
  the gemini cases in the mcp/chat endpoint validation sets. The provider impl
  lives in git history; restoring the literal + `_PROVIDERS` entry +
  `GeminiProvider` brings it back. Claude Code + Codex unaffected.
  Engine 596 green, mypy strict + ruff clean.

## [0.108.0] — 2026-06-23

### Removed

- **Per-node publish backend retired** (INT-g ⓒ engine, **D-2026-06-22-H**). In
  format F a node is published as an element inside its `vP` / `vS` bundle, never
  on its own, so the whole per-node publish subsystem is gone:
  - deleted modules `node_publish.py` (publish/unpublish/dirty/version-bump),
    `md_publish.py` (per-node MD + `can_publish`), `propagation.py` (MINOR
    propagation walk).
  - removed HTTP endpoints `POST …/nodes/{id}/publish`, `POST …/nodes/{id}/unpublish`,
    `GET …/nodes/{id}/published`, the MCP `publish_node_tool`, and the canvas
    GET/PUT `_dirty` response decoration.
  - removed the now-orphaned git helpers `publish_snapshot` / `ensure_clean_working_tree`
    / `find_latest_publish_commit` / `revert_publish`.
  - dropped ~100 obsolete tests across 7 files; engine 611 green, mypy strict + ruff clean.
- **Kept (deferred):** the vestigial node `version` / `_publish_baseline` fields stay
  for now — removing them is a wire-contract change (schema regen across repos) with no
  user value, tracked separately. The blueprint publish (`POST …/publish`, semver + git
  tag) stays — it is the `vP` freeze mechanism.

## [0.107.0] — 2026-06-22

### Added

- **format F publish reachable over HTTP** (INT-g first step, **D-2026-06-22-G**).
  Two POST endpoints mirror the existing MCP tools so the viewer / any HTTP
  client can trigger a format F publish:
  - `POST /api/projects/{id}/publish/snapshot` → freezes the `vP` project
    snapshot, returns the manifest (404 if the project is unknown).
  - `POST /api/projects/{id}/services/{service_id}/publish` → freezes a `vS`
    service release (404 project/service not found; **409** for the bootstrap
    gate "no vP yet" and the refs-integrity gate "ref does not resolve in the
    based_on vP").
  Thin wrappers over the tested `format_f` functions; the viewer publish UI and
  per-node publish retirement remain the gated follow-on. Engine 714 green,
  mypy strict + ruff clean.

## [0.106.0] — 2026-06-22

### Added

- **vS bundle now carries its features + UX flows** (completes INT-2, **D-2026-06-22-E**).
  `publish_service` previously froze only the service node into a `vS` release;
  it now also emits every feature nested under the service (directed edge
  `service → feature`) as an owned element (`feature/{slug}`, `flow: true`) with
  a `design/features/{slug}.md` rendering the feature's detail-canvas **UX flow**
  (참여자 + 행동(ordered steps, negative-polarity marked) + 분기(decisions →
  branch-labelled edges) + 참고(ambient notes)). A Solera `realizes: feature/login`
  now resolves into a real Execution-handoff flow instead of a name-only stub.

### Changed

- **Service-release refs roll up entity usage.** The features' steps'
  `ref_entity_ids` collect into the release `refs.entities` (resolved to `vP`
  entity slugs, not copied). The refs-integrity gate (format-f.md §1.4) now also
  covers those entity refs, and all ref validation runs **before any file is
  written** (validate-before-write — a dangling ref refuses the publish cleanly).
- **Richer format F design rendering, for the external agent reading it**
  (**D-2026-06-22-F**). The published `design/*.md` files now carry the actual
  content, not stubs:
  - **foundation.md** renders each node's *primary* typed field
    (`mission.statement` / `core_value.definition` / `identity.description`) —
    not only `body` — grouped under 미션 / 코어 밸류 / 아이덴티티 sections with a
    framing header. The element hash now includes that primary field, so an
    essence change is caught by the ID-diff.
  - **entities/{slug}.md** renders `summary` (the '무엇을 담나' line). The old
    code read a non-existent `body`, so entity files (and their hashes) were
    **empty** — a latent bug fixed here.
  - **actors.md** adds a 관계 (주고받음) section rendering the edges between
    actor nodes (label / action_verb), so the agent sees the value economy, not
    just the cast.
  - **service.md** surfaces what the service stands on in its `vP` (참여 액터 /
    지키는 가치 / 정체성 결, by slug), so the file reads standalone.
  Engine 708 green, mypy strict + ruff clean.

## [0.104.0] — 2026-06-22

### Added

- **format F reachable on the MCP surface** (INT-f) — `publish_project_snapshot_tool`
  and `publish_service_tool` expose the format F write half on the agent-facing
  MCP path (VISION's 주경로). Thin wrappers over the tested `format_f` functions;
  reachability smoke-tested. The viewer/HTTP trigger + per-node publish
  retirement remain a follow-on (they would otherwise remove the only
  user-facing publish UI before format F has one). Engine 699 green.

## [0.103.1] — 2026-06-22

### Added

- **format F write-side contract guard + Phase P pinned** (INT-1c, **D-2026-06-22-D**).
  `tests/test_format_f.py::test_manifest_contract_shape_is_pinned` pins the
  manifest shape + `FORMAT_F_VERSION` mashbill emits, in lock-step with Solera's
  `intake.SUPPORTED_FORMAT_F_VERSION` (a producer change that drops a field now
  fails before it reaches Solera). The 2-layer publish decision (vP project
  snapshot + vS service release, slug-referenced, per-node coexists/retires
  later) is pinned in `DECISIONS.md` D-2026-06-22-D; the contract spec lives in
  `noory-workspace/docs/specs/format-f.md` and `storage-publish.md` gains a format F
  section.

## [0.103.0] — 2026-06-22

### Added

- **format F export engine — mashbill "write" half of the mashbill↔Solera contract**
  (Phase P / INT-2, walking-skeleton scope). New `mashbill/format_f.py` writes
  the 2-layer published bundle defined in `noory-workspace/docs/specs/format-f.md`:
  - `publish_project_snapshot` → `published/_project/vP{N}/` freezes the shared
    structure (本質 / Actors / Entities).
  - `publish_service` → `published/{slug}/vS{N}/` freezes one service (5칸 +
    refs), pinning `based_on: vP` and referencing shared elements **by slug, not
    by copy**.
  - **Slug minting** via a per-project `_slugs.json` registry (P-4 = explicit
    slug): keyed on node id, so a slug is stable across label changes.
  - Two write-boundary gates: **bootstrap** (a `vS` requires a `vP`) and
    **refs-integrity** (every ref must resolve in the based_on `vP`).
  Built **alongside** the existing per-node publish (`node_publish.py`), not a
  replacement — per-node retirement + the formal DECISIONS pin land later
  (INT-1c). 6 tests in `tests/test_format_f.py`; engine 697 green.

## [0.102.0] — 2026-06-22

### Changed

- **In-app chat: gemini transport → `agy` (Antigravity)** (**D-2026-06-22-A**).
  The `gemini` provider now drives `agy -p --dangerously-skip-permissions`
  (plain-text passthrough, no `stream-json`) and is **stateless** — agy exposes
  no per-thread resume on stdout and `--continue` is most-recent-global (would
  cross Novel's per-scope threads). The provider name stays `gemini`; presence
  detection now looks for the `agy` binary.
- **Chat model selector is populated from each CLI's live catalogue**
  (**D-2026-06-22-B**, reverses D-2026-06-16-C, which went stale on arrival).
  New `GET /api/chat/models?provider=`: codex → `~/.codex/models_cache.json`,
  gemini → `agy models`, claude → its static aliases. Fail-soft to an empty
  list (selector still offers default + Custom…). `mashbill/chat_models.py`.
- **Codex reasoning effort as combined model×effort entries**
  (**D-2026-06-22-C**). The codex catalogue expands each model per
  `supported_reasoning_levels` (id `<slug>:<effort>`, e.g. `gpt-5.5:high`);
  `CodexProvider` splits it into `--model <slug> -c model_reasoning_effort=`.

### Notes

- **Requires a sidecar rebuild** for the standalone `.app`.
- The viewer half ships in the `plot` app repo (selector fetches the catalogue;
  `MODEL_SUGGESTIONS` removed; plus the `chat.scope.entities` i18n fix).
- Follow-ups filed (ROADMAP): agy multi-turn continuity, agy MCP registration
  (`agy mcp`), codex cache private-format coupling.

## [0.101.0] — 2026-06-22

### Changed

- **Flat storage: drop the `{project_id}/` folder layer** (**D-2026-06-21-AB**,
  builds on D-2026-06-21-AA). The lone project's files now live directly under
  `.noory/plot` (`.noory/plot/project.json`, `.noory/plot/foundation/canvas.json`,
  …) — no intermediate `{project_id}/` folder. The layout concentrates in
  `storage._project_dir` (returns the root itself when no nested `project.json`
  exists; honours a legacy nested folder only while it survives), so every
  derived path followed once the few self-built paths were routed through it.
  `resolve_plot_root` lazily flattens a single nested project up to the root on
  open; a forbidden multi-project root is left for the user to reconcile.
  `_ensure_project` now verifies the stored `id` matches the requested one (flat
  addresses the lone project by the root, so a wrong id 404s instead of
  leaking it). **Requires sidecar rebuild** for the `.app`.

## [0.100.0] — 2026-06-21

### Changed

- **One project per `.noory/plot` dir (one-project-per-dir)** (**D-2026-06-21-AA**,
  narrows D-2026-06-12-A). `create_project` now rejects a *second* project under a
  root that already holds one — `enumerate_projects(plot_root)` non-empty →
  `FileExistsError`, which the create endpoint maps to **409**. It is the single
  chokepoint, so this covers both the viewer (`POST /api/projects`) and the MCP
  `create_project_tool`. Multiple services in a monorepo go in **sibling
  directories**, each with its own `.noory/plot`. The guard is on the **write**
  path only — `enumerate_projects` / `discover_projects` still read N projects, so
  pre-existing multi-project roots and recursive sibling-dir discovery are
  unaffected. **Requires sidecar rebuild** for the `.app`.

## [0.99.0] — 2026-06-21

### Added

- **Chat shows the CLI's actual default model when it reports one** (**D-2026-06-21-Z**).
  The model selector's "default" option now reads e.g. `default · claude-opus-4-8`
  instead of a bare `default`, once the CLI reports its model. The claude-code
  provider parses the stream-json `system`/`init` frame's `model` and emits a new
  `ChatStreamEvent(type="meta", model=…)`; the viewer records it and relabels the
  default option. Asymmetric by design — only claude-code reports its model, so
  codex / gemini keep a plain `default`. Known after the first turn; reset on
  provider change; an explicit override is unaffected.

### Fixed

- **A canvas with a dangling edge on disk now opens instead of 400'ing**
  (**D-2026-06-21-X**, follow-up to D-2026-06-21-R). `read_canvas` strips any edge
  whose endpoint node is absent (`_drop_dangling_edges`) before validation, so a
  `canvas.json` corrupted by a node removed without its incident edges still
  loads. The synthetic project anchor stays a valid endpoint. The write path is
  unchanged — it still rejects dangling edges (the viewer prunes pre-save).

## [0.98.10] — 2026-06-21

### Fixed

- **In-app chat is grounded only in the workspace** (**D-2026-06-21-I**). The
  `claude -p` agent was pulling in parent / global `CLAUDE.md` (incl. the Novel
  repo's own dev instructions) + the user's auto-memory. The spawn now passes
  `--setting-sources local` + `--exclude-dynamic-system-prompt-sections` and
  sets `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. OAuth/subscription auth + the `plot`
  MCP are preserved (this is NOT `--bare`). New `ChatProvider._spawn_env()` hook
  threads the env through the spawn.

## [0.98.9] — 2026-06-21

### Changed

- **Initial Foundation layout** (**D-2026-06-21-H**) — a new project seeds Mission
  on top, Core Value on the left, Identity on the right (around the centre
  anchor), with a directed edge from the project anchor to each. Was: Core Value
  on top, Mission on the left, no edges. Seed-only — existing projects keep
  their layout.

## [0.98.8] — 2026-06-21

### Fixed

- **In-app Claude Code dead-ended on mashbill MCP tool permissions** (**D-2026-06-21-C**).
  Headless `claude -p` can't show a permission prompt, so the agent narrated
  "press Allow" with nothing to press whenever it called a Novel tool. The spawn
  now passes `--allowedTools mcp__plot__*` — auto-approving the user's **own**
  mashbill MCP tools (scoped; Bash / Write / filesystem keep default behaviour, so
  the agent can't silently touch anything outside `.noory/plot`). Verified flag
  against `claude --help` 2.1.176 + the permissions docs. Pinned by
  `test_chat_session`.

### Removed

- **The in-app Claude Code dual-billing warning banner** (**D-2026-06-21-D**,
  app-repo UI). Removed per user request; the per-token billing fact is
  unchanged, just no longer surfaced as a persistent banner.

## [0.98.7] — 2026-06-21

### Fixed

- **In-app Claude Code chat doubled every reply** (**D-2026-06-21-B**). The
  `stream-json` parser counted text from both the partial `content_block_delta`
  frames AND the full `assistant` recap message; with `--include-partial-messages`
  both arrive, doubling the text ("…살펴볼게요.…살펴볼게요."). The partials are now
  the single streaming source; the recap is ignored. Pinned by
  `test_claude_stream_parse` + updated `test_chat_session` fixtures.

## [0.98.6] — 2026-06-20

### Changed

- **Entity↔entity edges pinned to `flow`** (entity follow-up step 7,
  **D-2026-06-20-Q** / D-2026-06-17-J) — an edge on the entities canvas is a
  rough, directed conceptual link (사용자 —쓴다→ 글), no FK / cardinality, user-
  editable. No behaviour change (it already took the `flow` fallthrough);
  `classify_edge` now documents the intent and `test_edge_semantics` pins it so
  a future classify change can't silently re-route entity edges. (Mirror in the
  app's `edgeSemantics.ts` + vitest.) **Entity follow-up complete** — chips
  (step 6 authoring) + back-ref endpoint + edges (step 7); AI-surfacing (step 8)
  was already wired (D-2026-06-20-K).

## [0.98.5] — 2026-06-20

### Added

- **Entity back-reference endpoint** `GET /api/projects/{id}/entities/{entity_id}/usage`
  (entity follow-up step 6, **D-2026-06-20-Q**) — the read-only "어디서 쓰이나":
  which features (and their steps) reference an entity. New `entity_refs.entity_usage`
  scans every feature detail canvas's `step.ref_entity_ids` server-side (the viewer
  loads canvases lazily, so a complete reverse index can't be computed client-side).
  Pure derived projection; nothing is authored.

### Notes

- Engine **653 tests green**. The viewer half (entity inspector "어디서 쓰이나"
  view) ships in the `plot` app repo.

## [0.98.4] — 2026-06-20

### Added

- **`step.ref_entity_ids`** (entity follow-up, **D-2026-06-20-Q**) — a feature
  action references the entities it operates on via an id-array (chips →
  entities registry), mirroring the service inspector's `ref_*_ids`. Purpose =
  AI-maintained derived data map ("what data the product has + 어디서 쓰이나"),
  not flow visualisation; the reference is a lightweight declaration on the
  action, not a flow-participant node. Additive wire field (loss-free default
  `[]`); codegen regenerated (`StepJson`). The viewer half (chip picker +
  entity back-reference view) ships in the `plot` app repo.

### Notes

- Engine **649 tests green**. Entity edges (step 7) + the back-ref view land
  next.

## [0.98.3] — 2026-06-20

### Added

- **`/api/health` exposes `schema_version` + `engine_version`** (Phase D part c,
  **D-2026-06-20-O**) — additive, backward-compatible fields alongside
  `status`/`service`. They feed the app's boot-time wire-compat banner: the
  viewer compares the engine's `schema_version` against its committed
  `wire-contract.json` and warns on mismatch (a version-skewed `.app` would
  otherwise silently mis-parse canvases). Engine-unreachable does **not** fire
  the banner; an older engine that omits the field is treated as a mismatch.

### Notes

- Engine **648 tests green** (+`test_health_exposes_compat_versions`). The
  viewer half (compat check + banner + i18n) ships in the `plot` app repo.
  Phase D part (b) sidecar git-tag pin + `engine_version` build stamp remains.

## [0.98.2] — 2026-06-20

### Changed

- **Engine version is now a single source** (Phase D part a, **D-2026-06-20-N**).
  The four stale copies (`pyproject` `0.1.0`, `__init__` `0.1.0`,
  `schema_export.PLOT_VERSION` `0.14.18`, `plugin.json`) collapse to
  `mashbill/__init__.py::__version__`. `pyproject` derives it via hatchling
  (`dynamic = ["version"]`); `PLOT_VERSION` re-exports it; `plugin.json` is
  pinned equal by `tests/test_version_parity.py`. Gate 4 bumps `__init__` +
  `plugin.json` together going forward. `_meta.json plot_version` now reflects
  the real version (was stamping `0.14.18`).
- **`SCHEMA_VERSION` stays decoupled** from the package version on purpose —
  it is the wire-contract schema version (`2`), the value the upcoming runtime
  compat banner (Phase D part c) gates on, and changes on its own cadence.

### Notes

- Engine **647 tests green**. Phase D parts (b) sidecar git-tag pin +
  `engine_version` stamp and (c) runtime `schema_version` compat banner follow.

## [0.98.1] — 2026-06-20

### Changed

- The generated `wire.gen.ts` header now documents the **cross-repo** regen
  command (`PLOT_VIEWER_ROOT=<app>/viewer uv run python -m mashbill.ts_codegen`)
  — the bare `uv run python -m mashbill.ts_codegen` is a no-op post-cut
  (D-2026-06-20-M). Paired regen of the committed app artifact verified
  idempotent; the app's vitest stays green (929) against the new header.

## [0.98.0] — 2026-06-20

### Removed

- **`noory-ai/plot/viewer` (295 files)** — the irreversible open-core cut
  (**D-2026-06-20-M**, executing **D-2026-06-20-L**). The visual canvas is the
  paid app's value and now lives only in the proprietary `plot/` repo; this
  MIT engine is headless. `find_viewer_dist()` already returns `None`
  gracefully (headless mode), so no runtime change was needed.

### Changed

- **Codegen viewer-write is env-only.** `ts_codegen.write_wire_ts` and
  `schema_export._write_wire_snapshots` no longer hardcode the app's path —
  they resolve the viewer target only from `PLOT_VIEWER_ROOT` (new
  `ts_codegen.wire_ts_path()` / `schema_export.viewer_contract_path()`, `None`
  when unset). Unset → no-op for the viewer artifact; the engine still always
  writes its own `mashbill/wire_contract.json` self-copy. Dev cross-repo regen:
  `PLOT_VIEWER_ROOT=/abs/path/to/plot/viewer uv run python -m mashbill.ts_codegen`
  (+ `… schema_export --wire`) — verified idempotent against the committed
  `plot/viewer` artifacts.
- **Four viewer-reading parity tests re-homed** (they die once the viewer
  leaves): `test_ts_codegen` (now an engine-side per-kind interface guard),
  `test_wire_contract` (dropped the monorepo byte-identity test; keeps the
  engine self-copy guard), `test_chat_scope_parity` (engine member-set pin),
  `test_edge_semantics` (engine `{flow, injection, inheritance}` pin). The
  viewer half is guarded by the app repo's vitest against the committed
  artifacts. New `test_codegen_target` pins the env-only resolver.

### Notes

- Engine **643 tests green** after the cut. Phase D (engine version
  unification + sidecar git-tag pin + runtime `schema_version` compat banner)
  is next.

## [0.97.1] — 2026-06-20

### Docs

- Pinned **D-2026-06-20-L** — the viewer physical migration `noory-ai/plot/viewer`
  → `plot/viewer` (open-core boundary): approach (codegen = artifacts committed
  to the `plot` repo; engine pin = git-tag) + the staged execution. Phase-C-
  additive (viewer copied into `plot/viewer`, verified `npm ci` + `tsc` + 928
  vitest green there; `plot` `frontendDist` repointed + LICENSE) landed in the
  `plot` repo. The irreversible cut (remove `noory-ai/plot/viewer`, repoint
  `ts_codegen` / `schema_export` to the committed artifacts, R8 guard) + Phase D
  (engine version alignment + sidecar git-tag pin + runtime compat) follow.

## [0.97.0] — 2026-06-20

### Added

- **`entity` kind + `entities` canvas** (Chunk 2.4, D-2026-06-20-K, implementing
  D-2026-06-17-I / -K). Entities are the product data objects the services act
  on (글 / 댓글 / 결제내역 …) — an AI-maintained registry, populated last.
  - **Kind `entity`** — `EntityNode` with one kind-specific field `summary`
    (the "무엇을 담나?" one-liner; `label` is the name). No ERD fields, no
    relationship fields. Rounded node, pale-cyan `#cffafe`, `database` icon.
    Lean inspector: `label` + `summary`, both writable. Palette = **14 kinds**.
  - **Canvas `entities`** — singleton, allows `{project, entity}`, seeded empty
    (AI-derived / populated last), 4th main tab. `ChatScope` / `CanvasKey` +
    Python ↔ TS scope-parity extended. Canvas kinds = **5**.
  - Full lock-step: Pydantic model, domain class (consumes generated
    `EntityJson`), renderer, inspector, registries, i18n (en + ko), codegen
    regenerated, structural / parity / round-trip guards bumped.

### Notes

- Deferred to follow-ups (out of this scope): the AI-surfacing in-chat proposal
  UI (only the scope framing + wiring landed), feature-action → entity
  references (blocked on FEATURE-canvas work), entity↔entity relationship edges,
  and the read-only back-reference / rough-relationship inspector views.

## [0.96.0] — 2026-06-20

### Changed

- **Wire-string rename `service_detail` → `feature`** (Chunk 2.7 finish,
  D-2026-06-20-J). Completes the rename the v0.95.0 drill rewire deferred. Pure
  rename, no behavioural change. Renamed everywhere across engine + viewer
  (112+ files, zero leftovers):
  - `canvas_kind` value `service_detail` → `feature` (Python `CanvasKind`
    Literal + TS `CanvasKind`).
  - Scope / cache key prefix `service_detail:` → `feature:` (`ChatScope`,
    `CanvasKey`; Python ↔ TS parity green).
  - CanvasDoc field `service_ref` → `feature_ref`; helper
    `list_service_details` → `list_feature_details`.
  - Viewer `detailServiceId` → `detailFeatureId`, `drillIntoService` →
    `drillIntoFeature`.
  - i18n keys `serviceDetail` → `featureDetail`,
    `canvas.tabs.service_detail` → `canvas.tabs.feature` (en + ko symmetric).
  - Components `ServiceDetail{Canvas,Modal,InspectorHost,StencilPanel}` →
    `FeatureDetail*` (files renamed via `git mv`).

### Notes

- The on-disk storage path `services/{id}/detail.json` is unchanged (it never
  contained the `service_detail` string), so no data migration. The `?detail=`
  URL param and the `service` kind / `services` overview are untouched.

## [0.95.0] — 2026-06-20

### Changed

- **Drill rewire — `feature` is the drill target** (Chunk 2.7, D-2026-06-20-I,
  implementing D-2026-06-17-D). On the Services overview, selecting a service
  shows its inspector (no drill); clicking a `feature` drills into its detail.
  `ServicesCanvas` hands `shouldDrillFeature` to the routing brain;
  `App.onMainNodeDrill` drills on `feature`.
- **Detail canvas re-rooted service → feature.** `_ALLOWED_KINDS_BY_CANVAS`
  swaps `service`→`feature` on the detail canvas; the `_detail_canvas_rules`
  validator now requires a root **feature**; `detail_sync` seeds/archives one
  detail **per feature** (was per service) — a service with no features gets no
  detail. Propagation is unchanged (the ancestor walk crosses canvases by
  id-matching, so a feature-rooted detail propagates step → feature → service →
  category automatically). User-facing copy reads **"Feature detail" / "기능
  상세"** (en + ko).
- **v0.1 → v0.2 migration is now overview-only.** v0.1 predates the `feature`
  kind, so the migrator (`_split_services`) produces the services overview and
  creates **no** detail canvases; the legacy sub-service / rule decomposition is
  dropped (re-authored as features post-migration, whose details the live sync
  seeds on open). Removed the now-dead `_detail_actor_ref_seeds` /
  `_v01_to_composition` migrator helpers.

### Notes

- The persisted wire string stays **`service_detail`** (canvas kind, `service_ref`
  field, `service_detail:<id>` keys, `?detail=` param) — now carrying a *feature*
  id. The cosmetic full rename `service_detail`→`feature` is deferred
  (product-gated) to avoid a half-renamed churn; no existing projects ⇒ no data
  migration when it lands.

## [0.94.0] — 2026-06-20

### Removed

- **`metric` / `content` kinds retired** (Chunk 2.1, D-2026-06-20-H). Both sit
  below Novel's action altitude: a `metric` is implied by a flow's result node +
  edge, and `content` (implementation / user-facing artifacts) is the external
  agent's job or is carried by the producing action's edge. Removed across the
  stack: server `MetricNode` / `ContentNode`, the union + `NodeKind` Literal +
  `_ALL_KIND_CLASSES` + `schema_export` map + `models.py` re-exports +
  `migrate_builders` content branch; the viewer `Metric.ts` / `Content.ts`
  domain classes, their node renderers + inspectors, `CompositionList.tsx` +
  `ContentFields.tsx`, the `createBlankNode` cases, both registries, the
  `SketchNode` unions, `types.ts` `NodeKind`, the SERVICE_COMPOSITION metric
  stencil preset, and the service_detail "Value" stencil section (value is the
  service-inspector `ref_value_ids` chips now). `_drop_retired_kinds` strips
  both on read (loss-free). Palette = **13 kinds**.
- **Dead composition-child affordance removed.** `addCompositionChild` and its
  `onAddChild` / `onPatchChild` / `onRemoveChild` prop thread (through
  `useNodeCreation` → `SketchCanvas` → `SketchInspectorBindings` →
  `inspectors/types.ts`) were orphaned when `CompositionList` was deleted in
  v0.93.0; removed here rather than left narrowed-but-dead.
- **Retired-kind i18n swept (en + ko).** Completes the cleanup D-2026-06-20-G
  deferred to doc-sync: the `kind.*` labels for all retired kinds
  (`mission_ref` / `value_ref` / `identity_ref` / `metric` / `content` / the
  `value` relabel) + `kindTag.metric`, the whole dead `composition` object, and
  the orphaned `stencil.section.{composition,values,missions,identityAspects}` +
  `stencil.note.{compositionInsideService,valuesExchanged,dragMission…,dragValue…,dragIdentityAspect…}`
  keys. No retired-kind i18n debt remains.

### Changed

- Codegen artifacts regenerated to the 13-kind contract: `wire.gen.ts`,
  `mashbill/wire_contract.json`, and the viewer snapshot copy.
- Test kind-list / count fixtures reconciled to 13 across `structural-guards`,
  `styles-cursor-baseline`, `cursor-sweep`, `no-god-import`, `entity-roundtrip`,
  `wire-contract`, `nodes/registry`, the two `inspectors.*`, and the
  `domain/round-trip*` suites (several were silently stale, missing
  `feature` / `note` / `decision`; corrected to the true palette).

## [0.93.0] — 2026-06-20

### Removed

- **`mission_ref` / `value_ref` / `identity_ref` kinds retired** (Chunk 2.1,
  D-2026-06-20-G, implementing D-2026-06-17-H). Foundation references are the
  service inspector's chip pickers now (D-2026-06-20-F), not standalone nodes;
  `actor_ref` is the only surviving standalone reference node. Removed server
  models + `_FOUNDATION_REFS`, the viewer domain classes / renderers /
  inspectors / registries / stencil presets, and the **entire FoundationRefPicker
  machinery** (the picker modal + the `pendingFoundationRef` drag-drop state
  thread + the `availableMissions` chain). `_drop_retired_kinds` strips the 3
  from older canvases on read. Palette = **15 kinds**.

## [0.92.0] — 2026-06-20

### Changed

- **`actor_ref` = read-only anchor** (Chunk 2.6, implementing D-2026-06-19-I).
  On the Feature canvas an actor_ref now only marks the flow's subject ("who
  starts / who can"); its inspector shows which actor master it points at (+
  side) read-only, with an orphan re-pick / delete path. Role is edited on the
  Actors canvas; permissions on a `rule`.

### Removed

- **`actor_ref` per-service stake fields** `gives` / `receives` / `motivation`
  / `pain` (supersedes D-2026-06-15-J). Role-level value lives on the Actors
  relationship edges; aggregate value on the service "뭐가 좋아지나?". Discarded
  (no migration). The 4 editor textareas are gone from the actor_ref inspector.

## [0.91.0] — 2026-06-20

### Changed

- **Service inspector → 5 question-titled fields** (Chunk 2.5, D-2026-06-20-F,
  implementing D-2026-06-17-B). 2 typed-text (왜 필요한가? = `problem`, 뭐가
  좋아지나? = `value_created`) + 3 multi-select reference chip lists (누가
  참여하나? = `ref_actor_ids`, 뭘 양보 못 하나? = `ref_value_ids`, 어떤 결로
  다가가나? = `ref_identity_ids`). References are id arrays on the service
  (Option B), rendered as removable chips via the new
  `inspectors/service/RefChips.tsx` (pick-only; pick-OR-create is a follow-up).

### Removed

- **The legacy 9 service fields** (`target_side` / `what` / `scope` / `trigger`
  / `how` / `outcome` / `do` / `dont` / `body`) — **discarded**, no migration
  (no project uses Novel yet; Pydantic drops the old extras on read,
  D-2026-06-20-F). The service inspector's composition (rules / contents) panels,
  the `target_side` color tint, and the shared `DoDontFields` component are gone.

## [0.90.0] — 2026-06-20

### Added

- **`note` kind** (Chunk 2.3, D-2026-06-20-E, implementing D-2026-06-17-F). A
  canvas-global ambient memo on the Feature canvas ("모바일 우선·본문 500자") —
  a human-read guide. **Edgeless invariant:** a note never participates in an
  edge, enforced both viewer-side (`handleConnect` rejects note endpoints) and
  server-side (`CanvasDoc._notes_are_edgeless`). Field `body`. Full lock-step:
  `NoteNode` + generated `NoteJson` + viewer `Note` class / renderer / inspector
  / registries / i18n (en+ko) / a yellow ambient stencil preset + the edgeless
  guards (`tests/test_canvas_doc.py`). Palette = 18 kinds. The AI-framing
  injection (note bodies → per-canvas `chat_context` framing) is a tracked
  follow-up.

## [0.89.0] — 2026-06-20

### Added

- **`feature` kind** (Chunk 2.2, D-2026-06-20-D, implementing D-2026-06-17-D /
  D-2026-06-19-H). A capability the service offers (글쓰기 / 편집) — a behaviour
  grouping under a service, the **sole drill target**, not an independent value
  unit. Field `proposed` (one-line "무엇을 할 수 있나?"). Full lock-step:
  Pydantic `FeatureNode` + generated `FeatureJson` + viewer `Feature` class /
  renderer / inspector / registries / i18n (en+ko) / a "Feature" stencil preset
  that nests under a service (directed edge service→feature) + the drop-target
  resolver + structural / round-trip / registry guards. Palette = 17 kinds. The
  drill rewire (service→feature) + the `service_detail`→Feature-canvas rename
  ship separately (Chunk 2.7).

## [0.88.0] — 2026-06-20

### Removed

- **`group` kind retired** (Chunk 2.0, D-2026-06-20-C, implementing
  D-2026-06-19-H). Its chunking role moves to the `feature` level; folding a
  busy flow becomes a future **view affordance**, not a node kind. Removed
  server `GroupNode` + the viewer `Group` class / node / inspector / registry
  entries / i18n, and the whole group-folding feature (`groupActions`,
  `groupCollapse`, the Group/Ungroup context menu, the group-membership fold
  path in `useNodesMemo`). The palette is now **16 kinds**, reconciled across
  `_ALL_KIND_CLASSES` + the viewer `KIND_DIRS`/`NODE_RENDERERS`.

### Added

- **Retired-kind drop-on-read migration** (`canvas_io._drop_retired_kinds` +
  `RETIRED_KINDS`). A node of a retired kind (and any edge incident to it) is
  stripped when an older `canvas.json` is read, so projects authored before a
  kind's retirement keep loading — loss-free (retiring `group` drops only the
  container, never its member step/decision nodes). Reused by the remaining
  retirements. Pinned by `tests/test_retired_kinds.py`.

## [0.87.2] — 2026-06-20

### Changed

- **Migration resequenced** (D-2026-06-20-B): the viewer's physical move into
  the `plot/` app repo is deferred until AFTER the Chunk-2 concept code (kind
  add/remove/reform), which now lands in the monorepo first. The schema-parity
  blocker that required move-first is resolved by the v0.87.0 codegen, so the
  concept churn is safer/faster single-repo (rich guards alive, no cross-repo
  paired commits). Landing path when the move happens = `plot/viewer/`. No
  architecture change — only the order of realizing it.

## [0.87.1] — 2026-06-20

### Added

- **Transport-isolation guards** (`tests/test_transport_isolation.py`, migration
  Phase B, D-2026-06-20-A). TECH_REVIEW C2 confirmed the engine's headless
  4-layer seam but flagged that no test pinned it. Three guards now lock it: the
  pure-domain modules import no transport library (verified in a fresh
  interpreter so transitive leaks are caught); `mcp_tools` does not import the
  HTTP-for-viewer stack; and `create_http_app()` builds with no viewer dist
  present (the headless path Phase C — the viewer move — depends on). No
  behaviour change; the engine already degraded gracefully without a viewer
  dist (`http_app.py:224-228`).

## [0.87.0] — 2026-06-20

### Changed

- **Viewer wire types are now GENERATED from the engine schema** (migration
  Phase A, D-2026-06-20-A, TECH_REVIEW step 1). New `mashbill/ts_codegen.py`
  emits `viewer/src/domain/wire.gen.ts` (`BaseFieldsJson` + one `{Kind}Json`
  per kind) from the Pydantic models; every per-kind domain class now imports
  its wire interface from `./wire.gen` instead of hand-declaring it inline. The
  hand-written domain *classes* (`fromJson` / `toJson` / invariants) are
  untouched — only the wire shape is generated. This makes the server↔viewer
  contract survive the repo split: the old cross-side regex parity
  (`test_schema_parity.py::test_per_kind_field_parity`) read both repos and
  died on split; the generated artifact travels with the viewer and the app
  build regenerates it from the pinned engine.

### Added

- `tests/test_ts_codegen.py` — pins committed `wire.gen.ts` byte-for-byte
  against fresh generation (a model change without `uv run python -m
  mashbill.ts_codegen` fails here).

### Removed

- `test_schema_parity.py` cross-side regex parity (`test_per_kind_field_parity`
  + `test_base_fields_ts_matches_canonical_set`) — superseded by codegen drift +
  the viewer `wire-contract.test.ts` (both repointed at `wire.gen.ts`). The file
  keeps the Python-only guards (`test_export_map_covers_union`, base-field
  anchor). `no-god-import.test.tsx` invariant 3 now verifies the generated
  interface + class consumption + no inline re-declaration.

## [0.86.2] — 2026-06-20

### Fixed

- **`decision` / `group` registered in the schema-export map** (migration
  Phase A, D-2026-06-20-A). Both kinds had shipped in the `SketchNode` Pydantic
  union + the viewer for months while missing from
  `schema_export._ALL_KIND_CLASSES` (the "15/17 drift") — so they were absent
  from generated `schema/` files and unguarded by schema-parity. The export map
  is now the registered projection of the union (17 kinds), and
  `tests/test_schema_parity.py::test_export_map_covers_union` guards against
  re-omission. `wire_contract.json` (both copies) regenerated to 17 kinds. This
  is the registration half only; **`group` retirement is a separate concept
  decision** (Chunk 2.0), not done here.

## [0.86.1] — 2026-06-20

### Fixed

- **SessionStart hook resolved no docs** (D-2026-06-19-J). `session_start.py`
  assumed VISION.md, DECISIONS.md, NEXT_SESSION.md share one `docs/` dir, but
  after the 2026-06-18 doc move VISION lives in the cross-repo root `docs/`
  while DECISIONS/NEXT_SESSION stay in the plugin `docs/`. The hook now resolves
  the two roots separately and matches the Korean `## 본질` essence heading, so
  the session anchor (essence + last 5 decisions) surfaces again.

### Changed

- **Design/definition/spec docs consolidated to `noory-workspace/docs/`** (single
  SSOT — D-2026-06-19-J / D-2026-06-20-A). `SPEC.md` / `CONCEPTS.md` /
  `DOMAIN.md` / `CHAT_ARCH.md` / `node-format/` now carry a redirect header
  pointing at the root canonical source (definitions live there; these stay for
  code-near / historical reference). `plot/CLAUDE.md` gains a canonical-source
  pointer. New decisions D-2026-06-19-G…J + D-2026-06-20-A (mindmap dropped /
  `feature` = behaviour grouping / `actor_ref` = read-only anchor / docs
  consolidated / open-core system architecture).

## [0.86.0] — 2026-06-16

### Changed

- **Chat now syncs to the active project (× canvas)** (D-2026-06-16-G).
  `ChatDock` is keyed on the active project's path instead of the workspace
  root, so switching projects in a monorepo workspace switches the chat's
  threads + provider + model (each project owns its `.noory/plot`). Previously
  the chat was workspace-wide and didn't follow the project.

### Fixed

- **Chat selection context was inert on the service-detail canvas**
  (D-2026-06-16-F). The detail canvas now reports its selection
  (`onSelectionChange`) and the dock reads the active detail canvas's nodes, so
  the per-turn selection context (Layer 2) resolves against a selected detail
  node. Both guarded by `viewer/tests/chat-selection-detail.test.ts`.

## [0.85.1] — 2026-06-16

### Fixed

- **Inspector MD editor was a white island in dark mode** (D-2026-06-16-E).
  `MdTextarea`'s CodeMirror theme hardcoded a white background + slate/indigo
  border/focus colours; it now uses Novel's CSS tokens (`rgb(var(--surface))` /
  `--fg` / `--line-strong` / `--accent` + themed caret/selection), so every
  typed-text field in the Inspector reads correctly in dark mode. Guarded by
  `viewer/tests/md-textarea-theme.test.ts`.

## [0.85.0] — 2026-06-16

### Changed

- **Chat dock reshaped to a modern chat-app layout** (D-2026-06-16-D). The
  **model selector is now the prominent control at the top** of the chat (a
  dropdown + "Custom…" fallback), with provider connection as a compact chip
  beside it. The message log is now **left/right-aligned bubbles** (assistant
  left, user right, error tinted) instead of full-width boxes, and the input
  is a single **rounded composer** with an integrated circular send button.
  Familiar chat UX within Novel's existing theme tokens (no hardcoded colours,
  no new font); all behaviour, a11y, and i18n preserved.

## [0.84.1] — 2026-06-16

### Changed

- The chat provider bar now always shows the model state (`Provider · <model>`
  or `Provider · default` when no override) so "which model is in use" is
  visible at a glance even before a model is picked — completes D-2026-06-16-C ①.

## [0.84.0] — 2026-06-16

### Added

- **Chat model display + selection** (D-2026-06-16-C). The dock shows which
  model the active CLI will use (provider bar: `Provider · model`) and offers
  a model field to set it — free-text with a `<datalist>` of suggestions
  (only the `claude` CLI's own documented aliases `fable`/`opus`/`sonnet` are
  pre-listed; codex/gemini ids are free-text, not a hardcoded stale list).
  Persists per workspace + provider (`chat-provider` JSON gains `model`),
  resets on provider change, passed to the CLI as `--model <model>` (all three
  CLIs accept it). Empty = the CLI's own default. Pinned by
  `tests/test_chat_model.py` + `viewer/tests/chat-model-selection.test.tsx`.

### Changed

- The `GET`/`PUT /api/chat/provider` responses now carry `model` alongside
  `provider`.

## [0.83.0] — 2026-06-16

### Added

- **Live chat streaming indicator** (D-2026-06-16-B). While a turn streams,
  the dock shows three bouncing dots + an elapsed-seconds counter
  (`role="status"`) so it never looks frozen — including the gap between send
  and the first token, where the assistant bubble is still empty. A blinking
  caret trails the streaming text once it arrives. `ChatActivityIndicator` +
  `useElapsedSeconds`, pinned by `viewer/tests/chat-activity-indicator.test.tsx`.

## [0.82.1] — 2026-06-16

### Fixed

- **Drag-release context menu still popped on category / group nodes and
  inside the service-detail canvas** (D-2026-06-16-A). The v0.81.1 fix armed
  on React Flow's per-node `onNodeDragStop`, which didn't fire for every node
  kind / canvas, so the menu still leaked there (user report). Replaced with
  a window-level pointer-gesture watcher: a `pointerup` that moved > ~5 px
  from its `pointerdown` is a drag → the next `contextmenu` is swallowed.
  Kind- and canvas-agnostic; the `onNodeDragStop` wiring on `SketchCanvas`
  was removed. Right-clicks (no movement) still open the menu.

## [0.82.0] — 2026-06-15

### Added

- **ServiceDetail right panel shows the subject service (Option 1)**
  (D-2026-06-15-O). The detail canvas's right panel now has three states:
  by default (nothing selected) it shows the **subject service's read-only
  inspector** — its typed fields, problem-first, read cross-doc from the
  Services canvas; selecting a detail node shows that node's editable
  inspector; clicking empty space returns to the service. The service is
  read-only here (its home is the Services canvas). Implemented via a
  `fallbackInspector` render-prop on `SketchInspectorBindings` + a new
  `ServiceDetailInspectorHost`; `KindInspector` / `BaseInspector` /
  `ServiceInspector` gained a `readOnly` mode. Guards a deleted/unknown
  service (renders nothing). Pinned by
  `viewer/tests/service-detail-fallback-inspector.test.tsx`.

## [0.81.1] — 2026-06-15

### Fixed

- **Context menu popped after a node drag-release** (D-2026-06-15-N). On a
  macOS trackpad, a one-finger press-drag-release of a node emitted a
  trailing `contextmenu` event after pointerup; React Flow's d3-drag only
  blocks `contextmenu` *while* dragging, so the tail leaked to
  `onNodeContextMenu` / `onPaneContextMenu` and the menu opened at the
  release point ("drag a node, let go, it acts like a right-click").
  `useContextMenus` now arms a one-shot suppression on `onNodeDragStop`,
  disarmed by the next `pointerdown` so deliberate right-clicks still work.
  Pinned by `viewer/tests/context-menu-drag-suppression.test.tsx`.

## [0.81.0] — 2026-06-15

Two user-reported ServiceDetail bugs fixed — both were *claimed* fixed in
v0.78 (D-2026-06-15-H / -I) but the fixes were incomplete; root-caused via
adversarial diagnosis.

### Fixed

- **Node-label editor invisible in dark mode** (D-2026-06-15-M). The inline
  label editor and the StepNode `outcome` editor used the theme-following
  `bg-surface`, but inside `.node-card` `text-fg-strong` is locked dark in both
  themes → dark-on-dark. Now use the card-locked `bg-surface-subtle` (+ explicit
  `text-fg-strong` on the StepNode editor). D-2026-06-15-I fixed light mode only.
- **Clicking a user/actor in ServiceDetail jumped to the Actors canvas**
  (D-2026-06-15-L). `actor_ref` is no longer drillable on the detail canvas, and
  `useInspectorRouting` double-click now drills only `shouldDrill` nodes (it was
  unconditional — the jump fired through two ungated paths). Clicking an actor
  now opens its inspector to edit per-service motivation/pain;
  `useUrlSync.jumpToActor` also clears `detailActive`. Supersedes the actor_ref
  double-click → actor-master jump from D-2026-06-15-H #2.

## [0.80.0] — 2026-06-15

Minor. The `service` kind gains a one-line **`problem`** field
(D-2026-06-15-K) — the need / lack the service exists to solve. A service
is the process of solving a problem (user, 2026-06-15); the existing fields
(`what` / `value_created` / `outcome`) are all solution-side, so the
problem now has an explicit home. Distinct from an "overview" (which `what`
already covers) and from per-actor `actor_ref.pain` (per-participant
friction, D-2026-06-15-J) — `service.problem` is the single headline
problem for the whole service.

### Added

- **`service.problem`** (Pydantic `ServiceNode` + TS `Service`), rendered
  as the **first** field in the service inspector (above `target_side` /
  `what`). New i18n keys `inspector.field.problem` +
  `inspector.fieldHint.problem` (en + ko).

## [0.79.0] — 2026-06-15

Minor. Domain remodel: an actor's **motivation / pain become per-service**
(D-2026-06-15-J). They move off the global actor entity (now identity-only:
side + body) onto `actor_ref`, where each service-detail authors the actor's
stake *in that service* — per PHILOSOPHY P3 (Participation is Asymmetric), the
same human is a Hero in one service and a Fan in another, so motive/pain are
defined by the service, not globally. PURE per-service (no actor baseline).

### Added

- **`actor_ref.motivation` / `actor_ref.pain`** (D-2026-06-15-J) — per-service
  stake fields, alongside the existing `gives` / `receives`. The actor_ref
  inspector gains a "Stake in this service" box; a brand-new actor_ref starts
  blank, surfacing the per-service Discovery question where the participation
  is drawn. New i18n key `inspector.perServiceStakeHeader` (en + ko).

### Changed

- **The actor entity is identity-only** — `side` (Surface) + `body`. The actor
  inspector no longer shows motivation / pain (moved to actor_ref).
- **Actor inheritance refined** (refines D-2026-05-31-G): `INHERITABLE_FIELDS`
  shrinks from `[motivation, pain, side, body]` to `[side, body]`; the
  resolver machinery is unchanged.
- **Abstract-root superclass refined** (refines D-2026-05-31-H): the abstract
  tree root now hides only `side` (motivation / pain are no longer actor
  fields). `actorBaseHint` reworded.

### Removed

- `ActorNode.motivation` / `ActorNode.pain` (Python) and `Actor.motivation` /
  `Actor.pain` (TS). A legacy v0.1 actor's motivation/pain are not carried onto
  the v0.2 actor master on migration (accepted tradeoff; realistic data empty).
  No backfill — the move ships while existing data is empty, avoiding an unsafe
  cross-file fan-out migration later.

## [0.78.0] — 2026-06-15

Minor. Service-detail becomes a dynamic canvas tab; auth-boot fix; chat
switcher reverts to two tabs; several UX fixes (verified live in the `.app`).

### Added

- **Service-detail dynamic canvas tab** (D-2026-06-15-H). Selecting a
  (non-root) service node on the Services canvas appends a `{ServiceName}` tab
  after `Foundation | Actors | Services` and renders the detail canvas inline
  (was a modal overlay). Switching to an F/A/S tab keeps the tab; its × closes
  it.

### Changed

- **Single-click a service node opens its detail tab** instead of the right
  inspector (`selectOpensDrill`, Services canvas only). On the Service-Detail
  canvas a single click still opens the inspector — actor_ref drill stays on
  double-click, so clicking an actor no longer jumps to the Actors canvas.
- **Chat scope switcher reverts to two tabs** — `[selected canvas | project]`
  (the v0.77.0 full F/A/S picker, D-2026-06-15-E, is **superseded**). A
  service-detail canvas tab shows the **service's name**, not "Service detail".

### Fixed

- **Workspace failed to load under the bundled/dev shell** (D-2026-06-15-G):
  `main.tsx` now awaits the engine auth token before the first render — the
  fire-and-forget call lost the race against the first `/api/projects`,
  yielding a 401 and an empty workspace.
- **Node label edit text was invisible** (D-2026-06-15-I): the editor input now
  sets an explicit `text-fg-strong` instead of inheriting the card's (often
  light) label colour.

### Removed

- The ServiceDetail **modal overlay** (and its inert backdrop) — replaced by the
  inline dynamic tab above.

## [0.77.0] — 2026-06-15

Minor. Chat dock UX — full thread picker (D-2026-06-15-E) + always-legible
connected agent (D-2026-06-15-F).

### Changed

- **Scope switcher is now a full thread picker.** Fixed segments
  Foundation · Actors · Services · Project are always shown; a `{ServiceDetail}`
  segment (after a `|` separator) appears while a service-detail is the active
  canvas. Selecting a segment switches the chat thread only — never navigates
  the canvas; the selection defaults to + follows the active canvas, a click
  overrides until the next canvas change. Replaces the 2-way
  `[active canvas | project]` toggle, which hid the other threads inside a
  service-detail.
- **Compact provider bar shows the connected agent at a glance.** A persistent
  connection indicator (filled dot + agent name in a readable colour when
  connected; hollow dot + prompt when not; `data-connected` 1/0) makes the
  connected CLI legible without expanding the panel.

## [0.76.0] — 2026-06-15

Minor. Chat MCP path — the external agent gets the viewer's live context
(D-2026-06-15-D). The CHAT_ARCH.md "Scope honesty" follow-up to Layers 1–3:
the *primary* path (the user's own CLI via the `mashbill` sidecar) now sees the
same active canvas + selection + framing the in-app chat got.

### Added

- **`get_viewer_context(project_path)` MCP tool** → `{active_canvas, selection,
  framing, updated_at, stale, has_viewer}`. The agent resolves "fix this"
  against what's on screen; when no viewer is live it returns
  `has_viewer: false` / empty so the agent never treats stale context as
  current.
- **`POST /api/viewer/context`** — the viewer reports `{project_path, scope,
  selection}`; the engine stamps `updated_at` and writes a rendezvous file.
- **`useViewerContextBridge`** (viewer) — one mount in `ChatDock` over the
  active canvas + selection; debounced on-change post + ~30s heartbeat so an
  idle-but-open viewer stays "live".
- `mashbill/viewer_context.py` (filesystem rendezvous store) +
  `mashbill/endpoints_viewer.py`.

### Changed

- **Shared `mashbill/chat_context.py`** — `build_framing_preamble` +
  `SCOPE_FRAMING` + `build_context_preamble` moved out of the HTTP endpoint
  module so the MCP path shares them without importing the HTTP layer (SSOT;
  no MCP→HTTP dependency). `endpoints_chat.py` re-exports for back-compat.

### Notes

- The bundled MCP server is a **separate `--mcp-stdio` process** from the HTTP
  sidecar (D-2026-06-14-A), so context crosses the boundary via a
  `tempfile.gettempdir()` file keyed by `sha256(plot_root)` — ephemeral, atomic
  write, project-keyed. Liveness uses the shared machine clock (90s TTL). The
  originally-pinned "in-memory" store was physically impossible across that
  boundary; revised to filesystem after the topology finding.

## [0.75.0] — 2026-06-15

Minor. In-app chat Layer 3 — per-canvas system framing (D-2026-06-15-C).
Final layer of CHAT_ARCH.md's three-layer chat redesign.

### Added

- **Canvas-appropriate chat framing.** Each turn now prepends a system framing
  tied to the canvas's VISION phase — Foundation → Discovery, Actors / Services
  → Planning, Service-Detail → Execution. The `project` scope gets none. The
  engine assembles the CLI prompt as framing → selection context → user message
  (empty parts skipped); a parametric `service_detail:<id>` resolves to the
  shared `service_detail` framing. Framing is code constants (`_SCOPE_FRAMING`),
  not `.noory/`-editable.

### Notes

- In-app only — the primary MCP path is unaffected. Completes the chat redesign
  (Layers 2 → 1 → 3 shipped v0.73.0 → v0.74.0 → v0.75.0). Follow-up: selection
  + framing over the MCP path (viewer→engine bridge + MCP resource).

## [0.74.0] — 2026-06-15

Minor. In-app chat Layer 1 — per-service-instance conversation threads
(D-2026-06-15-B). Second of CHAT_ARCH.md's three sequenced layers.

### Added

- **Per-service chat threads.** `service_detail` is now a parametric scope:
  each service-detail canvas keys its own conversation as
  `service_detail:<service_id>`, so two services no longer share one mixed
  thread. The chat scope set now equals `CanvasKey ∪ {project}` — chat threads
  and canvas state key the same way. New engine helper `is_valid_scope`
  (base member OR `service_detail:<id>` with non-empty id).

### Changed

- `ChatStreamEvent.scope` (engine) + `ChatScope` (viewer) widened to carry the
  `service_detail:<id>` suffix; the session registry keys on the full scope
  string. App passes the open service's parametric scope (falling back to
  `services` when none is resolved); the scope switcher labels a parametric
  scope with its base `service_detail` i18n key.
- `tests/test_chat_scope_parity.py` now also parses the TS template-literal
  member and asserts `service_detail` accepts an id suffix.

### Notes

- In-app only — the primary MCP path is unaffected. Bare `service_detail`
  (no id) is rejected server-side (Fail Fast); a deleted service's thread is
  left orphaned (cleared on engine restart). Next: Layer 3 — per-canvas system
  framing.

## [0.73.0] — 2026-06-15

Minor. In-app chat Layer 2 — per-turn canvas + selection context injection
(D-2026-06-15-A); chat-architecture design red-teamed + committed.

### Added

- **Selection-aware chat.** Each in-app chat turn carries the active canvas +
  the live node selection; the engine prepends a `[Novel context]` preamble so
  the agent resolves "fix this" against what's selected. SketchCanvas reports
  its selection upward (`onSelectionChange`), App lifts it, ChatDock forwards
  it. Per-turn snapshot; `project` scope injects nothing; selection capped at
  20 detailed nodes. In-app only (MCP path is a follow-up).
- `docs/CHAT_ARCH.md` — red-teamed (verdict revise-first) then revised:
  committed defaults + three-layer implementation sequence (Layer 2 first).

### Removed

- Unused i18n keys left by earlier collapse-toggle removals
  (`chat.collapse`/`expand`, `sidebar.{show,hide}Projects`,
  `sidebar.{expand,collapse}ProjectList`).

## [0.72.0] — 2026-06-15

Minor (UX). Resizable workspace layout; chat dock moved to the leftmost
panel (D-2026-06-14-E).

### Added

- **Resizable workspace** (`WorkspacePanels`, `react-resizable-panels`):
  three horizontally-resizable panels — **chat (leftmost) | project sidebar |
  canvas** — with enforced minimum widths (canvas can't be squeezed away).
  Chat + sidebar collapse by dragging the separator. Layout persists across
  reloads (localStorage `plot:workspaceLayout`).

### Changed

- Chat dock moved from the right edge to the **leftmost** panel.

### Removed

- The chat dock's own collapse-to-rail toggle and the sidebar's own
  w-8/w-56 collapse toggle — the resizable panel owns width/collapse now
  (one mechanism instead of three bespoke toggles).

### Dependencies

- Add `react-resizable-panels` (MIT) — first runtime UI dep beyond reactflow.

## [0.71.0] — 2026-06-14

Minor (UX). Tidy the chat dock: provider connection behind a compact bar
(D-2026-06-14-D).

### Changed

- The "Connect your AI agent" provider panel no longer sits open at the top
  of the chat dock. It's now behind a **compact one-line bar** showing the
  active CLI (or "Connect your AI agent" when none) + a chevron; click to
  reveal the full provider list. Collapsed by default — provider connection
  is a setup step, not something to keep on screen while chatting. The
  active-CLI label loads without expanding; the provider list fetches only
  when opened. First slice of the planned Settings surface.

## [0.70.0] — 2026-06-14

Minor. Edge improvements (D-2026-06-14-C): services arrows diverge from the
anchor, edges easier to select, selection highlighted.

### Changed

- **Services canvas arrows diverge from the anchor.** The anchor-relative
  arrow control generalised from `convergeArrowsOnAnchor: boolean` to
  `anchorArrowMode: "converge" | "diverge" | "none"`. Foundation/Actors keep
  `"converge"`; Services now uses `"diverge"` so the `anchor → category →
  service` flow always renders outward regardless of how the edge was drawn
  (render-enforces the D-2026-06-01-D divergence spec). Applied in both
  `edgeTransform` (render) and `useFlowHandlers` (creation normalisation).

### Added

- **Edges easier to select** — `interactionWidth: 28` on every edge (RF
  default 20), a wider invisible click band.
- **Selected-edge highlight** — styles.css rule giving a selected edge an
  accent stroke + 3 px width (`!important`, to override the inline value-flow
  stroke that otherwise hid RF's `.selected` styling). Pinned by
  `tests/edge-selection-style.test.ts`.

## [0.69.0] — 2026-06-14

Minor (behavior change). Re-include claude-code in in-app chat with a
billing warning, reversing the v0.68.0 exclusion (D-2026-06-14-B). The
per-canvas scope model from v0.68.0 is unchanged.

### Changed

- **claude-code is selectable for in-app chat again.** The v0.68.0
  exclusion is removed: `/api/chat/send` no longer 400s a claude-code
  selection, the claude-code row regains its selection radio, and the dock
  no longer coerces a persisted claude-code choice to no-selection.

### Added

- **Billing-warning banner** in the chat frame when claude-code is the
  active CLI (`chat.claudeBillingWarning`, en + ko): Claude Code runs
  headless via `claude -p`, billed separately from the Claude subscription;
  the banner points the user to the non-double-charged MCP path.

### Notes

- Follow-up (pinned, not built): a dedicated Settings surface (provider +
  model selection + billing ack) stored across two tiers — global
  `~/.noory/plot/settings.json` + per-workspace overrides. Design first.

## [0.68.1] — 2026-06-14

Patch (fix). The bundled `.app` registered a broken mashbill MCP command into
external CLI configs, breaking the primary (MCP) chat path in the actual
product. Root-caused live: codex failed the turn with `MCP client for
'plot' failed to start: request timed out`; gemini ignored the failed MCP
and answered anyway. (D-2026-06-14-A.)

### Fixed

- **MCP registration in the bundled `.app`.** `_plot_entry` built the
  command from `plot_plugin_root()` (`__file__`-based), which under
  PyInstaller resolves to the ephemeral `_MEIxxxx` onefile extraction dir —
  deleted on app exit, not a uv project even while alive — so
  `uv run --directory <_MEIxxxx> …` timed out. When frozen, registration now
  writes the stable bundled binary instead: `command = sys.executable`,
  `args = ["--mcp-stdio"]`. Dev checkouts keep the `uv run` command.

### Added

- **`mashbill.server.run_mcp_stdio()`** — stdio MCP transport only (no HTTP),
  the mode the bundled binary runs when an external CLI launches it as a
  registered MCP server.
- **`--mcp-stdio` dispatch** in the sidecar entry
  (`plot/src-tauri/sidecar-build/mashbill_entry.py`): default = HTTP sidecar,
  `--mcp-stdio` = stdio MCP server.
- Root [`ARCHITECTURE.md`](../../ARCHITECTURE.md) documenting how the `.app`,
  mashbill MCP, and the user's VSCode-hosted agent mesh.

## [0.68.0] — 2026-06-14

Minor (feature). Implement the chat redesign pinned in D-2026-06-13-H:
per-canvas conversation scope + claude-code excluded from in-app chat.
TDD across the engine + viewer, six lock-step steps.

### Added

- **`ChatScope` wire enum** (`project` / `foundation` / `actors` /
  `services` / `service_detail`) defined on both sides — Python
  `mashbill/chat_providers/base.py`, TS `viewer/src/types.ts` — and
  parity-guarded by `tests/test_chat_scope_parity.py`.
- **Per-canvas chat scope.** Engine sessions are keyed on
  `(workspace, provider, scope)`; `ChatStreamEvent` carries `scope`;
  `POST /api/chat/send` + `POST /api/chat/reset` accept `scope`. The
  viewer's `useChatStream` keeps a separate thread per scope (an
  in-flight turn in one canvas keeps streaming while the user is on
  another), and the dock follows the active canvas.
- **Scope switcher.** A segmented control in the dock pins the shared
  `project` thread vs the active-canvas thread (explicit toggle, only
  shown when the active canvas is itself non-project).

### Changed

- **In-app chat excludes `claude-code` (D-2026-06-13-H).** Driving it
  via `claude -p` double-charges a Claude subscriber, so: the chat
  selection radio is suppressed on the claude-code row (its MCP
  register/unregister controls stay), the dock coerces a legacy
  persisted `claude-code` choice to no-selection, and
  `POST /api/chat/send` 400s a `claude-code` selection as the
  server-side backstop. `claude-code` remains in the MCP-registration
  list — the MCP path is the intended way to use Claude.
- **`sendChatMessage` / `resetChatSession`** now take a `scope`
  argument; `chat_stream_event` payloads carry `scope`.
- **`docs/SPEC.md` §R7** — rewritten for MCP-first framing, the
  claude-code exclusion, and the conversation-scope model.
- Scope decisions: a missing `scope` defaults to `project` (Postel);
  the `project` scope is reached by explicit toggle; `Reset` clears the
  active scope only.

## [0.67.1] — 2026-06-13

Patch (docs). Pin the chat-architecture decision after in-app chat
verification surfaced a `claude -p` double-billing problem.

### Changed

- `docs/DECISIONS.md` — D-2026-06-13-H: **chat is MCP-first.** Primary
  path = Novel is an MCP server the user's own interactive agent (Claude
  Code / Codex / Gemini, on their subscription) connects to; Novel does not
  host/drive the AI. Secondary = in-app chat for **Codex/Gemini only**
  (`claude-code` removed from in-app chat selection, kept in MCP
  registration) because `claude -p` bills separately from the Claude
  subscription (double-pay). Adds per-canvas-type + shared "project" chat
  scoping. Revises D-2026-06-11-E. Design pinned; implementation is a
  follow-up (engine scope-keyed sessions + viewer scope-aware dock +
  `scope` schema parity).

## [0.67.0] — 2026-06-13

Minor. **Stencil drag-and-drop works in the desktop app, and behaves as
the user expects.** WKWebView (the bundled Tauri `.app`) never fired
HTML5 `drop`, so stencil drops created no node on any canvas. The drag is
now captured with pointer events, plus the drop behaviour the user asked
for during in-app verification. See D-2026-06-13-C/D/E/F/G.

### Added

- `viewer/src/canvases/sketch/StencilDragContext.tsx` — pointer-drag
  channel: `StencilDragProvider` + `useStencilDrag` (begin a drag from a
  stencil item's `onPointerDown`) + `useStencilDropTarget` (register a
  canvas pane + `place` callback). A ghost chip follows the pointer.
  WebKit implicit-capture handled via `elementFromPoint`.
- `viewer/tests/stencil-pointer-drag.test.tsx` (5) + `nested-drop-edge.test.tsx` (1).

### Changed

- `viewer/src/canvases/sketch/useDragAndDrop.ts` — `handleDrop`/`handleDragOver`
  replaced by `placePresetAt(preset, clientX, clientY)`; the hook owns the
  pane ref + registers it with the channel. `SketchStencil` items use
  `onPointerDown` + `data-stencil-item`; `SketchCanvas` attaches the pane
  ref (no more `onDrop`/`onDragOver`); `App` mounts `StencilDragProvider`.
- `viewer/src/canvases/SketchStencil.tsx` — **category is optional**: a
  `service` dropped outside a category lands top-level instead of being
  rejected (D-2026-06-13-D, supersedes the D-2026-05-28-A requirement).
- `viewer/src/canvases/FoundationCanvas.tsx` — drops land at the cursor,
  not snapped to an anchor-radial slot (D-2026-06-13-G).
- `viewer/src/canvases/sketch/useNodeCreation.ts` — the nesting edge
  carries no visible "decomposes" label (D-2026-06-13-E).
- `viewer/src/canvases/sketch/LayoutControls.tsx` — arrange icon stroke
  is a fixed dark `#1a1a1a` (was `currentColor`, invisible on the light RF
  controls bar in dark theme) (D-2026-06-13-F).

### Removed

- `viewer/src/canvases/SketchStencil.tsx` `toTransferPreset` + its test —
  superseded by the pointer channel passing the full in-memory preset
  (no serialization, so `preset.id` can never be lost; D-2026-06-13-A's
  intent is now structural).

## [0.66.0] — 2026-06-13

Minor. **Flavor badge — `DEBUG` chip in non-release builds.** A small
amber `DEBUG` chip next to the `PLOT` logo makes a debug-flavor build
visually obvious; the release flavor shows nothing. Gated by the same
BUILD-TIME flag as the debug probe (`debugEnabled()` →
`VITE_PLOT_DEBUG === "1"`, D-2026-06-09-D), so there is no runtime
escape hatch. See [D-2026-06-13-B](docs/DECISIONS.md), SPEC.md §Chrome.

### Added

- `viewer/src/shell/FlavorBadge.tsx` — renders the `DEBUG` chip when
  `debugEnabled()` is true, `null` otherwise. A build identifier, not
  localizable copy, so it stays out of i18n (mirrors the hardcoded
  `PLOT` / "MCP: live" technical labels beside it).
- `viewer/tests/flavor-badge.test.tsx` (2 tests) — DEBUG shown when
  `VITE_PLOT_DEBUG=1`; empty render when unset.

### Changed

- `viewer/src/shell/Header.tsx` — mounts `<FlavorBadge />` immediately
  after the `PLOT` wordmark.

## [0.65.1] — 2026-06-13

Patch. **Fix: stencil drops lost `preset.id`, breaking nesting rules.**
`StencilItem.onDragStart` stripped `id` from the dataTransfer payload,
but `resolveDropTarget` keys the sub-actor / service-in-category
*nesting* rules off `id`. With `id` gone, every such drop fell through
to a silent top-level node — bypassing the pinned D-2026-05-28-A
contract (Service must nest in a Category; sub-actor must nest in an
Actor). The unit pin `service-detail-composition-drop.test` never
caught it because it calls `resolveDropTarget` with the preset directly,
skipping the lossy wire round-trip. Restores the contract at runtime;
no SPEC change. See [D-2026-06-13-A](docs/DECISIONS.md).

### Fixed

- `viewer/src/canvases/SketchStencil.tsx` — extracted `toTransferPreset()`
  (exported): drops the four display-only fields (`labelHint` /
  `dropHint` / `labelI18nKey` / `dropHintI18nKey`) but **keeps `id`**.
  `onDragStart` now serializes via it. Service-in-category / sub-actor
  drops once again require (and nest under) their container; dropping on
  empty space surfaces the guard message instead of dumping a stray
  top-level node.

### Added

- `viewer/tests/stencil-transfer-preset.test.tsx` (3 tests) — pins the
  dataTransfer round-trip: `toTransferPreset` keeps `id` + drops display
  fields; service-in-category and sub-actor still require their parent
  after `JSON.parse(JSON.stringify(...))`. Red→Green verified by
  reverting the `id` strip.

## [0.65.0] — 2026-06-12

Minor. **Track 3.5 — engine auth seam.** TABLET_ARCH §"지금 만들 것"
pinned this as a build-now item: pre-wire an ``Authorization`` header
+ ``?auth=`` query param across the engine + viewer + Tauri shell so a
future bundled / remote / tablet delivery can flip enforcement on with
one env var. Today's dev mode (env unset) is byte-identical to v0.64.x.
Architecture pin at
[D-2026-06-12-F](docs/DECISIONS.md). Spec section added at
SPEC.md §Engine auth.

### Added

- `mashbill/auth.py` — env reader (`configured_token`,
  `PLOT_AUTH_TOKEN`), `AuthMiddleware` (Starlette
  `BaseHTTPMiddleware` over `/api/*` only), `check_ws_token` (helper
  the WS endpoint calls — middleware can't ride `WebSocketRoute`),
  `extract_bearer` (case-insensitive scheme + whitespace-tolerant),
  `is_authorized` (constant-time via `hmac.compare_digest`).
  `/api/health` is the only always-open path; the Tauri shell probes
  it before injecting the token.
- `tests/test_auth.py` (16 tests) — pure helpers (env read every
  call, bearer extraction edge cases, constant-time compare),
  middleware behaviour through a real Starlette app (env unset →
  pass-through, env set + missing → 401, env set + wrong → 401, env
  set + good → through, `/api/health` always open), and WS helper
  parity.
- `viewer/src/api.ts` — `setEngineAuthToken` + `engineFetch` wrapper
  + `appendWsAuth` helper. All 30 `await fetch(...)` sites rewrote
  to `await engineFetch(...)` so the seam is a single place — flip
  the token, every call is authenticated. `openProjectSocket`
  appends `?auth=<token>` when the token is set.
- `viewer/src/app/auth.ts::initEngineAuth` — resolves the token at
  app boot. Source priority: Tauri `invoke('plot_auth_token')` →
  `import.meta.env.VITE_PLOT_AUTH_TOKEN` → null. Errors from the
  invoke are swallowed (the engine's 401 is louder than a thrown
  promise here would be).
- `viewer/src/main.tsx` calls `initEngineAuth()` once before
  ReactDOM render so React-effect-triggered fetches see the token
  by the time they evaluate.
- `viewer/tests/engine-auth.test.ts` (7 tests) — header injection
  on/off, `null` clearing, empty string treated as null, Tauri
  invoke first / dev env fallback / Tauri error swallow.
- Novel Tauri shell (separate `plot` repo): `mint_auth_token()`
  uses `rand::rngs::OsRng` to fill 32 bytes + hex-encode (64 lower
  hex chars). Stored in a Tauri `State` so the
  `#[tauri::command] plot_auth_token` returns it. The sidecar
  spawns with `.env("PLOT_AUTH_TOKEN", &token)`. 2 Rust unit tests
  pin hex shape + per-call uniqueness.

### Changed

- `mashbill/http_app.py::create_http_app` mounts `AuthMiddleware`
  in front of `CORSMiddleware` when `PLOT_AUTH_TOKEN` is set; when
  unset, the middleware is NOT mounted (zero latency cost on dev).
  `ws_endpoint` checks the `?auth=` param via `check_ws_token`
  before accepting the subscription.
- 30 `await fetch(...)` sites in `viewer/src/api.ts` route through
  `engineFetch` instead. Outside-of-engine code is unaffected — the
  wrapper is `api.ts`-internal so the structural-guard rule ("only
  `src/app/` + `src/hooks/` may import from `api`") still holds.

### Decisions

- [D-2026-06-12-F](docs/DECISIONS.md#d-2026-06-12-f--engine-auth-seam-track-35-tablet_arch-지금-만들-것)
  pins the env-gated design (vs always-on, vs stored secret), the
  per-launch token shape, constant-time comparison rationale, and
  the open-list-of-one for `/api/health`. SPEC.md §Engine auth is
  the user-facing summary.

## [0.64.1] — 2026-06-12

Patch. **D-2 Phase C breadth** — Codex and Gemini join Claude Code as
fully-streaming R7 chat providers, and `/api/chat/send` now dispatches
to whichever CLI the workspace selected (D-2026-06-11-E Phase B step
B3) instead of always running Claude. Architecture pin lives at
[D-2026-06-12-E](docs/DECISIONS.md). No viewer-facing changes.

### Added

- `mashbill/chat_providers/` subpackage — split out from the
  v0.64.0 `chat_session.py` so each per-CLI file owns one provider's
  quirks (command shape, JSONL event names, session-id capture,
  resume semantics). Members: `base.py` (ChatStreamEvent +
  ChatProvider ABC + `_SubprocessChatProvider` spawn-loop +
  `_decode_jsonl`), `claude_code.py` (ClaudeCodeProvider +
  `_parse_claude_line`), `codex.py` (CodexProvider), `gemini.py`
  (GeminiProvider). `chat_session.py` becomes a thin facade that
  re-exports the same public names plus the registry, so existing
  imports keep linking.
- `CodexProvider` — `codex exec --json --skip-git-repo-check`.
  Captures `thread_id` from the `thread.started` event and resumes
  via `codex exec resume <id>` on later turns. If the first turn
  never emits `thread.started` (CLI crash, parse skip), the next
  turn falls back to a fresh `exec` so we never call `resume None`.
- `GeminiProvider` — `gemini -y --output-format stream-json -p
  <prompt>`. Captures `session_id` from the `init` event and resumes
  via `--resume <id>` on later turns. `-y` (YOLO) skips per-action
  approvals — Novel is the canvas surface that owns user trust.
- Registry keying — `(workspace, provider_name)` not just
  `workspace`, so a user who flips Claude → Codex → Claude in one
  session resumes both conversations cleanly. New
  `ChatSessionRegistry.reset(workspace, provider_name=None)` drops
  one provider's session (or every provider's session for the
  workspace if `provider_name` is `None`). The endpoint's
  `/api/chat/reset` keeps the wipe-all semantics.
- `mashbill/endpoints_chat.py::chat_send_endpoint` reads
  `<workspace>/.noory/plot/chat-provider` to pick the provider. No
  selection → 400 (was: silent Claude default in v0.64.0). Novel
  doesn't pick a default AI for the user; the dock's "Pick a chat
  CLI above to start" state is the only valid entry point.
- 11 new chat_session tests pin per-provider command shape (`exec`
  vs `exec resume`, `--session-id` vs `--resume`, `-y` /
  `--output-format` / `-p`), session-id capture from the right event,
  and per-provider event filtering (codex `agent_message` text,
  gemini `assistant` content, both with non-message frames silently
  dropped). 4 new endpoint tests pin no-selection → 400, per-provider
  dispatch, all-providers reset, and an integration sanity that walks
  the registry through two provider switches.
- 3 new default-factory tests pin that `ChatSessionRegistry()` builds
  a `ClaudeCodeProvider` / `CodexProvider` / `GeminiProvider`
  depending on `provider_name`.

### Changed

- `chat_session.py` shrinks from 567 LOC → ~130 LOC (facade only)
  because the per-CLI code moved into `chat_providers/`. Stays under
  the engine's 500-LOC module rule
  (`test_module_size.py::test_no_engine_module_exceeds_the_500_line_rule`).
- `ChatSessionRegistry.get_or_create(workspace)` →
  `ChatSessionRegistry.get_or_create(workspace, provider_name)`. A
  call-site update; v0.64.0 tests + endpoints pass `"claude-code"`
  explicitly. The old single-arg form has no usable default (the
  registry doesn't know which CLI the workspace picked) so a runtime
  error is preferable to a silent default.
- `/api/chat/send` returns 400 `{"error": "no chat provider
  selected"}` when the workspace has no persisted selection. v0.64.0
  shipped without this guard.

### Decisions

- [D-2026-06-12-E](docs/DECISIONS.md#d-2026-06-12-e--r7-chat-codex--gemini-providers-land-alongside-claude)
  — pins the per-provider command shapes (`--skip-git-repo-check`,
  `-y`, etc.), the session-id capture strategy per CLI, the
  `(workspace, provider)` registry key, the no-selection → 400
  policy, and the chat_providers/ subpackage split. No new
  user-facing surface — D-2026-06-11-E + D-2026-06-12-D already
  pinned the dock copy and the engine-side architecture.

## [0.64.0] — 2026-06-12

Minor. **D-2 (R7 native chat panel) Phase C** — subprocess streaming
lands. The user picks a chat CLI, types a message, and Novel drives the
external `claude` (Codex / Gemini next) via `--print --output-format
stream-json`, fanning the streamed assistant text back to the dock over
the workspace WS. Per the new pin [D-2026-06-12-D](docs/DECISIONS.md):
the CLI subprocess lives in the **mashbill engine** (not the Tauri
shell), so dev mode (browser at `:5193`) and the bundled `.app` take the
same code path.

### Added

- `mashbill/chat_session.py` — `ChatProvider` ABC +
  `ClaudeCodeProvider` (one subprocess per turn, conversation
  continuity via `--session-id` then `--resume`) + permissive
  stream-json parser that emits `ChatStreamEvent`s
  (`turn_start` → `delta` × N → `turn_complete` / `error`) +
  `ChatSessionRegistry` (one provider per resolved workspace path,
  drop on `reset`). Subprocess invocation is injected so tests stay
  hermetic — real CLI calls live in the end-to-end smoke.
- `mashbill/endpoints_chat.py` — `POST /api/chat/send` (validate
  body, schedule streaming task, 202) + `POST /api/chat/reset`
  (drop cached provider). The streaming bridge `stream_chat_turn`
  is exported so unit tests exercise it without going through
  HTTP. Provider crashes are caught + broadcast as an `error`
  event so the viewer always surfaces them.
- `mashbill/broadcast.py::notify_event` — generalises `notify` to
  take an event name. The workspace WS room is now shared between
  `project_changed` and `chat_stream_event`; the viewer
  demultiplexes on `event`.
- `tests/test_chat_session.py` (13 tests) — stream-json parsing
  (assistant message, partial-delta, system init, invalid JSON,
  tool_use), registry identity + path canonicalisation + reset,
  subprocess lifecycle (success, first-turn vs resume command
  shape, non-zero exit → error, cancel kills the process).
- `tests/test_endpoints_chat.py` (9 tests) — bridge unit
  (broadcast each event, broadcast error on crash), HTTP
  validation (400 missing project_path / message, invalid JSON),
  202 wiring (registry returns the fake provider, message lands
  in `calls`), reset endpoint, `notify_event` fidelity end-to-end.
- `viewer/src/app/chat.ts` — application-layer re-export of
  `sendChatMessage` / `resetChatSession` / `ChatStreamPayload`
  (presentation rule: shell components never import from
  `../api` directly; the api-seam structural guard enforces).
- `viewer/src/hooks/useChatStream.ts` — opens one WS per
  workspace via `openProjectSocket`, demultiplexes
  `chat_stream_event` payloads through a pure `applyChatEvent`
  reducer (extracted + exported for tests), exposes
  `messages` / `send` / `reset` / `isStreaming` / `socketStatus`
  / `lastSendError`. User messages append optimistically on
  `send`; assistant messages land on `turn_start` and grow with
  each `delta`; late deltas for unknown turns are dropped
  silently.
- `viewer/tests/use-chat-stream.test.ts` (7 tests) — reducer
  pins: `turn_start` appends streaming row + flips
  `isStreaming`, `delta` only touches the matching turn,
  `turn_complete` reconciles engine text against streamed text,
  `error` marks the row + surfaces the message (including
  error-before-turn-start), unknown turn id drops silently.
- New i18n keys (en + ko, in lockstep): `chat.you` /
  `chat.assistant` / `chat.streamingHint` / `chat.errorPrefix`
  / `chat.resetSession` / `chat.confirmReset` /
  `chat.noWorkspace` / `chat.socketDisconnected` /
  `chat.inputPlaceholderUnselected` plus a parameterised
  `chat.inputPlaceholder` (`"Ask {{provider}}…"` /
  `"{{provider}}에게 묻기…"`).
- `plot/src-tauri/src/lib.rs::probe_login_shell_path` —
  best-effort PATH inheritance from the user's login shell
  (`$SHELL -ilc 'printf %s "$PATH"'`). Why: macOS `.app`
  launched from Finder inherits a four-entry launchd PATH that
  doesn't include `/opt/homebrew/bin`, `~/.local/bin`, or
  `~/.npm-global/bin` — so the engine sidecar would fail to
  find `claude`. The probe runs once at setup, propagates the
  result via `sidecar.env("PATH", …)`, and falls through
  silently when the shell rejects the command so degraded mode
  is never worse than today's behaviour. Dev mode (terminal
  launch) is unaffected.

### Changed

- `mashbill/http_app.py::create_http_app` accepts an optional
  `chat_registry_instance` so tests can inject a registry whose
  factory returns a fake `ChatProvider`. Production paths pass
  `None` and the module-level singleton is used. The hub +
  registry now sit on `app.state.broadcast_hub` /
  `app.state.chat_registry` (the legacy `app.state.hub` alias
  is preserved for backwards compat). Two new routes:
  `POST /api/chat/send` + `POST /api/chat/reset`.
- `viewer/src/types.ts::SocketEvent` gains the
  `chat_stream_event` variant; the generic string fallback
  stays so future event names don't break compilation.
- `viewer/src/shell/ChatDock.tsx` activates the message frame:
  the disabled Phase-B textarea is replaced with a live input
  (Enter sends, Shift+Enter newline), the message log renders
  user + assistant turns with streaming indicators, the status
  bar surfaces socket reconnect + a Reset button (uses the
  in-app `useDialog().confirm` per the
  `no-window-dialog` structural guard), the no-workspace
  empty state prompts the user to open one, the no-active-CLI
  state names the gating step. Error events surface inline
  under the assistant row that errored.
- Stale Phase-B test (`renders a disabled input + send
  button so Phase C can wire streaming later`) replaced with
  Phase-C expectation (input stays disabled until both
  workspace + active CLI are present; placeholder names the
  gating step).

### Decisions

- [D-2026-06-12-D](docs/DECISIONS.md#d-2026-06-12-d--r7-chat-subprocess-lives-in-mashbill-not-tauri)
  — Subprocess host is the engine, not Tauri. Three forces
  (dev parity, transport SSOT, existing WS plumbing) all point
  the same direction; the alternative (Tauri spawn) lost on
  dev parity (chat dead in dev mode) + transport split. Spec
  impact: SPEC.md §R7 chat gains a "Subprocess host" row.
  Tauri-side PATH inheritance is a smaller follow-up beneath
  this decision rather than a competing one.

## [0.63.3] — 2026-06-12

Patch. D-2 (R7 native chat panel) Phase B step B3 — closes Phase B.
Workspace-scoped chat-CLI selection persists at
`<workspace>/.noory/plot/chat-provider`. The user's pick survives
across reloads; unregistering the active provider auto-clears the
selection so the persisted choice can never name a CLI Novel can't
reach. Phase C (subprocess streaming) follows.

### Added

- `mashbill/chat_provider.py` — pydantic `ChatProviderSelection`
  (`provider: ProviderName | None`) + `read_selection` /
  `write_selection`. Missing or unreadable file → null selection (a
  corrupt file is never surfaced as a panel error; the next PUT
  overwrites cleanly). `mcp_registration.ProviderName` is the same
  literal union the rest of R7 uses, so unknown provider strings are
  rejected at the boundary.
- `mashbill/endpoints_mcp.py::chat_provider_get_endpoint` +
  `chat_provider_put_endpoint` — `GET /api/chat/provider` + `PUT
  /api/chat/provider` (workspace-scoped via `project_path`). Pydantic
  ValidationError → 422; missing `project_path` → 400. Routed in
  `http_app.py`.
- `tests/test_chat_provider.py` (7 tests) — fresh workspace → null,
  PUT persists + GET round-trips, PUT null clears, unknown provider →
  422, missing `project_path` → 400 on both verbs, workspace
  isolation (ws A's choice never leaks into ws B).
- `src/api.ts` — `getChatProvider(projectPath)` /
  `setChatProvider(projectPath, provider)` + `ChatProviderSelection`
  type. Re-exported through `src/app/mcp.ts` (application-layer seam
  rule).
- i18n key `chat.selectActive` in en + ko.
- `tests/chat-providers-panel.test.tsx` — 5 new cases pin the radio
  contract: panel hides the radio when selection props are omitted,
  shows one radio per row when present, checks the active row,
  disables radios on not-installed rows, dispatches `onSelectProvider`
  on click, auto-clears when the active row is unregistered.
- `tests/chat-dock.test.tsx` — 3 new cases pin the dock-level
  persistence: no `/api/chat/provider` call without `workspaceRoot`,
  GET fires on mount when `workspaceRoot` is given, clicking a radio
  PUTs the new selection.

### Changed

- `src/shell/ChatProvidersPanel.tsx` (163 → 196 LOC) — optional
  `activeProvider` + `onSelectProvider` props enable a per-row radio
  (`name="chat-active-provider"`, aria-labelled `chat.selectActive`,
  disabled on not-registered rows). Unregister handler auto-clears
  the selection if the row being unregistered was active.
- `src/shell/ChatDock.tsx` (127 → 160 LOC) — optional `workspaceRoot`
  prop. When present, loads `getChatProvider` on expand and PUTs the
  user's pick via `setChatProvider`. `App.tsx` always passes it; tests
  omit it to exercise the inert path.
- `src/App.tsx` — passes `workspaceRoot` into `<ChatDock>`.
- `docs/SPEC.md` §R7 chat — Provider-selection row expanded with the
  HTTP surface + auto-clear-on-unregister rule.

### Notes

- Server: 572 pytest green (+7); mypy clean. Viewer: 887 vitest green
  (+8); tsc clean. App.tsx 490/498.

## [0.63.2] — 2026-06-12

Patch. D-2 Phase B step B2 — message-log frame + disabled input frame
inside the dock. Visual only; no streaming, no state. Phase C wires up
subprocess streaming and flips the textarea / send button on.

### Added

- `ChatMessageFrame` (private to `src/shell/ChatDock.tsx`) — message log
  region (`role="log"`, aria-labelled), empty-state caption, and a
  bottom-anchored form with a disabled `<textarea>` (aria-labelled
  "Message input", placeholder names Phase C) + disabled Send button.
  Form has `onSubmit={preventDefault}` so accidental Enter on the
  (already-disabled) textarea is a no-op.
- i18n keys `chat.messagesLogLabel` / `chat.emptyMessages` /
  `chat.inputLabel` / `chat.inputPlaceholder` / `chat.send` in en + ko.
- `tests/chat-dock.test.tsx` — 3 new cases pin the frame contract: log
  role + empty-state caption when expanded, textarea + send button are
  `disabled` and the placeholder names Phase C, frame absent when
  collapsed.

### Changed

- `docs/SPEC.md` §R7 chat — UI row extended with the three-section dock
  layout (providers / log / input) and the disabled-until-Phase-C rule.

### Notes

- 879 viewer tests green (+3); tsc clean. `ChatDock.tsx` 127 LOC (no
  structural-guards ceiling on `shell/*.tsx`; the LOC column in CLAUDE.md
  is historical). App.tsx unchanged.

## [0.63.1] — 2026-06-12

Patch. D-2 (R7 native chat panel) Phase B step B1 — the right-side
collapsible dock shell. ChatProvidersPanel (from v0.63.0) is now mounted
inside the dock at `App.tsx`; collapse state persists across reloads in
`localStorage["plot:chatDockCollapsed"]`. B2 (message-list frame) and B3
(provider selection persistence at `.noory/plot/chat-provider`) follow
in the next two patches; Phase C (subprocess streaming) closes the
panel.

### Added

- `src/shell/ChatDock.tsx` — right-side aside, w-80 expanded / w-10
  collapsed, header + collapse / expand button (aria-labelled). Mounts
  `ChatProvidersPanel` only when expanded so the screen-reader tree
  stays honest and the provider fetch doesn't fire off-screen.
- i18n keys `chat.dockTitle` / `chat.collapse` / `chat.expand` in
  en + ko.
- `tests/chat-dock.test.tsx` (5 tests) — default-expanded render,
  collapse toggle removes the panel + persists `"1"`, second toggle
  re-expands + persists `"0"`, initial-collapsed reads from
  localStorage (provider fetch not called), `onError` forwards into the
  embedded panel.

### Changed

- `src/App.tsx` (488 → 490 LOC) — imports `ChatDock` and renders it as
  the trailing sibling of `<main>` inside the existing horizontal flex
  row. `handleError` (already memoised) is the error sink. No other
  layout change; sidebar + main canvas / modal positions unchanged.
- `docs/SPEC.md` §R7 chat — UI row extended with the collapse
  persistence rule (`localStorage["plot:chatDockCollapsed"]`, unmount
  on collapse).

### Notes

- 876 viewer tests green (+5); tsc clean. App.tsx 490/498 (ceiling
  unchanged; ChatDock takes the layout responsibility so the dock
  internals don't bloat App).

## [0.63.0] — 2026-06-12

Minor. D-2 (R7 native chat panel) Phase A — provider-management UI on
top of v0.62.0's MCP-registration backend. Two more phases follow:
Phase B (chat surface + provider selection persistence), Phase C
(Tauri subprocess streaming of the chosen CLI).

### Added

- `src/app/mcp.ts` — application-layer seam over `/api/mcp/*`
  (`getMcpProviders` / `registerMcpProvider` / `unregisterMcpProvider`
  + `McpProviderName` / `McpProviderStatus`). Presentation imports MCP
  ops from here, matching the existing api.ts-seam rule.
- `src/shell/ChatProvidersPanel.tsx` — provider list component. Renders
  one row per provider (Claude Code / Codex / Gemini), shows install +
  registration state, surfaces a one-click `Register Novel` /
  `Unregister` button per row. Loading state, error bubble-up via
  `onError`. Not mounted yet — Phase B wires it into the chat dock.
- i18n keys `chat.providersTitle` / `chat.providersHint` /
  `chat.providers.<name>` / `chat.providerInstalled` /
  `chat.providerNotInstalled` / `chat.providerRegistered` /
  `chat.register` / `chat.unregister` / `chat.loadingProviders` in
  en + ko.
- `tests/chat-providers-panel.test.tsx` (4 tests) — renders one row per
  provider, badges per status, register click → API call → refresh,
  error path surfaces via `onError`.

### Notes

- `ChatProvidersPanel` imports through `src/app/mcp`, not `src/api`
  directly, so `structural-guards.test.tsx`'s api-seam rule stays
  green.
- 871 viewer tests green (+4); tsc clean.

## [0.62.2] — 2026-06-12

Patch. Closes ROADMAP Track 1.4 — the last remaining item, semantic
theme tokens SSOT (D-2026-06-12-C).

### Added

- `src/theme/tokens.ts` — `SEMANTIC_TOKENS` const array + `SemanticToken`
  union type + Tailwind utility-class type helpers
  (`TokenTextClass` / `TokenBgClass` / `TokenBorderClass` /
  `TokenRingClass`). Single source of truth for the *names* of every
  semantic token.
- `tests/theme-tokens-ssot.test.ts` (3 tests) — parses
  `src/theme/tokens.css` (`:root` + `.dark` blocks) and
  `tailwind.config.js` (`colors` map), asserts each side declares
  exactly the same token name set as `SEMANTIC_TOKENS`. Catches
  silent drift where a token landed in only two of the three places.

### Notes

- No call site changes. Components still use Tailwind utility names
  (`bg-surface`, `text-fg-strong`) directly; the union type is
  available as an opt-in for typed props.
- The existing token set (~30) is already in sync across all three
  artefacts — guards pass 3/3 on day one.
- 867 viewer tests green (+3); tsc clean.

## [0.62.1] — 2026-06-12

Patch. Activates `parseEntity` at the viewer's wire boundary
(D-2026-06-12-B / ROADMAP Track 1.4). Until this commit, the
discriminated-union dispatch table assembled itself (every domain class
self-registered via `registerKindParser`) but had zero call sites — the
entity round-trip guard was the only thing exercising it. Now every
`CanvasDoc` arriving from the HTTP wire is validated before it leaks
deeper into the viewer.

### Added

- `api.ts::validateCanvas(canvas)` — runs every `canvas.nodes[i]` through
  `parseEntity`. Throws `DomainParseError` at the boundary on
  malformed nodes (unknown discriminator, type-incorrect required field,
  failed invariant). Returns the input reference unchanged so React Flow
  keeps working on the plain JSON shape (the class instances produced
  by `parseEntity` are deliberately discarded — see the prototype-strip
  warning at the top of `domain/SketchNode.ts`).
- `tests/wire-validate.test.ts` — 5 tests pin the invariant: valid input
  passes through (same reference), unknown kind / missing kind / type-bad
  field throw `DomainParseError`, empty `nodes` array is a no-op.

### Wired through

- `getCanvas` — initial canvas load + external-write refetch driven by
  `useProjectSocket`'s `project_changed` event.
- `getAllCanvases` — project-open multi-canvas load (via the `getCanvas`
  internally).
- `putCanvas` — server's mutated response (the `_md_warnings` +
  `_dirty` decorations) validated too; sync envelope preserved.

### Notes

- Server-side Pydantic enforces the same invariants on write, so any
  canvas that reaches the wire is already type-valid by server schema —
  a client-side `DomainParseError` is a real contract breach (drift
  between server Pydantic + viewer per-kind classes, or a hand-edited
  canvas.json that bypassed the server).
- 864 viewer tests green (+5); tsc clean.

## [0.62.0] — 2026-06-12

Minor. R7 multi-provider MCP registration backend (Track 2.5,
D-2026-06-11-E). Novel can now write its own `mcp_servers.plot` entry into
the user's external CLI configs (Claude Code / Codex / Gemini) so the CLI
can talk to Novel's MCP tools. No viewer UI yet — the R7 native chat panel
will plug into these endpoints in a separate session.

### Added

- `mashbill/mcp_registration.py` — provider-neutral register / unregister /
  detect API:
  - Claude Code → `~/.claude.json` (JSON), `mcpServers.plot`,
    `{type: "stdio"}` extra key.
  - Codex → `~/.codex/config.toml` (TOML), `[mcp_servers.plot]`.
  - Gemini → `~/.gemini/settings.json` (JSON), `mcpServers.plot`.
  - Every write preserves sibling MCP server entries (e.g. `pencil`) and
    unrelated top-level keys.
  - Novel entry points at `uv run --directory <plugin_root> python -m
    mashbill` so each CLI gets its own stdio instance (independent of the
    desktop app's HTTP sidecar).
- `mashbill/endpoints_mcp.py` — three HTTP endpoints:
  - `GET /api/mcp/providers` → list of `{name, installed, registered,
    config_path}` for all three providers.
  - `POST /api/mcp/providers/{name}/register` (201 / idempotent).
  - `POST /api/mcp/providers/{name}/unregister` (200 / idempotent).
- `tomli-w >= 1.0` added to plot's dependencies (Codex's TOML config
  needs writes; stdlib `tomllib` reads only).

### Tests

- `tests/test_mcp_registration.py` (23 tests) — per-provider
  create-when-missing / preserve-siblings / idempotent / unregister,
  detection both with and without CLIs on PATH, unknown provider raises.
- `tests/test_endpoints_mcp.py` (8 tests) — HTTP-layer parity, unknown
  provider returns 404.
- Tests isolate `$HOME` via `monkeypatch` so the real user config files
  are never touched.
- 565 server tests green; mypy + ruff clean.

## [0.61.1] — 2026-06-12

Docs-only. Pins two product decisions from tonight's session — no code
changes.

### Changed

- **SPEC §R7 chat** (new section, D-2026-06-11-E) — R7 in-app chat ships
  as a native panel inside Novel (option A out of native-panel /
  thin-launcher / staged). The brain is the user's external CLI
  (Claude Code / Codex / Gemini), spawned as a subprocess; Novel owns
  the chat shell, the CLI owns auth / model / billing. Multi-provider
  abstraction via per-CLI adapter classes. Implementation sequenced
  after Track 2.5 R7 MCP registration.
- **SPEC §Workspace & projects** (rewritten opening, D-2026-06-12-A) —
  pins the "why" behind the workspace-holds-many-projects shape:
  **workspace = monorepo, project = one service inside it.** Two apps
  in `apps/web/` and `apps/mobile/` are two separate Novel projects in
  one workspace. User-facing "project" copy means "one service",
  workspace-level affordances refer to the monorepo.

## [0.61.0] — 2026-06-11

Minor. Workspace = git repo (D-2026-06-11-C/D). Git lives at the user's
opened folder, not inside `.noory/plot/`. Novel never silently runs
`git init` — the first tag/publish without a repo asks the user via a
modal first.

### Changed (D-2026-06-11-C/D)

- `git_store`: workspace-root semantics throughout. `ensure_repo` removed
  (it silently inited); replaced by `assert_repo_initialized`
  (raises `GitNotInitializedError`) + `init_workspace_repo` (the only
  function that runs `git init`, called from the new
  `POST /api/workspace/git-init` endpoint).
- Novel-authored commits carry identity inline (`git -c user.name=Novel
  -c user.email=plot@noory-ai.local …`) so the user's repo-level config
  stays untouched, even on a workspace Novel initialised. `.gitignore` /
  `.gitattributes` writes removed (user's territory).
- `tag_snapshot` + `publish_snapshot` stage only `.noory/plot/`
  (`git add -A -- .noory/plot/`) so the user's working-tree edits outside
  that path are never folded into a Novel commit.
- `ensure_clean_working_tree` is path-scoped to `.noory/plot/`.
- `read_file_at_tag` paths shift from `{project_id}/…` to
  `.noory/plot/{project_id}/…` (the new file location inside the repo).
- `create_project` no longer auto-inits git.
- One-shot migration: `migrate_legacy_git_to_workspace` moves
  `.noory/plot/.git/` up to the workspace root when safe (no existing
  workspace `.git/`). Called from `resolve_plot_root`.

### Added

- `POST /api/workspace/git-init` — explicit user-consent endpoint. 201 on
  new init, 200 on existing repo (idempotent).
- Viewer: `GitNotInitializedError` (custom error class), `initWorkspaceGit`
  client, `withGitConsent` wrapper in `useProject`. Tag / blueprint
  publish / per-node publish / unpublish all route through it: on
  `GitNotInitializedError` they surface the "Initialize git repo at
  `<workspace>`?" confirm dialog, then call `initWorkspaceGit`, then
  retry. i18n keys (`gitConsent.title|message|confirm|cancel`) in en + ko.

### Tests

- New `tests/test_workspace_git.py` (rewritten end to end, 9 tests) pins:
  no auto-init, structured 409 with `needs_git_init=true`, idempotent
  `POST /api/workspace/git-init`, existing user `.git/` reused untouched
  (config + .gitignore preserved), Novel commit author is `Novel`,
  path-scoped staging, legacy `.noory/plot/.git` → workspace migration
  with no-clobber guard.
- `tests/test_git_store.py` rewritten for workspace-root semantics
  (20 tests).
- 534 server tests green; mypy + ruff clean. 859 viewer tests green;
  tsc clean.

## [0.60.0] — 2026-06-11

Minor. Splits the three remaining god modules in `mashbill/` so every
engine module sits under the 500-line monorepo SoC rule. The grandfather
ratchet in `tests/test_module_size.py` is now empty.

### Changed — god modules split (D-2026-06-11-B)

- `models.py` (993 LOC) → 7 modules + facade: `models_kinds.py`
  (Shape / NodeKind / ValueForm / BaseNodeFields), `models_foundation.py`
  (Foundation 4 + FoundationNode + PROJECT_ANCHOR_ID + FOUNDATION_* maps),
  `models_actors.py` (actor / actor_ref / service / category + 3 ref kinds),
  `models_composition.py` (metric / step / decision / group / rule / content),
  `models_union.py` (15-way SketchNode union + SketchEdge),
  `models_canvas.py` (CanvasDoc + AnchorPlacement + ProjectDoc),
  `models_discovery.py` (DiscoveredProject + DirTree models).
- `api_endpoints.py` (965 LOC) → 6 modules + facade: `endpoints_common.py`
  (`_require_plot_root` / `_ApiError` / `_parse_canvas_kind` / health),
  `endpoints_projects.py` (projects + workspace + dir tree),
  `endpoints_canvases.py` (canvas GET/PUT with `_dirty` + `_md_warnings`),
  `endpoints_tags.py` (tags + read-only at-tag snapshot),
  `endpoints_publish.py` (project + per-node publish/unpublish + published-list),
  `endpoints_files.py` (file get/raw/put + folder post).
- `migrate.py` (916 LOC) → 4 modules + facade: `migrate_v01_models.py`
  (legacy `_V01SketchDoc` + `_V01SketchNode` + `_normalise_legacy_node_kinds`),
  `migrate_builders.py` (per-canvas builders),
  `migrate_v01.py` (top-level v0.1 → v0.2 loop),
  `migrate_foundation.py` (inline Foundation upgrade).
- Pre-commit gate (`hooks/pre_commit_gate.py`) — the SketchNode union check
  now scans every `mashbill/*.py` instead of `models.py` only (the union
  body lives in `models_union.py` after the split).

### Notes

- 524 server tests green; mypy + ruff clean. Each public import (in
  `http_app.py`, `mcp_tools.py`, `canvas_io.py`, `endpoints_projects.py`,
  every test file) keeps using the facade names — zero call-site changes.
- New per-facade guards in `tests/test_module_size.py`
  (`test_models_is_a_thin_facade`, `test_api_endpoints_is_a_thin_facade`,
  `test_migrate_is_a_thin_facade`) pin every facade ≤ 180 LOC so a
  refactor cannot quietly re-merge the god module.

## [0.59.2] — 2026-06-11

### Fixed — anchor rendered 96×132 instead of 96×96 in the Tauri WKWebView (D-2026-06-11-A)

- `BaseNode`'s round-shape sizing now puts `flex flex-col justify-center` on
  the card root itself and drops `h-full` from the inner content div.
  WebKit resolved `width:fit-content + min-width + aspect-ratio + h-full
  child` into a non-square box (132 = 96 + 32 py-4 + 4 border-2). With the
  card as its own flex container the aspect-ratio resolves cleanly to
  96×96. Static guards in `tests/nodes/round-card-no-percent-height.test.tsx`
  pin both invariants per shape.
- Diagnosed via the debug probe (D-2026-06-09-D), which now reports
  `boxSizing`, the first non-handle inner child's `{w,h}`, and the React
  Flow viewport `zoom`. These three fields narrowed the cause from the
  box-sizing / browser-bug hypotheses to the `h-full ↔ aspect-ratio` loop.
  859 viewer tests green.

## [0.59.1] — 2026-06-10

### Fixed — tag / at-tag / blueprint-publish still used per-project git (D-2026-06-10-H)

- v0.53.0 moved git to the workspace level but missed 8 call sites: the tag
  list/create/delete endpoints, the at-tag reader, the blueprint-publish tag,
  and three MCP tool paths still passed `plot_root / project_id` — and
  `tag_snapshot`'s self-heal silently re-created a per-project repo. All git
  operations now target the workspace repo; the at-tag reader prefixes file
  paths with `{project_id}/`. Regression tests pin both (no per-project
  `.git` may appear; at-tag round-trip). 521 server green.

## [0.59.0] — 2026-06-10

### Changed — data root moves to `<workspace>/.noory/plot/` (R9, D-2026-06-10-G)

- `resolve_plot_root` resolves `.noory/plot/` (was `.plot/`); a legacy
  `.plot/` root migrates lazily on first access (one `shutil.move`). If both
  roots exist, `.noory/plot` wins and `.plot` is left for the user to
  reconcile. Discovery + `has_plot` check the new root and peek read-only at
  legacy roots so never-opened workspaces stay visible; `.noory` is pruned
  from descent. Plugin description + MCP tool docs updated.
- Scope: plot engine only — distill / evonest / solera follow per package
  (ROADMAP Track 2.3); distill's global `~/.distill` tier does not move.
- Tests: `test_noory_migration.py` (root location, lazy move, no-clobber,
  discovery incl. legacy). 519 server green, ruff + mypy clean.

## [0.58.0] — 2026-06-10

### Added — R8 build guard + commercial licence audit (D-2026-06-10-F)

- `tests/test_r8_independence.py`: AST import guard — the plugin can never
  import the viewer / Tauri shell / app repo / sibling plugins (the one
  forbidden direction, OVERHAUL R8), plus a `src-tauri` path-literal ban and
  a synthetic-violation self-check.
- `scripts/license_audit.py`: engine (pip-licenses) + viewer (`license-checker
  --production --failOn GPL;AGPL;LGPL`) audit. First run: 84 + 286 deps,
  zero blocking copyleft; hand-verified allowlist (docutils tri-license,
  caio metadata gap); UNKNOWN licences fail.
- Out of scope: single-owner CLA (blocked on the legal-entity decision),
  per-plugin guard replication, CI wiring (no pipeline yet).

## [0.57.0] — 2026-06-10

### Added — wire-contract snapshot: schema parity that survives the repo split (D-2026-06-10-E)

- `schema_export.wire_contract()` + `--wire` CLI export the server↔viewer wire
  contract (base fields + all 15 kind field sets, Pydantic = SSOT) into two
  committed snapshots: `mashbill/wire_contract.json` and
  `viewer/src/schema/wire-contract.json`. Engine and viewer each verify their
  own sources against their own copy (`test_wire_contract.py` /
  `wire-contract.test.ts`), so the parity guard no longer depends on both
  codebases sharing a repo. Monorepo-only sync test pins the copies identical.
- Rule mirrors (edge semantics, publish eligibility) stay behaviour-pinned per
  side — out of snapshot scope.

## [0.56.0] — 2026-06-10

### Changed — folder_io god-module split into a facade + six modules (D-2026-06-10-D)

- `folder_io.py` (1413 lines) split along its section headers into
  `storage.py`, `canvas_migrations.py`, `canvas_io.py`, `project_io.py`,
  `detail_sync.py`, `node_publish.py`; `folder_io.py` is now a pure re-export
  facade (every public + test-imported private name keeps its path — zero
  call-site changes). Dependency shape: storage ← migrations ← canvas_io ←
  {project_io, detail_sync, node_publish}; `read_project`/`write_project`
  live in `storage.py` to keep it acyclic.
- New guard `tests/test_module_size.py`: every engine module ≤ 500 lines,
  facade ≤ 180; `models.py`/`api_endpoints.py`/`migrate.py` grandfathered as
  a no-growth ratchet with a forced-cleanup companion test (debt in ROADMAP
  Track 1.4).
- Pure refactor — no behaviour change. 508 server tests green, ruff + mypy
  clean.

## [0.55.1] — 2026-06-10

### Removed — ARCH step 8 (Zustand) + 6c (useMutation) retired (D-2026-06-10-C)

- Docs-only. ARCH_REVIEW step 8's premise ("UI state scattered across App")
  no longer holds: App.tsx carries two raw UI useStates (error, helpOpen),
  one level deep; URL-synced state stays in useUrlSync where the URL is the
  SSOT. A store dependency for two booleans is YAGNI; mirroring URL state
  would dual-source it. Re-open trigger: ≥3-level prop drilling or the
  tablet shell. Step 6c (canvas PUT useMutation) likewise closed.

## [0.55.0] — 2026-06-10

### Added — debug/release flavor split + window screenshots + boot beacon (D-2026-06-10-A / D-2026-06-10-B / D-2026-06-09-D phase 2)

- **Flavor gating on all three layers.** Engine: `/api/debug` registers only
  under `PLOT_DEBUG=1` (release = 404). Viewer: probe enabled only when built
  with `VITE_PLOT_DEBUG=1`; the `?debug` runtime escape is removed and release
  bundles tree-shake the probe out (verified in built assets). Shell:
  `tauri-plugin-screenshots` is an optional Cargo dep behind a `debug-tools`
  feature; `tauri.debug.conf.json` (productName "Novel Debug", identifier
  `me.noory.plot.debug`, frontendDist `dist-debug`, inline screenshots
  capability) selects the debug flavor and spawns the sidecar with
  `PLOT_DEBUG=1`.
- **Window screenshots in the debug probe.** `captureScreenshot()` finds the
  Novel window (`pickPlotWindow`) and saves a PNG via tauri-plugin-screenshots;
  the path rides on the snapshot as `screenshotPath`. Time-boxed (1.5s) so a
  missing Screen Recording grant cannot stall the numeric probe.
- **Boot beacon** (inline `index.html` script, `%VITE_PLOT_DEBUG%`-gated):
  posts `{beacon:"boot"}` at page parse + error/unhandledrejection reports —
  a bundle-crash is now distinguishable from a dead engine without eyes on
  the window.
- **10s probe heartbeat** — survives the first-POST race against sidecar
  startup; a static screen keeps re-posting.
- Probe snapshots now carry sizing-diagnosis fields (`inline`, `aspect`,
  parent wrapper box, `classes`) — used to chase the anchor-ellipse bug.
- Tests: `test_debug_endpoint.py` (incl. release-404), `debugProbe.test.ts`
  (10 cases incl. hanging-capture + heartbeat), `debug-beacon.test.ts`.
  505 server + viewer suite green; ruff + mypy + tsc clean. End-to-end
  verified in the debug-flavor .app (boot beacon + heartbeats + screenshot
  received through the channel).

## [0.54.0] — 2026-06-09

### Added — dev-only debug channel for WKWebView introspection (D-2026-06-09-D)

- New `/api/debug` engine endpoint (GET/POST, in-memory, dev-only) in a separate
  `debug_endpoints.py` module. The viewer's `lib/debugProbe.ts` collects
  on-screen state (theme, React Flow watermark presence, per-node computed colour
  + layout rect) and POSTs it; `startDebugProbe()` (wired in `main.tsx`)
  auto-posts on debounced DOM mutations when enabled (`VITE_PLOT_DEBUG=1` or
  `?debug`). An external agent GETs `/api/debug` to introspect the Tauri
  WKWebView, which CDP tools (chrome-devtools, Playwright) can't attach to on
  macOS.
- Not part of the product surface; no-op unless explicitly enabled.
- Tests: `test_debug_endpoint.py` + `debugProbe.test.ts`. 504 server + 820 viewer
  green; ruff + mypy + tsc clean.

## [0.53.1] — 2026-06-09

### Fixed

- Sorted imports in `tests/test_sync.py` (ruff I001) — pre-existing lint, no
  behaviour change. Restores a clean `ruff check` across `mashbill/` + `tests/`.

## [0.53.0] — 2026-06-09

### Changed — git moves to the workspace (.plot/) level, not per project (D-2026-06-09-C)

- The per-project git repo (one `.git` per `.plot/{project_id}`) is replaced by
  a single repo at the `.plot/` workspace level. `ensure_repo` / `tag_snapshot` /
  `publish_snapshot` / `find_latest_publish_commit` / `revert_publish` all target
  `.plot/`, so every project under one `.plot/` shares one history (user:
  "워크스페이스에만 깃이 있어야 한다"). The repo sits at `.plot/`, not the launch
  folder, so non-Novel files there are never tracked.
- `git_store`'s `project_dir` parameter renamed to `workspace_root`; call sites
  (`folder_io.create_project` / `publish_node` / `unpublish_node`,
  `mcp_tools.plot_tag`) pass `plot_root`.
- Migration: none needed (no legacy per-project `.git` in scope). New workspaces
  init the repo at `.plot/` from the first project. Hoisting to the launch root
  for multi-`.plot` workspaces is deferred.
- Tests: `test_workspace_git.py` + updated `test_folder_io` git-wiring tests.
  500 server tests green, ruff + mypy clean.

## [0.52.2] — 2026-06-09

### Removed — React Flow attribution watermark (D-2026-06-09-B)

- The canvas no longer shows the bottom-right "React Flow" attribution badge.
  Added `proOptions={{ hideAttribution: true }}` to the `<ReactFlow>` in
  `SketchCanvas`. `reactflow` is MIT-licensed, so hiding the attribution (which
  xyflow recommends but does not require) is permitted; Novel ships as a
  commercial desktop app.
- SketchCanvas LOC ceiling 515 → 516 (the single added prop); pinned in
  `structural-guards.test.tsx`.
- Test: `react-flow-attribution.test.tsx` asserts `.react-flow__attribution`
  is absent. TDD Red→Green; 817 viewer green, tsc clean.

## [0.52.1] — 2026-06-09

### Fixed — node card text vanished on the light card in dark mode (D-2026-06-09-A)

- A node card's background is the user's fixed colour (`data.color`, usually a
  pastel), not a theme surface — so in dark mode the on-card text flipped to a
  light foreground and disappeared on the still-light card (user: "노드 안에
  글자 색깔은 검은 색으로 그냥 가도 되는데"). The card div now carries a
  `node-card` class; `theme/tokens.css` re-locks the on-card foreground vars
  (`--fg`, `--fg-strong`, `--fg-secondary`, `--fg-muted`, `--fg-faint`) plus
  the inline-code (`--surface-subtle`) and count-chip (`--line`) backgrounds to
  their `:root` (light) values, so card text reads dark-on-light identically in
  both themes. Chrome *outside* the card — handles, the ⚠ markdown-warning
  badge, the selection ring — still follows the theme.
- Light appearance is unchanged: the locked values equal `:root`.
- Tests: `theme-tokens.test.ts` asserts `.node-card` vars equal the `:root`
  light values (parity + light fidelity); `nodes/base-node-dark.test.tsx`
  asserts the card root carries `node-card`. TDD Red→Green; 816 viewer green,
  tsc clean, .app rebuilt + launched (engine :5190 healthy).

## [0.52.0] — 2026-06-09

### Changed — canvas cache moved onto TanStack Query (D-2026-06-08-A, step 6b)

- `useProject`'s canvas cache (`Map<CanvasKey, CanvasDoc>`) now lives in a
  TanStack Query (`["canvases", path, id]`) instead of `useState`, above the
  `api.ts` engine seam. `setCanvasCache` is preserved as a `setQueryData`-backed
  setter, so every mutation call site is unchanged (useCanvasPersist
  edits/undo/redo, useProjectSocket external changes, publish/unpublish).
  `openProject` is now `setActiveId` (the query loads on key change);
  tags/service_details + the undo reset sync on project *switch* only.
  `staleTime: Infinity` — the WebSocket drives external-change refresh.
- Tests: the 3 `useProject` tests are wrapped with `QueryClientProvider`
  (`makeQueryWrapper`). 807 viewer green; tsc clean; build OK.
- ⚠ Visual verification of live editing / save / undo / project-switch is
  pending — the test suite passes but does not exercise those interactions.

## [0.51.0] — 2026-06-09

### Added — TanStack Query infrastructure (D-2026-06-08-A, step 6a)

- `@tanstack/react-query` + `src/app/queryClient.ts` (local-engine defaults: no
  refetch-on-focus since the WS drives external-change refresh, short retry,
  modest staleTime) + `QueryClientProvider` at the app root (`main.tsx`). The
  foundation for moving server state (canvases, project list, published
  versions, dir tree) off the hand-rolled hooks onto the query/mutation cache,
  above the `api.ts` engine seam. No behaviour change yet — nothing queries.
- `tests/test-utils.tsx` `renderWithProviders` — a fresh, retry-disabled client
  per render for components that read server state.

## [0.50.3] — 2026-06-08

### Added — undo regression guard (D-2026-06-08-A, step 7 regression-first)

- `tests/project-history.test.ts` pins the project-level unified undo stack
  (cross-canvas LIFO, redo-frontier clear on push, reset on project switch /
  external change, 50-entry cap) — the weakest seam for the server-state
  migration. Any later step that regresses undo now fails the build.

## [0.50.2] — 2026-06-08

### Fixed — empty-state headings invisible in dark mode

- `EmptyState` ("No projects yet") and the `ProjectPicker` title had no colour
  class — they relied on the body default. In dark mode (and on any build where
  the body's colour token is missing) they rendered dark-on-dark / invisible.
  Pinned both headings to `text-fg-strong` so they theme explicitly rather than
  via inheritance (inheritance is exactly what broke here). The raw-palette
  guard can't catch a *missing* colour, so this was caught by user testing.

## [0.50.1] — 2026-06-08

### Changed — docs (D-2026-06-08-A, step 5)

- Reconciled the stale `App.tsx` LOC ceiling in CLAUDE.md Gate 2 (485 → the
  enforced 498 in `structural-guards.test.tsx`). The `useAppCallbacks` follow-up
  is deferred: App is under the ceiling (488/498) and the upcoming TanStack
  Query / Zustand steps move server + UI state out of App (net reduction), so
  the extraction would be churn now — revisit only if a step pushes it over 498.

## [0.50.0] — 2026-06-08

### Changed — engine seam confined to src/app + src/hooks (D-2026-06-08-A, step 4)

- New application layer `viewer/src/app/{files,workspace,project,publish}.ts` —
  the single seam over `api.ts` for presentation. Re-homed the 6 presentation
  imports (PublishedMDModal, DetailsSection, PublishedVersionsSection,
  DirTreePickerModal, MDFileEditor, App.tsx) + `mdImagePlugin` off `../api`
  onto `src/app`.
- A structural guard now fails the build if any file outside `src/app` /
  `src/hooks` value-imports `api.ts` (type-only imports stay allowed). So when
  the engine moves in-process (tablet, TS), only `src/app` + the data hooks
  change, not presentation.

### Fixed

- `mdImagePlugin` hardcoded `/api/files/raw?…`, bypassing the `VITE_PLOT_ENGINE`
  seam (would break a separately-bundled desktop frontend). It now builds the
  URL via `api.rawFileUrl` (through `src/app/files`), hitting the configured
  engine origin.

## [0.49.0] — 2026-06-08

### Fixed — self-echo guard no longer leaks (D-2026-06-08-A, step 3)

- Replaced the `Set<CanvasKey>` write-echo guard (shared by `useCanvasPersist`
  and `useProjectSocket`) with `lib/echoGuard.ts` — a per-key in-flight COUNT
  with a TTL safety net + an explicit error path. Fixes two bugs:
  - a failed PUT left the key in the Set forever, so every later *real*
    external change to that canvas was silently dropped as "our own echo";
  - the Set was count-blind, so two in-flight writes to one key produced two
    echoes but one delete → the second echo was treated as external and
    wrongly cleared the undo history.
- `expect()` now fires at PUT send-time (not schedule-time, so a debounced-away
  edit isn't counted); `fail()` retires the slot on PUT error; a TTL decrement
  retires a write whose echo never arrives.

## [0.48.0] — 2026-06-08

### Changed — theme becomes a design-token layer (D-2026-06-08-A, steps 1-2)

- Extracted the semantic theme tokens into `viewer/src/theme/tokens.css` (the
  design-token SSOT), imported ahead of `styles.css`. Added `color-scheme`
  (light / dark) so native UI (scrollbars, form controls) follows the theme.
- Added a FOUC pre-paint `<head>` script in `index.html` that applies `.dark`
  before React mounts, so there is no flash of the wrong theme. It mirrors
  `theme/ThemeProvider`; its unavoidable duplicated literals (storage key,
  media query, `dark` class) are pinned against the source of truth by
  `theme-fouc.test.ts`.

### Fixed

- `index.html` body still used the dead `bg-paper` / `text-ink` classes
  (removed in v0.47); replaced with the `bg-surface` / `text-fg` tokens. The
  structural raw-palette guard now also scans `index.html`, so a dead or raw
  colour class there fails the build.

## [0.47.0] — 2026-06-07

### Added — light / dark theme (D-2026-06-07-C)

- Semantic CSS-variable theme tokens in `styles.css` (`:root` = light,
  `.dark` = dark): `surface*` / `fg*` / `line*` / `overlay` neutrals +
  `accent` / `warn` / `ok` / `danger` / `info` / `special` status families.
  Tailwind maps them via `rgb(var(--token) / <alpha-value>)` with
  `darkMode: "class"`. Light values equal the pre-theme palette, so the
  light UI is preserved.
- `theme/ThemeProvider` + `useTheme` — resolves the choice against the OS
  `prefers-color-scheme`, applies `.dark` on `<html>`, and persists explicit
  choices to `localStorage["plot:theme"]` (`light` | `dark` | `system`);
  default follows the OS and tracks live changes.
- `shell/ThemeToggle` — Light / Dark / System pill next to the language
  toggle (sidebar footer + ServiceDetail stencil panel); labels i18n `theme.*`.
- Guards: `structural-guards` bans raw Tailwind palette colour classes
  viewer-wide (forces tokens so dark mode works); `theme-tokens.test.ts`
  pins each light token = its original palette hex; `theme*.test` cover
  resolution / persistence / toggle.

### Changed

- Migrated 614 hardcoded palette colour classes across 52 components to
  semantic tokens (text / background / border / ring / divide). Core
  neutrals are unchanged in light; a few in-between shades and per-kind
  reference-block tints consolidated to the nearest semantic token.
- Removed the dead `ink` / `paper` Tailwind colours (0 usages).

## [0.46.0] — 2026-06-07

### Added — project picker (Tauri desktop entry) + i18n single-namespace guard

- `viewer/src/shell/ProjectPicker.tsx` — the no-workspace screen. Inside Tauri
  (`window.__TAURI_INTERNALS__` present) it shows an "Open Folder" button that
  calls `@tauri-apps/plugin-dialog` `open({ directory: true })` and redirects to
  `/?project_path=<selected>`; in browser dev it keeps the URL-param hint. Makes
  a double-clicked `.app` (no URL bar) usable. (D-2026-06-07-B)
- `viewer/tests/structural-guards.test.tsx` — new guard: no `src` file may pass
  a namespace string to `useTranslation()`. The viewer loads one `translation`
  bundle (D-2026-05-11-D); a namespace arg points `t()` at a non-existent
  namespace. Pins the cause of the Fixed bug below across the whole viewer.
- `viewer/tests/project-picker-i18n.test.tsx` — renders ProjectPicker against
  the real i18n bundle and asserts translated text (not raw keys).
- `@tauri-apps/plugin-dialog` dependency (viewer).

### Changed

- `viewer/src/App.tsx` — the inline hardcoded "Novel" / URL-hint placeholder is
  replaced by `<ProjectPicker />` (also removes a hardcoded English string;
  495 → 487 LOC, ceiling 498).
- i18n: `shell.projectPicker.{title,openFolder,hint}` keys (en + ko).

### Fixed — ProjectPicker i18n namespace bug

- ProjectPicker called `useTranslation("shell")` and looked up keys without the
  `shell.` prefix. The viewer loads a single `translation` namespace (per
  D-2026-05-11-D), so there is no `shell` namespace — every key rendered as its
  raw string ("projectPicker.title" shown verbatim). Fixed to `useTranslation()`
  + full-path keys (`t("shell.projectPicker.*")`). The sibling
  `project-picker.test.tsx` missed it because it mocked `t: (k) => k`; the new
  real-bundle test + structural guard above prevent recurrence. (TDD Red→Green)

## [0.45.0] — 2026-06-07

### Added — EngineClient seam: configurable engine origin

- `viewer/src/api.ts` now derives the engine HTTP base from
  `VITE_PLOT_ENGINE` (falling back to same-origin `""`), and the WebSocket
  base mirrors it. This is the single place the engine location is set — the
  forward-compat seam for a bundled desktop app (Tauri serves the frontend
  from `tauri://` and calls the sidecar engine at `http://127.0.0.1:5190`)
  and a future relocated/remote engine (tablet). Web / engine-served /
  Vite-proxied dev are unchanged (empty base = same-origin).
- `viewer/src/vite-env.d.ts` — types `import.meta.env.VITE_PLOT_ENGINE`.

### Changed — engine allows cross-origin local calls

- `mashbill/http_app.py` mounts `CORSMiddleware` (`allow_origins=["*"]`) so a
  separately-bundled desktop frontend can call the `127.0.0.1` engine
  cross-origin. The engine binds loopback only; auth/token hardening is a
  separate follow-up.

## [0.44.0] — 2026-06-07

### Added — identity output model: status + provenance (D-2026-06-07-A)

- `identity` is an **output** kind (AI-derived from mission + core_value), so
  it now carries two structural output-model fields, stored in `canvas.json`
  only (NOT in the published MD typed-text split):
  - `status` — `manual` (hand-authored; default) / `derived` (AI draft) /
    `confirmed` (user-locked). Tracks the derive→confirm lifecycle.
  - `provenance` — `string[]` of source node ids this identity was derived
    from (traceability for "why does the AI say this is us").
- Inspector: a status `<select>` + a provenance chip editor (add via Enter /
  Add button, remove via ×). All strings routed through i18n (en + ko), incl.
  a new `fieldPlaceholder` namespace; the previously hardcoded identity
  description placeholder is now i18n-backed.
- Graceful degradation: identity stays fully usable hand-authored
  (`status="manual"`, `provenance=[]`). No migration needed — Pydantic /
  `fromJson` supply defaults for pre-v0.44 nodes lacking the keys.

### Deferred

- `evolution` (revision history) is **not** implemented — it overlaps git
  history + `BaseFields.version` and has no writer yet (AI derivation is
  unbuilt). Filed for when an AI-derivation writer lands. See
  docs/node-format/foundation/identity.md.

### Tests

- 5 new server cases (`test_identity_format_migration.py`) + 4 new viewer
  domain cases (`round-trip.test.ts`). 498 server + 745 viewer green;
  tsc + mypy + ruff clean. Schema parity holds.

## [0.43.2] — 2026-06-06

### Changed — identity kind = description + body (do/dont removed, D-2026-06-06-B)

- Removed identity's `do` / `dont` typed fields (the shared do/dont cut now
  covers the whole foundation triad); identity = `description` + `body`.
- Migration (no data lost), server + viewer: non-empty `do` / `dont` fold
  into `body` as `## Do` / `## Don't`. Verified on the BANAS blueprint
  (14 identity nodes, do/dont gone, descriptions intact).
- With all 3 foundation kinds now single typed-section, the MD-template
  multi-section tests were updated to the single-section reality.
- The identity **output-value model** (provenance / evolution / status) and
  facet grouping remain a separate future change — see
  docs/node-format/foundation/identity.md.
- Tests: `tests/test_identity_format_migration.py` (new) + updated
  canvas_doc / md_template / round-trip / smoke / parity. 493 server + 741
  viewer green; tsc clean.

## [0.43.1] — 2026-06-06

### Changed — core_value kind = definition + body (do/dont removed, D-2026-06-06-B)

- Removed core_value's `do` / `dont` typed fields; core_value = `definition`
  (the value as a decision-priority principle) + `body`. `do` was a
  restatement of `definition`; `dont` went unused (0/5 in the BANAS sim).
- Migration (no data lost), server + viewer: non-empty `do` / `dont` fold
  into `body` as `## Do` / `## Don't` paragraphs; keys dropped. Verified on
  the BANAS blueprint (관용: definition kept, do folded into body).
- Maps + SECTION_LABELS + inspector (DoDontFields dropped) updated; the
  shared `do`/`dont` i18n keys stay (identity/service still use them).
- Tests: `tests/test_core_value_format_migration.py` (new) + updated
  canvas_doc / md_template (multi-section coverage moved to identity) /
  round-trip / smoke / parity. 489 server + 740 viewer green; tsc clean.

## [0.43.0] — 2026-06-06

### Changed — mission kind format = label + statement + body (D-2026-06-06-C)

- Implemented the mission audit conclusion. The typed fields `what_we_do` /
  `why` / `direction` are removed; mission now carries a single
  **`statement`** field (the mission, one sentence; display label "미션") +
  the free `body`. A mission is one declaration, not 3 sliced angles.
- **Migration (no data lost):** both server (`MissionNode`
  `model_validator(mode="before")`) and viewer (`Mission.fromJson`) migrate
  legacy nodes — `what_we_do` → `statement`, `why` / `direction` fold into
  `body` as `## Why` / `## Direction` paragraphs. `label` is left untouched.
  Verified end-to-end on the BANAS blueprint.
- Publish + MD parity follow data-drivenly: `FOUNDATION_TYPED_TEXT_FIELDS`
  / `FOUNDATION_MD_FIELDS` / `SECTION_LABELS` updated; the mission inspector
  shows the statement field + body; i18n `inspector.field.statement` (en+ko),
  old whatWeDo/why/direction keys removed.
- Tests: `tests/test_mission_format_migration.py` (new) + updated
  test_canvas_doc / test_folder_io / test_md_publish / test_md_template /
  viewer round-trip + inspector smoke + schema parity. 485 server + 739
  viewer green.

## [0.42.4] — 2026-06-06

### Changed — stencil ⓘ popover copy tightened to the user's wording (D-2026-06-06-A)

- Mission — "이 프로젝트가 무엇을 위해 존재하는지 한 문장으로 표현하세요."
- Core values — "의사결정의 기준 가치예요."
- Identity — "정체성을 나타내는 방식이에요."
- i18n only (`stencil.info.*`, en + ko); SPEC table + test assertion updated.

## [0.42.3] — 2026-06-06

### Changed — stencil ⓘ popover copy is friendly + plain (D-2026-06-06-A)

- Rewrote the concept popover text from terse metaphors ("존재의 뿌리",
  "쌓여가는 지향") into friendly, plain descriptions a newcomer understands
  on first read:
  - Mission — why the project exists / what it's built for.
  - Core values — the values you lean on when deciding ("when X, choose Y").
  - Identity — the character (voice/design/attitude) the product wants;
    AI proposes a start from mission & core values, refined together.
- i18n only (`stencil.info.*`, en + ko). SPEC gist table updated.

## [0.42.2] — 2026-06-06

### Removed — Foundation stencil inline usage-notes (D-2026-06-06-B)

- Dropped the inline `note` under the Foundation stencil sections —
  "필요한 만큼 추가하세요" (Mission / Core values) and "속성별로 하나씩 —
  목소리, 에너지, 말투, …" (Identity). With the ⓘ concept popover
  (D-2026-06-06-A) carrying the meaning, the inline note was redundant
  clutter. Deleted i18n keys `stencil.note.addAsManyAsYouNeed` +
  `stencil.note.identityOnePerAspect`.
- Test: `stencil-concept-info.test.tsx` asserts no note text on foundation
  sections. Other canvases' notes (drop hints) unaffected.

## [0.42.1] — 2026-06-06

### Fixed — stencil ⓘ popover was clipped by the sidebar scroll container (D-2026-06-06-A)

- The concept popover (`w-56`) overflowed the narrow stencil sidebar and was
  cut off by its `overflow-y-auto` container (verified: popover right edge
  278px vs clipper 223px). Now the popover is **portaled to `document.body`**
  and positioned with fixed coords from the ⓘ button rect (+ right-edge
  clamp), so no parent overflow can clip it.
- Test: `viewer/tests/stencil-concept-info.test.tsx` — asserts the popover is
  portaled out of the stencil container.

## [0.42.0] — 2026-06-06

### Added — Foundation stencil concept info (ⓘ popover) (D-2026-06-06-A)

- Each Foundation stencil section header (Mission / Core values / Identity)
  now shows an always-visible ⓘ icon next to the title. Clicking it opens a
  small popover with that concept's definition, so a user who doesn't yet
  know what mission / core value / identity mean can learn it in place:
  - Mission — 존재의 뿌리, 왜 존재하는가
  - Core values — 현재의 노력, 지금 어떻게 결정하는가
  - Identity — 쌓여가는 지향, 어떤 존재가 되고 싶은가 (AI 도출)
- ⓘ is always-visible (discoverable, not hover-only); popover opens on click
  (works on touch). Concept SSOT = `docs/FOUNDATION_CONCEPT.md`.
- New `viewer/src/canvases/stencil/SectionInfo.tsx`; `Section` gains an
  optional `info` prop. i18n `stencil.info.*` (en + ko). Foundation-only.
- Tests: `viewer/tests/stencil-concept-info.test.tsx` (3 cases).

## [0.41.0] — 2026-06-04

### Changed — mindmap arm follows the stored hub-side handle (D-2026-06-01-H)

- Mindmap auto-layout assigns each top-level branch to an arm by reading,
  *first*, the **hub-side handle** its edge is pinned to (`t/r/b/l` →
  `U/R/D/L`). The connection becomes the control surface: drop a line on the
  hub's right handle and that branch lays out right, regardless of where the
  node box currently sits. When an edge has no stored hub-side handle (legacy
  floating-era edges), it **falls back** to the node's current side of the hub
  (the previous D-2026-06-01-F rule). On-hub + no-handle still spreads by
  subtree leaf-count.
- `edgeTransform.resolveHandles` is updated symmetrically: a **stored** handle
  wins for edge attachment, with the geometric facing-side used only when an
  end has no stored handle — keeping the attachment side consistent with the
  arm the layout chose.
- Supersedes the arm-assignment half of D-2026-06-01-F (the within-arm
  tidy-tree shape + leaf-count spread are unchanged).
- Tests: `viewer/tests/mindmapLayout.test.ts` — hub-handle override + no-handle
  fallback cases (10 passing). Authored 2026-06-01, shipped 2026-06-04.

## [0.40.5] — 2026-06-04

### Changed — auto-layout (⊞) is one action button; mode in tooltip text only (D-2026-06-04-A)

- v0.40.4 gave ⊞ a mode-*shaped* icon (tree vs flow). That made it read like
  the direction toggle (↔/↕), whose icon flips on click to switch a mode — so
  clicking ⊞ (which executes the layout, moving nodes) felt contradictory.
  User: *"그걸 누르면 왜 정렬이 변하냐고"*.
- ⊞ now shows **one mode-neutral "auto-arrange" icon** on every canvas
  (`TreeIcon`/`FlowIcon` → single `ArrangeIcon`). The layout still differs per
  canvas, but the mode is named only in the **tooltip text**
  (`autoLayoutTree` / `autoLayoutFlow`). Only the direction toggle shows
  mutable state now; ⊞ is purely an action.
- Supersedes the icon half of v0.40.4 (the mode-specific label +
  `data-layout-mode` are kept).

## [0.40.4] — 2026-06-03

### Changed — auto-layout (⊞) button icon is mode-specific (D-2026-06-03-D)

- ⊞ runs a different arrangement per canvas — mind-map tree on Foundation /
  Actors / Services, actor-anchored flow on ServiceDetail — but one glyph hid
  which. User: *"어떤 모드인지 아이콘이 같으니 알 수가 없네"*.
- The button now shows a mode-specific icon + label: a hub-and-branches mark
  ("마인드맵 정렬" / "Mind-map layout") in tree mode, a left→right node-sequence
  mark ("흐름 정렬" / "Flow layout") in flow mode. Mode derives from
  `showDirectionSwitch` (ServiceDetail = flow); button carries
  `data-layout-mode`. Same legibility logic as the v0.40.3 direction toggle.

### Removed

- i18n key `canvas.autoLayout` (replaced by `canvas.autoLayoutTree` /
  `canvas.autoLayoutFlow`).

## [0.40.3] — 2026-06-03

### Changed — ServiceDetail direction control is one state-showing toggle (D-2026-06-03-C)

- The two separate ↔ (LR) / ↕ (TB) layout buttons gave no indication of the
  current direction — pressing them rotated the flow with no visible state.
  User: *"누를 때마다 왔다 갔다 하는데 정렬 버튼에 어떤 상태를 표시해주면
  좋을 것 같은데"*.
- Replaced with a SINGLE toggle that shows the current direction as its icon
  (↔ horizontal / ↕ vertical) and flips to the other axis on click
  (horizontal → TB, vertical → LR). Current direction is read from the
  subject-edge handle via the new `detectAnchorDirection(doc)` (SSOT).
- `LayoutControls` takes a `doc` prop to derive the direction; `SketchCanvas`
  passes `doc` (stays under the 515-LOC ceiling).

### Removed

- i18n keys `canvas.layoutLR` / `canvas.layoutTB` (replaced by
  `canvas.layoutNowLR` / `canvas.layoutNowTB`, which name the current state).

## [0.40.2] — 2026-06-03

### Fixed — actor→entry gap scales with the entry's extent (D-2026-06-03-B)

- `actorAnchoredLayout` placed the entry step at a fixed 220 px centre-to-centre
  from the actor. A wide auto-fit entry overlapped the actor — surfaced in the
  BANAS sim s-onboard detail, where the ~307 px "닉네임 입력" entry overlapped
  the 168 px BANA actor circle by ~18 px after ⊞.
- The gap is now `max(220, actorHalf + entryHalf + 40)` along the layout axis
  (width for LR/RL, height for TB/BT). Small nodes keep the 220 px default;
  wide entries get pushed out until they clear the actor.
- Regression: `actor-anchored-layout.test.ts` — wide actor + wide entry; asserts
  the entry's near edge clears the actor's far edge. Same "no overlap" principle
  as v0.40.1, on the actor→entry tier.
- Scope: `flow/actorAnchoredLayout.ts` only.

## [0.40.1] — 2026-06-03

### Fixed — injection (essence) nodes never overlap in actor-anchored layout (D-2026-06-03-A)

- `actorAnchoredLayout` placed each injection-source ref at a fixed ≈160 px in
  its `targetHandle` direction with no collision check. When two refs' targets
  shared a dagre column and both defaulted to *above* (no `targetHandle`), the
  refs piled up on each other and the steps — visible in the BANAS sim s-auth
  detail after ⊞ (two essence circles overlapping the flow). User: *"적어도
  노드가 겹치면 안되구요. 핸들에 연결 위치로 노드 위치를 정해야해요."*
- Tier-3 now checks the slot against every placed node (actor anchor, dagre
  steps, earlier refs) and, on collision, pushes the ref **further out along
  the same handle axis** (80 px steps, ≤ 24 hops) until it clears. The ref
  stays on its target's column / row — handle direction preserved — only its
  distance grows. Deterministic.
- Regression: `actor-anchored-layout.test.ts` — branch with two same-column
  injection targets; asserts no pairwise node overlap and each ref stays on its
  target's column.
- Scope: `flow/actorAnchoredLayout.ts` only (ServiceDetail path); separate from
  the uncommitted handle-based mindmap layout work.

## [0.39.0] — 2026-06-01

### Changed — auto-layout is a hierarchy TREE, not concentric circles (D-2026-06-01-C)

- The v0.34.8 radial depth-ring layout placed nodes in concentric circles by
  hierarchy depth (level-1 inner ring, level-2 the ring outside that, …), so a
  child sat far from its parent on an outer ring. User: *"원을 자꾸 만드는데요
  … 원이 아니라 트리가 되어야죠 … 하위노드를 상위노드에 가깝게 정렬을
  해야지."*
- `useAutoLayout` now uses `computeAutoLayout` again — the Reingold-Tilford
  **tree**: each child is placed adjacent to its parent (subtree-spaced so
  branches don't overlap), so a service clusters beside its category, etc.
  Direction is inferred from the nodes' **current positions** (not edge
  handles), so the v0.34.8 swap/depth-crossing bugs — which came from reading
  floating edges' nulled handles — don't return.
- The radial `computeRadialLayout` (preserve mode + collision avoidance from
  v0.34.8/v0.37.2) stays for the `layoutAlgo="radial"` button; the default
  `"tree"` canvases (Foundation / Actors / Services) get the tree.
- `autoLayout.test.ts` direction tests rewritten position-inferred. viewer
  722/722; tsc clean. Browser-verified on BANAS Services: categories branch
  from the anchor with their services clustered beside them (a tree).
- Known follow-up: a couple of cross-branch nodes can still crowd near the
  anchor — tightening filed.

## [0.38.0] — 2026-06-01

### Changed — nodes auto-fit their content; manual resize removed (D-2026-06-01-B)

- Every node now sizes to its content (label + kind tag + body). The manual
  ``NodeResizer`` is gone (user: *"노드 사이즈를 컨텐츠에 핏하게 … 항상
  자동핏입니다. 수동 리사이즈 없애요."*). Rectangular kinds fit their content
  width (140–340px, wrap); round shapes (circle/ellipse incl. the **project
  anchor**) fit as a square (``aspect-square``) so they stay circular — the
  anchor shrinks to its content too (user: *"바나스 앵커는 왜 안줄이죠?"*).
- A ``ResizeObserver`` in ``BaseNode`` persists the measured size back to the
  doc (via ``onResize`` / ``onAnchorChange``), so React Flow's
  ``nodeInternals`` — which **floating edges** and **auto-layout** read — and
  the saved blueprint all match the visual. Fixes two regressions the auto-fit
  first introduced: edges attaching to a phantom old-size box (*"작아지고 난
  후에 연결선이 이상해졌어요"*) and auto-layout's no-overlap spacing using the
  old sizes (*"정렬이 예전 노드 사이즈를 기준으로 하는 것 같다"*).
- The kind tag (top-left) now clears the label with a top margin on compact
  nodes (user: *"태그하고 라벨하고 겹쳐요"*).
- Known caveat: the first measurement of each node on load settles its size
  through ``onDocChange`` (one undo entry per node until stable). Follow-up:
  a non-history "measurement sync" path + extract a ``useAutoFitSize`` hook.
- BaseNode LOC ceiling 270 → 300. viewer 722/722; tsc clean. Verified on the
  BANAS Foundation canvas (21 nodes): content-fit, edges attach, anchor
  circular + shrunk, auto-layout tight with 0 overlaps.

## [0.37.2] — 2026-06-01

### Fixed — auto-layout no longer overlaps nodes (collision avoidance) (D-2026-06-01-A)

- The angle-preserving depth-ring layout (v0.34.8) had no collision avoidance:
  on a busy canvas (BANAS Services — 7 categories + 11 services) running
  auto-layout collapsed many nodes onto the same ring slot — "정렬하면 노드들이
  다 겹쳐요" (11 overlapping pairs measured).
- ``computeRadialLayout`` now, per ring: (1) grows the ring radius so the
  circumference fits every node without overlap (2π·r ≥ count · node-arc), and
  (2) fans apart nodes whose angles sit closer than one node-span + gap
  (``spreadRingAngles``) — keeping relative order and recentring on the
  cluster's middle so the user's chosen side is preserved.
- Verified on the BANAS Services canvas: 11 overlapping pairs → **0**. Tests: 1
  new ``radialLayout`` collision-avoidance case. viewer 722/722; tsc clean.

## [0.37.1] — 2026-06-01

### Fixed — clicking a node now selects it and stays selected (D-2026-05-31-AD)

- The controlled ``nodes`` array (``useNodesMemo``) didn't carry ``selected``,
  so React Flow reset each node's selection to the prop on every re-render
  (e.g. the Inspector opening). A click selected the node then the next render
  deselected it — "선택되고 해제되고". Selection is now tracked as state in
  SketchCanvas (``selectedIds`` from RF's ``onSelectionChange``) and
  ``useNodesMemo`` sets ``selected: selectedIds.has(id)`` on each node, so RF
  keeps the selection across rebuilds (the controlled-mode-correct pattern).
- Tests: 3 new ``nodes-memo-selection.test.ts`` cases. SketchCanvas LOC
  ceiling 500 → 515 (selection-state plumbing; follow-up: extract a
  useNodeSelection hook). viewer 722/722; tsc clean.

## [0.37.0] — 2026-05-31

### Added — "+ New folder" in the Add-a-Project picker (D-2026-05-31-AC)

- The directory picker can now **create a brand-new subdirectory** before
  placing a project in it — previously you could only pick an existing folder
  (the picker was tree-only, and the server `resolve_plot_root` 404'd on a
  missing dir). So a project can start in a folder that doesn't exist yet
  (e.g. a fresh `banana/` in a monorepo).
- Each tree row gets a **"+ 새 폴더"** button → prompts for the folder name →
  creates it under that row's directory → flows straight into the project
  name prompt. Two prompts (folder, then project), one smooth flow.
- Server: new `POST /api/workspace/dir` endpoint + `create_workspace_dir`
  helper, path-safe via `resolve_safe_path` (rejects `..` / absolute /
  escaping), idempotent. Client: `api.createWorkspaceDir` + the picker button.
- New i18n keys `dirPicker.newFolder` / `dirPicker.newFolderPrompt` (en + ko).
- Browser-confirmed end-to-end: a brand-new `banana/` folder created from an
  empty workspace, with the Banana project inside it. Server 481/481; viewer
  718/718; tsc + mypy + ruff clean.

## [0.36.2] — 2026-05-31

### Changed — category nodes render with rounded corners (D-2026-05-31-AB)

- `effectiveShape` now forces `kind === "category"` to `"rounded"` (soft
  corners), regardless of the node's stored shape — matching the master-kind
  look. Category nodes are group headers on the Services canvas; sharp
  corners looked out of place. User: *"카테고리 모퉁이 둥그스럼하게"*.
  Render-time policy (SSOT in `nodeShape.ts`), so existing + new categories
  both round. Browser-confirmed. viewer 715/715; tsc clean.

## [0.36.1] — 2026-05-31

### Changed — restore the "no canvas_kind branching in sketch hooks" invariant (D-2026-05-31-AA)

- The v0.34.4 floating-edge work (D-2026-05-31-R) re-introduced
  `doc.canvas_kind === "foundation" || "actors"` branches in `useFlowHandlers`
  and `useEdgesMemo` — exactly the god-dispatch the v0.15 reset banned, which
  the `pre_commit_gate` reset-check had been flagging red.
- Replaced both with a wrapper-supplied `convergeArrowsOnAnchor` prop
  (FoundationCanvas + ActorsCanvas pass `true`), threaded through SketchCanvas
  to the two hooks — the same pattern as `hideRootServiceNode` /
  `layoutAlgo` / `showFoldButton`. The hooks no longer read `canvas_kind` to
  branch behaviour. `classifyEdge(canvas_kind, …)` stays (it passes the kind
  as data, not a branch).
- Behaviour preserved: Foundation + Actors arrows still converge on the
  project anchor (browser-confirmed). `test_pre_commit_gate` is green again
  (server 477/477). SketchCanvas LOC ceiling 490 → 500 (plumbing-only prop
  threading). viewer 714/714; tsc clean.

## [0.36.0] — 2026-05-31

### Added — project creation asks WHERE + a name, on both the web viewer and via a skill

- **Web viewer (D-2026-05-31-Y):** "+ Add a Project" → pick a directory →
  now **prompts for the project name** (in-app dialog) instead of silently
  creating "Untitled". Cancelling the name prompt aborts creation; opening an
  existing project (the dir already holds one) does NOT prompt. New i18n keys
  `sidebar.newProjectNamePrompt` / `newProjectNamePlaceholder` (en + ko).
- **`/plot-new-project` skill (D-2026-05-31-Z):** a user-invocable skill that
  creates a Novel project in a **chosen directory** and opens it. Built for the
  monorepo case (Banas + Banana side by side): the plugin is installed once at
  the monorepo root, but each app service gets its own `.plot/` next to its
  code. The skill asks WHERE (which subdir) + a name, builds a unique
  `project_id`, calls `create_project_tool`, then `open_canvas`. Never invents
  a directory.

These two share the same server foundation (`create_project` /
`create_project_tool`); the web picker and the skill are the two front doors
to it.

Tests: 3 new `project-create-name.test.tsx` cases (prompt+create, cancel,
open-existing-no-prompt); `create-in-dir.test.tsx` updated for the name
prompt. viewer 714/714 green; tsc clean.

## [0.35.1] — 2026-05-31

### Fixed — "Add a Project" picker no longer shows "열기" for an empty `.plot` (D-2026-05-31-X)

- `build_dir_tree`'s `has_plot` flag now means "this dir holds a **real
  project**", not merely "a `.plot` folder exists". A stray read can leave
  an empty `.plot/` behind (`resolve_plot_root` + the watcher both `mkdir`
  it); counting that as a project made the picker label the dir **열기**
  (open), and clicking it landed in `create()` with nothing to open → a
  phantom new project. `has_plot` now uses `enumerate_projects` (the same
  validated scan the sidebar lists), so it matches what is actually openable.
- This is the canonical monorepo case (e.g. Banas + Banana side by side):
  each app service has its own `.plot/` in its subdir, and the picker's
  열기/생성 fork is now honest per dir.
- Deferred (option B): the empty-`.plot`-on-read *litter* itself — making
  `.plot` creation lazy needs a watcher rework (watchdog requires the
  watched dir to exist).
- Tests: `test_dir_tree.py` pins empty-`.plot` → `has_plot False`, real
  project → `True`. Server 477/477 of the affected suites green; mypy + ruff
  clean. (Pre-existing unrelated red: `test_pre_commit_gate` god-dispatch
  scan, failing since before this change.)

## [0.35.0] — 2026-05-31

### Added — in-app dialog system replacing native browser popups (D-2026-05-31-W)

- New `shell/dialog/` — `DialogProvider` + `useDialog()` with a promise-based
  imperative API (`confirm` → boolean, `prompt` → string|null, `alert` →
  void). One styled modal renders at a time, matching the DirTreePicker
  chrome (slate backdrop, white rounded panel, `z-[60]` above other modals).
  Destructive confirms get rose (`danger`) styling.
- Mounted around `<App>` in `main.tsx` so every component AND hook can call
  `useDialog()`. Missing-provider only throws when a method is *called*
  (render-only unit tests don't need to wrap in the provider).

### Changed — all 13 native `window.confirm` / `window.alert` / `window.prompt` call sites migrated

- BaseInspector (delete / publish / unpublish), SketchSidebar (delete
  project / delete tag), SketchBodyModal (delete node), SketchEdgeModal
  (delete arrow), CompositionList (remove), BlueprintPublishButton
  (publish), useDragAndDrop (drop error → alert), useContextMenus (edge
  label → prompt), useProject (session tag name + message → prompt).
- Five previously hardcoded-English strings now route through i18n
  (`node.confirmDelete` / `node.confirmDeleteArrow` / `node.edgeLabelPrompt`
  / `snapshot.tagNamePrompt` / `snapshot.tagMessagePrompt`) + `common.ok` /
  `common.confirm`, added to both `en` and `ko`.

### Removed — native browser dialogs

- No `src/` file calls `window.confirm` / `window.alert` / `window.prompt`
  anymore. A new structural guard (`structural-guards.test.tsx`) fails the
  build if one creeps back.
- Tests: 8 new `dialog.test.tsx` cases (confirm/prompt/alert resolution +
  Escape/cancel + single-dialog invariant). viewer 711/711 green; tsc clean.
  Browser-verified: delete-project confirm renders styled, cancel preserves
  the project.

## [0.34.8] — 2026-05-31

### Changed — floating-canvas auto-layout: angle-preserving depth rings (D-2026-05-31-V)

- The `layoutAlgo="tree"` anchor path (Foundation + Actors directly;
  Services + ServiceDetail as the no-subject-edge fallback) no longer runs
  the handle-based directional tree. All edges are floating
  (D-2026-05-31-F) so their handles are nulled — the old tree read
  stale/arbitrary handles and (a) **swapped node sides** (Core value LEFT +
  Mission TOP came back swapped) and (b) let a **depth-2 node land between
  the anchor and its depth-1 parent** (edge crossing on
  `anchor ← user ← operator`).
- It now calls `computeRadialLayout` with a new `angleMode: "preserve"`:
  each node keeps its **current angle** from the anchor (side preserved, no
  swap), and its **distance is normalised to its BFS depth ring** (deeper
  node always farther out, no crossing).
- Implements **option (A)** of the 2026-05-31 NEXT_SESSION
  "자동정렬 위치+깊이 재작업" task. The user will review hands-on and decide
  whether to keep floating edges or instead **option (B)** revert them to
  handle-based rendering — for which `autoLayout.ts` (the old tree) is
  retained, unit-tested, as the fallback.
- Tests: 4 new `computeRadialLayout` preserve-mode cases
  (`viewer/tests/radialLayout.test.ts`) — depth enforced, side preserved,
  distance normalised, distribute mode unchanged. viewer 703/703 green;
  tsc clean.

## [0.34.7] — 2026-05-31

### Changed — blueprint version moves to the project (tab-bar); one-line status cluster (D-2026-05-31-U)

- The blueprint version badge moves from the header (next to the workspace
  path = the repo) to the **tab-bar center, next to the project name** — the
  version belongs to the project, not the repo path.
- The header status cluster (save / socket / error) drops its fixed width
  and uses `whitespace-nowrap` + `shrink-0`, so "저장 중…" no longer wraps to
  two lines; the error is the only flexible (truncating) item.

## [0.34.6] — 2026-05-31

### Fixed — arrows no longer float off the round anchor (D-2026-05-31-T)

- `floatingEdgeGeometry.nodeBorderPoint` is shape-aware: the round project
  anchor (and any circle/ellipse node) computes the floating endpoint on
  its actual ellipse circumference instead of its bounding box, so the
  arrowhead sits on the circle. Previously the box approximation — combined
  with the v0.34.5 angled bezier approach — left the arrow floating off the
  anchor. `FloatingEdge` reads each node's `data.shape`. Covered by new
  ellipse cases in `floating-edge-geometry.test.ts`.

## [0.34.5] — 2026-05-31

### Changed — floating edges render as bezier curves (D-2026-05-31-S)

- `FloatingEdge` now draws a bezier path (was straight). Control points
  leave each node perpendicular to the border side the floating endpoint
  exits (new pure `floatingEdgeGeometry.borderSide`). Diagonal edges (e.g.
  the actor inheritance tree) curve gently; axis-aligned spokes still read
  straight (clean). Covered by a `borderSide` case in
  `floating-edge-geometry.test.ts`.

## [0.34.4] — 2026-05-31

### Changed — Foundation + Actors: all arrows converge on the anchor; symmetric connect handles (D-2026-05-31-R)

- On Foundation + Actors every directed edge's arrowhead now points at the
  **anchor-ward endpoint** (nearer the project anchor) — elements compose
  INTO the service; actors PARTICIPATE in it; the actor tree's child→parent
  edges point up toward the root. Enforced at creation (`handleConnect`
  normalizes the new edge anchor-ward) and at render (`edgeTransform`
  re-orients the arrow for any stored edge; the doc edge stays the SSOT).
- All four node sides are now `source` handles (`ConnectionMode.Loose`), so
  a connection started from ANY side produces the same edge — the previous
  asymmetry (Top/Left = target, Right/Bottom = source) made the direction
  depend on which side you grabbed.
- New pure `canvases/sketch/anchorDistance.ts`. Services / ServiceDetail
  keep user-chosen direction. Covered by new `edge-transform` orientation
  cases.

## [0.34.3] — 2026-05-31

### Changed — swap: workspace path in header, project name in tab-bar center (D-2026-05-31-Q)

- The **workspace root path** now sits next to the `PLOT` logo at the very
  top (location); the **active project name** sits centered in the canvas
  tab bar. Swaps the v0.34.2 placement. The "MCP: …" socket label is
  unchanged. Header `projectName` prop → `workspaceRoot`; CanvasTabs
  `workspaceRoot` prop → `projectName`.
- Covered by updated `tests/canvas-tabs-root.test.tsx` (project name) +
  `tests/header-socket-label.test.tsx` (header shows the root path).

## [0.34.2] — 2026-05-31

### Changed — workspace root to tab-bar center; socket label "MCP: live" (D-2026-05-31-P)

- The workspace root absolute path moves from the header to the **center of
  the canvas tab bar**; the header left is just `PLOT · {project}` (the
  active project's dir is already shown in the sidebar subtitle). Supersedes
  v0.34.1's header relative-dir display (Header `projectPath`/`projectDir`
  props removed).
- The socket indicator now reads **"MCP: live"** / "MCP: connecting…" /
  "MCP: reconnecting…" / "MCP: offline" so the dot clearly refers to the MCP
  server connection.
- Covered by `tests/canvas-tabs-root.test.tsx` + `tests/header-socket-label.test.tsx`.

## [0.34.1] — 2026-05-31

### Changed — header shows the active project's relative dir (Phase 4; D-2026-05-31-O)

- The header's path slot now shows the active project's directory relative
  to the workspace root (e.g. `marketing`; root-level → "root" label)
  instead of the raw absolute workspace path. The absolute root is kept as
  the hover title. New `Header.projectDir` prop (fed `dirForId(activeId)`);
  reuses the `sidebar.rootDir` label. App.tsx LOC ceiling 497 → 498.
- Covered by `tests/header-project-dir.test.tsx`.

## [0.34.0] — 2026-05-31

### Added — "Add a Project" directory-tree picker (Phase 3; D-2026-05-31-N)

- The "Add a Project" button now opens a **directory-tree picker** (drill-
  down, rooted at the workspace root, with a `has_plot` badge per dir).
  Picking an empty dir creates a new project there; picking a dir that
  already holds a project lands in its most-recently-updated one (no
  duplicate). Tree-only — choose from existing folders (no free-text).
- New `shell/DirTreePickerModal.tsx` + `hooks/useDirPicker.tsx` (open-state
  in the hook). `useProject.create` now takes a `targetDir`. New top-level
  i18n `dirPicker.*` (en + ko). App.tsx LOC ceiling 495 → 497 (plumbing).
- Covered by `tests/dir-tree-picker.test.tsx` + `tests/create-in-dir.test.tsx`.

## [0.33.0] — 2026-05-31

### Added / Changed — multi-directory projects: unified discovery + effective path (Phase 2; D-2026-05-31-M)

- The viewer now treats the launch `?project_path=` as the **workspace
  root** and lists ALL projects discovered anywhere under it in one sidebar,
  each with a muted **directory label** (root-level shows a "root" label).
- Per-project I/O + the WebSocket use the **effective project path**
  (`root + project dir`), so projects in different subdirectories each
  read/write their own `.plot/`. Switching to a project in a different dir
  reconnects the socket; same-dir switches do not.
- The "New project" button is renamed **"Add a Project"** / "프로젝트 추가".
  (v0.33.0 still creates at the root; the directory-tree picker lands next.)
- New pure `lib/projectPath.ts::joinWorkspaceDir`; discovery + the id→dir map
  folded into `useProject` (a `dirMapRef` mirrors the map synchronously for
  the initial open). New i18n key `sidebar.rootDir`.
- Covered by `tests/projectPath.test.ts`, `tests/effective-project-path.test.tsx`,
  `tests/ws-reconnect-on-dir-switch.test.tsx`, `tests/sidebar-unified-list.test.tsx`.

## [0.32.0] — 2026-05-31

### Added — workspace discovery + dir-tree endpoints (multi-directory projects, Phase 1; D-2026-05-31-L)

- `GET /api/workspace/projects?project_path=<root>` — recursively discovers
  every Novel project anywhere under the workspace root, each with its
  directory relative to the root (`"."` for root-level). Backing the
  upcoming "a monorepo holds many projects, each in its own subdirectory"
  feature.
- `GET /api/workspace/tree?project_path=<root>` — nested directory tree
  (`name`/`rel`/`has_plot`/`children`) for the new-project picker.
- MCP mirror tool `discover_workspace_projects`. New pure helpers in
  `workspace.py` (`discover_projects`, `build_dir_tree`, shared
  `enumerate_projects`). Prune set + depth/breadth/count caps;
  `followlinks=False`. Covered by `tests/test_workspace_discovery.py`,
  `tests/test_dir_tree.py`, and new cases in `tests/test_api_endpoints.py`.
- Server-only; no user-visible behaviour yet (lands in Phase 2).

## [0.31.3] — 2026-05-31

### Fixed — hide the sidebar stencil when no project is active (D-2026-05-31-K)

- The left-sidebar stencil (`SketchStencil` in `SketchSidebar`) is now
  gated on `activeId`. With no project selected (empty workspace / "No
  projects yet") the stencil is hidden — previously it rendered the
  Foundation stencil (미션 / 코어밸류 / 아이덴티티) unconditionally, as
  if a Foundation canvas were open, with nothing to drop onto. Found in
  the hands-on empty-state walkthrough. Covered by
  `tests/sidebar-stencil-gating.test.tsx`.

## [0.31.2] — 2026-05-31

### Fixed — inherited Surface caption shows the localized label (D-2026-05-31-J)

- When an actor inherits `side` (Surface / 접점) from a parent, the
  greyed `↳ inherited from {parent}` caption now renders the localized
  option label ("사용자 — 앱" / "user — app") instead of the raw enum
  (`user`). `Inherited` gained an optional `format(raw)` prop; the
  `side` field maps operator/user → their option labels. Free-text
  fields (motivation / pain / body) are unaffected. Covered by
  `tests/inspectors/actor-inherited-surface.test.tsx`.

## [0.31.1] — 2026-05-31

### Changed — actor `side` reframed as "Surface / 접점" (D-2026-05-31-I)

- The actor Inspector's `side` field is relabeled from "Side / 역할 —
  which side of the value exchange" to **"Surface / 접점" — which system
  the actor accesses** (operator → admin console; user → app). The
  operator/user split exists because participants use different systems
  (Operator → operations page; end user → Banas app), which "role in the
  value exchange" mislabeled.
- **i18n text only** (`inspector.field.side`, `inspector.fieldHint.side`,
  `inspector.operatorOption`, `inspector.userOption`, en + ko). The
  stored enum (`operator`/`user`), the domain model, ServiceDetail
  subject detection (`side === "user"`) and layout are all unchanged.

## [0.31.0] — 2026-05-31

### Changed — abstract root superclass hides role/motive/pain (D-2026-05-31-H)

- OOP framing of the actors canvas: the **root** of an inheritance tree
  is an *abstract* superclass and carries no concrete role/motive/pain —
  those belong to the concrete subclasses. Its Inspector now **hides**
  the `side` (역할) / `motivation` (동기) / `pain` (어려움) fields and
  shows an "abstract base" caption; the `body` (노트) field stays.
- "Has children" is **not** the test: an intermediate concrete actor
  (e.g. Bana with Hero/Fans below it) has an actor parent, so it keeps
  all its fields — only the tree root is abstract. New pure
  `domain/actorInheritance.ts::isActorBaseSuperclass` (root = no actor
  parent + ≥1 actor child), covered by
  `tests/actor-base-superclass.test.ts`.
- New i18n key `inspector.actorBaseHint` (en + ko). Inheritance
  computation (`effectiveActorFields`) is unchanged — only Inspector
  field visibility.

## [0.30.4] — 2026-05-31

### Added — actor inheritance (computed) + inspector display

- On the actors canvas a sub-actor inherits its parent actor's common
  fields (motivation / pain / side / body) through the inheritance edges
  (child→parent toward the anchor). New pure
  `domain/actorInheritance.ts::effectiveActorFields` resolves each field
  `own → nearest ancestor → empty`, with the same inheritance-edge +
  lexicographic tie-break + cycle guard as fold / propagation
  (D-2026-05-31-G).
- The actor Inspector shows an inherited field as a greyed
  `↳ inherited from {parent}: …` caption under the empty input; typing
  overrides. New i18n key `inspector.inheritedFrom` (en + ko).
- Inheritance is a **derived view** — computed at render, nothing
  written; each node's value stays the SSOT.

## [0.30.3] — 2026-05-31

### Changed — floating edges (uniform connection from any side)

- Every non-self-loop edge now renders as a **floating edge**
  (`FloatingEdge` + pure `flow/floatingEdgeGeometry.ts`): it attaches to
  the point on each node's border facing the other node, ignoring
  handles, so a connection reads identically from any side
  (D-2026-05-31-F). Fixes the awkward loop seen on the Voice→Banas
  injection edge — it now runs straight Voice-left → Banas-right.
  Self-loops keep `SelfLoopEdge`.

### Fixed — injection animation stutter

- The injection edge's marching-dash animation stuttered because the
  inline dash period (`4 4` = 8) didn't divide RF's animated
  `stroke-dashoffset` cycle (10). Set to `5 5` (10) so the loop is
  seamless.

## [0.30.2] — 2026-05-31

### Changed — server publish-propagation reads `edge.relation` (Phase 2c)

- `propagation._build_parent_lookup` now derives parent↔child from the
  stored `edge.relation` via the new `edge_semantics.fold_endpoints` —
  the Python mirror of the viewer's `foldHierarchy.foldEndpoints`. `flow`
  source=parent, `inheritance` target=parent (inverted), `injection`
  excluded. Viewer fold and server publish-propagation now read the same
  SSOT (D-2026-05-31-E), closing the cross-boundary gap that motivated
  the stored field (plot-design-red-team A8).

## [0.30.1] — 2026-05-31

### Changed — viewer reads `edge.relation` (Phase 2b)

- Fold / render-sort now derive parent↔child from the stored
  `edge.relation` via the new pure `flow/foldHierarchy.ts`: `flow`
  source=parent, **`inheritance` target=parent (inverted)** — collapsing
  a superclass hides its subclasses — `injection` excluded from fold
  (D-2026-05-31-D).
- Injection edge styling (violet + animated) now reads
  `edge.relation === "injection"` in `edgeTransform`, so it fires on
  **every** canvas — foundation `mission`/`core_value`/`identity` →
  anchor edges now render as the "value injection" visual, not just
  service_detail refs. `actorAnchoredLayout` injection exclusion reads
  `edge.relation` too.

### Removed

- `flow/foundationRefKinds.ts` — dead after the switch to the stored
  `relation` SSOT (its kind set is now `edgeSemantics.ESSENCE_SOURCE_KINDS`).

### Notes — pinned behaviour change

- Injection (`*_ref`) edges are now **excluded from the service_detail
  fold map** (previously every directed edge counted). Correct — a ref
  injects into a step, it doesn't contain it. No fixture relied on the
  old behaviour; no data migration. Inheritance edge *styling* is
  deferred to the user's canvas look-and-feel review (renders as a
  default directed edge for now; only the fold semantic changed).

## [0.30.0] — 2026-05-31

### Added — stored edge `relation` semantic (Phase 2a)

- New stored `SketchEdge.relation` field
  (`flow` | `injection` | `inheritance`, default `flow`) — the one SSOT
  for an edge's semantic, read by both the viewer (fold / layout /
  styling, Phase 2b) and the server `propagation.py` (publish
  MINOR-bump, Phase 2c). D-2026-05-31-C.
- `classifyEdge(canvas, source-kind)` default-assigner, mirrored in
  `viewer/src/flow/edgeSemantics.ts` and `mashbill/edge_semantics.py`
  with a TS↔Python parity guard (`tests/test_edge_semantics.py`):
  actors-canvas → `inheritance`; essence source (`mission`/`core_value`/
  `identity` + their `*_ref`, not `actor_ref`) → `injection`; else `flow`.
- Read-time migration (`_migrate_assign_edge_relation`) assigns
  `relation` to legacy edges on first read (idempotent).

### Changed

- Edge **flip** (v0.29.2) now re-assigns `relation` from the new source
  so a flipped edge never keeps a stale semantic.

### Notes

- **No behaviour change yet** — this lands the field + assigner +
  migration only. Phase 2b wires the viewer to read it; Phase 2c the
  server. Decided via plot-design-red-team (stored over derived, A8/A4).

## [0.29.3] — 2026-05-31

### Changed — node shape encodes producer-vs-reference

- 원본/master kinds (`mission`, `core_value`, `identity`, `actor`) now
  render as a **rounded rectangle** (soft corners); symbol-reference
  kinds (`*_ref`) render as a **circle** (D-2026-05-31-B). The shape
  tells the original apart from the symbol pointer that stands in for
  it. Masters keep their kind corner-tag. `decision` stays a diamond;
  the `project` anchor keeps its user-toggled shape (default circle).
- **Supersedes** the v0.27.11 (D-2026-05-28-D) "all Symbol kinds always
  render as circles" rule, per user direction. Extracted the kind→shape
  policy into a pure, unit-tested module
  `viewer/src/canvases/sketch/nodeShape.ts`.

## [0.29.2] — 2026-05-31

### Added — edge "Flip direction" context-menu action

- Right-click an edge → **"Flip direction (swap source ↔ target)"**
  swaps the edge's `source`/`target` so the arrowhead points the other
  way (D-2026-05-31-A). Resolves the open "Direction switch UI" thread,
  and gives the user a manual tool to re-orient an edge toward the
  anchor on the Retention canvases. Available on every canvas;
  `directed` is preserved; Cmd+Z undoes it.

### Fixed — handles are nulled on flip (not swapped)

- BaseNode handles are typed by side (`t`/`l` target-only, `r`/`b`
  source-only), so a naive `sourceHandle ↔ targetHandle` swap fed a
  target-only handle into the source slot and React Flow dropped the
  edge (*"Couldn't create edge for source handle id: l"*, caught in
  live verification). Flip now nulls both handles and lets RF re-route
  through each node's default valid handle.

## [0.29.1] — 2026-05-30

### Fixed — canvas tabs showed raw i18n keys ("변수명")

- v0.28.3 added a **second** top-level `"canvas"` block to the locale
  files (for the direction-switch buttons) without noticing one
  already existed. JSON keeps only the **last** duplicate key, so the
  new block silently wiped `canvas.tabs.{foundation,actors,services}`
  — i18next then rendered the raw key, which showed on the canvas tabs
  as a variable-name-looking string. Merged the two blocks; tabs read
  Foundation / Actors / Services again (D-2026-05-30-J). Honest note:
  a regression introduced in v0.28.3.

### Added — duplicate-key guard

- `i18n-keys-parity.test.ts` now reads the **raw** locale text and
  fails on any duplicate top-level key. The existing parity test
  couldn't catch this — it imports the JSON, which the engine has
  already de-duplicated (both locales shared the same dup, so parity
  held). Green: viewer suite.

## [0.29.0] — 2026-05-30

Sub-flow grouping — the last deferred ServiceDetail 고도화 item. A new
`group` kind (the 17th) chunks a busy flow and collapses it.
[D-2026-05-30-I](./docs/DECISIONS.md).

### Added — `group` kind + collapse

- **`group`** container node. Multi-select ≥ 2 nodes → right-click →
  **"Group selected (N)"** wraps them in a group placed above the
  selection. Right-click a group → **"Ungroup"** removes it (members
  stay). Membership is the SSOT on the group (`member_ids`) — `step` /
  `decision` carry no group field, so it can't drift.
- **Collapse**: the group reuses the fold (▾/▸) chrome. Collapsed →
  its members are hidden and the group shows a member-count badge;
  expanding restores them. E.g. collapse the three OAuth branches into
  one "OAuth path" node.
- MVP is collapse; RF `parentNode` (drag-in visual containment) is
  deferred. MECE with `category` (Services-canvas thematic grouping) —
  `group` is a ServiceDetail flow chunk.

### Files (entity-template + membership)

- `viewer/src/domain/Group.ts` (class, `member_ids` + `body`); union /
  barrel / factory / `types.ts::NodeKind` (16 → 17).
- `nodes/group/index.tsx` + registry; `inspectors/group/index.tsx` +
  registry.
- `viewer/src/canvases/sketch/groupCollapse.ts` (pure: hidden member
  ids) + `groupActions.ts` (pure: group / ungroup); `useNodesMemo`
  hides collapsed members + folds the group on `member_ids`;
  `useContextMenus` adds the Group / Ungroup items (threaded
  `selectedNodeIds`).
- `mashbill/models.py`: `GroupNode` + `NodeKind` +
  `_COMPOSITION_KINDS` + both unions + `service_detail` allowed-kinds.
- i18n: `kind.group` + `inspector.group.memberCount` in en + ko.

### Tests

- `group-collapse.test.ts` + `group-actions.test.ts` (new, pure
  helpers, Red→Green) + entity-roundtrip / structural-guards (16 → 17)
  / nodes-registry / schema-parity. Green: viewer 630, server 438,
  mypy clean.

### Scope (the "덕지덕지" guarantee)

The only structural additions are the isolated `group` kind + two
additive, pure helpers wired into `useNodesMemo` /  `useContextMenus`.
**No new field on existing kinds** (membership lives on the group);
no LOC-ceiling bumps.

### Browser verification (Playwright, Login demo doc)

- A `group` ("Email path") renders with a fold button; collapsing it
  hides exactly its members (`n_lg_em_email` + `n_lg_em_pwd`) while the
  non-member magic-path `이메일 입력` stays; the group shows `▸ … 2`.
  0 console errors.

## [0.28.5] — 2026-05-30

ServiceDetail stencil regrouped by essence layer — the tool now reads
as the 2-layer model the whole session built toward.
[D-2026-05-30-H](./docs/DECISIONS.md).

### Changed — stencil layer groups

- The ServiceDetail stencil is split into two labelled groups:
  - **① Flow (Execution)** — Actors → Interactions (`step`) + Decision
    → Values. The concrete flow the user designs (Actors moved to the
    top as the tier-1 subject).
  - **② Essence injection (Retention)** — Mission / Core Value /
    Identity refs. The essence injected onto the flow.
  Reading top-to-bottom = "build the flow, then inject the essence."
  This makes VISION's 3-phase cycle legible in the tool at the
  Service-Detail altitude (Execution / Retention; Discovery is
  upstream in Foundation).
- New `LayerHeader` component in `SketchStencil`; i18n
  `stencil.layer.{flow,flowHint,essence,essenceHint}` in en + ko.

### Scope

Render-level only — section reorder + a header component + i18n. No
god-component flags, no LOC-ceiling bumps, no change to drop rules or
kinds (the session's "keep it clean, not 덕지덕지" guarantee).

### Browser verification (Playwright, Login demo doc)

- The modal stencil shows **① Flow (Execution)** (Actors → Interactions
  → Values) above **② Essence injection (Retention)** (Mission / Core
  Value / Identity). 0 console errors.

## [0.28.4] — 2026-05-30

Layout anchor priority — injection nodes are an overlay, not part of
the flow rank. The 2-layer essence model (concrete flow + essence
injection) made concrete at the layout level. [D-2026-05-30-G](./docs/DECISIONS.md).

### Fixed — injection nodes anchored by their handle, not ranked

- In `actorAnchoredLayout`, a foundation-injection edge (source =
  `mission_ref` / `value_ref` / `identity_ref`) is now **excluded from
  the dagre step rank**; its source node is anchored beside its target
  on the side the edge's `targetHandle` dictates (`t` → above,
  `b` → below, `l` → left, `r` → right; ≈ 160 px). Before, the
  injection node was swept into the LR rank — so 유머 (Humor) drawn
  into the entry's top landed to the *left* of the entry instead of
  *above* it (user: *"유머 정렬이 잘 안되죠? … 위쪽에 연결이 있는데
  그걸 기준으로 해야죠?"*).
- Realises the **layout anchor priority** (user: *"사람, 액터가 1등이고
  그다음은 스텝 디시전 등이 우선순위"*): ① actor (preserved) →
  ② step / decision (ranked) → ③ injection overlay (anchored last,
  never displaces ① or ②).

### Changed

- New `viewer/src/flow/foundationRefKinds.ts` — SSOT for the three
  foundation ref kinds, now shared by `edgeTransform` (injection
  styling) and `actorAnchoredLayout` (injection anchoring) so they
  never drift on what counts as an injection.

### Tests

- `viewer/tests/actor-anchored-layout.test.ts` — new case: an
  injection node is anchored above its target by `targetHandle="t"`,
  centred on the target column, while the step sequence is unaffected.
  Red→Green. Full suite green: viewer 617.

### Browser verification (Playwright, Login demo doc)

- After `⊞`, 유머 lands centred above the entry (cx 690 ≈ entry cx 689;
  bottom 572 ≤ entry top 625) — its top-connection honoured. 0 console
  errors.

## [0.28.3] — 2026-05-30

Auto-layout direction-switch buttons — the last open item from the
2026-05-28 ServiceDetail 고도화 queue. [D-2026-05-30-F](./docs/DECISIONS.md).

### Added — LR / TB direction buttons

- ServiceDetail's React Flow `<Controls>` gain two buttons next to
  `⊞`: **↔ (LR)** and **↕ (TB)**. Clicking one sets the subject
  edge's handle for that direction and re-runs `actorAnchoredLayout`
  along it, in one undoable `onDocChange`. Before, the only way to
  change LR↔TB was to manually redraw the subject edge with a
  different handle — undiscoverable.
- **Direction stays the SSOT in the subject-edge handle** (no new
  field) — a later `⊞` re-uses the chosen direction. The same
  `detectSubjectEdgeId` identifies the subject edge for both the
  layout and the buttons (one source of truth for "which edge").

### Changed

- `actorAnchoredLayout.ts` exports `detectSubjectEdgeId` +
  `setSubjectDirection`; `detectAnchor` now shares `detectAnchorActor`.
- `useAutoLayout` returns `{ trigger, layoutInDirection }` (was a bare
  callback).
- **New `viewer/src/canvases/sketch/LayoutControls.tsx`** holds the ⊞
  + LR/TB button JSX + i18n — extracted so the direction-switch wiring
  doesn't grow the `SketchCanvas` god component (the residual growth
  there is plumbing-only; ceiling 480 → 490 per D-2026-05-30-F).
- i18n: `canvas.autoLayout` / `canvas.layoutLR` / `canvas.layoutTB`
  in en + ko (the `⊞` aria-label is now translated too).

### Tests

- `viewer/tests/subject-direction.test.ts` (new) — `detectSubjectEdgeId`
  + `setSubjectDirection` (LR r→l, TB b→t, non-subject edges untouched,
  no-subject-edge no-op). Red→Green. Full suite green: viewer 616.

### Browser verification (Playwright, Login demo doc)

- The LR / TB buttons appear on ServiceDetail only (not the background
  canvas). Clicking ↕ stacks the step graph vertically (entry → 방식
  선택 top-to-bottom); clicking ↔ returns it to horizontal. Clean
  round-trip; 0 console errors.

## [0.28.2] — 2026-05-30

Negative-case (failure) visual distinction — the flow can now model
failure paths, not just the happy path. [D-2026-05-30-E](./docs/DECISIONS.md).

### Added — `step.polarity`

- New `step` field `polarity` (`positive` / `negative` / `neutral`,
  default `neutral`). A `negative` result step renders a red tint
  (`#fee2e2`), a `positive` step a green tint (`#dcfce7`); `neutral`
  keeps the user's own colour. A `decision` branches to result steps;
  marking the failure result `negative` makes success vs failure read
  at a glance. The failure *reason* is the step's label / `outcome`
  (no reason = 단순 실패; with = 이유 있는 실패).
- **Opt-in, so PHILOSOPHY P10 holds:** default `neutral` overrides
  nothing; the tint only applies once the user sets polarity.
  Precedent: `service.target_side` tints a service node the same way.
- The failure mark lives on the **result node**, not the edge — a
  failure is a property of where the flow lands. `decision` does not
  carry polarity (decisions are neutral forks).

### Changed

- `viewer/src/canvases/sketch/polarityTint.ts` (new pure helper);
  `useNodesMemo` applies it to `step` nodes (beside the orphan /
  `target_side` tints). `StepInspector` gains a polarity selector.
- `Step` domain class + `mashbill/models.py::StepNode` gain `polarity`.
- i18n: `inspector.field.polarity` + `fieldHint.polarity` +
  `inspector.polarity.{neutral,positive,negative}` in en + ko.

### Tests

- `viewer/tests/polarity-tint.test.ts` (new) — tint per polarity +
  Step parse default/round-trip. Red→Green before source. Green:
  viewer 607, server 438, schema-parity 18, mypy clean.

### Browser verification (Playwright, Login demo doc)

- A `negative` result step renders red (`rgb(254, 226, 226)`); 0
  console errors. (Verification node removed from the demo doc after.)

## [0.28.1] — 2026-05-30

Foundation-injection edges — the other half of the "ServiceDetail =
flowchart of the service with foundation injected onto it" vision
(pairs with v0.28.0's `decision` kind). [D-2026-05-30-D](./docs/DECISIONS.md).

### Added — injection edge styling

- An edge whose **source** is a foundation ref (`mission_ref` /
  `value_ref` / `identity_ref`) renders as an **injection** edge:
  animated (marching dashes flowing source → target) + violet stroke
  (`#8b5cf6`) + `4 4` dash. Expresses "this mission / core value /
  tone&manner *fires here*" at a concrete flow point — e.g. 유머
  (Humor) → 로그인 페이지 진입.
- **Derived from the source node kind** (like the v0.27.19 branch
  badge is derived from the edge count) — no new edge kind, no stored
  flag, no auto-emit. The user draws the edge (PHILOSOPHY P10); Novel
  only styles it. `actor_ref` is excluded (it is the sequence-anchor
  subject edge, not an injection).

### Changed

- `edgeTransform` gains an optional `nodeKindById` lookup;
  `useEdgesMemo` builds it from `doc.nodes` (memoised on the node set).

### Tests

- `viewer/tests/edge-transform.test.ts` (new) — injection for each
  foundation ref source, no injection for step→step or actor_ref
  source. Red→Green before source. Full suite green: viewer 598.

### Browser verification (Playwright, Login demo doc)

- The user's existing `유머 (Humor) → 로그인 페이지 진입` edge now
  renders animated violet dashed (`rgb(139, 92, 246)`); 0 console
  errors.

## [0.28.0] — 2026-05-30

New domain kind: **`decision`** — a flowchart decision diamond for the
ServiceDetail flow. The 16th kind, added via the full
`plot-domain-design` → `plot-entity-template` walk
([D-2026-05-30-C](./docs/DECISIONS.md)).

### Added — `decision` kind

- **A branch point as its own node** (rendered as a diamond), dropped
  from the ServiceDetail stencil's Interactions section beside `step`.
  One node covers both a *user choice* (방식 선택) and a *system
  judgment* (검증 성공/실패). Branches are user-drawn labelled edges;
  typed-failure results are ordinary result `step`s; validation
  conditions are ordinary `rule` nodes — no extra kinds.
- **Why a new kind:** promoting decision off `step` keeps `step` = a
  *user action* (SPEC §"Service composition model"). A system judgment
  that branches the flow cannot live in `step.outcome` text — it needs
  a node. This partially supersedes D-2026-05-28-J's "system work is
  only outcome text" stance: branching system *judgments* are now
  first-class `decision` nodes; non-branching side-effects stay in
  `step.outcome`.
- Fields: `BaseFields` + `body`. No `order` / `outcome` (a decision
  has many labelled outcomes — the edges — not one). Diamond shape is
  forced at the renderer (`BaseNode.effectiveShape`), the same pattern
  Symbol kinds use to force a circle (D-2026-05-28-D).

### Files (the entity-template walk)

- `viewer/src/domain/Decision.ts` (entity class + `fromJson` boundary
  + `registerKindParser`); union `SketchNode.ts`, barrel `index.ts`,
  factory `createBlankNode.ts`, `types.ts::NodeKind` (15 → 16).
- `viewer/src/canvases/nodes/decision/index.tsx` (renderer),
  `nodes/registry.ts`; `inspectors/decision/index.tsx`,
  `inspectors/registry.ts`.
- `BaseNode.effectiveShape` forces diamond for `decision`.
- `SketchStencil.tsx` Decision composition preset + free-form drop
  rule; `SketchIcons.ts` adds `git-fork`.
- `mashbill/models.py`: `DecisionNode` Pydantic model, `NodeKind`,
  `_COMPOSITION_KINDS`, both discriminated unions, `service_detail`
  allowed-kinds set.
- i18n: `kind.decision`, `inspector.decision.branchHint` in en + ko.

### Tests

- `entity-roundtrip.test.tsx`, `structural-guards.test.tsx`
  (`KIND_DIRS` + registry-count 15 → 16), `nodes/registry.test.tsx`,
  server `test_schema_parity.py` all extended / auto-cover `decision`.
  Full suites green: viewer 593, server 438, schema-parity 18,
  pre-commit-gate 11.

### Browser verification (Playwright, Login demo doc)

- Stencil Interactions section shows **Interaction + Decision** tools.
- A `decision` node renders as an amber diamond
  (`clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)`); 0
  console errors. (Verification node removed from the demo doc after.)

## [0.27.19] — 2026-05-30

ServiceDetail step-authoring affordances — the first two items from
the `ServiceDetail 캔버스 고도화` queue. The step graph now reads
naturally in-canvas: each step shows what the system does and where
the flow forks, without opening the Inspector.

### Added — Step `outcome` on canvas (D-2026-05-30-A)

- **`step.outcome` renders + edits in place.** The system-side end
  state shows as a muted `↳ …` subtitle under the step label and is
  inline-editable (multiline `EditableText`; Cmd/Ctrl+Enter commits,
  Esc cancels). Empty steps show a `(outcome — click to add)`
  placeholder. Was Inspector-only before. Implements SPEC §"step =
  user interaction" (system work lives in `step.outcome`) at the
  canvas layer.
- New `node.step.*` i18n keys in `en.json` + `ko.json`
  (`outcomePlaceholder`, `branchLabel`, `branchAria`).

### Added — Branch badge on decision steps (D-2026-05-30-B)

- **A step with ≥ 2 outgoing directed edges renders an amber
  `⑂ branch` badge.** Derived from the edge graph (no stored flag);
  the badge leaves the user's chosen shape and colour untouched.
  Makes branch points visible — previously identical to a linear
  step.

### Changed

- `BaseNodeData` gains `outcome` / `onOutcomeChange` / `branchCount`
  (read only by `StepNode`). `useNodesMemo` wires them for `step`
  kind only and counts outgoing directed edges once.
- `BaseNode.tsx` LOC ceiling 260 → 270 (structural-guards note
  updated; the new fields are the step-authoring data responsibility).

### Tests

- `viewer/tests/nodes/step.test.tsx` (new) — outcome renders, inline
  edit commits via `onOutcomeChange`, branch badge present at
  count ≥ 2 / absent at < 2. Red→Green ritual completed before the
  source landed.

### Browser verification (Playwright, Login demo doc)

- Decision step `방식 선택` shows `⑂ branch` + outcome
  `사용자가 email / Google / Magic link 중 하나 선택`.
- `Submit` shows `↳ 시스템이 자격증명 검증`; empty steps show the
  placeholder. 0 console errors.

## [0.27.18] — 2026-05-28

### Fixed (partial)

- **Background Services canvas no longer fires a `height` prop
  update on every modal action**
  ([D-2026-05-28-L](./docs/DECISIONS.md#d-2026-05-28-l--memoise-apptsx-project-anchor--name--sketchcanvas-to-dampen-background-canvas-prop-cascade-v02718)).
  User report: *"서비스 디테일 캔버스에서 뭔가 조작하면 뒤에
  화면이 반응을 하네요?"*. chrome-devtools MCP fiber probe on the
  user's Chrome confirmed `inert` was applied correctly (no
  interactive leak); the symptom was a stale-prop-identity
  re-render cascade. App.tsx computed `projectAnchor` inline
  on every render via `resolveProjectAnchor(summaries.find(…),
  activeTab)`, producing a fresh object reference each time.

### Changed

- `App.tsx` memoises `activeSummary`, `activeProjectAnchor`,
  `activeProjectName`.
- `canvases/SketchCanvas.tsx` wraps with `React.memo`.
- LOC ceilings raised in `viewer/tests/structural-guards.test.tsx`:
  `App.tsx` 485 → 495, `canvases/SketchCanvas.tsx` 470 → 480.

### Verification (chrome-devtools MCP, modal `onNodesChange` burst)

| Metric | Pre-fix | Post-fix |
|---|---:|---:|
| Services-store update events | 6 | 5 |
| `height` event | 1 | **0** |
| RF callbacks (`onConnect` / `onNodesChange` / `onNodesDelete` / `onEdgesDelete`) | 4 | 4 |
| `nodeInternals` Map identity flip | 1 | 1 |

### Honest limitation — partial fix

The 4 RF callback identity events + the trailing `nodeInternals`
flip still cascade. Likely culprit: SketchCanvasInner's RF
callbacks have stale identity. Audit + fix filed in
`docs/NEXT_SESSION.md` as the immediate next-session task; the
user-visible symptom should be quieter but is not yet fully
eliminated.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 588 / 588 pass.

## [0.27.17] — 2026-05-28

### Changed

- **`docs/NEXT_SESSION.md` gains a top-priority "Service composition
  model — v0.27.16 follow-ups" entry.** Captures the 2026-05-28
  ship state (D-2026-05-28-J SPEC pin + D-2026-05-28-K invariant +
  actor-anchored layout) and lists the open threads in priority
  order so a fresh Claude session can pick the next move without
  rebuilding context.

### Open in the queue

1. Admin actor_ref silent drop bug (user-visible 422 gone, data
   drop still open).
2. Auto-seed update — `sync_details_with_overview` still seeds
   two actor_refs; consider seeding one user-side actor only.
3. `IDENTITY.md` cleanup — still mentions the "≥ 2 baseline"
   that v0.27.16 retired.
4. D-2026-05-28-E (stencil per-item descriptions) — waits on
   user copy.
5. Bigger design questions left open mid-session — Actor
   계층 명시화, direction switch UI, multi-actor services,
   service 외 종류.

### Verification

- No code change. Docs-only ship.

## [0.27.16] — 2026-05-28

The implementation half of D-2026-05-28-J — ServiceDetail layout
behaves the way the user described, and the server invariant
stops blocking single-actor docs.

### Added — Actor-anchored layout

- **`viewer/src/flow/actorAnchoredLayout.ts`**
  ([D-2026-05-28-J](./docs/DECISIONS.md#d-2026-05-28-j--service-composition-model-one-purpose-user-interaction-steps-branchjoin-on-shared-outcome-v02715)).
  Preserves the user-side `actor_ref`'s `(x, y)`, infers the
  spatial direction from the subject edge's `sourceHandle`
  (`r` → LR, `l` → RL, `b` → TB, `t` → BT), lays the step graph
  out with dagre using that `rankdir`, then translates the step
  graph so the entry sits one rank (~220 px) away from the
  actor in the chosen direction. Orphan nodes keep their
  positions.
- **`useAutoLayout` priority swap.** When a doc has a user-side
  `actor_ref` + subject edge, `actorAnchoredLayout` runs *before*
  the mindmap BFS. (For ServiceDetail the mindmap BFS picks the
  hidden root-service as anchor and packs every other node —
  *including the user actor* — into the isolated-nodes grid, which
  is exactly the bug the user flagged: *"이렇게 정렬이 되면
  사람이 알아보겠어요???"*.)
- **`viewer/tests/actor-anchored-layout.test.ts`** — 6 regression
  cases (LR preservation, single-step LR alignment, TB direction,
  branch + join graph, orphan preservation, no-actor early
  return). Red→Green ritual completed before the source module
  landed.
- **`SPEC.md` §Auto-layout §"Actor-anchored layout (v0.27.16,
  D-2026-05-28-J)"** documents the priority, the direction
  inference, the orphan rule, and the static-test pointer.

### Changed — Invariant loosened

- **ServiceDetail `actor_ref` minimum drops from ≥ 2 to ≥ 1**
  ([D-2026-05-28-K](./docs/DECISIONS.md#d-2026-05-28-k--servicedetail-actor_ref-invariant-loosened-from--2-to--1-v02716)).
  Per D-2026-05-28-J the operator side of a service is the
  service itself; the canvas's subject is a single user-side
  `actor_ref`. The pre-v0.27.16 "≥ 2" rule forced an `Admin`
  placeholder that the user 2026-05-28 immediately flagged as
  nonsensical (*"어드민이 서버 검증을 하지는 않죠"*). Zero
  actor_refs is still rejected — every step needs a subject.
- `tests/test_canvas_doc.py` gains three regressions
  (zero rejected / one-user OK / one-operator OK).

### Browser verification (user's real Chrome)

After the priority swap:
- Bana (user actor) `(x, y)` preserved across ⊞ click.
- entry sits 195 px right of Bana; decision right of entry;
  result right of every branch terminal — Login graph reads
  left-to-right as the user authored it.
- Each branch (email / Google / Magic) stacks vertically as
  expected.

### Honest limitations / follow-ups

- **Sync seed still creates 2 actor_refs** (`{sid}-operator-ref`,
  `{sid}-user-ref`). The seed is the auto-fill for *new* service
  details; users can delete the operator-side one if they don't
  need it. Changing the seed itself is filed for a UX follow-up.
- **`IDENTITY.md` still mentions "≥ 2 baseline"** — SPEC.md
  §"Service composition model" (D-2026-05-28-J) is the new SSOT;
  `IDENTITY.md` needs a follow-up edit to point there.
- **Frontend Admin actor_ref drop bug.** During the v0.27.15
  ship a 422 toast surfaced because the PUT body had 1 actor
  while backend doc had 2 (Admin silently dropped between
  reload and PUT). v0.27.16's invariant loosening makes the
  422 disappear at the user-visible layer, but the drop bug
  itself is still open. Filed for the next session.
- **D-2026-05-28-E** (stencil per-item descriptions) still
  waits on user copy.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 588 / 588 pass.
- `uv run pytest` — 438 / 438 pass (+3 new in test_canvas_doc).
- chrome-devtools MCP on the user's Chrome — ⊞ click on the
  Login user-interaction graph: Bana preserved, step chain
  layered LR, branches stacked, result on the far right.

## [0.27.15] — 2026-05-28

### Added — Service composition model pinned

- **`SPEC.md` §ServiceDetail §"Service composition model"**
  ([D-2026-05-28-J](./docs/DECISIONS.md#d-2026-05-28-j--service-composition-model-one-purpose-user-interaction-steps-branchjoin-on-shared-outcome-v02715)).
  Concluded over a multi-turn 2026-05-28 conversation that walked
  the Login service through four drafts before the user accepted
  v4 with *"그렇지 이거죠"*. Pins:
  - **Service = one purpose** (the outcome the user reaches).
  - **Step = user-side action**; system work belongs in
    `step.outcome`, not as a separate node.
  - **Sequence** = directed `step → step` edges (labels are user
    copy, not new edge kinds).
  - **Branch** = decision step + multiple outgoing.
  - **Join** = multiple incoming **when the outcome is the same**.
    Different outcomes → different terminal steps (or services).
  - **Subject** = single `actor_ref → entry` edge. Subject
    inherits down the sequence; no per-step subject edge.
  - **Actors are always humans.** No `System` / `Server` master
    actor. System behaviour lives in `step.outcome`.
  - **Spatial direction** = LR or TB, user's choice. Auto-layout
    must preserve the user-established direction.

### Honest follow-ups (filed for v0.27.16)

- **Auto-layout actor anchor.** v0.27.12 `handleAwareLayout`
  (dagre LR fallback) sweeps the actor along with every other
  node — Bana drifts to the right and the canvas becomes
  unreadable. The replacement algorithm — *preserve the actor
  anchor + lay the step graph out from there along the
  user-established direction (LR / TB)* — is filed.
- **ServiceDetail invariant `≥ 2 actor_ref (operator + user)`**
  conflicts with D-2026-05-28-J (actors are humans, operator side
  is the service itself). A single user-side actor should be
  enough for many services.
- **PUT validation toast** ("1 validation error for CanvasDoc")
  surfaces after auto-layout — root cause to trace.
- **Stencil per-item descriptions (D-2026-05-28-E)** still waits
  on user copy.

### Verification

- No code change in this ship. SPEC + DECISIONS only.

## [0.27.14] — 2026-05-28

### Added

- **Archive guard for service details with user-authored content**
  ([D-2026-05-28-I](./docs/DECISIONS.md#d-2026-05-28-i--sync-archive-guard-for-user-authored-service-details-v02714)).
  `sync_details_with_overview` now refuses to silently archive a
  detail folder whose `detail.json` contains:
  - any node outside the default seed set
    (`{sid, {sid}-operator-ref, {sid}-user-ref}`), OR
  - any edge.

  Protected details land on the new `skipped_archive` field of the
  sync response (`{"created": [...], "archived": [...],
  "skipped_archive": [...]}`). The PUT canvas endpoint + the MCP
  `write_canvas` tool surface the same field. Frontend
  `useCanvasPersist` raises a toast + `console.warn` so the user
  immediately learns which details survived a drop in the overview.

### Fixed

- Closes the regression that lost `n_mpmrphpa_zs8v/detail.json`
  during the 2026-05-27 chrome-devtools session.

### Changed

- `viewer/src/api.ts::PutCanvasResponse.sync` types
  `skipped_archive?: string[]`.

### Honest limitations

- Guard fires only on the automated reconciliation path. A *manual*
  deletion of `services/{sid}/` still succeeds.
- "User content" is structural-only (extra nodes / any edges).
  Editing the *body markdown* of a seeded node without adding new
  structure is not caught yet; follow-up filed.
- The skipped-archive toast reuses the error channel for a *warning*;
  splitting errors and warnings into separate UI lanes is a UX
  follow-up.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 582 / 582 pass.
- `uv run pytest` — 436 / 436 pass (3 new `test_sync.py` cases:
  protected-by-extra-node, protected-by-edge, still-archives-empty).
- Red → Green ritual completed on the new tests before adding the
  guard.

## [0.27.13] — 2026-05-28

### Fixed

- **`GET .../canvases/service_detail/nodes/.../published` no longer
  returns 500 when `service_id` is missing**
  ([D-2026-05-28-H](./docs/DECISIONS.md#d-2026-05-28-h--500--400-on-published-endpoint-when-service_id-is-missing--inspector-now-threads-it-through-v02713)).
  Defence-in-depth fix:
  - **Backend:** `node_published_list_endpoint` catches the
    `ValueError("service_detail requires service_id")` from
    `read_canvas` and returns **400** with the exception
    message instead of an uncaught 500.
  - **Frontend:** `BaseInspectorProps` and `KindInspectorProps`
    gain `serviceId?: string`; `SketchInspectorBindings` passes
    `doc.service_ref ?? undefined` (gate-compatible alternative
    to `canvas_kind` branching — that pattern is blocked by the
    v0.15 Phase 3.4 pre-commit gate); `BaseInspector` threads
    `serviceId` into `PublishedVersionsSection`, which already
    accepted it.

### Honest scope note

- Demo nodes (id-prefix `demo_*`) injected by `ServiceDetailCanvas`
  for first-open guidance never have a published-versions folder
  on disk. After this fix the endpoint correctly returns
  `{ versions: [] }` (200) instead of the 500 the user saw — but
  a real publish for those demo ids is impossible. Suppressing the
  Inspector's published-versions section entirely for demo nodes
  is a separate UX decision filed for a follow-up.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 582 / 582 pass.
- `uv run pytest` — 433 / 433 pass.

## [0.27.12] — 2026-05-28

### Fixed

- **Auto-layout `⊞` now produces a handle-aware layered arrangement on
  ServiceDetail** (and on any other canvas where the BFS mindmap yields
  zero positions)
  ([D-2026-05-28-G](./docs/DECISIONS.md#d-2026-05-28-g--handle-aware-dagre-fallback-for--when-the-mindmap-bfs-has-no-entry-v02712)).
  User report 2026-05-28: *"정렬은 연결관계에 따라서 오른쪽에
  붙어있으면 오른쪽으로 정렬해야하는데 오른쪽에 붙어있는걸 왼쪽에
  정렬하고 이러니까 문제죠."* Root cause: v0.27.11's D-2026-05-28-B
  hid the root-service node on ServiceDetail; that node was the
  mindmap BFS's only entry point, and the user-authored ServiceDetail
  graph (actor / interaction / value peers) never connects to it.
  BFS therefore reached zero nodes and `⊞` was a silent no-op.

### Added

- New pure module `viewer/src/flow/handleAwareLayout.ts` — dagre
  layered layout (`rankdir: "LR"`) that swaps source/target in
  dagre's input whenever the edge's `sourceHandle` faces L or T,
  so the LR output matches "right handle → right side." Orphan
  nodes keep their original positions.
- `useAutoLayout` falls back to `handleAwareLayout(doc)` whenever
  the mindmap BFS yields `positions.size === 0`. Foundation /
  Actors / Services flows are unaffected (their anchors are
  always connected to peers via synthetic / user-drawn edges).
- New regression `viewer/tests/handle-aware-layout.test.ts` — 6
  cases (LR placement, L-source swap, 3-node chain ranking,
  orphan preservation, non-empty-positions invariant, 8-node
  user-shape reconstruction). Red→Green ritual performed
  before adding the module.

### Changed

- `docs/SPEC.md` §Auto-layout gains a new "Handle-aware fallback
  (v0.27.12, D-2026-05-28-G)" subsection documenting the rankdir,
  swap rule, orphan rule, cycle-handling limitation, and the
  static-test pointer.

### Honest limitations

- Dagre is a DAG layout. Cycles are broken by dagre's internal
  feedback-arc-set pass — one edge per cycle is silently
  reversed for layout. Typical ServiceDetail graphs include
  small actor → interaction → actor cycles (Hero → 모임 → Fan +
  Fan → 후원 → Hero); the result is still readable but the
  reversed edge may not align perfectly with its declared handle.
- `rankdir` is global. A user graph mixing LR-style
  (`sourceHandle: "r"`) and TB-style (`sourceHandle: "b"`) handles
  collapses to LR. Per-edge rankdir is not in dagre's model.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 582 / 582 pass (576 + 6 new).
- chrome-devtools bridge dropped mid-session — visual confirmation
  on the user's Chrome is a follow-up.

## [0.27.11] — 2026-05-28

User design pass — four corrections rolled into one ship, after the
user transcribed their original ServiceDetail design intent and
flagged where the running build had drifted from it.

### Changed

- **ServiceDetail canvas hides the root-service node**
  ([D-2026-05-28-B](./docs/DECISIONS.md#d-2026-05-28-b--servicedetail-canvas-hides-root-service-node-v02711)).
  Partial revert of D-2026-05-26-G: per the user's 2026-05-28
  design statement ("로그인 서비스인데 로그인 노드가 들어있는 것도
  이상하고") the canvas content is the actor / interaction / value /
  upper-link peer graph; the service itself is the *implicit*
  subject named by the modal header. `ServiceDetailCanvas` now
  passes `hideRootServiceNode={true}`. `doc.service_ref` stays so
  storage identity is preserved; the tree auto-layout still uses
  the hidden service_ref as the BFS hub.
- **ServiceDetail stencil sections rename to the user's mental model**
  ([D-2026-05-28-C](./docs/DECISIONS.md#d-2026-05-28-c--servicedetail-stencil-relabels-composition-to-interactions--values-v02711)).
  The `service_detail` SketchStencil branch now renders two
  separate sections — "Interactions / 인터랙션" (the `step` preset
  with `labelI18nKey: "kind.interaction"`) and "Values / 가치"
  (the `metric` preset with `labelI18nKey: "kind.value"`) —
  instead of one "Composition / 구성 요소" section. Underlying
  domain kinds stay `step` / `metric` (D-2026-05-26-C YAGNI
  preserved); only the user-facing labels move.
- **Symbol kinds always render as circles**
  ([D-2026-05-28-D](./docs/DECISIONS.md#d-2026-05-28-d--symbol-kinds-always-render-as-circles-v02711)).
  Per D-2026-05-19-D, Symbol = `mission` / `core_value` / `identity`
  / `actor` + their refs (`actor_ref` / `mission_ref` / `value_ref` /
  `identity_ref`). `BaseNode` now computes an `effectiveShape` that
  forces `"circle"` for any Symbol kind regardless of `data.shape`,
  so legacy data (mission saved as `"rounded"` pre-v0.27.11) snaps
  to circle on render without any data migration. STENCIL_PRESETS
  (static + dynamic ref factories) also default to `"circle"` so
  newly-dropped Symbols are circles on storage too. `shouldShowKindTag`
  gains a `kind?` argument; Symbol kinds suppress the corner tag
  because the corner falls outside the circle silhouette.
- **Modal-internal language toggle**
  ([D-2026-05-28-F](./docs/DECISIONS.md#d-2026-05-28-f--modal-internal-language-toggle-v02711)).
  The main sidebar is `inert` (D-2026-05-26-F) while the
  ServiceDetail modal is open, so its EN/KO toggle was
  unreachable. `ServiceDetailStencilPanel` now hosts its own
  `<LanguageToggle/>` at the bottom of the panel.

### Added

- `kind.interaction`, `kind.value`, `stencil.section.interactions`,
  `stencil.section.values`, `stencil.note.interactionsBetweenActors`,
  `stencil.note.valuesExchanged` in both `en.json` and `ko.json`
  (i18n parity preserved).

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 576 / 576 pass.
- chrome-devtools MCP on the user's Chrome — Login modal renders
  18 nodes / 28 edges from the test reconstruction; Symbol nodes
  (Hero / Fan / actor refs / core_value refs / mission ref) all
  render as circles regardless of stored shape; "Interactions" /
  "Values" sections visible in the modal stencil; EN/KO toggle
  visible at the bottom-left of the modal stencil; Login service
  node is no longer drawn on the canvas.

### Honest scope cut

- **(4) per-stencil-item descriptions (D-2026-05-28-E candidate)** —
  deferred. The user flagged "지표/단계 어떻게 사용해야하는지
  모르겠고… 설명을 제대로 해라"; the section-level note
  ("액터 사이의 접점을 끌어 놓으세요" / "인터랙션에서 교환되는
  가치를 끌어 놓으세요") covers the headline, but per-item hover
  tooltips + an in-modal usage hint are a separate UX design
  decision filed for a follow-up ship.

### Honest limitations carried forward

- **Symbol "동그라미" reads as an ellipse when width ≠ height.**
  `effectiveShape="circle"` only sets `borderRadius: 50%`; nodes
  whose stored size is non-square render as ellipses. Newly
  dropped Symbols use square stencil widths (140×140, 160×160,
  120×120), but legacy data carries its old size. Data migration
  to square Symbols is deferred — the visual mostly reads as a
  circle and forcing user data widths is a heavier decision.
- Layout still up to the user (PHILOSOPHY P10). Per the
  unresolved layout question from this session, the spatial
  arrangement of the reconstruction is "edge-crossy" in
  auto-layout; user-driven manual layout remains the canonical
  path.

## [0.27.10] — 2026-05-28

### Fixed

- **ServiceDetail: composition (metric / step) drop on empty space no
  longer errors**
  ([D-2026-05-28-A](./docs/DECISIONS.md#d-2026-05-28-a--servicedetail-composition-drop-is-free-form-v02710)).
  User report: dropping a Composition preset on empty space in the
  ServiceDetail modal canvas raised *"Drop inside a Service container"*
  — directly conflicting with the user's original design intent
  ("ServiceDetail = 관계 + 가치 흐름; 액터 / 인터랙션 / 가치 / 상위연결
  의 자유 그래프, service container 의 자식 구조가 아님") and with
  D-2026-05-26-C (ServiceDetail = user-authored interaction graph).
- Fix: `resolveDropTarget` gained an optional `canvasKind` parameter.
  When `canvasKind === "service_detail"`, composition drops on empty
  space resolve to `{ parentId: null }` (top-level peer); composition
  drops *inside* a service container still nest (backwards-compat).
  Other canvases and the omitted-arg case keep the pre-v0.27.10
  enforcement.

### Added

- New test file `tests/service-detail-composition-drop.test.tsx` —
  6 cases pinning both branches of the new contract (free on empty,
  still-nests inside service) plus Services (service-in-category)
  and Actors (sub-actor) regression coverage.

### Changed

- `docs/SPEC.md` §ServiceDetail §Stencil gains a new
  "Composition drop is free-form" subsection that transcribes the
  user's design model (actor → interaction → actor; interaction →
  value; interaction → core value; core value → mission).
- `useDragAndDrop` now threads `doc.canvas_kind` through to
  `resolveDropTarget`.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 576 / 576 pass (570 + 6 new).
- Red → Green ritual on the new test file confirmed pre-fix
  failure with the expected error message.

## [0.27.9] — 2026-05-27

### Fixed (real root cause — v0.27.7/8 chased a wrong hypothesis)

- **Nodes no longer turn `visibility: hidden` on drag / stencil drop**
  ([D-2026-05-27-D](./docs/DECISIONS.md#d-2026-05-27-d--rf-createnodeinternals-loses-dimensions-without-top-level-width-on-prop-nodes-v0279)).
  User report: dragging a node *or* dropping a new node from the
  stencil → every other node disappears. v0.27.7's useCallback hoist
  did not fix it (mount/remount hypothesis was wrong); chrome-devtools
  MCP measurement of the user's real Chrome — via React fiber direct
  access to RF's zustand store + a `subscribe` probe on
  `nodeInternals` — confirmed: SketchCanvas mount count stays 6,
  `useNodesInitialized` never flips, but `nodeInternals.width /
  height / handleBounds` go to `undefined` for 48/48 entries on every
  `setNodes` call. Source-level confirmation: RF v11's
  `createNodeInternals` (`@reactflow/core/dist/esm/index.js:1463`)
  builds `internals = { ...node, positionAbsolute }` into a brand-new
  `Map` and only carries `handleBounds` forward; width/height come
  ONLY from the prop node's top-level keys. ResizeObserver eventually
  measures and refills nodeInternals, but the next doc change wipes
  it again — under drag/onDocChange burst the measure cycle never
  catches up.

- **Fix:** `useNodesMemo` now emits `width` and `height` as top-level
  keys on every node it pushes (including the synthetic project
  anchor), not only under `style: { width, height }`. RF
  `createNodeInternals` now carries dimensions through every
  `setNodes` call.

- **Verification (fiber-level + invariant pin):**
  - 60-frame fiber-direct `onNodesChange` burst → `nodeInternals`
    `undef.width=0/53`, `visibility:hidden=0/53` (was 48/48
    immediately on the pre-fix code).
  - `structural-guards.test.tsx` Contract 5 (`RF nodeInternals.width
    invariant`) red→green: walks every `out.push({...})` /
    `out.unshift({...})` in `useNodesMemo` and asserts both `width`
    and `height` appear as top-level keys.

### Honest correction

- **v0.27.7 (`D-2026-05-27-B`) and v0.27.8 (`D-2026-05-27-C`) shipped
  a fix and a guard based on a *wrong root-cause hypothesis*** —
  "SketchCanvas remounts under drag, which resets
  `useNodesInitialized` and cancels the fitView fallback." Real
  measurement (this session, chrome-devtools MCP) refutes both
  claims: mount delta = 0 across drag, `useNodesInitialized` flip
  delta = 0. The useCallback hoist + Gate 1.5 (TDD) + Contract 4
  (inline-arrow ban) stay — they are correct best-practice in their
  own right — but they did not fix the visibility:hidden bug. Marked
  as **Superseded by D-2026-05-27-D** in DECISIONS.md.

### Honest limitations / follow-ups (separate from this fix)

- **500 error on `GET .../nodes/demo_inter_publish/published`** — the
  demo nodes ServiceDetailCanvas injects (the "Login" template
  starter graph) have no storage row; the publish-version endpoint
  returns 500. Filed as a follow-up server-side fix (skip / 404 for
  demo IDs).
- **Root service `n_mpmrphpa_zs8v` moved to `_archive/`** during this
  session's chrome-devtools probing. Cause not yet traced (likely
  `D-2026-05-25-A` `sync.archived` triggered when our injected
  `onNodesChange` bursts hit an edge case). Filed as a follow-up
  data-loss investigation.
- **Node-count growth (25 → 48 → 53)** in `plot-test-v013/.plot/banas-imported/services/`
  is the user's own stencil drops during the bug-hunt session, not
  test pollution. No data action needed; user can manually delete.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 570 / 570 pass (569 + new Contract 5).
- chrome-devtools MCP on the user's real Chrome — fiber-direct
  60-frame `onNodesChange` burst → 0/53 hidden (matches the
  pre-fix's 48/48 hidden on every burst).

## [0.27.8] — 2026-05-27

### Added

- **`viewer/tests/structural-guards.test.tsx` Contract 4 —
  "hot-path JSX prop callback stability"**
  ([D-2026-05-27-C](./docs/DECISIONS.md#d-2026-05-27-c--gate-15-tdd--bdd-pinned-to-plotclaudemd--inline-arrow-jsx-prop-guard-for-canvas-slots-v0278)).
  Two `it.each` suites scan App.tsx and assert that no
  `<Canvas>`, `<ServiceDetailCanvas>`, `<FoundationCanvas>`,
  `<ActorsCanvas>`, `<ServicesCanvas>` slot receives an
  inline-arrow callback prop or a no-op `() => {}` literal.
  Failure messages quote the offending capture and link to
  D-2026-05-27-B for the fix recipe.
- **Red → Green verification:** temporarily reverted one line in
  App.tsx (hoist → inline arrow) and confirmed the new guard
  fails with the expected message; restored. 56/56
  structural-guards pass.

### Changed

- **`plot/CLAUDE.md` gains `Gate 1.5 — Test before code (TDD / BDD)`**
  ([D-2026-05-27-C](./docs/DECISIONS.md#d-2026-05-27-c--gate-15-tdd--bdd-pinned-to-plotclaudemd--inline-arrow-jsx-prop-guard-for-canvas-slots-v0278)).
  Pinned between Gate 1 (spec coverage) and Gate 2 (LOC budget).
  Spells out Red → Green → Refactor ordering, four banned shortcuts
  (incl. *"chrome-devtools verification covers it"* and *"the
  behaviour is too dynamic to unit-test"*), and names v0.27.7 as
  the canonical regression the Gate exists to prevent. Static
  guards count as tests.

### Honest limitations

- **No dynamic mount-counter regression yet.** The "fire N
  back-to-back `onDocChange` calls + assert mount counter stays
  at 1" test needs an RF + jsdom harness that is known-flaky in
  this repo. Filed as a follow-up D-entry rather than papered
  over. Static guard + Gate 1.5 already cover the prop-identity
  surface the user flagged.
- **`pre_commit_gate.py` "src/ changed without tests/ changed"
  check not yet enforced.** Reviewer judgement holds the line
  today.

## [0.27.7] — 2026-05-27

### Fixed

- **ServiceDetail modal canvas no longer remounts mid-drag —
  prop-callback identity stabilized**
  ([D-2026-05-27-B](./docs/DECISIONS.md#d-2026-05-27-b--canvas--servicedetailcanvas-prop-callbacks-hoisted-to-usecallback-v0277)).
  User report: dragging any node inside the ServiceDetail modal
  made every node turn `visibility: hidden` (the data was intact,
  the canvas just looked empty). User's structural diagnosis was
  exactly right: *"이건 SW 설계를 잘 못 한기다. 구조 고쳐야지."*
- Root cause: App.tsx passed nine inline-arrow callbacks
  (`onDocChange`, `onPublishNode`, `onUnpublishNode`,
  `onNodeDrill`, `onSelectionConsumed` × main + modal surfaces) to
  the Canvas / ServiceDetailCanvas elements. Each drag event
  produced a new `canvasCache` Map → new `CanvasDoc` reference →
  new closures → SketchCanvas treated its `<ReactFlowProvider>`
  subtree as a remount, which reset `useNodesInitialized` and
  cancelled the 300 ms `fitView` fallback (D-2026-05-26-H) before
  it could un-hide the nodes.
- Fix: hoist all nine callbacks into `useCallback` with their real
  dependencies. SketchCanvas instance now survives drag /
  onDocChange flows; fitView fallback runs to completion.
- chrome-devtools MCP verification on the user's real Chrome:
  ServiceDetail modal mount produces 1 `MOUNT` + 1 `UNMOUNT` +
  1 `MOUNT` (StrictMode dev cycle only); auto-layout click
  produces no extra `MOUNT` lines. 60 fps drag could not be
  triggered from chrome-devtools (RF d3-drag rejects synthetic
  pointer events) — final user-hands-on check pending.

### Changed

- **Two-MCP debug workflow pinned to `plot/CLAUDE.md` Gate 3**
  ([D-2026-05-27-A](./docs/DECISIONS.md#d-2026-05-27-a--two-mcp-debug-workflow-when-playwright-cannot-reproduce-a-user-visible-bug)).
  When the user reports a UI bug that Playwright can't reproduce,
  switch to chrome-devtools MCP (live console + DOM probes against
  the user's real Chrome) rather than guessing or shipping CSS
  bandaids. Five high-value DIAG plant points + symptom-decoder
  table documented in CLAUDE.md.
- `App.tsx` LOC ceiling raised 430 → 485 to absorb the nine
  hoisted callbacks. Follow-up filed in the ceiling note to move
  callbacks into a `useAppCallbacks` hook and reclaim the LOC.
- `docs/ARCHITECTURE.md` Contracts table gained one row:
  *"Prop callbacks passed to a Canvas / ServiceDetailCanvas element
  must have stable identity across drag / onDocChange flows."*

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` — 563 / 563 pass.
- chrome-devtools MCP — ServiceDetail modal mount + auto-layout
  onDocChange both produce only the StrictMode base mount cycle
  (no extra remount).

## [0.27.6] — 2026-05-27

### Fixed

- **Auto-layout `⊞` now auto-fitView so the result is always visible**
  ([D-2026-05-26-J](./docs/DECISIONS.md#d-2026-05-26-j--auto-layout-auto-fitview-after-onDocChange-so-the-result-is-always-visible-v0276)).
  User report: *"정렬 하면 모든 노드 싹다 사라짐"*. The layout
  algorithm shifts nodes to new (x, y) values around the anchor,
  but the user's viewport (whatever zoom / pan they had) stays put
  — so the newly laid-out graph commonly lands off-screen.
  Pre-fix the user experienced this as "nodes vanish" since the
  fit-view button click did nothing (RF still had the post-layout
  store state in sync with their old viewport).
- Fix: `useAutoLayout` + `useRadialLayout` both now wrap a
  `setTimeout(() => rf.fitView({ padding: 0.2, duration: 250 }), 0)`
  after `onDocChange`. The setTimeout(0) lets the React commit +
  RF measure pass complete before fitView runs. Same gate on both
  algorithms so the behaviour is uniform across every canvas that
  opts into auto-layout. Verified browser: zoom out to `scale(0.5)`,
  click `⊞`, viewport returns to `scale(0.804843)` (initial fit
  position).

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser DOM probe: viewport transform changes from
  `scale(0.5)` → `scale(0.804843)` after auto-layout click. Pre-fix
  it stayed at `scale(0.5)` with nodes off-screen.

## [0.27.5] — 2026-05-26

### Fixed

- **Root-service `▾` fold button hid every other node on the
  ServiceDetail canvas** ([D-2026-05-26-I](./docs/DECISIONS.md#d-2026-05-26-i--root-service-suppresses-its-fold-button-on-servicedetail-v0275)).
  User report: *"오 서비스 디테일에서 노드 움직이니까 그냥 사라진다.
  모든 노드가 없어져버린다."*
- Diagnosis: with v0.27.3's visible root-service + the seeded demo
  graph where every node descends from the root via directed
  edges, clicking the root's fold button (small `▾` next to the
  label, easy to hit while reaching for the node body) collapsed
  the entire subtree — i.e. emptied the whole canvas. The user
  experienced this as "nodes vanish when I move things" because
  the click target was right next to the drag handle.
- Resolution: `useNodesMemo` suppresses the fold button on any
  node where `kind === "service" && is_root === true`. Other
  containers (`category`, sub-services, `actor` with sub-actors,
  `step` with composition children, …) keep their fold buttons
  — only the root-service (whose entire purpose IS the canvas)
  loses its fold affordance.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser: `[data-id="n_mpkyhvsj_mjzh"] button` count = 0 (was 1
  showing `▾`); all 14 descendant nodes stay visible while the
  user interacts with the root-service node.

## [0.27.4] — 2026-05-26

### Fixed

- **Canvas empty after page load even though nodes exist**
  ([D-2026-05-26-H](./docs/DECISIONS.md#d-2026-05-26-h--fitview-fallback-unsticks-visibilityhidden-when-usenodesinitialized-stalls-v0274)).
  Reloading the page directly onto a URL with `?detail=...` opened
  the ServiceDetail modal, but every node mounted with
  `visibility: hidden` and the canvas looked blank — even though
  DOM probes confirmed 15 nodes were laid out correctly inside the
  visible canvas region. `useNodesInitialized` was getting stuck at
  `false` (modal's initial DOM measurement races RF's internal
  measure pass) so the fitView gate in `SketchCanvas` never fired,
  and RF kept the nodes hidden waiting for a measure signal that
  never came.
- Resolution: 300 ms `setTimeout` fallback. If
  `useNodesInitialized` hasn't flipped by then, fire `fitView`
  anyway — RF honours the measured DOM rects and the canvas
  becomes visible. The cleanup function ensures the timer is
  cancelled if the signal arrives normally first, so well-behaved
  mounts pay no cost.

### Changed

- `structural-guards.test.tsx` SketchCanvas LOC ceiling raised
  450 → 470 to absorb the 300 ms fallback effect + its rationale
  comment.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser: hard-reload onto
  `/?project_path=...&canvas=services&detail=n_mpkyhvsj_mjzh`
  now shows the demo graph immediately (Login + Hero + Fan + 5
  interactions + 4 values + 3 refs + 23 edges, all visible).
  Previously the same URL produced a blank canvas requiring manual
  fit-view click that did nothing.

## [0.27.3] — 2026-05-26

### Changed

- **ServiceDetail's root-service node is now visible at the canvas
  centre** ([D-2026-05-26-G](./docs/DECISIONS.md#d-2026-05-26-g--servicedetail-root-service-is-the-design-subject-not-hidden-v0273)).
  User reframe: *"서비스를 디테일하게 설계하는 캔버스란 말입니다!"*
  ServiceDetail is the canvas where one service is designed in
  detail; the service itself is the *subject* of the canvas —
  analogous to Foundation / Actors' anchor — so it must be visible
  so the user can draw edges into / out of it and so the tree
  auto-layout has a meaningful BFS root.
- Concretely: `ServiceDetailCanvas.tsx` flips
  `hideRootServiceNode={true}` → `false`. v0.15 Phase 3.4's original
  framing (the modal header already names the service, so the canvas
  node is redundant) is rolled back. The modal header carries the
  *navigation breadcrumb*; the canvas node carries the *design
  subject* — two distinct surfaces.
- Knock-on fix for the user-reported "정렬 누르면 다 사라짐"
  symptom: the tree auto-layout now has a real root to spread from,
  and any nodes the user draws connected to that root land in the
  spanning tree (instead of all 14 going to the orphan grid off
  screen). Disconnected nodes still grid-fallback per the existing
  algorithm — unchanged.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser (banas-imported / Login modal): the `⚡ Login` node now
  shows at the canvas centre. After clicking `⊞`, the seeded demo
  graph (Hero / Fan / 5 인터랙션 step / 4 가치 step / refs) fans
  out as a tree from Login, all within the fitView frame.

## [0.27.2] — 2026-05-26

### Fixed

- **Dynamic ref stencil items now show their master's name**
  ([D-2026-05-26-E](./docs/DECISIONS.md#d-2026-05-26-e--dynamic-ref-stencil-items-show-master-name-v0272)).
  Previously every actor / mission / value / identity ref preset
  showed the generic kind label ("Actor (ref)" / "Mission (ref)" /
  "Core value (ref)" / "Identity (ref)") regardless of which master
  it pointed at — `SketchStencil`'s label resolver fell through to
  the `kind.${kind}` i18n key before reaching the preset's
  `labelHint`, which already carried `master.label || master.id`.
  Pre-v0.27.2 the ServiceDetail modal stencil read as "Actor (ref)
  × 7 indistinguishable rows" instead of the real master names.
  User feedback: *"왜 심볼이 제대로 안나오는거죠?"*.
- Resolution: dynamic ref preset factories (`actorRefPresetFor`,
  `missionRefPresetFor`, `valueRefPresetFor`, `identityRefPresetFor`)
  now pass explicit `labelI18nKey: null`; `StencilItem` treats
  `null` as "skip i18n, use labelHint directly". Static presets
  (top-level Actor / Category / etc) continue to use `kind.${kind}`.

### Added

- **ServiceDetail modal traps interaction outside itself**
  ([D-2026-05-26-F](./docs/DECISIONS.md#d-2026-05-26-f--servicedetail-modal-traps-interaction-via-inert-v0272)).
  User feedback: *"서비스 디테일 모달 뜰 때 다른거 동작안되게 해야죠."*.
  While the modal is open the root app `<div>` gets the HTML `inert`
  attribute — no clicks, no focus, no keyboard, no drag fires
  outside the modal. The modal sits as a sibling of the inert root
  so it remains fully interactive.

### Changed

- **`ServiceDetailModal` returns to viewport-level `fixed inset-0`**
  (was `absolute inset-0` per v0.27.0 / D-2026-05-26-B). Inert now
  blocks the main canvas + sidebar instead of relying on physical
  containment, so the v0.27.0 motivation (sidebar must stay
  click-reachable) no longer applies — the modal's self-contained
  stencil column (v0.27.1 / D-2026-05-26-D) already covers
  reachability. Inner panel sizing returns to `h-[92vh] w-[94vw]`.
- **App.tsx** moves the modal mount block from inside the canvas
  container back to a root-level sibling of the main app `<div>`.
  The root `<div>` carries `inert` whenever `modalOpen` is true.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser: open Login modal — left stencil column shows real master
  names (Admin / Bana / Hero / Fan / Bartender / 3rd party / 미용사
  / Mission / 관용 (Tolerance) / 지지 (Support) / 유머 (Humor) /
  공감 (Empathy) / 다양성 (Diversity) / Tone & Manner) instead of
  the generic "Actor (ref)" / "Mission" / "Core value (ref)".
- Probe `document.querySelector('div.flex.h-screen').hasAttribute('inert')`
  returns `true` while modal open, `false` after ESC.
- ESC closes; Services canvas (Banas → Auth → Login) renders intact.

## [0.27.1] — 2026-05-26

### Added

- **ServiceDetail modal is now self-contained**
  ([D-2026-05-26-D](./docs/DECISIONS.md#d-2026-05-26-d--servicedetail-modal-is-self-contained-v0271)).
  New `viewer/src/shell/ServiceDetailStencilPanel.tsx` (42 LOC) —
  a `w-56` aside that wraps `<SketchStencil canvas="service_detail" />`
  with the four `available*` master lists. Mounted inside the modal
  as its left column; the modal body is now a 2-column flex (stencil
  left, canvas right). User direction: *"디테일 서비스 캔버스 컨트롤은
  디테일 서비스 컨트롤 모달 안에서 다 이뤄져야합니다."*
- **`ServiceDetailModal` gains a `stencilSlot: ReactNode` prop**
  so the modal stays composable — App.tsx hands it the new
  StencilPanel, but the modal itself has no opinion about what
  goes in the left column.
- **New top-level `# ServiceDetail` section in `docs/SPEC.md`**
  ([D-2026-05-26-C](./docs/DECISIONS.md#d-2026-05-26-c--servicedetail--user-authored-interaction-graph-v0271)).
  ServiceDetail's spec was previously absent (SPEC.md L4 noted
  "Services / Service-Detail follow in later expansions"). The
  section pins the identity: ServiceDetail is a **user-authored
  interaction graph**, not a constrained "fill-in-the-spec" surface.
  User direction: *"인터렉션 그래프인데 사용자가 만들 수 있어야해요"*.
  No new kinds shipped this round (YAGNI).

### Changed

- **`App.tsx` no longer swaps the main sidebar's stencil**
  ([D-2026-05-26-D](./docs/DECISIONS.md#d-2026-05-26-d--servicedetail-modal-is-self-contained-v0271)).
  `stencilCanvas={activeTab}` always — the previous
  `stencilCanvas={activeTab === "services" && detailServiceId ? "service_detail" : activeTab}`
  split-personality layout is gone. Main Services sidebar shows ONLY
  Services stencil (Category / Service) regardless of modal state.
- **Main sidebar stays visible behind the modal backdrop** when the
  ServiceDetail modal is open. User-confirmed in same session:
  *"그대로 보이는데 모달의 크기가 화면을 다 덮겠죠?"*. The modal's
  `bg-slate-900/40` backdrop visually mutes the main sidebar without
  unmounting it.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser: Services tab — main sidebar shows only Services stencil;
  Login double-click opens modal with full service_detail stencil
  (COMPOSITION / ACTORS / MISSIONS / CORE VALUES / IDENTITY ASPECTS)
  in its own left column; ESC closes — Services canvas (Banas → Auth
  → Login) renders intact (no v0.27.0 "싹다 사라짐" regression).
- LOC: App.tsx 425/430; ServiceDetailModal 92 LOC; new
  ServiceDetailStencilPanel 42 LOC.

## [0.27.0] — 2026-05-26

### Changed

- **Services + ServiceDetail switched from `radial` to `tree` auto-layout**
  ([D-2026-05-26-A](./docs/DECISIONS.md#d-2026-05-26-a--services--servicedetail-switch-from-radial-to-tree-auto-layout-v0270)).
  Radial placement collapsed length-1 spoke chains onto a single
  vertical line — visually "everything stacked north of the anchor"
  — even after the v0.26.3 fan-out fix, because every BFS chain
  inherits its single parent's angle all the way out. User direction
  *"정렬은 액터 캔버스 참고하쇼"*. Both wrappers now use the same
  mindmap-style tree layout Actors / Foundation use: children fan out
  in the direction (T/R/B/L) of the parent-side edge handle, so chains
  follow user-drawn intent instead of fighting it. `useAutoLayout`
  picks the canvas's root-service node as the hub when the canvas has
  no synthetic anchor, mirroring `useRadialLayout`'s `pickHub`.
- **ServiceDetail modal now mounts inside the canvas container, not
  at the root** ([D-2026-05-26-B](./docs/DECISIONS.md#d-2026-05-26-b--servicedetail-modal-coexists-with-the-sidebar-v0270)).
  Previously the modal's `fixed inset-0` covered the entire viewport,
  hiding the left sidebar — and with it the COMPOSITION (metric / step)
  + Actor refs + Mission / Value / Identity ref sections that are the
  *only* way to populate a service-detail canvas. User feedback:
  *"서비스디테일 캔버스에서 뭘 할 수가 없어요. 여기 액터도 있고 해야하는데
  그게 없네요?"*. The modal now `absolute inset-0`'s the canvas region
  only; the sidebar stays visible and usable while the modal is open.
- `useAutoLayout` hub selection extended to fall back to the
  root-service node (`kind === "service" && is_root === true`) when
  `projectAnchor` is null — same shape as `useRadialLayout.pickHub`.
- `viewer/src/App.tsx` modal mount relocated; the `<div>` that wraps
  the active canvas now carries `relative` so `absolute inset-0`
  modal positioning resolves to the canvas region.
- `viewer/tests/auto-layout-isolation.test.tsx` updated: Services /
  ServiceDetail expectations now require `layoutAlgo="tree"` and the
  position-stability assertions exercise the tree algorithm.
- `docs/SPEC.md` §Auto-layout table — Services + ServiceDetail rows
  flipped to `"tree"`; History extended with D-2026-05-26-A/B.

### Verification

- Viewer vitest 563 passed; tsc clean.
- Browser: Services canvas auto-layout now lays out
  anchor → category → service as a left-to-right tree (Actor-canvas
  parity); ServiceDetail modal opens with the sidebar fully visible
  and stencil sections (COMPOSITION / ACTORS / MISSIONS / CORE VALUES)
  draggable onto the service-detail canvas.

## [0.26.3] — 2026-05-25

### Changed

- **Radial auto-layout now fans children around their parent's angle**
  ([D-2026-05-25-D](./docs/DECISIONS.md#d-2026-05-25-d--radial-fan-out-ring-k2-follows-parent-angle-v0263)).
  Prior behaviour: every ring started members at -π/2 (top), so a
  chain like `anchor → category → service` produced both child nodes
  stacked directly above the anchor. New behaviour: ring 1 keeps
  equal-distribution from top (no parent angle to inherit), but ring
  k>=2 groups members by their BFS parent and fans them around the
  parent's own angle. Single child → same angle as parent (chains
  follow one radial line outward); multiple children → evenly spread
  within a fan that narrows with depth (π/(k+1) — π/3 for ring 2,
  π/4 for ring 3, …). User-felt fix for "왜 앵커 위로 다 정렬해
  버리죠?".
- `docs/SPEC.md` §Auto-layout / radial section rewritten to describe
  the two-pass placement (angle assignment then radius).

### Verification

- Viewer vitest 563 passed; tsc clean.
- Server unaffected.

## [0.26.2] — 2026-05-25

### Added

- **`⊞` auto-layout button on `ServicesCanvas`** restored
  ([D-2026-05-25-C](./docs/DECISIONS.md#d-2026-05-25-c--servicescanvas-opts-back-into-radial-auto-layout-v0262-reverts-d-2026-05-24-c)).
  Reverts the same-day-prior D-2026-05-24-C decision to remove it.
  User feedback: *"서비스 메인 캔버스에 정렬기능 빠져있는건 여전하고"*.
  The radial algorithm itself (shipped in v0.25.0) is unchanged;
  ServicesCanvas now passes `layoutAlgo="radial"` again.

### Changed

- `viewer/tests/auto-layout-isolation.test.tsx` — ServicesCanvas test
  flipped from "must NOT opt in" back to "must opt in with radial";
  positions-only test restored.
- `docs/SPEC.md` §Auto-layout table — Services row back to `"radial"`;
  History entry for D-2026-05-25-C added.

## [0.26.1] — 2026-05-25

### Changed

- **Non-Symbol nodes default to rectangle shape** at creation time
  ([D-2026-05-25-B](./docs/DECISIONS.md#d-2026-05-25-b--non-symbol-nodes-default-to-rectangle-shape-v0261)).
  User direction *"캔버스에 앵커하고 심볼 빼고 다 사각형으로 노드를
  만들죠"*. The 11 non-Symbol kinds (`category`, `service`,
  `actor_ref`, `mission_ref`, `value_ref`, `identity_ref`, `metric`,
  `step`, `rule`, `content`) now drop as rectangles from the stencil
  + picker flow. Symbol kinds (`mission` / `core_value` /
  `identity` / `actor` / sub-actor) keep their current shape
  (rounded / circle); the project anchor stays a circle. Stencil-only
  change — Pydantic defaults untouched, existing stored shapes
  preserved (SSOT). 9 stencil presets + 4 picker-driven preset
  helpers + 2 server auto-seed `ActorRefNode` instances flipped.

## [0.26.0] — 2026-05-25  ⚠ BREAKING

### Removed

- **`BaseNodeFields.parent_id` field** ([D-2026-05-25-A](./docs/DECISIONS.md#d-2026-05-25-a--directed-edge-model--parent_id-removed-v0260-breaking)).
  Hierarchy / containment is now expressed via directed edges
  exclusively. Schema-level invariants that were ``parent_id``-based
  (cycle / self-parent / service-must-have-category / category-must-
  be-top-level / composition-kind-must-have-service-parent) have all
  been removed from Pydantic; domain guidance moves to docs.
- ``md_publish.py`` frontmatter ``parent_id`` key (was 1 of 7 — now
  6 keys).

### Added

- **`SketchEdge.directed: bool = True`**. New default for any edge
  created from a stencil drop, drag-to-connect, or nested-add. The
  renderer draws an arrowhead at the target end when directed.
- **Edge context-menu toggle** "Add direction" / "Remove direction" —
  flips ``directed`` on the selected edge.
- **`folder_io._migrate_parent_id_to_directed_edges`** — read-side
  one-shot migration that converts pre-v0.26 ``parent_id`` to a
  directed edge ``parent → child`` (id ``e_migrated_{node_id}``).
  Idempotent. Also backfills ``directed=true`` on any pre-v0.26 edge
  that lacks the field.
- **`useCollapsedTree`** rewritten to derive children / parents from
  directed edges; new ``parentIdsByChild`` output for the inverse
  walk. Ancestor / descendant walks use a visited-set BFS so
  user-introduced cycles in the directed-edge graph terminate
  safely.
- **New helper module `viewer/src/canvases/sketch/hierarchy.ts`**:
  ``parentIdOf`` / ``parentIdsOf`` / ``childIdsOf`` / ``hasParent``
  for consumers that need parent-child queries (Inspector child
  count, App.tsx drill context, useDragAndDrop sibling lookup,
  …).
- **Propagation walk** (`mashbill/propagation.py`) now follows
  incoming directed edges instead of ``parent_id``; multi-parent
  is resolved by picking the lexicographically smallest source id.

### Changed

- **`useCollapsedTree` signature** — gains ``edges: SketchEdge[]``.
  Every call site (`SketchCanvas.tsx`) updated.
- **`useDragAndDrop` signature** — gains ``edges: SketchEdge[]``;
  drag-to-parent calculations now use directed edges for sibling
  lookup. The parent-local coordinate system is gone (coordinates
  are flat across the whole canvas).
- **`KindInspectorProps`** — gains ``allEdges: SketchEdge[]``.
  CategoryInspector / ServiceInspector use it for child counts.
- **`useNodeCreation`** — nested drops materialise a directed edge
  for *every* kind, not just actor / service.
- ``viewer/src/flow/autoLayout.ts`` — implicit ``parent_id`` →
  decomposition-edge synthesis removed; only explicit edges drive
  the dagre layout.
- ``viewer/src/canvases/sketch/overlapNudge.ts`` /
  ``SketchModals.tsx`` — parent-absolute walks simplified to
  identity (flat coordinate system).
- **migrate.py** (v0.1 → v0.2 legacy migrator) — drops the
  ``parent_id`` arg from ``_v01_to_actor`` / ``_v01_to_service`` /
  ``_v01_to_composition``. v0.1 hierarchy info is lost in the
  migration (v0.1 data is effectively unused; the v0.26 read-side
  migration handles any newer pre-v0.26 ``parent_id`` data on disk).
- **`viewer/src/canvases/ActorRefPicker.tsx`** — parent-chain label
  feature dropped (was ``parent_id``-only). Follow-up if missed in
  practice.
- ``viewer/tests/structural-guards.test.tsx`` — ``App.tsx`` ceiling
  425 → 430 (D-2026-05-25-A entry recorded in the budget note) to
  absorb the services-edges-in-drill-context wiring.

### Migration notes for users

- **Open every existing project once** so the read-side migration
  fires and persists. After a single open, the project's
  canvas.json files settle into the new model (no ``parent_id`` on
  nodes; new directed edges with id ``e_migrated_{node_id}`` per
  former parent_id link).
- Inspect the resulting git diff before committing — the migration
  is idempotent + non-destructive, but the diff is large for
  projects with deep parent_id chains.

### Verification

- Server pytest **433 passed**; mypy clean.
- Viewer vitest **562 passed**; tsc clean.

## [0.25.1] — 2026-05-24

### Removed

- **Auto-layout `⊞` button on the main `ServicesCanvas`**
  ([D-2026-05-24-C](./docs/DECISIONS.md#d-2026-05-24-c--services-canvas-reverts-auto-layout-opt-in-controls-live-in-per-service-modal-v0251)).
  Same-day partial rollback of D-2026-05-24-B. User clarified the
  Services-as-summary intent: per-service controls belong inside the
  `ServiceDetailModal`, not on the overview canvas. `ServicesCanvas`
  now passes no `layoutAlgo`. `ServiceDetailCanvas` keeps
  `layoutAlgo="radial"` — the per-service modal is where auto-layout
  lives. The `layoutAlgo` prop generalisation from v0.25.0 is
  retained; the radial algorithm (`radialLayout.ts` /
  `useRadialLayout.ts`) stays live, used by `ServiceDetailCanvas`.

### Changed

- `viewer/tests/auto-layout-isolation.test.tsx` — Services test
  flipped back to "must NOT opt in"; Services positions-only test
  removed; header doc and contract list updated.
- `docs/SPEC.md` §Auto-layout table — Services row marked as no
  opt-in.

## [0.25.0] — 2026-05-24

### Added

- **Radial auto-layout for Services + ServiceDetail canvases**
  ([D-2026-05-24-B](./docs/DECISIONS.md#d-2026-05-24-b--services--servicedetail-opt-into-auto-layout-with-new-radial-algorithm-v0250)).
  ServicesCanvas and ServiceDetailCanvas now render the `⊞`
  auto-layout button. Clicking it places nodes in concentric rings
  around a hub (anchor on Services; hidden root-service on
  ServiceDetail) — appropriate for the hub-and-spoke topology those
  canvases use, where the directional-tree algorithm Foundation /
  Actors use is not a fit. BFS from the hub assigns ring levels;
  within a ring, id-sorted members are placed at equal angles
  starting from the top. Orphan nodes drop into a grid below the
  outermost ring. Pure algorithm in
  `viewer/src/canvases/sketch/radialLayout.ts` (8 new unit tests);
  React bridge in `viewer/src/canvases/sketch/useRadialLayout.ts`.

### Changed

- **`enableAutoLayout: boolean` → `layoutAlgo: "tree" | "radial" | null`**
  prop on `SketchCanvas`. Same isolation contract (per-wrapper
  opt-in; `Cmd+Z` undo; positions-only) — what changed is that each
  wrapper now picks an algorithm rather than just toggling the
  feature on. `FoundationCanvas` + `ActorsCanvas` migrate to
  `layoutAlgo="tree"`; `ServicesCanvas` + `ServiceDetailCanvas` opt
  in with `layoutAlgo="radial"`. SketchCanvas still has no default —
  without a wrapper, no button.
- `viewer/tests/auto-layout-isolation.test.tsx` — Services /
  ServiceDetail "must NOT opt in" tests flipped to "must opt in with
  radial" + 2 new positions-only tests covering the radial path.
- `docs/SPEC.md` §Auto-layout — rewritten with the algo table +
  per-algorithm behaviour sections.

## [0.24.15] — 2026-05-24

### Changed

- **Default node size 140×60 → 80×36**
  ([D-2026-05-24-A](./docs/DECISIONS.md#d-2026-05-24-a--default-node-size-14060--8036-v02415)).
  Second tightening pass after D-2026-05-17-N (180×80 → 140×60). Tighter
  default suits Services / ServiceDetail hub-spoke layouts without
  overflow. Existing nodes keep their stored width / height in
  `canvas.json`; only new stencil-drop / pane-double-click / paste
  creates an 80×36 node. SSOT trio updated: `mashbill/models.py`,
  `viewer/src/canvases/sketch/constants.ts`,
  `viewer/src/domain/BaseFields.ts`. Auto-layout padding stays at 64
  (set by D-2026-05-17-N) — now ~1.8× the longer node dimension, so
  overlap risk strictly decreases.

## [0.24.14] — 2026-05-21

### Added

- **Snapshot view ("view at git tag")**
  ([D-2026-05-21-C](./docs/DECISIONS.md)). Click any tag in the
  sidebar to enter read-only snapshot mode at that point in time.
  An amber banner appears in the header (*"Viewing snapshot at vN
  — edits are disabled until you exit"*); the canvas renders the
  project state at that tag without touching the working tree. The
  user's live work stays intact and resumes on `✕ exit`.
- Server: `git_store.py::read_file_at_tag()` (wraps `git show
  <tag>:<path>`, working tree untouched). New
  `GET /api/projects/{id}/at-tag/{tag}` endpoint returns the
  ProjectDoc + every canvas (foundation / actors / services + each
  service_detail) at the tag.
- Viewer: `useSnapshotView` hook owns the snapshot state machine
  (viewingTag / snapshotCache / enterTagView / exitTagView). App
  swaps cache + guards `applyEdit` so saves never touch tag data.
- 2 new server tests (snapshot returns tag-time state even after
  later mutation / unknown tag 404).

### Changed

- `SketchSidebar` tag rows are now clickable (entire row is the
  view-at-tag action; the ✕ delete remains on hover). The viewed
  tag highlights with a 👁 marker and amber background.
- `viewer/tests/structural-guards.test.tsx` — App.tsx ceiling raised
  410 → 425 for the snapshot-mode wiring per D-2026-05-21-C.

## [0.24.13] — 2026-05-21

### Added

- **설계도 발행 (project-level semver)**
  ([D-2026-05-21-B](./docs/DECISIONS.md)). Novel's output is now framed
  as a *설계도 (design blueprint)* — the whole project at one
  coherent point. Each project carries a `blueprint_version`
  (default `v0.1.0`); the user bumps major / minor / patch from the
  new `📤 설계도 발행 ▾` button on the canvas tab strip (replaces
  the old `Mark session…` button). Each bump persists the new
  version on `ProjectDoc` and creates a git tag at the resulting
  version name.
- `POST /api/projects/{id}/publish` endpoint (body
  `{"bump": "major"|"minor"|"patch", "message"?}`; returns 201 with
  `{from_version, to_version, tag}`).
- Header now shows the current blueprint version as a monospace
  badge next to the project name.
- 3 server tests pinning the publish endpoint behaviour
  (patch / minor+major chain / invalid bump → 400).

### Changed

- `ProjectDoc` Pydantic + TS interfaces gain optional
  `blueprint_version`. Existing projects backfill to `v0.1.0` via
  Pydantic default on first read (no explicit migration needed).
- `CanvasTabs` swaps `onMarkSession` for `blueprintVersion` +
  `onPublishBlueprint` props. The ad-hoc tag endpoint
  (`POST /tags`) stays for sidebar session-tag use; the canvas tab
  strip no longer triggers it.

## [0.24.12] — 2026-05-21

### Added

- **Header SaveIndicator** ([D-2026-05-21-A](./docs/DECISIONS.md)).
  Canvas auto-save now shows a visible state next to the live socket
  dot: 💾 saving… / ✓ saved / ⚠ save failed (hidden when idle).
  `useCanvasPersist` already computed `saveState` but no shell
  component rendered it — silent success was a bug per
  Novel's *"Clear Feedback"* UX rule. i18n keys
  `header.saveState.{saving,saved,error}` for en + ko.

### Fixed

- **PUT canvas response now includes `_dirty` decoration**
  ([D-2026-05-21-A](./docs/DECISIONS.md), v0.22.0 follow-up). The
  v0.22.0 dirty-tracking UX (publish button only enabled when the
  node differs from its last-published baseline) silently broke for
  edits made in the current session: GET response carried `_dirty`,
  but PUT response did not. After every auto-save, the viewer's
  `_dirty` stayed stale until a full page reload. v0.24.12 mirrors
  the GET endpoint's decoration in the PUT endpoint, and
  `useCanvasPersist` merges the response's per-node `_dirty` into
  the cache (non-destructive — only the `_dirty` field is
  overwritten, so in-flight user edits stay intact).

### Verification

- New server test `test_canvas_put_response_includes_dirty_decoration`
  (426 server pytest + 544 viewer vitest all pass; tsc + mypy clean).

## [0.24.11] — 2026-05-19

### Added

- **`Symbol` formalised as a first-class domain concept**
  ([D-2026-05-19-D](./docs/DECISIONS.md),
  [CONCEPTS.md §Symbol](./docs/CONCEPTS.md)). A Symbol is a node of
  one of 5 producer kinds — `mission`, `core_value`, `identity`,
  `actor`, sub-actor — that can be referenced from the consumer side
  (Service / ServiceDetail canvases) via the 4 alias kinds
  (`mission_ref` / `value_ref` / `identity_ref` / `actor_ref`).
  Symbol-ness is a *kind property*, not a per-instance toggle — every
  instance of a producer kind is always a Symbol candidate.
- `_migrate_actor_isroot_to_false` — idempotent canvas.json migrator
  that resets legacy `actor.is_root=true` to `false` on first read.
  banas-imported's Bana / Admin / Guest auto-migrate.

### Changed

- `actor.is_root` no longer surfaces in the Inspector. The
  *"Mark as Actor Root (centre of its tree)"* checkbox is gone, the
  actor badge no longer reads "액터 루트" (just "액터"), and the
  v0.3 `ActorCompositionPlaceholder` (which was gated on `!is_root`)
  is removed. `service.is_root` is preserved as the ServiceDetail
  anchor marker (still load-bearing for that one role).
- `docs/SPEC.md §Publish eligibility` table cleaned up: removed the
  `actor (is_root)` row since the field is now meaningless for
  actor kind.

### Removed

- `viewer/tests/inspectors/inspectors.smoke.test.tsx` — two tests
  that pinned the `ActorCompositionPlaceholder` visibility per
  `is_root` removed.

### Rationale

User flagged 2026-05-19 *"mark as actor root 의 의미가 대체 뭔지
몰라서 그래요"* — the toggle's label conveyed nothing. Tracking the
field's history (origin commit `54c2f4a`, 2026-04-20 → v0.13 reset)
showed the original intent (singleton trunk per tree + embedded
identity) had evaporated. v0.24.10 already removed the publish gate
on actor.is_root; this ship removes the last vestigial semantic.
The Symbol concept formalised here gives the producer/consumer model
a name and a SPEC home so future sessions don't re-derive it.

User direct quotes locking the change: *"모든 액터는 다른 캔버스에
참조됩니다"* / *"액터 및 서브액터는 심볼이 될 수 있고, 파운데이션에
있는 미션/코어밸류/아이덴티티 다 심볼이 될 수 있어요"* /
*"아니 1이지 모든게 다 심볼이 될 수 있다니까"*.

544/544 viewer vitest + 425/425 server pytest pass; mypy + tsc clean.

## [0.24.10] — 2026-05-19

### Changed

- **Actor master (is_root) now publishes directly**
  ([D-2026-05-19-C](./docs/DECISIONS.md)). v0.18.0's blanket
  `is_root` publish guard (waiting on Phase 5 referent flow) is
  narrowed to `is_root && kind === "service"`. Actor masters like
  Bana / Admin / Guest with their own typed text (motivation /
  pain / body) now hit the standard direct-publish path: per-node
  MD file + MAJOR version bump + git commit. Service is_root
  (ServiceDetail mirror) stays guarded — its Services-canvas
  master is the publish entry point. Phase 5 referent flow will
  layer cross-canvas referent updates on top of this direct
  path; no migration needed.
- Lockstep updates: `mashbill/md_publish.py::can_publish` +
  `viewer/src/domain/publishEligibility.ts::canPublish` +
  publish docstrings + `docs/SPEC.md §Publish eligibility` table.

### Fixed

- 4 server tests flipped from "actor is_root rejects publish" to
  "actor is_root succeeds": `test_md_publish.py`,
  `test_folder_io.py`, `test_api_endpoints.py`, +
  `viewer/tests/domain/publishEligibility.test.ts`. Service
  is_root rejection retained as a separate assertion. 425 server
  pytest + 546 viewer vitest all pass. mypy clean.

## [0.24.9] — 2026-05-19

### Changed

- **Korean i18n polish for actor inspector** —
  `viewer/src/i18n/locales/ko.json`. User flagged 2026-05-19 that
  `측` / `페인` / `운영자측` were awkward Korean (1-char
  translation + transliteration). Locked via AskUserQuestion preview:
  - `inspector.field.side`: `측` → `역할`
  - `inspector.field.pain`: `페인` → `어려움`
  - `inspector.fieldHint.side`: `가치 교환의 어느 쪽` →
    `가치 교환에서 맡는 역할`
  - `inspector.fieldHint.targetSide`: `운영자측 / 사용자측 / 둘 다`
    → `제공자 / 사용자 / 둘 다`
  - `inspector.operatorSideOption`: `운영자측` → `제공자`
  - `inspector.userSideOption`: `사용자측` → `사용자`
  - `bothSideOption` unchanged (`둘 다`).
  `en.json` untouched (already natural). Key set unchanged so
  `i18n-keys-parity` guard stays green. 546/546 viewer tests pass,
  tsc clean.

## [0.24.8] — 2026-05-19

### Fixed

- `viewer/tests/auto-layout-isolation.test.tsx` — Actor
  positions-only assertion was using `side: "consumer"` (shipped in
  v0.24.5), which is not a valid Novel enum value. Pydantic
  `ActorNode.side` is `Literal["operator", "user"] | None`; TS
  test slipped through because of an `as SketchNode` cast in
  `makeNode`. Replaced with `side: "operator"` (matches Hero's
  provider role). Test continues to pass (7/7). Root cause = not
  cross-checking `mashbill/models.py::ActorNode` before writing
  the test — global CLAUDE.md `honesty: 추측 금지` violation.

## [0.24.7] — 2026-05-19

### Changed

- Docs-only — `docs/DECISIONS.md`
  ([D-2026-05-19-B](./docs/DECISIONS.md)) pins the
  **actor state/transitions meta-question OPEN**. PHILOSOPHY P5
  "Actor as class" doesn't explicitly handle state/transitions
  (e.g., Guest → Login service → Bana). Current implicit stance:
  state lives in Service/ServiceDetail flow; actor stays static
  role. **Decision deferred (open)** — pinned so future sessions
  don't re-debate. Memory `project_plot_state_transitions_open.md`
  preserves 5 candidate resolutions (status quo / typed field /
  new kind / docs-only formalisation / state_via_service ref).
  Trigger to revisit: user starts drawing state-transition flows
  (login, payment, approval) and the actor/service boundary feels
  awkward.

No code or behaviour change.

## [0.24.6] — 2026-05-19

### Changed

- Docs-only — `docs/NEXT_SESSION.md` + `docs/DECISIONS.md`
  ([D-2026-05-19-A](./docs/DECISIONS.md)) pin the
  **research-subject backing-data feature deferred** decision.
  Actor 캔버스 stays role-level (4-layer max: anchor → Bana →
  mode → vertical). Real interview subjects (김유정, 박태식 등) live
  in the actor's `body` Markdown under a `## 인터뷰 대상자` section
  — no new typed field, no new kind, no new canvas. YAGNI per
  global CLAUDE.md `design: YAGNI > others` + Novel's v0.13 god
  SketchNode lesson. `fromJson` + `test_schema_parity.py` keep
  all future trajectories (new field / new canvas / external tool)
  backward-compat. Revisit trigger filed in NEXT_SESSION queue
  (10+ subject pile-up).

No code or behaviour change.

## [0.24.5] — 2026-05-18

### Added

- **Auto-layout button on the Actors canvas**
  ([D-2026-05-18-B](./docs/DECISIONS.md)). `ActorsCanvas` now opts
  into the `⊞` Auto-layout button alongside `FoundationCanvas`
  (`enableAutoLayout={true}`). Same contract as Foundation:
  one-shot apply via the regular `onDocChange` pipeline, `Cmd+Z`
  undoes it, positions-only mutation (no `kind` / `label` /
  `parent_id` / typed-text / edge changes). Driven by the
  `banas-imported` Actors canvas where Hero / Fan / Bana root
  personas were overlapping. `ServicesCanvas` and
  `ServiceDetailCanvas` remain off — hub-and-spoke / root-pinned
  geometry where the directional-tree algorithm has no obvious win
  yet; revisit when a real overlap case arrives.

### Changed

- `viewer/tests/auto-layout-isolation.test.tsx` — Actor wrapper
  test flipped from "must NOT render" to "renders the Auto-layout
  button"; a new Actor positions-only assertion mirrors the
  Foundation one. `Services` / `ServiceDetail` assertions
  unchanged — they remain the negative side of the contract.
- `docs/SPEC.md §Auto-layout` — "Foundation only" wording removed
  in favour of "opt-in per wrapper"; isolation contract section
  + history append.

## [0.24.4] — 2026-05-18

### Changed

- Docs-only — `plot/docs/NEXT_SESSION.md` adds a new top-priority
  entry **"Foundation 정리 + Actor 정리"** (user-filed at session
  end 2026-05-18: *"다음에는 파운데이션 정리 한번하고 액터 정리로
  갈거에요"*). Target = the `banas-imported` test project; scope
  open for re-anchor at next session start. Novel-space-vs-time rule
  ([[feedback_plot_space_vs_time]]) applies — only spatial
  (relations/structure) content gets imported; vision / roadmap /
  sprint are explicitly out.

No code or behaviour change.

## [0.24.3] — 2026-05-18

### Changed

- **Published folder name: ``slug`` → ``node_id``**
  ([D-2026-05-18-A](./docs/DECISIONS.md)). v0.23.0 used
  ``slugify(label)`` which preserved Korean / CJK characters,
  producing folder names like ``published/core_value/관용-tolerance/``.
  v0.24.3 switches to ``node.id`` (ASCII per Novel's id policy):
  ``published/core_value/core-tolerance/v2.0.md``. Bonus: label
  rename no longer renames the folder (id is stable).

- ``published_md_path`` signature: ``(canvas_dir, *, kind, label,
  version)`` → ``(canvas_dir, *, kind, node_id, version)``.

### Migration

- New ``_migrate_published_slug_to_id`` helper runs on first
  ``read_canvas``: walks the raw canvas nodes, computes the old
  slug for each ``(id, label)`` pair, and renames
  ``published/<kind>/<slug>/`` → ``published/<kind>/<node_id>/``.
  Idempotent (no-op when slug == node_id, or when the slug folder
  no longer exists). Conflicts leave the slug folder for audit
  rather than overwrite.
- Two-step migration for pre-v0.23.0 projects: flat-to-kind-slug
  → slug-to-id. Result identical regardless of source version.

## [0.24.2] — 2026-05-17

### Changed

- **Default node size 180×80 → 140×60**
  ([D-2026-05-17-N](./docs/DECISIONS.md)). Smaller default fits more
  nodes per viewport without scroll. Existing nodes keep their own
  width/height in canvas.json — only nodes created from now on adopt
  the new default. Changed in three SSOTs in lockstep: server
  ``BaseNodeFields``, client ``parseBaseFields`` fallback, and viewer
  ``DEFAULT_WIDTH``/``HEIGHT`` constants.
- **Auto-layout padding 32 → 64** + **isolated-node grid**. The
  ➤ align button now uses 64 px between sibling subtrees (was 32 px,
  which produced visual overlap for nodes ≥ 200 px wide), and packs
  isolated (not-BFS-reachable) nodes into a square-ish grid instead
  of a single vertical column. Grid cells use
  ``max(width)+padding × max(height)+padding`` so they never collide.

### Tests updated

- ``base-fields.test.ts``, ``round-trip.test.ts`` — expect 140×60
  defaults.
- ``autoLayout.test.ts`` — isolated-node test rewritten for grid
  placement.
- 421 pytest + 545 vitest pass; mypy + tsc clean.

## [0.24.1] — 2026-05-17

### Added

- **4-ref symmetry: ``notes_in_context`` for mission_ref / value_ref /
  identity_ref** ([D-2026-05-17-M](./docs/DECISIONS.md)). The three
  non-actor ref kinds now carry a free-form typed-text field so
  service authors can capture how the referenced Mission / CoreValue
  / Identity applies to **this** service without leaving the canvas.
  Mirrors the existing ``actor_ref.gives``/``receives`` pattern
  (D-2026-05-16-F) — same free-form MD textarea, same in-context
  semantics. User-locked via AskUserQuestion (option "(B) 확장").
- New i18n keys ``inspector.field.notesInContext`` +
  ``inspector.fieldHint.notesInContext`` (en + ko).

### Migration

- Zero-migration: ``notes_in_context`` defaults to ``""``. Pre-v0.24.1
  canvas.json files load unchanged.

## [0.24.0] — 2026-05-17

### Added

- **Live Preview Stage 3 — heading + list + image embed decorations**
  ([D-2026-05-17-L](./docs/DECISIONS.md)). Three new CodeMirror plugins
  layered into the MdTextarea on top of v0.21.0's mermaid plugin.
  Completes the 3-stage Obsidian Live Preview track started in v0.19.0.

  - **mdHeadingPlugin**: ``# Title`` / ``## Subtitle`` / ``### Section``
    lines now render with scaled font-size (1.5× / 1.3× / 1.15×) while
    the user keeps editing the raw ``#`` markers.
  - **mdListPlugin**: bullet list markers (``-`` / ``*`` / ``+``)
    render as a styled ``•`` glyph via CSS ``::before`` (mark
    decoration; raw markers stay in the doc).
  - **mdImagePlugin**: ``![alt](url)`` lines get an inline block
    widget below with the rendered image. URLs accepted:
    ``http(s)://``, ``data:image/``, and project-relative paths
    (``./img.png``). Lazy load + max-width 100% + max-height 480px.
    Broken image → red error block.

- New endpoint ``GET /api/files/raw`` serves raw image bytes for the
  image-embed plugin (the existing ``/api/files`` returns JSON
  ``{content}`` which an ``<img>`` tag can't render). Extension
  allow-list (``.png/.jpg/.jpeg/.gif/.webp/.avif/.svg``); same
  path-traversal safety as text reads.

### Tests

- 4 new pytest cases (``test_file_raw_endpoint.py``): byte round-trip
  + 404 + 400 (disallowed ext) + 400 (path traversal).
- Full suite: 421 pytest + 545 vitest pass; mypy + tsc clean.

## [0.23.2] — 2026-05-17

### Changed

- **Publish moved to sticky Inspector footer** as a primary CTA
  ([D-2026-05-17-K](./docs/DECISIONS.md)). Inspector header now
  carries only chrome (delete / widen / close); the publish action
  is a large emerald button at the bottom of the Inspector, full
  width, with the next version in its label (*"📤 publish → v3.0"*).
  Unpublish is a secondary amber text link below, visible only when
  there's a publish to revert. Footer only renders for publish-eligible
  kinds. User-picked layout via AskUserQuestion ASCII-mockup.
- **Published MD modal now opens centred on the viewport**
  ([D-2026-05-17-K](./docs/DECISIONS.md)). Root cause for the v0.23.0
  "trapped in Inspector" symptom was the aside's `backdrop-blur`
  making it the containing block for `position: fixed` descendants
  (CSS spec). Fix: ``PublishedMDModal`` is now rendered via
  ``createPortal`` into ``document.body``. Modal container is also
  user-resizable via CSS ``resize: both`` (drag the bottom-right
  grip; min 360×240, max 95vw×95vh, default 720×80vh).
- LOC ceiling raise: ``BaseInspector.tsx`` 340 → 380 (audit trail in
  ``structural-guards.test.tsx``).

## [0.23.1] — 2026-05-17

### Added

- **Unpublish button** ([D-2026-05-17-J](./docs/DECISIONS.md)). An
  ↩ unpublish button now sits next to 📤 publish in the Inspector
  header, visible only when the node has a publish to revert
  (``version !== "v1.0"``). Click → confirm dialog → server runs
  ``git revert`` on the most recent publish commit for the node,
  atomically undoing the version bump, the published MD file, and
  any Phase 4 ancestor MINOR bumps that were part of the same
  commit. History is preserved (revert is non-destructive).
- New endpoint
  ``POST /api/projects/{id}/canvases/{kind}/nodes/{node_id}/unpublish``
  returning ``{node_id, from_version, to_version, reverted_sha,
  revert_commit_sha}``. 409 when there's no publish to revert.

### Changed

- ``publish_node`` now calls ``ensure_clean_working_tree`` before
  staging its own changes — if the project's git working tree is
  dirty (e.g. fresh project where canvas.json isn't tracked yet),
  the helper snapshots that state into a separate ``chore(plot):
  seed pre-publish state`` commit. Without this, the very first
  publish in a project would bundle canvas.json into the publish
  commit, and a later unpublish revert would wipe canvas.json
  entirely. Idempotent no-op on a clean tree.
- LOC ceilings raised (audit trail in ``structural-guards.test.tsx``):
  ``BaseInspector.tsx`` 295 → 340, ``SketchCanvas.tsx`` 440 → 450,
  ``App.tsx`` 400 → 410.

## [0.23.0] — 2026-05-17

### Added

- **Inspector "Published versions" section + MD modal**
  ([D-2026-05-17-I](./docs/DECISIONS.md)). For every publish-eligible
  node, the Inspector now shows a list of every published MD version
  (newest first), with version label + publish timestamp + short
  commit sha. Clicking a row opens a modal that renders the MD via
  the existing ``MDPreview`` (GFM + Mermaid). Escape or backdrop
  closes. Empty when never published; auto-refreshes after a publish.
- New endpoint
  ``GET /api/projects/{id}/canvases/{kind}/nodes/{node_id}/published``
  returns the list metadata. Reuses the existing ``GET /api/files``
  for the actual MD content.

### Changed

- **Published MD folder layout reorganised**
  ([D-2026-05-17-I](./docs/DECISIONS.md)). Pre-v0.23.0 flat layout
  (``<canvas>/published/<kind>-<slug>-v<X>.md``) → new grouped
  layout (``<canvas>/published/<kind>/<slug>/v<X>.md``). All
  versions of the same logical document live in one folder; kind
  serves as the top-level taxonomy. ``published_md_path`` returns
  the new path; viewer's Published versions section reads it.
- ``SPEC.md §Publish §What lands on disk per publish`` updated;
  new ``§Published versions in the Inspector`` subsection added.
- ``BaseInspector.tsx`` LOC ceiling raised 285 → 295 to absorb the
  ``PublishedVersionsSection`` insertion (canPublish-gated).

### Migration

- Idempotent first-read migration in ``folder_io.read_canvas`` moves
  legacy flat files to the new layout on the next canvas read. No
  user action needed; no commit emitted (the move is silent — same
  pattern as the v0.13 ``_absorb_md_typed_text_into_json``).
- Skipped silently when the destination already exists (no
  overwrite).

## [0.22.2] — 2026-05-17

### Changed

- Docs-only — queued `v0.23.0` as the top item in
  `plot/docs/NEXT_SESSION.md`: **node publish UX (Inspector
  Published versions section + MD modal) + published-MD folder
  reorg** to `<canvas>/published/<kind>/<slug>/v<X>.md`. Critical
  design questions were locked this turn (folder layout picked via
  ASCII-tree AskUserQuestion; migration policy = smallest viable
  first-read idempotent move). Implementation deferred to v0.23.0
  per user *"다음 세션에서 ... 고민해봐야겠네요"* + *"그리고 어떻게
  정리할건지 저한테 말해주고 작업합시다."*

  Plan pinned at
  `/Users/woogis/.claude/plans/jolly-bouncing-orbit.md`.

  No code or behaviour change.

## [0.22.1] — 2026-05-17

### Changed

- Docs-only — D-2026-05-17-H Approval line gets a post-ship user
  confirm (*"이제 되네"*) after the v0.22.0 dirty-gate was verified
  in real Chrome. Same turn, the user proposed enlarging the
  publish button and moving it to the Inspector footer — queued
  in NEXT_SESSION.md as ``v0.22.x publish-button placement + size``
  (deferred per user *"이런건 나중에 합시다"*). No code change.

## [0.22.0] — 2026-05-17

### Added

- **Publish dirty tracking + button disable when clean**
  ([D-2026-05-17-H](./docs/DECISIONS.md)). The Inspector's 📤 publish
  button is now disabled when the selected node has no content
  changes since its last publish. "Content" = typed-text fields +
  ``label`` + ``body`` + the set of edges incident on the node.
  Visual changes (position / color / size / shape) and Phase 4 MINOR
  drift from a descendant publish do **not** trigger dirty. Hover
  tooltip on the disabled button names the last-published version
  (*"v2.0 이후 변경 사항 없음"* / *"No content changes since v2.0"*).
  Initial publish (no baseline yet) is always allowed.

  Server-side: new private ``publish_baseline: dict | None`` field on
  ``BaseNodeFields`` (aliased ``_publish_baseline``); ``publish_node``
  stamps it on the bumped target and any mirror canvas;
  ``canvas_get_endpoint`` recomputes ``_dirty`` per node on every GET.
  ``write_canvas`` preserves baseline from disk when client PUTs omit
  it.

### Changed

- ``SPEC.md §Publish §Idempotence`` rewritten as ``§Publish gated by
  dirty``. The "always-bump on the publish target (MAJOR)" clause is
  preserved but now conditioned on the button being enabled.
- ``BaseInspector.tsx`` LOC ceiling raised 270 → 285 to wrap the
  publish button in a dirty-aware IIFE (disabled state, conditional
  ``onClick``, dirty-vs-clean className + tooltip). Single audit
  trail in ``structural-guards.test.tsx``.

### Migration

- Existing canvas.json files load unchanged (``_publish_baseline``
  defaults to ``None``). Nodes that were published before v0.22.0
  will show as dirty on first GET (no baseline yet) — one harmless
  re-publish per node seeds the baseline.

## [0.21.4] — 2026-05-17

### Changed

- Docs-only — appended **Post-ship user confirm** lines to
  DECISIONS entries D-2026-05-17-E (focus), D-2026-05-17-F (handle
  hit area), and D-2026-05-17-G (loose connection mode). All three
  bug fixes from today were verified by the user in real Chrome.
  No code or behaviour change.

## [0.21.3] — 2026-05-17

### Fixed

- **Connection mode = Loose** (D-2026-05-17-G) — edges can now be
  drawn between any two handles regardless of `type="source"` vs
  `type="target"`. Previously, the RF default `strict` mode blocked
  target→target / source→source drags, so e.g. "Core Value top
  handle → Anchor left handle" silently failed (both are
  `type="target"` in BaseNode). This contradicted
  [SPEC.md §Anchor](./docs/SPEC.md#anchor) which states *"User may
  draw edges from / to the anchor like any other node"*. Single-line
  fix: `connectionMode={ConnectionMode.Loose}` on the ReactFlow
  component in SketchCanvas.

## [0.21.2] — 2026-05-17

### Fixed

- **Handle hit area** (D-2026-05-17-F) — connection handles now have
  a 30×30 invisible click target while the visible dot stays exactly
  10×10. Previously, the 10×10 hit area made it easy to miss the
  handle by 1–2 px and have nothing happen. Implemented as a single
  `.react-flow__handle::after { position: absolute; inset: -7px; }`
  rule in `styles.css`; pseudo-element clicks bubble to the parent
  so RF's `event.target.closest('.react-flow__handle')` identification
  is unaffected. User-approved RF default override (CLAUDE.md
  anti-pattern audit trail rule).

## [0.21.1] — 2026-05-17

### Fixed

- **MdTextarea focus redirect** (D-2026-05-17-E) — clicking an
  Inspector typed-text field now correctly lands keyboard focus on
  the CodeMirror editor. Previously, the browser's click processing
  could redirect focus to the hidden sr-only mirror textarea instead
  of the CM editor; the textarea now immediately delegates any
  received focus back to the CM view via `onFocus` → `view.focus()`.

## [0.21.0] — 2026-05-17

Live Preview Stage 2 — mermaid SVG inline decoration. Any
``` ```mermaid``` ``` fenced block inside the Inspector's MdTextarea
now renders as an SVG widget directly below the closing fence,
200 ms after the last keystroke. The user keeps editing the raw
markdown above; the SVG re-renders. Per
[D-2026-05-17-D](./docs/DECISIONS.md). Stage 2 of the 3-stage
Obsidian Live Preview track that v0.19.0 started; Stage 3 (heading
font-size + list bullet + image embed decorations) is queued for
v0.22.0+.

Mermaid is now **lazy-loaded** through a shared singleton
([viewer/src/edit/mermaidLoader.ts](./viewer/src/edit/mermaidLoader.ts)).
A project with no mermaid blocks pays zero mermaid bytes.
Bundle delta: index chunk **1,759 KB raw / 515 KB gzip** (v0.19.0)
→ **1,185 KB raw / 381 KB gzip** (v0.21.0) — mermaid moved to its
own `mermaid.core-*.js` lazy chunk plus per-diagram-type chunks.

Seven open spec questions, all locked in plan-mode
([D-2026-05-17-D](./docs/DECISIONS.md)): lazy singleton, reuse
MDPreview error pattern, no size cap, block widget below the fence
(SSOT keeps source visible), default mermaid theme, 200 ms debounce,
new vitest SSOT-invariant test.

### Added

- ``viewer/src/edit/mermaidLoader.ts`` (new) — shared
  ``loadMermaid()`` singleton. Lazy ``import("mermaid")`` + one-time
  ``mermaid.initialize({ startOnLoad: false, securityLevel: "loose",
  theme: "default" })``. Hands callers an ``{ render(id, code) }``
  API and never sees the markdown source itself.
- ``viewer/src/canvases/inspectors/shared/mdMermaidPlugin.ts``
  (new) — composite CodeMirror 6 extension. ``mermaidDecoField``
  ``StateField<DecorationSet>`` holds the current widget set;
  ``mermaidDebouncer`` ``ViewPlugin`` watches doc changes and
  dispatches ``setMermaidDecorations`` 200 ms after the last edit.
  ``MermaidWidget extends WidgetType`` renders the SVG via the
  shared loader; on failure swaps to a red-border
  ``data-mermaid="error"`` block.
- ``viewer/tests/inspectors/mermaid-decoration.test.tsx`` (new) —
  SSOT invariant + happy path + error path. Mocks ``mermaidLoader``
  so the real mermaid library is never pulled into the test bundle.

### Changed

- ``viewer/src/canvases/inspectors/shared/MdTextarea.tsx`` — adds
  ``mdMermaidPlugin`` to the EditorState extensions array (2 LOC).
- ``viewer/src/edit/MDPreview.tsx`` — switched from
  ``import mermaid from "mermaid"`` + module-level
  ``mermaid.initialize`` to the shared ``loadMermaid()`` singleton.
  First MDPreview render now awaits a dynamic import; first-paint of
  the Inspector improves because the Preview tab is not on the
  initial path.

### Architectural notes

- **CodeMirror 6 forbids ``ViewPlugin``-sourced block decorations.**
  Block widgets must come from a ``StateField`` so they participate
  in the layout pass. v0.21.0 splits the work: a ``StateField``
  owns the decoration set, a ``ViewPlugin`` handles the debounce
  and dispatches ``StateEffect``s. Both ship together as a single
  ``Extension`` array.
- **SSOT preserved.** The decoration only reads ``view.state.doc``
  and emits widgets; it never dispatches a transaction. The
  vitest ``mermaid decoration — SSOT invariant`` test pins this
  contract (verifies ``onChange`` is never called and the hidden
  read-only mirror still matches the original value after the
  widget renders).

## [0.20.0] — 2026-05-17

Phase 4 MINOR propagation up the ancestor chain. When a node is
published, every ancestor along its ``parent_id`` chain gets a
silent ``v<MAJOR>.<MINOR>`` MINOR bump in the same atomic git
commit, with one ``Publish-Propagated-Ancestor: <id> <from>→<to>``
trailer per ancestor. Per [D-2026-05-17-C](./docs/DECISIONS.md).
Closes the second half of the D-2026-05-13-O versioning model that
v0.18.0 (Phase 3) only delivered the MAJOR half of.

The 5 open spec questions filed in NEXT_SESSION.md are locked:

1. **Scope = ``parent_id`` chain only.** Refs (``actor_ref``,
   ``mission_ref``, ``value_ref``, ``identity_ref``,
   ``service_ref``) are not propagation paths. Same-id mirrors
   (ServiceDetail root service ↔ Services master service) are
   crossed by id-matching only.
2. **No new MD files for propagated ancestors** — only their JSON
   ``version`` field advances. Disk MD snapshots stay at their
   MAJOR-publish versions; the JSON/MD version gap is the
   "descendants moved" indicator.
3. **One git commit** with extra trailers (not separate commits).
4. **``git revert HEAD``** undoes the entire publish + propagation
   atomically.
5. **No new Inspector UI** for v0.20.0 — version badge already
   shows MINOR.

### Added

- ``mashbill/propagation.py`` (new) — pure ``walk_ancestors()``
  module + ``LogicalAncestor`` dataclass. Walks ``parent_id`` and
  same-id mirrors only; ignores all ``*_ref`` fields. Returns
  ancestors with the list of canvas keys each appears in so the
  caller can mirror-sync every file.
- ``mashbill/md_publish.py::bump_minor`` — ``v<MAJOR>.<MINOR>`` →
  ``v<MAJOR>.<MINOR+1>``. Mirror of existing ``bump_major``.
- ``mashbill/folder_io.py::_load_all_canvases`` —
  enumerates foundation / actors / services + every
  ``service_detail:<sid>`` into one dict for the propagation walk.
- ``mashbill/folder_io.py::_bump_node_version_in_canvas`` — pure
  helper, returns a CanvasDoc copy with one node's version
  replaced.
- ``viewer/src/api.ts::PublishPropagatedAncestor`` interface +
  ``propagated: PublishPropagatedAncestor[]`` on
  ``PublishNodeResponse``.
- Tests (server): 5 new in ``tests/test_propagation.py``, 3 new
  ``bump_minor`` cases in ``tests/test_md_publish.py``, 3 new
  integration tests in ``tests/test_folder_io.py``.
- Docs: ``SPEC.md`` §Publish — MINOR propagation (new
  subsection); ``PUBLISH.md`` extended trailer schema +
  cross-ref `git log --grep` recipe; ``DECISIONS.md``
  D-2026-05-17-C; ``NEXT_SESSION.md`` Phase 4 → completed,
  Mermaid SVG queue v0.20.0 → v0.21.0, Live Preview decorations
  queue v0.21.0 → v0.22.0.

### Changed

- ``mashbill/folder_io.py::publish_node`` — now MAJOR-bumps the
  target in **every** canvas it appears in (mirror sync; e.g. a
  service node lives in both Services and ServiceDetail), walks
  ancestors, MINOR-bumps each in every canvas it appears in, and
  persists every touched canvas in one pass. Returns a
  ``propagated`` array in the response dict so the client can
  refresh ancestor badges without a separate request.
- ``mashbill/git_store.py::publish_snapshot`` — new optional
  ``propagated: list[tuple[str, str, str]] | None = None``
  parameter; appends one ``Publish-Propagated-Ancestor: <id>
  <from>→<to>`` trailer per ancestor after the 5 existing base
  trailers. Five-trailer commit shape (D-2026-05-16-E)
  preserved for back-compat.
- ``mashbill/api_endpoints.py::node_publish_endpoint`` docstring
  updated; response JSON gained the ``propagated`` key.
- ``mashbill/mcp_tools.py::publish_node_tool`` docstring updated;
  return value gained ``propagated`` key.

### Removed

- The "Phase 4's job" line from ``PUBLISH.md`` §"What publish does
  NOT do". Phase 4 is no longer hypothetical.

## [0.19.0] — 2026-05-17

MD-aware Inspector typed-text editor (stage 1 of 3-stage Obsidian
Live Preview track). Per [D-2026-05-17-B](./docs/DECISIONS.md).
Replaces 19 plain monospace ``<textarea>`` blocks across the
Inspector with a single shared ``MdTextarea`` component backed by
**CodeMirror 6 + ``@codemirror/lang-markdown``**. Headings, lists,
bold, italic, code, links, and blockquotes now render with MD
syntax highlight while the user edits. Raw MD remains the SSOT —
the editor never transforms the value, only re-paints it.

Stages 2 (v0.20.0 mermaid SVG decoration) and 3 (v0.21.0 heading
font-size / list bullet / image embed decorations) build on the
``MdTextarea`` foundation without an editor library swap.

### Added

- ``viewer/src/canvases/inspectors/shared/MdTextarea.tsx`` — **new**
  shared component. ~110 LOC. CodeMirror 6 + markdown extension +
  ``EditorView.lineWrapping`` + history + base theme matching Novel's
  existing slate-300 border / indigo-600 focus chrome. Mounts once,
  syncs external ``value`` prop via replace transactions. Hidden
  ``<textarea>`` mirror keeps RTL ``getByDisplayValue`` queries
  working in the smoke tests.
- ``viewer/package.json`` — direct deps: ``codemirror`` (^6.0.2),
  ``@codemirror/lang-markdown`` (^6.5.0).

### Changed

- ``viewer/src/canvases/inspectors/shared/BodyField.tsx`` —
  ``<textarea>`` → ``<MdTextarea>``.
- ``viewer/src/canvases/inspectors/shared/DoDontFields.tsx`` — 2
  ``<textarea>`` → ``<MdTextarea>``.
- ``viewer/src/canvases/inspectors/service/index.tsx`` — internal
  ``ServiceTextarea`` helper now wraps ``<MdTextarea>``;
  propagates to all 6 service typed-text fields (what /
  value_created / scope / trigger / how / outcome).
- ``viewer/src/canvases/inspectors/service/RuleFields.tsx`` — 2
  ``<textarea>`` → ``<MdTextarea>``.
- ``viewer/src/canvases/inspectors/{mission,core_value,identity,actor,category,metric,step,actor_ref}/index.tsx``
  × 8 — every multi-line typed text ``<textarea>`` → ``<MdTextarea>``.
- Per-inspector ring color (sky/rose/violet/emerald/slate/lime/stone)
  dropped on typed-text fields in favor of a single canonical
  slate→indigo focus theme. Visual simplification per KISS; kind
  colors stay on header chrome (color badge + KIND tag).

### Bundle size

Vendor + viewer index bundle:
- Before (v0.18.3): index 1,257 KB raw / 340 KB gzip.
- After (v0.19.0): index 1,759 KB raw / 515 KB gzip.
- Delta: +502 KB raw / **+175 KB gzip** (within the planned
  150-180 KB gzip budget). Mermaid lazy chunks (cytoscape / katex /
  wardley) unchanged.

### Tests

- ``viewer/tests/inspectors/inspectors.smoke.test.tsx`` — auto-flowed
  via the hidden mirror ``<textarea>`` in MdTextarea (RTL
  ``getByDisplayValue`` finds it). No assertion changes needed.
- viewer: vitest **524/524** green; tsc clean.
- server: pytest 359/359 (unaffected).
- LOC budgets unchanged (BodyField / DoDontFields / per-kind
  inspectors all *smaller* after the swap; MdTextarea is its own
  file).

## [0.18.3] — 2026-05-17

Fixes a viewport-fit race surfaced on reload (D-2026-05-17-A):
loading a Foundation canvas with user-positioned nodes outside the
default 1080×720 box left the viewport stuck on (0, 0), so nodes
appeared "gone" until the user clicked fit-view manually. Root
cause: ``onInit``'s ``fitView`` ran before RF measured node DOM
boxes, so it fit to (0, 0). Replaced with a
``useNodesInitialized`` effect that fits exactly once after
measurement.

The v0.16.18 (D-2026-05-12-T) "fit once on mount, not every
render" intent is preserved — a ``didInitialFitRef`` ref gates
re-fits within the same mount, and ``activeCanvasKey`` remount in
``App.tsx`` still triggers a fresh fit on tab change.

### Changed

- ``viewer/src/canvases/SketchCanvas.tsx`` — moved ``fitView`` out
  of ``onInit`` into a ``useNodesInitialized`` effect; ``onInit``
  now only stores the instance reference.

## [0.18.2] — 2026-05-16

Brings the v0.17.0 Phase 1 *"JSON value = MD-formatted string +
monospace MD textarea + `body` field"* pattern from Foundation 3
kinds (mission / core_value / identity) to the **7 other
publish-eligible kinds** (actor / service / category / metric /
step / rule / content). v0.18.0 had shipped publish before the
input parity, so 7 of 10 publish-eligible kinds had plain-text
input while emitting MD on publish — inconsistent. v0.18.2 closes
the gap.

Also lifts `actor_ref`'s `gives` / `receives` textarea to
monospace MD for input consistency — ref is still
publish-ineligible and has no `body` (ref = relation tool, not
own-SSOT node). 4 ref kinds otherwise unchanged.

Per [D-2026-05-16-F](./docs/DECISIONS.md). Documents 15-kind H2
section reference in [`docs/PUBLISH.md`](./docs/PUBLISH.md).

### Added

- ``mashbill/models.py`` — ``body: str = ""`` on 7 kind classes
  (ActorNode / ServiceNode / CategoryNode / MetricNode / StepNode
  / RuleNode / ContentNode). ref 4 + ProjectNode unchanged.
- ``viewer/src/domain/{Actor,Service,Category,Metric,Step,Rule,
  Content}.ts`` × 7 — ``body: string`` through Json interface +
  class field + constructor + fromJson + toJson, mirroring the
  Foundation pattern.
- 7 per-kind inspectors (`actor` / `service` / `category` /
  `metric` / `step` / `rule` / `content`) — monospace MD textarea
  on every typed text field + ``<BodyField>`` + ``hideDetailsSection``.
- ``docs/PUBLISH.md`` — per-kind H2 section reference table for
  all 15 kinds (Foundation 3 + Actors/Services/composition 7 +
  publish-ineligible 5) + ref-as-relation-tool note.
- ``docs/SPEC.md`` §Publish — new "Typed text + body fields
  (v0.18.2+)" subsection.
- ``docs/DECISIONS.md`` — D-2026-05-16-F entry.
- ``docs/NEXT_SESSION.md`` — v0.18.2 archived; "cross-kind ref
  typed-text symmetry" follow-up filed (actor_ref 의 `gives`/
  `receives` 비대칭 검토).

### Changed

- ``viewer/src/canvases/inspectors/service/RuleFields.tsx`` —
  `policy` / `enforcement` textareas lifted to monospace MD.
- ``viewer/src/canvases/inspectors/service/ContentFields.tsx`` —
  `format` input gets `font-mono` class for visual consistency
  (remains single-line `<input>`).
- ``viewer/src/canvases/inspectors/actor_ref/index.tsx`` —
  `gives` / `receives` textareas lifted to monospace MD.

## [0.18.1] — 2026-05-16

Docs-only patch. Pins the "tree-in-forest" AI-context architecture
framing surfaced in the 2026-05-16 ideation session
(D-2026-05-16-D) and queues it as ROADMAP §D for future
implementation. No code changes.

### Added

- `docs/ROADMAP.md` §D — **Forest-anchored AI context (graph-RAG-lite
  + verification loop)**. Adds a queued item alongside A
  (isomorphic-git), B (work-item layer), C (repo split). Phased plan
  (Phase 1 Novel-internal `context_envelope` MCP tool + skill rule +
  interview pattern strengthening; Phase 2 post-Distill port for
  transcript crystallization; Phase 3 post-Evonest port for output
  consistency verification). Design red-team not yet run; checklist
  for what to surface before Phase 1 starts (envelope token budget,
  call-skip detection, staleness vs canvas updates).
- `docs/DECISIONS.md` D-2026-05-16-D — **AI-context architecture:
  "tree-in-forest" 3-layer framing**. Records the framing that
  splits the problem into (1) data structural connection — free
  via Novel's typed user-authored graph, (2) input-side call
  enforcement — small effort, and (3) output-side verification —
  large, downstream of Distill / Evonest ports. Includes the i18n
  global-service regression as the concrete failure case proving
  Layer 2 is the bottleneck (Layer 1 fully built + Layer 3 partial
  static guard still fails to stop AI hardcoding user-facing
  strings). Lists 3 rejected alternatives (full GraphRAG library
  import / single-feature bundle / defer until Distill+Evonest
  ports). Approved by user 2026-05-16.

### Changed

- None.

### Removed

- None.

### Fixed

- None.

## [0.18.0] — 2026-05-16

Phase 3 of the JSON SSOT migration (D-2026-05-16-E). The visible
surface of per-node publishing lands. Each eligible node now has a
**📤 publish** button in its Inspector header that bumps the node's
``version`` MAJOR component (``v1.0`` → ``v2.0``), emits a uniform
per-node MD file under ``<canvas>/published/{kind}-{slug}-{version}.md``,
and records a git commit with machine-readable ``Publish-*:``
trailers. The trailers are the **Phase 4 contract** (MINOR
propagation parses them via ``git interpret-trailers`` next phase).
A **version badge** in the Inspector header's left cluster shows the
node's current version next to its KIND tag.

Eligibility per D-2026-05-16-E §1.2: the project anchor, ``is_root``
nodes (Actors / Services root anchors), and the four ``*_ref`` alias
kinds are excluded — alias nodes publish via their referent.

Idempotence: always-bump. Two publishes = two distinct MD files +
two distinct commits. The confirm dialog is the human debounce; its
text explicitly names this contract so users from npm/cargo
ecosystems don't carry the wrong mental model.

Audit recovery: no Unpublish button this phase. Recovery procedure
is documented in ``docs/PUBLISH.md`` (manual ``git revert HEAD``
plus optional MD cleanup). The v0.18.x follow-up automating this is
queued in ``docs/NEXT_SESSION.md``.

The PSPEC §6 "canvas auto-commit" line was clarified in
**v0.17.4** ahead of this commit to avoid bundling a cross-cutting
docs fix into the feature commit (Novel CLAUDE.md anti-pattern).

### Added

- ``mashbill/md_publish.py`` — **new module**. ``render_node_md``
  emits the uniform "YAML frontmatter (7 keys) + per-typed-field H2
  sections" MD template across all 15 kinds. ``can_publish`` is the
  eligibility helper; ``bump_major`` is the version-string
  arithmetic.
- ``mashbill/folder_io.py::publish_node`` — reads the canvas,
  bumps the node's ``version``, writes the published MD, writes the
  bumped canvas, and creates the git commit via
  ``publish_snapshot``. Raises ``PublishNotEligibleError`` (409) on
  ineligible kinds; ``KeyError`` (404) on missing node.
- ``mashbill/git_store.py::publish_snapshot`` — parallel to
  ``tag_snapshot``. ``git add -A`` + ``git commit`` (no
  ``--allow-empty``, no tag). Subject is human-readable; 5 trailers
  encode the machine contract: ``Publish-Node-Id`` /
  ``Publish-Kind`` / ``Publish-Canvas`` / ``Publish-Version-From``
  / ``Publish-Version-To``.
- ``mashbill/api_endpoints.py::node_publish_endpoint`` →
  ``POST /api/projects/{id}/canvases/{kind}/nodes/{node_id}/publish``
  (optional ``service_id`` query param). Returns 201
  ``{node_id, from_version, to_version, md_path, sha}``.
- ``mashbill/mcp_tools.py::publish_node_tool`` — MCP wrapper.
- ``viewer/src/api.ts::publishNode`` — viewer client function.
- ``viewer/src/domain/publishEligibility.ts`` — **new helper**.
  Server-mirroring ``canPublish(node)`` predicate; drives both the
  Inspector button visibility and the no-god-import contract for
  publish gating.
- ``viewer/src/canvases/inspectors/BaseInspector.tsx`` — version
  badge in left cluster (no i18n — code value); ``📤`` publish
  button in right cluster between width-toggle and delete, gated on
  ``canPublish`` and ``onPublishNode != null``; ``window.confirm``
  dialog with ``inspector.confirmPublish`` body naming the MAJOR
  bump explicitly.
- ``viewer/src/hooks/useProject.ts::publishNodeAction`` — wraps
  the HTTP call + re-fetches all canvases so the Inspector's
  ``node.version`` reflects the bump on next paint.
- ``viewer/src/canvases/SketchCanvas.tsx`` — new ``onPublishNode``
  prop threaded through SketchInspectorBindings.
- ``viewer/src/canvases/sketch/SketchInspectorBindings.tsx`` —
  forwards ``onPublishNode`` to ``KindInspector``.
- ``viewer/src/canvases/inspectors/types.ts::KindInspectorProps``
  — optional ``onPublishNode`` field; auto-flows to every per-kind
  inspector via the ``{...props}`` spread pattern (no per-file
  thread).
- ``viewer/src/App.tsx`` — wires ``handlePublishNode`` from
  ``useProject`` to both the main Canvas and the ServiceDetail
  modal Canvas.
- ``viewer/src/i18n/locales/{en,ko}.json`` — 4 new keys:
  ``inspector.publish`` / ``inspector.publishShort`` /
  ``inspector.publishHint`` / ``inspector.confirmPublish`` (with
  ``{kind}`` / ``{label}`` / ``{fromVersion}`` / ``{toVersion}``
  placeholders).
- ``tests/test_md_publish.py`` — **new test file**. 24 cases:
  ``bump_major`` regex + invalid rejects (7), ``can_publish``
  parametric per kind (10+), uniform frontmatter shape (10),
  per-typed-field H2 sections, non-string field inline-YAML
  round-trip, empty-field heading preservation.
- ``tests/test_folder_io.py`` — 8 new publish tests (MD path,
  version bump, persisted version, distinct-files-per-publish,
  rejects project anchor / root actor / unknown node, git commit
  with trailers).
- ``tests/test_api_endpoints.py`` — 3 new endpoint tests (200 round-trip,
  404 on unknown node, 409 on ineligible root).
- ``viewer/tests/domain/publishEligibility.test.ts`` — **new test
  file**. 15 parametric cases mirroring the server eligibility
  table.
- ``plot/docs/SPEC.md`` — **new section** ``## Publish (v0.18.0)``.
- ``plot/docs/PUBLISH.md`` — **new doc**. MD format reference,
  ``published/`` semantics, manual recovery procedure.
- ``pyproject.toml`` — ``pyyaml>=6.0`` added as a direct dep (was
  transitive only).

### Changed

- ``viewer/tests/structural-guards.test.tsx`` — LOC ceilings raised
  for the two chrome files that absorbed Phase 3 responsibilities:
  - ``canvases/SketchCanvas.tsx``: 420 → 440 (one-time, +20 for
    publish-prop threading; no-growth henceforth).
  - ``canvases/inspectors/BaseInspector.tsx``: 220 → 270 (publish
    button + version badge + confirm dialog handler).
  Novel CLAUDE.md Gate 2 LOC table updated to match.
- ``plot/docs/NEXT_SESSION.md`` — Phase 3 entry → Completed;
  surfaced Phase 4 (MINOR propagation) as new Active queue head;
  surfaced v0.18.x ``Unpublish button`` follow-up.
- ``plot/docs/DECISIONS.md`` — D-2026-05-16-E entry.

## [0.17.4] — 2026-05-16

Docs-only PSPEC §6 clarifier. Lands ahead of v0.18.0 Phase 3 so
that the cross-cutting docs fix is **not bundled** into the
feature commit (per Novel CLAUDE.md anti-pattern: "Bundling a
cross-cutting visual change with a feature change in one commit",
v0.13.10 cursor saga precedent).

### Changed

- ``plot/docs/PRODUCT_SPEC.md`` §6 — annotated the "Edit a canvas
  → Auto-commit" row as **aspirational**: it lands with the
  isomorphic-git in-viewer integration (ROADMAP §"v0.17+" item A).
  Through v0.17 / v0.18 the canvas stays uncommitted between
  explicit user actions — only **publish** (v0.18.0+) and
  **session-tag** (v0.16+) trigger commits. Added the two
  explicit-action rows to the table and a one-paragraph
  reality-vs-aspiration note + an inline note on the
  ``isomorphic-git`` line clarifying subprocess git is the current
  implementation.

## [0.17.3] — 2026-05-16

Docs-only cleanup. Archives the lower-priority "잔여 silent state"
queue entry (D-2026-05-13-I) — both root issues have been closed
for some time: the 422 PATCH storm by v0.16.37
([D-2026-05-13-M](./docs/DECISIONS.md)) and the orphan-edge
cleanup by v0.16.38 ([D-2026-05-13-N](./docs/DECISIONS.md)). A
hands-on smoke run via chrome-devtools MCP on test-v010 confirmed
the live state today: 12 fetch/xhr requests, 0 at HTTP 422,
0 console errors, 0 warnings. Storage inventory across the four
``proj-monmft3s`` canvases showed zero dangling edges and zero
None-endpoint edges. NEXT_SESSION.md is now in sync with reality.

### Changed

- ``plot/docs/NEXT_SESSION.md`` — moved the "잔여 silent state"
  block from **Active queue** to the **Completed 2026-05-16**
  section; trigger phrases preserved verbatim for future
  regression re-surface; references to D-2026-05-13-M / -N + the
  v0.17.2 same-day verification recorded inline.

## [0.17.2] — 2026-05-16

Phase 2 of the JSON SSOT migration (D-2026-05-16-C). Adds a
per-node ``version`` field to ``BaseNodeFields`` (server) +
``BaseFields`` / ``BaseFieldsJson`` (viewer), defaulting to
``"v1.0"``. The field is the data foundation Phases 3–5 read from
and write to: Phase 3 increments it on explicit "Publish" (MAJOR
bump), Phase 4 propagates the bump up the ancestor chain (MINOR
bumps), Phase 5+ extends to folder-hierarchy publish semantics. The
format is locked by a regex contract (``^v\d+\.\d+$``) on both
sides; a three-component version (``"v1.0.0"``) fails loudly until a
fresh ``D-`` entry widens the contract. **No UI surface in this
phase** — no badge, no button, no visible difference. Pre-v0.17.2
canvases auto-fill ``"v1.0"`` on read; first write after open
serialises the new key.

### Added

- ``mashbill/models.py::BaseNodeFields.version`` — ``str = "v1.0"``
  default + ``_version_is_valid`` model validator enforcing
  ``^v\d+\.\d+$``. Inherited by all 15 per-kind classes via the
  discriminated union.
- ``viewer/src/domain/BaseFields.ts::asVersionString`` —
  ``parseBaseFields`` helper mirroring the server regex; defaults to
  ``"v1.0"`` on missing key, throws ``DomainParseError`` on invalid.
- ``viewer/src/domain/BaseFields.ts`` — ``version: string`` added to
  both ``BaseFieldsJson`` (wire) and ``BaseFields`` (in-memory)
  interfaces.
- 15 per-kind entity classes
  (``viewer/src/domain/{Actor,ActorRef,Category,Content,CoreValue,
  Identity,IdentityRef,Metric,Mission,MissionRef,Project,Rule,
  Service,Step,ValueRef}.ts``) — ``readonly version!: string;`` on
  the class body + ``version: this.version,`` in ``toJson()``.
- ``tests/test_node_models.py`` — 4 new tests covering default,
  valid regex matches, invalid rejections, and per-kind round-trip.
- ``viewer/tests/domain/base-fields.test.ts`` — 4 new tests
  covering default fill, valid versions, invalid rejections, and
  non-string rejection.

### Changed

- ``tests/test_schema_parity.py::_EXPECTED_BASE_FIELDS`` — added
  ``"version"`` so the 15-kind parametric parity test auto-asserts
  Pydantic ↔ TS interface agreement on the new field.

## [0.17.1] — 2026-05-16

Inspector UX polish (D-2026-05-16-B): clicking the synthetic project
anchor now closes any currently-open Inspector. Previously the
anchor branch in ``useInspectorRouting.onNodeClick`` was an
early-return no-op (a v0.13 leftover that read "anchor has no
Inspector"), which left the previously-selected node's content
visible on screen even after the user moved focus to the anchor.
Anchor click now reads as a deselect — the same effect as clicking
the empty pane. No other behaviour changes.

### Changed

- ``viewer/src/canvases/sketch/useInspectorRouting.ts::onNodeClick``
  — anchor branch sets ``inspectorNodeId`` to ``null`` and returns,
  instead of the previous no-op early return.

### Added

- ``viewer/tests/anchor-click-closes-inspector.test.tsx`` —
  regression guard. Two cases: anchor click while an Inspector is
  open closes it; anchor click while no Inspector is open stays
  closed (idempotent no-op).

## [0.17.0] — 2026-05-16

Phase 1 of the JSON SSOT migration (D-2026-05-16-A). JSON is now
the sole source of truth for Foundation typed-text fields on
mission / core_value / identity kinds; every field value
(``what_we_do`` / ``why`` / ``direction`` / ``definition`` / ``do``
/ ``dont`` / ``description`` + new ``body``) is an MD-formatted
string carried inline in the wire shape. The v0.13 co-equal JSON+MD
storage is retired: on first read of any pre-v0.17 project, the
read-side migrator ``_absorb_md_typed_text_into_json`` ingests the
typed H2 sections + post-``---`` free prose into the JSON node,
clears ``details_path``, and moves the source MD to
``foundation/_legacy/{kind}-{slug}.md`` for safekeeping. The
viewer's MD-editor surface (DetailsSection) is hidden for these 3
kinds — JSON SSOT means no per-file MD editing for typed-text
content. Per-node MD files become publish-output only, landing in
Phase 3.

### Added

- ``mashbill/folder_io.py::_absorb_md_typed_text_into_json`` — one-shot
  read-side migrator with 4-scenario conflict policy + ``_legacy/``
  quarantine + collision-suffix fallback.
- ``mashbill/folder_io.py::_legacy_md_dir`` — canonical
  ``foundation/_legacy/`` resolver.
- ``mashbill/models.py::FOUNDATION_MD_FIELDS`` — all-MD-syntax-fields
  map per kind (typed + body); SSOT for the viewer and Phase 3
  publish.
- ``mashbill/models.py::MissionNode/CoreValueNode/IdentityNode``
  ``body: str = ""`` field — JSON SSOT home for the legacy MD's
  post-``---`` free prose.
- ``viewer/src/canvases/inspectors/shared/BodyField.tsx`` — shared
  MD-aware ``body`` editor surface (monospace, newline-preserving).
- ``viewer/src/canvases/inspectors/BaseInspector.tsx``
  ``hideDetailsSection?: boolean`` prop — gates the legacy MD editor
  surface per kind.
- ``viewer/src/i18n/locales/{en,ko}.json`` — ``inspector.field.body``
  / ``inspector.fieldHint.body``.
- ``tests/test_folder_io.py`` — 7 new
  ``test_absorb_md_typed_text_into_json_*`` cases covering basic
  absorption, conflict policies, idempotency, MD-syntax
  preservation, free-prose→body mapping, no-md-file cleanup, and
  slug-collision suffixing.

### Changed

- ``mashbill/folder_io.py::read_canvas`` — Foundation branch swaps
  the old 2-call eviction chain for the single
  ``_absorb_md_typed_text_into_json``.
- ``mashbill/folder_io.py::write_canvas`` — Foundation branch drops
  the ``_split_foundation_typed_text_to_md`` call; Pydantic now
  serialises every typed + body field directly to JSON.
- ``mashbill/folder_io.py::collect_foundation_md_warnings`` —
  returns ``{}`` unconditionally (no canonical MD files survive
  absorption); kept as a stable callable for backward API
  compatibility.
- ``viewer/src/canvases/inspectors/{mission,core_value,identity}/index.tsx``
  — pass ``hideDetailsSection``, render the new ``body`` field,
  switch every typed-text textarea to ``font-mono whitespace-pre-wrap``
  so users see and edit the raw MD-syntax string.
- ``viewer/src/canvases/inspectors/shared/DoDontFields.tsx`` —
  monospace + newline-preserving textareas (``do`` / ``dont`` values
  are MD-syntax strings).
- ``viewer/src/domain/{Mission,CoreValue,Identity}.ts`` — add
  ``body`` field to the JSON shape, class, ``fromJson``, ``toJson``.
- ``tests/test_api_endpoints.py::test_file_put_does_not_touch_canvas``
  — assertion updated to reflect the v0.17 invariant that
  Foundation typed-text kinds carry no ``details_path`` after
  absorption.
- ``plot/docs/DECISIONS.md`` — new ``D-2026-05-16-A`` entry pinning
  the Phase 1 implementation decisions (unconditional ``details_path``
  clear; ``_legacy/`` quarantine; ``body`` as another MD-syntax
  field; ``hideDetailsSection``).
- ``plot/docs/PRODUCT_SPEC.md`` §15 #2 — Phase 1 status updated from
  "queued" to "shipped 2026-05-16"; Phase 2-6 remain queued.
- ``plot/docs/NEXT_SESSION.md`` — Phase 1 active-queue entry
  archived; Phase 2 (``version: str = "v1.0"`` in BaseFields) is
  the next trigger.

### Removed

- ``mashbill/folder_io.py::_evict_typed_text_to_md``,
  ``_merge_md_typed_text_into_nodes``,
  ``_split_foundation_typed_text_to_md`` — the v0.13
  eviction-and-rehydration trio. Replaced by the single read-side
  absorber.

## [0.16.40] — 2026-05-13

Phase 0 of the JSON SSOT + per-node MD + per-node versioning +
folder-hierarchy migration. User stated 7 principles in plain text
and approved the 6-phase ship sequence; this commit pins the
principles as docs only — no code changes.

The 7 principles supersede D-2026-05-13-J point #4 (the original
"per-canvas MD" wording) with "per-node MD file", and add three
new principles (per-node versioning, vMAJOR.MINOR rules, folder
hierarchy). Phase 1 (MD → JSON absorption) lands in the next
session under the trigger ``Phase 1`` / ``JSON SSOT 구현`` /
``MD 흡수``. (D-2026-05-13-O)

### Changed

- ``plot/docs/DECISIONS.md`` — D-2026-05-13-O entry pinning the
  7 principles + 6-phase ship sequence + D-J supersede chain.
- ``plot/docs/PRODUCT_SPEC.md`` §15 #2 — replace 4-point block
  with 7-principle list + cross-reference to D-2026-05-13-O.
- ``plot/docs/NEXT_SESSION.md`` — Active queue ``JSON SSOT 논의``
  entry transitions to ``Phase 1 — JSON SSOT 구현 (MD 흡수)`` with
  the 6-phase sequence referenced.

### Out of scope (this session)

- All Phase 1-6 code changes. Each subsequent phase opens its own
  plan-mode + user approval cycle.

## [0.16.39] — 2026-05-13

Pin user hands-on confirmation of v0.16.38 anchor-edge cleanup
whitelist fix (D-2026-05-13-N). After MCP HTTP server restart with
the cleanup-side ``PROJECT_ANCHOR_ID`` whitelist, user verified in
real Chrome: *"이제 동작하네"* — nodes no longer disappear on
reload; anchor edges persist across repeated hard reloads.

D-2026-05-13-N approval transitions Pending → Accepted.

### Changed

- ``plot/docs/DECISIONS.md`` — D-2026-05-13-N approval Pending →
  Accepted (hands-on verified by user, 2026-05-13).

### D-2026-05-13-I closure status (final)

- 422 storm + e_-prefixed unknown ids — **resolved** in
  D-2026-05-13-M (v0.16.37).
- Cleanup-side anchor-edge strip → refetch storm — **resolved** in
  D-2026-05-13-N (v0.16.38, this entry's prerequisite).
- ``services/canvas.json`` ``e_mopntgek_4y74 | None → None`` orphan
  edge — **still open**. Separate storage-cleanup pass needed.
  Filed: NEXT_SESSION.md ``잔여 silent state`` (now scoped to the
  orphan edge only).

## [0.16.38] — 2026-05-13

User reported v0.16.37 fix incomplete: *"안고쳐짐. 새로고침을 하다보면
캔버스에 노드들이 사라지는 이슈가 있네요"*. Investigation revealed a
**second anchor-id whitelist gap** in the same server file —
``_evict_legacy_project_anchor``'s defensive orphan-edge cleanup
(``folder_io.py:437-443``) used the same ``{n.id for n in nodes}``
pattern as the Pydantic validator fixed in v0.16.37, which means
anchor edges were getting stripped on read, the storage write
triggered the watcher, the watcher fired ``project_changed``, the
viewer refetched, the cleanup stripped again — the v0.16.34-shape
loop with anchor edges as the trigger payload. The 200 OK on PUT
masked the loop because every PUT raced with the next cleanup.

Fix: add the same ``PROJECT_ANCHOR_ID`` whitelist to the defensive
cleanup. Same one-character philosophical change as v0.16.37 (Phase 1
agent: *"two layers of defence broken in the same place"*).
(D-2026-05-13-N)

### Fixed

- ``plot/mashbill/folder_io.py::_evict_legacy_project_anchor``
  defensive orphan-edge cleanup — ``node_ids`` set now includes
  ``PROJECT_ANCHOR_ID``, so anchor edges survive the cleanup
  instead of being silently rewritten on every read.

### Added

- ``plot/tests/test_folder_io.py``:
  - ``test_read_canvas_preserves_anchor_edges_across_repeated_reads``
    — writes a canvas with two anchor edges (both directions),
    reads it three times, asserts edges survive + canvas.json mtime
    does not advance (write would advance it — the storm trigger).
  - ``test_orphan_non_anchor_edges_still_stripped`` — backward-compat
    pin: edges referencing truly missing nodes (not the anchor) are
    still stripped on read.

### Verification

- mashbill pytest — 283 / 283 (281 → 283, +2 regression).
- mashbill mypy — clean.
- mashbill ruff — clean (after I001 import-sort fix).
- viewer vitest — 486 / 486 (no regression).
- kill-switch — 11 / 11.

### Hands-on (Gate 3 — pending after MCP HTTP restart)

User to verify in real Chrome:
- Anchor edges persist across repeated hard reloads (the
  v0.16.37 fix already made PUT succeed; this fix makes the
  subsequent reads stable).
- Nodes do not disappear after reload.

## [0.16.37] — 2026-05-13

Fix anchor-edge 422 reject. User reported *"왜 새로 고침하면 연결선이
사라지죠?"* — user-drawn edges between the synthetic project anchor
and other nodes silently failed to persist.

Root cause: server-side Pydantic validator
``CanvasDoc._edges_reference_nodes`` (``models.py:538-545``) treated
``"__project_anchor__"`` as an unknown node id and rejected every
PATCH carrying an anchor edge with 422 Unprocessable Entity. The
viewer's optimistic update masked the failure (edge appears on
screen) until reload (which loses optimistic state → edge gone from
both client and server).

Compounding bug: the validator's error message reported the *edge
ids* of the dangling edges as if they were missing node ids, which
sent the D-2026-05-13-I diagnosis down a wrong path (e_-prefixed
ids that were never node ids to begin with).

Spec context: D-2026-05-04-B mandates *"User may draw edges from /
to the anchor like any other node"* — anchor edges are a
spec-supported feature, not an edge case to filter out.

(D-2026-05-13-M — closes the 422-storm half of D-2026-05-13-I; the
None→None services orphan edge remains separately tracked.)

### Fixed

- ``plot/mashbill/models.py::CanvasDoc._edges_reference_nodes`` —
  whitelist the new module-level ``PROJECT_ANCHOR_ID`` constant
  (mirrors the viewer's ``constants.ts``) so user-drawn anchor
  edges validate cleanly.
- Same validator — error message now reports the actual *missing
  endpoint ids* (sorted), not the *edge ids* of the dangling edges.
  Compatibility: callers that pattern-matched on edge-id text
  break, but no production code did (all D-2026-05-13-I
  speculation about ``e_``-prefixed ids was a symptom of this bug).

### Added

- ``plot/mashbill/models.py`` — ``PROJECT_ANCHOR_ID`` module-level
  constant (mirrors ``viewer/src/canvases/sketch/constants.ts``).
- ``plot/tests/test_canvas_doc.py`` — 5 regression tests:
  - anchor → user-node edge accepted (both directions).
  - error message reports missing endpoint, not edge id.
  - multi-edge case: sorted distinct missing endpoints, no edge ids.
  - one-anchor-one-ghost case: only the ghost surfaces in the
    error.

### Verification

- mashbill pytest — 281 / 281 (276 → 281, +5 regression).
- mashbill mypy — clean.
- mashbill ruff — clean.
- viewer vitest — 486 / 486 (no regression; schema-parity unaffected).
- kill-switch — 11 / 11.

### Hands-on (Gate 3 — pending after MCP HTTP server restart)

User to verify in real Chrome:
- Draw an edge between the project anchor and a user node.
- Server returns 200 on save (no 422 in DevTools console).
- Hard reload — the edge is still there.
- Multiple anchor edges, both directions — all persist.

## [0.16.36] — 2026-05-13

Re-introduce auto-layout as Foundation-only opt-in feature with a
4-layer isolation contract. User direct request: *"혹시 자동 정렬을
넣을 수 있을까요? ... 다른 곳에 영향이 안 가게 만들어야합니다."*
Closes the D-2026-05-10-G re-introduction policy with a fresh
decision (D-2026-05-13-L) that satisfies all four conditions:
fresh D-id, real-user workflow, cost/benefit vs D-G, explicit user
approval before code.

The v0.13.9 directional-tree algorithm
(`computeAutoLayout`, BFS spanning tree + handle-aware placement
+ Reingold-Tilford overlap avoidance, deterministic) is restored
unchanged — pure function from commit 75330c7, no type changes
needed (compatible with the v0.15+ discriminated union via
`BaseFields`).

### Added

- `viewer/src/canvases/sketch/autoLayout.ts` — restored v0.13.9
  pure function (297 LOC, no React import).
- `viewer/src/canvases/sketch/useAutoLayout.ts` — React hook
  wrapping `computeAutoLayout` (43 LOC).
- `viewer/tests/autoLayout.test.ts` — 13 unit tests restored.
- `viewer/tests/auto-layout-isolation.test.tsx` — 6 isolation
  regression tests:
  - FoundationCanvas renders the button (opt-in present).
  - ActorsCanvas / ServicesCanvas / ServiceDetailCanvas: button
    must NOT exist (isolation contract).
  - Clicking the button calls `onDocChange` exactly once
    (one-shot apply contract).
  - Auto-layout touches positions only (kind / label / typed-text
    byte-identical before vs after).

### Changed

- `viewer/src/canvases/SketchCanvas.tsx` — added optional
  `enableAutoLayout?: boolean` prop (default `false`). When
  true, the `<Controls>` panel renders an extra ⊞ button wired
  to `useAutoLayout`. SketchCanvas LOC 412 → 419 (within 420
  ceiling).
- `viewer/src/canvases/FoundationCanvas.tsx` — passes
  `enableAutoLayout={true}` (the only wrapper that does so).
- `viewer/tests/SketchCanvas.regression.test.tsx` — the
  "no Auto layout button" assertion is preserved but the comment
  is rewritten to reflect the new "default-off; FoundationCanvas
  wrapper opts in" semantics.
- `docs/SPEC.md` §Auto-layout — full rewrite. "Removed (again)"
  → "Re-introduced v0.16.36, Foundation only, opt-in" + the
  4-layer isolation contract + 5-cycle history block.
- `CLAUDE.md` rule 6 — *"No auto-layout"* →
  *"Auto-layout is Foundation-only opt-in. … never opt other
  wrappers in without a fresh D- entry that updates that test."*
- `docs/DECISIONS.md` — D-2026-05-13-L entry pinning vision +
  isolation contract.

### Design (one-shot apply + Cmd+Z, chose over preview/apply)

The user's *"다른 곳에 영향 안 가게"* constraint is satisfied by
the wrapper-opt-in pattern; the user-consent guarantee is the
explicit button click + the undo stack as the safety net. A
preview/apply state machine would add 15+ LOC and a separate
preview-state surface for no additional isolation gain. The
plan's preview/apply pattern is preserved as a deferred option
in the D-2026-05-13-L body for future consideration if hands-on
shows the one-shot UX is too aggressive.

### Verification

- viewer vitest — 486 / 486 (461 → 486, +25 new tests).
- viewer tsc — clean.
- structural-guards — SketchCanvas 419 / 420 ceiling.
- mashbill pre-commit gate (kill-switch) — 11 / 11.

### Hands-on (Gate 3 — pending user verification)

User to verify in real Chrome after viewer hot-reload:
- Foundation canvas: `<Controls>` shows the ⊞ Auto-layout button.
- Clicking it rearranges nodes deterministically; Cmd+Z reverts.
- Actors / Services / ServiceDetail canvases: no button (drag /
  pan / zoom / cursor unchanged).

## [0.16.35] — 2026-05-13

Pin user hands-on confirmation of v0.16.34 page-load refetch storm
fix (D-2026-05-13-K). After restart of the MCP HTTP server with the
new ``upgrade_foundation_canvas_if_needed`` step-4 guard, user
verified in real Chrome: *"이제 됐습니다"* — Foundation nodes
appear and stay visible; no refetch storm in server log.
D-2026-05-13-K approval transitions Pending → Accepted.

### Changed

- ``plot/docs/DECISIONS.md`` — D-2026-05-13-K approval status
  ``Pending → Accepted (hands-on verified by user, 2026-05-13)``.

## [0.16.34] — 2026-05-13

Fix page-load refetch storm. After user reported "Foundation nodes
appear briefly then disappear; need to reload to see them again",
server log showed the GET 3-call set (`/projects` →
`/projects/{id}` → `/projects/{id}/canvases/foundation`) repeating
dozens of times per page load — an infinite refetch loop.

Root cause: ``upgrade_foundation_canvas_if_needed`` step 4
(``migrate.py:834``) — a pre-v0.13 migration that synthesises a
``kind=project`` anchor node when ``canvas.json`` has none — fires
on *every* read for v0.13+ projects. The synthesised node is then
immediately removed by ``_evict_legacy_project_anchor``
(``folder_io.py:478``) on the same read because v0.13 Phase 0
moved the anchor to ``ProjectDoc.anchors``. Both functions write
the file, the watcher fires, the broadcast triggers a viewer
refetch, the next read repeats the cycle.

The two functions are running in opposing directions every read
because the v0.13 Phase 0 migration left step 4 in place without
gating it on the new anchor location.

Fix: guard step 4 on ``ProjectDoc.anchors[canvas_kind]``. When
``project.json`` already carries an anchor for foundation, step 4
short-circuits — no node synthesis, no write, no watcher fire.
Pre-v0.13 projects (no ``anchors`` field) still get the original
synthesis behaviour, preserving backward compatibility.
(D-2026-05-13-K)

### Fixed

- ``plot/mashbill/migrate.py:upgrade_foundation_canvas_if_needed``
  step 4 — added ``_project_doc_has_anchor`` guard so the legacy
  pre-v0.13 anchor synthesis no-ops when v0.13 Phase 0 has already
  migrated the anchor to ``ProjectDoc.anchors``.

### Added

- ``plot/tests/test_migrate.py`` — two regression tests:
  - ``test_upgrade_foundation_is_idempotent_when_anchor_in_project_doc``
    pins the new guard (no write on idempotent re-call when the
    anchor lives in project.json).
  - ``test_upgrade_foundation_still_synthesises_anchor_for_pre_v013_project``
    pins backward compat — pre-v0.13 projects still get synthesis.

### Verification

- mashbill pytest — 276 / 276 (274 → 276, +2 new tests).
- mashbill mypy — clean.
- mashbill ruff — clean.
- viewer tsc — clean.
- kill-switch (pre_commit_gate) — 11 / 11.

### Hands-on (Gate 3 — pending user verification)

User to verify in real Chrome after MCP HTTP server restart:
- page hard reload (Cmd+Shift+R)
- server log: GET 3-call set fires *once* on page load + idle
  silence afterward (no storm).
- Foundation nodes appear and stay visible.
- No console 422 storm.

## [0.16.33] — 2026-05-13

Vision pin for PRODUCT_SPEC §15 #2 Phase 2 (D-2026-05-12-A
deferral) reopening. User pinned a 4-point design vision during
Foundation hands-on testing:

1. JSON = SSOT (co-equal storage abolished).
2. JSON value = MD-formatted string (typed-text fields inside
   JSON, viewer edits via MD editor).
3. MD extraction = explicit button (no auto-sync).
4. Extraction unit = canvas (per-node MD files abolished, single
   MD file per canvas).

User direction 2026-05-13: *"이건 내일 논의해봅시다"* — today
ships vision pin only (docs); detail discussion (editor UX /
line-break handling / per-canvas layout / migration path / button
placement / idempotence / regression guard) and implementation
deferred to next session under the ``JSON SSOT 논의`` trigger.
(D-2026-05-13-J)

### Changed

- ``plot/docs/PRODUCT_SPEC.md`` §15 #2 — 4-point vision inlined;
  status transitioned from "deferred" to "in-discussion 2026-05-13".
- ``plot/docs/DECISIONS.md`` — D-2026-05-13-J entry (Pending —
  vision locked, detail decisions deferred to next session).
- ``plot/docs/NEXT_SESSION.md`` — new ``JSON SSOT 논의`` Active
  queue entry at the top, with the 7 open detail questions.

### Out of scope

- No code changes (no folder_io / models / api_endpoints / viewer
  edits). Phase 2 implementation deferred to next session.

## [0.16.32] — 2026-05-13

End-of-session bookkeeping. Pin user hands-on confirmation of
v0.16.24 anchor visual restoration + RF interaction working
correctly (D-2026-05-13-H). File two silent state inconsistencies
surfaced by automated page probe as a new lower-priority NEXT_SESSION
queue entry (D-2026-05-13-I): (1) console 422 storm with
``e_``-prefixed unknown node ids, (2) ``services/canvas.json`` orphan
edge with ``None`` endpoints. User interaction confirmed working —
neither of these surface visibly in the user's session, but both are
real data-integrity issues that should be fixed before next major
release.

### Changed

- ``plot/docs/NEXT_SESSION.md`` — RF 움직임 entry archived to
  Completed; new `잔여 silent state` entry added at top of Active
  queue for the 422 storm + orphan edge.
- ``plot/docs/DECISIONS.md`` — D-2026-05-13-H (hands-on confirm)
  and D-2026-05-13-I (silent state filing) entries.

## [0.16.31] — 2026-05-13

Skill classification correction. Novel's plugin-skill directory
``plot/skills/`` is meant for **end-user** skills that trigger in
the *consumer's* project after installing the mashbill plugin. Seven
of the eight skills there were actually **dev-facing** — they
trigger during Novel's *own* development and have no meaning to a
plugin consumer. Moving them to the monorepo-level
``noory-ai/.claude/skills/`` aligns the boundary: the plugin
manifest exposes only what a consumer actually needs; the dev-tool
procedures live in the monorepo's Claude Code workspace where they
trigger when working *on* Novel. (D-2026-05-13-G)

### Removed (moved out of plot/skills/)

The following moved to ``noory-ai/.claude/skills/`` via
``git mv`` (audit-trail preserved):

- ``plot-entity-template/`` (was v0.16.25 D-2026-05-13-B)
- ``plot-domain-design/`` (was v0.16.26 D-2026-05-13-C)
- ``plot-feature-tdd/``
- ``plot-frontend-bug-diagnosis/``
- ``plot-i18n-audit/`` (was v0.16.9 D-2026-05-12-L)
- ``plot-code-red-team/`` (was v0.16.7 D-2026-05-12-J)
- ``plot-design-red-team/`` (was v0.16.8 D-2026-05-12-K)

### Retained in plot/skills/ (end-user facing)

- ``plot-help/`` — Novel usage explanation.
- ``plot-new-sketch/`` — consumer creates a new sketch.
- ``plot-read-sketch/`` — consumer reads an existing sketch.

### Changed

- All cross-references inside the 7 moved SKILL.md files updated:
  ``(../../X)`` → ``(../../plot/X)`` to point from the new location
  back into the plot/ subdirectory.
- ``plot-entity-template/SKILL.md`` ``feedback_no_god_object``
  cross-reference converted from a broken cross-home filesystem
  link to plain-text reference (auto-memory paths are user-home
  specific and cannot be relative-linked from a monorepo file).

## [0.16.30] — 2026-05-13

Docs follow-up to v0.16.24-29 catch-up batch. Update
``NEXT_SESSION.md`` "RF 움직임" trigger entry to reflect:
- Anchor visual is now **restored** (v0.16.24, D-2026-05-13-A) —
  Open Question 3 is closed.
- Baseline for next-session diagnosis is **v0.16.29** with 461 / 461
  viewer tests + all 5 D-2026-05-12-B catch-up artefacts shipped.
- Reference plan switched from
  ``~/.claude/plans/dazzling-inventing-boole.md`` (historical
  rollback plan, now an over-reach reference) to
  ``~/.claude/plans/sparkling-discovering-blanket.md`` (current
  plan, Step 3 layer kill-switch bisect is the diagnosis entry).
- Recovery-commit list trimmed to currently-live commits.

### Changed

- ``plot/docs/NEXT_SESSION.md`` — RF 움직임 entry refreshed for the
  post-v0.16.24 baseline.

## [0.16.29] — 2026-05-13

Fifth and final of 5 deferred D-2026-05-12-B catch-up artefacts. Add
a row to ``plot/CLAUDE.md`` §Anti-patterns: *"Treating raw JSON as a
domain entity (no fromJson boundary)"*. Cross-references the
``plot-entity-template`` skill (Phase A), ``no-god-import.test.tsx``
(Phase C), ``entity-roundtrip.test.tsx`` (Phase D), and server-side
``test_schema_parity.py``. Closes the D-2026-05-12-B candidate list.
(D-2026-05-13-F)

### Added

- ``plot/CLAUDE.md`` — anti-pattern table row 11 ("Treating raw JSON
  as a domain entity").

## [0.16.28] — 2026-05-13

Fourth of 5 deferred D-2026-05-12-B catch-up artefacts. Add
``viewer/tests/entity-roundtrip.test.tsx`` — vitest static guard
verifying ``parseEntity(createBlankNode(kind, base)).toJson() ===
createBlankNode(kind, base)`` for every NodeKind. Catches silent
field drift between ``fromJson`` and ``toJson`` (a field added in
one and missed in the other) before the regression reaches the
React Flow render path. Companion to no-god-import (Phase C) and
test_schema_parity (server side). (D-2026-05-13-E)

### Added

- ``viewer/tests/entity-roundtrip.test.tsx`` — 16 sub-tests:
  - 15 per-kind round-trip (parseEntity ∘ toJson is identity).
  - 1 dispatch coverage (parseEntity accepts every NodeKind).

### Verification

- viewer vitest — 461 / 461 (445 → 461, +16).

## [0.16.27] — 2026-05-13

Third of 5 deferred D-2026-05-12-B catch-up artefacts. Add
``viewer/tests/no-god-import.test.tsx`` — static guard enforcing the
v0.15 Phase 2.10 invariant that ``viewer/src/types.ts`` re-exports
``SketchNode`` from the discriminated union rather than declaring a
god interface. Plus per-kind file existence + ``{Kind}Json`` export +
``registerKindParser`` call. Together with ``test_schema_parity.py``
(server side) and the upcoming ``entity-roundtrip.test.tsx`` (Phase D),
keeps the domain layer intact. Hook semantics realised via existing
``pre_commit_gate.py`` running vitest on every viewer commit.
(D-2026-05-13-D)

### Added

- ``viewer/tests/no-god-import.test.tsx`` — 46 sub-tests (1 anti-god
  + 15 file-exists + 15 Json-export + 15 registerKindParser).

### Verification

- viewer vitest — 445 / 445 (399 → 445, +46).
- New guard fails cleanly on regression (verified by inspection of
  assertion messages).

## [0.16.26] — 2026-05-13

Second of 5 deferred D-2026-05-12-B catch-up artefacts. Add
``plot/skills/plot-domain-design/SKILL.md`` — the **gate** that forces
the placement decision *before* any code lands. Five-decision walk
(thing-vs-rule / entity-vs-value / existing-kind-reuse / bounded-context
home / SSOT location) writes a Decision summary into DECISIONS.md
*before* implementation begins. The v0.13.3-v0.13.10 cursor saga was
caused by no domain map; this skill is the framework that saga lacked.
(D-2026-05-13-C)

### Added

- ``plot/skills/plot-domain-design/SKILL.md`` — procedure skill.

## [0.16.25] — 2026-05-13

First of 5 deferred D-2026-05-12-B candidate artefacts. Add
``plot/skills/plot-entity-template/SKILL.md`` — the single procedure
SSOT for adding a new domain entity (a new ``kind``) end-to-end.
14-step walk covers CONCEPTS / SPEC / domain class with ``fromJson`` /
union extend / factory / Pydantic model / schema-parity / per-kind
renderer / per-kind inspector / registry / i18n / round-trip test /
structural-guards. User direction 2026-05-12: *"필요하다면 스킬이나
룰을 만들구요"* (D-2026-05-12-B), surfaced as overdue 2026-05-13.
(D-2026-05-13-B)

### Added

- ``plot/skills/plot-entity-template/SKILL.md`` — procedure skill.

## [0.16.24] — 2026-05-13

Restore the v0.16.20-23 "RF 기본 동작 rollback" batch as a single
``git revert`` of all four commits (``ac35021`` v0.16.23, ``32f3dc5``
v0.16.22, ``7edbbf8`` v0.16.21, ``75ee0b0`` v0.16.20). User direct
correction "다 복구 하라" after the prior batch was identified as
over-reach (NEXT_SESSION.md:22-24). The original triggering message
"그냥 RF 기본 동작으로 동작하게 해주세요" had been interpreted as
"remove the synthetic anchor and all its visual layers"; the user's
actual intent was "keep the anchor + make *interaction* feel like
stock React Flow". (D-2026-05-13-A)

### Added (restored)

- ``viewer/src/canvases/edges/SelfLoopEdge.tsx`` — custom edge for
  ``source === target`` (arc rendering).
- ``viewer/src/canvases/edges/registry.ts`` — edge type registry.
- ``viewer/src/canvases/sketch/anchorRadialLayout.ts`` — 120°
  auto-radial slot computation for Foundation new nodes.
- ``viewer/src/canvases/sketch/applyAnchorChange.ts`` — anchor PATCH
  diff helper.
- ``viewer/src/lib/anchorOptimistic.ts`` — optimistic local update on
  anchor drag / resize.
- ``viewer/tests/anchor-drag-snap-back.test.tsx`` — 7 tests.
- ``viewer/tests/foundation-radial-layout.test.tsx``.
- ``viewer/tests/self-loop-render.test.tsx``.

### Changed (restored to v0.16.19 state)

- ``viewer/src/canvases/sketch/useNodesMemo.ts`` — synthetic anchor
  injection block + ``projectAnchor`` / ``projectName`` /
  ``onAnchorChange`` props restored.
- ``viewer/src/canvases/SketchCanvas.tsx`` — ``edgeTypes`` prop +
  anchor props + ``applyAnchorRadialLayout`` prop restored.
- ``viewer/src/canvases/FoundationCanvas.tsx`` /
  ``ActorsCanvas.tsx`` / ``ServicesCanvas.tsx`` — ``injectAnchor={true}``
  restored.
- ``viewer/src/canvases/ServiceDetailCanvas.tsx`` —
  ``injectAnchor={false}`` restored.
- ``viewer/src/canvases/sketch/useNodeCreation.ts`` —
  ``applyAnchorRadialLayout`` argument restored.
- ``viewer/src/canvases/sketch/edgeTransform.ts`` — ``isRealSelfLoop``
  branch restored.
- ``viewer/src/App.tsx`` — ``handleAnchorChange`` useCallback +
  ``onAnchorChange`` prop wiring restored.
- ``docs/SPEC.md`` — §Anchor / §Edges Self-loops / §Foundation
  Anchor-radial sections restored.
- ``docs/DECISIONS.md`` — D-2026-05-13-A entry; D-2026-05-12-V/W/X/Y
  removed by revert (their decisions are now Rejected as documented
  in D-2026-05-13-A).
- ``docs/ROADMAP.md`` — anchor / self-loop / radial archived entries
  removed by revert.

### Removed (the previous batch's removals undone)

- v0.16.20-23 removals (anchor injection, radial layout, self-loop,
  PATCH path) are no longer in effect. See "Added (restored)" above.

### Known unresolved

- Interaction "엉망" — the *actual* user complaint that originally
  triggered both v0.16.15-19 and v0.16.20-23 — is **not** addressed
  by this revert. v0.16.19 (anchor present) and v0.16.23 (anchor
  absent) both exhibited the issue. Diagnosis happens in the next
  session under the ``RF 움직임`` trigger (NEXT_SESSION.md).

## [0.16.19] — 2026-05-12

Minor stability — ``handleAnchorChange`` extracted from inline JSX
to a top-level ``useCallback``. ``useNodesMemo`` 's synthetic anchor
node carries an inline ``data.onResize`` that delegates to
``onAnchorChange``; by stabilising the source ref, the memo's
``data`` object now only rebuilds when anchor-relevant state
actually changes (projectPath / activeId / activeTab / summaries /
project), not on every App render. Closes the 5-commit React Flow
regression-fix batch (v0.16.15-19). (D-2026-05-12-U)

### Changed — viewer/src/App.tsx

- Inline ``onAnchorChange`` JSX arrow (17 lines) extracted into
  top-level ``handleAnchorChange = useCallback(...)``.
- JSX site uses the stable reference: ``onAnchorChange={handleAnchorChange}``.
- LOC: 380 → 385 (within 400 ceiling).

### Tests

No new dedicated test; existing ``anchor-drag-snap-back.test.tsx``
(7) + ``stable-handlers.test.tsx`` (5) cover both behaviour and
identity-stability patterns this commit applies.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 399 / 399 passed (no test count change).
- ``uv run pytest`` — 274 / 274.

### Batch closure (v0.16.15-19)

Five commits ship the React Flow regression-fix batch surfaced by
user hands-on review of v0.16.14:

| # | Fix | Decision | Tests |
|---|---|---|---:|
| 1 | Anchor drag snap-back | D-2026-05-12-Q | 7 |
| 2 | Refetch storm | D-2026-05-12-R | 5 |
| 3 | Cmd+A controlled contract | D-2026-05-12-S | 2 |
| 4 | fitView mid-session reset | D-2026-05-12-T | 2 |
| 5 | Anchor data.onResize stability | D-2026-05-12-U | (covered) |

Viewer tests: 383 → 399 (+16). Server: 274 / 274 unchanged.

Plugin patch bump 0.16.18 → 0.16.19.

## [0.16.18] — 2026-05-12

Bug fix — fitView gating. ReactFlow's ``fitView`` prop re-fits
whenever the ``nodes`` reference changes; Novel's ``useNodesMemo``
returns a fresh array every render, so the user's manual zoom/pan
was reset mid-session by every unrelated state update. Fix: drop
the prop, call ``inst.fitView({ padding: 0.2 })`` once inside
``onInit``. Canvas tab switches still re-fit because the wrapper
has ``key={activeCanvasKey}`` → remount → onInit fires.
(D-2026-05-12-T)

### Changed — viewer/src/canvases/SketchCanvas.tsx

- Remove ``fitView`` + ``fitViewOptions`` props from
  ``<ReactFlow>``.
- ``onInit`` now invokes ``inst.fitView({ padding: 0.2 })`` once.

### Added — viewer/tests/viewport-stability.test.tsx

2 static-grep guards:
- No top-level ``fitView`` prop on ``<ReactFlow ...>``.
- ``onInit`` JSX form present and contains an
  ``inst.fitView(...)`` call.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 399 / 399 passed (397 prior + 2 new).
- ``uv run pytest`` — 274 / 274.

Plugin patch bump 0.16.17 → 0.16.18.

## [0.16.17] — 2026-05-12

Bug fix — Cmd+A respects controlled-component contract. Previously
Cmd+A flipped RF's internal ``selected`` flag via ``setNodes`` /
``setEdges``, but never synced ``selectedNodeIds.current`` (the
SketchCanvas ref the clipboard reads). Cmd+C / Cmd+D following
Cmd+A copied / duplicated the *previous* selection, not "all nodes".
Fix: write ``selectedNodeIds.current = inst.getNodes().map(n => n.id)``
after the store mutation. (D-2026-05-12-S)

### Changed — viewer/src/canvases/sketch/useKeyboardShortcuts.ts

- Cmd+A branch: after ``setNodes``/``setEdges``, sync
  ``selectedNodeIds.current`` from the RF store.

### Added — viewer/tests/select-all-sync.test.tsx

2 tests:
- Cmd+A populates ``selectedNodeIds.current`` with all rendered
  node ids + RF store ``selected`` flag flips for all nodes.
- Cmd+C after Cmd+A copies the full set (via clipboard mock).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 397 / 397 passed (395 prior + 2 new).
- ``uv run pytest`` — 274 / 274.

Plugin patch bump 0.16.16 → 0.16.17.

## [0.16.16] — 2026-05-12

Bug fix — refetch storm. Playwright session recording showed 404 GETs
to the same 3 endpoints in a single idle browser session. Cause:
App.tsx passed inline arrow closures to ``useProject`` / ``useCanvasPersist``
/ ``useProjectSocket``; those closures were recreated every render,
which under specific WS event timings produced a fetch chain that
re-triggered on each iteration. Fix: ``useStableHandlers`` hook returns
``useCallback``-wrapped post-project handlers; pre-project handlers
(``handleError`` / ``handleActiveIdChange``) are inlined as direct
``useCallback`` in App.tsx. (D-2026-05-12-R)

### Added — viewer/src/hooks/useStableHandlers.ts

Returns ``useCallback``-wrapped:
- ``handleListStale`` — calls ``loadList``.
- ``handleExternalCanvas`` — Map-set into ``setCanvasCache``.
- ``handleTagsRefresh`` — passes through to ``setTags``.
- ``handleExternalChange`` — calls ``historyClear``.

### Changed — viewer/src/App.tsx

- Pre-project handlers (``handleError``, ``handleActiveIdChange``)
  defined as ``useCallback`` before ``useProject`` is invoked.
- Post-project handlers come from ``useStableHandlers`` (single
  destructure).
- ``useProject`` destructure compacted onto fewer lines.
- LOC: 393 → 380.

### Added — viewer/tests/stable-handlers.test.tsx

5 tests:
- Identity stability across re-renders when deps are stable.
- Identity change when ``loadList`` reference changes (correct
  recompute behaviour).
- ``handleExternalCanvas`` produces the right Map-updater.
- ``handleExternalChange`` calls ``historyClear``.
- ``handleListStale`` invokes ``loadList``.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 395 / 395 passed (390 prior + 5 new).
- ``uv run pytest`` — 274 / 274 (no server change).

### Why this wasn't caught by v0.15 structural guards

The structural-guards test (D-2026-05-12-F) is *static* — it checks
file shape, LOC ceilings, registry completeness, no-god-dispatch.
Callback identity stability is a *runtime* concern that no static
guard can detect; it surfaces only under hands-on use. The lesson
will go into the future v0.17+ "RF integration test layer" (filed
in ROADMAP) — runtime regression tests via Playwright.

Plugin patch bump 0.16.15 → 0.16.16.

## [0.16.15] — 2026-05-12

Bug fix — anchor drag snap-back. User dragging the synthetic project
anchor on Foundation / Actors / Services canvases would briefly snap
back to its pre-drag position during the 100-500ms server PATCH
round-trip. Cause: ``summaries`` state only updated *after* the PATCH
resolved, so React Flow's controlled ``nodes`` prop rendered the OLD
anchor placement during the gap. Fix: optimistic local update before
the network call, with revert on PATCH failure. (D-2026-05-12-Q)

### Added — viewer/src/lib/anchorOptimistic.ts

- ``applyOptimisticAnchorPatch(current, tab, patch): ProjectDoc`` —
  pure helper that merges an anchor patch into a ProjectDoc.
- ``resolveAnchorPlacement(proj, tab): AnchorPlacement`` — same
  fallback logic as App.tsx's resolveProjectAnchor, extracted for
  helper-internal use.

### Changed — viewer/src/App.tsx

- ``onAnchorChange`` handler:
  - Captures the previous ProjectDoc before mutation.
  - Calls ``replaceSummary(applyOptimisticAnchorPatch(...))`` *before*
    ``patchProjectAnchor``.
  - On PATCH success, ``replaceSummary(refreshed)`` with server doc.
  - On PATCH failure, ``replaceSummary(previous)`` to revert.
- LOC: 381 → 393 (under 400 ceiling per structural-guards).

### Added — viewer/tests/anchor-drag-snap-back.test.tsx

7 tests covering:
- x/y patch preserves other anchor fields.
- Missing-anchors project gets a default-fallback patch.
- Patching foundation leaves actors anchor untouched.
- Dimension-only patch preserves position.
- Revert path (``previous`` reference unchanged by merge).
- ``resolveAnchorPlacement`` default + stored variants.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 390 / 390 passed (383 prior + 7 new).
- ``uv run pytest`` — 274 / 274 (no server change).

### Series context

First of a 5-commit React Flow regression-fix batch (v0.16.15-19)
prompted by user hands-on review of v0.16.14. The batch addresses
multiple React Flow misuse patterns surfaced when the user dragged
the anchor: snap-back here, refetch storm (v0.16.16), Cmd+A
controlled-contract violation (v0.16.17), fitView mid-session resets
(v0.16.18), anchor data.onResize stability (v0.16.19).

Plugin patch bump 0.16.14 → 0.16.15.

## [0.16.14] — 2026-05-12

Docs-only — end-of-session wrap-up. Three remaining parked-backlog
items (isomorphic-git / work-item layer / repo split) are filed
in ``ROADMAP.md`` §"v0.17+" **with the ``plot-design-red-team``
8-attack findings inlined per item** so the next implementer
walks into pinned design questions instead of fresh discovery.
``NEXT_SESSION.md`` queue is empty pending user hands-on review
of the v0.16 ship.

### Changed — plot/docs/ROADMAP.md

- New top section "v0.17+ — Roadmap items (queued, design
  red-team findings inline)" listing:
  - **A) isomorphic-git source-data version control** — 6 Major
    findings need DECISIONS answers (UI vocab / .git location /
    agent commit identity / conflict resolution UX / commit
    granularity / MVP scope cut). Spec mandate quoted. 2-4 weeks
    estimated, 8-12 commits.
  - **B) Work-item layer (userstory + task)** — hard dep on A.
    4 Major findings (file locations / origin-metadata schema /
    orphan handling / MVP schema cut). 1-2 weeks after A.
  - **C) Novel repository split** — product decision the user
    owns. Technical side: 🟢 READY (one-time ``git filter-repo``).

### Changed — plot/docs/NEXT_SESSION.md

- Active queue empty; entry text points at ROADMAP §"v0.17+".
- Trigger phrases listed for each ROADMAP item so re-entry is
  one phrase away.
- First-priority next-session task = user-driven hands-on review
  of v0.16 ship.

### This session scorecard (v0.15.7 → v0.16.13, 19 commits)

| Track | Commits | Outcome |
|---|---:|---|
| v0.15 Phase 4-5 (검증) | 5 | reset COMPLETE; 8 acceptance gates + kill-switch |
| App.tsx split | 5 | 811 → 381 LOC, ceiling locked at 400 |
| Schema parity test | 1 | 15-kind Pydantic ↔ TS pinned |
| Red-team skills | 2 | code + design SKILL.md |
| First red-team dogfood (i18n-audit) | 1 | 6 findings → revised before code |
| Self-loop visual | 1 | SelfLoopEdge custom edge type |
| Foundation anchor-radial | 1 | Mission/CV/Id radial slots |
| Kill-switch cleanup | 1 | canvas_kind → wrapper prop |
| Owner field | 1 | BaseNodeFields multi-user prep |
| End-of-session wrap | 1 | this commit |

viewer 383/383 + server 274/274 + kill-switch 11/11. tsc / mypy /
ruff all clean.

Plugin patch bump 0.16.13 → 0.16.14.

## [0.16.13] — 2026-05-12

Multi-user prep — ``owner: str | None`` (default ``null``) added
to ``BaseNodeFields`` (Pydantic) and ``BaseFieldsJson`` / ``BaseFields``
(TS). Inherited by all 15 entity classes. Wire-format only — no UI,
no permission logic, no migration. Single-user sessions write
``null``; server will fill from session context once multi-user
ships. Canonical Novel spec §"데이터 구조 원칙":
> "owner 필드 포함 (멀티유저 확장 대비)."
(D-2026-05-12-P)

### Changed — mashbill/models.py

- ``BaseNodeFields.owner: str | None = None`` after ``details_path``.

### Changed — viewer/src/domain/BaseFields.ts

- ``BaseFieldsJson`` + ``BaseFields`` interfaces gain
  ``owner: string | null``.
- ``parseBaseFields`` reads ``obj.owner`` with null default
  (using existing ``asNullableString`` helper).

### Changed — viewer/src/domain/{15 entity files}

Each entity class adds:
- ``readonly owner!: string | null;`` declaration after
  ``readonly details_path!: string | null;``.
- ``owner: this.owner,`` line in ``toJson`` after ``details_path``.

(``Object.assign(this, base)`` in each constructor already copies
the new field through from ``parseBaseFields``; no per-class
fromJson change needed.)

### Changed — tests/test_schema_parity.py

- ``_EXPECTED_BASE_FIELDS`` gains ``"owner"`` so the 2-anchor +
  15-per-kind parity tests assert agreement on the new field.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 383 / 383 passed.
- ``uv run pytest`` — 274 / 274 (schema parity now asserts the
  14-field BaseFields canonical set on both sides).
- ``uv run mypy mashbill/`` — clean.
- ``uv run ruff check`` — clean.
- ``test_pre_commit_gate.py`` — 11 / 11 (kill-switch happy).

Plugin patch bump 0.16.12 → 0.16.13.

## [0.16.12] — 2026-05-12

Kill-switch cleanup — v0.16.11 (D-2026-05-12-N) introduced a
``doc.canvas_kind === "foundation"`` check in
``useNodeCreation.ts`` which the v0.15 reset's
``reset_complete_check`` kill-switch (D-2026-05-12-G) correctly
rejected on the next commit attempt. Same observable behaviour
reshipped via a wrapper-supplied prop ``applyAnchorRadialLayout``
(5th sibling to ``hideRootServiceNode`` / ``shouldDrill`` /
``showFoldButton`` / ``injectAnchor``). FoundationCanvas opts in;
other wrappers default ``false``. (D-2026-05-12-O)

### Changed — viewer/src/canvases/sketch/useNodeCreation.ts

- ``UseNodeCreationArgs`` gains optional
  ``applyAnchorRadialLayout?: boolean``.
- Inline ``current.canvas_kind === "foundation"`` removed.
- ``addNodeAt`` useCallback dep array adds the new flag.

### Changed — viewer/src/canvases/SketchCanvas.tsx

- ``SketchCanvasProps`` adds ``applyAnchorRadialLayout?: boolean``.
- Threaded into ``useNodeCreation`` call.

### Changed — viewer/src/canvases/FoundationCanvas.tsx

- Passes ``applyAnchorRadialLayout={true}``.

### Honest note

The design red-team that ran on the v0.16.11 proposal missed the
``D-2026-05-12-F structural-guards`` invariant about sketch hooks
not reading ``doc.canvas_kind``. The kill-switch caught it within
one commit; the fix is small (one prop, three line edits). The
lesson goes into ``plot-design-red-team`` Attack 2 (Unstated
invariants) as a calibration anchor.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 383 / 383 passed (no test changes).
- ``uv run pytest`` — 274 / 274.
- ``uv run pytest tests/test_pre_commit_gate.py`` — 11 / 11
  passed (kill-switch recovered).

Plugin patch bump 0.16.11 → 0.16.12.

## [0.16.11] — 2026-05-12

Foundation anchor-radial initial placement — when the user creates
a Mission / CoreValue / Identity node on the Foundation canvas, the
new node snaps to a slot on a circle of radius 320 px around the
anchor centre. Slots 120° apart for visual balance. No narrative
ordering. **Positional hint, not a constraint** — user can drag
afterward. D-2026-05-12-N.

### Added — viewer/src/canvases/sketch/anchorRadialLayout.ts

Pure helper module (~95 LOC). Exports:

- ``FOUNDATION_RADIAL_KINDS`` SSOT (the three radial kinds).
- ``isFoundationRadialKind`` type guard.
- ``anchorRadialSlot(kind, existing)`` — slot centre on the
  320 px circle.
- ``anchorRadialPosition(kind, existing, w, h)`` — top-left
  position so the node centre lands on the slot.
- ``countFoundationKinds(nodes)`` — counts of each radial kind
  in the current canvas (drives the +30° same-kind offset).

Clock-face mapping:

- Mission   →  9 o'clock (270°) — left of anchor.
- CoreValue →  1 o'clock (30°)  — upper-right of anchor.
- Identity  →  5 o'clock (150°) — lower-right of anchor.

### Changed — viewer/src/canvases/sketch/useNodeCreation.ts

- ``addNodeAt`` checks ``doc.canvas_kind === "foundation"`` AND
  ``isFoundationRadialKind(kind)``. If both true, ``x``/``y`` are
  overridden by ``anchorRadialPosition``. All other cases keep
  the caller-supplied position.

### Added — viewer/tests/foundation-radial-layout.test.tsx

15 tests covering: SSOT membership, kind-discrimination guard,
slot positions for first node of each kind, on-radius invariant
across all slots, +30° collision offset for repeat kinds,
top-left centring math, ``countFoundationKinds`` ignoring
non-radial kinds.

### Changed — docs/SPEC.md §Foundation

- New "Anchor-radial initial placement" subsection at the top
  of the Foundation section, citing the canonical spec mandate
  + D-2026-05-12-N + the D-2026-05-04-A relationship (auto-position
  is fine because user can drag; auto-edges still banned).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 383 / 383 passed (368 prior + 15 new).
- ``uv run pytest`` — 274 / 274 (no server change).

Plugin patch bump 0.16.10 → 0.16.11. Second of the 3-item
parked-backlog batch.

### Note on v0.16.12 (originally planned)

The third batch item (Service-Detail Mermaid panel) was **dropped**.
User clarification 2026-05-12: Service-Detail's
*"다이어그램 시각화"* is the existing React Flow canvas itself
(actor refs + their relationships + rule/content composition).
Not a separate Mermaid chart. ``ServiceDetailCanvas`` already
serves that role; no panel work needed.

## [0.16.10] — 2026-05-12

Self-loop visual rendering — user-drawn edges with
``source === target`` now render as a curved Bezier arc instead of
being silently dropped. The canonical Novel spec
(*"셀프 피드백 루프 표현 가능 (서비스 A → 서비스 A)"*) explicitly
permitted them; the previous ``edgeTransform.ts:40`` filter was a
spec violation. Plan ``~/.claude/plans/dazzling-inventing-boole.md``,
decision **D-2026-05-12-M**.

### Added — viewer/src/canvases/edges/SelfLoopEdge.tsx

- React Flow custom edge component. Cubic Bezier arc from source
  to target with two control points bulged 100 px above. Click-able,
  selectable, deletable like any edge. Label renders at the arc's apex.
- Exports ``selfLoopPath`` pure helper (the math is the
  worth-protecting part) for unit testing.

### Added — viewer/src/canvases/edges/registry.ts

- ``EDGE_TYPES`` SSOT (mirrors ``nodes/registry.ts`` pattern).
  Single entry today (``selfLoop``); future edge types extend here.

### Changed — viewer/src/canvases/sketch/edgeTransform.ts

- Filter at line 40 split into two cases:
  - **Real self-loop** (``e.source === e.target``) → emit with
    ``type: "selfLoop"``. Renders via ``SelfLoopEdge``.
  - **Pseudo self-loop** (``e.source !== e.target`` but both
    collapse to the same id) → filter (preserves pre-v0.16.10
    behaviour for collapsed subtrees).
- Collapsed-ancestor filter (line 39) unchanged.

### Changed — viewer/src/canvases/SketchCanvas.tsx

- ``ReactFlow`` now receives ``edgeTypes={EDGE_TYPES}``.

### Added — viewer/tests/self-loop-render.test.tsx

7 tests:
- Real self-loop → ``type: "selfLoop"`` emitted with label + value-flow.
- Pseudo self-loop (collapsed) → filtered (2 cases: both-collapse,
  one-side-collapse-to-other).
- Regular cross-node edge → no ``type`` (default Bezier).
- ``selfLoopPath`` → non-degenerate arc from zero-distance input;
  cubic Bezier shape preserved with different source/target.

### Changed — docs/SPEC.md §Edges

- New "Self-loops (source === target)" subsection citing the canonical
  Novel spec mandate + D-2026-05-12-M.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 368 / 368 passed (361 prior + 7 new).
- ``uv run pytest`` — 274 / 274 (no server change).

Plugin patch bump 0.16.9 → 0.16.10. First commit in the 3-item
parked-backlog batch (v0.16.10 — self-loop / v0.16.11 — Foundation
anchor-radial / v0.16.12 — Service-Detail Mermaid panel).

## [0.16.9] — 2026-05-12

New skill — ``plot-i18n-audit`` runs 4 static audits on the viewer
codebase for i18n compliance per ``feedback_plot_global_service`` +
D-2026-05-11-D. **First dogfood of the v0.16.8 ``plot-design-red-team``
skill** — the v1 proposal was design-reviewed before implementation;
6 findings (3 Major + 3 Minor) forced revisions before ship.
(D-2026-05-12-L)

### Added — plot/skills/plot-i18n-audit/SKILL.md

The 4 audits:
1. **Hardcoded user-facing strings** — JSX text + named attribute
   allowlist (aria-* / title / alt / placeholder / label); exemption
   rules for length ≤ 3 / NodeKind literals / brand regex
   ``^[A-Z]{2,8}$`` / MIME type / adjacent ``// i18n-skip`` comment.
2. **Undefined ``t()`` keys** — static + dynamic
   (``t(\`prefix.${var}\`)`` template-literal prefix expansion).
3. **Stale en.json keys** — zero static or dynamic-prefix references.
4. **Untranslated ko.json values** — ``ko[k] === en[k]`` AND length
   > 3 AND value ≠ key tail AND not in brand / MIME allowlist.

Output verdict: ✅ CLEAN / 🟡 FIX / 🔴 BLOCK. Audits 3-4 are
Minor; alone they never escalate verdict.

### Why now

Memory ``feedback_plot_global_service.md``
(*"이건 글로벌 서비스가 될거거든요"*, 2026-05-10) pinned i18n as
non-negotiable. ``i18n-keys-parity.test.ts`` enforces locale parity
but cannot see hardcoded strings, undefined ``t()`` calls, stale keys,
or untranslated values. This skill closes those four gaps without
TS-compiler infra.

### Process note — first red-team dogfood

The v1 proposal was reviewed via ``plot-design-red-team`` (v0.16.8)
before any SKILL.md was written. The skill returned 🟡 REVISE FIRST
with 3 Major + 3 Minor findings: fuzzy "user-facing" definition,
unhandled dynamic-key composition, over-fit untranslated check,
missing WIP escape hatch, undefined audit scope. **Every Major
finding was addressed in the revised proposal that shipped here.**
The dogfood loop was the value-add of v0.16.7 + v0.16.8: catch
proposal weaknesses before code.

### Evolution path (documented inside the skill)

- Phase 1 (now): manual invocation, manual scan, manual report.
- Phase 2: wire Audit 1 + 2 into a vitest static guard so missing
  keys / hardcoded strings fail the build.
- Phase 3: PreCommit hook gating FIX / BLOCK verdicts.
- Per ``project_red_team_review_skill.md`` philosophy: don't
  pre-build Phase 2-3; let usage shape them.

Plugin patch bump 0.16.8 → 0.16.9.

## [0.16.8] — 2026-05-12

New skill — ``plot-design-red-team`` runs 8 adversarial attacks
against a Novel proposal BEFORE implementation. Sister skill to
``plot-code-red-team`` (v0.16.7). Reads a SPEC change draft, a
DECISIONS entry draft, a plan file, or a verbal proposal and
attacks the *idea*, not the code. (D-2026-05-12-K)

### Added — plot/skills/plot-design-red-team/SKILL.md

The 8 attacks:
1. VISION re-anchor (off-essence / phase-leakage).
2. Unstated invariants (service / actor / anchor / edge
   assumptions pinned by DECISIONS).
3. Failure modes (worst-case input / timing / browser).
4. Reversibility (one-way write / user-state contamination /
   migration trap).
5. VISION / PRODUCT_SPEC alignment (canvas inventory, kind
   out-of-scope, global service).
6. Over-fit / under-fit (YAGNI vs AHA tension).
7. Hidden tradeoffs (every benefit must name what it makes harder).
8. Scope drift (implicit "and also…" additions).

Output verdict: ✅ READY TO IMPLEMENT / 🟡 REVISE FIRST /
🔴 REDESIGN.

### Why the two-skill split

Code reviews catch bad code; they don't catch bad ideas. Novel's
v0.13.2 auto-edges were good code that the user rolled back
same-day — the idea was wrong. D-2026-05-10-E auto-layout shipped
twice and was rejected twice. Catching these at the *proposal*
stage is cheaper than catching them at the diff.

The two skills together close the review loop end-to-end (proposal
→ code). Together with the v0.16.0 reset's structural guards +
v0.16.6 schema parity test, Novel now has:

- **Structural** review (8 acceptance gates + kill-switch from
  v0.16.0).
- **Schema** review (parity test from v0.16.6).
- **Code** red-team (v0.16.7).
- **Design** red-team (this commit).

### Evolution path (documented inside the skill)

Per the user's 2026-05-12 direction
(``memory/project_red_team_review_skill.md``):
*"이런 것들이 만들어지면 차차 정형화된 워크플로우로
진화되어야합니다."*

Phase 1 (now): manual invocation via trigger phrases.
Phase 2 (after several uses): hook on PR creation that nudges
"should this have run on the underlying decision?"
Phase 3 (mature): composed slash command ``/plot-propose <text>``.

Phases 2-3 are explicitly *not* pre-built; let usage shape them.

Plugin patch bump 0.16.7 → 0.16.8.

## [0.16.7] — 2026-05-12

New skill — ``plot-code-red-team`` runs 9 adversarial attacks
against a Novel branch / commit set / PR. Triggers on Korean (리뷰 /
코드리뷰 / 공격적으로 / 비판적으로) and English (review / red-team)
phrases. Output: structured report with evidence (file:line) → rule
violated → severity → suggested fix → verdict. (D-2026-05-12-J)

### Added — plot/skills/plot-code-red-team/SKILL.md

The 9 attacks, in order:
1. Diff-vs-claim (scope creep / behaviour-disguised-as-refactor).
2. Bad-faith input (null / wrong-type / path-traversal / PII).
3. Code-as-spec violations (un-specced behaviour, comments-as-spec).
4. Hidden coupling (closure state, prop-semantic drift).
5. God dispatch (micro-god in per-kind files; ``switch (node.kind)``
   regression).
6. Cross-cutting visual bundle (cognitive scapegoat).
7. LOC budget creep (file absorbing responsibility without
   admitting it).
8. Rotted comments (TODO additions, stale module references).
9. Test coverage (regression-bait, brittle tests).

Output verdict: ✅ MERGE OK / 🟡 MERGE WITH FIXES / 🔴 DO NOT MERGE.

### Why now

Memory ``project_red_team_review_skill.md`` filed the user's
direction during the v0.15 Phase 2 session: *"코드 리뷰나 설계
리뷰를 하는 스킬도 필요할 것 같구요. 이건 레드팀 처럼 비판적
시각으로 바라 볼 수 있게."* Deferred until after the v0.15 reset.
The reset shipped at v0.16.0; this is the first follow-up skill.

Sister skill ``plot-design-red-team`` (pre-implementation review)
lands in v0.16.8.

Plugin patch bump 0.16.6 → 0.16.7.

## [0.16.6] — 2026-05-12

Schema parity test — Pydantic ↔ TS XxxJson field sets pinned for
all 15 kinds. The v0.15 reset's parallel union is now machine-checked
end-to-end; field-name drift between server and viewer fails at CI
time with the offending kind named. (D-2026-05-12-I)

### Added — plot/tests/test_schema_parity.py

- 18 tests across three describe-equivalent groups:
  - 2 anchor tests pinning ``BaseNodeFields`` (Pydantic) and
    ``BaseFieldsJson`` (TS) against the canonical 13-field set
    (id / label / x / y / width / height / color / shape / icon /
    parent_id / collapsed / is_root / details_path).
  - 15 parametrised per-kind parity assertions
    (``Pydantic.model_fields.keys() == TS XxxJson field set``).
  - 1 sanity assertion that the discriminated union has exactly
    15 entries.

### Verification

- ``uv run pytest`` — 274 / 274 passed (256 prior + 18 new).
- ``uv run mypy mashbill/`` — clean.
- ``uv run ruff check mashbill/ tests/`` — clean.

Plugin patch bump 0.16.5 → 0.16.6.

## [0.16.5] — 2026-05-12

v0.16.0 follow-up — App.tsx split commit 5 of 5, **DONE**. The
plan target ``≤ 400`` LOC for App.tsx (deferred from Phase 5.2,
filed in D-2026-05-12-F) is now locked in. App.tsx 423 → 381 LOC;
``structural-guards.test.tsx`` ceiling lowered from **830 → 400**.
(D-2026-05-12-H)

### Added — viewer/src/hooks/useAvailableNodes.ts

- Derives the four cross-canvas "available master" lists from the
  canvas cache: ``availableActors`` (actors canvas, kind="actor") +
  ``availableMissions`` / ``availableValues`` / ``availableIdentities``
  (foundation canvas, kind="mission" / "core_value" / "identity").
- Replaces 4 inline ``useMemo`` blocks in App.tsx.

### Added — viewer/src/hooks/useAppKeyboard.ts

- Owns the App-shell keyboard shortcuts: ⌘/Ctrl+Z (undo), ⌘/Ctrl+
  Shift+Z / ⌘/Ctrl+Y (redo), ``?`` (toggle help), Esc (close help
  when open).
- Skips when focus is in an editable field (INPUT / TEXTAREA /
  contentEditable).

### Changed — viewer/src/App.tsx

- 423 → 381 LOC (-42).
- 4 inline ``availableX`` ``useMemo`` blocks replaced by one
  ``useAvailableNodes(canvasCache)`` call.
- 33-LOC inline keyboard ``useEffect`` replaced by ``useAppKeyboard({
  onUndo, onRedo, helpOpen, setHelpOpen })``.
- ``useEffect`` import dropped (no longer used in App).
- ``SketchNode`` type import dropped (now scoped inside
  ``useAvailableNodes``).

### Changed — viewer/tests/structural-guards.test.tsx

- ``App.tsx`` ceiling **830 → 400**. The plan target from
  D-2026-05-12-F is now enforced. Raising the ceiling requires a
  fresh ``D-YYYY-MM-DD-X`` entry that names the new responsibility
  App.tsx legitimately absorbed.

### Changed — plot/CLAUDE.md §Gate 2

- App.tsx row updated: 811 / 830 → 381 / 400.
- New rows for ``shell/*`` and ``hooks/use*`` outlining the
  per-concern split pattern.

### Changed — plot/docs/ARCHITECTURE.md

- "What's still pending" section: App.tsx ≤ 400 marked **DONE**.
  Pointer to the v0.16.1–v0.16.5 commit sequence.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed.
- ``uv run pytest`` — 256 / 256 passed (no server-side changes).
- App.tsx LOC budget assertion: 381 ≤ 400 ✓.

### App.tsx split scorecard (v0.16.1 → v0.16.5)

| Commit | App.tsx LOC | Δ | Extracted |
|---|---:|---:|---|
| v0.16.0 (baseline) | 811 | — | — |
| v0.16.1 | 715 | -96 | ``shell/Header.tsx`` |
| v0.16.2 | 564 | -151 | ``shell/CanvasTabs.tsx``, ``HelpCheatsheet.tsx``, ``states.tsx`` |
| v0.16.3 | 496 | -68 | ``shell/ServiceDetailModal.tsx`` |
| v0.16.4 | 423 | -73 | ``hooks/useUrlSync.ts`` |
| v0.16.5 | 381 | -42 | ``hooks/useAvailableNodes.ts``, ``useAppKeyboard.ts`` + ceiling lock |

Plugin patch bump 0.16.4 → 0.16.5. App.tsx no longer owns chrome
or glue — only project-level state + canvas wiring.

## [0.16.4] — 2026-05-12

v0.16.0 follow-up — App.tsx split commit 4 of 5. URL ⟷ tab /
drill / selection state pulled out of App into a new
``useUrlSync`` hook. App owns only project-level state +
canvas wiring now; tab/drill/selection live in the hook.
(D-2026-05-12-H)

### Added — viewer/src/hooks/useUrlSync.ts

A hook that owns the three browser-URL query params Novel keeps in
sync (``?canvas`` / ``?detail`` / ``?select``) and exposes:

- State: ``activeTab`` / ``detailServiceId`` / ``selectedNodeId``.
- Action: ``syncUrl`` — generic URL writer (also used by App.tsx
  to sync ``?project=<id>`` when useProject changes activeId).
- Navigation callbacks: ``selectTab`` / ``drillIntoService`` /
  ``backToOverview`` / ``jumpToActor`` / ``consumeSelection`` /
  ``focusCanvas`` (the last consumed by ``handleUndo`` / ``handleRedo``
  in App to refocus the right tab after a cross-tab undo).

### Changed — viewer/src/App.tsx

- 496 → 423 LOC (-73).
- Three ``useState`` blocks for tab/drill/selection removed.
- Six navigation callbacks (selectTab / drillIntoService /
  backToOverview / jumpToActor / consumeSelection / focusCanvas)
  removed.
- ``syncUrl`` callback removed.
- ``CANVAS_TAB_IDS`` import dropped (only used inside the hook now;
  ``CanvasTab`` type still imported for the local ``tabToKind`` helper).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed.

Plugin patch bump 0.16.3 → 0.16.4. One more extraction
(``useAvailableNodes`` + ``useAppKeyboard``) lands in v0.16.5,
followed by lowering the structural-guards ceiling from 830 to 400.

## [0.16.3] — 2026-05-12

v0.16.0 follow-up — App.tsx split commit 3 of 5. ServiceDetailModal
extracted; ``useTranslation`` import dropped from App.tsx (only
consumer was the modal). Pure JSX move, no behaviour change.
(D-2026-05-12-H)

### Added — viewer/src/shell/ServiceDetailModal.tsx

- ``ServiceDetailModal`` — overlay that mounts ServiceDetailCanvas
  on top of the still-mounted services canvas (v0.12 drill-in
  pattern). Esc / backdrop click / × button all call ``onClose``.

### Changed — viewer/src/App.tsx

- 564 → 496 LOC (-68).
- Inline ``ServiceDetailModal`` definition removed.
- ``useTranslation`` import dropped (App.tsx no longer renders any
  i18n-aware JSX directly — every i18n string lives inside an
  extracted shell or canvas component).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed.

Plugin patch bump 0.16.2 → 0.16.3. Two more extractions (URL sync +
filters/keyboard hooks) land through v0.16.5; the final commit
lowers the structural-guards ceiling from 830 to 400.

## [0.16.2] — 2026-05-12

v0.16.0 follow-up — App.tsx split commit 2 of 5. Tab strip, help
overlay, and the three placeholder states extracted to
``viewer/src/shell/``. Pure JSX move, no behaviour change.
(D-2026-05-12-H)

### Added — viewer/src/shell/

- ``CanvasTabs.tsx`` — Foundation / Actors / Services tab strip +
  Mark-session button. **Also exports the ``CanvasTab`` discriminator
  + ``CANVAS_TAB_IDS`` SSOT** (the type now lives next to its only
  visual consumer; App.tsx imports both).
- ``HelpCheatsheet.tsx`` — keyboard-shortcut cheat sheet overlay.
- ``states.tsx`` — ``Loading`` + ``ErrorPanel`` + ``EmptyState``
  (each < 15 LOC; grouped per file).

### Changed — viewer/src/App.tsx

- 715 → 564 LOC (-151).
- ``CanvasTab`` type + ``CANVAS_TAB_IDS`` const moved out (now
  imported from ``./shell/CanvasTabs``).
- ``CanvasTabs`` / ``Loading`` / ``ErrorPanel`` / ``EmptyState`` /
  ``HelpCheatsheet`` inline definitions removed.
- ``// Small UI bits`` divider comment removed.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed.

Plugin patch bump 0.16.1 → 0.16.2. Three more extractions land
through v0.16.5; the final commit lowers the structural-guards
ceiling from 830 to 400.

## [0.16.1] — 2026-05-12

v0.16.0 follow-up — App.tsx split commit 1 of 5. Header +
SocketIndicator + ``truncateMiddle`` extracted to
``viewer/src/shell/Header.tsx``. Pure JSX move, no behaviour
change. (D-2026-05-12-H)

### Added — viewer/src/shell/Header.tsx

- ``Header`` component (project path + name + socket + error +
  migration toast).
- Internal ``SocketIndicator`` + ``truncateMiddle`` helpers,
  scoped to this file.

### Changed — viewer/src/App.tsx

- 811 → 715 LOC (-96).
- ``SocketStatus`` type import dropped (now scoped inside the new
  shell module).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed (no test changes; same
  component tree, just imported from a new path).
- ``uv run pytest`` — 245 / 245 passed (no server-side changes).

Plugin patch bump 0.16.0 → 0.16.1. Four more extractions land
through v0.16.5; the final commit lowers the structural-guards
ceiling from 830 to 400.

## [0.16.0] — 2026-05-12

**v0.15 structural reset COMPLETE.** Domain layer + per-kind
inspectors + per-kind node renderers + 4 thin wrappers + 8 acceptance
gates + 1 kill-switch land at v0.16.0. (D-2026-05-12-G)

### Added — hooks/pre_commit_gate.py::reset_complete_check

A single-boolean kill-switch that fires on every commit touching
viewer or server code. Verifies four structural invariants the
existing acceptance-gate suite cannot detect:

1. ``mashbill/models.py`` exposes ``SketchNode`` as a 15-way
   discriminated union (not a god class).
2. ``viewer/src/canvases/SketchInspector.tsx`` stays absent from disk.
3. ``viewer/src/canvases/SketchNode.tsx`` stays absent from disk.
4. Zero ``canvas_kind`` branching in ``viewer/src/canvases/sketch/``
   source files (comments-only references ignored).

Docs-only / non-viewer / non-server commits skip the check entirely.

### Added — tests/test_pre_commit_gate.py (11 tests)

- Pass-case against the real repo (verifies the current tree
  satisfies all four invariants).
- Docs-only skip-case (3 parametrised non-viewer / non-server paths).
- Each invariant has an isolated failure-mode test using a
  ``tmp_path`` scaffold so the deny path is exercised without
  mutating the real working tree.
- Comment-stripping test (``canvas_kind`` inside ``//`` and ``/* */``
  comments does NOT trip the gate).

### Changed — docs/ARCHITECTURE.md

- New "Post-v0.15 shape" section at the top documenting the
  Domain → UI dependency direction, a contracts table linking
  each invariant to its test + decision id, and a "how to add a
  16th kind" recipe.
- Legacy pre-reset section preserved below with a "historical only"
  banner; LOC numbers in that section no longer reflect reality.

### Changed — docs/NEXT_SESSION.md

- ``검증`` queue item moved to Completed with a per-commit summary
  (v0.15.7 → v0.16.0). Active queue now empty.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed.
- ``uv run pytest`` — 256 / 256 passed (245 prior + 11 new from
  ``test_pre_commit_gate.py``).
- ``uv run mypy mashbill/`` — clean.
- ``uv run ruff check mashbill/ tests/ hooks/pre_commit_gate.py`` —
  clean.
- ``reset_complete_check`` returns ``None`` (= reset COMPLETE)
  against the current tree.

### Reset scorecard (v0.14.15 → v0.16.0, 28 commits)

| Phase | Commits | Versions | Outcome |
|---|---:|---|---|
| 0 — Pre-existing ruff/mypy debt | 1 | v0.14.15 | 17 → 0 |
| 1 — Server SSOT (Pydantic 15-class union) | 3 | v0.14.16-18 | god ``SketchNode`` class → ``Annotated[Union[15]]`` |
| 2 — Viewer entities + per-kind Inspector fan-out | 12 | v0.14.19-v0.15.0 | god ``SketchInspector.tsx`` (1491 LOC) deleted; ``SketchNode`` (TS) is now a 15-way union |
| 3 — Canvas wrappers + per-kind node renderers | 5 | v0.15.1-5 | 4 thin wrappers + 15 per-kind nodes + god ``SketchNode.tsx`` (245 LOC) deleted |
| 4 — Cursor uniformity sweep + extended guard | 2 | v0.15.7-8 | 8 + 128 new cursor tests; ``cursor_kind`` drift structurally impossible |
| 5.1 — Exhaustive 15-kind sweeps | 1 | v0.15.9 | 75 viewer + 31 server tests, parametrised across all kinds |
| 5.2 — Structural guards (god + LOC + registry) | 1 | v0.15.10 | 44 tests; CLAUDE.md Gate 2 LOC table updated |
| 5.3 — Kill-switch + docs + complete pin | 1 | v0.16.0 | This commit. Reset DONE. |

- viewer tests: 106 → 361.
- server tests: 214 → 256.
- god files removed: 2 (1491 + 245 = 1736 LOC).
- god switches removed: 4 (3 in transforms + 1 in App.tsx tabToKind).
- structural invariants pinned: 8 acceptance gates + 1 kill-switch.

Plugin minor bump 0.15.10 → 0.16.0 — the only minor bump in the
entire reset sequence. Subsequent work (App.tsx split, schema
parity, Actors v0.15 migration, …) starts from this baseline.

## [0.15.10] — 2026-05-12

v0.15 reset Phase 5.2 — three structural guards protect the post-reset
shape against regression: no-god-union-import (the deleted
``SketchInspector.tsx`` / ``SketchNode.tsx`` must stay absent + no
``switch (X.kind)`` god dispatch in wrappers, App.tsx, SketchCanvas,
BaseNode, BaseInspector, KindInspector, DetailsSection, or any sketch
hook), loc-budget (per-file ceilings — raise via decision, never via
test edit), and registry-completeness (every kind has a per-kind
node + inspector file + registry entry). (D-2026-05-12-F)

### Added — viewer/tests/structural-guards.test.tsx

- 44 tests across three describe blocks:
  - ``no-god-union-import``: 2 god-files-absent + 17 no-switch-dispatch
    across wrappers / shared shell / App.tsx / 14 sketch hooks.
  - ``loc-budget``: 8 named-file ceilings + 2 per-kind sweeps
    (every per-kind node ≤ 100 LOC, every per-kind inspector ≤ 250 LOC).
  - ``registry-completeness``: per-kind file existence + non-empty +
    ``NODE_RENDERERS`` registry contains the 15 kinds and only those.

### Changed — plot/CLAUDE.md §Gate 2

- LOC table replaced. Stale 1476 / 1422 / 791 / 523 entries removed;
  new 8-row post-reset table added with current LOC + runtime-enforced
  ceiling for each canvas-internal file.
- Two "deleted-file" rows pin ``SketchInspector.tsx`` and
  ``SketchNode.tsx`` as absent (re-creating fails the test).
- Documentation pin: "raise a ceiling via decision id; never via
  test edit". App.tsx no-growth deviation (current 811 vs plan target
  ≤ 400) explicitly documented.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 361 / 361 passed (317 prior + 44 new).
- ``uv run pytest`` — 245 / 245 passed (no server-side changes).

### App.tsx refactor follow-up (deferred)

The original Phase 5.2 plan targets ``App.tsx ≤ 400`` LOC. Current
811 reflects URL sync + filter callbacks + handler glue that has not
been extracted into hooks. The split is filed for the v0.16 cycle;
doing it inside this commit would have bundled structural rules +
a behavioural refactor (cross-cutting bundle violation). The
no-growth ceiling (830) catches any further bloat in the meantime.

Plugin patch bump 0.15.9 → 0.15.10.

## [0.15.9] — 2026-05-12

v0.15 reset Phase 5.1 — exhaustive 15-kind smoke + round-trip
sweeps across viewer and server. Each parametric suite iterates
over the 15-way node-kind union and asserts the structural
contract; a future drop / addition / mis-registration in any of
{ Pydantic class, parseEntity dispatch, KindInspector registry }
fails the suite immediately with the offending kind in the test
name. (D-2026-05-12-E)

### Added — viewer/tests/inspectors/inspectors.exhaustive.test.tsx

- 30 tests = 15 kinds × { ``KindInspector`` returns a non-null
  tree, no ``console.error`` during render }.
- Uses ``createBlankNode`` (domain SSOT) to build each synthetic
  node from canonical defaults.

### Added — viewer/tests/domain/round-trip.exhaustive.test.ts

- 45 tests = 15 kinds × { ``parseEntity`` dispatches to a class
  instance, ``fromJson(toJson())`` is idempotent, kind is
  preserved across the round-trip }.

### Added — plot/tests/test_node_models.py (exhaustive section)

- 31 new tests = 15 kinds × { adapter dispatches to right class,
  ``model_validate(instance.model_dump())`` is idempotent } +
  1 union-size sanity. Pins the server-side 15-way discriminated
  union as the source of truth for kind enumeration.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 317 / 317 passed (242 prior + 75 new).
- ``uv run pytest`` — 245 / 245 passed (214 prior + 31 new).
- ``uv run mypy mashbill/`` — clean.
- ``uv run ruff check mashbill/ tests/`` — clean.

Phase 5.1 leaves the hand-written per-kind tests in place (they
cover kind-specific edge cases the structural sweep can't
enumerate — e.g. ``CategoryInspector`` empty-warning,
``ActorRefInspector`` orphan rendering, Service composition lists).
The sweep is additive, not a replacement.

Plugin patch bump 0.15.8 → 0.15.9.

## [0.15.8] — 2026-05-12

v0.15 reset Phase 4.2 — extended cursor-baseline static guard.
The existing 1-test ``styles.css`` guard (D-2026-05-11-C) is
broadened into a 129-test sweep that asserts ZERO raw ``cursor:``
declarations and ZERO ``style.cursor =`` JS assignments across
every canvas-internal source file: 4 wrappers, shared shell (SketchCanvas
/ BaseNode / BaseInspector / KindInspector / DetailsSection /
registries / types), 15 per-kind node renderers, 15 per-kind
inspectors, inspectors/shared, and all 17 sketch hooks. With
``cursor-sweep.test.tsx`` (D-2026-05-12-C, ships in 0.15.7) and
this guard, per-canvas cursor drift is structurally impossible.
(D-2026-05-12-D)

### Added — guards inside viewer/tests/styles-cursor-baseline.test.tsx

- ``KIND_DIRS`` SSOT for the 15 node-kind names (assertion: every
  expected per-kind directory exists under both
  ``canvases/nodes/`` and ``canvases/inspectors/``).
- ``it.each`` raw ``cursor:`` guard across all 60-ish canvas-internal
  source files (regex ``cursor\s*:`` — colon-suffixed; intentionally
  ignores Tailwind ``cursor-X`` utility class names by design).
- ``it.each`` ``style.cursor =`` JS assignment guard (regex
  ``\bstyle\s*\.\s*cursor\s*=``).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 242 / 242 passed (114 prior + 128 new from this
  file).
- ``uv run pytest`` — 214 / 214 passed (no server-side changes).

### Note on Tailwind utility classes

``cursor-grab`` (SketchStencil), ``active:cursor-grabbing``
(SketchStencil), ``cursor-not-allowed`` (SketchContextMenu,
SketchToolbar), ``cursor-pointer`` (SketchEdgeModal),
``disabled:cursor-not-allowed`` (DetailsSection): each is a class
string with a hyphen after ``cursor``, not a colon, and lives on
chrome surfaces shared identically across all 4 wrappers. The
regex above intentionally does not match these; their per-file
addition is allowed and tracked by the cursor-sweep DOM-equivalence
test instead (which would notice class-set drift across wrappers).
See D-2026-05-12-D §"What the guard does not match" for the full
rationale.

Plugin patch bump 0.15.7 → 0.15.8.

## [0.15.7] — 2026-05-12

v0.15 reset Phase 4.1 — cursor uniformity audit + JSDOM sweep.
The user's complaint that fired the v0.15 reset
(*"파운데이션에서 사용되는 커서 컨트롤하고 액터나 서비스에서
사용되는 커서 컨트롤이 다릅니다"*) is now answered empirically:
all 4 wrappers (Foundation / Actors / Services / ServiceDetail)
route through a single SketchCanvas + NODE_RENDERERS + BaseNode
pipeline, with **zero** per-canvas cursor declarations anywhere
in the wrapper / per-kind node / per-kind inspector / sketch hook
files, and **identical** ``react-flow__*`` class skeletons under
DOM sweep. Cursor inventory is fully determined by the shared RF
vendor CSS + Tailwind preflight stack; per-canvas drift is now
structurally impossible. (D-2026-05-12-C)

### Added — viewer/tests/cursor-sweep.test.tsx

- 8 tests across 3 describe blocks:
  1. Zero inline ``style.cursor`` assignments on any element rendered
     by FoundationCanvas / ActorsCanvas / ServicesCanvas /
     ServiceDetailCanvas (empty doc).
  2. Zero inline ``style.cursor`` when each wrapper is seeded with
     all 15 node kinds (via ``createBlankNode`` from the domain layer).
  3. ``react-flow__*`` class-skeleton equivalence across the 4
     wrappers — same set of fragments (``react-flow__pane``,
     ``react-flow__renderer``, ``react-flow__viewport``, …) on each.
- Per-kind node renderer probes: Foundation seed (project + mission +
  core_value + identity) and Services seed (category + service) each
  render with zero inline cursor on any descendant.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 114 / 114 passed (106 prior + 8 new from this
  file).
- ``uv run pytest`` — 214 / 214 passed (no server-side changes).

### Audit evidence (pinned via D-2026-05-12-C)

| Probe | Result |
|---|---|
| ``grep -rn "cursor:" viewer/src/canvases/`` | 0 raw CSS hits |
| Tailwind ``cursor-*`` utility usage | Only in chrome (Stencil / ContextMenu / Toolbar / EdgeModal / DetailsSection) — shared across all wrappers |
| ``grep -rEn "style\.cursor\|cursor\s*="`` viewer/src/ | 0 hits |
| ``styles.css`` cursor declarations | 0 (guarded by ``styles-cursor-baseline.test.tsx`` since D-2026-05-11-C) |
| Wrapper LOC (Foundation / Actors / Services / ServiceDetail) | 22 / 16 / 22 / 23 — props-only thin shells |

### Deviation from the original Phase 4.1 plan

The plan called for a Playwright spec that probes
``getComputedStyle()`` in a real browser. The audit above proves
cursor uniformity structurally — every per-canvas cursor source
has been eliminated — and the JSDOM sweep pins the DOM-shape
equivalence. Adding Playwright would re-derive the same conclusion
at the cost of ~300 MB browser binaries + a separate test runner.
The user-runnable DevTools recipe in ``docs/CURSOR.md`` §"How to
verify the cursor state in the browser" (lines 197-215) remains
the canonical sensory confirmation when the user wants one. See
D-2026-05-12-C §Alternatives for the reversal path if a future
drift report needs live evidence.

Plugin patch bump 0.15.6 → 0.15.7.

## [0.15.6] — 2026-05-12

Docs-only — handoff for the next session. v0.15 reset Phases 4–5
queued in NEXT_SESSION.md under the new ``검증`` trigger; the
original ``구조 리셋`` queue entry is moved to Completed with the
per-phase summary of what shipped this session (v0.14.15 → v0.15.5,
23 commits). (D-2026-05-12-B)

### Changed — plot/docs/NEXT_SESSION.md

- New active queue item: ``검증`` (triggers: 검증 / verification /
  phase 4 / phase 5 / 커서 sweep). Carries the Phase 4 (cursor
  sweep + drift audit) and Phase 5 (verification gates +
  kill-switch → v0.16.0) per-phase plan.
- Old ``구조 리셋`` entry moved to "Completed Phase 1+2+3 in this
  session" with a per-phase summary. The original problem statement,
  code evidence, and Phase A–F plan blocks were removed (preserved
  in git history at v0.14.14 + the plan file
  ``~/.claude/plans/dazzling-greeting-diffie.md``).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed (no test changes).
- ``uv run pytest`` — 214 / 214 passed (no test changes).

Plugin patch bump 0.15.5 → 0.15.6.

## [0.15.5] — 2026-05-12

v0.15 structural reset Phase 3.5 — legacy ``SketchNode.tsx`` (245
LOC) DELETED. ``NODE_RENDERERS`` is now wired into SketchCanvas's
React Flow ``nodeTypes`` map; each node carries its kind as the
React Flow ``type`` discriminator instead of the v0.14 ``"sketch"``
god type. Phase 3 complete. (D-2026-05-12-B)

### Removed (BREAKING within viewer/src/canvases/)

- ``viewer/src/canvases/SketchNode.tsx`` — the 245-LOC god renderer
  that branched on ``data.kind`` for every cosmetic choice. Now
  zero LOC on disk.

### Changed — SketchCanvas

- ``NODE_TYPES = NODE_RENDERERS`` (was ``{ sketch: SketchNode }``).
  React Flow now dispatches by kind; each per-kind component from
  ``nodes/{kind}/`` handles its own node rendering.

### Changed — useNodesMemo

- Each rendered node's ``type`` field is now ``n.kind`` (was the
  hardcoded ``"sketch"`` god type).
- Synthetic project anchor's ``type`` is ``"project"``.
- ``SketchNodeData`` import replaced by ``BaseNodeData`` from
  ``../nodes/BaseNode`` (the per-kind data shape).

### Verification

- ``find viewer/src -name "SketchNode.tsx"`` — absent.
- ``grep '"sketch"' viewer/src/canvases/sketch/`` — only inside
  a comment, no live code reference.
- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed.

### Phase 3 complete

15 per-kind React Flow node renderers + 4 canvas wrappers
(Foundation / Actors / Services / ServiceDetail) + zero
``canvas_kind`` switches in transforms + zero ``"sketch"`` god
type. The viewer canvas layer now mirrors Phase 2's Inspector
layer's per-kind discipline end-to-end.

Plugin patch bump 0.15.4 → 0.15.5. Phase 4 (per-canvas cursor
sweep) is the natural next ship.

## [0.15.4] — 2026-05-12

v0.15 structural reset Phase 3.4 — canvas_kind switches stripped
from useNodesMemo + useEdgesMemo + edgeTransform; each per-canvas
wrapper now supplies its own behaviour via 4 explicit props.
(D-2026-05-12-B)

### Changed — useNodesMemo

The 4 ``doc.canvas_kind`` switches inside the transform are gone.
``useNodesMemo`` now takes 4 new wrapper-supplied args:

- ``hideRootServiceNode: boolean`` — drop the canvas's root-service
  node from the rendered list. Was: ``canvas_kind === "service_detail"``.
- ``shouldDrill: ((node) => boolean) | undefined`` — predicate that
  opts nodes into double-click drill. Was: inline kind-specific
  conditions on services / service_detail.
- ``showFoldButton: boolean`` — render the fold (▾/▸) button on
  container nodes. Was: ``canvas_kind !== "foundation"``.
- ``injectAnchor: boolean`` — inject the synthetic project anchor
  at the top of the node list. Was: ``ANCHOR_KINDS.has(canvas_kind)``.

### Changed — useEdgesMemo + edgeTransform

The ``canvasKind`` parameter is gone; ``hideRootServiceNode`` flows
in instead. ``edgeTransform`` is still pure + unit-testable in
isolation; the change just renamed the input flag.

### Changed — SketchCanvas

Forwards the 4 new props to the transforms with safe defaults
(``hideRootServiceNode=false``, ``showFoldButton=true``,
``injectAnchor=true``, ``shouldDrill=undefined``) so any direct call
without a wrapper still works (none today; the default just means
"normal main-canvas behaviour").

### Changed — wrappers

- ``FoundationCanvas``: ``hideRootServiceNode=false``,
  ``shouldDrill=undefined``, ``showFoldButton=false``,
  ``injectAnchor=true``.
- ``ActorsCanvas``: ``showFoldButton=true``, others as Foundation.
- ``ServicesCanvas``: ``shouldDrill=(n => n.kind === "service" && !n.is_root)``,
  others as Foundation but ``showFoldButton=true``.
- ``ServiceDetailCanvas``: ``hideRootServiceNode=true``,
  ``shouldDrill=(n => n.kind === "actor_ref")``, ``injectAnchor=false``,
  ``showFoldButton=true``.

### Verification

- ``grep -nE "canvas_kind\s*===" useNodesMemo useEdgesMemo edgeTransform App.tsx`` — 0 hits.
- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed.

Plugin patch bump 0.15.3 → 0.15.4.

## [0.15.3] — 2026-05-12

v0.15 structural reset Phase 3.3 — ServicesCanvas + ServiceDetailCanvas
wrappers added; ``App.tsx`` no longer calls ``SketchCanvas`` directly.
(D-2026-05-12-B)

### Added

- ``viewer/src/canvases/ServicesCanvas.tsx`` — services-overview
  wrapper. Pass-through; Phase 3.4 absorbs canvas-kind-specific
  behaviour.
- ``viewer/src/canvases/ServiceDetailCanvas.tsx`` — service-detail
  modal wrapper. Pass-through; Phase 3.4 absorbs the service-detail-
  specific anchor + edge filter rules; Phase 3.5 wires NODE_RENDERERS.

### Changed

- ``viewer/src/App.tsx`` — the ``SketchCanvas`` import is gone.
  Both call sites (main canvas + service-detail modal) now mount
  the named wrapper. The activeTab dispatch picks
  Foundation / Actors / Services per tab.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed.

Plugin patch bump 0.15.2 → 0.15.3.

## [0.15.2] — 2026-05-12

v0.15 structural reset Phase 3.2 — FoundationCanvas + ActorsCanvas
wrappers introduced as named pass-throughs; App.tsx routes by
``activeTab``. (D-2026-05-12-B)

### Added

- ``viewer/src/canvases/FoundationCanvas.tsx`` — pure pass-through
  to ``SketchCanvas``. Phase 3.4 absorbs canvas-kind-specific
  behaviour; Phase 3.5 wires ``NODE_RENDERERS`` so this wrapper
  supplies a Foundation-only ``nodeTypes`` map.
- ``viewer/src/canvases/ActorsCanvas.tsx`` — same pattern.

### Changed

- ``viewer/src/App.tsx`` — the main canvas mount now picks
  ``FoundationCanvas`` / ``ActorsCanvas`` / (legacy)
  ``SketchCanvas`` based on ``activeTab``. The component identity
  is now named per tab; behaviour unchanged.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed.

Plugin patch bump 0.15.1 → 0.15.2.

## [0.15.1] — 2026-05-12

v0.15 structural reset Phase 3.1 — BaseNode shell + 15-kind React
Flow node renderer registry. Mirrors the Phase 2 Inspector pattern
(BaseInspector + KIND_INSPECTORS + per-kind wrappers) at the node
layer. (D-2026-05-12-B)

The legacy ``SketchNode.tsx`` (245 LOC) is unchanged and still in
use by ``SketchCanvas`` until Phase 3.5 wires the registry.
Phase 3.2–3.4 introduces canvas wrappers that consume the registry.

### Added — viewer/src/canvases/nodes/

- ``BaseNode.tsx`` — chrome SSOT: NodeResizer, the outer
  shape-styled div, the 4 React Flow Handles, the MD-warnings
  badge, the label / icon / fold / body area. Per-kind callers
  pass a small ``chrome`` prop with ``showKindTag`` /
  ``isAnchor`` / ``labelAlignLeft`` / ``bodyOverride`` overrides.
- ``shouldShowKindTag(shape)`` helper — returns true for
  ``rectangle`` / ``rounded`` shapes (where the top-left corner
  is inside the visible silhouette).
- ``{kind}/index.tsx`` × 15 — minimal per-kind wrappers (avg
  ~12 LOC each). Currently same chrome as today; the per-file
  structure is the hook point for future per-kind visual variations.
  ``ProjectNode`` carries ``isAnchor: true``; ``CategoryNode``
  carries ``labelAlignLeft: true``; Foundation + composition kinds
  enable ``showKindTag`` for rectangle / rounded shapes.
- ``registry.ts`` — ``NODE_RENDERERS: Record<NodeKind,
  NodeRendererComponent>`` covering all 15 kinds.

### Added — tests

- ``viewer/tests/nodes/registry.test.tsx`` — 3 tests: registry
  has all 15 NodeKind entries, every entry is a callable
  component, and ``shouldShowKindTag`` returns true only for
  rectangle / rounded shapes.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 106 / 106 passed (103 prior + 3 new).

Plugin patch bump 0.15.0 → 0.15.1.

## [0.15.0] — 2026-05-12

v0.15 structural reset Phase 2.10 — viewer-side god ``SketchNode``
interface RETIRED. The TypeScript wire shape is now a discriminated
union of 15 per-kind ``XxxJson`` interfaces (mirroring the server-side
Pydantic union landed in v0.14.17). This is the version-bump moment
the entire reset has been climbing toward. (D-2026-05-12-B)

### Atomic flip — types.ts

- ``viewer/src/types.ts`` no longer defines an ``interface SketchNode``
  with all 47 typed fields collapsed. The 130-LOC god block (and the
  4 ``*FoundationNode`` cosmetic-narrowing types) are gone.
- ``viewer/src/types.ts`` re-exports ``SketchNode`` from ``./domain``;
  the dozen+ files that already import from ``../types`` keep working
  without any import path changes.
- New ``viewer/src/domain/SketchNode.ts`` defines:
  - ``SketchEntity`` — class-instance union (used by parseEntity +
    tests; rare in viewer code).
  - ``SketchNode`` — JSON-shape union (used by React Flow state,
    Inspector props, api.ts response casts, undo/redo). Class
    instances satisfy this structurally; plain objects from
    ``{...node, x: newX}`` spread also satisfy it (no method
    requirement on the union).

### Per-kind ``XxxJson`` interfaces tightened to required

The wire shape from the server (Pydantic ``model_dump()``) always
populates every field with its default, so each ``XxxJson`` is now
"required everywhere". This eliminates ``?? ""`` / ``?? null``
fallbacks throughout the Inspector code and matches reality.

### Per-kind Inspector narrowing

Every ``inspectors/{kind}/index.tsx`` now opens with:

```ts
if (props.node.kind !== "<kind>") return null;
const node = props.node;
```

so TypeScript narrows ``node`` to the per-kind ``XxxJson`` shape
inside the body. The matching ``XxxFields`` component declares
``node: XxxJson`` (was ``node: SketchNode`` god). Per-kind components
now type-check the kind-specific field accesses they always relied
on (``node.target`` for Metric, ``node.target_side`` for Service,
etc.).

### Added — viewer/src/domain/createBlankNode.ts

Factory that builds a wire-shape node for a given kind by running
the per-kind entity class's ``fromJson`` + ``toJson``. Replaces the
v0.14 god-style 47-field inline initialiser in
``useNodeCreation.ts``. Each blank node now carries exactly the
canonical defaults its kind owns — no foreign fields.

### Added — narrowed shared components

- ``inspectors/shared/DoDontFields.tsx`` accepts a structural
  ``DoDontCarrier`` (``{ do?: string; dont?: string }``) instead
  of a god-typed ``SketchNode``.
- ``inspectors/shared/FoundationRefBlock.tsx`` accepts the
  ``MissionRefJson | ValueRefJson | IdentityRefJson`` narrowed
  union.

### Removed

- God ``SketchNode`` interface (130 LOC) from ``viewer/src/types.ts``.
- ``BaseFoundationNode`` + ``ProjectFoundationNode`` +
  ``MissionFoundationNode`` + ``CoreValueFoundationNode`` +
  ``IdentityFoundationNode`` (the v0.13 cosmetic-narrowing aliases
  superseded by the real per-kind entity classes).
- The "kind: NodeKind | null" path in node-creation. Every node now
  has a non-null kind discriminator at construction time.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 103 / 103 passed.
- All 15 per-kind inspectors narrow correctly; no ``as any`` /
  no untyped accesses on the union.

Plugin minor bump 0.14.27 → 0.15.0 — the v0.15 reset's central
promise (no god object on either server or viewer; per-kind
discriminated union end-to-end) is now LIVE.

## [0.14.27] — 2026-05-12

v0.15 structural reset Phase 2.9 — final per-kind vertical slice
(Service + Rule + Content) AND deletion of the legacy
``SketchInspector.tsx`` (was 1491 LOC at v0.14.18; this commit
removes the last remnants and cuts the file from disk).
(D-2026-05-12-B)

### Decision — phase merge

The plan had Phase 2.10 do "delete SketchInspector + retire god
types.ts" as one step. This commit pulls the SketchInspector
deletion forward because by the time service migrated, every kind
was in the registry — the legacy fallback path was unreachable
dead code. Phase 2.10 (next commit) now does ONLY the types.ts
atomic flip (god interface → 15-way discriminated union).

### Added — viewer/src/domain/ (3 final entity classes)

- ``Service.ts`` — target_side + 6 typed fields (what /
  value_created / scope / trigger / how / outcome) + do/dont.
- ``Rule.ts`` — policy + enforcement + actor_permissions
  (Record<string,string> with strict value typing).
- ``Content.ts`` — format + producer_actor_id + consumer_actor_id.

### Added — viewer/src/canvases/inspectors/ (3 per-kind + 3 shared)

- ``service/index.tsx`` — ServiceInspector wraps ServiceFields +
  two CompositionList panels (rules + contents).
- ``service/CompositionList.tsx`` — extracted CompositionList +
  CompositionRow.
- ``service/RuleFields.tsx`` — extracted RuleFields with the
  per-actor-permissions editor.
- ``service/ContentFields.tsx`` — extracted ContentFields +
  ContentActorPicker.
- ``rule/index.tsx`` — direct-selection variant of RuleFields
  inside BaseInspector chrome.
- ``content/index.tsx`` — direct-selection variant of ContentFields.
- KindInspectorProps grows ``onAddChild?`` + ``onPatchChild?`` +
  ``onRemoveChild?`` (all optional — only ServiceInspector uses
  them; other kinds receive undefined).

### Removed

- ``viewer/src/canvases/SketchInspector.tsx`` — the 1491-LOC
  god component is now ZERO LOC on disk.
- All local fields helpers and composition components that lived
  inside it (CompositionList, CompositionRow, ServiceFields,
  ServiceTextarea, RuleFields, ContentFields, ContentActorPicker).

### Changed

- ``viewer/src/canvases/sketch/SketchInspectorBindings.tsx`` now
  calls ``KindInspector`` directly, with an inline null-guard for
  the no-selection case. The bindings file is the same external
  contract — it's the ONLY consumer of the inspector framework
  outside ``inspectors/`` itself.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 103 / 103 passed (90 prior + 13 new
  covering Service / Rule / Content round-trip + dispatch + smoke).

### Registry status — all 15 kinds migrated

```
metric, step, core_value, identity, mission, project, category,
actor_ref, mission_ref, value_ref, identity_ref, actor,
service, rule, content
```

Plugin patch bump 0.14.26 → 0.14.27.

## [0.14.26] — 2026-05-12

v0.15 structural reset Phase 2.8 — ``actor`` kind vertical slice
(D-2026-05-12-B). Includes the v0.3 actor-composition placeholder
that fires for non-root actors.

### Added

- ``viewer/src/domain/Actor.ts`` (motivation + pain + side validator).
- ``viewer/src/canvases/inspectors/actor/index.tsx`` — renders the
  side select + motivation + pain + the placeholder for non-root.
- registry: ``actor: ActorInspector``.
- 4 round-trip + 3 smoke tests.

### Removed

- Local ``ActorFields`` (~58 LOC) + the actor-placeholder branch
  from ``SketchInspector.tsx``.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 90 / 90 passed (83 prior + 7 new).

Plugin patch bump 0.14.25 → 0.14.26.

## [0.14.25] — 2026-05-12

v0.15 structural reset Phase 2.7 — bundled vertical slice for the 4
reference kinds: ``actor_ref`` + ``mission_ref`` / ``value_ref`` /
``identity_ref``. (D-2026-05-12-B)

### Added — KindInspectorProps grew ref-related optional fields

- ``availableActors?: SketchNode[]`` (ActorRef master lookup).
- ``availableMissions?`` / ``availableValues?`` / ``availableIdentities?``
  (FoundationRef master lookups).
- ``onRepickActorRef?`` + ``onRepickFoundationRef?`` callbacks for
  re-pick UI on orphaned refs.

### Added — viewer/src/domain/

- ``ActorRef.ts`` (ref_actor_id + gives + receives + side validator).
- ``MissionRef.ts``, ``ValueRef.ts``, ``IdentityRef.ts`` (each with
  the corresponding ref_*_id field).

### Added — viewer/src/canvases/inspectors/

- ``shared/FoundationRefBlock.tsx`` — extracted from the legacy
  inspector. Resolves master from available-list; surfaces orphan
  state with re-pick + delete actions.
- ``actor_ref/index.tsx`` — gives/receives form + actor-master
  display + orphan handling.
- ``mission_ref/`` + ``value_ref/`` + ``identity_ref/`` — each wraps
  the shared FoundationRefBlock inside BaseInspector.
- registry: all 4 ref kinds registered.

### Removed — SketchInspector.tsx

- All 4 ref-kind branches (~85 LOC of inline JSX).
- Local ``ActorRefFields`` (~40 LOC) + ``FoundationRefBlock``
  (~85 LOC). Now in ``inspectors/`` per-kind + shared paths.
- Stale ``refTarget`` / ``isOrphanActorRef`` locals (used only by the
  removed branches).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 83 / 83 passed (71 prior + 12 new).

Plugin patch bump 0.14.24 → 0.14.25.

## [0.14.24] — 2026-05-12

v0.15 structural reset Phase 2.5 + 2.6 — bundled vertical slice for
the two simplest remaining kinds: ``project`` (Foundation anchor,
no typed body) and ``category`` (one-line ``theme`` + ``childCount``
empty-warning). (D-2026-05-12-B)

### Added — KindInspectorProps grew an `allNodes` field

Category needs to count nested services for its empty-warning. Rather
than build a context-provider for one prop, the existing
``SketchInspector`` already passes ``allNodes`` and the registry now
forwards it through ``KindInspector`` to every per-kind component.
Most kinds ignore it; Category uses it.

### Added

- ``viewer/src/domain/Project.ts`` (no typed fields beyond BaseFields).
- ``viewer/src/domain/Category.ts`` (theme).
- ``viewer/src/canvases/inspectors/project/index.tsx`` —
  ``ProjectInspector`` is just ``BaseInspector`` (chrome only).
- ``viewer/src/canvases/inspectors/category/index.tsx`` — computes
  ``childCount`` from ``allNodes`` and renders the empty-warning when
  zero.
- registry: ``project`` + ``category``.
- 7 round-trip tests + 3 smoke tests.

### Removed

- Local ``CategoryFields`` (~38 LOC) from ``SketchInspector.tsx``.
- Stale "returns null for unmigrated kinds" smoke test (used
  ``category`` as the unmigrated example; now category IS migrated).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 71 / 71 passed (62 prior + 9 new).

Plugin patch bump 0.14.23 → 0.14.24.

## [0.14.23] — 2026-05-12

v0.15 structural reset Phase 2.4 — ``mission`` Foundation kind
vertical slice. (D-2026-05-12-B)

### Added

- ``viewer/src/domain/Mission.ts`` (what_we_do + why + direction).
- ``viewer/src/canvases/inspectors/mission/index.tsx``.
- registry: ``mission: MissionInspector``.
- 4 round-trip tests + 1 smoke test.

### Removed

- Local ``MissionFields`` (~55 LOC) from ``SketchInspector.tsx``.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 62 / 62 passed (57 prior + 5 new).

Plugin patch bump 0.14.22 → 0.14.23.

## [0.14.22] — 2026-05-12

v0.15 structural reset Phase 2.3 — bundled vertical slice for the
two Foundation kinds that share the do / dont AI-first pair:
``core_value`` and ``identity``. (D-2026-05-12-B)

### Added

- ``viewer/src/domain/CoreValue.ts`` — definition + do + dont.
- ``viewer/src/domain/Identity.ts`` — description + do + dont.
- ``viewer/src/canvases/inspectors/shared/DoDontFields.tsx`` —
  shared do/dont pair extracted from ``SketchInspector.tsx``.
  CoreValue + Identity per-kind inspectors consume it; the legacy
  ``Service`` branch (still on the legacy code path until Phase 2.9)
  imports it from the new shared location.
- ``inspectors/core_value/index.tsx`` + ``inspectors/identity/index.tsx``.
- registry: ``core_value: CoreValueInspector`` + ``identity: IdentityInspector``.
- 8 round-trip tests + 2 dispatch tests + 3 smoke tests.

### Removed

- Local ``CoreValueFields`` / ``IdentityFields`` / ``DoDontFields``
  (~95 LOC) from ``SketchInspector.tsx``.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 57 / 57 passed (47 prior + 10 new).

Plugin patch bump 0.14.21 → 0.14.22.

## [0.14.21] — 2026-05-12

v0.15 structural reset Phase 2.2 — ``step`` kind vertical slice
(D-2026-05-12-B). Repeats the Phase 2.1 pattern.

### Added

- ``viewer/src/domain/Step.ts`` — ``class Step`` with ``order: int |
  null`` (null for parallel branches) + ``outcome``. Self-registers
  with ``parseEntity``.
- ``viewer/src/canvases/inspectors/step/index.tsx`` — ``StepInspector``
  wraps the per-kind body inside ``BaseInspector``.
- ``inspectors/registry.ts`` registers ``step: StepInspector``.
- 5 round-trip tests for Step (defaults / ordered / fractional-rejection
  / wrong-kind rejection / null-order round-trip).
- 1 dispatch test (parseEntity → Step).
- 2 smoke tests (StepInspector renders ordered + unordered nodes
  without console.error).

### Removed

- Local ``StepFields`` (47 LOC) from ``SketchInspector.tsx``.

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 47 / 47 passed (39 prior + 8 new).

Plugin patch bump 0.14.20 → 0.14.21 per the mashbill plugin rule.

## [0.14.20] — 2026-05-12

v0.15 structural reset Phase 2.1 — first vertical slice.
``metric`` kind migrates out of the legacy god ``SketchInspector``
into ``viewer/src/domain/Metric.ts`` + ``viewer/src/canvases/inspectors/metric/``.
The pattern this commit establishes is the template Phase 2.2+
will repeat for every remaining kind. (D-2026-05-12-B)

### Decision — types.ts atomic flip stays in Phase 2.10

Considered: trim god ``SketchNode`` interface kind-by-kind in each
Phase 2.X. Rejected: leaves transient type holes mid-migration and
contradicts the Phase 1.2 atomic-flip principle. Per-kind RENDERING
moves out incrementally; the god TYPE shape stays intact until
Phase 2.10 retires it atomically (mirrors v0.14.17's god-class flip).

### Added — viewer/src/domain/

- ``Metric.ts`` — ``class Metric`` with BaseFields slice + ``target`` +
  ``measurement`` + ``kind: "metric"`` literal. Static
  ``fromJson(raw)`` validates via ``parseBaseFields`` then per-kind
  invariants. Self-registers with ``parseEntity`` on module load.
- ``index.ts`` re-exports ``Metric`` + ``MetricJson``.

### Added — viewer/src/canvases/inspectors/metric/

- ``index.tsx`` — ``MetricInspector`` wraps the per-kind
  ``MetricFields`` body (``target`` text input + ``measurement``
  textarea, identical i18n keys to the legacy ``MetricFields``)
  inside the shared ``BaseInspector`` chrome.

### Added — registry + short-circuit wiring

- ``inspectors/registry.ts`` registers ``metric: MetricInspector``.
- ``SketchInspector.tsx`` — top of the function (after the
  ``if (!node)`` guard) checks ``lookupKindInspector(node.kind)`` and
  delegates to ``KindInspector`` when the kind is migrated. Unmigrated
  kinds fall through to the legacy ``aside`` body unchanged.

### Added — tests

- ``viewer/tests/domain/round-trip.test.ts`` — 9 tests covering
  ``Metric.fromJson`` defaults / overrides / kind validation /
  type coercion / round-trip / spread-safety (React Flow
  ``applyNodeChanges`` compatibility) + ``parseEntity`` dispatch.
- ``viewer/tests/inspectors/inspectors.smoke.test.tsx`` — 3 tests:
  MetricInspector renders shared chrome + typed fields, no
  ``console.error`` fires, ``KindInspector`` returns ``null`` for
  unmigrated kinds (the resolver contract).

### Removed

- ``viewer/src/canvases/SketchInspector.tsx`` — local ``MetricFields``
  function + its props interface (43 LOC). Now lives in
  ``inspectors/metric/index.tsx``. SketchInspector LOC drops
  1413 → 1394 (Gate 2 ✓).

### Verification

- ``npx tsc --noEmit`` — clean.
- ``npx vitest run`` — 39 / 39 passed (27 prior + 12 new).

Plugin patch bump 0.14.19 → 0.14.20 per the mashbill plugin rule.

## [0.14.19] — 2026-05-12

v0.15 structural reset Phase 2.0 — viewer-side scaffolding for the
domain entity layer + per-kind Inspector framework. Pure additive +
one mechanical refactor (extract `DetailsSection` so the new
`BaseInspector` shell and the legacy `SketchInspector` share one
implementation). No user-visible behaviour change. (D-2026-05-12-B)

### Added — `viewer/src/domain/`

- `DomainParseError.ts` — custom error subclass thrown by every
  per-kind `fromJson` parser; carries the offending raw input on
  the error so callers can surface it without re-deriving.
- `BaseFields.ts` — `BaseFieldsJson` (wire shape) + `BaseFields`
  (in-memory shape with defaults filled) + `parseBaseFields(raw)`
  validator that throws `DomainParseError` on any invariant
  violation. Mirrors `mashbill/models.py::BaseNodeFields` 1:1.
- `parseEntity.ts` — discriminator dispatch on `raw.kind`. Each
  per-kind class registers its parser via `registerKindParser`
  during module load; `parseEntity` looks up at runtime. Throws
  `DomainParseError` for missing / unknown kinds.
- `index.ts` — barrel re-export.

### Added — `viewer/src/canvases/inspectors/`

- `types.ts` — `KindInspectorProps` (the prop slice every per-kind
  inspector consumes; kind-specific extras live on per-kind prop
  interfaces inside `inspectors/{kind}/index.tsx`).
- `BaseInspector.tsx` — chrome SSOT for every per-kind inspector.
  Wraps the per-kind body as `children` and renders the shared
  header (kind tag, delete, width toggle, close), MD-warnings
  banner, label input, long-form details section, and actor-root
  toggle. Width preference (narrow / wide) persists across reloads
  via the same localStorage key the legacy inspector uses.
- `DetailsSection.tsx` — extracted from `SketchInspector.tsx`
  (was a local function). Now a standalone shared chrome piece
  consumed by both the legacy inspector and `BaseInspector`.
- `registry.ts` — `KIND_INSPECTORS: Partial<Record<NodeKind,
  KindInspectorComponent>>` (intentionally `Partial` during the
  migration so a kind without a registered inspector returns
  `undefined` and the caller can fall back). Phase 2.1+ populates
  one entry per commit.
- `KindInspector.tsx` — resolver. Looks up the registered
  per-kind inspector for the current node and renders it; returns
  `null` when the kind isn't migrated yet so the legacy inspector
  stays in charge.

### Added — tests

- `viewer/tests/domain/base-fields.test.ts` — 13 tests covering
  `parseBaseFields` (defaults / overrides / id-required /
  type-required / shape-validation / `DomainParseError.raw`
  attachment) and `parseEntity` (empty registry / missing kind /
  non-string kind / unknown kind / dispatch wiring with a
  test-only registered parser).

### Changed

- `viewer/src/canvases/SketchInspector.tsx` — removed local
  `DetailsSection` function (71 LOC) and the unused
  `createFolder` / `MDFileEditor` / `folderSlug` imports it
  needed; now imports `DetailsSection` from
  `./inspectors/DetailsSection`. SketchInspector LOC drops
  1491 → 1413 (Gate 2 ✓ — file shrinks, no new responsibilities).

### Why

Phase 2.0 puts the rails in place so each Phase 2.1+ commit can
land one kind at a time (vertical slice — entity class +
per-kind inspector + types.ts cleanup) without inventing new
infrastructure on every ship. The `Partial<Record<...>>`
registry typing lets the legacy `SketchInspector` keep handling
unmigrated kinds while migrated ones flow through `KindInspector`,
so the user sees no UI change at any commit boundary.

### Verification

- `npx tsc --noEmit` — clean.
- `npx vitest run` — 27 / 27 passed (14 prior + 13 new).
- Existing `i18n-keys-parity.test.ts` and
  `styles-cursor-baseline.test.tsx` static guards still pass.

Plugin patch bump 0.14.18 → 0.14.19 per the mashbill plugin rule.

## [0.14.18] — 2026-05-12

v0.15 structural reset Phase 1.3 — extend `schema_export` to all 15
kinds. Server SSOT now publishes per-kind JSON Schemas + Foundation
MD templates for the full discriminated union introduced in v0.14.17
(D-2026-05-12-B).

### Added

- `mashbill/schema_export.py` — `_ALL_KIND_CLASSES` map covering all
  15 per-kind Pydantic classes (replaces Foundation-only
  `_FOUNDATION_KIND_CLASSES`). `SCHEMA_VERSION` bumped 1 → 2 to flag
  the expansion to downstream consumers.
- `mashbill/schema_export.py` — `export_all_schemas(project_root,
  project_id)` (renamed from `export_foundation_schemas`). Emits 15
  `{kind}.json` JSON Schema files + 3 `{kind}.md.template` heading
  templates (Foundation typed-text kinds only). Idempotent — files
  with unchanged content keep their mtime.
- `plot/tests/test_schema_export.py` — 7 tests covering the export
  surface:
  - all 15 `{kind}.json` files emitted
  - only Foundation typed-text kinds emit `{kind}.md.template`
  - Foundation JSON strips typed-text fields
  - non-Foundation JSON includes typed fields
    (Actor.motivation, Service.target_side, Metric.target, …)
  - `_meta.json` lists every kind with the right schema/plot version
  - idempotent — second call preserves mtime
  - each schema parses with `id` in required props (smoke)

### Changed

- `mashbill/folder_io.py:724` — `create_project` now calls
  `export_all_schemas` instead of `export_foundation_schemas`.

### Why

Phase 2 (viewer-side domain entity classes) needs a server SSOT that
publishes the full per-kind shape, not just the Foundation subset.
The schema files under `.plot/{project_id}/schema/` will back the
TS↔Pydantic field-name parity test introduced when
`viewer/src/domain/` lands in Phase 2.0.

### Verification

- `uv run pytest` — 214 / 214 passed (207 prior + 7 new).
- `uv run mypy mashbill/` — Success: no issues found in 17 files.
- `uv run ruff check mashbill/ tests/` — All checks passed.

## [0.14.17] — 2026-05-12

v0.15 structural reset Phase 1.2 — atomic flip. God `SketchNode`
class retired; `SketchNode` is now a 15-way Pydantic discriminated
union dispatched on the `kind` literal. The 4 composition kinds
(metric / step / rule / content) join the per-class family. No
behaviour change; round-trip and migration paths preserved
(D-2026-05-12-B).

### Added

- `mashbill/models.py` — four composition Pydantic classes:
  - `MetricNode` (target / measurement)
  - `StepNode` (order: int | None / outcome)
  - `RuleNode` (policy / enforcement / actor_permissions)
  - `ContentNode` (format / producer_actor_id / consumer_actor_id)
- `mashbill/models.py` — `SketchNode` is now
  `Annotated[Union[15 per-kind classes], Field(discriminator="kind")]`.
  Pydantic dispatches construction / validation on the `kind` literal;
  `CanvasDoc.nodes: list[SketchNode]` automatically narrows.
- `mashbill/models.py` — `SketchNodeAdapter: TypeAdapter[SketchNode]`
  exposed for raw-dict validation outside a `CanvasDoc` wrapper
  (e.g. WebSocket payloads in v0.15 Phase 2).
- `mashbill/models.py` — `BaseNodeFields._details_path_is_safe`
  validator (hoisted from the retired god class) so every per-kind
  class enforces the path-traversal check at construction time.
- `mashbill/models.py` — `ActorRefNode.side` field. Mirrors the
  referenced actor's side so canvases can colour-code without
  dereferencing the master each render.
- `mashbill/migrate.py` — `_V01SketchNode` legacy class. Permissive
  superset that accepts v0.1 raw JSON (including the legacy
  `mission` / `core_values` / `identity` god string fields). Owned by
  the migration module; `models.py` stays clean of legacy concerns.
- `mashbill/migrate.py` — `_v01_to_service` / `_v01_to_composition`
  converters. Translate `_V01SketchNode` instances into current
  per-kind classes at the canvas-build boundary.
- `plot/tests/test_node_models.py` — 10 new tests:
  - 5 round-trip per composition kind (metric / step ordered + unordered
    / rule / content).
  - 5 discriminated-union dispatch via `SketchNodeAdapter`
    (actor / metric / actor_ref-with-validator / unknown-kind /
    missing-kind rejections).

### Removed

- `mashbill/models.py` — god `SketchNode` class (203 LOC, lines
  102-305 in v0.14.16). Every kind's typed-text fields no longer
  pool together as defaults on a single class.
- `mashbill/models.py` — `_REF_KIND_TO_ID_FIELD` map and the god
  `_ref_kind_requires_ref_id` validator. Each ref kind class now
  owns its own validator (added in v0.14.16).
- Tests — `test_typed_fields_default_to_empty` (god polymorphism
  check; replaced by `test_actor_does_not_carry_foreign_typed_fields`
  which now asserts the OPPOSITE: that ActorNode does NOT carry
  Mission's typed fields).

### Changed

- 134 call sites across `mashbill/migrate.py`, `mashbill/folder_io.py`,
  `tests/test_canvas_doc.py`, `tests/test_folder_io.py`, and
  `tests/test_sync.py` migrated from `SketchNode(id=..., kind="X", ...)`
  to the per-kind constructor `XNode(id=..., ...)`. One-shot codemod
  written + applied + deleted (no committed migration scaffolding).
- `mashbill/migrate.py` — `_build_actors_canvas`, `_split_services`,
  `_backfill_actor_sides`, `_ensure_minimum_actors` now consume
  `_V01SketchNode` (legacy) and emit per-kind class instances
  (current). Conversion happens at the function boundary; downstream
  helpers operate on current per-kind classes.
- `tests/test_canvas_doc.py::test_actor_permissions_default_empty`
  rewritten to validate via `SketchNodeAdapter.validate_python(...)`
  (the union exposed by Pydantic) instead of the retired
  `SketchNode.model_validate(...)`.

### Why

The god `SketchNode` was the load-bearing piece of the v0.14
god-object pattern (D-2026-05-12-B, user direct quote: "엔티티 정의도
안되어 있구요... fromJson, toJson 같은걸 쓰고 클래스를 코드로 만들어서
개념화해야 했다"). v0.14.17 ships the principled atomic flip with
zero remaining ruff / mypy debt and zero behavioural regressions
(207 / 207 tests green, up from 197 in v0.14.16 thanks to the new
composition + adapter coverage).

## [0.14.16] — 2026-05-12

v0.15 structural reset Phase 1.1 — server-side per-class Pydantic
models for 7 of the 11 non-Foundation node kinds (D-2026-05-12-B).
Additive only; god `SketchNode` is untouched and remains the type
backing `CanvasDoc.nodes` until v0.14.17 promotes the union.

### Added

- `mashbill/models.py` — seven per-kind Pydantic classes extending
  `BaseNodeFields`:
  - `ActorNode` (motivation / pain / side)
  - `ActorRefNode` (ref_actor_id required + gives / receives)
  - `ServiceNode` (target_side + 6 service-typed fields + do / dont)
  - `CategoryNode` (theme)
  - `MissionRefNode` (ref_mission_id required)
  - `ValueRefNode` (ref_value_id required)
  - `IdentityRefNode` (ref_identity_id required)
- Each ref class carries its own `@model_validator` mirroring the
  dispatch `_ref_kind_requires_ref_id` on god `SketchNode`.
- `plot/tests/test_node_models.py` — 15 tests covering per-class
  round-trip (`Cls.model_validate(Cls(...).model_dump()) == original`),
  ref-id required invariants, and default-field wire parity with the
  god `SketchNode` defaults.

### Why

Per the v0.15 plan (B → A order, no-shim policy), Phase 1 ships
the server SSOT first so viewer entity classes in Phase 2 can mirror
a fully-disciplined Pydantic discriminated union. v0.14.16 is the
additive prep; v0.14.17 promotes `SketchNode` to a 15-way
`Annotated[..., Field(discriminator="kind")]` and retires the god
class.

## [0.14.15] — 2026-05-12

v0.15 structural reset Phase 0 — pre-existing lint / type-check
debt cleared to zero so subsequent phases land on a green baseline
(D-2026-05-12-B). No behaviour change.

### Fixed — `ruff check` → 0 errors

- `mashbill/http_app.py` — import block sorted.
- `mashbill/md_template.py` — extracted `tail` local variable to fit
  the typed-area / free-prose split under the 100-char line limit.
- `mashbill/models.py` — `FoundationNode` discriminated union now
  uses the PEP 604 `X | Y` form instead of `typing.Union[...]`;
  unused `Union` import removed. `_foundation_canvas_rules` error
  message split across two lines.

### Fixed — `mypy mashbill/` → 0 errors

Root causes addressed (not suppressed):

- `mashbill/schema_export.py` — `_FOUNDATION_KIND_CLASSES` now
  declares `dict[str, type[BaseNodeFields]]` so `cls.model_json_schema()`
  resolves against the Pydantic `BaseModel` API instead of the bare
  `ModelMetaclass`. `_node_canvas_schema` return value gets an
  explicit `dict[str, Any]` annotation.
- `mashbill/folder_io.py` — three Foundation-MD helpers
  (`_evict_typed_text_to_md`, `_merge_md_typed_text_into_nodes`,
  `_split_foundation_typed_text_to_md`) narrow `kind = n.get("kind")`
  with an `isinstance(kind, str)` guard before passing to
  `_foundation_md_path` / `parse_md_template` / `render_md_template`
  (which all require `str`, not `Any | None`).
- `mashbill/folder_io.py` — removed an unused
  `# type: ignore[arg-type]` on the legacy project-anchor `shape`
  read; renamed the second `edges` local in
  `_evict_legacy_project_anchor` to `all_edges` to satisfy the
  `no-redef` rule.

### Fixed — formatting

`ruff format` applied across `mashbill/` + `tests/`. 10 files
reformatted; no semantic changes.

### Why

The v0.15 structural reset requires every phase to leave the tree
green at the commit boundary. Inheriting a pre-existing baseline
of 5 ruff + 12 mypy errors would have made each Phase 1.x ship
fight the noise. Zero-debt cleanup commits first, structural
changes afterward.

## [0.14.14] — 2026-05-12

### Changed — Backlog re-prioritised: v0.15.0 structural reset is now next-session top priority (D-2026-05-12-B)

End-of-session user critique surfaced a fundamental
architectural debt the v0.14.x cleanup commits did not touch:

- No domain layer in `viewer/src/`.
- `SketchNode` is a god TypeScript interface holding every
  kind's flat fields (self-admitted at `types.ts:174`).
- No JSON↔domain boundary (`fromJson` / `toJson` patterns
  return 0 hits across `viewer/src`).
- No real classes (`class` / `export class` returns 0 hits).
- `SketchCanvas.tsx` is one god component serving 3 canvases
  via runtime `canvas_kind` discrimination.
- `SketchInspector.tsx` is 1422 LOC branching on `kind` for
  every typed field.

User direct quotes (recorded in D-2026-05-12-B):

- *"엔티티 정의도 안되어 있구요."*
- *"기본을 못하고 있는겁니다."*
- *"코드 재활용 할 수도 없게 해뒀어요. fromJson, toJson
  같은걸 쓰고 클래스를 코드로 만들어서 개념화해야 했다."*
- *"도메인 레이어 설계가 제대로 되어 있는지도 모르겠구요."*

The v0.14.3–v0.14.12 i18n + cleanup commits delivered correct
surface polish but did not address the god object. Honest
correction logged: the assistant should have surfaced the debt
*before* adding more surface work, not after the user flagged it.

### Added — NEXT_SESSION.md trigger entry

`구조 리셋` / `v0.15` / `도메인` / `엔티티` — any of these as
the first session message fires the v0.15.0 structural reset
plan:

- **Phase A — Domain entity classes** (`viewer/src/domain/` with
  15 per-kind classes + fromJson/toJson + invariants +
  discriminated union).
- **Phase B — Server alignment** with `mashbill/models.py`.
- **Phase C — Inspector kind fan-out** (per-kind files).
- **Phase D — Canvas componentisation** (FoundationCanvas /
  ActorsCanvas / ServicesCanvas / ServiceDetailCanvas).
- **Phase E — Cursor / interaction contracts per canvas.**
- **Phase F — Verification.**

### Added — Skills / rules candidate list (user-allowed)

User permission 2026-05-12: *"필요하다면 스킬이나 룰을
만들구요."* Candidates to evaluate at structural-reset session
start (create only those that prove their weight):

- `plot/skills/plot-entity-template/`
- `plot/skills/plot-domain-design/`
- Pre-commit hook `no-god-import` (post-Phase-A)
- Vitest entity-shape round-trip test
- `plot/CLAUDE.md` anti-pattern row: *"Treating raw JSON as
  domain entity (no fromJson boundary)."*

### Parked — old backlog (until structural reset lands)

The 10-item backlog pinned in v0.14.13 is paused. These items
remain valid but should not be picked up before Phase A above:

- i18n audit skill, owner field on SketchNode, Mermaid
  Service-Detail rendering, self-loop visual, Foundation flow
  visual, Novel repository split, isomorphic-git integration,
  MD-as-export migration (user-deferred regardless), snapshot
  work-item layer, v0.15 Actors model migration.

### Not changed

- No code changes. Docs + backlog re-prioritisation only.

### Verification

- Pre-commit gate self-trip → PASS.

## [0.14.13] — 2026-05-12

### Changed — NEXT_SESSION.md backlog pinned (session wrap)

User flagged 2026-05-12 *"이거 다 할일로 지정해두고요"* —
capture every queued item (small wins, meta decisions, mid-size
plans) so the backlog persists into the next session.

Backlog now spelled out across three layers (each layer is a
mirror; pick any one as the source of truth when planning):

- `plot/docs/NEXT_SESSION.md` — three sections (small wins / meta
  decisions / mid-size). 10 items. User picks the next item
  explicitly each session.
- `~/.claude/projects/.../memory/project_plot_next_session.md`
  — full prose with AI's prioritisation analysis +
  repository-split 7-step plan + closed-this-session log.
- TodoWrite (this assistant's session-scoped checklist) — same
  10 items.

### Backlog items recorded (cross-link)

Small wins:
1. i18n audit skill (`plot/skills/plot-i18n-audit/`)
2. `owner` field on `SketchNode`
3. Mermaid Service-Detail rendering UI location
4. Self-loop visual verification (`Service A → Service A`)
5. Foundation single-canvas flow visual check

Meta decisions:
6. Novel repository split (extract `plot/` from noory-ai
   monorepo — AI recommends; user decision)

Mid-size:
7. isomorphic-git integration (PRODUCT_SPEC §6)
8. MD-as-export migration (user-deferred)
9. Snapshot work-item layer
10. v0.15 Actors → v0.13 model (re-evaluate after #8)

### Verification

- Pre-commit gate self-trip → PASS (no code changes; docs +
  plugin.json + CHANGELOG only).

## [0.14.12] — 2026-05-12

### Changed — PRODUCT_SPEC.md revision 2 (D-2026-05-12-A)

User delivered a substantially revised product spec. The new
material:

- **Language split:** Novel is a "mindmap" to users, "graph"
  internally. Cycles + self-loops are part of the model.
- **`isomorphic-git`** added to the tech stack.
- **Source-data version control** is now an explicit subsystem
  (§6 of PRODUCT_SPEC). Canvas JSON / user stories / tasks are
  git-versioned independent of any source-code repo. Snapshot ≡
  commit; agent proposal ≡ branch; user approve ≡ merge.
- **Foundation = one canvas** (Mission + Core value + Identity).
  Resolves the v0.14.7 open question. Audience distinction is
  visual, not structural.
- **Service-Detail starts empty,** fills bottom-up through
  agent-interview + user-story loop. Living document.
- **Service interview produces two artefacts** — Service-Detail
  content + user-story draft, shared provenance.
- **Feedback loop is git-branch shaped** per the new §6.
- **GitHub integration** added to future items.
- **MVP scope section removed** — rev-1 framing dropped.

### Queued — open questions

PRODUCT_SPEC §15 reorganised. Closed: Mission/Identity canvas
split. Added:

- MD-as-export migration (today's co-equal MD becomes derived
  from JSON). Deferred per user direction *"이 부분은 나중에
  다시 다듬어 봅시다."*
- isomorphic-git integration timing.
- i18n string lifecycle skill (delete unused keys) — user
  flagged *"사용되지 않는 것들 삭제하고 하는 거 관리되어야해요."*
- Novel repository split (move out of noory-ai monorepo) — user
  flagged for analysis.

### Not changed (deliberate)

- No code changes — spec-only update.
- SPEC.md / CONCEPTS.md / ROADMAP.md unchanged. Each will get
  its own update when the queued items (MD-as-export, git,
  Foundation merger if not already that way) land.

## [0.14.11] — 2026-05-12

### Added — i18n: Stencil draggable preset labels

Final stencil-side i18n step. Migrates the labels that appear
inside each draggable preset card in `SketchStencil` (visible in
every per-canvas stencil), plus the tooltip / drop-hint text on
the same cards.

**New `stencil.*` keys:**

- `subActor` (Sub-Actor / 서브 액터)
- `dragOntoCanvas` (interpolated `{{name}}`)
- `dropHintIntoCategory` / `dropHintIntoService` /
  `dropHintIntoActor` — replace the three hardcoded English
  drop-hints.

### Changed

- `plot/viewer/src/canvases/SketchStencil.tsx`:
  - `StencilPreset` interface gains optional `labelI18nKey` and
    `dropHintI18nKey` fields.
  - Sub-Actor preset declares `labelI18nKey: "stencil.subActor"`
    (its kind is "actor" so the default `kind.${kind}` fallback
    would conflict with `TOP_LEVEL_ACTOR`).
  - SERVICE_INSIDE_CATEGORY / metric / step / sub-actor declare
    their `dropHintI18nKey`.
  - `StencilItem` renders with `useTranslation()`; resolves the
    label via (preset.labelI18nKey ?? `kind.${preset.kind}` ??
    preset.labelHint). Resolves the drop-hint title similarly.
    The drag-onto-canvas fallback tooltip uses the interpolated
    `stencil.dragOntoCanvas` key.
  - `onDragStart` data-transfer payload strips the new i18n key
    fields (alongside `id` / `labelHint` / `dropHint`) before
    serialising the preset.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` → 14/14 (parity active).
- Browser smoke (Playwright KO on Services): stencil reads
  최상위 / 카테고리 / 서비스 + "카테고리 안에 놓으세요" drop
  hint. Confirmed via direct screenshot.
- Pre-commit gate self-trip → PASS.

### Out of scope

The *initial label of the dropped node* (`preset.label`) stays
language-pinned (English by default). Rationale: as soon as the
drop lands, that string is user data — the user will edit it.
Localising the drop time would create asymmetric data (KO user's
node "미션", EN user's node "Mission") which is wrong: it's the
same project, viewed in different locales. The stencil-side
label (visible only while dragging) follows locale; the dropped
node's label is data and stays as-is.

### Queued — separate diagnosis

- "❀ ❀ ❀" Inspector MD preview font fallback investigation.
- "1 validation error for CanvasDoc Val…" toast briefly during
  Inspector load — verify whether it persists.

## [0.14.10] — 2026-05-12

### Added — i18n: composition lists + Long-form details + Actor placeholder (Phase C)

Final Inspector i18n phase. Migrates the remaining Service
composition lists (Rules / Contents), the Long-form details
section, and the Actor v0.3 placeholder.

**New `composition.*` keys:**

- `add` (+ Add / + 추가)
- `expand` / `collapse` (펼치기 / 접기)
- `namePlaceholder` (Name / 이름)
- `remove` (Remove / 삭제)
- `confirmRemove` (interpolated `{{name}}`)
- `untitled` ((untitled) / (이름 없음))
- `rules` (Rules / 규칙)
- `rulesSubtitle` ("정책 · 제약 · SLA · 권한" — user-approved)
- `contents` (Contents / 콘텐츠)
- `contentsSubtitle` ("아티팩트 · 결과물 · 자산" — user-approved)

**New `inspector.*` keys:**

- `actorCompositionDeferred` ("v0.3 에서 액터 구성(권한 · 기능 ·
  목표 · 상태)을 지원할 예정입니다." — user-approved)
- `longFormDetailsHeader` (장문 상세)
- `longFormDetailsIntro` (Korean retained verbatim; English
  translation user-approved)
- `createDetails` (📁 상세 만들기)
- `creating` (생성 중…)

All new hint sentences in this commit went through the
`AskUserQuestion` review workflow per `I18N_KO_GLOSSARY.md` §3.

### Changed

- `plot/viewer/src/canvases/SketchInspector.tsx`:
  - `CompositionList` migrated (title / subtitle pass-through;
    `+ Add` button; empty-state placeholder).
  - `CompositionRow` migrated (expand / collapse aria + title;
    Name placeholder; Remove confirm dialog with `{{name}}` +
    `(untitled)` fallback; Remove aria-label).
  - `DetailsSection` migrated (header; intro paragraph; busy
    label; idle label).
  - Actor v0.3 placeholder migrated.
- `plot/viewer/src/i18n/locales/{en,ko}.json` — ~15 new keys.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` → 14/14 (parity active).
- Browser smoke (Playwright KO on Services → Login Inspector):
  서비스 / 라벨 / ✕ 삭제 / 장문 상세 / 📁 상세 만들기 / 대상
  측 운영자측 / 무엇 / 만드는 가치 / 범위 / 트리거 / 방법 /
  결과 / 할 것 / 하지 말 것. Category node badge reads 카테고리.
- Pre-commit gate self-trip → PASS.

### Queued — v0.14.11 (Stencil draggable labels)

The labels INSIDE each draggable preset in `SketchStencil`
("Mission" / "Core Value" / "Identity" / "Actor" / "Sub-Actor" /
"Category" / "Service" / "Metric" / "Step" / "Rule" / "Content")
are still English. They render via `StencilPreset.label`
hardcoded in TS module-level constants. Migration needs a
runtime t() call at the StencilItem render site (since module-
level constants can't call hooks). Small follow-up commit.

### Queued — separate diagnosis (deferred)

- "❀ ❀ ❀" Inspector MD preview font fallback investigation.
- "1 validation error for CanvasDoc Val…" toast briefly visible
  during Inspector load — not regression (pre-existing, surfaced
  by Playwright nav timing). Worth a closer look if it persists.

## [0.14.9] — 2026-05-12

### Added — i18n: Inspector typed-field labels per kind (Phase B)

Continues v0.14.8. Migrates every Inspector typed-field section
across all node kinds (Mission / Category / Service / actor_ref /
Actor / Metric / Step / FoundationRef / CoreValue / Identity /
DoDont / Rule / Content). All section headers reuse the
`kind.*` SSOT from v0.14.8.

**New `inspector.field.*` keys** (label per field):

- theme / whatWeDo / why / direction / targetSide / what /
  valueCreated / scope / trigger / how / outcome / policy /
  enforcement / actorPermissions / format / producer / consumer /
  definition / description / side / motivation / pain / target /
  measurement / order / gives / receives / do / dont /
  longFormDetails.

**New `inspector.fieldHint.*` keys** (italic hint per field).
Translated to natural Korean per the new
[`I18N_KO_GLOSSARY.md`](docs/I18N_KO_GLOSSARY.md) workflow.

**Misc new `inspector.*` keys** (modal flow + select options):

- `valueFlowHeader` (이 서비스 ↔ 이 액터 가치 흐름 헤더)
- `referencesHeader` (interpolated `{{label}}`)
- `rePick` / `unset` / `empty` /
  `operatorOption` / `userOption` / `operatorSideOption` /
  `userSideOption` / `bothSideOption` /
  `addActorPermission` / `permissionRemove` / `masterNotFound`.

### Added — `plot/docs/I18N_KO_GLOSSARY.md`

New doc capturing:

1. Canonical Novel vocabulary (Korean spellings the project
   commits to — 미션 / 코어밸류 / 아이덴티티 / 액터 / 서비스 /
   파운데이션 / 등).
2. UI-context fragments (Undo / Redo / Delete / etc.).
3. **Hint-sentence review process** — before committing new
   `inspector.fieldHint.*` strings, surface them via
   `AskUserQuestion` for review. The AI-translated-Korean
   failure mode (e.g. 측면별로 → 속성별로) is structural, not
   one-off, so the workflow needs a gate.
4. Correction log — every user-driven Korean fix gets a row so
   the same mistake does not repeat across sessions.

### Fixed — Korean translation drift caught by user 2026-05-12

- `stencil.note.identityOnePerAspect`: 측면별로 하나씩 →
  **속성별로 하나씩** (user direction; 측면 is unnatural in this
  register).
- `IdentityFields` description placeholder: 이 측면이 어떻게
  드러나는가 → **이 속성이 어떻게 드러나는가** (same rule).
- `ActorFields` motivation placeholder: "이 actor 가 …" →
  **"이 액터가 …"** (canonical naming consistency).

### Changed

- `plot/viewer/src/canvases/SketchInspector.tsx` — every
  `<Fields>` subcomponent (10 of them) gained `useTranslation()`;
  ~50 hardcoded label / hint strings replaced with `t()`
  lookups; per-kind section headers now read from `kind.*`.
- `plot/viewer/src/i18n/locales/{en,ko}.json` — net ~40 new keys.

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` → 14/14 passed (parity test active; en/ko
  remain in sync).
- Browser smoke (Playwright KO on Foundation): Mission node →
  Inspector header shows 미션 + 라벨 + ✕ 삭제; Mission section
  reads 미션 / 하는 일 — 현재형으로 표현한 매일의 활동 / 이유
  — 존재 이유 / 방향 — 포지셔닝 (공간이지 시간이 아님). Stencil
  reads 속성별로 하나씩 — 목소리, 에너지, 말투, …
- Pre-commit gate self-trip → PASS.

### Queued — Phase C (v0.14.10)

- Composition items (Name placeholder, Remove, Expand / Collapse,
  Rules / Contents tab labels).
- "Creating…" / "📁 Create details" button.
- Foundation-ref label prefix (already handled in Phase B
  references header; verify no straggler).
- `body` placeholder / Edge modal headers.

### Queued — separate

- "❀ ❀ ❀" Inspector MD preview font fallback investigation.

## [0.14.8] — 2026-05-12

### Added — i18n: kind labels SSOT + Inspector header / actions / Label

Continues the v0.14.4 → v0.14.6 i18n rollout. This is **Phase A**
of the Inspector migration. Two more phases follow (typed-field
section labels per kind, then composition items / modals / misc).

**New `kind.*` namespace** — canonical Novel kind names per
locale. Korean follows the user-provided product spec's canonical
vocabulary (2026-05-11):

- project / actorRoot / node / mission / core_value / identity /
  actor / actor_ref / mission_ref / value_ref / identity_ref /
  service / category / metric / step / rule / content.

Korean values: 프로젝트 / 액터 루트 / 노드 / 미션 / 코어밸류 /
아이덴티티 / 액터 / 액터 (참조) / 미션 (참조) / 코어밸류 (참조)
/ 아이덴티티 (참조) / 서비스 / 카테고리 / 지표 / 단계 / 규칙 /
콘텐츠.

**New `kindTag.*` namespace** — the small UPPERCASE label
painted top-left of each node (`SketchNode`). Subset of kinds
that get the visual badge per `KIND_TAG_KINDS`: project / mission
/ core_value / identity / metric / step / category.

**New `inspector.*` keys** — header bar + actions + Label field:

- label / deleteNode / deleteShort / confirmDelete (interpolated
  `{{name}}`).
- narrow / widen / narrowInspector / widenInspector /
  closeInspector.
- mdWarnings / mdWarningsFixHint (HTML-interpolated `{{path}}`,
  rendered via `dangerouslySetInnerHTML` for the `<code>` tag).

### Changed

- `plot/viewer/src/canvases/SketchNode.tsx` — replaced the
  hardcoded `KIND_TAG_LABELS` lookup with a membership-only
  `KIND_TAG_KINDS` set + `t(\`kindTag.${kind}\`)` lookup. The
  badge text now follows the user's locale.
- `plot/viewer/src/canvases/SketchInspector.tsx` — `useTranslation()`
  in `SketchInspector`; kind badge in header reads from `kind.*`
  with the `project` / `actorRoot` fallback chain; delete button
  text + tooltip + confirm dialog use `inspector.*`; narrow/widen
  + close labels + tooltips use `inspector.*`; MD warnings panel
  header + fix hint (with `<code>{{path}}</code>` interpolation)
  use `inspector.mdWarnings*`; Label field heading uses
  `inspector.label`.
- `plot/viewer/src/i18n/locales/ko.json` — retroactive label fix
  per user direction: `canvas.tabs.foundation` 토대 → **파운데이션**.
  (v0.14.5 shipped 토대; v0.14.6 corrected actors 행위자 → 액터;
  this commit completes the canonical-naming pass on the tabs.)

### Verification

- `npx tsc --noEmit` clean.
- `npx vitest run` → 14/14 passed (parity test still passes;
  `kind` + `kindTag` + `inspector` keys present in both locales).
- Browser smoke (Playwright KO sweep on Foundation): node badges
  read 미션 / 코어밸류 / 아이덴티티; Inspector top-bar reads 미션
  + ✕ 삭제 + 라벨; tabs read 파운데이션 / 액터 / 서비스.
- Pre-commit gate self-trip → PASS (styles.css not touched).

### Queued — Phase B (v0.14.9)

- Inspector typed-field section labels per kind:
  - Mission: What we do / Why / Direction.
  - Core value: Definition / Do / Don't.
  - Identity: Description / Do / Don't.
  - Actor: Side / Motivation / Pain / Target side.
  - Service: What / Value created / Scope / Trigger / Outcome /
    Theme.
  - actor_ref: Gives / Receives.
  - step: Order / Outcome.
  - metric: Target / Measurement.
  - rule: Policy / Enforcement / Actor permissions.
  - content: Format / Producer / Consumer.
  - Long-form details.

### Queued — Phase C (v0.14.10)

- Composition items (Name placeholder, Remove, Expand/Collapse).
- Inspector edit / split / preview tabs.
- Foundation refs label ("Actor:" prefix).
- Inspector "Create details" button.
- ⚠ MD preview "❀ ❀ ❀" font fallback investigation.

## [0.14.7] — 2026-05-11

### Added — `plot/docs/PRODUCT_SPEC.md` (D-2026-05-11-E)

User delivered a Novel product spec mid-session covering platforms,
business model, tech stack, data principles, Figma-style symbol
system, four canvas layers, agent-interview UX, snapshot work-item
layer, PR-style feedback loop, MVP scope, future items. Per user
direction *"이건 잘 정리해두세요"* the spec is pinned as a new
canonical document.

**Position:** PRODUCT_SPEC sits *above* VISION.md in the doc set.
VISION = the essence; PRODUCT_SPEC = how the essence becomes a
shippable product (platforms, business model, MVP scope).

**Translation:** Korean source → English per noory-ai CLAUDE.md
"Language" rule. Korean vocabulary preserved where it's a Novel
term (Mission / Core value / Identity / Actor / Service / User
journey / Snapshot).

**Open questions captured in §16** (not decided in this commit):

1. `owner` field on every node — multi-user prerequisite. Land
   date unset.
2. Mission-Core-value vs Identity canvas split (audience: humans
   vs agents). Today both live in Foundation.
3. PR-style feedback loop enforcement — MCP tools today write
   directly.
4. Snapshot work-item layer — net-new subsystem.
5. Mermaid Service-Detail rendering — UI location unset.
6. `canvas.tabs.foundation` Korean label review if Mission /
   Identity canvases split.

### Changed

- `plot/docs/VISION.md` — Cross-references now point at
  PRODUCT_SPEC first.
- `plot/CLAUDE.md` — reading order updated; PRODUCT_SPEC is step
  2 (right after VISION, before DOMAIN).
- `plot/docs/DECISIONS.md` — new D-2026-05-11-E entry pinning the
  decision.

### Not changed (deliberate)

- No code changes.
- No canvas / kind / Inspector behaviour changes.
- SPEC.md / CONCEPTS.md / ROADMAP.md / DOMAIN.md left as-is — each
  remains the source of truth for its own concern. PRODUCT_SPEC
  cross-links into them.

## [0.14.6] — 2026-05-11

### Added — i18n migration: Stencil section headers + helper notes

Continues v0.14.5. Migrates the SketchStencil's per-canvas section
labels and helper notes across all four canvases (Foundation /
Actors / Services / Service-Detail).

Korean translations align with the canonical Novel vocabulary
provided by the user 2026-05-11:

> 심볼 종류: 미션, 코어밸류, 아이덴티티 / 액터 / 서비스

So Korean reads as 미션 / 코어밸류 / 아이덴티티 / 액터 / 서비스 —
NOT a literal "정체성" / "행위자" / "핵심 가치" translation.

### Translated keys added

`stencil.section.*`:
- mission / coreValues / identity / topLevel / actorHierarchy /
  service / composition / actors / missions / identityAspects

`stencil.note.*`:
- addAsManyAsYouNeed (필요한 만큼 추가하세요)
- identityOnePerAspect (측면별로 하나씩 — 목소리, 에너지, 말투, …)
- dropOnActor (액터 위에 놓으세요)
- dropInsideCategory (카테고리 안에 놓으세요)
- compositionInsideService (이 서비스 안의 지표 + 단계)
- dragActorOntoService (이 서비스에 액터를 끌어 놓으세요)
- dragMissionThisServiceAnswersTo
- dragValueThisServiceEmbodies
- dragIdentityAspectThisServiceExpresses

### Changed

- `plot/viewer/src/canvases/SketchStencil.tsx` — `useTranslation()`
  in `SketchStencil`; replaced 10 hardcoded `title=` props and 8
  hardcoded `note=` props with `t()` lookups across the four
  per-canvas branches.
- `plot/viewer/src/i18n/locales/ko.json` — `canvas.tabs.actors`
  corrected from "행위자" to "액터" per the user-provided product
  spec's canonical naming. (Was set in v0.14.5; before that locale
  reached any user, so retroactive fix in the same i18n rollout.)

### Verification

- `npx tsc --noEmit` → clean.
- `npx vitest run` → 14/14 passed (parity test catches en/ko
  drift).
- Browser smoke (Playwright KO sweep): Foundation stencil shows
  미션 / 코어밸류 / 아이덴티티 with the new notes. Tabs read
  토대 / 액터 / 서비스 as expected.
- Pre-commit gate self-trip → PASS (styles.css not touched).

### Queued for v0.14.7+

- Inspector form labels (largest single migration surface; will
  land as its own commit / session).
- Novel product spec → `plot/docs/PRODUCT_SPEC.md` consolidation
  per user direction 2026-05-11 ("이건 잘 정리해두세요. 작업 다
  끝나고").
- "❀ ❀ ❀" MD preview font fallback investigation.

## [0.14.5] — 2026-05-11

### Added — i18n migration: canvas tabs + Mark session + Service-Detail modal header

Continues the v0.14.4 i18n rollout. Migrates the next-most-visible
surface: the three canvas tab labels at the top of the viewer, the
"Mark session…" button + its hint, and the Service-Detail modal's
header / aria-label / close-button.

**Translated keys added to `en.json` + `ko.json`:**

- `canvas.tabs.foundation` / `canvas.tabs.actors` / `canvas.tabs.services`
  — 토대 / 행위자 / 서비스.
- `header.markSession` / `header.markSessionHint` — 세션 기록… /
  현재 프로젝트 상태에 git 태그를 찍습니다.
- `serviceDetail.label` — 서비스 상세.
- `serviceDetail.ariaWithCategory` / `serviceDetail.ariaWithoutCategory`
  — interpolation-driven aria-label so screen readers see the
  Korean "서비스 상세 — {category} › {service}" form.

**Changed:**

- `plot/viewer/src/App.tsx` — replaced hardcoded `CANVAS_TABS`
  label table with `CANVAS_TAB_IDS` + `t("canvas.tabs.{id}")`,
  switched `aria-label="Canvas"` to `t("canvas.aria")`, swapped
  the `Mark session…` button text + hint, and rewrote
  `ServiceDetailModal` to read all visible / aria text from i18n
  (including the close-button label/title via the existing
  `shell.closeEsc` key).

### Out of scope this release (queued for v0.14.6+)

- Stencil section headers (TOP-LEVEL, MISSION, CORE VALUES,
  IDENTITY, ACTOR HIERARCHY, COMPOSITION, ACTORS, IDENTITY
  ASPECTS) and helper hints ("add as many as you need", "drop
  inside a Category", "drop on an Actor").
- Inspector form labels and section headers (largest single
  migration surface; will land as its own commit / session).
- Investigation: Inspector MD preview renders `* * *` separators
  as "❀ ❀ ❀" — looks like a font fallback issue, queued for
  separate diagnosis.
- Decision: Novel kind labels (Mission, Core Value, Identity,
  Actor, Service, Category, …) shown inside nodes — stay English
  as canonical kind names vs. localise? Will surface as an
  AskUserQuestion before the v0.14.6 Stencil migration lands.

## [0.14.4] — 2026-05-10

### Added — i18n infrastructure (English primary, Korean locale) — D-2026-05-11-D

Novel is being positioned as a global service (user direction
2026-05-10: *"이건 글로벌 서비스가 될거거든요"*). This release
boots the i18n stack and migrates the most visible UI strings.
Remaining hardcoded text (Inspector forms, Stencil, modals,
context menus, App-level toasts) is queued for follow-up commits;
the new anti-pattern row + parity test prevent NEW hardcoded text
from leaking in.

**New module — `plot/viewer/src/i18n/`:**

- `index.ts` — bootstraps `i18next` + `react-i18next` +
  `i18next-browser-languagedetector`. Detection order
  `localStorage["plot:lang"] → navigator.language → en`. Fallback
  `en`. Imported for side effects from `main.tsx`.
- `locales/en.json` — primary resource bundle.
- `locales/ko.json` — Korean locale.
- `LanguageToggle.tsx` — compact EN / KO pill rendered at the
  bottom of `SketchSidebar`. Choice persists via localStorage.

**Migrated strings (this commit):**

- `SketchToolbar.tsx` — Undo / Redo button labels + tooltip
  shortcuts.
- `SketchSidebar.tsx` — collapse / expand controls, "Projects"
  header, "+ New project" button, "(none yet)" placeholder,
  per-project Rename / Delete buttons + confirm dialogs, "Session
  tags" section + per-tag confirm dialogs + delete tooltips.

**Guards:**

- `plot/viewer/tests/i18n-keys-parity.test.ts` — Vitest static
  guard asserting `ko.json` has the identical key set as `en.json`
  and every value is a non-empty string. Locale drift is a build
  failure.
- `plot/CLAUDE.md` anti-patterns table — new row "Hardcoding
  user-facing UI text in a viewer component", pointing to
  D-2026-05-11-D.

**Dependencies added:** `react-i18next ^15`, `i18next ^23`,
`i18next-browser-languagedetector ^8`. ~30KB cost (production
build) is acceptable for a viewer that already ships Mermaid +
React Flow + React Markdown.

**Out of scope this release** (queued for follow-up):

- Inspector typed-field labels per kind (largest single migration
  surface).
- Stencil draggable labels.
- Modal headings and confirm dialogs in `SketchModals`.
- App-level toast / error messages.
- Context-menu items.

## [0.14.3] — 2026-05-10

### Added — Cursor ⊥ auto-layout structural gate (D-2026-05-11-C)

Concludes the architectural review queued via the `NEXT_SESSION.md`
"다음" trigger filed in D-2026-05-11-B.

**Diagnosis:** the perceived cursor ↔ auto-layout coupling was
*cognitive (commit bundling in v0.13.10)*, not *mechanical (shared
files)*. Empirical verification of v0.13.7..v0.14.2 git history:
`viewer/src/styles.css` was never modified by any auto-layout
commit, and `autoLayout.ts` was never modified by any cursor
commit. The cursor flicker root cause (RF v11 `role="button"` +
Tailwind preflight) had existed since v0.13.0; the auto-layout
work merely surfaced it during browser verification.

**Three orthogonal enforcement mechanisms ship in this release:**

- `plot/hooks/pre_commit_gate.py` — new
  `cross_cutting_bundle_check()` denies commits that stage
  `viewer/src/styles.css` (cross-cutting visual SSOT) alongside
  feature code under `viewer/` or `mashbill/`. Tests excluded from
  the "feature" category.
- `plot/viewer/tests/styles-cursor-baseline.test.tsx` — static
  Vitest guard asserting `styles.css` contains zero cursor
  declarations outside comments. Adding a cursor rule requires a
  fresh `D-YYYY-MM-DD-X` decision id and updating the test
  together — the audit trail becomes mechanical.
- `plot/agents/plot-verifier.md` — Step 4 default now runs the
  cursor DOM probe sweep FIRST on every viewer change, regardless
  of declared change kind. Latent cross-cutting visual regressions
  cannot hide behind unrelated feature commits.
- `plot/CLAUDE.md` anti-patterns table — new row "Bundling a
  cross-cutting visual change with a feature change in one
  commit", pointing to D-2026-05-11-C.

**No viewer behaviour change. No DOMAIN.md change** — DOMAIN.md
line 205 already correctly characterises cursor as cross-cutting
with no natural domain home. The right enforcement layer is
commit hygiene + static guard + verification default, not domain
re-modelling.

Code-level alternatives (extract `cursorContract.ts` module,
refactor `useNodesMemo` / `useEdgesMemo`) considered and rejected
as YAGNI — `styles.css` is 27 LOC with zero cursor rules
post-v0.14.2, and the ghost-edge symptom from v0.13.9 was already
resolved by D-2026-05-10-G.

## [0.14.2] — 2026-05-11

### Removed — All cursor cancellation rules; pure RF default + Tailwind preflight

User direction: *"일단 RF 기본으로 돌리라구요. 이해를 못하지?"* The
v0.13.6 (D-2026-05-10-C) and v0.13.10 (D-2026-05-10-F) Tailwind
preflight cancellation rules were the assistant repeatedly forcing
`node = grab` to match RF's nominal default — but the user's
mental model was always "node = pointer (clickable), pane = grab
(pannable), handle = crosshair (drawable)" which is **exactly what
pure RF default + Tailwind preflight composes to** with zero
overrides.

`viewer/src/styles.css` now contains only `@tailwind` imports and
`html/body/#root` sizing. Resulting cursors:

| Region | Cursor | Source |
|---|---|---|
| `.react-flow__pane` | `grab` / `grabbing` | RF default |
| `.react-flow__node` (RF v11 sets `role="button"`) | `pointer` | Tailwind preflight `[role="button"]` |
| `.react-flow__node.dragging` | `grabbing` | RF default beats preflight via specificity |
| EditableText label span (`role="button"`) | `pointer` | Tailwind preflight |
| Fold `<button>` | `pointer` | Tailwind preflight |
| `.react-flow__handle.connectionindicator` | `crosshair` | RF default |
| Resize controls | `ew/ns/nwse/nesw-resize` | `@reactflow/node-resizer` default |

Anchor body shows `grab` because the anchor uses a static `<span>`
(no EditableText, no `role="button"`); the inner divs inherit the
parent's cursor without preflight matching them. Acceptable
asymmetry per D-2026-05-11-A.

### Removed — MiniMap (bottom-right overview)

User: *"오른쪽 아래에 있는 오버뷰? 이거 없애요."* Drop the
`<MiniMap zoomable pannable />` and its import from
`viewer/src/canvases/SketchCanvas.tsx`. The lower-right corner is
now empty.

### Added — `plot/docs/NEXT_SESSION.md` queue + SessionStart hook integration

User: *"다음세션에서 심층적으로 검토하고 개선할 수 있게 해두세요.
다음세선서 '다음' 이라고 하면 이거 해야해요."*

A new `plot/docs/NEXT_SESSION.md` file holds keyword-triggered tasks
that the assistant should pick up at the next Novel session start.
The first queued item: **`다음`** ⇒ architectural review of how
auto-layout work bled into cursor code (see D-2026-05-11-B for
context, NEXT_SESSION.md for full scope).

`plot/hooks/session_start.py` reads `NEXT_SESSION.md`'s "Active
queue" section and surfaces each `### \`<TRIGGER>\` — <title>`
heading in the SessionStart `additionalContext`. The assistant
watches the user's first message; if it contains a trigger keyword,
that item becomes the active task.

### Added — DECISIONS.md entries

- **D-2026-05-11-A** — Pure RF default cursors + MiniMap removal,
  with the lesson "default to NO cursor rules in `styles.css`".
- **D-2026-05-11-B** — Architectural concern: auto-layout work
  affected cursor code; review queued for next session via the
  `다음` trigger.

### Updated — SPEC.md / CURSOR.md

Both rewritten to reflect "no overrides" and the resulting cursor
table. CURSOR.md change-history extended with the v0.14.2 entry.

### Verification

- `tsc --noEmit`: clean.
- `vitest run`: 11/11 passing.
- Playwright probe: pane=`grab`, mission body span=`pointer`,
  handle=`crosshair`, anchor body=`grab` (asymmetry as documented),
  MiniMap absent.
- SessionStart hook smoke test: VISION + 5 DECISIONS + `다음`
  trigger all surfaced in `additionalContext`.

## [0.14.1] — 2026-05-10

### Removed — Auto-layout (again)

User cost/benefit call: *"근데 auto layout 빼야겠네 문제가 너무 많다.
넣고 나서 커서 들에 문제 너무 많고."*

The feature added across v0.13.8 (spec) → v0.13.9 (impl) → v0.13.10
(button placement) carried more debugging / verification load than
its current value justified. Novel has no users with complex
multi-actor / multi-service graphs yet; the layout-readability
benefit is theoretical at this stage. Re-introduction in the future
needs a fresh decision id with concrete user workflows in evidence.

### Honest correction — cursor problems were not caused by auto-layout

The user temporally associated cursor flicker with auto-layout
(*"넣고 나서 커서 들에 문제 너무 많고"*). The actual root cause was
unrelated and was diagnosed + fixed in v0.13.10 (D-2026-05-10-F):
RF v11 sets `role="button"` on `.react-flow__node`; Tailwind preflight
matches that selector and overrides the RF default `cursor: grab`.
The Tailwind preflight cancellation rule in `viewer/src/styles.css`
fixes the flicker independently of auto-layout's existence. This
removal therefore does not undo any cursor fix — Novel v0.14.1 still
has uniform `grab` on pane and nodes, no flicker.

### Files removed

- `viewer/src/canvases/sketch/autoLayout.ts` (297 LOC pure algorithm).
- `viewer/src/canvases/sketch/useAutoLayout.ts` (43 LOC React bridge).
- `viewer/tests/autoLayout.test.ts` (11 unit tests).

### Files reverted

- `viewer/src/canvases/SketchCanvas.tsx`:
  - Drop `ControlButton` from the React Flow imports.
  - Drop `useAutoLayout` import.
  - Drop the `applyAutoLayout` hook call and the `<ControlButton>`
    block inside `<Controls>`.
  - LOC 366 → 360 (back to the v0.13.7 baseline).
- `viewer/tests/SketchCanvas.regression.test.tsx`:
  - The `'toolbar does not render an Auto layout button'` test from
    v0.13.8 is restored (with a new comment block referencing the
    full lineage D-2026-05-04-D → -10-E → -10-G).

### Documentation

- `docs/SPEC.md` §Auto-layout — rewritten to "Removed" with a single
  history paragraph linking the four-decision lineage.
- `docs/DECISIONS.md`:
  - **D-2026-05-10-E** marked **Rejected (rolled back v0.14.1)** with
    a forward pointer to D-2026-05-10-G.
  - **D-2026-05-10-G** new entry, Accepted, with the cost/benefit
    reasoning + the cursor-causation correction + the
    re-introduction policy (must cite real-user workflows and
    cost/benefit comparison).

### Verification

- `tsc --noEmit`: clean.
- `vitest run`: 11/11 passing (24 → 11 because the 11 auto-layout
  tests were deleted with their source; the remaining 11 cover
  every other regression and pass after the inverted auto-layout
  test was re-inverted).

## [0.14.0] — 2026-05-10

### Added — Novel dev infrastructure (the "AI develops Novel reliably" milestone)

After two weeks of tactical fixes (six rounds on cursor; auto-layout
misattributed; SPEC drift across sessions), the user's diagnosis cut
through: *"플러그인 설치가 되어 있는데? 왜? 그러지? ... 진짜 큰일이네
... 필요한 스킬, 룰, 서브 에이전트들, 다 만들면서 해야 제대로 빠르고
효율적으로 일 할 수 있습니까? 그럼 그렇게 하구요."*

The fix is structural: replace human-memory-dependent rules with
deterministic infrastructure that fires automatically. This release
ships the full set so the next session inherits a workable AI dev
environment instead of starting from "be careful next time."

#### `docs/VISION.md` (new) — single-source-of-truth essence

The one sentence that overrides every other priority:

> **Novel 은 본질을 모르는 사람이 본질을 찾고, 그걸 놓치지 않으면서, 그
> 본질 아래에서 서비스를 쉽게 기획·개발할 수 있게 AI 와 협업하는
> 툴이다.**

Plus the three-phase cycle (Discovery / Retention / Execution with
AICollaboration cross-cutting), who Novel is for, the feature-decision
checklist, and a banned-pattern table calibrated to past drift
(cursor 6 rounds; auto-edges D-2026-05-04-A; auto-layout removal
D-2026-05-04-D).

#### `docs/DOMAIN.md` (new) — bounded contexts + ubiquitous language

Translates VISION into 5 bounded contexts:

- **EssenceDiscovery** — Foundation canvas, Inspector typed text
- **EssenceRetention** — anchor injection, cross-canvas refs
- **EssencePlanning** — Actors / Services, value-flow, auto-layout
- **EssenceExecution** — Service-Detail, MCP tools
- **AICollaboration** — cross-cutting (skills, hooks, agents, MCP)

Each context names its surfaces, what it owns vs not, current code
home (with file paths), and where current code violates the model
(refactor candidates with severity).

Plus the ubiquitous language table that disambiguates Novel terms
("Node" vs "rf-node" vs DOM node, "Service" vs REST service, etc.),
the entity-vs-VO classification, and the dependency-direction
mermaid that codifies "EssenceExecution may read EssenceDiscovery
but not the reverse."

#### `skills/plot-frontend-bug-diagnosis` (new) — Playwright probe-first

The deterministic procedure that v0.13.10 finally stumbled on after
six failed cursor rounds. Triggers on `cursor / hover / pointer /
hit-test / flicker / 깜빡` keywords. 10 mandatory steps:

1. Verify Playwright + dev server.
2. Navigate to affected canvas.
3. Baseline screenshot.
4. Cursor / hit-test probe at suspect coordinates (templates included).
5. Walk parent chain to find the cursor source.
6. Identify source rule (CSS file + selector + line).
7. Propose fix anchored to probe.
8. Apply fix, re-probe.
9. Confirmation screenshot.
10. Update SPEC + CURSOR + DECISIONS per Gate 0.

Banned shortcuts table (5 patterns) + quick-reference for common Novel
cursor bug patterns.

#### `skills/plot-feature-tdd` (new) — essence-anchored test-first

Triggers on `feature / 기능 추가 / 만들어줘 / add / implement`. 10
mandatory steps:

1. Re-read VISION.md first sentence.
2. Identify VISION phase.
3. Look up bounded context in DOMAIN.md.
4. Sketch entity / VO touched.
5. Check SPEC.md for existing coverage.
6. Write regression test FIRST (Red).
7. Implement minimally (Green).
8. Browser-verify with `plot-verifier` agent.
9. Update SPEC + DECISIONS + CHANGELOG (Gate 0).
10. Commit + push (Gate 4).

Non-negotiables table (test first; one context per change; no SPEC
drift; browser-verify all UI changes; never grow oversize files;
never auto-emit user-visible state).

#### `hooks/session_start.py` (new) — surface VISION + recent DECISIONS

Runs on every Claude Code session start when the mashbill plugin is
loaded. Emits an `additionalContext` payload that prepends to the
assistant's system prompt:

- VISION.md essence sentence verbatim.
- Last 5 DECISIONS.md headings.
- Pre-action gate list (Gate -1 → Gate 4).
- Available skills.

This is the deterministic answer to "the assistant forgets what we
agreed last session." Output verified via direct invocation.

#### `hooks/pre_commit_gate.py` (new) — block bad commits

Fires on PreToolUse when the assistant runs `git commit` or `git
push`. Reads the staged file list:

- If `plot/viewer/` changed → run `npx tsc --noEmit` + `npx vitest run`.
- If `plot/mashbill/` changed → run `uv run pytest`.

Failures return `permissionDecision: deny` with the failure output,
so the assistant must fix and retry. No more "tests broke after
commit" surprises.

#### `agents/plot-verifier.md` (new) — Playwright sub-agent

A read-only browser verifier. Parent assistant invokes it after any
UI change in `viewer/`. Sub-agent navigates, screenshots,
DOM-probes, and returns one of three verdicts:

- **MATCHES SPEC** — with evidence (paths + probe data).
- **DIVERGES** — with the specific element / cursor / position that
  differs and the most likely cause.
- **CANNOT VERIFY** — environment broken; exact obstacle named.

Sole tools: Playwright MCP browser_* + Bash + Read. Cannot mutate
the canvas (mutations belong to the parent assistant).

#### `CLAUDE.md` updates

- New **Gate -1** (re-anchor to essence) added at the top of
  Pre-action gates. Gate 0-4 now follow.
- "Pairs with" list updated to read VISION → DOMAIN → SPEC →
  DECISIONS → ARCHITECTURE → CONCEPTS → CURSOR → PHILOSOPHY →
  ROADMAP, in that order, every session.
- Gate 3 rewritten to delegate to the `plot-verifier` sub-agent
  (with the manual fallback path retained for offline cases).

#### `plot/.claude-plugin/plugin.json` updates

- Registered `agents` and `hooks` paths.
- Version bump to **0.14.0** (minor bump because the assistant's
  effective behaviour changed — new gates, new procedures, new
  automation — without breaking any product API).

### Verification

- `tsc --noEmit`: clean.
- `vitest run`: 24/24 passing.
- `session_start.py`: produces VISION + last 5 DECISIONS as
  `additionalContext`, 600+ chars.
- `pre_commit_gate.py`: passes through non-gating commands; runs
  checks on `git commit`; returns `deny` with output on failure.
- Skills + agent: SKILL.md / agent.md frontmatter validates;
  triggers and tools listed explicitly.

### Why minor bump (0.13 → 0.14)

The product UX is unchanged. What changed is the assistant's
operating environment — the rules / tools / procedures by which
future Novel work happens. By the user's framing, this is the
"AI develops Novel reliably" milestone, which conceptually opens a
new release line. v0.14.x will iterate on this infrastructure as
real sessions surface gaps.

## [0.13.10] — 2026-05-10

### Fixed — Cursor flicker root cause: `[role="button"]` on `.react-flow__node`

After six rounds across v0.13.3 → v0.13.6 with every diagnosis
proven wrong by the user reporting the same flicker, **the actual
cause was finally identified via Playwright DOM probe**:

> React Flow v11 sets `role="button"` on the
> `.react-flow__node` element itself for accessibility. Tailwind
> preflight ships `[role="button"] { cursor: pointer }`, which
> matches that element directly and overrides RF's intended
> `cursor: grab` *before any descendant rule runs*.

The v0.13.6 reset's premise ("RF default is grab; remove our
overrides and grab will work") was correct in theory but Tailwind
preflight had been silently shadowing it the whole time. None of
the prior six rounds walked the actual DOM parent chain to find
this — they all theorised from CSS files instead.

#### Fix

`viewer/src/styles.css` — add a second cursor rule (the first one
from v0.13.6 still applies to descendants):

```css
.react-flow__node[role="button"] {
  cursor: grab;
}
.react-flow__node[role="button"].dragging {
  cursor: grabbing;
}
```

#### Verification

Playwright DOM probe sweep across the entire post-layout canvas
(50 px grid sample × 22 cols × 21 rows) returned only three
distinct cursors anywhere:

- `grab` — `.react-flow__pane` AND every node body (uniform).
- `auto` — SVG inside MiniMap (never user-interactive).
- `not-allowed` — disabled toolbar buttons.

Zero `pointer` on any node body. Zero cursor changes when crossing
between pane and node. The flicker is structurally impossible now.

#### Process change

- **First step on any cursor / hit-test bug = Playwright DOM probe**,
  not code reading.
- Tailwind preflight is a hidden source of cursor regressions —
  it interacts silently with vendor library accessibility attributes.

### Changed — Auto layout button moved from top-right toolbar to lower-left Controls panel

Per user direction (*"정렬은 그리고 왼쪽 아래에 핏하는거하고 같은
곳에 넣어도 되요. 오른쪽 상단에 둘 필요 없음."*) the v0.13.9 Auto
layout button moves from `<SketchToolbar>` (top-right) into the
React Flow `<Controls>` panel at lower-left, rendered as a
`<ControlButton>` below zoom / fit / lock.

Rationale: the user grouped auto-layout mentally with view-state
controls (zoom / fit) rather than mutation actions (undo / redo).
Lower-left is also where the user's eye already goes for
camera-related operations. Algorithm itself is unchanged from
D-2026-05-10-E.

#### Files

- `viewer/src/canvases/SketchCanvas.tsx` — adds `ControlButton` to
  the `<Controls>` panel; removes the auto-layout props from the
  `<SketchToolbar>` instantiation.
- `viewer/src/canvases/SketchToolbar.tsx` — reverts to its v0.13.8
  shape (no `canAutoLayout` / `onAutoLayout` props, no Auto layout
  button).
- `viewer/tests/SketchCanvas.regression.test.tsx` — the
  v0.13.9-inverted regression test still asserts "auto layout
  button exists" via `aria-label="Auto layout"`, which still
  matches because the button kept the same accessible name when
  it moved into Controls.

### Documentation

- `docs/SPEC.md` §Cursor states — explicitly mentions BOTH
  Tailwind preflight cancellation rules (descendants from v0.13.6
  + `.react-flow__node[role="button"]` from v0.13.10).
- `docs/SPEC.md` §Auto-layout — Trigger and undo section updated
  with the new lower-left location and rationale.
- `docs/CURSOR.md` — Tailwind cancellation section expanded to
  cover the `.react-flow__node` element itself (in addition to
  descendants); change-history entry for v0.13.10.
- `docs/DECISIONS.md` — D-2026-05-10-F new entry, Accepted, with
  the full diagnosis story and the implied process change ("probe
  the DOM first, theorise second").

## [0.13.9] — 2026-05-10

### Added — Auto-layout button (mindmap directional tree implementation)

Implements the spec shipped in v0.13.8. Single click on the new
"Auto layout" button on `<SketchToolbar>` runs the directional-tree
algorithm against the active canvas, repositions every non-anchor
node, and dispatches one `onDocChange` so `Cmd+Z` reverses the
layout in one step.

#### New files

- `viewer/src/canvases/sketch/autoLayout.ts` (297 LOC) — pure
  module, no React imports. Exports `computeAutoLayout(input):
  { positions: Map<id, {x, y}> }`. Implements:
  - BFS spanning tree from the anchor.
  - Per-child direction from the parent-side handle (R / L / T / B).
    Falls back to positional inference when the edge has null
    `sourceHandle` / `targetHandle`.
  - R / L children → vertical column on the parent's right / left.
  - T / B children → horizontal row above / below the parent.
  - Recursive: grandchildren follow the same rule using *their*
    incoming handle.
  - Reingold-Tilford-style subtree-extent tracking → no node
    footprint overlaps (verified by unit test on a mixed-depth
    grandchild case).
  - Determinism: ties broken by node id at every level.
  - Isolated nodes (not reachable from anchor) → vertical column
    in the anchor's lower-right empty quadrant, sorted by id.
  - Cycles handled by BFS spanning tree (no infinite loop;
    cycle-closing edges are not used for placement).
- `viewer/src/canvases/sketch/useAutoLayout.ts` (43 LOC) — thin
  React hook bridging `computeAutoLayout` to `onDocChange`. Reads
  `docRef.current` + `projectAnchor`, computes positions, builds
  the next `CanvasDoc` with updated `nodes[]`, fires `onDocChange`
  once.
- `viewer/tests/autoLayout.test.ts` — 11 new unit tests pinning:
  per-direction grouping (R children stay right, T children above,
  …), strict no-migration-downward when right is crowded, recursion
  into grandchildren in their own direction, no overlap on a mixed
  R + grandchildren case, determinism across runs, cycle handling,
  isolated nodes, handle-direction inference fallback, and helper
  contracts.

#### Wired changes

- `viewer/src/canvases/SketchToolbar.tsx` — new `canAutoLayout`
  + `onAutoLayout` props; new `IconBtn` rendered between Redo and
  end of toolbar (glyph: `⊞`).
- `viewer/src/canvases/SketchCanvas.tsx` — imports `useAutoLayout`,
  calls it, passes the result to `<SketchToolbar>`. Six lines of
  glue; no new responsibility (the algorithm and the React bridge
  both live in `sketch/`). LOC 360 → 366.
- `viewer/tests/SketchCanvas.regression.test.tsx` — the
  D-2026-05-04-D regression test (`'toolbar does not render an
  Auto layout button'`) was updated to assert the **opposite** per
  D-2026-05-10-E: button MUST render and is enabled when the
  canvas has an anchor + at least one non-anchor node.

#### What stayed the same

- The anchor is never moved by auto-layout.
- Edges keep their `sourceHandle` / `targetHandle` after layout.
- No animation, no preview, no confirmation dialog — single click
  ⇒ instant re-layout per spec.

## [0.13.8] — 2026-05-10

### Spec — Auto-layout restored as a mindmap-style directional tree

D-2026-05-04-D (auto-layout removed) was based on a misread of the
user's v0.11.6 toolbar-cleanup request. The user wanted only
download / upload buttons removed; auto-layout was meant to stay.
The 2026-05-10 Foundation re-verification surfaced this — direct
user quote: *"내가 없애라는건 다운로드 업로드 이런거였는데.
오토레이아웃만 남기라는거였는데."*

This release ships the **spec** for the corrected behaviour. The
implementation lands in v0.13.9.

#### Algorithm shape (full table in `docs/SPEC.md` §Auto-layout)

- **Root:** the canvas anchor, kept fixed in place. Surrounding
  nodes arrange around the anchor's current position.
- **Spanning tree:** BFS from the anchor over `doc.edges`. Tree
  edges drive layout; cycle-closing edges are drawn but ignored.
- **Direction per child:** the **parent-side handle** of each tree
  edge picks the child's direction relative to its parent — `R`
  handle ⇒ child to the right, `T` handle ⇒ child above, etc.
- **R / L children:** stacked in a vertical column on the right /
  left of the parent.
- **T / B children:** placed in a horizontal row above / below the
  parent.
- **Recursive:** grandchildren follow the same rule, using *their*
  incoming-edge parent-side handle. Direction is absolute.
- **No overlap:** Reingold-Tilford-style subtree-extent tracking
  guarantees node footprints never collide. `padding` defaults to
  32 px; node footprint = its `data.width × data.height`.
- **Determinism:** node-id sort order breaks every tie. Same input
  ⇒ same output, every time.
- **Isolated nodes:** placed in the anchor's lower-right empty
  quadrant in a separate vertical column.

#### Trigger

- A single "Auto layout" button on `<SketchToolbar>` (next to
  undo / redo). Click ⇒ instant execution, no confirmation.
- Result is applied via `onDocChange`, so `Cmd / Ctrl + Z` reverses
  it in one step.

#### What auto-layout does NOT do

- Does not move the anchor.
- Does not change which nodes are connected (edges stay).
- Does not re-balance handles after layout.
- Does not animate or preview — single-click determinism is the
  product feature.

### Documentation

- `docs/SPEC.md` §Auto-layout — fully rewritten from "Removed" to
  the directional-tree spec above.
- `docs/DECISIONS.md`:
  - **D-2026-05-04-D** marked **Rejected** with a misattribution
    note explaining the 2026-05-04 / 2026-05-10 timeline.
  - **D-2026-05-10-E** new entry, Accepted: full algorithm rationale
    (why directional, why not radial, why not force-directed, why
    no library, why anchor stays fixed, why no animation).

### First Gate 0 application

This entire release exists because Gate 0 (added in v0.13.7) fired
on the user's *"네 일단 해봐요"* during the spec discussion. SPEC +
DECISIONS were updated in the same commit cycle as the version
bump, exactly as Gate 0 prescribes.

## [0.13.7] — 2026-05-10

### Added — Gate 0: user confirmation pins the spec immediately

`plot/CLAUDE.md` adds a new pre-action gate at position 0 (before the
existing Gate 1). Trigger: any user message containing one of a fixed
keyword set (`승인합니다 / 좋아요 / 네 좋아요 / 됐다 / 이제 됐다 /
맞아요`, English equivalents). When the trigger fires, the assistant
must, before any other tool call:

1. State the confirmed behaviour in one declarative sentence.
2. Verify or add the matching line to `docs/SPEC.md`.
3. Append a `D-YYYY-MM-DD-X` entry to `docs/DECISIONS.md` with
   `Approval: Accepted by user, YYYY-MM-DD`.
4. Stage SPEC + DECISIONS changes into the current commit cycle (or
   a docs-only follow-up if the implementing commit already shipped).

Banned shortcuts: deferring to "next session", assuming the SPEC was
already updated without verifying the diff, batching multiple
confirmations into one update, treating an unclear confirmation as
implicit (must ask the user).

This is a structural fix for the "work doesn't accumulate across
sessions" problem the user has flagged repeatedly. Without it, each
session re-asks questions the previous session already answered.
The v0.13.3 → v0.13.6 cursor saga is the canonical motivating
example — six rounds of cursor work because confirmed behaviour
never made it into the spec until v0.13.6 reset.

Authored as the first application of Gate 0 itself (user said *"네
좋아요"* on 2026-05-10 in the same conversation that drafted the
gate). See [D-2026-05-10-D](./docs/DECISIONS.md).

## [0.13.6] — 2026-05-10

### Changed — Reset to React Flow vendor cursor / handle defaults

Six rounds of cursor / handle interventions across v0.13.3 → v0.13.5
shipped overrides on top of overrides. Each round fixed one
localised symptom and revealed or introduced another. After the
user's *"정리한게 이상하지 않아요?"* / *"RF 디폴트로 일단 가세요.
거기서부터 다시 시작하죠. 코드 정리 제대로 하구요."* feedback,
v0.13.6 removes the entire override stack and restarts from the
React Flow vendor baseline.

The structural reasoning (D-2026-05-10-C):

- **One known state** to reason from. Vendor CSS in
  `node_modules/reactflow/dist/style.css` is now the single source
  of truth — no mental model lives in our `styles.css`.
- **No flicker by construction.** RF baseline puts `cursor: grab`
  on both `.react-flow__pane` and `.react-flow__node` — the cursor
  literally cannot change when the mouse crosses the boundary, so
  the "arrow ↔ pointer flicker" the user kept reporting is gone
  not because we patched it but because the conditions for it no
  longer exist.
- **The RF mental model is uniform:** anything draggable shows
  `grab`; active drag shows `grabbing`; drawing a connection shows
  `crosshair`; resizing shows the directional resize cursor. This
  is the standard React Flow contract that ships in every other
  React Flow product.

#### Two changes that did not need rolling back

- **Pan re-enable** (`SketchCanvas.tsx`: `panOnDrag={false}` →
  `panOnDrag`) shipped earlier in this release per D-2026-05-10-A
  and matches RF default. Stays.
- **Border-replaces-outline** on the inner node decoration (v0.13.5,
  D-2026-05-08-G) is about visual extent matching the click target
  — clicks on the visible decoration must select the node, not
  pass through to the pane. Independent of cursor, stays.

### Removed — The full v0.13.3 → v0.13.5 cursor / handle override stack

`viewer/src/styles.css` — removed:

- `.react-flow__node { cursor: pointer }` (was D-2026-05-08-C —
  unified node cursor). RF default `grab` restored.
- `.react-flow__node.dragging { cursor: grabbing }` (was redundant
  with RF default).
- `.react-flow__pane / .react-flow__viewport / .react-flow__renderer { cursor: default !important }` (was v0.13.4 — already removed earlier in this release per D-2026-05-10-A).
- `.react-flow__handle { width 10px / height 10px / 1.5px slate-400 border / white background / opacity 0 / cursor: pointer !important }` (was D-2026-05-08-F + earlier). RF default 6×6 dark-fill always-visible dot restored.
- `.react-flow__node.selected .react-flow__handle { opacity 1 / indigo border + bg }` (was D-2026-05-08-F — handles-on-select). Handles now always visible per RF default.
- `.react-flow__handle.connecting / .connectingfrom { cursor: crosshair !important / opacity 1 / indigo border }` (was D-2026-05-08-C). RF's native `.connectionindicator` selector covers crosshair-while-connecting.

`viewer/src/edit/EditableText.tsx` — removed:

- `cursor-pointer` Tailwind class on the display span (was
  D-2026-05-08-E — label cursor unification). The label inherits
  from the node, which under RF default is `grab`.

`viewer/src/canvases/SketchNode.tsx` — simplified the v0.13.5 border
comment block from a six-line cursor-flicker rationale to a single
sentence about hit-box matching the visual extent (the cursor part
of the rationale was disproven by D-2026-05-10-C anyway).

### Added — One single retained CSS rule (Tailwind preflight cancellation)

After the reset, the user reported flicker still present on node
hover. Investigation found the source: **Tailwind preflight** ships
`button, [role="button"] { cursor: pointer }`, which inside our
nodes matches:

- The fold `<button>` on container nodes.
- The EditableText label span (has `role="button"` for keyboard
  accessibility — needed for screen readers).

These elements flipped the cursor from RF's `grab` to Tailwind's
`pointer` — re-introducing the very flicker the reset was meant to
kill, with no override of ours involved.

The fix is one CSS rule that cancels the Tailwind preflight effect
inside `.react-flow__node`, restoring RF's inheritance chain:

```css
.react-flow__node *:not(.react-flow__handle):not(.react-flow__resize-control) {
  cursor: inherit;
}
```

The :not() exclusions preserve RF's own semantic cursors on
connection handles (crosshair) and resize controls (directional
resize). This is the **only** cursor rule in `styles.css` after the
reset; it does not change RF, only stops Tailwind from contradicting
it. (D-2026-05-10-C.)

### Documentation

`docs/SPEC.md`:

- §Pan and select rewritten — the pan-off paragraph from v0.13.4 is
  gone; the new prose codifies "drag empty pane = pan; Shift+drag =
  selection box; node drag = node move".
- §Hover behaviour rewritten — was "handles only when selected,
  cursor pointer everywhere"; now "RF defaults, handles always
  visible".
- §Cursor states rewritten — table mirrors the React Flow vendor
  CSS exactly + the one Tailwind cancellation rule so future
  sessions can verify against the spec without re-reading vendor
  CSS. Includes the "RF mental model in one sentence" summary.

`docs/CURSOR.md` — **new file**, dedicated cursor SSOT:

- TL;DR table for the five cursor regions a user actually sees.
- Full table with selectors mirroring React Flow vendor CSS.
- Detailed write-up of the Tailwind preflight cancellation rule:
  what it is, why it's not "just another override", why we don't
  fix the problem upstream by removing `role="button"` from the
  label.
- Anti-patterns derived from v0.13.3 → v0.13.5 mistakes.
- "How to deviate" workflow for any future cursor change — must
  open a `D-YYYY-MM-DD-X` decision id, get user approval, add a
  CSS comment naming the id, update SPEC + CURSOR + add a
  regression test.
- DevTools probe script for verifying cursor state in the browser.

`plot/CLAUDE.md`:

- "Pairs with" list — `docs/CURSOR.md` added.
- Anti-patterns table updated: replaced the four cursor-related
  rows with one general rule about not adding cursor / handle
  overrides without a decision id.

`docs/DECISIONS.md` — three new entries:

- **D-2026-05-10-A** Pan re-enable (Accepted, shipped earlier in
  this release).
- **D-2026-05-10-B** Force-pointer on every node descendant
  (Rejected, rolled back in same session before commit).
- **D-2026-05-10-C** Reset to RF defaults + Tailwind preflight
  cancellation (Accepted, this release).

## [0.13.5] — 2026-05-08

### Fixed — **Cursor flicker root cause: outline paints outside hit-box**

After three previous rounds of cursor fixes (v0.13.3 → v0.13.4) the
user still reported `default ↔ pointer` flicker on a slow mouse-move
across one node ("커서 검지 커서 검지 이렇게 되요"). DOM probing
returned a single cursor (`pointer`) for every descendant of the
node, which ruled out competing cursor declarations and left only
one possible cause: the cursor was crossing the **node's actual
hit-box boundary** while the user thought they were still inside
the visual node.

The decoration `outline outline-2 outline-slate-600 outline-offset-2
ring-1 ring-slate-300` on the synthetic project anchor paints the
visual ring **8–10 px outside** the `.react-flow__node` bounding box.
Pixels in that ring zone — though they look like part of the node —
hit-test to `.react-flow__pane` (cursor: default). Slow movement
across the ring zone flicked the cursor `pointer ↔ default`.

Fix: replace `outline` (paints outside the box, excluded from
hit-testing) with `border` (part of the border-box, included in
hit-testing). After the change the hit-box and the visual box are
pixel-identical (verified via `getBoundingClientRect`); the cursor
is `pointer` everywhere on the node region with no flicker zone.

Per-state class change in `viewer/src/canvases/SketchNode.tsx`:

| State | Before | After |
|---|---|---|
| Selected | `outline outline-2 outline-indigo-500` | `border-2 border-indigo-500` |
| Anchor (idle) | `outline outline-2 outline-slate-600 outline-offset-2 ring-1 ring-slate-300` | `border-2 border-slate-600` |
| Regular (idle) | `outline outline-1 outline-slate-300` | `border border-slate-300` |

The anchor loses its 8 px breathing-room visual + thin slate-300
inner ring (those were the source of the flicker zone). The new
2 px slate-600 border keeps the anchor visually distinct from the
1 px slate-300 of regular nodes and the 2 px indigo-500 of selected
nodes. If the original "double ring" look matters, an `inset
box-shadow` is the right tool for a follow-up — it paints inside
the box and doesn't touch hit-testing.

[D-2026-05-08-G](./docs/DECISIONS.md) records the diagnosis and the
general rule that follows: **node decoration must coincide with the
hit-box; never use `outline` / `outline-offset` / `ring` /
`shadow-[…]` rules that paint outside the box for any pointer-
significant element.**

## [0.13.4] — 2026-05-08

### Fixed — **Cursor / handle visual flicker on node hover (final)**

The user reported "커서였다가 검지였다가 큰 검지였다가 작은
검지였다가 등등" — the cursor itself appearing to vary in size /
shape as it moved across a node, even after the v0.13.3 cursor
unification. DOM probing showed the cursor was never actually
varying; the perceived variation was the four handle dots
pulsing in opacity (0 → 0.55 on node-hover) and the one near
the pointer scaling to 1.25× on direct handle-hover. The dots
near the pointer were reading as "cursor".

- **Handles now appear only when the node is selected.** Hovering
  a node no longer reveals or animates anything. Click to select
  the node → handles appear at full opacity with indigo styling
  → drag from a handle to draw an edge. One extra click compared
  to the prior hover-to-reveal flow, but the canvas reads still
  on hover.
- **All transition / scale animations on handles removed** —
  they were the actual flicker source.
- SPEC §Hover behaviour rewritten: three visibility states (idle
  / hover / direct-handle-hover) collapse to two (hidden /
  selected). DECISIONS [D-2026-05-08-F](./docs/DECISIONS.md)
  records the user direction and the diagnosis trail.

## [0.13.3] — 2026-05-08

### Changed — **SketchCanvas refactor: test baseline + extraction in progress**

The viewer's central component (`canvases/SketchCanvas.tsx`, 1476
LOC, 16 concerns in one closure) is being split down to a thin React
Flow shell (target ≈ 150 LOC) per
[D-2026-05-08-A](./docs/DECISIONS.md). Approach: Candidate A
(modified) — surgical responsibility split with pure transforms
(nodes / edges / overlap math) extracted as `.ts` modules, hooks for
the rest, React Flow prop wiring stays in the shell.

This release ships the **test baseline** that gates the extraction:

- **JSDOM `localStorage` mock added** to `viewer/tests/setup.ts`.
  JSDOM previously shipped a placeholder without `getItem` /
  `setItem` methods, which crashed any test that mounted a component
  calling `window.localStorage.getItem(...)` (notably `SketchInspector`'s
  width-toggle persistence). The previously-broken
  `SketchCanvas.smoke.test.tsx` is green again.
- **`viewer/tests/useSketchHistory.test.ts` deleted.** It imported a
  hook that was never implemented (orphan from a planned-but-skipped
  feature). The actual undo/redo lives in
  `viewer/src/canvases/useProjectHistory.ts`; if dedicated coverage is
  wanted there, that's a new feature task.
- **Regression test set added** at
  `viewer/tests/SketchCanvas.regression.test.tsx` — four pinning
  assertions for invariants the v0.13.2 bugs flipped: 0 auto-edges
  on Foundation when `doc.edges` is empty (D-2026-05-04-A);
  anchor renders 4 React Flow handles (D-2026-05-04-B); no "Auto
  layout" button in the toolbar (D-2026-05-04-D); Inspector aside
  appears after a node click. All four match real-browser state
  (verified at the v0.13.3 baseline). Test suite now: 4 files /
  13 tests, all passing.
- **Step 1 + 2 of the SketchCanvas split** — extracted the
  value-flow toggle state (`canvases/sketch/useValueFlow.ts`) and
  the orphan actor_ref detection memo
  (`canvases/sketch/useOrphanActorRefs.ts`). New folder:
  `viewer/src/canvases/sketch/`. SketchCanvas.tsx: 1476 → 1466 LOC
  (−10).
- **Step 3 — collapsed-tree state**
  (`canvases/sketch/useCollapsedTree.ts`). One hook now owns
  `childIdsByParent`, `nodeById`, `nearestCollapsedAncestor`,
  `toggleCollapsed` (reads `docRef` for mid-drag freshness per the
  coupling map), and `subtreeSize`. The lookup map is also used by
  drag/drop and keyboard, so the hook is the single source. SC:
  1466 → 1409 LOC (−57).
- **Step 4 — Inspector routing**
  (`canvases/sketch/useInspectorRouting.ts`) plus
  `canvases/sketch/constants.ts` for the shared
  `PROJECT_ANCHOR_ID`. The hook owns `inspectorNodeId` state, the
  `selectNodeId` jump-and-fit effect, and the three React Flow
  callbacks (`onNodeClick`, `onNodeDoubleClick`, `onPaneClick`),
  including the anchor read-only guard. SC: 1409 → 1394 LOC
  (−15). Browser verified: clicking Mission opens Inspector;
  clicking the anchor does not.
- **Step 5 — Doc-to-node transform**
  (`canvases/sketch/useNodesMemo.ts`). One hook owns the
  parents-before-children sort, the hide rules
  (collapsed-ancestor / rule&content / service-detail
  service-root), the orphan-actor_ref visual override, the
  master-derived ref label sync, the service.target_side body
  tint, drill routing, and synthetic project anchor injection.
  Plan called for a separate pure `nodeTransform.ts` + thin
  wrapper, but the transform reads ten-plus callbacks; a "pure"
  form would be cosmetic. Documented as
  [D-2026-05-08-B](./docs/DECISIONS.md). SPEC §Anchor and SPEC
  §Rendering order updated with the implementation invariants
  this hook preserves. SC: 1394 → 1246 LOC (−148). Browser
  verified: Foundation renders 4 nodes (anchor + Mission +
  CoreValue + Identity), 0 edges, 3 ⚠ badges intact.
- **Step 6 — Doc-to-edge transform**
  (`canvases/sketch/edgeTransform.ts` pure +
  `canvases/sketch/useEdgesMemo.ts` thin wrapper). The pure
  module survives here because edges have far fewer callback
  dependencies than nodes — only data + collapse hide rule +
  value-flow recolour. Genuinely unit-testable in isolation if
  someone later wants snapshot tests over thousands of edge
  shapes. SC: 1246 → 1212 LOC (−34). Browser sanity (Foundation,
  banas-v013): 0 edges (regression test still pinned), 0
  console errors. Recolour path not exercised against this
  fixture (no user-drawn edges); the pure code is byte-equal to
  the prior inline so the recolour invariant is preserved by
  construction.
- **Step 7 — Anchor mutation branch**
  (`canvases/sketch/applyAnchorChange.ts`, pure helper).
  `handleNodesChange` stays in the shell (React Flow's
  `onNodesChange` prop must dispatch atomically per the coupling
  map) but the anchor-vs-regular-node split now reads as one
  helper call, surfacing SPEC §Anchor "Mutation routing". SC:
  1212 → 1199 LOC (−13). Browser sanity: anchor present, 4
  handles, 0 console errors. Mid-drag persistence path cannot be
  exercised through Playwright synthetic clicks (they bypass
  d3-zoom's drag pipeline); the helper is a byte-equal
  extraction of the prior inline so the persistence invariant is
  preserved by construction.

- **Step 8 — Three context menus**
  (`canvases/sketch/useContextMenus.ts`). One hook owns
  `menu` state, `openPaneMenu`, `openNodeMenu`, `openEdgeMenu`,
  `closeMenu`. `MenuState` type lives in the hook; `DEFAULT_WIDTH`
  / `DEFAULT_HEIGHT` / `DEFAULT_COLOR` lifted to
  `sketch/constants.ts` so the future `useNodeCreation` (Step 10)
  can reuse them without circular imports. Color palette also
  lifted to a const inside the hook (was a per-call inline
  array). SC: 1199 → 1073 LOC (−126). Browser verified: right-click
  on a Mission node renders the Duplicate / Copy / Color × 7 /
  Delete menu items.
- **Step 14 — Shell consolidation; split complete.** Three
  more reductions land:
  - `addCompositionChild(parentId, kind)` factored into
    `useNodeCreation`. The Inspector's `onAddChild` (60 lines
    of inline default-everything DocNode boilerplate) becomes
    a one-line callback.
  - `SketchInspectorBindings.tsx` (new) wraps the SketchInspector
    with all the SC-side glue (which node is selected, repick /
    delete / patch / add-child routing). SC's render block goes
    from ~100 lines of inline JSX to one
    `<SketchInspectorBindings ... />` element.
  - `nodeChanges.ts` (new pure module) exposes
    `collectNodeChanges(changes)` and
    `applyNodeChangesToDoc(doc, posById, dimById)`.
    `handleNodesChange` shrinks to 10 lines while still living
    in the shell (React Flow's `onNodesChange` requires
    atomic dispatch per the coupling map).
  Final SC LOC: **1476 → 360 (75.6 % reduction).** 16 hook
  modules + 5 pure helpers under `viewer/src/canvases/sketch/`
  each carry a single responsibility. The 360-LOC floor
  (instead of the plan's 150 design target) is recorded in
  [D-2026-05-08-D](./docs/DECISIONS.md): pushing further would
  reintroduce the controller-hook god scope that
  D-2026-05-08-A explicitly rejected.

- **Step 13 — Small flow handlers**
  (`canvases/sketch/useFlowHandlers.ts`). One hook bundles
  `handleConnect` (new edge), `handleEdgesChange` (no-op stub
  React Flow still requires), `handleNodesDelete` (with anchor
  + legacy project-kind protection per SPEC §Anchor),
  `handleEdgesDelete`, `handlePaneDoubleClick` (add node where
  the user double-clicked, only on the React Flow pane), and
  `handleSelectionChange` (selection ref sync). `handleNodesChange`
  stays in the SC shell — its mid-drag `docRef.current` read is
  load-bearing per the coupling map and would regress if the
  React Flow event were dispatched through a longer call chain.
  Cleanup: SC drops six unused reactflow type imports
  (`Connection`, `Edge`, `EdgeChange`, `OnSelectionChangeParams`,
  the `SketchEdge` type, the constants block), and the
  `applyEdgeChanges` / `applyNodeChanges` re-export at the
  bottom of the file (dead code — nothing imports them from SC).
  **SC LOC: 546 → 472 (−74) — under the 500-LOC threshold for
  the first time since the file was born.** Gate 2 satisfied;
  one-step-from-final-shell remains.
- **Step 12 — Modal / picker renders**
  (`canvases/sketch/SketchModals.tsx`). One component renders the
  four conditional modal blocks: SketchBodyModal (long-form node
  body editor), SketchEdgeModal (edge label + dashed + value-form),
  FoundationRefPicker (mission/value/identity ref picker), and
  ActorRefPicker (actor ref picker, both create + rewire flows).
  Inspector stays in the SC shell. Side-cleanup: extracted a
  `parentAbsolute()` helper that the two picker callbacks both
  used to walk the parent chain (was duplicated inline). SC drops
  six imports (ActorRefPicker, FoundationRefPicker family,
  SketchBodyModal, SketchEdgeModal, NodePreset). SC: 673 → 546
  LOC (−127). One step under the 500-LOC threshold mark.
- **Step 11 — Drag-and-drop + overlap nudging**
  (`canvases/sketch/useDragAndDrop.ts` hook +
  `canvases/sketch/overlapNudge.ts` pure module). The pure
  module owns `containerAtFlowPoint` and `findFreeSpot` — both
  pure functions of (nodes, point) / (rect, siblings); React-
  free, unit-testable. The hook owns the drop orchestration:
  preset parse, hit-test, hierarchy edge creation,
  reference-kind picker dispatch, and the two `pendingActorRef`
  / `pendingFoundationRef` states. `PendingActorRef` and
  `PendingFoundationRef` types lifted to `sketch/types.ts` so
  the modal render block (Step 12 next) can read them. SPEC
  §Drag-and-drop section added with the canonical hit-test /
  nudge / hierarchy-edge / picker rules. SC: 857 → 673 LOC
  (−184). Browser sanity (Foundation, banas-v013): nodes still
  render, no console errors. Real drag-from-stencil cannot be
  exercised via Playwright (synthetic dataTransfer doesn't
  round-trip the way the browser's native drag does); the hook
  body is byte-equal to the prior inline so the drop pipeline
  is preserved by construction.
- **Step 10 — Node creation helpers**
  (`canvases/sketch/useNodeCreation.ts`).  `addNodeAt` (top-level)
  and `addNestedNodeAt` (drop onto an existing container, with
  decomposition edge for actor / service kinds) move out of the
  shell. Side-extraction: `NodePreset` interface lifted to
  `canvases/sketch/types.ts` so multiple sketch hooks (and
  `SketchStencil`) can import without circular deps. The
  default-everything DocNode boilerplate is duplicated across
  `addNodeAt` and `addNestedNodeAt` — intentionally preserved
  byte-equally during this extraction; a `makeBlankNode()`
  follow-up is worth doing once Step 11 is also out of the way.
  Cleanup: SC drops `NodeKind` and `DEFAULT_COLOR` imports (only
  the new hook needs them). SC: 1030 → 857 LOC (−173). Browser
  sanity: Foundation renders (4 nodes incl. anchor).
- **Step 9 — Window keyboard shortcuts**
  (`canvases/sketch/useKeyboardShortcuts.ts`). One hook owns the
  `window.addEventListener("keydown")` effect and the canonical
  combo set (Cmd+Z / Cmd+Shift+Z / Cmd+Y / Cmd+C / Cmd+V /
  Cmd+D / Cmd+A). The editable-target guard
  (`INPUT` / `TEXTAREA` / `contentEditable`) is preserved
  byte-equally — typing in Inspector text fields still does NOT
  trigger canvas undo. SPEC §Keyboard shortcuts added with the
  full combo table and the load-bearing guard note. SC: 1073 →
  1030 LOC (−43). Browser verified: synthetic `keydown` reaches
  the listener and `preventDefault` fires for Cmd+A; the
  imperative `setNodes` selection path doesn't survive a
  Playwright synthetic dispatch (React Flow re-renders from our
  `useNodesMemo` and overwrites the imperative state) — that's a
  pre-existing limitation of synthetic testing, not a regression
  of this refactor.

### Changed — **Canvas pan-on-drag removed; node cursor invariant tightened**

Per [D-2026-05-08-E](./docs/DECISIONS.md):

- **`panOnDrag={false}` on `<ReactFlow>`.** Grabbing an empty
  canvas region and dragging no longer pans the viewport. Use the
  zoom controls (bottom-left) or the minimap (bottom-right) to
  move the view. Users were accidentally panning while reaching
  for nodes; removing the affordance lets the canvas read as a
  fixed page.
- **Pane / viewport cursor forced to `default`** with a CSS
  override on `.react-flow__pane` / `.react-flow__viewport` /
  `.react-flow__renderer`. React Flow's baseline CSS keeps the
  `cursor: grab` rule on those elements even after `panOnDrag` is
  disabled — that reintroduced the cursor flicker the user had
  reported (`grab` over empty canvas ↔ `pointer` over a node).
  After the override the canvas region reads "default" (page) and
  only the node region reads "pointer" (clickable).
- **Cursor on a node is now `pointer` everywhere, in every state**
  (idle, hover, mousedown). The `.react-flow__node:active {
  cursor: grabbing }` rule is gone — clicking a node no longer
  flashes the grabbing cursor, only an actual drag does (via
  `.react-flow__node.dragging`).
- **`EditableText` display span uses `cursor-pointer`**, not
  `cursor-text`. The display span is `role="button"` (click to
  edit), so the I-beam cursor was misleading and was the
  remaining flicker source the v0.13.3 cursor fix didn't catch.

SPEC §Pan and select (new) and §Hover behaviour (clarified)
codify the cursor invariant.

### Fixed — **Cursor flicker on node hover**

`.react-flow__handle` now uses `cursor: pointer` (matching the node
body); `cursor: crosshair` is restored only while a connection is
actively being drawn (`.connecting` / `.connectingfrom`). Previously
React Flow's default crosshair on handles fought our pointer rule on
the node body — moving the mouse across a node would flip the cursor
back and forth (described by the user as "보자기 / 가위 계속 바뀌는",
paper / scissors swapping). The v0.13.2 hover tone-down made handles
visually quieter but left the cursor invariant ambiguous; this fix
addresses the root cause. (D-2026-05-08-C, SPEC §Hover behaviour
updated.)

The extraction commits land incrementally over subsequent versions
under this same v0.13.x line; each commit is a single concern moved
out, browser-verified per the plan's matrix.

## [0.13.2] — 2026-05-05

### Added — **Foundation SPEC + decision log**
- ``plot/docs/SPEC.md`` — first canonical behaviour spec (Foundation
  canvas only). Codifies anchor / edges / auto-layout / ⚠ badge /
  hover / Inspector / viewport behaviour with explicit user approval.
- ``plot/docs/DECISIONS.md`` — append-only UX / behaviour decision
  log. Today's seven decisions are logged with status (accepted /
  rejected / pending). Future UI changes must add an entry here
  before / alongside the code change.
- Reason: prior to this release, behavioural decisions lived only in
  code comments (not agreed) or in session memory (didn't survive).
  Cross-session work didn't accumulate. The two new files are the
  fix.

### Changed — **Foundation canvas: smaller, agreed-upon polish**
- **Anchor visually distinct from Service circles.** The project
  anchor now wears a slate-600 outline + offset + slate-300 inner
  ring so it reads as "this is the project itself, not a peer", even
  when it appears on Actors / Services where same-coloured Service
  circles also exist. (Decision D-2026-05-04-C.)
- **⚠ MD-warning badge contrast.** Was amber-100 fill on amber-100 /
  amber-50 cards — nearly invisible. Now white fill, amber-700
  glyph, amber-500 ring + shadow; legible on every Foundation card
  colour. (Decision D-2026-05-04-F.)
- **Quieter hover.** Connection handles stay hidden at rest; fade to
  opacity 0.55 while the cursor is on the node body; only become
  fully opaque + scaled on direct handle hover. The previous "all
  four handles pop the moment the cursor approaches" felt noisy.
  (Decision D-2026-05-04-E.)
- **Defensive viewport sizing.** Outermost shell uses ``h-screen
  min-h-screen``; ``html, body, #root`` add ``min-height: 100dvh``
  fallback. Belt-and-braces against cascading quirks so the canvas
  always reaches the bottom of the window. (Decision D-2026-05-04-G,
  approval pending user confirmation.)

### Removed — **Auto-layout button + auto-edges (rolled back same day)**
- **"Auto layout" button gone** from the canvas toolbar and the pane
  context menu. ``handleAutoLayout`` callback and ``autoLayout`` /
  ``radialLayout`` imports dropped from ``SketchCanvas``. Layout is
  fully manual — node positions encode user intent and shouldn't be
  silently rewritten. (Decision D-2026-05-04-D.)
- **Synthetic anchor → child auto-edges removed** before reaching a
  release. Briefly added during this session as dashed slate-400
  lines connecting the anchor to Mission / CoreValue / Identity, but
  the user rejected the approach: edges that the user can't edit or
  delete break the "every line on the canvas is mine to control"
  expectation. All edges on Foundation are user-drawn. (Decision
  D-2026-05-04-A.)
- **Anchor handle suppression rolled back.** Briefly hid the anchor's
  four React Flow handles on the assumption that "synthetic =
  read-only" (a stale code comment, not an agreed decision). Handles
  restored — the user may draw edges from / to the anchor like any
  other node. (Decision D-2026-05-04-B.)

## [0.13.1] — 2026-05-04

### Fixed — **Radial auto-layout under v0.13's derived project anchor**
- ``radialLayout`` was still looking for the project node inside
  ``doc.nodes`` (legacy v0.12 path). v0.13 moved the anchor out to
  ``ProjectDoc.anchors``; the lookup returned nothing on Foundation /
  Actors and silently fell back to dagre LR, collapsing the canvas
  into a horizontal row.
- New ``options.anchorOverride`` parameter; SketchCanvas passes the
  derived anchor in. Legacy in-doc.nodes lookup preserved as a
  fallback.

### Fixed — **Peer overlap on radial rings**
- The "minimum angular separation" between adjacent peers was a fixed
  15°. With node widths > 120 px on a 220 px ring, two peers could
  end up visibly overlapping. Now derives the gap from
  ``(maxNodeDim + 24px padding) / radius`` so it scales with actual
  footprint. Caps at π/2.
- If the spread chain wraps past 2π (user's nodes were so clustered
  that respecting angles couldn't yield separation), fall back to
  even distribution around the full circle.

## [0.13.0] — 2026-05-04

A foundational rework of how a project's data is laid out on disk —
**graph in JSON, typed content in Markdown, schema in its own folder**.
Foundation canvas is the v1 surface; Actors / Services / Service
Detail keep the v0.12 layout for now and join the new model in v0.14+.

### BREAKING — file layout

The first time Novel reads a v0.12 project, it migrates Foundation in
place:

  .plot/{project}/
    project.json                 ← + new ``anchors`` field
    schema/                      ← ✨ NEW (auto-generated, git-tracked)
      _meta.json                 schema_version=1, plot_version, kinds
      project.json               JSON Schema for project node entry
      mission.json               + core_value.json, identity.json
      mission.md.template        + core_value.md.template, identity.md.template
    foundation/
      canvas.json                ← graph only (no project node, no typed text)
      mission-mission.md         ← ✨ per-node typed text + free prose
      core_value-{slug}.md
      identity-voice.md
    actors/canvas.json           ← v0.12 layout, project node evicted
    services/                    ← v0.12 layout, project node evicted

### Phase 0 — Project SSOT
- New ``ProjectDoc.anchors: dict[CanvasKind, AnchorPlacement]``. Each
  AnchorPlacement carries x/y/w/h/color/shape for the project anchor
  on a given canvas. Default-seeded; old projects fall back cleanly.
- Per-canvas seeds (foundation/actors/services) no longer create a
  ``project`` kind node — the anchor is no longer canvas data.
- Eviction migrator on canvas read: legacy ``project`` node →
  ``ProjectDoc.anchors[canvas]`` + node removed + orphan edges stripped.
- Frontend: SketchCanvas injects a synthetic project anchor (id
  ``__project_anchor__``) derived from ProjectDoc.anchors. Drag /
  resize routes through a new ``PATCH /api/projects/{id}/anchors/{canvas}``;
  the canvas .json never carries a project node again.
- ``ProjectDoc.version`` bumped 2 → 3.

### Phase 1 — Pydantic discriminated union (Foundation)
- ``BaseNodeFields`` carries the 13 graph fields. Per-kind subclasses
  ``ProjectNode`` / ``MissionNode`` / ``CoreValueNode`` /
  ``IdentityNode`` declare a ``Literal`` discriminator on ``kind`` and
  their own typed-text fields. ``FoundationNode = Annotated[Union[...],
  Field(discriminator="kind")]``.
- The legacy god ``SketchNode`` stays in place — Foundation just gains
  type-safer per-kind constructors.

### Phase 2 — Schema auto-export
- New module ``schema_export.py``. ``create_project`` writes
  ``.plot/{project}/schema/`` with one JSON Schema per kind (graph
  fields only) plus per-kind MD templates. Idempotent.

### Phase 3 — Markdown template I/O
- New module ``md_template.py``. ``parse_md_template`` is **lenient**
  (missing sections → empty + warning, unknown headings preserved in
  warnings, case-insensitive headings, HTML comments stripped, free
  prose below the ``---`` rule preserved verbatim).
  ``render_md_template`` is **strict** (canonical section order per
  kind, free prose round-trips).
- 18 round-trip + lenient + strict tests.

### Phase 6 — Migration v0.12 → v0.13 (Foundation)
- ``_evict_typed_text_to_md`` runs on first foundation read: per-kind
  typed text in canvas.json → ``foundation/{kind}-{slug}.md`` template
  (preserving any existing free prose), then stripped from JSON.
- ``_merge_md_typed_text_into_nodes`` re-attaches typed text from the
  canonical MD path into the in-memory node so Inspector / API
  continue to see populated fields.
- ``_split_foundation_typed_text_to_md`` runs on every foundation
  write so Inspector edits land in MD, not back in canvas.json.

### Phase 4 — File watcher
- Watcher recognises ``foundation/*.md`` (any .md directly under
  ``foundation/``) as v0.13 per-node templates. External Obsidian /
  VS Code edits trigger ``project_changed`` with ``canvas_kind:
  "foundation"`` so any open viewer reloads.

### Phase 5 — TypeScript Foundation discriminated union
- ``BaseFoundationNode`` + ``MissionFoundationNode`` /
  ``CoreValueFoundationNode`` / ``IdentityFoundationNode`` /
  ``ProjectFoundationNode`` per-kind types.
  ``FoundationNode = ...`` discriminated on ``kind``. Ready for
  Foundation-aware code paths to narrow safely.

### Phase 7 — Resilience UX
- New helper ``collect_foundation_md_warnings`` runs alongside
  canvas read; ``canvas_get_endpoint`` injects per-node
  ``_md_warnings`` into the response without polluting the model.
- Frontend: ``SketchNode`` shows a yellow ⚠ badge when warnings
  present. Inspector displays the warning list with a hint pointing
  at the file the user should fix.

### Compatibility
- v0.12 projects auto-migrate on first read. Eviction is idempotent:
  re-running on v0.13 data is a no-op. The legacy v0.7
  ``{slug}/details.md`` per-node folders are left in place for
  backward compatibility but no longer used by Foundation reads;
  ``details_path`` may continue to point at them for the user's
  reference.
- 182 tests pass (164 prior + 18 new for md_template).

## [0.12.6] — 2026-05-03

Code-level audit cleared the v0.10/v0.11 residue still leaking into
the v0.12 Services surfaces.

### Changed — **`is_root` UI no longer applies to service**
- Inspector still surfaced a "Mark as Service Root" checkbox and a
  "Service Root" header for any parentless service. v0.12 made
  `service` a category leaf — there is no service-root concept any
  more. The toggle and the header branch now apply only to `actor`.
  The `is_root` field stays on the data model (still meaningful for
  actor); only the service UI path is removed.

### Changed — **Service Detail modal shows the parent category**
- The header used to read just "SERVICE DETAIL — Login". Inside the
  modal users had no way to see which category the service belonged
  to; drill context was lost. Header now reads
  "SERVICE DETAIL  {Category} › {Service}", with the category label
  derived from the service's `parent_id` lookup against the cached
  Services canvas.

### Added — **Soft warning on empty categories**
- A `category` with zero child services is structurally legal but
  semantically noise (categories exist to group services). Inspector
  now surfaces an amber hint inside `CategoryFields` when child
  count = 0, suggesting the user either drop a service in or delete
  the category. Not a hard validator — autosave-friendly.

### Changed — **Stale "sub-service" wording removed**
- Comments and JSDoc across `types.ts`, `SketchStencil.tsx`, and
  `SketchCanvas.tsx` still described the v0.10/v0.11 sub-service
  decomposition. Updated to v0.12 phrasing
  ("category → service leaf"; "service detail = modal").

### Changed — **Auto-layout button tooltip drops "(dagre LR)"**
- v0.12.4 made auto-layout dispatch by canvas (radial for
  Foundation/Actors, dagre for Services/Detail), so the literal
  "(dagre LR)" tooltip was a lie on half the canvases. Tooltip is
  now just "Auto layout".

## [0.12.5] — 2026-05-03

### Fixed — **Radial auto-layout preserves the user's angle**
- v0.12.4's radial placed peers around the project in `doc.nodes`
  declaration order (top → clockwise), so a node the user had
  dragged to the right could end up on the left after auto-layout.
  The placement felt arbitrary because it ignored where the user
  put things.
- New behaviour: each peer keeps its **current angle** from the
  project anchor; auto-layout only normalises distance (snap onto
  the same ring) and nudges any pair that would sit within 15° of
  each other so they don't visually overlap. If the user dragged
  Identity to the right, it stays on the right.

## [0.12.4] — 2026-05-03

Three corrections from continued usage.

### Changed — **Auto-layout dispatches by canvas shape**
- `dagre LR` lays a graph out as a left→right tree, which only fits
  the canvases that *are* trees (Services, Service Detail). On
  Foundation and Actors — both "project anchor at the centre, peers
  around it" — it collapsed everything into a single horizontal row
  and broke the radial mental model.
- New `radialLayout` keeps the `project` anchor where it sits and
  spreads the other connected nodes on a circle around it (top-down
  start, equal angular steps, ring sized to the largest peer node).
  `SketchCanvas.handleAutoLayout` dispatches by `canvas_kind` —
  Foundation / Actors radial; Services / Service Detail stay dagre.

### Changed — **Label alignment: category left, service centre**
- v0.12.2 left-aligned service titles to read them as "headers", but
  in v0.12 the actual *header* role belongs to `category` (the
  container). Service nodes are leaves and read better centred like
  every other kind. So the conditional flips: only `category` uses
  `justify-start`; everything else (including `service`) stays
  centred.

### Changed — **Collapse button: lose the circle, grow the arrow**
- The 32×32 white-circle-with-shadow control read as a UI chrome
  blob detached from the label. Replaced with a borderless inline
  arrow at `text-xl` (`▸` / `▾`) that hugs the label, hover
  darkens. Same hit area, much less visual noise.

## [0.12.3] — 2026-05-03

Docs only — sync `CONCEPTS.md` to v0.12 reality.

### Changed — **CONCEPTS.md**
- Canvas table: Services row now `project / category / service`;
  Service Detail row drops `service (sub via parent_id)` (sub-service
  was eliminated in v0.12) and is labelled "(modal, per-service)".
- `service` kind: the "Top-level service" / "Sub-service" sub-sections
  are merged into a single v0.12 service definition with one typed
  field block (`target_side`, `what`, `value_created`, `scope`,
  `trigger`, `how`, `outcome`, `do`, `dont`).
- Design principles: the validator floor for the Services canvas is
  rewritten — `service` must sit under a `category`, no nested
  categories. The v0.11.2 "≥ 1 Foundation anchor on the Services
  canvas" rule is removed (anchors now live inside the per-service
  modal, not on the top view).
- Stylistic phrasings updated from "Service Detail canvas" to
  "Service Detail modal" wherever the old surface was named.

## [0.12.2] — 2026-05-03

Visual polish on the v0.12 surfaces, driven by direct usage feedback.

### Changed — **Collapse button is a clear circle, not a tiny chevron**
- The fold/unfold control on container nodes (categories on the
  Services canvas, sub-actor parents on Actors) was a 24×24 square
  with no border that visually disappeared. Now 32×32, `rounded-full`,
  white background with a slate border and shadow. Same arrow glyph,
  much higher discoverability.

### Changed — **Service titles align left**
- Service node labels were centered like every other kind. With the
  v0.12 service-as-leaf model the label reads better as a header,
  so service nodes now `justify-start`. Other kinds still center.

### Fixed — **Service-detail modal hides the redundant root node**
- The modal's inner canvas seeded a copy of the service itself as a
  visible node, even though the modal header already names it
  ("SERVICE DETAIL — Login"). The modal now filters the root
  (matched by `doc.service_ref === node.id`) from both the nodes
  and edges memos, so refs and composition read against an empty
  background.

## [0.12.1] — 2026-05-03

Two decisive bugs from the v0.12.0 cleanup pass.

### Fixed — **Service double-click now opens the detail modal**
- The intended v0.12 gesture (double-click a service → modal overlay)
  silently failed: `SketchNode`'s inner `dblclick` handler called
  `e.stopPropagation()` and opened the generic Edit Node modal,
  shadowing React Flow's `onNodeDoubleClick → onNodeDrill`. The
  `ServiceDetailModal` was unreachable via the documented gesture.
- `SketchNodeData` now carries an optional `onDrill`. `SketchCanvas`
  wires it for kinds where drill is the intended dblclick gesture
  (services-canvas service → detail modal; service_detail actor_ref →
  jump to actor master). `SketchNode` prefers `onDrill` over
  `onOpenBody` when both could fire, so the Edit Node modal stops
  hijacking drill-eligible nodes.

### Changed — **Inspector says "Service", not "Sub-service"**
- v0.12 eliminated sub-service, but `SketchInspector.ServiceFields`
  still branched on `isTopLevel` and rendered "Sub-service" as the
  section header for any service with a `parent_id` (i.e. all
  services on the v0.12 services canvas, plus the service_detail
  root). Header is now always "Service".
- The dead "top-level vs sub" branch is gone: every service surfaces
  the same six typed fields (`what` / `value_created` / `scope` /
  `trigger` / `how` / `outcome`) plus Do/Don't, matching v0.12's
  "service is one kind" model.

## [0.12.0] — 2026-05-03

A larger refactor — the **Service vs Category split**. v0.10.3's
choice to keep top-level service and sub-service in a single `service`
kind never matched the user's mental model: top-level was always a
*grouping* (Admin / App / Backend), and the actual unit of value
production+exchange was the sub-service. v0.12 splits them.

### Added — **`category` kind**
- New top-level kind on the Services canvas. Categories are pure
  containers — they don't carry actor_refs, foundation refs, or any
  composition. Services nest inside them.
- One typed field: `theme` (one-line common thread).
- Stencil: a Category preset (top-level) and a Service preset that
  drops *inside* a category container.
- Validator: services on the Services canvas must have a category
  parent; categories must be top-level (no nested categories).

### Changed — **Service is now a leaf**
- The "service hierarchy depth = unlimited" rule from v0.10.3 is
  retired. A service has no sub-service. The Services canvas reads
  exactly two levels: `category → service`.
- All the previous sub-service typed fields (`value_created` /
  `trigger` / `how` / `outcome` / `do` / `dont`) and the v0.11.4
  `target_side` field stay on `service` exactly as before.

### Changed — **Service detail is now a modal overlay**
- Double-clicking a service no longer swaps the main canvas. The
  Services canvas stays mounted; the detail content opens in a
  modal overlay (Esc / backdrop click closes).
- The on-disk `service_detail/{id}/detail.json` file structure is
  unchanged. The change is purely UI — modal instead of canvas-swap.
- The drill-in breadcrumb is removed.

### Migration
- v0.1 → v0.2 split now seeds a single default `Category` ("Services",
  with `theme = "Migrated services"`) and parents the migrated
  top-level services under it.
- On read of the Services canvas, any orphan top-level services left
  by v0.11.x projects are silently re-parented under a seeded
  `default-category`. Idempotent.

### Notes
- 164 Python tests passing. Test fixtures updated to wrap services
  in a category. ruff / mypy / tsc all clean.
- `category` brings the kind count from 14 to 15.
- The "user can keep building deep service hierarchies" claim from
  v0.11.4 is rescinded for v0.12 — that's no longer the model. Depth
  in the picture maxes at category → service.

## [0.11.6] — 2026-05-03

Three small UX fixes from continued use.

### Removed — **Toolbar Download / Upload / save-state indicator**
- Save is automatic and silent already; the persistent indicator was
  noise. Errors still surface via the App-level error toast.
- `SketchToolbar` now only carries Undo / Redo / Auto layout.
- `SketchCanvasProps` no longer takes `saveState` / `onDownload` /
  `onUpload`; App.tsx drops `handleDownload` / `handleUpload`. JSON
  import/export, if it ever returns, will be a dedicated flow.

### Changed — **Top-level service default size shrinks**
- Was 300×200, now 180×100. Users still resize after drop; the
  smaller default keeps the Services canvas tidy when many top-level
  services are added (the previous size felt overscale next to the
  project anchor).

### Notes
- This release is viewer-only. Python schema unchanged.
- Pairs naturally with the user's flow after v0.11.5: drop a top-
  level service, drill in, and use the per-master stencil for refs.

## [0.11.5] — 2026-05-03

Two paired user-experience changes triggered by hands-on use.

### Changed — **Services top view only carries Project + Services**
- `_ALLOWED_KINDS_BY_CANVAS["services"]` is now `{"service", "project"}`
  (was `{"service", "project"} | _FOUNDATION_REFS`).
- All Foundation references (`mission_ref` / `value_ref` /
  `identity_ref`), participant references (`actor_ref`), and
  composition kinds (`metric` / `step`) are **service-detail-only**
  from now on. Sub-service decomposition already lives there, so the
  whole "rich detail" lives in one place.
- The v0.11.2 anchor hard validator on the Services canvas is dropped
  along with this change. Alignment ownership now lives inside each
  Service-Detail canvas.
- Migrator: read of an older Services canvas silently drops any
  Foundation ref nodes (idempotent) so existing projects open clean.

### Changed — **Stencil generates one draggable per master**
- The Service-Detail stencil no longer shows a generic "Mission ref"
  preset. Instead it renders **one draggable per master**, labelled
  with that master's real label and tinted with its colour. Ten
  missions on the Foundation canvas → ten mission entries on the
  Service-Detail stencil. Same for `value_ref`, `identity_ref`, and
  `actor_ref`.
- Drops are now **direct**: the preset already carries the target
  master id, so the picker no longer opens for the create flow. The
  picker is reserved for the Inspector's rewire button on orphans.
- `StencilCanvas` type gains a `service_detail` value; `App.tsx`
  passes `"service_detail"` whenever the user is drilled into a
  service detail (was always `"services"` before).

### Notes
- 162 Python tests passing. Existing fixtures padded to match the
  new allowed-kinds set.
- The Inspector's existing actor_ref / foundation_ref orphan UX
  (Re-pick / Delete) still works — the rewire flow keeps the picker.
- "Product as a kind" remains rejected from the v0.11.4 discussion.

## [0.11.4] — 2026-05-03

First user-experience-driven patch on the v0.11 model. Two paired
changes triggered by hands-on use:

- "Where's the project? Each canvas feels like it floats on its own."
  → Project anchor visible on every primary canvas.
- "Operator-facing services and user-facing services need to read
  differently at a glance."
  → New `target_side` typed field on `service`, mirror of `actor.side`.

### Added — **Project anchor on Actors / Services canvases**
- `_ALLOWED_KINDS_BY_CANVAS` admits `project` on Actors and Services
  in addition to Foundation.
- New `_seed_project_anchor()` factory; `_seed_actors_canvas()` and
  the new `_seed_services_canvas()` both seed it at the centre.
- `rename_project()` now propagates the rename to Actors / Services
  copies in addition to Foundation. All three labels stay in sync.
- `read_canvas` quietly backfills the anchor for projects created
  before v0.11.4 (idempotent).

### Added — **`service.target_side` typed field**
- `SketchNode.target_side: Literal["operator", "user", "both"] | None
  = None`. Mirror of `actor.side`.
- Inspector ServiceFields gains a Target side selector
  (운영자측 / 사용자측 / 둘 다 / 미지정).
- Canvas tints the service body by `target_side`:
  - `operator` → blue (`#dbeafe`)
  - `user` → red (`#fee2e2`)
  - `both` → violet (`#ede9fe`)
- No new kind. The two-axis classification (actor side ↔ service
  target_side) keeps the model's mental shape consistent.

### Notes
- Tests: 162 passing. Two existing fixtures updated for the new
  Actors / Services seeds.
- "Product" is intentionally **not** a new kind — operator-facing
  services and user-facing services are distinct service instances
  with different `target_side`, not a separate kind. This decision
  was confirmed during the discussion (see plan file).
- Users can keep building deep service hierarchies (sub-sub-service
  is fine — depth stays unlimited).

## [0.11.3] — 2026-04-30

Closes the v0.11 release line. Phase D (Mode 2 time-axis layer
compatibility) was verified without code changes — every Phase A/B/C
decision extends non-destructively when the time-axis kinds (Task,
schedule, etc.) are eventually added. The infrastructure layer joins
Mode 2 as already documented in IDENTITY.md.

### Changed — `docs/ROADMAP.md`
- Reorganised to cover both v0.10 and v0.11 release lines with a
  per-phase ship table for v0.11.

### Notes — what's next
- v0.11 model is now intentionally stable. The next round is
  **user-experience polish** — known follow-ups (e.g. node click
  going to label-edit instead of opening the Inspector) and anything
  surfaced by hands-on use of the new actor/service model.
- Mode 2 (time-axis task layer) waits until that polish round
  generates concrete requirements.
- No code or schema changes in this release.

## [0.11.2] — 2026-04-30

Phase C of v0.11. Two long-standing soft rules graduate to hard
validators, and `actor_ref` joins the typed-field family with a
per-actor-per-service value-flow pair.

### Added — **`actor_ref` typed fields (Phase C3)**
- `SketchNode.gives: str = ""` — what this actor gives to the service.
- `SketchNode.receives: str = ""` — what this actor receives back.
- Inspector renders an "Value flow" form on `actor_ref` selection
  with the two fields side by side. Both optional.
- Rationale: PHILOSOPHY.md P6 ("arrows carry action + value") in its
  weakened form. The flow lives on the ref node rather than on an
  explicit edge, so the value economy is captured per-pair without
  forcing the user to draw and label dozens of arrows.
- `service.value_created` (aggregate) and `actor_ref.gives` /
  `receives` (per-pair) are deliberately orthogonal.

### Changed — **Top-level service Foundation anchor is now a hard
validator (Phase C2)**
- A `services` canvas containing at least one top-level service must
  also contain at least one Foundation reference (`mission_ref` /
  `value_ref` / `identity_ref`). An empty services canvas is fine.
- The same rule was already in IDENTITY.md and CONCEPTS.md as docs;
  this release wires it into Pydantic.
- Mapping is **canvas-level, not per-service**: the visual layout
  (which anchor sits next to which service) carries the 1:1 nuance.
  This keeps the model schema free of new fields and matches the
  existing `mission_ref` placement pattern from v0.10.2.
- Migrator: legacy v0.1 sketches whose split overview canvas had no
  anchor get a single `mission_ref → "mission"` seeded automatically
  so the canvas validates after open. Idempotent.

### Notes
- Tests: 162 passing. New test `test_overview_services_without_anchor_rejected`
  asserts the new floor; existing fixtures padded with anchors.
- Phase D (time-axis compatibility + v0.11 vs v0.12+ scoping) remains
  the last v0.11 step.

## [0.11.1] — 2026-04-30

Phase B of v0.11. The `actor_ref` orphan UX (re-pick, delete) now
extends to all four ref kinds, and ref labels stay in sync with their
masters automatically.

### Added — **Foundation ref orphan UX**
- `mission_ref` / `value_ref` / `identity_ref` Inspector blocks now
  show a **Re-pick…** + **Delete** button pair when the master is
  missing from the Foundation canvas. Mirrors the existing
  `actor_ref` orphan UI.
- `FoundationRefPicker` already supported a `rewire` mode (since
  v0.10.2); this release wires it through `SketchCanvas` so the
  Inspector's Re-pick button opens the picker and the user-selected
  master replaces the orphan's `ref_*_id`.

### Added — **Ref label auto-sync**
- The displayed label for any ref kind (`actor_ref`, `mission_ref`,
  `value_ref`, `identity_ref`) is now **derived from the master at
  render time** — `→ {master.label}`. The stored label remains as a
  fallback for the orphan case (master missing).
- This means: rename the master `Mission` to `우리의 사명`, and every
  `mission_ref` on every canvas updates instantly with no propagation
  step. No more stale denormalised labels.

### Notes
- Implementation: the label transform happens in `SketchCanvas`'s
  React Flow node mapping (`useMemo`), via lookups against the
  `availableActors` / `availableMissions` / `availableValues` /
  `availableIdentities` props the App already passes through. No
  backend / migration change needed.
- Phase C (Service field polish) and Phase D (time-axis
  compatibility) remain.

## [0.11.0] — 2026-04-28

The Actor model promised by v0.10.6 / v0.10.7 lands as code. Phase A
of the v0.11 redefinition (A1–A5) is fully implemented; B/C/D follow
in later releases.

### Added — **Actor typed fields**
- `SketchNode.motivation: str = ""` — why this actor participates.
- `SketchNode.pain: str = ""` — frictions / frustrations they face.
- `SketchNode.side: Literal["operator", "user"] | None = None` —
  flat category; partitions actors by which side of the value
  exchange they occupy. Set on every actor; mirrored onto every
  `actor_ref` so service-detail canvases can validate operator/user
  mixes without cross-canvas lookups.
- Inspector renders an `Actor` form (Side selector + Motivation +
  Pain textareas) when `kind === "actor"`.

### Changed — **Hard validators**
- `actors` canvas now requires **≥ 2 actor classes**.
  IDENTITY.md baseline: a project without two sides can't host value
  exchange. New projects seed two placeholders (Operator + User) so
  this floor is satisfied out of the box.
- `service_detail` canvas now requires **≥ 2 `actor_ref` nodes**.
  Auto-creation paths (`sync_details_with_overview`, the v0.10
  migrator) seed two stub refs (operator + user) for every new or
  migrated detail canvas.

### Added — **Project + migration seeding**
- `_seed_actors_canvas()` (folder_io.py) seeds two actor classes
  ("Operator" + "User", with `side` set) on project creation.
- Migration path (`_backfill_actor_sides` + `_ensure_minimum_actors`
  + `_detail_actor_ref_seeds`) heals legacy v0.10.x projects on open:
  defaults missing `side` to `"user"`, pads under-populated actors
  canvases, and seeds operator/user actor_refs for any service_detail
  that doesn't already have them. Idempotent.

### Changed — **`docs/CONCEPTS.md` actor section**
- Adds the "two orthogonal mechanisms" subsection (`side` flat
  category + `parent_id` is-a tree) — the central insight from Phase
  A3 of the discussion.
- Documents the v0.11 typed fields (`motivation`, `pain`) and notes
  the deliberate exclusion of Do/Don't and permissions from the
  actor.

### Notes
- Phase A discussion log lives at
  `~/.claude/plans/ancient-pondering-petal.md`.
- Phase B (actor_ref Symbol justification + orphan UX), Phase C
  (Service field polish), and Phase D (time-axis compatibility) are
  the remaining v0.11.x work.
- This release re-asserts every IDENTITY.md floor as Pydantic
  validation, not just doc text. Existing projects migrate cleanly;
  no data loss is expected.

## [0.10.7] — 2026-04-28

Docs-only patch capturing the load-bearing Actor / Service decisions
made in v0.11 Phase A1 + A2 planning. The code changes (validators,
seed actors) ship later as v0.11.0; this release is the philosophy
front-load so the docs are accurate before any model moves.

### Added — `IDENTITY.md` "Actor & Service — the Core Philosophy" section
- **Actor definition**: a *class of people* who participate in the
  project's value economy. Class, not individual; people only — APIs,
  systems, bots, and infrastructure are out of scope until Mode 2.
- **Service definition**: a *playground* where stakeholders **produce
  and exchange** value (the dual phrasing is deliberate — services
  produce new value through actor participation, not just route
  pre-existing value).
- **Service minimum baseline**: every service must include **≥ 2**
  participating `actor_ref` nodes — non-negotiable.
- **Operator-explicit rule**: the operator/developer must always be
  one of those `actor_ref`s. The reasoning is moderation: services
  are playgrounds, freedom needs alignment-keepers, and *which*
  operator owns alignment for *which* service must be visible —
  exactly Novel's stated purpose.
- A "Why these are philosophy, not just rules" subsection explains
  that loosening any of these floors changes the product, not just
  the schema.

### Changed — `CONCEPTS.md`
- `actor` kind: redefined as "a class of people," with the people-only
  scope and the project-level `≥ 2` floor stated. Previous "person /
  system / organisation" wording retired.
- `service` kind: re-introduced with the playground metaphor,
  "produce + exchange" phrasing, and a new explicit subsection
  documenting the service minimum baseline (≥ 2 actor_refs, explicit
  operator).
- "Design principles" #2 ("templates rich, requirements minimal") now
  enumerates the current set of hard floors and cross-references
  IDENTITY.md.

### Notes
- This is **not** a behaviour change. The validators and the seed
  actors (User / Operator placeholders) land in v0.11.0 once the rest
  of Phase A — A3 (sub-actor semantics), A4 (typed fields), A5
  (naming) — and Phase B / C / D are decided. Doing docs first means
  the model changes can be evaluated against a stable spec.
- Plan-file framework with the running discussion log lives at
  `~/.claude/plans/ancient-pondering-petal.md`.

## [0.10.6] — 2026-04-28

Docs-only patch ahead of v0.11. Captures Novel's product identity in
permanent storage so future sessions (human or AI) can ground their
decisions in what Novel actually is — and is not.

### Added — **`docs/IDENTITY.md`**
- New canonical document stating what Novel is (a strategic operations
  design + alignment tool) and what it is not (a simple mindmap or
  brainstorming tool).
- The four use purposes: concrete service planning, direction alignment,
  position in the big picture, relationship visualisation.
- The two modes — today's picture mode and the future time-axis task
  mode — and the implication that v0.11+ models must survive the
  transition.
- Korean original quote from the user (2026-04-28) preserved so the
  source intent is auditable.

### Changed — `docs/CONCEPTS.md`
- Header now points to `IDENTITY.md` first. CONCEPTS remains the
  technical reference (kinds, canvases, fields); IDENTITY is the
  "why and for whom" check applied before any new concept lands.

### Notes
- This release contains no code changes. It exists to fix a gap caught
  during v0.11 planning: the user-stated identity from 2026-04-28 was
  living only in the in-progress plan file, which is volatile across
  sessions.

## [0.10.5] — 2026-04-28

Step 6 of the v0.10 kind-redefinition program — and the **final** step.
The two pre-existing composition kinds (`rule`, `content`) gain typed
fields so the Inspector can drive them as deterministically as the
kinds added earlier in v0.10.

### Added — **`rule` typed fields**
- `SketchNode.policy: str = ""` — the rule statement.
- `SketchNode.enforcement: str = ""` — how it's enforced.
- `SketchNode.actor_permissions: dict[str, str] = {}` — actor-id →
  permission-string map. Free-form value; suggested vocabulary is
  C/R/U/D shorthand (`"RUD"`, `"CRUD"`, etc.).

### Added — **`content` typed fields**
- `SketchNode.format: str = ""` — artifact shape (JSON, MD, image, …).
- `SketchNode.producer_actor_id: str | None = None` — actor master id
  that creates the content.
- `SketchNode.consumer_actor_id: str | None = None` — actor master id
  that consumes it.

### Added — **Expandable Inspector rows**
- The `CompositionList` rows for Rules and Contents are now expandable
  via a chevron toggle. Collapsed: just the label input. Expanded:
  the kind-specific typed form.
- Rule form includes a **permission editor**: a dropdown of actor
  masters not yet assigned + a per-row permission text input + a
  remove button.
- Content form includes producer/consumer **actor pickers** populated
  from the same `availableActors` list the Inspector already uses.

### Notes
- `actor_permissions` is keyed by actor master id (matching the
  `actor_ref` semantic from Step 3); the editor surfaces the actor's
  label for readability.
- The permission string is intentionally free-form for v0.10. A future
  release may switch to a richer schema (e.g. `{create, read, update,
  delete}` booleans) once the convention settles.
- This release closes out the v0.10 kind-redefinition program: every
  kind now has a clear semantic purpose, typed fields where the
  domain has separable facets, and Inspector rendering. The next
  release line can focus on edge utilisation or the time-axis layer.

## [0.10.4] — 2026-04-28

Step 5 of the v0.10 kind-redefinition program. Two new composition
kinds for the Service-Detail canvas — explicit success indicators
(metrics) and ordered procedural flow (steps).

### Added — **`metric` kind**
- New node kind admitted only on the **service_detail** canvas, with
  the same parent-must-be-a-service rule that already governs
  `rule` / `content`.
- Typed fields:
  - `target: str = ""` — goal value or threshold (e.g. `>99%`).
  - `measurement: str = ""` — how the metric is measured.
- Stencil entry on the Services-tab stencil under "Composition"
  (drop on a Service container).

### Added — **`step` kind**
- New node kind admitted only on the **service_detail** canvas, same
  parent constraint as the other composition kinds.
- Typed fields:
  - `order: int | None = None` — ordinal position in the sequence;
    `None` leaves the step unordered (e.g. parallel branches).
  - `outcome: str = ""` — observable end state. Shared with `service`
    (declared once on the model in v0.10 Step 4).
- Stencil entry on the Services-tab stencil under "Composition".

### Changed — **`_COMPOSITION_KINDS`**
- Now `{rule, content, metric, step}`. Inside a `service_detail`
  canvas all four kinds must have a service parent.

### Notes
- `metric` and `step` are canvas-first composition (visible on the
  Service-Detail canvas), unlike `rule` / `content` which remain
  Inspector-only `+ Add` items. The model accepts both kinds in either
  position; the editorial choice is a UI policy.
- Inspector forms render the typed fields per-kind. Drop validator
  rejects metric/step placed at top level with the standard
  "Drop inside a Service container" message.

## [0.10.3] — 2026-04-28

Step 4 of the v0.10 kind-redefinition program. Service nodes gain typed
fields differentiated by canvas — top-level services (the strategic
view) and sub-services (the operational view) get different forms while
sharing one model.

### Added — **Service typed fields**
- `SketchNode` gains six optional `str` fields (default `""`):
  - Top-level focus: `what`, `value_created`, `scope`.
  - Sub-service focus: `value_created`, `trigger`, `how`, `outcome`.
  - The shared Do/Don't pair from Step 2 (`do`, `dont`) is reused.
- One model carries all six on every service node; the **Inspector**
  surfaces them per branch:
  - `kind === "service"` on the **services** canvas with no parent →
    Label · What · Value created · Scope · Do · Don't.
  - `kind === "service"` on a **service_detail** canvas →
    Label · Value created · Trigger · How · Outcome · Do · Don't.

### Notes — **No hard validator gating**
- The ROADMAP suggested gating top-level services on either a
  Foundation ref or non-empty `value_created`. Per the v0.10 design
  philosophy ("rich fields, minimal required"), this is **not** a
  hard validator: writes succeed regardless. The Inspector's typed
  form makes the missing fields visible without blocking drafting.
- Round-trip and per-branch tests added in `tests/test_canvas_doc.py`.

## [0.10.2] — 2026-04-28

Step 3 of the v0.10 kind-redefinition program. Generalises the existing
`actor_ref` Symbol/Component pattern to the three Foundation masters
(Mission / Core Value / Identity), so a Service can declare which
Foundation commitment it answers to without leaving its canvas.

### Added — **Foundation reference kinds**
- New node kinds: `mission_ref`, `value_ref`, `identity_ref`. Together
  with the pre-existing `actor_ref` they form a uniform four-member
  family of "instance points at master" symbols.
- New `SketchNode` fields: `ref_mission_id`, `ref_value_id`,
  `ref_identity_id` (each `str | None = None`). Validator rule: every
  `*_ref` kind requires its corresponding `ref_*_id` to be set.
- `_ALLOWED_KINDS_BY_CANVAS`: the three new ref kinds are admitted on
  the **Services** overview canvas and on **Service-Detail** canvases.
  They stay forbidden on Foundation (would be a self-loop) and on
  Actors (out of place there).

### Added — **Stencil presets + picker UI**
- New stencil entries on the Services-side stencil: Mission ref, Value
  ref, Identity ref (under a "Foundation refs" section). Each gets a
  distinct hue and Lucide icon (flag / star / heart) so the canvas reads
  at a glance.
- New `FoundationRefPicker` modal — drop a ref onto the canvas, the
  picker lists candidates pulled from the Foundation canvas (Mission /
  Core Value / Identity, depending on the kind dropped). Clicking one
  spawns the ref node with the right `ref_*_id` set and a `→ {label}`
  display label.
- `App` derives the three master lists (`availableMissions`,
  `availableValues`, `availableIdentities`) from the Foundation canvas
  cache and passes them down to the canvas/inspector.

### Added — **Inspector ref display**
- The Inspector shows a "References — {kind}" block for each ref node,
  listing the resolved master label or a "⚠ master not found" warning
  when the target doesn't exist (orphan).

### Notes
- The orphan re-pick UX from `actor_ref` is **not** generalised in this
  step — for now users can drop a fresh ref preset and delete the
  broken one. Re-pick is on the list for a follow-up patch.
- The validator does not (yet) cross-check that `ref_mission_id` etc.
  point at an actual master in the project's Foundation canvas: writes
  succeed even with stale ids so drafting stays cheap; the Inspector's
  orphan warning surfaces the issue interactively.

## [0.10.1] — 2026-04-28

Step 2 of the v0.10 kind-redefinition program (see
[`docs/ROADMAP.md`](docs/ROADMAP.md)). Re-introduces typed fields on
the remaining two Foundation kinds, with the AI-first **Do / Don't**
pair shared between them.

### Added — **Core Value typed fields**
- `SketchNode.definition` (`str`, default `""`) — what the value means.
- Inspector renders a typed form when `kind === "core_value"`:
  Label · Definition · Do · Don't.

### Added — **Identity typed fields**
- `SketchNode.description` (`str`, default `""`) — how the aspect is
  expressed (Voice / Energy / Speech style / …).
- Inspector renders a typed form when `kind === "identity"`:
  Label · Description · Do · Don't.

### Added — **Shared Do / Don't pair**
- `SketchNode.do`, `SketchNode.dont` (`str`, default `""`). Both fields
  exist on every node so the schema stays uniform; only the Inspector
  forms for `core_value` and `identity` surface them today. Future kinds
  (Mission, Service) may opt in without a schema migration.

### Notes
- All four new fields are optional and default to `""` — none of them
  introduce a validator that could reject a legacy canvas. Mirroring
  v0.10 Step 1's principle: "rich fields, minimal required".
- Long-form prose still belongs in `details.md` per node. Typed fields
  are for short, structured facets that an LLM (or human reader) can
  consume deterministically.

## [0.10.0] — 2026-04-28

This release kicks off the v0.10 kind-redefinition program (see
[`docs/CONCEPTS.md`](docs/CONCEPTS.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md)).
Step 1 ships the rename of the identity canvas and the first AI-first typed
fields on `mission`. Subsequent steps will re-introduce typed fields on the
remaining kinds where the domain has clearly distinct facets.

### Changed — **`core` canvas → `foundation` canvas**
- Canvas kind/id rename: `"core"` → `"foundation"`. The folder is now
  `.plot/{project_id}/foundation/canvas.json`. Existing v0.5–v0.9 projects
  are migrated transparently on open: the `core/` directory is renamed to
  `foundation/` and the `canvas_kind` field is rewritten. Legacy alias
  `migrate.upgrade_core_canvas_if_needed` still works.
  ([`mashbill/folder_io.py`](mashbill/folder_io.py),
   [`mashbill/migrate.py`](mashbill/migrate.py),
   [`mashbill/models.py`](mashbill/models.py))
- Viewer tab label is now **Foundation** (not Core); `CanvasKind` /
  `CanvasKey` types match. Default folder slug is `foundation/…`.
  ([`viewer/src/types.ts`](viewer/src/types.ts),
   [`viewer/src/App.tsx`](viewer/src/App.tsx),
   [`viewer/src/lib/slug.ts`](viewer/src/lib/slug.ts))

### Added — **Mission typed fields** (AI-first)
- `SketchNode.what_we_do`, `SketchNode.why`, `SketchNode.direction` (all `str`,
  default `""`). These three facets are stored directly on the `mission` node
  in `canvas.json` — Novel is the sole editor. Long-form prose still lives in
  `details.md`. Other kinds also carry the fields as empty strings; only the
  Inspector for `kind === "mission"` exposes a typed form.
  ([`mashbill/models.py`](mashbill/models.py),
   [`viewer/src/types.ts`](viewer/src/types.ts),
   [`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx))

### Added — **Concept docs**
- [`docs/CONCEPTS.md`](docs/CONCEPTS.md) — the full glossary
  (4 canvases × 13 kinds + design principles). SSOT for human and AI tooling.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — six-step v0.10 implementation
  plan. Step 1 is this release.

### Notes
- Mission is **0..N** (was effectively 1..N). Validator unchanged; the doc
  surface now matches what the model already allowed since v0.5.
- Foundation rename is backward-compatible at the file-system layer — opening
  a v0.9 project rewrites it in place to the new layout.

## [0.9.1] — 2026-04-28

### Removed
- **Typed fields on `SketchNode`** (`tagline`, `audience`, `method`, `goal`, `summary`, `criteria`). For most kinds the typed `summary` was just a worse copy of `label`. The viewer's `TypedFieldsForm` and the per-kind `TYPED_FIELDS` map go with them. Long-form structure (Tagline / Audience / Method / Goal sections) now lives wherever the user wants it inside `details.md`.
- **`details.md` legacy text bridge from v0.1 migration** — the old core-root `mission` / `identity` text used to land in `tagline` / `summary`. With those fields gone the text is dropped on migration. The structural mission / identity nodes still get created so the user can paste the text into the new node's `details.md` if they care. (Practically nobody ever ran v0.1 → v0.9 on real data.)
- **`leftover bodySections.ts` viewer file** — finally tracked the deletion that should have ridden along with v0.9.0.

### Notes
- Inspector layout per node is now: **Label** input + per-node **`details.md` editor** (or "Create details" button). That's it. No middle tier.
- On-canvas node preview is just the label — the body block is hidden when `data.body` is empty (which it always is now).
- `details.md` is still SSOT for prose; external editors (Obsidian, VS Code) can still edit it freely with watcher-driven sync.

## [0.9.0] — 2026-04-26

### Changed — **typed JSON fields + per-node `details.md`** (no more sync conflicts)
- **JSON and MD now hold different data.** Typed short fields live on the node in `canvas.json` and are written/read only by Novel; long prose lives in a per-node `details.md` and Novel reads/writes that file just like any other editor (Obsidian, VS Code) can. Same content is never duplicated, so the sync question that haunted v0.7 / v0.8 disappears entirely. ([`mashbill/models.py`](mashbill/models.py))
- **`SketchNode` typed fields**: `tagline`, `audience`, `method`, `goal`, `summary`, `criteria`. All optional; Inspector renders kind-specific subsets (Mission → Tagline/Audience/Method/Goal, CoreValue → Summary/Criteria, Identity / Project → Summary).
- **`SketchNode.body` is gone.** Its preview-cache role is moot (typed fields are direct), and its long-form-edit role moves to `details.md`. v0.1 migration drops legacy `mission` text into `tagline`, `identity` text into `summary`.
- **`SketchNode.folder_path` → `SketchNode.details_path`.** Same path-traversal validator, clearer name (it points at the node's `details.md`, not a generic folder).
- **Inspector**: dropped the H3-section `KindTemplate` and the `ConnectToFolderButton` flow. Replaced with `TypedFieldsForm` (binds directly to typed fields) + `DetailsSection` (opens `MDFileEditor` if `details_path` is set, otherwise shows "Create details"). ([`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx))
- **External MD editing is now safe.** The watcher tracks `details.md` files too — edits in Obsidian, VS Code, or any other editor raise a `project_changed` event and the open viewer reloads. There's nothing to drift because the JSON has no mirror of the MD content. ([`mashbill/watcher.py`](mashbill/watcher.py), [`mashbill/broadcast.py`](mashbill/broadcast.py))
- **On-canvas node preview** now picks from typed fields directly: Mission shows `tagline` (falling back to `summary`); everything else shows `summary`. No more H3 parsing on the client.

### Removed
- `mashbill/body_sections.py`, `viewer/src/lib/bodySections.ts`, `tests/test_body_sections_py.py` — no callers.
- `_sync_node_body_cache_on_md_write` and the `preview` field on `PUT /api/files` — typed fields are direct, no cache to sync.
- `ConnectToFolderButton`, `KindTemplate`, `REFERENCES_FIELD`, `TEMPLATES` (Inspector).
- `body` field on `SketchNode` (Python and TypeScript).
- Long-form textarea in `SketchBodyModal` (visual properties only now).

### Notes
- **No automatic migration from v0.8.** User confirmed no production data; v0.9 is a clean break.
- `details.md` is intentionally never parsed by Novel. Use whatever Markdown layout you like — `# Heading`, tables, Mermaid blocks, etc.

## [0.8.0] — 2026-04-23

### Changed — **breaking disk-layout refactor**
- **`.plot/` is wrapper-less and canvas-grouped.** Every project now owns a single folder under `.plot/` containing one subfolder per canvas kind; each canvas folder holds its structure (`canvas.json`) alongside its nodes' content folders. The former sibling `workspace/` tree is gone — long-form content lives inside the project's own folder.
  ```
  .plot/{project_id}/
    project.json
    core/
      canvas.json
      {slug}/index.md
    actors/
      canvas.json
      {slug}/index.md
    services/
      canvas.json                 ← top-view
      {service_id}/
        index.md
        detail.json               ← per-service drill-down
  ```
  - `.plot/sketches/` intermediate removed.
  - `core.json` / `actors.json` / `services-overview.json` → `{canvas}/canvas.json`.
  - `services-detail/{sid}.json` → `services/{sid}/detail.json` (co-located with the service's `index.md`).
- **`CanvasKind` literal `services_overview` → `services`.** Tab label is already "Services" — the canvas key now matches.
- **`/api/files`, `/api/folders` are project-scoped.** `project_id` is required; `path` is relative to `.plot/{project_id}/`. Client can no longer accidentally address another project's tree via `..`.
- **`folderSlug` drops the `workspace/` prefix.** Returns `{canvas}/{kind}-{label}` on both server (`mashbill/slug.py`) and client (`viewer/src/lib/slug.ts`).
- **`sync_details_with_overview`** archives a service's whole folder (including `index.md`) to `services/_archive/{sid}/` when it disappears from the top-view — the previous `.json`-only archive would have orphaned any long-form notes.

### Removed
- `workspace/` wrapper folder (everything moved inside `.plot/{project_id}/`).
- `services-detail/` dedicated folder.
- `.plot/sketches/` intermediate directory for new projects (legacy v0.1 migration still reads from it when it exists).

### Notes
- **No automatic migration from v0.7.** The user confirmed no production data — BANAS is a dev-only artifact. Opening an old v0.7 project in v0.8 will look empty; re-create or run a manual port.
- v0.1 → v0.4 auto-migration path still works and lands new projects in the v0.8 layout.

## [0.7.1] — 2026-04-23

### Added
- **Inspector width toggle** (`⇤` / `⇥`). Narrow stays at 320px; wide expands to `min(720px, 60vw)`. Choice persists in `localStorage` so the next node opens at the user's preferred size. ([`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx))
- **MDPreview component + Edit / Split / Preview tabs in the MD editor.** Rendered view is powered by `react-markdown` + `remark-gfm` (tables, task lists) plus a custom code renderer that pipes `` ```mermaid `` blocks through `mermaid.render`. Diagrams appear inline; parse errors fall back to the raw source instead of crashing the Inspector. Split mode pairs well with the wide Inspector for drafting diagrams next to the source. ([`viewer/src/edit/MDPreview.tsx`](viewer/src/edit/MDPreview.tsx), [`viewer/src/edit/MDFileEditor.tsx`](viewer/src/edit/MDFileEditor.tsx))

## [0.7.0] — 2026-04-23

### Added
- **Folder-backed node content — Inspector becomes an MD editor.** Click a node with a `folder_path`, the right panel turns into a full Markdown editor for that folder's `index.md`. Free-form text, structured ### H3 sections, wiki links — all round-trip to disk via a 600 ms debounced save. Mirrors the Claude-skill pattern the user asked for ("each node = folder, each folder has an `index.md`"). ([`viewer/src/edit/MDFileEditor.tsx`](viewer/src/edit/MDFileEditor.tsx))
- **`SketchNode.folder_path` field.** Optional relative path (under `project_path`) that binds a node to a folder on disk. When set, `body` holds only a short summary cache for the canvas preview; the long-form lives in the MD file. Validator rejects absolute paths, `..` segments, and blanks. ([`mashbill/models.py`](mashbill/models.py))
- **`/api/files` and `/api/folders` endpoints.** `GET /api/files`, `PUT /api/files`, `POST /api/folders`. Path-traversal, absolute paths, and symlink-escapes are all rejected; writes go through a tmp-rename so readers never see half a file. Folder POST uniquifies on collision (`-2`, `-3`, …). ([`mashbill/file_io.py`](mashbill/file_io.py), [`mashbill/api_endpoints.py`](mashbill/api_endpoints.py))
- **Server-side preview cache sync.** `PUT /api/files` with `project_id` + `node_id` query hints parses the saved `index.md`, picks the `### Tagline` (Mission) or `### Summary` (everything else), and mirrors it into the node's `body`. The on-canvas preview stays current without a separate fetch per node.
- **"Connect to folder" button in Inspector.** Legacy body-backed nodes (BANAS and everything shipped before 0.7) can opt into the folder model one click at a time: the button asks the server for a fresh folder based on `kind + label`, seeds `index.md` with whatever `body` already had, and attaches `folder_path`. No big-bang migration. ([`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx))
- **Shared slug convention.** `mashbill/slug.py` + `viewer/src/lib/slug.ts` compute the same default folder path — `workspace/{canvas}/{kind}-{label-slug}/` — so the client doesn't need a round-trip just to guess a name. Korean and CJK characters are preserved; server uniquifies on collision.

### Notes
- BANAS (and any pre-0.7 project) keeps working exactly as before until the user presses "Connect to folder" on a node. Migration is opt-in, not automatic.
- `index.md` is free-form. Use whatever headings you like — `### Tagline` and `### Summary` are the only ones the canvas preview reads.

## [0.6.0] — 2026-04-22

### Added
- **Markdown body rendering.** `SketchNode` now renders its body through `react-markdown`, so Inspector template fields (`### Tagline`, `### Summary`, …) appear as small uppercase section labels inside the node, and bold / italic / lists / links stay readable. Left-aligned body text reads naturally once multiple sections are stacked; the label keeps its centred treatment. ([`viewer/src/canvases/SketchNode.tsx`](viewer/src/canvases/SketchNode.tsx))
- **References field in Inspector templates.** Mission / Core Value / Identity / Project each pick up a `References` field for wiki-style links (e.g. `[[workspace/identity/mission.md]]`) pointing at long-form narrative docs. Novel stays the structural SSOT; MD files stay the narrative SSOT — no auto-sync. ([`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx))

## [0.5.1] — 2026-04-22

### Fixed
- **Legacy Core children no longer trap inside the Project anchor.** Pre-v0.5 projects (like BANAS) stored Mission / Identity nested under a `core`-kind octagon. The v0.5 upgrade now un-parents every node whose `parent_id` pointed at a legacy core anchor, so after opening the pillars land as peers around the small circular Project — not inside it. ([`mashbill/migrate.py`](mashbill/migrate.py))

### Changed
- **Top-left kind tag on Core nodes.** Mission / Core Value / Identity / Project nodes carry a small uppercase "MISSION" / "CORE VALUE" / … label in the top-left so the kind is legible at a glance, before opening the Inspector. ([`viewer/src/canvases/SketchNode.tsx`](viewer/src/canvases/SketchNode.tsx))
- **Star icon retired from Core kinds.** Mission / Core Value / Identity / Project no longer seed with a `star` icon (every Core kind had the same star, so it couldn't tell them apart). The new kind tag carries the identity signal. Legacy disk files carrying `icon: "star"` on Core kinds get cleaned up on the next open.
- **Fold button shifted to 24×24** (was 16×16) so it's no longer easy to miss. The Core canvas suppresses it entirely — Core is a peer layout, fold has no meaning there. Other canvases (actors / services) keep it.

## [0.5.0] — 2026-04-22

### Added
- **Project anchor on the Core canvas.** Every project now carries a central, circular **Project** node — auto-seeded on create / on the first open of a legacy project, protected from deletion (keyboard Delete, right-click Delete, Inspector Delete all refuse to touch it), and label-synced with `ProjectDoc.name` in both directions. Rename from the sidebar updates the node; editing the node label renames the project (the server reconciles on `PUT /canvases/core`). ([`mashbill/folder_io.py`](mashbill/folder_io.py), [`mashbill/migrate.py`](mashbill/migrate.py), [`viewer/src/canvases/SketchCanvas.tsx`](viewer/src/canvases/SketchCanvas.tsx))
- **Multi-Mission and multi-Identity on the Core canvas.** Mission is now 1..N (was exactly 1); Identity is now 1..N peers (was 1 + N Facet children). Each Identity node represents one aspect (Voice / Energy / Speech style / Visual tone / …) — drag the preset for every aspect you need. ([`mashbill/models.py`](mashbill/models.py))
- **Kind-aware Inspector templates.** Selecting a Mission / Core Value / Identity / Project node now surfaces the right fields instead of a bare Description textarea:
  - Mission → Tagline, Audience, Method, Goal, Story
  - Core Value → Summary, Decision criteria
  - Identity → Summary, Details
  - Project → Summary
  Fields persist as `### H3` Markdown sections inside `SketchNode.body` — no schema change, unknown sections and free-form notes round-trip untouched. ([`viewer/src/canvases/SketchInspector.tsx`](viewer/src/canvases/SketchInspector.tsx), [`viewer/src/lib/bodySections.ts`](viewer/src/lib/bodySections.ts))
- **Automatic v0.4 → v0.5 Core-canvas migration.** Opening a project with legacy `core`-kind octagons or `identity_facet` children heals itself lazily — the `read_canvas` path calls `upgrade_core_canvas_if_needed`, which rewrites kinds in-place and persists the result. No manual step. ([`mashbill/migrate.py`](mashbill/migrate.py))

### Changed
- **`NodeKind` shrinks.** Removed `core` (was the legacy octagon anchor) and `identity_facet` (absorbed into `identity`). Added `project`. Disk files carrying the retired kinds are rewritten on open.
- **`_core_canvas_rules`** relaxes Mission / Identity from "exactly 1" to "≥ 1" and adds "exactly 1 Project, top-level".
- **Stencil copy.** Mission / Core values / Identity sections now read "add as many as you need". Identity adds a hint listing example aspects. Identity Facet preset disappears.

### Fixed
- Right-click context menus no longer show their items with text pre-highlighted. The residual text selection the browser leaves behind on right-click is now suppressed with `select-none` + a `mousedown` preventDefault on the menu container. ([`viewer/src/canvases/SketchContextMenu.tsx`](viewer/src/canvases/SketchContextMenu.tsx))
- The Inspector no longer shows an empty "Select a node to see details" placeholder — it renders `null` when nothing is selected, reclaiming canvas width.

## [0.4.1] — 2026-04-21

### Added
- **Drop-overlap nudge.** Dragging a preset onto a spot already occupied by a sibling node no longer buries the new node behind the old one — the drop position slides diagonally by 32px until it finds a free slot (max 24 tries). Works for both top-level drops and container-nested drops. ([`viewer/src/canvases/SketchCanvas.tsx`](viewer/src/canvases/SketchCanvas.tsx))
- **Keyboard cheatsheet.** Press `?` anywhere to toggle a modal listing every shortcut; `Esc` or click-outside closes it. ([`viewer/src/App.tsx`](viewer/src/App.tsx))
- **Inspector delete button.** Every non-root, non-core node gets a `✕ delete` button in the Inspector header (with a confirmation prompt). The actor_ref orphan banner still has its own Delete button.
- **Inspector color swatch.** Small square next to the kind label shows the node's current fill colour at a glance.
- **Auto-layout now arranges Core / Actors / Detail canvases.** `autoLayout` treats `parent_id` relationships as implicit dagre edges, so the toolbar "Auto layout" button finally does something useful on canvases whose semantic links live in the hierarchy rather than in explicit edges. ([`viewer/src/flow/autoLayout.ts`](viewer/src/flow/autoLayout.ts))

### Fixed
- Tab-switch fit-view is now reliable: the canvas key includes the active canvas, so React Flow remounts and its `fitView` runs fresh on every tab change.

## [0.4.0] — 2026-04-21

### Added
- **Full viewer / HTTP cutover to the v0.2 folder layout.** New REST surface: `GET/POST /api/projects`, `GET/PATCH/DELETE /api/projects/{id}`, `GET/PUT /api/projects/{id}/canvases/{kind}[?service_id=]`. The viewer now loads one canvas at a time — no more in-memory tab-filtering. ([`mashbill/api_endpoints.py`](mashbill/api_endpoints.py), [`plot/viewer/src/api.ts`](viewer/src/api.ts))
- **Per-project git repo for session bookmarks.** Each project folder gets its own `.git/` at creation time, but editing never auto-commits. The user plants named tags at meaningful moments via the new **Mark session…** button or the `tag_project` MCP tool. `GET/POST /api/projects/{id}/tags` + `DELETE .../tags/{name}` expose the tag surface. ([`mashbill/git_store.py`](mashbill/git_store.py))
- **Project-level unified undo/redo.** New `useProjectHistory` hook holds one in-memory stack per loaded project with `{canvasKey, prev, next}` entries — `Ctrl+Z`/`Ctrl+Z+Shift`/`Ctrl+Y` rewinds any canvas's last edit and auto-switches tabs to where the change landed. 50-entry cap, cleared on project switch or external WebSocket write. ([`viewer/src/canvases/useProjectHistory.ts`](viewer/src/canvases/useProjectHistory.ts))
- WebSocket event shape: `sketch_changed` → **`project_changed`** with `{project_id, canvas_kind?, service_id?}` so the viewer only reloads the affected canvas.
- Sidebar has a **Session tags** collapsible panel listing the project's `git tag` entries with a hover × to delete (commit stays reachable via reflog).
- Silent v0.1 → v0.2 auto-migration on the first `GET /api/projects` call; banner toast reports what was migrated.
- New MCP tools: `tag_project`, `list_project_tags`, `delete_project_tag`. Canvas-level tools from v0.3 (`list_projects`, `get_project`, `get_canvas`, `update_canvas`, etc.) stay.

### Changed
- Sidebar "Sketches" → "Projects", "+ New sketch" → "+ New project". Summary's `node_count`/`edge_count` columns are dropped (canvases are loaded lazily now).
- `create_project` (Python + MCP) calls `git_store.ensure_repo` on the new folder.
- `mashbill/sketches.py` is now an internal module; only `migrate.py` imports it.

### Removed (breaking)
- `/api/sketches/*` REST endpoints — any external script that hit them needs to move to `/api/projects/*`.
- v0.1 MCP tool wrappers (`list_sketches_tool`, `get_sketch`, `create_sketch_tool`, `update_sketch`, `delete_sketch_tool`). Use the canvas-level equivalents.
- `useSketchHistory` viewer hook.

### Notes
- **Nested git repo.** `.plot/sketches/{id}/.git/` sits inside whatever project directory you're pointing Novel at. git naturally stops at inner `.git/` boundaries, so the parent repo sees `.plot/` as untracked. Recommended: add `.plot/` to your project's top-level `.gitignore`.
- Identity configured per-repo as `user.name=Novel`, `user.email=plot@noory-ai.local` so Novel commits don't inherit your global git identity.
- Undo/redo is in-memory only; tags are the durable history mechanism.

## [0.3.0] — 2026-04-21

### Added
- **Folder-per-project storage** — `.plot/sketches/{id}/` with one JSON file per canvas (`core.json`, `actors.json`, `services-overview.json`, `services-detail/{service_id}.json`). Writing one canvas no longer touches any other. ([`mashbill/folder_io.py`](mashbill/folder_io.py))
- **v0.1 → v0.2 migration** — `mashbill.migrate.migrate_v01_to_v02` (also exposed as the `migrate_v01_sketches` MCP tool). Idempotent; promotes `mission` / `core_values` / `identity` text fields on the core-root into their own nodes; multi-line core-values split into one node per line. Originals rename to `{id}.json.v01.bak`.
- **Canvas-level MCP tools** — `list_projects`, `get_project`, `create_project_tool`, `delete_project_tool`, `rename_project`, `get_canvas`, `update_canvas`, `list_detail_canvases`, `migrate_v01_sketches`. The legacy sketch tools stay available during the transition.
- **Overview ↔ Detail auto-sync** — writing the `services_overview` via `update_canvas` auto-creates a Detail canvas for any new service and archives (does not delete) the Detail of a removed service.
- **Actor_ref picker UI** — dragging "Actor ref" onto the Services canvas opens a modal listing every actor from the Actor canvas; picking one creates a reference node with `ref_actor_id` and a "→ {label}" prefix.
- Inspector shows a read-only `References` pill for `actor_ref` nodes.

### Changed
- Inspector no longer renders `mission` / `core_values` / `identity` text fields on root nodes — those are first-class node kinds now.

### Notes
- The v0.1 viewer (single-file `SketchDoc` + tab-filter) still works. Switching the HTTP layer and viewer to the new canvas-level API is a follow-up; until then, the new tools and folder layout are opt-in via MCP.

## [0.2.0] — 2026-04-21

### Added
- Multi-canvas split — the sketch is now viewed through three tabs (**Core**, **Actors**, **Services**) so each cognitive layer has its own canvas. The underlying `SketchDoc` stays single-file for v0.2; separate canvas storage arrives in a later release.
- **Core canvas** — drops for Mission, Core Value, Identity, and Identity Facet promote what used to be Inspector text fields into structural child nodes of the Core octagon.
- **Services drill-down** — double-click any non-root service in the Overview to enter its Detail view; a breadcrumb at the top navigates back. `?canvas=services&detail=<id>` makes the view deep-linkable.
- **Canvas-aware stencil** — each tab surfaces only the presets it can accept, and `resolveDropTarget` knows the new core-child / identity-facet parenting rules.
- `CanvasDoc` + `CanvasKind` in `mashbill/models.py` with per-canvas-kind validators (core: 1 mission + 1 identity; actors: actor-only; services-overview: top-level only; service-detail: requires service_ref matching canvas_id).
- Expanded `NodeKind`: `mission`, `core_value`, `identity`, `identity_facet`, `actor_ref`. `SketchNode.ref_actor_id` carries the pointer for Actor→Service references.
- 26 new tests in `tests/test_canvas_doc.py`.

### Changed
- `?canvas=` URL param now carries the active tab; refreshing lands back on the same canvas.
- `SketchSidebar.stencilCanvas` prop switches the presets shown in the stencil.

### Notes
- Backward compatible: existing v0.1 `.plot/sketches/{id}.json` files keep loading; legacy untyped nodes default to the Services tab.
- `SketchDoc`'s old `mission` / `core_values` / `identity` text fields on root nodes remain for round-tripping until the v0.1→v0.2 migration script lands.

## [0.1.0] — 2026-04-20

### Added
- Initial release.
- Schema-free sketch store at `.plot/sketches/{id}.json`.
- Starlette HTTP server on port 5190 with 5 endpoints (list / get / create / put / delete) + WebSocket push.
- FastMCP tool surface: `list_sketches`, `get_sketch`, `create_sketch`, `update_sketch`, `delete_sketch`.
- React Flow 11 viewer with full editing: multi-select, copy/paste, undo/redo, auto-layout (dagre), context menu, MiniMap, Controls, resize, color picker, body markdown modal.
- Claude Code plugin manifest + initial skills (`plot-help`, `plot-new-sketch`, `plot-read-sketch`).
