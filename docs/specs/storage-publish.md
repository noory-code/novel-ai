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

## Storage principle — JSON is the SSOT

- A node's *graph data* (id/kind/position/label/refs/details_path) + *typed text* are all
  inline in `canvas.json`. **MD files = publish deliverables only** (not the work SSOT).
- The filesystem is the SSOT; the Novel UI is one editor on top of it.

## Publish (2-layer, explicit)

Publishing freezes a **bundle**, never a single node. There are exactly two publish acts, both explicit:

- **`vP` project snapshot** — the shared structure (foundation · actors · entities).
- **`vS` service release** — one service, pinned to the `vP` it is based on.

The model is §format F below; [`format-f.md`](./format-f.md) is the contract. Both write **files only**, under
`published/`: `_project/vP{N}/` for a `vP`, `{service-slug}/vS{N}/` for a `vS`. Each manifest records the
workspace git sha as a best-effort provenance stamp (empty string when there is no repo) — **neither publish
commits or tags**, and neither is blocked by the absence of a git repo.

`POST /api/projects/{id}/publish` is a **separate third act** and the only publish-named one that touches git:
it bumps `blueprint_version` and git-tags the workspace at that version (`D-2026-05-21-B`). It writes no
format F bundle. There is no "unchanged since the last publish" gate on it — every call bumps and tags.

- **git consent** applies to the acts that write git (the blueprint publish above, and tagging). Novel never
  auto `git init`: when the workspace root has no `.git` those endpoints answer `409 {needs_git_init: true}`
  → viewer modal → `POST /api/workspace/git-init`, which stages `.noory/novel/` only.
- **No Unpublish button** anywhere. Reverting is manual. A fresh `vP`/`vS` directory is not in git yet, so
  deleting it is enough — until the next blueprint publish or tag, whose `git add -A -- .noory/novel/` sweeps
  the whole data root (bundles included) into that commit. After that, `git revert`.

### Retired: per-node publish (`D-2026-06-22-H`, engine v0.108.0)

Selecting one node and publishing it on its own **no longer exists**. Retired with it: the per-node `version`
MAJOR bump, the `{canvas}/published/{kind}/{node_id}/v{MAJOR}.{MINOR}.md` layout, the dirty gate judged via
`_publish_baseline`, MINOR propagation up the ancestor chain, and the `…/nodes/{id}/published` history
endpoint. **There is no publish-eligibility list**, because no kind is individually publishable — a node is an
element *inside* a `vP`/`vS`, not its own release.

Two node fields outlive the mechanism because removing them is a wire-breaking schema regen: `version` and
`_publish_baseline` (`mashbill/models_kinds.py`). Nothing reads them — not `format_f.py`, not
`endpoints_publish.py`. Treat them as dead weight, not as state.

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
- **Gates:** bootstrap (reject a `vS` without a `vP`) + refs-integrity (reject a ref that does not resolve in `vP`).
- **Implementation:** mashbill `mashbill/format_f.py` (write) + Solera `intake.py` (read, with a
  `format_f_version` contract guard). **format F is the only publish model** — per-node publish was retired in
  engine v0.108.0 (`D-2026-06-22-H`), so the two no longer coexist.

## Schema parity (repository boundary)

- Mashbill's Pydantic models are the engine-side schema source.
- TypeScript and wire-contract files are generated explicitly and committed in the commercial app repository;
  the app does not import Mashbill by filesystem path.
- Mashbill tests pin its generated contract, and app-side tests pin the committed consumer artifact. A schema
  change updates and verifies both repositories in lock-step.
