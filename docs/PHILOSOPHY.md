# Novel — Philosophy & Design Principles

> **Established: 2026-04-20**
>
> Novel's foundational thinking. Every data model, visual, and AI behavior traces back to these principles. When designing a new feature, evaluate it against these.

---

## Core Definition

> **A service owns one coherent outcome that one or more people seek, and groups the capabilities that help them reach it.**

Korean: *"서비스는 한 명 또는 여러 명이 이루려는 결과 하나를 맡고, 그 결과에 필요한 기능을 묶는다."*

---

## 11 Principles

### P1. Value Arises in Use
Value does not live inside a feature. It appears when a person uses a service
and moves toward an outcome. When several people participate, value can also
arise through their exchange or interaction. This aligns with Service-Dominant
Logic's value-in-use without making a multi-actor exchange mandatory.

### P2. Value is Plural
Money, attention, name recognition, relationships, trust, information, experience, access, time-and-effort — all are forms of value. Reducing any interaction to a single form (e.g., money) misses the point. In a given exchange, each side typically trades *different forms* of value.

### P3. Participation Can Be Asymmetric
When several people participate, each may bring different inputs and take away
different outputs.

- **Hero**: inputs time, creativity, content → outputs money, followers, fame
- **Fan**: inputs money, attention → outputs access, belonging
- **Admin**: inputs infrastructure, moderation → outputs fees, trust capital

The service can match these asymmetric contributions while still owning one
coherent outcome. A service used by one person does not need artificial
participants.

### P4. Added Value Changes the Person's Situation
A service is not a list of screens or internal steps. It changes a person's
situation: something becomes clearer, easier, safer, or newly possible. In a
multi-actor service, several participants may gain surplus at the same time.

### P5. A Service is a Hub, Not a Wire
The service itself is not a relation, screen, or process step. It is the
**outcome-owning hub** that groups the capabilities and relationships needed to
reach that outcome. It is visualized as a **node**, not an edge.

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
- **Services plane** — which outcomes the product helps people reach and which
  capabilities belong to each outcome.

Originally this was sketched as a spatial top/bottom split on the canvas, then reframed as two kinds coexisting in one 2D space. The current model gives **each plane its own canvas** (D-2026-06-16-R, D-2026-06-17-C): Foundation, Actors, and Services are separate canvases, not bands or kinds sharing one space — Foundation stays a single canvas whose three concepts compose the essence (D-2026-06-16-R), and the Services overview has no first-class service→service edge (D-2026-06-17-C). Within a canvas users drag freely without positional constraints; edges are governed by their definition, not by y-position.

### P8. CE Before ME
When designing the set of primitives, **coverage (Collectively Exhaustive)** is the primary criterion. Strict non-overlap (Mutually Exclusive) is relaxed — some overlap between primitive types is acceptable and left to user judgement.

### P9. General Before Specific
Novel is generic. BANAS is just a validation example. The primitives must be capable of modeling Netflix, GitHub, Airbnb, Obsidian — any service. Domain-specific terms (Role, Drop, ...) are **never** elevated to Novel primitives; users fill them in as free-text labels.

### P10. Expression Before Classification
The primary goal is to help users externalize their thinking. Rigid classification schemes block thought. We ship minimal primitives; everything else is free text on labels and edges.

### P11. Easy to Read, Nothing Left Out (the Feynman-diagram model)
A Feynman diagram replaces a long calculation with a drawing of a few symbols —
lines and the points where they meet — and its rules map each symbol to exactly
one term of the calculation. Anyone can read the drawing, and the drawing holds
the whole calculation. Novel's canvases follow the same model:

- **Few symbols.** Each canvas has a small, fixed set of kinds and edges
  ([`specs/kinds-fields.md`](specs/kinds-fields.md)). A person can read a canvas
  without learning a large vocabulary.
- **One meaning per symbol.** A written rule says what each kind, field, and edge
  means and where each fact lives. For example, an outcome lives only on a step's
  `outcome`; a decision holds no outcome, and its branches are the labels of its
  outgoing edges. When two shapes could say the same thing, a rule picks one.
- **Nothing left out.** Every fact the design needs has a place on some canvas,
  and the canvases together are the whole design. What the person said and what
  a canvas holds is drawn; what nobody has said is asked, not guessed.
- **The drawing is the design.** Because each symbol has one meaning, the person,
  the coach, and the external agent read the same canvas the same way, and the
  published design can be turned into work without interpretation.
- **The rules are written and taught.** A notation spreads only when its rules are
  explicit; Feynman's diagrams spread after Dyson derived and taught their rules. A
  rule that lives only in someone's head is not part of the notation.

P11 and P10 work together: P10 keeps the *content* free (labels are free text, and
no domain taxonomy is imposed); P11 keeps the *grammar* exact (what each primitive
means).

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
11. **Outcome boundary**: D-2026-08-18-B makes one coherent human outcome the
    service boundary. Multi-actor value exchange remains a valid service shape,
    but is no longer required.

---

## How v0.2 Implements This

| Principle | Implementation |
|---|---|
| P1, P2, P6 | Relationship edges carry `value_form` (plural select) + `action_verb`; hierarchy edges carry neither (D-2026-06-17-A) |
| P3 | A service references the human actors who take part; one actor is valid, and multi-actor asymmetry is represented only when it exists |
| P4 | AI skill detects positive-sum patterns |
| P5 | Services are a node kind (not edge) |
| P7 | Separate canvases per plane (Foundation / Actors / Services), not bands in one space (D-2026-06-16-R, D-2026-06-17-C) |
| P8 | Multiple node kinds across canvases; the kind set is the registry's SSOT (D-2026-06-17-D/F/I added `feature` / `note` / `entity`); free labels everywhere |
| P9 | No BANAS-specific terms in Novel |
| P10 | Stencil = hint only; labels and connections free |
| P11 | Kinds and fields registry ([`specs/kinds-fields.md`](specs/kinds-fields.md)) validated on every write; the coach drafts and draws in that grammar and asks about what no one has said (D-2026-10-10-D) |

---

## Relationship to Other Frameworks

Novel's model borrows from:

- **Event Storming** (Brandolini) — the "actions as first-class" idea; we absorbed Command + Domain Event into a unified `action_verb`.
- **Domain Storytelling** (Hofer & Schwentner) — the "actors connected by labeled arrows" sentence grammar.
- **Jobs-to-be-Done** (Ulwick, Christensen) — the "value statement" vocabulary for describing what flows.
- **Service Blueprint** (Shostack) — the layer-of-visibility idea, generalized across our separate canvases (Foundation / Actors / Services / Feature, D-2026-06-16-R).
- **Feynman diagrams** (Feynman, 1948; rules derived by Dyson) — the aim for the picture as a whole: few symbols, one exact meaning each, easy to read and holding everything (P11, D-2026-10-11-A).

But Novel is **not** any of these. It's a synthesis centered on the Added Value principle.

---

## Not Philosophy (But Nearby)

This document captures *conceptual* commitments. The following live elsewhere:

- Implementation decisions → the version's plan file in `~/.claude/plans/` or the `CHANGELOG.md`
- UX / interaction patterns → `README.md` (quick start) or `docs/UX.md` (future)
- API contract → MCP tool docs, HTTP endpoint reference
- Code conventions → repo-level `CLAUDE.md`
