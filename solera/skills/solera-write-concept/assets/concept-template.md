---
id: {concept_id}
name: {concept_name}
status: active
created: {YYYY-MM-DD}
# parent: {parent_concept_id}   # optional — omit for top-level Concepts
---

# Intent
{1-2 sentences — the north star of this Concept in this project. Provided by the human. Rarely changes.}

# Current Design
{What the human is drawing right now. The ideal shape. Evolves as understanding deepens.}

# Current Shape
{AI-maintained summary of what has actually been produced so far, based on completed Stories.
Initially: "(no Stories have contributed yet)".
Updated (with human approval) at each Story Wrap-up.}

# Horizon
{Optional. Directions this Concept is expected to extend toward. Hypotheses, not commitments. If the human has no input, write: "(not set yet)".}

# Health
(no signals yet)
<!--
When signals appear, replace the line above with entries like:
- 🟢 {what is healthy}
- 🟡 {what needs attention / debt}
- 🔴 {what is urgent or broken}
-->

# Contributions
| Story | What it left behind | Date |
|-------|---------------------|------|
<!-- Append-only. Added automatically by solera-write-story at Wrap-up. -->

# Related Artifacts
<!-- Only include lines for artifacts that actually exist or are explicitly confirmed by the human. Remove the rest. -->
- Personas: [[persona/...]]
- Service Map: [[service-map/...]]
- Journey: [[journey/...]]
- Use Cases: [[use-case/...]]
- Domain Model: [[domain-model/...]]
- External: {Figma URL / code path / Notion link / ...}

## Workflow

### Step 0. Setup
- [ ] Ensure `concepts/` and `_index.md` exist
- [ ] Resolve file path; enforce mode (create → file absent, others → file present)

### Step 1. Create (mode = create)
- [ ] Human provides **Intent** (blocking — AI must not invent)
- [ ] AI surfaces **observations** (overlaps, related artifacts, prior Stories) — advisory
- [ ] Human provides **Current Design**; AI may reword with approval (word-smithing only, no new ideas)
- [ ] Optionally collect Horizon
- [ ] Write file from template; set `status: active`, `created: today`
- [ ] Leave Current Shape as `(no Stories have contributed yet)`
- [ ] Seed Related Artifacts only with human-confirmed links (remove unused placeholders)

### Step 2. Update (mode = update)
- [ ] Human picks which sections to revise
- [ ] **Intent is not editable** — changing it triggers archive-and-new dialog
- [ ] Human confirms each change; persist with `<!-- updated: YYYY-MM-DD -->` marker

### Step 3. Deprecate (mode = deprecate)
- [ ] Human provides one-line reason
- [ ] `status: deprecated`; prepend `> ⚠️ Deprecated {date} — {reason}`

### Step 4. Archive (mode = archive)
- [ ] Human confirms
- [ ] `status: archived` (file stays on disk)

### Step 5. Wrap-up (all modes)
- [ ] Rebuild `_index.md`: active listed with one-line Intent summary; deprecated listed separately; archived omitted
- [ ] Emit short summary to user
