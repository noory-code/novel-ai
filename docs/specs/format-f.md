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
    ├── manifest.json             # based_on: vP{N} (the snapshot at _project/vP{N}/)
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
  "blueprint_version": "v0.4.0",
  "git_sha": "<workspace git sha at publish time>",
  "elements": [
    { "id": "mission",          "kind": "mission",     "hash": "<first 16 hex of sha256(design payload)>" },
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
  "based_on": "vP3",
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
- `blueprint_version` (project only) — the project's blueprint version this `vP` was published as; the
  blueprint publish tags the commit that contains the bundle with this version, and that tag is the anchor
  of immutability. `vP{N}` and `blueprint_version` count separately.
- `git_sha` — the workspace git sha when the bundle was written (the commit before the tagged one for a `vP`).
- `based_on` (service only) — the referenced project snapshot's `release`, a bare `vP{N}` (e.g. `vP3`). The
  snapshot itself sits at `_project/vP{N}/`.
- `category` (service, optional) — the parent category ID (omitted if none — a root service).
- `elements[]` — the elements this release *owns*. `{id, label, kind, hash}` (+ a feature carries `flow: true`).
  `label` is the node's name at publish time. The id is a slug frozen at first publish and can be
  opaque (a non-ASCII label slugs to `x`, `x-2`, …), so readers match ids to names through `label`.
  Wherever a rendered design file cites another element it writes the name followed by the id,
  e.g. 본질 (`core_value/x`).
  `hash` = the first 16 hex characters of the sha256 of that element's design payload (the ID-diff input).
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
**무엇을 할 수 있나:** a user opens a session with credentials.

## UX 흐름 (action 고도)

참여자: user

### 흐름
1. enter credentials
   - 다음 → 2. (분기) credentials valid?
2. (분기) credentials valid?
   - success → 3. create session
   - failure → 1. enter credentials
3. create session

### 규칙
- lock after five failures (걸린 단계: 2)
```

The rendered labels and section headings are Korean (`**무엇을 할 수 있나:**`, `## UX 흐름 (action 고도)`, `참여자:`,
`### 흐름`, `### 규칙`, `### 참고 (ambient)`); node labels are the user's own text. The flow body follows these rules:

- **`### 흐름` keeps the drawn order.** Every `step` and `decision` node gets a number in the
  first-visit order of a depth-first walk along the canvas edges, starting from the edges that
  leave the actor. Steps no edge reaches are appended after the walk, so none is lost. A
  decision is prefixed `(분기)`.
- **A step's or decision's body follows its numbered line**, before its edges, one `   > {line}` per
  body line (`   >` for a blank line), so the design prose written on the node reaches the external
  agent. A node with an empty body adds no line. Edge targets repeat only the name, never the body.
- **Every edge between steps and decisions is written** under its source, as
  `- {edge label, or 다음} → {n}. {target}`. A loop points back to the earlier number. Two steps
  with the same text stay distinguishable by number.
- **`### 규칙` lists the flow's rule nodes**: the label, then the policy (or body) when present,
  then the numbers of the steps each rule is attached to. Rules are constraints the external
  agent must honour while realising the feature.
- Ambient notes follow under `### 참고 (ambient)`. A feature with no steps or decisions renders
  `_아직 흐름이 그려지지 않음._`.

`hash` is computed from the element's design fields (`kind|label|<its typed content fields>`), not from the
rendered file, so a rendering change does not change it. A service's `refs` are not part of its hash; re-pin
compares `refs` separately.

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
  pinned to untouched shared elements is kept. A referenced vP element that is removed, or a change in the service's
  `refs`, also marks that service's work stale; an ID that was removed and then re-added is escalated.
- **Adjacent releases only:** re-pin compares `vS{N}` with `vS{N+1}` of the same service. To cross several
  releases, import each one and compare step by step.
- **re-pin = human approval** (the deterministic ID-diff script *proposes* with a `proposal_id`; the human approves
  that id; apply recalculates and reopens only if the proposal is unchanged).

---

## 6. Solera-side contract (read) — summary

- **import** = copy `vS` + its `based_on` vP slice into `solera/specs/{label}/` (immutable→immutable), through a
  temporary folder so a failed import leaves nothing. Solera validates both manifests before copying: the
  `format_f_version`; `scope`; `release` and `based_on` as bare `vS{N}` / `vP{N}` names (the snapshot at
  `_project/{based_on}/` beside the service bundle, whose `release` must equal `based_on`); required `elements`
  with unique ids (a service's include the service itself) and required `refs`. It rejects symlinks and a label
  that is not a single safe path name, and refuses a second import of the same release with different content.
  It does not verify `git_sha` or recompute hashes. `story.md` carries `source: specs/{label}` (points only inside its own folder).
- **link** = a work item's `realizes: feature/login`, the result commit `[realizes feature/login@vS2]`. Bidirectional
  tracing by ID matching, no import.
- **reverse direction (feedback·retrospective)** = `feedback/{id}.md` (`about: feature/login@vS2`) · `RETROSPECTIVE.md`
  (ID tags). Reflecting into Novel goes *through the human as the bridge* (no automatic code import).

---

## 7. Both-sides committed contract guard (INT-1c)

The format F schema crosses the boundary the same way the wire contract does — **a committed schema artifact, not a
live import**. mashbill (write)·Solera (read) each pin this spec's **version + required field set** in their own tests,
and fail if `format_f_version` diverges (a drift guard). The exact guard wiring is in INT-1c.
