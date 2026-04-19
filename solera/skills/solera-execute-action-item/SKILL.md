---
name: solera-execute-action-item
user-invocable: true
description: Implement one Action Item end-to-end — write the code, run tests, commit. One focused change at a time; always contributing to the parent Story's Concepts.
metadata:
  version: "8.0.0"
  category: writing
  type: unit
  style: procedural
  triggers: [start an Action Item, execute Action Item, implement and commit, work on ACT-NNN, ACT-NNN]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Action Item status icons, transitions, and commit scope tag invariant live there -->

# Executing Action Item

> An Action Item is the smallest workflow unit. **1 Action Item = 1 commit.**
> Every commit belongs to exactly one Story, and that Story contributes to at least one Concept.
> The Concept names appear in the commit message — history stays searchable by "what was advanced."

## Philosophy

Action Items are the terminal leaves of the Time-bound Axis. They end in a single commit and their effect is never "lost" — as soon as this skill completes, the parent Story records the produced files in its `# Output Artifacts` section, and at Story Wrap-up those artifacts roll up into the contributed Concept's `# Current Shape`.

This skill is the bridge between **일** (the commit-sized unit of work) and **결과 확정** (the contribution that survives beyond the Story).

## Prerequisites

- `{project_path}/.solera/stories/{story_id}-{story_name}/_story.md` exists with `status: 🔄` or `⏳`.
- The ACT must be listed in the `_story.md` Action Items table.
- All prerequisite ACTs named in `depends_on` must be ✅ complete.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **story_id** | Y | Parent Story ID | US-001, TS-014 |
| **story_name** | Y | Parent Story name | google-login |
| **action_item_id** | Y | Action Item ID | ACT-001 |
| **action_item_name** | Y | Action Item name | google-provider-config |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Execute | Code/document changes | Files declared in `output_paths` | Final |
| Wrap-up | git commit | `[{primary_concept}][{story_id}][ACT-NNN] title` | Final |
| Wrap-up | ACT status ✅ + commit hash | `{story_path}/ACT-NNN-{name}.md` | Final |
| Wrap-up | Output Artifacts row on Story | `{story_path}/_story.md` — appends to `# Output Artifacts` | Final |

> `{story_path}` = `{project_path}/.solera/stories/{story_id}-{story_name}`

## Skill Resolution

1. Read the `Skill:` metadata field from the Action Item file.
2. If it contains a skill name (not `-`): invoke `Skill(name="{skill_name}")` directly.
3. If `-` or missing: fall back to keyword-matching task content against scanned skill triggers.

## Procedure

### 1. Setup

- [ ] Confirm `{story_path}/_story.md` exists. If not, halt and advise `solera-write-story`.
- [ ] Read `_story.md` frontmatter. Extract:
  - `contributes_to` list (must be non-empty)
  - `primary_concept` = `contributes_to[0]` (used for the commit message scope tag)
- [ ] Confirm this ACT is listed in the Action Items table.
- [ ] Confirm all prerequisite ACTs (`depends_on`) are ✅.
- [ ] **Gate `act.start`** (if defined in team-process.md): iterate `checks[]` per **Gate check execution** below; halt on any failure.
- [ ] Read the Action Item file (`ACT-NNN-{name}.md`) — confirm Goal and Task Content checklist.
- [ ] Check previous ACT retrospectives in this Story: `Glob {story_path}/ACT-*.md`; read any completed ones' `## Retrospective` and apply "Improvements" notes.
- [ ] Set ACT status → 🔄.

### 2. Write tests (if code changes required)

- [ ] Design test cases from the parent Story's acceptance criteria + this ACT's Goal.
- [ ] Write Unit / Widget / Integration test code (Red — expected to fail before implementation).

### 3. Development

- [ ] Resolve skill per Skill Resolution above.
- [ ] Invoke the resolved skill (or perform manual coding if no skill is assigned).
- [ ] Complete all items in the Task Content checklist.

### 4. Test verification

- [ ] Build passes.
- [ ] Tests pass (Green).
- [ ] Confirm all files listed in `output_paths` exist.
- [ ] **Architecture check** (when `architecture_rules.rules` is non-empty in team-process.md):
  - Read `architecture_rules.rules` from `{project_path}/.solera/team-process.md`.
  - For each rule:
    - Collect files matching `rule.scope` via Glob.
    - Intersect with this ACT's changed files (`output_paths` + `git diff --name-only`).
    - For each intersected file, run `Grep {pattern}` for each pattern in `rule.forbidden_imports`.
    - If ANY match: display `"Architecture violation in {file}: matched {pattern} — {rule.message}"` and **BLOCK** until resolved.
  - If `architecture_rules` section is absent or `rules: []`: skip.

### 5. Wrap-up

- [ ] Record the list of changed files in the Action Item file's `## Result → Changed Files` section.
- [ ] **Commit** (1 ACT = 1 commit) using the format:
  ```
  [{primary_concept}][{story_id}][ACT-NNN] title

  - change description
  ```
  Where `{primary_concept}` is `contributes_to[0]` from `_story.md`. If `contributes_to` has multiple entries, only the first appears in the tag; subsequent ones are mentioned in the commit body (`- contributes also to: {other_concepts}`).
- [ ] **Append Output Artifacts to the parent Story** (`{story_path}/_story.md` → `# Output Artifacts`):
  ```
  - ACT-NNN commit {short_hash}: `{output_path_1}`, `{output_path_2}`
  ```
  This is a must-do, not an optional step — the Story's Wrap-up depends on this accumulated list to update Concept Current Shape.
- [ ] Record the commit line in the ACT file's `## Result → Commit` section: `` `{short_hash}` {commit message title} ``.
- [ ] **Gate `act.done`** (if defined): iterate `checks[]` per **Gate check execution** below; halt on any failure.
- [ ] Write the ACT file's `## Retrospective` section — ref: [assets/retrospective.md](assets/retrospective.md).
  - Did well / Did poorly / Improvements / Instruction issues.
- [ ] **System improvement** (when retrospective has "Improvements" or "Instruction System Issues"):
  - Classify each entry:
    - `skill_change`: edit the relevant SKILL.md.
    - `rule_change`: edit the relevant `.claude/rules/*.md`.
    - `framework_change`: record as a new Technical Story in the backlog (do not apply here).
  - `skill_change` and `rule_change` are **staged as a separate commit** immediately after the ACT commit, not amended into it (Atomic Commits: code change and process change are different purposes). Use a commit message of the form: `chore(solera): apply improvements from [{primary_concept}][{story_id}][ACT-NNN]`.
  - Log each applied change: `"System improvement applied: {file} — {description}"`.
- [ ] Set ACT status → ✅.
- [ ] Decide: next Action Item in the Story, or return control to `solera-write-story` for Story Wrap-up.

## Human–AI Protocol

This skill is a pure **Moment 3 (Work)** skill but it also owns the critical handoff that makes **Moment 3 → 결과 확정** possible: populating `# Output Artifacts` on the parent Story.

| AI does | AI does not |
|---------|-------------|
| Write code, run tests, commit | Skip the Output Artifacts append step — this breaks Concept Current Shape update later |
| Classify and apply system improvements inline | Silently merge multiple ACTs into one commit |
| Tag commit scope with `primary_concept` (contributes_to[0]) | Invent a scope tag that isn't a declared Concept |
| Record changed files factually | Overstate or paraphrase the change summary |

## Gate check execution

All `workflow_gates.*.checks[]` entries in `team-process.md` share the same execution model. For each check object, dispatch by `type`:

| `type` | What it does | `params` |
|---|---|---|
| `glob_exists` | Run `Glob {pattern}` — PASS if ≥1 match | `{ pattern: "path/glob" }` |
| `act_complete` | Read `_story.md` Action Items table — PASS if every listed ACT ID has status ✅ | `{ ids: [ACT-001, ACT-002] }` |
| `command_passes` | Run command via Bash — PASS if exit code = 0 | `{ run: "npm test" }` |
| `grep_absent` | Run `Grep {pattern}` restricted to `{glob}` — PASS if 0 matches | `{ pattern: "TODO\|FIXME", glob: "src/**/*.ts" }` |
| `concept_exists` | For each `concept_id` in params (or `contributes_to` if params empty), Glob `concepts/{id}.md`; PASS if all exist with `status: active` | `{ ids: [authentication] }` or `{}` (defaults to the parent Story's `contributes_to`) |
| `milestone_status` | Read `milestones/{id}.md`; PASS if its `status` matches `equals` | `{ id: "mvp", equals: "agreed" }` |

Rules:
- A gate with `checks: []` or no `checks` key falls back to text evaluation of the `condition` field.
- ALL checks must pass for a gate to pass. Any failure → halt with the failing check's `type` and `params` in the error message.
- Unknown `type` values → halt with `"unknown gate check type: {type}"` (do not silently skip).

## Commit Message Format

```
[{primary_concept}][{story_id}][ACT-NNN] title

- change description
```

Where `{primary_concept}` is `contributes_to[0]` from the parent Story. If the Story contributes to multiple Concepts, add a body line:
```
- contributes also to: {other_concept_ids}
```

Examples:
```
[authentication][US-001][ACT-001] Add GoogleLoginUseCase
[liquor-search][TS-014][ACT-003] Write FTS5 index migration
  - contributes also to: admin-tools
```

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| `_story.md` missing | File not found at story_path | Invoke `solera-write-story` | Resume after Story creation |
| `contributes_to` missing/empty | Story frontmatter lacks the field | Halt; Story must be fixed first | Blocking |
| ACT not listed | No matching ACT row in `_story.md` table | Halt; request `_story.md` update | Blocking |
| Dependencies unmet | A `depends_on` ACT is not ✅ | Halt; request prior ACT completion | Blocking |
| ACT file missing | `ACT-NNN-{name}.md` not found | Create from [action-item template](assets/action-item.md) | Continue after creation |
| Build failed | Build command exits non-zero | Report; request code fix | Blocking |
| Tests failed | Test run non-zero | Report failing tests; request fix | Blocking |
| Missing output files | `output_paths` references a file not on disk | Report missing list | Blocking |
| Architecture violation | Forbidden import found | Report file + pattern + rule message | Blocking |
| Commit failed | git hook / permission error | Report git output; do NOT retry with `--no-verify`. Investigate. | Blocking |
| Output Artifacts append failed | Cannot write to `_story.md` | Report; do not consider ACT complete until append succeeds | Blocking |

## Completion Checklist

- [ ] ACT Goal achieved
- [ ] Task Content checklist complete
- [ ] Build + tests pass
- [ ] Architecture rules passed (if defined)
- [ ] Output Artifacts appended to parent `_story.md`
- [ ] Result (changed files, commit hash) recorded in ACT file
- [ ] `act.done` gate passed
- [ ] Retrospective written; system improvements applied inline where possible
- [ ] ACT status → ✅
- [ ] 1 Action Item = 1 commit principle observed

## Cautions

| Wrong | Correct |
|-------|---------|
| Creating a branch per Action Item | An ACT is **a commit only**, on the Story branch |
| Bundling multiple ACTs in one commit | One ACT = one commit |
| Using Epic name as commit scope tag | Epic no longer exists. Use `contributes_to[0]` (Concept ID) |
| Skipping Output Artifacts append because "it's just a small file" | Always append. Story Wrap-up depends on it |
| Using `--no-verify` to bypass failing hooks | Fix the underlying issue; hooks exist for reasons |
