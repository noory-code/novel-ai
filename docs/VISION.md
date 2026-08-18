# Novel — VISION (essence + identity, top-level SSOT)

> **Every session, before touching code, read this file first.** The single
> sentence at the top overrides everything. When definitions conflict, this file
> wins — you fix the other rule.
>
> Canonical map = [`index.md`](https://github.com/noory-code/novel-ai/blob/main/docs/index.md). The *detailed*
> definitions of canvases and kinds are in [`concepts/`](https://github.com/noory-code/novel-ai/tree/main/docs/concepts),
> the *behaviour* specs in [`specs/`](https://github.com/noory-code/novel-ai/tree/main/docs/specs).

---

## Essence — one sentence

**The person and the AI never lose sight of the essence or where the current
work fits into the whole.**

(한국어: 사람과 AI가 본질과 전체 맥락을 놓치지 않는다.)

Novel helps the person and the AI discover the essence together. They always
know why the current work matters and where it fits into the whole. They build
the service from that essence.

This one sentence beats all other priorities. If a change does not serve this
essence, it does not ship.

This sentence states the outcome Novel exists to preserve. What Novel *is* —
the product category — belongs to
[§What Novel is](#what-novel-is--is-not-identity), not here. The product may
change form without changing this essence.

---

## Three-phase cycle (how the essence *works*)

The essence unfolds into a single workflow that repeats as a project grows. Every
canvas, MCP tool, and inspector field must trace back to one of these three.

| # | Phase | What it does | Where | AI collaboration |
|---|---|---|---|---|
| 1 | **Discovery** | Draws out an essence not yet put into words | Foundation (mission/core value/identity) | Active discussion coach — interviews and proposes, the person reviews and confirms. No empty forms❌, no silent auto-generation❌ |
| 2 | **Retention** | Keeps the discovered essence visible and working | Anchor (project node) + later canvases reference earlier ones | Anchors every proposal in the Discovery output — never proposes a service that conflicts with the mission |
| 3 | **Execution** | Plans and builds the services that realize the essence | Actors → Services (service→feature; category optional) → Feature canvas (UX flow) | Planning participation (proposes actors, outcome-based services, and features) + development (code the person reviews against the essence) |

> **The cycle is not linear.** While attempting Execution you may belatedly
> discover part of the essence by realizing what was missing. Novel must support
> **tracing back** from a Feature canvas → Foundation without losing anything.

---

## What Novel is / is not (identity)

> The single source for identity is this section (it absorbed the old
> `IDENTITY.md`). Other documents do *not rewrite* the definition — they only
> reference it.

### Novel is *not*

- ❌ **Not a mindmap / brainstorming tool.** Novel is not free divergence but a
  **structured, opinionated, coach-led** design tool. (The old PRODUCT_SPEC's
  "mindmap-based" + the user-facing word "mindmap" are **retired** — they plant
  the wrong expectation of free divergence.)
- ❌ Not a diagram-only canvas (it does not compete with draw.io / Excalidraw).
- ❌ Not a prose document (Notion / Docs do that).
- ❌ Not an ERD / DB-modeling tool (normalization, FK, field types are outside Novel, the external agent's job).
- ❌ Not a flowchart tool — UX flow is only *the bottommost single layer (the Feature canvas)*,
  and the layers above it (service/feature value maps) are not flowcharts.

### Novel *is*

✅ **A collaborative design tool where a person and AI together structure and
define a service's essence and concepts.** The picture (canvas) *is* the
deliverable, and it is the source the AI reads and works from.

**4 uses** — every feature serves one or more of these:

1. **Concrete service planning** — draws "which outcome each service owns, who
   takes part, what people can do, and what is enforced."
2. **Direction alignment** — captures and checks mission, value, and identity in
   one place so the person and AI move consistently.
3. **Position in the big picture** — locate yourself via "today's work" → feature
   → service → mission. A category may group several related services.
4. **Relationship visualization** — interactions among actors and services that
   only become visible when you look broadly.

### Two modes (present / future)

- **Mode 1 — picture (present):** strategic visualization. Foundation/Actors/Entities/Services/Feature
  canvases. Holds "how it was *intended* to work" (not what happens this week ❌).
- **Mode 2 — timeline (future):** actual work/task management. The picture's
  structure (category, service, feature, owning actor) becomes the reporting
  structure. (Not built — commit/hold is a separate decision.)

---

## Core concepts — one line of meaning each (details = [`concepts/`](https://github.com/noory-code/novel-ai/tree/main/docs/concepts))

> Includes concepts newly pinned this session. The *why* and the *detailed
> fields* are in `concepts/`.

- **essence** = the **emergent whole** of the 3 Foundation kinds (mission, core value, identity). No separate node — the core is the mission, the anchor is name-only (a visual grouping).
- **mission** = the fundamental change to make in the world (the root of existence).
- **core value** = the value that wins when a decision is split.
- **identity** = the execution/expression rule that always applies (AI-derived, person-confirmed).
- **actor** = a relational *role* (not a person or persona). Hierarchy (operator/user→subordinate, inheritance) + give-and-take.
- **service** = one coherent outcome that one or more human actors seek, together
  with the capabilities that help them reach it. Multi-actor value exchange is
  possible, not required. 5-cell question-form inspector (who, why needed, what
  gets better, what you can't give up, by what tone).
- **feature** = a capability that helps a person reach its service's outcome
  (writing/editing) — a behaviour grouping under a service. When it starts to
  own a distinct outcome, **promote** it to a service.
- **Feature canvas** = a **UX flowchart** (action → branch → result, action altitude). The implementation
  below it (storage, query, render) is the external agent's job. Here the **actor is a read-only anchor**
  ("who starts / who can"), *not a value exchange* — per-service exchange data is retired, value lives in
  Actors + the service's 5 cells.
- **entity** = the product's data objects (post, comment, user), a **conceptual map** the AI
  emerges and registers during feature design (no normalization, FK, types). Actor = who / entity = what.

---

## AI collaboration model (details = [`concepts/ai-collaboration.md`](https://github.com/noory-code/novel-ai/blob/main/docs/concepts/ai-collaboration.md))

- **AI = the user's *external* agent** (Pencil model). Novel does not own the model, and
  produces behaviour only through per-canvas guidance. Primary path = the user's own agent
  attaches via **MCP**.
- **Everything is created through discussion** — no empty forms❌, no silent auto-generation❌. The AI
  interviews and proposes → the person reviews and confirms (the person is always the final confirmer).
- **Stage separation** — the design-canvas (Foundation/Actors/Services) interview = the **in-app coach**
  directly / execution (build, code) = the **external MCP agent**. The Feature canvas's hand-off edge =
  the action-altitude guard.
- **Context envelope** = active canvas + selection + earlier-canvas summary + entity registry, passed
  behind the CAG/RAG seam. The external agent also receives the selection + envelope via MCP (required, as it is the primary path).

---

## How a feature decision uses this file

Every feature, bugfix, and refactor is checked against this cycle:
1. **Which of the three phases does it serve?** If none, ask the user.
2. **Does it preserve reversibility?** Tracing back from a Feature canvas → Foundation must keep working.

If unclear, **stop and re-read the one sentence at the top.**

---

## When this file changes

It changes only when the user explicitly redefines the essence, three-phases, or
identity — with `D-YYYY-MM-DD-X` + `Approval: Accepted by user`. Drift in tactical
documents (specs/plans) does not change this file — those documents are brought
into line with this file.
