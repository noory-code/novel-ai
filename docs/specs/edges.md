# Edge model

> **Canon (shared behaviour RULES, `D-2026-06-28-B`).** Meaning principles = [`../concepts/kinds.md`](../concepts/kinds.md)
> §edges. **Detailed render·classification implementation** = engine [`SPEC.md`](../../plugins/mashbill/docs/SPEC.md)
> + `ARCHITECTURE`; classification logic code = TS `flow/edgeSemantics.ts` + Python `edge_semantics.py` (mirror).

## Principle — governed by definition, not authorship

An edge is **governed by its meaning (`relation` + payload), not by who drew it** (`D-2026-06-17-J`,
retiring the old "every edge is by the user / no auto-emission" [D-2026-05-04-A]). The AI can also propose·draw edges
(especially the AI-maintained Entities canvas). A human can edit·delete at any time. **Forbidden = a meaningless·silently-uneditable
edge** (the old v0.13.2 anchor→child auto-edge). A canvas may be user-draw-only by its own spec
(Foundation/Actors/Services currently) — a per-canvas choice.

## `relation` classification (3 kinds, SSOT)

On creation·migration, `classifyEdge(canvas, source-kind)` assigns the default (after it's set, that is
authoritative; flipping the direction reassigns):

| relation | meaning | parent | notes |
|---|---|---|---|
| `flow` | order/hierarchy | source = parent | default |
| `injection` | essence injected into the target | — | excluded from fold (the overlay doesn't include the target) |
| `inheritance` | actors tree | target = upper (reversed) | folding the upper hides the lower |

- **Invariant:** every hierarchy edge between actors on the actors canvas = `inheritance`; the only other edge between
  actors is a value exchange (`flow` with a label, see below).
- (Old: essence source mission/value/identity [+ their *_ref] → `injection`. Those *_ref were retired, so
  the Feature canvas has no injection source → effectively `flow`-centric. The injection relation itself is kept.)

## payload fields

- `directed: bool` (default true) — when directed, an arrow on the target + participates in hierarchy/fold; undirected is a flat line.
  Drag direction sets source/target (the handle pressed = source).
- `relation` — the 3 kinds above.
- `action_verb` — present in the data model (v0.26.0), **but no inspector editor yet** (follow-up).
- `value_form` — array (VO). The `valueFlowOn` toggle colors per value_form. No editor (follow-up).
- `label` — user copy (edited in the edge modal).
- `style` — default solid; the user can set `dashed`. (injection = purple animated dash.)
- `sourceHandle`/`targetHandle` — per-side type (t/l=target-only, r/b=source-only); null on flip (RF re-routes).

## Hierarchy derivation (from directional edges only)

Parent-child is derived **only from the directional edge's `relation`** (`flow/foldHierarchy.ts`). The legacy node
`parent_id` is removed — on read, the v0.26.0 migration creates a directional edge from legacy parent_id once.
Multiple parents can be expressed; the ancestor walk picks the lexicographically minimal source id for determinism.

## Render · edit

- A non-self-loop edge = **floating** (attaches to the boundary point toward the opposite node, ignoring handles). A self-loop = curve.
- A selected edge = accent 3px. `interactionWidth` widened.
- **Edit:** double-click → edge modal (label·value-form·dashed). Right-click → context menu (toggle direction·
  **flip** [swap source↔target, preserving directed/dashed/label]·delete). flip works on every canvas.
- **`anchorArrowMode`** (direction override at render time, the document edge stays the SSOT): Foundation=`converge`,
  Actors=`diverge-structure` (structure lines point out from the anchor; value-exchange lines keep giver→receiver,
  `D-2026-07-04-K`), Services=`diverge`, Feature=`none`.

## Actors value-exchange edge

On the Actors canvas a **value-exchange edge** is a labeled `flow` edge from the giver to the receiver, distinct from the
hierarchy (`inheritance`) edge; a mutual exchange is two edges. Connecting two actors by hand asks which meaning the line
has (`D-2026-07-05-D`). Value-exchange lines render dashed in amber, keep their own direction, and rank below structure
lines in auto-layout (`D-2026-07-04-I`, `D-2026-07-05-A`). [`../concepts/canvases.md`](../concepts/canvases.md) Actors.
