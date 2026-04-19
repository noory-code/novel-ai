---
id: {journey_id}
kind: journey
name: {journey_name}
status: active
created: {YYYY-MM-DD}
walks: {persona_id}
# parent: {parent_journey_id}   # optional — omit for top-level Journeys
---

# Trigger
{One sentence: what kicks off this Journey for the Persona. Provided by the human.}

# Steps

| # | Stage | Step | Touchpoint | Emotion | Pain |
|---|-------|------|------------|---------|------|
| 01 | {stage} | {action the persona takes} | {channel/screen} | 😀 | {pain text or —} |
| 02 | {stage} | {action} | {channel/screen} | 😐 | {pain or —} |
| 03 | {stage} | {action} | {channel/screen} | 😟 | {pain or —} |

<!-- Steps stay in this table — never split into separate files. -->

# Outcome
{One sentence: what success looks like for the Persona at the end. Provided by the human.}

# Related
<!-- Only include lines for relations that exist or are explicitly confirmed. Remove the rest. -->
- Persona: [[persona/{walks}]]
- Narratives: [[narrative/...]]
- Concepts touched: [[concept/...]]

## Workflow

### Step 0. Setup
- [ ] Ensure `journeys/` and `_index.md` exist
- [ ] Resolve file path; enforce mode (create → file absent, others → file present)

### Step 1. Create (mode = create)
- [ ] Resolve `walks` (required, exactly one active Persona)
- [ ] Human provides **Trigger** (blocking — AI must not invent)
- [ ] AI surfaces **observations** (sibling Journeys, anchored Narratives) — advisory
- [ ] Human provides **Steps** (blocking — table-driven, one row at a time or pasted markdown)
- [ ] Human provides **Outcome** (blocking)
- [ ] Resolve `parent` (AI proposes; human decides; cycle/self-parent rejected)
- [ ] Write file from template; set `status: active`, `created: today`

### Step 2. Update (mode = update)
- [ ] Human picks which sections to revise (Trigger / Steps / Outcome / Related / walks / Parent)
- [ ] Each chosen section: show current, accept new, replace with `<!-- updated: YYYY-MM-DD -->` marker
- [ ] `walks` change: warn that this is rare; suggest creating a new Journey instead

### Step 3. Deprecate (mode = deprecate)
- [ ] Human provides one-line reason
- [ ] `status: deprecated`; prepend `> ⚠️ Deprecated {date} — {reason}`

### Step 4. Archive (mode = archive)
- [ ] Human confirms (warn that anchored Narratives become loose)
- [ ] `status: archived` (file stays on disk)

### Step 5. Wrap-up (all modes)
- [ ] Rebuild `_index.md`: active grouped by `walks` Persona, then indented by parent chain
- [ ] Emit short summary to user
