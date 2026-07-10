# Novel — Philosophy & Design Principles

> **Established: 2026-04-20**
>
> Novel's foundational thinking. Every data model, visual, and AI behavior traces back to these principles. When designing a new feature, evaluate it against these.

---

## Core Definition

> **A service is a device that produces value — value that did not previously exist — through the interaction of multiple actors.**

Korean original: *"서비스란 = 여러 행위자의 상호작용을 통해 이전에 없던 가치를 만들어내는 장치"*

---

## 10 Principles

### P1. Value is Relational
Value doesn't live inside things. It arises *between* actors when they meet and exchange or interact. This aligns with Simmel's relational value theory and Vargo & Lusch's Service-Dominant Logic (value-in-use, not value-in-exchange).

### P2. Value is Plural
Money, attention, name recognition, relationships, trust, information, experience, access, time-and-effort — all are forms of value. Reducing any interaction to a single form (e.g., money) misses the point. In a given exchange, each side typically trades *different forms* of value.

### P3. Participation is Asymmetric
Each participant brings a different set of inputs and takes away a different set of outputs.

- **Hero**: inputs time, creativity, content → outputs money, followers, fame
- **Fan**: inputs money, attention → outputs access, belonging
- **Admin**: inputs infrastructure, moderation → outputs fees, trust capital

The service is the mechanism that matches these asymmetric I/O profiles.

### P4. Added Value is Emergent Surplus
A service is not a simple exchange. It's a *transformation*. When Fan spends $10 to receive a $15-subjective-value experience, they get +$5 surplus. Hero can simultaneously receive surplus. The service exists precisely because the sum of all participant surpluses > 0 (positive-sum).

### P5. A Service is a Hub, Not a Wire
The service itself is not the relation — it's the **field / mechanism** where relations are enabled. It's visualized as a **node**, not an edge. Participant nodes sit around it; arrows flow in and out, carrying inputs and outputs.

### P6. Value-Carrying Arrows Bundle Action and Value
A **value-carrying (relationship) arrow** bundles three things:

- **Verb**: what was done (create, deliver, pay, mediate, consume, ...)
- **Value form**: what kind of value flowed (money, attention, fame, ...)
- **Direction**: from whom to whom

Not every line carries value, though. The Actors canvas (D-2026-06-17-A)
distinguishes two edge types: a **relationship edge** ("gives value to") is the
directed, labelled, value-carrying arrow above; a **hierarchy edge**
("is-a-kind-of") is structure only — it carries no value and is a quiet line.
This principle governs the former, not the latter.

### P7. Distinct Planes of Thinking, on Distinct Canvases
There are distinct planes of thinking:

- **Actors plane** — who participates and how they relate.
- **Services plane** — what value-creating machinery they interact through.

Originally this was sketched as a spatial top/bottom split on the canvas, then reframed as two kinds coexisting in one 2D space. The current model gives **each plane its own canvas** (D-2026-06-16-R, D-2026-06-17-C): Foundation, Actors, and Services are separate canvases, not bands or kinds sharing one space — Foundation stays a single canvas whose three concepts compose the essence (D-2026-06-16-R), and the Services overview has no first-class service→service edge (D-2026-06-17-C). Within a canvas users drag freely without positional constraints; edges are governed by their definition, not by y-position.

### P8. CE Before ME
When designing the set of primitives, **coverage (Collectively Exhaustive)** is the primary criterion. Strict non-overlap (Mutually Exclusive) is relaxed — some overlap between primitive types is acceptable and left to user judgement.

### P9. General Before Specific
Novel is generic. BANAS is just a validation example. The primitives must be capable of modeling Netflix, GitHub, Airbnb, Obsidian — any service. Domain-specific terms (Role, Drop, ...) are **never** elevated to Novel primitives; users fill them in as free-text labels.

### P10. Expression Before Classification
The primary goal is to help users externalize their thinking. Rigid classification schemes block thought. We ship minimal primitives; everything else is free text on labels and edges.

---

## Iteration Log

How we arrived at this philosophy (2026-04-20 session):

1. **v0.1 starting point**: Schema-free 6-stencil (Role/Service/Narrative/Actor/Concept/Note). User pointed out ME violations.
2. **Two-axis proposal**: User suggested "Role-Relation / Intent-Action" as classification axes.
3. **Four frameworks surveyed**: Event Storming, Domain Storytelling, JTBD, Service Blueprint.
4. **6-primitive attempt**: Actor/Object/Intent/Action/Rule/Note. User asked to step back.
5. **Third-axis attempt**: "Production-Sharing" added. Terminology debate (sharing vs consuming).
6. **Return to fundamentals**: User: "the most important thing is that added value is created." Reset to value theory.
7. **Value-nature discussion**: Relational value, plural forms, asymmetric I/O.
8. **"Service = edge" misread**: AI interpreted "service must be a relation" as "service is an edge." User corrected.
9. **"Service = hub node" confirmed**: User: "Service is a node — a node that creates value and enables relationships."
10. **Two-layer structure**: User: "Not 2D, but 2 *layers*." (Superseded by D-2026-06-16-R / D-2026-06-17-C: the model is now **separate canvases per plane**, not layers/bands in one space.)

---

## How v0.2 Implements This

| Principle | Implementation |
|---|---|
| P1, P2, P6 | Relationship edges carry `value_form` (plural select) + `action_verb`; hierarchy edges carry neither (D-2026-06-17-A) |
| P3 | Actor nodes are identity-only (body + inheritance; `side` field removed US-303); per-service asymmetric I/O lives on `actor_ref` in the feature canvas (D-2026-06-17-A/G) |
| P4 | AI skill detects positive-sum patterns |
| P5 | Services are a node kind (not edge) |
| P7 | Separate canvases per plane (Foundation / Actors / Services), not bands in one space (D-2026-06-16-R, D-2026-06-17-C) |
| P8 | Multiple node kinds across canvases; the kind set is the registry's SSOT (D-2026-06-17-D/F/I added `feature` / `note` / `entity`); free labels everywhere |
| P9 | No BANAS-specific terms in Novel |
| P10 | Stencil = hint only; labels and connections free |

---

## Relationship to Other Frameworks

Novel's model borrows from:

- **Event Storming** (Brandolini) — the "actions as first-class" idea; we absorbed Command + Domain Event into a unified `action_verb`.
- **Domain Storytelling** (Hofer & Schwentner) — the "actors connected by labeled arrows" sentence grammar.
- **Jobs-to-be-Done** (Ulwick, Christensen) — the "value statement" vocabulary for describing what flows.
- **Service Blueprint** (Shostack) — the layer-of-visibility idea, generalized across our separate canvases (Foundation / Actors / Services / Feature, D-2026-06-16-R).

But Novel is **not** any of these. It's a synthesis centered on the Added Value principle.

---

## Not Philosophy (But Nearby)

This document captures *conceptual* commitments. The following live elsewhere:

- Implementation decisions → the version's plan file in `~/.claude/plans/` or the `CHANGELOG.md`
- UX / interaction patterns → `README.md` (quick start) or `docs/UX.md` (future)
- API contract → MCP tool docs, HTTP endpoint reference
- Code conventions → repo-level `CLAUDE.md`
