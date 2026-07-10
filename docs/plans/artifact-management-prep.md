# Deliverable management — preparing the next session's discussion

> A preparation document (discussion agenda). The discussion's results get pinned into `DECISIONS.md` `D-` entries + the relevant canon
> (`specs/storage-publish.md`, etc.). Written: end of the 2026-06-20 session (at the user's request).

## Essence anchor (where to return first)

- Novel = **a service for making projects.** A deliverable = "*what* Novel puts out".
- **Big projects are a first-class premise** — big deliverables·big nodes are not a future problem, they must be handled from the start.
- In VISION's 3 phases (Discovery → Retention → Execution), **the deliverable = the Execution boundary**.

## The scope of this discussion

- **mashbill only.** Solera connects *naturally* (execution makes a deliverable and returns it to the graph) —
  this time, **just be conscious of the connection point**, don't go deep.

## Already decided (no re-discussion ❌ — basis)

- **Storage:** `.noory/novel/{project}/`, **JSON = SSOT, MD = for published deliverables only**
  (`specs/storage-publish.md`).
- **per-node publish:** explicit (user confirmation) → version MAJOR bump + MD generation + git commit,
  dirty gate, MINOR propagation to ancestors when a descendant publishes (`D-2026-05-16-E` and other publish history).
- **git consent:** Novel does not auto `git init`.

## Open — to be decided in this discussion

1. **Deliverable definition (T5).** What is it that Novel puts out? A value story? A bundled document? A git tag? —
   the old definition (= a service's **value story**: purpose+produced-value+embodiment+flow) had its expression
   mechanism (metric·injection edges·`*_ref`) retired by the marathon → **needs re-sourcing.**
2. **Re-assess publish eligibility.** With the new palette (add feature/note/entity, retire metric/content),
   **which kinds get published** — redefine (the old list predates the marathon).
3. **Versioning 3-axis unification (T6).** per-node `version` / `blueprint_version` / git tag —
   the unification strategy (currently only per-node is canon, the rest live only in code/PRODUCT_SPEC).
4. **Big-deliverable handling (new today, 5.11 b/c).** For a big node/deliverable, (a) **how to attach** it
   to the graph, (b) **how to put it into context** (summary/chunking). Premised on big projects.
5. **Whether to adopt the invariant (5.11 a).** "Every new deliverable enters the graph *with an edge to the
   thing it implements*" — adopting it makes graph traversal hold forever (no vector needed).
6. **Solera connection point (awareness only).** How an execution deliverable comes back into the mashbill graph.

## Read to start (for a cold start)

- `docs/specs/storage-publish.md` — the current storage/publish canon (§deliverable-definition parked·§versioning not unified).
- `docs/VISION.md` §3 phases — the deliverable = the Execution boundary.
- The commercial application's private product specification — blueprint / "publishing the blueprint"
  (a separate axis from per-node and not part of the public contract).
- `DECISIONS.md`: `D-2026-05-16-E` (per-node publish) · `D-2026-05-21-B` (blueprint publish/blueprint) ·
  `D-2026-05-31-U` (blueprint version = project) · `D-2026-06-20-P` (context search = graph traversal).
- `ROADMAP.md` 5.11 (b/c deliverable management) + the big-picture topic table T5 (deliverable)·T6 (versioning).

## Proposed order of proceeding

Definition (1) → publish eligibility (2) → big deliverable (4) → invariant (5) → versioning unification (3) → Solera connection (6).
If the definition isn't set, everything else floats, so start with (1).
