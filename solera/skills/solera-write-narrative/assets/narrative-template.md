---
id: {narrative_id}
kind: narrative
form: user_story                    # user_story | jtbd | scenario
status: active
created: {YYYY-MM-DD}
about_roles: [{role_id}]            # 1+ active Roles this Narrative concerns (required)
# about_personas: [{persona_id}]    # optional — concrete Persona archetypes
# in_journey: {journey_id}          # optional — anchors to a Journey
# proposes: [{concept_id}]          # optional — Concepts this Narrative proposed (canvas-fillable)
---

# Statement
> As a {role}, I want {goal} so that {benefit}.
<!--
Form templates:
  user_story → "As a {role}, I want {goal} so that {benefit}."
  jtbd       → "When {situation}, I want {motivation}, so I can {outcome}."
  scenario   → 2–3 sentence prose scenario in the Role's (or named Persona's) voice.
-->

# Context
{Why this matters. What state the Role (or specific Persona) is in. Provided by the human.}

# Acceptance Cues
- {Observable sign that the system delivered the benefit}
- ...
<!--
NOT acceptance criteria. Acceptance criteria belong on the Story (Time-bound work
item) that this Narrative may eventually inspire — written via solera-write-story.
-->

# Related
<!-- Only include lines for relations that exist. Remove the rest. -->
- Role(s): [[role/...]]             <!-- mirrors `about_roles:` -->
- Persona archetype(s): [[persona/...]]   <!-- mirrors `about_personas:` -->
- Journey: [[journey/...]]
- Proposed Concepts: [[concept/...]]
- External: {Figma URL / interview transcript / Notion link / ...}

## Workflow

### Step 0. Setup
- [ ] Ensure `narratives/` and `_index.md` exist
- [ ] Resolve file path; enforce mode (create → file absent, others → file present)

### Step 1. Create (mode = create)
- [ ] Resolve `form` (user_story | jtbd | scenario)
- [ ] Resolve `about_roles` (≥1 active Role — required)
- [ ] Resolve `about_personas` (optional; each Persona's `role` must be in `about_roles`)
- [ ] Resolve `in_journey` (optional; validate active if provided)
- [ ] Human provides **Statement** in the chosen form (blocking — AI must not invent)
- [ ] Human provides **Context** (blocking)
- [ ] Human provides **Acceptance Cues** (blocking — ≥1)
- [ ] AI surfaces **observations** (overlapping Narratives, candidate Concepts) — advisory
- [ ] Resolve `proposes` (optional; never auto-finalize a new Concept here — direct to Actors canvas)
- [ ] Write file from template; set `status: active`, `created: today`

### Step 2. Update (mode = update)
- [ ] Human picks which sections to revise (Statement / Context / Acceptance Cues / Related)
- [ ] Validate any reference changes (`about_roles` / `about_personas` / `in_journey` / `proposes`)
- [ ] Each chosen section: show current, accept new, replace with `<!-- updated: YYYY-MM-DD -->` marker

### Step 3. Deprecate (mode = deprecate)
- [ ] Human provides one-line reason
- [ ] `status: deprecated`; prepend `> ⚠️ Deprecated {date} — {reason}`

### Step 4. Archive (mode = archive)
- [ ] Human confirms (Concepts in `proposes` continue independently)
- [ ] `status: archived` (file stays on disk)

### Step 5. Wrap-up (all modes)
- [ ] Rebuild `_index.md`: active grouped by `in_journey` (with "Loose Narratives" group); deprecated flat; archived omitted
- [ ] Emit short summary to user
