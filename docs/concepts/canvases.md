# Canvases — 5 kinds, each answering a different question

> **Canon (shared concept, `D-2026-06-28-B`).** Parent = [`../VISION.md`](../VISION.md). Per-kind *meaning* =
> [`kinds.md`](./kinds.md), canvas *behaviour* spec (render·drill·edge rules etc.) = [`../specs/`](../specs/).
> (The engine [`mashbill/docs/CONCEPTS.md`](../../mashbill/docs/CONCEPTS.md) points to this file.)

Each canvas forces **one sharp question**. That question is that canvas's identity.

| Canvas | The question it forces | Kinds it holds | Phase |
|---|---|---|---|
| **Foundation** | Who are we, and why do we exist? | `project` · `mission` · `core_value` · `identity` | Discovery |
| **Actors** | Who participates? | `project` · `actor` | Planning |
| **Entities** | What does the product deal with? | `project` · `entity` (AI-maintained) | Planning (derived) |
| **Services** (overview) | What value is created and exchanged? | `project` · `category` · `service` · `feature` | Planning |
| **Feature** (per-feature, drill target) | How does this feature work? | `step` · `decision` · flow edge · `note` · `rule` · `actor_ref` | Execution |

> All primary canvases (Foundation/Actors/Entities/Services) radiate from the
> **project anchor**. The anchor = name only (a visual grouping tool, not a content container).

---

## Foundation — "Who are we, and why do we exist?"

Defines the project's identity. **Single canvas** (no audience split — the very composition of
mission·core value·identity visually states the essence, so splitting it breaks it).

- **The essence has no node.** Essence = the **emergent whole** of the 3 kinds ("our service = *this* mission +
  *this* core value + *these* identities"). The core is the mission. To read the one-line essence, read the mission.
- Mission·core value = **inputs** (interview). Identity = **output** (AI-derived, human-confirmed).
- Edges: currently user-drawing only (the canvas's own choice — not a global law, `kinds` §edges).

## Actors — "Who participates?"

Draws the **roles** of the service value economy and their relationships.

- `actor` = a relational *role* (not a person·persona). **Hierarchy tree** (US-303: side field removed; asymmetry via actor_ref/edges).
  inheriting down to sub-roles). The hierarchy is core, not optional.
- **2 kinds of edges — never confuse them:**
  1. **Hierarchy edge** ("is-a-kind-of") — structure only, no value, a quiet edge.
  2. **Relationship edge** ("gives value to") — a **value arrow** with direction·label (which role gives what
     value to which role). A mutual relationship = 2 arrows.
- Actors holds **role-level general value flow**. Concrete per-service exchanges are no longer
  stored granularly (this session: `actor_ref`'s gives/receives retired —
  value lives here [role level] + in the service's 5 fields [aggregate]).

## Entities — "What does the product deal with?"

Manages the product's **data objects** (post·comment·user) in one place. Symmetric with Actors
(**actor = who / entity = what**).

- **AI-maintained, the user does not draw it directly.** AI emerges and registers it during feature/service
  design → human reviews·confirms (never done silently). Bottom-up creation (during feature work) + top-down management.
- **A conceptual map, not a physical ERD.** Name + one-line "what it holds" + rough relationships only. Normalization·FK·
  cardinality·types are outside Novel (the external agent's job) — putting them in violates the identity.
- **A derived canvas filled in last** (emerges from feature work).
- AI can propose·draw entity↔entity rough relationship edges (edges are governed by definition, not authorship).

## Services (overview) — "What value is created and exchanged?"

Maps the value economy at a high level. Hierarchy = **category → service → feature**.

- **category** = visual grouping (mindless, no value). Groups services by theme.
- **service** = an arena where multiple actors **create and exchange value**. **Selection = a 5-field
  question-form inspector, no drill.** 5 fields: who participates? (actor reference) · why is it needed? · what
  gets better? · what can't be given up? (core_value reference) · with what grain do we approach? (identity reference).
- **feature** = a *capability* the service provides (writing/editing) — a **behaviour grouping** under the service.
  **Click = drill into the Feature canvas** (the only drill target). Not an independent value unit — when it becomes a
  multi-actor value exchange → **promoted** to a service.
- **No service↔service edge** (old "user journey edge" retired — flowcharting violates the identity,
  value flow is already held by Actors·actor_ref).
- References (actor/core_value/identity) = **pick** from Foundation/Actors; if absent, create and register
  a new one there, then chip (not free typing). "Later canvases reference earlier ones."

## Feature (per-feature) — "How does this feature work?"

The **UX flowchart** that opens when you click a feature (action → branch → result). The old "Service-Detail" canvas.

- **Only this one bottom layer** is a flowchart, so it doesn't clash with IDENTITY "not a flowchart tool".
- **action altitude guard:** user action → branch → result. Below that, the implementation (save·query·render) is
  **outside Novel, the external agent's job.** This altitude line is the **hand-off line** from the in-app coach → external agent.
- **Actor-anchored, value-oriented** (inherits PHILOSOPHY P5/P6) — not dry abstract shapes.
- **Here `actor` is a read-only anchor** ("who starts / who can") — *not value-exchange editing*.
  The role itself = in Actors / permissions = in `rule.actor_permissions`.
- Nodes: `step` (action) · `decision` (branch, ◇) · flow edge · `note` (edge-less global context) ·
  `rule` (per-feature operating constraint) · `actor_ref` (read-only actor anchor).

---

## Canvas ↔ Phase ↔ Coach

| Canvas | Phase | Coach (in-app) job |
|---|---|---|
| Foundation | Discovery | Mission·core value interview (discover→filter), derive identity draft |
| Actors | Planning | Role discovery (3 branches: perform·produce·benefit) + relationship·value flow |
| Services | Planning | 5-field interview (JTBD) → feature proposal → promotion test |
| Feature | Execution | Happy-path first → branch → result; altitude guard (implementation = external agent) |
| Entities | Planning (derived) | Discover·propose·register entities during feature conversation (strong dedup) |

Coach content canonical source = [`ai-collaboration.md`](./ai-collaboration.md).
