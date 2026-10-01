# Solera HTTP contract (v1)

Decision: D-2026-10-02-A (public `novel-ai/plugins/mashbill/docs/DECISIONS.md`). Solera runs as its own
engine; Mashbill never calls it; the app asks both engines and joins the answers.

## Process

- Entry: console script `solera-http` → `solera.server:run_http_only()`. Host fixed `127.0.0.1`.
- Port: env `SOLERA_PORT`, default `5191` (invalid value → 5191, like Mashbill's `MASHBILL_PORT`).
- Auth: env `SOLERA_AUTH_TOKEN`, read on every request. Unset → no auth (dev). Set → every `/api/*` path
  except `GET /api/health` needs `Authorization: Bearer <token>` (scheme case-insensitive,
  `hmac.compare_digest`); failure → 401 `{"error": "auth token required" | "invalid auth token"}`.
  WebSocket takes the token as query param `auth`; failure closes with code 1008.
- CORS: `allow_origins=["*"]`, all methods, all headers (the bundled front end is cross-origin `tauri://`).
- HTTP dependencies live in an optional extra `http` (starlette, uvicorn[standard], watchdog), so the
  standalone MCP plugin does not install them.

## Common rules

- Every route takes the project as query param `project_path` (absolute path of the project folder);
  the Solera workspace is `{project_path}/.noory/solera`. Missing/relative path → 400.
  A project with no `.noory/solera` yet: reads return an empty tree; the first write creates it.
- Errors: Solera validation/order errors → 400 `{"error": "<Solera's message>"}`; unknown item id → 404
  `{"error": "unknown work item: <id>"}`. Never 500 for a rule violation.
- Item JSON = `WorkItem.model_dump()` (`id, level, status, gate, children, realizes, after, goal`).

## Routes

| Method & path | Body (JSON) | Response |
|---|---|---|
| `GET /api/health` | — | `{"ok": true, "engine": "solera", "version": "<solera.__version__>"}` (no auth) |
| `GET /api/work` | — | `{"items": [Item...], "progress": {id: Completion}, "ready": [id...], "blocked": [{"id", "waiting_on": [id...], "reasons": [str...]}], "current": id \| null}` |
| `POST /api/work/by-slugs` | `{"slugs": [str...]}` | `{"by_slug": {slug: [id...]}}` — every requested slug is a key (empty list when none); an item matches when its own `realizes` contains the slug |
| `POST /api/work/items` | `{"parent": id \| null, "goal": str, "level"?: str, "gate"?: str, "realizes"?: [str], "after"?: [id]}` | `201` Item. `parent: null` = new root (same as `plan`); otherwise same as `add` |
| `PATCH /api/work/items/{id}` | `{"goal"?: str, "realizes"?: [str]}` (at least one key) | Item |
| `POST /api/work/items/{id}/move` | `{"parent": id \| null, "index": int \| null}` | `{"items": [Item...]}` — every item the move rewrote |
| `POST /api/work/items/{id}/after` | `{"predecessor": id}` | Item (idempotent) |
| `DELETE /api/work/items/{id}/after/{predecessor}` | — | Item (idempotent) |
| `WS /ws?project_path=…&auth=…` | inbound ignored | pushes `{"event": "work_changed"}` (200 ms debounce) when anything under `.noory/solera/` changes (items, specs, progress) |

`Completion` = `dataclasses.asdict(graph.completion(...)[id])`.
Completing an item over HTTP is not offered yet.
