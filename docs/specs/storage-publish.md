# Storage · versioning · publish

> Canonical (design level). The publish contract for mashbill↔Solera is **format F** — see §format F below
> (resolves the old T5/T6 versioning question). Bundle layout and file rendering are pinned in
> [`format-f.md`](./format-f.md).
> Mashbill's [`PUBLISH.md`](../../plugins/mashbill/docs/PUBLISH.md) documents the **retired** per-node MD
> format; it is kept only so the files older projects still carry on disk stay readable.

## Storage layout (`.noory/`)

- A project sits **directly under** `.noory/novel/` (flat — `D-2026-06-21-AB`, the `{project_id}/` layer removed).
  `project.json` + per-canvas JSON: `foundation/canvas.json` · `actors/canvas.json` ·
  `services/canvas.json` · `entities/canvas.json` · per-feature detail. Each `canvas.json` has nodes +
  `edges[]` inline. (A legacy nested `{project_id}/` is lazily flattened on open — single project only.)
- The anchor position is outside `canvas.json` — `ProjectDoc.anchors[canvasKind]` (VO).
- **A workspace = a monorepo**, **a project = one service inside it**. Recursive discovery
  `/api/workspace/projects`.
- **one-project-per-dir (`D-2026-06-21-AA`):** a single `.noory/novel` root holds **only one** project.
  Two are not stacked at the same level — `create_project` rejects a second creation in a root that already
  has a project (`FileExistsError`→409, a viewer+MCP common chokepoint). With multiple services, split them into
  **sibling directories**, each with its own `.noory/novel` (`apps/web/.noory/novel/{id}` + `services/api/.noory/novel/{id}`).
  The guard sits on the *write* path only; `enumerate_projects`/`discover_projects` (read) still see N — existing
  multi-root and sibling-directory recursive discovery are unaffected.
- A legacy `.plot/` root is lazily migrated on first open (`.noory/novel` takes priority).
- Deleting a project moves `.noory/novel` (or the nested project folder) to the computer's trash and never erases it. A failed move leaves the project untouched and reports `trash_failed`.

## Storage principle — JSON is the SSOT

- A node's *graph data* (id/kind/position/label/refs/details_path) + *typed text* are all
  inline in `canvas.json`. **MD files = publish deliverables only** (not the work SSOT).
- The filesystem is the SSOT; the Novel UI is one editor on top of it.

## Publish (2-layer, explicit)

Publishing freezes a **bundle**, never a single node. There are exactly two publish acts, both explicit:

- **`vP` project snapshot** — the shared structure (foundation · actors · entities).
- **`vS` service release** — one service, pinned to the `vP` it is based on.

The model is §format F below; [`format-f.md`](./format-f.md) is the contract. Bundles live under
`published/`: `_project/vP{N}/` for a `vP`, `{service-slug}/vS{N}/` for a `vS`. A `vS` writes **files only**:
it neither commits nor tags, and is not blocked by the absence of a git repo. A `vP` is written only as part
of the blueprint publish below, which commits and tags it. Each manifest records the workspace git sha at
write time as a provenance stamp (empty string when there is no repo).

`POST /api/projects/{id}/publish` is the **blueprint publish** (`D-2026-05-21-B`, `D-2026-10-01-E`): one
request that writes the `vP` bundle, bumps `blueprint_version` and git-tags the workspace at that version,
all or nothing. Before writing anything it checks that the blueprint changed and that the new version's tag
does not exist yet. It then writes the `vP` bundle (its manifest carries the new `blueprint_version`), bumps
the version, and commits and tags, so the bundle is inside the tagged commit. If any step fails, the bundle
is removed, the version is restored and nothing is tagged. It publishes only when the blueprint changed
(`D-2026-09-28-B`): the
design content of the canvas files under `foundation/`, `actors/`, `services/` (feature details included) and
`entities/` differs from the same files in the commit the current `blueprint_version` tag points at. The
current side is read from the files on disk, so a canvas the user keeps out of git still counts; a file on
only one side is a change. Presentation is not content: node `x`, `y`, `width`, `height`, `color`, `shape`,
`icon`, `collapsed` and edge `sourceHandle`, `targetHandle`, `style` are dropped before comparing, and nodes
and edges are matched by id, so moving, resizing, recolouring or reordering alone is not a change. Every
other field counts. Chat, `project.json`, publish bundles, `schema/` and provider state are not compared.
With no such tag (first publish, or the tag was removed) the blueprint counts as changed. Each blueprint tag
message ends with a `Novel-Blueprint-Content: sha256:<hex>` trailer — the SHA-256 of that normalized
content — and the check compares against it first, so a data root the user keeps out of git still has a
baseline. A tag without the trailer (made before the trailer existed, or by hand) falls back to comparing
the files in its commit. An unchanged call answers
`409 {unchanged: true}` and writes nothing. `GET /api/projects/{id}/publish/status` answers
`{current_version, changed}` without writing; with no git repo it answers `changed: true`, and the git-consent
gate stays on the publish call itself.

**In the app this is one action.** The `📤 설계도 발행` button calls `/publish` once, under a single
git-consent prompt (`viewer` `useProject.ts` `publishBlueprint`). Only `vS` is triggered on its own. The MCP
tool `publish_project_snapshot_tool` runs the same blueprint publish and requires a `bump`. Publishing is the
person's act — the app's confirm dialog, or a host CLI's tool approval — so the in-app coach is not given
`publish_project_snapshot_tool` or `publish_service_tool` (`D-2026-10-01-E`). When a node published for the
first time needs an English slug (format F §1 invariant 3), the app first calls
`POST /api/projects/{id}/publish/slug-proposals`, shows the AI proposals for the person to confirm or edit, and
passes the result as `slugs` with the publish; both MCP publish tools take the same `slugs` (`D-2026-10-01-F`).

- **git consent** applies to the acts that write git (the blueprint publish above, and tagging). Novel never
  auto `git init`: when the workspace root has no `.git` those endpoints answer `409 {needs_git_init: true}`
  → viewer modal → `POST /api/workspace/git-init`, which stages `.noory/novel/` only. The blueprint publish
  writes git, so this prompt precedes every `vP`.
- **No Unpublish button** anywhere. Reverting is manual. A `vP` is committed with its version tag, so it is
  reverted in git. A fresh `vS` directory is not in git yet, so deleting it is enough — until the next
  blueprint publish or tag, whose `git add -A -- .noory/novel/` sweeps
  the whole data root (bundles included) into that commit. After that, `git revert`. The blueprint confirm
  dialog says so before the user confirms: a published version can't be deleted in the app (`D-2026-09-28-B`).
  To keep that true, a blueprint version tag — a name of the form `v<MAJOR>.<MINOR>.<PATCH>` — cannot be
  deleted through Novel: `git_store.delete_tag` refuses it (HTTP `409 {published_version: true}`, MCP
  `delete_project_tag` raises), and the sidebar shows no delete button on it. Session tags with other names
  are still deletable. Deleting a version tag would also remove the baseline the change check compares against.
  The same names are reserved for the blueprint publish: a session tag (HTTP tag endpoint, MCP `tag_project`,
  both through `git_store.tag_session`) named `v<MAJOR>.<MINOR>.<PATCH>` is refused before any git write
  (HTTP `409 {reserved_version_name: true}`), so no session tag can pose as a version baseline or collide with
  the next version's tag.
- **Empty parts are named, not blocked** (`DE-00000012`). A bundle is what an external agent reads as the
  frozen truth, so publishing one with nothing in it is worth surfacing — but keeping an intermediate
  snapshot mid-design is legitimate, so the app does not refuse. The confirm dialog lists which of the five
  `vP` slots are empty (mission / core values / identity / actors / entities) and publishes on an
  explicit yes. A foundation slot counts as empty when the published section would carry nothing but its
  heading: both the kind's primary field and `body` blank. The counting lives in `viewer`
  `src/domain/publishGaps.ts`, mirroring `format_f.py`'s `_FOUNDATION_PRIMARY`.

### Retired: per-node publish (`D-2026-06-22-H`, engine v0.108.0)

Selecting one node and publishing it on its own **no longer exists**. Retired with it: the per-node `version`
MAJOR bump, the `{canvas}/published/{kind}/{node_id}/v{MAJOR}.{MINOR}.md` layout, the dirty gate judged via
`_publish_baseline`, MINOR propagation up the ancestor chain, and the `…/nodes/{id}/published` history
endpoint. **There is no publish-eligibility list**, because no kind is individually publishable — a node is an
element *inside* a `vP`/`vS`, not its own release.

Two node fields outlive the mechanism because removing them is a wire-breaking schema regen: `version` and
`_publish_baseline` (`mashbill/models_kinds.py`). **Nothing interprets either one** — no publish path reads
them, so neither affects any behaviour. `_publish_baseline` is still *carried*: `canvas_io.py` copies a
non-`None` on-disk baseline forward across a PUT, so a viewer write does not clobber it. That is preservation,
not use. Treat both fields as inert payload, not as state.

Legacy publish **files** on disk are still migrated in place on read (`canvas_io.py` — flat → `{kind}/{slug}/`
→ `{kind}/{node_id}/`). That migration keeps old artifacts readable; it does not mean per-node publish runs.

## format F — 2-layer publish bundle (resolves T5·T6, `D-2026-06-22-D`)

> **Canonical = [`format-f.md`](./format-f.md)** (the contract) + [`../plans/phase-p-format-f.md`](../plans/phase-p-format-f.md) (foundational design, two design-review passes). Summary only here.

The mashbill↔Solera publish contract is a **2-layer frozen bundle ("format F")**:

- **`vP` project snapshot** — freezes the shared structure (essence·Actors·Entities) into `published/_project/vP{N}/`.
- **`vS` service release** — freezes one service (5 cells + features + category) into `published/{slug}/vS{N}/`,
  pins `based_on: vP`, and **references shared elements by slug (not copied)**.
- **T5 (deliverable) resolved:** the deliverable = this bundle. The value story is *derived* from the 5 cells +
  actor relations + UX flow (not stored separately). The old expression mechanisms (metric·injection·*_ref) are unused.
- **T6 (versioning) resolved:** 2 semantic axes (vP·vS) + git tag (the mechanism) + content-hash **ID-diff**
  (changed/removed/added, derived). **The per-node `version` number axis is retired** (format F does not use it).
  `blueprint_version` = the identity of vP.
- **Gates:** bootstrap (reject a `vS` without a `vP`) + refs-integrity (reject a ref that does not resolve in `vP`) + English ids (reject a publish until every node published for the first time whose name has letters outside ASCII has a person-confirmed English id; nothing is written before this check).
- **Implementation:** mashbill `mashbill/format_f.py` (write) + Solera `intake.py` (read, with a
  `format_f_version` contract guard). **format F is the only publish model** — per-node publish was retired in
  engine v0.108.0 (`D-2026-06-22-H`), so the two no longer coexist.

## Schema parity (repository boundary)

- Mashbill's Pydantic models are the engine-side schema source.
- TypeScript and wire-contract files are generated explicitly and committed in the commercial app repository;
  the app does not import Mashbill by filesystem path.
- Mashbill tests pin its generated contract, and app-side tests pin the committed consumer artifact. A schema
  change updates and verifies both repositories in lock-step.
