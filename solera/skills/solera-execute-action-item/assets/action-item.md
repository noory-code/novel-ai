# Template: Action Item

Defines the decomposition unit of a Story that corresponds to a single commit.

## ACT-NNN-{name}.md

```markdown
# ACT-NNN: {title}

> Story: {story_id} {story_name}
> Status: ⏳ Pending | 🔄 In Progress | ✅ Complete | ❌ Cancelled
> Skill: {skill name or -}
> Agent: {agent name or -}
> Phase: {N}
> depends_on: {ACT-NNN, ...} or -
> output_paths: {expected output file paths}

## Goal

{What this Action Item aims to achieve. Must advance the parent Story's contributed Concept(s).}

## Task Content

- [ ] {task 1}
- [ ] {task 2}

---

## Result

### Changed Files

- `path/to/file.ext` — {change description}

### Commit

- `abc1234` [{primary_concept}][{story_id}][ACT-NNN] {title}

## Retrospective

### Did Well

- {effective decisions or execution}

### Did Poorly

- {mistakes, inefficiencies, unnecessary repetition}

### Improvements

- {specific behaviors to change in the next Action Item}

### Instruction Issues

- {omissions or ambiguities found in skills / rules / templates}
```

## Workflow

### Step 0. Setup
- [ ] Confirm `_story.md` exists; if missing, invoke `solera-write-story`
- [ ] Read `contributes_to` from `_story.md` frontmatter (non-empty); set `primary_concept = contributes_to[0]`
- [ ] Confirm this ACT is listed in `_story.md` Action Items table
- [ ] Confirm all `depends_on` ACTs are ✅
- [ ] Gate `act.start` check (if configured)
- [ ] Status → 🔄

### Step 1. Execute
- [ ] Resolve Skill per `Skill:` metadata; if `-`, match task content to available skill triggers
- [ ] Invoke the resolved skill or perform manual coding
- [ ] Complete all task content items

### Step 2. Test verification
- [ ] Build / tests pass (if applicable)
- [ ] `output_paths` files exist
- [ ] Architecture rules pass (if configured)

### Step 3. Wrap-up
- [ ] Record changed files in `## Result → Changed Files`
- [ ] Commit using `[{primary_concept}][{story_id}][ACT-NNN] title` format
- [ ] **Append to parent Story's `# Output Artifacts`**: `- ACT-NNN commit {short_hash}: \`{paths}\``
- [ ] Record commit hash in `## Result → Commit`
- [ ] Gate `act.done` check (if configured)
- [ ] Write `## Retrospective` (Did Well / Poorly / Improvements / Instruction Issues)
- [ ] Apply system improvements inline (skill_change / rule_change); record framework_change as a new TS
- [ ] Status → ✅

## Folder Structure

```
{project_path}/.solera/stories/{story_id}-{story_name}/
├── _story.md
├── ACT-001-{name}.md
├── ACT-002-{name}.md
└── ACT-003-{name}.md
```

## Commit Message Format

```
[{primary_concept}][{story_id}][ACT-NNN] title

- change description 1
- change description 2
```

If the parent Story contributes to multiple Concepts, append a body line:
```
- contributes also to: {other_concept_ids}
```

**Examples:**
```
[authentication][US-001][ACT-001] Add GoogleLoginUseCase
[liquor-search][TS-014][ACT-003] Write FTS5 index migration
  - contributes also to: admin-tools
```

## Cautions

| Wrong | Correct |
|-------|---------|
| Creating a branch per Action Item | An ACT is **a commit only**, on the Story branch |
| Bundling multiple ACTs in one commit | One ACT = one commit |
| Using Epic name as scope tag | Use `contributes_to[0]` (Concept ID) from `_story.md` |
| Skipping the Output Artifacts append | Required — Story Wrap-up depends on it |
| `git commit --no-verify` to bypass hooks | Fix the underlying issue |
