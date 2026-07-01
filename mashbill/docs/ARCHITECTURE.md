# ARCHITECTURE — current shape + split plan

> **Purpose:** make the structural state of the Novel viewer explicit
> so the next architectural change isn't a guess. Pairs with
> [`SPEC.md`](./SPEC.md) (behaviour) and
> [`DECISIONS.md`](./DECISIONS.md) (history).
>
> **Scope today:** viewer (`plot/viewer/src/`). The MCP server
> (`mashbill/mashbill/`) already follows the noory-ai monorepo's Tool/Core
> separation and is not the bottleneck.

---

## Post-v0.15 shape (Domain layer + per-kind components)

> **Status (v0.16.0 / 2026-05-12):** the v0.15 structural reset
> (D-2026-05-12-B → -G) reshaped the viewer end-to-end. This section
> documents what the code *actually looks like now*. The legacy
> "Current shape" section below is preserved for historical context
> (pre-reset) but its LOC numbers and split-candidate analysis no
> longer reflect reality — read this section first.

### Layers (dependency direction = outer ← inner)

```
viewer/src/
  domain/                       — pure entity layer. No React, no UI.
    BaseFields.ts                 - shared graph fields (id / label / x / y / …)
    DomainParseError.ts           - Fail-Fast exception thrown by fromJson
    {Mission,CoreValue,…,Project}.ts × 15
                                  - per-kind entity class
                                    • static fromJson(raw): Class
                                    • toJson(): { …json shape }
                                    • invariants inline in fromJson
                                  - composition over inheritance: each class
                                    uses parseBaseFields(raw) helper, not a
                                    Base class. No methods beyond fromJson /
                                    toJson — safe to spread.
    SketchNode.ts                 - 15-way discriminated union
                                    (export type SketchNode = Mission | … )
    parseEntity.ts                - kind-discriminator dispatcher; throws
                                    DomainParseError on unknown kind
    createBlankNode.ts            - per-kind factory using the entity classes
                                    (the only legitimate switch(kind) in the
                                    viewer)
    Canvas.ts                     - Canvas-level domain object

  canvases/                     — UI layer.
    nodes/
      BaseNode.tsx                - chrome SSOT: NodeResizer + 4 Handles +
                                    kind-tag + MD-warning badge + shape clip
      {kind}/index.tsx × 15       - wraps BaseNode with per-kind chrome
                                    flags + body override
      registry.ts                 - NodeKind → component map (size 15,
                                    runtime-asserted)

    inspectors/
      BaseInspector.tsx           - chrome SSOT: header + label + delete +
                                    close + details-section slot
      KindInspector.tsx           - resolver: looks up per-kind component
                                    from registry, returns null if unknown
      DetailsSection.tsx          - shared "Connect to folder" + MD edit
                                    chrome
      shared/                     - composition helpers used by 2+ per-kind
                                    inspectors (FoundationRefBlock,
                                    DoDontFields)
      {kind}/index.tsx × 15       - per-kind typed-field body
      registry.ts                 - NodeKind → component map (size 15)

    {Foundation,Actors,Services,ServiceDetail}Canvas.tsx   (★ pending rename: ServiceDetail→Feature canvas + new Entities canvas + drill service→feature, D-2026-06-17-D/G/I; current code keeps these names until that ships)
                                  - 16-23 LOC wrappers. Each supplies four
                                    props to a shared SketchCanvas:
                                    hideRootServiceNode, shouldDrill,
                                    showFoldButton, injectAnchor.

    SketchCanvas.tsx              - shared shell. Mounts React Flow with
                                    NODE_RENDERERS = registry, wires the
                                    sketch hooks.

    sketch/                       - hooks (`use*.ts`) + pure transforms.
                                    None branch on canvas_kind any more;
                                    behaviour comes from the wrapper props.
                                    Static guard: structural-guards.test.tsx
                                    asserts zero `switch (kind)` here.
```

### Contracts (runtime-enforced)

Each contract is a test file. A future commit that violates one
fails the build with a pointer to the relevant `D-2026-05-12-X`
entry.

| Contract | Test | Decision |
|---|---|---|
| `styles.css` has zero cursor declarations | `styles-cursor-baseline.test.tsx` | [D-2026-05-11-C](./DECISIONS.md) |
| Wrappers / nodes / inspectors / hooks have zero raw `cursor:` declarations and zero `style.cursor =` JS assignments | `styles-cursor-baseline.test.tsx` (extended) | [D-2026-05-12-D](./DECISIONS.md) |
| 4 wrappers produce identical `react-flow__*` class skeletons + zero inline cursors when seeded with the same doc | `cursor-sweep.test.tsx` | [D-2026-05-12-C](./DECISIONS.md) |
| Every kind has a per-kind inspector + node renderer + entry in `NODE_RENDERERS` | `structural-guards.test.tsx` + `nodes/registry.test.tsx` | [D-2026-05-12-F](./DECISIONS.md) |
| No god dispatch (`switch (X.kind)`) in wrappers / SketchCanvas / BaseNode / BaseInspector / KindInspector / DetailsSection / App.tsx / sketch hooks | `structural-guards.test.tsx` | [D-2026-05-12-F](./DECISIONS.md) |
| File LOC fits the ceiling table in `CLAUDE.md §Gate 2` | `structural-guards.test.tsx` | [D-2026-05-12-F](./DECISIONS.md) |
| Prop callbacks passed to a Canvas / ServiceDetailCanvas element must have stable identity across drag / onDocChange flows — inline arrow functions are forbidden on these slots so SketchCanvas's `<ReactFlowProvider>` subtree stays mounted | `structural-guards.test.tsx` Contract 4 | [D-2026-05-27-B](./DECISIONS.md) + [D-2026-05-27-C](./DECISIONS.md) |
| `useNodesMemo` emits top-level `width` + `height` on every pushed node (incl. the synthetic project anchor). RF v11's `createNodeInternals` only carries these from the prop node's top-level keys; bury them under `style` only and every `setNodes` call wipes `nodeInternals.width` → every node `visibility: hidden` under drag/onDocChange burst. | `structural-guards.test.tsx` Contract 5 | [D-2026-05-27-D](./DECISIONS.md) |
| 15-kind exhaustive Inspector + entity round-trip | `inspectors.exhaustive.test.tsx` + `round-trip.exhaustive.test.ts` + `test_node_models.py` | [D-2026-05-12-E](./DECISIONS.md) |
| Server `SketchNode` is the 15-way discriminated union; deleted god files stay absent; no `canvas_kind` branching in `canvases/sketch/` | `hooks/pre_commit_gate.py::reset_complete_check` | [D-2026-05-12-G](./DECISIONS.md) |

### What's still pending

- **~~App.tsx ≤ 400~~** — **DONE** in v0.16.5 (D-2026-05-12-H).
  App.tsx 811 → 381 LOC over five commits (v0.16.1–v0.16.5).
  Header / CanvasTabs / HelpCheatsheet / ServiceDetailModal /
  states moved to `viewer/src/shell/`; useUrlSync /
  useAvailableNodes / useAppKeyboard moved to `viewer/src/hooks/`.
  LOC ceiling locked at 400 in
  `viewer/tests/structural-guards.test.tsx`.
- **Server schema export parity with viewer** — `schema_export.py`
  exports all 15 kinds (v0.14.17). A test asserting field-name
  parity between `Cls.model_fields.keys()` (Pydantic) and the TS
  domain class shape would close the round-trip loop. Filed as
  future work in [D-2026-05-12-B](./DECISIONS.md).

### How to add a 16th kind (post-reset)

> **Pending palette growth (2026-06-17 big-picture marathon).** The
> "15-kind" count in this doc is about to move: three new kinds are
> pinned but **not yet landed** — `feature` (capability under a
> service on the Services overview, [D-2026-06-17-D](./DECISIONS.md)),
> `note` (edgeless, canvas-global context on the feature canvas,
> [D-2026-06-17-F](./DECISIONS.md)), and `entity` (project-wide data
> object on the new AI-maintained Entities canvas,
> [D-2026-06-17-I](./DECISIONS.md)). In the same redesign,
> `mission_ref` / `value_ref` / `identity_ref` / `metric` / `content`
> / `group` are slated for **retirement** from the feature canvas
> (the old Service-Detail) — `group`'s chunking role moves to the
> `feature` level and folding becomes a view affordance, not a node
> kind ([D-2026-06-17-H](./DECISIONS.md)). Each landing/retirement is
> a full lock-step (mashbill-entity-template) + guard update; the final
> kind count is the SSOT of the registries, not this prose. Treat the
> steps below as the per-kind procedure regardless of the running
> total.

1. **Server:** new `XNode(BaseNodeFields)` in
   `mashbill/models.py`, add to `SketchNode = Annotated[Union[...]]`,
   add to `_ALL_KIND_CLASSES` in `schema_export.py`.
2. **Viewer domain:** new `domain/X.ts` (class + JSON type + fromJson
   + toJson), add to `parseEntity.ts` dispatch, add to
   `createBlankNode.ts` switch, add to `domain/index.ts` barrel.
3. **Per-kind UI:** new `canvases/nodes/x/index.tsx`,
   `canvases/inspectors/x/index.tsx`, both registered in their
   respective `registry.ts`.
4. **Tests:** add the kind name to `KIND_DIRS` in
   `styles-cursor-baseline.test.tsx` + `structural-guards.test.tsx`
   + the exhaustive smoke/round-trip files + the server-side sweep.

The 5 static guards will scream until each step is done — that's
the intentional friction. Don't bypass.

---

## Current shape (legacy — pre-v0.15 reset)

> **Section below is historical.** LOC numbers and split-candidate
> analyses describe the pre-reset state (SketchCanvas at 1476,
> SketchInspector at 1422, etc.). The v0.15 reset (D-2026-05-12-B
> shipped over v0.14.15 → v0.16.0) executed Candidate A + B
> simultaneously: domain layer (B) + per-responsibility sketch
> hooks (A). The legacy text is kept for context only; do not
> reference it as a description of today's code.

### File sizes

Measured 2026-05-05, post-v0.13.2:

| File | LOC | 500-line rule |
|---|---:|---|
| `viewer/src/canvases/SketchCanvas.tsx` | **1476** | Violated |
| `viewer/src/canvases/SketchInspector.tsx` | **1422** | Violated |
| `viewer/src/App.tsx` | **791** | Violated |
| `viewer/src/canvases/SketchStencil.tsx` | **523** | Violated |
| `viewer/src/canvases/SketchEdgeModal.tsx` | 255 | OK |
| `viewer/src/canvases/SketchNode.tsx` | 241 | OK |
| `viewer/src/canvases/SketchBodyModal.tsx` | 228 | OK |
| `viewer/src/canvases/SketchSidebar.tsx` | 212 | OK |
| `viewer/src/canvases/FoundationRefPicker.tsx` | 133 | OK |

Project rule (`noory-ai/CLAUDE.md`): *"Review for splitting when a
file exceeds 500 lines."* Four files violate; one of them (1476 lines)
is **3× the threshold**.

### `SketchCanvas.tsx` — responsibility inventory

The component carries 13+ distinct concerns in a single closure
scope. Each row below names a concern and the lines it lives on
(approximate, file is large and mutates):

| # | Concern | Anchor lines |
|---:|---|---|
| 1 | **Document → React Flow node transform** | `nodes` `useMemo` ~line 313–479 |
| 2 | **Document → React Flow edge transform** | `edges` `useMemo` ~line 481–517 |
| 3 | **Synthetic project anchor injection** | inside the `nodes` memo, ~line 436–465 |
| 4 | **Anchor drag/resize routing** | `handleNodesChange` ~line 521–577 |
| 5 | **Node click → Inspector + collapse + drill-down** | `inspectorNodeId` state + `onNodeClick` prop |
| 6 | **Three context menus** (pane / node / edge) | `menu` state + `openPaneMenu` / `openNodeMenu` / `openEdgeMenu` |
| 7 | **Keyboard shortcuts** (Cmd+Z / copy / paste / Delete) | `useEffect` ~line 939 |
| 8 | **Drag-and-drop creation** (stencil → canvas) | `handleDragOver` / `handleDrop` ~line 991–1175 |
| 9 | **Overlap nudging** (`slideOff`, `findFreeSpot`) | bottom of file |
| 10 | **Value-flow toggle** + edge re-colour | `valueFlowOn` state + `VALUE_FORM_COLORS` |
| 11 | **Collapsed-tree state** (`childIdsByParent`, `nearestCollapsedAncestor`, `subtreeSize`) | memos ~line 255–311 |
| 12 | **Orphan actor_ref detection + visual override** | `orphanActorRefIds` memo + node-fill override ~line 340 |
| 13 | **Service-Detail modal routing** | `onNodeDrill` prop + double-click handler |
| 14 | **Edge edit modal** | `edgeModalId` state + render block |
| 15 | **Body edit modal** | `bodyModalNodeId` state |
| 16 | **Foundation-ref picker** | `pendingActorRef` state + render block |

Side effects of the entanglement:

- A change to (8) drag-drop can mis-trigger (4) anchor drag because
  both feed `handleNodesChange`.
- (1) and (3) share the same memo, so anchor-injection bugs surface
  as node-render bugs.
- (10) value-flow recolour and (12) orphan visual override compete
  for the same `style` field.
- React Flow's d3-zoom event handling and (5)/(6)'s click handling
  interact through React Flow internals — today's "hover handles
  feel jittery" symptom likely lives in this seam.

### `SketchInspector.tsx` — responsibility inventory

1422 lines is too coarse to break down here in this first pass; the
high-level concerns are: header bar, MD-warning banner, label edit,
typed-field forms (per kind: actor / mission / core_value / identity /
service / actor_ref / mission_ref / value_ref / identity_ref / metric
/ step / rule / content), MD template editor with edit/split/preview,
delete, width toggle. **Per-kind form rendering is the bulk** — split
candidate is obvious (see below).

### `App.tsx` — responsibility inventory

App-level: routing (project / canvas), summary loading, project CRUD,
WebSocket plumbing, error toast, header, sidebar wrapper. 791 lines
is bloated mainly because routing + data loading + UI shell all live
together.

### `SketchStencil.tsx` — responsibility inventory

523 lines is bloated mainly because every kind's stencil entry is
hand-rolled in one file. Split candidate is obvious.

---

## Candidate split boundaries

Three candidates for `SketchCanvas.tsx`. Each has different trade-offs;
**user picks in plan mode in a subsequent session.** No code is moved
until the choice is approved and an entry is appended to
[`DECISIONS.md`](./DECISIONS.md).

### Candidate A — by responsibility (one file per concern)

```
canvases/sketch/
  SketchCanvas.tsx            // shell + ReactFlow root only (~150 LOC)
  useNodesMemo.ts             // (1) + (3) + (12) — node transform incl. anchor + orphan style
  useEdgesMemo.ts             // (2) + (10) — edge transform incl. value-flow recolour
  useAnchorSync.ts            // (4) — anchor drag/resize routing
  useCollapsedTree.ts         // (11)
  useContextMenus.ts          // (6) — pane/node/edge menus
  useKeyboardShortcuts.ts     // (7)
  useDragAndDrop.ts           // (8) + (9) — drop + overlap nudging
  useInspectorRouting.ts      // (5) + (13) — click → Inspector / drill-down
  modals/
    SketchEdgeModal.tsx       // (14, already its own file, just move)
    SketchBodyModal.tsx       // (15, already its own file, just move)
    FoundationRefPicker.tsx   // (16, already its own file, just move)
```

- **Pro:** clean SRP; each hook is single-purpose; unit-testable in
  isolation.
- **Con:** lots of small files; potential prop-drilling through the
  shell if hooks don't compose cleanly; React Flow's onNodeClick /
  onEdgeClick / onNodesChange need a single handler each, so the
  "split" is partly cosmetic — the shell still wires hook outputs to
  React Flow props.
- **Risk:** medium — many edits, each small. Easy to lose
  closure-shared state by accident (e.g. `docRef` ref shared between
  nodes-change + drop + keyboard).

### Candidate B — by domain layer (Clean Architecture)

```
canvases/sketch/
  ui/
    SketchCanvas.tsx          // React Flow shell + JSX
    SketchToolbar.tsx
  domain/
    nodeTransform.ts          // pure: doc.nodes -> rf nodes (no React)
    edgeTransform.ts          // pure: doc.edges -> rf edges (no React)
    overlapNudge.ts           // pure: collision math
    collapsedTree.ts          // pure: parent_id graph queries
  app/
    useSketchController.ts    // composes domain + UI; the only React-aware glue
```

- **Pro:** matches global CLAUDE.md "architecture: Clean Architecture,
  DDD"; pure domain functions are trivially unit-testable; UI thinness.
- **Con:** higher upfront cost; requires extracting state machines
  cleanly; React Flow's mutation-y APIs (drag mid-frame node updates)
  resist purity.
- **Risk:** high if rushed; low if done with discipline.

### Candidate C — minimal pragmatic split (just bring under 500 LOC)

```
canvases/
  SketchCanvas.tsx            // node/edge memos + ReactFlow JSX (~450 LOC)
  SketchCanvas.handlers.ts    // every useCallback handler (~400 LOC)
  SketchCanvas.dragdrop.ts    // drag/drop + overlap nudging (~300 LOC)
  SketchCanvas.menus.ts       // three context menus (~250 LOC)
```

- **Pro:** small move; under-500 mechanical fix; minimum behaviour-risk.
- **Con:** doesn't fix the underlying coupling — concerns still share
  closure scope through props passed back and forth.
- **Risk:** low.

### Candidate split for `SketchInspector.tsx`

Independent of which SketchCanvas option is picked:

```
canvases/inspector/
  SketchInspector.tsx               // shell + header + width toggle (~150 LOC)
  fields/
    LabelField.tsx
    MissionFields.tsx
    CoreValueFields.tsx
    IdentityFields.tsx
    ActorFields.tsx
    ServiceFields.tsx
    RefFields.tsx                   // actor_ref / mission_ref / value_ref / identity_ref
    MetricFields.tsx
    StepFields.tsx
    RuleFields.tsx
    ContentFields.tsx
  MdTemplateEditor.tsx              // foundation MD edit/split/preview pane
```

- Per-kind field components are independent of each other and of the
  Inspector shell; this split has near-zero risk.

---

## Risk register

| Risk | Mitigation |
|---|---|
| Splitting breaks React Flow's d3-zoom / drag handling | Keep the React Flow root mount in one file; only extract pure transforms and event-emit hooks. Verify drag + click after every move via the browser, not only via tests. |
| `docRef` and other refs shared across handlers lose freshness | Pass the ref into each extracted hook explicitly; do not rebuild new refs. |
| Undo/redo (`useSketchHistory` upstream) breaks because state-shape changes | Keep `doc` shape unchanged; only re-organise where mutations are dispatched. |
| Anchor sync regresses (anchor drag stops persisting) | Keep `handleNodesChange` as a single React Flow handler; it can dispatch internally to extracted hooks. |
| Tests miss the regressions because the existing two smoke tests are broken | Fix the two pre-existing smoke-test failures (localStorage in JSDOM + missing `useSketchHistory` import) **before** starting any split. |

---

## Migration order (when the split happens)

In strict dependency order — never do step N before N-1 is green:

1. **Fix the broken smoke tests** so we have a baseline. (Pre-existing
   localStorage / import failures.)
2. **Add a "render Foundation with N children + auto-edges = 0"
   regression test** — scoped **Foundation-local**, not a global law
   ([D-2026-06-17-J](./DECISIONS.md) removed the blanket
   "all edges are user-drawn / never auto-emit" rule; edges are now
   governed by their *definition*, and Foundation keeps its
   user-draw-only behaviour as a per-canvas choice). Today's session
   would have flagged the auto-edge addition immediately.
3. **Split `SketchInspector.tsx` per-kind first** (lowest risk; wins
   under-500 quickly; no React Flow interaction).
4. **Split `SketchStencil.tsx`** (also low risk).
5. **Pick a SketchCanvas candidate** (A / B / C) — that is the
   step requiring plan mode + user approval.
6. **Execute SketchCanvas split** in small commits, one extracted
   hook per commit, browser-verified each time.
7. **Touch `App.tsx` last** — it ties everything together.

---

## What this file is NOT

- Not behaviour spec — that's [`SPEC.md`](./SPEC.md).
- Not a decision — the split-boundary choice happens in plan mode in
  a later session and is recorded in [`DECISIONS.md`](./DECISIONS.md)
  as `D-YYYY-MM-DD-X` once approved.
- Not a refactor PR — no code is moved by this file's existence.
