---
name: solera-publish-artifacts
user-invocable: false
description: Promote a Story's produced design artifacts to the published catalog and wire them into the contributed Concepts' Related Artifacts sections. Invoked automatically at Story Wrap-up.
metadata:
  version: "5.1.0"
  category: workflow
  type: unit
  style: procedural
  triggers: [publish story artifacts, promote artifacts to catalog, story wrap-up artifact promotion]
  uses: []
---

# Publish Artifacts (v3)

> Invoked at **Story Wrap-up** (not Goal Create / Epic Wrap-up — those don't exist in v3).
> Moves design artifacts (persona, service-map, journey, use-case, domain-model, …) from the Story's staging area to `catalog/published/`, then registers the new links on every Concept the Story contributed to.

## Philosophy

In v2, artifacts were promoted at Goal Create and Epic Wrap-up — two separate hooks tied to now-removed layers. In v3 there is exactly one promotion hook: **Story Wrap-up**. This is where the Time-bound axis transfers its durable output to the Living axis (Concepts' Related Artifacts) and the project-wide catalog.

Key invariants:

1. **Story ID is the version tag.** An artifact promoted by `US-001-google-login` gets `applied-version: US-001` in its header / frontmatter. There are no Phase/Goal numbers in v3.
2. **The Story's `artifacts/` staging directory is the discovery source.** Files in `{story_path}/artifacts/{type}/` are candidates for promotion. `# Output Artifacts` on `_story.md` is a different record (commits from Action Items) — it is not read by this skill.
3. **Concepts get the links, not the files.** Files move to `catalog/published/{type}/`. Each contributed Concept's `# Related Artifacts` section gains a markdown link pointing to the canonical catalog location.
4. **No promotion = no error.** A Story that produced only code (no design artifacts) invokes this skill and it completes cleanly with zero moves.

### Why no `## Workflow` section

This skill is a **hook**, not a work item. It runs once as part of `solera-write-story`'s Wrap-up step. It doesn't represent an item that lives on any axis, doesn't hold state between invocations, and doesn't decompose into child work. The procedure below lives entirely in this SKILL.md — there is no template-level `## Workflow` to drive, which is why `solera-manage-workflow` never invokes it directly. (Same pattern as `solera-release`.)

## Prerequisites

- Called by `solera-write-story` during Step 5 (Wrap-up), after all ACTs are ✅ and RETROSPECTIVE.md is written.
- The Story folder `{project_path}/.solera/stories/{story_id}-{story_name}/` exists.
- The Story's `_story.md` frontmatter has non-empty `contributes_to`.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **story_id** | Y | Parent Story ID (used as the version tag) | US-001 |
| **story_name** | Y | Parent Story name | google-login |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Move | Promoted artifact files | `{project_path}/.solera/catalog/published/{type}/` | Final |
| Tag | Version header line | Each promoted file's header | Final |
| Link | `# Related Artifacts` row | Each contributed `concepts/{id}.md` | Final |

## Procedure

### 1. Discover artifacts to publish

- [ ] Read `{project_path}/.solera/stories/{story_id}-{story_name}/_story.md`.
- [ ] Extract `contributes_to` from frontmatter (list of concept IDs; must be non-empty).
- [ ] Scan the Story's staging directory for design artifacts:
  - Path: `{story_path}/artifacts/{type}/`
  - `{type}` = the directory name directly under `artifacts/`.
  - Every file under a `{type}/` directory is a candidate.
- [ ] For each candidate, classify its `{type}` against the Move Mapping table:
  - **Known type** → promote in Step 3 to its mapped destination.
  - **Unknown type** → promote in Step 3 to the fallback `catalog/published/_unclassified/{type}/`, **after** a one-shot BLOCKING prompt: `"Found unknown artifact type '{type}' under {source}. Move to _unclassified/{type}/ for now? (yes / skip this type / abort)"`. Record the human's decision in the final summary.
- [ ] If zero candidates: log `"no artifacts to publish for {story_id}"` and exit cleanly with status success.

**Note**: This skill does **not** read `# Output Artifacts` from the Story. That section tracks **code/doc commits** produced by Action Items. Design artifacts for publication live in `{story_path}/artifacts/`, written there by write-* skills or the human during Story execution.

### 2. Verify destination

- [ ] Ensure `{project_path}/.solera/catalog/published/` exists; `mkdir -p` if not.
- [ ] For each artifact type in the batch: ensure `catalog/published/{type}/` exists; `mkdir -p` if not.

### 3. Tag + move each artifact

For each claimed artifact:

- [ ] Compute destination path using the Move Mapping table. Preserve the source filename.
- [ ] Collision check:
  - If the destination does not exist: proceed.
  - If it exists with **identical content** (byte-identical or diff-clean modulo the `> Applied version:` header line): skip the move; log `"skipped (identical): {filename}"`.
  - If it exists with **different content**: **BLOCKING** — show the human a short diff summary and three options:
    1. **Overwrite** — the Story's version replaces the existing catalog file. Previous version recorded in `<!-- prev-version: {prior_story_id} -->` comment.
    2. **Rename new** — the new file lands as `{name}__{story_id}.{ext}` alongside the old. Both remain; human can merge later.
    3. **Skip** — the new file stays in staging; no catalog update for this file.
  - Log the human's choice in the final summary.
  - Never overwrite silently.
- [ ] Insert/update the version line in the file header (below any frontmatter):
  ```
  > Applied version: {story_id}
  > Updated: {YYYY-MM-DD}
  ```
  If the file already had `Applied version: ...` from a previous Story, replace with the new Story ID and record the prior one in a comment: `<!-- prev-version: US-00X -->`.
- [ ] If the file has Obsidian-style YAML frontmatter and the team uses Obsidian, update:
  - `applied-version: {story_id}`
  - `updated: {today}`
  - Leave other fields alone.
- [ ] Move the file (git-aware if possible: use `git mv` when inside a git repo to preserve history).

### 4. Wire Related Artifacts on each contributed Concept

For each `concept_id` in `contributes_to`:

- [ ] Read `{project_path}/.solera/concepts/{concept_id}.md`.
- [ ] Locate the `# Related Artifacts` section.
- [ ] For each artifact moved in Step 3, ensure a link line exists under the appropriate category (Personas / Service Map / Journey / Use Cases / Domain Model / External):
  ```
  - Personas: [[persona/{filename-without-ext}]]
  ```
  - If a line with the same target already exists: skip (idempotent).
  - If the category header doesn't exist yet in the Concept file: add the full line with its header.
- [ ] Preserve any human-curated entries (notes, External links) — only add, never remove.

### 5. Verify

- [ ] Every claimed artifact file is now under `catalog/published/{type}/` (or explicitly logged as skipped-identical / renamed on collision).
- [ ] The Story's staging directory (`{story_path}/artifacts/`) is empty of types in the mapping table (unknown types remain).
- [ ] Each contributed Concept's `# Related Artifacts` section includes the newly promoted items.
- [ ] Emit summary: `"Published {N} artifacts from {story_id} to catalog; wired into {M} Concepts."`

## Version Tag

| Pattern | Example |
|---------|---------|
| `{story_id}` | `US-001`, `TS-014` |

**File header example** (after promotion):
```markdown
# Journey: first-explore

> Applied version: US-001
> Updated: 2026-04-16

...rest of the file...
```

## Move Mapping

| Artifact type (source dir) | Destination |
|---|---|
| `persona/` | `.solera/catalog/published/persona/` |
| `service-map/` | `.solera/catalog/published/service-map/` |
| `journey/` | `.solera/catalog/published/journey/` |
| `use-case/` | `.solera/catalog/published/use-case/` |
| `domain-model/` | `.solera/catalog/published/domain-model/` |
| `erd/` | `.solera/catalog/published/schema/` |
| `dto/` | `.solera/catalog/published/dto/` |
| `api-spec/` | `.solera/catalog/published/api/` |
| `reference/` | `.solera/catalog/published/reference/` |
| **(unknown type)** | `.solera/catalog/published/_unclassified/{type}/` (requires BLOCKING confirmation at Step 1) |

> Types not on this table go to `_unclassified/` as a fallback so no artifact is silently dropped. If `_unclassified/` fills with a recurring type, extend this mapping (bump the skill version) so future Stories route that type to a proper home.

## Related Artifacts Line Format

On each contributed Concept, links are grouped by category:

```markdown
# Related Artifacts

- Personas: [[persona/bana]], [[persona/hero]]
- Service Map: [[service-map/admin]]
- Journey: [[journey/first-explore]]
- Use Cases: [[use-case/UC-001-google-login]]
- Domain Model: [[domain-model/user-session]]
- External: (human-curated, preserved as-is)
```

One category line, comma-separated link targets. Links are wikilinks so they resolve in Obsidian and most markdown viewers.

## Obsidian Frontmatter (optional)

If promoted files use Obsidian-style YAML frontmatter, update these keys:

```yaml
---
title: {unchanged}
type: {unchanged — persona / service / journey / use-case / domain-model / ...}
tags:
  - status/published
  - relates-to/{concept_id}          # one per contributed Concept
created: {unchanged}
updated: {YYYY-MM-DD}                 # updated to promotion date
applied-version: {story_id}           # Story ID
---
```

Teams not using Obsidian can skip this step — the plain-text `> Applied version:` line at the top of the file is the canonical record.

## Human–AI Protocol

This skill is a **handoff from Time-bound to Living** — at Story Wrap-up, the work turns into durable knowledge. Rules:

| AI does | AI does not |
|---------|-------------|
| Move files claimed by the Story | Move files the Story didn't produce |
| Tag files with the Story ID | Invent a version tag unrelated to the Story |
| Add Related Artifacts links to contributed Concepts | Remove or reorder human-curated entries |
| Rename on content collision (never overwrite) | Silently overwrite an existing published file |
| Log skipped / renamed files so humans can reconcile | Hide a skip/rename from the summary |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Story file missing | `_story.md` not found | Halt; report Story path | Skill halts |
| contributes_to empty | Frontmatter lacks the field | Halt; Story must be fixed first | Skill halts |
| No claimed artifacts | Story produced only code | Log "no artifacts to publish"; exit success | Skill completes |
| Unknown artifact type | Source dir not in mapping | BLOCKING prompt at Step 1 → move to `_unclassified/{type}/` on approval, skip on rejection; logged in summary | Continue after decision |
| Destination missing | `catalog/published/{type}/` absent | `mkdir -p` | Continue |
| Content collision | Same filename, different content exists | Rename new file to `{name}__{story_id}.{ext}`, log | Continue |
| Git mv failure | Not in a git repo, or permission error | Fall back to plain move; log the fallback | Continue |
| Concept file missing | `concepts/{id}.md` absent | Halt; contributes_to references invalid Concept | Skill halts |
| Related Artifacts category absent in Concept | Category header missing | Add the header line and the new entry | Continue |

## Completion Checklist

- [ ] Claimed artifacts all relocated (or explicitly logged as skipped / renamed)
- [ ] Each promoted file has `> Applied version: {story_id}` in its header
- [ ] Obsidian frontmatter updated (if applicable)
- [ ] Each contributed Concept's `# Related Artifacts` section includes the new promotions
- [ ] Human-curated entries in Related Artifacts untouched
- [ ] Summary emitted with counts and any skip/rename log

## Example

### Invocation (called by solera-write-story at Wrap-up)

```python
Skill(name="solera-publish-artifacts", args={
  "project_path": "banas",
  "story_id": "US-001",
  "story_name": "google-login"
})
```

### Before

`_story.md` frontmatter:
```yaml
contributes_to: [authentication, onboarding]
```

Story staging:
```
stories/US-001-google-login/artifacts/
├── persona/
│   └── bana.md           # new
├── journey/
│   └── first-login.md    # new
└── use-case/
    └── UC-001-google-login.md
```

Catalog published (prior state):
```
catalog/published/
├── persona/              # empty
├── journey/              # empty
└── use-case/             # empty
```

### After

Catalog published:
```
catalog/published/
├── persona/
│   └── bana.md           # header: > Applied version: US-001
├── journey/
│   └── first-login.md    # header: > Applied version: US-001
└── use-case/
    └── UC-001-google-login.md   # header: > Applied version: US-001
```

`concepts/authentication.md` → `# Related Artifacts`:
```markdown
- Personas: [[persona/bana]]
- Journey: [[journey/first-login]]
- Use Cases: [[use-case/UC-001-google-login]]
```

`concepts/onboarding.md` → `# Related Artifacts`:
```markdown
- Personas: [[persona/bana]]
- Journey: [[journey/first-login]]
```

(Same files referenced by both Concepts — one canonical location, two references.)

Summary emitted:
```
Published 3 artifacts from US-001 to catalog; wired into 2 Concepts.
```

## Notes

- This skill is `user-invocable: false` — it's only called by `solera-write-story` internally. Humans who want to publish something manually should invoke write-story's Wrap-up or move files by hand.
- `git mv` is preferred over plain move so `git log --follow` continues to work on promoted files.
- Previous Story versions of a file are preserved via git history and the `<!-- prev-version: ... -->` comment. There's no per-file version folder.
