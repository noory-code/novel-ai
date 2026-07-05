# CLAUDE.md — Novel operational guide

> **Audience:** Claude Code (or any assistant) working inside `mashbill/`.
>
> **Relationship to other CLAUDE.md files:**
> - `~/.claude/CLAUDE.md` — global *principles* (SOLID, Clean
>   Architecture, "추측 금지", "임시 통과 금지", TDD, …). Theory.
> - `noory-ai/CLAUDE.md` — monorepo *rules* (500-line split, atomic
>   commits, plugin change rule, AI-First Docs banned phrases, …).
>   Theory + monorepo conventions.
> - **This file** — Novel-local *practical triggers, checklists, and
>   commands*. The other two files tell you *what* to value; this one
>   tells you *exactly what to do, when*. When this file disagrees with
>   the others, this file is wrong — fix this file, not the others.
>
> **Pairs with (read in this order on session start):**
>
> ⚠ **정본 거처 (2026-06-28, `D-2026-06-28-B` — `D-19-J` 실현):** 두 제품(오픈 엔진·상용
> 앱)이 공유하는 Novel 개념·동작 규칙의 단일 출처 = `noory-workspace/docs/`(맵 `index.md` · 의미
> `concepts/` · 동작 규칙 `specs/`). 아래 3·7 (DOMAIN/CONCEPTS)은 root를 가리키는 **포인터**
> + 엔진 코드-near(코드 거처·스키마)만 남고, 4 (SPEC)는 **상세 구현·메커니즘**을 보유하되
> *동작 규칙*은 root `specs/` 가 정본(충돌 시 root 우선).
>
> 1. [`docs/VISION.md`](../../docs/VISION.md) — **the essence** + 3-phase cycle. Single source of truth above everything else. Read first, every session.
> 2. [`docs/PRODUCT_SPEC.md`](../../plot/docs/PRODUCT_SPEC.md) — **product-level decisions** (platforms, business model, MVP scope, symbol system, canvas inventory, future / out-of-scope). Read second; it is the framing every other doc sits inside.
> 3. [`docs/DOMAIN.md`](./docs/DOMAIN.md) — engine code-to-domain map (per-context code homes). Concept canon = root [`specs/domain.md`](../../docs/specs/domain.md).
> 4. [`docs/SPEC.md`](./docs/SPEC.md) — detailed behaviour implementation / mechanism / edge cases. The *rules* (what Novel does per canvas) are canon at root [`specs/canvas-behavior.md`](../../docs/specs/canvas-behavior.md) — root wins on conflict.
> 5. [`docs/DECISIONS.md`](./docs/DECISIONS.md) — *why* it does what it does, and what was tried and rejected (last 5 entries auto-surfaced by the SessionStart hook).
> 6. [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — what shape the code is in and how to fix it.
> 7. [`docs/CONCEPTS.md`](./docs/CONCEPTS.md) — pointer to root concepts/. Kind / canvas *meaning* canon = root [`concepts/kinds.md`](../../docs/concepts/kinds.md); wire schema = root [`specs/kinds-fields.md`](../../docs/specs/kinds-fields.md).
> 8. [`docs/CURSOR.md`](./docs/CURSOR.md) — canvas cursor SSOT.
> 9. [`docs/PHILOSOPHY.md`](../../docs/PHILOSOPHY.md) — value-flow / 10 principles.
> 10. [`docs/ROADMAP.md`](./docs/ROADMAP.md) — release order.

---

## Session start — read these first

1. `mashbill/docs/DECISIONS.md` — last 5 entries. What was just decided,
   what was rolled back.
2. `mashbill/docs/SPEC.md` — only the canvas you're about to touch.
3. `mashbill/CHANGELOG.md` — last 1–2 release entries.

If the user's first message references a behaviour you don't recall,
re-read the relevant SPEC section *before* answering. **Never answer a
behaviour question from memory or from code comments alone.**

---

## Pre-action gates

### Gate -1 — Re-anchor to the essence (every session, before answering anything)

The single rule that keeps every other rule honest. Novel's essence
(from [`docs/VISION.md`](../../docs/VISION.md)):

> **Novel 은 본질을 모르는 사람이 본질을 찾고, 그걸 놓치지 않으면서, 그
> 본질 아래에서 서비스를 쉽게 기획·개발할 수 있게 AI 와 협업하는
> 툴이다.**

This sentence + the last 5 DECISIONS entries are auto-surfaced via
`hooks/session_start.py` at SessionStart. **Read both before
formulating the first answer.** When this gate disagrees with any
other rule, this gate wins; fix the other rule.

When the user makes a request, classify it against the three phases
(Discovery / Retention / Execution per VISION.md). If it doesn't fit
any phase or threatens the cycle's reversibility, **stop and ask**
before proceeding.

### Gate 0 — User confirmation pins the spec (immediately, before any other action)

The single most important rule for making work *accumulate* across
sessions. Without this gate, confirmed behaviour evaporates between
sessions and the next session re-asks questions the user already
answered. (See the v0.13.3 → v0.13.6 cursor saga for what happens
when this gate is missing.)

**Trigger — fires the moment the user's message contains any of:**

| 한국어 | 영어 |
|---|---|
| 승인합니다 / 승인 / 그래 / 좋아 / 좋아요 / 네 좋아요 | approved / OK / ship it / looks good |
| 됐다 / 됐어 / 이제 됐다 / 맞아요 / 맞다 | works / right / correct / done |

**Execution order (no skipping, no batching, before any other tool call):**

1. **State the confirmed behaviour in one sentence.** Extract from
   the user's message + the immediately preceding context what,
   precisely, was just approved. Write it as one declarative line —
   the same shape that would go into SPEC.md.
2. **Locate the behaviour RULE in root [`specs/canvas-behavior.md`](../../docs/specs/canvas-behavior.md)**
   (the shared-model rule canon since `D-2026-06-28-B`; detailed mechanism /
   edge cases live in engine [`SPEC.md`](./docs/SPEC.md)).
   - YES, it exists there → verify the existing text matches the
     confirmed behaviour exactly. If it diverges, edit the rule doc
     immediately so the spec text and the confirmed behaviour are
     pixel-identical (and update engine `SPEC.md` if a detail changed).
   - NO, it does not exist → add a new line / table row / section
     to the appropriate canvas. If the location is genuinely
     unclear, ask the user where it goes — never invent a section.
3. **Append a `D-YYYY-MM-DD-X` entry to [`docs/DECISIONS.md`](./docs/DECISIONS.md).**
   Use the template at the top of that file. Approval line:
   `**Approval:** Accepted by user, YYYY-MM-DD.`
4. **Stage SPEC + DECISIONS into the current commit cycle.** If a
   commit has already shipped before the confirmation arrived,
   open a docs-only follow-up immediately:
   `docs(mashbill): pin D-YYYY-MM-DD-X to SPEC`. The version bump is
   patch-level when only docs changed.

**Banned shortcuts:**

- *"다음에 정리하겠습니다"* / *"I'll do this later"* — the next
  session does not see this conversation. Not pinning now = never
  pinned. Same severity as `behavior: 부분 완료 → 금지` in the
  global CLAUDE.md.
- *"이미 이번 commit 에 들어갔다고 가정"* — verify by reading the
  staged diff. Don't assume a SPEC line exists because you intended
  to write one.
- *"한 confirmation 으로 여러 동작을 한꺼번에 batch"* — each
  confirmed behaviour gets its own 1-4 cycle. If three things were
  approved in one message, three SPEC updates + three D entries.
- *"Confirmation 의미가 모호하니 그냥 넘어감"* — if the trigger
  fires but you cannot identify the confirmed behaviour, ask
  *"어떤 동작을 승인하신 건지 한 줄로 확인 부탁드립니다"* before
  doing anything else.

### Gate 1 — Before any UI / behaviour change

```
1. Is the change covered by a SPEC.md line?
   YES → implement what the spec says, no more, no less.
   NO  → STOP. Ask the user. Get explicit "do X" approval.
         Append a D-YYYY-MM-DD-X entry to DECISIONS.md FIRST.
         Then implement.
```

**Banned reasoning:** "the code comment says X is Y, so I'll follow
that." Comments are not spec. They're stale notes from a previous
session that may never have had user approval. See
[D-2026-05-04-B](./docs/DECISIONS.md) for the canonical example: the
"synthetic anchor is read-only" comment caused the assistant to remove
anchor handles, which the user never agreed to.

### Gate 1.5 — Test before code (TDD / BDD)

Per global CLAUDE.md `methodology: TDD(Red→Green→Refactor), BDD(Given/When/Then) ... 테스트 없이 구현 먼저 작성 금지`.
This Gate is non-negotiable. It applies to **every** code change in
`viewer/` or `mashbill/`, no matter how small — bug fix, refactor,
guard, feature.

**Trigger:** the moment Gate 1 hands you a green light, before you
open any source file (other than a test file) for editing.

**Order (never skip, never reorder, never batch):**

1. **Red.** Write the failing test or regression guard that pins
   the behaviour you are about to add / restore. Run it; observe
   the failure. For static guards (no runtime branch), simulate
   the pre-fix code state in your head or temporarily revert the
   suspected line to confirm the guard would have caught the bug
   — then restore. **The test must point at the responsibility
   that is broken, not at a side effect.**
2. **Green.** Implement the smallest change that makes the test
   pass. Stop the moment it passes.
3. **Refactor.** Improve the implementation. Re-run the test
   after every refactor.

**Banned shortcuts (every one of these has been seen in this repo
— each entry below was sanctioned by the user the first time it
shipped without one):**

- *"I'll add the regression test after shipping"* / *"테스트는 다음
  commit 에"* — same severity as Gate 0 *"다음에 정리하겠습니다"*
  ban. Tests added after the fact are **not** TDD; they're
  unverified retroactive guards. If you cannot write the test
  *first*, you do not understand the bug well enough to fix it.
- *"It's just a static type fix / rename / comment edit"* —
  these still need a test if they change behaviour. If they don't
  change behaviour, the existing test suite must still pass on
  the diff.
- *"chrome-devtools verification covers it"* — chrome-devtools
  MCP is a Gate 3 *verification*, not a Gate 1.5 *test*. The user
  rebooting their browser does not run a regression in the next
  session. **A green chrome-devtools probe without a green vitest
  case is half a verification.**
- *"The behaviour is too dynamic to unit-test"* — write a static
  guard that pins the *structural cause* of the behaviour.
  Examples: ban inline-arrow JSX prop callbacks on a hot-path
  slot (string grep over `App.tsx`); assert that a kind exists
  in the registry (length check over `NODE_RENDERERS`). Static
  guards are tests too; `viewer/tests/structural-guards.test.tsx`
  is the canonical home.

**Where the test lives:**

- Behaviour spec → `viewer/tests/{feature}.test.tsx` (vitest +
  testing-library).
- Structural / architectural guard →
  `viewer/tests/structural-guards.test.tsx` or a sibling
  `*-baseline.test.tsx`.
- Server / pydantic → `mashbill/tests/test_*.py`.
- Cross-cutting boundary (server ↔ viewer schema) →
  `mashbill/tests/test_schema_parity.py`.

**Acceptance:** Gate 4 (`Before commit`) fails the commit if the
diff touches `src/` without a corresponding test addition or
update under `tests/`. This is enforced by reviewer judgement
today; a `pre_commit_gate.py` check ('any file under src/ changed
without any file under tests/ changing') is filed as a follow-up.

**Canonical regression that this Gate is named after:**
v0.27.7 (D-2026-05-27-B) — Canvas prop callbacks hoisted to
`useCallback` to prevent a SketchCanvas remount under drag. Shipped
*without* either (a) the static guard banning inline-arrow JSX
callbacks on the Canvas / ServiceDetailCanvas slot, or (b) a
dynamic regression that mounts SketchCanvas, fires N back-to-back
`onDocChange` calls, and asserts the mount counter stays at 1.
User flagged the omission within minutes (*"왜자꾸 테스트를 안하려고해
... TDD 몰라? BDD 모르냐고"*). Follow-up `D-2026-05-27-C` adds
both tests + retro-pin to this Gate.

### Gate 2 — Before editing a file near its LOC budget

Per [D-2026-05-12-F](./docs/DECISIONS.md). The v0.15 structural
reset (D-2026-05-12-B) deleted `SketchInspector.tsx` (Phase 2.10)
and `SketchNode.tsx` (Phase 3.5); the remaining oversize file is
`App.tsx`. Every canvas-internal file has a runtime-enforced LOC
ceiling — see `viewer/tests/structural-guards.test.tsx`.

The per-file **responsibility rule** lives here; the **current LOC + enforced
ceiling** are the SSOT of `viewer/tests/structural-guards.test.tsx`
`LOC_BUDGETS` — numbers drift, the test doesn't (this table used to carry
LOC/Ceiling columns and went stale). **Check the test for the number before
editing near a budget.**

| File | Responsibility rule |
|---|---|
| `viewer/src/App.tsx` | Largest remaining file. `useAppCallbacks` follow-up (D-2026-05-27-B) is **deferred**; D-2026-06-08-A steps 6/8 move server + UI state out of App (net reduction). Extract only if a step pushes it over the ceiling. |
| `viewer/src/canvases/SketchCanvas.tsx` | v0.18.0 Phase 3 (D-2026-05-16-E) absorbed the publish-handler thread to SketchInspectorBindings. **No-growth henceforth** — new responsibilities → new sketch hook or wrapper. |
| `viewer/src/shell/*.tsx` | App-chrome components (Header / CanvasTabs / HelpCheatsheet / ServiceDetailModal / states). Each owns its slice of chrome JSX; new chrome → new file in `shell/`. |
| `viewer/src/hooks/use*.ts` | App-shell hooks (useProject / useCanvasPersist / useProjectSocket / useUrlSync / useAvailableNodes / useAppKeyboard). Per-concern; do not bundle. |
| `viewer/src/canvases/nodes/BaseNode.tsx` | Chrome SSOT for every per-kind node renderer (count = the registry SSOT, `NODE_RENDERERS`; palette is expanding per D-2026-06-17-D/F/I — `feature` / `note` / `entity`, with `group` re-audited for retirement — so never hardcode the count here). New visual responsibilities → per-kind file. |
| `viewer/src/canvases/inspectors/BaseInspector.tsx` | Chrome SSOT for every per-kind inspector (count = the registry SSOT, not this table). New chrome → here; new typed-field body → per-kind file. |
| `viewer/src/canvases/{Foundation,Actors,Services,ServiceDetail}Canvas.tsx` | Props-only thin shells. **Never** put behaviour here — push it into a sketch hook or BaseNode chrome flag. |
| `viewer/src/canvases/nodes/{kind}/index.tsx` (one per registered kind) | Per-kind node renderer; wraps `BaseNode` with kind-specific chrome flags + body override. Kind count = `NODE_RENDERERS` registry SSOT (expanding per D-2026-06-17-D/F/I), not a fixed 15. |
| `viewer/src/canvases/inspectors/{kind}/index.tsx` (one per registered kind) | Per-kind inspector; renders inside `BaseInspector`'s slot. |
| ~~`viewer/src/canvases/SketchInspector.tsx`~~ | **DELETED** in v0.15.0 (Phase 2.10). Re-creating fails `structural-guards.test.tsx`. |
| ~~`viewer/src/canvases/SketchNode.tsx`~~ | **DELETED** in v0.15.5 (Phase 3.5). Re-creating fails `structural-guards.test.tsx`. |

**Raising a ceiling** = open a fresh `D-YYYY-MM-DD-X` entry that
either (a) names the new responsibility the file legitimately
absorbed, or (b) accepts a refactor follow-up. **Never** edit the
test ceiling without the decision id.

**Lowering a ceiling** (i.e. enforcing the planned target after a
split) = the same — pin via a decision so the next session knows
what changed.

If a fix to one of these files needs new state / handler / render
block AND grows LOC past the ceiling, it goes in a new file or
waits for the planned split (see
[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)).

### Gate 3 — Before claiming "done"

**Use the [`mashbill-verifier`](./agents/mashbill-verifier.md) sub-agent.**
For any UI change in `viewer/`, invoke `mashbill-verifier` to navigate
the browser, screenshot the change, and probe the DOM. Do not claim
"done" until the verifier returns **MATCHES SPEC**.

For UI bugs specifically, the `mashbill-frontend-bug-diagnosis` skill is the
upstream procedure (probe → diagnose → fix → re-probe).

For features, the `mashbill-feature-tdd` skill is the end-to-end pipeline;
Step 8 invokes the verifier.

> Dev-facing skills live in the workspace-root `.claude/skills/` (D-2026-07-05-I,
> superseding D-2026-05-13-G's monorepo-level home) and are invoked by name via
> the Skill tool — not by file path from here.

The legacy "manual" path below is kept as a fallback for sessions
where the Playwright MCP is offline:

```bash
cd mashbill && uv run mashbill-http &              # MCP HTTP on 5190
cd plot/viewer && npm run dev                  # Vite on 5193
open "http://localhost:5193/?project_path=$ABSOLUTE_PATH"
```

Then in **the user's real browser** (not just Playwright synthetic
clicks — Playwright bypasses React Flow's d3-zoom event path on
direct `.click()` calls):

- Click the changed element. Does it do the new thing?
- Click around it. Did anything else regress?
- Resize the window. Does layout still fill?

If you can't run a real browser this session, say so explicitly. Do
not say "verified" if you only ran type-check.

### Debugging UI bugs the user sees but Playwright can't reproduce (D-2026-05-27-A)

When the user reports "노드가 사라짐" / "버튼이 안 눌림" / similar
visual bug and Playwright synthetic events fail to reproduce it (RF's
d3-drag / d3-zoom event paths often reject `dispatchEvent` /
`page.mouse` flows), the bug is in the user's real Chrome process
— not in your Playwright instance. **Do not keep guessing.**

**The two-MCP debug workflow:**

1. **Playwright MCP** — your scratch browser. Use for: synthetic
   probes, automated regression runs, taking before/after screenshots,
   simulating drags that DO work (most do). Cannot observe the user's
   actual Chrome process.

2. **chrome-devtools MCP** — bridges into a real Chrome instance.
   Use for: reading the user's live console messages, evaluating JS
   in their page, inspecting DOM state at the moment of the bug.

**When the user says "지금 사라졌다 / 봤제?"** — do NOT reply "no, I
can't see your browser." That is true but useless. Instead:

```
1. Confirm the user has chrome-devtools attached:
     list_pages → should show their page (not just about:blank)
2. Pull console + DOM immediately:
     list_console_messages({types: ["error", "warn"]})
     evaluate_script(() => /* DOM probe of the suspect element */)
3. Match the captured state against the DIAG logs you planted
   in the code earlier.
```

**Plant DIAG logs proactively when chasing a vanish / state-corruption
bug.** Five high-value points to instrument:
- `handleNodesChange` (SketchCanvas) — incoming changes + before/after node count.
- `applyEdit` (useCanvasPersist) — `console.error` on `next.nodes.length < prev.nodes.length`.
- `useNodesMemo` filter — `console.error` when `out.length === 0 && doc.nodes.length > 0`.
- `handleExternalCanvas` (useStableHandlers) — warn when fresh < cached.
- `useEffect` for fitView — log every run + the values it gates on.

Tag each log `[DIAG vX.Y.Z (D-id)]` so they can be grep-removed before
ship.

**Symptom decoder:**

| User says | Likely diagnostic class | First probe |
|---|---|---|
| "노드가 사라졌다" | (a) doc nodes wiped, OR (b) render filter hides them, OR (c) RF `visibility: hidden` lock, OR (d) viewport off-screen | DOM: `getComputedStyle(node).visibility` + `node.getBoundingClientRect()` vs RF rect |
| "정렬 누르니까 사라졌다" | viewport stayed; new layout off-screen | `viewport.style.transform` before vs after; `rf.fitView` call site |
| "드래그하니까 사라졌다" | RF `useNodesInitialized` re-flipped false; mount-time gate held | console logs of fitView effect runs; check `visibility: hidden` count |
| "확대 후 드래그하니까 사라졌다" | same as above but more obvious because zoomed in | same |

**Never claim a fix without observing it in the user's Chrome via
chrome-devtools MCP.** A Playwright pass that didn't reproduce the bug
proves nothing about whether your fix works for the user.

### Gate 4 — Before commit (mashbill plugin change rule)

Per `noory-ai/CLAUDE.md` plugin rule:

1. Bump `mashbill/.claude-plugin/plugin.json` `version` (patch / minor).
2. Append a section to `mashbill/CHANGELOG.md`. **Use the
   Added / Changed / Removed / Fixed structure.** Mention any rolled-back
   attempts honestly — same-day rollbacks belong under "Removed".
3. Append `D-YYYY-MM-DD-X` entries to `DECISIONS.md` for every
   user-visible decision in the change. Mark approval status.
4. Update `SPEC.md` if behaviour changed.
5. `git add` only the files in scope (no `git add -A` — keeps
   unrelated `.claude/settings.json` / debug PNGs out).
6. `git commit` with `type(mashbill): vX.Y.Z — short summary` first
   line; body uses **Added / Changed / Removed / Fixed** sections
   matching the CHANGELOG; ends with the `Co-Authored-By` line.
7. `git push origin main` in the same step.

---

## During-action rules

### Translate the global principles into Novel triggers

| Global principle | Novel trigger |
|---|---|
| `honesty: 추측 금지` | Don't guess what a function does. `grep` for it. Click the button in the browser. If you can't verify in this session, write "I don't know — verify before next change" in your reply. |
| `behavior: 임시 통과 금지` | No CSS-only fixes for behaviour bugs. Find the component that owns the responsibility, fix the responsibility. (Today's hover bug is the canonical example: CSS tone-down was a bandaid; the real cause is the SketchCanvas god component — see ARCHITECTURE.md.) |
| `behavior: 부분 완료 금지` | If a fix touches 5 places, finish all 5 in the same commit. If you can only do 3, ship none and leave a DECISIONS entry "in progress, blocked by X". |
| `behavior: 요청 대체(silent) 금지` | If the user asked for X but you think Y is better, **say so** and ask. Don't ship Y silently. |
| `thinking: SSOT` | Anchor placement SSOT = `ProjectDoc.anchors`. Project name SSOT = `ProjectDoc.name`. Foundation typed text SSOT = `foundation/{kind}-{id}.md`. Never read these from a second source. |
| `thinking: MECE` | Before adding a node kind, an edge kind, or a new canvas, audit the existing ones. New ≠ overlap with existing. New + existing must cover every case the user described. |
| `design: YAGNI` | If the user didn't ask for it, don't add it. The auto-edges in v0.13.2 violated YAGNI and were rolled back same day. |
| `design: 패턴 2회+ 시 추상화` | First time you write something, leave it. Second time, copy it. Third time, abstract — and only if the abstraction reads cleaner than the duplication. (AHA: Avoid Hasty Abstraction.) |
| `design: SOLID/SRP` | Hard signal: any single file > 500 LOC violates the project rule. (The pre-v0.15 god SketchCanvas hit 1476 — 3× over — and was structurally reset; files are now budget-enforced.) See Gate 2. |
| `architecture: Clean Architecture` | New domain logic (transforms, math, graph queries) goes in pure modules without React imports. UI files import from domain, never the reverse. |
| `ux: User-Centricity` | Test against the user's stated workflow. "User selects node → Inspector appears" is a workflow; verify it end-to-end after every relevant change. |
| `ux: Don't Make Me Think` | If a user has to ask "what is this badge?", you have a UX bug, not a knowledge gap. Either the visual or the spec is missing. |
| `ux: Clear Feedback` | Every action that mutates the doc must show some visual response within ~100 ms (handle hover, drag preview, save indicator). Silent success is a bug. |
| `ux: Visual Hierarchy` | 1 화면 = 1 Primary CTA. The Foundation canvas's primary CTA is "place / edit a Foundation node". Anything that competes (e.g. a giant "Auto layout" button on the toolbar) is wrong. |
| `ux: Accessibility` | The ⚠ badge must hit ≥ 4.5:1 contrast against **every** card colour in the Foundation palette (cream / pastel-orange / pastel-yellow). Verify before changing the badge. |
| `methodology: TDD` | Bug fix without a test = the bug will return. Write the regression test first (Red), make it pass (Green), then refactor. |

### Novel-specific operational rules

1. **Code comments are not spec.** If you read a comment that says
   "X is read-only" or "X is auto-generated", you may *act on it*
   only if SPEC.md confirms. Otherwise treat it as a stale note.
2. **Behaviour decisions belong in DECISIONS.md, not in code comments.**
   Code comments may reference a `D-YYYY-MM-DD-X` id but should not
   contain the decision itself.
3. **Same-day rollbacks are honest.** If you ship a change and the
   user rolls it back the same session, document both — the addition
   in CHANGELOG `Added` / `Changed`, the rollback in `Removed`, and a
   `Rejected` DECISIONS entry. Don't hide the attempt.
4. **Anchor ≠ Service circle.** The synthetic project anchor must be
   visually distinguishable from a yellow Service circle on every
   canvas it appears on. Per
   [SPEC §Anchor](./docs/SPEC.md#anchor-the-centre-node).
5. **Edges are governed by their definition, not by who draws them**
   ([D-2026-06-17-J](./docs/DECISIONS.md), which removed the former
   "all edges are user-drawn" ban [D-2026-05-04-A](./docs/DECISIONS.md)).
   Every edge means something — its `relation` (flow / injection /
   inheritance) + payload (direction, `action_verb`, `value_form`,
   label). The AI **may propose / draw edges** (especially on
   AI-maintained canvases like Entities); the user may edit or delete
   any edge. What must hold is the edge's *definition* — **never emit a
   meaningless or silently-uneditable line.** A canvas may still be
   user-draw-only by its own spec (Foundation / Actors / Services
   currently are). Per [SPEC §Edges](./docs/SPEC.md#edges).
6. **Auto-layout is Foundation-only opt-in.** The
   `FoundationCanvas` wrapper passes `enableAutoLayout={true}` to
   `SketchCanvas`; no other wrapper may. The trigger touches
   `x`/`y` only and lands via the regular `onDocChange` (Cmd+Z
   undoes it). Per [SPEC §Auto-layout](./docs/SPEC.md#auto-layout)
   and [D-2026-05-13-L](./docs/DECISIONS.md). The isolation contract
   is pinned by `viewer/tests/auto-layout-isolation.test.tsx` —
   never opt other wrappers in without a fresh `D-` entry that
   updates that test.
7. **No silent automated change to user-visible state.** The canvas is a
   co-drawing surface (Novel's PHILOSOPHY.md). The AI **may propose / draw**
   edges and entities — especially on **AI-maintained canvases** (the
   Entities canvas, [D-2026-06-17-I](./docs/DECISIONS.md), where AI surfaces
   entities **and their relationships**; edges are governed by definition,
   not authorship, [D-2026-06-17-J](./docs/DECISIONS.md)). What is banned is
   *silent* finalization: every AI-originated change surfaces for the user to
   review / edit / delete (build-through-discussion, never silent —
   [D-2026-06-16-P](./docs/DECISIONS.md)). A canvas may still be
   user-draw-only by its own spec (Foundation / Actors / Services currently
   are). **The in-app coach writing a confirmed value into the selected node
   via `update_node` is NOT a violation of this rule**
   ([D-2026-06-26-D](./docs/DECISIONS.md)): a write that lands *after* an
   explicit user confirmation is the *completion* of build-through-discussion,
   not silent finalization. The line this rule draws is "never write *without*
   a confirmation" — confirmation → write is exactly the model.

### Commands you'll use often

```bash
# Run viewer + MCP for manual verification
cd mashbill && uv run mashbill-http &
cd plot/viewer && npm run dev

# Type-check viewer
cd plot/viewer && npx tsc --noEmit

# Run viewer tests (note: 2 pre-existing failures from JSDOM
# localStorage + a missing useSketchHistory import; fix these
# before any architecture work — see ARCHITECTURE.md migration order)
cd plot/viewer && npx vitest run

# Run MCP tests
cd mashbill && uv run pytest

# Type-check MCP
cd mashbill && uv run mypy mashbill/

# Lint
cd mashbill && uv run ruff check mashbill/ tests/
cd mashbill && uv run ruff format mashbill/ tests/
```

---

## Communication rules

1. **Match the user's language.** User asks in Korean → answer in
   Korean. Code, comments, commit messages, docs stay English (per
   noory-ai CLAUDE.md "Language" section).
2. **Brief over verbose.** A clear sentence beats a clear paragraph.
   Don't explain three options when one is clearly right; just ask
   which they want.
3. **Show evidence, not opinion.** "Mission node Inspector shows
   `_md_warnings: ['missing or empty section for declaration']`"
   beats "I think the badge means missing fields". (Mission is one
   `declaration` + `body` since [D-2026-06-16-J](./docs/DECISIONS.md);
   the former `what_we_do` / `why` / `direction` fields are gone.)
4. **Don't expand scope silently.** If the user says "remove X",
   remove X. If removing X needs Y to also change, *ask first*. Don't
   ship X+Y as one commit unless you've named both.
5. **Acknowledge mistakes plainly.** "I treated a code comment as
   spec; that was wrong" is better than three paragraphs of
   meta-justification.
6. **When the user repeats a frustration, the next reply must address
   the structural cause, not just re-fix the symptom.** Today's "why
   doesn't work accumulate?" was structural; the answer was SPEC +
   DECISIONS + ARCHITECTURE + this file — not another tactical CSS
   change.

---

## Anti-patterns (things this guide is here to stop)

| Anti-pattern | Concrete example seen | Counter |
|---|---|---|
| **Add features that nobody asked for** | v0.13.2 auto-edges between anchor and Foundation children | Gate 1: ask first, get approval, log decision. |
| **Treat code comments as spec** | "synthetic anchor is read-only" → hid anchor handles | "Code comments are not spec" rule. Verify against SPEC.md. |
| **CSS-only fixes for behaviour bugs** | Hover handle tone-down via CSS opacity | "임시 통과 금지" trigger: find the responsible component, fix the responsibility. |
| **Editing god components further** | Adding a 30-line auto-edge block to the then-1476-line SketchCanvas | Gate 2: hold or reduce LOC; new responsibilities go in new files. |
| **Claiming "verified" without browser** | Type-check passes ≠ feature works | Gate 3: open the URL, click the thing. |
| **Silently rolling user-visible state** | (Hypothetical) Auto-rebalance Foundation nodes radially | Rule 7: any automated change to user-visible state needs explicit consent. |
| **Burying decisions in commit messages** | (Past pattern) "fix anchor click → no Inspector" with no DECISIONS entry | Gate 4: every user-visible decision = a `D-YYYY-MM-DD-X` entry. |
| **Decorating a node with paint-outside-box CSS** | `outline` + `outline-offset-2` + `ring-1` on the project anchor — clicks on the visible decoration passed through to the pane (see D-2026-05-08-G) | Use `border` (part of border-box, hit-tested). Inset `box-shadow` is OK; outset isn't. Visual extent and click target of an interactive node must coincide. |
| **Adding any cursor / handle / pan override on top of RF defaults** | v0.13.3 → v0.13.5 stacked six rounds of cursor / handle interventions; each fix introduced or revealed the next round's bug, ending with a full reset in v0.13.6 (see D-2026-05-10-C) | Default to React Flow vendor CSS (`reactflow/dist/style.css`, `@reactflow/node-resizer/dist/style.css`). To deviate, open a fresh `D-YYYY-MM-DD-X` entry, get user approval, and add the rule to `styles.css` with an `!important` comment naming the decision id. The override stack itself is the regression engine — never grow it without an audit trail. |
| **Bundling a cross-cutting visual change with a feature change in one commit** | v0.13.10 shipped `styles.css` cursor patch + auto-layout button move together. The visual fix turned out to address a latent RF v11 + Tailwind preflight bug that had existed since v0.13.0; the auto-layout feature commit became the cognitive scapegoat for ~6 cursor rounds (see D-2026-05-11-C). | Pre-commit gate (`pre_commit_gate.py::cross_cutting_bundle_check`) blocks. Split into two atomic commits: visual fix first (own D-id), feature second. The static guard `viewer/tests/styles-cursor-baseline.test.tsx` further locks `styles.css` to zero cursor rules. |
| **Hardcoding user-facing UI text in a viewer component** | Novel is a global service (user direction 2026-05-10: *"이건 글로벌 서비스가 될거거든요"*). A hardcoded English or Korean string in a `.tsx` file bypasses the i18n resource bundle and creates per-component sprawl that resists later migration. | Route every user-facing string through `useTranslation()` + `t("namespace.key")`, with the value added to BOTH `viewer/src/i18n/locales/en.json` (primary) and `viewer/src/i18n/locales/ko.json` (Korean). The `i18n-keys-parity.test.tsx` static guard fails the build if locales drift. See D-2026-05-11-D. |
| **Treating raw JSON as a domain entity (no `fromJson` boundary)** | Pre-v0.15 god `SketchNode` interface: UI code read `.what_we_do` directly off the wire shape, no class, no invariant check, no normalisation. The v0.15 reset (D-2026-05-12-B) retired this by introducing per-kind classes in `viewer/src/domain/{Kind}.ts` with `fromJson` / `toJson` / invariant boundaries (15 at the time; the palette is expanding per D-2026-06-17-D/F/I — `feature` / `note` / `entity`). Adding **any new kind** without the class is the new shape of the old mistake. | Every new kind lands as a domain class via the `mashbill-entity-template` skill (14-step walk). The `fromJson` method is the **JSON↔domain boundary** — invariants throw `DomainParseError` there, not in UI validation. Three static guards enforce no regression: `no-god-import.test.tsx` (Phase C, types.ts re-export only + per-kind file exists + `{Kind}Json` exported + `registerKindParser` called), `entity-roundtrip.test.tsx` (Phase D, `fromJson` ∘ `toJson` is identity for every kind), and server-side `test_schema_parity.py` (Pydantic ↔ TS interface drift). See D-2026-05-13-D / E. |

---

## Open meta-rules (not yet enforced; awaiting setup)

- **Session-start readback hook** — automate the "read DECISIONS.md +
  SPEC.md before answering" gate. Today this is a manual rule; a
  SessionStart hook (or skill) should surface the relevant entries
  automatically. See pending decision item.
- **Pre-edit gate hook** — block writes to `SketchCanvas.tsx` /
  `SketchInspector.tsx` / `App.tsx` / `SketchStencil.tsx` unless the
  edit reduces LOC, with a confirmation prompt. Today this is a
  manual rule.
- **Pre-commit gate** — run type-check + viewer tests + a "behaviour
  smoke" set (Foundation renders without auto-edges; anchor remains
  draggable; ⚠ badge contrast ≥ 4.5:1). Today only the first two run.

These will get added when one of them blocks real work; do not build
hooks speculatively (YAGNI).
