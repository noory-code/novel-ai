# Storage · versioning · publish

> Canonical (design level). Publish MD format detail = Mashbill [`PUBLISH.md`](../../mashbill/docs/PUBLISH.md).
> The publish contract for mashbill↔Solera is **format F** — see §format F below (resolves the old T5/T6 versioning question).

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

## Publish (per-node, explicit)

Select node → inspector 📤 → confirm. An atomic 3 effects:
1. **per-node `version` MAJOR bump** (`v1.0 → v2.0`).
2. **MD file creation** = `{project}/{canvas}/published/{kind}/{node_id}/v{MAJOR}.{MINOR}.md`.
3. **git commit** (subject `publish: {kind} "{label}" → {version}` + `Publish-*:` trailer;
   on ancestor propagation, adds `Publish-Propagated-Ancestor:`).

- **dirty gate:** there must be ≥1 content change since the last publish (typed text·label·body·touched edge;
  visual x/y/w/h/color etc. are not dirty) for publish to be possible. Judged via `_publish_baseline`.
- **MINOR propagation:** on a descendant publish, bump only the ancestor's `version` MINOR (no new MD made).
- **git consent:** Novel never auto `git init`. On the first publish/tag, if there is no `.git`,
  `{needs_git_init: true}` → viewer modal → `POST /api/workspace/git-init`. Stages `.noory/novel/` only.
- **Publish history:** `GET …/nodes/{id}/published` → version list. No Unpublish button (manual `git revert`).

> **Publish-eligibility list needs reconciliation:** the old list (visible: mission/core_value/identity/actor/service/
> category/**metric**/step/rule/**content**) is **pre-marathon** — metric/content retired, feature/
> note/entity added; must be re-derived against the new palette (plans/). No predictive assertion made.

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
- **Implementation (INT, walking skeleton):** mashbill `mashbill/format_f.py` (write) + Solera `intake.py` (read, with a
  `format_f_version` contract guard). **Coexists with the existing per-node publish** — retirement is a follow-on migration.

> ⚠ The "## Publish (per-node, explicit)" section above is the **current code (pre-transition)**. format F is the new
> contract, and the two coexist until per-node is retired.

## Schema parity (cross-repo caution)

- The wire-schema guard = `plot/tests/test_schema_parity.py` (Pydantic ↔ TS `types.ts`).
- **Works only inside the current monorepo** — before `viewer/` leaves `noory-ai/`, `types.ts` must be
  switched to a `schema_export.py` generated artifact so the guard doesn't die (a precondition for repo separation).
