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
- Item JSON = `WorkItem.model_dump()` (`id, level, status, gate, children, realizes, after, goal,
  accept, phase, phase_note, judgments, gate_passed`). `judgments` is the append-only list of
  `{"action", "reason", "at"}` a person's judgments left on the item. `status` is one of `todo`, `doing`,
  `review`, `rework`, `done`, `cancelled`; `accept` is `gate`, `children` or `person`; `phase` is
  `""`, `exploring` or `executing` ([SPEC.md](SPEC.md) §Who accepts a result). Clients must accept
  every listed status; a client that rejects an unknown status breaks as soon as a person judges a
  result.

`moved_at` is the item's last movement time in ISO-8601 UTC, or `""` for a legacy item that has not moved since tracking began. The `GET /api/work` item view also includes `needs_check`: true only for a `doing` or `rework` item with `moved_at` at least 7 days old and no cancelled ancestor; all other items report false. Repeating the same `phase` or `phase_note` through `PATCH` records a new movement.

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
| `check_container` | 400 | The item has children or `accept: children`; such an item is finished by its children, not by a check. | check, uncheck |
| `check_blocked` | 400 | The item waits on order links or, in a workspace with an imported design, reaches no design node, so it cannot be checked yet. | check |
| `check_conflict` | 400 | The item's status, gate or children changed while its gate ran; nothing was written. | check |
| `uncheck_gated` | 400 | The item has a gate; a gate's verdict is not undone by hand (reopen gated work with `repin`). | uncheck |
| `invalid_accept` | 400 | `accept` does not fit the item: `gate` without a gate, or `children` with a gate. | POST items, PATCH item |
| `accept_required` | 400 | An item without a gate was created without `accept` (`children` or `person`). | POST items |
| `accept_locked` | 400 | `accept` was changed on an item that is not `todo`, `doing` or `rework`. | PATCH item |
| `item_protected` | 400 | An edit or move touches an `accept: person` item that is `review` or `done`; the person must reject or reopen it first. | PATCH item, POST items, move |
| `check_cancelled` | 400 | The item is `cancelled` or lies under a cancelled item (a frozen subtree); nothing on it can change. | check, uncheck, PATCH item, POST items, move, accept, reject, reopen |
| `not_person` | 400 | Accept or reject was asked for an item whose `accept` is not `person`. | accept, reject |
| `invalid_phase` | 400 | `phase` is not `""`, `exploring` or `executing`. | PATCH item |
| `blank_reason` | 400 | A reject, reopen or cancel came without a non-blank `reason`. | reject, reopen, cancel |
| `not_in_review` | 400 | Accept or reject was asked for an item that is not in `review`. | accept, reject |
| `reopen_not_person` | 400 | Reopen was asked for an item whose `accept` is not `person` (a gate verdict is reopened only by `repin`). | reopen |
| `reopen_not_done` | 400 | Reopen was asked for an item that is not `done`. | reopen |
| `cancel_finished` | 400 | Cancel was asked for an item that is already `done` or `cancelled`. | cancel |
| `invalid_plan` | 400 | A planned tree is malformed: a blank or duplicate `key`, an `after_keys` entry that names no key in the request, or a blank string in `conditions`, `pass_examples`, `fail_examples`, `risks` or `basis`. | POST plans, PATCH item (blank strings) |
| `request_id_conflict` | 409 | A `request_id` that was already planned arrives with a different body. Nothing is written. | POST plans |
| `import_source_outside` | 400 | The import `source` does not resolve to a directory inside the request's project root. | POST imports |
| `invalid_release` | 400 | The import `source` is not a valid published service release (missing or malformed manifest, missing `based_on` snapshot, a symlink). | POST imports |
| `import_conflict` | 409 | A different bundle was already imported under the same label, or the same release identity has different content. Nothing is written. | POST imports |
| `invalid` | 400 | Fallback for a rejection that has no more specific public code. | Any project route |

## Routes

| Method & path | Body (JSON) | Response |
|---|---|---|
| `GET /api/health` | — | `{"ok": true, "engine": "solera", "version": "<solera.__version__>"}` (no auth) |
| `GET /api/work` | — | `{"items": [Item...], "progress": {id: Completion}, "ready": [id...], "blocked": [{"id", "waiting_on": [id...], "reasons": [str...], "names_no_design_node": bool}], "current": id \| null}` |
| `POST /api/work/by-slugs` | `{"slugs": [str...]}` | `{"by_slug": {slug: [id...]}}` — every requested slug is a key (empty list when none); an item matches when its own `realizes` contains the slug |
| `POST /api/work/items` | `{"parent": id \| null, "goal": str, "level"?: str, "gate"?: str, "realizes"?: [str], "after"?: [id], "accept"?: str}` (`accept` required when there is no `gate`) | `201` Item. `parent: null` = new root (same as `plan`); otherwise same as `add` |
| `POST /api/work/imports` | `{"source": str}` — see "Importing a release" | `201` `{"label": str, "release": str, "imported": true}`; the same release already imported under that label returns `200` with `"imported": false` |
| `POST /api/work/plans` | `{"request_id": str, "parent": id \| null, "items": [PlanNode...]}` — see "Planning a tree" | `201` `{"created": {key: id}, "items": [Item...]}`; a repeated `request_id` with the same body returns `200` with the recorded `created` and the current items |
| `PATCH /api/work/items/{id}` | `{"goal"?: str, "realizes"?: [str], "accept"?: str, "phase"?: str, "phase_note"?: str, "conditions"?: [str], "pass_examples"?: [str], "fail_examples"?: [str], "risks"?: [str]}` (at least one key) | Item. `accept` may change only while the item is `todo`, `doing` or `rework` (else `accept_locked`); it never finishes a leaf, and on a container the ordinary rollup then applies. A protected item rejects goal/realizes edits (`item_protected`) |
| `POST /api/work/items/{id}/accept` | — | `{"item": Item}` — see "Judging a result" |
| `POST /api/work/items/{id}/reject` | `{"reason": str}` | `{"item": Item}` |
| `POST /api/work/items/{id}/reopen` | `{"reason": str}` | `{"item": Item}` |
| `POST /api/work/items/{id}/cancel` | `{"reason": str}` | `{"item": Item}` |
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

## Importing a release

`POST /api/work/imports` imports one published format F service release, the same way the MCP `import_spec` tool
does ([SPEC.md](SPEC.md), format-f §6), so the app can link a workspace to its design (D-2026-10-09-B). `source` is the
path of a published `vS{N}` folder (`…/published/{service-slug}/vS{N}`); it must resolve to a directory inside the
request's `project_path`, else `import_source_outside`. The label is `{service-slug}-vS{N}`, taken from the folder
names. If that label already holds the same release (equal manifests), nothing is written and the response is `200`
with `"imported": false`; any other content under the label, or a release identity imported elsewhere with different
content, is `import_conflict` (409). A malformed bundle is `invalid_release`. The write takes the workspace lock and
emits `work_changed` once when something was imported. Once any release is imported, the design-connectedness rule
applies to the workspace ([SPEC.md](SPEC.md) §Design connectedness).

## Planning a tree

`POST /api/work/plans` creates a whole confirmed tree at once ([SPEC.md](SPEC.md) §Planning a tree at once,
D-2026-10-09-A). `parent: null` makes every top-level node a new root; otherwise they become children of that
existing item, appended in order. The tree is the single shape shared with Mashbill's work proposals (canvas-behavior
§Work, AI proposals); each package pins the example below in a test.

`PlanNode`:

| Key | Type | Rule |
|---|---|---|
| `key` | str | required; unique in the request; names this node for `after_keys` and in `created` |
| `goal` | str | required, not blank |
| `accept` | `"person"` \| `"children"` | required. `gate` is not accepted here (`invalid_request`, extra field) |
| `realizes` | [str] | optional; slugs, as for POST items |
| `conditions`, `pass_examples`, `fail_examples`, `risks`, `basis` | [str] | optional; no blank strings |
| `after_keys` | [str] | optional; keys of nodes in this request that must finish first |
| `after` | [id] | optional; existing item ids that must finish first |
| `children` | [PlanNode] | optional; a node with `accept: children` needs at least one child |

```json
{
  "request_id": "b8f0c1d2-3e4f-4a5b-8c6d-7e8f9a0b1c2d",
  "parent": null,
  "items": [
    {
      "key": "k1",
      "goal": "주문자가 가게 메뉴를 보고 주문한다",
      "accept": "children",
      "realizes": ["feature/order-food"],
      "basis": ["feature/order-food@vS2"],
      "conditions": ["메뉴를 고르면 주문 확인 화면에 같은 메뉴와 가격이 보인다"],
      "children": [
        {"key": "k2", "goal": "메뉴 목록을 보인다", "accept": "person",
         "pass_examples": ["메뉴가 열 개면 열 개가 다 보인다"]},
        {"key": "k3", "goal": "주문을 확정한다", "accept": "person", "after_keys": ["k2"],
         "fail_examples": ["품절 메뉴는 주문되지 않는다"], "risks": ["같은 주문이 두 번 들어간다"]}
      ]
    }
  ]
}
```

Response `201`: `{"created": {"k1": "<id>", "k2": "<id>", "k3": "<id>"}, "items": [Item...]}` — the created items in
`created` order. Ids follow the same rules as POST items. Validation errors use the same codes as POST items and move
(`unknown_parent`, `unknown_predecessor`, `parent_is_leaf`, `item_protected`, `check_cancelled`, `order_cycle`,
`order_waits_on_ancestor`, `order_waits_on_descendant`, `invalid_realizes_slug`, `duplicate_realizes_slug`) plus
`invalid_plan` and `request_id_conflict`. Any error writes nothing. Item responses on every route include the five
confirmed-in-plain-words fields (empty lists when unset).

## Checking an item

Decision: D-2026-10-02-D. Only this HTTP surface finishes an item that has no gate; no CLI command or
MCP tool does, and `next` never hands such an item to an agent.

`POST /api/work/items/{id}/check`, in one workspace lock:

1. Unknown id → 404 `unknown_work_item`. Item with children → 400 `check_container`.
2. Already `done` → 200, unchanged, no gate run.
3. A `cancelled` item → 400 `check_cancelled`. An item with `accept: children` → 400
   `check_container`. A startable item (`todo` or `rework`) must be able to start by the rules of
   `next`: every id in its own and its ancestors' `after` is `done`, and in a workspace with an imported
   design it or an ancestor has `realizes`. Otherwise → 400 `check_blocked`. A `review` item is finished
   by `accept`, not by check: checking it → 400 `check_blocked`, with an English message that names `accept`.
4. No gate → `done`, and ancestors whose children are all done roll up to `done`. `gate` is `null`.
5. Gate → the gate runs in the project folder, outside the workspace lock, so other writes go on
   while it runs. Afterwards, under the lock again: if the item's status, gate or children changed
   meanwhile → 400 `check_conflict` and nothing is written. Pass → `done` + rollup, and the
   `progress.md` pointer is cleared when it named this item. Fail or timeout → status unchanged (a
   `doing` leaf stays `doing`). A failing gate is a 200 answer with `gate.passed: false`.

`GateRun` = `{"passed": bool, "exit_code": int | null, "timed_out": bool, "output": str}`; `output`
is the gate's stdout followed by its stderr, cut to the last 4000 characters.

A check runs the gate as a subprocess of the engine. Like every write route, it is protected only by
the per-run token (`SOLERA_AUTH_TOKEN`); with no token set (development), any local caller can
trigger it.

`DELETE /api/work/items/{id}/check`: unknown id → 404 `unknown_work_item`; children → 400
`check_container`; a gate → 400 `uncheck_gated`; a `todo` item → 200 unchanged; a `done` item →
`todo`, and every ancestor that was `done` only because of it goes back to `todo`.

## Judging a result

Decisions: D-2026-10-04-A, D-2026-10-04-B. Only this HTTP surface judges a result; no CLI command or
MCP tool does ([SPEC.md](SPEC.md) §Who accepts a result). Each route runs in one workspace lock and
answers `{"item": Item}` with the judged item; every ancestor whose derived status changed is rewritten
in the same call.

Every judgment appends `{"action", "reason", "at"}` to the item's `judgments`.

- `POST .../accept`: unknown id → 404 `unknown_work_item`; `accept` not `person` → 400 `not_person`;
  status not `review` → 400 `not_in_review`. Otherwise `done`, and ancestors roll up.
- `POST .../reject` `{"reason"}`: blank reason → 400 `blank_reason`; `accept` not `person` → 400
  `not_person`; status not `review` → 400 `not_in_review`. Otherwise `rework`. A container in `rework`
  returns to `review` only when one of its children finishes after the rejection.
- `POST .../reopen` `{"reason"}`: blank reason → 400 `blank_reason`; `accept` not `person` → 400
  `reopen_not_person`; status not `done` → 400 `reopen_not_done`. Otherwise `rework`, and every ancestor
  that was `done` or `review` only because of it goes back to `todo` (a protected `done` ancestor stays).
  Use it when the accepted result never met its pass conditions; when it met them and broke later, keep
  the acceptance and create a new item instead.
- `POST .../cancel` `{"reason"}`: blank reason → 400 `blank_reason`; status `done` or `cancelled` →
  400 `cancel_finished`. Otherwise `cancelled`; the `progress.md` pointer is cleared when it names the
  item or anything under it; ancestors re-derive (a container whose other children are all finished may
  roll up). The cancelled subtree is frozen. Work waiting on the cancelled item through `after` stays
  blocked until the link is changed.
