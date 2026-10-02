# Solera HTTP contract (v1)

Decision: D-2026-10-02-A (public `novel-ai/plugins/mashbill/docs/DECISIONS.md`). Solera runs as its own
engine; Mashbill never calls it; the app asks both engines and joins the answers.

## Process

- Entry: console script `solera-http` → `solera.server:run_http_only()`. Host fixed `127.0.0.1`.
- Port: env `SOLERA_PORT`, default `5191` (invalid value → 5191, like Mashbill's `MASHBILL_PORT`).
- Auth: env `SOLERA_AUTH_TOKEN`, read on every request. Unset → no auth (dev). Set → every `/api/*` path
  except `GET /api/health` needs `Authorization: Bearer <token>` (scheme case-insensitive,
  `hmac.compare_digest`); failure → 401 with `error` and `code` as described below.
  WebSocket takes the token as query param `auth`; failure closes with code 1008.
- CORS: `allow_origins=["*"]`, all methods, all headers (the bundled front end is cross-origin `tauri://`).
- HTTP dependencies live in an optional extra `http` (starlette, uvicorn[standard], watchdog), so the
  standalone MCP plugin does not install them.

## Common rules

- Every route takes the project as query param `project_path` (absolute path of the project folder);
  the Solera workspace is `{project_path}/.noory/solera`. Missing/relative path → 400.
  A project with no `.noory/solera` yet: reads return an empty tree; the first write creates it.
- Errors: every JSON 4xx response is `{"error": "<Solera's message>", "code": "<code>"}`.
  Solera validation/order errors are 400; unknown item and parent ids are 404. Never 500 for a rule
  violation. `error` is English diagnostic text for agents and logs. Human-facing clients must select
  translated text by `code` instead of displaying or matching `error`.
- Item JSON = `WorkItem.model_dump()` (`id, level, status, gate, children, realizes, after, goal`).

### Error codes

`POST items` means `POST /api/work/items`. `PATCH item`, `move`, `add after`, and `remove after`
mean the four item routes listed in the route table. “All project HTTP routes” means every HTTP
route below except health; WebSocket failures still use close code 1008 and an English reason.

| Code | Status | Meaning | Routes |
|---|---:|---|---|
| `auth_required` | 401 | Authentication is enabled but no bearer token was supplied. | Every protected `/api/*` route |
| `invalid_auth_token` | 401 | The supplied bearer token does not match. | Every protected `/api/*` route |
| `project_path_required` | 400 | The `project_path` query parameter is missing or empty. | All project HTTP routes |
| `project_path_not_absolute` | 400 | `project_path` is not an absolute path. | All project HTTP routes |
| `invalid_request` | 400 | JSON is malformed, the body has the wrong shape/type or extra fields, or a patch names no field. | Body-taking routes |
| `unknown_work_item` | 404 | The item addressed by the route does not exist. | PATCH item, move, add after, remove after |
| `unknown_parent` | 404 | The requested create or move parent does not exist. | POST items, move |
| `unknown_predecessor` | 400 | An `after` link names an item that does not exist. | POST items, add after; also a move that exposes such an invalid graph |
| `blank_goal` | 400 | The requested goal is empty or whitespace-only. | POST items, PATCH item |
| `invalid_realizes_slug` | 400 | A `realizes` slug is empty or whitespace-only. | POST items, PATCH item |
| `duplicate_realizes_slug` | 400 | A `realizes` list contains the same slug more than once. | POST items, PATCH item |
| `invalid_name` | 400 | An id/name is not a safe single path component; for example, a level would create an unsafe id prefix. | POST items; any project route that encounters an unsafe stored name |
| `invalid_gate` | 400 | A supplied gate/check command contains only whitespace. | POST items |
| `invalid_order_link` | 400 | An `after` list contains a blank id or duplicate id. | POST items, add after |
| `parent_is_leaf` | 400 | The requested parent has a gate/check command and therefore cannot have children. | POST items, move |
| `order_cycle` | 400 | Order links form a direct or otherwise unclassified dependency cycle. | POST items, add after, move |
| `order_waits_on_ancestor` | 400 | An item waits for its own ancestor, whose completion depends on that item. | POST items, add after, move |
| `order_waits_on_descendant` | 400 | An item waits for its own descendant, which cannot start before that item. | POST items, add after, move |
| `move_under_self` | 400 | A move would put an item under itself. | move |
| `move_under_descendant` | 400 | A move would put an item under one of its descendants. | move |
| `root_index_not_supported` | 400 | A move to the root supplies an index, but root order is fixed by item id. | move |
| `index_out_of_range` | 400 | The destination sibling index is outside the accepted range. | move |
| `multiple_parents` | 400 | The source item already appears under more than one parent. | move |
| `workspace_lock_timeout` | 400 | A write could not acquire the workspace lock before its timeout. | POST items, PATCH item, move, add after, remove after |
| `invalid_format` | 400 | Stored Solera workspace data is malformed. | Any project route that reads the malformed data |
| `check_container` | 400 | The item has children; a container is done only when all its children are done. | check, uncheck |
| `check_blocked` | 400 | The item waits on order links or, in a workspace with an imported design, reaches no design node, so it cannot be checked yet. | check |
| `uncheck_gated` | 400 | The item has a gate; a gate's verdict is not undone by hand (reopen gated work with `repin`). | uncheck |
| `invalid` | 400 | Fallback for a rejection that has no more specific public code. | Any project route |

## Routes

| Method & path | Body (JSON) | Response |
|---|---|---|
| `GET /api/health` | — | `{"ok": true, "engine": "solera", "version": "<solera.__version__>"}` (no auth) |
| `GET /api/work` | — | `{"items": [Item...], "progress": {id: Completion}, "ready": [id...], "blocked": [{"id", "waiting_on": [id...], "reasons": [str...], "names_no_design_node": bool}], "current": id \| null}` |
| `POST /api/work/by-slugs` | `{"slugs": [str...]}` | `{"by_slug": {slug: [id...]}}` — every requested slug is a key (empty list when none); an item matches when its own `realizes` contains the slug |
| `POST /api/work/items` | `{"parent": id \| null, "goal": str, "level"?: str, "gate"?: str, "realizes"?: [str], "after"?: [id]}` | `201` Item. `parent: null` = new root (same as `plan`); otherwise same as `add` |
| `PATCH /api/work/items/{id}` | `{"goal"?: str, "realizes"?: [str]}` (at least one key) | Item |
| `POST /api/work/items/{id}/move` | `{"parent": id \| null, "index": int \| null}` | `{"items": [Item...]}` — every item the move rewrote |
| `POST /api/work/items/{id}/after` | `{"predecessor": id}` | Item (idempotent) |
| `DELETE /api/work/items/{id}/after/{predecessor}` | — | Item (idempotent) |
| `POST /api/work/items/{id}/check` | — | `{"item": Item, "gate": GateRun \| null}` — see "Checking an item" |
| `DELETE /api/work/items/{id}/check` | — | `{"item": Item}` — see "Checking an item" |
| `WS /ws?project_path=…&auth=…` | inbound ignored | pushes `{"event": "work_changed"}` (200 ms debounce) when anything under `.noory/solera/` changes (items, specs, progress) |

`Completion` = `dataclasses.asdict(graph.completion(...)[id])`.
`blocked` lists every `todo` item without children that cannot start or be checked now — gated leaves
and items without a gate. `ready` lists only gated leaves that can start now; it is the agent's list.
`blocked[].reasons` is English diagnostic text for agents and logs. Human-facing clients must derive
translated blocked text from `waiting_on` and `names_no_design_node` instead of displaying or matching
`reasons`.

## Checking an item

Decision: D-2026-10-02-D. Only this HTTP surface finishes an item that has no gate; no CLI command or
MCP tool does, and `next` never hands such an item to an agent.

`POST /api/work/items/{id}/check`, in one workspace lock:

1. Unknown id → 404 `unknown_work_item`. Item with children → 400 `check_container`.
2. Already `done` → 200, unchanged, no gate run.
3. A `todo` item must be able to start by the rules of `next`: every id in its own and its ancestors'
   `after` is `done`, and in a workspace with an imported design it or an ancestor has `realizes`.
   Otherwise → 400 `check_blocked`.
4. No gate → `done`, and ancestors whose children are all done roll up to `done`. `gate` is `null`.
5. Gate → the gate runs in the project folder. Pass → `done` + rollup, and the `progress.md` pointer
   is cleared when it named this item. Fail or timeout → status unchanged (a `doing` leaf stays
   `doing`). A failing gate is a 200 answer with `gate.passed: false`.

`GateRun` = `{"passed": bool, "exit_code": int | null, "timed_out": bool, "output": str}`; `output`
is the gate's stdout followed by its stderr, cut to the last 4000 characters.

`DELETE /api/work/items/{id}/check`: unknown id → 404 `unknown_work_item`; children → 400
`check_container`; a gate → 400 `uncheck_gated`; a `todo` item → 200 unchanged; a `done` item →
`todo`, and every ancestor that was `done` only because of it goes back to `todo`.
