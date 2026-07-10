# Per-canvas behavior

> **Canon (shared behaviour RULES, `D-2026-06-28-B`).** The single source of the canvas behaviour rules both
> products follow — what does what. **Detailed implementation·edge cases·code-mechanism** (render detail·layout
> algorithm·cursor·dagre) = engine [`SPEC.md`](../../mashbill/docs/SPEC.md) +
> `AUTO_LAYOUT`/`CURSOR`/`ARCHITECTURE`. Meaning = [`../concepts/`](../concepts/).

## Common — project anchor

- The primary canvases (Foundation/Actors/Services/Entities) float a **synthetic project anchor** at the
  center. Label = `ProjectDoc.name` mirror (SSOT = `ProjectDoc.anchors`, outside `canvas.json`).
- Exactly 1·non-deletable (synthetic id `__project_anchor__`, delete events ignored).
- Drag·resize persist via **`PATCH /api/projects/:id/anchor`** (not `onDocChange`).
- Visual: 2px slate-600 **border** (no outline — triggers cursor flicker). Square auto-fit.
- 4-side handles visible, the user can draw edges to the anchor. Holds **the name only** (not a content container).
- `anchorArrowMode` (arrow direction at render time, the document edge stays the SSOT): Foundation/Actors=`converge`
  (converge toward the anchor), Services=`diverge` (out from the anchor), Feature=`none`.

---

## Foundation — Discovery

- **Nodes:** `project` (anchor) · `mission` · `core_value` · `identity`. No essence node (emergent).
- **Drill:** none.
- **Edges:** **user-draw-only by this canvas's spec** (not a global law — edges are governed by definition,
  `edges.md`). **No automatic edge emission on node creation.**
- **Inspector:** right `<aside>` (when selected), sections = header (kind·delete·width-toggle·close) → label →
  per-kind typed form. Width toggle 320 ↔ min(720,60vw), localStorage persisted. (Typed-text
  kinds hide the legacy details-MD section.)
- **Layout:** auto-layout ON (`layoutAlgo="tree"` = anchor BFS angle-preserving depth ring; ⊞ button,
  touches position only, Cmd+Z undo). Drag-dropped nodes settle **where dropped** (no snap);
  pressing ⊞ aligns them. (The old anchor-radial forced placement is retired for drop only.)
- **Later expansion/TBD:** anchor click→inspector behavior (TBD), connection rules (which kinds), multi-select bulk.

## Actors — Planning

- **Nodes:** `actor` only (rounded). Color is per-node user-selected.
- **Hierarchy = inheritance tree** (anchor root). Every directional edge on the actors canvas = `relation:"inheritance"`
  (child→parent, toward the anchor). Inheritance fields = `[body]` (US-303: side removed). (self→nearest ancestor→blank, computed
  at render time, not stored; grey `↳ inherited from {parent}` caption). An **abstract root** (actor with no
  actor parent and actor children ≥1) shows body only.
- **2 edge kinds:** hierarchy (inheritance, valueless quiet edge) + relationship (value arrow). The relationship-edge model·render
  is implemented in ROADMAP 5.9 (current code is inheritance-centric). [`../concepts/canvases.md`](../concepts/canvases.md) Actors.
- **Drill:** none.
- **Inspector (identity-only):** `body`. (US-303: side field/editing/schema removal complete; old motivation/pain removed earlier)
- **Layout:** `tree` (angle-preserving depth ring). Edges are floating bezier, circle nodes attach to the circumference.

## Services (overview) — Planning

- **Nodes:** `category` (visual grouping, low-friction/dumb) · `service` (5-field inspector) · `feature` (capability).
  Hierarchy category → service → feature. Services are **optional** under a category (not forced).
- **Drill:** **Selecting a service = 5-field inspector, no drill. Clicking a feature = drill into the Feature canvas**
  (the sole drill target). [The old "single-click on service = drill" is retired.]
- **Edges:** user-draw-only. **No first-class service↔service edge** (user-journey retired). `anchor→
  category→service` outward direction (diverge).
- **Inspector (service 5 question-style fields):** ① `"누가 참여하나?"` (who participates?) (actor reference chips,
  multiple) ② `"왜 필요한가?"` (why is it needed?) (typed) ③ `"뭐가 좋아지나?"` (what improves?) (typed) ④ `"뭘 양보 못 하나?"`
  (what can't be conceded?) (core_value chips, multiple) ⑤ `"어떤 결로 다가가나?"` (in what manner does it approach?) (identity
  chips, multiple). The title is itself the interview question. References = pick from Foundation/Actors
  (if absent, create new, [`../concepts/ai-collaboration.md`](../concepts/ai-collaboration.md) §0.2). The old 9 fields are deleted.
- **Layout:** `tree`. **Later expansion:** Services overview full behavior spec (model pinned only).

## Feature canvas — Execution (formerly Service-Detail)

A **UX flowchart** opened by clicking a feature (action → branch → outcome, action altitude). Opens as a dynamic
canvas tab (`{feature/service name}` label). Not a modal.

- **Anchor:** **none.** A hidden root-service node is the layout-hub fallback.
- **Nodes:** `step` (action) · `decision` (branch ◇) · flow edge · `note` (global context with no edges) ·
  `rule` (per-feature operating constraint) · `actor_ref` (read-only actor anchor). [Retired: mission_ref/value_ref/
  identity_ref/metric/content/group.]
- **`actor_ref` = read-only anchor (the crux this session):** displays "who starts/who can". Not edited here.
  The old `gives`/`receives`/`motivation`/`pain` are **retired** (value lives in Actors + the service
  5 fields). See `kinds-fields.md`.
- **Altitude guard:** up to user action → branch → outcome. Implementation logic (storage·query·render) is outside Novel
  (external agent). This line is the in-app coach → external-agent handoff.
- **Drill:** this canvas is the drill target. `actor_ref` click (single/double) = inspector only, no jump to Actors.
- **Edges:** governed by definition. Flow edge = `flow` (step→step). [The old injection edge was from when a foundation ref was a
  node — those refs moved out as chips, so the Feature canvas has no injection source.]
- **Inspector (3-state, Option 1):** (a) no detail node selected → **subject-service read-only
  inspector** (cross-doc from Services, 5-field summary; renders empty when the service is deleted, no crash);
  (b) node selected → that node's editing inspector; (c) click on empty space → return to the service.
- **Node render:** `step` = STEP tag + label (user action) + `⑂` badge (outgoing edges ≥2, derived) +
  `outcome` subtitle (inline edit) + `polarity` tint (positive=green/negative=red/neutral=user color).
  `decision` = diamond forced (no tag). Shape=meaning (master=rounded rectangle, `*_ref`=circle, decision=◇).
- **Layout:** actor-anchor layout (when there are subject edges): preserve actor positions → step/decision get dagre
  rank → direction from the subject edge handles (↔/↕ toggle). Code detail = Mashbill
  [`AUTO_LAYOUT.md`](../../mashbill/docs/AUTO_LAYOUT.md).
- **Later expansion:** full body re-description (drill·layout), action↔entity reference mechanism.

## Entities — Planning (derived, AI-maintained)

- **Status:** model pinned, **on-canvas interaction detail unwritten (later expansion).**
- **Nodes:** `entity` (+ project anchor). Symmetric with Actors (who/what).
- **Authorship:** not directly by the user. The AI synthesizes·registers them as a by-product of feature/service
  design → a human confirms.
- **Form:** concept map (name + one-line `"무엇을 담나"` (what does it hold) + rough relationship). Not a physical ERD.
- **Behavior:** strong dedup (identity matching, ask when ambiguous, quiet merge·no duplicates❌) · back-reference (read-only) ·
  proposed during chat (no auto-scan❌) · lean inspector. Integrity = [`../concepts/ai-collaboration.md`](../concepts/ai-collaboration.md) §3.
- **Edges:** governed by definition. Being AI-maintained, the AI can propose·draw entity↔entity rough relationship edges; the user can edit·delete.
