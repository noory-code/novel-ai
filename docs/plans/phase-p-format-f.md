# Phase P — foundational design: the two-layer publication = format F (reconciling T5·T6·publish unit)

> Status: **draft (design proposal), v2 — reflects the mashbill-design-red-team adversarial review.** Not pinned (decision authority = the user).
> Once made canon, it moves into `docs/specs/storage-publish.md` + Mashbill [`DECISIONS.md`](../../plugins/mashbill/docs/DECISIONS.md) (D-id).
>
> Inputs: [`VISION`](../VISION.md) · the archived private pipeline record (historical context only) ·
> [`specs/storage-publish`](../specs/storage-publish.md) · [`specs/kinds-fields`](../specs/kinds-fields.md).
> For why v1→v2 changed, see §Adversarial-review summary at the very end.

---

## 0. Essence anchoring (Gate -1)

> **Novel is a collaboration tool where a person and AI together structure·define the essence and concepts of a
> service, so the AI works better on top of that and the person thinks faster and deeper.** (VISION)

This sentence determines the publish structure **directly**. VISION distinguishes two kinds:

- **Shared structure = "the essence and concepts"** — Foundation (mission·core value·identity) + Actors (roles) +
  Entities (concept map). **Project-wide, the ground the AI works on top of.** Several services stand on it together.
- **The realization on top = services·features** — what gets made *on the shared structure* in the Execution phase.

> **So publishing is fundamentally two-layer.** To hand a single service to an external agent, *that service's design*
> alone is not enough — *the shared structure it stands on* must be frozen together. Folding it to one layer (per-service)
> copies the shared elements (entities·actors·essence) into each service and **splits them** — an SSOT violation. (v1's
> fatal flaw, caught by adversarial review A2.)

---

## 1. Already decided (no re-discussion — 04-pipeline + A1, 2026-06-21 user)

Build on top of this. Phase P is not a new decision but a **concretization into format F + reconciliation with the old per-node spec**.

- **Publish unit = a service/feature bundle** — a coarse grouping + **stable ID slugs** for the inner elements + a fine-grained ID-diff.
- **The publication is frozen (immutable)** — vX = MD + version + git. Solera looks only at the publication and imports it into its own `specs/`.
- **Explicit versions only on the publication** — vX only on what is "pinned as a fixed contract externally". The Solera side uses git+tags only.
- **Connection = stable ID as a value** — `realizes: feature/login`, commit `[realizes feature/login@vX]`. R8: no importing each other.
- **Re-pin = human approval** — an ID-diff proposes what's stale → re-opened after human approval.

---

## 2. The two-layer publish model (foundational)

| Layer | What it freezes | Scope | Why (essence) |
|---|---|---|---|
| **Project snapshot `vP`** | Foundation (essence) + Actors (roles·relationships) + Entities (concept map) | project-wide | VISION's "shared structure" — the ground several services stand on |
| **Service release `vS`** | one service's 5 fields + the features under it + each Feature canvas (UX flow) + category position | 1 service | the Execution hand-off unit — what the external agent makes |

**Core rules:**

- **A service release `vS` pins the `vP` it stands on** (`based_on: _project/vP3`). And the shared elements it uses
  (entities·actors·essence) are **not copied but referenced by ID within that `vP`**.
- So when Solera imports a single `vS`, it is **self-contained** — the `vS` + the `vP` slice it points at come together.
  Entities never get copied per service and split (the A2 fix).
- **per-node publish is retired.** The act of publishing is *freezing a snapshot/release*, and a node is a particle
  within it (stable ID + content-hash). The old `storage-publish §publish` flow of node-select→📤→per-node MD+per-node
  version is **replaced by the vP/vS release flow** (the A4 migration is §6.D).

**Two-layer invariants (2nd adversarial review):**

- **Bootstrap — vP before vS.** A service release can only be published if its `based_on: vP` exists. The first
  publish either **cuts vP first** (recommended: on a vS publish, auto-cut a vP from the current shared structure, then
  put the vS on top of it) or the user explicitly issues a vP first. "vS publish without vP" is rejected.
- **`_project` reserved.** It collides with the snapshot directory `published/_project/`, so `_project` is forbidden as
  a service slug (rejected at the publish-eligibility gate).
- **revert integrity.** To revert a vP, no vS may pin it as `based_on` (if any do, clean up those vS first). A broken
  `based_on` is forbidden.
- **Skew made visible.** "Which service lags behind the current vP" is surfaced via status (immutable = normal, but the
  person needs to know when to re-pin). Tracking is the infrastructure's job (mashbill/Solera), not the person's.

---

## 3. The deliverable = what format F holds (T5)

The old value-expression mechanism the marathon retired (metric·injection edges·per-service exchange data) is not used.
Value is **re-sourced** (the surviving model in VISION/kinds-fields).

**Project snapshot `vP` (shared structure):**

| What it holds | Source canvas | Phase |
|---|---|---|
| Essence — mission + core value + identity (full text) | Foundation | Discovery/Retention |
| Actors — role hierarchy + give-and-take (role-level value) | Actors | Execution ground |
| Entities — the product's data-object concept map (no types/FKs) | Entities | Execution ground |

**Service release `vS` (realization unit):**

| What it holds | Source | Phase |
|---|---|---|
| Service value definition — 5 fields (why needed·what gets better + refs: actor·core_value·identity) | Services | Execution |
| Category position — reference to the parent category (if any) | Services | "position in the big picture" (VISION use #3, the A2 fix) |
| Features + each UX flow — feature `proposed` + Feature canvas (action→branch→result, action altitude) | Services/Feature | the Execution hand-off line |
| Refs — the entities/actors/essence this service uses = **IDs within the `vP`** | (points at vP) | Retention revisit |

> **The value story = derived, not stored separately.** "purpose+value+embodiment+flow" is a *view rendered* from the
> 5 fields + actor relationships + UX flow, not a hand-written deliverable (DRY/SSOT). format F holds the source, and the
> reading side assembles.

Each element's stable ID: `service/auth` `feature/login` `entity/post` `actor/user` `category/identity`
`mission` `core_value/trust` `identity/clear`.

---

## 4. Versioning — 2 axes (T6)

Current state (not unified): per-node `version` + `blueprint_version` + git tag. The foundational model = **2 semantic
axes + mechanism + derived**:

| Axis | Fate | Basis |
|---|---|---|
| **Project snapshot `vP`** | **semantic axis 1 — shared-structure release.** ← the true identity of the old `blueprint_version`. | Entities·actors·essence are project-scoped (shared) → they need their own release axis (A2/A7). |
| **Service release `vS`** | **semantic axis 2 — realization-unit release.** Pins the snapshot via `based_on: vP`. | The 04-pipeline publish unit = service/feature. An external contract. |
| **git tag** | **mechanism** — realizes vP·vS immutability (that sha = that version). | 04-pipeline "MD+version+git, frozen" / "git sha identity". |
| Element change (old per-node version) | **derived** — content-hash diff of element IDs within a release. Doesn't bump a number. | Re-pinning is ID-diff-based (§5). |

> v1 was "fold to one axis", which was **wrong** — the shared scope and the service scope are genuinely different.
> `blueprint_version` is not a duplicate but **the project-snapshot axis (vP)**. (Adversarial review A2/A7.)
>
> **Current code fit (confirmed):** `vP` is not something new to build — it is an **already-existing** mechanism.
> `POST /api/projects/{id}/publish` (`endpoints_publish.project_publish_endpoint`) bumps
> `ProjectDoc.blueprint_version` as semver and **makes a git tag with that version name** (a project-wide snapshot
> = vP). That is, **vP = a refinement of the existing blueprint_version/project-publish**, what is **newly added is the
> service layer (vS)**, and what is **retired is per-node publish** (node-select→📤→per-node MD+per-node `version`,
> `storage-publish §publish`). The git tag is the *mechanism* that freezes the whole tree, and the vP/vS manifests
> define *which bundle* it is (the two are orthogonal).

---

## 5. ID-diff — 3 kinds: changed·removed·added (the input to re-pinning)

On a re-publish (`vP+1` or `vS+1`), the manifest's `{id, hash}` list is compared against the old version:

| diff kind | What | Solera handling |
|---|---|---|
| `changed` | same ID, different hash | that ID's task is **stale → re-open** (human approval) |
| `removed` | ID gone (deleted, or slug moved by promotion) | that task is **orphaned → escalate** (not re-pin, the human decides) |
| `added` | new ID | new task candidate |

- **`vP+1` (shared-structure change) ripple:** only service releases that *reference* the changed `vP` element IDs are
  affected. Service work tied to untouched entities/actors is kept (almost no progress lost).
- **Renaming:** per 04-pipeline it's rare and handled explicitly then — it falls out as `removed` (old) + `added` (new)
  and the human joins them.
- v1 only handled `changed` (the A2/A3 fix).

---

## 6. format F skeleton (concrete — the INT-1 seed)

The neutral SSOT = `docs/specs/` (Korean canon). mashbill writes it and Solera reads it. Storage = 04-pipeline `published/`.

```
.noory/novel/published/
├── _project/vP{N}/                 ← project snapshot (shared structure, immutable)
│   ├── manifest.json
│   └── design/
│       ├── foundation.md           # mission·core value·identity
│       ├── actors.md               # role hierarchy + relationships
│       └── entities/{slug}.md      # concept map (one-line "what it holds")
│
└── {service-slug}/vS{N}/           ← service release (realization unit, immutable)
    ├── manifest.json               # based_on: _project/vP{N}
    └── design/
        ├── service.md              # 5 fields
        └── features/{slug}.md      # proposed + UX flow
```

**`_project/vP{N}/manifest.json`:**
```json
{
  "format_f_version": 1,
  "scope": "project",
  "release": "vP3",
  "git_sha": "<sha>",
  "elements": [
    { "id": "mission",            "kind": "mission",    "hash": "…" },
    { "id": "core_value/trust",   "kind": "core_value", "hash": "…" },
    { "id": "actor/user",         "kind": "actor",      "hash": "…" },
    { "id": "entity/post",        "kind": "entity",     "hash": "…" }
  ]
}
```

**`{service}/vS{N}/manifest.json`:**
```json
{
  "format_f_version": 1,
  "scope": "service",
  "service": "service/auth",
  "release": "vS2",
  "based_on": "_project/vP3",
  "git_sha": "<sha>",
  "category": "category/identity",
  "elements": [
    { "id": "service/auth",  "kind": "service", "hash": "…" },
    { "id": "feature/login", "kind": "feature", "hash": "…", "flow": true }
  ],
  "refs": {
    "anchors": { "mission": "mission", "core_values": ["core_value/trust"], "identity": ["identity/clear"] },
    "actors":   ["actor/user", "actor/operator"],
    "entities": ["entity/post", "entity/session"]
  }
}
```

- **`refs`** points at the shared elements *without copying*, by ID within the `based_on` snapshot (the heart of the A2 fix).
- **ID + hash** = the ID-diff input. **`format_f_version`** = the version of the contract format itself (the fundamental
  boundary insurance — the same grain as what the engine already does with `schema_version`).
- **The reverse direction (feedback·retrospective)** also uses the same ID vocabulary + `@vS`/`@vP`. Reflecting it into
  Novel is *the human as the bridge* (no automatic code import).
- **Solera import:** copy the `vS` into `specs/` but bring the referenced `vP` slice from `based_on` along, so it's
  self-contained (`realizes: feature/login@vS2`).

---

## 7. Decided (user 2026-06-22 — all recommendations accepted)

> **A = a single vP / B = service by default + feature as an exception / C = adopt the recommended gate (dirty+publish-eligibility+refs integrity)
> / D = a clean cut.** (User accepted 2026-06-22.) **The formal D-entries get pinned into `DECISIONS.md` at INT-implementation
> time** (§8) — until then **this doc is the design SSOT**. Below is the basis for each decision (preserved for reading).

**A. `vP` (project snapshot) granularity.** Freeze the whole shared structure as one vP (recommended) vs version
Foundation/Actors/Entities separately. *Recommended: a single vP* — the three are together "the ground", and there's no
external contract to pin them separately (not YAGNI, it's essence: the ground moves as one lump).

**B. Publish granularity: service vs feature.** If a feature becomes a multi-actor value exchange it's promoted to a
service (VISION) → is service-level publishing enough? *Recommended: service-level by default, allow `feature/...` in the
manifest `service` slot too (an exception for features that need an independent release before promotion).*

**C. dirty gate + publish eligibility + refs integrity (bundle level).** Re-assess the old per-node dirty·publish-eligibility
list (pre-marathon palette) against the new palette (add feature/note/entity, retire metric/content). *Recommended:*
- *release dirty = a hash change in ≥1 child element* + *≥1 publishable element exists* (block publishing an empty service, A3).
- **refs integrity gate (the new invariant the two layers create):** every `refs` ID (entity·actor·essence) of a service
  release `vS` must **resolve** within the `based_on` snapshot `vP` for publishing to be allowed. A `vS` that points at a
  missing shared element = dangling → publish rejected. (Applies the same spirit as the living canvas's dangling-edge
  read-healing `D-2026-06-21-X`, at the *publish write* boundary.)
- *Re-assessing publish eligibility is a separate plans task — no predictive assertion is made here.*

**D. Migration + rollback (A4).** The old per-node layout (`{project}/{canvas}/published/{kind}/{node_id}/v{M}.{m}.md`)
→ the new two-layer. *Recommended: check whether existing publications exist → if none, a clean cut (with 0 real data, cost
is 0); if any, a migration mapper or a user notice. Rollback = git revert (don't delete the vP/vS directories — storage-publish
"no Unpublish button").*

---

## 8. Next (once made canon)

1. **§7 A·B·C·D user decisions** → `DECISIONS.md` D-entries + update `storage-publish.md §publish/§versioning`.
2. **The formal format F spec** = the §6 skeleton as canon in `docs/specs/` (INT-1). A both-sides commit contract guard.
3. **The thinnest single strand** (INT-4): 1 small service + its vP → import → 1 Story·Action → execute → gate.

---

## Adversarial-review summary (mashbill-design-red-team, v1→v2)

- **🔴 A2 entity ownership (Critical):** v1 *copied* entities into the service bundle → split. VISION L100 + 1 entities
  canvas per project. **Fix: entities/actors/essence = the project snapshot vP, the service refs by ID only.**
- **🔴 A2/A7 two-layer scope (Critical):** shared elements are project-scoped, so a per-service single axis isn't
  self-contained. **Fix: vP + vS, 2 axes. `blueprint_version` = the true identity of vP (not retired).**
- **A2/A3 ID-diff removed (Major):** v1 handled changed only. **Fix: changed/removed/added, 3 kinds, removed=escalation.**
- **A2 category (Major):** the service's parent category was missing. **Fix: add `category` to the manifest.**
- **A4 migration·rollback (Major/Minor):** no back-out path. **Fix: §7.D.**
- **A3 empty service (Minor):** block 0 publishable elements. **Fix: the §7.C dirty gate.**
- **A8 big-bang (Major, procedural):** **Fix: the §8 sequence — the 2-axis decision first.**
