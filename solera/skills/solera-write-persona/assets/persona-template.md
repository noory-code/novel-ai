---
id: {persona_id}
kind: persona
name: {persona_name}
status: active
created: {YYYY-MM-DD}
role: {role_id}
# parent: {parent_persona_id}   # optional — omit for top-level Personas within this Role
---

# Identity
{One paragraph: who they are. Demographic shorthand, profession, context. Provided by the human.}

# Goals
- {What they are trying to accomplish in life/work that touches our service}
- ...

# Pains
- {What hurts them now}
- ...

# Triggers
- {Events that make them seek a service like ours}
- ...

# Quotes
- "{verbatim quote}" — *real interview*
- "{composite quote}" — *composite (captures the voice)*

# Channels
{Optional. Where we reach them. Channels, devices, hours, languages.}

# Related
<!-- Only include lines for relations the human confirms. Remove the rest. -->
- Journeys: [[journey/...]]
- Narratives: [[narrative/...]]
- Concepts they pressure: [[concept/...]]

## Workflow

### Step 0. Setup
- [ ] Ensure `personas/` and `_index.md` exist
- [ ] Resolve file path; enforce mode (create → file absent, others → file present)

### Step 1. Create (mode = create)
- [ ] Human provides **Identity paragraph** (blocking — AI must not invent)
- [ ] AI surfaces **observations** (overlapping Personas, identity references, narratives) — advisory
- [ ] Human provides **Goals** (blocking); Pains / Triggers / Quotes / Channels optional
- [ ] Resolve `parent` (AI proposes; human decides; cycle/self-parent rejected)
- [ ] Write file from template; set `status: active`, `created: today`

### Step 2. Update (mode = update)
- [ ] Human picks which sections to revise
- [ ] Each chosen section: show current, accept new, replace with `<!-- updated: YYYY-MM-DD -->` marker

### Step 3. Deprecate (mode = deprecate)
- [ ] Human provides one-line reason
- [ ] `status: deprecated`; prepend `> ⚠️ Deprecated {date} — {reason}`

### Step 4. Archive (mode = archive)
- [ ] Human confirms (warn if Journeys still walk this Persona)
- [ ] `status: archived` (file stays on disk)

### Step 5. Wrap-up (all modes)
- [ ] Rebuild `_index.md`: active indented by parent chain; deprecated flat; archived omitted
- [ ] Emit short summary to user
