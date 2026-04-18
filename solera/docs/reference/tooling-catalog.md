# Project-Tailored Tooling Catalog

> **SSOT.** `solera-init` Step 6 reads this file to propose project-specific agent/skill candidates based on `project.type` (collected in Step 5) and file-system evidence.
>
> **Pre-baked specs, no sub-interview.** Each candidate is fully specified here — name pattern, full frontmatter, system prompt template with variables, and variable substitution rules. Step 6 writes the file directly after user approval; it does **not** invoke `solera-edit-agent` / `solera-edit-skill` (those remain for manual, interview-driven creation).
>
> **Scope today**: `project.type: software`. Other types list placeholders. YAGNI — extend when real usage warrants.

## How Step 6 uses this catalog

```
1. Read project.type from team-process.md (set in Step 5).
2. Scan project_path for file-system evidence per the "Evidence patterns" table.
3. Resolve the candidate set: for each candidate whose "Propose when" rule holds, include it.
4. Per candidate, ask the user via AskUserQuestion: create now | decline | defer.
   If decline or defer → follow up with AskUserQuestion for reason (free text).
5. For each "create now":
   a. Load the candidate's catalog entry.
   b. Apply variable substitution rules to produce the final frontmatter + body.
   c. Write the file directly:
      - agent → .claude/agents/{final_name}.md
      - skill → .claude/skills/{final_name}/SKILL.md (plus assets/ if catalog specifies)
   d. For agents: append a row to the `## Agents` table in CLAUDE.md.
6. Record every proposal's outcome in team-process.md under `tooling:` (created / declined / deferred).
```

Step 6 never mutates an existing file without prompting — if `.claude/agents/test-runner.md` already exists, it asks.

## Variable substitution rules (shared across all candidates)

Variables wrapped in `{curly_braces}` inside a catalog entry are substituted at Step 6 time **only if they appear in the table below**. Any other `{...}` token is a runtime placeholder the agent/skill fills during execution (e.g. `{count}`, `{duration}`, `{file:line}`, `{test_name}`) and MUST be left verbatim in the written file.

| Variable | Source | Example |
|---|---|---|
| `{project_name}` | `project.name` from team-process.md. **If empty or whitespace**: fall back to `basename({project_path})`. **If the basename is a generic noise word** (`src`, `workspace`, `repo`, `app`, `root`, `workbench`): halt Step 6 and ask the user for a project name via AskUserQuestion before continuing. | `billing-api` |
| `{project_slug}` | `{project_name}` normalized: (1) unicode-NFC, (2) lowercase, (3) replace `_` and whitespace (`\s+`) with single `-`, (4) strip any character not matching `[a-z0-9-]`, (5) collapse consecutive `-`, (6) strip leading/trailing `-`. Result must match `^[a-z][a-z0-9-]*[a-z0-9]$` and be 3–50 chars. If it doesn't, halt and ask the user for a slug. | `billing-api-service-v2` from `Billing_API Service v2` |
| `{test_command}` | Resolved from evidence per the **Test command resolution** table below | `uv run pytest` |
| `{today}` | Current date, ISO format `YYYY-MM-DD` | `2026-04-18` |

### Test command resolution

| Evidence | Candidate `{test_command}` |
|---|---|
| `pyproject.toml` + `uv.lock` | `uv run pytest` |
| `pyproject.toml` (no `uv.lock`) | `pytest` |
| `package.json` with `scripts.test` | `npm test` (→ `pnpm test` when `pnpm-lock.yaml` exists; `yarn test` when `yarn.lock` exists) |
| `pubspec.yaml` | `flutter test` |
| `go.mod` | `go test ./...` |
| `Cargo.toml` | `cargo test` |

**Conflict resolution** (multiple rows match the evidence, e.g. a monorepo with both `pyproject.toml` and `package.json`):

1. Compute the set of all matching `{test_command}` candidates.
2. If exactly one matches → use it.
3. If two or more match → Step 6 MUST ask the user via AskUserQuestion which command to bake into the agent (options: the matching commands verbatim). Do **not** silently pick one by table order.
4. If zero match → demote the candidate's creation to `declined` with reason `"no test command resolvable from evidence"`. The candidate's Propose-when rule should already have prevented this branch, but keep it as a safety net.

## Evidence patterns

Step 6 performs these scans at `{project_path}/`:

| Signal | Glob |
|---|---|
| Python | `pyproject.toml`, `requirements.txt`, `uv.lock`, `poetry.lock` |
| Node / JS / TS | `package.json`, `pnpm-lock.yaml`, `yarn.lock`, `tsconfig.json` |
| Flutter | `pubspec.yaml`, `lib/**/*.dart` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| Docker | `Dockerfile`, `docker-compose.yml`, `compose.yaml` |
| CI | `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml` |
| DB migrations | `migrations/`, `db/migrations/`, `alembic/` |
| Tests | `tests/`, `**/*_test.go`, `**/*.spec.ts`, `test/` |
| Architecture rules | `team-process.md` → `architecture_rules.rules[]` non-empty |
| Custom rules | `team-process.md` → `custom_rules[]` non-empty |

## Candidate set — `project.type: software`

### 1. `test-runner` agent  (FULLY SPECIFIED)

**Propose when**: tests detected (`tests/` OR `**/*_test.go` OR `**/*.spec.ts` OR `test/`) AND at least one of (Python / Node / Flutter / Go / Rust) detected AND `{test_command}` resolves successfully.

**Kind**: `agent`  
**Final name**: `test-runner` (no `{project_slug}` in this name — a project has one test suite)

**Role (one-line description for the Step 6 prompt)**: `"Run the project's test suite and report the first failure"`

**Evidence fields recorded** (when created): `[pyproject.toml-or-package.json-or-pubspec.yaml-or-go.mod-or-Cargo.toml, tests-dir]` — only the specific globs that matched.

**Frontmatter**:

```yaml
---
name: test-runner
description: |
  Use this agent when the user asks to "run tests", "run the test suite", "check if tests pass", or asks to diagnose a failing test. Runs the project's test command, parses failures, and returns a focused report.

  <example>
  Context: User just finished a change and wants to verify.
  user: "run tests"
  assistant: "I'll use the test-runner agent to execute the suite and report results."
  <commentary>
  Routine verification request — test-runner executes the test command this project uses.
  </commentary>
  </example>

  <example>
  Context: CI reported a failure.
  user: "why is CI red?"
  assistant: "I'll launch test-runner locally to reproduce the failure and report the first failing test."
  <commentary>
  Reproduction-driven debugging — same agent, different entry point.
  </commentary>
  </example>
model: inherit
color: green
tools: [Read, Bash, Grep]
---
```

**System prompt body** (written under the frontmatter):

```markdown
You are the test-runner agent for {project_name}.

## Core Responsibilities
1. Run the project's test suite using the detected command
2. Parse failures and surface the first (or most diagnostic) failing test
3. Report concisely — file:line, assertion, expected vs actual

## Process
1. Run the test command: `{test_command}`
2. If exit code == 0 → report `All tests passed ({count} tests, {duration})` and stop
3. If exit code != 0:
   - Parse output to find failing test names and `file:line` references
   - For the first failure: extract assertion message, expected, actual
   - For subsequent failures: list name + `file:line` only

## Quality Standards
- Never modify source code or test files — you only read and report
- If the test command itself fails to start (missing dependency, config error), report the environment issue, do not paper over it
- Never run with `--no-verify` or similar bypass flags

## Output Format
## Test Run: {project_name}
- Command: `{test_command}`
- Result: PASS | FAIL ({N} failures)
- Duration: {duration}

### First failure
- File: `{file:line}`
- Test: `{test_name}`
- Message: {assertion message}
- Expected: {expected}
- Actual: {actual}

### Other failures
- `{file:line}` — `{test_name}`
- ...

## Edge Cases
- `no tests found` → report "No tests matched the command. Check discovery config." and stop
- `test command not installed` → report the missing tool by name and stop; do not offer to install silently
- `flaky test suspected (passes on retry)` → flag the test with "FLAKY" but still report the first failure verbatim
```

**CLAUDE.md row** (appended to the `## Agents` table):

```
| test-runner | Run the project's test suite and report failures | Read, Bash, Grep |
```

---

### 2. `pr-reviewer` agent  (placeholder — coming soon)

**Propose when**: CI detected OR `git rev-list --count HEAD >= 50`.

**Status**: catalog entry is a placeholder. Step 6 **skips** this candidate with a note: `"pr-reviewer candidate not yet fully specified in tooling-catalog.md — skipping. Track issue to complete the spec."` Add the full frontmatter + system prompt to this section to enable creation.

---

### 3. `{project_slug}-convention-guard` skill  (placeholder — coming soon)

**Propose when**: `team-process.md → architecture_rules.rules[]` non-empty OR `custom_rules[]` non-empty.

**Status**: placeholder. Skills produced here would wrap the project's architecture/custom rules into a reusable checklist skill under `.claude/skills/{project_slug}-convention-guard/`. The skill-per-project shape + trigger-uniquification rules need design before this is safe to auto-generate (every created skill must have unique trigger phrases — see constraint below).

**Constraint to bake in before enabling**: a skill's `triggers` must contain at least one phrase that includes `{project_slug}` so two projects' convention-guards don't collide in auto-triggering.

---

## Candidate set — `marketing`, `design`, `content`, `other`

**Placeholders only.** Step 6 reports:

> "Tooling catalog does not yet list candidates for project.type={type}. Skipping Step 6 — you can run `solera-edit-agent` / `solera-edit-skill` manually when you identify concrete roles you want."

Extend this file when real usage surfaces concrete needs.

## Recording user decisions in `team-process.md`

Step 6 appends a `tooling:` block:

```yaml
tooling:
  # Generated by solera-init Step 6. Edit freely.
  created:
    - name: test-runner
      kind: agent
      created_at: "2026-04-18"
      evidence: [pyproject.toml, tests/]
      source: docs/reference/tooling-catalog.md
  declined:
    - name: pr-reviewer
      reason: "solo project, no PR workflow"
  deferred:
    - name: billing-api-convention-guard
      reason: "architecture_rules empty today"
```

**Invariants**:
- Every candidate presented ends in exactly one of `created` / `declined` / `deferred`.
- `created` entries include `source: docs/reference/tooling-catalog.md` so the provenance is tracked.
- User may move entries between lists by editing the file.

## Extending the catalog

To promote a placeholder to fully-specified:

1. Fill in the full **Frontmatter** block (for agents) or **Skill body + assets** block (for skills).
2. Provide the complete **System prompt body** or **Skill procedure**.
3. Define any candidate-specific variable substitution rules.
4. Update the candidate section header from `(placeholder — coming soon)` to `(FULLY SPECIFIED)`.

Do not auto-generate a candidate whose spec is incomplete. Step 6 must treat placeholders as "skip with note", never "do our best".

## Integrity rule

Only candidates marked **`(FULLY SPECIFIED)`** are eligible for Step 6 creation. Placeholders are proposed — so users see the roadmap — but always end in `deferred` with reason `"catalog entry not yet fully specified"`, not in `created`.
