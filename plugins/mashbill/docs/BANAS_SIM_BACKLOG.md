# BANAS simulation — backlog

> Live tracking of everything surfaced while populating the real BANAS
> blueprint into Novel (2026-05-31 → 2026-06-01). The user fired findings
> rapidly; nothing is dropped. User: *"못따라가겠다면 어디 기록해둬야합니다."*
> Status: ✅ shipped · 🔨 next (designed) · 💡 idea (needs direction) · ⏳ verify.
>
> **Sim project:** `banas-sim/banas/.plot/banas/` (workspace
> `/Users/woogis/Workspace/banas-sim`). Source of truth for content:
> `project-noory/banas/workspace/{identity,concepts,catalog}`. Foundation
> (20 nodes), Actors (6), Services (7 cat + 11 svc) are populated.

## ✅ Shipped (committed + pushed)

| Item | Ship |
|---|---|
| Category nodes render with rounded corners | v0.36.2 (D-2026-05-31-AB) |
| "+ New folder" in Add-a-Project picker | v0.37.0 (D-2026-05-31-AC) |
| Node click selection sticks (controlled array carries `selected`) | v0.37.1 (D-2026-05-31-AD) |
| Auto-layout collision avoidance — no node overlap | v0.37.2 (D-2026-06-01-A) |
| Node auto-fit content (+ anchor, edges, tag margin; manual resize removed) | v0.38.0 (D-2026-06-01-B) |
| Auto-layout is a TREE, not concentric circles (children near parents) | v0.39.0 (D-2026-06-01-C) |
| ServiceDetail injection (essence) refs never overlap (push along handle axis) | v0.40.1 (D-2026-06-03-A) |
| ServiceDetail actor→entry gap scales with the entry's extent (wide auto-fit entry no longer overlaps the actor) | v0.40.2 (D-2026-06-03-B) |
| ServiceDetail direction control is ONE state-showing toggle (↔/↕ shows current, click flips) | v0.40.3 (D-2026-06-03-C) |
| **All 11 service details filled + verified** (s-auth, s-onboard, s-profile, s-profile-edit, s-landing, s-me, s-blocked, s-salon, s-comm, s-push, s-admin) | 2026-06-03 (sim data, committed 43b3fad) |

> **Service details: COMPLETE (11/11).** All follow the D-2026-05-28-J
> composition model (subject actor_ref → entry, step = user action with
> system work in `outcome`, decision per branch, join on shared outcome,
> essence injection). All ⊞-laid-out with zero node overlap (verified).
> Sim blueprint committed to its own repo (`banas-sim/banas/.plot/banas`,
> initial commit 43b3fad). Sources:
> `project-noory/banas/workspace/{concepts,catalog/published/{use-case,journey}}`.
> Next sim pass: populate node bodies / sub-flows, or move to a different
> canvas (actors state/transitions, foundation group hubs #2 below).

## 🔨 NEXT SESSION — pick up here (designed + user-confirmed)

### 1. Mindmap-quality tree layout  (the active layout task)
User criteria (2026-06-01), confirmed: **(1)** no node overlap, **(2)** no
edge crossing/overlap, **(3)** each parent's children read as ONE visual
group around the parent. The v0.39.0 cartesian tree splits a parent's
children across T/R/B/L and lets cross-branch edges cross near the anchor.

**Approach (user-approved direction):** a recursive **mindmap radial tree**
— new `computeMindmapLayout`, wired into `useAutoLayout` for the `"tree"`
canvases:
- Anchor's children fan around the circle; each gets an **angular sector**
  sized by its subtree leaf-count.
- Each node's children are placed **just outside the node** (parent-relative:
  `parentRadius + gap + childRadius`), **fanned within the parent's sector**,
  on the outward side → children cluster beside their parent.
- Per-level radius = `max(clearance, arc-fit)` where arc-fit =
  `Σ(childDiameter+gap) / sectorAngle` so children always fit along their arc
  (no overlap).
- Subtrees own **disjoint sectors** → branches never overlap or cross.
- Acceptance test (was drafted in a removed WIP `mindmapLayout.test.ts`): no
  node overlap; each child nearer its parent than the anchor; each branch
  span < π (grouped, not wrapped); deterministic.
- Keep `computeRadialLayout` (radial button) + `computeAutoLayout` (cartesian
  tree) as-is; just swap what `useAutoLayout` calls.

### 2. Foundation group hubs  (needs a MODEL change first)
User: *"파운데이션에 그룹 노드 (코어밸류, 아이덴티티)가 필요합니다. 미션
그룹 노드는 필요 없고."* Desired structure:
`BANAS ← 미션 (direct)`, `BANAS ← [핵심 가치] ← {5 values}`,
`BANAS ← [아이덴티티] ← {14 identities}`.
**Blocked:** the server rejects non-`{mission,core_value,identity,project}`
kinds on the Foundation canvas (422 "kinds not allowed on 'foundation'", the
canvas-kind structural gate). So a hub can't be added as data.
**Decision needed:** allow a grouping kind on Foundation (e.g. permit
`category`/`group`) **vs** a dedicated foundation-group kind. Then: update the
allowed-kinds gate + stencil + schema-parity + structural tests, then populate
the BANAS Foundation (`/tmp/regroup_banas_foundation.py` has the rewiring,
needs the kind swapped once allowed).

## 💡 Ideas — need direction

- **Service-scoped identity in Foundation** — some "identity" I placed in
  Foundation is service-specific (디자인 톤/컬러/감정 여정 etc.). Options:
  (A) define in Foundation + a service references it via `identity_ref` (scope
  = who references); (B) move pure service-local identity into that service's
  body/detail; (C) design-system tokens aren't "identity" — separate layer.
  Decision rule drafted; user to pick.

## ⏳ Awaiting user verify

- **Selection fix** (v0.37.1) — confirm real clicks select & stay (synthetic
  probe can't fully reproduce RF's d3 click path).
- **Tree layout** (v0.39.0) — a couple of cross-branch nodes can still crowd
  near the anchor; the mindmap rewrite (#1) is the proper fix.
