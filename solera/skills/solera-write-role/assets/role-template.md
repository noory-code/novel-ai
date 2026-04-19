---
id: {role_id}
kind: role
name: {role_name}
status: active
created: {YYYY-MM-DD}
# parent: {parent_role_id}   # optional — omit for top-level Roles
---

# Description
{One paragraph: the position someone occupies when they use the service. Not an individual — a class. Provided by the human.}

# Context
{Optional. When / where this Role shows up. Omit this whole section if the human skipped it.}

# Related
<!-- Only include lines for relations the human confirms. Remove the rest.
     These lines are advisory; the canonical relations live on each related
     entity (e.g., a Journey's `walks` field, a Persona's `role` field). -->
- Personas: [[persona/...]]
- Journeys: [[journey/...]]
- Narratives: [[narrative/...]]
- Concepts pressured: [[concept/...]]

## Workflow

### Step 0. Setup
- [ ] Ensure `roles/` and `_index.md` exist
- [ ] Resolve file path; enforce mode (create → file absent, others → file present)

### Step 1. Create (mode = create)
- [ ] Human provides **Description** (blocking — AI must not invent)
- [ ] Human provides **Context** (optional, blocking with explicit skip)
- [ ] AI surfaces **observations** (overlapping Roles, identity hints) — advisory
- [ ] Resolve `parent` (AI proposes; human decides; cycle/self-parent rejected)
- [ ] Write file from template; set `status: active`, `created: today`

### Step 2. Update (mode = update)
- [ ] Human picks which sections to revise
- [ ] Each chosen section: show current, accept new, replace with `<!-- updated: YYYY-MM-DD -->` marker

### Step 3. Deprecate (mode = deprecate)
- [ ] Human provides one-line reason
- [ ] `status: deprecated`; prepend `> ⚠️ Deprecated {date} — {reason}`

### Step 4. Archive (mode = archive)
- [ ] Human confirms (warn about Personas/Journeys/Narratives that will orphan)
- [ ] `status: archived` (file stays on disk)

### Step 5. Wrap-up (all modes)
- [ ] Rebuild `_index.md`: active indented by parent chain; deprecated flat; archived omitted
- [ ] Emit short summary to user
