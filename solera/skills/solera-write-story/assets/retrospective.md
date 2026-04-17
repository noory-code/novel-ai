# Story Retrospective Rules

> Follow these rules when writing `RETROSPECTIVE.md` at Story Wrap-up.
> Template base: [solera-manage-workflow/assets/retro.md](../../solera-manage-workflow/assets/retro.md) — use the "AI Behavior Retrospective" form.

## Perspective: AI Behavior

Story retrospectives focus on **AI behavior** — this is not a business retrospective. The goal is to improve how AI decomposes, implements, and hands off work.

## Required Sections

| Section | Writing Guide |
|---------|---------------|
| **AI Did Well** | Action Item decomposition, acceptance criteria design, TDD execution, artifact capture, collaboration |
| **AI Did Poorly** | Inappropriate commit scope, missing tests, merge conflicts, drifting from Concept intent |
| **AI Improvements** | Specific behaviors AI should change in the next Story |
| **Instruction System Issues** | Omissions, ambiguities, or errors in skill / rule / workflow / template definitions |
| **Concept Contribution Summary** | **Required (v3).** See below. |

## Concept Contribution Summary (required)

For each Concept in `contributes_to`, the retrospective must record:

```markdown
### {concept_name}

**What this Story left behind**: {1–2 sentences describing the actual advance — grounded in Output Artifacts, not intent.}

**Proposed Current Shape update**: {AI's draft revision to this Concept's `# Current Shape`.}

**Approved Current Shape**: {the version the human approved — may equal the proposed, may be edited, may be rejected.}

**Drift note**: {optional — if the Story drifted from the Concept's Intent or Current Design, flag it for future awareness.}
```

If `contributes_to` has multiple Concepts, include one block per Concept.

## Story-Specific Review Questions

- Was the Action Item decomposition strategy effective?
- Were the acceptance criteria sufficiently clear during development?
- Was the commit scope appropriate for each Action Item?
- When using agent teams, were clean results produced without conflicts?
- Did the Output Artifacts end up fully captured, or were some lost?
- Did the Current Shape revision feel mechanical, or did it actually capture what changed? (Drift detector.)

## Anti-Patterns to Flag

- **Rubber-stamp Current Shape** — AI proposed a revision and the human approved without reading. Flag in Drift note.
- **Empty Output Artifacts** — Story produced commits but the artifacts section stayed empty. Indicates Execute-time capture failed.
- **`contributes_to` mismatch** — the work done doesn't actually advance the listed Concept. Indicates a planning mistake at Step 2 of write-story. Record so the next Story avoids it.
