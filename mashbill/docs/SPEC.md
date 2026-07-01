# SPEC — Novel canvases

> **동작 RULE 정본은 root** (`D-2026-06-28-B`) — [`docs/specs/canvas-behavior.md`](../../../docs/specs/canvas-behavior.md)
> · [`edges.md`](../../../docs/specs/edges.md) · [`kinds-fields.md`](../../../docs/specs/kinds-fields.md).
> "무엇이 어떻게 작동하나"의 *현행 규칙*은 거기 있다(두 제품이 공유하는 동작 약속). 이 파일은
> 그 규칙의 **상세 구현·메커니즘·엣지케이스**(렌더 세부, 레이아웃, 인스펙터 상태, 워크스페이스/
> 프로젝트 구조 등)를 보유한다. **규칙이 충돌하면 root가 우선** — 이 파일엔 마라톤 전 잔재
> (폐기된 actor_ref `gives`/`receives`, 옛 kind 표기 등)가 일부 남아 있으니, 동작의 *현행 정의*는
> root에서 확인한다. 코드 메커니즘 세부(오토레이아웃·커서)는 `AUTO_LAYOUT`/`CURSOR`/`ARCHITECTURE`.

> **Scope:** 상세 동작이 가장 깊은 곳은 Foundation·Actors이고, Services 오버뷰·**feature**
> 캔버스(옛 Service-Detail — 서비스의 feature가 드릴해 들어감)·**Entities**는 모델만 핀,
> 상세 per-canvas 동작은 later expansion.

> **Status:** 코드·주석·옛 결정은 spec이 아니다 — root 규칙 + 명시 승인만 권위. 이 파일이
> 코드와 다르면 코드가 틀린 것; 이 파일이 root 규칙과 다르면 이 파일(낡음)이 틀린 것.

---

# Workspace & projects (v0.33.0, D-2026-05-31-M)

A **workspace is a monorepo, and a project is one service inside it**
(D-2026-06-12-A). Two apps in `apps/web/` and `apps/mobile/`, or two
services in `services/api/` and `services/billing/`, are two **separate
projects** in Novel — each with its own Foundation / Actors / Services /
Service-Detail canvases — sitting inside ONE workspace that shares ONE
git repo at its root (D-2026-06-11-C/D). Under **one-project-per-dir**
(D-2026-06-21-AA) each service lives in its **own** directory with its
**own** `.noory/novel` (R9) holding exactly one project — `create_project`
rejects a second project under a root that already has one
(`FileExistsError` → 409). The viewer **recursively discovers** every
project under the launch root (`/api/workspace/projects`) and shows them
in ONE sidebar list, each with a muted **dir label** (its path relative to
the workspace root; root-level shows the localized "root" label).

The term **"project"** in user-facing strings means "one service in the
monorepo" — not "the monorepo as a whole". Workspace-level affordances
("open another workspace", "the workspace path") refer to the monorepo.

- **Effective project path** — per-project server I/O (canvas read/write,
  anchors, tags, publish) addresses `<root>/<project dir>`, not the bare
  root. Switching to a project in a **different directory** reconnects the
  WebSocket to that dir's `.plot/`; switching between projects in the
  **same directory** does not reconnect.
- **Add a Project** (v0.34.0, D-2026-05-31-N) — the sidebar/empty-state
  "Add a Project" button opens a **directory-tree picker** (drill-down,
  rooted at the workspace root, `has_plot` badge per dir). Picking an empty
  dir creates a new project there; picking a dir that already holds a
  project lands in its most-recently-updated one (no duplicate). Tree-only
  — choose-from-existing-folders, no free-text new folder.
- **URL** — `?project_path=<root>` (workspace root) + `?project=<id>`. The
  active project's directory is resolved from discovery (id→dir map). Off-
  root absolute paths are out of scope (future native/desktop host).
- **Chrome (v0.34.3, D-2026-05-31-Q)** — the **workspace root absolute path**
  sits at the very top next to the `PLOT` logo (the "where am I" location);
  the **active project name** sits **centered in the canvas tab bar** (the
  "what am I working on"). The socket indicator reads **"MCP: live"** /
  "MCP: connecting…" / "MCP: reconnecting…" / "MCP: offline" so the dot
  clearly refers to the MCP server connection. (Supersedes D-2026-05-31-O's
  header-dir display and D-2026-05-31-P's root-in-tab-bar placement.)
- **Flavor badge (v0.66.0, D-2026-06-13-B)** — a small amber **`DEBUG`**
  chip sits next to the `PLOT` logo **only in the debug flavor**
  (`VITE_MASHBILL_DEBUG=1`). The release flavor renders nothing. Same
  BUILD-TIME gate as the debug probe (`debugEnabled()`, D-2026-06-09-D) —
  no runtime escape hatch, so a release build can never light it up. It
  is a build identifier, not localizable copy, so (like `PLOT` / "MCP:
  live") it stays out of i18n.
- **Version control (v0.53.0, D-2026-06-09-C)** — git lives at the `.noory/novel/`
  workspace level: **one repo per `.noory/novel/`**, not per project. `.noory/novel/{id}` no
  longer gets its own `.git`; `ensure_repo` / `tag_snapshot` / `publish_snapshot`
  all target `.noory/novel/`, so every project under one `.noory/novel/` shares one history
  (user: "워크스페이스에만 깃이 있어야 한다"). Session-bookmark tags and per-node
  publish commits live in this single repo.

- **Workspace = git repo (D-2026-06-11-C)** — the **workspace is the user's
  opened folder**, and that folder IS the git repo. `.noory/novel/` lives
  *inside* the workspace repo (alongside the user's own source / docs / `.env`
  / whatever they keep in that folder); Novel does not create its own `.git`
  under `.noory/novel/`. Consequence: tracking decisions (`.gitignore`) are the
  user's. If the user wants Novel's data tracked, it just is; if not, they
  add `.noory/novel/` to their `.gitignore`. Novel itself never auto-adds an
  ignore entry for its own data (the v0.53.0 → v0.59.x design that scoped
  the repo to `.noory/novel/` is superseded — see DECISIONS.md
  [D-2026-06-11-C](./DECISIONS.md#d-2026-06-11-c--workspace--git-repo-not-noory-plot)).

- **Git consent (D-2026-06-11-D)** — Novel **never silently runs `git init`** on
  the workspace. If `.git/` already exists, Novel uses it as-is (never touches
  `user.name` / `user.email` / `.gitignore` / `.gitattributes`). If `.git/`
  does NOT exist, the first tag/publish call replies with
  `{error: "git not initialized", needs_git_init: true}` and the viewer
  surfaces an **"Initialize git repo at `<workspace>`?"** modal; only an
  explicit Yes triggers `POST /api/workspace/git-init`. Novel-authored commits
  carry identity inline (`git -c user.name=Novel -c user.email=plot@noory-ai.local
  …`) so the user's repo-level config stays untouched. Novel's tag/publish
  stages **only `.noory/novel/`** (`git add -A -- .noory/novel/`) so the user's
  working-tree edits outside that path are never folded into a Novel commit.
  See DECISIONS.md
  [D-2026-06-11-D](./DECISIONS.md#d-2026-06-11-d--git-init-requires-explicit-user-consent-plot-never-auto-creates-git).

- **Data root = `.noory/novel/` (v0.59.0, D-2026-06-10-G, OVERHAUL R9)** — every
  plugin's per-project artifacts consolidate under ONE `.noory/` dotfolder per
  workspace (`.noory/novel/`, `.noory/distill/`, …), so plugin mode and app mode
  share artifacts continuously. A project lives **flat** directly under
  `.noory/novel/` (`project.json` + canvas dirs, no `{project_id}/` layer —
  one project per dir, D-2026-06-21-AB); a legacy nested `{project_id}/` is
  flattened up on open. A legacy pre-R9 `.plot/` root is migrated lazily on first open (one
  `shutil.move`); if BOTH roots exist, `.noory/novel` wins and `.plot` is left
  untouched for the user to reconcile. Workspace discovery also peeks at
  legacy `.plot/` roots (read-only) so never-opened workspaces stay visible.

---

# R7 chat — in-app AI panel (D-2026-06-11-E, revised D-2026-06-13-H)

The R7 chat surface ships as a **native panel** inside Novel, not a thin
"open Claude Code" launcher. The panel renders the conversation, the input,
and the message history in Novel's own chrome; the *brain* is the user's
external CLI, which Novel drives as a subprocess.

**Primary path is MCP, not the in-app panel (D-2026-06-13-H).** Novel is an
MCP server; the user connects their OWN interactive agent (Claude Code /
Codex / Gemini, already on their subscription) to it. The in-app subprocess
panel is the **secondary** convenience.

**claude-code in-app: allowed, with a billing warning (D-2026-06-14-B,
reversing the D-2026-06-13-H exclusion).** All three CLIs — Codex, Gemini,
and Claude Code — are selectable for in-app chat. Because driving Claude Code
in-app uses `claude -p` (headless), which Anthropic bills **separately** from
the Claude subscription, selecting it shows a warning banner in the chat
frame (`chat.claudeBillingWarning`) pointing the user to the non-double-charged
MCP path. There is no server-side block; the user opts in with the warning
visible.

| Aspect | Behaviour |
|---|---|
| **Brain** | The user's external CLI. For in-app chat Novel spawns `codex` / `agy` / `claude` (`claude -p`) inside the workspace folder and parses streamed output. The **`gemini` provider's transport is the `agy` (Antigravity) CLI** as Google consolidates Gemini onto it (D-2026-06-22-A): `agy -p --dangerously-skip-permissions` emits plain text (no `stream-json`), so its turns are plain-text passthrough and **stateless** (no per-scope resume — agy exposes no resume handle on stdout). Claude Code in-app shows a billing warning (D-2026-06-14-B) since `claude -p` bills separately from the subscription. |
| **Subprocess host (D-2026-06-12-D)** | The CLI subprocess lives in the **mashbill engine** (Python), not the Tauri shell. Viewer talks to it through `POST /api/chat/send` + `WS /ws/chat?project_path=…` — the same HTTP/WS transport every other Novel operation uses. Dev mode (browser at `:5193`) and the bundled `.app` therefore take identical code paths. |
| **API keys / billing** | Never Novel's job. The CLI is responsible for auth (`claude login`, etc.); token usage bills the user's Anthropic / OpenAI / Google account. Novel exposes no key-management UI. |
| **Provider selection** | Auto-detected at workspace open (which CLIs are on `$PATH` + logged in). User picks one when several are present via a radio per registered row; choice (+ model, D-2026-06-16-C) persists in the **active project's** `.noory/novel/chat-provider` (JSON `{"provider": "claude-code" \| "codex" \| "gemini" \| null, "model": str \| null}`) — per-project, not workspace-wide (D-2026-06-16-G). HTTP surface: `GET /api/chat/provider?project_path=…` reads, `PUT` writes. All three CLIs carry an in-app chat radio (D-2026-06-14-B); selecting `claude-code` shows the billing warning. Unregistering the active provider clears the selection automatically so the persisted choice can never name a CLI Novel can't reach. |
| **Context injection (D-2026-06-15-A, in-app)** | Each turn carries the active canvas + the live node selection. The viewer sends `selection` (`[{id, kind, label}]`) on `POST /api/chat/send`; the engine prepends a `[Novel context] Active canvas: <scope>. Selected (N): …` preamble to the CLI message so "fix this" resolves against the selection. The selection is read from the **active surface** — including the **service-detail canvas** (D-2026-06-16-F: the detail canvas reports its selection via `onSelectionChange`, and the dock reads the detail canvas's nodes, not just the main canvas). Per-turn snapshot; `project` scope injects nothing; selection capped at 20 detailed nodes (rest = ids only). In-app only — the MCP path is a follow-up. (CHAT_ARCH.md Layer 2.) |
| **Active canvas map (D-2026-06-24-C, in-app, Phase 2a)** | Beyond the selected nodes, the engine injects a compact `[Canvas: <scope>] N node(s):` map of **every** node on the active canvas (`kind "label" (id)`, with selected ones marked `[selected]`), read engine-side, so the agent sees the **whole current screen** — not just the selection. Labels only (bodies ride in the selection-content block; the agent fetches the rest via its MCP tools). Capped at 60 nodes. Replaces the wire-label selection header when the canvas reads cleanly; falls back to it otherwise. `project` scope / unresolvable canvas inject nothing. |
| **Cross-canvas registry (D-2026-06-24-D, in-app, Phase 2b)** | On scopes whose design work **references** actors / entities — `feature` (steps carry `actor_ref` + `ref_entity_ids`) and `services` (`ref_actor_ids`) — the engine lists the **existing** actors (`"label" (id)`) and entities (`"label" (id): summary`) from their canvases, so the agent references them instead of minting a duplicate (글 / 게시물 / 포스트 as three entities). Each list capped at 40. Other scopes skip it to spare the context window. The D-2026-06-17-L "entity registry" envelope piece. |
| **Selected-node content injection (D-2026-06-24-B, in-app, Lever 1a)** | Beyond the selection *header* (kind / label / id), the engine reads the selected nodes' **actual typed text** and injects it as a `[Selected node details]` block, so "polish this mission" reaches the agent **with the mission text** instead of inventing one (the core context-starvation fix, `docs/idea/chat/00-problem.md`). The content is read **engine-side** via `read_canvas` (`mashbill/chat_selection.py`) — never sent over the wire by the viewer — keyed off the single project under the data root (one-project-per-root, D-2026-06-21-AB). The renderer is **generic**: it dumps every non-empty text field that isn't structural / visual / server-managed, so a new kind needs no per-kind branch. Every failure mode (no project, missing / invalid canvas, selection id absent) yields nothing rather than a wrong or fabricated detail. Assembly: `context header → selected-node details → user message`. `project` scope and an empty selection inject nothing; capped at the same 20 nodes. In-app only; the MCP path's external agent reads canvases itself, so it needs no injection. |
| **Coach writes a confirmed value into the selected node (D-2026-06-26-D, `update_node`)** | The in-app coach **saves** a value the user confirms into the node they mean (the selected node, or — for a kind that is unique on the canvas like the mission / identity — one it finds itself, no selection required; `D-2026-06-27-A`) — closing the gap where it could only propose and tell the user to paste (Novel's core promise is that the AI fills the canvas). Three parts. (1) MCP tool `update_node(project_path, project_id, canvas_kind, node_id, fields, service_id?)` patches **one node's content** (`label` + the kind's typed text) via read → merge writable fields → re-validate against the kind → atomic `write_canvas`; visual / structural / server fields are rejected (returned as `rejected_fields`), every other node + edge is left untouched (clobber-safe), and an absent node id (including the synthetic project anchor, which is not a node) errors. (2) The per-turn context injects a `[Write target]` block (the `project_path` / `project_id` / `canvas_kind` / `service_id` the agent passes — the in-app agent's MCP server is stateless and never otherwise learns the open project) plus each selected node's **writable field names** (so a *blank* node still tells the coach what to fill — the "mission won't fill" case). (3) The canvas-scope system prompt's `WRITE_PLAYBOOK` tells the coach to call `update_node` on an **explicit** confirmation, then confirm in one line what it saved; never before the yes; ask when nothing / several nodes are selected. This is the **completion** of build-through-discussion (`D-2026-06-16-P`), not silent finalisation — never write *without* a confirmation. **Known limit:** a coach write reaches the viewer via the file watcher, which treats it as an external change and clears the undo stack (recover via git / re-edit). In-app context-injection half; the tool is on the shared MCP surface so the external agent gets it too. Pinned by `tests/test_update_node.py`, `tests/test_chat_selection_detail.py`, `tests/test_chat_system_prompt.py`. |
| **Coach ADDS a new node (D-2026-06-27-B, `create_node`)** | The in-app coach **adds** a node the user confirms is genuinely new — closing the other half of "the AI fills the canvas" (filling an existing node was `D-2026-06-26-D`; before this, lacking an add tool, the coach rewrote the *whole* canvas via `update_canvas` with an LLM-guessed position — the clobber-unsafe path `D-2026-06-26-D` rejected). MCP tool `create_node(project_path, project_id, canvas_kind, kind, fields?, service_id?)` is a clobber-safe single-node **append** mirroring `update_node`: validate `kind` is creatable on the canvas → mint the id + auto-position server-side (never LLM-supplied) → apply only the kind's writable content fields (`writable_node_fields` SSOT, the rest returned as `rejected_fields`) → `read_canvas` → append the one node → re-validate the whole `CanvasDoc` → atomic `write_canvas`, leaving every other node + edge untouched. Returns `{node, rejected_fields}`. It is the **single SSOT for node creation**: `masters.create_master` (the reference pick-or-create, `D-2026-06-19-C`) is now a thin wrapper that resolves the master's home canvas and calls `create_node`. **Creatable kinds:** foundation → mission / core_value / identity; actors → actor; services → category / service / feature; entities → entity; feature → step / decision / rule / note / actor_ref. **Rejected:** `project` (synthetic anchor, not a node) on every canvas; `feature` on the feature canvas (root must pre-exist). The tool adds a **bare** node only — containment / edges are drawn separately (directed-edge-only since v0.26.0), never auto-wired silently. A cross-canvas master uses the reference flow, not `create_node`. The `WRITE_PLAYBOOK` create branch gates it on an **explicit** confirmation: read / search first → propose ("새로 ~를 만들까요?") → only on the user's yes call `create_node` → confirm in one line; never create before the yes (`D-2026-06-16-P`). **Known limits (inherited):** last-write-wins (same as `update_node`) and undo-stack clear (same as `D-2026-06-26-D`). Pinned by `tests/test_create_node.py`, `tests/test_chat_system_prompt.py`. |
| **Conversation scope (D-2026-06-13-H; Layer 1 per-instance D-2026-06-15-B)** | Chat threads are partitioned per canvas scope — `foundation` / `actors` / `services` / `service_detail` — plus one shared `project` scope. `service_detail` is **per-service-instance**: the wire scope carries the service id as `service_detail:<service_id>`, so each service-detail canvas keys its own thread (the scope set equals `CanvasKey ∪ {project}`). The dock follows the active canvas. The scope switcher has **exactly two tabs** — `[selected canvas | project]` (D-2026-06-15-H, reverting the D-2026-06-15-E full picker): the "canvas" tab follows the active canvas tab (including a service-detail tab), the "project" tab pins the shared cross-canvas thread. A service-detail canvas tab is labelled with the **service's name** (falling back to "Service detail" when the name isn't available), not the raw `service_detail:<id>`. The engine keys sessions on `(plot_root, provider, scope)` where `plot_root` is resolved from the path the viewer sends — the **active project's** path (D-2026-06-16-G), so the chat is scoped to **(project × canvas)**: switching projects in the same workspace switches the chat's threads + provider/model too (each project has its own `.noory/novel`). The viewer sends the active scope on `POST /api/chat/send` and demultiplexes `chat_stream_event` payloads on their `scope`. `Reset` wipes only the active scope's session; other scopes survive. A send / reset that omits `scope` defaults to `project`; an unknown scope — or bare `service_detail` with no id — is a 400. A deleted service's thread is left orphaned (in-memory, cleared on engine restart). The `ChatScope` base member set is parity-guarded (Python ↔ TS, including the parametric `feature:<id>` and `service:<id>` suffixes) by `tests/test_chat_scope_parity.py`. (The per-instance wire scope is `feature:<id>` since the `service_detail`→`feature` rename, D-2026-06-20-J.) |
| **Per-service thread (D-2026-06-26-A)** | A service is the *value-level big picture* ("what value, for whom"); a feature is its *flow design* ("how it actually runs") — different conversation topics. Alongside the per-feature `feature:<id>` thread, **selecting a single service on the Services canvas keys a per-service thread `service:<id>`** (value/Planning coaching — `build_framing_preamble` maps base `service` to the `services` framing — parallel to `feature:<id>`'s flow/Execution coaching). Drilling into a feature keys `feature:<id>`; deselecting returns to the canvas `services` thread. Bare `service` with no id is a 400, same as bare `feature`. The selected service node's typed text already injects via selected-node content (D-2026-06-24-B), so the per-service envelope needs no special path. |
| **Conversation persistence (D-2026-06-26-B)** | Chat conversations persist to disk as **one append-only log per scope** at `.noory/novel/chat/<scope>.json` (parametric scopes sanitise `:`→`__`, e.g. `service:abc`→`service__abc.json`). The **engine is the sole writer**, appending the user message when a turn is sent and the assistant message on `turn_complete`, via the atomic `storage._write_json`. So a project's conversations travel with the project, restore on another machine, and **survive an engine restart** (the failure that motivated this — in-memory chat died on app restart). The dock lists saved conversations per canvas/service (`GET /api/chat/conversations`) and reopens one (`GET /api/chat/conversations/{scope}` → hydrate the scope's message bucket). `title` = first user message (≤60 chars), set once. **Scope:** one conversation per scope (mirrors the one-session-per-scope registry). **Out of scope (v1):** multiple conversations per scope, CLI `--session-id` revival (reopening restores the **transcript for reading**, not the live CLI session — continuing starts a fresh turn), orphan pruning on service deletion, search/rename/delete-from-UI. |
| **Per-canvas framing + hallucination guard (D-2026-06-15-C → system prompt D-2026-06-24-A, in-app)** | Each turn delivers a canvas-appropriate **system framing** plus a constant **hallucination guard** as an **authoritative system prompt**, not glued into the user message where the model reads it as mere conversation (Lever 2, `docs/idea/chat/01-levers.md`). The guard ("ground every statement in the given context, read the canvas with your mashbill MCP tools when you don't know, ask otherwise — never invent project details; resolve 'this' to the selected node") is the load-bearing anti-starvation instruction; it ships on **every** scope, including `project`. The base scope maps to its VISION phase, and the framing is the canvas's **full coaching playbook** (D-2026-06-24-E): Foundation → Discovery (the mission / core-value / identity interview), Actors / Services → Planning (role-family elicitation / the 5-slot JTBD interview + promotion test), Feature → Execution (actor-anchored happy-path-first flow + altitude guard). A shared **coach tone** (gentle, one-question-at-a-time, follow-the-user's-words; + the pick-or-create reference principle) prefixes every canvas framing. Content SSOT = `docs/concepts/ai-collaboration.md` §0–§2 (the canonical question script; the English framings instruct the agent to run that interview in the user's language). The `project` scope gets the guard alone (no tone, no framing). Delivery is per-CLI: **claude** uses the native `--append-system-prompt` flag; **codex** (`exec`, no system-prompt flag) prepends it to the message. The engine assembles the user message as **canvas map → cross-canvas registry → selected-node details → user text** (framing now lives in the system prompt, not the message). `build_system_prompt` is code constants (`HALLUCINATION_GUARD` + `COACH_TONE` + `SCOPE_FRAMING`), not `.noory/`-editable, SSOT in `mashbill/chat_context.py`, and is **shared with the MCP path** (D-2026-06-24-F). (CHAT_ARCH.md Layer 3.) |
| **Name search (D-2026-06-24-I, both paths)** | The MCP tool `search_project_nodes(project_path, project_id, query)` is the **name** leg of the context entry-point chain (selection → map → **name** → semantic; D-2026-06-20-P §1.2): a case-insensitive label scan over **every** canvas, returning ≤20 `{id, kind, label, canvas}` hits, so the agent can resolve a node it knows by name but that isn't on the active canvas. A plain label index, **not** vector search (the data is already a graph; vector is a later option behind the same seam). Both the in-app `-p` agent and the external agent reach it via `mcp__mashbill__*`; the hallucination guard names it. |
| **MCP-path context (D-2026-06-15-D, primary path)** | The external agent (the user's own CLI connected via the `mashbill` sidecar) reads the viewer's live context through a read-only MCP tool `get_viewer_context(project_path)` → `{active_canvas, selection, framing, updated_at, stale, has_viewer}`. It is fed by a viewer→engine push: the viewer `POST`s `/api/viewer/context` `{project_path, scope, selection}` (debounced, from one `App` effect over the lifted `[activeScope, selection]`, plus a ~30s heartbeat). Because the bundled MCP server is a **separate `--mcp-stdio` process** from the HTTP sidecar (D-2026-06-14-A), the two share state via a **filesystem rendezvous file** — a sha256(`plot_root`)-keyed JSON under `tempfile.gettempdir()` (OS temp, ephemeral, atomic write); the HTTP process writes, the MCP process reads. Project-keyed by resolved `plot_root`. `framing` is the **same full coaching system prompt the in-app path uses** — guard + coach tone + the canvas playbook via `build_system_prompt(scope)` (D-2026-06-24-F), so the primary path is never context-poorer than in-app (D-2026-06-19-F). **Liveness:** same-machine shared clock — the HTTP process stamps `updated_at`, the MCP tool compares to its own `time.time()`; older than the 90s TTL ⇒ `stale`. The 30s viewer heartbeat keeps an idle-but-open viewer fresh, so `stale` / no file ⇒ `has_viewer: false`, `active_canvas: null`, `selection: []` — the agent never treats stale context as current. **Multi-viewer:** last-writer-wins (later atomic write overwrites), disambiguated by `updated_at`. This is the CHAT_ARCH.md "Scope honesty" follow-up giving the primary path the same context the in-app chat got in Layers 1–3. |
| **Model selection (D-2026-06-16-C → live catalogue D-2026-06-22-B)** | Per-workspace, per-provider model override, persisted in the `chat-provider` JSON alongside the provider (`{"provider", "model"}`). The selector is a dropdown populated from each CLI's **own live catalogue** — fetched from `GET /api/chat/models?provider=<name>` — plus a **Custom…** free-text fallback (reverses the D-2026-06-16-C hardcoded list, which went stale immediately). Sources: **codex** → `~/.codex/models_cache.json` (`visibility == "list"` + `supported_in_api`); **gemini** → `agy models` (labels carry effort, e.g. "Gemini 3.5 Flash (Medium)", passed verbatim as `--model`); **claude** → its static documented aliases (`fable` / `opus` / `sonnet`). Each option's `id` is the `--model` value, `label` is shown; the current model stays selectable even if absent; **fail-soft** — a missing / unreadable source yields an empty list, leaving default + Custom…. Empty = the CLI's own configured default. Changing the provider clears the model and refetches the catalogue. The engine applies the value via `ChatProvider.set_model(model)` before each turn. Pinned by `tests/test_chat_model.py`, `tests/test_chat_models.py`, `tests/test_endpoints_chat.py` + `viewer/tests/chat-model-selection.test.tsx`, `viewer/tests/chat-model-catalogue.test.tsx`. |
| **MCP wiring** | Novel's MCP server is registered with each CLI separately (Track 2.5: `~/.claude.json` / `~/.codex/config.toml` / `~/.gemini/settings.json`). The canvas ↔ chat feedback loop runs through MCP. **Registered command shape (D-2026-06-14-A):** in a dev checkout, `uv run --directory <src> python -m mashbill`; in the bundled `.app` (PyInstaller-frozen), `<bundled binary> --mcp-stdio` (`command = sys.executable`) — the dev `uv run` command points at the ephemeral `_MEIxxxx` extraction dir and times out, so the frozen path registers the stable bundled binary in its stdio-MCP mode instead. **In-app chat does NOT use this global registration (D-2026-06-26-E):** the engine spawns the coach with `--mcp-config` naming the *running build's own* Novel stdio server (same frozen/dev command shape) plus `--strict-mcp-config`, so the coach always carries this build's Novel tools — never a drift-prone global pointer at a deleted/older build — and sees no other MCP servers. The global registration remains for the user's *external* agent (the MCP-first primary path). |
| **UI (reshaped v0.85.0, D-2026-06-16-D)** | The chat dock is the **leftmost of three horizontally-resizable panels** — chat \| project sidebar \| canvas (D-2026-06-14-E, `WorkspacePanels` + `react-resizable-panels`). Widths persist (localStorage `novel:workspaceLayout`); chat + sidebar are collapsible; the canvas keeps a hard min width. The dock reads like a modern chat app, top→bottom: a **top conversation bar** with the **model selector** as the prominent control on the left (a dropdown of per-CLI suggestions + "Custom…" free-text fallback; D-2026-06-16-C/D) and a **compact provider chip** on the right (D-2026-06-14-D — click to reveal the full `ChatProvidersPanel`; carries the connection indicator `data-connected` 1/0 + agent name, D-2026-06-15-F; when no agent is connected the chip fills the bar as the call-to-connect and the model selector is hidden); then the 2-tab scope switcher; then the **message log** (`role="log"`) of **left/right-aligned bubbles** (assistant left on `surface-muted`, user right on `surface-inverse`, error on `warn`) with the streaming activity indicator + caret (D-2026-06-16-B); then a single **rounded composer** (textarea + integrated circular send button `↑`). claude-code selected → a billing-warning banner shows above the log (D-2026-06-14-B). |
| **No CLI installed** | Panel surfaces per-CLI install + login guidance instead of an input box (`brew install claude` / `npm i -g @openai/codex` / etc.). |
| **Streaming feedback (D-2026-06-16-B)** | While a turn streams, the dock shows a live **activity indicator** (three bouncing dots + an elapsed-seconds counter, `role="status"`) so the turn never looks frozen — including the gap between send and the first token (CLI spawning / thinking), where the assistant bubble has no text yet. Once text arrives, a blinking caret trails the streaming text. Shown in the status bar (whole streaming duration) and inside an empty assistant bubble. `ChatActivityIndicator` + `useElapsedSeconds`, pinned by `viewer/tests/chat-activity-indicator.test.tsx`. |

See DECISIONS.md
[D-2026-06-11-E](./DECISIONS.md#d-2026-06-11-e--r7-in-app-chat--native-panel-with-external-cli-subprocess)
for the design discussion (option A vs B vs C, Pencil-model
invariants, multi-provider abstraction, sequencing).

---

# Engine auth (v0.65.0, D-2026-06-12-F)

Novel's engine exposes one auth seam — env-gated, Bearer for HTTP,
``?auth=`` query parameter for WebSocket. TABLET_ARCH §"지금 만들 것"
pinned this as a build-now item so a future bundled / remote / tablet
delivery doesn't break every consumer with a wire-shape change.

| Aspect | Behaviour |
|---|---|
| **Trigger** | The env var ``MASHBILL_AUTH_TOKEN``. Unset → enforcement off (every request passes through; today's dev parity). Set to a non-empty string → enforcement on. |
| **HTTP** | ``Authorization: Bearer <token>`` required on every ``/api/*`` request when enforcement is on. Missing → 401 ``{"error": "auth token required"}``. Wrong → 401 ``{"error": "invalid auth token"}``. Comparison is constant-time (``hmac.compare_digest``). |
| **WebSocket** | The handshake reads ``?auth=<token>`` (Starlette middleware can't ride ``WebSocketRoute``; the param is the only path). Missing or wrong → close 1008 with reason ``"auth token required"``. |
| **Always-open paths** | ``/api/health`` only, so the Tauri shell can probe the engine before the invoke command is registered. Every other endpoint is post-boot and must respect enforcement. |
| **Token shape** | 32 bytes of OS RNG → 64 lowercase hex chars (canonical webhook-secret shape). Bundled Tauri builds mint one per launch; the shell exports it into the sidecar's env and serves it to the viewer via the ``mashbill_auth_token`` invoke command. |
| **Dev parity** | Unset env → middleware NOT mounted at all (zero latency cost). The dev workflow (``uv run mashbill-http`` + browser at ``:5193``) stays byte-identical to v0.64.x. |

See DECISIONS.md
[D-2026-06-12-F](./DECISIONS.md#d-2026-06-12-f--engine-auth-seam-track-35-tablet_arch-지금-만들-것)
for the design discussion (env-gated vs always-on, per-launch token vs
stored secret, why constant-time compare on loopback, why
``/api/health`` is the only open endpoint).

---

# Appearance — light / dark theme (v0.47.0, D-2026-06-07-C)

The viewer ships **light and dark** themes. Colour is expressed through
**semantic CSS-variable tokens** (e.g. `surface`, `text`, `text-muted`,
`border-subtle`, `accent`) defined once in `styles.css`: `:root` holds the
light values, `.dark` holds the dark values. Components never hardcode a raw
palette colour (`bg-white`, `text-slate-700`, …); they use the semantic
token classes, so a theme switch is a single CSS-variable swap. A structural
guard fails the build if a component reintroduces a raw neutral colour class.

- **Default = OS preference.** On first load, with no stored choice, the
  theme follows `prefers-color-scheme` and tracks live OS changes.
- **Manual override, persisted.** A theme toggle next to the language toggle
  (sidebar footer + ServiceDetail stencil panel) sets an explicit choice
  stored in `localStorage` (`novel:theme` = `light` | `dark` | `system`),
  mirroring the `novel:lang` pattern. `system` reverts to following the OS.
- **`.dark` class on `<html>`.** Tailwind runs in `darkMode: "class"`; the
  resolved theme toggles the `dark` class on `document.documentElement`.
- **Light appearance is unchanged.** Each token's light value equals the
  pre-theme palette colour, so the existing light UI is preserved 1:1; only
  dark values are new.
- **Node cards keep dark-on-light text in both themes.** A node card's
  background is the user's chosen colour (`data.color`, usually a pastel), not
  a theme surface — so flipping its text to a light foreground in dark mode
  would make it vanish on the (still light) card. The card div (`node-card`
  class) re-locks the on-card foreground vars + inline-code / count-chip
  background vars to their light values, so card text reads dark-on-light
  identically in light and dark. Chrome *outside* the card (handles, the ⚠
  markdown-warning badge, selection ring) still follows the theme.
  (D-2026-06-09-A)
- **No third-party watermark on the canvas.** The React Flow attribution badge
  (bottom-right "React Flow" link) is hidden via `proOptions={{ hideAttribution:
  true }}` on the canvas. `reactflow` is MIT-licensed, so removing the
  attribution (which xyflow recommends but does not require) is permitted; Novel
  ships as a commercial desktop app. (D-2026-06-09-B)

---

# Foundation

## What Foundation is

The canvas that answers **"who are we, and why do we exist?"** for the
project. It carries the four kinds defined in
[`CONCEPTS.md`](./CONCEPTS.md): `project`, `mission`, `core_value`,
`identity`. (See CONCEPTS.md for kind definitions; this spec covers only
behaviour, not data model.)

---

## Stencil concept info (ⓘ) (v0.42.0, D-2026-06-06-A)

The Foundation stencil's three section headers (Mission / Core values /
Identity) each carry an **always-visible ⓘ icon** next to the title.
Clicking it opens a small **popover** with that concept's definition, so a
user who does not yet know what mission / core value / identity mean can
learn it in place. Concept SSOT = [`concepts/kinds.md`](../../../docs/concepts/kinds.md)
(absorbed the old FOUNDATION_CONCEPT); the popover is a short surface of it.

| Section | Popover text (full text in `stencil.info.*`) |
|---|---|
| Mission | 이 프로젝트가 무엇을 위해 존재하는지 한 문장으로 표현하세요. |
| Core values | 의사결정의 기준 가치예요. |
| Identity | 정체성을 나타내는 방식이에요. |

Copy is **plain + concise** (no metaphors like 뿌리/노력/지향 — D-2026-06-06-A
copy refinement, user-worded); a newcomer should understand each on first read.

- ⓘ is **always visible** (not hover-only) → the affordance is discoverable.
- Popover opens on **click** (works on touch, unlike hover).
- Text is i18n'd (`stencil.info.*`), English primary + Korean.
- **The old inline usage-notes are removed** (D-2026-06-06-B): the
  Foundation sections no longer show "add as many as you need" /
  "one per aspect — …". The ⓘ popover carries the meaning; the inline
  note was redundant clutter. (`stencil.note.addAsManyAsYouNeed` and
  `stencil.note.identityOnePerAspect` deleted.)
- Implementation: `viewer/src/canvases/stencil/SectionInfo.tsx` (the ⓘ +
  popover); `Section` gains an optional `info` prop. Foundation-only for
  now (other canvases' sections pass no `info`).

---

## Anchor-radial initial placement (D-2026-05-12-N)

Per the canonical Novel spec:
> "프로젝트 노드 놓고(앵커) 그 주변에 미션, 코어밸류, 아이덴티티
> 붙이면 되요. 뭐가 먼저고 말고는 없습니다."

When the user creates a Mission / CoreValue / Identity node on the
Foundation canvas, the new node's initial position is set to a slot
on a circle of radius 320 px around the anchor centre (canvas
``(0, 0)``). Slots are 120° apart for visual balance — Mission at
9 o'clock, CoreValue at 1 o'clock, Identity at 5 o'clock. **No
narrative ordering** is implied; the radial arrangement signals
"each of the three is an aspect of the same project."

The slot is **a positional hint, not a constraint**:
- After creation, the user can drag the node anywhere.
- Subsequent same-kind nodes get a +30° offset to avoid overlap.
- No edges are emitted on creation — Foundation stays user-draw-only
  by its own spec (a per-canvas choice, **not** the old global ban;
  D-2026-06-17-J removed the blanket "all edges are user-drawn" rule —
  edges are now governed by their definition, not authorship).
- Other canvases (Actors / Services / ServiceDetail) unaffected.

Implementation: ``viewer/src/canvases/sketch/anchorRadialLayout.ts``
(pure helper) consumed by ``useNodeCreation`` 's ``addNodeAt``.

---

## Anchor (the centre node)

The yellow circle in the middle of the canvas, labelled with the
project name (e.g. "Banas v0.13").

| Aspect | Behaviour |
|---|---|
| **Origin** | Auto-seeded; SSOT lives in `ProjectDoc.anchors`, not in `canvas.json`. Rendered as a synthetic node. |
| **Injection scope** | Injected on every primary canvas kind — `foundation`, `actors`, `services`. Service-Detail (modal) does **not** carry an anchor. (See [CONCEPTS.md §project](./CONCEPTS.md#project--the-project-anchor).) |
| **Mutation routing** | Drag / resize updates flow through `onAnchorChange` (a separate prop), **never** through `onDocChange`. Canvas-level mutation handlers must branch on `id === PROJECT_ANCHOR_ID` and dispatch to the anchor path before falling through to the regular-node path. |
| **Count** | Exactly 1. |
| **Delete** | Not allowed (no UI affordance). The synthetic id is silently ignored if it ever surfaces in a delete event. |
| **Label** | Mirrors `ProjectDoc.name`. |
| **Drag** | Allowed. Persists via `PATCH /api/projects/:id/anchor`. |
| **Resize** | Allowed. Persists via the same PATCH. |
| **Handles (4 sides)** | Visible. User may draw edges from / to the anchor like any other node. |
| **Inspector on click** | **TBD — open question, see below.** |
| **Visual differentiation** | 2 px slate-600 **border** so users tell it apart from same-colour Service circles on other canvases. (Border, not outline — outline paints outside the hit-box and caused cursor flicker on slow hover; see [D-2026-05-08-G](./DECISIONS.md). Regular nodes use a 1 px slate-300 border, selected nodes 2 px indigo-500.) |
| **Sizing** | Auto-fits content as a SQUARE (round shapes use `aspect-square`, with the card itself as a flex column so vertical centering works without a percentage-height child). [D-2026-06-11-A](./DECISIONS.md#d-2026-06-11-a--round-cards-use-flex-column-not-h-full-on-the-inner-webkit-aspect-ratio-fix) corrected the 96×132 anchor produced by the Tauri WKWebView under the prior `h-full` inner. |

### Open questions (not yet decided)

- **Anchor click → Inspector?** Currently no. CONCEPTS.md implies the
  label edit goes through `ProjectDoc.name`, but there's no spec for
  *where* that edit UI lives. Decision needed before next anchor-edit
  work.

---

## Rendering order

Parents must be emitted to React Flow **before** their children in
the node array. React Flow's parent / nesting machinery uses array
order to resolve `parentNode` references during the first paint. Any
future node-transform refactor must preserve this property — sort by
`parent_id == null` first, then children.

## Edges

| Aspect | Behaviour |
|---|---|
| **Source of edges** | An edge is governed by its **definition** (its `relation` + payload), **not by who draws it** — the former "all edges are user-drawn / no auto-emit" ban is removed (**D-2026-06-17-J**). Edges may be **user-drawn OR AI-proposed/drawn**; the AI maintains relationships on **AI-maintained canvases** (e.g. Entities, D-2026-06-17-I), and the user can always edit / delete any edge. A canvas may still be user-draw-only by its own spec (Foundation / Actors / Services currently are — a per-canvas choice, not a global law). **Never emit a *meaningless* or *silently-uneditable* line** — that specific harm (v0.13.2) stays banned. (Migration: read-side v0.26.0 auto-creates directed edges from legacy ``parent_id`` — one-time per canvas, D-2026-05-25-A.) |
| **Persistence** | Stored in `foundation/canvas.json` `edges[]`. |
| **Edit** | Double-click → edge modal (label, value-form, dashed). Right-click → context menu (toggle direction, **flip direction**, dashed, label, delete). |
| **Flip direction (v0.29.2, D-2026-05-31-A)** | Context-menu **"Flip direction (swap source ↔ target)"** swaps the edge's ``source``/``target`` so the arrowhead points the other way. Handles are nulled (BaseNode handles are typed by side — ``t``/``l`` target-only, ``r``/``b`` source-only — so the old ids can't carry over); RF re-routes through each node's default valid handle. ``directed`` is preserved. Orientation only; lands via ``onDocChange`` (Cmd+Z undoes it). Available on every canvas. |
| **Rendering (v0.30.3, D-2026-05-31-F)** | Non-self-loop edges are **floating** — they attach to the point on each node's border facing the other node (computed from node geometry, handles ignored), so a connection reads the same from any side. Self-loops keep the curved `SelfLoopEdge`. Injection edges keep the violet animated dash (period `5 5`, seamless). |
| **Delete** | Select + Delete/Backspace, or via context menu. |
| **Style** | Solid by default. Dashed only when the user sets `style: "dashed"` in the edge modal. |
| **Direction (v0.26.0)** | Each edge carries a ``directed: bool`` flag. **Default for new edges = `true`**. Directed edges render an arrowhead at the target end; undirected edges render plain. Drag direction defines the orientation: the handle the user pressed becomes ``source`` (= ``from``), the handle released on becomes ``target`` (= ``to``). |
| **Relation (v0.30.0, D-2026-05-31-C)** | Each edge carries a stored ``relation``: ``flow`` (sequence / hierarchy — source = parent), ``injection`` (essence flows into the target — excluded from fold), ``inheritance`` (actors-canvas tree — target = superclass = parent). The **one SSOT** read by both viewer (fold / layout / styling) and server (`propagation.py` publish MINOR-bump). Default-assigned by `classifyEdge(canvas, source-kind)` on creation / migration (mirrored TS + Python); authoritative once set; re-assigned on flip. **Invariant:** every directed edge on the **actors canvas is `inheritance`** (single edge type); an essence source (`mission`/`core_value`/`identity` + their `*_ref`, not `actor_ref`) → `injection`; else `flow`. |
| **Anchor-relative direction (D-2026-06-14-C)** | Each canvas wrapper supplies an ``anchorArrowMode``: **Foundation/Actors `"converge"`** (arrowhead points toward the anchor-ward endpoint — elements compose into / participate in the service), **Services `"diverge"`** (arrowhead points AWAY from the anchor, so the `anchor → category → service` flow always reads outward — per D-2026-06-01-D, now render-enforced regardless of stored edge direction), **ServiceDetail/default `"none"`** (drawn direction kept). Applied both at render (`edgeTransform`) and creation normalisation (`useFlowHandlers`); the doc edge stays the SSOT, only the rendered orientation is forced. |
| **Selection (D-2026-06-14-C)** | Every edge carries a widened `interactionWidth` (28; RF default 20) so thin edges are easy to click. A selected edge is highlighted via styles.css (`.react-flow__edge.selected .react-flow__edge-path` → accent stroke + 3 px, `!important` to beat the inline value-flow stroke). |

### Hierarchy from directed edges (v0.26.0, D-2026-05-25-A)

Parent-child / containment relationships are derived **exclusively
from directed edges** (``edge.source`` = parent, ``edge.target`` =
child, when ``directed === true``). The legacy ``parent_id`` field on
nodes has been removed.

> **v0.30.1 (D-2026-05-31-D) — fold reads the edge ``relation``.**
> The parent/child for fold is resolved by ``flow/foldHierarchy.ts``
> per the stored ``relation`` (not raw ``directed``): ``flow`` →
> source=parent; ``inheritance`` → **target=parent (inverted)** so
> collapsing a superclass hides its subclasses; ``injection`` →
> excluded (an essence overlay doesn't contain its target). The same
> rule feeds the server publish-propagation walk (Phase 2c).

- Fold (▾ / ▸) button surfaces on a node iff it has at least one
  *outgoing* directed edge to another node (i.e. someone is its child).
- Drill / nested-drag / Inspector "child count" all derive children
  from outgoing directed edges.
- Multi-parent (more than one incoming directed edge) is now
  expressible; the ancestor walk picks the lexicographically smallest
  source id for deterministic single-parent traversal.
- Undirected edges (``directed === false``) are purely visual
  relationships and do **not** participate in hierarchy / fold.

> **Edges are defined by meaning, not authorship (D-2026-06-17-J).** The
> former "no auto-edges / user must own every line" rule (D-2026-05-04-A)
> is removed: its real target was *silent, uneditable, meaningless* edges
> (the v0.13.2 anchor→child auto-edges), not AI help. An edge is valid when
> its **definition** holds (its `relation` + payload) **and** the user can
> edit / delete it; AI-maintained canvases (Entities) may carry AI-proposed
> edges. The v0.26.0 read-side migration remains a one-shot ``parent_id`` →
> directed-edge transform.

### Self-loops (source === target)

User-drawn edges where ``source === target`` render as a curved arc
bulging away from the node (via ``SelfLoopEdge`` custom edge type,
``viewer/src/canvases/edges/SelfLoopEdge.tsx``). The arc is
click-able for select / delete / context-menu like any other edge.

Self-loops are permitted as a general edge behaviour (a node may point
at itself — e.g. a feedback loop). *(The former justification cited the
"서비스 간 연결 = 유저저니" concept, which was **abolished by
D-2026-06-17-C**; the self-loop behaviour survives independently.)*

Permitted on every canvas that accepts user-drawn edges. The
collapsed-ancestor filter in ``edgeTransform.ts`` is preserved —
edges whose endpoints fold into the same collapsed parent (but
were *not* originally a self-loop) still drop. Decision
**D-2026-05-12-M**.

---

## Auto-layout

**Re-introduced v0.16.36 per [D-2026-05-13-L](./DECISIONS.md);
generalised v0.25.0 per [D-2026-05-24-B](./DECISIONS.md) into
per-wrapper algorithm choice.** Novel's `SketchCanvas` default
behaviour is *no auto-layout button*. Each wrapper opts in by setting
`layoutAlgo`:

| Wrapper | `layoutAlgo` | Algorithm | Since |
|---|---|---|---|
| `FoundationCanvas` | `"tree"` | Angle-preserving depth rings (BFS from anchor) | v0.16.36; **angle-preserve since v0.34.8 (D-2026-05-31-V)** |
| `ActorsCanvas` | `"tree"` | Angle-preserving depth rings (same as Foundation) | v0.24.5; **angle-preserve since v0.34.8** |
| `ServicesCanvas` | `"tree"` | Actor-anchored when a subject edge exists; else angle-preserving depth rings | v0.27.0 (D-2026-05-26-A switches from `"radial"`); **angle-preserve fallback since v0.34.8** |
| `ServiceDetailCanvas` | `"tree"` | Actor-anchored when a subject edge exists; else angle-preserving depth rings (hidden root-service as hub) | v0.27.0; **angle-preserve fallback since v0.34.8** |

> **SUPERSEDED by v0.40.0 (D-2026-06-01-F) — kept for history.**
> v0.34.8 (D-2026-05-31-V): the anchor path ran `computeRadialLayout`
> with `angleMode: "preserve"` (depth rings). v0.39.0 (D-2026-06-01-C)
> swapped that for the Reingold-Tilford `computeAutoLayout`. Both are now
> replaced by `computeMindmapLayout` (see the v0.40.0 note above).
> `computeRadialLayout` survives only behind the `layoutAlgo="radial"`
> button; floating edges were removed in v0.40.0 (D-2026-06-01-E).

Isolation regression test:
`viewer/tests/auto-layout-isolation.test.tsx`.

### Behaviour (any canvas that opts in)

- The `<Controls>` panel (bottom-left of the canvas) renders an extra
  `⊞` button labelled "Auto-layout".
- Clicking it runs the wrapper's chosen algorithm.
- The new positions are dispatched via the regular `onDocChange`
  pipeline, so **`Cmd+Z` undoes the auto-layout exactly like any
  manual move**. The user-consent guarantee comes from the explicit
  button click + the undo stack — no separate preview state.
- Auto-layout touches **positions only**. `kind`, `label`,
  `parent_id`, typed-text fields, edges — all byte-identical
  before vs after. True for both algorithms.

### Angle-preserving depth rings (`layoutAlgo="tree"` anchor path, v0.34.8, D-2026-05-31-V)

Implemented in
`viewer/src/canvases/sketch/radialLayout.ts`
via `computeRadialLayout({ …, angleMode: "preserve" })`, dispatched by
`useAutoLayout`:

- Hub is the project anchor when the canvas injects one
  (Foundation / Actors / Services); for `ServiceDetailCanvas`
  (which injects no anchor) `useAutoLayout`'s `pickAnchor` falls
  back to the hidden root-service node
  (`kind === "service" && is_root === true`).
- The hub stays fixed in place.
- BFS from the hub assigns each reachable node a **depth ring**
  (hub = 0, neighbours = 1, …). A node's distance from the hub is
  its ring radius — so a deeper node always sits farther out than a
  shallower one (no edge crossing).
- Each node keeps its **current angle** from the hub centre
  (`atan2(cy − hubCy, cx − hubCx)`) — the side the user placed it on
  is preserved (no swap). A node exactly on the hub centre falls back
  to −π/2 (top).
- Orphans (unreachable from hub) drop into a grid below the rings.
- Deterministic — same input → same output.

**Handle-based directional tree — retained fallback (`autoLayout.ts`).**
Pre-v0.34.8 this was the live `"tree"` algorithm: BFS spanning tree
placing each child T/R/B/L per the parent-side edge handle, with
Reingold-Tilford sibling spacing. It is kept (and unit-tested) but no
longer wired into production; it is the option-(B) path if floating
edges are reverted to handle-based rendering.

### Actor-anchored layout (v0.27.16, D-2026-05-28-J)

When the doc has a user-side `actor_ref` wired to an entry step (the
"subject edge" — actor → entry, per D-2026-05-28-J), `useAutoLayout`
runs `viewer/src/flow/actorAnchoredLayout.ts` **before** the mindmap
BFS path. Behaviour:

- The actor's `(x, y)` is **preserved** (it's the user-placed
  anchor).
- The direction (`LR` / `RL` / `TB` / `BT`) is inferred from the
  subject edge's `sourceHandle`: `r` → LR, `l` → RL, `b` → TB,
  `t` → BT.
- The step graph (every edge that doesn't originate from the
  anchor) is laid out by dagre with that `rankdir`.
- The whole step graph is translated so the entry sits one rank
  (≈ 220 px centre-to-centre) away from the actor in the chosen
  direction.
- Orphan nodes (no incident step edges — operator-side placeholder
  actors, the hidden root-service, isolated notes) keep their
  existing positions.
- **Injection nodes are anchored, not ranked (v0.28.4, D-2026-05-30-G).**
  A foundation-injection edge (source = `mission_ref` / `value_ref` /
  `identity_ref`, per D-2026-05-30-D) is excluded from the dagre step
  rank; its source node is placed beside its target on the side the
  edge's `targetHandle` dictates (`t` → above, `b` → below, `l` → left,
  `r` → right; ≈ 160 px gap). So 유머 (Humor) drawn into the entry's
  **top** lands *above* the entry, not swept left into the rank.

  This realises the **layout anchor priority** (user 2026-05-30:
  *"사람, 액터가 1등이고 그다음은 스텝 디시전 등이 우선순위"*):
  **① actor** (preserved anchor) → **② step / decision** (dagre rank)
  → **③ injection overlay** (anchored beside its target, placed last).
  Tier 3 never displaces a tier-1 actor or a tier-2 step. This is the
  2-layer essence model at the layout level: the concrete flow (1층 /
  Execution) is ranked; the essence injection (2층 / Retention) is an
  overlay anchored onto it.
- **Injection nodes never overlap (v0.40.1, D-2026-06-03-A).** The
  ≈160 px slot in the `targetHandle` direction can collide with an
  already-placed node — e.g. two injection refs whose targets sit in
  the same dagre column both default to *above* and pile up. When the
  slot intersects any placed node (the actor anchor, a dagre step, or
  an earlier injection ref), the ref is pushed **further out along the
  same handle axis** (in 80 px steps) until it clears. The ref stays on
  its target's column / row — the handle direction is preserved (user
  2026-06-03: *"적어도 노드가 겹치면 안되구요. 핸들에 연결 위치로 노드
  위치를 정해야해요"*) — only its distance grows. Deterministic and
  bounded (≤ 24 hops).
- **Actor→entry gap scales with the entry's extent (v0.40.2,
  D-2026-06-03-B).** The entry step is placed at a centre-to-centre gap
  from the actor of `max(220, actorHalf + entryHalf + 40)` along the
  layout axis (width for LR/RL, height for TB/BT). The fixed 220 px gap
  overlapped the actor when the entry was a wide auto-fit step (surfaced
  in BANAS sim s-onboard: the wide "닉네임 입력" entry overlapped the
  BANA actor circle). Small nodes keep the 220 px default.

Why this came before the mindmap BFS: `ServiceDetail`'s `pickAnchor`
falls back to the hidden root-service, which is disconnected from
every edge. `computeAutoLayout` reaches only the root and dumps every
other node — including the user actor — into the isolated-nodes
grid, sweeping the anchor away from its placed position. User
2026-05-28: *"이렇게 정렬이 되면 사람이 알아보겠어요???"*. The
priority order fixes that for any doc shaped per D-2026-05-28-J.

Static guard: `viewer/tests/actor-anchored-layout.test.ts` (6 cases:
LR preservation, single-step LR alignment, TB direction, branch
+ join graph, orphan preservation, no-actor early return).

#### Direction toggle (v0.28.3, D-2026-05-30-F; single toggle v0.40.3, D-2026-06-03-C)

ServiceDetail's RF `<Controls>` carry **one** direction toggle next to
`⊞`. It **shows the current layout direction** as its icon — **↔** when
horizontal (LR/RL), **↕** when vertical (TB/BT) — and **flips** to the
other axis on click (horizontal → TB, vertical → LR). Clicking sets the
subject edge's handle for the target direction (`setSubjectDirection`:
LR → source `r` / target `l`; TB → `b` / `t`) and re-runs
`actorAnchoredLayout` along it, in one undoable `onDocChange`.

The current direction is read from the subject-edge handle via
`detectAnchorDirection` (the SSOT; `null` → treated as horizontal
default) — so the toggle always reflects state, fixing the v0.28.3 two-
button design that gave no indication of the current direction (user
2026-06-03: *"누를 때마다 왔다 갔다 하는데 정렬 버튼에 어떤 상태를
표시해주면 좋을 것 같은데"*). Direction stays the SSOT in the subject-
edge handle — a later `⊞` re-uses it. Wrapper opt-in via
`showDirectionSwitch` (ServiceDetail only). The button JSX lives in
`viewer/src/canvases/sketch/LayoutControls.tsx`. Static guards:
`viewer/tests/subject-direction.test.ts`,
`viewer/tests/layout-controls.test.tsx`.

#### Auto-layout (⊞) is one action button; mode lives in the tooltip text (v0.40.5, D-2026-06-04-A)

⊞ is an **action**: pressing it runs the layout (re-arranges the nodes).
It shows **one mode-neutral "auto-arrange" icon on every canvas** — the
icon never changes shape. The layout it produces still differs per canvas
(mind-map tree on Foundation / Actors / Services, actor-anchored flow on
ServiceDetail), and that mode is named in the **tooltip text only**:
`canvas.autoLayoutTree` ("마인드맵 정렬") vs `canvas.autoLayoutFlow`
("흐름 정렬"), chosen by `flowMode = showDirectionSwitch`. The button still
carries `data-layout-mode` (test hook).

**Supersedes the icon half of D-2026-06-03-D (v0.40.4).** That version gave
⊞ a *mode-shaped* icon (tree vs flow), which made it look like a switchable
mode — like the direction toggle (↔/↕), whose icon flips on click. But ⊞
does not toggle a mode; it executes. User 2026-06-04: *"그걸 누르면 왜
정렬이 변하냐고"* — a mode-shaped icon on an action button reads as
contradictory. The icon is now a constant action mark; only the toggle
(↔/↕) shows mutable state. Static guard:
`viewer/tests/layout-controls.test.tsx` (same icon in both modes).

### Handle-aware fallback (v0.27.12, D-2026-05-28-G)

When the mindmap BFS yields zero positions (typical case:
ServiceDetail's hidden root-service per D-2026-05-28-B is the
anchor but is *intentionally* disconnected from every edge, so BFS
has no starting neighbours), `useAutoLayout` falls back to
`viewer/src/flow/handleAwareLayout.ts`:

- Dagre layered graph drawing with `rankdir: "LR"`.
- For every edge whose `sourceHandle` faces L or T, the source/target
  pair is **swapped in dagre's input** so dagre's LR output still
  places nodes "right handle = on the right" per the user's mental
  model (2026-05-28).
- Orphan nodes (no incident edges) keep their original positions.
- Cycle handling is dagre's internal feedback-arc-set pass: one
  edge per cycle is silently reversed for layout. Novel's typical
  ServiceDetail graphs contain small actor → interaction → actor
  cycles; the result is still readable but not always pixel-perfect.

Static guard: `viewer/tests/handle-aware-layout.test.ts`.

### Radial algorithm (`layoutAlgo="radial"`)

Implemented in
`viewer/src/canvases/sketch/radialLayout.ts`:

- A single hub node is the layout origin. For `ServicesCanvas` the
  hub is the synthetic project anchor; for `ServiceDetailCanvas`
  (which injects no anchor) the hub is the hidden root-service node
  (`kind === "service" && is_root === true`).
- BFS from the hub via undirected edges assigns a ring level to every
  reachable node (hub = 0, immediate neighbours = 1, ...). During the
  walk each node also records its BFS parent (the node that first
  reached it).
- **Angle assignment (two-pass since v0.26.3, D-2026-05-25-D):**
  - **Ring 1** members are sorted by id (determinism) and spaced at
    equal angles starting from the top (-π/2): a ring with N members
    uses 2π / N per slot.
  - **Ring k>=2** members are grouped by their BFS parent and *fan
    around the parent's angle* (not the canvas top). The fan width
    narrows with depth — π/(k+1), so ring 2 spans π/3, ring 3 spans
    π/4, etc. A parent with one child places that child on the same
    radial line as itself; multiple children spread evenly within
    the fan. The effect: a chain of length-1 spokes follows a single
    direction outward instead of collapsing back to the top.
- Ring radius accumulates: ring 1 = `hub_half + ring1_span/2 + gap`;
  subsequent rings add `ring_k_span + gap`. Span = the longest node
  dimension in that ring. Gap defaults to 40 px.
- Orphan nodes (not reachable from the hub) drop into a grid below
  the outermost ring — same fallback shape that `autoLayout.ts`
  uses for disconnected subtrees.

### Isolation contract (D-2026-05-13-L, extended D-2026-05-18-B and D-2026-05-24-B)

Four layers of defence keep auto-layout from affecting any wrapper
that did not opt in:

1. **Wrapper opt-in** — each wrapper supplies its own `layoutAlgo`.
   `SketchCanvas` itself has no default; without a wrapper there is
   no button.
2. **Conditional render** — `SketchCanvas` only renders the
   `ControlButton` when `layoutAlgo` is truthy.
3. **No state mutation when disabled** — both `useAutoLayout` and
   `useRadialLayout` are called unconditionally (React hooks rule)
   but their returned callbacks are only wired to a button that
   doesn't exist when `layoutAlgo` is null / undefined.
4. **Touches positions only** — both algorithms replace `x` / `y` on
   nodes via `onDocChange`; no edges / anchor / typed-text mutation.

### History (5 prior add/remove/extend cycles)

- **D-2026-05-04-D** — removed (misattributed user request; real
  intent was to remove download/upload only). **Rejected**.
- **D-2026-05-10-E** — reversed; full directional-tree spec.
  Implemented in v0.13.9.
- **D-2026-05-10-F** — button placement tuned (toolbar →
  `<Controls>`). v0.13.10. **Cursor flicker that the user
  attributed to auto-layout was independently caused by Tailwind
  preflight on `.react-flow__node[role="button"]` — fixed in this
  decision and remains fixed.**
- **D-2026-05-10-G** — removed again per user cost/benefit
  reasoning: *"auto layout 빼야겠네 문제가 너무 많다"*. The cursor
  problems were already fixed; the cited "문제" was likely the
  feature's complexity in the absence of a real user with a
  complex graph.
- **D-2026-05-13-L** — re-introduced as Foundation-only opt-in.
  User direct request: *"혹시 자동 정렬을 넣을 수 있을까요? ...
  다른 곳에 영향이 안 가게 만들어야합니다."* The isolation
  contract above is the cost/benefit answer to D-2026-05-10-G —
  the feature now cannot affect other canvases by construction.
- **D-2026-05-18-B** — extended opt-in to `ActorsCanvas`. User
  direct request after opening banas-imported and seeing Hero / Fan /
  Bana overlap: *"액터 캔버스에 노드 정렬 기능 넣기"*. Isolation
  contract honoured (`Services` / `ServiceDetail` still off);
  same one-shot apply + `Cmd+Z` + positions-only contract.
- **D-2026-05-24-B** — extended opt-in to `Services` + `ServiceDetail`
  with a new **radial** algorithm (hub-and-spoke), since the
  directional-tree algorithm assumed by D-2026-05-18-B for those
  canvases would not match their topology. The `enableAutoLayout`
  boolean prop is renamed `layoutAlgo: "tree" | "radial" | null`.
  User direct request after opening Services and finding no button:
  *"다른 캔버스에는 있는데 캔버스 정렬기능이 없다"*. The isolation
  contract is preserved (each wrapper still chooses; SketchCanvas
  still has no default).
- **D-2026-05-24-C** — same-day partial rollback of D-2026-05-24-B.
  `ServicesCanvas` reverted to no opt-in. User direction *"메인
  캔버스는 서비스에 대한 요약을 보여주는 것 뿐이에요"* +
  *"컨트롤하는것도 따로 해야지"* — the main Services canvas is a
  summary view; auto-layout and other controls belong inside the
  per-service modal (`ServiceDetailModal` + `ServiceDetailCanvas`),
  not on the overview. `ServiceDetailCanvas` keeps its `"radial"`
  opt-in. The `layoutAlgo` prop generalisation from D-2026-05-24-B
  is retained — only the Services wrapper's choice changed.
- **D-2026-05-25-C** — reverts D-2026-05-24-C: `ServicesCanvas` opts
  back into `layoutAlgo="radial"`. User direction next session
  *"서비스 메인 캔버스에 정렬기능 빠져있는건 여전하고"* — practice
  showed the lack of auto-layout on the main canvas hurt more than
  the "summary canvas" framing helped. Algorithm is unchanged
  (anchor as hub, BFS rings); `ServiceDetailCanvas` continues to use
  the hidden root-service as its hub.
- **D-2026-05-26-A** — `ServicesCanvas` + `ServiceDetailCanvas` switch
  from `"radial"` to `"tree"`. User direction *"정렬은 액터 캔버스
  참고하쇼"*. Even after the v0.26.3 fan-out fix, length-1 spoke
  chains (anchor → category → service) collapsed onto a single radial
  line because every node inherits its parent's angle and parents only
  have one angle. The tree algorithm follows user-drawn edge handle
  direction (T/R/B/L) instead — same shape Actors / Foundation use.
  `useAutoLayout`'s hub selection extended to fall back to the
  root-service node when `projectAnchor` is null (mirrors
  `useRadialLayout.pickHub`). The radial code stays in the tree as
  a future option but is not currently wired to any wrapper.
- **D-2026-05-26-B** — ServiceDetail modal mount relocated from the
  app root into the canvas container. User direction *"서비스디테일
  캔버스에서 뭘 할 수가 없어요. 여기 액터도 있고 해야하는데 그게
  없네요?"*. Diagnosis: the modal's `fixed inset-0` covered the whole
  viewport, hiding the sidebar and with it every drag-source the
  service-detail canvas needs (composition + actor / mission / value /
  identity refs). Fix: `<div>` wrapping the active canvas gets
  `relative`; the modal switches to `absolute inset-0` so it overlays
  only the canvas region. Sidebar stays visible and usable while the
  modal is open. ESC / backdrop-click close paths unchanged.

---

## Foundation typed-text storage (v0.17+)

Each Foundation typed-text node (`mission`, `core_value`, `identity`)
stores its content **inline in JSON** as MD-syntax string values per
D-2026-05-13-O principle #2 + D-2026-05-16-A. Fields are:

- `mission` — `body` only (**v0.43.0, D-2026-06-06-C**: `what_we_do` /
  `why` / `direction` removed — mission is one declaration = `label` +
  `body`; old values fold into `body` on read, server + viewer.)
- `core_value` — `body` only (**D-2026-06-16-M**: `definition` removed —
  `definition` and `body` both explained the value, so they collapse to the
  value's name (`label`) + `body`; `body` carries the value's meaning *and the
  trade-off it makes*. Old `definition` folds into `body` on read, server +
  viewer. Earlier **v0.43.1, D-2026-06-06-B** had already removed `do` / `dont`.)
- `identity` — `body` only, holding the **action-rule list** (**D-2026-06-16-N/O**:
  identity = the service's consistent execution / expression standards captured
  as always-applied action-rules ("we design / speak / behave like ~"), AI-derived
  from mission + core_value then refined through discussion; `description` removed
  — it folds into the rules. The inspector shows **name (`label`) + the action-rule
  list** only. Earlier **v0.43.2, D-2026-06-06-B** had already removed `do` /
  `dont`.) The **output-model fields** `status` (`manual` | `derived` | `confirmed`)
  + `provenance` (`string[]` of source node ids), added in **v0.44.0,
  D-2026-06-07-A**, are **inert / deferred (D-2026-06-16-O)**: no producer auto-sets
  `derived` / `confirmed` or fills provenance today, so the inspector shows no
  status / provenance inputs for now — they return with the AI-derive flow
  (ROADMAP 5.7). `evolution` (revision history) is deferred — overlaps git +
  `version`, no writer yet.

Every value is a Markdown-formatted string; newlines, bullets, bold,
links survive verbatim. The viewer's per-kind Inspector renders each
field as a monospace `<textarea>` so users edit the raw MD source
(rendered preview lands in a later phase).

**No per-file MD editing surface.** The shared `DetailsSection.tsx`
chrome (legacy MD editor for kinds whose long-form lives in
`{slug}/details.md`) is hidden on these 3 kinds via the
`hideDetailsSection` prop on `BaseInspector`. `details_path` carries
no value on Foundation typed-text kinds — it is cleared
unconditionally by the read-side migrator. Per-node MD files become
publish-output only in Phase 3.

**Pre-v0.17 migration:** First `read_canvas` of any project with
legacy `foundation/{kind}-{slug}.md` files runs
`_absorb_md_typed_text_into_json` to ingest the H2 sections + the
post-`---` free prose into the JSON node, then renames the source
file into `foundation/_legacy/`. Subsequent reads are no-ops
(idempotent). Quarantine — not deletion — preserves user data until
Phase 6 purge (v0.19.1).

**⚠ MD-template warning badge — retired (kept as no-op):** The pre-
v0.17 badge surfaced parser warnings on the canvas card. After
absorption no canonical MD file remains, so warnings are always
empty; `collect_foundation_md_warnings` returns `{}` and the badge
no longer renders on the 3 typed-text kinds. The function is kept
callable for backward API compatibility; Phase 6 deletes the call
site.

---

## Pan and select

The canvas **pans** when the user grabs an empty area (the React
Flow pane) and drags. The empty pane shows the `grab` cursor while
idle and `grabbing` while a pan is in flight. Selection box is
**Shift+drag** on the empty pane (the `selectionKeyCode`); plain
drag pans, plain drag on a node moves the node.

> **Why:** v0.13.4 removed pan-on-drag because users were
> accidentally panning while trying to click a node. v0.13.6 puts
> it back per the user's "노드 밖에 호버했을 때 보여야하는 손바닥
> 커서가 안생기구요" — the absence of a hand cursor read as the
> canvas being inert, which it isn't. The 4 px `nodeDragThreshold`
> already disambiguates a click on a node from a drag of a node;
> there is no equivalent disambiguation needed for the pane (a
> click that doesn't move = nothing happens; a click that moves =
> pan). See [D-2026-05-10-A](./DECISIONS.md).

## Context menu

The node / edge / pane context menu opens on a **genuine secondary
click only** (right-click, Ctrl+click, or two-finger trackpad click).
A **drag-release must never open it.**

> **Why (D-2026-06-15-N, broadened D-2026-06-16-A):** on a macOS
> trackpad, a one-finger press-drag-release emits a trailing `contextmenu`
> event *after* pointerup. React Flow's d3-drag only suppresses
> `contextmenu` *while* a drag is active, so the tail leaked to
> `onNodeContextMenu` / `onPaneContextMenu` and the menu popped at the
> release point ("drag a node, let go, it acts like a right-click" — user
> report 2026-06-15). `useContextMenus` watches the **raw pointer gesture
> at the window level**: a `pointerup` that moved more than ~5 px from its
> `pointerdown` is a drag, so the next `contextmenu` is swallowed. This is
> **kind- and canvas-agnostic** — it does NOT depend on React Flow firing
> `onNodeDragStop` per node, which left categories / group nodes / detail
> canvases uncovered in the first cut (v0.81.1, user-reported 2026-06-16).
> A real right-click never moves, so its menu still opens; each fresh
> `pointerdown` re-enables the menu. Pinned by
> `viewer/tests/context-menu-drag-suppression.test.tsx`.

## Hover behaviour

Hover behaviour is **React Flow defaults, no overrides**. All four
connection handles (○ at top / left / right / bottom) are visible at
all times — RF default `width: 6px; height: 6px; background: #1a192b`.

> **Why this is RF default and not our previous custom gating:** six
> rounds of cursor / handle interventions (v0.13.3 → v0.13.5) chased
> a "click vs draw vs drag" affordance problem and produced more
> regressions than they fixed. v0.13.6 reset to RF defaults so the
> baseline is uniform and the next session starts from one known
> state instead of an override stack. See
> [D-2026-05-10-C](./DECISIONS.md). If a future requirement needs to
> deviate (e.g. hide handles until selection), open a new decision
> with explicit user approval *before* re-introducing the override.

---

## Inspector (right panel)

Appears as an `<aside>` overlaying the right edge of the canvas when a
node is selected. Hidden when nothing is selected — **except** on the
ServiceDetail canvas, which renders the subject service's read-only
inspector as a fallback when no detail node is selected (see
[ServiceDetail → Right panel](#right-panel-option-1-d-2026-06-15-o)).

| Aspect | Behaviour |
|---|---|
| **Trigger** | Single click on a node (any kind except — TBD anchor). |
| **Width** | Toggle: 320 px ("narrow") ↔ `min(720, 60vw)` ("wide"). Choice persists in `localStorage`. |
| **Sections (Foundation)** | Header (kind, delete, width-toggle, close) → `_md_warnings` list (if any) → Label field → Typed-field forms per kind → MD-template editor (edit / split / preview). |
| **Close** | × button in header, or click empty canvas (pane click clears selection). |
| **Read-only mode (D-2026-06-15-O)** | `KindInspector` / `BaseInspector` accept `readOnly`: the label input is non-editable, and the delete / close / publish / published-versions / details-MD affordances are hidden. The per-kind body renders its fields read-only (Service shows its 5-field question-titled summary — 누가 참여하나? / 왜 필요한가? / 뭐가 좋아지나? / 뭘 양보 못 하나? / 어떤 결로 다가가나?, D-2026-06-17-B). Used by the Feature-canvas fallback (formerly ServiceDetail). |

---

## Viewport

The viewer must occupy the full browser window (no white strip on top,
bottom, or sides). Implementation defends this with `h-screen
min-h-screen` on the root and `min-height: 100dvh` fallback on
`html, body, #root`.

---

## Drag-and-drop

The canvas accepts drag-and-drop from the sidebar stencil. Drop
behaviour:

- **Capture mechanism (v0.67.0, D-2026-06-13-C):** the drag gesture is
  captured with **pointer events** (`pointerdown` on the stencil item →
  window `pointerup` over a canvas pane), NOT HTML5 `draggable` /
  `dataTransfer`. WKWebView — the bundled Tauri `.app`, Novel's only
  product surface — does not fire HTML5 `dragstart` / `drop`, so the old
  mechanism created no node on any canvas. The drop placement / hit-test /
  nudge / picker rules below are unchanged; only the gesture capture moved.
- **Hit-test order:** when computing which node "contains" the drop
  point, iterate the doc nodes in **reverse** order so later-drawn
  (visually on-top) nodes win over earlier-drawn parents. Without
  this, dropping onto a nested sub-actor would land on the parent
  actor instead.
- **Free drop (no container):** the new node lands at the cursor
  flow-point, centred. If it would overlap an existing top-level
  sibling, slide it diagonally by 32 px steps (max 24 tries) until
  free. **(v0.67.0, D-2026-06-13-G)** This applies on **every** canvas
  including Foundation — a dropped mission / core_value / identity lands
  where the user released, not snapped to an anchor-radial slot (the old
  drop-time radial snap is removed; the ⊞ auto-layout button still
  arranges on demand).
- **Nested drop (inside a container):** the new node uses
  parent-local coordinates relative to the container's top-left. If
  it overlaps a sibling, the same 32 px diagonal nudge applies among
  parent's direct children.
- **Optional category (v0.67.0, D-2026-06-13-D):** on the Services
  canvas a `service` is **not** required to nest in a `category`.
  Dropped onto a category it nests under it; dropped on empty space it
  lands top-level. Category is an optional thematic grouping, not a
  mandatory parent. (Supersedes the D-2026-05-28-A "service must nest in
  a Category" rule. Sub-actor still requires an Actor parent.)
- **Hierarchy edge:** dropping a kind onto an existing container also
  creates a dashed directed edge parent→child so the user can edit the
  relationship like any other edge. **(v0.67.0, D-2026-06-13-E)** the
  edge carries **no visible verb label** (the old "decomposes" label was
  clutter); the direction + relation still encode the structure.
- **Reference kinds (`actor_ref`, `mission_ref`, `value_ref`,
  `identity_ref`)** with no preset target id open a picker modal
  before the node is created. Presets that already carry the master
  id (the v0.11.5+ stencil generates per-master entries) skip the
  picker.

## Keyboard shortcuts

The canvas listens on `window` for keyboard shortcuts. The listener
is a no-op when focus is inside an editable target (`INPUT`,
`TEXTAREA`, or `contentEditable`) — so typing in the Inspector text
fields never triggers canvas actions.

| Combo | Action |
|---|---|
| `Cmd/Ctrl + Z` | Undo (one step). |
| `Cmd/Ctrl + Shift + Z` *or* `Cmd/Ctrl + Y` | Redo (one step). |
| `Cmd/Ctrl + C` | Copy currently-selected nodes to the in-app clipboard. No-op if nothing is selected. |
| `Cmd/Ctrl + V` | Paste from the in-app clipboard. No-op if the clipboard is empty. |
| `Cmd/Ctrl + D` | Duplicate currently-selected nodes in place. |
| `Cmd/Ctrl + A` | Select all nodes and edges on the active canvas (uses React Flow's `setNodes` / `setEdges` directly, bypassing `onNodesChange`). |

> **Editable-target guard is load-bearing.** Without it, `Cmd+Z`
> inside a text input would undo the canvas doc instead of the local
> text edit, which is surprising and destructive. Any keyboard hook
> refactor must preserve the guard.

## Cursor states (canvas-wide SSOT, applies to every canvas)

**v0.14.2 reset:** every cursor follows **pure React Flow default
+ pure Tailwind preflight, with NO overrides** in `styles.css`. The
v0.13.6 (D-2026-05-10-C) and v0.13.10 (D-2026-05-10-F) Tailwind
preflight cancellation rules were removed in v0.14.2 per direct
user request *"일단 RF 기본으로 돌리라구요"* (D-2026-05-11-A).

This table reproduces the resulting cursors so future sessions can
verify them without re-reading vendor CSS.

| Region | State | Cursor | Source |
|---|---|---|---|
| Empty canvas (`.react-flow__pane`) | idle | `grab` | RF default |
| Empty canvas (`.react-flow__pane.dragging`) | panning | `grabbing` | RF default |
| `.react-flow__node` (RF v11 sets `role="button"`) | idle | `pointer` | Tailwind preflight `[role="button"]` overrides RF's `grab` |
| `.react-flow__node.dragging` | dragging | `grabbing` | RF default beats preflight via specificity |
| Anchor body inner divs | idle hover | `grab` | inherits from `.react-flow__node` BUT anchor uses static `<span>` (no `role="button"`) so inner divs show their own inherited cursor — empirically `grab` because the inner div isn't itself preflight-matched |
| EditableText label span (mission / core_value / identity / actor / service / etc.) | idle hover | `pointer` | Tailwind preflight on `[role="button"]` (the role kept for keyboard a11y) |
| Fold `<button>` inside container nodes | idle hover | `pointer` | Tailwind preflight on `<button>` |
| Multi-selection rect (`.react-flow__nodesselection-rect`) | hover | `grab` | RF default |
| Connection handle (`.react-flow__handle.connectionindicator`) | hover, connectable | `crosshair` | RF default |
| Connection handle (`.react-flow__handle.connecting / .connectingfrom`) | active edge drag | `crosshair` | RF default |
| Edge (`.react-flow__edge`) | hover | `pointer` | RF default |
| Edge updater (`.react-flow__edgeupdater`) | hover end-point | `move` | RF default |
| Resize control side (`.react-flow__resize-control.left/right`) | hover | `ew-resize` | `@reactflow/node-resizer` default |
| Resize control side (`.react-flow__resize-control.top/bottom`) | hover | `ns-resize` | `@reactflow/node-resizer` default |
| Resize control corner (`.react-flow__resize-control.top.left / bottom.right`) | hover | `nwse-resize` | `@reactflow/node-resizer` default |
| Resize control corner (`.react-flow__resize-control.bottom.left / top.right`) | hover | `nesw-resize` | `@reactflow/node-resizer` default |
| Inspector / Toolbar / context menu | per element | per element | Tailwind / browser defaults |

**Asymmetry note:** anchor body shows `grab` while
mission / core_value / identity / etc. body shows `pointer` because
EditableText (which carries `role="button"`) is conditionally
attached only to nodes with an `onLabelChange` callback. Anchor
labels are not user-edited from the canvas (label mirrors
`ProjectDoc.name`), so anchor lacks the EditableText span. This is
a known asymmetry of the pure-RF-default decision; deemed
acceptable per D-2026-05-11-A.

**The RF mental model in one sentence:** anything draggable shows
`grab`, the active drag shows `grabbing`, drawing a connection shows
`crosshair`, clicking-to-select an edge shows `pointer`, and
resizing shows the directional resize cursor. Both pane and node
share `grab` so the cursor never changes when crossing between
them — by construction there is nothing to flicker.

**To deviate from this table:** open a `D-YYYY-MM-DD-X` entry,
record the rationale, and only then add a CSS rule in `styles.css`
guarded by an `!important` comment naming the decision id.

See [D-2026-05-10-C](./DECISIONS.md) for the reset rationale and
the full list of v0.13.3-v0.13.5 overrides that were removed.

## Things explicitly NOT in this Foundation spec yet

- Behaviour of the Anchor's Inspector (open / closed?).
- Drag-and-drop from the Foundation stencil onto the canvas (creation
  rules).
- Connection rules (which kinds can connect to which kinds).
- Multi-select + bulk operations.
- Keyboard shortcuts on Foundation specifically.

These are deferred to subsequent SPEC entries. **No implementation
decision should be made on these without first appending to this spec
and getting user approval.**

---

# Actors

## What Actors is

The canvas that answers **"who participates?"** for the project. It
carries the `actor` kind only ([`CONCEPTS.md`](./CONCEPTS.md)). Each
actor represents a participant — a person, role, system, organisation
— that takes part in any of the project's services.

## Anchor

Same anchor as Foundation: same synthetic node, same SSOT in
``ProjectDoc.anchors``, same label (mirrors `ProjectDoc.name`), same
visual differentiation. Auto-seeded on the Actors canvas — v0.11.4 —
so every primary canvas radiates from one centre.

> See [Foundation §Anchor](#anchor-the-centre-node) for full anchor
> behaviour. Behaviour is identical on Actors.

## Nodes — `actor`

| Aspect | Behaviour |
|---|---|
| **Shape** | `rounded` (rectangle with rounded corners). |
| **Colour** | Per-node, user-chosen via the Inspector. Default fill (when not yet set) — **TBD, see open question below.** |
| **Hierarchy** | An **inheritance tree** rooted at the project anchor: every directed edge on the actors canvas is `relation: "inheritance"` (child→parent, toward the anchor). The stencil exposes "Actor" (top-level) and "Sub-Actor" (drop onto an existing actor). |
| **Inheritance (v0.30.4, D-2026-05-31-G; REFINED D-2026-06-15-J)** | A sub-actor **inherits** its parent actor's common **identity** fields (`side` / `body`): a field resolves `own non-empty → nearest ancestor's non-empty → empty`. Computed at render (`domain/actorInheritance.ts`); nothing is written (each node's value stays the SSOT). The Inspector shows an inherited field as a greyed `↳ inherited from {parent}` caption; typing overrides. For the `side` (Surface) enum the caption renders the **localized option label** (e.g. "사용자 — 앱"), not the raw enum (`user`) — D-2026-05-31-J. **`motivation` / `pain` are no longer inheritable** — they left the actor for per-service-context `actor_ref` (D-2026-06-15-J), so `INHERITABLE_FIELDS = [side, body]`. |
| **Abstract root superclass (v0.31.0, D-2026-05-31-H; REFINED D-2026-06-15-J)** | OOP framing: the **root** of an inheritance tree — an actor with **no actor parent** (only parent is the anchor) **and** ≥1 actor child — is *abstract*. Its Inspector **hides** `side` (a superclass carries no concrete surface). The `body` field stays. "Has children" is **not** the test: an intermediate concrete actor (e.g. Bana with Hero/Fans below it) has an actor parent, so it keeps all fields — only the tree root is abstract. Detection: `domain/actorInheritance.ts::isActorBaseSuperclass`. (Originally also hid `motivation` / `pain`; those moved to `actor_ref` in D-2026-06-15-J and are no longer actor fields.) |
| **Surface field — `side` (v0.31.1, D-2026-05-31-I)** | The `side` field is labeled **"Surface / 접점"** — *which system the actor accesses* (operator → admin console; user → app). It is **not** "role in the value exchange"; the operator/user split exists because participants use different systems (Operator → operations page; end user → app). The stored enum stays `operator` / `user` (ServiceDetail subject detection reads `side === "user"`); only the i18n labels changed. `side` stays on the actor master as **identity** (it is *who the actor is*, not a per-service stake — D-2026-06-15-J keeps it here). |
| **Inspector (identity only, D-2026-06-15-J)** | The actor inspector edits **identity** only: `side` (Surface) + `body`. **`motivation` / `pain` are NOT here** — they are per-service-context, authored on the `actor_ref` inspector inside ServiceDetail. Rationale: PHILOSOPHY P3 (Participation is Asymmetric) — the same human is a Hero in one service and a Fan in another, so motive/pain are defined *by the service*, not globally. An actor not yet placed in any service therefore holds no motivation/pain (by design). |
| **⚠ MD-warning badge** | Same mechanism as Foundation typed-text nodes. (Per-actor MD file path: TBD — verify in code before next change.) |

## Edges

Same as Foundation: the Actors canvas is **user-draw-only by its own
spec** — a per-canvas choice, not the old global ban (D-2026-06-17-J
removed the blanket "all edges are user-drawn" rule; edges are governed
by their definition, not authorship). No auto-edges between anchor and
actors, no auto-edges between actors. Edited via double-click (edge
modal). Persisted in `actors/canvas.json`.

**Arrows converge on the anchor (v0.34.4, D-2026-05-31-R).** On Foundation
+ Actors every directed edge's arrowhead points at the **anchor-ward
endpoint** (the endpoint nearer the project anchor by hop-distance) —
Foundation elements compose INTO the service; actors PARTICIPATE in it. The
actor inheritance tree's child→parent edges therefore point *up* toward the
root, even though they don't touch the anchor directly. This is enforced
two ways: `handleConnect` normalizes a newly-drawn edge to point anchor-ward
(so which side/handle you start the drag from no longer flips the
direction), and `edgeTransform` re-orients the rendered arrow anchor-ward
for any already-stored edge (the doc edge stays the SSOT; only the RF
render swaps). All four node sides are `source` handles
(`ConnectionMode.Loose`) so a connection can be started from any side
identically. Services / ServiceDetail are unaffected (user-chosen
direction).

Floating edges render as **bezier curves** (v0.34.5, D-2026-05-31-S) —
diagonal edges bow gently toward the border side each endpoint exits;
axis-aligned edges stay straight. The round anchor (and any circle/ellipse
node) attaches the edge on its **actual ellipse circumference**
(v0.34.6, D-2026-05-31-T), not its bounding box, so the arrowhead sits on
the circle.

> The `valueFlowOn` toggle in `SketchCanvas` recolours edges by
> ``value_form``; whether that toggle is reachable from the UI on
> Actors specifically is **TBD** — verify before next edge work.

## Auto-layout, hover, viewport

Same as Foundation. (Defensive viewport CSS / hover behaviour /
auto-layout removal apply globally to every canvas.)

## Open questions (Actors)

- **Default actor colour / palette** — does dragging "Actor" from the
  stencil produce a deterministic colour, or random, or does the user
  always pick? Today's banas-v013 has Operator=blue, User=pink — were
  those defaults or chosen? Decision needed before next stencil work.
- **Sub-actor visual relationship** — when an actor has `parent_id`,
  does the canvas draw a synthetic edge to the parent? Or is the
  parent–child relationship visualised some other way (nesting,
  proximity, label)? Today's banas-v013 has no sub-actors so behaviour
  isn't visible. Verify before adding any sub-actor.
- **Anchor ↔ actor relationship** — should there be any *visual*
  indicator that "this actor participates in this project", or is
  membership purely positional (actor lives on Actors canvas =
  belongs to project)? Today: nothing. Decision needed if anything
  should be added.
- **Actor's typed fields + per-actor MD file** — which fields exist on
  an `actor` node? Does it carry an MD template like Foundation
  typed-text nodes? Confirm in the code or with the user before
  Inspector / Actors-related changes.
- **Edge semantics on Actors** — are edges between actors meant to
  encode value-flow (gives / receives), reporting lines, social ties,
  or just freeform? CONCEPTS.md hints at value_form on edges; SPEC
  needs to nail what's expected on Actors.

These remain implementation-defined until the user gives direction
and a `D-YYYY-MM-DD-X` entry is added to
[`DECISIONS.md`](./DECISIONS.md).

---

## Publish (v0.18.0+)

Per [D-2026-05-16-E](./DECISIONS.md). Publish is an explicit
per-node action: the user selects a node, clicks the **📤** button
in the Inspector header, confirms the dialog, and three things
happen atomically — the node's ``version`` bumps MAJOR
(``v1.0 → v2.0``), a uniform MD file lands at
``<canvas>/published/{kind}-{slug}-{version}.md``, and a git commit
is recorded with machine-readable ``Publish-*:`` trailers.

### What the Inspector shows

- **Version badge** (left header cluster, after KIND tag) —
  monospace ``v<MAJOR>.<MINOR>`` (e.g. ``v1.0``). No i18n.
- **Publish button** (right header cluster, between width-toggle and
  delete) — labeled ``📤 publish`` (i18n via
  ``inspector.publishShort``). Hidden when the node is publish-
  ineligible (see eligibility table below).

### Publish eligibility (15 kinds)

| kind | Inspector button | Reason |
|---|:---:|---|
| `project` | hidden | anchor mirrors ``ProjectDoc.name`` |
| `service` (is_root) | hidden | ServiceDetail mirror; the Services-canvas master publishes, mirror follows |
| `actor_ref` / `mission_ref` / `value_ref` / `identity_ref` | hidden | aliases; publish the referent instead |
| 11 publish kinds (mission / core_value / identity / actor / service non-root / category / metric / step / rule / content) | visible | publish bumps own MAJOR. `actor.is_root` is no longer a publish gate per [D-2026-05-19-D](./DECISIONS.md) — every actor is a Symbol (CONCEPTS.md). |

The eligibility predicate is implemented twice in lockstep —
``mashbill/md_publish.py::can_publish`` and
``viewer/src/domain/publishEligibility.ts::canPublish``. Drift
between the two is a Phase 4-blocking bug; both must stay in sync.

### Typed text + body fields (v0.19.0+)

Per [D-2026-05-16-F](./DECISIONS.md) (body field on 10 kinds) +
[D-2026-05-17-B](./DECISIONS.md) (MD-aware editor). All
publish-eligible kinds carry a ``body`` field for free-form notes
(a "노트" extra). All typed text fields on these kinds (e.g.
`mission.body`, `actor_ref.motivation`, the service inspector's
"왜 필요한가?" / "뭐가 좋아지나?" fields (D-2026-06-17-B), `rule.policy`)
are stored as **MD-formatted strings**
(D-2026-05-13-O #2) and edited via a **CodeMirror 6 MD-aware
editor** in the Inspector (headings / lists / bold / italic / code
/ links / blockquotes render with syntax highlight as the user
edits). The legacy DetailsSection MD-file editor is hidden for all
10 publish-eligible kinds — JSON SSOT.

**Service inspector — 5 question-titled fields ([D-2026-06-17-B](./DECISIONS.md)).**
The Services-overview `service` inspector is redefined to **5
question-titled fields**, in order: (1) **"누가 참여하나?"** — multi-select
**actor** references (chips picked from the Actors canvas), (2) **"왜
필요한가?"** — typed, the gap / need the service fills (renames + reframes
the old `problem`, dropping the negative "문제" framing), (3) **"뭐가
좋아지나?"** — typed, the improvement it creates (renames `value_created`),
(4) **"뭘 양보 못 하나?"** — multi-select **core_value** references (chips
picked from Foundation), (5) **"어떤 결로 다가가나?"** — multi-select
**identity** references (chips picked from Foundation). All three reference
pickers are multi-select (복수 선택); core_value / identity are *picked*
from Foundation, like actors, not free-typed. The field titles are
question-form so each doubles as the AI interview prompt
(D-2026-06-16-P — everything built through discussion).

Each reference picker is **pick-OR-create** (D-2026-06-19-C, wired
D-2026-06-24-G): an inline "create" input makes a real master on its home
canvas — actor → Actors, core_value / identity → Foundation — via
`POST /api/projects/{id}/masters` `{kind, label}`, which returns the new id so
the chip resolves once that canvas refreshes. The master is created lightweight
(name only, deepened later by its home-canvas coach); creating is **not**
free-typing — it always yields a chip pointing at a real upstream node. The
engine owns the home-canvas + positioning (`mashbill/masters.py`) so the viewer
never writes across the canvas boundary.

The old service text fields — **`what`, `scope`, `trigger`, `how`,
`outcome`, `do`, `dont`** — are **DELETED** (their substance lives on the
feature canvas as nodes: `step` = "how", `rule` = "do/dont", and the
per-participant 하는 일 / 받는 것 / 페인 lives on each `actor_ref`). Also
deleted: **`target_side`** (redundant — participants are now shown directly
via "누가 참여하나?", and each actor carries its own side) and **`body`**
(the 5 structured fields replace the free memo). Per-actor `actor_ref.pain`
(per-(actor × service) friction, D-2026-06-15-J) stays the per-participant
detail.

**Mermaid Live Preview (v0.21.0+, [D-2026-05-17-D](./DECISIONS.md)):**
Any ``` ```mermaid``` ``` fenced block inside the MdTextarea renders
as an inline SVG widget below the closing fence, 200 ms after the
last keystroke. The raw markdown source stays visible and editable
above the diagram (SSOT — the decoration is visual-only). Mermaid
is lazy-loaded the first time *any* mermaid block enters the
viewer; projects without mermaid blocks pay zero mermaid bytes.
Invalid mermaid syntax swaps the SVG for a red-border error block
without disturbing the source.

The ref 4 kinds (`actor_ref` / `mission_ref` / `value_ref` /
`identity_ref`) are **publish-ineligible** and carry **no
``body``** — they are relation tools on the services canvas
("who for / by whom / under which mission, value, identity"), not
own-SSOT nodes. The one ref-specific typed text pair
(`actor_ref.gives` / `actor_ref.receives`) still renders as a
monospace MD textarea for input consistency, but no MD file is
emitted on publish.

### What lands on disk per publish

- **MD file** at
  ``<project_id>/<canvas>/published/<kind>/<node_id>/v<MAJOR>.<MINOR>.md``
  (v0.24.3 layout per [D-2026-05-18-A](./DECISIONS.md); pre-v0.24.3
  used ``<slug>`` instead of ``<node_id>``, which could produce
  Korean / CJK folder names. v0.23.0 → v0.24.3 migration runs on
  first ``read_canvas``: ``<slug>`` folder renamed to ``<node_id>``.
  Pre-v0.23.0 flat ``<canvas>/published/<kind>-<slug>-v<MAJOR>.<MINOR>.md``
  is still auto-migrated by the older first-read pass.) MD format
  pinned in [`PUBLISH.md`](./PUBLISH.md). All versions of the same
  logical document live in one ``<kind>/<node_id>/`` folder,
  browsable in the Inspector's "Published versions" section.
- **Bumped ``version`` field** persisted to the canvas's
  ``canvas.json`` via the regular write path. When the published
  node has a mirror in another canvas (e.g. a service master in
  Services + its ServiceDetail root mirror), **both files** are
  bumped in lockstep.
- **Git commit** in the project's git repo
  (``.plot/{project_id}/.git``) with subject
  ``publish: {kind} "{label}" → {version}``, the 5 base
  ``Publish-*:`` trailers (Phase 3), plus zero or more
  ``Publish-Propagated-Ancestor:`` trailers (Phase 4 — see next
  section).

### Published versions in the Inspector (v0.23.0+)

Per [D-2026-05-17-I](./DECISIONS.md). The Inspector, for every
publish-eligible node, shows a **Published versions** section
underneath the per-kind body + DetailsSection. The section lists
one row per existing published MD file, newest version first, with
``{version, published_at, sha}``. Clicking a row opens a modal that
renders the MD via ``MDPreview`` (GFM + Mermaid). Escape or
backdrop-click closes.

Empty when the node has never been published. The list refreshes
when the node's ``version`` changes (i.e. immediately after a
publish-button press).

The list endpoint is
``GET /api/projects/{id}/canvases/{kind}/nodes/{node_id}/published``
and returns ``{versions: [{version, path, published_at, sha, size}]}``.
``published_at`` is parsed from the MD frontmatter; ``sha`` is the
short hash of the git commit that introduced the file.

### Publish — MINOR propagation (v0.20.0+)

Per [D-2026-05-17-C](./DECISIONS.md). When the user publishes
``N``, the server walks ``N``'s ``parent_id`` chain across every
canvas in the project and **MINOR-bumps every ancestor**.

- **Walk rule:** ``parent_id`` chain only. Refs
  (``actor_ref``, ``mission_ref``, ``value_ref``, ``identity_ref``,
  and ``CanvasDoc.service_ref``) are **not walked**. When the same
  id has file-presence in multiple canvases (ServiceDetail root
  service ↔ Services master service), the walk treats them as one
  logical node and crosses the canvas boundary via id-matching
  only.
- **What changes per ancestor:** only the JSON ``version`` field
  (``v1.0`` → ``v1.1``, ``v2.3`` → ``v2.4``). **No new MD file** is
  emitted. The on-disk MD stays at its MAJOR-publish snapshot
  version; the JSON ``version`` legitimately drifts past the
  latest on-disk MD filename, and the gap is the "descendants
  moved since" indicator.
- **Where in the commit:** one
  ``Publish-Propagated-Ancestor: <node_id> <from_v>→<to_v>``
  trailer per ancestor, appended after the 5 base trailers. Single
  atomic commit; ``git revert HEAD`` undoes the entire propagation.
- **Walk termination examples:**
  - **Mission published** → 0 ancestors (Foundation peers are
    top-level; no propagation).
  - **Step in service_detail published** → 2 ancestors:
    (a) the service (mirrored in services + service_detail),
    (b) the parent category.
  - **Service in services published** → 1 ancestor: the parent
    category. The MAJOR bump also lands in the ServiceDetail
    mirror file to keep them in lockstep.
- **No Inspector UI for propagation history.** The existing
  version badge already shows ``vMAJOR.MINOR``; users see MINOR
  moving silently as descendants ship. Git log is authoritative
  for "who propagated what when".

### Publish is gated by dirty (v0.22.0+)

Per [D-2026-05-17-H](./DECISIONS.md). Publishing requires the node to
have at least one **content change** since the last publish. Content =
typed-text fields + ``label`` + ``body`` + the set of edges incident
on the node. Visual changes (``x`` / ``y`` / ``width`` / ``height`` /
``color`` / ``shape`` / ``icon`` / ``collapsed``) are silently saved to
``canvas.json`` like any other state but do **not** mark the node
dirty. The Phase 4 ancestor MINOR drift
([D-2026-05-17-C](./DECISIONS.md)) is also not dirty by itself — the
propagated ``version`` bump is bookkeeping, not new content.

The Inspector **disables the 📤 publish button when the node is
clean**, with a ``title`` tooltip naming the last-published version
(*"v2.0 이후 변경 사항 없음"* / *"No content changes since v2.0"*).
When the user first creates a publish-eligible node, the button is
enabled (no baseline yet → initial publish always allowed).

Edge changes are bilateral: adding, removing, or editing an edge
``(A → B)`` marks both ``A`` and ``B`` dirty (each endpoint's
incident-edge set changed).

Implementation: the server stamps a ``_publish_baseline`` private
field on the bumped node (and any mirror) at publish time, then
recomputes ``_dirty`` on every canvas GET by comparing the current
content + incident edges against the baseline. The viewer never
round-trips ``_publish_baseline``; ``write_canvas`` preserves it from
disk state when a PUT payload omits it.

When the user *does* press a still-enabled publish button, the bump
is still always-MAJOR (``v1.0 → v2.0``); each publish produces a
distinct MD file (``-v2.0.md`` / ``-v3.0.md`` / …) and a distinct
commit. Ancestor MINOR propagation runs as before.

### Recovery from a misclick

No Unpublish button in v0.20.0. Manual recovery is documented in
[`PUBLISH.md`](./PUBLISH.md) — ``git revert HEAD`` plus optional
MD-file cleanup. Revert is atomic across the MAJOR bump, the new
MD file, every mirror bump, and every ancestor MINOR bump — they
all live in one commit. An automated **Unpublish** button is queued
as a follow-up in [`NEXT_SESSION.md`](./NEXT_SESSION.md).

### What Phase 4 explicitly does NOT do

- **Cross-ref propagation** (following ``actor_ref`` /
  ``mission_ref`` etc.). Refs are *links*, not parent–child.
  Bumping the Actor because a service references it would create
  wide noisy ripples with unclear semantics. User-rejected
  alternative in D-2026-05-17-C.
- **Container-publish semantics** (publishing a `category` pulls
  children too). Phase 5.
- **Folder-hierarchy MD layout** (``published/foundation/mission/
  v2.0.md`` style). Phase 5.
- **Render-preview surface** for published MD files inside the
  viewer. Out of scope.
- **Bulk publish** / publish-history viewer / batched publish.
  Out of scope.
- **Inspector "propagated by descendant X" badge.** YAGNI; queued
  for a future release if usage warrants.

---

# ServiceDetail (→ Feature canvas)

> **Renamed to the *feature* canvas (D-2026-06-17-D/G).** The Services
> overview now holds three node kinds under the anchor — **category**
> (visual grouping only), **service** (the 5-field inspector, D-2026-06-17-B),
> and a NEW **`feature`** node nested under a service (a capability the
> service offers — 글쓰기 / 글편집 / …). **Selecting a service shows its
> 5-field inspector — it no longer drills; clicking a `feature` opens what
> this section calls "ServiceDetail," so the drill target is now the
> *feature*, and this canvas is effectively the *feature detail.***
> Hierarchy: **카테고리 → 서비스 → 기능** (overview) → **행동 / 룰**
> (detail). The feature canvas is a **behaviour flowchart at action-altitude
> inheriting the service philosophy** (actor-anchored, value-oriented;
> D-2026-06-17-G) — it shows user actions → branches → results, and does NOT
> descend into implementation logic (that is the user's AI agent's job,
> outside Novel). The references below to "the service node / service-detail
> subject" read as the *feature* under the new model; the body of this
> section predates the rename and is brought current in a later expansion.

## What ServiceDetail is

The canvas where one service is **designed in detail** — opened as
a **dynamic canvas tab** when the user selects (single-click) a
non-root service node on the Services canvas (D-2026-06-15-H;
previously a modal overlay). The tab (`Foundation | Actors | Services
| {ServiceName}`) renders the detail canvas inline; switching to an
F/A/S tab keeps it, and its × closes it. The service itself is the **subject** of the
canvas: the root-service node is rendered at the centre
(D-2026-05-26-G) and serves as both the visible composition anchor
and the BFS root for the tree auto-layout. The user composes
around it: actors, interactions, value flows, references to mission
/ value / identity.

**Identity (D-2026-05-26-C, refined by D-2026-05-26-G):**
ServiceDetail is a **user-authored design canvas for one service**.
The service is the load-bearing centre — every other node the user
draws sits in relation to it, even if not always edge-connected.
The system does *not* prescribe a meaning for each node kind — the
user adds nodes (actor refs, mission / value / identity refs,
composition primitives) and draws edges between them to express
whatever interaction / value model fits the service. The stencil
sections are *hints* ("here are the kinds worth reaching for"),
not a constrained drop palette.

**Tab label vs canvas root-service node** (D-2026-06-15-H; was a modal
header pre-tab):
- Canvas tab label (`{ServiceName}`) = navigation.
- Canvas root-service node = design subject.

Two distinct surfaces, not a duplication.

User intent (verbatim 2026-05-26):
> *"인터렉션 그래프인데 사용자가 만들 수 있어야해요. 사용자가 그릴수
> 있어야한다구요. 노드 추가하고 선 이어서 그리고 등등"*

This matches Novel's PHILOSOPHY P10 ("the user controls every line,
every position, every colour") and VISION's user-authored cycle. No
auto-edges; no auto-positioning beyond the `⊞` tree button.

## Right panel (Option 1, D-2026-06-15-O)

The detail canvas's right panel follows a three-state rule so the user
always knows "what am I looking at / editing":

| State | Panel shows |
|---|---|
| **Default** (no detail node selected) | The **subject service's read-only inspector** — its typed fields (problem-first), read cross-doc from the Services canvas. The service is the canvas's implicit subject (it has no node here, D-2026-05-28-B), so this is where the user reads "what is this service" without leaving the detail canvas. |
| **A detail node selected** | That node's **editable** inspector (actor_ref motivation/pain, step, rule, content, …) — the normal per-kind inspector. |
| **Empty space clicked** | Back to the service (pane click clears the selection → fallback). |

The service is read **cross-doc**: it lives on the Services canvas, so
`ServiceDetailInspectorHost` resolves it from the cached Services
`CanvasDoc` (App holds it) by `doc.service_ref`. If the service has been
deleted on the Services canvas (the detail tab can outlive it), the
fallback renders nothing — no crash. The service is **read-only here**
(editing happens on the Services canvas, the service's home); the
read-only inspector hides every edit affordance (see
[Inspector → Read-only mode](#inspector-right-panel)).

Seam: `SketchInspectorBindings` renders a `fallbackInspector` render-prop
in place of its old empty `return null`; `SketchCanvas` threads it; only
the ServiceDetailCanvas wrapper is given one (via App's memoised
`detailFallbackInspector`). Pinned by
`viewer/tests/service-detail-fallback-inspector.test.tsx`.

## Stencil

> **Feature-canvas inventory (D-2026-06-17-H).** The feature canvas (renamed
> from Service-Detail) holds exactly: **행동 (`step`) + 분기 (`decision`) +
> 흐름선 (flow edges) + 노트 (`note`, D-2026-06-17-F) + 룰 (`rule`,
> D-2026-06-17-E, per-feature) + 액터 참조 (`actor_ref`)**. **Removed** from
> the old set: **`mission_ref` / `value_ref` / `identity_ref`** (now held on
> the *service* inspector as chips, D-2026-06-17-B — the feature inherits
> them, so duplicating on the canvas is redundant), **`metric`** (not needed),
> **`content`** (implementation artifacts = below action-altitude = AI's job),
> and **`group`** (its chunking role is now the "feature" level; folding a
> busy flow is a view affordance, not a node kind). The stencil table below
> predates this trim; the `Composition` (metric), `Missions`, `Core Values`,
> and `Identity aspects` sections are slated for removal in the
> feature-canvas implementation.

Per the `SketchStencil` (`viewer/src/canvases/SketchStencil.tsx`)
`service_detail` branch + the modal-internal `ServiceDetailStencilPanel`:

| Section | Items | Source |
|---|---|---|
| **Composition** | `metric`, `step` | Static — defined inline. |
| **Actors** | one preset per `actor` master | `availableActors` (Actors canvas) |
| **Missions** | one preset per `mission` master | `availableMissions` (Foundation canvas) |
| **Core Values** | one preset per `core_value` master | `availableValues` (Foundation canvas) |
| **Identity aspects** | one preset per `identity` master | `availableIdentities` (Foundation canvas) |

Each ref preset is generated from its master so dropping it skips
the picker — the resulting node carries `ref_*_id` already.

### Layer grouping (v0.28.5, D-2026-05-30-H)

The sections are grouped under two `LayerHeader`s that mirror the
2-layer essence model (VISION 3-phase), read top-to-bottom:

- **① Flow (Execution)** — Actors → Interactions (`step`) + Decision
  (`decision`) → Values (`metric`). The concrete flow the user
  designs. Actors sit at the top — the flow's tier-1 subject.
- **② Essence injection (Retention)** — Mission / Core Value /
  Identity refs. The essence injected onto the flow (rendered as the
  violet injection edges per D-2026-05-30-D, anchored per
  D-2026-05-30-G).

"Build the flow, then inject the essence." Render-level grouping only;
no change to drop rules or kinds.

### Composition drop is free-form (D-2026-05-28-A, v0.27.10)

The Composition presets (`metric`, `step`) drop **free-form** on the
ServiceDetail canvas — they do **not** require a `service` container
parent. This matches the user's design intent (verbatim 2026-05-28):

> 서비스 디테일 캔버스는 **기능 명세가 아니라 관계와 가치 흐름**을
> 보여줘야 한다. … 인터랙션 노드 중심으로 구성.

In that model:
- **Actor nodes** (`actor_ref`) — e.g. Hero (전문가), Fan
- **Interaction nodes** (`step` re-purposed) — 액터 간 접점:
  모임 개설/참여, 콘텐츠 발행/소비, 후원/구독, 1:1 소통, 클래스/이벤트
- **Decision nodes** (`decision`, v0.28.0 D-2026-05-30-C) — 흐름의
  분기점 (마름모): 사용자 선택 (방식 선택) 또는 시스템 판정 (검증
  성공/실패). 분기는 사용자가 그린 라벨 엣지로 표현.
- **Value nodes** (`metric` re-purposed) — 인터랙션에서 교환되는 것:
  전문 지식, 경험/취향, 수익, 팬덤/소속감
- **Upper-link nodes** (`mission_ref`, `value_ref`) —
  개요 캔버스에서 내려오는 핵심가치 / 미션

Edge directions per the user's design (no auto-emit — the user draws
each one):
- 액터 → 인터랙션 → 액터  (가치 흐름)
- 인터랙션 → 가치 노드  (무엇이 교환되는가)
- 인터랙션 → 핵심가치  (어떤 가치가 실현되는가)
- 핵심가치 → 미션  (어떻게 미션에 기여하는가)

### Foundation-injection edges (v0.28.1, D-2026-05-30-D)

An edge whose **source** is a foundation ref (`mission_ref` /
`value_ref` / `identity_ref`) renders as an **injection** edge:
animated (marching dashes flowing source → target) + a violet stroke
(`#8b5cf6`) + `4 4` dash. It expresses "this mission / core value /
tone&manner *fires here*" at a concrete flow point (e.g. 유머
(Humor) → 로그인 페이지 진입). Like the branch badge, the style is
**derived from the source node kind** — no new edge kind, no stored
flag, no auto-emit (the user draws the edge). `actor_ref` is excluded:
the user-side `actor_ref → entry` subject edge is the sequence anchor,
not an injection.

**Backwards-compat:** dropping a composition preset *inside* a
service container still nests it (the user can still build the
old service-anchored composition graph if they want). The change
is that an empty-space drop is now allowed and lands as a
top-level peer. The previous error message *"Drop inside a Service
container"* is no longer shown on the ServiceDetail canvas.

The static guard at `viewer/tests/service-detail-composition-drop.test.tsx`
pins both forks of this contract (free on empty + still-nests inside
service).

## Service composition model (D-2026-05-28-J, v0.27.15)

> *"이거죠"* — user, 2026-05-28, on the Login user-interaction
> graph (Bana-anchored, branch on method choice, join at the shared
> "대시보드 진입" outcome).

The Service is **one *purpose*, multiple *paths*** to reach it.
ServiceDetail's canvas expresses that purpose by laying out the
sequence of **user interactions** that bring the user to the
service's outcome.

### Definitions

| Concept | Representation |
|---|---|
| **Service** | one *purpose* (= the outcome the user reaches). On the canvas: the modal header + the (hidden, D-2026-05-28-B) `service_ref` anchor. |
| **Step** | a single **user-side action** — what the user does (입력, 클릭, 선택, 동의, 링크 클릭, …). System work is NOT a step; it lives inside the step's `outcome` text. |
| **Sequence** | `step → step` directed edge (label `next` / `branch` / `join` are user copy, not new edge kinds). |
| **Branch** | `decision` step followed by *multiple outgoing* edges to per-path first steps. Each path may have any number of further steps. |
| **Join** | *multiple incoming* edges into one result step **when the outcome is the same**. Three OAuth flavours that all land at `대시보드 진입` should merge there — anything else over-fragments the canvas. |
| **Result** | the final step of the service. Single result = the paths share one outcome; multiple results = the outcomes legitimately differ (different state, different next-service entry point). |
| **Subject (actor)** | the **human** doing the steps. Wired by **one** `actor_ref → entry` subject edge — every downstream step inherits the subject by following the sequence. (No need to draw a subject edge per step; that's chrome noise.) |
| **Subject scope** | actors are always *humans* (no `System` / `Server` master). System behaviour belongs in `step.outcome`. If the user encounters multiple human roles in the same service, draw one `actor_ref` per role and split the relevant subjects across the entry points of their sub-flows. |
| **Per-service stake (`actor_ref`, D-2026-06-15-J)** | An `actor_ref` carries the actor's stake **in this one service**: `motivation` (why this actor participates here), `pain` (what hurts here), plus the existing `gives` / `receives` value exchange. Authored on the `actor_ref` inspector; SSOT is per-(actor × service) — the global actor master holds none of these (PHILOSOPHY P3). A brand-new `actor_ref` starts blank, surfacing the per-service Discovery question at the moment the participation is drawn. `side` is **not** authored here — it stays a denormalized colour-coding mirror of the master's identity `side`. |
| **`actor_ref` click — no jump (D-2026-06-15-L)** | On a ServiceDetail canvas, clicking a user/actor (`actor_ref`) — single **or** double — opens its inspector (to edit the per-service motivation/pain), and **never navigates away** to the Actors canvas. Supersedes the actor_ref double-click → actor-master jump from D-2026-06-15-H #2 (reach the master via the Actors tab). Mechanism: ServiceDetail marks **no** node drillable, and `useInspectorRouting` double-click drills only `shouldDrill` nodes (the unconditional double-click drill was the bug). |
| **Spatial direction** | LR or TB — picked by the user. The auto-layout MUST preserve whichever direction the user has already established (`actor → entry` handle direction is the cue). |

### What "step = user interaction" rules out

- *Server verifies credentials* is **not** a step. It is the outcome
  text on the `Submit` step.
- *Send confirmation email* is **not** a step. It is the outcome
  text on the *user's* triggering step.
- An `Admin / System` actor as the subject of a "verify" step
  is a category error: Admin is itself a user, and verification is
  not a user action.

### Why "merge on shared outcome"

A service exists to deliver a specific outcome. If three login
methods all deposit the user on the dashboard, *the dashboard
arrival* is the service's single user-visible answer; splitting it
into three nodes turns the canvas into an implementation diagram
instead of a user-interaction diagram. The *paths* differ, the
*purpose* doesn't. When two outcomes genuinely diverge (e.g. login
vs. password reset request), you have two services (or one branch
with two terminal results) — not a forced single result.

### Worked example — Login

```
   ┌── 이메일 입력 → 비밀번호 입력 → Submit ──┐
Bana → 진입 → 방식선택 ─┼── Google 클릭 → 권한 동의 ──────┼── 대시보드 진입
   └── 이메일 입력 → 링크 클릭 ──────────┘
```

Live demo doc: `plot-test-v013/.plot/banas-imported/services/n_mpkyhvsj_mjzh/detail.json`.

### Canvas rendering of a step (v0.27.19, D-2026-05-30-A/-B)

A `step` node on the ServiceDetail canvas renders, top-to-bottom:

- the `STEP` kind tag (existing).
- the **label** = the user-side action (inline-editable, existing).
- an `⑂ branch` badge **iff** the step has ≥ 2 outgoing directed
  edges (a Branch per the table above). Derived from the edge graph,
  not a stored flag — the branch *is* the multiple-outgoing-edge
  structure (D-2026-05-30-B). The badge never changes the node's
  user-chosen shape or colour.
- the **outcome** = the system-side end state, as a muted `↳ …`
  subtitle, **inline-editable** (multiline; Cmd/Ctrl+Enter commits,
  Esc cancels). Empty steps show a `(outcome — click to add)`
  placeholder (D-2026-05-30-A). This keeps the SPEC rule "system
  work is NOT a step; it lives in `step.outcome`" legible without
  opening the Inspector.

### Negative-case (failure) tint (v0.28.2, D-2026-05-30-E)

A `step` carries `polarity` (`positive` / `negative` / `neutral`,
default `neutral`) so the flow can model **negative cases**, not just
the happy path. A `decision` branches to result steps; a `negative`
result renders a **red tint** (`#fee2e2`), a `positive` result a green
tint (`#dcfce7`). `neutral` keeps the user's own colour — the tint is
**opt-in** (the user sets polarity), so it does not violate the "user
controls every colour" rule. The failure *reason* is the step's label
/ `outcome` text (no reason = "단순 실패"; with = "이유 있는 실패").
`decision` does not carry polarity — decisions are neutral forks, not
outcomes.

### Group (flow chunk) (v0.29.0, D-2026-05-30-I)

A `group` is a container that chunks a busy flow — e.g. collapse the
three OAuth branches into one node.

- **Create**: multi-select ≥ 2 nodes → right-click → "Group selected
  (N)". A `group` node is placed just above the selection's bounding
  box, with `member_ids` = the selection. Right-click a group →
  "Ungroup" removes it (members stay).
- **Membership SSOT**: `group.member_ids` — `step` / `decision` carry
  no group field, so membership can't drift.
- **Collapse**: the group reuses the fold (▾/▸) chrome. Collapsed →
  its members are hidden (`useNodesMemo` via `collapsedGroupMemberIds`)
  and the group shows a member-count badge. Expanding restores them.
- **MVP scope**: collapse is the feature. RF `parentNode` (drag-in
  visual containment) is deferred — an expanded group is a labelled
  marker, not a true visual box around its members.
- **MECE**: distinct from `category` (the Services-canvas *thematic*
  grouping of services). `group` is a ServiceDetail *flow* chunk.

### Node shape — producer vs reference (v0.29.3, D-2026-05-31-B)

Shape encodes whether a node is the **original** or a **symbol pointer**
to one. Forced at the renderer (`BaseNode.effectiveShape` →
`viewer/src/canvases/sketch/nodeShape.ts`, a pure module), overriding
the stored `shape`:

| Kind group | Kinds | Shape |
|---|---|---|
| **원본 / master** (producer plane) | `mission`, `core_value`, `identity`, `actor` | **rounded rectangle** (soft corners) |
| **symbol reference** (consumer plane) | `mission_ref`, `value_ref`, `identity_ref`, `actor_ref` | **circle** |
| `decision` | — | diamond (shape is the semantic) |
| **anchor** | `project` (synthetic) | its stored shape (user toggle; default circle) |
| everything else | `service` / `category` / `metric` / `step` / `rule` / `content` / `group` | their stored `shape` |

- The rounded-rectangle masters keep the kind corner-tag
  (`shouldShowKindTag` derives from the *rendered* shape); circles and
  the diamond have no flat corner so no tag.
- **Supersedes D-2026-05-28-D** ("all Symbol kinds always render as
  circles"). The user clarified (2026-05-31) that the original should
  read as a 네모 with soft corners and only the *reference* pointer as a
  circle — the shape now tells producer from reference at a glance.

### Decision node (v0.28.0, D-2026-05-30-C)

A `decision` is a flowchart branch point, dropped from the stencil's
Interactions section alongside `step`:

- **Renders as a diamond**, forced at the renderer
  (`BaseNode.effectiveShape` → `nodeShape.ts`) — the shape is the
  semantic, so a stored `shape` is ignored (same pattern as the
  producer-vs-reference shape rule below: master kinds force a rounded
  rectangle, `*_ref` kinds force a circle, D-2026-05-31-B). No kind tag
  (diamond has no flat corner).
- **One node for both flavours** — a *user choice* (방식 선택) and a
  *system judgment* (검증 성공/실패) are both `decision`s. This keeps
  `step` = *user action*: a system judgment is never a step.
- **Branches are labelled edges** (성공 / 실패 / a choice) — on this
  user-draw-only canvas the user draws each one. (The former "never
  auto-emit" framing is now per-canvas, not a global ban — edges are
  governed by their definition, D-2026-06-17-J; see SPEC §Edges.)
  Typed-failure results are ordinary result `step`s; validation conditions
  are ordinary `rule` nodes.
- **Fields**: `label` (the question) + `body` (notes). No `order` /
  `outcome` — a decision has many labelled outcomes (the edges), not a
  single one.

### Auto-layout responsibility

Per D-2026-05-28-J, auto-layout for ServiceDetail must
**preserve the actor anchor** and lay the step graph out from there
along the direction the user has already chosen. The v0.27.12
`handleAwareLayout` dagre LR fallback violates this — it rebuilds
the whole rank ordering and sweeps the actor along with everything
else. The replacement algorithm is filed as a follow-up
("actor-anchored layout", v0.27.16+). Until that lands, users
should arrange the canvas manually.

## Modal structure (D-2026-05-26-D, D-2026-05-26-F)

The ServiceDetail modal is **self-contained**: it owns its own left
stencil column. The main app sidebar does *not* swap to the
`service_detail` stencil when the modal is open; the modal owns its
own controls.

**Interaction trap (v0.27.2, D-2026-05-26-F):** while the modal is
open the root app `<div>` carries the HTML `inert` attribute — no
clicks, no focus, no keyboard reach the main canvas / sidebar /
header / tabs. The modal sits OUTSIDE the inert subtree (sibling of
the root `<div>`) so it remains fully interactive. Modal returns to
`fixed inset-0` (was `absolute inset-0` in v0.27.0–v0.27.1, when
containment-by-canvas was the trap mechanism).

```
┌─────────────────────────────── Service Detail · Auth › Login   [×] ┐
├──────────────┬───────────────────────────────────────────────────────┤
│ COMPOSITION  │                                                       │
│  Metric      │                                                       │
│  Step        │                                                       │
│ ACTORS       │                                                       │
│  → Hero      │       ServiceDetailCanvas (interaction graph)         │
│  → Fan       │                                                       │
│ MISSIONS     │                                                       │
│  → Mission   │                                                       │
│ CORE VALUES  │                                                       │
│  → Value     │                                              ⊞ ↶ ↷    │
└──────────────┴───────────────────────────────────────────────────────┘
   w-56 stencil          flex-1 canvas
```

Implementation:
- `viewer/src/shell/ServiceDetailStencilPanel.tsx` — `w-56` aside
  that renders `<SketchStencil canvas="service_detail" />` with the
  four `available*` master lists.
- `viewer/src/shell/ServiceDetailModal.tsx` — body is a 2-column
  flex (`stencilSlot` prop on the left, `children` on the right).
  `fixed inset-0` + inner panel `h-[92vh] w-[94vw]` (v0.27.2).
- `viewer/src/App.tsx` — `stencilCanvas={activeTab}` always; modal
  mounts as root-level sibling; root `<div>` is `inert` when modal
  is open.

ESC / backdrop click / × close paths unchanged.

## Auto-layout

`layoutAlgo="tree"` — same algorithm as Foundation / Actors / Services.
`useAutoLayout`'s `pickAnchor` falls back to the hidden root-service
node (`kind === "service" && is_root === true`) since ServiceDetail
injects no synthetic anchor. See [§Auto-layout](#auto-layout) and
[D-2026-05-26-A](./DECISIONS.md).

## Edges

Edges are **governed by their definition, not by who draws them**
(D-2026-06-17-J removed the blanket "all edges are user-drawn" rule —
see the main [§Edges](#edges) "Source of edges" row). This canvas is
currently user-draw-only by its own spec; never emit a *meaningless* or
*silently-uneditable* line. The v0.26.0 directed-edge model (`directed`,
`action_verb`, `value_form`) applies here too. Inspector UI for
`action_verb` / `value_form` is a follow-up.

## Open questions (ServiceDetail)

- **New kinds for "interaction" / "value token"?** User's working
  vocabulary distinguishes liaison nodes (e.g. "모임 개설", "콘텐츠
  발행") from value tokens ("전문 지식", "수익"). Current model
  expresses both via free labels on existing kinds (`step` /
  `metric` reinterpreted) or via `edge.value_form`. Whether a
  dedicated `interaction` kind earns its place is **OPEN** —
  decide after enough usage that a pattern is visible.
- **Inspector UI for edge `action_verb` + `value_form`** — fields
  exist on the data model since v0.26.0 but no editor yet.
- **Composition primitives (`rule`, `content`)** — **RESOLVED** by the
  2026-06-17 marathon. `rule` **stays**, as a **per-feature operational
  constraint** (password length, validation, limits — a concrete functional
  constraint, *not* identity/core_value; D-2026-06-17-E). `content` is
  **retired** from the feature canvas (implementation artifacts are below
  action-altitude = the AI's job; D-2026-06-17-H) — its project-level role
  is re-homed on the new Entities canvas (D-2026-06-17-I). A NEW **`note`**
  kind is added: edgeless, canvas-global ambient context read by the human
  and injected into the per-canvas AI framing (D-2026-06-17-F).

---

# Entities (D-2026-06-17-I/K)

> **Status:** pinned by the 2026-06-16~17 big-picture marathon; full
> per-canvas behaviour spec is a later expansion. The model below is fixed,
> the on-canvas interaction detail is not yet written.

## What Entities is

A new **project-level canvas**, symmetric to Actors — **액터 = 누가 /
엔티티 = 무엇**. It holds the product's **data objects** (글 · 댓글 ·
사용자), managed **project-wide in one place** via a NEW kind `entity`.

**The user does NOT author it manually.** Entities are **created by the AI
together with the user as a byproduct of designing features / services**
(D-2026-06-17-I): when a feature's action produces or uses a "thing," the
AI surfaces it and **auto-registers** it on the Entities canvas. The user
reviews / refines / confirms (never silent — D-2026-06-16-P), but never
starts from a blank entity canvas. **Bottom-up creation** (in feature work)
**+ top-down management** (project registry). Because entities emerge from
feature/service work, the canvas is a **derived surface that accumulates at
the end** of the design flow.

**Form = a conceptual entity map, NOT a physical ERD.** These are abstract,
pre-normalisation entities. The surface may show entities **+ rough
relationships** (사용자 ─쓴다─▶ 글 ─달린다─▶ 댓글) but **stops at the
conceptual level** — no normalisation, no foreign keys, no cardinality, no
field types. **Altitude guard:** Novel holds only **name + one-line "무엇을
담나"** (rough shape); detailed schema / field types / relations / indexes
are the user's AI agent's job, **outside Novel** (else Novel becomes an
ERD / DB-modelling tool — an identity violation).

## Behaviour (pinned by D-2026-06-17-K)

| Aspect | Behaviour |
|---|---|
| **Dedup** | **Fully smart, first-class.** Before creating an entity the AI must **strongly semantic-match** the candidate against the existing registry (글 = 게시물 = 포스트 → **one** entity). Only genuinely ambiguous cases go to the user ("이거 기존 '글'과 같은가요?"). **Never silent-merge, never silent-duplicate.** A 1급 duty of the AI chat playbook (ROADMAP 5.10). |
| **Back-reference** | **Shown, read-only.** Selecting an entity shows which features / actions reference it (글 → "글쓰기 · 글편집 · 글보기에서 쓰임"). Derived, read-only — core to project-wide management. |
| **AI-surfacing** | **In-chat proposal, not auto-scan.** During feature-design chat, when an action handles a "thing," the AI proposes the entity ("이건 '글' 엔티티네요 — 등록할까요?") → user confirms → it registers. **No silent background scan.** |
| **Inspector (when selected)** | **Lean, conceptual:** 이름 + **"무엇을 담나?"** (one line, rough fields 제목·본문·작성자 — no types / FK) + **어디서 쓰이나** (the read-only back-reference) + **거친 관계** (rough relationships to other entities). |
| **Edges** | Governed by their definition, not authorship (D-2026-06-17-J). The Entities canvas is **AI-maintained**, so the AI may propose / draw the rough entity↔entity relationship edges; the user can edit / delete any of them. |

A feature `step` / action gains a **reference relation to an `entity`**
("발행 → 글 생성"). The action↔entity reference mechanism is an open
implementation detail (D-2026-06-17-I).
