# format F — publish-bundle contract (mashbill ↔ Solera neutral SSOT)

> Canonical (contract level). **mashbill writes it, Solera reads it.** Neither side's code —
> a neutral zone. The definition lives in this one place; each side implements
> independently (R8 — no mutual import / path reference).
>
> Foundational design = [`plans/phase-p-format-f.md`](../plans/phase-p-format-f.md) (the 2-layer model, two design reviews).
> The private pipeline record that preceded this contract is historical context, not a public dependency.
> Storage plane = [`storage-publish.md`](./storage-publish.md).

---

## 0. One sentence

format F is the **directory + manifest format of a frozen design publish-bundle**. It splits into two scopes —
the project snapshot (`vP`: essence·actors·entities = shared structure) and the service release (`vS`: one service's
realization design, referencing `vP`). Solera imports `vS` + the `vP` slice it points to, and breaks it into work items.

---

## 1. Invariants (the implementation must hold these)

1. **Immutable.** A published `vP{N}`/`vS{N}` directory must *never* be edited in place. To change it,
   re-publish (`+1`). Rollback = git revert (do not delete the directory).
2. **Independent.** mashbill·Solera do not import / path-reference each other. The link is format F + the stable ID *value* only.
3. **Stable ID = slug.** `service/auth` · `feature/login` · `entity/post` · `actor/user` ·
   `category/identity` · `mission` · `core_value/{slug}` · `identity/{slug}`. Renames are rare and
   handled explicitly then (= `removed` old + `added` new).
4. **refs integrity.** Every reference ID in `vS` must resolve inside its `based_on` snapshot `vP`.
   If it does not (dangling) → **reject the publish** (write-boundary gate).
5. **Bootstrap.** A `vS` publish requires its `based_on` `vP` to exist. The first publish cuts a
   `vP` from the current shared structure first, then lays `vS` on top of it. No "vS without vP".
6. **`_project` reserved.** A service slug must not be `_project` (collides with the snapshot directory).
7. **revert integrity.** A `vP` revert is allowed only when no `vS` pins it as `based_on`.

---

## 2. Storage layout

```
.noory/novel/published/
├── _project/vP{N}/
│   ├── manifest.json
│   └── design/
│       ├── foundation.md         # mission + core_values[] + identities[]
│       ├── actors.md             # role hierarchy + relations (give/receive)
│       └── entities/{slug}.md    # concept map (one-line "what it holds")
│
└── {service-slug}/vS{N}/
    ├── manifest.json             # based_on: _project/vP{N}
    └── design/
        ├── service.md            # 5 cells (value definition)
        └── features/{slug}.md    # proposed + UX flow (action → branch → result)
```

`{service-slug}` is the slug part of the service's stable ID (e.g. `service/auth` → `auth/`).

---

## 3. Manifest schema

### 3.1 Project snapshot — `_project/vP{N}/manifest.json`

```json
{
  "format_f_version": 1,
  "scope": "project",
  "release": "vP3",
  "git_sha": "<workspace git sha at publish time>",
  "elements": [
    { "id": "mission",          "kind": "mission",     "hash": "<sha256 of design payload>" },
    { "id": "core_value/trust", "kind": "core_value",  "hash": "…" },
    { "id": "identity/clear",   "kind": "identity",     "hash": "…" },
    { "id": "actor/user",       "kind": "actor",        "hash": "…" },
    { "id": "entity/post",      "kind": "entity",       "hash": "…" }
  ]
}
```

### 3.2 Service release — `{service}/vS{N}/manifest.json`

```json
{
  "format_f_version": 1,
  "scope": "service",
  "service": "service/auth",
  "release": "vS2",
  "based_on": "_project/vP3",
  "git_sha": "…",
  "category": "category/identity",
  "elements": [
    { "id": "service/auth",  "kind": "service", "hash": "…" },
    { "id": "feature/login", "kind": "feature", "hash": "…", "flow": true }
  ],
  "refs": {
    "anchors":  { "mission": "mission", "core_values": ["core_value/trust"], "identity": ["identity/clear"] },
    "actors":   ["actor/user", "actor/operator"],
    "entities": ["entity/post", "entity/session"]
  }
}
```

**Field rules:**
- `format_f_version` (int) — the contract format version. +1 on an incompatible change.
- `scope` — `"project"` | `"service"`.
- `release` — `vP{N}` or `vS{N}` (N = a monotonically increasing integer).
- `git_sha` — the workspace git sha at publish time (the anchor of immutability).
- `based_on` (service only) — the referenced project snapshot's `release`.
- `category` (service, optional) — the parent category ID (omitted if none — a root service).
- `elements[]` — the elements this release *owns*. `{id, kind, hash}` (+ a feature carries `flow: true`).
  `hash` = the sha256 of that element's design payload (the ID-diff input).
- `refs` (service only) — the shared-element IDs inside the `based_on` vP that this service *references* (not copied).
  `anchors.mission` **always** points to that project's single mission (`"mission"`) — the mission is
  the project's essence and every service stands on it (VISION), so when the mission changes (`vP+1`) that change
  must propagate to *every* service (refs = the propagation surface). `core_values`/`identity` carry only what the
  service *chose* (per-service `ref_*_ids`), but the mission is singular so it is anchored universally.
  (`D-2026-06-23-D`.)

---

## 4. design/ MD format

Each `*.md` = frontmatter (`id`/`kind`) + body (the design prose a person·agent reads). The body is *rendered*
from the live canvas's typed fields, and **the value story is not stored separately but derived from the 5 cells +
actor relations + UX flow** (DRY/SSOT). Example `features/login.md`:

```markdown
---
id: feature/login
kind: feature
---
# Login
**What it lets you do:** a user opens a session with credentials.

## UX flow (action altitude)
- [user] enter credentials → validation branch (success/failure) → success: create session / failure: retry
```

`hash` is computed from this design payload (normalized body excluding frontmatter + that element's manifest meta).

---

## 5. Versioning + ID-diff

- **2 semantic axes:** `vP` (shared structure) + `vS` (service). **the git tag is the mechanism** (that sha = that version).
  No per-node version number — element changes are *derived* (below).
- **re-publish diff:** compare the new release manifest's `{id, hash}` list against the immediately prior version → 3 kinds:

  | diff | meaning | Solera handling |
  |---|---|---|
  | `changed` | same ID, different hash | that ID's work item is stale → reopen (human approval) |
  | `removed` | ID gone | that work item is orphaned → **escalate** (not a re-pin) |
  | `added` | new ID | a new work-item candidate |

- **`vP+1` blast radius:** only the `vS` that *references* the changed vP element ID is affected (refs matching). Work
  pinned to untouched shared elements is kept.
- **re-pin = human approval** (the deterministic ID-diff script *proposes*, the human approves, then reopen).

---

## 6. Solera-side contract (read) — summary

- **import** = copy `vS` + its `based_on` vP slice into `solera/specs/{label}/` (immutable→immutable,
  with git-sha identity verification). `story.md` carries `source: specs/{label}` (points only inside its own folder).
- **link** = a work item's `realizes: feature/login`, the result commit `[realizes feature/login@vS2]`. Bidirectional
  tracing by ID matching, no import.
- **reverse direction (feedback·retrospective)** = `feedback/{id}.md` (`about: feature/login@vS2`) · `RETROSPECTIVE.md`
  (ID tags). Reflecting into Novel goes *through the human as the bridge* (no automatic code import). Detail = 04-pipeline.

---

## 7. Both-sides committed contract guard (INT-1c)

The format F schema crosses the boundary the same way the wire contract does — **a committed schema artifact, not a
live import**. mashbill (write)·Solera (read) each pin this spec's **version + required field set** in their own tests,
and fail if `format_f_version` diverges (a drift guard). The exact guard wiring is in INT-1c.
