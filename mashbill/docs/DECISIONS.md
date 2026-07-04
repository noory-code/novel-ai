# DECISIONS — Novel UX / behaviour log

> Every decision that shapes how Novel **looks or behaves** belongs here.
> If a UI / behaviour change is not represented by an entry below (or
> by an explicit line in [`SPEC.md`](./SPEC.md)), it was not properly
> agreed and should be reverted.

---

## How to use this file

**Before** a UI / behaviour change:
1. Check [`SPEC.md`](./SPEC.md) — does it cover this?
   - If yes: implement what the spec says.
   - If no: **stop. Ask the user.** Don't read code comments and treat
     them as spec — comments are not approved decisions.
2. After user gives direction, append a `D-YYYY-MM-DD-X` entry below
   *first*, then implement.

**After** a change ships:
- Mark the decision **Accepted** if the user kept it after seeing it.
- Mark it **Rejected** if the user asked to revert.
- Rejected entries stay in the log so the next session knows not to
  re-propose the same idea.

**Entry template:**

```
### D-YYYY-MM-DD-X — short title

- **What:** the proposed / made change in one line.
- **Why:** the rationale (problem the change addresses).
- **Alternatives:** what was considered and rejected.
- **Approval:** Accepted | Rejected | Pending — by whom, when.
- **Spec impact:** which line of SPEC.md this updates (if any).
```

---

## Log

### D-2026-07-04-M — feature detail seeds one real subject ref, not English stubs

- **What:** `sync_details_with_overview` seeds a new feature detail canvas
  with the feature node + ONE actor_ref pointing at the first user-side
  actor on the actors canvas under its current label — the two hardcoded
  English stubs ("→ Operator"/"→ User") are gone.
- **Why:** live coupang review — 19 of 22 detail canvases were stub-only
  shells ("기능 캔버스 안에 아무것도 없네요"); the Operator stub had been
  semantically retired since D-2026-05-28-J/K but the seeder still planted
  it, in English, pointing at possibly-renamed seed actors.
- **Approval:** Accepted by user (live review, 2026-07-04).
- **Spec impact:** `test_sync.py::test_sync_seeds_one_real_user_side_ref_not_english_stubs`.

### D-2026-07-04-L — entity relationship lines carry their verb

- **What:** services + entities framings require a verb label on every
  entity relationship line (주문 —담는다→ 상품); unlabeled = unfinished.
- **Why:** live coupang review — 7 entity lines, zero labels; the picture
  read as nothing. Rule 5 ("never emit a meaningless line") already banned
  this in spirit; the framing now says it operationally.
- **Approval:** Accepted by user (live directive, 2026-07-04).
- **Spec impact:** `test_chat_context.py::test_entity_relationship_lines_carry_a_verb_label`.

### D-2026-07-04-J — families take domain words; same-nature families nest (actors)

- **What:** the actors framing tells the coach (1) the seeded 운영자/사용자
  labels are placeholders to RENAME into the service's own words (쿠팡:
  사용자 → 구매자), and (2) same-nature families nest under one parent
  (광고주·카드사·은행 → 파트너/3rd party) so the top level stays a handful.
- **Why:** live coupang review — "너무 운영자와 사용자에 얽매이는 것
  같은데" + "카드사나 은행 그리고 광고주 도 파트너 혹은 3rd party 라고
  묶을 수 있죠." The hierarchy is the coach's understanding made visible;
  generic seed taxonomy is not understanding.
- **Approval:** Accepted by user (live directives, 2026-07-04).
- **Spec impact:** `test_chat_context.py::test_actors_seed_families_are_renamed_to_domain_words`.
- **Follow-up (same day):** 운영자 = the INTERNAL-STAFF family ("운영자는
  내부직원이라는 뜻입니다") — employed operational roles (배송 기사, 물류,
  CS) nest under it, not beside it. Same test extended (v0.158.1).
- **Follow-up 2 (same day):** membership is decided by the EMPLOYMENT
  relation, not the role name — a gig rider may be external (파트너); the
  coach asks when ambiguous (v0.158.2).

### D-2026-07-04-I — value-exchange lines: dashed, layout-weak; seeded families spoke (actors)

- **What:** three user directives from the live coupang review: (1) value-
  exchange (labeled flow) lines on the actors canvas render DASHED
  ("가치교환에 대한 거니까" — viewer `dashValueExchange` prop, Actors-only
  opt-in); (2) auto-layout ranks structure first — hub spokes + inheritance
  build the spanning tree, flow lines only attach otherwise-unreachable
  nodes ("가치 교환은 정렬 할 때 우선순위를 낮춥니다", actors-only in
  effect); (3) the coach wires SEEDED families to the anchor too (운영자
  floated hub-less in the verification round). SketchCanvas ceiling
  563 → 567 (plumbing-only prop threading).
- **Why:** with taxonomy and value flows now coexisting on one canvas
  (D-2026-07-04-G), the two meanings must read apart at a glance and the
  skeleton must own the geometry.
- **Approval:** Accepted by user (live directives, 2026-07-04).
- **Spec impact:** viewer `edge-transform.test.ts` (dash pins),
  `mindmapLayout.test.ts` (structure-first spanning tree),
  `test_chat_context.py` (seeded-family spokes).

### D-2026-07-04-H — summary becomes writable; seeds mint localized (B-32/B-19)

- **What:** (1) identity's writable-fields allow-list gains ``summary`` and
  drops ``body``; (2) ``create_project(locale=...)`` mints seed placeholder
  labels in the viewer's language (ko: 미션/코어밸류/보이스/운영자/사용자),
  wired viewer→endpoint→seeder; the sim harness sends ko.
- **Why:** the coupang verification round showed the v0.154.0 summary rule
  never landing — the fail-safe allow-list rejected the field the prompt
  demanded (rule without capability). And the seeded labels stayed English
  in a Korean project, the second confirmed sighting of B-19.
- **Alternatives:** coach renames kind-name labels per conversation language
  — rejected (fixes only coached canvases, costs prompt budget); Korean-only
  hardcoded seeds — rejected (Novel is a global service, D-2026-05-11-D).
- **Approval:** Accepted by user (live loop, 2026-07-04).
- **Spec impact:** pins in ``test_update_node.py`` (allow-list + end-to-end
  summary write), ``test_endpoints_projects.py`` (localized seeds), viewer
  ``create-project-locale.test.ts`` (locale sent, normalized).

### D-2026-07-04-G — actors edges: labeled = flow, arrow points at the family (B-34/B-35)

- **What:** (1) `classify_edge`/`classifyEdge` on the actors canvas returns
  flow when a label arrives at creation, inheritance otherwise; (2) the
  coach draws inheritance child → family (matching `fold_endpoints`'s
  target-is-parent convention) with handles child-top → family-bottom;
  (3) `fold_endpoints`/`foldEndpoints` exclude actors-canvas flow edges
  from the fold hierarchy (peer exchange ≠ containment).
- **Why:** user live-watch — fold buttons sat on LEAF actors ("접기 기능이
  가장 말단에 있는데 이거 잘못된거 아닌가요?") and the actors edges needed
  auditing ("액터 캔버스 연결선 확인하세요"). Root cause: the v0.152.0
  hierarchy prompt said family → actor, contradicting the stored fold
  convention; and the v0.30.0 single-type table stamped value flows as
  inheritance.
- **Alternatives:** flipping the viewer fold convention instead — rejected
  (converge normalization + actorInheritance + user-drawn edges all assume
  target = parent); a data migration for existing canvases — deferred,
  fix-forward (live rounds re-create canvases).
- **Approval:** Accepted by user (live directives, 2026-07-04).
- **Spec impact:** truth tables mirrored byte-for-byte both sides; pins in
  `test_edge_semantics.py`, `test_create_edge.py`, `test_chat_context.py`,
  viewer `edge-semantics.test.ts` / `fold-hierarchy.test.ts`.

### D-2026-07-04-F — mission one-liner, identity summaries, flow immediacy (B-30/B-32/B-21)

- **What:** three coach-prompt rules from the live canvas-by-canvas rounds:
  (1) the mission statement is ONE line, reasoning to the note; (2) EVERY
  filled identity — seeded included — gets a one-line summary + description;
  (3) the actors coach draws value-flow lines in the same turn an actor
  registers, never deferred to the end.
- **Why:** live watching — mission faces arrived as paragraphs; the seeded
  Voice had no summary so its face was blank; the coupang round closed with
  12 actors and 0 flows despite the B-21 rule (deferral loophole).
- **Alternatives:** raising the word budget again — rejected; trimmed the
  foundation framing instead (compress-before-add, D-2026-07-03-U).
- **Approval:** Accepted by user (live directives, 2026-07-04).
- **Spec impact:** chat prompt only; tests
  `test_mission_lands_as_one_line_with_detail_in_the_note`,
  `test_actors_flows_land_with_each_registration`.

### D-2026-07-04-D/E — viewer-side (novel repo) id reservations

- **What:** D = a kind's pinned hub side is the layout SSOT (unpinned seeds
  join it); E = the visual arrowhead swap carries stored handles (B-28).
  Logged here to keep the single D-id namespace coherent; full context in
  novel repo commits 5382340 / 62bffcd.
- **Approval:** Accepted by user (live rounds, 2026-07-04).

### D-2026-07-04-A/B — viewer-side (novel repo) id reservations

- **What:** A = mindmap layout groups same-kind branches into one hub sector
  (B-20); B = per-kind node face — mission=statement, value=body,
  identity=summary — with the identity `summary` field added engine-side in
  v0.151.0 (B-24). Full context in novel repo commits 6b18606 / e7ebb5e.
- **Approval:** Accepted by user (live rounds, 2026-07-04).

### D-2026-07-04-C — edge handles pin at creation; layout follows (B-26)

- **What:** create_edge stores handles — anchor spokes per target kind
  (core_value l / identity r / mission t, target gets the opposite side);
  inheritance edges b→t. Flows stay floating.
- **Why:** User: moving a node moved its connection point; wants fixed points
  WITH grouping. Stored handles are already the viewer/layout SSOT
  (D-2026-06-01-H), so pinning at creation makes grouping stable by
  construction.
- **Approval:** User directive ("연결점 고정. 그룹화 잘하는 방법을 찾으세요"),
  2026-07-04.
- **Spec impact:** Pinned by
  ``test_create_edge.py::test_create_edge_pins_handles_for_anchor_spokes_and_hierarchy``.

### D-2026-07-03-W — the synthetic anchor is visible in agent canvas reads

- **What:** The agent-facing canvas read injects the project anchor (kind
  ``project``, a labelled hub entry) on foundation/actors/services — mirroring
  what the viewer renders. Storage unchanged (anchor stays synthetic).
- **Why:** User proposal during the live loop: edge fixes (D-T) made the anchor
  a legal endpoint, but the coach still could not SEE the hub in get_canvas —
  anchor knowledge lived only in prompt special-cases.
- **Approval:** User ("헤드리스라도 넣어주면 좋지 않을까요? 앵커 개념을?"),
  2026-07-03 밤.
- **Spec impact:** Pinned by
  ``tests/test_mcp_tools.py::test_get_canvas_surfaces_the_synthetic_anchor``.

### D-2026-07-03-U — B-17/B-18 rules land; prompt budget 1,300 → 1,350

- **What:** Services framing gains the two-way feature/service discriminator
  (B-17) and ERD-style entity relationship edges via create_edge (B-18); the
  saturation budget rises to 1,350 words.
- **Why:** Live-watch reports. The raise: evaluation principles moved OUT to
  the get_design_principles tool (D-2026-07-03-P), and successive user-directed
  mechanics (anchor parent, label rules, entity edges) exhausted the 1,300
  headroom — further micro-trims had started cutting elicitation wording.
- **Approval:** User bug reports + 자율실행, 2026-07-03 밤.
- **Spec impact:** Pinned by the two new framing tests + the budget guard.

### D-2026-07-03-T — the synthetic anchor is a first-class edge/near endpoint (B-14)

- **What:** create_edge accepts ``__project_anchor__`` as an endpoint (spokes
  mirror seed edges, relation ``flow``); create_node's ``near=anchor`` falls
  back to kind-clustering; the write playbook names the anchor as the
  foundation parent.
- **Why:** Live-watch B-14 + canvas forensics: every coach-registered value
  floated (edge tool rejected the anchor — it is viewer-synthetic, not in
  ``nodes``) and pillars marched rightward (coach chained near=<previous
  sibling> for lack of a nameable parent), overlapping identity.
- **Approval:** User bug report ("여전히 연결선을 못 만드는데?"), 2026-07-03 밤.
- **Spec impact:** Foundation pillars are now AI-connectable to the anchor —
  edges governed by definition, not authorship (D-2026-06-17-J). Pinned by
  ``test_create_edge.py::test_create_edge_accepts_the_synthetic_anchor`` +
  ``test_create_node.py::test_create_node_near_synthetic_anchor_uses_kind_cluster`` +
  ``test_chat_context.py::test_write_playbook_names_the_anchor_as_foundation_parent``.

### D-2026-07-03-S — identity keeps one prose field: description (B-15)

- **What:** Identity's 설명(description) is the single prose field; the
  inspector's 노트(body) field is removed and a non-empty body folds into
  description on read. Supersedes the D-2026-06-06-B split.
- **Why:** User live-watch (B-15): the two fields duplicate each other for a
  kind whose content is one voice/tone description.
- **Approval:** User bug report + field choice ("설명이다"), 2026-07-03 밤.
- **Spec impact:** Pinned by ``tests/test_identity_format_migration.py`` fold
  tests + novel ``inspectors-per-kind`` / ``inspectors.smoke`` pins.

### D-2026-07-03-R — unique-kind labels stay the kind name (B-12, refines L)

- **What:** Mission/identity labels = kind name in the user's language; content
  never goes in the label. Multi-instance kinds keep the meaningful-label rule.
- **Why:** User live-watch (B-12): the coach renamed the mission node to its
  content sentence. Q (viewer, novel repo) reverses the face excerpt the same
  session (B-13) — labels + save pulse are the canvas feedback.
- **Approval:** User bug report, 2026-07-03 밤 (live watch).
- **Spec impact:** Pinned by
  ``tests/test_chat_context.py::test_write_playbook_fills_placeholder_labels_too``.

### D-2026-07-03-P — the principles ride as an MCP tool, consulted before challenging

- **What:** ``get_design_principles(area)`` (MCP tool) serves the distilled
  discriminators; the propose playbook adds one line: consult it before
  challenging weak content, challenge as questions. Runtime copy =
  ``mashbill/coaching_principles.py``; canon = workspace
  ``docs/concepts/design-principles.md`` (sync canon → engine on change).
- **Why:** Prompt budget (≤1,300 words) can't hold the principles; the
  discuss-note verdict (2026-07-02) already picked MCP-carried over installed
  skills for the in-app coach. Tool-served text loads only when the coach
  judges — zero cost on ordinary turns.
- **Approval:** Implements the user's distilled-principles selection
  (D-2026-07-03-O); wiring within 자율실행 승인.
- **Spec impact:** Pinned by ``tests/test_mcp_tools.py`` (registry + content)
  and ``tests/test_chat_context.py::test_coach_consults_design_principles_when_judging``.

### D-2026-07-03-O — coach design knowledge = distilled principles, not RAG

- **What:** The coach's design knowledge (what makes a good mission / value /
  feature design — the source of "propose the higher-level concept the user
  hasn't reached") will be curated principles distilled into coach
  instructions/skills, NOT a vector-RAG corpus.
- **Why:** The 20-iteration benchmark loop proved the distill-and-pin pipeline
  works (phrase guards + budget + measurable axes); RAG adds infrastructure,
  latency, and quality variance for breadth the coach doesn't yet need.
- **Alternatives:** vector RAG over design books — rejected for now; hybrid
  (principles in prompt + deep material as MCP resources) remains the natural
  extension path if breadth is needed later.
- **Approval:** User selection (AskUserQuestion, 2026-07-03 밤).
- **Spec impact:** none yet — implementation design queued (todo/active.md);
  prompt budget requires the principles to live outside the per-turn prompt.

### D-2026-07-03-L — the coach fills placeholder labels in the same write

- **What:** WRITE_PLAYBOOK: when filling a node whose label is still a
  placeholder (Mission, Core value, Voice), the same update_node call also
  sets a short meaningful label.
- **Why:** Chrome-UI smoke: the coach saved a mission statement but the canvas
  face showed only the default label — no visible change. User picked all
  three feedback mechanisms (label fill + face excerpt + save flash).
- **Approval:** User selection, 2026-07-03 (AskUserQuestion, all three).
- **Spec impact:** Coaching behaviour. Pinned by
  ``tests/test_chat_context.py::test_write_playbook_fills_placeholder_labels_too``.

### D-2026-07-03-M — the node face previews its content (viewer, novel repo)

- **What:** useNodesMemo maps an excerpt of the node's primary text
  (mission statement / prose body, 120 chars) into the face body preview —
  it was hardcoded to "" so no node ever showed content.
- **Why / Approval:** same finding and user selection as D-2026-07-03-L.
- **Spec impact:** Viewer display. Pinned by novel
  ``viewer/tests/node-face-content.test.ts``. Verified live in the browser.

### D-2026-07-03-N — the canvas pulses when content lands (viewer, novel repo)

- **What:** ``useContentFlash`` (new hook) flips a highlight class on a node
  for ~1.5s whenever its label/body signature changes after mount; BaseNode
  wires it; keyframes in styles.css. Local edits flash too (accepted).
- **Why / Approval:** same finding and user selection as D-2026-07-03-L.
- **Spec impact:** Viewer display. Pinned by novel
  ``viewer/tests/node-save-flash.test.tsx``. Verified live (MutationObserver
  caught the pulse on a WS-driven write).

### D-2026-07-03-K — the batch-landing rule is restored (same-day revert of D-2026-07-03-I)

- **What:** The foundation framing's batch-landing sentence returns; the
  absence-guard flips back to a presence pin.
- **Why:** Removal regressed values in BOTH v0.143 confirmation runs (12-turn:
  3 and 2 registered vs the v0.142 arm's 5–7; judged 1/7) while features and
  entities ballooned (38/28) — the rule never fired as written (no
  multi-register, transcript-audited) yet its presence held session energy on
  the value hunt. Dead by the letter, load-bearing in effect.
- **Alternatives:** rewriting it as an explicit "keep landing values" pressure
  rule — deferred: restore the proven text first; rewording is a fresh
  iteration with its own measurement.
- **Approval:** Accepted by user (자율실행 승인; same-day-rollback honesty per
  operational rule 3).
- **Spec impact:** Restores D-2026-07-03-G behaviour. Lesson: never judge a
  prompt rule by compliance alone — measure removal. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_lands_values_in_batches``.

### D-2026-07-03-J — dev MCP entry is stdio-only, like the frozen one (B-11)

- **What:** The dev-checkout MCP entry (``uv run … python -m mashbill``) gains
  ``--mcp-stdio``; ``__main__`` dispatches that flag to the stdio-only
  transport. A registered tool server never starts the HTTP listener.
- **Why:** B-11 (found by the Chrome-UI smoke, 2026-07-03): the full engine
  binds the default HTTP port whenever free, so every in-app coach turn's
  spawned tool server could capture :5190 — blocking a real engine from
  starting, invisibly in normal use because the user's engine already holds
  the port. The frozen entry has passed ``--mcp-stdio`` since D-2026-06-14-A
  for exactly this collision; the dev path was asymmetric.
- **Alternatives:** an env toggle in the coach's mcp-config only — rejected:
  external dev-checkout registrations have the same race; the flag fixes all
  spawn paths symmetrically.
- **Approval:** Accepted by user (수렴 후속 자율실행 승인, 2026-07-03).
- **Spec impact:** none user-visible. Pinned by
  ``tests/test_server.py::test_module_main_dispatches_mcp_stdio_flag`` +
  ``tests/test_mcp_registration.py::test_plot_entry_dev_command_is_stdio_only_too``.

### D-2026-07-03-I — the batch-landing rule is removed as a dead letter (twentieth sim iteration)

- **What:** The foundation framing's batch-landing sentence (values put on the
  table together, multi-registered per turn — D-2026-07-03-G) is removed; a
  guard now pins its absence.
- **Why:** Agent transcript audit of three v0.142 runs: the rule never fired —
  strict one-value-per-turn everywhere; it structurally loses to the
  one-question-at-a-time tone rule. The values goal was reached by the domain
  sweep (D-2026-07-03-H) × the 12-turn session budget instead (dual-arm
  experiment: coverage ~2/7 → 4/5–6/7). A dead instruction costs prompt budget
  and keeps a live conflict between blocks.
- **Alternatives:** rewriting the tone rule to allow multi-item turns —
  rejected: one-at-a-time warmth is a pinned coaching principle
  (D-2026-06-24-J) and the goal is already met without batching.
- **Approval:** Accepted by user (수렴 후속 자율실행 승인, 2026-07-03).
- **Spec impact:** Supersedes D-2026-07-03-G. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_has_no_batch_rule_residue``.

### D-2026-07-03-H — the value hunt sweeps domains, numeric anchors removed (nineteenth sim iteration)

- **What:** Foundation framing sweeps the value TERRAIN — distinct domains
  (customers, quality, speed vs polish, money vs principle, how people work),
  probing one the talk hasn't touched before closing — and drops its numeric
  anchors: the identity checkpoint triggers on "once the first values stand",
  the batch rule on "as the talk surfaces candidates"; only the anti-anchor
  ("never settle for the first two or three") still names a number.
- **Why:** Five consecutive measurements (v0.137–141) held values coverage at
  ~2/7 while registration snapped to exactly the numbers the prompt named —
  anchors read as quotas. Registered values cluster mission-adjacent; corpus
  values span operating principles nobody fished for. Domain sweep changes
  what gets fished; anchor removal stops the early close.
- **Alternatives:** more turns — being measured separately as a harness arm
  (12-turn sample), per the same user directive; a fixed value-count target —
  rejected: it recreates the anchor problem.
- **Approval:** Accepted by user ("셋다해요", 2026-07-03 — card ① of three).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_sweeps_value_domains_without_numeric_anchor``.

### D-2026-07-03-G — values land as a batch, not a drip (eighteenth sim iteration)

- **What:** Foundation framing: once the mission talk holds two or three
  candidate values, the coach puts them on the table together and registers
  every confirmed one in the same turn — no one-value-per-turn drip.
- **Why:** v0.140 sample: the pit-stop rule fixed identity (3/3) and challenge
  (all present) but values registration stayed at 2–3 — the ceiling is
  structural: one-per-turn landing × 8-turn budget caps at 2–3, whatever the
  prompt says about returning to the hunt. Batch landing changes the cadence,
  not the budget.
- **Alternatives:** raise the foundation turn budget — rejected twice already
  (harness knob); registering unconfirmed values — violates the write gate.
- **Approval:** Accepted by user (standing improve directive; 자율 실행 승인
  2026-07-03).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_lands_values_in_batches``.

### D-2026-07-03-F — canvas text must be natural, correctly-spelled Korean (B-10)

- **What:** The write playbook demands that everything written onto a canvas be
  natural, correctly-spelled Korean in the user's own words — no translationese,
  no typos — reread before saving. The sim judge gains a language axis that
  sweeps canvas labels for violations.
- **Why:** User report (2026-07-03): the coach registered "자유하되, 방치하지
  않는다" — "자유하다" is not a Korean verb — compressing the founder's natural
  phrasing into translationese; the sweep also found hangul typos landed as
  entity labels (캐페인, 리봰, 숬폼). Both founder families showed it, so it is
  coach-side. Canvas artifacts are user-facing product output.
- **Alternatives:** post-hoc lint of canvas files — rejected for now: silent
  automated rewrites of user-visible state would breach Rule 7; measurement
  (judge axis) + prompt rule first.
- **Approval:** Accepted by user (bug report + "계속합시다", 2026-07-03).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_write_playbook_demands_natural_korean``.

### D-2026-07-03-E — the identity confirm is a pit stop, not the finish line (seventeenth sim iteration)

- **What:** Foundation framing names the mid-phase identity checkpoint as a pit
  stop: registering the identity does not end the value hunt — the coach goes
  straight back to the next fork until the founder runs dry.
- **Why:** Values stalled at 1–3 registered in all 11 runs of 2026-07-03,
  across personas and founder model families (the codex-founder pairwise
  experiment excluded same-family rapport as a cause) — the "once two or three
  values stand" anchor (D-2026-07-03-A) read as a quota and the return clause
  never fired.
- **Alternatives:** raise the foundation turn budget — rejected before
  (D-2026-07-03-A): harness knob, not a coach skill.
- **Approval:** Accepted by user (standing improve directive; 자율 실행 승인
  2026-07-03).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_resumes_value_hunt_after_identity``.

### D-2026-07-03-D — the coach prompt compresses under a word budget (sixteenth sim iteration)

- **What:** The composed canvas system prompt is rewritten for density — zero
  rule loss, all cross-block duplicates collapsed to one home (upstream-reference
  matching: COACH_TONE → WRITE_PLAYBOOK; pace playbook's per-canvas enumerations →
  the framings that already carry them; save-gate restatements → one line each).
  Foundation 1,828 → 1,219 words, services 1,954 → 1,296. A saturation guard
  (``test_system_prompt_stays_under_saturation_budget``) pins every composed
  canvas prompt at ≤ 1,300 words: future rotations must compress before adding.
- **Why:** Fifteen add-only rotations saturated the prompt; the v0.138 sample
  showed instruction *slips* (a feature batch with no connecting edges — first
  since v0.128; one "저장했어요" announcement) rather than missing rules. When
  every rule is present but some stop firing, the lever is size, not content.
- **Alternatives:** keep adding sharper rules — rejected: that is the mechanism
  that produced the saturation; the ~30 phrase guards already pin the content,
  so compression is safe and additive rules are not.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02 밤;
  compression queued as rotation 16 in todo/active.md).
- **Spec impact:** Coaching behaviour only — no rule added or removed. Content
  pinned by the existing phrase guards in ``tests/test_chat_context.py`` +
  ``tests/test_chat_system_prompt.py``; size pinned by the new budget guard.

### D-2026-07-03-A — identity lands mid-phase, after 2-3 values stand (thirteenth sim iteration)

- **What:** Foundation framing: once two or three values stand, draft the identity
  from the mission and values for a quick confirm, then return to hunting values.
  A foundation session ending with an empty identity is named a failed session.
- **Why:** Round 3: identity unfinished in 12/12 runs (round 2: all complete).
  Values-until-dry (D-2026-07-02-Q) consumed the phase and the pace playbook's
  wrap-up never fired — the coach cannot see the session ending, so the landing
  point must be positional (mid-phase), not temporal (wind-down).
- **Alternatives:** longer foundation turn budget — rejected: harness knob, not a
  coach skill; real sessions are budget-bound too.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02 밤 "밤새 돕시다").
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_lands_identity_mid_phase``.

### D-2026-07-03-B — the coach proposes candidate values it hears (fourteenth sim iteration)

- **What:** The core-value interview alternates probing with PROPOSING — the coach
  names the candidate values it hears in the mission talk, one or two at a time.
- **Why:** Round 3: values depth collapsed with the recalibrated (guarded) founder
  personas — probing alone stalled at 1–3 values, while the terse run proved
  reaction-to-draft elicitation works (1→5 registered). A guarded founder reveals
  through reactions what they never volunteer.
- **Alternatives:** probe-only with more turns — rejected: budget-bound and
  persona-dependent.
- **Approval:** Accepted by user (standing improve directive).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_proposes_candidate_values_from_the_talk``.

### D-2026-07-03-C — entities register in the same breath as each feature batch (fifteenth sim iteration)

- **What:** Services framing: the entity map lands with EACH service's feature
  batch (2–5 per service is normal), never as a deferred pass; features standing
  with zero entities mean the service is unfinished — checked before moving on.
- **Why:** Round 3: all-or-nothing entity behaviour (0 in 9 of 12 runs vs 9/9/23) —
  the single "before leaving the canvas" checkpoint fired too late or never.
  Attaching the habit to a per-service event makes it fire N times, not once.
- **Alternatives:** engine-side auto-derivation without the coach — rejected: the
  entities canvas is AI-maintained but content must come from the design talk
  (D-2026-06-17-I), not a silent batch job.
- **Approval:** Accepted by user (standing improve directive).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_services_framing_registers_entities_with_each_feature_batch``.

### D-2026-07-02-T — flooding replies get distilled and landed, not chased (twelfth sim iteration)

- **What:** The propose playbook's reply-weight rule gains its second pole: when
  replies flood (long tangents, several ideas at once), the coach acknowledges in a
  line, distills the usable pieces (a value, an actor, a feature, a body line),
  lands each into its node while fresh — proposing the distilled text for a quick
  yes — then steers back to the thread.
- **Why:** Persona round (2026-07-02, YouTube × rambler): 6 actors registered,
  ZERO with body text; the content was all said but never anchored. The pace
  playbook says land items, but nothing told the coach what to do when the user's
  torrent keeps moving the conversation before anything lands.
- **Alternatives:** summarising at canvas end — rejected: by then the tangent's
  content is stale and the founder's words are gone; capture must be in-flow.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_propose_playbook_distills_flooding_replies``.

### D-2026-07-02-S — thin replies flip the coach into draft-first mode (eleventh sim iteration)

- **What:** The propose playbook now reads reply weight: when the user's replies
  come back thin (a word, a fragment, a bare yes), the coach stops widening with
  open questions and narrows to draft-first mode — ONE concrete candidate at a
  time, answerable in a word, landing items at that yes/no rhythm.
- **Why:** Persona round (2026-07-02, Discord × terse): a terse founder answers a
  broad question with less, not more. The coach kept asking open questions and
  produced the worst elicitation of any run — one core value (J 1/7), unfinished
  identity, reference slots half-empty. The existing "when the user is vague or
  stuck, lead with your proposal" line did not fire because terse answers are
  neither vague nor stuck — they are short but definite.
- **Alternatives:** a persona classifier / mode switch in the engine — rejected:
  reply weight is visible in the conversation itself; a prompt rule suffices and
  degrades gracefully when the user opens up.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_propose_playbook_switches_to_drafts_on_thin_replies``.

### D-2026-07-02-R — the service landscape spans value exchanges, not internal layers (tenth sim iteration)

- **What:** The services framing now defines a service as one value-exchange surface
  (a distinct pair of sides trading value), states the landscape SPANS the different
  exchanges the mission reaches rather than slicing one exchange into internal
  layers, and — when the map covers only one exchange — has the coach ask what
  other exchanges the vision touches before drilling in.
- **Why:** Benchmark round 2 (2026-07-02, Uber): the landscape-first rule
  (D-2026-07-02-K era) fired, but the "map" it drew was four horizontal layers of
  ONE marketplace (matching·safety·settlement) — semantically a single exchange.
  The rule said "map first" without pinning what counts as a member of the map.
  This aligns the coach with the root concept canon (a service = value exchange).
- **Alternatives:** post-hoc dedup of layer-like services — rejected: the failure is
  at proposal time; teaching the member definition prevents it, a cleanup can't.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_services_framing_landscape_spans_exchanges_not_layers``.

### D-2026-07-02-Q — foundation interview draws core values out until the founder runs dry (ninth sim iteration)

- **What:** The foundation framing's core-value interview now states: each recurring
  fork is a candidate value; after one value lands, hunt the NEXT fork and keep
  drawing until the user runs dry — never settle for the first two or three.
- **Why:** Benchmark round 2 (2026-07-02): J-values (semantic coverage vs published
  values) was the weakest axis in EVERY run — canvases held 2–3 values against
  ground truths of 4–8. The founder-sim knows more values and reveals them when
  probed; the coach simply stopped asking.
- **Alternatives:** a numeric quota ("collect at least 4") — rejected: a project may
  genuinely hold 3; the stop condition is the founder running dry, not a count.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02).
- **Spec impact:** Coaching behaviour only. Pinned by
  ``tests/test_chat_context.py::test_foundation_framing_draws_values_out_until_dry``.

### D-2026-07-02-P — a tool call resets the coach's turn text (pre-tool planning monologue is not reply)

- **What:** In the claude-code stream parser, a ``tool_use`` ``content_block_start``
  frame clears the accumulated turn text. Only text produced after the LAST tool
  call becomes the persisted assistant message / ``turn_complete`` text (the viewer
  already reconciles its streamed text against ``turn_complete``). Turns without
  tool calls are unchanged; text/thinking block starts do not reset.
- **Why:** Benchmark (B-9, 2026-07-02): 19 coach messages across every sim run
  opened with an English planning monologue glued to the Korean reply — "The user
  confirmed. Let me add it.네, 올라갔어요…". The model plans in text before
  calling tools; the pipeline concatenated every text block of the turn. This is
  the same internals-exposure D-2026-07-02-D banned, through a channel a system
  prompt cannot reach — a pipeline rule, not a prompt rule.
- **Alternatives:** (a) prompt-only ("never write text before tool calls") —
  rejected: unenforceable, D-2026-07-02-D already tried the prompt lever for this
  family; (b) buffering all text until turn end to filter — rejected: kills
  streaming; (c) regex-stripping English prefixes — rejected: heuristic, breaks
  legitimate English replies.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02); sim-found B-9.
- **Spec impact:** Chat pipeline behaviour (CHAT_ARCH territory, no canvas-rule change).
  Pinned by ``tests/test_claude_stream_parse.py`` (pre-tool drop / between-tools drop /
  no-tool keep / text-block-start no-reset).

### D-2026-07-02-O — entity registration is autonomous coach judgment (visible surfacing, no per-entity ask)

- **What:** The services framing now has the coach derive the entity map from the
  registered features and register the entities itself — no per-entity "등록해둘까요?"
  gate — mentioning it in one light conversational line. The user reviews / edits /
  deletes on the canvas (live-updating = visible, not silent). The confirm-first
  write gate is unchanged for foundation / services content.
- **Why:** User (2026-07-02): "엔티티는 찾을 수 없으니 자율적 판단이 필요" — a founder
  cannot name their data model, so asking them to approve each entity is theater.
  This is exactly the pinned model: the entities canvas is AI-MAINTAINED
  (D-2026-06-17-I), and Rule 7 / D-2026-06-16-P bans *silent finalization*, not
  autonomous surfacing — an entity appearing on a live canvas the user can edit or
  delete IS the review surface.
- **Alternatives:** batch-confirm before leaving the canvas (previous iteration,
  D-2026-07-02-M) — retired: still asks the user to adjudicate what they can't know.
- **Approval:** Accepted by user (explicit direction 2026-07-02).
- **Spec impact:** Refines the entity-surfacing line of D-2026-07-02-I/M. Pinned by
  ``tests/test_chat_context.py::test_services_framing_derives_the_entity_map_unprompted``.

### D-2026-07-02-N — ``set_node_references``: the coach wires reference slots (seventh sim-benchmark iteration)

- **What:** New ``references`` module + MCP tool ``set_node_references(project_path,
  project_id, canvas_kind, node_id, refs, service_id?)`` — assigns a node's ``ref_*``
  fields from an allow-list per kind (service → ref_actor_ids / ref_value_ids /
  ref_identity_ids; step/feature → ref_entity_ids), validating every referenced id
  against its home canvas (actors / foundation / entities). Same read → merge →
  re-validate-whole-doc → atomic-write shape as ``update_node``. Playbook: wire the
  reference on the user's pick; empty slots = an unfinished service.
- **Why:** Benchmark (2026-07-02): reference slots 0/N in EVERY run. They are rightly
  protected from ``update_node`` free-text (D-2026-06-26-D red-team), but no tool
  could set them at all — the playbook demanded what the tool surface made impossible.
  Same defect family as ``create_edge`` (D-2026-07-02-J): the coach lacked hands, not
  instructions.
- **Alternatives:** loosening ``update_node``'s allow-list — rejected: free-text
  repointing is the exact risk the protection exists for; an explicit tool keeps
  id validation and intent.
- **Approval:** Accepted by user (standing improve directive, 2026-07-02).
- **Spec impact:** MCP surface + coaching behaviour. Pinned by
  ``tests/test_update_node.py`` (fill / unknown-master / non-ref-field / playbook).

### D-2026-07-02-M — coach derives the entity map unprompted; coach-registered features seed their detail canvas

- **What:** (1) Services framing: before leaving the canvas the coach DERIVES the
  entity map itself from the registered features — imagining the plausible data
  things they must act on, even ones nobody named — and proposes the batch for
  confirmation (still gated, strong-dedup). (2) The MCP ``create_node`` path now
  seeds a feature's detail canvas via the same sync the app's endpoint flow uses,
  so a coach-registered feature is drillable (기능 캔버스 exists).
- **Why:** User directives (2026-07-02): "엔티티는 상상해서라도 만들어보세요" — the
  reactive spot-a-thing instruction (D-2026-07-02-I) still produced 0 entities in
  runs where the founder never volunteered a data noun; derivation is the coach's
  leap, exactly the imagination the user wants. And "기능 캔버스 뜨지 않네?" — detail
  canvases seeded only through the app endpoint flow, so every sim/coach-registered
  feature had no drill-in canvas at all.
- **Alternatives:** running a separate entities-scope interview — rejected before
  (D-2026-07-02-I): entities are byproducts of design talk, not their own interview.
  Seeding detail canvases inside ``canvas_io.create_node`` — rejected: circular
  import (detail_sync imports canvas_io); the MCP wrapper mirrors the endpoint
  layer, where the app already does it.
- **Approval:** Accepted by user (explicit directives 2026-07-02).
- **Spec impact:** Coaching behaviour + MCP create side-effect. Pinned by
  ``tests/test_chat_context.py::test_services_framing_derives_the_entity_map_unprompted``
  + ``tests/test_create_node.py::test_feature_created_via_mcp_seeds_its_detail_canvas``.

### D-2026-07-02-L — ``near`` placement: a coach-registered child lands beside its parent (fifth sim-benchmark iteration)

- **What:** ``create_node`` gains an optional ``near=<node id>``: the new node is
  placed right of that anchor (one child column per anchor), stacking below earlier
  siblings within the anchor's band — overriding the kind-cluster heuristic
  (D-2026-07-02-C). Unknown anchor → ValueError (Fail Fast). The write playbook now
  has the coach pass the parent's id when registering a child (a feature near its
  service) in the same confirmed action as the connecting ``create_edge``. Placement
  policy split into its own ``placement`` module (500-line rule).
- **Why:** User, looking at a sim canvas (2026-07-02): "캔버스는 잘 못그리네..결함을
  고쳐야죠." Kind-clustering — right for peers like core values — piled every feature
  of EVERY service into one global column, so the drawing carried no structure even
  once edges existed. A child belongs beside ITS parent; the drawing must read as a
  hierarchy at a glance (thinking-through-sight).
- **Alternatives:** running auto-layout after coach writes — rejected: silent
  whole-canvas motion (Rule 7 / layout-saga lesson); initial placement should be
  right instead. Storing containment as ``parent_id`` — rejected: retired model
  (v0.26 directed edges are the SSOT).
- **Approval:** Accepted by user (2026-07-02 report + standing improve directive).
- **Spec impact:** Placement behaviour of coach creates. Pinned by
  ``tests/test_create_node.py`` (near-parent placement, unknown anchor, playbook
  guard + MCP schema pin).

### D-2026-07-02-K — services coaching maps the landscape first (fourth sim-benchmark iteration)

- **What:** The services framing now opens at canvas altitude: derive 3–6 candidate
  value-exchange services from the mission and actors, confirm the map with the
  user, register the confirmed ones — THEN detail each service one by one (slots,
  features). Explicit guard: never let the whole session sink into the first
  service named.
- **Why:** Benchmark (2026-07-02): real products run on 5–6 surfaces (Airbnb:
  Stays/Experiences/Hosting/Trust…; Netflix: streaming/games/live/ads/partnership)
  but the coach landed 2–3 and the semantic judge scored services worst (0–2/5) —
  it dove deep into the first service mentioned with no sweep of the landscape.
  Same thinking-through-sight logic as the canvas itself: the big picture first,
  then depth. User pressed the gap directly ("서비스는???").
- **Alternatives:** raising the services-phase turn budget — rejected: more turns
  spent the same depth-first way still misses the map; the order is the defect.
- **Approval:** Accepted by user (2026-07-02).
- **Spec impact:** Coaching behaviour (system prompt). Pinned by
  `tests/test_chat_context.py::test_services_framing_maps_the_landscape_first`.

### D-2026-07-02-J — `create_edge`: the coach connects what it registers (clobber-safe single-edge append)

- **What:** New engine primitive + MCP tool ``create_edge(project_path, project_id,
  canvas_kind, source_id, target_id, service_id?, label?)`` — the edge mirror of
  ``create_node``: validate both endpoints exist (Fail Fast), mint the id
  server-side, classify ``relation`` from canvas + source kind (the same SSOT the
  viewer uses), append the ONE edge, re-validate the whole doc, write atomically.
  **Idempotent** (an existing directed source→target line is returned, never
  duplicated). Lives in its own ``edge_io`` module (500-line rule). The write
  playbook now instructs the coach: when a registered node belongs to another (a
  feature under its service, a step after a step), connect it in the SAME confirmed
  action — one yes covers the node and its line; a registered node must never float
  unconnected.
- **Why:** Benchmark batch (2026-07-02): 40/40 coach-registered features floated
  unconnected — 0 service→feature edges across all runs — because the only edge
  write was the clobber-unsafe whole-doc ``update_canvas``. A scatter of unlinked
  nodes defeats thinking-through-sight (VISION). Edges are governed by their
  definition, not authorship (D-2026-06-17-J), and the containment line of a
  confirmation-gated create is part of that confirmed change (D-2026-06-16-P's
  build-through-discussion, same shape as D-2026-06-26-D's write-after-yes) — the
  services canvas's user-draw-only note in SPEC §Edges is amended accordingly for
  coach-registered containment edges.
- **Alternatives:** (a) auto-edge inside ``create_node`` via a parent param —
  rejected: hides the line inside a node write and revives the v0.13.2 silent
  auto-edge shape; an explicit tool keeps each artifact reviewable. (b) prompt-only
  fix telling the coach to use ``update_canvas`` — rejected: clobber-unsafe on a
  canvas another writer may touch.
- **Approval:** Accepted by user (standing directives 2026-07-02: 캔버스가 대화로
  자연스럽게 완성 + 문제있는 거 개선).
- **Spec impact:** SPEC §Edges services-canvas user-draw-only note amended (coach
  containment edges allowed on confirmed creates). Pinned by
  ``tests/test_create_edge.py`` (5 tests incl. the playbook guard).

### D-2026-07-02-I — coach surfaces entities from design talk; wraps up empty required items (second sim-benchmark iteration)

- **What:** (1) The services framing now surfaces entities as byproducts: when a
  feature handles a data 'thing' (a post, a payment, an account), the coach points
  it out and, on yes, registers it on the entities canvas — with the write playbook
  explicitly allowing that ONE cross-canvas create (still confirmation-gated,
  strong-dedup). (2) The pace playbook gains a wrap-up rule: when the conversation
  winds down with a required item still empty, draft it NOW from what stands and ask
  one quick confirm.
- **Why:** 8-service benchmark batch (2026-07-02): entities 0/8 — the
  surface-the-entity instruction lived only in the entities-scope framing, which no
  design conversation ever runs under, and the write playbook's "current canvas
  only" line blocked the byproduct registration. Identity filled only 3/8 —
  sessions ended with required items empty despite the derive instruction.
- **Alternatives:** running a separate entities-scope chat phase in the sim —
  rejected: the spec (entities canvas = AI-maintained byproduct, D-2026-06-17-I)
  says entities surface DURING feature/service design, not in their own interview.
- **Approval:** Accepted by user (direction 2026-07-02: "기능은?? 서비스는?? 엔티티는??"
  + standing improve-what's-broken directive).
- **Spec impact:** Coaching behaviour (system prompt). Pinned by
  `tests/test_chat_context.py::test_services_framing_surfaces_entities_as_byproduct`,
  `::test_write_playbook_allows_entity_registration_cross_canvas`,
  `::test_pace_playbook_wraps_up_missing_items`.

### D-2026-07-02-H — coach paces the whole canvas; services coaching proposes features early (first sim-benchmark iteration)

- **What:** Added a `PACE_PLAYBOOK` to the canvas system prompt (between
  `PROPOSE_PLAYBOOK` and `WRITE_PLAYBOOK`): budget the session across every concept
  the canvas needs; land an item once it is good enough (saved, confirmed) and move
  on instead of polishing; derive later items from what already stands (identity
  from mission+values, service slots seeded from foundation/actors) and offer the
  draft for a quick yes. Reworked the services framing: propose 3–5 concrete
  features as soon as the service's problem/value stand (slots 2–3), not after all
  five slots; reference slots fill via proposed matches along the way.
- **Why:** First finding of the coach-sim benchmark (2026-07-02, Airbnb full-flow
  baseline, 21 turns): quality per item was good (mission ≈ the real service's own
  mission; values carried tradeoffs) but the coach never FINISHED — identity empty
  after 8 foundation turns, zero features after 8 services turns, zero entities.
  Depth crowded out coverage; user direction: "헤드리스에서 완벽하게 돌아야" — the
  canvas must complete within a realistic session.
- **Alternatives:** raise sim turn budgets — rejected: real users won't give 20+
  turns per canvas; the coach's pacing is the defect, not the session length.
  Hard-coding a per-item turn cap in code — rejected: conversational judgment
  belongs in the prompt, not a mechanical cutoff.
- **Approval:** Accepted by user (direction 2026-07-02: "일단 문제있는거 개선하고" /
  "헤드리스에서 완벽하게").
- **Spec impact:** Coaching behaviour (system prompt). Pinned by
  `tests/test_chat_context.py::test_canvas_system_prompt_paces_the_whole_canvas` +
  `::test_services_framing_pulls_features_forward`. Baseline vs post-change
  comparison = sim reports before/after this version (0.125.x vs 0.126.0).

### D-2026-07-02-G — opening an existing subdir project always resolves its real dir (no bare-root guess; create self-heals into the existing project)

- **What:** Two viewer fixes in the project-open path. (1) The active project's
  effective ``project_path`` now derives from the discovery *state* and resolves to
  ``null`` (I/O holds) while the active id is not yet in the dir map — before, a
  URL-restored open raced discovery, guessed the bare workspace root ("." fallback),
  and the memo never recomputed once discovery landed (it read only a ref), so a
  subdir project 404'd forever. (2) ``create(targetDir)`` hitting the engine's
  one-project-per-dir guard (409, D-2026-06-21-AA) now re-discovers and OPENS the
  project actually in that dir instead of surfacing a raw error.
- **Why:** Dogfood report B-4 (2026-07-02): "기존거 열면 못여는데" — opening the
  workspace showed the existing project unreachable (404 at the bare root), and
  retrying through the folder picker produced a 409 error toast. Root cause was
  entirely viewer-side path resolution; the engine read the project fine.
- **Alternatives:** keep the "." fallback but force a refetch when discovery lands —
  rejected: still fires one guaranteed-wrong request per open (404 + error flash).
  Engine-side: relax the 409 into open-on-create — rejected: creation staying strict
  is correct (D-2026-06-21-AA); the *viewer* owns open-vs-create intent.
- **Approval:** Accepted by user (report 2026-07-02; fix under the standing
  record-and-regression-test directive).
- **Spec impact:** Behaviour fix, no rule change. Pinned by viewer
  ``tests/effective-project-path.test.tsx`` (URL-restored subdir project never fetched
  at the bare root) + ``tests/project-create-name.test.tsx`` (create self-heals into
  the existing project).

### D-2026-07-02-F — identity inspector hides the inert status / provenance inputs (code catches up to D-2026-06-16-O)

- **What:** Removed the ``status`` (select) and ``provenance`` (id-chip) editors from the
  identity per-kind inspector (viewer). The fields stay on the model / wire (unchanged);
  only their inspector inputs are gone. The inspector now shows description + body only.
- **Why:** Dogfood report (2026-07-02): the identity inspector surfaced status + 도출출처
  (provenance), which SPEC.md "Foundation typed-text storage" already declares **inert /
  deferred (D-2026-06-16-O)** — "the inspector shows no status / provenance inputs for now;
  they return with the AI-derive flow." Same code-vs-spec drift shape as core_value's
  ``definition``. This is the code catching up to the pinned spec, not a new decision.
- **Alternatives:** also fold ``description`` into the body rule-list (full D-2026-06-16-N
  compliance) — **deferred / flagged, not done**: that is a cross-repo schema change (like
  core_value) the user did not explicitly request; raised separately rather than bundled.
- **Approval:** Accepted by user (report + direction 2026-07-02).
- **Spec impact:** Implements D-2026-06-16-O; no SPEC.md change (already correct). Pinned by
  viewer ``tests/inspectors/inspectors.smoke.test.tsx`` (identity hides status/provenance).

### D-2026-07-02-E — coach leads and fills a concept's full set through conversation (no premature "done", no handing the wheel back)

- **What:** Added to `PROPOSE_PLAYBOOK`: the coach keeps leading — it must not hand the
  wheel back with a bare "what next?" nor declare a canvas done the moment one item
  exists. A concept usually has several facets (a project holds several core values; an
  identity has more than one voice), so the coach draws the full set out through
  conversation before moving on, so the user never has to point out what is missing.
- **Why:** Dogfood transcript (2026-07-02): the coach declared "Foundation 완성됐네요"
  with only one identity facet, and the user had to ask "voice만 있고 다른 아이덴티티는?".
  The chat wasn't smoothly completing the canvas — the user had to drive. This makes the
  coach cover the concept and lead, matching "대화하다 보면 캔버스가 자연스럽게 완성".
- **Alternatives:** enforce completeness in code (validator requiring N facets) — rejected:
  facet count isn't fixed and code-forcing fights build-through-discussion; the coach
  should draw it out, not a hard gate.
- **Approval:** Accepted by user (report + direction 2026-07-02).
- **Spec impact:** Coaching behaviour (system prompt). Pinned by
  `tests/test_chat_context.py::test_coach_leads_and_covers_full_concept`.

### D-2026-07-02-D — coach keeps its internal operations out of sight (no "saved", no internal field names)

- **What:** The coach must not verbalise its internal operations. Edited `WRITE_PLAYBOOK`
  (removed the "confirm in one short line what you saved" instruction; replaced with "do
  NOT announce the save, name the field, or say 'saved'/'done' — the canvas reflects it on
  its own") and `HALLUCINATION_GUARD` (added: speak in the user's own words — never expose
  Novel's internal field names like statement / body / definition / provenance / status).
- **Why:** Dogfood transcript (2026-07-02): the coach said "저장됐어요" and exposed internal
  field names ("미션 statement는… body는 비어 있어요") to the user. User directive: "코치는
  노블이 어떻게 돌아가는지 사용자에게 알려주면 안 된다." The canvas updating live IS the
  feedback (Clear-Feedback ux), so the mechanics stay invisible. Resolves the tension where
  the old `WRITE_PLAYBOOK` explicitly told the coach to confirm the save out loud.
- **Alternatives:** keep a soft "saved ✓" confirmation — rejected by user: any internal-op
  narration is banned; the live canvas is the confirmation.
- **Approval:** Accepted by user (report + direction 2026-07-02).
- **Spec impact:** Coaching behaviour (system prompt); supersedes the confirm-the-save line
  of `D-2026-06-26-D`. Pinned by
  `tests/test_chat_context.py::test_coach_keeps_mechanics_and_field_names_out_of_sight`.

### D-2026-07-02-C — a newly created node clusters with its own kind (visual grouping, not a fixed drop spot)

- **What:** `_compute_fresh_position` (the server-side auto-position for `create_node`)
  now places a new node **with the existing cluster of its own kind**: left-align to
  the same-kind nodes and drop just below their lowest member. Only the first node of
  a kind (no siblings yet) uses the generic drop lane, staggered by total node count.
  Before, every create landed at a fixed spot (`_FRESH_X`, staggered only by same-kind
  count) regardless of where the siblings actually sat — so a new core value never
  joined the existing core-value cluster and appeared scattered.
- **Why:** User report (2026-07-02): the coach attached a new core value to the anchor
  "아무 곳에나" instead of grouping it with the existing core value ("장인정신") on the
  left. Placing same-kind nodes apart breaks Novel's essence — *thinking-through-sight*
  (VISION): the canvas must stay visually coherent for the structure to accelerate the
  user's thinking. This is a placement heuristic, not auto-layout (foundation auto-layout
  stays a manual button, D-2026-05-13-L) — it only sets a sensible *initial* position.
- **Alternatives:** (a) auto-run radial layout on every create so grouping is enforced
  globally — rejected: foundation auto-layout is deliberately opt-in (D-2026-05-13-L), and
  silently relayouting the user's canvas on each coach create is the kind of unrequested
  motion the layout sagas warned against. (b) centroid-based placement — rejected as
  overkill; stacking below the cluster is predictable and undo-friendly.
- **Approval:** Accepted by user (report + direction), 2026-07-02.
- **Spec impact:** Refines the `create_node` placement noted at SPEC.md "Coach ADDS a new
  node". Pinned by `tests/test_create_node.py::test_create_node_clusters_with_same_kind_siblings`.

### D-2026-07-02-B — in-app coach PROPOSES proactively (system-prompt playbook realises the active-coach spec)

- **What:** Added a `PROPOSE_PLAYBOOK` to the canvas system prompt (`chat_context.py`,
  composed by `build_system_prompt` between `COACH_TONE` and `WRITE_PLAYBOOK`). It
  instructs the coach to **take a position and propose** once it has enough — draft
  a concrete candidate (a mission phrasing, 2–3 core values, features a service
  enables, an entity it noticed, a next step) and offer the higher-level angle the
  user hasn't reached — rather than only interviewing and waiting. Kept few + concrete
  (1–2 options, framed as a draft to sharpen or reject) and does **not** touch the
  save gate: proposing is talk; `WRITE_PLAYBOOK` still requires an explicit yes before
  any `create_node` / `update_node`.
- **Why:** User report (2026-07-02): the chat should actively suggest but stays
  passive. The intended behaviour was **already pinned** as the "적극 토론 코치"
  (active discussion coach) in `D-2026-06-16-H` + root `concepts/ai-collaboration.md`
  §0.1 — "사람이 못 떠올린 고차원 개념·방법을 먼저 제안하는 상대." The prompt carried
  the *intent* scattered in `SCOPE_FRAMING` ("propose features", "draft identity") but
  the dominant tone/write constants pushed toward question-asking; no constant told the
  coach *when to stop asking and start proposing*. This closes that gap — the code
  catches up to the spec.
- **Alternatives:** (a) UI proposal cards with Accept/Reject buttons — deferred (YAGNI;
  start with prompt behaviour, add affordance only if dogfood shows proposals get
  missed in plain text). (b) a separate `propose_node` MCP tool — rejected: proposing
  is conversation, not a write; `create_node` / `update_node` on confirmation already
  cover the write.
- **Approval:** Accepted by user (report + direction), 2026-07-02.
- **Spec impact:** Realises `D-2026-06-16-H`. Pinned by `tests/test_chat_context.py`
  (`test_canvas_system_prompt_instructs_proactive_proposing`,
  `test_project_scope_has_no_propose_playbook`).

### D-2026-07-02-A — core_value definition-removal lands in code + viewer (implements the pending D-2026-06-16-M)

- **What:** Implemented `D-2026-06-16-M` (core_value = name (`label`) + `body`, no
  separate `definition`) in the **engine model + viewer domain/inspector**, which had
  drifted from the spec for two weeks. Removed the `definition` field from
  `CoreValueNode` (Pydantic) and `CoreValue` (viewer domain class); regenerated the
  wire contract + `wire.gen.ts`; dropped `definition` from the writable-field allow-list
  and the typed-field maps. Legacy `definition` folds into `body` on read as the **lead
  paragraph** (it *is* the value's meaning), then the prior body, then any do/dont as
  `## Do` / `## Don't` sections. The inspector now shows a one-line guide (name vs
  meaning) + a body labelled "meaning & tradeoff" with a worked placeholder — directly
  addressing the developer report that the label/definition/body roles were unclear.
- **Why:** A developer reported (2026-07-02) that the three slots' roles weren't
  intuitive. Root cause: the spec (`D-2026-06-16-M`, SPEC.md "Foundation typed-text
  storage", root `concepts/kinds.md`) had already collapsed the kind to name + body,
  but the code still exposed three fields — so the confusion was structural, not a
  wording problem. Fixing it = making code match the pinned model.
- **Alternatives:** (a) keep three fields, clarify with help text — rejected by user:
  contradicts the pinned two-field model and leaves the redundancy. (b) fold
  `definition` after the body — rejected: it is the value's core meaning, so it leads.
- **Approval:** Accepted by user (direction 2026-07-02: "두 칸으로 정리, 정본 따름").
- **Spec impact:** Implements `D-2026-06-16-M`; no SPEC.md change (already correct).
  Pinned by `tests/test_core_value_format_migration.py`, `tests/test_canvas_doc.py`,
  `tests/test_create_node.py`, `tests/test_format_f.py`, and viewer
  `tests/domain/round-trip.test.ts`, `tests/inspectors/inspectors.smoke.test.tsx`,
  `tests/inspectors-per-kind.test.tsx`.

### D-2026-06-28-B — doc homes: shared conceptual model → root single canon; engine docs keep code-near + point to root

- **What:** Resolve the standing root↔noory canon-*direction* conflict. The conceptual model — canvas behaviour / kind meaning / bounded contexts — lived in BOTH `noory-workspace/docs/{concepts,specs}` and `noory-ai/mashbill/docs/{SPEC,CONCEPTS,DOMAIN}` with contradictory "who is canon" headers. Reframed by the user around the **two products** built in this workspace: the open MIT engine (`noory-ai/` plugins) and the commercial app (`plot/`). The shared *conceptual model* both products build on becomes **root `docs/` single canon**; the engine docs keep only **code-near implementation detail** (code homes, wire-field schema, code-to-domain gap lists) and point to root for the model; the commercial-app docs reference root. `index.md` routes it: **concept = root · implementation = noory · business = plot**.
- **Why:** The model is one shared spec both products implement; duplicating it produced drift and mutually-contradictory canon claims (e.g. root `concepts/kinds.md` carried the post-marathon model while noory `CONCEPTS.md` still described the retired `gives/receives` actor_ref model as current). One home kills the drift. Root is the right home because the model is what BOTH products agree on, not engine-private; the engine *implements* it.
- **Alternatives:** (a) noory stays canon, root → pointers — rejected: root already held the *newer* articulation, and the model is shared, not engine-private. (b) leave the split — rejected: it is the drift source. (c) duplicate the model in each repo — rejected (SSOT).
- **Approval:** Accepted by user, 2026-06-28.
- **Spec impact:** Doc-home restructure, executed in stages (DOMAIN → CONCEPTS → SPEC → rewire index/gates/pointer-tables). Tradeoff accepted: a standalone MIT clone of `noory-ai/` sees a pointer to the workspace-root model, not the full body. Updates `index.md` §3/§4, the doc-home sections of the `CLAUDE.md` files, and the `PRODUCT_SPEC` pointer tables.

### D-2026-06-28-A — external canvas changes refresh the screen again (watcher broadcast descriptor fixed for the flat layout)

- **What:** Fixed `_describe_change` (broadcast layer) to read the **flat** one-project-per-root layout (`.noory/plot/{canvas_kind}/canvas.json`, `D-2026-06-21-AB`): the leading path segment is the **canvas kind**, and the project id is resolved from the root's `project.json` (via `enumerate_projects`), not read off the path. Before, it still assumed the legacy `{project_id}/{canvas_kind}/…` shape and read `parts[0]` as the project id — so on the flat layout every external write produced `{project_id: "<canvas_kind>"}` with **no** `canvas_kind`. The viewer then treated it as "some other project changed" and skipped the canvas refetch.
- **Why:** Corrects the load-bearing **false premise of `D-2026-06-26-D`** — *"Reload already worked (file watcher → WS broadcast → viewer refetch)."* It did not: the `D-2026-06-21-AB` flatten had silently broken the watcher→viewer descriptor, and `_describe_change` had **zero test coverage**, so the regression shipped unnoticed. Surfaced in dogfood (2026-06-28): the coach's `update_node` landed on disk but the canvas never updated (*"데이터는 갱신되는데 UI 갱신을 못한다"*). Every external mutation (coach create/update, Obsidian / VS Code edits) was affected; the viewer's own optimistic edits masked it. With the descriptor correct, the coach write was reproduced end-to-end (disk change + a `project_changed` carrying the real `project_id` + `canvas_kind`) and confirmed in the real app.
- **Alternatives:** (a) also handle the legacy nested layout in the same branch — deferred (YAGNI; flat is canonical, nested is read-only discovery). (b) emit the descriptor from `update_node` directly instead of via the watcher — rejected: the watcher path is the single propagation SSOT (HTTP PUT, external editors, and MCP writes all ride it); fixing the descriptor fixes every producer at once.
- **Approval:** User dogfood-confirmed, 2026-06-28 (*"이제 되는구나"*).
- **Spec impact:** Regression fix; pins the watcher→viewer contract. Guard: `tests/test_broadcast_describe.py` (was zero-coverage). Corrects the `D-2026-06-26-D` "reload already worked" note.

### D-2026-06-27-B — in-app coach ADDS a node via a clobber-safe `create_node` (one SSOT for node creation)

- **What:** New MCP tool `create_node(project_path, project_id, canvas_kind, kind, fields?, service_id?)` — a clobber-safe single-node *append* mirroring `update_node`: validate `kind` is creatable on `canvas_kind`, mint the id server-side, auto-position server-side, apply only the kind's writable content fields (reuse `writable_node_fields`), `read_canvas → append one node → re-validate the whole CanvasDoc → atomic write_canvas`, return `{node, rejected_fields}`. It **generalizes** the former `create_master` (`masters.py`) into one creation SSOT: `create_master` is now a thin reference-flow wrapper that resolves the master's home canvas and calls `create_node` (the pick-or-create endpoint, D-2026-06-19-C, is behaviourally unchanged). The `WRITE_PLAYBOOK` gains a create branch: for something genuinely **new** (not an existing node), the coach reads/searches first, then **proposes** ("새로 ~를 만들까요?") and only on an explicit yes calls `create_node`, then confirms in one line — adding a node follows the same consent gate as filling (never create before the yes).
- **Why:** Empirically reproduced (2026-06-27, the real frozen-binary coach driven against a copy of a live project): **filling an existing node works reliably**, but **adding** a new node had *no* dedicated tool, so the coach fell back to `update_canvas` — rewriting the WHOLE canvas to slip one node in, with an **LLM-guessed position**. That is the clobber-unsafe path `D-2026-06-26-D` explicitly rejected (drops a concurrent edit / risks the model dropping fields on a large JSON round-trip, on the load-bearing path). A safe single-node append closes it. This is the missing half of Novel's core promise (the AI fills the canvas through discussion).
- **Accepted kinds per canvas** (verified against `_ALLOWED_KINDS_BY_CANVAS` + each validator): foundation → mission / core_value / identity; actors → actor; services → category / service / feature (the feature *node* = drill anchor; the detail canvas is a separate orchestration); entities → entity; feature → step / decision / rule / note / actor_ref. **Rejected everywhere:** `project` (the synthetic anchor lives in `ProjectDoc.anchors`, not as a node). **Rejected on the feature canvas:** `feature` (its validator requires the root feature to already exist — bootstrap, not append). The tool adds a **bare** node only; containment/edges are user/coach-drawn separately (parent_id is gone since v0.26.0 / D-2026-05-25-A — containment is directed-edge-only), never auto-wired silently. A cross-canvas master (e.g. a new actor referenced from a service) uses the existing reference pick-or-create flow, not `create_node`.
- **Alternatives:** (a) keep adding via `update_canvas` with better playbook guidance — rejected: clobber-unsafe on the load-bearing path (the reproduced failure mode). (b) a singleton guard that errors when a mission/identity already exists — rejected as **backwards**: the schema enforces only a *minimum* of one (`_foundation_canvas_rules` checks `< 1`, never `> 1`), and `D-2026-06-27-A`'s playbook already routes a unique kind to *find-and-update*, never re-create; `create_node` does not second-guess create-vs-update — the playbook owns it. (c) 409-conflict / file-lock / count-gate concurrency machinery — rejected as out of scope: `create_node` inherits `update_node`'s last-write-wins semantics, which the user already accepted at human pace (`D-2026-06-26-D`); only the limit is named, no machinery added.
- **Known limits (named, inherited):** last-write-wins (same as `update_node`) — a concurrent edit to another node on the same canvas, or two concurrent same-kind creates, may collide/be lost; acceptable at human pace. Undo-stack clear (same as `D-2026-06-26-D`) — a coach create lands via the file watcher, treated as an external change, so it clears the undo stack (recover via git / re-edit).
- **Approval:** User direction, 2026-06-27 ("작업합시다" — build the confirm-then-create model). Design adversarially red-teamed before code (six lenses → GO-WITH-FIXES; the singleton-guard reversal + the create_master generalization came from that review).
- **Spec impact:** `SPEC.md` §R7 chat — the coach adds a node via `create_node` on an explicit confirmation; accepted-kinds matrix + named limits. Engine guards: `tests/test_create_node.py`, `tests/test_chat_system_prompt.py` (create branch of `WRITE_PLAYBOOK`).

### D-2026-06-27-A — coach writes to the node the user means; no selection needed for a unique kind

- **What:** The write playbook is loosened on targeting. The coach writes to the node the user *means*: the selected node if one is selected, otherwise the node they name — and for a kind that is unique on the canvas (the mission, the identity) it finds that node via `get_canvas` and writes **without** requiring a prior selection. It asks "which one?" only when several nodes of the same kind could match (e.g. one of many core values) and none is selected. The `[Write target]` block no longer hard-codes "the selected node's id".
- **Why:** Dogfood — the user asked "왜 동그라미를 꼭 골라야 하죠?". Requiring a manual node selection to fill the singular mission node is needless friction; the mission is unambiguous, so the coach can locate it itself. Selection stays as the disambiguator only where a kind genuinely repeats. The confirmation gate is unchanged — still writes only on an explicit yes, so this loosens *targeting*, not *consent* (`D-2026-06-16-P` intact).
- **Approval:** User direction, 2026-06-27 ("왜 동그라미를 꼭 골라야하죠?").
- **Spec impact:** `SPEC.md` §R7 chat write row. Guard: `tests/test_chat_system_prompt.py` write-playbook test.

### D-2026-06-26-F — chat quality: re-feed session memory on restart + ban fabricated saves

- **What:** Two coaching fixes after the first real dogfood of `D-2026-06-26-D/E`. (1) **Session-memory rehydration** — on a fresh CLI session (the first turn after an app/engine restart wiped the in-memory session registry), the send endpoint re-feeds the saved transcript (`chat_store.read_recent_transcript`, newest-bounded) so the coach continues from what's already agreed. `--resume` keeps memory *within* a live session, so only the first turn needs this. (2) **Ban fabricated saves** — the hallucination guard now forbids claiming you saved / wrote / recorded / filled anything unless the write tool actually ran and succeeded this turn, and forbids inventing a file path, line number, or "refresh to see it" (the canvas auto-updates on a real write). The write playbook also treats a value already agreed earlier in the conversation as the confirmation (write it, don't re-ask), but still never says it's done until the tool call lands.
- **Why:** The dogfood transcript exposed two failures that made the feature feel broken even after `D-2026-06-26-E`. (a) The coach **re-asked questions the user had already answered** ("누구의 무엇을 바꾸나요" several times; the user repeatedly: "위에 다 썼다 / 다 정해져 있다") — because every restart wiped its memory and the persisted transcript was never re-fed. (b) The coach **announced "저장했어요 ✓" and even cited "디스크 23~24번째 줄" while the mission node was actually empty** — a fabricated save that destroyed trust. Ground truth on disk: `statement`/`body` were `""` the whole time. The user's verdict — "기억 문제도 있고, 그래도 미션을 못 넣잖아요" — names both exactly.
- **Alternatives:** (a) always inject the full transcript every turn — rejected: duplicates `--resume`'s own memory within a live session and burns the context window; first-turn-only is enough. (b) rehydrate the CLI session itself (replay) — rejected: heavier, and a context block achieves the same continuity. (c) leave the save-claim wording as "confirm what you saved" — rejected: it still allowed a confident false "saved".
- **Approval:** User direction, 2026-06-26/27 ("대화 내용을 개선해 나아가야 합니다", "미션을 못 넣잖아요", "기억 문제도 있고").
- **Spec impact:** `SPEC.md` §R7 chat — a fresh session re-feeds the saved transcript; the coach never claims a save it didn't make, and never narrates files / refresh. Guards: `tests/test_chat_store.py` (`read_recent_transcript`), `tests/test_chat_system_prompt.py`.

### D-2026-06-26-E — in-app coach attaches its OWN mashbill MCP server (`--mcp-config` + `--strict-mcp-config`)

- **What:** The in-app chat provider now spawns `claude` with `--mcp-config <file>` naming THIS engine's own Novel stdio server (built via the existing frozen/dev resolution, now exposed as `mcp_registration.mashbill_config`) plus `--strict-mcp-config`, so claude uses ONLY that server and ignores every other MCP source. Previously the coach inherited the `plot` server from the user's global `~/.claude.json` registration.
- **Why:** First real dogfood of `D-2026-06-26-D` (2026-06-26): the coach reported it had no canvas tools at all. Root cause — the global `plot` registration pointed at a **deleted older app build**, so the spawned coach loaded a missing binary and silently got zero Novel tools. That is the literal "in-app chat can't write to the canvas" failure: even with `update_node` shipped, the coach could never call it because the tool was never attached. Binding the coach to the *running build's own* server removes the dependency on a drift-prone global pointer; `--strict-mcp-config` also means the in-app coach no longer sees the user's unrelated servers (Gmail / Notion / Supabase …), tightening the workspace grounding from `D-2026-06-21-I`.
- **Alternatives:** (a) keep relying on the global registration + re-register on app launch — rejected: still drifts, and re-registration silently rewrites the user's global config (the safety layer also blocks an agent from touching it). (b) inline JSON for `--mcp-config` — deferred: a content-addressed temp file under the OS temp dir (cross-platform, idempotent) is unambiguously supported.
- **Approval:** Accepted by user, 2026-06-26 (approach delegated: "문제 해결을 어떻게 해야 할지는 너의 몫").
- **Spec impact:** `SPEC.md` §R7 chat (MCP wiring) — the in-app coach carries the running build's Novel tools via `--mcp-config` + `--strict-mcp-config`, not the global registration. Guard: `tests/test_chat_system_prompt.py::test_claude_attaches_own_mashbill_strictly`.

### D-2026-06-26-D — in-app coach writes a confirmed value into the selected node (`update_node`)

- **What:** Closes the load-bearing gap that the in-app chat coach could only *talk* — it proposed a mission / value / step and told the user to paste it, because nothing let it write. Three parts: (1) new MCP tool **`update_node`** (`project_path, project_id, canvas_kind, node_id, fields, service_id?`) — a clobber-safe single-node content patch: read canvas → merge only *writable content* fields (`label` + the kind's typed text; visual / structural / server fields are rejected, reported under `rejected_fields`) → re-validate against the node's kind → write the whole canvas atomically via `write_canvas`, leaving every other node + edge untouched. An absent node id (including the synthetic project anchor, which is not a node) → error. (2) The per-turn chat context now injects a **`[Write target]`** block (the `project_path` / `project_id` / `canvas_kind` / `service_id` the agent must pass — the in-app agent's MCP server is stateless and never otherwise learns the open project) plus, for every selected node, its **writable field names** (so a *blank* node — the exact "mission won't fill" case — still tells the coach what to write). (3) New **`WRITE_PLAYBOOK`** in the canvas-scope system prompt: on an explicit user yes, save the value into the selected node via `update_node`, then confirm in one line what was saved; never write before the yes, and ask when the target is empty / ambiguous.
- **Why:** User dogfood (2026-06-26): confirming a mission didn't fill the mission node — the coach said "I can't write, paste it yourself", breaking Novel's core promise (the AI fills the canvas). Root cause was two independent gaps: the playbook never told the coach to write (Gap A), and even if it tried, every write tool needs `project_path` / `project_id` which were never in its context and which the sandboxed agent had no allowed way to discover (Gap B — the write path was architecturally unreachable). Reload already worked (file watcher → WS broadcast → viewer refetch), and Foundation typed text has been a single JSON SSOT since `D-2026-05-16-A`, so only A + B needed closing. Design red-teamed before code; that surfaced the empty-node field-schema need, the structural-field write-guard, the anchor-is-not-a-node guard, and the confirmation-gate risk.
- **Relation to `D-2026-06-16-P` ("everything through discussion, never silent"):** This does **not** weaken P. P bans (a) a blank form and (b) silent auto-generation the AI commits *without* the user. Writing *after* an explicit confirmation is the *completion* of build-through-discussion, with the human as the confirmer — exactly what P mandates. The guardrail is unchanged in force, sharpened in wording: never write *without* a confirmation. Rule 7 in `CLAUDE.md` ("no silent automated change to user-visible state") gets the same caveat.
- **Alternatives:** (a) reuse whole-canvas `update_canvas` (agent does get → mutate → put) — rejected: clobbers a concurrent user edit and risks the LLM dropping fields on a large JSON round-trip, on the load-bearing path. (b) a two-step "propose on canvas → user clicks accept" — rejected for v1 (more build; the verbal confirm + the visible result + the git backstop are enough; revisit if false-positive writes bite). (c) give the agent the open project via server state — rejected: the in-app agent's MCP server is a separate, stateless process with no shared open-project binding.
- **Known limit (named):** a coach write lands via the file watcher, which the viewer treats as an external change and so **clears the undo stack** — Cmd+Z does not undo a coach write (recover via git / re-edit). Acceptable for a *confirmed* write; the one-line "saved" confirm makes a mistake visible immediately. An undo-preserving write path is a follow-up if it bites.
- **Approval:** Accepted by user, 2026-06-26 (design + the granular-tool choice confirmed; "코드도 짜고 빌드도 하고 검증도 하고").
- **Spec impact:** `SPEC.md` §AI collaboration — the coach saves a confirmed value into the selected node via `update_node`. Engine guards: `tests/test_update_node.py`, `tests/test_chat_selection_detail.py` (write-target + writable-field schema), `tests/test_chat_system_prompt.py` (`WRITE_PLAYBOOK`).

### D-2026-06-26-C — chat: memoise message rows (fix resize-during-stream) + copy assistant replies

- **What:** (1) `ChatMessageRow` is `memo`'d and a streaming assistant turn renders **plain text** (Markdown only once the turn completes). Previously every token re-rendered the whole thread and re-parsed **every** prior reply's Markdown, starving the main thread — the panel-resize drag went dead while the AI was streaming. (2) Each completed assistant reply gets a **Copy** button (`navigator.clipboard`).
- **Why:** User dogfood (2026-06-26): "AI 생각 중에 좌측 패널 사이즈 조정이 안 먹는다" (perf), and "AI 답변을 복사할 수 있게 해달라". The memo is safe because `useChatStream`'s delta update keeps completed messages' object identity (only the streaming message is replaced), so reference-equal rows skip re-render.
- **Approval:** Accepted by user, 2026-06-26.
- **Spec impact:** none (viewer rendering). Guards: `plot/viewer/tests/chat-md.test.tsx` (copy calls clipboard; streaming stays plain, no Markdown parse / no copy button).

### D-2026-06-26-B — persist chat conversations to `.noory/plot/chat/<scope>.json`, engine-side, one-per-scope

- **What:** Chat is saved to disk under the project at `chat/<scope>.json` — one append-only `ChatConversationDoc` per scope (`feature:<id>`→`feature__<id>.json`). The **engine** is the sole writer, appending the user message when a turn is sent (`chat_send_endpoint`) and the assistant message on `turn_complete` (`stream_chat_turn`), via the existing atomic `storage._write_json`. Two new read endpoints — `GET /api/chat/conversations` (list metadata, `updated` desc) and `GET /api/chat/conversations/{scope}` (full messages) — feed a new `ChatConversationsPanel` in the dock; reopening hydrates `messagesByScope[scope]`. `title` = first user message (≤60 chars), set once.
- **Why:** In-memory chat died on an app restart and the user lost real work (defining Novel's own mission via the coach). Persisting inside `.noory/` (git-tracked) makes conversations travel with the project and restore on another machine. **Engine-side capture is the load-bearing choice** — it survives a viewer crash *and* an engine restart, the actual failure. The engine already sees the full user message (`chat_send_endpoint`) and the assembled assistant turn (`turn_complete`), so capture costs two `_write_json`s per turn with zero new transport.
- **Alternatives:** (a) Viewer-side save (localStorage/IndexedDB) — rejected: doesn't travel with the project, doesn't survive a viewer crash, and `.noory/` is the established persistence home. (b) Persist the CLI `--session-id` and rehydrate live sessions on restart — deferred: codex has no session_id ctor param and claude's resume reattaches CLI state we don't own; v1 restores the transcript for reading only. (c) Multiple conversations per scope (archival branching) — deferred (YAGNI); one-per-scope mirrors the existing one-session-per-scope registry.
- **Known limits (named, not v1 blockers):** whole-file rewrite per turn (O(n), fine at human pace); orphaned files on service deletion / scope rename left as harmless history (no prune in v1); **reopen is a half-restore** — it revives what was said, not the CLI session behind it, so continuing a reopened conversation silently starts a fresh CLI turn with the old turns as visible history only. Full fix (persist + rehydrate session ids per provider) is the real follow-up.
- **Approval:** Accepted by user, 2026-06-26 ("기능 추가해주세요"), after the real data loss.
- **Spec impact:** `SPEC.md` Conversation-persistence row (D-2026-06-26-B). Guards: `tests/test_chat_store.py` (+ endpoint tests in `tests/test_endpoints_chat.py`); viewer `useChatStream` hydrate + `ChatConversationsPanel` tests.

### D-2026-06-26-A — per-service chat thread: `service:<id>` alongside `feature:<id>`

- **What:** Chat threads gain a second parametric scope `service:<id>`. Selecting a single service on the Services canvas keys that service's own thread; drilling into one of its features keys `feature:<id>`; deselecting returns to the canvas-wide `services` thread. The engine accepts `service:<id>` in `is_valid_scope` (bare `service` with no id → invalid, same Fail-Fast rule as `feature`), and `build_framing_preamble` maps the base `service` to the existing `services` (Planning/value) framing so a per-service thread coaches the value-level big picture. The selected service node's typed text already injects via selected-node content (D-2026-06-24-B), so no per-service envelope path is added.
- **Why:** User (2026-06-26): a service and its features are *different conversations* — a service is the value-centred big picture ("what value, for whom"), a feature is its flowchart ("how it actually runs"). The shipped model only had a per-feature thread plus the whole-`services`-canvas thread; selecting one service still used the canvas-wide thread, so a single service had no conversation of its own. Both granularities should exist, each with its matching coaching.
- **Alternatives:** (a) Keep as-is (per-feature + whole-canvas only) — rejected: the user identified the missing middle (no per-service thread). (b) Make `service` a base canvas-kind member of the `ChatScope` literal — rejected: a service is not a canvas (selecting one shows an inspector, not a canvas), so it stays a parametric instance scope parallel to `feature:<id>`, keeping the base set = `project` + canvas kinds (MECE). (c) A dedicated per-service framing string — rejected as duplication; the `services` Planning framing ("intent → five slots → propose features") already fits one service (DRY).
- **Approval:** Accepted by user, 2026-06-26 ("승인합니다").
- **Spec impact:** `SPEC.md` Conversation-scope section — adds the **Per-service thread (D-2026-06-26-A)** row and corrects the stale `service_detail` naming to `feature:<id>`. Guards: `tests/test_chat_scope_parity.py` (service scope validity), `tests/test_chat_system_prompt.py` (per-service framing = services framing).

### D-2026-06-24-J — coach output hygiene: keep the read/ask machinery silent + warmth light

- **What:** Two guideline principles added to the coaching system prompt (`HALLUCINATION_GUARD` + `COACH_TONE` in `mashbill/chat_context.py`): (1) keep the read/ask machinery out of sight — never narrate tools, a read that didn't land, or "what I'm certain of"; speak as if you simply know the project or simply need to hear it; an empty canvas is a fresh start to invite, not a gap to announce. (2) warmth is light — lead with the one question, don't stack reassurance on reassurance. Guideline form (principles the coach reasons from), not scripts or sentence-count mechanics.
- **Why:** First Gate-3 dogfood of the chat-quality work (Phases 1–3) on an empty project: the coach did NOT invent a mission (the core anti-hallucination goal held), but it (a) leaked its plumbing — "the tool call was cancelled, I couldn't read the body, here's what I'm certain of" — and (b) stacked reassurances into a verbose wall. Both were unconstrained: no rule told it to operate silently or to keep it brief.
- **Alternatives:** (a) Hardcode the user's example phrasing / a canned opener — rejected: scripts make the coach brittle and off-context; a principle the model reasons from generalises (user direction, 2026-06-24: pin a guideline, not the dialogue). (b) A rigid length cap ("2–3 sentences") — softened to a principle (lead with the question, don't stack caveats) so mechanical curtness doesn't undercut the gentle-coach purpose.
- **Approval:** Accepted by user, 2026-06-24 (previewed via a live `claude -p` run before landing; "그대로 진행하세요").
- **Spec impact:** Content SSOT = `docs/concepts/ai-collaboration.md` §0.1 ⑥⑦. Guard: `tests/test_chat_system_prompt.py` (`test_guard_keeps_read_ask_machinery_silent`, `test_coach_tone_keeps_warmth_light_not_stacked`).

### D-2026-06-24-I — node name-search entry point: `search_project_nodes` MCP tool (the "name" leg of D-2026-06-20-P)

- **What:** A new MCP tool `search_project_nodes(project_path, project_id, query)` + the `node_search.search_nodes` it wraps: a case-insensitive label substring scan over **every** canvas of a project (singletons + feature details), returning up to 20 `{id, kind, label, canvas}` hits. The hallucination guard now names it so the agent reaches for it when the user references a node by name that isn't on the active canvas.
- **Why:** D-2026-06-20-P §1.2 fixed the context entry-point chain as **selection → map → name → (last) semantic search**, and said the title/id index (name lookup) is the thing to "build early". Selection (Lever 1a) + map (Phase 2a) shipped; this is the **name** leg — so the agent can jump to "the comment feature" / "the Reader actor" even when it's on another canvas, instead of guessing.
- **Alternatives:** (a) vector / embedding search — rejected now (the data is already a graph; a plain label index suffices until text drifts outside the graph — vector stays a later option behind the same seam). (b) HTTP endpoint instead of MCP — not needed: both the in-app `-p` agent and the external agent reach it through `mcp__plot__*`, one surface for both.
- **Approval:** Implements pinned D-2026-06-20-P (no new product decision); built in the 2026-06-24 autonomous push.
- **Spec impact:** SPEC.md R7 context. Guard: `tests/test_node_search.py` (6).

### D-2026-06-24-H — context-provider seam landed: `build_turn_preamble` is the single per-turn assembly point (implements D-2026-06-17-L)

- **What:** The in-app chat endpoint's per-turn Layer-2 assembly (active-canvas map → cross-canvas registry → selected-node detail) moves out of `endpoints_chat.py` into one function `chat_selection.build_turn_preamble(plot_root, scope, selection)`. Behavior-preserving refactor — same output, one named home.
- **Why:** D-2026-06-17-L specified a **context-provider abstract seam** so the delivery strategy can swap (CAG now → RAG / graph-traversal for large projects, D-2026-06-20-P) without touching callers. This lands that seam: the current body is the CAG implementation (inject everything, bounded by caps); a future RAG provider replaces this one function's internals. The endpoint shrinks to "build preamble + system prompt".
- **Approval:** Implements pinned D-2026-06-17-L / D-2026-06-20-P (no new product decision); done in the 2026-06-24 chat-quality push.
- **Spec impact:** none (internal). Guard: `tests/test_chat_selection_detail.py` (turn-preamble composition).

### D-2026-06-24-G — pick-OR-create reference masters wired (engine endpoint + service-inspector affordance)

- **What:** Implements the manual side of D-2026-06-19-C. A new engine endpoint `POST /api/projects/{id}/masters` `{kind, label}` (kind ∈ actor / core_value / identity) creates a **lightweight master** (name only) on its **home canvas** — actor → Actors, core_value / identity → Foundation — positioned so fresh ones don't stack, and returns its id (`mashbill/masters.py`). The Services inspector's reference chips (`RefChips`) gain an inline "create" input; on submit the viewer calls the endpoint, appends the new id to the field, and refreshes the master's home canvas so the chip resolves. The home-canvas + positioning logic lives **only in the engine** so the viewer never writes across the canvas boundary.
- **Why:** D-2026-06-17-B made references pick-only; D-2026-06-19-C said they must be pick-OR-create (reference a needed-but-missing concept without leaving the flow), but only the chat-coach side shipped (Phase 3 playbook). This adds the **direct-edit** path so a user editing the inspector manually isn't forced to "go create it on the Foundation canvas first". The created master is name-only + incomplete (deepened later by its home-canvas coach), so the current flow isn't derailed (D-2026-06-19-C step 6).
- **Alternatives:** (a) viewer reads the upstream canvas, adds the node, writes it back — rejected: cross-canvas write juggling in the viewer, two SSOTs for "where a master lives". The engine endpoint encapsulates it + is fully unit-tested. (b) free-type the reference — rejected (D-2026-06-17-B ban; create a real master instead). (c) run the full master interview inline — rejected (derails the flow; lightweight stub + later deepening).
- **Approval:** Builds on D-2026-06-19-C (Provisional, user 2026-06-19 "그래요 일단 해봅시다"); implemented in the 2026-06-24 viewer-UI push ("뷰어 UI 해야죠?"). Full click-loop verification in the debug `.app` is the user's hands (Gate 3).
- **Spec impact:** SPEC.md R7 / Services inspector. Guards: engine `tests/test_masters.py` (8); viewer `tests/inspectors/ref-chips-create.test.tsx` (3).
- **Follow-up (2026-06-24, viewer-only — engine binary unchanged):** (a) **Fix** — the service-inspector `onCreateMaster` was wired only to the `FeatureDetailCanvas` instance, not the main `ServicesCanvas` where the service inspector lives, so the inline "create" never rendered there; now passed to the main canvas too (the component vitest passed in isolation — this is exactly the gap real-browser Gate 3 exists to catch). (b) **Extend** — the Feature canvas's **actor anchor** (`ActorRefPicker`) gains the same inline create affordance (D-2026-06-19-C also specifies it for the feature actor anchor): creating makes a real actor master via the masters endpoint, then spawns the `actor_ref` pointing at it. Both land in the plot repo (`fix(viewer): … Feature actor anchor`); viewer 1017 green. Guard: `tests/actor-ref-picker-create.test.tsx` (3).

### D-2026-06-24-F — MCP-path parity: the external agent gets the same coaching system prompt as in-app (chat-quality Phase 3)

- **What:** `get_viewer_context` (the external-agent MCP path) now returns `build_system_prompt(scope)` — guard + coach tone + the canvas playbook — as its `framing` field, instead of the bare one-line `build_framing_preamble`. The two delivery layers now share one SSOT for the canvas coaching prompt.
- **Why:** the MCP path is the **primary** path (CHAT_ARCH MCP-first), so it must not be context-poorer than the in-app convenience panel (D-2026-06-19-F). Before this, the external agent saw only a one-liner while in-app got the full guard + playbook — backwards.
- **Alternatives:** (a) leave the MCP path on the one-liner — rejected, inverts the primary/convenience relationship. (b) a separate, lighter MCP framing — rejected (two SSOTs drift; the playbook is the product's coaching content and should be identical on both paths).
- **Approval:** Accepted by user, 2026-06-24 (chat-quality push; resolves the named "MCP 경로 선택-인지" design-undecided item).
- **Spec impact:** SPEC.md R7 chat → "MCP-path context" row. Guard: `tests/test_viewer_context.py::test_framing_carries_full_coaching_system_prompt`.

### D-2026-06-24-E — expand per-canvas framing into full coaching playbooks (chat-quality Phase 3)

- **What:** `SCOPE_FRAMING` grows from a one-sentence-per-canvas stub into the canvas's full coaching interview, and a shared `COACH_TONE` (gentle, one-question-at-a-time, follow-the-user's-words + pick-or-create reference principle) now prefixes every canvas system prompt. Foundation = mission/core-value/identity interview; Actors = three-role-family elicitation, actor≠persona; Services = 5-slot JTBD interview + promotion test; Feature = actor-anchored happy-path-first flow + altitude guard; Entities = identity-not-name dedup + propose-don't-finalise. Content sourced verbatim-in-intent from `docs/concepts/ai-collaboration.md` §0–§2.
- **Why:** the whole product is built *through the chat coach* (D-2026-06-16-P), so the per-canvas coaching instructions are the load-bearing content — a one-line stub can't run the interviews the design (`D-2026-06-16-K/L/N`, `D-2026-06-17-B/D/G/I`, `D-2026-06-18-C`, `D-19-A/B/D`) calls for. This wires the already-decided coaching script into the code constant (the "code constants first, editable later" home, YAGNI). Resolves the "Actors 코칭 질문 세트 비어있음" design-undecided item.
- **Alternatives:** (a) keep one-liners — rejected, the coach can't actually coach. (b) put the playbooks in `.noory/`-editable files now — deferred (YAGNI; code constants until a user wants to edit them). (c) invent the questions — forbidden (honesty); they are sourced from the ai-collaboration.md SSOT.
- **Approval:** Accepted by user, 2026-06-24 (chat-quality push, "설계미결 해결").
- **Spec impact:** SPEC.md R7 chat → "Per-canvas framing + hallucination guard" row. Guards: `tests/test_chat_system_prompt.py` (per-canvas playbook signals + coach-tone composition).

### D-2026-06-24-D — cross-canvas registry: list existing actors / entities on feature & services chat scopes (chat-quality Phase 2b)

- **What:** On the `feature` and `services` scopes, the in-app chat message lists the **existing** actors (`"label" (id)`) and entities (`"label" (id): summary`), read from their canvases engine-side (`render_cross_canvas_registry`). Each list capped at 40; other scopes inject nothing.
- **Why:** those scopes design things that *reference* actors / entities (a feature step carries `actor_ref` + `ref_entity_ids`; a service carries `ref_actor_ids`). Without the existing list in front of it, the agent reinvents — minting 글 / 게시물 / 포스트 as three entities instead of referencing the one that exists. This is the D-2026-06-17-L "entity registry" envelope piece, scoped to where the reference actually happens.
- **Alternatives:** (a) inject the registry on every scope — rejected: foundation / actors / project don't cross-reference, so it's pure context-window cost there. (b) inject once per session instead of per turn — deferred: simpler to send per turn under a cap; per-session caching is a budget optimisation for later. (c) full canvas content rather than a label/summary list — rejected: the list is the dedup signal; deep content is the agent's MCP fetch.
- **Approval:** Accepted by user, 2026-06-24 (chat-quality push, "다음 작업하죠").
- **Spec impact:** SPEC.md R7 chat → "Cross-canvas registry" row. Guards: `tests/test_chat_selection_detail.py` (registry cases), `tests/test_endpoints_chat.py::test_chat_send_injects_actor_registry_on_feature_scope`.

### D-2026-06-24-C — active canvas map: inject the whole current canvas (not just the selection) into in-app chat (chat-quality Phase 2a)

- **What:** The in-app chat message now leads with a compact `[Canvas: <scope>] N node(s):` map of **every** node on the active canvas (`kind "label" (id)`, selected ones marked), read engine-side (`render_canvas_map`). It replaces the former wire-label selection header when the canvas reads cleanly, and falls back to that header otherwise. Labels only; capped at 60 nodes.
- **Why:** the agent saw only the *selected* nodes, so it was blind to the rest of the screen it was helping with — neighbours, siblings, what's already on the canvas. The map gives it the whole current surface cheaply (labels only), while bodies stay in the selection-content block (Lever 1a) and deep reads stay the agent's MCP-fetch job (the inject-small / fetch-large boundary, `docs/idea/chat/01-levers.md`).
- **Alternatives:** (a) keep only the selection header — rejected, leaves the agent blind to context it's clearly working within. (b) inject full node bodies for the whole canvas — rejected: blows the window on a large canvas; the cap + labels-only keeps it bounded, deep content is fetched. (c) add the map *alongside* the selection header — rejected as redundant; the map marks the selection, so it subsumes the header (MECE).
- **Approval:** Accepted by user, 2026-06-24 (same chat-quality push).
- **Spec impact:** SPEC.md R7 chat → "Active canvas map" row. Guards: `tests/test_chat_selection_detail.py` (canvas-map cases).

### D-2026-06-24-A — in-app chat framing delivered as an authoritative system prompt + hallucination guard (chat-quality Lever 2)

- **What:** The per-canvas Layer-3 framing moves out of the user message into a real **system prompt**, and a constant **hallucination guard** is prepended to it on every scope. `mashbill/chat_context.build_system_prompt(scope)` composes `HALLUCINATION_GUARD` + the scope's framing; `ChatProvider.set_system_prompt` carries it; claude maps it to `--append-system-prompt`, codex (no system-prompt flag) prepends it to the message. The user message is now `context → selection detail → user text` (framing removed from it).
- **Why:** the in-app `-p` agent hallucinates because it is **context-starved**, not because of the `-p` mode (`docs/idea/chat/00-problem.md`). The framing sat inside the user message, where the model treats it as conversation, not a binding instruction — and nothing told the agent to *read* the canvas rather than invent. A system-prompt-delivered guard ("ground every claim in the given context; read the canvas with your mashbill MCP tools or ask; never invent mission text / values / actors / entities; resolve 'this' to the selected node") is the single cheapest, highest-leverage anti-hallucination lever (`docs/idea/chat/01-levers.md`, Lever 2).
- **Alternatives:** (a) keep framing in the user message — rejected, weak authority, the status quo that drifts. (b) force a `get_viewer_context` call every turn instead of a guard — deferred (extra round-trip; `-p` adherence unverified; can combine later). (c) a claude-only flag with no codex path — rejected, both providers must carry the framing, so codex falls back to message-prepend.
- **Approval:** Accepted by user, 2026-06-24 (chat-quality work, "설계미결 해결하고 채팅 품질 잡읍시다"; plan SSOT `docs/idea/chat/`).
- **Spec impact:** SPEC.md R7 chat → "Per-canvas framing + hallucination guard" row. Guards: `tests/test_chat_system_prompt.py`, `tests/test_endpoints_chat.py::test_chat_send_routes_framing_to_system_prompt_context_to_message`.

### D-2026-06-24-B — inject the selected node's actual content into the in-app chat context (chat-quality Lever 1a)

- **What:** The engine now reads the selected nodes' **typed text** (mission statement / body, core_value definition, …) and injects a `[Selected node details]` block into the user message, in addition to the existing kind/label/id header. Read engine-side via `read_canvas` in the new `mashbill/chat_selection.py`, keyed off the single project under the data root; the renderer is generic (dumps non-empty, non-structural text fields).
- **Why:** the selection header named the node but never carried its content, so "polish this mission" reached the agent without the mission text and it invented one — the concrete face of context starvation (`docs/idea/chat/00-problem.md`, Lever 1a).
- **Alternatives:** (a) have the viewer send node bodies in the `selection` payload — rejected: bloats the wire, the viewer doesn't hold every typed field, and it wouldn't serve the MCP path. Engine-side read keeps the canvas the SSOT (D-2026-06-15-D) and fails safe. (b) per-kind content renderers — rejected as premature; a generic field dump (drop structural / visual / server keys) is MECE and auto-covers new kinds. (c) inject the whole active canvas now — deferred to the Phase-2 context envelope; Lever 1a is the cheap, bounded first cut (selected nodes only).
- **Approval:** Accepted by user, 2026-06-24 (same chat-quality push).
- **Spec impact:** SPEC.md R7 chat → "Selected-node content injection" row. Guards: `tests/test_chat_selection_detail.py`, `tests/test_endpoints_chat.py::test_chat_send_injects_selected_node_content`.

### D-2026-06-23-F — chat subprocess spawns with `stdin=DEVNULL` (fixes in-app Codex no-response hang)

- **What:** `ChatProvider.stream_turn`'s subprocess spawn (and the `_SubprocessFactory` protocol + `_default_spawn`) now pass `stdin=asyncio.subprocess.DEVNULL`.
- **Why:** the spawn set `stdout`/`stderr=PIPE` but never set `stdin`, so the child inherited the engine sidecar's stdin, which is not at EOF. `codex exec` reads stdin for "additional input" even when the prompt is passed as a positional arg (it prints `Reading additional input from stdin...` to stderr), so it blocked indefinitely and the turn yielded **no response** — exactly the "코덱스는 응답이 없고" the user reported. Reproduced directly: `codex exec --json` returns a clean `agent_message` and the engine parser already matches its event shape (`thread.started` / `item.completed`+`agent_message` / `turn.completed`), so the only fault was the open stdin.
- **Scope:** shared base, so it covers claude / codex / (future) providers. The prompt is always an arg; no provider is meant to read stdin, so DEVNULL is universally correct.
- **Relation to D-2026-06-23-E:** independent bug. E was Claude erroring on a bogus flag (loud failure); F is Codex silently hanging on stdin (quiet failure). Both surfaced in the same in-app chat test session.
- **Approval:** user-reported bug, 2026-06-23 ("코덱스는 응답이 없고.."), user chose to investigate Codex before rebuilding.
- **Spec impact:** none. Guard: `tests/test_chat_session.py::test_stream_turn_closes_child_stdin`.

### D-2026-06-23-E — remove the bogus `--exclude-dynamic-system-prompt-sections` claude flag (it broke all in-app Claude chat)

- **What:** The `claude -p` spawn (`chat_providers/claude_code.py::_build_command`) no longer passes `--exclude-dynamic-system-prompt-sections`.
- **Why:** that flag does not exist in the claude CLI. It was introduced by D-2026-06-21-I to "keep cwd / env / memory-paths / git-status out of the system prompt," but was **never verified against the CLI** (an honesty-rule violation — 추측/지어내기 금지 for CLI flags). The installed CLI (2.1.17) rejects it (`error: unknown option '--exclude-dynamic-system-prompt-sections'`), so **every** Claude chat turn — any model, Opus included — died before emitting output. The user hit it the moment they chatted with Claude Opus in the debug `.app`.
- **Impact on D-2026-06-21-I's goal:** none. The real isolation is `--setting-sources local` (no parent/global CLAUDE.md discovery) + `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` (no auto-memory). The removed flag was only a token/privacy nicety; the CLI offers no equivalent, so it is dropped, not replaced.
- **Verification:** every remaining spawn flag (`--print` / `--output-format` / `--include-partial-messages` / `--verbose` / `--allowedTools` / `--setting-sources` / `--session-id` / `--resume` / `--model`) was checked against `claude --help` and is supported — so the next turn won't hit a different unknown option.
- **Approval:** user-reported bug, 2026-06-23 ("클로드 오푸스로 하니 에러나네 … unknown option '--exclude-dynamic-system-prompt-sections'"). Corrects D-2026-06-21-I.
- **Spec impact:** none. Guard: `tests/test_chat_session.py::test_stream_turn_yields_start_delta_complete_on_success` now asserts the flag is **absent**.

### D-2026-06-23-D — every service release (`vS`) anchors to the project mission (format F refs)

- **What:** `publish_service` now always includes `refs.anchors.mission = "mission"` in the `vS` manifest (guarded by `"mission" in vP`). Previously `anchors` carried only `core_values` + `identity`, both selected per-service via the service node's `ref_*_ids`; the mission was never anchored.
- **Why:** anchored to the essence (VISION) — the mission is the project's **single** essence, and every service stands on it. `refs` is the **propagation surface** (format-f.md §5: a `vP+1` element change reaches only the `vS` that *reference* it). With the mission absent from every `vS`, a mission change would propagate to **no** service — the most fundamental possible change reaching nothing, which contradicts "본질을 놓치지 않는다." Unlike `core_value`/`identity` (referenced selectively), the mission is singular with no per-service selection field, so it is anchored universally.
- **Code or spec?** The user asked which fit the purpose. The format-f.md §3.2 example already showed `"mission": "mission"`; the **code** was the side out of step. Fixed the code to match the spec, not the reverse.
- **Compat:** additive — `format_f_version` stays 1 (Solera's intake copies the bundle; an extra anchor key is tolerated). The foundation invariant guarantees ≥1 mission node, so the `"mission" in vP` guard only ever falls through for a malformed `vP`.
- **Approval:** Accepted by user, 2026-06-23 (delegated the code-vs-spec judgment; chose to align with purpose). Surfaced by the mashbill↔Solera pipeline dogfood.
- **Spec impact:** `docs/specs/format-f.md §3.2` field rules note that mission is always anchored. Guard: `tests/test_format_f.py::test_service_refs_anchor_to_project_mission`.

### D-2026-06-23-C — debug channel (`/api/debug`) is auth-exempt (restore the WKWebView introspection bridge)

- **What:** `/api/debug` is added to the auth middleware's open-paths set (alongside `/api/health`), so it is callable without the `PLOT_AUTH_TOKEN`.
- **Why:** the auth seam (later than the debug channel, D-2026-06-09-D) gated everything except `/api/health`. The viewer's debug probe (`debugProbe.postProbe`) POSTs snapshots with a **plain unauthenticated** `fetch`, and the agent GETs them — neither carries the per-launch token the shell mints. So the probe was 401'd, no snapshot landed, and the only WKWebView introspection bridge (CDP can't attach to a Tauri WebView on macOS) was dead. Discovered while trying to visually verify the format F publish UI.
- **Safety:** `/api/debug` is **dev-only** — registered only under `PLOT_DEBUG=1` (the debug-flavor shell sets it), in-memory (cleared on restart), localhost-bound, and NOT product surface. In a release build the route isn't registered, so exempting the path is harmless there.
- **Alternatives:** route the probe through the token (`engineFetch`) — rejected: it fixes the POST but the *agent's GET* still needs the token, which is per-launch and not extractable (macOS hides process env). Exempting the path makes both sides work.
- **Approval:** Accepted by user, 2026-06-23 (chose to fix the debug channel to verify in-app).
- **Spec impact:** none. Guard: `tests/test_auth.py::test_debug_channel_open_without_token_in_debug_flavor`.

### D-2026-06-23-B — codex reasoning effort is a SEPARATE control (reverses D-2026-06-22-C combined entries)

- **What:** Model and reasoning effort are chosen with two distinct dropdowns, not one combined `<slug>:<effort>` model entry. Engine: `parse_codex_models` emits ONE bare `ModelOption` per model (`id` = slug) carrying its `supported_reasoning_levels` as a separate `efforts` list. Viewer: `ChatModelSelector` shows a model dropdown + (when the selected model has efforts) a separate effort dropdown, splitting any stored `<slug>:<effort>` apart for display and recombining the pick into `<slug>:<effort>`.
- **Why:** user direction ("effort 는 분리하는게 맞는거 같아요. 모델 따로 에포트 따로"). The combined entries (D-2026-06-22-C) multiplied the model list by its effort levels and coupled two independent choices into one control.
- **Design:** persistence stays `<slug>:<effort>` so **`CodexProvider` is unchanged** (it already splits that into `--model` + `-c model_reasoning_effort=`); only the catalogue shape (per-model `efforts`) and the viewer UI change. A bare slug (default effort) round-trips as before.
- **Approval:** Accepted by user, 2026-06-23.
- **Spec impact:** none (the `/api/chat/models` response + selector are runtime, not wire-contract). Guards: `tests/test_chat_models.py::test_parse_codex_models_carries_reasoning_levels_separately` (engine); `viewer/tests/chat-effort-control.test.tsx` (viewer split / recombine / no-effort cases).

### D-2026-06-23-A — Gemini (agy) chat provider temporarily removed (re-add October)

- **What:** The gemini chat provider is removed from the product for now — engine (`ProviderName` literal, `_PROVIDERS`, `chat_providers/gemini.py`, `GeminiProvider`, the `agy models` catalogue branch, mcp/chat endpoint validation sets) and viewer (`McpProviderName`, the `chat.providers.gemini` i18n label, stale test fixtures). Claude Code + Codex are unaffected. The full impl stays in git history.
- **Why:** user direction — gemini (via the `agy` CLI) is untestable in the current setup, so it's pulled rather than left half-verified, and slated to return in October. Removing the literal cascades cleanly (mypy-enforced); a half-removal (keeping `gemini.py` dormant) would leave dangling references.
- **Restore (October):** add `"gemini"` back to `ProviderName` + the `_PROVIDERS` entry + `GeminiProvider` wiring (`chat_session`) + the `agy` model branch (`chat_models`) + the viewer `McpProviderName` / i18n label. git history has the deleted `chat_providers/gemini.py` and the removed tests.
- **Approval:** Accepted by user, 2026-06-23 ("제미나이 빼버리죠 … 제미나이는 10월에 넣읍시다").
- **Spec impact:** none (provider set is not a wire-contract field). Guards: the chat/mcp tests now pin claude-code + codex only.

### D-2026-06-22-H — publish UI is format F: 설계도 발행 → vP, service publish → vS, per-node publish retired

- **What:** The viewer's publish surface is repointed at format F (INT-g ⓑ + ⓒ), **reusing the existing buttons** — no net-new publish UI:
  - **vP (project snapshot)** ← the existing Header **`📤 설계도 발행`** action. It still bumps `blueprint_version` + git-tags (the freeze mechanism), and now **also** writes the format F `vP` snapshot (manifest + design). D-2026-06-22-D: "vP = blueprint_version의 진짜 정체."
  - **vS (service release)** ← publishing a **service** node. The inspector publish footer, when the selected node is a `service`, calls the format F `vS` endpoint (the whole service bundle: 5칸 + features + UX flows) instead of a per-node MD.
  - **per-node publish retired (ⓒ)** — every other kind (mission / core_value / identity / actor / feature / entity / step / …) is no longer individually publishable: in format F it is an *element inside* `vP`/`vS`, not its own release. The per-node publish footer, unpublish link, and published-versions history are removed for non-service kinds; the engine's `node_publish` / `node_unpublish` / `node_published_list` endpoints + `node_publish.py` + per-node `version` / `_publish_baseline` fields + the old `published/{kind}/{node}/v*.md` layout are retired.
- **Why:** anchored to VISION + D-2026-06-22-D/E/F/G — the deliverable the external agent reads is the *frozen bundle*, and the bundle is 2-layer (vP project-shared + vS service). Per-node publish was the pre-overhaul model; keeping it alongside format F means two publish mental models for the same canvas. The user confirmed the existing buttons already cover the two layers, so this is a **rewire + demolition**, not new UI.
- **Sequence:** ⓑ rewire first (additive: vP + vS reach format F), then ⓒ retire per-node (viewer UI → engine backend), each as atomic green commits — so the publish UI is never left with zero working triggers.
- **Shipped:** ⓐ HTTP endpoints (v0.107.0, D-22-G) · ⓑ viewer rewire (plot `c1a218a`) · ⓒ viewer UI retirement (plot `cd61993`) · ⓒ engine backend retirement (v0.108.0 — `node_publish.py` / `md_publish.py` / `propagation.py` + per-node endpoints + `publish_node_tool` + `_dirty` decoration + orphaned git helpers deleted). **Deferred (no user value, wire-breaking):** removing the vestigial node `version` / `_publish_baseline` fields — a schema-regen change tracked separately; the fields stay (default-valued, unused) for now.
- **Alternatives:** add separate format F buttons beside the per-node ones — rejected (redundant UI, two mental models). Keep per-node publish as well — rejected (MECE: a node is published *as part of* its vP/vS, not standalone).
- **Approval:** Accepted by user, 2026-06-22 ("C로 갑시다" = full ⓑ+ⓒ, after confirming the buttons already exist). Builds on D-2026-06-22-G.
- **Spec impact:** `storage-publish.md §발행` — the publish model is now format F 2-layer (per-node section retired). Guards land per-step in `plot/viewer/tests/*` (rewire + eligibility) and `noory-ai/mashbill/tests/*` (endpoint removal).

### D-2026-06-22-G — format F publish reachable over HTTP (INT-g first step; viewer UI + per-node retirement still gated)

- **What:** Two POST endpoints expose the format F write half on the HTTP surface, mirroring the existing MCP tools: `POST /api/projects/{id}/publish/snapshot` (→ `vP` project snapshot) and `POST /api/projects/{id}/services/{service_id}/publish` (→ `vS` service release). Thin wrappers over the tested `format_f.publish_project_snapshot` / `publish_service`. Error mapping: 404 (project/service not found), **409** for the two write-boundary gates — bootstrap (no `vP` yet) and refs-integrity (a ref does not resolve in the based_on `vP`).
- **Why:** the MCP path is the 주경로, but the .app is the product (VISION) and its viewer talks to the engine over HTTP — so a format F publish button needs an HTTP endpoint. This is the decision-free precursor to INT-g (the endpoint is needed regardless of where the button lands). User chose "엔진 HTTP 먼저" (2026-06-22).
- **Still gated (NOT done here):** the viewer publish **UI** (button placement / modal / flow — proprietary `plot/` repo, UX decision) and the **per-node publish retirement** (removing `node_publish` + per-node `version` + the old `published/{kind}/{node}/v*.md` layout + 📤). Removing per-node now would delete the only user-facing publish UI before format F has one — so the UI lands first.
- **Alternatives:** build the full INT-g (endpoints + viewer UI + retirement) in one go — deferred (crosses repos, needs UX decisions). Skip HTTP and keep format F MCP-only — rejected (the viewer can't reach MCP tools; an in-app publish needs HTTP).
- **Approval:** Accepted by user, 2026-06-22 (AskUserQuestion "INT-g 접근" → "엔진 HTTP 먼저"). Engine 714 green, mypy strict + ruff clean.
- **Spec impact:** none new — the neutral contract (`format-f.md`) is unchanged; HTTP is a Novel-internal trigger. Guards: `tests/test_api_endpoints.py::{test_format_f_snapshot_endpoint, test_format_f_snapshot_unknown_project_is_404, test_format_f_service_publish_endpoint, test_format_f_service_without_snapshot_is_409, test_format_f_service_unknown_service_is_404}`.

### D-2026-06-22-F — format F design files render the real content (richer vP/vS rendering; entity-summary bug fixed)

- **What:** The published `design/*.md` files now carry the actual design content the external agent reads, not stubs. **foundation.md** renders each node's *primary* typed field (`mission.statement` / `core_value.definition` / `identity.description`) in addition to `body`, grouped under 미션 / 코어 밸류 / 아이덴티티 sections under a framing header; the element hash now folds in that primary field (so an essence change registers in the ID-diff). **entities/{slug}.md** renders `summary` (the '무엇을 담나' line) with `id`/`kind` frontmatter. **actors.md** adds a 관계 (주고받음) section rendering edges between actor nodes (label / action_verb). **service.md** surfaces the service's vP refs (참여 액터 / 지키는 가치 / 정체성 결, by slug) so it reads standalone.
- **Bug fixed:** the entity rendering read a non-existent `body` attribute (the field is `summary`), so every entity design file — and its content hash — was **empty**. Latent since v0.103.0; an entity change would not have surfaced in the ID-diff.
- **Why:** anchored to VISION — the canvas IS the deliverable the external agent reads; a name-only design file fails the handoff. format-f.md §3 mandates the primary fields + actor 주고받음 + service refs; the rendering was reading the wrong / secondary fields. No new behavioural choice — conforms `format_f.py` to the spec.
- **Alternatives:** entity per-file edge/relationship rendering — out of scope (spec keeps entity files to a one-line '무엇을 담나'; entity relationships live on the entities canvas, a later concern). Prose single-line UX flow — deferred (the structured rendering is graph-faithful + gives a stable hash).
- **Approval:** Accepted — implements the approved format-f.md spec (D-2026-06-22-D/E). Engine 708 green, mypy strict + ruff clean.
- **Spec impact:** none new — conforms to `noory-workspace/docs/specs/format-f.md` §3/§4. Guards: `tests/test_format_f.py::{test_foundation_design_renders_primary_statements, test_foundation_hash_tracks_primary_statement, test_entity_design_renders_summary, test_actors_design_renders_relationships, test_service_design_surfaces_refs}`.

### D-2026-06-22-E — vS bundle carries its features + UX flows (completes INT-2 per format-f.md §3/§4)

- **What:** `publish_service` now puts the service's **features** into the `vS` release, not just the service node. Each feature nested under the service (a directed edge `service → feature`, D-2026-06-17-D) becomes an **owned element** `{id: feature/{slug}, kind: "feature", hash, flow: true}` with a `design/features/{slug}.md` that renders its detail-canvas **UX flow** (참여자 + 행동(steps, ordered, negative-polarity marked) + 분기(decisions → branch-labelled edges) + 참고(ambient notes)). The features' steps' `ref_entity_ids` roll up into the release's `refs.entities` (resolved to `vP` entity slugs, not copied). The refs-integrity gate (§1.4) now also covers those entity refs, and all ref validation runs **before any file is written** (validate-before-write).
- **Why:** without this the published service bundle was a name-only stub — `feature/login` had no flow, so a Solera `realizes: feature/login` resolved to nothing and the Execution handoff was empty. The canvas IS the deliverable the external agent reads (VISION); the feature flows are the Execution-handoff content. format-f.md §2/§3/§4 already mandated this — the v0.103.0 walking skeleton shipped the layer shape but only the service node; this fills the gap.
- **Alternatives:** prose single-line flow (format-f.md §4 example) — deferred to a later enrichment pass (design-MD richness); the structured deterministic rendering here is graph-faithful and gives a stable element hash for the ID-diff. Lenient entity refs (drop dangling) — rejected for strict refs-integrity (a dangling entity ref breaks Solera self-containment, same as actor refs).
- **Approval:** Accepted — implements the already-approved format-f.md spec (D-2026-06-22-D); no new behavioural choice. Engine 704 green, mypy + ruff clean.
- **Spec impact:** none new — conforms `format_f.py` to `noory-workspace/docs/specs/format-f.md` §2/§3/§4. Guards: `tests/test_format_f.py::{test_publish_service_includes_feature_elements, test_feature_design_renders_capability_and_flow, test_feature_element_hash_tracks_flow_change, test_service_entity_refs_collected_from_steps, test_publish_service_with_dangling_entity_ref_is_rejected}`.

### D-2026-06-22-D — Phase P: 2-layer format F publish (vP project snapshot + vS service release); per-node publish coexists, retires later

- **What:** The mashbill→Solera publish contract is a **2-layer frozen bundle** (= "format F", design SSOT `noory-workspace/docs/plans/phase-p-format-f.md`, spec `noory-workspace/docs/specs/format-f.md`). **`vP` (project snapshot)** freezes the *shared structure* — 본질(Foundation) + Actors + Entities — under `published/_project/vP{N}/`. **`vS` (service release)** freezes one service (5칸 + features + category) under `published/{slug}/vS{N}/`, pins `based_on: vP`, and references shared elements **by stable slug, not by copy** (so re-publishing one service can't fork the shared entities — the v1 single-layer draft's fatal flaw, caught by mashbill-design-red-team). Stable ids are **slugs** minted into a per-project `_slugs.json` registry, keyed on node id so a slug survives a label change (P-4 = explicit slug). Versioning collapses the old 3 axes to **2 semantic axes (vP, vS) + git tag (the freeze mechanism) + content-hash ID-diff (changed/removed/added, derived)** — per-node `version` numbers are not used by format F. Two write-boundary gates: **bootstrap** (a `vS` requires a `vP`) and **refs-integrity** (every ref must resolve in the based_on `vP`). The reverse channel (feedback / retro) uses the same slug vocabulary; mashbill reflection stays human-in-the-loop (no code auto-import — R8).
- **§7 sub-decisions (user, 2026-06-22):** A single vP (shared structure moves as one); B service-granular publish with feature-standalone as an exception; C release-dirty + publish-eligibility + refs-integrity gate; D clean migration cut (no live per-node published data).
- **Scope shipped (INT-1a/2/3/4):** `mashbill/format_f.py` (write half: `publish_project_snapshot` / `publish_service` / `mint_slug`, v0.103.0) + `noory-ai/solera/solera/intake.py` (read half: `import_release` / `diff_releases` + `format_f_version` guard, solera v7.3.0). Walking-skeleton e2e proven: mashbill publish → Solera import → plan → run → gate PASS, with neither package importing the other. Built **alongside** the existing per-node publish (`node_publish.py` + `project_publish` blueprint_version) — **not yet a replacement.**
- **Not yet done (follow-on):** retire per-node publish (`node_publish.py`, per-node `version` field, the old `published/{kind}/{node}/v*.md` layout) + wire a `realizes` field through the Solera CLI. Tracked in `workspace/solera-redesign.md` (INT follow-on).
- **Why:** anchored to VISION — the canvas IS the deliverable the external agent reads, a *service* is the Execution handoff unit, and 본질·개념(Foundation·Actors·Entities) are project-shared. So the publish shape *is* 2-layer; forcing it to one layer forks shared structure. Foundation built first-principles + adversarially verified (2× red-team) over a YAGNI-minimal patch, per user direction.
- **Alternatives:** single-layer per-service bundle (v1 draft) — rejected (entity/actor fork). Keep 3 versioning axes — rejected (vP=blueprint_version reinterpreted; per-node retired). label-slugify or node.id slugs — rejected for explicit slug (stability vs readability).
- **Approval:** Accepted by user, 2026-06-22 (§7 AskUserQuestion + "마무리로 갑시다"). Design = `phase-p-format-f.md` (red-team v1→v2). Narrows D-2026-06-12-A / builds on D-2026-06-21-AB.
- **Spec impact:** `noory-workspace/docs/specs/format-f.md` (new, the contract) + `storage-publish.md` §발행 gains a format F section. Engine guard `tests/test_format_f.py::test_manifest_contract_shape_is_pinned`; reader guard `solera tests/test_intake.py::test_import_rejects_unsupported_format_f_version`. mashbill 698 green, Solera 101 green, both mypy + ruff clean.

### D-2026-06-22-C — codex reasoning effort: model×effort combined entries (composite `<slug>:<effort>` id)

- **What:** The codex model catalogue (D-2026-06-22-B) expands each listed model into one entry **per supported reasoning level** from `models_cache.json` (`supported_reasoning_levels`): id `"<slug>:<effort>"`, label `"<display> (<Effort>)"` (e.g. `gpt-5.5:high` → "GPT-5.5 (High)"). A model with no levels stays a bare `{slug}` entry. The `CodexProvider` splits the composite id on selection: `--model <slug> -c model_reasoning_effort=<effort>` (codex's documented `-c` config override). The selector + wire are **unchanged** — the composite is just the `model` string (no new field), opaque to the viewer, which keeps showing `label` and persisting `id`. gemini already carries effort inside its `agy` label (D-2026-06-22-A/B), so this is codex-only; both providers end up as one combined model×effort dropdown.
- **Why:** codex exposes reasoning effort as a real, separate knob (`model_reasoning_effort`), and the user wants it selectable (2026-06-22). A combined dropdown keeps the UI to one selector, consistent with gemini, with **zero wire/UI change** — the cost is confined to the catalogue builder + the codex provider's arg split.
- **Alternatives:** (b) a separate `effort` wire field + second dropdown (matches codex's native bare-model picker) — rejected by the user (more surface). (c) skip codex effort — rejected: the user asked for it.
- **Approval:** Accepted by user, 2026-06-22 (AskUserQuestion — "합친 드롭다운").
- **Spec impact:** SPEC §R7 "Model selection" (codex entries are model×effort). Engine `chat_models.parse_codex_models` (level expansion) + `chat_providers/codex.py` (`_model_args` composite split). Pinned by `tests/test_chat_models.py` (codex expansion) + `tests/test_chat_model.py` (codex composite → `--model` + `-c model_reasoning_effort`). Engine green. **Requires sidecar rebuild.**

### D-2026-06-22-B — chat model selector is populated from each CLI's live catalogue (reverses D-2026-06-16-C)

- **What:** The in-app chat model dropdown is no longer a hardcoded per-CLI list. It is fetched from a new engine endpoint `GET /api/chat/models?provider=<name>` (`mashbill/chat_models.py`): **codex** → `~/.codex/models_cache.json` (slug + display_name of every `visibility == "list"` + `supported_in_api` model); **gemini** → `agy models` (plain-text labels, used **verbatim** as `--model`, with effort baked into the label); **claude** → its static documented aliases (`fable`/`opus`/`sonnet` — claude publishes stable aliases). The viewer (`ChatModelSelector`) renders one `<option>` per returned `{id, label}` (`id` → `--model`, `label` shown), keeps the current model as an option even when absent from the list, and keeps the **Custom…** free-text fallback. **Fail-soft:** any source error (agy missing / cache unreadable) → empty list → the selector still offers default + Custom…. `ChatModelOption` is hand-mirrored Python↔TS (chat types aren't codegen'd, per D-2026-06-21-Z), so no wire-artifact regen.
- **Why:** The hardcoded approach (D-2026-06-16-C: claude aliases only; codex/gemini blank) showed the user an empty `default / Custom…` — read as "no models" — and was stale on arrival: within this window the live gemini list had already moved 2.5 → 3.1/3.5 + gemma-4, codex to gpt-5.5/5.4. Each CLI already curates its own short, fresh model list; reading that is both more honest and lower-maintenance than a list Novel must chase.
- **Alternatives:** (a) keep hardcoding (D-16-C) — rejected: stale + opaque (the user demonstrated the staleness live). (b) query the vendor API (`/v1/models` / Google ListModels) — rejected: needs keys + auth, and returns a messy full catalogue vs the CLI's curated short list. (c) codex via its private cache is a coupling risk — accepted with fail-soft fallback (a format change yields `[]`, never a crash).
- **Approval:** Accepted by user, 2026-06-22 ("0123 다 해야한다 … 고고"; chose dynamic after seeing the hardcoded list go stale live).
- **Spec impact:** SPEC §R7 "Model selection" row (was D-2026-06-16-C). Engine `mashbill/chat_models.py` + `endpoints_chat.chat_models_endpoint` + `/api/chat/models` route. App viewer `api.ts` (`fetchChatModels` + `ChatModelOption`), `app/mcp.ts` seam, `ChatDock` (fetch + `models` prop; `MODEL_SUGGESTIONS` removed). Pinned by `tests/test_chat_models.py`, `tests/test_endpoints_chat.py` (models endpoint), `viewer/tests/chat-model-catalogue.test.tsx`. Engine 687 green, viewer 1006 green. **Requires sidecar rebuild.**

### D-2026-06-22-A — in-app gemini chat transport: `gemini` CLI → `agy` (Antigravity); stateless per-turn

- **What:** The in-app chat's `gemini` provider now drives the **`agy` (Antigravity) CLI** instead of `gemini`. The provider **name stays `gemini`** — the user-facing identity is the model family; `agy` is only the transport. Command shape: `agy -p --dangerously-skip-permissions [--model <m>] <prompt>`. agy has **no `--output-format stream-json`**, so the JSONL parser is replaced by **plain-text line passthrough** (each stdout line becomes a `delta`). `--dangerously-skip-permissions` replaces gemini's `-y` (auto-approve, same role inside an IDE shell). **Stateless:** agy emits no session id on stdout and its `--continue` resumes the *most-recent* conversation globally, which would cross Novel's per-(project×scope) thread isolation (D-2026-06-13-H) — a silent contamination bug — so the provider **does not resume**; each turn is an independent `agy -p` call.
- **Why:** `agy` is the surface Google is consolidating Gemini onto (user-confirmed, 2026-06-22 — "agy 로 동작하게 된다네요. 통합하는 것 같습니다"); the `gemini` binary's `-p` path is being superseded. Plain-text passthrough is the only honest reading of agy's output (verified: `agy -p` prints text, not JSONL). Stateless is the only **correct** option given agy exposes no per-thread resume handle to stdout — the alternatives either contaminate scopes or depend on Antigravity's private on-disk store.
- **Alternatives:** (a) keep the `gemini` CLI — rejected: superseded transport. (b) `--continue` for multi-turn — rejected: most-recent-global, breaks per-scope isolation (silent bug, banned). (c) `--conversation <id>` by mining `~/.antigravity` for a per-scope id — rejected for now: depends on Antigravity's undocumented private format (brittle). (d) Novel replays prior turns into the prompt for continuity — deferred (session-layer change, token cost).
- **Approval:** Accepted by user, 2026-06-22 ("0123 다 해야한다 … 이름은 유지 좋습니다. 고고"). **Known regression filed:** in-scope multi-turn continuity (old gemini had `--resume`) is lost under agy; resume is a follow-up (option c/d).
- **Spec impact:** SPEC §R7 chat — the gemini transport line + the provider table's "Brain" row (`gemini` → `agy`). Engine `chat_providers/gemini.py` (command + plain-text `_parse_line`, no session capture). Pinned by `tests/test_chat_session.py` (agy command shape + plain-text delta + no-resume) + `tests/test_chat_model.py` (`--model` still spliced). **Requires sidecar rebuild** for the `.app`.

### D-2026-06-21-AB — flat storage: drop the `{project_id}/` folder layer (one project stored directly under `.noory/plot`)

- **What:** With one-project-per-dir pinned (D-2026-06-21-AA), the intermediate `{project_id}/` folder is redundant, so the lone project's files now live **directly under `.noory/plot`**: `.noory/plot/project.json`, `.noory/plot/foundation/canvas.json`, `…/actors`, `…/services/{sid}/detail.json`, `…/schema`, `…/{canvas}/published/…`. The layout logic concentrates in `storage._project_dir`, which returns `plot_root` itself when no nested `project.json` is present (and the legacy nested `{project_id}/` only while it physically survives). Every other path (`_canvas_file`, schema export, publish, file API, detail-sync, foundation/v01 migrations, the at-tag git prefix) derives from `_project_dir`, so they followed for free once those few self-built paths (`endpoints_files`, `endpoints_tags`, `endpoints_publish`, `schema_export`, `migrate_foundation`, `migrate_v01`) were routed through it. **Lazy migration:** `resolve_plot_root` calls `flatten_nested_project`, which moves a *single* nested project up to the root on open; a multi-project (forbidden-stacking) root is left untouched for the user to reconcile.
- **Why:** Under one-per-dir the `{project_id}` segment is a UUID-ish folder that never holds a sibling — pure indirection. Flat matches the pipeline design (`docs/idea/harness/04-pipeline.md` "층 없이 평탄") and makes `.noory/plot` a project's home directly. Done now while there is no live data at risk (same window as D-2026-06-21-AA).
- **Alternatives:** (a) keep the `{project_id}/` layer (handoff's conservative default) — rejected: the user opted to flatten this session; the indirection has no remaining purpose under one-per-dir. (b) auto-flatten a multi-project root by picking a winner — rejected: silent data choice; leave it for the user (handoff S5). (c) hard id-validation off — rejected: flat addresses the lone project by the root, so `_ensure_project` must verify the stored `id` matches the requested one, else a wrong id would leak the only project (now 404s).
- **Approval:** Accepted by user, 2026-06-21 ("지금 S2까지 진행"). Builds on D-2026-06-21-AA; updates D-2026-06-12-A's disk-layout note.
- **Spec impact:** Engine — `storage._project_dir`/`_ensure_project`, `workspace.enumerate_projects` + new `flatten_nested_project`, `project_io.create_project`/`delete_project`, and the self-built paths listed above. Root `docs/specs/storage-publish.md` §저장 레이아웃 + this repo's `SPEC.md` §Workspace switch to the flat path. Pinned by `test_folder_io.py::test_create_project_builds_flat_layout` / `::test_read_project_with_wrong_id_raises`, `test_noory_migration.py::test_resolve_flattens_single_nested_project` / `::test_resolve_leaves_multiple_nested_projects_untouched`, and the updated nested-path assertions across `test_{migrate,sync,unpublish,published_endpoint,schema_export,file_raw_endpoint,api_endpoints}`. Engine 673 green, mypy + ruff clean. **Requires sidecar rebuild** (S7) for the `.app`.

### D-2026-06-21-AA — one project per `.noory/plot` dir (one-project-per-dir); multiple services = sibling directories

- **What:** `create_project` now rejects creating a *second* project under a `.noory/plot` root that already holds one — even with a fresh id. The guard is `enumerate_projects(plot_root)` non-empty → `FileExistsError`, which the HTTP create endpoint already maps to **409**. `create_project` is the single chokepoint, so this covers both the viewer (`POST /api/projects`) and the MCP tool (`create_project_tool`). Multiple services in a monorepo go in **sibling directories**, each with its own `.noory/plot` (e.g. `apps/web/.noory/plot/{id}` + `services/api/.noory/plot/{id}`). The guard is on the **write** path only — `enumerate_projects` / `discover_projects` still read N projects under a root, so pre-existing multi-project roots and recursive discovery of sibling-dir projects keep working unchanged.
- **Why:** Stacking multiple `project_id` folders under one `.noory/plot` (e.g. `Banas/.noory/plot/{banas, proj-mqmtt316}`) was confusing and let stray/orphaned projects accumulate invisibly. Pinning "one project per dir" makes each project's home unambiguous (its own directory) while leaving the monorepo-of-services model intact via sibling dirs. The user fixed this at a moment with no live data at risk ("지금 아니면 못 하는, 사용자 없을 때 깨는 변경").
- **Alternatives:** (a) keep allowing N projects per root (status quo) — rejected: the stacking confusion is the problem being solved. (b) Also flatten the `{project_id}/` folder layer now so a root holds the canvases directly (S2) — deferred: a large migration touching every storage path + schema export; the handoff recommends weighing cost separately. The 409 guard stands on its own regardless of internal layout. (c) Enforce on `enumerate_projects`/discovery too — rejected: would break reading legacy multi-project roots and recursive sibling discovery; the write-path guard is sufficient and non-destructive.
- **Approval:** Accepted by user, 2026-06-21 (handoff `docs/plans/one-project-per-dir-handoff.md` §사용자 결정; this session implements it). Narrows **D-2026-06-12-A**.
- **Spec impact:** Engine `mashbill/project_io.py::create_project` (guard). Root `docs/specs/storage-publish.md` §저장 레이아웃 + this repo's `SPEC.md` §Workspace & projects gain the one-per-dir line. Pinned by `tests/test_folder_io.py::test_create_second_project_in_same_root_rejected` / `::test_create_in_sibling_dirs_is_allowed` and `tests/test_noory_migration.py::test_discovery_sees_sibling_dir_projects`. Engine 669 green, mypy + ruff clean. **Requires sidecar rebuild** (S7) for the `.app`.

### D-2026-06-21-Z — chat shows the CLI's actual default model when it reports one (claude-code only)

- **What:** The chat model selector's "default" option now shows the model the CLI actually loaded — e.g. `default · claude-opus-4-8` — instead of a bare `default`, **when** the CLI reports it. Mechanics: the engine's claude-code provider parses the stream-json `system`/`init` frame's `model` and emits a new `ChatStreamEvent(type="meta", model=…)`; `useChatStream` records it as `reportedModel`; `ChatDock` lifts it into the `ChatModelSelector`'s default-option label. **Asymmetry by design:** only claude-code reports its model, so codex / gemini keep a plain `default`. **Timing:** the value is only known *after the first turn* of a session (the init frame), and is reset on provider change so a stale model can't leak across CLIs. An explicit user override is unchanged (the picked model stays selected; `meta` only relabels the default option).
- **Why:** When the user hasn't overridden the model, "default" was a label, not a fact — they couldn't see what was actually running. User chose (2026-06-21) to show the real model where the CLI reports it, accepting the claude-only asymmetry, over a per-turn caption or not implementing.
- **Alternatives:** (b) show the model as a per-assistant-turn caption ("ran on …") — rejected: more chrome, same claude-only limit. (c) don't implement, keep the "default" label (YAGNI) — rejected: the user wants the real model visible. Inferring codex/gemini defaults — impossible (their CLIs don't report it).
- **Approval:** Accepted by user, 2026-06-21 (AskUserQuestion — "보고되면 표시").
- **Spec impact:** Engine `chat_providers/base.py` (`meta` event type + `model` field) + `chat_providers/claude_code.py` (`_extract_anthropic_model` → `meta`). App viewer `types.ts` / `api.ts` (mirror `meta` + `model`), `useChatStream` (`reportedModel`), `ChatDock` (`ChatModelSelector` reported-default label + lift). The chat event is **hand-mirrored**, not codegen'd, so no wire-artifact regen. Pinned by `tests/test_claude_stream_parse.py` (init→meta), `use-chat-stream.test.ts` (meta sets reportedModel), `chat-model-reported.test.tsx` (default-option label). Engine 667 green, viewer 1003 green. **Requires sidecar rebuild.**

### D-2026-06-21-Y — native File > Open Folder… menu (open a different folder without quitting to the picker)

- **What:** The Tauri shell (`plot/src-tauri/src/lib.rs`) extends the platform **default** menu (so Quit / Edit / Window survive) with a **File** submenu carrying **Open Folder…** (`CmdOrCtrl+O`), inserted at index 1 (right after the macOS app menu). Clicking it emits a `menu:open-folder` event; the viewer listens (`useMenuOpenFolder`, mounted at the App root before any early return) and runs the **shared** folder-pick + `?project_path=` navigation. That navigation moved into `openProjectFolder.ts` so the picker screen (`ProjectPicker`) and the menu use one SSOT.
- **Why:** Until now the only entry point to open a different folder / workspace was the initial "Open Folder" picker screen — once a project was loaded there was no in-app way to switch to an unrelated folder. A native File menu is the conventional location (Don't-Make-Me-Think).
- **Alternatives:** (a) do the dialog + navigate entirely in Rust (webview `eval`) — rejected: duplicates the navigation logic in Rust instead of reusing the viewer's; the emit→listen path keeps a single TS SSOT. (b) replace the whole menu instead of extending the default — rejected: would drop standard Quit / copy-paste / Window shortcuts.
- **Approval:** Accepted by user, 2026-06-21 (session plan item; ROADMAP 🅿).
- **Spec impact:** App repo only — `plot/src-tauri/src/lib.rs` (menu + `on_menu_event` emit) and `plot/viewer/src/shell/{openProjectFolder.ts,useMenuOpenFolder.ts}` + `ProjectPicker` refactor + `App` mount; new direct dep `@tauri-apps/api`. Pinned by `tests/menu-open-folder.test.tsx` (subscribes only in Tauri; event fires pick+navigate; cancel = no-nav). Full viewer suite green (999). **Verify in app:** with a project open, File > Open Folder… → picker → switching folders navigates.

### D-2026-06-21-X — engine read leniency: drop dangling edges on GET instead of rejecting (D-2026-06-21-R follow-up)

- **What:** `canvas_io.read_canvas` now runs a new `_drop_dangling_edges` read-side healer (right before `CanvasDoc.model_validate`, after every other migration) that strips any edge whose source or target node is absent from the canvas. The synthetic project anchor (`PROJECT_ANCHOR_ID`) stays a valid endpoint (D-2026-05-04-B), so an edge to it survives. Idempotent; persists the healed canvas on first read (same shape as `_drop_retired_kinds`). The **write path is unchanged** — `CanvasDoc` still hard-rejects dangling edges on PUT / `update_canvas`, because the viewer prunes them before save (D-2026-06-21-R).
- **Why:** D-2026-06-21-R fixed the in-memory (PUT) case but explicitly left on-disk resilience as a follow-up: a `canvas.json` already corrupted with a dangling edge (a node removed without its incident edges) made the engine 400 every GET, so the canvas could never open. Healing on read fixes the canvas regardless of how it was corrupted, and is the engine analogue of the viewer's persist-boundary prune.
- **Alternatives:** (a) heal only when validation actually fails (try/except around `model_validate`, re-strip, retry) — rejected: opaque, and the explicit pre-pass matches the existing read-path migration chain. (b) make the *write* path also lenient — rejected: a PUT carrying a dangling edge is a real viewer bug (the prune guard should have run), so the engine should keep rejecting it to surface regressions.
- **Approval:** Accepted by user, 2026-06-21 (standing follow-up named in D-2026-06-21-R; session plan item).
- **Spec impact:** Engine `noory-ai/mashbill/mashbill/canvas_io.py` (`_drop_dangling_edges` + one call in `read_canvas`). Pinned by `tests/test_dangling_edges.py` (unit: strips missing-node edge / keeps anchor edge / no-op when clean; integration: a corrupted canvas.json opens via `read_canvas`). Full engine suite green (665). **Requires sidecar rebuild** for the standalone `.app`.

### D-2026-06-21-W — fix: `.noory/plot/.noory/plot/{id}` double-nesting (resolve_plot_root guard) + workspace cleanup

- **What:** `resolve_plot_root(project_path)` now **guards against double-nesting**: if `project_path` already points AT a `.noory/plot` data root (`base.name == "plot" and base.parent.name == ".noory"`), it returns that path directly instead of appending another `.noory/plot`. Engine change in `mashbill/workspace.py`.
- **Why:** A project (`id="banas"`) was found orphaned at `playground/Banas/.noory/plot/.noory/plot/banas/` — one `.noory/plot` too deep, invisible to discovery (which scans `{ws}/.noory/plot/*` and prunes `.noory`). Cause: `resolve_plot_root` blindly did `base / ".noory" / "plot"` with no guard, and an **MCP caller** passed a `project_path` already pointing into `.noory/plot` (the viewer can't trigger it — the dir picker prunes `.noory`). The id was a human "banas" (not `proj-{ts}`), confirming the MCP/agent path, not the viewer.
- **Cleanup performed (data, with user OK "싹다 깔끔하게"):** moved the orphaned `…/.noory/plot/.noory/plot/banas` → `…/.noory/plot/banas` (real canvases — foundation 7 nodes — preserved, NOT deleted); `rmdir`'d the now-empty `.noory/plot/.noory` wrappers under `Banas/` and `playground/` (empty-only removal). Banas workspace now has two correctly-placed projects (`banas` + `proj-mqmtt316`); the user dedupes in-app (no project with user nodes deleted without explicit per-project confirmation).
- **Alternatives:** delete the orphaned banas as a presumed dup — rejected (it had distinct user work, 7 foundation nodes vs proj-mqmtt316's 3; can't verify redundancy → never blind-delete user data). Fix only the caller — insufficient (the engine guard is the durable invariant for any caller).
- **Approval:** Accepted by user, 2026-06-21 ("둘다 해주세요. 정리 싹다 … 깔끔하게").
- **Spec impact:** Engine (`mashbill/workspace.py::resolve_plot_root`). Pinned by `test_noory_migration` (`…_guards_against_double_nesting`, `…_double_nest_then_create_lands_correctly`). Engine suite green (661). **Requires sidecar rebuild** for the bundled .app + the agent's MCP binary to pick up the guard.

### D-2026-06-21-V — every workspace panel gets a hard pixel minimum width (chat 280 · canvas 480 · tools 280)

- **What:** All three `Panel`s in `WorkspacePanels` get pixel `minSize`s: chat `"280px"`, canvas `"480px"`, tools/sidebar `"280px"` (were numeric 14/30/12 = px, i.e. effectively none). `react-resizable-panels` v4 reads a bare number as **pixels** and a unit-suffixed string by its unit (verified in lib source: `case "number": return [e,"px"]`); `defaultSize` stays proportional. **`collapsible` removed from chat + sidebar** — a collapsible panel snaps to 0 (vanishes) when dragged *past* its min; the user wants a hard stop, never disappearing. A divider drag now stops at the neighbour's min, period.
- **Why:** User: "캔버스 최소 너비를 정하죠" → "옆으로 밀면 다른 창이 좁아지는데 그렇게 되지 않게 … 좌우 패널들도 최소 너비를" → "최소폭에서 멈추긴 하는데 더 밀면 아예 사라지네요" (collapse). A resize must not crush *or vanish* a neighbour.
- **Approval:** Accepted by user, 2026-06-21 (values proposed + applied; adjustable).
- **Spec impact:** App-repo viewer (`WorkspacePanels` minSizes). Config value — runtime resize enforcement isn't unit-testable in jsdom; verified in the .app. Full viewer suite green (995).

### D-2026-06-21-U — project switcher → header (next to path); tab bar = scrollable tabs + fixed version/publish; chat default narrower

- **What:** Three tab-bar/header tweaks: (1) the **project switcher (name ▾) moves from the tab-bar center to the header**, right of the workspace path (path = which workspace, project = which one inside — one "where am I" cluster). The tab bar keeps only tabs + the blueprint-version badge + publish. (2) The tab bar's **tabs are the shrinking side** — `flex-1 min-w-0 overflow-x-auto`, tabs `shrink-0 whitespace-nowrap` — so when the canvas narrows they scroll horizontally instead of compressing; the **version + publish cluster is `shrink-0`** and never wraps/moves. (3) The **publish button is `whitespace-nowrap`** (it wrapped to 2 lines when narrow). (4) **Chat panel default width 22% → 18%** (canvas 56% → 60%) — chat doesn't need 22%; still drag-resizable.
- **Why:** User: "프로젝트 선택 드롭다운 메뉴는 워크플로우 path 옆에 둘까요?" (yes, version stays in tab bar — ⓐ); "캔버스가 좁아질 때 퍼블리시 블루프린트가 두 줄이 되는데 1줄이 되게 … 줄어드는 쪽은 탭이어야 하고 줄어들면 탭 리스트는 스크롤"; "채팅창은 왜 이렇게 커진걸까요?" (the `:v2` reset put it back to the 22% default → lower it).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** App-repo viewer (`Header` gains the switcher + project props; `CanvasTabs` drops the switcher/project props, gains `hasProject`, tabs-scroll + fixed cluster; `BlueprintPublishButton` nowrap + shrink-0; `WorkspacePanels` chat 18 / canvas 60; `App` rewires project props Header←). Pinned by updated `canvas-tabs-root` (version not name; hasProject gate) + new `header-project-switcher` (name in header). Full viewer suite green (995).

### D-2026-06-21-T — workspace layout: chat LEFT · canvas CENTER · tools(palette/inspector) RIGHT

- **What:** `WorkspacePanels` reorders the three columns to **chat | canvas | tools**. Previously chat + tools(sidebar) were both on the left of the canvas. The tools panel default widens 16% → 22% (it now hosts the inspector too, D-2026-06-21-Q); canvas 62% → 56%; chat stays 22%. The tools panel's divider border flips `border-r` → `border-l` (canvas-facing). Layout storage id bumped `plot:workspaceLayout` → `:v2` so the new order starts from a clean default.
- **Why:** User — "채팅과 캔버스 컨트롤 패널이 둘 다 왼쪽에 있잖아요 … 이거 하려고 내가 인스펙터 바꾸라고 했지." Moving the inspector into the tools panel (Q) was the enabling step: it freed the canvas's right edge so chat ↔ tools could split to opposite sides. User picked **tools on the RIGHT, chat on the LEFT** ("채팅 왼쪽 / 도구 오른쪽").
- **Alternatives:** tools left / chat right (Cursor/Copilot convention) — offered + recommended, but the user chose chat-left / tools-right. Inspector as its own 4th column — rejected (palette + inspector stay one "tools" panel, cover-on-select per Q).
- **Approval:** Accepted by user, 2026-06-21 (AskUserQuestion → "채팅 왼쪽 / 도구 오른쪽").
- **Spec impact:** App-repo viewer (`WorkspacePanels` order/sizes/storage id; `SketchSidebar` border side). Pinned by `workspace-panels-order` test. Full viewer suite green (993). **Deferred small follow-ups (logged, not "fast"):** native File menu (open other folder), inspector auto-widen on select, engine lenient read.

### D-2026-06-21-S — empty-canvas onboarding hint (all canvases, anchor-aware)

- **What:** When a canvas has no user nodes, a non-blocking hint appears top-center (`CanvasEmptyHint`, rendered by SketchCanvas, gated on `doc.nodes.length === 0`): a per-canvas line of what belongs there (foundation / actors / services / entities / feature) + a shared "drag from the palette, or ask your AI agent" line. `pointer-events-none` so dropping onto the canvas still works through it; positioned at the top so it never covers the centered project anchor.
- **Why:** User: the entities canvas "현재 아무것도 없어서 … 안내라도 해줘야할 것 같은데". Generalized to all canvases (ⓑ): the user weighed ⓐ entities-only vs ⓑ all and asked which is best. Decisive point — the **synthetic anchor is NOT in `doc.nodes`** (it's derived from `ProjectDoc.anchors`), so "0 nodes" correctly means "nothing placed yet". Fresh services/entities are genuinely empty → the hint fires exactly where it helps; seeded canvases (foundation/actors) stay quiet. So ⓑ is not dead weight.
- **Alternatives:** ⓐ entities-only — rejected (services is equally empty on a fresh project; one generic anchor-aware component covers all consistently for little extra cost). A blocking modal / full-canvas empty state — rejected (must not block dragging onto the canvas, and the anchor is always rendered so it's never visually blank).
- **Approval:** Accepted by user, 2026-06-21 ("네 모든 캔버스 공통으로 갈까요?" + asked for the recommendation → ⓑ).
- **Spec impact:** App-repo viewer (`CanvasEmptyHint` new; one gated render in SketchCanvas). New i18n `canvas.empty.{hint,foundation,actors,services,entities,feature}` (en+ko parity). Pinned by `canvas-empty-hint` (per-kind message) + `SketchCanvas.regression` (shows when empty, hidden once a node exists). Full viewer suite green (992).

### D-2026-06-21-R — fix: a dangling edge (node removed, edge kept) 400'd every save; prune at the persist boundary

- **What:** `useCanvasPersist.applyEdit` now runs `pruneDanglingEdges(next)` (new pure `canvases/sketch/pruneDanglingEdges.ts`) before caching / persisting — dropping any edge whose source or target node is absent. The viewer owns the canvas SSOT, so it must never emit a doc that the engine's `CanvasDoc` validator rejects. **The synthetic project anchor (`PROJECT_ANCHOR_ID`) is exempted** — it lives in `ProjectDoc.anchors`, not `doc.nodes`, but is a valid edge endpoint (D-2026-05-04-B), exactly as the engine validator allows (`node_ids | {PROJECT_ANCHOR_ID}`). A first cut omitted this and silently dropped ALL anchor edges on save (edges broke across every canvas, caught same-session); the anchor allowance + a regression test (`KEEPS edges to the synthetic project anchor`) fix it.
- **Why:** User hit a live error: `1 validation error for CanvasDoc … edges reference unknown nodes: ['n_mqn21dco_3ryl']`. The engine hard-rejects a canvas with edges pointing at missing nodes; a single mutation path that drops a node without its edges then wedges every subsequent save (PUT 400). The id was in-memory (not on disk — grep of the workspaces found nothing), i.e. a save being rejected, not a load. The two obvious delete paths already prune edges (`useFlowHandlers.handleNodesDelete`, and `applyNodeChangesToDoc` handles only position/dimensions, never removal), so the leak is a subtler path (undo/redo replay or a composition reshape) — not pinned. The persist-boundary guard fixes it independent of the source, which is the correct invariant location regardless.
- **Alternatives:** (a) hunt and fix the exact leaky path only — insufficient (the next leaky path recurs); the chokepoint guard is the durable invariant. (b) make the engine's read lenient (drop dangling edges on GET instead of rejecting) — sensible **follow-up** for resilience to any already-corrupted file on disk, but the reported case is a PUT (in-memory), so viewer-side pruning resolves it without an engine change / sidecar rebuild.
- **Approval:** Accepted by user, 2026-06-21 (bug report mid-session).
- **Spec impact:** App-repo viewer only (`pruneDanglingEdges` + one call in `applyEdit`). Pinned by `prune-dangling-edges` test. Full viewer suite green (987). **Follow-up:** engine-side lenient read (drop dangling edges on GET) for on-disk resilience.

### D-2026-06-21-Q — node inspector moves into the left sidebar panel (cover-palette-on-select); feature canvas loses its always-on read-only inspector

- **What:** Phase 2 of the panel reorg (Phase 1 = D-2026-06-21-N). The node inspector no longer overlays the canvas on the right; it renders **inside the left sidebar panel**, covering the palette when a node is selected and reverting to the palette on deselect (decision **1-ⓐ**). Mechanics: the inspector's data graph stays in `SketchCanvas`/`SketchInspectorBindings`; the canvas `createPortal`s the inspector DOM into a host element owned by `SketchSidebar`, coordinated by a tiny `InspectorPanelContext` (shares only the host element + a `active` boolean). `BaseInspector` now fills its container (the old `absolute right-0` overlay + narrow/wide width toggle removed — the panel is resizable). When no host is mounted (sidebar collapsed / isolated test), the canvas falls back to the prior absolute-right overlay. The **feature canvas's always-on read-only subject-service inspector** (D-2026-06-15-O) is **removed** (decision **ⓐ**): an always-on panel would permanently hide the feature palette, so the feature canvas now behaves like every other (palette by default, a node's inspector on select). `FeatureDetailInspectorHost` + the `fallbackInspector` prop are kept (no longer wired from App) for a possible future ⓑ.
- **Why:** User 2026-06-21 — the inspector covered the canvas while the sidebar had empty space; "오른쪽에 나오는 노드 인스펙터를 왼쪽 패널에 … 선택되었을 때 왼쪽 패널을 덮고 선택 해제하면 없어지게" (1-ⓐ), and on the feature-canvas conflict "순서대로 … 일단 갑시다" → ⓐ. Anchors to VISION (canvas-first): the canvas is no longer occluded by the inspector.
- **Alternatives:** lift the inspector state graph to App and render it in the sidebar — rejected (doc/updateNode/publish/available* all live in SketchCanvas; portal moves only the DOM, not the graph). Feature-canvas ⓑ (read-only service as a top context strip) / ⓒ (keep always-on, special-case palette) — deferred; ⓐ chosen for consistency. Programmatic auto-widen of the (16%-default) sidebar when the inspector opens — **follow-up**; the panel is user-resizable via the separator for now.
- **Approval:** Accepted by user, 2026-06-21 ("1. a … 2. a", "일단 갑시다. 1,2,3").
- **Spec impact:** App-repo viewer (`InspectorPanelContext` new; `SketchCanvas` portal/overlay + active flag; `SketchSidebar` host + palette/inspector toggle; `BaseInspector` fills container, width toggle removed; `App` provider + feature fallback unwired). Pinned by `inspector-panel-relocation` (sidebar covers palette on active) + updated `SketchCanvas.regression` (overlay-fallback aside). SketchCanvas LOC ceiling 537→560 (documented). Full viewer suite green (979). **Verify in app:** select a node → inspector fills the sidebar (palette hidden); deselect → palette back; feature canvas no longer shows an always-on right panel.

### D-2026-06-21-P — fix: the engine sidecar orphaned on 5190 (quit didn't reap it; new launch then errored)

- **What:** The Tauri shell now `free_engine_port()`s (kills whatever listens on 127.0.0.1:5190) at two points: (a) in `setup`, BEFORE spawning the sidecar; (b) in `RunEvent::Exit`, AFTER `child.kill()`. Implemented in `plot/src-tauri/src/lib.rs` (best-effort `lsof -ti tcp:5190` → `kill -9`, `#[cfg(unix)]`).
- **Why:** User hit "지금 에러나요" after repeated relaunches: a previous launch's engine still held 5190, so the new launch's sidecar couldn't bind. Two root causes, both now covered: (1) **crash / force-quit** (incl. dev `pkill`) → `RunEvent::Exit` never runs → orphan survives → next launch is blocked; the startup free-port clears it. (2) **PyInstaller onefile**: `CommandChild::kill()` reaps only the bootloader parent; the uvicorn child can survive and keep the port; the on-exit free-port reaps it. The existing `RunEvent::Exit` `child.kill()` was real but insufficient on both counts.
- **Alternatives:** (b) "reuse the already-running engine instead of spawning" (user's idea) — rejected: each launch mints a **per-launch auth token** (`PLOT_AUTH_TOKEN`, D-2026-06-12-F) and the viewer calls with it; an old sidecar enforces the old token → 401. Reuse would require persisting/sharing the token, weakening the one-shot-token model. (c) spawn the sidecar in its own process group and kill the group — more invasive than tauri-plugin-shell exposes; the port-reap achieves the same end portably enough for the macOS bundle. Only the HTTP engine binds 5190, so `--mcp-stdio` agent sessions are never touched.
- **Approval:** Accepted by user, 2026-06-21 ("종료할 때 MCP 도 같이 종료되게 해야하는데" → A안, "순서대로 해요. 1, 2, 3").
- **Spec impact:** App-repo Tauri shell only (`lib.rs`). No viewer/SPEC change. **Verification is manual** (OS process management — no meaningful unit test): quit the app → 5190 frees; relaunch over a deliberately-orphaned sidecar → app binds and loads. `cargo check` green.

### D-2026-06-21-O — fix: the Entities tab rendered blank (getAllCanvases never loaded the entities canvas)

- **What:** `getAllCanvases` (viewer `api.ts`) fetched only foundation / actors / services (+ feature details), omitting **entities**. So `canvasCache` never held the entities canvas → `App`'s `activeCanvas` was null on the Entities tab → the render guard `phase === "ready" && activeCanvas && …` skipped the whole surface (no canvas, no palette drop target, no loading/empty state). Fix: add `["entities", getCanvas(…, "entities")]` to the fetch list. The entities canvas is already seeded server-side on project create (`_seed_entities_canvas`), so this was a pure client load-list omission from when the entities canvas shipped (v0.97.0 / D-2026-06-17-I).
- **Why:** User on a brand-new project: "엔티티 캔버스는 현재 아무것도 없어서 아무런 동작이 안되는거죠? … 왼쪽 팔레트에서 끌어다 놓지 못해요 … 캔버스가 없거든요." Diagnosed as the missing loader entry, not a stencil/drag bug.
- **Alternatives:** (a) render a loading/empty state when `activeCanvas` is null — still worth doing as defense-in-depth (a missing canvas should never be an invisible no-op), filed as a follow-up; the root cause is the load omission, fixed here. (b) lazy-load entities on first tab open — rejected; `getAllCanvases` is the single load SSOT (initial + refresh + snapshot reuse it), so one entry fixes every path.
- **Approval:** Accepted by user, 2026-06-21 (bug report).
- **Spec impact:** App-repo viewer (`api.ts::getAllCanvases`). Pinned by `get-all-canvases` test (map includes entities). Full viewer suite green (977). **Separate open item:** empty-Entities-canvas guidance (the canvas now renders but starts empty; AI auto-surfacing still a follow-up) — pending user choice ⓐ entities-only vs ⓑ all-canvases.

### D-2026-06-21-N — project switcher moves from the sidebar to a tab-bar dropdown (Phase 1 of the panel reorg)

- **What:** The always-expanded project LIST (switch / rename / delete / new) is removed from the left `SketchSidebar` and becomes a dropdown on the tab-bar's centered project name (`ProjectSwitcher`, new `shell/ProjectSwitcher.tsx`, mounted in `CanvasTabs`). Clicking the project name opens the list; the sidebar now holds only the work surfaces (session tags + stencil/palette). The sidebar's "Projects" header is dropped.
- **Why:** User 2026-06-21 — "프로젝트 선택하는 곳은 자주 쓰지 않을 것 같은데 자리를 많이 차지하는 것 같아요." Project switching is once-per-session navigation; it shouldn't hold persistent vertical space. This is **Phase 1** of a two-phase panel reorg; **Phase 2** moves the node inspector into the freed sidebar space (cover-palette-on-select, decided 1-ⓐ / 2-ⓐ this session — not yet built).
- **Alternatives:** (a) collapse the list into an accordion at the top of the sidebar — rejected (user chose the header/tab-bar dropdown, 2-ⓐ). (b) put the switcher in the very top Header row — the project NAME already lives in the tab-bar center (D-2026-05-31-U), so the dropdown lands there to avoid duplicating the name.
- **Approval:** Accepted by user, 2026-06-21 ("2. a 로 합시다").
- **Spec impact:** App-repo viewer (`ProjectSwitcher` new; `CanvasTabs` gains `projects`/`activeProjectId`/`dirForId`/`onPick|Create|Rename|DeleteProject`; `SketchSidebar` drops `projects`/`onPick`/`onCreate`/`onRename`/`onDelete`/`dirForId`; `App` rewires). New i18n `sidebar.switchProject` (en+ko parity). Pinned by `project-switcher` test (renamed from `sidebar-unified-list`); `sidebar-stencil-gating` updated to the trimmed props. Full viewer suite green (976).

### D-2026-06-21-M — Foundation identity stencil drops labelled "Identity", not "Voice"

- **What:** The `identity` stencil preset (`CORE_IDENTITY` in `SketchStencil.tsx`) now drops onto the Foundation canvas labelled **"Identity"** — by its kind name, like its siblings Mission → "Mission" and Core Value → "Core Value". It previously dropped as **"Voice"**, an example aspect from the flat-peers identity model.
- **Why:** User asked "Identity 가 캔버스에 놓일 때 Voice 라고 나오는 특별한 이유?" → the "Voice" default read as confusing (Don't Make Me Think) and was the only Foundation symbol not labelled by its kind. Identity's label is just a name (`specs/kinds-fields.md`: identity `label = 이름`); the aspect (Voice / Energy / Speech style / …) is what the user types into the node, not a baked-in default.
- **Alternatives:** (a) keep "Voice" as a placeholder example — rejected (inconsistent with siblings; the user explicitly wanted "Identity"). (b) empty label + placeholder hint "예: Voice / Energy…" — deferred (larger change; preset labels are plain strings today, no placeholder seam).
- **Approval:** Accepted by user, 2026-06-21 ("Identity 라고 나오면 좋을 것 같은데").
- **Spec impact:** App-repo viewer only (`SketchStencil.tsx` `CORE_IDENTITY.label`). No SPEC line change (identity label is a name per `specs/kinds-fields.md`). Pinned by `stencil-identity-label` test (identity/mission/core_value preset labels = kind name). Full viewer suite green (973).

### D-2026-06-21-L — new-project onboarding polish: folder picker + name prompts + empty-chat surface

- **What:** Five coupled tweaks to the "new project → first conversation" flow (all app-repo viewer):
  1. **No "+ New folder" on a dir that already holds a project.** In `DirTreePickerModal`, the per-row "+ New folder" button is hidden when `node.has_plot` — you don't nest a fresh project inside an existing one (the only action there is "Open").
  2. **Folder name validated inline, before submit.** The new-folder prompt rejects a name that collides with an existing sibling folder *as the user types* (case-folded + trimmed, since macOS FS is case-insensitive), instead of letting them hit create and silently reusing the dir. Backed by a new optional `validate(value) => string | null` on the dialog `prompt` API: `DialogHost` runs it each keystroke, shows the message under the input, and disables Accept while it returns non-null.
  3. **Browser autofill chrome killed on the shared dialog input.** `autoComplete/autoCorrect/autoCapitalize="off"` + `spellCheck={false}` + `data-1p-ignore` / `data-lpignore`. These fields are app identifiers (project / folder / node names), never personal data — autofill suggestions only covered the field.
  4. **Empty chat with no agent → in-body "Connect your AI agent" CTA.** Replaces the misleading "No messages yet" when `activeProvider === null`; clicking opens the same provider register/connect panel the top chip toggles (the chip alone was easy to miss on a brand-new project).
  5. **Empty chat with an agent → per-canvas starter templates.** Once connected with zero messages, the surface shows 3 starter prompts keyed by the conversation scope (foundation / actors / services / entities / feature / project). Clicking one **fills the composer** (does NOT auto-send) so the user can edit before sending.
- **Why:** User requests 2026-06-21 — the new-project flow had foot-guns (nest-a-project, silent dir reuse, autofill overlay) and a dead-end empty chat ("뭘 먼저 말해야 할지 모름"). Anchors to VISION: lower the friction from "empty project" to "collaborating with your own agent on the canvas", per phase.
- **Alternatives:** (a) Enforce unique project *names* — rejected: name is display-only, identity is `id` + path (`project_io.create_project`); duplicate names are allowed by the model. The user explicitly scoped the duplicate fix to **folder names only**, validated pre-submit. (b) Auto-open the provider panel on mount when disconnected — deferred in favour of an explicit in-body CTA (less jarring, more discoverable). (c) Template click auto-sends — rejected: filling the composer keeps the user in control (no surprise turn). (d) A template config system — YAGNI; templates are hardcoded per-kind i18n arrays for now.
- **Approval:** Accepted by user, 2026-06-21 ("전면 진행", "5번은 일단 해보는거죠").
- **Spec impact:** App-repo viewer only (`DirTreePickerModal`, `DialogProvider`/`DialogHost` `validate` API, `ChatDock` `ChatConnectCta` + `ChatStarterTemplates`). New i18n keys `dirPicker.folderExists`, `chat.connectHint`, `chat.starter.*` (en + ko, parity green). Pinned by `dir-tree-picker` (hide + validator), `dialog` (autofill-off + validation gating), and `chat-dock` (connect CTA + per-canvas templates) tests. Full viewer suite green (971). **Follow-up unchanged:** `ChatDock.tsx` is now ~660 LOC — the `ChatComposer` extraction (D-2026-06-21-G/J/K follow-up) is overdue; `ChatConnectCta` / `ChatStarterTemplates` should move with it.

### D-2026-06-21-K — chat scope tabs = canvas-name | project-name, moved above the input; provider/LLM panel no inner scroll

- **What:** Three chat-dock tweaks: (1) the scope switcher's **project tab now shows the project NAME** (e.g. "Banas") instead of the generic word "Project" (the canvas tab already showed the canvas name); a new `projectName` prop threads it from `App` (`activeProjectName`). (2) the **scope switcher moves ABOVE the input box** (its own row inside the composer, just above the textarea) — out of the control row, which now holds only the provider chip + model selector + send. (3) the **provider / LLM register panel no longer scrolls internally** (dropped `max-h-64 overflow-y-auto` → sizes to its content).
- **Why:** User request 2026-06-21 — "캔버스|프로젝트 는 캔버스 이름 | 프로젝트 이름 으로 하고 위치는 채팅 입력창 위로" + "LLM 선택하는거 스크롤 안되게."
- **Note on the "scroll" item:** interpreted as the provider/LLM register panel (the CSS-controllable scroll). The model `<select>` is a native control whose dropdown scroll is OS-managed (not CSS-disableable) — if that was meant, it's a separate change (a custom non-native dropdown). To be confirmed with the user.
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** App-repo viewer (`ChatDock` — `projectName` prop, `scopeBar` above the input, panel no-scroll; `App` passes `projectName`). Pinned by `chat-dock` test (project tab shows the name). Composer-layout + project-name tests green (964 viewer). **Follow-up unchanged:** `ChatDock.tsx` is >500 LOC — extract `ChatComposer`.

### D-2026-06-21-J — chat bubbles render Markdown (assistant replies); user input stays literal

- **What:** Assistant chat replies now render as **Markdown** (reusing the inspector's `MDPreview` — react-markdown + remark-gfm + fenced-mermaid + the same prose styling), so headings / lists / bold / code / tables / links format properly in the bubble. The streaming caret renders after the rendered MD. The **user's own input** and **error text** stay **literal** (plain `whitespace-pre-wrap`) — what the user typed isn't transformed, and the user bubble's inverse background keeps its own text colour.
- **Why:** User request 2026-06-21 ("채팅 버블이 MD 포멧을 지원해주면 참 좋겠네"). Agents reply in Markdown; rendering it makes long structured answers readable instead of a wall of `**` / `#` / `-` characters.
- **Alternatives:** (a) render the user bubble as MD too — rejected (transforms their literal input + clashes with the inverse-bg text colour; VS Code-style keeps user input plain). (b) a chat-specific MD renderer — rejected (DRY: `MDPreview` already does GFM + mermaid + themed prose).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** App-repo viewer (`ChatDock.ChatMessageRow` → `MDPreview` for assistant). Pinned by `chat-md` test (assistant `**bold**`→`<strong>`, lists render, user input stays literal). **Follow-up (SoC):** `ChatDock.tsx` is now 589 LOC — the `ChatComposer` extraction (D-2026-06-21-G follow-up) is overdue.

### D-2026-06-21-I — in-app chat is grounded ONLY in the workspace (no parent/global CLAUDE.md, no auto-memory)

- **What:** The in-app Claude Code agent was pulling context from **outside the workspace** — the parent-directory `CLAUDE.md` files (e.g. the Novel repo's own dev instructions, since a user workspace can live under the Novel tree), the global `~/.claude/CLAUDE.md`, and the user's auto-memory. The `claude -p` spawn now isolates it: command flags **`--setting-sources local`** (load only the workspace's `.claude/settings.local.json` — no user/project scope, so no parent / global CLAUDE.md auto-discovery) + **`--exclude-dynamic-system-prompt-sections`** (keep cwd / env / memory-paths / git-status out of the system prompt), and the spawn env sets **`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`** (fully disables auto-memory). A new `ChatProvider._spawn_env()` hook (default `None` = inherit) threads the env through `stream_turn` → `_spawn` → `_default_spawn`.
- **Why:** User report 2026-06-21 — "워크스페이스 밖의 것들을 보고 있는 것 같은데… 워크스페이스 안의 것들만으로 대화가 되어야합니다." The in-app coach must reason about the user's project (its `.noory/plot` data via the `plot` MCP), not the Novel codebase / the user's global Claude config / saved memories.
- **OAuth + MCP preserved (the key constraint):** this is **NOT** `--bare` (which sets `CLAUDE_CODE_SIMPLE=1` and forces `ANTHROPIC_API_KEY`, breaking the user's subscription). The chosen flags keep OAuth/subscription auth, and the `plot` MCP still loads because it lives in `~/.claude.json` (read independently of `--setting-sources`). Flags verified against `claude --help` 2.1.176 + the permissions/settings docs.
- **Alternatives:** (a) `--bare` — rejected (breaks OAuth). (b) only `--exclude-dynamic-system-prompt-sections` — insufficient (it relocates memory paths but doesn't disable memory, and doesn't stop CLAUDE.md loading). (c) set the env process-wide on the engine — rejected (global side-effect; the per-spawn `_spawn_env` hook is scoped + clean).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** `claude_code._build_command` (+2 flags) + `_spawn_env` + base `ChatProvider._spawn_env` + `_default_spawn`/protocol `env` param. Pinned by `test_chat_session` (spawn argv carries the flags; `spawn_env` carries the memory-disable). **Known limitation (per Claude Code docs):** `--setting-sources local` stops *loading* discovered parent CLAUDE.md but the discovery *walk* itself isn't suppressible without `--bare`; harmless (found files aren't loaded). Codex / Gemini have their own context models — untouched. Engine **659 green**. Needs live `.app` verification (build = AI, visual = user).

### D-2026-06-21-H — initial Foundation layout = Mission top / Core Value left / Identity right, with anchor edges

- **What:** A new project's seeded **Foundation** canvas now arranges its three pillars around the centre project anchor (0,0): **Mission on top** (centred above), **Core Value on the left**, **Identity on the right**, and a directed **edge from the project anchor out to each** (relation `flow`). Previously Core Value was seeded on top and Mission on the left, with no edges.
- **Why:** User request 2026-06-21 ("미션이 위, 코어밸류가 왼쪽, 아이덴티티가 오른쪽 + 연결선도"). A clear, conventional foundation arrangement read top-down (the mission crowns the values + identity), with the connecting lines showing the three are one structure radiating from the project.
- **Note:** The edge seeding **revisits the v0.13.2 auto-edge rollback** (D-2026-05-04-A era) — that was rejected as *unrequested* (YAGNI); it is now *explicitly requested*, so the seed draws them. Edges target the synthetic `PROJECT_ANCHOR_ID`, which `CanvasDoc._edges_reference_nodes` already accepts as a valid endpoint. **Seed-only:** existing projects keep their current Foundation layout (loss-free; this only changes what a *new* project starts with).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** `_seed_foundation_canvas` positions + 3 anchor edges. Pinned by `test_create_project_foundation_layout_and_anchor_edges`. Engine **659 green**. The Foundation canvas stays user-editable (the seed is just the starting point).

### D-2026-06-21-G — chat composer redesign: controls under the input (VS Code-style) + auto-scroll + auto-grow input

- **What:** Three chat-surface UX changes (all `ChatMessageFrame`, one user thread): (1) **controls move from a top bar into a control row directly under the composer input** (VS Code / Pencil pattern, user-chosen "VS Code-style") — provider chip, model selector, scope toggle on the left + send on the right; the messages log fills the freed top space; the providers register/connect panel expands just above the composer when the provider chip is toggled; `ChatScopeSwitcher` gains a `compact` inline variant. (2) **auto-scroll** — the log follows the conversation (new message / streaming delta scrolls to bottom) **only when the user is already near the bottom** (`chatScroll.isNearBottom`, 80px), so reading history isn't yanked down. (3) **auto-grow input** — the textarea grows with its content up to the `max-h-40` cap and shrinks back when cleared.
- **Why:** User request 2026-06-21 — "컨트롤이 채팅 입력창 근처에 몰려 있어야하지 않겠습니까?" (controls should cluster near the input). Don't-Make-Me-Think + Visual Hierarchy: the controls that shape a message belong next to where you type it, not in a separate bar at the far end. The user picked the VS Code-style (control row under the box) over the Pencil-style (controls inside the box) via an AskUserQuestion mockup.
- **Alternatives:** (a) Pencil-style (controls inside the rounded input card) — offered, user chose VS Code-style. (b) keep the top bar — rejected (the user's whole point).
- **Approval:** Accepted by user, 2026-06-21 (AskUserQuestion → "VS Code식 — 입력박스 아래 별도 줄").
- **Spec impact:** App-repo viewer only (`ChatDock.tsx`). Behaviour preserved (provider connect / model select / scope / send / stream all unchanged) — pure layout. Pinned by `chat-dock` test (the messages `role="log"` now precedes the scope tablist + input in DOM order). **Follow-up (SoC):** `ChatDock.tsx` is 546 LOC (>500); extract a `ChatComposer` component (the composer + control row) — tracked, not blocking.

### D-2026-06-21-F — engine sidecar tag convention = `mashbill-v{version}` on `noory-ai`, pushed at build

- **What:** The git-tag that pins a built sidecar (the Phase-D-b reproducible build, `D-2026-06-20-Q` / `build_sidecar.py --engine-tag`) is named **`mashbill-v{__version__}`** on the **`noory-ai`** repo (the engine's home). Tags are **pushed to `origin`** (outward-facing — they're public on `github.com/noory-code/noory-ai`). First pushed: `mashbill-v0.98.6`, `mashbill-v0.98.8` (2026-06-21).
- **Why:** `noory-ai` is a monorepo (evonest / distill / solera / plot / …), so an engine release tag needs a **package prefix** to disambiguate — hence `mashbill-` (the package name) + `v{semver}`. The version is the single-source engine version (`mashbill/__init__.__version__`, `D-2026-06-20-N`). The build script verifies HEAD is exactly the tag before building, so the bundled binary corresponds 1:1 to a public, reproducible commit.
- **Approval:** Accepted by user, 2026-06-21 ("푸시 하세요" — confirmed pushing the held tags + the `mashbill-v{version}` convention).
- **Spec impact:** Release process — each sidecar build tags `noory-ai` `mashbill-v{version}` and pushes it. `noory-workspace/CLAUDE.md` §빌드 파이프라인 already references `--engine-tag mashbill-v<ver>`; the "⚠ 태그 push 는 사용자 확인 후" note now has a standing yes for this convention (the *act* of pushing a specific release can still be a judgement call, but the naming + push-to-origin policy is settled).

### D-2026-06-21-E — default canvas focus = Foundation; a returning project resumes its last-worked canvas

- **What:** On open, the app focuses the **Foundation** tab by default (was **Services** — `readInitialTab` fallback). If the user has worked a project before, it reopens on the **canvas they last had active**. "Last worked" = the last active tab, persisted **per project** in `localStorage` (`plot:lastCanvas:<projectId>`), restored once the project id is known (`useLastCanvas`). An explicit `?canvas=` deep-link still wins (it sets the initial tab before the resume runs).
- **Why:** User request, 2026-06-21 — the standalone `.app` (URL = `tauri://localhost`, no `?canvas`) always landed on Services; the user wanted Foundation by default (start at the essence, VISION) and a resume-where-I-left-off for returning projects.
- **Design:** last-active-tab (focus), not last-*edited* — the intuitive "reopen where I was". Stored in `localStorage` (machine-local UI state, survives app restarts in the WKWebView data store), not in the project doc — it's a per-machine view preference, not portable project data (no wire/schema change). Fresh project (nothing stored) → Foundation.
- **Alternatives:** (a) derive from canvas-file mtimes server-side — rejected (fresh-project mtimes are ambiguous; needs a content/creation heuristic; localStorage is unambiguous and zero-engine-change). (b) persist `last_active_canvas` in the ProjectDoc (travels across machines) — rejected for now (wire/schema churn + an extra write per tab switch; "which tab I last viewed" is machine-local UI state). (c) resume on last-*edited* (server-stamp on canvas PUT) — rejected (the user said "작업했던 곳" = where I was; last-active is the intuitive resume).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** App-repo viewer only. `useUrlSync.readInitialTab` default `services`→`foundation`; new `useLastCanvas` hook (persist on tab change / resume once per project); App wires it (one import + one call). Pinned by `use-last-canvas.test` (7 cases) + `structural-guards` App ceiling 510→512 (plumbing-only). No engine change.

### D-2026-06-21-D — the in-app Claude Code dual-billing warning banner is removed

- **What:** The `ChatDock` banner shown for a `claude-code` selection ("Claude Code runs headless (claude -p), billed separately… connect over MCP instead.") is **removed** — the JSX block + the `chat.claudeBillingWarning` i18n keys (en + ko). Supersedes the warning added by `D-2026-06-14-B`.
- **Why:** User request, 2026-06-21 ("이거 없애죠"). The banner was noisy on every claude-code turn.
- **Note (fact still holds):** in-app `claude -p` IS billed per-token (API), separate from a Claude subscription — that cost reality is unchanged; it is simply no longer surfaced as a persistent banner. The MCP-first path (the user's own agent over `mcp__plot`) remains the no-double-charge route.
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** App-repo UI only (`plot/viewer/src/shell/ChatDock.tsx` + i18n). `chat-dock` test updated: a claude-code selection now enables input with **no** `role="note"` warning. No engine change.

### D-2026-06-21-C — in-app Claude Code auto-allows the user's own mashbill MCP tools (`--allowedTools mcp__plot__*`)

- **What:** The engine's `claude -p` spawn (`claude_code._build_command`) now passes **`--allowedTools mcp__plot__*`**. Headless `-p` cannot show an interactive permission prompt, so when the in-app agent called a mashbill MCP tool (`mcp__plot__list_projects`, …) the call dead-ended and the model narrated "press Allow" with nothing to press. The flag auto-approves **all mashbill MCP tools** so the in-app coach actually works.
- **Why:** User report 2026-06-21 (the agent kept telling the user to approve a prompt that can't appear in headless mode; "이런건 처리가 되어야죠… 알아서 되던"). The exact flag was verified against `claude --help` (2.1.176) + the permissions docs (an MCP allow-rule must be anchored: `mcp__plot__*`, not bare `mcp__plot`).
- **Scope / safety:** Auto-allow is **scoped to `mcp__plot__*` only** — Bash / Write / Read / filesystem keep their default behaviour, so the in-app agent **cannot silently touch anything outside the user's `.noory/plot` data**. Novel tools operate only on that data, which is git-recoverable and surfaced on the canvas (build-through-discussion, PHILOSOPHY rule 7), so auto-approving them — including mutating ones — is consistent with Novel's "AI proposes, user sees it on the canvas" model. The meaningful boundary (no silent filesystem/shell access) is preserved.
- **Alternatives:** (a) `--dangerously-skip-permissions` / `--permission-mode bypassPermissions` — rejected (auto-allows Bash/Write to the whole machine; defeats the boundary). (b) enumerate only read Novel tools — rejected (brittle vs the tool list; the coach also edits canvases, and Novel mutations are reviewable + recoverable). (c) a setup/permission UI in the chat — deferred (the user's primary ask was "알아서 되던" / just-work; the scoped auto-allow delivers that with no new UI).
- **Approval:** Accepted by user, 2026-06-21.
- **Spec impact:** In-app chat (claude-code) now invokes mashbill MCP tools without a dead-end prompt. Pinned by `test_chat_session` (the spawn command carries `--allowedTools mcp__plot__*`). Codex / Gemini providers have their own permission models — not touched (separate, if reported). Engine **658 green**.

### D-2026-06-21-B — in-app Claude Code chat doubled every reply; the `stream-json` parser counted text twice

- **What:** The in-app chat (claude-code provider) rendered each reply **doubled** ("바나스 파운데이션 캔버스를 살펴볼게요.바나스 파운데이션 캔버스를 살펴볼게요."). Cause: `claude_code._extract_anthropic_text` pulled text from **two** frame shapes — the partial `content_block_delta` stream AND the full `assistant` recap message. With `--include-partial-messages` (always on) **both** arrive for the same block, so the engine's accumulator (and each viewer delta) counted the text twice. Fix: the partials are the single streaming source; the full `assistant` recap is **ignored** for text. Now an `assistant` message yields no delta and the accumulated turn text equals the produced text exactly once.
- **Why:** Pre-partials, the `assistant` message was the only text frame, so the parser read it. When `--include-partial-messages` was added, the partials became the live stream and the `assistant` message became a redundant recap — but the parser kept reading both, doubling every reply. (The viewer reducer was correct; the engine was double-emitting.)
- **Alternatives:** (a) dedupe in the viewer reducer — rejected (treats the symptom; the engine is the wire SSOT and `turn_complete` reconciles to the engine's accumulator, which was itself doubled). (b) drop `--include-partial-messages` and keep the `assistant` message as the source — rejected (loses incremental streaming; the dock would show text only at block end).
- **Approval:** Bug fix per user report 2026-06-21 ("이거 이상한데요?").
- **Spec impact:** No behavioural spec change — a streaming-correctness fix. Pinned by `tests/test_claude_stream_parse.py` (partials + recap → text once) + updated `test_chat_session` fixtures (the old test that asserted assistant-message extraction encoded the bug; now asserts the recap is ignored). Engine **658 green**.

### D-2026-06-21-A — standalone `.app` ATS exception (`NSAllowsLocalNetworking`) so the WKWebView reaches the loopback engine

- **What:** The bundled `Novel.app`'s viewer showed **"Load failed"** on every engine request. Root cause (evidence-based, alternatives eliminated — engine healthy via curl, CORS correct incl. on 401, CSP `null`, frontend embedded, sidecar spawned): the **bundle `Info.plist` carried no `NSAppTransportSecurity` key**, so default App Transport Security blocked the viewer (a `tauri://` secure origin) from fetching the engine over **cleartext `http://127.0.0.1:5190`** — WebKit rejects the fetch at the network layer (`TypeError: Load failed`, not an HTTP status). Fix: a committed `plot/src-tauri/Info.plist` (Tauri v2 merges it at bundle time) with `NSAppTransportSecurity → NSAllowsLocalNetworking = true` — re-permits **loopback / local** cleartext only, **not** arbitrary public cleartext (`NSAllowsArbitraryLoads` rejected as too broad). Verified: rebuilt `.app` → Info.plist carries the key → relaunch → **user confirmed the viewer loads ("제대로 떴네요")**.
- **Why it was latent:** every prior `.app` verification used `tauri dev` (the viewer served from an `http://localhost:5193` origin + a same-origin Vite proxy to `/api`), so requests were same-origin http→http and never triggered ATS. The **standalone bundle's** webview→cleartext-engine path (absolute `http://127.0.0.1:5190`, baked via `VITE_PLOT_ENGINE`) was never exercised end-to-end until now — the first real standalone-bundle run surfaced it.
- **Alternatives:** (a) `NSAllowsArbitraryLoads = true` — rejected (opens all public cleartext; the exception must be scoped to loopback). (b) serve the sidecar over HTTPS — rejected (self-signed-cert hassle for a loopback backend). (c) route fetches through the Tauri HTTP plugin (Rust-proxied, bypasses webview ATS) — rejected for now (rewrites `api.ts`'s fetch/WS seam; the ATS exception is the minimal correct fix). (d) switch `127.0.0.1` → `localhost` — not needed (`NSAllowsLocalNetworking` covers loopback IPs); kept on file as a fallback if a future macOS tightens raw-IP handling.
- **Approval:** Accepted by user, 2026-06-21 ("제대로 떴네요" after the ATS-fixed rebuild).
- **Spec impact:** App-repo build config only — **no engine change** (engine version stays `0.98.6`; per D-2026-06-20-N the version must not move when the engine didn't). Fix lives in `plot/src-tauri/Info.plist`. Known follow-up: a real standalone-bundle smoke gate (the dev-only path masked this for the whole project's life).

### D-2026-06-20-Q — feature→entity reference = `ref_entity_ids` chips on the `step` (action) node; purpose = AI-maintained derived data map, not flow visualization

- **What:** Unblocks the entity follow-ups (`D-2026-06-17-K` step 6/7; `D-2026-06-20-K` deferred them "no data source until feature→entity refs exist"). A **feature action references the entities it operates on** via `ref_entity_ids: list[str]` — an id-array **chip picker on the `step` node** (the action), picking from the `entities` registry, mirroring the service inspector's `ref_actor_ids` / `ref_value_ids` chips (`D-2026-06-20-F`) and reusing `RefChips.tsx` + a new `availableEntities` source in `useAvailableNodes`. The entity inspector's **"어디서 쓰이나" back-reference** (step 6) is **derived read-only** by scanning every feature canvas's `step` nodes for the entity id (the reverse index the plan flagged as missing). Edges (step 7) stay separate (entity↔entity rough relationships on the entities canvas).
- **Why (purpose-anchored — user's call, 2026-06-20):** The reference's purpose is the **AI-maintained derived data map** — letting the user see *what data the product has and where each is used*, as a byproduct of feature design, **without ERD work** (`D-2026-06-17-I`: entities are AI-maintained, populated last). It is **NOT** for visualizing data plumbing in the flow (that is below action-altitude — the external coding agent's job, `D-2026-06-17-G`). Because the reference is a lightweight AI-written *declaration* on the action (not a flow participant), it lives as a **chip on the action**, not as a placed `entity_ref` node — keeping the feature flow about *actor behaviour*, and yielding the back-ref for free (scan `step.ref_entity_ids`). This follows the recent "chips beat ref-nodes for derived/declared references" direction (`D-2026-06-20-G`).
- **Alternatives:** (a) `entity_ref` **node** on the feature canvas (mirrors `actor_ref`) — rejected: a node renders the entity as a *flow participant* (purpose 2, data-flow visualization), which contradicts the AI-maintained-byproduct purpose and clutters the behaviour flow. (b) a cross-canvas **edge** action→entity — rejected: Novel cross-canvas references use id-matching, not edges; an edge would also read as flow-visualization. (c) put `ref_entity_ids` on the `feature` node, not `step` — rejected: the *action* (step) is what touches data; feature-level would lose which action uses what (and weaken the back-ref granularity).
- **Approval:** Accepted by user, 2026-06-20 (purpose-1 confirmed: "그렇게 가보죠" after agreeing the reference exists for the derived data-map + 어디서-쓰이나, not flow visualization).
- **Spec impact:** New additive wire field `step.ref_entity_ids` (loss-free default `[]`); palette/canvas counts unchanged. `entity` inspector gains the read-only "어디서 쓰이나" derived view. Root `docs/plans/ENTITIES_PLAN.md` step 6 unblocked; `docs/specs/kinds-fields.md` (step fields) + `docs/specs/edges.md` (entity edges, step 7). Cross-repo lock-step: engine field + codegen regen (the wire half) then viewer domain/inspector/back-ref. Guards: schema-parity / wire-contract auto-bump; new step-inspector + back-ref + entity-edge tests.

### D-2026-06-20-P — Context layer "find" side: graph traversal + entry-point resolution + title/id index (vector deferred); headroom rejected

- **What:** Completes the context layer's *retrieval* ("find") half — the complement to `D-2026-06-17-L`'s *delivery* ("envelope" + CAG/RAG) half. (1) **Retrieval = graph traversal.** A Novel project's data *is* a graph (canvases / nodes / edges / actor_ref), so the agent locates context by following edges from a foothold — **no vector DB is needed** for the primary case (connection beats similarity; the user drew the edges deliberately). (2) **Entry-point resolution order = selection → map → name → (last resort) semantic search.** Novel is a canvas app, so the current selection/scope is usually the foothold for free; whole-project questions start from the overview/map; named targets resolve via a lookup; only vague-with-no-anchor queries need similarity. The in-app path is selection-rich; the external-agent path (no canvas selection) leans on map + name. (3) **Build early: a title/id index** for name lookup — a lightweight index, **not** a vector store. (4) **Vector / RAG-for-find = deferred behind the same context-provider seam** (`D-2026-06-17-L`) — earned only by blind no-anchor search or by text that escapes the graph. (5) **headroom (token-saving LLM proxy) = rejected for Novel** — measured ~0.1% net savings on real Claude Code transcripts because Novel's AI is Claude Code, which already uses Anthropic prompt-cache; the headline 50–90% comes from provider prompt-cache reuse Claude Code already exploits.
- **Why:** Session discussion 2026-06-20. `D-2026-06-17-L` settled what the AI *sees* and how it is *delivered*, but not how the layer *finds* the right slice as a user's project grows large. Graph-native retrieval keeps the layer **concept-independent** (it does not depend on which kinds/canvases exist), so it is safe to record now while the concept/structure rework runs in another session.
- **Alternatives:** (a) vector DB / RAG from the start — rejected (YAGNI; data is already a graph, traversal covers the primary case; vector slots behind the seam later). (b) treat main-vs-secondary AI path as decisive for retrieval — rejected (both paths are the same `claude` binary on the same `.noory` data; what differs is who configures it). (c) adopt headroom for token savings — rejected (measured ~0.1% net for Novel).
- **Open:** **Connectedness invariant** — every new artifact (work-item / design file / Solera / Evonest output) must enter the graph *with an edge to what it implements*; floating unlinked text is what would eventually force vector. Needs a pinned decision + confirmation against Solera/Evonest's actual data shape. Tracked in ROADMAP 5.11.
- **Approval:** Accepted by user, 2026-06-20.
- **Spec impact:** Consolidated into `docs/concepts/ai-collaboration.md` §1.2 (adds the "찾기" paragraph beside the existing "전달" envelope). Refines Track 5.4 (graph-RAG-lite → deferred behind the seam) and ROADMAP 5.11. No code yet.

### D-2026-06-20-O — runtime wire-compat: `/api/health` exposes `schema_version`; the app warns on mismatch (Phase D part c)

- **What:** Closes the open-core safety gap that a **stale `.app`** (frontend built against one wire schema, bundled sidecar engine built against another — e.g. after a kind change rebuilt only one half) would silently corrupt reads. The engine's `/api/health` now returns `schema_version` (the wire-contract `SCHEMA_VERSION`, `2`) + `engine_version` (the package `__version__`) alongside the existing `status`/`service` (backward-compatible additive fields). The viewer, at boot, fetches `/api/health` and compares the engine's `schema_version` against its **own committed** `wire-contract.json` `schema_version` (`src/app/compat.checkEngineCompat`); on mismatch it shows a full-width danger banner (`src/shell/CompatBanner`, self-probing via `useEngineCompat`) naming both versions and telling the user to rebuild the sidecar / update the app. **Engine-unreachable does NOT fire the banner** (engine-down is surfaced by the normal error UI — the compat banner is only for a *reachable* engine whose schema disagrees). An older engine that omits the field is treated as a mismatch (cannot prove compatibility → warn).
- **Why:** The viewer and engine version independently in separate repos (`D-2026-06-20-A`/`-L`); the only contract is the wire `schema_version`. Without a boot check, a version-skewed `.app` reads canvases against the wrong schema and silently mis-parses. A one-fetch boot comparison turns a silent corruption into a loud, actionable banner.
- **Alternatives:** (a) compare full `wire_contract` payloads, not just `schema_version` — rejected (the `schema_version` int is the designed compatibility token; field-level drift is caught at regen/CI time, `D-2026-06-20-M`). (b) block the whole app on mismatch — rejected (a banner that still lets the user read is less destructive than a hard lock; the user may just need to rebuild). (c) fire on engine-unreachable too — rejected (conflates two conditions; engine-down has its own UI).
- **Approval:** Executes the user-approved Phase D part (c) ("런타임 schema_version compat 배너", 2026-06-20 autonomous directive).
- **Spec impact:** New behaviour — `/api/health` carries `schema_version` + `engine_version`; the app shows a wire-compat banner on boot mismatch. Engine **648 green** (+`test_health_exposes_compat_versions`); viewer **939 green** (+`compat` / `compat-banner`, i18n `shell.compat.*` en+ko). `specs/` (engine health / app boot) — code-near behaviour, logged here. Phase D part (b) sidecar git-tag pin + `engine_version` build stamp remains.

### D-2026-06-20-N — engine version single-source (`mashbill/__init__.py`); `SCHEMA_VERSION` stays separate (Phase D part a)

- **What:** Collapses the four stale copies of the engine version (`pyproject.toml` `0.1.0` / `mashbill/__init__.py` `0.1.0` / `schema_export.PLOT_VERSION` `0.14.18` / `.claude-plugin/plugin.json` — the only one that moved) to a **single source = `mashbill/__init__.py::__version__`**. `pyproject.toml` derives it dynamically via hatchling (`dynamic = ["version"]` + `[tool.hatch.version] path = "mashbill/__init__.py"`); `schema_export.PLOT_VERSION` re-exports `__version__` (it only feeds the informational `_meta.json plot_version`, no viewer consumer); the Claude Code `plugin.json` manifest is a **separate artifact** pinned **equal** by `tests/test_version_parity.py`. Gate 4 now bumps `__init__.__version__` **+** `plugin.json` in lock-step (two files; pyproject auto-follows). The current true version `0.98.x` is adopted. **`SCHEMA_VERSION` (wire-contract schema version, `2`) is intentionally NOT unified** with the package version — it is a different concept (the thing the Phase-D runtime compat banner gates on, parts b/c) and is pinned decoupled by the same test.
- **Why:** Four drifting copies meant `_meta.json` stamped `0.14.18` while the plugin shipped `0.98.x` — a silent lie about what engine is running, and a blocker for the Phase-D sidecar `engine_version` stamp + runtime compat. One source removes the drift; deriving (hatchling dynamic + `PLOT_VERSION` re-export) means future bumps touch one real line. `SCHEMA_VERSION` must stay separate: the wire schema changes on its own cadence (a kind-field change bumps it; a package patch does not), and conflating them would force a schema-version bump on every release.
- **Alternatives:** (a) `pyproject` static version as SSOT + `importlib.metadata` at runtime — rejected (an editable checkout that forgot to re-sync returns a stale installed version; a literal in `__init__` is unambiguous and import-only). (b) `plugin.json` as SSOT — rejected (it is a Claude-Code-specific manifest, not the Python package's identity; the package owns its version, the manifest mirrors it). (c) merge `SCHEMA_VERSION` into the package version — rejected (different cadence; MECE violation).
- **Approval:** Executes the user-approved Phase D ("#3 엔진 버전화", 2026-06-20 autonomous directive). SSOT-file choice is the implementation mechanic.
- **Spec impact:** No behaviour change; engine **647 green** (+`test_version_parity`). `_meta.json plot_version` now reflects the real version. Phase D parts (b) sidecar git-tag pin + `engine_version` stamp and (c) runtime `schema_version` compat banner build on this. `ROADMAP.md` Track 2 Phase D.

### D-2026-06-20-M — the irreversible cut: `noory-ai/plot/viewer` removed; codegen viewer-write is env-only (`PLOT_VIEWER_ROOT`)

- **What:** Executes the irreversible half of `D-2026-06-20-L` (the Phase-C cut). The 295 tracked `noory-ai/plot/viewer` files are **removed** (`git rm -r`) — the viewer now lives only in the proprietary app repo `plot/`. The engine codegen no longer hardcodes the app's path: both `ts_codegen.write_wire_ts` and `schema_export._write_wire_snapshots` resolve the viewer write-target **only** from the `PLOT_VIEWER_ROOT` env var (new `ts_codegen.wire_ts_path()` / `schema_export.viewer_contract_path()`, each returning `None` when unset). Unset → the viewer artifact is not this repo's concern and the write is a clean no-op; the engine still always writes its own `mashbill/wire_contract.json` self-copy. The dev cross-repo regen is `PLOT_VIEWER_ROOT=/abs/path/to/plot/viewer uv run python -m mashbill.ts_codegen` (+ `... schema_export --wire`) — verified idempotent against the committed `plot/viewer` artifacts. The four **viewer-reading parity tests** that silently die once the viewer leaves the repo are re-homed: `test_ts_codegen` (committed-file freshness → app vitest; engine keeps a deterministic per-kind interface guard), `test_wire_contract::test_monorepo_copies_are_identical` (retired; engine keeps its self-copy guard), `test_chat_scope_parity::test_chat_scope_parity` (→ app vitest; engine keeps the explicit member-set pin), `test_edge_semantics::test_relation_value_set_matches_viewer` (→ app vitest; engine keeps an explicit `{flow, injection, inheritance}` pin). `find_viewer_dist()` already returns `None` gracefully (headless mode, `test_transport_isolation`) — no change needed.
- **Why:** `D-2026-06-20-L` open-core (`D-2026-06-20-A`): the visual canvas = paid app value (proprietary `plot/`), the engine = MIT headless (`noory-ai`). A MIT engine must not hardcode the proprietary app's filesystem path — env-only keeps the engine standalone (an engine-alone checkout regenerates only its self-copy) while the cross-repo awareness lives in the documented dev command, not in engine source. The four parity tests read viewer TS from disk, so they die the moment the viewer leaves — each is replaced by an engine-side pin (the app's vitest owns the viewer half against the committed artifacts).
- **Alternatives:** (a) sibling-default path resolution (`../../plot/viewer`) in the engine module — rejected (names the proprietary app inside MIT engine source; env-only is cleaner and an engine-alone checkout stays a no-op). (b) repoint the parity tests cross-repo to `plot/viewer` — rejected (assumes the sibling layout in a noory-ai-alone CI; the viewer half belongs in the app's CI per `D-L`). (c) delete `find_viewer_dist` viewer-serving — deferred (already returns `None` headless; removing it is a separate cleanup, not part of the cut).
- **Approval:** Executes the user-approved `D-2026-06-20-L` (the cut + Phase-D were named there as the immediate follow-up) under the user's autonomous "#2 컷 우선" directive (2026-06-20).
- **Spec impact:** Cross-repo lock-step is now live — the viewer half is regenerated by the dev command + committed in `plot/`. No behaviour change (pure structural migration); engine **643 green** after the cut (was 638 + the new `test_codegen_target` set − the retired viewer reads). `ROADMAP.md` Track 2 / ARCHITECTURE §마이그레이션: Phase-C cut **done**; Phase D (engine version unification + sidecar git-tag pin + runtime `schema_version` compat banner) is next.

### D-2026-06-20-L — viewer physical migration `noory-ai/plot/viewer` → `plot/viewer` (open-core; codegen = committed artifacts; engine pin = git-tag)

- **What:** The viewer moves out of the open-source `noory-ai` monorepo into the proprietary app repo `plot/` — implementing the open-core boundary (`D-2026-06-20-A`: visual canvas = app-exclusive / engine = MIT headless). Prereqs done earlier this overhaul: types.ts → `schema_export` codegen (Phase A — so schema parity survives the repo split, TECH_REVIEW step 1) and `mashbill` headless dual-mode (Phase B). **Approach (user-gated 2026-06-20):** (1) **codegen = committed artifacts** — `wire.gen.ts` + both `wire_contract.json` are checked into the `plot` repo; a dev regen script (aware of both repo paths) refreshes them when the engine schema changes, and the drift guard runs in `plot`'s CI against the committed artifact (vs. the prior monorepo regex parity, which dies the moment viewer leaves `noory-ai`). (2) **engine pin = git-tag** — the sidecar PyInstaller build installs `mashbill` from an explicit git-tag ref (simplest at the monorepo-adjacent stage; the build manifest stamps `engine_version`); published-wheel rejected as overkill now.
- **Staged execution (to avoid a broken cross-repo state):** **Phase C-additive (this step):** the 295 tracked viewer files are copied into `plot/viewer`, `plot/src-tauri/tauri.conf.json` + `tauri.debug.conf.json` `frontendDist` repointed `../../noory-ai/plot/viewer/dist` → `../viewer/dist`, `mashbill/.gitignore` + a proprietary `LICENSE` placeholder added — verified `npm ci` + `tsc` + **928 vitest green** in the new home. `noory-ai/plot/viewer` is still present and green, so nothing is broken. **Remaining (the irreversible cut + Phase D):** remove `noory-ai/plot/viewer`; repoint `ts_codegen.py` / `schema_export.py --wire` output to the committed `plot/viewer` artifacts; adjust the now-cross-repo drift guards; R8 import guard in `plot`; align engine versions (`pyproject` `0.1.0` / `PLOT_VERSION` `0.14.18` stale / `plugin.json` `0.97.0`) to one source; sidecar git-tag pin + runtime `schema_version` compat banner.
- **Why:** `D-2026-06-20-A` open-core. The viewer is the visual canvas (paid app value); the engine is the MIT headless plugin. They must live in separate repos with the wire contract surviving the split via committed codegen artifacts.
- **Alternatives:** (a) configurable codegen output path invoked by the app build — rejected (needs engine source at app-build time; committed artifacts are simpler + keep the drift guard in the app repo). (b) published-wheel engine pin — rejected (PyPI/internal-index overhead; git-tag suffices at this stage). (c) rename the on-disk `services/` storage folder — N/A (separate concern; not part of the move).
- **Approval:** Accepted by user, 2026-06-20 (chose checkpoint ① migration + confirmed codegen = committed-artifacts, pin = git-tag).
- **Spec impact:** Cross-repo lock-step begins (each later kind change = paired engine/app commit; codegen automates the wire half). `ROADMAP.md` Track 2 / ARCHITECTURE §마이그레이션. Phase-C-additive landed; the cut + Phase D are the immediate follow-up.

### D-2026-06-20-K — `entity` kind + `entities` canvas landed (kind + canvas + lean inspector; AI-surfacing / edges / back-ref deferred)

- **What:** Implements `D-2026-06-17-I` (entity kind + Entities canvas) at the lean scope settled by `D-2026-06-17-K`. **New kind `entity`** — `EntityNode(BaseNodeFields)` with exactly one kind-specific field `summary: str` (the "무엇을 담나?" one-liner; `label` is the entity name). **NO** ERD fields (FK / cardinality / field-types — below altitude) and **NO** relationship fields (relationships are edges, separate). Full lock-step: Pydantic model (`models_entity.py`), `models_union` + `models.py` + `schema_export._ALL_KIND_CLASSES`, viewer `domain/Entity.ts` (consumes generated `EntityJson` from `wire.gen.ts`), node renderer (`rounded`, pale-cyan `#cffafe` — unused elsewhere, `database` icon), lean inspector (`label` + `summary`, both writable), registries, codegen regenerated, i18n, structural-guards. **Palette = 14 kinds.** **New canvas `entities`** — `CanvasKind += "entities"`; `_ALLOWED_KINDS_BY_CANVAS["entities"] = {"project", "entity"}`; seeded EMPTY (entities are AI-derived / populated last, never hand-authored at create time); anchor seeded; no structural validator (YAGNI, mirrors `services`); 4th main tab (`foundation, actors, services, entities`); `ChatScope` / `CanvasKey` / scope-parity (Python ↔ TS) + the HTTP / broadcast / publish-load / snapshot singleton sites all extended. **Canvas kinds = 5.**
- **Scope boundary (deferred follow-ups, per the agreed scope):** the AI-surfacing **in-chat proposal UI** (only the `SCOPE_FRAMING["entities"]` string + scope wiring landed, not the proposal flow); **feature-action → entity references** (blocked on FEATURE-canvas work); **entity↔entity relationship edges** (B1); the read-only **"어디서 쓰이나" back-reference** + **"거친 관계"** inspector views (`D-2026-06-17-K` B3/B5 step 6 — no data source until feature→entity refs exist). The inspector is 2 writable fields for now.
- **Why:** `D-2026-06-17-I` — entities are the **product data objects the services act on** (글 / 댓글 / 결제내역 …), an AI-maintained registry surfaced as a byproduct of feature design, populated last. The lean 2-field node (name + rough "what it holds") matches the settled conceptual-not-ERD model (`D-2026-06-17-K` B5). User confirmed this implementation scope 2026-06-20 ("kind+캔버스+lean 인스펙터만").
- **Alternatives:** (a) ERD-style entity with typed fields / FKs — rejected (below altitude; the external coding agent owns the schema). (b) ship the back-ref / AI-surfacing views now — rejected (no data source yet; blocked on feature→entity refs). (c) `kind.entity.{label,description}` nested i18n per the generic skill template — rejected for the repo's actual flat `kind.{kind}` convention (a nested object would break the stencil's `t("kind.entity")` resolver; `description` has no consumer → YAGNI).
- **Approval:** Accepted by user, 2026-06-20 (scope confirmed: kind + canvas + lean inspector; AI-surfacing deferred — the design itself was pre-approved in `D-2026-06-17-I` / `D-2026-06-17-K`).
- **Spec impact:** Palette 13 → **14** (`+entity`); canvas kinds 4 → **5** (`+entities`). Root design SSOT (`concepts/`, `specs/`) already describe the entity kind + Entities canvas. Guards bumped: `test_schema_parity` / `test_wire_contract` (14), `test_chat_scope_parity` (+entities), viewer `structural-guards` (KIND_DIRS + count + `EntitiesCanvas` LOC), `entity-roundtrip` / `no-god-import` / `nodes/registry` (+entity). Codegen (`wire.gen.ts` + both `wire_contract.json`) regenerated, idempotent.

### D-2026-06-20-J — Wire-string rename `service_detail` → `feature` completed (the interim string from D-I is gone)

- **What:** The detail canvas's wire string is renamed everywhere: the persisted **`canvas_kind` value** `service_detail`→`feature` (Python `CanvasKind` Literal + TS `CanvasKind`); the **runtime / scope key** prefix `service_detail:`→`feature:` (cache keys, `ChatScope`, `CanvasKey` — Python ↔ TS parity green); the **CanvasDoc field** `service_ref`→`feature_ref`; the helper `list_service_details`→`list_feature_details`; the viewer state `detailServiceId`→`detailFeatureId` / `drillIntoService`→`drillIntoFeature`; the i18n keys `serviceDetail`→`featureDetail` + `canvas.tabs.service_detail`→`canvas.tabs.feature` (en + ko symmetric); and the four `ServiceDetail*` components → `FeatureDetail*` (files `git mv`-renamed). Kebab prose comments swept too. `_ALLOWED_KINDS_BY_CANVAS["feature"]` correctly holds the `feature` root node kind (canvas-kind and node-kind are different fields — no collision). **112+ files, zero leftover tokens** (snake / camel / Pascal / kebab all verified clean).
- **Kept (not renamed):** the on-disk storage path `services/{id}/detail.json` (the `services/` folder is the services-area; the detail nests by id — the path never contained the `service_detail` string, so it needs no change and no data migration); the `?detail=` URL param (already generic); the `service` node kind / `services` overview canvas / `ServiceNode` / `ServicesCanvas`.
- **Why:** Supersedes the "wire string kept (interim)" decision in `D-2026-06-20-I`. The interim left `service_ref` / `service_detail:` carrying *feature* ids — misleading. With the drill rewire shipped (v0.95.0) and **no projects using Novel yet** (zero data-migration risk), the user gated the full rename (2026-06-20, "wire-string rename 마저"). One coherent rename beats a permanent misnomer.
- **Alternatives:** (a) keep the `service_detail` wire string permanently — rejected (misnomer; the canvas is a feature's detail). (b) also rename the storage folder `services/`→`features/` — rejected (the folder holds the services overview *and* the per-feature details nested under it; splitting them out is a structural change with no payoff, and the path carries no `service_detail` string).
- **Approval:** Accepted by user, 2026-06-20 (explicit "wire-string rename 마저" gate, lifting the product-gate noted in `D-I`).
- **Spec impact:** Canvas-kind enum value is now `feature` (root design SSOT `specs/canvas-behavior.md` describes the feature canvas). No behavioural change vs v0.95.0 — pure rename; engine 635 + viewer 914 + parity/schema/wire guards all green.

### D-2026-06-20-I — Drill rewire implemented: `feature` is the drill target, the detail canvas re-roots service→feature (wire string kept)

- **What:** Implements the drill portion of `D-2026-06-17-D`. On the Services overview, **selecting a service shows its inspector (no drill); clicking a `feature` drills into its detail.** Concretely: `ServicesCanvas` now hands `shouldDrillFeature` (`n.kind === "feature"`) to the routing brain (was `service && !is_root`); `App.onMainNodeDrill` drills on `feature` (the `actor_ref → jumpToActor` branch is untouched). The detail canvas is **re-rooted from a `service` node to a `feature` node** across the engine: `_ALLOWED_KINDS_BY_CANVAS["service_detail"]` swaps `service`→`feature`; the `_detail_canvas_rules` validator requires a **root feature**; `detail_sync.sync_details_with_overview` seeds/archives one detail **per feature** (was per service) — a service with no features gets no detail. User-facing copy reads **"Feature detail" / "기능 상세"** (en + ko). The v0.1→v0.2 migrator (`_split_services`) now produces the **overview only** — v0.1 predates the feature kind, so it creates no detail canvases and drops the legacy sub-service / rule decomposition (the user re-authors it as features, whose details the live sync seeds on open).
- **Wire string kept (interim):** the persisted `canvas_kind` value, the `service_ref` field name, the `service_detail:<id>` cache/scope key, and the `?detail=` URL param all stay **`service_detail`** (now carrying a *feature* id). The cosmetic full rename `service_detail`→`feature` (CanvasKind literal + storage + keys + ChatScope) is **deferred (product-gated)** per `SERVICES_PLAN`/`FEATURE_CANVAS_PLAN` — both plans keep the wire string until that rename, to avoid a half-renamed two-repo churn. No existing projects ⇒ no data migration needed when it lands.
- **Why:** `D-2026-06-17-D` (user-approved 2026-06-17, "네 맞아요!") — a service = value description; features = capabilities under it; actions/rules live inside a feature (its detail). So the feature, not the service, is the thing you open to design the flow. Propagation is unchanged: `walk_ancestors` crosses canvases by **id-matching** (never reads `service_ref` or canvas kind), so the feature-rooted detail propagates step → feature → service → category automatically.
- **Alternatives:** (a) flip only the viewer predicate, keep per-service detail seeding — rejected (drilling a feature would open an empty/missing canvas; the detail cache has no lazy-create, so a working feature drill *requires* per-feature seeding). (b) do the full `service_detail`→`feature` wire rename now — deferred (product-gated; both plans keep the wire string for the interim). (c) migrate v0.1 sub-services into synthetic feature-rooted details — rejected (produces details unreachable from a service overview node, since services don't drill; overview-only migration is coherent and loss-free for the top-level service nodes).
- **Approval:** Implements the user-approved `D-2026-06-17-D`; executed under the user's autonomous "드릴/rename" directive (2026-06-20). The wire-string full rename remains for explicit user gating.
- **Spec impact:** Services = service shows inspector (no drill) / feature is the sole drill target; the detail canvas is feature-rooted. `specs/canvas-behavior.md` + `specs/kinds-fields.md` (root design SSOT) already describe the feature drill model. Tests: new `viewer/tests/services-drill-target.test.ts` (predicate); server detail-canvas fixtures across `test_canvas_doc` / `test_dirty_tracking` / `test_folder_io` / `test_propagation` / `test_sync` / `test_api_endpoints` re-rooted to feature; `test_migrate` asserts overview-only migration.

### D-2026-06-20-H — `metric` / `content` kinds retired (below action altitude); retired-kind i18n swept

- **What:** The two service-composition kinds are **retired**. `metric` (a KPI / success-indicator node) and `content` (an implementation-artifact node) are removed across the stack: server `MetricNode` / `ContentNode` (`models_composition`) + the two `models_union` unions + `NodeKind` Literal + `_ALL_KIND_CLASSES` + `schema_export` map + `models.py` re-exports + `migrate_builders` v0.1 content branch; the viewer `Metric.ts` / `Content.ts` domain classes, their node renderers + inspectors, `CompositionList.tsx` + `ContentFields.tsx`, the `createBlankNode` cases, both registries, `SketchNode` unions, `types.ts` `NodeKind`, and the SERVICE_COMPOSITION metric stencil preset + the service_detail "Value" stencil section (value is the service-inspector `ref_value_ids` chips now, `D-2026-06-20-F`). The dead **composition-child affordance thread** (`addCompositionChild` → `onAddChild` / `onPatchChild` / `onRemoveChild`, orphaned when `CompositionList` was removed in `D-2026-06-20-F`) is removed with them. `_drop_retired_kinds` strips both from older canvases on read (loss-free). Codegen (`wire.gen.ts` + `wire_contract.json` ×2) regenerated. **Also sweeps the retired-kind i18n that `D-2026-06-20-G` left for doc-sync:** the `kind.{mission_ref,value_ref,identity_ref,metric,content,value}` + `kindTag.metric` labels, the whole dead `composition` object, and the orphaned `stencil.section.{composition,values,missions,identityAspects}` + `stencil.note.{compositionInsideService,valuesExchanged,dragMission…,dragValue…,dragIdentityAspect…}` keys (en + ko, symmetric). Palette = **13 kinds**.
- **Why:** Both kinds sit **below action altitude** — the level Novel operates at (service → feature → flow). A `metric` is implied by a flow's result node + edge; `content` (implementation artifacts / user-facing outputs) is the external agent's job or is carried by the producing action's edge. Neither earns a standalone node in the 본질→서비스 model. Retiring them keeps the Feature canvas about *what flows between actors*, not *how it is built*.
- **Alternatives:** (a) keep `metric` as a visible "Value" node — rejected (value is the service inspector's `ref_value_ids` chips; one mechanism beats two). (b) keep `content` for artifact tracking — rejected (below altitude; the external coding agent owns artifacts). (c) keep the `addCompositionChild` primitive narrowed to `rule` for a future creation path — rejected (dead-wiring = `임시 통과`; rule is AI-creatable via MCP, and a user-direct rule-creation affordance is a fresh design when needed).
- **Approval:** Accepted by user via the approved Chunk-2 plan (the "정리 폐기 5종" mandate: `group` + 3 refs + `metric` + `content`).
- **Spec impact:** Palette − 2 (13 kinds). `concepts/kinds.md` / `specs/kinds-fields.md` already list both retired (root design SSOT led the code). `RETIRED_KINDS` already holds both. The deferred refs/composition i18n cleanup from `D-2026-06-20-G` is now done — no i18n debt remains for any retired kind.

### D-2026-06-20-G — `mission_ref` / `value_ref` / `identity_ref` kinds retired (Foundation references → service-inspector chips)

- **What:** The three Foundation-reference kinds are **retired** (implementing `D-2026-06-17-H`). Foundation references are now the service inspector's chip pickers (`ref_value_ids` / `ref_identity_ids`, `D-2026-06-20-F`), not standalone nodes; `actor_ref` is the only surviving standalone reference node. Removed across the stack: server `MissionRefNode` / `ValueRefNode` / `IdentityRefNode` + `_FOUNDATION_REFS`; the viewer domain classes / node renderers / inspectors / registries / stencil presets; and the **whole FoundationRefPicker machinery** (the picker modal + the `pendingFoundationRef` drag-drop state thread across App / SketchCanvas / SketchModals / SketchInspectorBindings / useDragAndDrop + the `availableMissions` chain). ESSENCE_SOURCE_KINDS / publish-eligibility / edge-classification ref entries trim to the masters + `actor_ref`. `_drop_retired_kinds` strips the 3 from older canvases on read (loss-free). Palette = **15 kinds**.
- **Why:** A service declares which Foundation commitments it answers to via the 5-field inspector's reference chips; a separate standalone ref node per commitment duplicated that and cluttered the Feature canvas. One mechanism (chips) beats two.
- **Alternatives:** (a) keep the ref nodes alongside the chips — rejected (duplication). (b) keep the picker for orphan-rewire — rejected (no ref nodes left to rewire).
- **Approval:** Accepted by user via the approved Chunk-2 plan (implements the pinned `D-2026-06-17-H`).
- **Spec impact:** Palette − 3 (15 kinds). `concepts/kinds.md` / `specs/kinds-fields.md` already list them retired. `RETIRED_KINDS` gains the 3. The now-unused stencil/inspector i18n keys for the refs are left (symmetric; cleaned at doc-sync).

### D-2026-06-20-F — Service inspector = 5 question-titled fields (2 typed + 3 ref-chip lists, Option B); legacy 9 fields discarded

- **What:** The `service` inspector is redesigned to **5 question-titled fields** (`D-2026-06-17-B`): 2 typed-text — 왜 필요한가? (`problem`) / 뭐가 좋아지나? (`value_created`) — + 3 **multi-select reference chip lists** — 누가 참여하나? (`ref_actor_ids` → actors) / 뭘 양보 못 하나? (`ref_value_ids` → core_values) / 어떤 결로 다가가나? (`ref_identity_ids` → identities). References are **id arrays on `ServiceNode` (Option B)**, rendered as removable chips picked from the upstream masters (pick-only; pick-OR-create `D-2026-06-19-C` is a follow-up). The old **9 free-text fields** (target_side / what / scope / trigger / how / outcome / do / dont / body) are **deleted and discarded** — no loss-free migration (Pydantic drops the old extras on read). The service inspector's composition (rules / contents) panels are removed (composition lives on the Feature canvas); the `target_side` color tint + the shared `DoDontFields` component are deleted.
- **Why:** The service is the value-exchange hub; the 5 questions ARE the AI interview ("제목이 곧 질문"). The old 9 fields were a flat free-text bag that didn't encode the value-exchange model; 2 typed + 3 references capture it sharply (who / why / what-improves / what-can't-give-up / what-tone). Option B (id arrays) is forced by the marathon's retirement of the `value_ref` / `identity_ref` kinds — the chips can't be those nodes, so they are ids on the service. Discard is safe: **no project uses Novel yet**, and Pydantic ignores removed fields on read.
- **Alternatives:** (a) keep `body` as a hidden migration sink for the deleted content — not taken (no data to preserve; YAGNI). (b) Option A (refs as separate `*_ref` nodes + edges) — rejected (those ref kinds are retired; would contradict the marathon).
- **Approval:** Accepted by user, 2026-06-20 (AskUserQuestion checkpoint ② — "아직 플롯을 사용하는 프로젝트가 없어요. 그래서 폐기해도 되지 않을까요?" → discard; Option B confirmed earlier this session).
- **Spec impact:** `ServiceNode` field-set → `problem` + `value_created` + `ref_actor_ids` / `ref_value_ids` / `ref_identity_ids` (the 9 deleted). `specs/kinds-fields.md` / `concepts/kinds.md` already describe the 5-field service. Multi-select chip picker = `inspectors/service/RefChips.tsx`. The drill rewire (service inspector-only / feature drill) is a separate step (Chunk 2.7); pick-OR-create + the AI interview-question wiring are follow-ups (ROADMAP 5.7).

### D-2026-06-20-E — `note` kind added (edgeless canvas-global ambient memo on the Feature canvas)

- **What:** New `note` node kind (implements `D-2026-06-17-F`). A canvas-global ambient memo on the Feature canvas ("모바일 우선·본문 500자") — a human-read guide. **Edgeless invariant:** a note NEVER participates in an edge (ambient, not a flow participant), enforced **both** viewer-side (`handleConnect` rejects note endpoints) and server-side (`CanvasDoc._notes_are_edgeless` rejects any edge incident to a note). Field: `body`. Full lock-step: `NoteNode` + generated `NoteJson` + viewer `Note` class / renderer / inspector / registries / i18n / a yellow ambient stencil preset + guards. Palette = 18 kinds.
- **Why:** A feature flow often carries cross-cutting context the human should always see and the AI should always work under, but that isn't a flow step. A dedicated edgeless kind captures it without polluting the flow graph. The edgeless rule is load-bearing — a note in an edge would imply it participates in the flow, which it must not.
- **Alternatives:** (a) a free-text field on the canvas — rejected (not an addressable node the AI framing can enumerate). (b) allow edges from notes — rejected (`D-2026-06-17-F`: ambient context is not a flow participant).
- **Approval:** Accepted by user via the approved Chunk-2 plan (implements the pinned `D-2026-06-17-F`).
- **Spec impact:** Palette + `note` (18 kinds). Allowed on the `service_detail`/Feature canvas. Edgeless invariant pinned by `tests/test_canvas_doc.py` (server) + the `handleConnect` guard (viewer). **Follow-up (ROADMAP):** the AI-framing injection (note bodies appended to the per-canvas `chat_context` framing) — the "AI가 늘 깔고 작업" half — is deferred; the human-read memo + edgeless invariant ship now.

### D-2026-06-20-D — `feature` kind added (capability under a service; the sole drill target)

- **What:** New `feature` node kind (implements `D-2026-06-17-D` / `D-2026-06-19-H`). A feature is a **capability the service offers** (글쓰기 / 편집) — a behaviour grouping under a service, **not** an independent value unit (value exchange is a property of the *service*; a feature that grows its own multi-actor exchange is promoted to a service). It is the **sole drill target**. Field: `proposed` — the one-line "무엇을 할 수 있나?" summary. Nests under a service via a directed edge (service→feature), placed from the services stencil. Full lock-step: Pydantic `FeatureNode` + generated `FeatureJson` + viewer `Feature` class / renderer / inspector / registries / i18n / stencil preset + drop-into-service resolver + guards (palette = 17 kinds).
- **Why:** The services-overview redesign pivots on `feature` as the drill target: selecting a service opens its 5-field inspector (never drills), while the behaviour flow belongs to a *capability*. A feature is the right altitude for that flow — fine enough to drill into, coarse enough to stay above implementation. Anchored to VISION: the feature/service split keeps "value = service property" honest.
- **Alternatives:** (a) keep `service` as the drill target — rejected (`D-2026-06-17-D`: a service shows its inspector, never drills). (b) `feature` = independent value unit (own actors/value) — rejected (`D-2026-06-19-H`: then it is indistinguishable from a service; the promotion test becomes meaningless).
- **Approval:** Accepted by user via the approved Chunk-2 plan (implements the pinned `D-2026-06-17-D` / `D-2026-06-19-H`).
- **Spec impact:** Palette + `feature` (17 kinds). `concepts/kinds.md` / `specs/kinds-fields.md` already define it. Allowed on the `services` canvas. The **drill rewire** (service→feature) + the **`service_detail`→Feature canvas rename** are a separate step (Chunk 2.7).

### D-2026-06-20-C — `group` kind retired (folding = a future view affordance, not a node kind); retired-kind drop-on-read added

- **What:** The `group` node kind is **retired** from the palette (server + viewer), implementing `D-2026-06-19-H`. Its chunking role moves to the **feature** level; folding a busy flow becomes a **view affordance** (deferred to ROADMAP), not a node kind. Removed: `GroupNode` (Pydantic) + the viewer `Group` class / node / inspector / registries / i18n + the group-folding feature (`groupActions` / `groupCollapse`, the Group/Ungroup context menu, the group-membership fold path in `useNodesMemo`). Added a general **retired-kind drop-on-read** migration (`canvas_io._drop_retired_kinds` + `RETIRED_KINDS`): a node of a retired kind (and any edge incident to it) is stripped when an older `canvas.json` is read, so pre-retirement projects keep loading — loss-free (only the group container goes, never its member step/decision nodes).
- **Why:** Marathon + 2026-06-19 review (`D-2026-06-19-H`): a `feature` is a behaviour grouping, so a separate `group` chunking kind is redundant at the feature altitude; folding is a UI view concern, not a domain kind. Anchored to VISION — fewer, sharper kinds keep the structure the user/AI reason over honest.
- **Alternatives:** (a) keep `group` for canvas folding — rejected (folding is a view feature; baking it into the domain palette conflates UI with domain). (b) drop `group` but keep the folding code dead — rejected (YAGNI; the future view affordance is designed fresh, tracked in ROADMAP).
- **Approval:** Accepted by user via the approved Chunk-2 plan (implements the pinned `D-2026-06-19-H`).
- **Spec impact:** Palette − `group` (16 kinds; server `_ALL_KIND_CLASSES` + viewer registries/`KIND_DIRS` reconciled to 16). `concepts/kinds.md` / `specs/kinds-fields.md` already list `group` as retired. Folding-as-view → ROADMAP. New read-path migration `_drop_retired_kinds` is reused by the remaining retirements (metric / content / refs).

### D-2026-06-20-B — Migration physical move (viewer → app repo) resequenced to AFTER the Chunk-2 concept code; concepts land in-monorepo first

- **What:** The viewer's physical move into the `plot/` app repo (+ the app→versioned-engine dependency), pinned by `D-2026-06-20-A` as a prerequisite *before* concept implementation, is **resequenced to land AFTER the Chunk-2 concept code** (retire `group` + the 5 doomed `*_ref` / `metric` / `content` kinds; add `feature` / `note` / `entity`; service 5-field chip inspector; actor_ref reform; drill rewire). Concepts are done **in the monorepo first**; the move follows. Landing path when it happens = `plot/viewer/`.
- **Why:** The migration's schema-parity blocker — the reason it had to precede implementation — is **already resolved**: v0.87.0 made the viewer wire types a generated artifact (`ts_codegen.py` → `wire.gen.ts`) alongside the `wire_contract.json` snapshot, both split-survivable. With parity secured, the heavy concept churn (≈9 kind add/remove/reform, each a lock-step across Pydantic model + TS class + renderer + inspector + i18n + tests) is **safer and faster in one repo**: the rich guards stay alive, there is no cross-repo paired-commit lock-step, and iteration is single-tree. Anchored to VISION — the concept code directly serves the essence (the structure users define), so doing it first delivers essence value sooner; the move serves the open-core/business boundary and loses nothing by following.
- **Alternatives:** (a) physical move first per `D-2026-06-20-A` literal order — not taken (every later kind change becomes a cross-repo paired commit; friction with no parity benefit now that codegen secured it). (b) skip the move entirely — rejected (the open-core boundary is still required; only deferred, not dropped).
- **Approval:** Accepted by user, 2026-06-20 (AskUserQuestion — "개념을 모노레포에서 먼저"; landing path "plot/viewer/").
- **Spec impact:** Resequences `D-2026-06-20-A`'s migration-prereq clause (the move is now post-concept, not pre-implementation). No change to the architecture itself (open-core boundary, canvas = app-exclusive) — only the *order* of realizing it. ROADMAP Track 2 ordering.

### D-2026-06-20-A — Novel system architecture = open-core (open plugin engines / closed paid app); the visual canvas is app-exclusive

- **What:** Novel's system architecture is pinned as **open-core**:
  - **Open-source plugins (MIT)** — each is a **headless MCP engine** (+ Claude Code glue: skills/agents/hooks). They produce **structured data + text/markdown artifacts** only; **no visual canvas.** (`mashbill` = the canvas/sketch engine; `solera_mcp` = the project-workflow engine; …)
  - **Closed, paid Novel app** — an **MCP host + visual canvas + composition shell.** The **visual canvas is the app's exclusive paid value**; if a plugin shipped the canvas the app would have no differentiated value.
  - **Shared open data** — `.noory/` JSON, read/written by both. The app's moat = **visual experience / UX / composition quality**, NOT data lock-in (the format is open).
  - **Dependency = one-way:** app → plugin engines (the app hosts/consumes them); the engine never imports the app (R8). Plugins run standalone (Claude Code + MCP) without the app.
  - **Value split = VISION's physical division of labour:** the AI works the *structure* (plugin), the human thinks via the *visual* (app), over the shared `.noory/` data.
  - **Composition vision (deferred):** the app may host multiple engines (mashbill + solera_mcp + …) as one product; the unified-canvas UX is unspecified for now (engines are MCP, so wiring stays open).
- **Why:** Settling the structure before implementation (user, 2026-06-19~20). The plugin/app/engine arrangement was scattered; the load-bearing question — where the canvas lives — is answered by the value boundary: the canvas must be app-only or the paid app has no value, so the open plugin stays text/structured-only.
- **Alternatives:** (a) the plugin ships the visual canvas — rejected (collapses the app's paid value). (b) keep the viewer in noory-ai / a web canvas — rejected (canvas = app-exclusive; the web product is dropped). (c) close the engine into the app — rejected (loses the open MCP value: any agent can drive Novel).
- **Approval:** Accepted by user, 2026-06-20 (open-core boundary + canvas = app-exclusive + plugin = text artifacts, confirmed across the structure discussion).
- **Spec impact:** NEW `noory-workspace/docs/ARCHITECTURE.md` (system architecture SSOT) + index. Migration prereq: viewer → `plot/` (app); `viewer/types.ts` → a `schema_export.py`-generated artifact **before** the move (schema-parity guard, TECH_REVIEW step 1); `mashbill` headless. ROADMAP Track 2. Builds on the Pencil model (OVERHAUL R7) + the viewer→app overhaul direction.

### D-2026-06-19-J — Design/definition/spec docs consolidated into a single source (`noory-workspace/docs/`)

- **What:** Novel's scattered, mutually-conflicting concept/definition/spec docs are consolidated into **one directory `noory-workspace/docs/`** as the single source: `index.md` (canonical map) + `VISION.md` (essence + 3-phase + identity) + `concepts/` (canvases / kinds / ai-collaboration — meaning) + `specs/` (canvas-behavior / kinds-fields / edges / storage-publish / domain — behavior). Old root docs absorbed + deleted (`IDENTITY.md` → VISION §identity; `FOUNDATION_CONCEPT.md` → ai-collaboration §2.1 + VISION; `AI_CHAT_PLAYBOOK.md` → ai-collaboration; `BIG_PICTURE_REVIEW.md` → open topics to ROADMAP, decision log already mirrored here; `DOC_SYNC.md`, old `README.md` → index.md). `noory-ai/mashbill/docs/{SPEC,CONCEPTS,DOMAIN}.md` get a redirect header pointing at the root source (code-near mechanics — CURSOR / AUTO_LAYOUT / PUBLISH / ARCHITECTURE — stay in noory-ai). `DECISIONS.md` (this log) stays in noory-ai (D-id log, hook-wired).
- **Why:** The AI (in-app coach + external coding agents) was referencing scattered docs whose definitions disagreed (e.g. IDENTITY "NOT a mindmap" vs PRODUCT_SPEC "mindmap-based"; 15/17 kind drift; feature concept unreconciled), producing bad context. A single coherent new-concept source is the prerequisite for resuming development.
- **Alternatives:** (a) leave docs split, fix conflicts in place — rejected (root cause is scattering). (b) one big file — rejected (one *directory* with concepts/ + specs/ reads better). (c) move everything incl. DECISIONS/code-near out of noory-ai — rejected (breaks hooks/skills; DECISIONS is the hook-wired D-log).
- **Approval:** Accepted by user, 2026-06-19 ("싹다 새로운 개념으로 정리... SSOT... index.md... 다해요 4개 다").
- **Spec impact:** New SSOT = `noory-workspace/docs/`. `session_start.py` paths fixed (VISION from root docs/, DECISIONS/NEXT_SESSION from plugin docs/). Skills + `noory-ai/mashbill/CLAUDE.md` doc links repointed. This log + SPEC/CONCEPTS/DOMAIN bodies remain for code-near reference behind redirect headers.

### D-2026-06-19-I — Feature-canvas `actor_ref` = read-only anchor; per-service exchange fields retired

- **What:** On the Feature canvas, `actor_ref` is a **read-only anchor** that marks the flow's subject ("who starts / who can"), **not** a value-exchange editor. Its former per-(actor×service) fields — `gives` / `receives` / `motivation` / `pain` — are **retired** (supersedes the `D-2026-06-15-J` move that put motivation/pain on actor_ref). Value now lives at two existing places only: **Actors** (role-level relationship edges) and the **service inspector** "뭐가 좋아지나?" (the aggregate). Role identity is edited on Actors; permissions on `rule.actor_permissions`.
- **Why:** Big-picture review (2026-06-19). A feature is a behaviour grouping, not a value-exchange unit (`D-2026-06-19-H`), so granular per-actor exchange on the feature canvas duplicated what Actors edges + the service 5-field already capture (redundant). The user confirmed actor_ref is "표현하는 수단" (display) and not editable there.
- **Alternatives:** (a) keep gives/receives on actor_ref — rejected (redundant). (b) move the per-service exchange to the service inspector as new fields — not taken now (Actors role-level + service aggregate suffice; revisit only if a concrete need for per-actor granularity appears).
- **Approval:** Accepted by user, 2026-06-19 ("네네 좋아요" on read-only anchor + retire).
- **Spec impact:** `actor_ref` field-set → `ref_actor_id` + denormalized read-only `side` only; drop `gives`/`receives`/`motivation`/`pain` (loss-free migration; code = `plans/`). `specs/kinds-fields.md`, `concepts/kinds.md`. Supersedes `D-2026-06-15-J` actor_ref payload.

### D-2026-06-19-H — `feature` = a service-level capability / behaviour grouping (not an independent value unit); Feature canvas = UX flowchart

- **What:** A `feature` is a **capability the service offers** (글쓰기 / 편집) = a **behaviour grouping under a service**, NOT an independent value unit. **Value exchange is a property of the *service*** (multiple actors create/exchange value — PHILOSOPHY), not of a feature; a feature that grows its own multi-actor value exchange is **promoted to a service** (the promotion test). The **Feature canvas** (the old Service-Detail) is a **UX flowchart** (행동 → 분기 → 결과) at **action altitude** only; implementation below it (저장·쿼리·렌더) is the external agent's job.
- **Why:** Big-picture review (2026-06-19). The `feature` kind (`D-2026-06-17-D`) and `actor_ref`'s "per-service" semantics were unreconciled after the drill target moved service→feature. Anchoring on "value = service property" resolves it cleanly: feature = behaviour grouping, so the Feature canvas is a UX flow and its actors are anchors (`D-2026-06-19-I`), not value participants.
- **Alternatives:** (a) feature = independent value unit (own actors/value) — rejected (then it is indistinguishable from a service; the promotion test becomes meaningless). (b) leave the service/feature boundary fuzzy — rejected (it caused the actor_ref placement confusion).
- **Approval:** Accepted by user, 2026-06-19 (UX-흐름도 + 행동 묶음 reading confirmed, "네네 좋아요").
- **Spec impact:** `concepts/kinds.md` (`feature`, `service`), `concepts/canvases.md` (Feature canvas = UX 흐름도), `specs/canvas-behavior.md`. Builds on `D-2026-06-17-D/G`.

### D-2026-06-19-G — Identity SSOT consolidated to VISION; "mindmap" dropped as the user-facing word

- **What:** Novel's identity statement has **one source = `VISION.md` §identity** (absorbing the old `IDENTITY.md`); other docs reference it, never restate it. The **"mindmap" framing is dropped** — both the old PRODUCT_SPEC "mindmap-based planning tool" claim and the user-facing "mindmap" word are retired. Novel is a **structured, opinionated, coach-led design tool**, the opposite of free-association brainstorming; post-marathon (interview-driven canvases) the word actively miscues.
- **Why:** Three docs defined Novel's identity in conflicting words (IDENTITY "NOT a mindmap" / PRODUCT_SPEC "mindmap-based" / VISION's purpose sentence) — an SSOT violation flagged but never resolved (BIG_PICTURE §9-A / T1, decision slot empty). Dropping "mindmap" auto-reconciles all three (only PRODUCT_SPEC asserted it; VISION + IDENTITY already say "not a mindmap").
- **Alternatives:** (a) keep "mindmap" as the friendly user word — rejected (requires overriding IDENTITY + carries the free-association miscue post-marathon). (b) formal "strategic design tool" everywhere — rejected (too stiff for the user-facing surface).
- **Approval:** Accepted by user, 2026-06-19 ("좋아요" on the consolidated VISION).
- **Spec impact:** `VISION.md` §정체성 (IS/IS NOT, mindmap retired). `IDENTITY.md` deleted (absorbed). PRODUCT_SPEC §1 "mindmap" claim superseded (partial supersede of `D-2026-05-12-A`).

### D-2026-06-19-F — The external agent gets selection-awareness + context over MCP (required, not deferred) — fulfills the Layer-2 selection requirement for the R7 primary path

- **What:** The external agent (the user's own Claude Code / Codex / Gemini, connected
  over **MCP** — the R7 primary path) must receive **selection-awareness** and the
  **context envelope** (`D-2026-06-17-L`: active canvas + current selection + upstream
  summary + entity registry + per-canvas framing) **through MCP** — the same connection it
  already uses. The agent pulls it the way it reads everything else. Internally Novel needs a
  **viewer→engine selection bridge** so the engine knows the current viewer selection and
  can report it via the MCP context tool (`get_viewer_context`).
- **Required, not deferred.** This corrects CHAT_ARCH Layer 2's "MCP path … deferred"
  (selection-awareness): the original requirement — "the chat must **know the selection**;
  everything selected synced" (user 2026-06-14) — **plus** `OVERHAUL` R7 (the external agent
  is the **primary** AI path) make external selection-awareness a **requirement**, not an
  option. The primary path must not be more context-starved than the in-app chat.
- **Double-billing set aside** per user (2026-06-19, "일단 이중 과금 생각하지 맙시다") — C
  does not hinge on it.
- **Why:** Agenda C (playbook §3-C). The Pencil model makes the external agent primary
  (R7); the selection-awareness requirement (Layer 2) must therefore cover it. User: "MCP로
  이게 된다며 그렇게 바깥에도 제공해주면 됩니다" — the mechanism already exists (the agent is
  on MCP); expose selection + envelope through it.
- **Alternatives:** (a) keep MCP selection deferred / external agent works canvas-content-only
  (user names things by hand) — rejected (the primary path must be first-class). (b) push to
  the external agent — not possible (it is outside Novel; it pulls via MCP).
- **Approval:** Accepted by user, 2026-06-19 ("그렇게 바깥에도 제공해주면 됩니다").
- **Spec impact:** CHAT_ARCH Layer 2 (un-defer MCP selection-awareness → required) + the MCP
  context tool (`get_viewer_context` returns selection + the `D-2026-06-17-L` envelope) + a
  viewer→engine selection bridge. Playbook §3-C resolved. Code = follow-up. Builds on
  CHAT_ARCH Layer 2 (2026-06-14 ask), `D-2026-06-17-L` (envelope), `OVERHAUL` R7.

### D-2026-06-19-E — Chat thread keying is selection-driven: a selected service / feature node keys its own thread (resolves agenda B / CHAT_ARCH Layer-1 pending)

- **What:** In the Services/Feature area the chat **thread** is keyed by the **selected
  node instance**, not just by the canvas:
  - A selected **service** node → thread `service:<service_id>` (that service's design
    conversation — the 5-field interview, which features it holds).
  - A drilled / selected **feature** → thread `feature:<feature_id>` (that feature's
    behaviour-flowchart conversation).
  - **Nothing relevant selected** → the canvas-level thread (overview `services`; or
    `foundation` / `actors` / `entities` / `project`).
  - **Only `service` and `feature` nodes key a thread.** Other selections (step,
    decision, actor, …) stay **context-injection** (CHAT_ARCH Layer 2), not separate
    threads — avoids thread-per-node sprawl.
- This **refines CHAT_ARCH Layer 1**: the prior model keyed *thread = canvas*, with the
  selection merely *injected* as context. Now a selected service/feature node keys its
  **own per-instance thread**. It **replaces the single `service_detail:<service_id>`
  parametric scope with two — `service:<id>` + `feature:<id>`** (the feature one follows
  `D-2026-06-17-D`'s drill-from-feature rewire).
- **Why:** Agenda B (playbook §3-B), explicitly flagged unpinned in CHAT_ARCH Layer 1
  (the ⚠ Pending note) to resolve with the 5.10 playbook work. User: each **service** AND
  each **feature** needs its own conversation, and **the selected node decides which**
  ("선택한 서비스 노드가 있다면 그렇게 해야"). A service's design talk and a feature's
  flowchart talk are distinct histories and must not share one thread.
- **Alternatives:** (a) feature-only (assistant's first proposal) — rejected by user
  (service also needs its own thread). (b) service-only / keep `service_detail` keyed by
  service — rejected (drill is now per-feature; features need their own threads). (c)
  thread-per-any-selected-node — not taken (sprawl; only service/feature are design units).
- **Approval:** Accepted by user, 2026-06-19 ("네").
- **Spec impact:** CHAT_ARCH Layer 1 (thread table + resolve the ⚠ Pending note) + the
  Decisions / Implementation-sequence scope identifiers (`service_detail` → `service` +
  `feature`). `test_chat_scope_parity` + engine session key `(plot_root, provider, scope)`
  follow. Playbook §3-B resolved. Code = follow-up (scope rename/split + viewer thread
  routing keyed on the selected service/feature). Builds on `D-2026-06-17-D` (drill from
  feature), CHAT_ARCH Layer 1/2.

### D-2026-06-19-D — Concept-registry integrity is strict from the start (hybrid: code guards + LLM matching), NOT YAGNI-deferred

- **What:** The **concept registry** — entities (`D-2026-06-17-I/K`) **plus** the referenced
  masters actor / core_value / identity (`D-2026-06-19-C` unified them) — is the **SSOT for
  domain concepts**, so its integrity is designed **strict from the start** (global CLAUDE.md:
  *YAGNI exception for 도메인 경계 / SSOT*). Reliability is **not playbook-trust-only**; it is a
  **hybrid** (the entity-resolution / MDM standard = deterministic + probabilistic):
  1. **Deterministic uniqueness guard (code):** a normalized-name collision is **blocked** — the
     system cannot silently create a second master with the same name. (Kills the cheap, common
     *silent split*.)
  2. **Mandatory match-before-create:** every create is checked against the in-context registry
     (`D-2026-06-17-L`) first — **not optional.**
  3. **Naming ≠ identity (sharpens `D-2026-06-17-K`-B2):** match on **identity** ("같은
     것인가?"), not name similarity — so 글/게시물/포스트 merge (same identity, different names)
     while 글/댓글 do **not** (similar name, different identity). (KG warning: collapsing naming
     and identity into one fuzzy check is what corrupts the graph.)
  4. **No silent merge / finalize:** the LLM **proposes**, the user **confirms** (B2/B4).
  5. **Correction path = stewardship (do NOT defer):** because no matching is perfect, the
     registry must be **correctable** — **merge** (two that turned out the same) / **split** (one
     wrongly merged) + **survivorship** (which values survive; user picks). Surfaced on the
     **Entities canvas** (no separate review-queue workflow — disproportionate).
  6. **Applies to all references (`D-2026-06-19-C`):** actor / core_value / identity masters get
     the same integrity, not just entities.
  This **revises `D-2026-06-17-K`-B2's "this is a playbook responsibility, not code"** → split:
  **semantic matching = playbook (LLM); integrity guards (uniqueness, mandatory match, merge/split
  correction) = code.**
- **Why:** Agenda E (playbook §3-E). Without guards, one wrong LLM match silently fragments the
  registry (글/게시물/포스트 as three) or wrongly merges distinct concepts — corrupting the domain
  SSOT. User: "YAGNI로 판단하면 안 됩니다 … 처음부터 확실하게 하세요." Grounded in entity resolution
  (hybrid deterministic+probabilistic, human-in-the-loop on ambiguous via a confidence threshold),
  MDM (golden record / survivorship / stewardship), and the knowledge-graph naming≠identity warning.
- **Alternatives:** (a) playbook-trust-only + revisit on drift (the assistant's earlier YAGNI
  recommendation) — **rejected by user** (registry integrity is an SSOT matter, not YAGNI). (b)
  full review-queue MDM workflow — not taken (disproportionate; in-context registry + confirm +
  canvas merge/split suffices).
- **Approval:** Accepted by user, 2026-06-19 ("처음부터 확실하게 하세요").
- **Spec impact:** Playbook §2.5 (Entities reliability), §0 reference principle (`D-2026-06-19-C`
  gains the integrity layer), §3-E resolved. Revises `D-2026-06-17-K`-B2 (playbook→hybrid). Code
  = follow-up on the registry (deterministic name-uniqueness guard, mandatory match-before-create,
  merge/split + survivorship affordance) — ROADMAP. Builds on `D-2026-06-17-I/K`, `D-2026-06-19-C`,
  `D-2026-06-17-L`.

### D-2026-06-19-C — Reference fields are pick-OR-create (match → pick, else create the master upstream), unified with entity surfacing

- **What:** Every coach field that *references an upstream concept* — the Services
  inspector's 3 reference fields (누가 참여하나?=actor, 뭘 양보 못 하나?=core_value,
  어떤 결로 다가가나?=identity, `D-2026-06-17-B`) and the Feature canvas's actor anchor,
  and any later-canvas→earlier-canvas reference — is **not pick-only.** It is
  **pick-OR-create**, and the mechanism is **the SAME rule as entity surfacing**
  (`D-2026-06-17-K` B2/B4), now applied to actor / core_value / identity too:
  1. **The user answers in natural language** (does not manually open a picker).
  2. **The coach semantically matches** the answer against existing upstream masters —
     the strong-dedup matching of `D-2026-06-17-K`-B2 (글=게시물=포스트 → one).
  3. **Match → pick:** the coach proposes the existing master ("그거 '관용과 지지'랑
     같죠? 그걸로 달게요") → on confirm, a **chip** is added.
  4. **No match → create upstream:** the coach proposes creating it ("'초보 환대'를
     Foundation에 새로 넣고 여기 달까요?") → on confirm, a **real master node is created
     on its home canvas (Foundation / Actors)** and a chip references it here.
  5. **"Create" is NOT free-typing** — it makes a real upstream node, so `D-2026-06-17-B`'s
     "references are picked, not free-typed" ban is preserved. The result is always a chip
     pointing at a real master, never inline free text.
  6. **The new master is created lightweight (name + one line), flagged incomplete (⚠);
     its deep definition is filled later by its home-canvas coach** (mission/core_value =
     `D-2026-06-16-K/L`, etc.) — so the current interview flow is **not derailed**.
  7. **Never silent** — the coach proposes, the user confirms (`D-2026-06-16-P`).
  8. This opens the **backward direction** of "뒤 캔버스가 앞을 참조" (downstream fills
     upstream), consistent with VISION's **non-linear, reversible cycle** and `D-2026-06-17-I`
     (entities born during downstream design and registered upstream).
- **Why:** User: "우리는 액터·코어밸류·아이덴티티를 이미 가지고 있거나 … 새롭게 필요하다면
  만들어서 사용해야 한다." `D-2026-06-17-B` only specified *pick* (chips, not free-typed); it
  never covered the needed-but-missing case. Forcing pick-only would make the user either pick
  a wrong existing concept or leave the flow to go create one manually (which is exactly what
  the current pre-D-17-B pickers do — "Add one on the Foundation canvas first"). Unifying with
  the entity rule keeps it one mechanism, not a second one.
- **Alternatives:** (a) pick-only — rejected (can't reference a missing concept without
  leaving the flow). (b) free-type the new reference inline — rejected (violates `D-2026-06-17-B`;
  create a real master instead). (c) run the full master mini-interview inline on create —
  not taken now: lightweight stub + later deepening on the home canvas, to avoid derailing the
  current interview.
- **Approval:** Provisional — user, 2026-06-19 ("그래요 일단 해봅시다"). Emphasis: pin the full
  discussed content, lose nothing ("토론을 한 내용을 빼면 안 되요. 그게 핵심이에요").
- **Spec impact:** AI playbook §0 (common reference principle), §2.3 (Services 3 refs), §2.4
  (Feature actor anchor). Extends `D-2026-06-17-B`; unifies with `D-2026-06-17-K` (B2 match /
  B4 propose). Code = follow-up (the D-17-B chip inspector + create-upstream affordance are not
  yet built — the pre-D-17-B pickers are pick-only; ROADMAP / 5.7).

### D-2026-06-19-B — Feature-canvas coach content (happy-path-first) + hand-off point = the altitude guard (resolves D-2026-06-18-B's deferred item)

- **What:** Feature-canvas coach content (AI playbook §2.4), grounded in behavior-flow
  methods (user story mapping / use case scenarios / UX user flows — sources in playbook):
  1. **Coach flow** (§0 gentle tone + **"happy path first"**, which all three methods agree
     on): **anchor** on actor + goal → **happy path first** ("잘 풀릴 때 처음부터 끝까지 뭘
     하나요") → **then branches** ("중간에 갈리는 데 있을까요", condition→branch) → **outcome**
     ("마지막엔 어떻게 끝나나요").
  2. **Altitude guard as coach behavior**: when the user drifts into implementation
     (저장·쿼리·렌더), the coach redirects up — "그건 만들 때 에이전트 몫, 여기선 사람이 뭘
     하는지에 머물러요."
  3. **note** (`D-2026-06-17-F`, edgeless ambient) + **rule** (`D-2026-06-17-E`, per-feature
     constraint) prompts.
  4. **Hand-off point (resolves `D-2026-06-18-B`'s deferred Feature item):** the **altitude
     guard (`D-2026-06-17-G`) IS the hand-off line** — no new decision needed. In-app coach
     owns the behavior flowchart (at/above user-action altitude = *design*); the external MCP
     agent owns everything below (저장·쿼리·렌더 = *execution / build*). This composes
     `D-2026-06-17-G` (altitude) + `D-2026-06-18-B` (in-app coach designs, external agent
     executes) cleanly.
- **Why:** AI playbook §2.4 / §3-D (ROADMAP 5.10), continuing the F→A→S→기능 order. User
  directed grounding in expert method. `D-2026-06-18-B` explicitly deferred "where the in-app
  coach hands off to the external agent on the feature canvas" to this 기능 discussion; it falls
  out of the existing altitude guard rather than needing a fresh fork.
- **Alternatives:** (a) a separate, new hand-off boundary distinct from the altitude guard —
  rejected (redundant; the altitude guard already draws exactly that line). (b) elicit branches
  before the happy path — rejected (story mapping / use case / user-flow all say map the happy
  path first, then alternates).
- **Approval:** Accepted by user, 2026-06-19 ("네 좋습니다" on the draft).
- **Spec impact:** Playbook §2.4 (Feature coach + hand-off) + §3-D. Resolves the open note in
  `D-2026-06-18-B`. Remaining = code: `chat_context.py` feature framing text (the altitude
  guard) + `service_detail`→`feature` scope-key rename (5.7 / implementation). Builds on
  `D-2026-06-17-G` (altitude), `D-2026-06-17-F/H` (note / inventory), `D-2026-06-18-B/C`.

### D-2026-06-19-A — Services coach content: 5-field interview voiced gently + JTBD technique (no "why", ask "what/how"), feature-proposal + promotion test

- **What:** Services-overview coach content (AI playbook §2.3), grounded in
  value-proposition / JTBD / service-design methods (sources in the playbook):
  1. The 5 inspector fields (`D-2026-06-17-B`) are **labels**; the coach delivers them
     in the §0 gentle tone (`D-2026-06-18-C`) as a top-down interview (intent → 5 fields
     → feature proposal).
  2. **"왜 필요한가?" is elicited via JTBD's rule — do NOT ask "why" directly** (people
     rationalize/мислead on why); ask **what/how about the struggling moment** ("이게
     없을 때 뭘 하느라 답답했나, 마지막으로 안 풀렸던 순간"). "뭐가 좋아지나" = the gain,
     asked concretely from the user's perspective.
  3. **Feature proposal**: once the 5 fields are filled, the coach proposes concrete
     capabilities ("이 안에서 뭘 할 수 있을까요") for the user to pick/confirm.
  4. **Promotion test (feature → service)**: when a feature becomes a *multi-actor
     value exchange*, the coach gently asks whether to promote it to its own service —
     grounded in Novel's own definition (a service = new value via multiple-actor
     interaction, PHILOSOPHY P1/P5). AI may draw the chip reference line (`D-2026-06-17-J`).
- **Why:** AI playbook §2.3 / §3-D (ROADMAP 5.10). User directed grounding the coach in
  expert method (as with Actors). The load-bearing finding: JTBD's "ask what/how, not
  why" both sharpens "왜 필요한가" and reinforces the §0 gentle, non-defensive tone.
- **Alternatives:** (a) ask "why do you need this?" literally — rejected (JTBD: why →
  rationalized, misleading answers). (b) re-list the 5 fields verbatim as the coach
  script — rejected; the fields are inspector labels, the coach voices them per §0 tone.
- **Approval:** Accepted by user, 2026-06-19 ("네 넘어갑시다" after reviewing the draft).
- **Spec impact:** Playbook §2.3 (Services coach content + sources), §3-D agenda. The 5
  fields themselves are unchanged (`D-2026-06-17-B`). No code (prompt wiring = 5.7🅿).
  Builds on `D-2026-06-17-B/D` (5 fields, feature node, promotion), `D-2026-06-18-C`
  (gentle tone), `D-2026-06-18-B` (in-app coach runs design-canvas interviews).

### D-2026-06-18-C — Coach tone-and-manner (gentle, courage + ease) + research-grounded Actors interview question set + Foundation questions re-voiced

- **What:** Three things, all in the per-canvas coach playbook
  ([`AI_CHAT_PLAYBOOK.md`](../../../docs/AI_CHAT_PLAYBOOK.md), now root `docs/`):
  1. **Tone-and-manner principle (§0, ALL canvases):** every coach question must let
     the person speak **with courage, at ease** (용기 내어 여유 있게) — sharp questions
     make people defensively "guess the right answer." Five rules: ① lay out "no right
     answer" first ("막연해도 괜찮아요"), ② one thing at a time with room to think, ③ no
     assertions / interrogation → invitational endings ("~떠오르세요?"), ④ accept before
     correcting (affirm → then gently reframe), ⑤ follow the user's own words (no forced
     jargon).
  2. **Actors interview question set (§2.2)** — was empty (only the actor *model* was
     pinned in `D-2026-06-17-A`). Grounded in established actor/role-identification
     methods (sources in the playbook). Structure mirrors Foundation (발견 → 거르기).
     Research-driven additions vs the naive draft: **separate the "producer" role**
     (who *makes* the core value, distinct from operator and pure consumer — CATWOE's
     doer≠beneficiary≠owner + platform 4-roles), **surface owner/governance + supplier
     + regulator + settlement roles** (stakeholder coverage), and a **role≠persona
     guard** (drift to "a specific person" → reframe to the role).
  3. **Foundation questions re-voiced** to the same gentle tone in
     [`FOUNDATION_CONCEPT.md`](../../../docs/FOUNDATION_CONCEPT.md) (mission +
     core_value). **Substance unchanged** — `D-2026-06-16-K/L` intact; tone only, per
     the user's "모든 질문이 동일[한 톤]".
- **Why:** AI playbook §2/§3-D (ROADMAP 5.10 — define the layer-2 per-canvas coach
  content). User: "질문 좋습니다. 부드럽게 해야해요. 사람들이 자신의 의사를 용기내어서
  여유있게 말할 수 있게" → tone is cross-cutting, so pinned as a §0 common principle and
  applied uniformly to all question sets. The Actors content was the genuine gap; the
  user directed grounding it in how experts actually identify actors ("전문가들이 하는
  방식 ... 논문이나 인터넷 서칭해보면서").
- **Alternatives:** (a) operator/user binary only (naive draft) — rejected: misses the
  producer role (the value-maker, e.g. BANAS hero). (b) tone as Actors-only — rejected:
  user said "모든 질문이 동일", so it is a global §0 principle. (c) re-list Foundation
  questions in the playbook — rejected: playbook §2.1 points to FOUNDATION_CONCEPT (SSOT)
  to avoid duplicate drift; Actors lives in §2.2 (no separate concept doc).
- **Approval:** Accepted by user, 2026-06-18 (substance "질문 좋습니다"; tone directive +
  "모든 질문이 동일[한 톤]").
- **Spec impact:** Playbook §0 (tone), §2.1 (Foundation → SSOT pointer + tone + delivery),
  §2.2 (Actors question set + sources), §3-D (agenda marked progressing). FOUNDATION_CONCEPT
  mission/core_value re-voiced. No code yet (packaging into skill/MCP = ROADMAP 5.7🅿;
  Actors edge model = 5.9). Builds on `D-2026-06-16-H` (active coach), `D-2026-06-18-B`
  (in-app coach runs design-canvas interviews), `D-2026-06-17-A` (actor model).

### D-2026-06-18-B — Per-canvas coach is phase-split: in-app coach runs the design-canvas interviews; the external MCP agent owns execution (resolves §9-E)

- **What:** The "interview-first vs Pencil MCP-first" conflict (BIG_PICTURE §9-E,
  feeds T1/T4) is resolved by **splitting along the VISION phase boundary**, not by
  picking one narrative:
  - **Discovery / Planning (Foundation, Actors, Services design canvases)** → the
    **in-app coach runs the interview directly.** This keeps PRODUCT_SPEC §9's
    "empty canvas → interview → draft → approve" loop for exactly these canvases.
    The in-app chat is **not** merely a thin launcher here; it is the coach.
  - **Execution (actual building / code)** → the **user's external MCP agent**
    (Pencil model). The in-app chat does not try to match an interactive coding
    agent (it structurally can't — `project_chat_architecture`); building is the
    external agent's job, fed by the canvas context envelope (`D-2026-06-17-L`).
- **Why:** AI_CHAT_PLAYBOOK §3-A (the biggest cross-cutting fork — decides whether
  the coach is the *entrance* or a *sidekick*, which gates the F→A→S→feature
  discussion order). The two docs only *appeared* to conflict because both claimed
  the "primary loop"; they are about different phases. Interview is primary for
  authoring the design canvases; the external agent is primary for execution.
- **Alternatives:** (a) Pure thin-launcher / MCP-first — rejected: would push the
  Foundation/Services interview question sets out to an external agent via framing
  only, giving the in-app surface no guided-authoring UX, which is heavier than the
  interview it replaces. (b) Interview-first everywhere (in-app coach owns
  execution too) — rejected: in-app chat is a strict subset of an interactive
  coding agent (`project_chat_architecture`); full parity for *building* is only
  reachable MCP-first.
- **Open (deferred to the `기능` agenda) — ✅ RESOLVED by `D-2026-06-19-B`:** the
  **Feature canvas hand-off point** = the **altitude guard (`D-2026-06-17-G`)**. In-app
  coach owns the behaviour flowchart (at/above user-action altitude = design); the external
  MCP agent owns implementation below it (저장·쿼리·렌더 = execution). No new boundary needed
  — it composes the altitude guard + this entry. (Still relates to agenda B thread keying,
  `D-2026-06-17-D`.)
- **Approval:** Accepted by user, 2026-06-18 (AskUserQuestion — "단계로 나눔" chosen
  over thin-launcher / interview-first).
- **Spec impact:** PRODUCT_SPEC §9 gains a reconciling note (interview loop scoped
  to the design canvases; external agent owns execution). BIG_PICTURE §9-E marked
  resolved + §11 log row. AI_CHAT_PLAYBOOK §3-A resolved.

### D-2026-06-18-A — Hard actor/service count floors relaxed (the ≥2 validators are dropped; count is emergent from the role hierarchy)

- **What:** The pre-marathon hard count validators are relaxed during doc-sync:
  - **actor "≥ 2 per project"** — the hard validator is **dropped.** Under the new
    actor model (`D-2026-06-17-A`) operator/user sit at the top of the role
    hierarchy, so a project naturally carries ≥2 roles; the count is an **emergent
    property** of the hierarchy, not a separately enforced floor.
  - **service "≥ 2 actor_ref (operator included)"** — already loosened to **≥ 1** by
    `D-2026-05-28-K`; the "≥2 with operator" requirement is formally dropped. Under
    `D-2026-06-17-B` the operator is the **default participant** of every service
    ("누가 참여하나?" multi-select), so an explicit ≥2-with-operator floor is
    redundant. The service keeps the current **≥ 1** participant minimum.
- **Why:** Doc-sync of the 2026-06-16~17 marathon (`DOC_SYNC.md` 결정 1). CONCEPTS.md /
  IDENTITY.md still asserted the old ≥2 floors as hard validators, contradicting the
  new role model. The floors are not behaviour the new model needs enforced — they
  fall out of the operator/user hierarchy + operator-as-default-participant.
- **Alternatives:** (a) keep the ≥2 hard validators — rejected (contradicts
  emergent-from-hierarchy; redundant). (b) drop all minimums incl. service ≥1 — not
  taken (a ≥1 named participant is a reasonable floor; revisit only if a real
  zero-participant case appears).
- **Approval:** Accepted by user, 2026-06-18 ("네 제안대로 일단 가봅시다" — provisional).
- **Spec impact:** CONCEPTS.md actor/service baseline lines + IDENTITY.md service
  min-baseline → reworded (no hard ≥2 validator; service ≥1). Resolves `DOC_SYNC.md`
  결정 1. Code-side validator changes (if any) are a separate follow-up.

### D-2026-06-17-L — AI chat context envelope + delivery behind a CAG/RAG seam (CAG-first, any-size user project)

- **What:** The AI chat's per-turn context ("what the AI sees" — playbook layer 1)
  = (1) **active canvas** (full), (2) **current selection** (`D-2026-06-16-F`), (3)
  **upstream-canvas SUMMARY** — the essence + key nodes of the canvases earlier in
  the dependency order (Foundation → Actors → Services → Feature → Entities), **not a
  full dump**, (4) **entity registry** (names + one-line, for strong dedup
  `D-2026-06-17-K`-B2 + references), (5) **deeper detail fetched on demand.**
  Delivery = **CAG-first** (Cache-Augmented): preload the **stable project skeleton**
  as a **prompt-cached prefix**; append the **dynamic** turn data (active-canvas
  detail, selection, user message) as the uncached suffix. **RAG only when scale
  forces it** — if the skeleton exceeds the agent's context window, or deep node
  content / published artifacts / cross-project material must be pulled.
- **Abstraction seam (user, 2026-06-17 — the load-bearing refinement):** delivery
  (CAG vs RAG) sits **behind a context-provider abstraction**; the **playbook depends
  only on the abstraction** ("what the AI sees"), never on the mechanism. Novel's
  **primary path = the user's own external agent (Pencil model)** = **any model**
  (only Opus has a 1M window; most Claude models are smaller) running against a
  **user project of any size** → a 1M-context CAG **cannot be assumed.** The seam
  picks **CAG** (skeleton fits the window) or **RAG** (it doesn't — large user
  project and/or small-window agent), **at runtime.** **Build the seam now + CAG-first
  impl; slot RAG in behind the same seam later (YAGNI).** Because the playbook only
  touches the abstraction, **playbook design continues now**, unblocked by the
  CAG/RAG implementation choice.
- **Why:** Big-picture review, AI playbook §1 (2026-06-17). Everything in the new
  design **references upstream canvases** ("뒤 캔버스가 앞을 참조") and the **entity
  registry** (strong dedup), so the AI must see more than today's active-canvas +
  selection (CHAT_ARCH Layer 2). **The "project" here = the USER's project built with
  Novel, NOT Novel itself — it can be ANY size** (Novel is a general tool: some users'
  projects are tiny, some enormous; Novel can't assume small). So **CAG cannot be
  assumed to fit.** When the user's skeleton fits the agent's window, a cached preload
  (CAG) is simpler / faster / avoids retrieval error; when it doesn't, **RAG is
  required** — RAG-readiness is a real requirement behind the seam, not a distant edge
  case. Prompt caching (Claude) makes the CAG stable-prefix reuse cheap across turns.
- **Alternatives:** (a) full upstream dump every turn — rejected (heavy, costly). (b)
  full RAG / vector store from the start — rejected (YAGNI; CAG covers user projects
  that fit the agent window; build the seam so RAG slots in for large projects /
  small-window models — lighter than committing to graph-RAG-lite, Track 5.4, up
  front). (c) keep today's active-canvas-only context — rejected (AI can't reference
  upstream / dedup). (d) assume CAG always fits — **rejected** (the user's project can
  be any size; Novel can't assume small).
- **Approval:** Accepted by user, 2026-06-17 ("좋아요. 좋습니다." + asked for the
  CAG/RAG judgment → CAG-first).
- **Spec impact:** Extends **CHAT_ARCH Layer 2** — add upstream-summary +
  entity-registry to the context preamble; structure as **cached prefix (stable
  skeleton) + dynamic suffix**. Refines **Track 5.4** ("graph-RAG-lite"): start CAG,
  add RAG-lite only at scale. Core of the **AI chat playbook** (ROADMAP 5.10).
  Implementation follow-up.

### D-2026-06-17-K — Entity open questions resolved (dedup / back-reference / AI-surfacing / inspector)

- **What:** The four open entity questions (`D-2026-06-17-I` §B; B1 already resolved
  by `D-2026-06-17-J`) are closed:
  - **B2 — dedup = fully smart, first-class.** Before creating an entity the AI must
    **strongly semantic-match** the candidate against the existing registry (글 =
    게시물 = 포스트 → **one** entity, never duplicated). Only genuinely ambiguous
    cases go to the user ("이거 기존 '글'과 같은가요?"). **Never silent-merge, never
    silent-duplicate.** This is a **1급 duty of the AI chat playbook** (ROADMAP 5.10).
  - **B3 — back-reference = shown (read-only).** Selecting an entity shows which
    features/actions reference it (글 → "글쓰기 · 글편집 · 글보기에서 쓰임").
    Derived, read-only — core to project-wide management.
  - **B4 — AI-surfacing = in-chat proposal, not auto-scan.** During feature-design
    chat, when an action handles a "thing," the AI proposes the entity ("이건 '글'
    엔티티네요 — 등록할까요?") → user confirms → it registers on the Entities canvas.
    No silent background scan. (Part of the AI chat playbook.)
  - **B5 — entity inspector (when selected) = lean, conceptual.** 이름 + **"무엇을
    담나?"** (one line, rough fields 제목·본문·작성자 — no types/FK) + **어디서
    쓰이나** (B3 back-ref, read-only) + **거친 관계** (rough relationships to other
    entities).
- **Why:** Big-picture review, entity close (2026-06-17). Completes the Entities
  canvas design (`D-2026-06-17-I`). All four follow the project principles: AI
  proposes / user confirms (`D-2026-06-16-P`), high-altitude conceptual (no physical
  schema, D-I), project-wide managed.
- **Approval:** Accepted by user, 2026-06-17 (B2 "완전 똑똑해야죠"; B3/B4/B5 "추천대로
  / 네 좋습니다. 좋아요!").
- **Spec impact:** Resolves `ENTITIES_PLAN.md` §B (B2–B5). **B2 (strong dedup) + B4
  (in-chat surfacing) are core duties of the AI chat playbook** (ROADMAP 5.10); B3/B5
  are entity-inspector content (lock-step with the `entity` kind). **Closes the
  Entities topic** of the big-picture review.

### D-2026-06-17-J — Remove the "all edges are user-drawn / never auto-emit" rule; edges are governed by their definition, not authorship

- **What:** Novel's blanket rule **"All edges are user-drawn / never auto-emit
  edges"** (`D-2026-05-04-A`, SPEC §Edges, `mashbill/CLAUDE.md` during-action rule #5)
  is **removed.** What governs an edge is its **definition (semantics)** — its
  `relation` (flow / injection / inheritance / …) + payload (`directed`,
  `action_verb`, `value_form`, label) — **not who draws it.** The AI **may propose
  / draw edges**, especially on **AI-maintained canvases** (the Entities canvas,
  `D-2026-06-17-I`, where AI surfaces entities **and their relationships**). The old
  rule conflated *ownership* (who draws) with *meaning* (what the edge is); only
  meaning matters. (User: "선에 대한 정의가 제대로 잡혀있으면 이제 크게 문제가
  없습니다.")
- **Why:** Big-picture review (2026-06-17). The original ban (`D-2026-05-04-A`) came
  from v0.13.2 **silently** auto-emitting *uneditable, meaningless* anchor→child
  edges — the real harm was **silent / unowned / uneditable** lines, **not** "AI
  drawing edges." Under the Pencil + AI-maintained-canvas model the AI must be able
  to express relationships (entity ↔ entity, etc.); with a proper edge **definition**
  in place (the v0.30.0 `relation` taxonomy + payload), AI-drawn edges are safe and
  the user can always edit / delete them.
- **Does NOT mandate auto-edges anywhere.** A canvas may still be user-draw-only by
  its own spec — Foundation / Actors / Services keep their current behaviour as a
  **per-canvas choice, not a global law.** Never emit a *meaningless* or
  *silently-uneditable* line (that specific harm stays banned).
- **Alternatives:** (a) keep the blanket ban — rejected (blocks AI-maintained entity
  relationships; conflates ownership with meaning). (b) narrow to "AI proposes, user
  confirms; no silent finalize" — considered; user chose **full removal** ("통째로
  삭제"), with the edge-**definition** requirement as the real guard.
- **Approval:** Accepted by user, 2026-06-17 ("통채로 삭제하세요" + "선에 대한
  정의가 제대로 잡혀있으면 이제 크게 문제가 없습니다").
- **Spec impact:** **Supersedes the blanket-ban portion of `D-2026-05-04-A`** (the
  specific anchor→child auto-edge rejection survives only as a *Foundation-local*
  behaviour, not a global rule). Rewrote SPEC §Edges "Source of edges" + the "Why no
  auto-edges" blockquote; removed `mashbill/CLAUDE.md` during-action rule #5; annotated
  the VISION anti-pattern. **Doc-sync follow-up:** scattered per-canvas "all edges
  user-drawn" mentions (SPEC Foundation/Actors/Services/feature sections,
  ARCHITECTURE no-auto-edge smoke test, CLAUDE.md YAGNI/anti-pattern examples) →
  reword to "edges defined by semantics; per-canvas authorship is a canvas choice."

### D-2026-06-17-I — Entity = project-wide data object on an AI-maintained Entities canvas, born from feature/service design

- **What:** A new **project-level "Entities" canvas** (symmetric to Actors —
  **액터 = 누가 / 엔티티 = 무엇**) holds the product's **data objects** (글 ·
  댓글 · 사용자), **managed project-wide in one place.** **The user does NOT author
  it manually.** Entities are **created by the AI together with the user as a
  byproduct of designing features / services** — when a feature's action produces
  or uses a "thing," the AI surfaces it as an entity and **auto-registers it on the
  Entities canvas.** The user reviews / refines / confirms (D-2026-06-16-P — not
  silent), but never starts from a blank entity canvas. **Bottom-up creation** (in
  feature work) **+ top-down management** (project registry). **Altitude guard:**
  Novel holds only **name + one-line "무엇을 담나"** (rough shape); detailed schema /
  field types / relations / indexes = the user's AI agent's job, **outside Novel**
  (else Novel becomes an ERD / DB-modelling tool — identity violation). Feature
  actions **reference** entities ("발행 → 글 생성").
- **Form — conceptual entity map, NOT a physical ERD (user, 2026-06-17):** these
  are **abstract, pre-normalisation** entities ("정규화 전의 추상적 엔티티"). The
  surface is a **graph/canvas** that may show entities **+ rough relationships**
  (사용자 ─쓴다─▶ 글 ─달린다─▶ 댓글), but **stops at the conceptual level** — no
  normalisation, no foreign keys, no cardinality, no field types. Those (physical
  schema) are the AI agent's job, below the altitude. So it is *ERD-like in shape*
  but explicitly **not a technical ERD**.
- **Sequence:** entities are **populated last** in the design flow — they emerge
  from feature/service work — so the Entities canvas is a **derived surface that
  accumulates at the end** (even though it is managed project-wide).
- **Why:** Big-picture review (2026-06-17). Entities are shared across
  features/services → need one project-wide home; but you don't model them upfront
  — they **emerge from designing behaviour** ("기능 만들면서 엔티티가 만들어진다"),
  and the **AI**, not the user, maintains them. Keeps the value/behaviour-tool
  identity while giving the building AI a clean entity context.
- **Alternatives:** (a) per-service entities — rejected (project-wide). (b) user
  manually authors entities upfront — rejected (waterfall/ERD; they emerge from
  feature work). (c) no surface, AI infers entirely — rejected (user wants them
  explicit + managed). (d) full data-model canvas — rejected (ERD tool, identity
  violation). Re-homes the deleted `content` (D-B/H) at project level,
  AI-maintained, high-altitude.
- **Approval:** Accepted by user, 2026-06-17 ("엔티티는 관리되어야 해요. 전체에서"
  + "캔버스 형태면 좋긴한데 … 사용자가 만들 필요가 없잖아요. AI가 사용자와 같이
  기능을 만들면서 혹은 서비스를 정의하면서 만들어지는 것").
- **Spec impact:** **NEW project-level canvas "Entities" + NEW kind `entity`**
  (lock-step via mashbill-entity-template). AI-maintained / auto-populated from
  feature/service design; user can edit/confirm. A feature `step`/action gains a
  **reference relation to an `entity`**. Implementation + doc-sync = follow-up
  (`ENTITIES_PLAN.md`). **Open:** the AI-surfacing UX (how/when AI proposes an
  entity), the action↔entity reference mechanism.

### D-2026-06-17-H — Feature canvas node inventory: keep step/decision/edge/note/rule/actor_ref; drop the rest

- **What:** The feature canvas (D-2026-06-17-G) holds exactly: **행동 (`step`) +
  분기 (`decision`) + 흐름선 (flow edges) + 노트 (`note`, D-F) + 룰 (`rule`,
  D-E, per-feature) + 액터 참조 (`actor_ref`)**. **Removed** from the old
  Service-Detail set: **`mission_ref` / `value_ref` / `identity_ref`** (already
  held on the service inspector as chips, D-B — the feature *inherits* them;
  duplicating on the canvas is redundant), **`metric`** (not needed), **`content`**
  (implementation artifacts = below action-altitude = AI's job; user-facing
  artifacts are implied by the producing action or carried by the flow edge —
  redundant), **`group`** (its chunking role is now the "feature" level; folding a
  busy flow is a **view affordance, not a node kind**).
- **Why:** Big-picture review, feature-canvas inventory (2026-06-17). Keep the
  behaviour flowchart lean and at action-altitude; everything removed was either
  redundant with the service level, below the altitude (implementation), or
  superseded by the new `feature` concept.
- **Alternatives:** (a) keep refs per-feature — rejected (redundant with service
  inspector). (b) keep metric/content — rejected (not needed / below altitude). (c)
  keep group as a node — rejected (feature replaces its role; folding is a view).
- **Approval:** Accepted by user, 2026-06-17 ("네 빼죠" + "네 일단 정리하시고요").
- **Spec impact:** Feature-canvas allowed-kinds = `step`, `decision`, flow edges,
  `note`, `rule`, `actor_ref`. **MECE / retirement audit (follow-up):**
  `mission_ref` / `value_ref` / `identity_ref` are likely **retired entirely**
  (their job moved to the service inspector chips, D-B); `metric` / `content` /
  `group` removed from their only home (Service-Detail) → likely **retired** too —
  confirm during implementation, each retirement gets its own lock-step + guard
  update. CONCEPTS / SPEC doc-sync. `SERVICES_PLAN.md`.

### D-2026-06-17-G — Feature canvas = a behavior flowchart, at action-altitude, inheriting the service philosophy

- **What:** The feature canvas presents the feature's **concrete behaviour as a
  flowchart** (행동 → 분기 → 결과). This is the **deepest layer only** — Novel's
  upper layers (service / feature value map) stay non-flowchart, so it does **not**
  break IDENTITY.md's "NOT a flowchart tool" (the flow is the floor, not the whole
  building). **Altitude guard:** the flow shows **user actions → branches →
  results** (the behaviour a human designs); it does **NOT** descend into internal
  implementation logic (storage / queries / rendering) — that is the user's AI
  agent's job, **outside Novel**. Crossing that line would make Novel an engineering
  spec tool. The flowchart **inherits the service philosophy** — it is
  **actor-anchored and value-oriented** (the flow is participants doing actions
  that create / exchange value — PHILOSOPHY P5/P6), not a dry abstract diagram.
- **Why:** Big-picture review, feature canvas (2026-06-17). The feature's "how it
  works" needs a concrete, human-readable form so the human can understand + steer
  the AI's draft; a flowchart at action-altitude is that form, and anchoring it to
  actors/value keeps it continuous with the service above it.
- **Alternatives:** (a) prose / form instead of a flowchart — rejected (behaviour
  reads clearest as a flow). (b) full implementation flowchart — rejected (altitude
  guard: that is the AI agent's job, breaks identity). (c) abstract boxes, no actor
  anchor — rejected (loses the service philosophy).
- **Approval:** Accepted by user, 2026-06-17 ("서비스의 철학을 이어받아서 정리가
  되어야겠죠. 물론." + altitude agreement).
- **Spec impact:** Confirms the feature canvas (old Service-Detail) as an
  actor-anchored behaviour flowchart. Nodes: 행동(step) + 분기(decision) +
  흐름선(flow edges) + 노트(D-F) + 룰(D-E, per-feature). Old detail's remaining
  kinds (refs / metric / content / group) — **fit-to-flowchart = open** (node
  inventory follow-up). Existing actor-anchored ServiceDetail layout already
  matches; doc-sync + the feature-rename are follow-ups (`SERVICES_PLAN.md`).

### D-2026-06-17-F — `note` node: edgeless, canvas-global context on the feature canvas

- **What:** A new **`note` node** lives on the feature canvas (the old
  service-detail). It carries **no edges** — it never connects to other nodes —
  and applies to the **entire canvas globally** (an ambient context/memo for
  everything on that canvas, e.g. "이 기능은 모바일 우선 · 본문 500자 제한"). It
  is **read by the human** (guidance) **and is always-on context the AI takes into
  account** when it designs / proposes on that canvas (the canvas is a co-design
  surface — D-2026-06-16-P). Introduced on the **feature canvas now**; reusable to
  other canvases later **if** a need shows (not forced everywhere — YAGNI). One or
  more allowed; each applies globally.
- **Why:** Big-picture review, Services overview → feature canvas (2026-06-17).
  Even when the AI can draft a feature, the human must understand + steer, and some
  context applies to the **whole feature** rather than one node. An edgeless,
  canvas-global note pins that without wiring it to every node. Edgeless because it
  is **ambient**, not a participant in the flow.
- **Alternatives:** (a) attach context to each node via edges — rejected (it is
  canvas-wide, not node-specific). (b) reuse a regular `content` node — rejected
  (content is a node among others in the flow; the note is deliberately
  edgeless + global). (c) human-only memo — narrowed (it is also AI context, since
  the canvas is co-designed).
- **Approval:** Accepted by user, 2026-06-17 ("기능 캔버스에 노트 같은 걸 하나 …
  연결선 없이 그 캔버스 전역에 영향" + "노트 노드"). Dual human+AI purpose and
  feature-canvas-first scope were assistant-proposed defaults, open to correction.
- **Spec impact:** **NEW kind `note`** — lock-step via mashbill-entity-template, with
  an **edgeless invariant** (never gains an edge) + canvas-global semantics + an
  AI-context hook (the note is injected into the per-canvas AI framing). On the
  feature canvas for now (extensible). Implementation = follow-up (`SERVICES_PLAN.md`).

### D-2026-06-17-E — Operational rules live inside each feature (provisional); "policy" = a concrete constraint, not identity

- **What:** Operational rules / constraints — e.g. "password must be ≥ N chars",
  field validation, limits — live **inside each feature's canvas** (the feature
  detail), **per feature.** This is **provisional** ("일단 / 가장 확실"): how a
  genuinely **cross-cutting** policy (spanning multiple features or services)
  should be modelled is unknown, so it is **not built yet** (YAGNI). No separate
  "policy" kind, no service-level rule home for now — revisit only when a concrete
  cross-cutting constraint actually shows up.
- **Clarification (user correction):** "정책 / policy" here means a **concrete
  operational/functional constraint** (password length, validation, limits) — it
  is **NOT** related to identity or core_value. The assistant's earlier "policy ≈
  identity cousin" framing was **wrong** and user-corrected. This anchors the
  existing `rule` kind as a per-feature operational constraint, plainly distinct
  from identity (brand voice / expression) and core_value (tie-breaker value).
- **Why:** Big-picture review, Services overview (2026-06-17). The cross-cutting
  case ("모든 글은 검수를 거친다") is real but its home is unclear; forcing a new
  policy concept now would be premature. Per-feature rules are the most certain
  placement today.
- **Alternatives:** (a) service-level rules — deferred (only needed once a
  cross-service policy appears). (b) standalone referenced "policy" kind —
  deferred (new kind + reference machinery, premature). (c) policy in Foundation
  beside value/identity — **rejected (user, 2026-06-17): Foundation holds the
  stable essence (mission/value/identity — the anchor that must not drift), but a
  policy changes frequently ("수시로 바뀔 수 있어서"). Putting a volatile
  operational rule into the stable anchor pollutes it.** A password rule is
  operational, not a project-wide commitment, and not identity.
- **Approval:** Accepted by user, 2026-06-17 ("일단은 각 펑션에 넣습니다 … 이게
  지금으로서는 가장 확실해요").
- **Spec impact:** Closes the rule-placement question raised under D-2026-06-17-D.
  `rule` kind stays per-feature (operational). Cross-cutting policy = parked
  (ROADMAP). Revisit trigger: a constraint that genuinely spans features/services.

### D-2026-06-17-D — Services overview gains a "feature" node; service shows inspector, feature drills to detail

- **What:** The Services overview canvas holds **three node kinds** (+ the project
  anchor): **category** (visual grouping only — "무지성" low-friction, no value),
  **service** (value description, the 5-field inspector from D-2026-06-17-B), and a
  **NEW `feature` node nested under a service** (a capability the service offers —
  글쓰기 / 글편집 / 이모지 반응 …). **Selecting a service shows its 5-field
  inspector — it no longer drills.** **Clicking a `feature` opens what is today the
  Service-Detail canvas** (that feature's actions/rules) — the feature is the
  **drill target**, so the current "service detail" becomes effectively "feature
  detail." Hierarchy: **카테고리 → 서비스 → 기능** (overview) → **행동 / 룰**
  (detail). Built top-down by AI interview: rough intent → service (5-field
  interview) → **AI-proposed features (human confirms)**; a proposed feature that
  turns out to carry its **own multi-actor value exchange is promoted to a
  service** (the value-exchange test).
- **Why:** Big-picture review, Services overview (2026-06-17). 글쓰기/편집/삭제 등은
  서비스가 아니라 서비스가 제공하는 **능력(기능)**. A service = value description;
  features = capabilities under it; actions/rules = inside a feature (detail). The
  three-tier shape (service / feature / action) is the same decomposition found in
  activity→action→operation, story-map activity→task→detail, and JTBD job→feature
  — levels distinguished by **동기 / 목표 / 조건**, not by size.
- **Alternatives:** (a) keep service as the drill target, no feature layer —
  rejected (features are real units between service and steps). (b) features as
  sub-services on the overview — rejected (resurrects the removed sub-service;
  features aren't multi-actor value exchanges). (c) reuse `group` for features —
  superseded (feature = the named capability; `group` = visual fold, to be
  re-audited/retired). (d) fully recursive value-node — rejected (unbounded
  nesting; Novel's sub-service lesson + JTBD over-granularity warning).
- **Approval:** Accepted by user, 2026-06-17 ("네 맞아요!").
- **Spec impact:** **NEW kind `feature`** — full lock-step via mashbill-entity-template
  (domain class, Pydantic model, node renderer, inspector, i18n, schema-parity,
  structural guards). Overview allowed-kinds += `feature`; **drill rewires**
  (service = inspector only; feature = drill to detail) — supersedes the
  service-as-detail-subject drill (D-2026-05-28-B + D-2026-06-15-H drill portion).
  `group` MECE re-audit. CONCEPTS / SPEC doc-sync. All implementation =
  follow-up (`SERVICES_PLAN.md`). **Open:** the `feature` node's own inspector
  content when selected (leaning small inspector = name + action summary).

### D-2026-06-17-C — No first-class service→service edge on the Services overview (drop "user journey" edges)

- **What:** The Services overview has **no first-class service→service edge
  concept.** The previously-specced **"Service-to-service edges = User journey"**
  (PRODUCT_SPEC §7) is **dropped** — Novel will not build journey / value-flow
  edge semantics between services. The overview is about **each service's own
  definition** (D-2026-06-17-B: 누가·왜·뭐가 좋아지나 + 작동 코어밸류/아이덴티티),
  not about wiring services together. (Generic user-drawn edges remain technically
  possible per the "all edges are user-drawn" rule, but carry no special
  inter-service meaning and are not a provided/encouraged feature; revisit only on
  a concrete need — YAGNI.)
- **Why:** Big-picture review, Services overview §S2 (2026-06-17). A
  service→service line could only mean (a) **순서/여정** — but that is per-actor
  (different participants take different paths) and turns the overview into a
  flowchart, which fights IDENTITY.md ("NOT a diagram / flowchart tool"); (b)
  **가치 흐름** — already captured at the **role level** (Actors relationship
  edges, D-2026-06-17-A) and **per-participant** (`actor_ref` on Service-Detail),
  so a third rendering is redundant (MECE); (c) **의존** — too niche to elevate.
  User confirmed the doubt: "서비스 간의 선은 없애죠."
- **Alternatives:** (a) build "user journey" edges per PRODUCT_SPEC §7 — rejected
  (flowchart, fights identity). (b) build "value-flow" edges — rejected (redundant
  with actor / actor_ref value flow). (c) keep as a special optional edge type —
  rejected (YAGNI; no concrete need named).
- **Approval:** Accepted by user, 2026-06-17 ("ㅇㅋ 서비스 간의 선은 없애죠").
- **Spec impact:** **Retire / rewrite PRODUCT_SPEC §7** "Service-to-service edges
  = User journey" + the §8 row 3 "user-journey edges" mention (doc-sync follow-up).
  Closes big-picture review **§S2**. With D-2026-06-17-B, the **Services overview
  topic is fully resolved.**

### D-2026-06-17-B — Services-overview service inspector = 2 typed + 3 selectable references; old service text fields deleted

- **What:** The Services-overview **service inspector** is redefined to **5
  question-titled fields**, in order — (1) **"누가 참여하나?"** selectable
  **actor** references, (2) **"왜 필요한가?"** typed (the gap/need the service
  fills — renames + reframes the old `problem`, dropping the negative "문제"
  framing), (3) **"뭐가 좋아지나?"** typed (the improvement it creates — renames
  `value_created`), (4) **"뭘 양보 못 하나?"** selectable **core_value**
  references, (5) **"어떤 결로 다가가나?"** selectable **identity** references.
  Field titles are **question-form** so each doubles as the AI interview prompt
  (D-2026-06-16-P — everything built through discussion). Core values and
  identities are **picked from the Foundation canvas exactly like actors** (chips,
  not free-typed) — the "뒤 캔버스가 앞을 참조" principle. **All three reference
  pickers are multi-select** (복수 선택): one service can hold several actors,
  several core_values, and several identities (rendered as multiple chips). The old service text
  fields — **`what`, `scope`, `trigger`, `how`, `outcome`, `do`, `dont`** — are
  **DELETED (not moved to detail):** their substance already lives on the
  Service-Detail canvas as nodes (`step` = "how", `rule` = "do/dont") and the
  **per-participant behaviour** (하는 일 / 받는 것 / 페인 — which varies per
  participant) lives on each **`actor_ref`** on the detail canvas, not as a flat
  service field. Also deleted: **`target_side`** (redundant — participants are now
  shown directly via "누가 참여하나?", and each actor carries its own side) and
  **`body`** (free memo — the 5 structured fields replace it).
- **Why:** Big-picture review, Services overview (2026-06-17). 9 typed fields made
  the overview heavy and duplicated detail-canvas nodes. A service = where
  participants interact and value arises (user) → the overview should show **who
  participates + why-needed + what-improves + which foundation values/identity
  operate**, with the upstream concepts as **references** and the per-participant
  detail pushed inside.
- **Alternatives:** (a) keep the 9 fields — rejected (heavy, duplicates detail).
  (b) move old fields to detail instead of deleting — **rejected by user**
  ("옛것들 다지워야죠"); detail nodes + `actor_ref` already cover them. (c)
  free-type core value / identity — rejected; they are references picked from
  Foundation, like actors. (d) title "푸는 문제" / "목적" — rejected (too
  negative / too stiff); question-form "왜 필요한가?" chosen.
- **Approval:** Accepted by user, 2026-06-17 ("네네 맞아요. 좋아요. 굿" +
  "옛것들 다지워야죠").
- **Spec impact:** Replaces the v0.12 "Service typed fields" set in CONCEPTS.md +
  the SPEC service inspector. **Follow-ups (not this turn):** doc-sync
  (CONCEPTS / SPEC), and code (Service domain class, Pydantic model, service
  inspector — typed×2 + reference-picker×3, i18n, schema-parity, structural
  guards) — logged in ROADMAP. `target_side` + `body` deletion **confirmed by
  user 2026-06-17** ("누구쪽 없애고 새롭게 정의한거 씁시다. 그리고 자유 메모
  없애요"). Builds on D-2026-06-15-K (`problem`), D-2026-06-15-J
  (`actor_ref` per-service stake), D-2026-06-16-P (build-through-discussion).

### D-2026-06-17-A — Actor = a relational role in a hierarchy; two edge types on the Actors canvas

- **What:** An **actor = a role / class of participant** in the service's value
  economy — defined by position and resources, **not a person / persona** (no demographics; one person can
  occupy several actor-roles, and roles can switch). Every actor both **gives and
  receives** value. Actors form a **hierarchy (tree)**: the top split is operator vs
  user (`side`), inherited down to child roles (user → hero, fan; operator →
  super-admin, manager) — actor inheritance is **core, not optional**. A role is
  **relational** (a role alone is meaningless), so the **Actors canvas shows
  relationships** and carries **two distinct edge types** that must never be
  confused: (1) a **hierarchy edge** ("is-a-kind-of") — structure only, no value, a
  quiet line; (2) a **relationship edge** ("gives value to") — a **directed,
  labelled arrow** carrying *what value flows from which role to which* (hero
  →expertise→ fan); a reciprocal relationship is **two arrows** (hero →expertise→
  fan; fan →support→ hero). The Actors canvas shows the **general / role-defining**
  value flow; the **concrete per-service exchange** (specific value, steps, metrics,
  motivation/pain) lives in **Service-Detail** (`actor_ref`). Two levels: abstract
  (Actors) → concrete (Service-Detail).
- **Why:** Big-picture review, Actors (2026-06-17). User: roles are hierarchical
  (operator/user at top, specific roles below) and relational (cannot be a role
  alone). The current model already matches — actor is identity-only (`side` +
  `body`) with inheritance; per-service stake (gives/receives, motivation/pain) is
  on `actor_ref` (PHILOSOPHY P3 — participation is asymmetric, varies per service).
- **Alternatives:** (a) actor = a person/persona — rejected (it's a role). (b)
  inheritance is YAGNI — rejected (hierarchy is core). (c) relationships only in Services
  (Actors = cast + hierarchy) — **rejected**; a role's defining relationship is
  service-independent and must show on Actors (the concrete per-service exchange
  still lives in Service-Detail). (d) one bidirectional edge with two labels —
  rejected for two directed arrows (clearer "from where to where").
- **Approval:** Accepted by user, 2026-06-17 — role + hierarchy + two-edge-type
  design ("이거 기술적으로 잘 만들어야합니다. 좋습니다").
- **Spec impact:** Node/inspector unchanged (label + `side` + body + inheritance).
  **Edge work IS needed** — render two visually-distinct edge types on Actors
  (hierarchy vs value-carrying relationship arrow; relationship edges carry value +
  direction; reciprocal = two arrows). Logged in ROADMAP. CONCEPTS.md / SPEC Actors
  section to be brought current (doc-sync follow-up). Builds on D-2026-06-15-J (actor
  identity-only) + actor_ref per-service stake.

### D-2026-06-16-R — F4 resolved: Foundation stays a single canvas (no audience split)

- **What:** Foundation remains **one canvas** holding mission + core_value +
  identity together. The proposed audience split (mission/core_value for humans,
  identity for the agent) is **rejected**.
- **Why:** Big-picture review F4 (2026-06-16). D-2026-06-16-Q makes it decisive: the
  essence is the **emergent composition** of the three concepts around the anchor —
  splitting them across canvases would break that single visual statement ("our
  service = this mission + this core_value + these identities"). Also, identity is
  now a brand voice (D-2026-06-16-N, F3 reframe) that humans read too, so the
  "agent-only surface" rationale no longer holds.
- **Alternatives:** (a) split Foundation by audience — rejected (breaks the
  composition; identity is no longer agent-only).
- **Approval:** Accepted by user, 2026-06-16 ("단일 캔버스죠. … 맞아요. 시각적 묶음! 근본!").
- **Spec impact:** Resolves big-picture review **F4**. **Closes the §1.5 Foundation
  review (F1–F4 all resolved).** No code change — Foundation is already a single canvas.

### D-2026-06-16-Q — F2 resolved: essence is the emergent Foundation composition, not a node; anchor = name only

- **What:** Foundation needs **no separate "essence (본질)" node**. The essence is
  the **emergent whole** of the three Foundation concepts — "our service is made of
  *this* mission + *this* core_value + *these* identities" — and its irreducible core
  is **mission** (the root of existence). The essence has **no dedicated container**
  (neither a node nor text on the anchor); to read the one-line essence, read the
  mission node. The essence is conveyed **visually by the composition itself** (the
  three concepts arranged around the project centre) — that arrangement *is* the
  statement of what the service is. The **project anchor carries only the project /
  service name** — it is a **visual-grouping device**, not a content holder.
- **Why:** Big-picture review F2 (2026-06-16). Essence is a *whole*, so a sibling
  node would demote the whole to a part. mission already carries its core
  (D-2026-06-16-K = "존재의 뿌리"). The anchor's job is visual cohesion (Retention —
  the project stays centred/visible); putting essence text on it misuses a visual
  device. Making "service = these concepts" legible is a *visualisation* job for the
  Foundation canvas, not a new node.
- **Alternatives:** (a) a dedicated essence node — rejected (whole-as-part). (b) a
  one-line essence on the anchor — rejected (anchor = visual grouping, not content).
- **Approval:** Accepted by user, 2026-06-16.
- **Spec impact:** Resolves big-picture review **F2**. Anchor stays name-only
  (affirms SPEC §Anchor — no content fields added). Feeds the Foundation-canvas
  visualisation topic (the composition must be legible). §1.5 remaining: **F4** only.

### D-2026-06-16-P — Everything in Novel is created through discussion (AI coach + human confirm), never silent

- **What:** The universal interaction model: **every concept / node on every canvas
  is created through discussion** — the AI is an active coach that interviews /
  proposes, and the human reviews, refines, and confirms. This holds for input kinds
  (the user brings raw material, the AI questions and shapes — discover→filter) and
  output kinds (the AI drafts first, then discusses and the user confirms — e.g.
  identity). **Two anti-modes are excluded:** (1) a lonely **blank form** the user
  fills with no AI, and (2) **silent auto-generation** the AI commits without the
  user. The human always retains direct control (can edit any line directly —
  PHILOSOPHY co-drawing) and is always the confirmer.
- **Why:** User principle (2026-06-16): "모두 모두 토론을 통해서 만들어지는 거에요."
  Generalises D-2026-06-16-H (per-canvas active coach) and D-2026-06-16-I (Novel = AI
  builds context + human reviews) into one rule, and matches FOUNDATION_CONCEPT's
  "채우는 방식 = AI 대화창(인터뷰)" — now scoped to *all* canvases, not just
  Foundation. It is the through-line of today's whole Foundation discussion.
- **Alternatives:** (a) blank-form data entry — rejected (the Notion-like form the
  VISION reframe moved away from). (b) silent AI auto-fill — rejected (violates
  human-in-the-loop, D-I).
- **Approval:** Accepted by user, 2026-06-16 ("맞죠?" — affirmed).
- **Spec impact:** Novel-wide principle; concretely realised by the per-canvas coach
  guides + interview question sets (skill, ROADMAP 5.7). FOUNDATION_CONCEPT "Novel
  작동 전제" already states it for Foundation; this lifts it to a Novel-wide rule.

### D-2026-06-16-O — identity inspector = name + action-rule list now; output-metadata deferred to the derive flow

- **What:** The identity inspector is reduced to **two items now — name (`label`) +
  the action-rule list** (the rules are the content; `description` is dropped,
  folding into the rules). The output-model fields **`status` and `provenance` are
  deferred** until the AI-derive flow exists (ROADMAP 5.7): both are inert today (no
  producer auto-sets `derived`/`confirmed` or auto-fills provenance; hand-typing
  node ids is the wrong UX). `evolution` stays covered by git/version.
  **Clarification:** identity being "AI-derived" does **not** mean silent
  auto-generation — the AI drafts the first rules from mission + core_value, then
  **interviews / discusses** with the user to refine, and the user confirms. (That
  derive → discuss → confirm loop is exactly what `status` will track once the flow
  ships.)
- **Why:** Big-picture inspector review (2026-06-16). `status`/`provenance` were
  built ahead of their workflow (v0.44.0) and are confusing while inert — the user,
  designing it, could not tell what `status` was (the Don't-Make-Me-Think signal).
  YAGNI: surface them when the derive flow gives them meaning. For now identity
  matches mission/core_value (name + body→rules). The "derived is still a
  discussion, never silent" point keeps identity inside the human-in-the-loop
  principle (D-2026-06-16-I).
- **Alternatives:** (a) keep status/provenance now — rejected; inert + confusing.
  (b) keep description + body separate — rejected; same redundancy as core_value (D-M).
- **Approval:** Accepted by user, 2026-06-16 ("좋습니다").
- **Spec impact:** viewer identity inspector (drop `description`; render rules list;
  remove status/provenance inputs for now) + `Identity.ts` are a TDD follow-up.
  status/provenance return with ROADMAP 5.7 (AI-derive interview). Completes the
  Foundation node/inspector pass (mission J / core_value M / identity O). Pairs with
  D-2026-06-16-N.

### D-2026-06-16-N — identity definition: standing execution/expression rules (not value-conflict judgment)

- **What:** identity = the service's **consistent execution / expression standards,
  captured as action-rules** ("we design / speak / behave like ~") that accumulate
  into the service's character. It is **not** value-conflict judgment: core_value
  resolves *which value wins when goods conflict* (a conflict-triggered tie-breaker),
  while identity rules are **always-applied standing standards** for how every
  output looks, sounds, and behaves (e.g. "design = vivid, appetising"). If the two
  ever collide, core_value adjudicates (it is the tie-breaker by definition). The
  per-service `rule` kind is different again (operational policy / SLA). identity is
  an **output** kind — AI-derived from mission + core_value (+ accumulated behaviour)
  and evolving.
- **Why:** Big-picture discussion (2026-06-16), research-grounded. The user reframed
  identity from abstract personality to executable action-rules; validated by
  identity-as-practice scholarship (identity is enacted through "doing," not "being"
  — Oliver & Vough 2020; Brown 2022) and brand-voice practice (personality is
  operationalised as Do/Don't rules; Aaker 1997's five dimensions are the *summary*,
  the rules are the usable form). Fluid/evolving identity is the adaptive norm
  (Gioia, Schultz & Corley 2000). The action-rule form is also exactly what an
  external agent can match — resolving F3 (identity under the Pencil model = a brand
  voice anyone's agent can match, not an embedded persona).
- **Alternatives:** (a) identity = abstract brand personality (adjectives) —
  rejected; not executable, and action-rules are what agents/teams actually use.
  (b) fold identity into core_value — rejected; identity is standing expression,
  core_value is conflict judgment — different jobs (MECE).
- **Approval:** Accepted by user, 2026-06-16 ("좋아요. 멋져!").
- **Spec impact:** FOUNDATION_CONCEPT.md identity section rewritten. Resolves
  big-picture review **F3**. Next: identity node/inspector reviewed as an
  **action-rule list (facet)** model (current inspector = label + description + body
  + status + provenance — to reconcile). Feeds the interview-skill (ROADMAP 5.7).

### D-2026-06-16-M — core_value node collapses to name (label) + body (no separate definition)

- **What:** The core_value entity's three editable text slots (`label` +
  `definition` + `body`) collapse to **two — the value's name (`label`) + `body`**.
  The separate `definition` field is removed (folded into `body` on read). The
  inspector shows **name + body**, where body carries the value's meaning *and the
  trade-off it makes* (what it chooses / what it sacrifices). The node chip keeps
  showing the name — unchanged.
- **Why:** Big-picture inspector-items discussion (2026-06-16). Same 3-slot
  redundancy as mission (D-J), but the redundant pair differs: for mission it was
  label ≈ statement (both the one sentence); for core_value the name (`label`) and
  the meaning are genuinely distinct, so the redundant pair is **`definition` vs
  `body`** (both explain the value). The name is load-bearing — it is referenced in
  decisions ("by '관용과 지지' we…") — so it stays; the overlapping `definition`
  goes.
- **Alternatives:** (a) copy mission's fix verbatim (merge label + definition) —
  rejected; name and meaning are not duplicates for a value. (b) make core_value a
  single decision-principle declaration like mission — rejected; a value needs a
  short, referenceable name distinct from its full meaning.
- **Approval:** Accepted by user, 2026-06-16 ("네 그렇게 두 개로 합시다").
- **Spec impact:** CONCEPTS.md core_value fields + SPEC.md to be brought current;
  viewer `CoreValue.ts` (drop `definition`, fold to body) + core_value inspector +
  migration are a TDD follow-up (code unchanged today). Mirrors D-2026-06-16-J
  (mission). Pairs with D-2026-06-16-L (core_value concept).

### D-2026-06-16-L — core_value definition + Foundation "discover → filter" interview structure

- **What:** Two things. **(1) core_value** = the value that *wins when decisions
  conflict* — the decision criterion you actually run on *now* (not the
  future-facing identity). **(2)** Every Foundation concept's interview runs in
  **two stages — Discovery → Refinement — grounded in the user's concrete service
  intent**, not abstract values talk. For core_value: *Discovery* surfaces
  candidates from the decisions the intended service will force (frequent decisions
  → instinctive lean → what you'd reject that competitors accept); *Refinement*
  filters candidates by three tests: forces a trade-off (Schwartz 1992), held even
  at a competitive disadvantage (Collins & Porras; Lencioni's core vs
  permission-to-play), and lived not merely espoused (Bourne & Jenkins 2013).
  **Mission is refined to match** — its interview now leads with Discovery (what
  change / for whom / why-you-now) before the sustainability filter.
- **Why:** User insight (2026-06-16): the quality tests answer "what should a core
  value be *like*?" but skip the prior question — "what could even *be* my values?"
  Discovery must precede filtering, and values are not invented in a vacuum; they
  are excavated from the service you intend to build. Abstract "what are your
  values?" yields decoration ("integrity"); decision-grounded discovery yields real
  candidates. The structure generalises across Foundation.
- **Alternatives:** (a) keep only the quality filter — rejected; no way to
  *generate* candidates. (b) discover values abstractly — rejected; yields generic,
  non-deciding values.
- **Approval:** Accepted by user, 2026-06-16 ("네. 미션도 잘 다듬어주고요").
- **Spec impact:** FOUNDATION_CONCEPT.md core_value section rewritten (2-stage) +
  mission section reordered (discovery-first); refines D-2026-06-16-K. Feeds the
  interview-question-set skill (ROADMAP 5.7). Identity likely differs (it is
  AI-*derived*, not user-input) — to confirm when identity is reviewed.

### D-2026-06-16-K — Mission definition: root change + sustainability test (theory-grounded)

- **What:** "What a mission *is*" is defined as: **the fundamental change the
  service intends to make for the world / its people (the root of its
  existence)** — a Massive Transformative Purpose. Its decisive test is
  **sustainability**, with two engines: **(a)** it solves a *recurring* problem
  (demand never dries up — Jobs-to-be-Done) and **(b)** it delivers *value that did
  not exist before* (hard to replace — Value Innovation / Blue Ocean, = PHILOSOPHY's
  "value that didn't exist"). Its success state is when the innovation **becomes
  everyday** (absorbed into the culture — Rogers' Diffusion of Innovations). This
  yields the **mission interview question set**: (1) Does this problem keep
  recurring? (2) Is this value new to the world? (3) How does the world change once
  it's everyday?
- **Why:** Big-picture discussion (2026-06-16), research-informed. The user's
  framing maps onto established strategy / innovation theory; naming it sharpens the
  definition and gives the AI a concrete, defensible interview. The question set is
  the operational form of D-2026-06-16-H (per-canvas active coach), mission edition.
- **Alternatives:** (a) mission = "왜 존재하는가" alone — kept but judged too soft
  (answerable at feature level); the sustainability test was added to force depth.
  (b) leave it untheorised — rejected; the user asked for grounding, and the AI
  coach needs explicit criteria.
- **Approval:** Accepted by user, 2026-06-16 ("매우 좋아요").
- **Spec impact:** FOUNDATION_CONCEPT.md 미션 section enriched. The interview
  question sets across Foundation kinds are to be packaged as a **skill / MCP
  prompt** (the active-coach implementation) — logged as a deferred (🅿) item in
  ROADMAP. Pairs with D-2026-06-16-H / J. Refined by D-2026-06-16-L (interview
  reordered to discovery-first).

### D-2026-06-16-J — Mission node collapses to a single declaration + body (no separate label/statement)

- **What:** The mission entity's two short text slots (`label` + `statement`)
  collapse into **one declaration field** — the single one-sentence statement that
  *is* the node's primary text on the canvas — plus the free-form `body`. The
  mission inspector then shows exactly: **declaration (one sentence) + body**.
- **Why:** Big-picture inspector-items discussion (2026-06-16). Lens: each
  inspector item must earn its place by helping **define** the concept (= good AI
  context + human clarity). A mission is one indivisible declaration
  (D-2026-06-06-C); two short fields made the user hesitate ("where do I write
  it?") — a Don't-Make-Me-Think violation — and `label` as a separate slot is just
  a canvas handle, redundant with the declaration. `label` stays the right "name"
  slot for kinds whose content is a name (actor / service); mission is special
  because its content *is* a sentence.
- **Alternatives:** (a) keep label + statement separate (label = short nickname,
  statement = sentence) — rejected; a mission has no useful nickname distinct from
  its declaration. (b) drop label entirely — rejected at the data layer (every node
  needs a label for the chip + references); instead the single declaration
  populates `label`, and legacy `statement` folds into it (or into `body`) on read.
- **Approval:** Accepted by user, 2026-06-16 ("받아들입니다").
- **Spec impact:** CONCEPTS.md mission fields + SPEC.md Foundation/mission inspector
  to be brought current in the T3 doc-sync; viewer `Mission.ts` + mission inspector
  + migration are a TDD follow-up (code unchanged today). Pairs with D-2026-06-06-C.
  Likely applies to core_value / identity too — **not decided here** (separate
  per-node review).

### D-2026-06-16-I — VISION essence sentence reframed to Novel's purpose (AI context + human acceleration)

- **What:** The VISION first sentence (the essence) is rewritten to: **"Novel is a
  collaboration tool where a person and AI together structure and define a
  service's essence and concepts — so the AI works better on that shared structure,
  and the person thinks faster and deeper."** The three-phase cycle (Discovery →
  Retention → Execution) is unchanged and becomes the *how* under this purpose.
- **Why:** Big-picture discussion (2026-06-16). The user reframed Novel's purpose:
  Novel builds good **context for the AI to work well** and **accelerates the
  human's thinking** (with human review). The canvas — structured concepts + their
  definitions / relationships — is the single artefact that delivers both. The old
  sentence cast the human as a solo essence-seeker and a typed form as the surface;
  the new one names the actual job. Pairs with D-2026-06-16-H (per-canvas active
  coach).
- **Alternatives:** (a) keep the old sentence, add the purpose elsewhere — rejected;
  the essence sentence is the override-everything anchor, so it must carry the
  purpose. (b) drop essence/"본질" from the sentence — rejected; essence stays a
  central concept (its first-class status is open as F2). (c) replace the
  three-phase cycle too — rejected; the cycle is the still-valid workflow.
- **Approval:** Accepted by user, 2026-06-16 ("박으세요").
- **Spec impact:** VISION.md essence sentence + English mirror rewritten; three-
  phase cycle section unchanged. Downstream docs (PRODUCT_SPEC §9 interview-first,
  PHILOSOPHY) to be reconciled as the big-picture review continues.

### D-2026-06-16-H — Each canvas's chat is an active discussion coach, not a passive topic-setter

- **What:** Each canvas's in-app chat carries an **active** per-canvas guide that
  shapes the user's own AI into a high-level discussion partner for that canvas's
  job: (1) organise that canvas's concepts and their relationships, and (2) propose
  higher-order concepts / methodologies the user has not considered. This
  **strengthens CHAT_ARCH Layer 3** from a passive topic-setter ("Help surface the
  essence") to an active coach. The AI remains the user's **external** agent
  (Pencil model); Novel shapes its behaviour through the per-window guide, not by
  owning the model.
- **Why:** This session's big-picture discussion (2026-06-16) reframed Novel's
  purpose: Novel builds good **context for the AI to work well** and **accelerates
  the human's thinking** (with human review). The canvas — structured concepts +
  their definitions / relationships — is the single artefact that serves both. For
  that to hold, the per-canvas AI must actively organise concepts and propose what
  the human missed, not hand over a blank form.
- **Alternatives:** (a) one generic chat guide across all canvases — rejected; each
  canvas has a different job. (b) keep Layer 3's weak topic-setter framing —
  rejected as too passive. (c) build the AI into Novel — rejected; contradicts the
  pinned Pencil model (AI is the user's external agent).
- **Approval:** Accepted by user, 2026-06-16.
- **Spec impact:** CHAT_ARCH.md Layer 3 (design intent strengthened). SPEC.md R7
  unchanged until implemented — today's in-app framing is still the weak
  topic-setter; the active-coach guide is a named follow-up.

### D-2026-06-16-G — Chat is scoped to the active project (× canvas), not the whole workspace

- **What:** `ChatDock` is now keyed on the **active project's path**
  (`activeProjectPath`) instead of the workspace root. So the chat's threads,
  provider, and model are **per-project × per-canvas** — switching projects in
  a monorepo workspace switches the chat to that project's `.noory/plot`. The
  engine already keys sessions on the resolved `plot_root`; the viewer just
  sends the project path now (previously the workspace/monorepo root, frozen
  at mount via `useMemo(resolveWorkspaceRoot, [])`).
- **Why:** user (2026-06-16) — "채팅 창은 프로젝트에 싱크되어야 합니다. 내가
  어떤 프로젝트인지, 프로젝트에서 어떤 캔버스에 있는지로 싱크돼야 해요." The
  chat was workspace-wide, so it didn't follow the active project.
- **Alternatives:** add a project dimension to the wire `scope` instead of
  re-keying the path — rejected; the per-project `.noory/plot` already IS the
  natural boundary (each project owns its chat config + history), so keying on
  the project path is simpler and consistent with the rest of the app
  (canvases already load per `activeProjectPath`).
- **Approval:** Accepted by user, 2026-06-16 (requested).
- **Spec impact:** updated [`SPEC.md` → R7 chat](./SPEC.md) Provider-selection
  + Conversation-scope rows + [`CHAT_ARCH.md`](./CHAT_ARCH.md). Guarded by
  `viewer/tests/chat-selection-detail.test.ts`.

### D-2026-06-16-F — Chat selection context works on the service-detail canvas

- **What:** The service-detail `<ServiceDetailCanvas>` now reports its node
  selection up via `onSelectionChange`, and the `ChatDock` selection prop
  reads the **active detail canvas's** nodes (not just the main canvas). So
  while editing inside a service-detail canvas, the chat's per-turn selection
  context (Layer 2) resolves "이거 고쳐줘" against the selected detail node.
- **Why:** the selection context was inert on service-detail — App wired
  `onSelectionChange` only on the main F/A/S `<Canvas>`, and the dock read
  `activeCanvas` (Services), so detail-canvas selections were invisible to the
  agent (sweep finding).
- **Approval:** Accepted by user, 2026-06-16 (chose the theme/state follow-ups).
- **Spec impact:** [`SPEC.md` → R7 chat Context-injection row](./SPEC.md).
  Guarded by `viewer/tests/chat-selection-detail.test.ts`.

### D-2026-06-16-E — Inspector MD editor (CodeMirror) follows the app theme

- **What:** `MdTextarea`'s CodeMirror `baseTheme` now uses Novel's CSS tokens
  (`rgb(var(--surface))` / `--fg` / `--line-strong` / `--accent` / caret +
  selection) instead of a hardcoded white surface + slate/indigo literals. So
  every typed-text field in the Inspector (service problem/what/…, decision,
  etc.) is readable in dark mode instead of a white island.
- **Why:** dark-mode "흰 섬" — the edit-inspector textareas stayed white with
  dark text + wrong border/caret colours under `.dark` (sweep finding +
  user-visible). Mirrors D-2026-06-15-M (on-card editors) for the MD editor.
- **Approval:** Accepted by user, 2026-06-16 (chose the theme/state follow-ups).
- **Spec impact:** none (contrast/theme fix). Guarded by
  `viewer/tests/md-textarea-theme.test.ts` (source guard: tokens used, no
  hardcoded colours).

### D-2026-06-16-D — Chat dock reshaped to a modern chat-app layout (model selector on top)

- **What:** Restructured `ChatDock.tsx` to read like ChatGPT / Claude desktop:
  (1) a **top conversation bar** whose prominent control is the **model
  selector** (dropdown + "Custom…" fallback) on the left, with the provider
  connection as a compact chip on the right (it fills the bar as the
  call-to-connect when no agent is connected); (2) the message log as
  **left/right-aligned bubbles** (assistant left, user right, error tinted)
  instead of full-width boxes; (3) a single **rounded composer** with an
  integrated circular send button (`↑`). Behaviour, accessible names/roles,
  `data-*` hooks, i18n, and theme tokens are all preserved.
- **Why:** user (2026-06-16) — "다른 채팅처럼 했으면 하는데… 채팅 창 위에 모델
  선택하게" and "UX는 잘 못하네요." The previous layout buried the model field
  under the provider bar and used boxy full-width rows that didn't read as a
  chat. The model selector is now the top control, as asked.
- **Alternatives:** a bold/distinctive aesthetic (per the frontend-design
  skill) — rejected: Novel has an established design system (theme tokens,
  shared font), and the user wants *familiar* chat UX, so the right move is a
  refined, conventional chat layout executed precisely within Novel's tokens,
  not a new visual language. No hardcoded colours (tokens only); no new font.
- **Approval:** Accepted by user, 2026-06-16 (requested + direction given).
- **Spec impact:** rewrote the [`SPEC.md` → R7 chat "UI" row](./SPEC.md).
  Viewer-only. Tests: `chat-dock.test.tsx` + `chat-model-selection.test.tsx`
  (model selector is now a top dropdown).

### D-2026-06-16-C — Chat model is shown + selectable (per-workspace, per-provider)

- **What:** The chat dock now shows which model the active CLI will use (on the
  provider bar, `Provider · model`) and lets the user set it via a model field
  (free-text + a `<datalist>` of suggestions). The choice persists per
  workspace alongside the provider (`chat-provider` JSON gains `model`),
  resets when the provider changes, and is passed to the CLI as
  `--model <model>` (engine: `ChatProviderSelection.model` →
  `ChatProvider.set_model` → each provider splices `--model` into its argv).
  Empty = the CLI's own default. Supersedes the prior SPEC line ("no model
  picker").
- **Why:** user (2026-06-16) — "채팅에 어떤 모델을 쓰는지 보여야 하고, 지원하는
  모델을 선택할 수 있어야 합니다."
- **Alternatives:** (a) curated dropdown of model ids per CLI — rejected for
  codex/gemini: their model ids are vendor/version-specific and Novel would
  ship a stale, fabricated list (honesty: don't invent specs). Free-text +
  best-effort suggestions (only the `claude` CLI's own documented aliases,
  read from its `--help`) avoids that. (b) parse the model from the CLI's
  stream init event — rejected; not all CLIs report it, and the user wants to
  *choose*, not just observe. (c) a separate global Settings surface
  (CHAT_ARCH.md note) — deferred; the in-dock field is what was asked for.
- **Approval:** Accepted by user, 2026-06-16 (requested). This is a Gate 0
  SPEC change (the old "no model picker" line is replaced).
- **Spec impact:** rewrote the [`SPEC.md` → R7 chat "Model selection"
  row](./SPEC.md). All three CLIs' `--model` flag verified against the
  installed binaries. Pinned by `tests/test_chat_model.py` +
  `viewer/tests/chat-model-selection.test.tsx`.

### D-2026-06-16-B — Chat shows a live streaming activity indicator (not frozen)

- **What:** While a chat turn streams, the dock renders a live activity
  indicator — three bouncing dots + an elapsed-seconds counter
  (`ChatActivityIndicator` + `useElapsedSeconds`) — in the status bar and
  inside an assistant bubble that has no text yet. A blinking caret trails
  the streaming text once it arrives.
- **Why:** user — "채팅 과정이 좀 더 다이나믹하게, 사람들이 기다리지만 멈추지
  않은 것처럼 보여야 해요." Between send and the first token the CLI is
  spawning / thinking and the panel looked frozen (only a static
  "streaming…" label, and the assistant bubble was empty).
- **Alternatives:** static text only (status quo) — rejected, reads as
  frozen. A full token-rate / spinner overlay — YAGNI; dots + elapsed convey
  liveness cheaply.
- **Approval:** Accepted by user, 2026-06-16 (requested).
- **Spec impact:** new "Streaming feedback" row under
  [`SPEC.md` → R7 chat](./SPEC.md). Pinned by
  `viewer/tests/chat-activity-indicator.test.tsx`.

### D-2026-06-16-A — Drag-release context-menu suppression is gesture-based (kind/canvas-agnostic)

- **What:** Replaces the v0.81.1 (D-2026-06-15-N) implementation. Instead of
  arming on React Flow's per-node `onNodeDragStop`, `useContextMenus` now
  watches the raw pointer gesture at the window level (capture-phase
  `pointerdown` / `pointerup`): a `pointerup` that moved > ~5 px from its
  `pointerdown` is a drag → the next `contextmenu` is swallowed. The
  `onNodeDragStop` prop wiring on `SketchCanvas` is removed.
- **Why:** user — "서비스 노드만 고쳤네 카테고리는? 서비스 디테일 안에는?"
  The `onNodeDragStop` signal did not cover every case (category / group /
  container nodes, and nodes inside the service-detail canvas), so the menu
  still popped there. The gesture watcher is independent of React Flow's
  per-node callbacks, so it covers every node kind on every canvas
  uniformly. Same user-facing behaviour as D-2026-06-15-N, broader coverage.
- **Alternatives:** keep `onNodeDragStop` + add more RF drag hooks — rejected;
  brittle and still RF-coupled. A global `contextmenu` `preventDefault` —
  rejected; kills legitimate right-clicks.
- **Approval:** Accepted by user, 2026-06-16 (reported the v0.81.1 gap).
- **Spec impact:** updated [`SPEC.md` → Context menu](./SPEC.md#context-menu).
  Pinned by `viewer/tests/context-menu-drag-suppression.test.tsx` (now
  drives the suppression with window pointer events, not a mocked
  `onNodeDragStop`).

### D-2026-06-15-O — ServiceDetail right panel = the subject service, read-only (Option 1)

- **What:** The ServiceDetail canvas's right panel now has three states:
  (1) **default** (no detail node selected) → the subject service's
  **read-only** inspector, read cross-doc from the Services canvas
  (problem-first); (2) a **detail node selected** → that node's editable
  inspector; (3) **empty-space click** → back to the service. Implemented
  with a `fallbackInspector` render-prop on `SketchInspectorBindings`
  (replacing its empty `return null`), threaded through `SketchCanvas`;
  App builds a memoised `<ServiceDetailInspectorHost>` (resolves the service
  from the cached Services `CanvasDoc` by `doc.service_ref`, renders the
  read-only `KindInspector`) and passes it only to the ServiceDetailCanvas
  wrapper. `KindInspector` / `BaseInspector` / `ServiceInspector` gained a
  `readOnly` flag (non-editable label; hidden delete / close / publish /
  published-versions / details-MD; Service body becomes a problem-first
  read-only summary).
- **Why:** the detail canvas's subject IS the service, but the service has
  no node on the canvas (D-2026-05-28-B), so there was nowhere to *see* the
  service's own definition (problem / what / value) while working in its
  detail canvas. The right panel sat empty until a node was clicked. This
  was the originally requested behaviour; it had been designed (workflow
  diagnosis) but not implemented across the v0.79–v0.81 domain detour.
- **Alternatives:** (a) put the service back as a centre node — rejected,
  read as duplication ("로그인 서비스인데 로그인 노드가 들어있는 것도
  이상하고", D-2026-05-28-B). (b) a bespoke read-only summary component
  instead of reusing `KindInspector` — rejected; reusing the per-kind
  inspector keeps the displayed fields identical to what the user edits on
  the Services canvas (one SSOT for "what a service looks like").
- **Approval:** Accepted by user, 2026-06-15 (chose "다음 1: Option 1
  패널" — the original request).
- **Spec impact:** [`SPEC.md` ServiceDetail → Right panel](./SPEC.md#right-panel-option-1-d-2026-06-15-o)
  + Inspector read-only mode. Pinned by
  `viewer/tests/service-detail-fallback-inspector.test.tsx`. LOC:
  SketchCanvas 530 → 537, App 498 → 510 (`structural-guards.test.tsx`),
  both plumbing-only.

### D-2026-06-15-N — Context menu never opens on a drag-release (trackpad contextmenu tail)

- **What:** `useContextMenus` arms a one-shot suppression flag on React
  Flow's `onNodeDragStop`; the next `contextmenu` (node / edge / pane) is
  swallowed instead of opening the menu. The flag is disarmed by any
  `pointerdown` (capture, window-level) so a genuine right-click — which
  fires `pointerdown` before its `contextmenu` — still opens the menu.
  `SketchCanvas` wires `onNodeDragStop` to the hook.
- **Why:** user — "노드 드래그 하고 마우스 놓으면 오른쪽 클릭한 것처럼
  동작합니다." On a macOS trackpad a one-finger press-drag-release emits a
  trailing `contextmenu` *after* pointerup. d3-drag (React Flow) only blocks
  `contextmenu` *while* a drag is active, not the tail, so it leaked to
  `onNodeContextMenu` / `onPaneContextMenu` and popped the menu at the
  release point.
- **Alternatives:** (a) time-window suppression (suppress contextmenu within
  N ms of dragStop) — rejected as fragile / timing-dependent; the
  pointerdown-disarm flag is deterministic and self-clears on the next real
  interaction. (b) `preventDefault` on a global `contextmenu` listener —
  rejected; would also kill legitimate right-clicks.
- **Approval:** Accepted by user, 2026-06-15 (reported bug; gesture +
  symptom confirmed via clarifying question — one-finger trackpad, no
  modifier; context menu appears).
- **Spec impact:** new "Context menu" section in
  [`SPEC.md`](./SPEC.md#context-menu). Pinned by
  `viewer/tests/context-menu-drag-suppression.test.tsx`. LOC: SketchCanvas
  ceiling 529 → 530 (`structural-guards.test.tsx`) for the `onNodeDragStop`
  prop wiring (plumbing-only).

### D-2026-06-15-M — On-card inline editors are readable in dark mode (surface-subtle, not surface)

- **What:** The inline node-label editor (`EditableText` default input) and
  the StepNode `outcome` editor now use `bg-surface-subtle` (not
  `bg-surface`) for the input background. Inside `.node-card`, `text-fg-strong`
  is locked to slate-900 in **both** themes (D-2026-06-09-A), while
  `bg-surface` follows the theme (dark in dark mode) → dark-text-on-dark =
  invisible. `bg-surface-subtle` is card-locked to slate-100 in both themes,
  so the editor reads dark-on-light everywhere. StepNode's editor also gained
  the missing `text-fg-strong`.
- **Why:** user — "노드에 라벨 편집할 때 다크/라이트 테마 적용 안 되어서 글씨가
  보이지도 않는다." D-2026-06-15-I fixed light mode only (where bg-surface =
  white) and missed dark mode — the real invariant is "on-card surfaces must
  use card-locked tokens (surface-subtle), never theme-following ones
  (surface)." Found by the workflow diagnosis, 2026-06-15.
- **Approval:** Accepted by user, 2026-06-15 (reported bug).
- **Spec impact:** none (contrast fix). Guarded by
  `viewer/tests/editable-text-contrast.test.tsx`.

### D-2026-06-15-L — actor_ref click never jumps away in ServiceDetail (supersedes D-2026-06-15-H #2 drill)

- **What:** On a ServiceDetail canvas, clicking a user/actor (`actor_ref`) —
  single OR double — opens its inspector (to edit per-service motivation/pain,
  D-2026-06-15-J) and **never** navigates to the Actors canvas. Two changes:
  (1) `ServiceDetailCanvas` marks **no** node drillable (removed
  `shouldDrill={actor_ref}`); (2) `useInspectorRouting.onNodeDoubleClick` now
  drills only `shouldDrill` nodes (it was unconditional — the latent bug).
  Also `useUrlSync.jumpToActor` now sets `detailActive=false` so any
  navigation to the actor master leaves the detail-tab state consistent.
- **Why:** user — "서비스 디테일에서 유저 혹은 액터 누르면 액터 캔버스로
  가버리는거 수정 안 했고." D-2026-06-15-H #2 declared single=inspector /
  double=jump, but the fix only touched the routing hook's single-click path;
  the double-click jump fired through TWO ungated paths (the hook's
  unconditional `onNodeDoubleClick` AND `BaseNode`'s DOM `onDoubleClick` →
  `data.onDrill`). With actor_ref now the primary editing target in
  ServiceDetail (D-2026-06-15-J), jumping away on a body click is wrong;
  reach the master via the Actors tab.
- **Alternatives:** keep double-click=jump but make it reliable — rejected
  (the user does not want a body-click jump now that motivation/pain are
  edited here). Add an explicit "Go to actor master →" button — deferred
  (YAGNI; the Actors tab already reaches it; revisit if asked).
- **Approval:** Accepted by user, 2026-06-15 (reported bug + repeated intent
  to edit motivation/pain in place).
- **Spec impact:** SPEC §ServiceDetail — new "`actor_ref` click — no jump"
  row. Supersedes the drill portion of D-2026-06-15-H #2. Guarded by
  `viewer/tests/use-inspector-routing-drill.test.ts` (double-click drills only
  drillable nodes) + `use-url-sync-detail-tab.test.ts` (jumpToActor clears
  detailActive).

### D-2026-06-15-K — Service gains a one-line `problem` field (the need it solves)

- **What:** The `service` kind gains a one-line `problem` typed field —
  the need / lack the service exists to solve. Rendered as the **first**
  field in the service inspector, above `target_side` / `what`. Optional
  (defaults `""`, like every other service field).
- **Why:** the service definition reached this session — *"서비스의 본질은
  문제해결이죠 … 문제해결의 과정이 서비스에요"* (user, 2026-06-15). A
  service is the process of solving a problem; the existing fields
  (`what` / `value_created` / `outcome`) are all the **solution** side —
  the problem itself had no home. `problem` is the anchor the detail
  canvas (the solving process) sits under (Retention).
- **Distinct from (MECE):** (a) an **overview** — *"문제와 개요는 다르다"*
  (user): an overview ≈ the existing `what` field, so an overview field
  would duplicate `what`; `problem` (the need) is the genuinely missing
  piece. (b) `actor_ref.pain` (D-2026-06-15-J) — that is per-(actor ×
  service) friction; `service.problem` is the single headline problem for
  the whole service. The actors' pains are the per-participant detail of
  the same problem.
- **Alternatives:** add an "overview" field — rejected (duplicates
  `what`). Derive the problem from the actors' pains only — rejected (the
  user wants an explicit one-line headline at the service level).
- **Approval:** Accepted by user, 2026-06-15 (*"문제 한 줄 좋죠!"* +
  *"문제와 개요는 다르다는 관점 좋아요"*).
- **Spec impact:** SPEC.md §Typed text + body fields — new "Service
  `problem`" paragraph.
- **Lock-step (one commit):** engine `models_actors.py` (ServiceNode +=
  `problem`); viewer `domain/Service.ts` (interface/ctor/fromJson/toJson);
  service inspector (problem field first); i18n `inspector.field.problem`
  + `inspector.fieldHint.problem` (en + ko); regen `--wire`; guards
  (schema-parity, wire-contract, entity-roundtrip, i18n-parity).

### D-2026-06-15-J — Actor motivation/pain become per-service-context (move to actor_ref); refines D-2026-05-31-G/H

- **What:** `motivation` and `pain` move OFF the global actor entity and
  ONTO `actor_ref` (the actor's appearance inside one service_detail). The
  actor inspector becomes **identity-only** (`side` + `body`); the
  `actor_ref` inspector gains `motivation` + `pain` editors alongside the
  existing `gives` / `receives`. Scope is **motivation/pain only** —
  `side` stays on the actor as identity (still a denormalized mirror on
  actor_ref); `value` is explicitly NOT added (gives/receives already
  cover per-service exchange). Refines D-2026-05-31-G (`INHERITABLE_FIELDS`
  drops to `[side, body]`) and D-2026-05-31-H (abstract-root now hides
  `side` only).
- **Why:** PHILOSOPHY.md P3 (Participation is Asymmetric) defines
  motive/pain BY the service — the same human is a Hero in one service, a
  Fan in another. A global actor-level motivation forces one answer across
  every service = the doctrine's own counterexample collapsed into one box,
  and invites Retention drift (VISION). User: *"동기와 어려움 … 이건 너무
  작은 스코프 … 분리되어야 … 서비스 디테일에서 액터 인스펙터와 액터
  캔버스에서 액터 인스펙터."* DDD: motivation/pain have no cross-service
  identity → value-object fields on actor_ref (the same category as
  gives/receives), not entity fields on actor.
- **Fork (pinned):** PURE per-service (no global baseline on the actor),
  chosen over baseline+override. The actor's general character lives in
  `body`/identity; motivation/pain are written fresh per context. Accepted
  tradeoff: an actor not yet placed in any service has **no home** for
  motivation/pain (by design — per P3 there is no participation-motivation
  yet). Verified safe to do NOW: all existing actors carry empty
  motivation/pain (zero data loss); doing it before users author real text
  avoids the unsafe cross-file fan-out migration later.
- **Alternatives:** (a) baseline+override (master default + actor_ref
  override) — rejected: keeps motivation/pain in BOTH inspectors (not the
  separation the user asked), two-axis 3-source resolution, contradicts
  P3's "no global motive". (b) copy-master→all-refs-then-clear migration —
  rejected: lossy for orphan actors, irreversible (Pydantic extra=ignore),
  cross-file-infeasible via read-time migration. (c) also move `side` / add
  `value` — rejected: side is load-bearing for ServiceDetail subject
  detection (D-2026-05-31-I/K); value is scope creep (gives/receives exist).
- **Approval:** Accepted by user, 2026-06-15 (chose "순수 per-service";
  "개념이 가장 잘 해결되는 방향으로, 어려워도, 지금").
- **Spec impact:** SPEC.md §Nodes—actor (Inheritance / Abstract-root /
  Inspector rows refined) + §ServiceDetail (new "Per-service stake
  (actor_ref)" row).
- **Lock-step (부분 완료 금지, one commit):** engine `models_actors.py`
  (ActorRefNode += motivation/pain, ActorNode -=); viewer
  `domain/ActorRef.ts` (+= interface/ctor/fromJson/toJson) +
  `domain/Actor.ts` (-=) + `createBlankNode.ts` (actor_ref defaults);
  `domain/actorInheritance.ts` (INHERITABLE_FIELDS → [side, body];
  EffectiveActorFields contraction); inspectors `actor/index.tsx` (remove
  motivation/pain + captions) + `actor_ref/index.tsx` (add motivation/pain);
  regen `--wire`; tests: schema-parity, entity-roundtrip, structural-guards,
  rewrite actor-inheritance / actor-inherited-surface / actor-base-superclass,
  new actor_ref-context-fields. i18n keys `inspector.field.motivation/pain`
  already exist; reword actor-centric hint copy for per-service context.

### D-2026-06-15-I — Node label edit input has an explicit readable text colour

> **REFINED by [D-2026-06-15-M].** This fixed light mode only; the input's
> `bg-surface` still went dark-on-dark in dark mode. M switches it to the
> card-locked `bg-surface-subtle`.

- **What:** The inline node-label editor (`EditableText`) input now sets
  `text-fg-strong`. Without it the input inherited the node card's label colour
  (often light on a saturated card) and rendered invisible on its `bg-surface`
  background.
- **Why:** user — "노드 라벨 편집모드에서 글씨 안보인다 … 테마 잘못 만든거 같은데?"
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** none (contrast fix). Guarded by the explicit class.

### D-2026-06-15-H — Service-detail opens as a dynamic canvas tab; chat switcher reverts to two tabs (supersedes D-2026-06-15-E)

> **#2 drill SUPERSEDED by [D-2026-06-15-L].** H #2 said actor_ref jumps to
> the actor master on double-click; the fix only covered the routing hook's
> single-click path, so the jump still fired via two ungated double-click
> paths. L removes the actor_ref body-jump entirely (click → inspector).

- **What:** Three linked changes to the service-detail / chat UX:
  1. **Service-detail is a dynamic canvas tab, not a modal.** Selecting a
     (non-root) service node on the Services canvas appends a `{ServiceName}`
     tab after `Foundation | Actors | Services`; it renders the detail canvas
     **inline** (no overlay/inert). Switching to an F/A/S tab keeps the detail
     tab; its × closes it. State lives in `useUrlSync` (`detailActive` +
     `activateDetail` / `closeDetail`); the stencil switches to `service_detail`
     while the detail tab is active.
  2. **Single-click on a service node opens its detail tab** instead of the
     right inspector (`selectOpensDrill`, Services canvas only). On the
     Service-Detail canvas a single click still opens the inspector — actor_ref
     drill stays on DOUBLE-click, so clicking an actor no longer jumps away.
  3. **Chat scope switcher reverts to two tabs** — `[selected canvas |
     project]` (the v0.77.0 full F/A/S picker, D-2026-06-15-E, is **superseded**
     — the canvas tabs, not the chat dock, are where the user picks a canvas).
     A service-detail canvas tab shows the **service's name**, not the generic
     "Service detail".
- **Why:** user — "서비스 디테일이 모달로 뜨는데 캔버스 탭이 동적으로 추가되게";
  "서비스 노드 선택하면 오른쪽 서비스 설명 없애고 디테일 탭에서 보이게"; "채팅창 탭은
  선택한 캔버스 | 프로젝트 두 개"; "채팅창에 서비스 상세 말고 서비스 이름으로".
- **Alternatives:** keep the modal (rejected — user wants a tab); full F/A/S
  chat picker (D-2026-06-15-E, rejected — duplicates the canvas tabs).
- **Approval:** Accepted by user, 2026-06-15 (iterated live in the running
  `.app`).
- **Spec impact:** SPEC §R7 chat (Conversation-scope row → 2-tab + service name)
  + a Service-Detail canvas-tab note. Verified by
  `viewer/tests/chat-dock.test.tsx` (2-tab + service-name),
  `viewer/tests/canvas-tabs-root.test.tsx` (detail tab + close),
  `viewer/tests/use-url-sync-detail-tab.test.ts` (tab lifecycle),
  `viewer/tests/use-inspector-routing-drill.test.ts` (select-opens-drill scope).
- **LOC:** raised `SketchCanvas` ceiling 522 → 529 (selectOpensDrill plumbing).
- **Follow-up (not yet built):** the Service-Detail page's right panel should
  default to the **service's own inspector** and switch to a node's inspector
  on selection (user-approved "Option 1", 2026-06-15) — deferred; it needs a
  cross-doc inspector (the service node lives in the Services doc).

### D-2026-06-15-G — Engine auth token is awaited before the first render

- **What:** `main.tsx` now `await`s `initEngineAuth()` before mounting React
  (inside a `boot()` async fn) instead of fire-and-forget. The Tauri
  `invoke('plot_auth_token')` is an IPC round-trip; firing it without awaiting
  lost the race against the first `/api/projects` effect under the bundled/dev
  shell → **401 → the workspace never loaded**. Awaiting trades a brief
  pre-token blank for a correct boot.
- **Why:** observed live in `tauri dev` — `/api/projects` returned 401 then
  `/api/workspace/tree` 200 one second later (token resolved in between). User —
  "워크스페이스 잘 못 잡혔어요".
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** none (boot-ordering correctness). The old comment's claim
  that "effects run after render so they always see the token" was false for
  the IPC path.

### D-2026-06-15-F — Connected agent is legible on the compact provider bar without expanding

- **What:** The compact provider bar (D-2026-06-14-D) gains a persistent
  connection indicator so the user sees *which* agent is connected at a glance
  without expanding the panel: a filled status dot + the agent name in a
  readable colour (`text-fg-strong`, medium weight) when connected; a hollow
  dot + the muted "Connect your AI agent" prompt when not. A `data-connected`
  attribute (`"1"`/`"0"`) pins the state for tests. The bar already showed the
  name as muted toggle text; this makes "connected: X" unmistakable.
- **Why:** user — "현재 연결된 AI 에이전트[를] 펼치지 않아도 볼 수 있게 해주세요."
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** SPEC §R7 chat — UI row (compact provider bar). Verified by
  `viewer/tests/chat-dock.test.tsx` (`data-connected` 1/0, name visible while
  collapsed).

### D-2026-06-15-E — Chat scope switcher becomes a full thread picker — ⚠️ SUPERSEDED by D-2026-06-15-H (reverted to 2-tab same day)

- **What:** The in-dock chat scope switcher changes from a 2-way
  `[active canvas | project]` toggle to a **full thread picker**: fixed
  segments **Foundation · Actors · Services · Project** are always shown, plus a
  **{ServiceDetail}** segment (after a `|` separator) while a service-detail is
  the active canvas (`activeScope` is `service_detail:<id>`). Selecting a
  segment switches **only the chat thread** — it does NOT navigate the canvas.
  The selection defaults to and follows the active canvas (so opening a
  service-detail moves the chat there), but a click overrides until the next
  canvas change. This refines D-2026-06-13-H's "dock follows the active canvas"
  + the project toggle.
- **Why:** user — "각 캔버스마다 있는 채팅창 … 서비스 디테일은 선택되면
  Foundation Actors Services | {ServiceDetail} 이렇게 … 채팅을 계속 쓸 수 있게."
  Inside a service-detail the old toggle collapsed to `[Service detail |
  Project]`, hiding the other canvas threads; the picker keeps every thread
  reachable so chat stays usable across canvases.
- **Alternatives:** keep the 2-way toggle (rejected — hides threads); make the
  switcher navigate the canvas on click (rejected — the user wants thread-only
  switching, no canvas jump); persist multiple service-detail segments
  (rejected — only the active drill's segment shows; multi-pin is YAGNI).
- **Approval:** Accepted by user, 2026-06-15 (chose "full scope picker +
  service-detail").
- **Spec impact:** SPEC §R7 chat — Conversation-scope + UI rows. Verified by
  `viewer/tests/chat-dock.test.tsx` (segments present, SD segment appears,
  click switches thread, follows active canvas).

### D-2026-06-15-D — Chat MCP path: viewer context (selection + framing) for the external agent

- **What:** The PRIMARY chat path — the user's own agent connected via the
  `mashbill` sidecar — gains the same canvas context the in-app chat already
  has (CHAT_ARCH.md "Scope honesty" follow-up to Layers 1–3). A new read-only
  MCP tool `get_viewer_context(project_path)` returns
  `{active_canvas, selection, framing, updated_at, stale, has_viewer}`. It is
  fed by a viewer→engine push: the viewer `POST`s `/api/viewer/context`
  `{project_path, scope, selection, updated_at}` (debounced, from a single
  `App` effect watching the already-lifted `[activeScope, selection]`) into a
  **project-keyed in-memory** store (sibling to `ChatSessionRegistry`). Framing
  reuses the same per-canvas constants as the in-app path.
- **Pinned decisions (post design red-team, 2026-06-15; store mechanism
  revised after a topology finding — see below):**
  - **Store = filesystem rendezvous file, project-keyed.** The bundled MCP
    server runs as a SEPARATE `--mcp-stdio` process from the HTTP sidecar
    (D-2026-06-14-A); they share only the filesystem, so an in-memory store is
    invisible across the boundary (the originally-pinned "in-memory" was
    physically impossible — caught at implementation). The HTTP process writes
    a small JSON file at a deterministic path derived from the resolved
    `plot_root` (a sha256-keyed file under `tempfile.gettempdir()`); the MCP
    process reads it. **OS temp, not `.noory/`** — truly ephemeral (cleared on
    reboot), no gitignore management, no user-folder pollution; the "no
    user-state contamination" intent is preserved (this is runtime cache, not
    user content). Project-keyed by `plot_root` (NOT `workspace_root` — a
    monorepo holds N projects, D-2026-06-12-A). Writes are atomic
    (temp-file + `os.replace`).
  - **Exposure = MCP tool**, not a resource (universal client support;
    consistent with the tools-only surface). A resource is YAGNI.
  - **Liveness = timestamp TTL (same machine → shared clock, no skew).** The
    HTTP process stamps `updated_at` (server `time.time()`); the MCP tool
    compares to its own `time.time()`. A report older than the TTL (90s) is
    `stale`. The viewer bridge sends a heartbeat (~30s) in addition to
    on-change posts, so an idle-but-open viewer stays fresh and `stale`
    genuinely means "no live viewer." Stale / no file → `has_viewer: false`,
    `active_canvas: null`, `selection: []` — the agent never asserts stale
    context as current. (The WS-hub liveness idea is dropped — also invisible
    cross-process.)
  - **Multi-viewer** = last-writer-wins (the later atomic write overwrites the
    file), disambiguated by `updated_at`; documented (Novel is single-viewer per
    project in practice; per-window tracking is YAGNI).
  - **Framing SSOT** = `build_framing_preamble` + `SCOPE_FRAMING` +
    `build_context_preamble` move to a neutral `mashbill/chat_context.py` that
    BOTH `endpoints_chat.py` and `mcp_tools.py` import (no MCP→HTTP dependency).
  - **Reverse engine→agent push** (real-time nav) = CUT (YAGNI; pull-on-demand
    via the tool is enough).
- **Why:** CHAT_ARCH.md is explicit that Layers 1–3 cover only the **in-app**
  chat; the Pencil model makes the external agent the primary path, so context
  parity belongs there. user — "각 캔버스마다 맞게 동작" applies to the agent the
  user actually drives.
- **Alternatives:** persisted store (rejected — reversibility / contamination);
  MCP resource (rejected — client support / YAGNI); keying by workspace_root
  (rejected — loses project granularity); reverse push (rejected — YAGNI).
- **Approval:** Accepted by user, 2026-06-15 (design red-team verdict was
  REVISE-FIRST; all four Majors resolved in the pins above before approval).
- **Spec impact:** SPEC §R7 chat — new MCP-path context rows. Verified by
  `tests/test_chat_context.py` (shared extraction), `tests/test_viewer_context.py`
  (store + bridge endpoint + liveness), `tests/test_mcp_tools.py`
  (`get_viewer_context`), viewer `useViewerContextBridge` test.

### D-2026-06-15-C — In-app chat Layer 3: per-canvas system framing

- **What:** Each chat turn now carries a **canvas-appropriate system framing**
  prepended to the CLI message (CHAT_ARCH.md Layer 3, the last of the three
  sequenced layers). The base scope maps to its VISION.md phase: Foundation →
  Discovery ("surface/sharpen the essence"), Actors / Services → Planning
  ("design the value-creation machinery"), Service-Detail → Execution ("break
  the plan into concrete steps"). The cross-canvas `project` scope gets no
  framing. Engine assembles the prompt as **framing → Layer 2 context →
  user message** (empty parts skipped). A parametric `service_detail:<id>`
  resolves to the shared `service_detail` framing (base extraction).
- **Committed defaults (CHAT_ARCH.md decision 4):** framing lives in **code
  constants** (`_SCOPE_FRAMING` in `endpoints_chat.py`), not `.noory/`-editable.
  **In-app only** — the primary MCP path doesn't receive this framing (named
  follow-up: a viewer→engine bridge + MCP resource).
- **Why:** user — "각 캔버스마다 있는 채팅창은 각 캔버스에 맞게 동작을 해야할 것
  같아요"; per-canvas behaviour that matches Novel's three-phase cycle.
- **Alternatives:** `.noory/`-editable framing (rejected as YAGNI until asked);
  no framing / rely on selection alone (rejected — the agent needs to know
  *how* to help on each canvas, not just *what* is selected).
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** SPEC §R7 chat — new Per-canvas framing row. Verified by
  `tests/test_endpoints_chat.py` (per-phase framing, base extraction, project
  empty, framing→context→message order).

### D-2026-06-15-B — In-app chat Layer 1: per-service-instance conversation threads

- **What:** `service_detail` becomes a **parametric** chat scope — on the wire
  it carries the service instance id as `service_detail:<service_id>`, so each
  service-detail canvas keys its own conversation thread (CHAT_ARCH.md Layer 1,
  the second of the three sequenced layers). The scope set now equals
  `CanvasKey ∪ {project}`, so chat threads and canvas state key the same way.
  Engine: `ChatStreamEvent.scope` widened to `str`; the session registry key
  `(workspace, provider, scope)` carries the full string; `_read_scope`
  validates via a new `is_valid_scope` (base member OR `service_detail:<id>`
  with non-empty id). Viewer: `ChatScope` widened to
  `… | \`service_detail:${string}\``; App passes the active service's parametric
  scope (falling back to `services` when no service is resolved); the scope
  switcher labels a parametric scope with its base `service_detail` i18n key.
- **Committed defaults (post red-team, CHAT_ARCH.md):** thread keyed by stable
  `service_id` (survives rename); on service delete the thread is left orphaned
  (in-memory, cleared on engine restart) — no eager cleanup; an unresolved
  `service_detail:<id>` degrades to the `services` scope; bare `service_detail`
  (no id) is rejected server-side (Fail Fast). **In-app only** — the primary MCP
  path is unaffected.
- **Why:** user — "각 캔버스마다 있는 채팅창은 각 캔버스에 맞게 동작을 해야할 것
  같아요" + "Services: 서비스(서비스-디테일 캔버스)마다 채팅 하나".
- **Alternatives:** keep a single shared `service_detail` thread (rejected —
  mixes unrelated services' contexts, breaks the CLI's resumed-session
  continuity). Tradeoff named (CHAT_ARCH.md A7): per-instance threads fragment
  cross-area continuity; Layer 2 selection injection partly mitigates.
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** SPEC §R7 chat — Conversation-scope row (per-instance
  service_detail). Verified by `tests/test_chat_scope_parity.py`
  (`is_valid_scope` suffix + TS template-literal parity),
  `tests/test_endpoints_chat.py` (per-service session keying + parametric
  accept), `viewer/tests/use-chat-stream-scope.test.ts` (per-instance routing)
  + `viewer/tests/chat-dock.test.tsx` (base-label fallback).
- **LOC:** App stayed at 498 (narrowed `tabToKind` return type, no new lines).

### D-2026-06-15-A — In-app chat Layer 2: per-turn canvas + selection context injection

- **What:** Every in-app chat turn now carries the active canvas + the live
  node selection, so the agent can resolve "이거 / fix this" against what the
  user has selected (CHAT_ARCH.md Layer 2, the first of the three sequenced
  layers). Flow: `SketchCanvas` reports its multi-selection upward
  (`onSelectionChange`) → App lifts it + maps ids → `{id, kind, label}` from
  the active canvas → `ChatDock` → `useChatStream.send` → `POST /api/chat/send`
  `selection` field → engine `build_context_preamble(scope, selection)`
  prepends a `[Novel context] Active canvas / Selected …` preamble to the CLI
  message.
- **Committed defaults (post red-team, CHAT_ARCH.md):** per-turn snapshot at
  send time (no live sync); `project` scope injects nothing; selection capped
  at 20 detailed nodes (rest = ids only) so a large multi-select can't blow the
  prompt; framing in code (no `.noory/`-editable config). **In-app only** — the
  primary MCP path doesn't get selection yet (named follow-up).
- **Why:** user — "노드를 선택한 상태에서 선택된 노드를 채팅에서 인지" +
  "앱에서 어떤 게 선택되어 있는지 다 연동".
- **Approval:** Accepted by user, 2026-06-15.
- **Spec impact:** SPEC §R7 chat — context-injection row. Verified by
  `tests/test_endpoints_chat.py` (preamble unit + cap + integration) +
  `tests/use-chat-stream-scope.test.ts` (send forwards selection).
- **LOC:** raised `SketchCanvas` ceiling 516 → 522 (the `onSelectionChange`
  lift — plumbing-only; follow-up: extract a `useNodeSelection` hook). App
  stayed at 498.

### D-2026-06-14-E — Resizable workspace layout; chat dock moved to the leftmost panel

- **What:** The workspace is now three **horizontally-resizable panels** —
  **chat (leftmost) | project sidebar | canvas** — via `react-resizable-panels`
  (v4, `Group`/`Panel`/`Separator`), in a new `viewer/src/shell/WorkspacePanels.tsx`.
  Each panel has a **minimum width** (chat 14%, sidebar 10%, canvas 30% — the
  canvas can never be squeezed away). Chat + sidebar are collapsible (drag to
  the edge / double-click the separator). Layout persists across reloads via
  `useDefaultLayout` (localStorage, id `plot:workspaceLayout`). The chat dock's
  own collapse-to-rail toggle AND the sidebar's own w-8/w-56 collapse toggle
  are **removed** — the panel owns width/collapse now (the user preferred free
  resizing over per-panel collapse buttons).
- **Why:** user feedback — "채팅 창을 제일 왼쪽으로", "각 패널들 가로 사이즈
  자유롭게 조정", "접기 펼치기보다 그게(리사이즈) 나은 거 같은데". One
  resize mechanism instead of three bespoke collapse toggles.
- **Approval:** Accepted by user, 2026-06-14 (chose: standard library +
  enforced minimums + resize-replaces-collapse).
- **Spec impact:** SPEC §R7 chat (dock is now the leftmost resizable panel).
  Verified by `tests/chat-dock.test.tsx` (collapse tests removed; dock fills
  its panel) + full viewer suite green; ChatDock/App stay under LOC ceilings.
- **Dependency:** adds `react-resizable-panels` (MIT) — the first runtime UI
  dependency beyond reactflow; standard, widely-used, accepted by the user.
- **Follow-up:** unused i18n keys left behind by the removed collapse toggles
  (`chat.collapse`/`chat.expand`, `sidebar.{expand,collapse}ProjectList`,
  `sidebar.{show,hide}Projects`) — harmless (en/ko parity intact); prune in a
  later i18n sweep.

### D-2026-06-14-D — Chat dock: provider connection behind a compact bar (collapsed by default)

- **What:** The "Connect your AI agent" provider panel no longer occupies the
  top of the chat dock permanently. It's now behind a **compact one-line bar**
  showing the active CLI (or "Connect your AI agent" when none) + a ▸/▾
  chevron; clicking it reveals the full `ChatProvidersPanel`. Collapsed by
  default. The active-CLI label loads on mount (so the bar is informative
  without expanding); the provider *list* (`getMcpProviders`) only fetches when
  expanded.
- **Why:** user feedback — "커넥트 유어 AI agent 너무 커요. 이걸 매번 보고
  있을 이유가 없을 것 같은데?" Provider connection is a setup step, not
  something to stare at while chatting. This is the first slice of the larger
  Settings surface (D-2026-06-14-B follow-up) — provider/model config will
  eventually live in a dedicated Settings area; the compact bar is the
  reversible interim.
- **Approval:** Accepted by user, 2026-06-14 ("컴팩트 바 + 접기").
- **Spec impact:** SPEC §R7 chat — UI row updated (provider panel behind a
  compact bar). Verified by `tests/chat-dock.test.tsx` (collapsed-by-default,
  expand-on-click, active-label-on-bar).

### D-2026-06-14-C — Services arrows diverge from the anchor; edges easier to select + selection highlighted

Three edge changes (one batch):

- **Services canvas = forced divergence.** The anchor-relative arrow control
  generalises from a boolean (`convergeArrowsOnAnchor`) to a mode
  `anchorArrowMode: "converge" | "diverge" | "none"`. Foundation/Actors =
  `"converge"` (arrow toward anchor, unchanged); **Services = `"diverge"`**
  (arrow points AWAY from the anchor, so the anchor → category → service flow
  always reads outward regardless of how the edge was drawn); ServiceDetail /
  default = `"none"`. Applies to both render orientation (`edgeTransform`) and
  creation normalisation (`useFlowHandlers`). This enforces the
  D-2026-06-01-D services-divergence spec at render time instead of relying on
  the stored edge direction.
- **Edges easier to select.** `edgeTransform` sets `interactionWidth: 28` on
  every edge (RF default is 20) — a wider invisible click band.
- **Selected edge highlighted.** `edgeTransform` writes the edge stroke
  inline (value-flow recolour), which beats RF's default `.selected` class
  styling, so selection showed no visual change. Added a styles.css rule
  (`.react-flow__edge.selected .react-flow__edge-path { stroke: accent !important; stroke-width: 3 !important }`)
  that overrides the inline stroke. Not a cursor rule → the cursor-baseline
  guard is unaffected.

- **Why:** user feedback while reviewing the v0.69.0 app — services arrows
  must flow outward from the anchor; edges were hard to click; selecting an
  edge gave no feedback.
- **Approval:** Accepted by user, 2026-06-14.
- **Spec impact:** SPEC §Services (divergence now render-enforced) + §Edges
  (interaction width + selection highlight). Verified by
  `tests/edge-transform.test.ts` (diverge orientation + interactionWidth),
  `tests/edge-selection-style.test.ts` (selected-edge `!important` rule).
- **LOC:** SketchCanvas stayed under its 516 ceiling (515) — the mode rename
  is net-neutral; no ceiling change.

### D-2026-06-14-B — Re-include claude-code in in-app chat, with a billing warning (reverses D-2026-06-13-H exclusion)

- **What:** claude-code is selectable for in-app chat again. The three
  exclusion points added in v0.68.0 are removed: the `/api/chat/send`
  400 backstop, the suppressed selection radio on the claude-code row, and
  the dock's coercion of a persisted claude-code choice to no-selection.
  In their place, when claude-code is the active chat CLI the chat frame
  shows a **billing-warning banner** (`chat.claudeBillingWarning`): "Claude
  Code runs headless (`claude -p`), billed separately from your Claude
  subscription — connect over MCP to avoid double-charging." The per-canvas
  scope model (D-2026-06-13-H) is unchanged.
- **Why:** the user chose to make claude-code available in-app despite the
  double-billing tradeoff, surfaced as an informed-consent warning rather
  than a hard block ("일단 넣어요. 오늘 결정을 바꿉니다" + "경고표시하고
  넣기"). The MCP path remains the recommended, non-double-charged way to use
  Claude; the warning points users to it.
- **Alternatives:** (a) keep the hard exclusion (D-2026-06-13-H) — rejected
  by the user. (b) silent re-include with no warning — rejected: the
  double-billing cost must stay visible (the warning is the whole point of
  re-including it safely).
- **Approval:** Accepted by user, 2026-06-14.
- **Spec impact:** SPEC §R7 chat — updated: claude-code selectable in-app
  with a billing warning; the exclusion language is removed. Verified by
  `tests/test_endpoints_chat.py` (claude-code send → 202),
  `tests/chat-providers-panel.test.tsx` (claude-code radio present),
  `tests/chat-dock.test.tsx` (warning banner on claude-code, absent on codex).
- **Follow-up (pinned, not yet built):** a dedicated **Settings surface**
  (separate from the inline chat dock) holding provider + **model selection**
  + the claude billing acknowledgment, stored across **two tiers** — global
  `~/.noory/plot/settings.json` (new) for user defaults (preferred model,
  billing ack) and per-workspace `<ws>/.noory/plot/` overrides
  (provider/model per project). Design via mashbill-design-red-team before code.

### D-2026-06-14-A — Bundled .app registers mashbill MCP via `<binary> --mcp-stdio` (frozen-aware)

- **What:** The MCP-registration entry Novel writes into each CLI config
  (`~/.claude.json` / `~/.codex/config.toml` / `~/.gemini/settings.json`)
  now has two shapes:
  - **dev checkout** — unchanged: `uv run --directory <src> python -m mashbill`.
  - **frozen .app** — `command = sys.executable` (the stable bundled binary
    path inside `Novel.app/Contents/MacOS/mashbill`), `args = ["--mcp-stdio"]`.
  The bundled binary gains a `--mcp-stdio` mode (`mashbill.server.run_mcp_stdio`,
  stdio MCP transport only — no HTTP). Dispatch lives in the sidecar entry
  `plot/src-tauri/sidecar-build/mashbill_entry.py`.
- **Why (the bug):** `_plot_entry` built the command from
  `plot_plugin_root()` = `Path(__file__).parent.parent`. Inside the
  PyInstaller-frozen `.app`, `__file__` resolves to the ephemeral `_MEIxxxx`
  onefile extraction dir — deleted on app exit, and not a uv project even
  while alive. So an agent launching the registered `plot` MCP ran
  `uv run --directory <_MEIxxxx> …`, which times out. Observed live
  (2026-06-14): codex failed the turn (`MCP client for 'plot' failed to
  start: request timed out`); gemini ignored the failed MCP and answered
  anyway. This broke the **primary** chat path (D-2026-06-13-H: the agent
  connects to Novel over MCP) in the actual product. The HTTP sidecar was
  also HTTP-only (`run_http_only`), so even a corrected path had no stdio
  MCP mode to point at — hence both halves of this fix.
- **Alternatives:** (a) register an HTTP/SSE MCP transport at the running
  sidecar (:5190) — rejected for now: needs the sidecar up when the agent
  connects, per-CLI HTTP-MCP config differs, and the `PLOT_AUTH_TOKEN` seam
  would have to be threaded. The stdio path keeps the model each CLI already
  expects. (b) frozen-guard only (refuse to write a broken entry) — rejected:
  leaves the .app with no working MCP registration.
- **Approval:** Accepted by user, 2026-06-14 ("stdio 모드 추가" 선택).
- **Spec impact:** SPEC §R7 chat — MCP wiring row notes the dev vs bundled
  command. Verified by `tests/test_mcp_registration.py` (frozen branch) +
  `tests/test_server.py` (stdio-only transport). End-to-end .app verification
  needs a sidecar rebuild (PyInstaller) — pending.

### D-2026-06-01-D — Services canvas = divergence (anchor → category → service)

- **What:** On the Services canvas the flow runs OUT from the anchor:
  `BANAS → category → service`. Foundation stays convergence
  (element → anchor), Actors stays inheritance (parent → child).
- **Why:** the service canvas reads as BANAS *decomposing* into its
  services ("서비스는 발산입니다. 파운데이션이 수렴이고. 액터는 상속이고").
  The BANAS-sim had category→anchor edges (convergence); flipped the 7
  anchor-incident edges to anchor→category.
- **Approval:** Accepted by user, 2026-06-01.
- **Spec impact:** SPEC.md §Edges flow-semantics; docs/AUTO_LAYOUT.md §2.

### D-2026-06-01-E — Floating edges removed; edges attach to the facing side

- **What:** Removed the v0.30.3 floating-edge renderer (`FloatingEdge`,
  `floatingEdgeGeometry`, registry entry). Regular edges use RF's default
  bezier again. `edgeTransform` now attaches each end to the handle on the
  side of the node **facing the other node** (computed from node centres
  passed via `useEdgesMemo`, anchor seeded from `projectAnchor`), so the
  connection reads clean from any direction without floating.
- **Why:** user asked to remove floating ("플로팅 노드 없앱시다") and to
  tidy the arrows ("화살표 좀 정리"). The facing-side picker fixes the
  arrow-tangle that floating had papered over.
- **Approval:** Accepted by user, 2026-06-01 (chose "플로팅만 제거").
- **Spec impact:** SPEC.md §Edges; docs/AUTO_LAYOUT.md §1, §5.

### D-2026-06-01-F — Auto-layout = mindmap 4-direction tidy tree, placement-respecting

- **What:** Replaced the radial depth-ring layout (`computeRadialLayout`,
  v0.34.8) with `computeMindmapLayout` — a four-direction (上下左右) tidy
  tree wired into `useAutoLayout` for every anchor canvas. Top-level
  branch → arm assignment is **one rule, no per-kind special-casing**:
  each branch keeps the side of the hub its centre is currently on
  (dominant axis wins). The user groups by WHERE they place nodes — drag
  mission up, core_value left, identity right and they stay there.
  Brand-new nodes sitting on the hub (no usable side) spread across the
  emptiest arms by subtree leaf-count so a fresh graph still fans out.
  Each arm is a tidy tree growing outward (disjoint cross bands, parent
  centred on children); arms start just beyond the perpendicular spread,
  kept tight (rankGap 44, crossGap 16) so the first ring sits close to
  the hub → no node overlap, no edge crossing, short edges.
- **Why:** every circular layout was rejected ("원이 아니라", "마인드 노드
  참고"); user wants type-grouped, placement-respecting, non-overlapping
  ("종류별로 나눠야지", "미션은 위 아이덴티티는 오른쪽 코어밸류는 왼쪽",
  "선도 겹치지 않게"). MindNode-style.
- **Alternatives:** radial / concentric rings (rejected, looped many
  rounds); single L→R tree (rejected — wanted 4 directions); per-kind arm
  grouping (tried, rejected — "또 카테고리별로 정렬 규칙을 만들어뒀구만요";
  the single position-respecting rule already groups when the user groups
  by placement); always-on auto-layout (user cancelled — manual button).
- **Approval:** Accepted by user, 2026-06-01.
- **Spec impact:** SPEC.md §Auto-layout (table + algorithm); full
  criteria in **docs/AUTO_LAYOUT.md** (new SSOT). Tests:
  `viewer/tests/mindmapLayout.test.ts`.

### D-2026-05-31-G — Actor inheritance (computed effective fields + inspector)

> **REFINED by [D-2026-06-15-J].** `motivation` / `pain` left the actor
> for per-service-context `actor_ref`, so `INHERITABLE_FIELDS` shrinks
> from `[motivation, pain, side, body]` to `[side, body]`. The resolver
> machinery (own → ancestor → empty, actor-tree axis) is unchanged.

- **What:** On the actors canvas a sub-actor inherits its parent
  actor's common fields (motivation / pain / side / body) through the
  inheritance edges (child→parent toward the anchor). New pure module
  `domain/actorInheritance.ts::effectiveActorFields` resolves each field
  `own non-empty → nearest ancestor's non-empty → empty`, with the same
  inheritance-edge + lexicographic tie-break + cycle guard as fold /
  propagation. The actor Inspector shows an inherited field as a greyed
  `↳ inherited from {parent}: …` caption under the (empty) input;
  typing overrides.
- **Why:** the confirmed model (this session) — `anchor(project) ←
  User(base) ← {Operator, Bana}` — where a base actor holds common
  properties the sub-actors inherit. User chose **real/computed**
  inheritance (over visual-only), but it stays a *derived view*:
  nothing is written, each node's value remains the SSOT (Novel is a
  cognition tool, not a data engine).
- **Alternatives:** persist inherited values onto children — **rejected**
  (duplication / drift; violates SSOT). Compute at render — **chosen**.
- **Approval:** Accepted by user, 2026-05-31 (model + "계속").
- **Spec impact:** SPEC.md §Actors — inheritance note. i18n
  `inspector.inheritedFrom`. Tests: `actor-inheritance.test.ts`
  (own / inherited / override / cycle / multi-parent tie-break).

### D-2026-05-31-F — Floating edges (border-to-border, uniform from any side)

- **What:** Every non-self-loop edge now renders as a **floating edge**
  (`canvases/edges/FloatingEdge.tsx` + pure
  `flow/floatingEdgeGeometry.ts`): it attaches to the point on each
  node's border that faces the other node, computed from live node
  geometry (RF `nodeInternals`), ignoring handles. Self-loops keep
  `SelfLoopEdge`. Also fixed the injection animation stutter: the dash
  period is now `5 5` (10) to match RF's animated `stroke-dashoffset`
  cycle (10), so the marching dashes loop seamlessly.
- **Why:** the node's 4 handles are asymmetric (emit only right/bottom,
  receive only top/left), so an edge to a node on your left/top had to
  loop awkwardly out the wrong side (user saw it on the Voice→Banas
  injection edge). Confirmed empirically that ConnectionMode.Loose does
  **not** let a target-type handle act as a source (RF "couldn't create
  edge for source handle" warning). User direction: *"노드의 4개 핸들
  어디에서 앵커의 어떤 핸들로 연결하든 같아야 한다"* — connection must
  read identically from any side. Floating edges deliver exactly that:
  the handle choice becomes irrelevant to rendering.
- **Note:** BaseNode handles are unchanged (still t/l/r/b). Drag-create
  still uses them (Loose mode = any-to-any), but the resulting edge
  floats, so the asymmetry no longer affects the visual. No new/changed
  edge data; floating is render-only (Cmd+Z, persistence unaffected).
- **Alternatives:** (a) both-source+target handles per side —
  **rejected** (overlapping-handle drag ambiguity, still snaps to 4
  fixed points, id migration). (b) floating edges — **chosen** (user
  via AskUserQuestion): truly uniform, no handle gymnastics.
- **Approval:** Accepted by user, 2026-05-31 (chose floating).
- **Spec impact:** SPEC.md §Edges — floating-edge rendering note.
  Tests: `floating-edge-geometry.test.ts` (border-point math).

### D-2026-05-31-E — Server propagation reads `edge.relation` (Phase 2c)

- **What:** `propagation._build_parent_lookup` (publish MINOR-bump
  ancestor walk) now derives parent↔child from the stored
  `edge.relation` via a new `edge_semantics.fold_endpoints(edge)` — the
  Python mirror of `viewer/src/flow/foldHierarchy.ts::foldEndpoints`.
  `flow` → source=parent; `inheritance` → target=parent (inverted);
  `injection` → excluded. Closes the loop opened by D-2026-05-31-C/D:
  viewer fold and server publish-propagation now read the **same** SSOT.
- **Why:** mashbill-design-red-team A8 — before this, the server walked
  every directed edge as source=parent, so publishing on a canvas with
  inheritance edges would bump the wrong ancestor (subclass↔superclass
  inverted) and injection edges would be walked as containment. The
  stored-field decision (D-2026-05-31-C) exists precisely so the server
  can read the semantic; this wires it in.
- **Approval:** Accepted by user, 2026-05-31 ("계속").
- **Spec impact:** SPEC.md §Edges Hierarchy note (already records the
  shared fold rule). Tests: `test_propagation.py` — inheritance bumps
  the superclass, injection never walked.

### D-2026-05-31-D — Viewer reads `edge.relation` (fold / style / layout) (Phase 2b)

- **What:** The viewer now derives behaviour from the stored
  `edge.relation` (D-2026-05-31-C) instead of re-deriving from source
  kinds. New pure module `flow/foldHierarchy.ts::foldEndpoints(edge)`:
  `flow` → source=parent / target=child; `inheritance` → **target=parent
  / source=child (inverted)** — collapsing a superclass hides its
  subclasses; `injection` → `null` (excluded from fold). Consumed by
  `useCollapsedTree` (fold maps) + `useNodesMemo` (render sort).
  `edgeTransform` injection styling (violet + animated) now reads
  `e.relation === "injection"`, so it fires on **every** canvas
  (foundation essence→anchor edges now render violet, not just
  service_detail). `actorAnchoredLayout` injection exclusion reads
  `e.relation`. Removed the now-dead `flow/foundationRefKinds.ts`
  (its kind-set is superseded by `edgeSemantics.ESSENCE_SOURCE_KINDS`).
- **Why:** make the stored SSOT authoritative across the viewer (the
  point of the stored-field decision); enable the foundation "value
  injection toward the anchor" visual the user asked for.
- **Behaviour change pinned:** injection (`*_ref`) edges are now
  **excluded from the service_detail fold map** (previously every
  directed edge — including a `mission_ref` → step — counted as a
  parent-child fold link). Correct: a ref *injects into* a step, it
  doesn't *contain* it. Verified no existing fixture relied on folding a
  `_ref` (full suite green). No data migration.
- **Alternatives:** style inheritance edges with a distinct stroke now —
  **deferred**: the user is reviewing canvas look-and-feel (NEXT_SESSION
  top item); picking an arbitrary inheritance colour pre-empts that.
  Inheritance edges render as default directed edges for now; only the
  fold semantic changed.
- **Approval:** Accepted by user, 2026-05-31 ("계속").
- **Spec impact:** SPEC.md §Edges relation row (already covers it);
  fold semantics noted under Hierarchy.

### D-2026-05-31-C — Stored edge `relation` semantic (flow / injection / inheritance)

- **What:** New stored `SketchEdge.relation` field
  (`"flow" | "injection" | "inheritance"`, default `"flow"`). Phase 2a
  of the Retention-canvases work: it carries the edge's semantic so
  *both* the viewer (fold / layout / styling, Phase 2b) and the server
  `propagation.py` (publish MINOR-bump, Phase 2c) read one SSOT.
  `edge_semantics.classify_edge(canvas, source_kind)` (mirrored in TS
  `flow/edgeSemantics.ts::classifyEdge`) is the **default assigner** at
  edge creation + a read-time migration (`_migrate_assign_edge_relation`)
  for legacy edges. Rules: actors-canvas → `inheritance`; essence source
  (`mission`/`core_value`/`identity` + their `*_ref`, excluding
  `actor_ref` = subject) → `injection`; else `flow`. Edge **flip**
  (D-2026-05-31-A) now re-assigns `relation` from the new source so it
  never goes stale.
- **Why:** mashbill-design-red-team flagged (A8) that a viewer-only derived
  classifier would drift from `propagation.py`, which independently
  derives parent-child from directed edges and would misread injection /
  inheritance edges (publish would bump the wrong ancestor). A stored
  field is the one wire SSOT both sides read (A4 — chosen over derived
  for exactly this cross-boundary reason; user-decided 2026-05-31).
- **Invariant pinned (red-team A2):** every directed edge on the **actors
  canvas is `inheritance`** — the actors canvas has a single edge type
  (user: "액터 캔버스에선 연결선이 1종류만"). `classifyEdge` encodes this.
- **Alternatives:** (a) derived, no stored field — **rejected** (A8/A4:
  server can't read it without a duplicate Python classifier = SSOT
  violation across the boundary). (b) stored, plus this default-assigner
  + parity test (`test_edge_semantics.py` locks the TS↔Python value set
  and truth table) — **chosen**.
- **Approval:** Accepted by user, 2026-05-31 (chose stored field via
  AskUserQuestion after the red-team).
- **Spec impact:** SPEC.md §Edges — `relation` row + actors-edges
  invariant. No behaviour change yet (2a); 2b wires the viewer, 2c the
  server.

### D-2026-05-31-B — Node shape encodes producer-vs-reference

- **What:** Shape now distinguishes the original from its symbol
  pointer. 원본/master kinds (`mission`, `core_value`, `identity`,
  `actor`) render as a **rounded rectangle** (soft corners);
  symbol-reference kinds (`mission_ref`, `value_ref`, `identity_ref`,
  `actor_ref`) render as a **circle**. `decision` stays a diamond;
  `project` anchor keeps its user-toggled shape (default circle).
  Forced at the renderer via a new pure module
  `viewer/src/canvases/sketch/nodeShape.ts::effectiveShape`.
- **Why:** user direction (2026-05-31): *"원본캔버스는 네모, 심볼 노드는
  동그라미"* + *"네모의 코너들을 좀 둥그스럼하게 해서 부드러운 느낌"*.
  The shape should tell producer from reference at a glance — the real
  node is a soft 네모, the pointer that stands in for it is a circle.
- **Alternatives:** (a) sharp-corner rectangle (`borderRadius:0`) —
  **rejected**, user asked for soft corners → mapped to the existing
  `rounded` shape (8px). (b) keep D-2026-05-28-D (all Symbol kinds
  circles) — **rejected/superseded**: it made the original and its
  reference indistinguishable.
- **Approval:** Accepted by user, 2026-05-31 (gave the direction +
  confirmed `actor` is included via AskUserQuestion).
- **Spec impact:** SPEC.md §"Node shape — producer vs reference" (new);
  supersedes D-2026-05-28-D. Aligns with the pre-existing SPEC actor
  shape line ("rounded — rectangle with rounded corners").

### D-2026-05-31-A — Edge "Flip direction" context-menu action

- **What:** New edge context-menu item **"Flip direction (swap source
  ↔ target)"**. Swaps the edge's ``source``/``target`` so the arrowhead
  points the other way; nulls ``sourceHandle``/``targetHandle`` and
  lets React Flow re-route through each node's default valid handle.
  ``directed`` is preserved. Available on every canvas.
- **Why:** user asked for a way to change an edge's direction without
  redrawing it (*"서비스 캔버스에서 연결선 방향을 바꿀 수 있는 기능도
  들어가면 좋을 것 같아요"*). Resolves the open "Direction switch UI"
  thread. Also the manual tool for re-orienting an edge toward the
  anchor on the Retention canvases (the planned all-edges-toward-anchor
  model, this session).
- **Alternatives:** (a) swap the handle ids too — **rejected**: BaseNode
  handles are typed by side (``t``/``l`` target-only, ``r``/``b``
  source-only), so a target handle can't act as a source; reusing the
  ids made RF drop the edge (verified live — *"Couldn't create edge for
  source handle id: l"*). (b) auto-flip edges to a convention —
  **rejected**: violates "all edges are user-drawn / user controls
  every line". Flip is an explicit per-edge user action.
- **Approval:** Accepted by user, 2026-05-31 (requested the feature).
- **Spec impact:** SPEC.md §Edges — new "Flip direction" row.

### D-2026-05-04-A — No auto-edges from anchor

> ⚠️ **Blanket-ban portion SUPERSEDED by `D-2026-06-17-J` (2026-06-17).** The global
> "all edges are user-drawn / never auto-emit" rule is removed — edges are governed
> by their *definition*, and AI may draw/propose edges (esp. AI-maintained canvases).
> What survives from this entry: the *specific* Foundation anchor→child auto-edges
> were rejected (silent + uneditable), and **silent/meaningless/uneditable** lines
> stay banned. AI-proposed, editable, well-defined edges are now allowed.

- **What:** Renderer was emitting synthetic dashed slate-400 edges from
  the project anchor to every top-level Mission / CoreValue / Identity
  node on Foundation.
- **Why:** the relationship "this Mission belongs to this project" was
  implicit; auto-edges were proposed to make it visible.
- **Alternatives:** real seed edges written into `canvas.json`
  (rejected — auto-creates user data without consent); leave it to
  the user (chosen).
- **Approval:** **Rejected** by user, 2026-05-04 — auto-edges weren't
  editable / deletable, which broke the user's "every line on the
  canvas is mine to control" expectation.
- **Spec impact:** [`SPEC.md` §Edges](./SPEC.md#edges) — codifies "all
  edges are user-drawn".

---

### D-2026-05-04-B — Anchor handles stay visible

- **What:** Hide the four React Flow connection handles on the
  synthetic project anchor.
- **Why:** code comment said "synthetic anchor is read-only"; assumed
  this meant the user shouldn't draw edges from it either.
- **Alternatives:** keep the handles (chosen after rejection).
- **Approval:** **Rejected** by user, 2026-05-04 — the user never
  agreed the anchor was read-only. The "read-only" claim was a stale
  code comment from v0.13 Phase 0 development that the assistant
  treated as spec. Anchor handles are restored.
- **Spec impact:** [`SPEC.md` §Anchor](./SPEC.md#anchor-the-centre-node)
  — "Handles (4 sides): Visible. User may draw edges from / to the
  anchor like any other node."

---

### D-2026-05-04-C — Anchor visually distinct from Service circles

- **What:** Add a slate-600 outline + offset + slate-300 inner ring to
  the project anchor, so it's recognisable as "the project itself" and
  not confused with the same-coloured Service nodes that appear on
  the Services canvas.
- **Why:** without differentiation, a user landing on Services / Actors
  (where the anchor is also auto-seeded) couldn't tell which yellow
  circle was the project vs a Service.
- **Alternatives:** different fill colour (rejected — fill is already
  meaningful per kind palette); icon overlay (rejected — competes
  with kind-tag corner labels).
- **Approval:** **Accepted** by user, 2026-05-04 — implicitly, by not
  asking to revert when other items were rolled back.
- **Spec impact:** [`SPEC.md` §Anchor](./SPEC.md#anchor-the-centre-node)
  — "Visual differentiation".

---

### D-2026-05-04-D — Auto-layout removed entirely — **Rejected (misattribution corrected 2026-05-10)**

- **What was implemented:** Removed the "Auto layout" toolbar button
  and the corresponding pane-context-menu entry. Dropped the
  `radialLayout` / `autoLayout` calls and the `handleAutoLayout`
  callback from `SketchCanvas`.
- **Original (incorrect) rationale:** layout encodes user intent;
  auto-layout silently overwrites that intent.
- **Why this entry is now Rejected:** the user confirmed in the
  2026-05-10 Foundation re-verification session that this removal
  was a misread of their actual intent. Direct quote (2026-05-10):
  *"내가 없애라는건 다운로드 업로드 이런거였는데. 오토레이아웃만
  남기라는거였는데."* The earlier session's *"그리고
  오토레이아웃도 없앴어요. 이해?"* (2026-05-04) was the
  assistant's own erroneous summary of the v0.11.6 toolbar cleanup,
  not a fresh user instruction. The user wanted only download /
  upload buttons removed; auto-layout was meant to stay.
- **What replaces this:** [D-2026-05-10-E](#d-2026-05-10-e--auto-layout-restored-as-mindmap-style-directional-tree) —
  auto-layout restored with a proper handle-aware directional-tree
  spec.
- **Lesson encoded into Gate 0:** assistant-summarised "이해?"
  questions are not user confirmations of the underlying claim. A
  decision id requires the user to **affirmatively** approve the
  precise behaviour, not nod along to the assistant's paraphrase.
- **Approval:** **Rejected** by user, 2026-05-10. The original
  "Accepted (removal)" line from 2026-05-04 stands as a historical
  record of the misattribution.
- **Spec impact:** [`SPEC.md` §Auto-layout](./SPEC.md#auto-layout) —
  rewritten by D-2026-05-10-E.

---

### D-2026-05-04-E — Hover handles only fade in lightly

- **What:** Connection handles stay invisible at rest; fade to
  `opacity: 0.55` while the cursor is on the node body; only become
  fully opaque + scaled when the cursor lands directly on a handle.
- **Why:** the prior behaviour (all four handles pop to full opacity +
  scale 1.35× the moment the cursor enters the node) felt noisy and
  read as "the node is constantly inviting a connection".
- **Alternatives:** keep prior behaviour (rejected — noisy); hide
  handles entirely until a modifier key (rejected — too hidden,
  discoverability suffers).
- **Approval:** **Accepted** by user, 2026-05-04 — implicitly.
- **Spec impact:** [`SPEC.md` §Hover behaviour](./SPEC.md#hover-behaviour).

---

### D-2026-05-04-F — ⚠ badge contrast bumped

- **What:** Change MD-warning badge from `bg-amber-100 text-amber-800
  ring-amber-300` to `bg-white text-amber-700 ring-amber-500 shadow-sm`
  so it stays legible on cream / pastel-orange / pastel-yellow card
  backgrounds.
- **Why:** the prior amber-on-amber palette nearly disappeared into
  the Mission and CoreValue card colours.
- **Alternatives:** stronger amber fill (rejected — competes with
  card colour); red fill (rejected — overstates severity for a
  fixable parse warning).
- **Approval:** **Accepted** by user, 2026-05-04 — implicitly.
- **Spec impact:** [`SPEC.md` §⚠ Markdown-template warning badge](./SPEC.md#-markdown-template-warning-badge).

---

### D-2026-05-04-G — Defensive viewport CSS

- **What:** Add `h-screen min-h-screen` to the outermost shell `<div>`
  and `min-height: 100vh / 100dvh` fallbacks on `html, body, #root`.
- **Why:** user reported the canvas not filling top-to-bottom in
  their browser, even though Playwright measurement showed the
  existing `height: 100%` chain was correct. Defensive doubling
  (`100vh` + `100dvh`) costs nothing in clean cascades and rescues
  edge cases (mobile-style viewports, iframe embeds, dev-tools
  docking).
- **Alternatives:** require user to share a screenshot before
  changing anything (rejected as too slow — defensive CSS is cheap);
  do nothing (rejected — user reported a real symptom).
- **Approval:** Pending — user has not yet confirmed whether their
  browser symptom resolved after the change.
- **Spec impact:** [`SPEC.md` §Viewport](./SPEC.md#viewport).

---

### D-2026-05-05-A — SPEC + DECISIONS files exist; comments are not spec

- **What:** Introduce `mashbill/docs/SPEC.md` (Foundation only, for now)
  and `mashbill/docs/DECISIONS.md` (this file). Future UI / behaviour
  changes must reference an entry in one of these.
- **Why:** session-to-session work was not accumulating: every
  session re-relitigated the same trade-offs because the prior
  session's decisions lived only in code comments (which were not
  agreed) or in the assistant's working memory (which doesn't
  survive). The fix is a single canonical place where every
  behavioural decision is written down with date + rationale +
  approval status.
- **Approval:** **Accepted** by user, 2026-05-05.
- **Spec impact:** none — meta-rule about how decisions are recorded.

---

### D-2026-05-05-B — Architecture violation acknowledged: god components

- **What:** Acknowledge that today's viewer code violates the
  project's own structural rule (project CLAUDE.md: "Review for
  splitting when a file exceeds 500 lines") and the user's stated
  design principles (global CLAUDE.md: SOLID / SRP / Clean
  Architecture / DDD).
- **Evidence (measured 2026-05-05, post-v0.13.2):**
  - `viewer/src/canvases/SketchCanvas.tsx` — **1476 lines, 40 hooks,
    ≥13 distinct responsibilities** (node transforms, edge
    transforms, anchor sync, click→Inspector routing, three context
    menus, keyboard shortcuts, drag-and-drop, overlap nudging,
    value-flow toggle, collapsed-tree state, orphan ref detection,
    Service-Detail modal routing, undo/redo glue).
  - `viewer/src/canvases/SketchInspector.tsx` — **1422 lines.**
  - `viewer/src/App.tsx` — **791 lines.**
  - `viewer/src/canvases/SketchStencil.tsx` — **523 lines.**
- **Why this matters:** today's hover bug, today's edge regressions,
  and the recurring "small change here breaks something over there"
  pattern are symptoms of the god-component shape — every concern
  shares the same closure scope, so changes have unbounded blast
  radius. CSS-only fixes (today's hover tone-down) cover the
  symptom without fixing the cause.
- **Decision:** **No new responsibilities are added to
  SketchCanvas.tsx, SketchInspector.tsx, App.tsx, or
  SketchStencil.tsx until each is split.** New behaviour goes into
  new files. Existing-file edits must reduce or maintain LOC, never
  grow.
- **Plan:** see [`ARCHITECTURE.md`](./ARCHITECTURE.md) — responsibility
  inventory + candidate split boundaries. Actual split happens in a
  subsequent session, in plan mode, with user approval of the chosen
  boundary.
- **Approval:** Pending — user has agreed the violation exists and
  asked for the inventory; the chosen split boundary is **not yet
  approved**.
- **Spec impact:** none on behaviour SPEC; lives in ARCHITECTURE.md.

---

### D-2026-05-05-C — `mashbill/CLAUDE.md` for practical guidance

- **What:** Create `mashbill/CLAUDE.md` translating the global / project
  core principles (SOLID, Clean Architecture, SRP, SSOT, AHA, YAGNI,
  TDD, "임시 통과 금지", "추측 금지", etc.) into Novel-specific
  *practical* checklists, triggers, and commands the assistant must
  follow inside the `plot/` subtree.
- **Why:** the principles are theoretical and live two directories
  up; in-session, the assistant defaults to "do the change" without
  consulting them. A Novel-local file with concrete triggers ("before
  editing SketchCanvas.tsx, do X") makes the principles operational.
- **Approval:** **Accepted** by user, 2026-05-05.
- **Spec impact:** none — meta rule about how the assistant operates
  inside `plot/`.

---

### D-2026-05-08-G — Node decoration must coincide with the hit-box (no `outline` / `ring`)

- **What:** Replace the three node-decoration class strings in
  `SketchNode.tsx` with `border` equivalents. Old: `outline …
  outline-offset-2 ring-1 …` (anchor) / `outline outline-1 …`
  (regular) / `outline outline-2 outline-indigo-500` (selected).
  New: `border-2 border-slate-600` / `border border-slate-300` /
  `border-2 border-indigo-500`.
- **Why — the diagnosis the previous rounds missed:** v0.13.3 and
  v0.13.4 unified the cursor inside the node and on the pane to
  `pointer` and `default` respectively. DOM probing showed a
  single cursor inside the node region. Yet the user still saw
  `pointer ↔ default` flicker on a slow mouse-move across a
  single node. The reason is that **`outline` paints outside the
  border-box and is excluded from hit-testing.** Pixels under the
  outline (and inside the `outline-offset` gap) look like they
  belong to the node, but a hit-test there resolves to the parent
  `.react-flow__pane` (cursor: default). For the anchor, the
  flicker zone was 8–10 px wide. For regular nodes (1 px outline)
  it was sub-pixel-perceivable.
- **The general rule (recorded for every future node-styling
  change):**
  > Visual extent and hit-box of an interactive node must
  > coincide. Use `border` (border-box, hit-tested) rather than
  > `outline` / `outline-offset` / `ring` / outset
  > `box-shadow` for any decoration on `.react-flow__node`,
  > `.react-flow__handle`, or any clickable element. Inset
  > `box-shadow` is fine — it paints inside the box and doesn't
  > affect hit-testing.
- **Verified:** `getBoundingClientRect()` on the
  `.react-flow__node` and its inner decorated `<div>` returns
  identical x/y/w/h after the change (banas-v013 anchor:
  710.875, 636.062, 206.54×206.54). Single distinct cursor =
  `pointer` across the entire node tree.
- **Approval:** Accepted by user, 2026-05-08 (plan approved
  before commit).
- **Spec impact:** SPEC §Anchor "Visual differentiation" row
  updated to reference `border` instead of outline + offset +
  ring. The general rule is also added to `mashbill/CLAUDE.md`
  anti-patterns.

---

### D-2026-05-08-F — Handles appear only when the node is selected

- **What:** Removed the hover-fade and direct-handle-scale animations
  on `.react-flow__handle`. Handles are now `opacity: 0` until the
  node is selected (`.react-flow__node.selected`), at which point
  they appear at full opacity with the indigo "connectable"
  styling.
- **Why:** the user reported "커서였다가 검지였다가 큰 검지였다가
  작은 검지였다가 등등" — the cursor itself appearing to vary in
  size / shape as it moved across a node. DOM-level cursor probing
  showed only `pointer` and `default` were ever set; the perceived
  variation was the four handle dots pulsing in opacity (0 →
  0.55 on node-hover) and one of them scaling to 1.25× on direct
  handle-hover. The dots near the pointer reading as "cursor".
- **What this changes for the user:**
  - To draw an edge: click a node first (selects it; handles
    appear). Then drag from a handle. One extra click vs. before.
  - Hovering a node now never changes the visual at all. The node
    just sits there. Selecting (clicking) is the explicit gesture
    that opens both Inspector and edge-drawing handles.
- **Approval:** Pending — matches the user's evolving "노드 선택할
  수 있게만" direction (D-2026-05-08-E) plus this round's flicker
  diagnosis. User can override if the extra click feels
  too costly.
- **Spec impact:** SPEC §Hover behaviour rewritten — three states
  collapse to two (hidden / selected), no more fade / scale.

---

### D-2026-05-08-E — Pan-on-drag removed; cursor stays pointer on click

- **What:** Three paired changes (the third was discovered after
  the user said "같아" to the first two — pure prop disable
  wasn't enough; the baseline CSS still set `grab`):
  - **`panOnDrag={false}` on `<ReactFlow>`.** Grabbing an empty
    canvas region and dragging no longer pans the viewport.
    Zoom / fit-view controls (bottom-left) and the minimap remain
    the only ways to move the view.
  - **CSS override on `.react-flow__pane` / `.react-flow__viewport`
    / `.react-flow__renderer` to `cursor: default !important`.**
    React Flow's baseline stylesheet keeps `cursor: grab` on the
    pane / viewport even when `panOnDrag` is off, which
    reintroduced the cursor flicker (grab over canvas ↔ pointer
    over node) that the user reported.
  - **Removed `.react-flow__node:active { cursor: grabbing }`
    rule.** Clicking a node previously flipped the cursor to
    grabbing for a frame even on a pure click (no drag); that
    competed with the v0.13.4 hover invariant ("on a node the
    cursor is `pointer`, period"). The
    `.react-flow__node.dragging` rule is kept so an actual drag
    still surfaces grabbing.
  - **Removed `cursor-text` from the EditableText display span**
    (separate but-related fix in the same commit). The display
    span is `role="button"` (click to enter edit mode) and now
    uses `cursor-pointer`. Previously hovering the label flipped
    the cursor to I-beam — the user described it as
    "보자기 / 가위 계속 바뀌는" (paper / scissors swapping).
- **Why:** user said exactly:
  > "노드 위에 커서 올리면 노드 선택할 수 있게만하고 캔버스 쥐고
  > 옮기는 동작을 없애세요"
  — when the cursor is on a node, only "select" should read; and
  the canvas grab-and-move action should be removed.
- **What we kept:** `nodesDraggable={true}`. The user did not ask
  to remove node drag; only the *visual signal* that the node
  was draggable on hover. They keep the position-control they've
  always wanted; the cursor just doesn't advertise it on every
  click.
- **Approval:** Accepted by user, 2026-05-08.
- **Spec impact:** SPEC §Pan and select (new), §Hover behaviour
  (clarified cursor invariant).

---

### D-2026-05-08-D — SketchCanvas split: stop at 360 LOC (not 150)

- **What:** The SketchCanvas split lands at 360 LOC, not the
  plan's 150-LOC design target.
- **Why stopped:** The plan's "ideal shell ≈ 150 LOC" was
  aspirational. Realistic floor for the current shell shape is
  ~330 LOC, broken down as:
  - ~50 LOC imports (16 sketch hooks + reactflow + types)
  - ~55 LOC `SketchCanvasProps` interface with JSDoc — the
    component's public API surface; cannot compress without
    losing documentation
  - ~10 LOC component setup (refs + 2 modal-id useStates)
  - ~140 LOC hook composition (12 hooks × ~10 LOC each for
    args + destructured returns)
  - ~15 LOC `handleNodesChange` shell (must stay in shell
    per the coupling map)
  - ~80 LOC JSX render block (ReactFlow root + Toolbar +
    SketchModals + Inspector + ContextMenu)
- **Further compression would mean** introducing a
  `useSketchCanvasModel(props)` umbrella hook that returns ~30
  fields the JSX consumes — exactly the **Candidate B
  controller pattern rejected in D-2026-05-08-A**. Going there
  now would re-concentrate the previously-decomposed concerns
  into a single 30-output return value, undoing the SRP win.
- **Net result:** SC went from **1476 LOC → 360 LOC (76%
  reduction)**. The original violation (CLAUDE.md "Review for
  splitting when a file exceeds 500 lines") is resolved with
  140-LOC headroom. 16 extracted modules under
  `canvases/sketch/` each have a single responsibility and
  unit-testable surface (4 of them — `nodeTransform`,
  `edgeTransform`, `overlapNudge`, `applyAnchorChange`,
  `nodeChanges`, `useOrphanActorRefs`,
  `useCollapsedTree.toggleCollapsed` — are pure or
  near-pure modules).
- **Approval:** Pending — user can override and request the
  controller-hook step if the 360-LOC floor is unacceptable.
- **Spec impact:** none.

---

### D-2026-05-08-C — Cursor-flicker fix on node hover

- **What:** Set `.react-flow__handle { cursor: pointer }` (matching
  the node body), restoring `cursor: crosshair` only when a
  connection is actively being drawn
  (`.react-flow__handle.connecting` / `.connectingfrom`).
- **Why:** moving the mouse across a node would flicker the cursor
  between `pointer` (node body, our rule) and `crosshair` (React
  Flow's default handle cursor). The user described it as "보자기 /
  가위 계속 바뀌는" — paper / scissors swapping — which was visually
  noisy and made the canvas feel jittery.
- **Why this isn't another bandaid:** the v0.13.2 hover tone-down
  (D-2026-05-04-E) reduced the *visual* prominence of handles but
  left React Flow's default `cursor: crosshair` rule untouched.
  That CSS default is the real source of the flicker — making the
  cursor invariant deterministic across the whole node region is
  the actual fix, not a fade.
- **What we kept:** crosshair during active edge drawing — that's
  semantic (the user IS doing something crosshair-shaped). And
  `cursor: grabbing` on `:active` when a drag actually starts.
- **Approval:** Pending — user requested the fix, ship and confirm.
- **Spec impact:** SPEC §Hover behaviour now codifies the cursor
  invariant explicitly.

---

### D-2026-05-08-B — Step 5 deviation: hook only, no pure node-transform module

- **What:** Plan called for Step 5 to extract two files —
  `nodeTransform.ts` (pure, no React) plus a thin `useNodesMemo.ts`
  wrapper. Implementation ships only `useNodesMemo.ts` (a single
  React hook).
- **Why:** the node transform reads ten-plus callbacks
  (`updateNode`, `setBodyModalNodeId`, `onNodeDrill`,
  `onAnchorChange`, plus collapsed-tree's four exports) and
  produces per-node closures (`onLabelChange`, `onResize`,
  `onToggleCollapse`, `onDrill`). A "pure" version would still
  require those callbacks as inputs — the purity would be
  cosmetic, paid for in a 10-field input interface and a
  React-aware wrapper that mostly just shuffles arguments. AHA
  ("avoid hasty abstraction") + YAGNI.
- **What this gives up:** node transform is not unit-testable in
  isolation today. If a future use case needs that (e.g. snapshot
  testing thousands of doc shapes), the hook can be split then —
  one rewrite is cheaper than the wrong abstraction now.
- **What this preserves:** edge transform (Step 6) is still split
  pure + thin-hook. Edges have far fewer callbacks (one: edge
  modal open) so the pure form is genuinely useful.
- **Approval:** Pending — recorded as a same-day execution decision;
  user can override and request the pure node-transform split if
  they want.
- **Spec impact:** none.

---

### D-2026-05-08-A — SketchCanvas split: Candidate A (modified)

- **What:** Split `plot/viewer/src/canvases/SketchCanvas.tsx` (1476
  LOC, 16 concerns) down to a thin React Flow shell (target ≈ 150
  LOC, hard ceiling 200 LOC) using **Candidate A modified**: surgical
  responsibility split per ARCHITECTURE.md, with the two pure
  transforms (nodes / edges) and overlap math extracted as plain
  `.ts` modules (no React imports) — borrowing Candidate B's domain
  purity for the parts where it actually fits.
- **Why:**
  - Candidate B (Clean Architecture controller) rejected: would
    re-concentrate `docRef`'s 19+ read sites into one
    `useSketchController.ts` — same god scope, different filename.
    The pure-transform win is real but only for two of 16 concerns,
    so we cherry-pick that part.
  - Candidate C (mechanical 4-file split) rejected: trades visible
    LOC for unchanged coupling. The next bug still has 1476-LOC
    blast radius across 4 files, just spread thinner.
  - Candidate A surgically isolates the 5 easy concerns (memos,
    inspector routing, value-flow, collapse, orphan) into
    single-purpose hooks, and keeps React Flow's prop wiring in the
    shell where it must live (per coupling map: `onNodesChange`,
    `onEdgesChange`, etc. need single handlers).
- **Plan:** see [`/Users/woogis/.claude/plans/wiggly-herding-pixel.md`](../../../.claude/plans/wiggly-herding-pixel.md)
  — Pre-Step 0 (test baseline) + Steps 1–14 (extraction in
  risk-ascending order), each commit-sized and browser-verified per
  the matrix.
- **Layout:** new files under `plot/viewer/src/canvases/sketch/`.
  16 files total (10 hooks + 4 pure modules + 1 modal component +
  1 shell remainder).
- **Approval:** **Accepted** by user, 2026-05-08.
- **Spec impact:** none on behaviour. Some load-bearing comments
  surface as new SPEC entries before extraction (Steps 5/7/9/11)
  per the plan's "Comments policy".

---

### D-2026-05-10-A — Pan re-enabled; canvas reads as a pannable surface again

- **What:** `panOnDrag` flipped back to `true` on the React Flow
  surface, and the v0.13.4 `cursor: default !important` override on
  `.react-flow__pane` / `.react-flow__viewport` /
  `.react-flow__renderer` is removed so React Flow's native
  `cursor: grab` (idle) and `cursor: grabbing`
  (`.react-flow__pane.dragging`) take effect.
- **Why:** the user reports — quoted directly — *"노드 밖에 호버
  했을 때 보여야하는 손바닥 커서가 안생기구요."* The absence of a
  hand cursor on the empty canvas read as the surface being inert
  (a "page", not a "canvas"), which conflicted with the user's
  workflow of moving the viewport to inspect different regions of
  the project graph. The v0.13.4 reasoning ("users were
  accidentally panning while clicking nodes") is reversed by the
  4 px `nodeDragThreshold`: clicks short of 4 px on a node still
  register as clicks (Inspector opens), and drags on the empty
  pane unambiguously start panning. There is no behaviour collision
  to disambiguate.
- **Methodology — probe before fix for the lingering flicker:** the
  user *also* reports — *"노드 위에 올라가면 화살표하고 검지모양
  커서가 깝박 거리고 있어요."* — that the arrow ↔ pointer flicker
  on nodes persists after v0.13.5. Five rounds of cursor work have
  fixed five distinct localised sources, but a pervasive source
  remains. Per the mashbill/CLAUDE.md "추측 금지" / "임시 통과 금지"
  rules, the v0.13.6 ship deliberately splits in two: Part 1 (this
  decision — pan reverse) ships immediately because it is
  spec-driven and definite; Part 2 (find and fix the pervasive
  flicker) requires a live-DOM probe in the user's real browser
  before any node-cursor code changes. The probe script and its
  expected outcomes are recorded in
  [`/Users/woogis/.claude/plans/wiggly-herding-pixel.md`](../../../.claude/plans/wiggly-herding-pixel.md).
- **Alternatives:**
  - "Hand cursor visual only, no pan" — rejected as user-hostile
    (a misleading affordance is worse than a missing one).
  - Keep pan off + a different visible cursor (e.g. `default`) —
    user explicitly asked for the hand back AND for the pan, so
    no daylight between visual and behaviour.
- **Approval:** **Accepted** by user, 2026-05-10 (plan approved
  before commit).
- **Spec impact:** [`SPEC.md` §Pan and select](./SPEC.md#pan-and-select)
  — rewritten from "does not pan" to "pans on empty-pane drag".
  [`SPEC.md` §Cursor states](./SPEC.md#cursor-states-canvas-wide-ssot-applies-to-every-canvas)
  — new section establishing the canvas-wide cursor SSOT (later
  rewritten in D-2026-05-10-C).
  [`mashbill/CLAUDE.md`](../CLAUDE.md) anti-patterns — new row banning
  the "force `cursor: default` on the pane to suppress flicker
  while disabling pan altogether" pattern.

---

### D-2026-05-10-B — Force-pointer on every node descendant — Rejected (rolled back same session)

- **What proposed:** Add
  `.react-flow__node *:not(.react-flow__handle):not(.react-flow__resize-control) { cursor: pointer !important }`
  to `styles.css` so every descendant of a node shows `pointer`,
  killing the "anywhere on the node" arrow-flicker the user kept
  reporting.
- **Why proposed:** Symptomatic fix when the diagnostic probe
  approach (D-2026-05-10-A Part 2) felt too slow.
- **Why rolled back:** As soon as the user saw the cursor
  table I had drafted, they pushed back — *"정리한게 이상하지
  않아요?"* / *"커서 동작 다 정리해보세요 일단."* — and on a
  follow-up cleanup request, *"RF 디폴트로 일단 가세요. 거기서
  부터 다시 시작하죠. 코드 정리 제대로 하구요."* The force-pointer
  rule was the latest in a six-round cursor-override stack
  (v0.13.3-v0.13.6 Part 1) where each round papered over a
  prior round's regression. The user's call: stop adding
  overrides, restart from the React Flow vendor baseline, then
  decide what (if anything) to deviate from. See D-2026-05-10-C.
- **Approval:** **Rejected** by user, 2026-05-10 (rolled back in
  the same session before commit).
- **Spec impact:** None — the override never shipped. The
  D-2026-05-10-A entry was edited to remove the
  D-2026-05-10-B forward reference.

---

### D-2026-05-10-C — Reset all RF cursor / handle overrides; restart from vendor baseline

- **What:** Remove **every** custom cursor / handle / handle-size /
  handle-colour CSS rule from `viewer/src/styles.css`. The file now
  contains only the html/body/#root sizing block. All cursor
  behaviour comes from `node_modules/reactflow/dist/style.css` and
  `node_modules/@reactflow/node-resizer/dist/style.css` directly.
  Also remove the `cursor-pointer` Tailwind class from
  `EditableText.tsx`'s display span — the label inherits from the
  node, which under RF default is `grab`.
- **Why:** Six rounds of cursor / handle interventions
  (D-2026-05-04-E hover-fade, D-2026-05-08-C handle-cursor unify,
  D-2026-05-08-E pan-off + label cursor-text removal, D-2026-05-08-F
  handles-on-select, D-2026-05-08-G border-replaces-outline,
  D-2026-05-10-A pan re-enable) shipped overrides on top of
  overrides. Each fix solved one localised symptom and revealed or
  introduced another. After the user's *"정리한게 이상하지 않아요?"*
  / *"RF 디폴트로 일단 가세요"* feedback, the structural problem
  is plain: the override stack itself is the regression engine,
  not any single rule in it. Removing the whole stack and
  restarting from the vendor baseline gives us:
  - **One known state** to reason from. Future "what should the
    cursor be on X?" questions answer themselves by reading the
    vendor CSS.
  - **No flicker by construction.** RF's baseline puts `cursor:
    grab` on both `.react-flow__pane` and `.react-flow__node` —
    the cursor literally cannot change when crossing the boundary.
  - **One predictable mental model for the user.** RF's "anything
    draggable shows `grab`; active drag shows `grabbing`; drawing
    a connection shows `crosshair`; resizing shows the directional
    resize cursor" is uniform and well-known across all React Flow
    deployments.
- **What we kept (not part of this reset):**
  - v0.13.6 Part 1 pan re-enable (`panOnDrag` on, no
    `cursor: default !important` override on the pane). That
    matches RF default and stays.
  - v0.13.5 border-replaces-outline on the inner node decoration.
    That decision is about *visual extent matching the click
    target*, not about cursor — clicks on the visible decoration
    must select the node, not pass through to the pane. Keeps.
  - SketchCanvas split (D-2026-05-08-A) and all other
    architecture / behaviour decisions unrelated to cursor.
- **One single rule retained — Tailwind preflight cancellation:**
  Tailwind's preflight forces `cursor: pointer` on every
  `<button>` and `[role="button"]`. The fold button and the
  EditableText label span (`role="button"`) inside a node match
  these selectors and re-introduce the very flicker this reset
  was meant to kill — node hover = `grab` (RF), label hover =
  `pointer` (Tailwind). To honor RF's "node = uniform grab"
  contract, `styles.css` keeps a **single** rule:
  ```css
  .react-flow__node *:not(.react-flow__handle):not(.react-flow__resize-control) {
    cursor: inherit;
  }
  ```
  This is not an override of RF — it is an override of *Tailwind
  preflight* that restores the RF inheritance chain inside the
  canvas. The :not() exclusions preserve RF's own semantic cursors
  on connection handles (crosshair) and resize controls
  (directional resize). This is the only cursor rule in
  `styles.css` and may not grow without a fresh decision id.
- **What this rolls back:**
  - `.react-flow__node { cursor: pointer }` (was D-2026-05-08-C).
  - `.react-flow__node.dragging { cursor: grabbing }` (was redundant
    with RF default).
  - `.react-flow__handle { width 10px / height 10px / opacity 0 / 1.5px slate-400 border / white background / cursor: pointer !important }` (was D-2026-05-08-F + earlier).
  - `.react-flow__node.selected .react-flow__handle { opacity 1 / indigo border + bg }` (was D-2026-05-08-F).
  - `.react-flow__handle.connecting / .connectingfrom { cursor: crosshair !important / opacity 1 / indigo border }` (was D-2026-05-08-C — RF default already covers this via `.connectionindicator`).
  - `EditableText` display span `cursor-pointer` class (was D-2026-05-08-E).
- **Cursor behaviour after this reset** — see
  [`SPEC.md` §Cursor states](./SPEC.md#cursor-states-canvas-wide-ssot-applies-to-every-canvas).
  In one sentence: hover anywhere on the canvas (pane or node) =
  `grab`; drag (pane or node) = `grabbing`; hover a connection
  handle = `crosshair`; hover an edge = `pointer`; hover a resize
  control = directional resize cursor.
- **Future deviation rule:** any new cursor / handle override must
  open a fresh `D-YYYY-MM-DD-X` entry with explicit user approval
  *and* a comment in the CSS rule naming that decision id. The
  override stack must never grow without an audit trail.
- **Approval:** **Accepted** by user, 2026-05-10 — *"RF 디폴트로
  일단 가세요. 거기서부터 다시 시작하죠. 코드 정리 제대로 하구요."*
- **Spec impact:** [`SPEC.md` §Hover behaviour](./SPEC.md#hover-behaviour)
  rewritten from "handles only when selected, cursor pointer
  everywhere" to "RF defaults, handles always visible". [`SPEC.md`
  §Cursor states](./SPEC.md#cursor-states-canvas-wide-ssot-applies-to-every-canvas)
  rewritten to mirror the vendor CSS exactly. [`mashbill/CLAUDE.md`](../CLAUDE.md)
  anti-patterns updated.

---

### D-2026-05-10-D — Gate 0: user confirmation pins the spec immediately

- **What:** Add a new pre-action gate at position 0 (before the
  existing Gate 1) in [`mashbill/CLAUDE.md`](../CLAUDE.md). The gate
  fires on a fixed keyword set in the user's message
  (`승인합니다 / 좋아요 / 네 좋아요 / 됐다 / 이제 됐다 / 맞아요`,
  English equivalents) and forces the assistant, before any other
  tool call, to: (1) state the confirmed behaviour in one
  declarative sentence, (2) update `docs/SPEC.md` so its text
  matches the confirmation pixel-identically, (3) append a
  `D-YYYY-MM-DD-X` entry to this file with `Accepted by user,
  YYYY-MM-DD`, and (4) stage SPEC + DECISIONS into the current
  commit cycle (or a docs-only follow-up if the implementing
  commit already shipped).
- **Why:** This is a structural fix for the "work doesn't
  accumulate across sessions" pattern the user has flagged
  repeatedly. The v0.13.3 → v0.13.6 cursor work is the canonical
  motivating example — six rounds of cursor changes because each
  confirmed behaviour evaporated before reaching the spec, so the
  next session re-asked questions the user had already answered.
  The user's exact framing this session: *"plot 의 claude.md 에
  제품의 스펙이 확정되면 문서에 반영한다는 룰이 있어야할 것
  같구요."*
- **Why these specific keywords (not a free-form trigger):**
  Concrete `literal-string-match` triggers are far more reliably
  applied by the assistant than vague conditions like "behaviour
  changed". The list is closed and short on purpose. New
  approval-style phrasings can be added later via a follow-up
  decision id; do not silently expand the list.
- **Why "before any other tool call":** Without an ordering
  constraint, the assistant defers SPEC updates to the next
  message, then forgets, then ships an implementation commit
  with no spec line to back it. The "before any other tool call"
  language matches the same fail-fast severity as `behavior:
  부분 완료 → 금지` in the global CLAUDE.md.
- **Banned shortcuts (encoded in the gate body):** deferring to
  "next session"; assuming the SPEC line exists without verifying
  the diff; batching multiple confirmations into one update;
  treating an unclear confirmation as implicit (must explicitly
  ask the user instead).
- **Approval:** **Accepted** by user, 2026-05-10 — *"네 좋아요"*
  in response to the proposed Gate 0 draft. This decision entry
  is itself the first application of Gate 0.
- **Spec impact:** None on product spec. This is an operational
  rule change in `mashbill/CLAUDE.md`. SPEC.md remains the canonical
  product behaviour spec; Gate 0 is the discipline that keeps it
  in sync with reality.

---

### D-2026-05-10-E — Auto-layout restored as mindmap-style directional tree — **Rejected (rolled back v0.14.1, 2026-05-10)**

> Originally Accepted 2026-05-10 (this entry). Rolled back the same
> day in v0.14.1 — see [D-2026-05-10-G](#d-2026-05-10-g--auto-layout-removed-again-cost-vs-benefit).
> Original entry preserved below for the historical record.

- **What:** Bring back an "Auto layout" button on the
  `<SketchToolbar>`. Implementation is a custom directional-tree
  algorithm rooted at the canvas anchor, grouping each node's
  children by the parent-side handle of the connecting edge:
  - `R` handle ⇒ child stacked in a vertical column to the right.
  - `L` handle ⇒ child stacked in a vertical column to the left.
  - `T` handle ⇒ child placed in a horizontal row above.
  - `B` handle ⇒ child placed in a horizontal row below.
  Spacing uses Reingold-Tilford-style subtree-extent tracking to
  guarantee no node-to-node overlap. Tree edges follow a BFS
  spanning tree from the anchor; cycle-closing edges are drawn but
  ignored for placement. Node-id ordering breaks ties for full
  determinism. Result is applied via `onDocChange` so it lands in
  the standard undo stack.
- **Why this shape (not radial / not force-directed):** the user's
  two binding constraints are *"오른쪽에 연결된 노드들을 오른쪽에
  정렬해야하고 (아래로 정렬하면 안됨), 위쪽에 있는건 위쪽에 정렬"*
  (handle direction is strict — the side a child connects from is
  the side it lands on) and *"노드들이 서로 겹치지 않게"* (no
  overlap, period). Radial layouts (e.g. d3 `tree()` with polar
  coordinates) violate the first because they distribute children
  evenly around 360° regardless of which handle was used.
  Force-directed layouts (e.g. d3-force) violate the first because
  edge directionality has no preferred axis in the simulation.
  A custom directional tree is the smallest algorithm that hits
  both constraints exactly.
- **Why no library:** the four-direction grouping is unconventional
  enough that no off-the-shelf layout library matches without
  significant adaptation. The pure algorithm fits in one ~150-LOC
  module under `plot/viewer/src/canvases/sketch/autoLayout.ts`
  with no new runtime dependency.
- **Why anchor stays put:** moving the anchor would yank the entire
  visual centre of the canvas every time the user runs auto-layout.
  Keeping it fixed lets the user position the anchor manually once
  and use auto-layout to clean up everything around it.
- **Why BFS spanning tree (not full graph layout):** the spec
  promises *no edge crossings in the spanning tree* — that's only
  achievable on an actual tree. Cycles in the user's graph are
  collapsed to a tree by BFS; the leftover edges are drawn as
  cross-links so the user still sees them. Crossings on
  cross-links are unavoidable on graphs with cycles and are
  acknowledged in the spec.
- **Why no animation, no preview:** explicit user requirement is
  that auto-layout be predictable. Single-click → instant re-layout
  → `Cmd+Z` if you don't like it. Adding animation or preview
  introduces a moment where the user is staring at an in-progress
  layout and can't tell whether to trust it.
- **Approval:** **Accepted** by user, 2026-05-10 — *"네 일단
  해봐요"* on the proposed spec table.
- **Spec impact:** [`SPEC.md` §Auto-layout](./SPEC.md#auto-layout) —
  fully rewritten from "Removed" to the directional-tree spec
  above.

---

### D-2026-05-10-F — Cursor flicker root cause: `[role="button"]` on `.react-flow__node`; Auto layout button moved to lower-left Controls

Two related fixes shipped together because the user surfaced both
in the same browser-verification round:

#### Part 1 — Tailwind preflight cancellation on `.react-flow__node[role="button"]`

- **What:** Add `.react-flow__node[role="button"] { cursor: grab }`
  (and its `.dragging` companion → `grabbing`) to `viewer/src/styles.css`.
- **Why — root cause finally identified:** v0.13.3-v0.13.6 chased
  cursor flicker through six rounds and *every diagnosis was wrong*.
  The actual cause: **React Flow v11 sets `role="button"` on
  `.react-flow__node` itself** for accessibility. Tailwind preflight
  `[role="button"] { cursor: pointer }` matches that element directly,
  which overrides the RF-default `cursor: grab` *on the node* and
  then propagates pointer down the inheritance chain. The v0.13.6
  reset's premise ("RF default is grab; just remove our overrides")
  was correct in theory but Tailwind preflight had been silently
  shadowing it the whole time. Verified empirically via Playwright
  DOM probe — walking the parent chain from a span inside a Mission
  node showed `cursor: pointer` originating at the
  `.react-flow__node` element, not at any of our descendant rules.
- **Verification:** post-fix Playwright sweep across the entire
  canvas grid (50px sample × 22 columns × 21 rows) returned only
  three distinct cursors anywhere: `grab` (pane + every node body),
  `auto` (SVG inside MiniMap, never user-interactive), `not-allowed`
  (disabled toolbar buttons). No `pointer` on any node body. No
  cursor changes when crossing between pane and node.
- **Why this didn't surface earlier:** every prior round assumed
  the cursor cascade stopped at our rules vs RF defaults. Nobody
  walked the actual DOM tree to find that Tailwind was injecting
  via an attribute selector neither our code nor RF documentation
  highlighted. The fix took 30 seconds once the cause was known;
  the prior six rounds spent ~60 minutes of round-trip on wrong
  diagnoses. Process lesson: probe the live DOM **first**, theorise
  **second**.

#### Part 2 — Auto layout button moved from `<SketchToolbar>` to React Flow `<Controls>`

- **What:** Move the v0.13.9 Auto layout `IconBtn` (top-right
  toolbar) into the React Flow `<Controls>` panel at lower-left,
  rendered as a `<ControlButton>` below zoom / fit / lock.
- **Why:** the user grouped auto-layout mentally with view-state
  controls (zoom / fit) rather than mutation actions (undo / redo).
  Direct quote: *"정렬은 그리고 왼쪽 아래에 핏하는거하고 같은 곳에
  넣어도 되요. 오른쪽 상단에 둘 필요 없음."* Lower-left is also where
  the user's eye already goes for camera-related operations.
- **What this preserves:** the algorithm itself is unchanged from
  D-2026-05-10-E; only the trigger UI moved. Disabled state still
  fires when no anchor exists or when the canvas has no non-anchor
  nodes.

#### Process change implied for future sessions

- **First step on any cursor / hit-test bug = Playwright DOM probe**,
  not code reading. CURSOR.md's probe script is the canonical
  starting point. Walking the parent chain from
  `document.elementFromPoint` is mandatory before proposing a fix.
- **Tailwind preflight is a hidden source of cursor regressions.**
  It applies to attribute selectors (`[role="button"]`, `[disabled]`)
  that interact silently with vendor library accessibility
  attributes. CURSOR.md's anti-patterns table now includes this
  failure mode.

- **Approval:** **Accepted** by user, 2026-05-10.
- **Spec impact:** [`SPEC.md` §Cursor states](./SPEC.md#cursor-states-canvas-wide-ssot-applies-to-every-canvas)
  — augmented to mention BOTH preflight cancellation rules (v0.13.6
  for descendants, v0.13.10 for the node element itself).
  [`SPEC.md` §Auto-layout — Trigger and undo](./SPEC.md#auto-layout)
  — button location updated to lower-left Controls panel.
  [`CURSOR.md`](./CURSOR.md) updated.

---

### D-2026-05-10-G — Auto-layout removed again — cost vs benefit

- **What:** Remove auto-layout from Novel in v0.14.1. Delete
  `viewer/src/canvases/sketch/autoLayout.ts`,
  `viewer/src/canvases/sketch/useAutoLayout.ts`, and the unit test
  file. Drop the `<ControlButton>` invocation in `SketchCanvas.tsx`
  along with its imports. Revert the regression test from
  v0.13.9-inverted ("auto layout button MUST exist") back to its
  v0.13.8 form ("auto layout button MUST NOT exist").
- **Why (user):** *"근데 auto layout 빼야겠네 문제가 너무 많다. 넣고
  나서 커서 들에 문제 너무 많고."* User cost/benefit assessment
  after observing the feature in action: the value of auto-layout
  at this stage of Novel does not justify the complexity / debugging
  load it added across v0.13.8 → v0.14.0.
- **Honest correction on causation:** the user attributed the cursor
  flicker problems to auto-layout temporally ("after adding it,
  cursor problems were too many"). The actual root cause was
  unrelated — RF v11 sets `role="button"` on `.react-flow__node`
  which Tailwind preflight matched and overrode the RF default
  `cursor: grab` (see [D-2026-05-10-F](#d-2026-05-10-f--cursor-flicker-root-cause-rolebutton-on-react-flow__node-auto-layout-button-moved-to-lower-left-controls)).
  The Tailwind preflight cancellation rule shipped in v0.13.10 fixes
  the cursor flicker independently and remains in place after this
  removal. Removing auto-layout therefore does not undo any cursor
  fix — it simplifies the canvas surface.
- **Why the user's call still stands despite the misattribution:** the
  removal is a separate cost/benefit decision. Even if cursor was
  the trigger to revisit, the broader argument ("the feature added
  too much complexity for too little user value at this stage")
  applies on its own merits. Novel has no users with complex
  multi-actor / multi-service graphs yet; the value of auto-layout
  is theoretical until then. When real users surface a clear need,
  re-introduction can be weighed afresh with concrete user
  workflows in mind.
- **What stays:** the v0.13.10 cursor fix
  (`.react-flow__node[role="button"] { cursor: grab }` + the
  descendant inheritance rule). Novel v0.14.1 has no cursor flicker;
  pane and node both show `grab`, transitions are clean.
- **Re-introduction policy:** any future "let's bring back
  auto-layout" proposal must (a) open a fresh `D-YYYY-MM-DD-X` entry,
  (b) cite specific real-user workflows that demand it, (c) include
  a cost/benefit comparison against this entry's reasoning, and
  (d) get explicit user approval before any code lands. The
  D-2026-05-04-D / D-2026-05-10-E / D-2026-05-10-G oscillation in
  this DECISIONS log is itself the cautionary tale.
- **Approval:** **Accepted** by user, 2026-05-10 — *"빼야겠네"*
  (in response to assistant's offer to verify Foundation behaviour
  next).
- **Spec impact:** [`SPEC.md` §Auto-layout](./SPEC.md#auto-layout)
  rewritten back to "Removed", with the full history paragraph
  preserving the lineage of decisions D-2026-05-04-D →
  D-2026-05-10-E → D-2026-05-10-F → D-2026-05-10-G so future
  sessions can read the saga in one place.
- **Files removed:**
  - `viewer/src/canvases/sketch/autoLayout.ts`
  - `viewer/src/canvases/sketch/useAutoLayout.ts`
  - `viewer/tests/autoLayout.test.ts`
- **Files reverted:**
  - `viewer/src/canvases/SketchCanvas.tsx` (drop ControlButton + useAutoLayout)
  - `viewer/tests/SketchCanvas.regression.test.tsx` (re-invert auto layout assertion)

---

### D-2026-05-11-A — Pure RF default cursors (revert all cancellation rules); remove MiniMap

- **What:** Two related simplifications shipped in v0.14.2.
  1. **Cursor:** Remove every cursor rule from
     `viewer/src/styles.css`. The v0.13.6 (D-2026-05-10-C) and
     v0.13.10 (D-2026-05-10-F) Tailwind preflight cancellation rules
     are gone. `styles.css` now contains only `@tailwind` imports +
     `html/body/#root` sizing. Resulting cursors come purely from
     React Flow defaults + Tailwind preflight composition.
  2. **MiniMap:** Remove the `<MiniMap zoomable pannable />` from
     `viewer/src/canvases/SketchCanvas.tsx` (and its import). No
     more bottom-right overview.
- **Why (user):** *"일단 RF 기본으로 돌리라구요. 이해를 못하지?"* —
  the user's core mental model has been "pointer on clickable node,
  crosshair on draw-from handle, grab on pannable pane" all along.
  v0.13.6 and v0.13.10 added cancellations to force `node = grab`
  (RF's nominal default) but that contradicted the user's intent.
  Pure RF default + Tailwind preflight COMPOSES to exactly what the
  user wants:
  - `.react-flow__node` (RF v11 sets `role="button"`) → preflight
    overrides RF's `grab` to `pointer`.
  - EditableText label span (`role="button"` for keyboard a11y) →
    preflight `pointer`.
  - Fold `<button>` → preflight `pointer`.
  - `.react-flow__pane` → RF default `grab`.
  - `.react-flow__handle.connectionindicator` → RF default
    `crosshair`.
  - Resize controls → vendor defaults.
  Verified empirically via Playwright DOM probe at multiple
  coordinates after the revert.
- **Lesson encoded for future sessions:** The assistant repeatedly
  added cancellation rules to "fix" Tailwind preflight matching RF's
  attribute-based selectors. The user's preference was always to
  let preflight + RF compose naturally. Four iterations of this
  mistake (v0.13.5 / v0.13.6 / v0.13.10 / v0.14.2) should have been
  one. Heuristic for future Novel cursor work: **default to NO
  cursor rules in `styles.css`. Only add a rule when a real,
  Playwright-probed user complaint cannot be explained by Tailwind
  + RF interaction.**
- **Anchor asymmetry note:** anchor body shows `grab` (because the
  anchor uses a static `<span>`, no `role="button"`) while the
  other Foundation nodes show `pointer` (EditableText). Acceptable
  per this decision; if a future requirement demands anchor =
  pointer too, a single focused rule + new decision id.
- **Approval:** **Accepted** by user, 2026-05-11 — *"이제 됐네 자
  문서들 업데이트하구요."* User additionally requested MiniMap
  removal in the same exchange (*"오른쪽 아래에 있는 오버뷰? 이거
  없애요."*) which is bundled here.
- **Spec impact:**
  - [`SPEC.md` §Cursor states](./SPEC.md#cursor-states-canvas-wide-ssot-applies-to-every-canvas)
    — fully rewritten to "pure RF default + Tailwind preflight, no
    overrides" with the new cursor table and the anchor-asymmetry
    note.
  - [`CURSOR.md`](./CURSOR.md) — cancellation sections removed,
    "no overrides — pure RF default + Tailwind preflight" section
    added; change-history updated.
  - [`SPEC.md`](./SPEC.md) — MiniMap removed from the implicit
    canvas surface inventory (no explicit MiniMap section existed,
    so no rewrite needed beyond noting in CHANGELOG).
- **Files touched:**
  - `viewer/src/styles.css` — strip cursor rules.
  - `viewer/src/canvases/SketchCanvas.tsx` — remove `MiniMap` import + JSX.

---

### D-2026-05-11-B — Architectural concern: auto-layout work bled into cursor code (review next session)

- **What (user observation):** *"지금 문제는 오토레이아웃을
  넣어달라고 했는데 이거 때문에 커서 관련된 코드에 영향을 받는거에요.
  이거 잘못된거죠. 완전히 다른 영역인데 영향을 받는다? 이거 설계를
  잘못한거에요. 다음세션에서 심층적으로 검토하고 개선할 수 있게
  해두세요."*
- **Why this matters:** Cursor (visual contract for the canvas
  surface) and Layout (positioning algorithm) are two independent
  concerns. The fact that v0.13.8 → v0.14.1 auto-layout work
  triggered ~6 cursor regressions demonstrates that the codebase
  does not isolate these contexts. Per
  [`DOMAIN.md`](./DOMAIN.md): cursor is a cross-cutting visual
  contract; layout belongs to `EssencePlanning`. They should not
  share files, mutation paths, or runtime state. Today they do.
- **Trigger for next session:** When the user says **"다음"** in a
  Novel session start, this entry's "Review scope" below becomes
  the active task. The SessionStart hook surfaces this trigger
  via [`mashbill/docs/NEXT_SESSION.md`](./NEXT_SESSION.md) — see
  there for the full review scope and execution plan.
- **Approval:** **Accepted** by user, 2026-05-11 (instruction
  to record + execute next session).
- **Spec impact:** No immediate code change. Spec impact from the
  next-session review goes into a follow-up D-YYYY-MM-DD-X entry
  once the architectural fix is designed.

---

### D-2026-05-11-C — cursor ⊥ auto-layout: cognitive coupling, not mechanical; structural gate added

- **What:** The "cursor was broken by auto-layout work" review
  (queued in D-2026-05-11-B + NEXT_SESSION.md, fired by the
  user saying "다음") concludes that the coupling was
  **cognitive (commit bundling), not mechanical (shared files)**.
  Verified empirically against the v0.13.7..v0.14.2 git history:
  - `viewer/src/styles.css` (cursor SSOT) was not modified by any
    auto-layout commit (v0.13.8 docs, v0.13.9 impl, v0.14.1 revert).
  - `autoLayout.ts` / `useAutoLayout.ts` were not modified by any
    cursor commit (v0.13.10, v0.14.2).
  - The only mechanical intersections were `SketchCanvas.tsx`
    (shell, 359 LOC, well within the 500-line rule) and
    `SketchToolbar.tsx` (button-location decision) — both edits
    touched disjoint JSX regions.
  - v0.13.10 commit ("cursor flicker root cause + auto-layout
    button placement") bundled both concerns in one atomic commit;
    this is the cognitive coupling vector.
  - Cursor flicker existed since v0.13.0 (RF v11's `role="button"`
    + Tailwind preflight `[role="button"] { cursor: pointer }`
    collision) — auto-layout was the *trigger for discovery*, not
    *insertion*. D-2026-05-10-G already records this causal
    correction; this entry generalises the lesson.

  Structural gate ships in v0.14.3 with three orthogonal
  enforcement mechanisms:
  1. `mashbill/hooks/pre_commit_gate.py::cross_cutting_bundle_check`
     denies any commit that stages `viewer/src/styles.css`
     (cross-cutting visual SSOT) alongside feature code under
     `viewer/` or `mashbill/`. Tests are excluded from the
     "feature" category so test-with-target shipping stays normal.
  2. `viewer/tests/styles-cursor-baseline.test.tsx` asserts
     `styles.css` has zero cursor declarations outside comments.
     Adding one requires a fresh D-id and updating the test
     together — making the audit trail mechanical.
  3. `mashbill/agents/mashbill-verifier.md` Step 4 default now runs the
     cursor DOM probe sweep FIRST on every viewer change,
     regardless of declared change kind. A latent cursor
     regression hidden behind an unrelated feature commit fails
     verification.

  `mashbill/CLAUDE.md` anti-patterns table gains a row pointing here.

- **Why this matters:** Cursor (cross-cutting visual contract) and
  Layout (`EssencePlanning` algorithm per
  [`DOMAIN.md`](./DOMAIN.md)) cannot share a natural domain
  home. DOMAIN.md line 205 already records this correctly:
  *"Cursor SSOT | Cross-cutting | OK as-is — visual contract has
  no natural domain home."* The right enforcement layer is
  **commit hygiene + static guard + verification default**, not
  domain re-modelling.
- **Alternatives considered and rejected:**
  - (a) Extract `cursorContract.ts` module — rejected: `styles.css`
    is currently 27 LOC with zero cursor rules (post-v0.14.2).
    Empty abstraction violates YAGNI.
  - (b) Pre-commit gate via shell hook in `.git/hooks/` instead
    of `pre_commit_gate.py` — rejected: noory-ai CLAUDE.md
    "Cross-Platform Compatibility" bans shell scripts; the Novel
    hook already runs through `pre_commit_gate.py` PreToolUse.
  - (c) Add cursor as a separate bounded context in DOMAIN.md —
    rejected: DOMAIN.md line 205 already explicitly decided
    cursor is cross-cutting with no domain home. Adding a context
    would contradict that decision.
  - (d) Refactor `useNodesMemo` / `useEdgesMemo` to isolate
    transient runtime state — rejected: the ghost-edge symptom
    from v0.13.9 testing was resolved by D-2026-05-10-G
    (auto-layout removal). No live problem to refactor for.
- **Honest premise correction:** the original D-2026-05-11-B
  framing implied a mechanical coupling between cursor and
  auto-layout files. Phase 1 analysis showed this was wrong —
  the files never shared territory. The architectural review
  therefore targets the real failure mode (commit bundling +
  latent visual bugs surfacing during feature verification)
  rather than the named one (cursor ↔ auto-layout file
  coupling). User confirmed this re-framing during the 2026-05-10
  session.
- **Approval:** Pending — user, 2026-05-10.
- **Spec impact:** none. Structural / process change with no
  observable Novel behaviour difference.

---

### D-2026-05-11-D — i18n infrastructure (English primary, Korean locale)

- **What:** Bootstrap i18n in the Novel viewer using `react-i18next`
  + `i18next` + `i18next-browser-languagedetector`. New module
  `viewer/src/i18n/` owns the resource bundles
  (`locales/en.json` + `locales/ko.json`), the `init()` call
  (imported from `main.tsx` for side effects), and the
  `LanguageToggle` component rendered at the bottom of
  `SketchSidebar`. First-batch migrations: `SketchToolbar` (Undo /
  Redo + tooltips) and `SketchSidebar` (project list controls,
  rename / delete confirmations, session-tags section). All
  remaining hardcoded UI text is queued for follow-up commits.

  Static guards shipped:
  - `viewer/tests/i18n-keys-parity.test.ts` — asserts `ko.json`
    has the identical key set as `en.json` and that every value is
    a non-empty string. Locale drift = test fail.
  - `mashbill/CLAUDE.md` anti-patterns table gains a row blocking
    hardcoded UI text.

  Detection order is `localStorage["plot:lang"] → navigator.language
  → en`. User choice persists across sessions.

- **Why:** User direction (2026-05-10):
  > "우리는 로컬라이즈도 신경 써야합니다. 이건 글로벌 서비스가
  > 될거거든요."

  Establishes the global-service identity recorded in
  `feedback_plot_global_service.md`. Domain-boundary + SSOT must be
  strict from inception (user CLAUDE.md "design"); deferring i18n
  to a "later" milestone would compound hardcoded-text sprawl and
  force a high-cost retrofit.

- **Library choice rationale:** `react-i18next` (over a custom
  ~50 LOC wrapper or `lingui`):
  - Mature production stack; well-documented React hooks API.
  - Supports interpolation (`{{name}}`), pluralization, namespaces
    out of the box — needed within months as the UI surface
    grows.
  - Standard pattern for the global-service identity; ~30KB cost
    is acceptable for a viewer that already ships Mermaid +
    React Flow + React Markdown.
  - User explicitly selected this option via AskUserQuestion.

- **Scope limit (first commit):** Only the most visible toolbar +
  sidebar strings migrate in v0.14.4. The rest of the viewer
  (Inspector forms, Stencil labels, App-level toasts, context
  menus, modals) will migrate in subsequent commits. The
  anti-pattern row + the parity test prevent NEW hardcoded text
  from appearing in the meantime.

- **Approval:** Pending — user, 2026-05-10.
- **Spec impact:** none observable beyond the new language toggle
  pill in the sidebar's footer. No canvas behaviour changes.

---

### D-2026-05-11-E — Product spec pinned as PRODUCT_SPEC.md; product framing now lives above VISION

- **What:** User delivered a Novel product spec mid-session
  (2026-05-11) covering platforms (Claude plugin → macOS app),
  business model (individual free / enterprise paid, PLG growth),
  tech stack (React Flow / JSON / Markdown / Mermaid / MCP), data
  principles (JSON SoT, owner field, MD export targets), Figma-style
  symbol system, four canvas layers with audience split (humans vs
  agents), agent-interview UX pattern, snapshot work-item layer,
  PR-style feedback loop, MVP scope, future / out-of-scope.

  Per user direction *"이건 잘 정리해두세요. 작업 다 끝나고"*, the
  spec is pinned to [`plot/docs/PRODUCT_SPEC.md`](../../../plot/docs/PRODUCT_SPEC.md)
  as a new canonical document. Translated to English (per
  noory-ai CLAUDE.md "Language" rule), reorganised into AI-First
  structured sections with cross-references to existing docs.

- **Why this matters:** product-level facts (who Novel is for, what
  platforms, what's in MVP, what's deferred) were scattered across
  conversation history and partially in VISION.md. Consolidating to
  one file gives every future session a single place to read the
  framing before touching code. Without it, the next session is
  liable to re-litigate decisions that already have a user mandate.

- **Position in the doc set:** PRODUCT_SPEC sits **above** VISION.md.
  VISION is the essence; PRODUCT_SPEC is how the essence becomes a
  shippable product. `mashbill/CLAUDE.md` reading order updated to put
  PRODUCT_SPEC as step 2 (right after VISION, before DOMAIN).
  `VISION.md` Cross-references updated to point at PRODUCT_SPEC
  first.

- **What this does NOT do:**
  - Does NOT change code. No new fields on `SketchNode`, no canvas
    splits, no new MCP tools.
  - Does NOT change the existing doc files beyond cross-link
    insertion. SPEC, CONCEPTS, ROADMAP, DOMAIN unchanged.
  - Does NOT decide the open questions captured in §16 of
    PRODUCT_SPEC (Mission/Identity canvas split, PR-loop
    enforcement, snapshot subsystem, Mermaid rendering, owner field
    landing date). Each becomes its own follow-up `D-YYYY-MM-DD-X`
    when the user calls.

- **Alternatives considered and rejected:**
  - **Fold the product spec into VISION.md** — rejected: VISION's
    "one sentence at the top" discipline (D-pre-VISION) breaks if
    platform / business-model / MVP detail gets bolted on. Two
    files, clear roles.
  - **Distribute the spec content across existing docs** (Mermaid
    → ROADMAP, owner field → CONCEPTS, snapshot → SPEC, …) —
    rejected: scatter violates SSOT and makes the framing hard to
    read in one session. PRODUCT_SPEC is the framing; the other
    docs implement it.
  - **Skip pinning, treat as conversation memory only** — rejected:
    explicitly contradicts the user instruction *"이건 잘
    정리해두세요"*.

- **Approval:** Pending — user, 2026-05-11.
- **Spec impact:** SPEC.md unchanged (PRODUCT_SPEC is upstream).
  VISION.md gains a Cross-references entry. mashbill/CLAUDE.md reading
  order updated to include PRODUCT_SPEC as item 2.

---

### D-2026-05-12-A — PRODUCT_SPEC.md revision 2: mindmap/graph split, isomorphic-git, Foundation single canvas, MD-as-export queued

- **What:** User delivered a substantially revised product spec
  on 2026-05-12 (full text recorded in the conversation). The
  spec changes flowing into `plot/docs/PRODUCT_SPEC.md` rev 2:
  1. **§1 — Language split.** Novel is a "mindmap" to users,
     "graph" internally. Internal model supports cycles +
     self-loops; trees alone don't fit.
  2. **§4 — `isomorphic-git` added** to the tech stack.
  3. **§5 — "Cycles allowed"** explicit. Self-loops legal.
  4. **§6 — Source-data version control (new section).**
     Novel's *content* (canvas JSON, user stories, tasks) is git-
     versioned, isolated from any source-code git the user
     happens to be in. Snapshot ≡ commit. Agent proposal ≡
     branch. User approve ≡ merge. User reject ≡ branch delete.
     GitHub remote integration is a future option.
  5. **§8 — Mission / Core-value / Identity → one canvas.** The
     v0.14.7 open question (#2) "split or keep one canvas?" is
     resolved by the user: keep one. Audience distinction
     (human-facing for Mission + Core value; agent-facing for
     Identity) is visual, not structural.
  6. **§8 — Service-Detail starts empty.** Fills bottom-up
     through the agent-interview + user-story loop. Living
     document framing.
  7. **§9 — Service interview produces two artefacts.** Service-
     Detail content AND user-story draft, sharing provenance.
  8. **§10 — Snapshot ≡ commit SHA**, formalising the link
     between the work-item layer and §6.
  9. **§11 — Feedback loop is git-branch shaped** per §6.
  10. **§13 — GitHub integration** added to future items.
  11. **MVP section removed.** The rev-1 "MVP scope" framing is
      gone; the user has moved past pre-launch scope discussion.
  12. **§15 Open questions reorganised.**
      - Closed: Mission/Identity canvas split (resolved in §8).
      - Added: MD-as-export migration (Phase 2; the v0.13 co-
        equal MD becomes a derived export). User direction:
        *"이 부분은 나중에 다시 다듬어 봅시다."* Deferred.
      - Added: isomorphic-git integration timing.
      - Added: i18n string lifecycle skill (delete unused keys).
      - Added: Novel repository split (move out of noory-ai
        monorepo).
- **Why:** The product framing matures. Cycles + git + bottom-up
  service-detail + branch-shaped agent proposals are concrete
  enough now to commit. Open items either have a clear
  deferral marker or a clear future plan.
- **Approval:** Pending — user, 2026-05-12 (delivered spec
  verbatim, no further confirmation requested).
- **Spec impact:** PRODUCT_SPEC.md fully rewritten (rev 2). No
  immediate code change. The MD-as-export shift (§15 #2) and the
  git integration (§15 #3) are large enough to need their own
  D entries when work begins. SPEC.md / CONCEPTS.md / ROADMAP.md
  unchanged — each will get its own update when the queued items
  land.
- **Files:** `plot/docs/PRODUCT_SPEC.md` (rev 2), this entry.

---

### D-2026-05-12-B — Structural reset planned: v0.15.0 = domain layer + entity classes + componentisation

- **What:** Capture the architectural-debt diagnosis the user
  surfaced at the end of the 2026-05-12 session and queue the
  v0.15.0 structural reset as the next session's top priority.
  Old backlog items (i18n audit, Mermaid, owner field, repo
  split, isomorphic-git, MD-export, snapshot layer, v0.15 Actors
  migration) are PARKED until the reset lands.

  User direct quotes:
  - *"파운데이션에서 사용되는 커서 컨트롤하고 액터나
    서비스에서 사용되는 커서 컨트롤이 다릅니다. 코어 원칙이
    지켜지고 있지않아요. 이게 진짜 문제인거에요. 개발을 잘
    못하고 있는거거든요. 이건 당장해야하는거에요."*
  - *"엔티티 정의도 안되어 있구요."*
  - *"기본을 못하고 있는겁니다."*
  - *"코드 재활용 할 수도 없게 해뒀어요. JSON을 직접 건드리고
    있는게 아닌지 모르겠네요. fromJson, toJson 같은걸 쓰고
    클래스를 코드로 만들어서 개념화해야 했다."*
  - *"도메인 레이어 설계가 제대로 되어 있는지도
    모르겠구요."*
  - *"이런 작업들을 다음 세션에 해야해요."*
  - *"필요하다면 스킬이나 룰을 만들구요."*

- **Code evidence supporting the critique (verified 2026-05-12):**

  | Probe | Result |
  |---|---|
  | `viewer/src/types.ts:174` comment | Self-admits *"The runtime payload is still SketchNode (god interface)"* |
  | `grep -rE "fromJson\|toJson\|parse(\|serialize("` in viewer/src | **0 hits** (JSON.parse / stringify excluded) |
  | `grep -rE "^class \|^export class "` in viewer/src | **0 hits** |
  | `find viewer/src -type d \| grep -iE "domain\|entit\|model"` | No directory |
  | `types.ts` 305 LOC | 100% type / interface declarations; zero methods, zero invariants |
  | `SketchInspector.tsx` | 1422 LOC, kind-branching for every typed field |
  | `SketchCanvas.tsx` | 359 LOC, one god component for 3 canvas tabs via `doc.canvas_kind` runtime discriminator |

  The viewer has **no domain layer** in the Clean-Architecture /
  DDD sense. It has a god TypeScript interface (`SketchNode`)
  holding every kind's flat fields, no JSON↔domain boundary, no
  per-kind entity classes, no per-canvas components, no per-kind
  Inspector modules. The v0.13 "Phase 5 discriminated union" is
  cosmetic aliases only (per the `types.ts:174` comment); runtime
  is still god.

- **Why this matters:** the rule violation is explicit. Both:
  - User CLAUDE.md `architecture: Clean Architecture, DDD`, and
  - Memory `feedback_no_god_object.md` non-negotiable rule:
    *"kind 별 클래스 + Pydantic/TS discriminated union 비협상.
    한 클래스에 모든 kind 필드 = 디자인 실패."*

  The 9 i18n / UI cleanup commits shipped this session
  (v0.14.3–v0.14.12) are paint on top of the god object. They
  do not fix the structural problem and they make further
  surface work increasingly fragile.

- **What ships in v0.15.0 (planned, multi-session):**

  - **Phase A — Domain entity classes** in
    `viewer/src/domain/`. 15 per-kind classes (Mission /
    CoreValue / Identity / Actor / ActorRef / Service /
    Category / MissionRef / ValueRef / IdentityRef / Metric /
    Step / Rule / Content / Project), each with kind-specific
    fields only + `static fromJson` / `toJson` / invariants.
    `domain/SketchNode.ts` = discriminated union. `domain/CanvasDoc.ts`
    = `Canvas` class.
  - **Phase B — Server alignment** with
    `mashbill/models.py` Pydantic.
  - **Phase C — Inspector kind fan-out.** Split
    `SketchInspector.tsx` into per-kind inspectors.
  - **Phase D — Canvas componentisation.** `FoundationCanvas`,
    `ActorsCanvas`, `ServicesCanvas`, `ServiceDetailCanvas` as
    separate components.
  - **Phase E — Cursor / interaction contracts per canvas.**
  - **Phase F — Verification.** Per-canvas cursor sweep +
    per-kind Inspector smoke + entity-shape round-trip test.

  Done criteria: `viewer/src/domain/` has ≥ 15 entity classes,
  UI components do not import god `SketchNode`, per-canvas
  cursor sweeps return identical allow-listed inventories,
  `SketchInspector.tsx` reduces to dispatch shell (≤ 300 LOC) or
  is removed.

- **Skills / rules to consider** (user-allowed: *"필요하다면
  스킬이나 룰을 만들구요"*), discussed at session start:
  - `mashbill/skills/mashbill-entity-template/`
  - `mashbill/skills/mashbill-domain-design/`
  - Pre-commit hook `no-god-import` (block god `SketchNode`
    import in new viewer files post-Phase-A)
  - Vitest entity-shape round-trip test
  - `mashbill/CLAUDE.md` anti-pattern row: *"Treating raw JSON as
    domain entity (no fromJson boundary)."*

- **Honest correction on prior commits:** The 9 i18n / UI
  cleanup commits this session were technically clean but they
  delivered surface polish on top of a known god object. The
  god object is documented in `types.ts:174` and in
  `feedback_no_god_object.md` — the assistant did not surface
  this debt earlier in the session and proceeded with surface
  work. Better behaviour next session: when a feedback rule
  says "비협상" and the codebase visibly violates it, surface
  the debt BEFORE adding more surface work, not after the user
  flags it.

- **Approval:** Pending — user, 2026-05-12 (the user delivered
  the diagnosis + the *"다음 세션에 해야해요"* + the
  *"필요하다면 스킬이나 룰을 만들구요"* permission).
- **Spec impact:** No PRODUCT_SPEC change. No SPEC.md /
  CONCEPTS.md / DOMAIN.md change yet — those will update when
  Phase A lands (CONCEPTS.md in particular). NEXT_SESSION.md
  trigger queue: `구조 리셋` / `v0.15` / `도메인` / `엔티티`
  all surface this entry's plan.
- **Files in this commit:**
  - `mashbill/docs/NEXT_SESSION.md` — new active queue entry.
  - `mashbill/docs/DECISIONS.md` — this entry.
  - `~/.claude/projects/.../memory/project_plot_next_session.md`
    — full plan + skill/rule candidates.

---

### D-2026-05-12-C — Cursor uniformity audit: 4 wrappers verified equivalent (Phase 4.1)

- **What:** Empirical confirmation, after v0.15 reset Phases 1-3,
  that the 4 canvas wrappers (Foundation / Actors / Services /
  ServiceDetail) produce a uniform cursor inventory. Pinned via a
  new JSDOM-side sweep (`viewer/tests/cursor-sweep.test.tsx`) +
  the existing static guard (`styles-cursor-baseline.test.tsx`).

- **Why:** the v0.15 reset was fired by the user's complaint
  *"파운데이션에서 사용되는 커서 컨트롤하고 액터나 서비스에서
  사용되는 커서 컨트롤이 다릅니다"* (D-2026-05-12-B). With Phase 3
  routing every wrapper through one SketchCanvas + NODE_RENDERERS +
  BaseNode pipeline, that complaint can be answered empirically.

- **Audit evidence (verified 2026-05-12 by static + DOM sweep):**

  | Probe | Result |
  |---|---|
  | `grep -rn "cursor:" viewer/src/canvases/ viewer/src/edit/` | **0 hits** outside Tailwind utility classes |
  | Tailwind `cursor-*` utility usage | Only in chrome files (`SketchStencil.tsx`, `SketchContextMenu.tsx`, `SketchToolbar.tsx`, `SketchEdgeModal.tsx`, `inspectors/DetailsSection.tsx`) — shared across all 4 wrappers |
  | `grep -rEn "style\.cursor\|cursor\s*=" viewer/src/` | **0 hits** |
  | `viewer/src/styles.css` cursor declarations | **0** (already guarded by `styles-cursor-baseline.test.tsx` since D-2026-05-11-C) |
  | `viewer/src/canvases/nodes/{kind}/index.tsx` (15 per-kind renderers) | All wrap `BaseNode`; zero per-kind cursor overrides |
  | `viewer/src/canvases/inspectors/{kind}/index.tsx` (15 per-kind inspectors) | All wrap `BaseInspector`; zero per-kind cursor overrides |
  | Wrapper files (Foundation/Actors/Services/ServiceDetail) | 16-23 LOC each; props-only thin shells over a shared `SketchCanvas` |
  | DOM sweep — 4 wrappers seeded with same doc | Identical `react-flow__*` class skeletons (pane, renderer, viewport, …); zero inline `style.cursor` on any element |
  | DOM sweep — 4 wrappers seeded with all 15 kinds | Zero inline `style.cursor` on any node, anywhere |

  Cursor inventory is therefore determined exclusively by the three
  shared stylesheet sources documented in
  [`docs/CURSOR.md`](./CURSOR.md):
  1. React Flow vendor CSS (`reactflow/dist/style.css`).
  2. `@reactflow/node-resizer` vendor CSS.
  3. Tailwind preflight (`@tailwind base;` injecting
     `button, [role="button"] { cursor: pointer }`).

  None of these is per-canvas; all four wrappers compose the same
  three layers. Per-canvas cursor drift is structurally impossible
  with the post-Phase-3 code.

- **Alternatives considered:**
  - **Playwright sweep** (per original Phase 4.1 plan): would run
    real `getComputedStyle()` in Chromium. **Rejected** for this
    audit because (a) the static + DOM proof above is exhaustive
    given the cursor SSOT is entirely in CSS / vendor stylesheets,
    (b) Playwright adds ~300 MB browser binaries + a separate test
    runner that no other Novel test relies on, and (c) the user-runnable
    DevTools recipe in `docs/CURSOR.md` §"How to verify the cursor
    state in the browser" (lines 197-215) is the appropriate
    sensory confirmation when the user wants one. If a future
    drift report turns out to need live `getComputedStyle()`
    evidence, this decision can be reversed with a follow-up
    `D-YYYY-MM-DD-X` entry.
  - **Per-canvas Tailwind `cursor-*` allowlist guard** (folded
    into Phase 4.2): the wrapper files contain zero Tailwind
    cursor utility classes today; Phase 4.2 will pin that as a
    static guard so a future addition fails the build with a
    decision-id prompt.

- **Approval:** Pending user confirmation. Audit findings + the
  JSDOM sweep test were chosen as the verification mechanism
  per "make the reasonable call, the user will redirect"
  direction at session start. If the user reads this entry and
  wants the live-browser sweep too, that becomes Phase 4.1.5 and
  reuses the same fixture + `seedAllKinds()` helper.

- **Spec impact:** none — `docs/CURSOR.md` already documents the
  cursor SSOT; this audit confirms the post-Phase-3 code satisfies
  it. `docs/SPEC.md §Cursor states` likewise unchanged.

- **Files in this commit:**
  - `plot/viewer/tests/cursor-sweep.test.tsx` — new JSDOM sweep
    (8 tests: zero-inline-cursor across 4 wrappers on empty + all-15-kinds
    seeds; react-flow class-skeleton equivalence across the 4
    wrappers; per-kind node renderer no-cursor checks).
  - `mashbill/docs/DECISIONS.md` — this entry.
  - `mashbill/CHANGELOG.md` — v0.15.7 section.
  - `mashbill/.claude-plugin/plugin.json` — patch bump 0.15.6 → 0.15.7.

---

### D-2026-05-12-D — Extend cursor-baseline guard to all canvas-internal files (Phase 4.2)

- **What:** Extend ``viewer/tests/styles-cursor-baseline.test.tsx``
  from a 1-test ``styles.css`` guard to a 129-test static sweep
  that asserts ZERO raw ``cursor:`` declarations and ZERO
  ``style.cursor =`` JS assignments across every canvas-internal
  source file:
  - 4 wrapper files (Foundation / Actors / Services / ServiceDetail).
  - Shared shell: SketchCanvas, BaseNode, BaseInspector,
    KindInspector, DetailsSection, the two registries, inspectors/types.
  - 15 per-kind node renderers under ``canvases/nodes/{kind}/``.
  - 15 per-kind inspectors under ``canvases/inspectors/{kind}/``.
  - inspectors/shared/* (composition helpers).
  - All sketch hooks under ``canvases/sketch/`` (~17 files).
  Plus a registry-size sanity (15 per-kind node + 15 per-kind
  inspector dirs).

- **Why:** D-2026-05-12-C established that, *as of today*, cursor
  inventory is uniform across the 4 wrappers. The job of this
  decision is to make the property **structurally permanent** —
  any future edit that introduces a per-canvas cursor rule fails
  the build with a pointer to this decision id and a forced choice:
  either (a) open a new ``D-YYYY-MM-DD-X`` entry and update
  ``docs/CURSOR.md`` (the documented escape hatch per
  D-2026-05-11-A §"How to deviate"), or (b) keep cursor inventory
  uniform.

- **What the guard does *not* match:** Tailwind utility class
  strings (``cursor-grab``, ``cursor-not-allowed``,
  ``cursor-pointer``, ``cursor-grabbing``, ``active:cursor-grabbing``,
  ``disabled:cursor-not-allowed``) — the regex ``cursor\s*:``
  requires a literal ``cursor:`` (colon-suffixed), while utility
  classes are ``cursor-<state>`` (hyphen-suffixed). This is by
  design: those utilities appear on chrome surfaces
  (``SketchStencil`` drag tray, ``SketchContextMenu`` items,
  ``SketchToolbar`` buttons, ``SketchEdgeModal`` form rows,
  ``DetailsSection`` button) that are shared identically across
  all 4 wrappers and are not part of the canvas/node/edge cursor
  contract. Adding the same Tailwind utility to a wrapper or a
  per-kind file would still pass this guard but immediately fail
  the DOM-equivalence test in
  ``viewer/tests/cursor-sweep.test.tsx`` if the resulting class
  composition differs from the other wrappers.

- **Alternatives considered:**
  - **Allowlist per-file overrides via inline marker comments**
    (e.g. ``/* eslint-cursor-override D-... */``): rejected as
    YAGNI. The escape hatch is "open a new decision id and update
    ``docs/CURSOR.md``"; if a future override is needed, it warrants
    deliberate human decision, not a per-line comment.
  - **Ban Tailwind ``cursor-*`` utility classes from canvas files
    too** (not just raw ``cursor:`` declarations): tempting for
    extra strictness, but the chrome usage in
    ``DetailsSection.tsx`` (``disabled:cursor-not-allowed``) is
    correct UX feedback for an interactive button. The line
    between "chrome inside an inspector body" and "canvas surface"
    is the per-kind inspector file boundary, not the
    inspectors/-tree boundary, and is already covered: any per-kind
    inspector that *adds* a cursor utility will live in
    ``inspectors/{kind}/index.tsx`` which the new guard *does*
    scan — so it would have to use a raw ``cursor:`` declaration
    (caught) or a ``style.cursor =`` JS assignment (caught). Pure
    utility class additions would slip through the guard but be
    immediately visible in the cursor-sweep DOM test, which would
    show the class on the per-kind node DOM and break the
    skeleton-equivalence assertion.
  - **Live-browser Playwright sweep** (per original Phase 4.1
    plan): see D-2026-05-12-C §Alternatives. Same rationale.

- **Approval:** Pending — same direction as D-2026-05-12-C.

- **Spec impact:** none — ``docs/CURSOR.md`` already declares the
  cursor SSOT; this decision makes the SSOT *unbypassable in code*.

- **Files in this commit:**
  - ``plot/viewer/tests/styles-cursor-baseline.test.tsx`` —
    extended from 1 test to 129 (1 styles.css + 128 from it.each
    across the canvas files).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.15.8 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.15.7 → 0.15.8.

---

### D-2026-05-12-E — Exhaustive 15-kind smoke + round-trip sweeps (Phase 5.1)

- **What:** Add three parametric ``it.each`` / ``parametrize`` suites
  that exhaustively iterate over the 15-way node-kind union:

  - **Viewer ``KindInspector`` smoke** —
    ``viewer/tests/inspectors/inspectors.exhaustive.test.tsx``
    (30 tests = 15 kinds × { non-null tree, no console.error }).
  - **Viewer entity round-trip** —
    ``viewer/tests/domain/round-trip.exhaustive.test.ts``
    (45 tests = 15 kinds × { parseEntity dispatches, idempotent
    round-trip, kind preservation }).
  - **Server adapter sweep** — appended to
    ``mashbill/tests/test_node_models.py`` (31 tests = 15 kinds ×
    { adapter dispatches to right class, round-trip idempotent } +
    1 union-size sanity).

- **Why:** Phase 2's per-kind asserts in
  ``inspectors.smoke.test.tsx`` + ``round-trip.test.ts`` +
  ``test_node_models.py`` cover every kind by hand. The new
  parametric suites pin the *contract*: if a future commit adds a
  16th kind and forgets to register an inspector or a parseEntity
  branch or a Pydantic class, the sweep fails immediately with
  the offending kind in the test name. Same goal as the per-kind
  ``it.each`` cursor guard in D-2026-05-12-D — make per-kind
  drift impossible without a test failure.

- **Alternatives considered:**
  - **Delete the hand-written per-kind tests** in
    ``inspectors.smoke.test.tsx`` + ``round-trip.test.ts`` now
    that the exhaustive sweep covers them: rejected. The
    hand-written tests check kind-specific edge cases (e.g.
    ``CategoryInspector`` empty-warning, ``ActorRefInspector``
    orphan rendering, ``Service`` composition list) that a
    structural sweep can't enumerate. They stay; the sweep is
    *additive*.
  - **Use a snapshot test** to capture each kind's full Inspector
    DOM: rejected as brittle. A snapshot fires on every benign
    Tailwind class reshuffle; we want failure only when the
    structural contract breaks.

- **Approval:** Pending — same direction as D-2026-05-12-C / -D.

- **Spec impact:** none — internal verification scaffolding.

- **Files in this commit:**
  - ``plot/viewer/tests/inspectors/inspectors.exhaustive.test.tsx``
    — new (30 tests).
  - ``plot/viewer/tests/domain/round-trip.exhaustive.test.ts`` —
    new (45 tests).
  - ``mashbill/tests/test_node_models.py`` — appended exhaustive
    sweep section (31 new tests).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.15.9 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.15.8 → 0.15.9.

---

### D-2026-05-12-F — Structural guards: no-god-import + LOC budget + registry-completeness (Phase 5.2)

- **What:** Pin three structural contracts that protect the v0.15
  reset's shape against regression:

  1. **no-god-union-import** — the deleted god files
     (``SketchInspector.tsx``, ``SketchNode.tsx``) must remain
     absent from disk, and no ``switch (X.kind)`` god dispatch may
     appear in the 4 wrappers, App.tsx, SketchCanvas, BaseNode,
     BaseInspector, KindInspector, DetailsSection, or any sketch
     hook. (The single legitimate ``switch (kind)`` lives in
     ``domain/createBlankNode.ts`` — the per-kind factory; per-kind
     narrowing guards inside ``inspectors/{kind}/index.tsx`` and
     ``nodes/{kind}/index.tsx`` are allowed because those files
     are the kind's *home*, not god dispatchers.)
  2. **loc-budget** — each canvas-internal file has a ceiling in
     ``viewer/tests/structural-guards.test.tsx``. The test enforces
     the ceiling; the table in ``mashbill/CLAUDE.md §Gate 2`` documents
     the current LOC + the ceiling side by side.
  3. **registry-completeness** — every kind in the 15-way union
     must have an ``inspectors/{kind}/index.tsx`` file, a
     ``nodes/{kind}/index.tsx`` file, and an entry in
     ``NODE_RENDERERS``. Adding a 16th kind requires updating the
     ``KIND_DIRS`` SSOT in both ``structural-guards.test.tsx`` and
     ``styles-cursor-baseline.test.tsx`` — intentional friction.

- **App.tsx refactor follow-up:** the original plan
  (``dazzling-greeting-diffie.md`` §"LOC budget guard") targets
  ``App.tsx ≤ 400``. Current 811 reflects URL sync (~75 LOC) +
  filter callbacks for the 4 wrappers (~50 LOC) + handler glue
  that has not been extracted into hooks. Phase 5.2's loc-budget
  guard therefore ships a **no-growth ceiling** (830) rather than
  the plan target. The split is filed for the v0.16 cycle; doing
  it inside this commit would have bundled three structural rules
  + a behavioural refactor, violating "small ships over big bangs"
  (``feedback_small_ships_over_big_bangs.md``).

- **Why three guards in one commit:** they share a single failure
  mode — *a future commit makes one of the 15 kinds invisible to a
  per-kind file*. Splitting into three commits would each be
  defensible in isolation, but the next session's Phase 5.3
  kill-switch (``reset_complete_check``) reads all three together
  to decide "is the reset complete?". Co-shipping keeps the
  contract surface coherent.

- **Alternatives considered:**
  - **Force the App.tsx split inside this commit** to land
    the plan-target ``≤ 400``: rejected. The split needs its own
    decision id, its own commit, and its own verification gate
    (Phase 3 verifier on every canvas tab after the refactor).
    Mixing it with structural guards would defeat "atomic commits"
    + the cross-cutting bundle check.
  - **Use AST parsing (ts-morph) instead of regex** for the
    god-dispatch scan: rejected as YAGNI. The regex
    ``switch\s*\(\s*[\w.]*\.?kind\s*\)`` catches the only god
    dispatch shape we care about (``switch (X.kind)``);
    per-kind narrowing guards (``if (node.kind !== "X")``) are
    structurally different and aren't matched.
  - **Snapshot every per-kind file's contents** as a registry SSOT:
    rejected as brittle — Tailwind class reshuffles would trigger
    false positives.

- **Approval:** Pending — same direction as D-2026-05-12-C/D/E.

- **Spec impact:** ``mashbill/CLAUDE.md §Gate 2`` LOC table replaced
  with the 8-row post-reset table (stale 1476/1422/791/523 entries
  removed; new ceilings + the deleted-file rows added).
  ``docs/SPEC.md`` unchanged.

- **Files in this commit:**
  - ``plot/viewer/tests/structural-guards.test.tsx`` — new, 44 tests
    (2 god-files-absent + 17 no-switch-dispatch + 8 LOC ceilings +
    2 per-kind LOC sweeps + 3 registry-completeness assertions +
    rest from it.each fanout).
  - ``mashbill/CLAUDE.md`` — Gate 2 LOC table updated.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.15.10 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.15.9 →
    0.15.10.

---

### D-2026-05-12-G — Structural reset complete: reset_complete_check kill-switch (v0.16.0 / Phase 5.3)

- **What:** Mark the v0.15 structural reset (D-2026-05-12-B)
  COMPLETE at v0.16.0. Ship a single-boolean kill-switch
  (``hooks/pre_commit_gate.py::reset_complete_check``) that fires
  on every commit touching viewer or server code and verifies the
  four structural invariants the reset was designed to enforce.
  Update ``docs/ARCHITECTURE.md`` to document the post-reset
  Domain layer + the runtime-enforced contracts. Move the
  ``검증`` queue item to Completed.

- **Why:** the reset deleted ``SketchInspector.tsx`` (Phase 2.10)
  and ``SketchNode.tsx`` (Phase 3.5), promoted Pydantic
  ``SketchNode`` to a 15-way discriminated union (Phase 1),
  stripped every ``canvas_kind`` switch from the sketch transforms
  (Phase 3.4), and shipped 5 acceptance gates (Phases 4-5). Each
  was a deliberate, hard-to-reverse move. The kill-switch makes
  the reset's done-state machine-checkable: any future commit that
  re-introduces a god dispatch trips the gate with a pointer to
  this decision.

- **The single boolean (AND of four):**

  1. ``mashbill/models.py`` exposes
     ``SketchNode = Annotated[Union[...], Field(discriminator="kind")]``
     (the 15-way discriminated union — both ``Union[...]`` and
     ``X | Y | ...`` syntaxes accepted; the gate matches either).
  2. ``viewer/src/canvases/SketchInspector.tsx`` absent from disk.
  3. ``viewer/src/canvases/SketchNode.tsx`` absent from disk.
  4. Zero ``canvas_kind`` branching (``===`` / ``!==`` / ``switch``
     / ``case``) in ``viewer/src/canvases/sketch/`` source files
     (comments-only references ignored).

  The fifth criterion in the plan (*"5 acceptance gates green"*)
  is enforced separately by the pre-commit gate's existing
  ``npx vitest run`` + ``uv run pytest`` invocations: any
  acceptance-gate failure already blocks the commit, so the
  kill-switch focuses on the structural invariants the test
  suite cannot detect (deleted file present, server union form).

- **Lifecycle:** the plan suggested the kill-switch be removed
  *after* v0.16.0. Kept in place as a permanent guard — the
  structural invariants are non-negotiable per the user's
  ``feedback_no_god_object.md`` memory ("kind 별 클래스 + Pydantic /
  TS discriminated union 비협상"). Removing the gate after one
  green commit would be premature; the test costs ~10 ms per
  viewer-touching commit and detects regressions the rest of
  the suite cannot.

- **Tests:** ``mashbill/tests/test_pre_commit_gate.py`` — 11 tests
  exercising the pass-case against the real repo, the docs-only
  skip-case, each of the four invariants' failure modes in a
  ``tmp_path`` scaffold, and the comment-stripping behaviour for
  ``canvas_kind`` mentions that live inside comments.

- **Docs:**
  - ``docs/ARCHITECTURE.md`` — new "Post-v0.15 shape" section at the
    top documenting the actual Domain → UI dependency direction,
    a contracts table linking each invariant to its test +
    decision id, and a "how to add a 16th kind" recipe. The legacy
    pre-reset section is preserved below with a "historical only"
    banner.
  - ``docs/NEXT_SESSION.md`` — ``검증`` queue item moved to
    Completed with a per-commit summary (v0.15.7 → v0.16.0).

- **Alternatives considered:**
  - **Skip ARCHITECTURE.md update; the test suite IS the docs:**
    rejected. Tests describe what cannot happen; they don't
    describe what the code IS. New contributors need a 5-paragraph
    layer overview to read the test file as a contract, not a
    riddle.
  - **Remove the kill-switch after v0.16.0** (per the original plan
    text): rejected — see Lifecycle above.
  - **Bundle the App.tsx split into v0.16.0**: rejected. Phase
    5.2's no-growth ceiling (830) protects against further bloat;
    the split is a separate decision with its own verification
    surface.

- **Approval:** Pending — same direction as D-2026-05-12-C/D/E/F.

- **Spec impact:** none — the reset is internal structure. SPEC.md
  unchanged (per Gate 0: behaviour is the SPEC's domain, structure
  is ARCHITECTURE's).

- **Files in this commit:**
  - ``mashbill/hooks/pre_commit_gate.py`` — new
    ``reset_complete_check`` function wired into ``main()``.
  - ``mashbill/tests/test_pre_commit_gate.py`` — new (11 tests).
  - ``mashbill/docs/ARCHITECTURE.md`` — new "Post-v0.15 shape" section.
  - ``mashbill/docs/NEXT_SESSION.md`` — ``검증`` moved to Completed.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.0 section.
  - ``mashbill/.claude-plugin/plugin.json`` — **minor** bump 0.15.10 →
    0.16.0 (structural reset complete; the only minor bump in the
    entire reset sequence).

---

### D-2026-05-12-H — App.tsx split (5-commit refactor → reach plan target ≤ 400 LOC)

- **What:** Reduce ``viewer/src/App.tsx`` from 811 LOC to ≤ 400 LOC
  (the plan target from D-2026-05-12-F, deferred from Phase 5.2)
  by extracting:

  | Target file | Source LOC | Sliced commit |
  |---|---:|---|
  | ``shell/Header.tsx`` (Header + SocketIndicator + truncateMiddle) | ~96 | v0.16.1 |
  | ``shell/CanvasTabs.tsx`` + ``shell/HelpCheatsheet.tsx`` + ``shell/states.tsx`` (Loading + ErrorPanel + EmptyState) | ~140 | v0.16.2 |
  | ``shell/ServiceDetailModal.tsx`` | ~67 | v0.16.3 |
  | ``hooks/useUrlSync.ts`` (syncUrl + activeTab / detailServiceId / selectedNodeId state + 6 navigation callbacks: selectTab / drillIntoService / backToOverview / jumpToActor / consumeSelection / focusCanvas) | ~80 | v0.16.4 |
  | ``hooks/useAvailableNodes.ts`` (4 filter memos) + ``hooks/useAppKeyboard.ts`` (undo/redo/help shortcuts) + ceiling 830 → 400 | ~58 | v0.16.5 |

- **Why now:** v0.16.0 left App.tsx as the lone oversize file in the
  post-reset tree. The structural-guards no-growth ceiling (830)
  prevents further bloat but doesn't redeem the gap. Each extraction
  is mechanically safe (props-in / props-out boundaries are clean,
  no shared closure state to thread) and is verifiable with the
  existing 361-test suite at every step.

- **Commit slicing rationale:** five extractions, one per commit.
  Each ships viewer green (tsc + vitest) and pushes LOC down
  monotonically. The final commit (v0.16.5) lowers the
  ``structural-guards.test.tsx`` ceiling from 830 to **400**,
  locking in the plan target — that lowering is the only change
  in the final commit that requires this decision id.

- **Alternatives considered:**
  - **Single big-bang commit:** rejected per "small ships over big
    bangs" (``feedback_small_ships_over_big_bangs.md``). 5 atomic
    commits give 5 verification points; a single 280-LOC delta has
    one.
  - **Extract logic before UI** (hooks first, components second):
    rejected. The hooks reference component-local state (activeTab /
    detailServiceId / selectedNodeId) that lives outside the
    extracted components; extracting components first leaves a
    smaller, cleaner App.tsx for the hook extraction to operate on.

- **Approval:** Pending — follow-up to D-2026-05-12-F where the gap
  was filed.

- **Spec impact:** none — internal refactor. No user-visible
  behaviour change.

- **Per-commit summary (v0.16.1 → v0.16.5):**
  - v0.16.1 — ``shell/Header.tsx`` (Header + SocketIndicator +
    truncateMiddle). App.tsx 811 → 715.
  - v0.16.2 — ``shell/CanvasTabs.tsx`` + ``shell/HelpCheatsheet.tsx`` +
    ``shell/states.tsx`` (Loading + ErrorPanel + EmptyState).
    ``CanvasTab`` type SSOT moved next to its visual consumer.
    App.tsx 715 → 564.
  - v0.16.3 — ``shell/ServiceDetailModal.tsx``. ``useTranslation``
    dropped from App.tsx (modal was the only consumer).
    App.tsx 564 → 496.
  - v0.16.4 — ``hooks/useUrlSync.ts`` (3 useState + 6 navigation
    callbacks + syncUrl). App.tsx 496 → 423.
  - v0.16.5 — ``hooks/useAvailableNodes.ts`` + ``hooks/useAppKeyboard.ts``.
    structural-guards ceiling 830 → 400. CLAUDE.md Gate 2 LOC table
    + ARCHITECTURE "What's still pending" updated. App.tsx 423 → 381.

- **Final state at v0.16.5:**
  - App.tsx LOC: 811 → 381 (-430).
  - LOC ceiling locked at 400 in ``structural-guards.test.tsx``.
  - 5 new shell files + 3 new hook files; each owns one slice of
    chrome / glue. No prop-drilling beyond the App composition root.
  - 361/361 viewer tests green at every commit boundary; tsc clean
    at every commit boundary.

- **Approval:** Accepted by structural verification — final ceiling
  assertion in ``structural-guards.test.tsx`` enforces the plan
  target on every future commit.

---

### D-2026-05-12-I — Schema parity test (Pydantic ↔ TS XxxJson, 15 kinds)

- **What:** Add ``mashbill/tests/test_schema_parity.py`` — 18 tests that
  assert, for every kind in the 15-way discriminated union, the
  Pydantic class's ``model_fields.keys()`` is identical to the
  TypeScript ``XxxJson`` interface's field set in
  ``viewer/src/domain/{Kind}.ts``. Closes the schema round-trip
  loop end-to-end.

- **Why:** the v0.15 reset gave server and viewer a parallel 15-way
  union; both sides currently agree, but nothing *enforces* that
  agreement. The next time someone adds a field to ``ServiceNode``
  on the server but forgets the TS side (or vice versa), the
  drift would only surface as a runtime parse failure on an actual
  user document. This test catches the drift at CI time with the
  offending field set in the failure message.

- **Test composition (18 tests):**
  - 1 anchor: ``BaseNodeFields.model_fields`` matches the canonical
    13-field set (id / label / x / y / width / height / color /
    shape / icon / parent_id / collapsed / is_root / details_path).
  - 1 anchor: ``BaseFieldsJson`` interface (TS) matches the same
    canonical set.
  - 15 parametrised per-kind asserts: Pydantic field set ==
    (TS XxxJson kind-specific fields) ∪ (BaseFieldsJson 13 fields).
  - 1 sanity: ``_ALL_KIND_CLASSES`` has exactly 15 entries.

- **Implementation choice — regex over TS-compiler parsing:** TS
  source is parsed with a regex (matching ``export interface XxxJson
  extends BaseFieldsJson { ... }`` and pulling field names off
  ``\w+\s*:``). Adding a TS compiler dependency (ts-morph or
  typescript via tsc API in a Python harness) would be heavier than
  the test's payoff. The interface idiom is stable post-reset (every
  per-kind file follows the same template), and if a future commit
  changes the idiom, the regex fails loudly — that failure is
  the signal to update the parser, not to silence the test.

- **Alternatives considered:**
  - **Have the build emit a JSON manifest of TS field names**: more
    robust, but introduces a build step that runs before the test
    and requires Node.js in the pytest harness. YAGNI.
  - **Run the parity assertion on the viewer side via
    ``schema_export.py`` JSON Schema files**: server already exports
    these; the viewer could load them and cross-check. Rejected
    because the JSON Schema files exclude the typed-text fields for
    Foundation kinds (they live in MD templates) — so the parity
    test would need a different shape per kind, defeating the
    structural argument. Server-side regex is simpler and uniform.

- **Approval:** Accepted by structural verification — all 18 tests
  green against the current tree confirms parity holds today; any
  future drift fails the test with the offending kind named.

- **Spec impact:** none — internal verification scaffolding.

- **Files in this commit:**
  - ``mashbill/tests/test_schema_parity.py`` — new, 18 tests.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.6 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.5 → 0.16.6.

---

### D-2026-05-12-J — mashbill-code-red-team skill (adversarial code review)

- **What:** Add ``mashbill/skills/mashbill-code-red-team/SKILL.md`` — a
  procedure skill that runs 9 adversarial attacks against a Novel
  branch / commit set / PR. Triggers on Korean (리뷰 / 코드리뷰 /
  공격적으로 / 비판적으로) and English (review / red-team / check
  this) review-request phrases. Output is a structured report:
  evidence (file:line) → rule violated (CLAUDE.md / DECISIONS /
  SPEC citation) → severity (Critical / Major / Minor) →
  suggested fix → verdict (✅ MERGE OK / 🟡 MERGE WITH FIXES /
  🔴 DO NOT MERGE).

- **Why:** the user's 2026-05-12 direction (memory:
  ``project_red_team_review_skill.md``):
  *"코드 리뷰나 설계 리뷰를 하는 스킬도 필요할 것 같구요. 이건
  레드팀 처럼 비판적 시각으로 바라 볼 수 있게 작성이 되어야해요."*
  Novel has lived 1491-LOC god components for 8 months, six cursor
  rounds in three sessions, an anchor decoration painting outside
  the click target for two weeks. Each was reviewed in isolation
  and passed. The fix is not "review harder" — the fix is
  "review *adversarially*."

- **The 9 attacks:**
  1. **Diff-vs-claim** — scope creep, behaviour-change-disguised-as-refactor,
     cross-cutting bundle.
  2. **Bad-faith input** — null / wrong-type / path-traversal /
     PII-leak failure modes.
  3. **Code-as-spec violations** — un-specced behaviour, comment-as-spec
     (D-2026-05-04-B), broken decision trail.
  4. **Hidden coupling** — closure-shared state, prop-semantic
     drift, architecture-direction violation.
  5. **God dispatch** — micro-god in per-kind files,
     ``switch (node.kind)`` regression in non-allowlisted files.
  6. **Cross-cutting visual bundle** — cognitive scapegoat
     (D-2026-05-11-C rationale).
  7. **LOC budget creep** — file growing without absorbing a
     legit responsibility (god-object precursor signal).
  8. **Rotted comments** — TODO/FIXME/XXX/HACK additions, stale
     references to deleted modules, what-not-why comments.
  9. **Test coverage** — regression-bait (TDD violation), brittle
     tests asserting implementation details, fixtures bypassing
     ``createBlankNode``.

- **Approval:** Pending — first iteration. Per the user's direction
  (*"이런 것들이 만들어지면 차차 정형화된 워크플로우로
  진화되어야합니다"*), the skill calibrates from real use; if five
  consecutive reviews produce zero findings, the codebase has
  internalised the rules and the skill is doing its job by being
  obsolete. Sister skill ``mashbill-design-red-team`` lands in v0.16.8
  for pre-implementation reviews.

- **Alternatives considered:**
  - **One unified ``plot-red-team`` skill** that branches code-vs-design
    by trigger: rejected. The two procedures share intent but
    diverge sharply on what to attack (code = bad-faith input,
    coupling, dispatch; design = unstated invariants, reversibility,
    user-essence match). Splitting keeps each procedure tight.
  - **Auto-run as a hook on every commit**: rejected per the user's
    *"차차 정형화된 워크플로우로 진화"* direction. Don't pre-build
    the workflow layer; let it crystallize from the first few real
    uses.

- **Files in this commit:**
  - ``mashbill/skills/mashbill-code-red-team/SKILL.md`` — new, ~200 LOC.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.7 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.6 → 0.16.7.

---

### D-2026-05-12-K — mashbill-design-red-team skill (adversarial design review)

- **What:** Add ``mashbill/skills/mashbill-design-red-team/SKILL.md`` — the
  pre-implementation companion to ``mashbill-code-red-team`` (D-2026-05-12-J).
  Reads a SPEC change draft, a DECISIONS entry draft, a plan file
  (e.g. ``~/.claude/plans/*.md``), or a verbal proposal and runs 8
  adversarial attacks on the *idea*, not the code.

- **Why:** code reviews catch bad code; they don't catch bad
  ideas. Novel's v0.13.2 auto-edges were good code that the user
  rolled back same-day — the idea was wrong. D-2026-05-10-E
  auto-layout shipped twice and was rejected twice. Catching
  these at the proposal stage is cheaper than catching them at
  the diff.

- **The 8 attacks:**
  1. **VISION re-anchor** — off-essence / phase-leakage findings.
  2. **Unstated invariants** — assumptions about service / actor /
     anchor / edge that the existing DECISIONS pin down.
  3. **Failure modes** — worst-case input / timing / browser.
  4. **Reversibility** — one-way write / user-state contamination /
     migration-trap.
  5. **VISION / PRODUCT_SPEC alignment** — product-framing
     conflicts (canvas inventory, kind out-of-scope, global service).
  6. **Over-fit / under-fit** (YAGNI vs AHA) — bespoke
     ``if (kind === "X")`` smell vs premature abstraction.
  7. **Hidden tradeoffs** — every benefit must name what it makes
     harder; if no tradeoff can be named, the benefit is suspect.
  8. **Scope drift** — implicit additions ("and also…") that
     weren't in the one-line proposal.

  Output verdict: ✅ READY TO IMPLEMENT / 🟡 REVISE FIRST /
  🔴 REDESIGN.

- **Evolution path documented in the skill:**
  1. Phase 1 (now): manual invocation via trigger phrases.
  2. Phase 2 (after several uses): hook on PR creation that nudges
     "should this have run on the underlying decision?"
  3. Phase 3 (mature): composed slash command
     ``/plot-propose <text>`` running design red-team →
     appending DECISIONS entry → gating implementation.
  Phases 2-3 are explicitly *not* pre-built per the user's
  *"차차 정형화된 워크플로우로 진화"* direction; let usage
  shape them.

- **Approval:** Pending — first iteration. Sister skill
  ``mashbill-code-red-team`` shipped at v0.16.7 (D-2026-05-12-J).
  Together the two skills close the review loop end-to-end
  (proposal → code).

- **Alternatives considered:**
  - **Single ``plot-red-team`` skill that auto-detects whether the
    target is code or design**: rejected — the failure modes
    attacked at design time (unstated invariants, reversibility)
    are categorically different from code time (god dispatch, LOC
    creep). Separate skills keep each procedure tight.
  - **Make the design review mandatory on every new SPEC line**:
    rejected as YAGNI workflow-layer. The user explicitly said
    *"차차 정형화"* — wait until usage justifies the gate.

- **Files in this commit:**
  - ``mashbill/skills/mashbill-design-red-team/SKILL.md`` — new, ~240 LOC.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.8 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.7 → 0.16.8.

---

### D-2026-05-12-L — mashbill-i18n-audit skill (revised after dogfooded design red-team)

- **What:** Add ``mashbill/skills/mashbill-i18n-audit/SKILL.md`` — a
  procedure skill that runs 4 static audits on the viewer
  codebase for i18n compliance per
  ``feedback_plot_global_service.md`` (Novel is a global service)
  + D-2026-05-11-D (English primary / Korean locale, parity
  guard already in place).

- **Why:** the existing ``i18n-keys-parity.test.ts`` enforces
  *parity* (en ↔ ko key sets), but cannot see:
  1. **Hardcoded** user-facing strings the bundle never receives.
  2. **Undefined** ``t("foo.bar")`` calls whose key is missing
     from en.json.
  3. **Stale** keys in en.json that no source file references.
  4. **Untranslated** values where ``ko[k] === en[k]`` for
     non-trivial text.

  This skill closes those four gaps without TS-compiler infra.

- **Design-red-team verdict (dogfooded ``mashbill-design-red-team``
  v0.16.8 on the v1 proposal):** 🟡 REVISE FIRST. Three Major
  + three Minor findings led to these revisions before ship:

  | Finding | Severity | Revision applied |
  |---|---|---|
  | A2.1 — "user-facing string" too fuzzy | Major | Explicit definition: JSX text + named attribute allowlist (aria-* / title / alt / placeholder / label) + exemption rules (length ≤ 3 / NodeKind literal / brand regex / adjacent ``// i18n-skip``) |
  | A2.2 — dynamic ``t(\`prefix.${var}\`)`` un-handled | Major | Audit 2 + Audit 3 explicitly extract template-literal prefix; mark ``prefix.*`` entirely referenced |
  | A3.1 — dynamic composition false-positives | Major | Same as A2.2 |
  | A6.1 — untranslated check over-fits | Minor | Equal-string check gated by length > 3 AND value ≠ key tail |
  | A7.1 — WIP / dev-only handling absent | Minor | ``// i18n-skip`` comment marker (no permanent variant — forces eventual i18n) |
  | A8.1 — audit scope undefined | Minor | Explicit "scan ``viewer/src/**/*.{ts,tsx}``, exclude i18n / tests / main.tsx" |

  After revisions: 🟢 READY TO IMPLEMENT (per skill's verdict
  scale). The dogfood loop was the value-add of v0.16.7 + v0.16.8
  red-team skills — caught real proposal weaknesses before code.

- **Output verdict scale (skill itself):**
  - ✅ CLEAN — zero findings.
  - 🟡 FIX — ≥ 1 hardcoded / undefined-key finding (user-visible
    bug in the running viewer).
  - 🔴 BLOCK — ≥ 3 hardcoded / undefined-key findings (systematic
    i18n bypass).
  - Stale (Audit 3) + untranslated (Audit 4) are Minor — they
    appear in the report but never escalate verdict on their own.

- **Phase 1 / 2 / 3 evolution (documented inside the skill):**
  - Phase 1 (now): manual invocation, manual scan, manual report.
  - Phase 2: wire Audit 1 + 2 into a vitest static guard
    (``i18n-static-audit.test.tsx``) so missing keys / hardcoded
    strings fail the build. Audits 3 + 4 stay manual.
  - Phase 3: PreCommit hook gating FIX / BLOCK verdicts.
  - Per ``project_red_team_review_skill.md`` evolution philosophy:
    don't pre-build Phase 2-3; let usage shape them.

- **Approval:** Pending — first iteration. Calibrates from real
  use; if five consecutive runs convert no findings to changes,
  move to Phase 2 and retire manual invocation.

- **Alternatives considered:**
  - **Auto-fix:** rejected. Auto-translation guesses, auto-key-naming
    guesses, auto-exemption guesses each multiply risk. Read-only
    by design.
  - **TS compiler (ts-morph) parsing:** rejected. Same rationale
    as D-2026-05-12-I (schema parity): regex is brittle but the
    failure mode is loud and fixable; compiler dependency is
    heavier than the skill's payoff.
  - **Merge with ``i18n-keys-parity.test.ts``:** rejected. Parity
    is a single binary contract enforced at vitest time; the audit
    is a 4-category report enforced at human-review time. Mixing
    them buries the report inside test failures and loses the
    structured output.

- **Files in this commit:**
  - ``mashbill/skills/mashbill-i18n-audit/SKILL.md`` — new, ~220 LOC.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.9 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.8 →
    0.16.9.

---

### D-2026-05-12-M — Self-loops render as curved arcs (SelfLoopEdge)

- **What:** Custom React Flow edge type ``SelfLoopEdge`` renders a
  cubic-Bezier arc for any edge with ``source === target`` whose
  endpoints don't collapse to a different ancestor. The
  ``edgeTransform`` filter at line 40 is now precise: it drops
  collapsed-ancestor pseudo-self-loops (cross-subtree edges that
  fold into the same parent) but lets user-drawn self-loops through.

- **Why:** the canonical Novel spec re-delivered by the user
  (2026-05-12, recorded in plan
  ``~/.claude/plans/dazzling-inventing-boole.md``) explicitly
  permits feedback loops:
  > "셀프 피드백 루프 표현 가능 (서비스 A → 서비스 A)."

  The previous unconditional ``if (src === tgt) continue;`` filter
  in ``edgeTransform.ts:40`` silently dropped every self-loop —
  including user-drawn ones — leaving a spec-violating gap: the
  data model allowed self-loops, the renderer didn't show them.

- **What the arc looks like:** cubic Bezier from source to target
  with two control points bulged 100 px above the source/target
  line. For a same-handle self-loop (``sourceX === targetX``,
  ``sourceY === targetY``) the curve becomes a vertical teardrop;
  for opposite-handle (R→L) self-loops it's a wide arc over the
  node. Always non-degenerate (visibly clickable / selectable /
  deletable).

- **Real vs pseudo self-loop classification:**
  - **Real** = ``edge.source === edge.target`` in the doc
    (user-drawn). Renders as ``type: "selfLoop"``.
  - **Pseudo** = ``edge.source !== edge.target`` but at least one
    side collapses to match the other. Filtered (preserves the
    pre-v0.16.10 behaviour for collapsed subtrees).
  Both sides covered by ``self-loop-render.test.tsx``.

- **Alternatives considered:**
  - **No filter change — accept React Flow default rendering**:
    rejected. RF's default draws a zero-length line on same-handle
    self-loops; on opposite-handle the line goes through the node
    body (chord). Neither is readable.
  - **Force handles to differ before allowing connect** (i.e. block
    same-handle self-loops at draw time): rejected as YAGNI. The
    arc renderer handles same-handle gracefully; constraint at
    draw time is more code for no benefit.
  - **External library (e.g. d3 self-loop helpers)**: rejected.
    The math fits in ~30 LOC; an extra dep would dwarf it.

- **Approval:** Accepted by spec mandate. The canonical Novel spec
  required this; the previous filter was a violation.

- **Spec impact:** ``docs/SPEC.md §Edges`` gains a "Self-loops
  (source === target)" subsection citing this decision.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/edges/SelfLoopEdge.tsx`` — new (~80
    LOC); custom edge component + ``selfLoopPath`` pure helper
    (exported for tests).
  - ``plot/viewer/src/canvases/edges/registry.ts`` — new (~10
    LOC); ``EDGE_TYPES`` SSOT.
  - ``plot/viewer/src/canvases/SketchCanvas.tsx`` — wire
    ``edgeTypes={EDGE_TYPES}`` on ReactFlow + import.
  - ``plot/viewer/src/canvases/sketch/edgeTransform.ts`` — split
    real vs pseudo self-loop at the filter; add ``type: "selfLoop"``
    on real self-loop output.
  - ``plot/viewer/tests/self-loop-render.test.tsx`` — new (7 tests).
  - ``mashbill/docs/SPEC.md`` — new "Self-loops" subsection under §Edges.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.10 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.9 → 0.16.10.

---

### D-2026-05-12-N — Foundation anchor-radial initial placement

- **What:** When a user creates a Mission / CoreValue / Identity
  node on the Foundation canvas, the new node's initial position
  snaps to a slot on a circle of radius 320 px around the anchor
  centre (canvas ``(0, 0)``). Slots are 120° apart — Mission at
  9 o'clock, CoreValue at 1 o'clock, Identity at 5 o'clock.
  Subsequent same-kind nodes offset +30°. The slot is a
  *positional hint, not a constraint* — user can drag the node
  anywhere after creation.

- **Why:** the canonical Novel spec re-delivered by the user
  (plan ``~/.claude/plans/dazzling-inventing-boole.md``) says:
  > "프로젝트 노드 놓고(앵커) 그 주변에 미션, 코어밸류, 아이덴티티
  > 붙이면 되요. 뭐가 먼저고 말고는 없습니다."

  Previously the three nodes dropped wherever the cursor was —
  no visual signal that they belonged to the same project's
  essence. Anchor-radial placement makes the relationship
  spatially explicit on first sight.

- **Relationship to D-2026-05-04-A (no auto-edges):** preserved.
  This decision adds *auto-position*, not *auto-edges*. The
  canonical objection in D-2026-05-04-A was that auto-edges
  weren't editable / deletable. A position can be re-set by
  dragging the node — fully reversible, fully user-controllable.

- **Order is intentionally absent:** the user explicitly said
  *"뭐가 먼저고 말고는 없습니다"*. The 9 / 1 / 5 clock-face slots
  are chosen for *visual balance* (120° apart), not for any
  narrative reading order. Mission is not "first."

- **Alternatives considered:**
  - **Lane backgrounds with Why / Drives / Tone labels**:
    rejected — adds visual chrome and implies a sequence; user
    explicitly said no sequence.
  - **Suggested-edge buttons** (sidebar "Add Mission→CoreValue
    arrow"): rejected — re-introduces the auto-edge problem
    D-2026-05-04-A solved.
  - **Auto-edges from anchor** to each Foundation kind: rejected
    same reason.
  - **Only fire on empty canvas (don't offset for repeats)**:
    rejected — adding a 2nd Mission would stack on the 1st;
    +30° offset is the cheapest fix.

- **Approval:** Accepted by spec mandate; pure-helper coverage
  ensures the slot math doesn't drift.

- **Spec impact:** ``docs/SPEC.md §Foundation`` gains an
  "Anchor-radial initial placement" subsection at the top of
  the Foundation section, before the anchor table.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/sketch/anchorRadialLayout.ts`` —
    new (~95 LOC). Pure helper: ``anchorRadialSlot`` /
    ``anchorRadialPosition`` / ``countFoundationKinds`` /
    ``isFoundationRadialKind`` / ``FOUNDATION_RADIAL_KINDS`` SSOT.
  - ``plot/viewer/src/canvases/sketch/useNodeCreation.ts`` —
    ``addNodeAt`` overrides ``x``/``y`` when canvas is foundation
    and kind is one of the three radial kinds.
  - ``plot/viewer/tests/foundation-radial-layout.test.tsx`` —
    new (15 tests).
  - ``mashbill/docs/SPEC.md`` — new "Anchor-radial initial placement"
    subsection.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.11 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.10 → 0.16.11.

---

### D-2026-05-12-O — Anchor-radial via wrapper-supplied prop (kill-switch cleanup of v0.16.11)

- **What:** Replace the ``doc.canvas_kind === "foundation"`` check
  inside ``useNodeCreation.addNodeAt`` (shipped v0.16.11,
  D-2026-05-12-N) with a wrapper-supplied prop
  ``applyAnchorRadialLayout?: boolean``. FoundationCanvas passes
  ``true``; other wrappers default ``false``. Same observable
  behaviour, but the per-canvas decision now lives at the wrapper
  layer where D-2026-05-12-F structural-guards expect it.

- **Why:** v0.16.11 introduced a ``canvas_kind`` branching pattern
  inside ``viewer/src/canvases/sketch/useNodeCreation.ts``. The
  ``reset_complete_check`` kill-switch (D-2026-05-12-G) caught it
  on first run and refused the next commit — exactly the gate's
  intended behaviour. The gate's failure message:
  > "Per Phase 3.4 the sketch transforms never branch on canvas
  > kind; each wrapper supplies behaviour via 4 explicit props
  > (``hideRootServiceNode`` / ``shouldDrill`` / ``showFoldButton``
  > / ``injectAnchor``)."

  This decision adds the **5th** wrapper-supplied prop
  (``applyAnchorRadialLayout``) so anchor-radial joins the same
  pattern. No god-dispatch reintroduced.

- **Honest note:** v0.16.11 (D-2026-05-12-N) *should* have been
  authored with the wrapper-prop pattern from the start — the
  design red-team that ran on the v0.16.11 proposal missed the
  invariant pinned by D-2026-05-12-F. The fact that the
  kill-switch caught it on the next commit attempt is the value
  of the structural guard system; the cleanup is small (one
  prop, three lines) but the lesson goes into
  ``mashbill-design-red-team`` SKILL.md Attack 2 "Unstated
  invariants" as a calibration anchor: future Foundation /
  Service / Actor canvas-kind branching needs to pass through
  the wrapper-prop SSOT.

- **Alternatives considered:**
  - **Loosen the kill-switch** to allow ``canvas_kind`` reads in
    ``useNodeCreation.ts``: rejected. The structural guard's
    purpose is to keep the wrapper-prop pattern the SSOT for
    canvas-specific behaviour. Adding a per-file exemption
    would create an "is it on the list?" question every time
    something new touches the file.
  - **Move the check into the wrapper** (FoundationCanvas
    intercepts ``addNodeAt`` calls and overrides x/y): rejected.
    The wrapper would need access to the underlying state +
    layout helpers — more surface to maintain than a boolean
    flag.
  - **Re-introduce ``canvas_kind`` as a wrapper prop**: pointless
    — the existing 4 props (``hideRootServiceNode`` /
    ``shouldDrill`` / ``showFoldButton`` / ``injectAnchor``) and
    the new 5th do the same thing without giving the underlying
    sketch hook back a god discriminator.

- **Approval:** Accepted — kill-switch recovery; viewer 383/383
  + server 274/274 + pre_commit_gate 11/11 green.

- **Spec impact:** none — internal cleanup.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/sketch/useNodeCreation.ts`` —
    add ``applyAnchorRadialLayout?: boolean`` arg, replace
    ``current.canvas_kind === "foundation"`` with the flag.
  - ``plot/viewer/src/canvases/SketchCanvas.tsx`` — add
    ``applyAnchorRadialLayout?: boolean`` to ``SketchCanvasProps``,
    thread it into ``useNodeCreation``.
  - ``plot/viewer/src/canvases/FoundationCanvas.tsx`` — pass
    ``applyAnchorRadialLayout={true}``. Other wrappers unchanged
    (default false).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.12 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.11 → 0.16.12.

---

### D-2026-05-12-P — Add ``owner: str | None`` to BaseNodeFields (multi-user prep)

- **What:** Add an ``owner`` field to ``BaseNodeFields`` (Pydantic)
  and ``BaseFieldsJson`` / ``BaseFields`` (TS), plus the matching
  ``readonly owner!: string | null`` declaration + ``owner:
  this.owner`` toJson emission on each of the 15 entity classes.
  Type ``string | null``, default ``null``. Schema parity test
  ``_EXPECTED_BASE_FIELDS`` extended.

- **Why:** the canonical Novel spec re-delivered by the user
  (plan ``~/.claude/plans/dazzling-inventing-boole.md``) §"데이터
  구조 원칙":
  > "owner 필드 포함 (멀티유저 확장 대비)."

  Multi-user editing itself is out of scope for the current cycle
  (per spec §"추후 과제"); this commit lands the *data field* so
  the wire format is ready when multi-user does ship. Single-user
  sessions write ``null``; server fills from session context once
  multi-user lands.

- **Scope discipline (what this decision does NOT do):**
  - **No UI surface.** Inspector / node renderers / display
    unchanged. ``owner`` is invisible to today's user.
  - **No permission logic.** Read / write authorisation comes
    later with the rest of the multi-user track.
  - **No retroactive backfill.** Existing nodes load with
    ``owner=null`` via Pydantic + TS defaults; no migration.
  - **All 15 kinds inherit.** Refs (``mission_ref`` /
    ``value_ref`` / ``identity_ref`` / ``actor_ref``) and
    composition kinds (``rule`` / ``content`` / ``step`` /
    ``metric``) can each be owned independently if needed. The
    spec doesn't say "symbols only" — every node gets it.

- **Alternatives considered:**
  - **Structured owner** (``{ id: string; type: "user" | "team" |
    "org" }``): rejected per YAGNI. Multi-user data shape is not
    yet specced; ``string | null`` is the cheapest extensible
    placeholder.
  - **Owner only on symbol kinds** (Mission / CoreValue /
    Identity / Actor / Service): rejected. Future scope (e.g.
    a workspace where service rules carry team-specific
    permissions) would need it on rules. Default ``null`` on all
    is cost-free today and future-proof.
  - **Skip the field, add it when multi-user starts**: rejected.
    Wire-format migrations are expensive once user data is in
    the wild; adding the field now (with default ``null``) is
    backwards-compatible.

- **Approval:** Accepted by spec mandate. Schema parity test
  pins TS ↔ Pydantic agreement on the new field.

- **Spec impact:** none in ``docs/SPEC.md`` (no user-visible
  behaviour change). ``docs/PRODUCT_SPEC.md §5 데이터 구조 원칙``
  could later be reconciled with the canonical spec wording, but
  that is a separate doc-only commit.

- **Files in this commit:**
  - ``mashbill/mashbill/models.py`` — ``BaseNodeFields`` adds
    ``owner: str | None = None`` after ``details_path``.
  - ``plot/viewer/src/domain/BaseFields.ts`` —
    ``BaseFieldsJson`` + ``BaseFields`` interfaces add ``owner:
    string | null``; ``parseBaseFields`` reads it with null
    default.
  - ``plot/viewer/src/domain/{15 entity files}`` — each gets a
    ``readonly owner!: string | null`` field + ``owner:
    this.owner`` line in ``toJson``.
  - ``mashbill/tests/test_schema_parity.py`` — ``_EXPECTED_BASE_FIELDS``
    gains ``"owner"``.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.13 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.12 → 0.16.13.

---

### D-2026-05-12-Q — Anchor drag snap-back: optimistic local update

- **What:** ``App.tsx`` 's ``onAnchorChange`` handler now updates
  ``summaries`` state **optimistically** (via the new pure helper
  ``viewer/src/lib/anchorOptimistic.ts::applyOptimisticAnchorPatch``)
  *before* the ``patchProjectAnchor`` PATCH request fires. After the
  server response, the optimistic doc is replaced with the canonical
  server doc. On PATCH failure, the previous (pre-patch) doc is
  restored.

- **Why:** React Flow is a *controlled* component — its ``nodes``
  prop is the SSOT for node positions. The anchor drag flow was:
  ```
  user drag → onNodesChange → handleNodesChange → applyAnchorChange
  → onAnchorChange(patch) → patchProjectAnchor (async, 100-500ms)
  → replaceSummary
  ```
  Before this fix, ``summaries`` state only updated *after* the PATCH
  resolved, so during the round-trip the computed ``projectAnchor``
  prop carried the OLD position. React Flow, being controlled,
  rendered the anchor at the OLD position prop → user saw the anchor
  snap back to its pre-drag location.

  Same pattern as any optimistic-update UX: client commits the
  local view first, reconciles with server response after.

- **Why this wasn't caught earlier:** v0.13 Phase 0 introduced the
  anchor PATCH path but only tested it with localhost MCP server,
  where the PATCH round-trip is < 5ms — fast enough that the snap-back
  was sub-perceptible. Once the user's actual workflow involved any
  network latency (slow local CPU under HMR, real-world deploy
  latency, etc.), the gap became visible.

- **Architecture:**
  - New ``viewer/src/lib/anchorOptimistic.ts`` (~50 LOC):
    ``applyOptimisticAnchorPatch(current, tab, patch): ProjectDoc``
    + ``resolveAnchorPlacement(proj, tab): AnchorPlacement``. Pure,
    side-effect-free, testable in isolation.
  - ``App.tsx`` onAnchorChange shrinks from 7 lines to 17 lines
    (added optimistic update + error revert) but uses helper so
    the *new* logic stays in a 50-LOC pure module instead of
    bloating App.tsx (which has a 400-LOC structural ceiling).

- **Tests:** ``plot/viewer/tests/anchor-drag-snap-back.test.tsx``
  — 7 tests covering: x/y patch, missing-anchors-default, other-tab
  isolation, dimension-only patch, revert-via-previous, default
  fallback, stored-placement readback.

- **Alternatives considered:**
  - **Use ``useReactFlow().setNodes()`` to forcibly write the new
    anchor position into RF's store before the PATCH**: rejected —
    breaks the controlled-component contract (same anti-pattern as
    Cmd+A in D-2026-05-12-R, addressed separately at v0.16.17).
  - **Synchronous PATCH (await before returning)**: rejected — would
    block the drag handler on the server round-trip.
  - **Move ``summaries`` to a Context with optimistic+server
    reducer pattern**: over-engineering for one patch site. If a
    second optimistic site appears later, revisit.

- **Approval:** Accepted by spec mandate (RF controlled-component
  contract) + regression test pinning.

- **Spec impact:** ``docs/SPEC.md §Anchor`` already says
  "Mutation routing: anchor changes flow through ``onAnchorChange``
  (a separate prop), **never** through ``onDocChange``". This decision
  doesn't change that — only the *timing* of the state propagation
  back into ``summaries``.

- **Files in this commit:**
  - ``plot/viewer/src/lib/anchorOptimistic.ts`` — new (~55 LOC).
  - ``plot/viewer/src/App.tsx`` — onAnchorChange uses the helper +
    error revert. 381 → 393 LOC (within 400 ceiling).
  - ``plot/viewer/tests/anchor-drag-snap-back.test.tsx`` — new
    (7 tests).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.15 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.14 → 0.16.15.

- **Series context:** First of 5-commit React Flow regression-fix
  batch (v0.16.15-19) prompted by user hands-on review of v0.16.14.
  Companion fixes: refetch storm (v0.16.16), Cmd+A controlled
  contract (v0.16.17), fitView gating (v0.16.18), anchor
  data.onResize stability (v0.16.19).

---

### D-2026-05-12-R — Stable callback handlers (refetch storm fix)

- **What:** New ``viewer/src/hooks/useStableHandlers.ts`` returns
  ``useCallback``-wrapped post-project handlers (handleListStale /
  handleExternalCanvas / handleTagsRefresh / handleExternalChange).
  ``App.tsx`` additionally inlines ``handleError`` + ``handleActiveIdChange``
  pre-project as direct ``useCallback`` (they must be stable BEFORE
  ``useProject`` is invoked).

- **Why:** Playwright session recording showed **404 GETs to the same
  3 endpoints** in a single idle browser session — a refetch storm.
  Root cause: App.tsx passed inline arrow closures to ``useProject``,
  ``useCanvasPersist``, and ``useProjectSocket``. Those closures
  were recreated on every render. ``useProject``'s ``loadList`` had
  ``onError`` in its dependency array, so ``loadList`` was rebuilt
  every render too. Under certain WebSocket event timings the
  cascade could trigger a refetch chain: WS event → onListStale →
  loadList → setSummaries → App re-render → new closures → next
  WS event sees a different ``handlersRef.current`` snapshot → repeat.

- **Stability boundary:**
  - *Pre-project* handlers (``handleError``, ``handleActiveIdChange``)
    must be stable before ``useProject`` runs, so they live as
    direct ``useCallback`` in App.tsx (2 callbacks, 5 lines).
  - *Post-project* handlers (the 4 above) depend on ``useProject``'s
    output (``loadList``, ``setCanvasCache``, ``setTags``) and are
    bundled into ``useStableHandlers``.
  - This 2-stage shape keeps App.tsx under its 400-LOC ceiling
    (App.tsx 393 → 380 LOC after extraction).

- **Why the refetch storm appeared *now*:** the v0.16.0 App.tsx
  split (D-2026-05-12-H) extracted useUrlSync / useAvailableNodes /
  useAppKeyboard, leaving the *project / persist / socket* trio of
  hook wirings inline with their inline callbacks. None of the v0.15
  / v0.16 structural guards catch callback identity issues —
  structural-guards.test.tsx is *static* (file shape / LOC), not
  *runtime* (re-render behaviour). The storm only surfaced under
  hands-on use, exactly as the user predicted.

- **Tests:** ``plot/viewer/tests/stable-handlers.test.tsx`` —
  5 tests covering: identity stability across re-renders, identity
  change when ``loadList`` ref changes, ``handleExternalCanvas``
  produces the right Map-updater, ``handleExternalChange`` calls
  ``historyClear``, ``handleListStale`` invokes ``loadList``.

- **Alternatives considered:**
  - **Move all inline closures to refs in useProject / useCanvasPersist
    / useProjectSocket** (so caller stability doesn't matter):
    rejected. Already done in useCanvasPersist + useProjectSocket
    via ``handlersRef``. useProject doesn't follow the same pattern;
    converting it would change its public contract. Caller-side
    useCallback is the localised fix.
  - **Wrap each handler in a separate ``useCallback`` inline in App.tsx**:
    rejected — would push App.tsx past 400 LOC ceiling without a
    structural decision. The hook extraction is structurally cleaner.

- **Approval:** Accepted by regression test + LOC budget compliance.

- **Spec impact:** none — internal refactor.

- **Files in this commit:**
  - ``plot/viewer/src/hooks/useStableHandlers.ts`` — new (~60 LOC).
  - ``plot/viewer/src/App.tsx`` — pre-project handlers via
    ``useCallback``, post-project via ``useStableHandlers``. 393 →
    380 LOC.
  - ``plot/viewer/tests/stable-handlers.test.tsx`` — new (5 tests).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.16 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.15 → 0.16.16.

---

### D-2026-05-12-S — Cmd+A respects controlled-component contract

- **What:** ``useKeyboardShortcuts`` 's ``Cmd+A`` handler used to flip
  the RF store's ``selected`` flag via ``setNodes`` / ``setEdges``,
  but never synced ``selectedNodeIds.current`` (the SketchCanvas ref
  the clipboard reads). After Cmd+A, the user's next ``Cmd+C`` /
  ``Cmd+D`` copied the *previous* selection, not "all nodes". Fix:
  after the store mutation, write ``selectedNodeIds.current =
  inst.getNodes().map(n => n.id)`` so the ref tracks the RF store.

- **Why:** RF emits ``onSelectionChange`` only on *user-initiated*
  selection events (click / box-select / arrow keys). Programmatic
  ``setNodes(... selected: true)`` does NOT trigger it. The
  SketchCanvas wire-up assumed onSelectionChange was the single
  source of selection truth — Cmd+A broke that assumption.

- **Architecture honesty:** the deeper fix would be to *not* use
  ``setNodes`` for selection at all, but RF v11 doesn't expose a
  public "select all programmatically + fire onSelectionChange" API.
  Manual ref sync is the localised fix that preserves both sides
  of the contract.

- **Tests:** ``plot/viewer/tests/select-all-sync.test.tsx`` — 2 tests:
  Cmd+A populates ``selectedNodeIds.current`` with all rendered node
  ids + RF store ``selected`` flag flips for all nodes; then Cmd+C
  copies the full set (via clipboard mock).

- **Approval:** Accepted by regression test.

- **Spec impact:** ``docs/SPEC.md §Keyboard shortcuts`` already
  declares Cmd+A's user-visible behaviour ("Select all nodes and
  edges"); this fix makes the *internal contract* match.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/sketch/useKeyboardShortcuts.ts`` —
    Cmd+A branch now also syncs ``selectedNodeIds.current``.
  - ``plot/viewer/tests/select-all-sync.test.tsx`` — new (2 tests).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.17 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.16 → 0.16.17.

---

### D-2026-05-12-T — fitView gating: onInit only, not as ReactFlow prop

- **What:** Remove the ``fitView`` (+ ``fitViewOptions``) prop from
  the ``<ReactFlow>`` element in ``SketchCanvas``. Call
  ``inst.fitView({ padding: 0.2 })`` once inside the ``onInit``
  callback. Tab changes still re-fit because the wrapper has
  ``key={activeCanvasKey}`` (App.tsx) which forces remount → new
  ``onInit`` fires.

- **Why:** Novel's ``useNodesMemo`` returns a fresh ``nodes`` array
  on every render (synthetic anchor is re-injected from the prop).
  RF v11's ``fitView`` prop re-fits whenever the ``nodes`` reference
  changes, so the user's manual zoom / pan was reset mid-session
  by every unrelated state update (Inspector form input, history
  push, etc.). Visible bug: cannot zoom-into a region — the view
  springs back to "fit all" on next render.

- **Approval:** Accepted by static guard. The
  ``viewport-stability.test.tsx`` regex catches reintroduction of
  the ``fitView`` prop.

- **Tests:** ``plot/viewer/tests/viewport-stability.test.tsx``
  — 2 static-grep tests:
  - No top-level ``fitView`` prop on ``<ReactFlow ...>``.
  - ``onInit`` JSX form present and contains an ``inst.fitView(...)``
    call.

- **Alternatives considered:**
  - **Memoize ``nodes`` array reference** to make the prop stable
    across non-content-changing renders: would need deep equality
    on ``useNodesMemo`` output, which is non-trivial and bypasses
    React's normal reference-equality contract.
  - **Use ``useNodesInitialized`` + a once-only effect**: more
    code; the simpler ``onInit`` callback covers initial mount and
    tab-switch remount equally well.
  - **Set ``fitView={false}`` explicitly**: same effect as removing
    the prop (default is undefined-falsy), but slightly clearer
    intent. Either is fine; we go with removal.

- **Spec impact:** ``docs/SPEC.md §Viewport`` already says
  "Fit view fires once on mount + once per canvas switch." This
  fix makes the code match.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/SketchCanvas.tsx`` — remove
    ``fitView`` + ``fitViewOptions`` props from ``<ReactFlow>``;
    add ``inst.fitView({ padding: 0.2 })`` to ``onInit``.
  - ``plot/viewer/tests/viewport-stability.test.tsx`` — new
    (2 static-grep tests).
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.18 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.17 → 0.16.18.

---

### D-2026-05-12-U — Stable handleAnchorChange via useCallback (data.onResize ref stability)

- **What:** Extract App.tsx's inline ``onAnchorChange`` JSX arrow into
  a top-level ``useCallback``-wrapped ``handleAnchorChange`` declared
  alongside the other stable handlers. ``useNodesMemo`` 's synthetic
  anchor node carries an inline ``data.onResize: (w, h) => onAnchorChange?.(...)``;
  by stabilising ``onAnchorChange`` ref at the source, the memo's
  ``data`` object now only rebuilds when anchor-relevant state
  actually changes (projectPath / activeId / activeTab / summaries /
  project), not on every App render.

- **Why:** Closes the loop of the 5-commit React Flow regression
  batch (v0.16.15-19). Before this commit, even after v0.16.16's
  callback stabilisation, ``onAnchorChange`` was still inline JSX —
  recreated every App render. Each render triggered ``useNodesMemo``
  recomputation → fresh anchor node data → RF rerenders the anchor
  node. Visually subtle but contributes to anchor flicker / hover
  jitter under heavy use.

- **Approval:** Accepted by no-regression (399 / 399 tests still
  pass, no new failures) + LOC budget compliance (App.tsx 380 →
  385 LOC; well under 400 ceiling).

- **Tests:** No new dedicated test — the existing
  ``anchor-drag-snap-back.test.tsx`` (7 tests) covers
  ``handleAnchorChange`` 's behaviour (optimistic merge, revert);
  the existing ``stable-handlers.test.tsx`` (5 tests) covers the
  identity-stability pattern this commit applies to anchor too.

- **Spec impact:** none — internal stability optimization.

- **Files in this commit:**
  - ``plot/viewer/src/App.tsx`` — extract inline arrow JSX to
    ``handleAnchorChange = useCallback(...)``; replace prop usage
    with the stable reference.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.19 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.18 → 0.16.19.

- **Batch closure (v0.16.15-19):** This is the 5th and final commit
  of the React Flow regression-fix batch surfaced by user hands-on
  review of v0.16.14. All four major issues + this minor are now
  addressed with regression tests pinning each:

  | # | Issue | Decision | Test |
  |---|---|---|---|
  | 1 | Anchor drag snap-back | D-2026-05-12-Q | anchor-drag-snap-back.test.tsx (7 tests) |
  | 2 | Refetch storm | D-2026-05-12-R | stable-handlers.test.tsx (5 tests) |
  | 3 | Cmd+A controlled contract | D-2026-05-12-S | select-all-sync.test.tsx (2 tests) |
  | 4 | fitView mid-session reset | D-2026-05-12-T | viewport-stability.test.tsx (2 tests) |
  | 5 | Anchor data.onResize ref stability | D-2026-05-12-U | (covered by 1 + 2) |

  Total: 399 viewer tests (383 baseline + 16 new across the batch).

---

### D-2026-05-13-A — Restore anchor visual layer (v0.16.20-23 batch reverted)

- **What:** Revert all four commits of the v0.16.20-23 "RF 기본 동작
  rollback" batch as a single squashed git-revert:
  - ``ac35021`` v0.16.23 (batch closure docs / version bump)
  - ``32f3dc5`` v0.16.22 (synthetic anchor + PATCH path revert)
  - ``7edbbf8`` v0.16.21 (anchor-radial layout revert)
  - ``75ee0b0`` v0.16.20 (self-loop custom edge revert)

  Restores: synthetic project anchor on Foundation / Actors / Services
  canvases; anchor-radial initial placement for Foundation new nodes
  (120° auto-radial around anchor); ``SelfLoopEdge`` custom edge for
  ``source === target``; anchor PATCH path (``applyAnchorChange`` +
  ``anchorOptimistic`` + ``handleAnchorChange``).

  Keeps reverted: nothing — all four layers fully restored to their
  v0.16.19 state.

- **Why:** User direct correction — "다 복구 하라" — after the
  v0.16.20-23 batch was identified as over-reach. The original
  triggering message "그냥 RF 기본 동작으로 동작하게 해주세요"
  (v0.16.20 commit body) was interpreted as "remove the synthetic
  anchor and all its associated visual layers"; the user's actual
  intent was "keep the anchor + make *interaction* feel like stock
  React Flow". Removing the anchor itself violated the canonical
  Novel spec mandate ("프로젝트 노드가 가운데" — SPEC §Anchor) and
  contradicted the user's mental model. NEXT_SESSION.md:22-24 already
  recorded this as over-reach before this session.

- **Why not partial restore (anchor only, skip radial / self-loop):**
  User asked to restore *all*; partial restore would silently
  re-interpret the message a second time after the first
  mis-interpretation already cost a 4-commit batch.

- **Why not surgical revert of useNodesMemo block only:** The four
  layers were entangled at the commit level (anchor injection feeds
  PATCH path; PATCH path feeds optimistic update; radial layout
  reads anchor position; self-loop edge is independent but was
  bundled in the same batch). A single git-revert of the four
  commits is the audit-trail-preserving inverse — every restoration
  becomes a documented git event, not a hand-rewrite.

- **Real bug remains unresolved:** Interaction "엉망" — the user's
  *actual* complaint that triggered v0.16.15-19 *and* v0.16.20-23 —
  was never fixed by either batch. v0.16.19 (anchor present) and
  v0.16.23 (anchor absent) both exhibit the issue. This restoration
  is a precondition for diagnosis, not the diagnosis itself.
  Next-session work: ``RF 움직임`` trigger — reproducible step
  capture + layer kill-switch bisect (NEXT_SESSION.md).

- **Approval:** Accepted by user, 2026-05-13, via in-session
  ``AskUserQuestion`` answer: *"다 복구 하라고 그리고 문제의 원인을
  찾자고"*.

- **Spec impact:** [SPEC.md §Anchor](./SPEC.md#anchor-the-centre-node)
  / §Edges Self-loops / §Foundation Anchor-radial all restored to
  v0.16.19 text by the revert. No new spec lines.

- **Files in this commit:** all files in the
  ``ac35021..75ee0b0`` four-commit revert + ``plugin.json`` version
  ``0.16.19`` → ``0.16.24`` + ``CHANGELOG.md`` v0.16.24 section +
  this entry.

- **Reverted decisions (now back in force):**
  - D-2026-05-12-M (self-loop visual)
  - D-2026-05-12-N (anchor-radial layout)
  - D-2026-05-12-O / P / Q (anchor injection / PATCH / optimistic)
  - D-2026-05-04-B / C (anchor handles visible + visually distinct)

- **Rejected decisions (these are reverted away):**
  - D-2026-05-12-V (self-loop revert) — **Rejected**.
  - D-2026-05-12-W (anchor-radial revert) — **Rejected**.
  - D-2026-05-12-X (synthetic anchor + PATCH revert) — **Rejected**.
  - D-2026-05-12-Y (rollback batch closure) — **Rejected**.

  Note: revert removed these entries from the DECISIONS.md file
  itself (since the v0.16.22-23 commits added them). They are
  documented here so the next session sees both the proposal and
  its rejection.

- **Lesson:** When the user says "RF 기본 동작" mid-session, the
  scope is **interaction (cursor / drag / pan / zoom / select)**,
  not the synthetic node decoration. Spec mandates ("프로젝트 노드
  가운데", "셀프 피드백 루프", "주변에 붙임") override at-the-moment
  preference unless the user *explicitly* says "spec 도 폐기".

---

### D-2026-05-13-B — mashbill-entity-template skill (overdue from D-2026-05-12-B)

- **What:** Add ``mashbill/skills/mashbill-entity-template/SKILL.md`` — a
  procedure skill that walks adding a new ``kind`` end-to-end in 14
  steps (CONCEPTS / SPEC / domain class with ``fromJson`` / union
  extend / factory / Pydantic model / schema-parity / per-kind
  renderer / per-kind inspector / registry / i18n / round-trip test
  / structural-guards). Frontmatter triggers on "new kind",
  "엔티티 추가", "새 종류", "fromJson", "discriminated union" etc.

- **Why:** This is the first of five artefacts the user *allowed*
  building under D-2026-05-12-B's *"필요하다면 스킬이나 룰을
  만들구요"* permission. The v0.15 reset (Phase 1-5) shipped the
  15 entity classes + per-kind UI files; the procedure for *future*
  kind additions was the missing piece. User flagged on 2026-05-13
  that **none of the five candidates had been built** ("개발 스킬을
  좀 만들라고 했는데 하나도 안 만들었네"). This entry is the first
  ship of the five-phase catch-up batch (D-2026-05-13-B through F).

- **Why a procedure skill, not free-text in CLAUDE.md:** A 14-step
  walk that names ~14 files is too long for CLAUDE.md (which is the
  triggers + gates SSOT, not implementation walkthrough). A skill
  surfaces only when the trigger fires ("new kind" etc.), keeping
  Novel CLAUDE.md focused. Also matches the existing pattern —
  ``mashbill-feature-tdd`` / ``mashbill-frontend-bug-diagnosis`` /
  ``mashbill-i18n-audit`` are also procedure skills.

- **Approval:** Accepted by user, 2026-05-13 (in-session
  ``AskUserQuestion`` answer "5개 다").

- **Spec impact:** None — skill is procedure docs, not a behaviour
  change. Cross-references SPEC.md / CONCEPTS.md / DOMAIN.md as the
  truths each step writes into.

- **Files:**
  - ``mashbill/skills/mashbill-entity-template/SKILL.md`` — new, ~250 LOC.
  - ``mashbill/CHANGELOG.md`` — v0.16.25 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.24 → 0.16.25.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Companion artefacts (queued):**
  - D-2026-05-13-C → ``mashbill-domain-design`` skill.
  - D-2026-05-13-D → ``no-god-import`` pre-commit hook.
  - D-2026-05-13-E → ``entity-roundtrip`` vitest test.
  - D-2026-05-13-F → ``mashbill/CLAUDE.md`` anti-pattern row.

  All five close the D-2026-05-12-B "Skills / rules to consider"
  candidate list.

---

### D-2026-05-13-C — mashbill-domain-design skill (overdue from D-2026-05-12-B)

- **What:** Add ``mashbill/skills/mashbill-domain-design/SKILL.md`` — a
  procedure skill that runs **before** entity-template / feature-tdd
  when a new concept doesn't yet have a clear home. 5-decision walk:
  1. Thing vs Rule
  2. Entity vs Value-object
  3. Does an existing kind already cover it? (MECE check against
     CONCEPTS.md 15 rows)
  4. Which bounded context owns it? (against DOMAIN.md 5 contexts)
  5. SSOT location

  Output: a Decision summary the user approves *before* implementation
  begins.

- **Why:** The v0.13.3 → v0.13.10 cursor saga (six rounds, see
  D-2026-05-10-C / D-2026-05-10-F) was caused by no domain-placement
  framework — every fix picked "where does this rule live?"
  ad-hoc, and the next bug surfaced in a different ad-hoc location.
  DOMAIN.md (2026-05-12) ended that by giving every concern a
  bounded-context home; this skill is the **gate** that forces the
  placement decision early in the workflow, before code lands.

- **Why a separate skill, not part of mashbill-feature-tdd:** The
  placement decision is heavy enough (5 distinct decisions, often
  involving DOMAIN.md / CONCEPTS.md / DECISIONS.md cross-references)
  to warrant its own trigger surface. mashbill-feature-tdd already
  references "Step 3 — Identify bounded context"; this skill is the
  detailed unpack of that step for *new* concepts.

- **Approval:** Accepted by user, 2026-05-13 (the "5개 다" answer of
  the same session that opened D-2026-05-13-B).

- **Spec impact:** None — procedure docs. Cross-references
  DOMAIN.md / CONCEPTS.md / SPEC.md / VISION.md.

- **Files:**
  - ``mashbill/skills/mashbill-domain-design/SKILL.md`` — new, ~230 LOC.
  - ``mashbill/CHANGELOG.md`` — v0.16.26 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.25 → 0.16.26.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Position in the 5-batch:** 2 of 5. Remaining queued:
  D-2026-05-13-D (no-god-import hook), D-2026-05-13-E (entity-roundtrip
  test), D-2026-05-13-F (CLAUDE.md anti-pattern row).

---

### D-2026-05-13-D — no-god-import static guard (overdue from D-2026-05-12-B)

- **What:** Add ``viewer/tests/no-god-import.test.tsx`` — vitest
  static guard with four invariants:
  1. ``viewer/src/types.ts`` does **not** declare a god ``SketchNode``
     interface (must be a re-export from ``domain/SketchNode.ts``).
  2. Every ``NodeKind`` discriminator value has a corresponding
     ``domain/{Kind}.ts`` entity class file.
  3. Every domain class exports its JSON wire interface
     ``{Kind}Json``.
  4. Every domain class registers its parser via
     ``registerKindParser("{kind}", {Kind}.fromJson)``.

  Hook semantics: ``pre_commit_gate.py`` already runs vitest on every
  viewer commit (per D-2026-05-11-C). A failure here blocks ``git
  commit``. No new hook code needed — the guard inherits the existing
  enforcement layer.

- **Why:** D-2026-05-12-B requested a "pre-commit hook ``no-god-import``
  (block god ``SketchNode`` import in new viewer files post-Phase-A)".
  v0.15 Phase 2.10 retired the god interface; this guard prevents
  drift back. Without it, a future session could quietly re-add
  ``export interface SketchNode { ... }`` to types.ts and the
  discriminated-union pattern would silently rot.

- **Why a vitest test, not a separate Python hook:** Two reasons.
  (1) ``pre_commit_gate.py`` already runs vitest for viewer changes;
  a static guard *is* a pre-commit check via that path, with no new
  code surface. (2) A Python hook would have to re-implement TS
  parsing for ``types.ts`` and the domain files; vitest gets file
  globbing + regex assertion + actionable failure messages for free.

- **Why test.each over a single multi-assertion test:** Per-kind
  failure messages are essential — when a developer forgets ``Foo.ts``
  for a new ``foo`` kind, the failure should say "domain/Foo.ts is
  missing for NodeKind 'foo'", not "some kind file is missing". 46
  individual sub-tests cost ~6 ms and give pinpoint diagnostics.

- **Approval:** Accepted by user, 2026-05-13 (the "5개 다" answer of
  the same session that opened D-2026-05-13-B).

- **Spec impact:** None — internal guard. Cross-references
  CONCEPTS.md (NodeKind), DOMAIN.md (discriminated-union mandate),
  mashbill-entity-template SKILL.md (the procedure this guard enforces).

- **Files:**
  - ``plot/viewer/tests/no-god-import.test.tsx`` — new, ~120 LOC,
    46 sub-tests.
  - ``mashbill/CHANGELOG.md`` — v0.16.27 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.26 → 0.16.27.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 399 viewer tests.
  - After: 445 viewer tests (+46 sub-tests).

- **Position in the 5-batch:** 3 of 5. Remaining queued:
  D-2026-05-13-E (entity-roundtrip test), D-2026-05-13-F (CLAUDE.md
  anti-pattern row).

---

### D-2026-05-13-E — entity-roundtrip vitest test (overdue from D-2026-05-12-B)

- **What:** Add ``viewer/tests/entity-roundtrip.test.tsx`` — vitest
  static guard verifying that for every NodeKind:

  ```ts
  parseEntity(createBlankNode(kind, base)).toJson() ===
    createBlankNode(kind, base)
  ```

  Two test groups:
  1. 15 per-kind cases (``test.each(NODE_KINDS)``) asserting the
     round-trip equality with actionable failure messages.
  2. 1 dispatch-coverage case asserting ``parseEntity`` accepts every
     NodeKind without throwing.

- **Why:** ``fromJson`` and ``toJson`` are inverse operations by
  contract. A common drift mode: a field gets added to fromJson
  (e.g., a new typed-text validator) but the developer forgets to
  emit it in toJson (or vice versa). The result is a field that's
  read on the wire, normalised on parse, and **dropped on the next
  serialisation** — a silent data-loss bug. This guard catches the
  drift at commit time, not at runtime when a user saves a project
  and loses fields. Closes the v0.13-v0.14 era's class of bugs
  where the absence of a fromJson boundary made this drift
  undetectable.

- **Why createBlankNode as the input fixture:** ``createBlankNode``
  is already the canonical "valid wire shape for kind K with default
  typed-text". It exercises the same fromJson + toJson pair as
  production code; if a kind's fromJson normalises a field that
  toJson omits, ``createBlankNode`` itself produces a non-idempotent
  result and the round-trip test catches it.

- **Why REF_OVERRIDES carve-out:** The four ref-family kinds
  (``actor_ref`` / ``mission_ref`` / ``value_ref`` / ``identity_ref``)
  require a non-null ``ref_{target}_id`` to land as valid. Other kinds
  accept default overrides. The overrides map keeps the test
  self-contained without leaking per-kind branching into the test
  body.

- **Approval:** Accepted by user, 2026-05-13 (the "5개 다" answer of
  the same session that opened D-2026-05-13-B).

- **Spec impact:** None — internal guard. Strengthens
  mashbill-entity-template SKILL.md Step 13 (round-trip test) from
  "should write one" to "the test exists and passes for every kind".

- **Files:**
  - ``plot/viewer/tests/entity-roundtrip.test.tsx`` — new, ~95 LOC,
    16 sub-tests.
  - ``mashbill/CHANGELOG.md`` — v0.16.28 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.27 → 0.16.28.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 445 viewer tests.
  - After: 461 viewer tests (+16 sub-tests).

- **Position in the 5-batch:** 4 of 5. Remaining queued:
  D-2026-05-13-F (CLAUDE.md anti-pattern row).

---

### D-2026-05-13-F — CLAUDE.md anti-pattern row "Treating raw JSON as domain entity" (overdue from D-2026-05-12-B)

- **What:** Add a row to ``mashbill/CLAUDE.md`` §Anti-patterns:
  *"Treating raw JSON as a domain entity (no fromJson boundary)"*.
  Cross-references the four upstream artefacts shipped in this
  catch-up batch:
  - ``mashbill-entity-template`` skill — Phase A.
  - ``no-god-import.test.tsx`` — Phase C.
  - ``entity-roundtrip.test.tsx`` — Phase D.
  - server-side ``test_schema_parity.py`` — pre-existing.

  Concrete example cited: pre-v0.15 god SketchNode interface where
  UI read ``.what_we_do`` directly off the wire shape with no class,
  no invariant check, no normalisation.

- **Why:** mashbill/CLAUDE.md's anti-pattern table is the **trigger
  surface** for the session-start sanity scan. Without a row naming
  the god-JSON anti-pattern explicitly, a future session could
  silently regress to it. The other four artefacts in this batch
  enforce the rule at code-gen time (skill), commit time (vitest
  guards), and CI time; this row enforces it at session-start
  *reading* time — the layer that's been the weak link historically
  (the v0.13-v0.14 god SketchNode lived for ~30 sessions before
  anyone called it out).

- **Why this is enough for closure of D-2026-05-12-B:** The original
  D-2026-05-12-B entry listed exactly five candidates under "Skills /
  rules to consider":
  1. ``mashbill/skills/mashbill-entity-template/`` — landed in D-2026-05-13-B.
  2. ``mashbill/skills/mashbill-domain-design/`` — landed in D-2026-05-13-C.
  3. Pre-commit hook ``no-god-import`` — landed in D-2026-05-13-D as
     vitest guard (functionally equivalent: pre_commit_gate.py runs
     vitest on every viewer commit).
  4. Vitest entity-shape round-trip test — landed in D-2026-05-13-E.
  5. ``mashbill/CLAUDE.md`` anti-pattern row "Treating raw JSON as
     domain entity" — landed in this entry.

  All five candidates now shipped; D-2026-05-12-B's deferred work is
  closed.

- **Approval:** Accepted by user, 2026-05-13 (the "5개 다" answer of
  the same session that opened D-2026-05-13-B).

- **Spec impact:** None — CLAUDE.md is operational guide, not spec.

- **Files:**
  - ``mashbill/CLAUDE.md`` — one new row in §Anti-patterns table.
  - ``mashbill/CHANGELOG.md`` — v0.16.29 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.28 → 0.16.29.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Position in the 5-batch:** 5 of 5 — **batch closed**.

---

### D-2026-05-13-G — Skill classification: dev-facing skills move to monorepo-level .claude/skills/

- **What:** Move 7 dev-facing skills from ``mashbill/skills/`` to
  ``noory-ai/.claude/skills/`` (monorepo-level Claude Code workspace
  skills directory):
  - ``mashbill-entity-template/`` (was v0.16.25 D-2026-05-13-B).
  - ``mashbill-domain-design/`` (was v0.16.26 D-2026-05-13-C).
  - ``mashbill-feature-tdd/``.
  - ``mashbill-frontend-bug-diagnosis/``.
  - ``mashbill-i18n-audit/`` (was v0.16.9 D-2026-05-12-L).
  - ``mashbill-code-red-team/`` (was v0.16.7 D-2026-05-12-J).
  - ``mashbill-design-red-team/`` (was v0.16.8 D-2026-05-12-K).

  Retained in ``mashbill/skills/`` (end-user-facing):
  - ``mashbill-help/``.
  - ``mashbill-new-sketch/``.
  - ``mashbill-read-sketch/``.

  All cross-references inside the 7 moved SKILL.md files updated
  via ``sed`` batch: ``(../../X)`` → ``(../../plot/X)``. The single
  cross-home filesystem link (``mashbill-entity-template`` ref to
  ``feedback_no_god_object`` auto-memory) converted to plain-text
  reference.

- **Why:** Novel's plugin-skill directory ``mashbill/skills/`` is meant
  for **end-user** skills — procedures that trigger in a *consumer's*
  project after they install the mashbill plugin (``mashbill-new-sketch``,
  ``mashbill-read-sketch``, ``mashbill-help`` make sense there). The other
  seven skills are **dev-facing**: they trigger during Novel's *own*
  development, reference Novel's internal source (``viewer/src/``,
  ``mashbill/``, ``docs/``), and would be useless noise in a
  consumer's project. User flagged 2026-05-13:
  *"플롯 안에 스킬이 클로드 동작을 시키는 스킬인가요? 저건 플러그인이
  가진 스킬이잖아요. .claude/ 에 들어가야하는거 아닌가?"*

- **Why monorepo-level (.claude/) over user-global (~/.claude/):**
  These skills reference Novel-specific files (``Mission.ts``,
  ``DOMAIN.md``, ``CONCEPTS.md``, ``CLAUDE.md`` Gate references).
  In another project they would mis-trigger or break links. Scoping
  them to the monorepo means they only activate when the developer
  is *in* this monorepo — exactly where they apply.

- **Why scope is 7, not all 10:** Three skills (``mashbill-help``,
  ``mashbill-new-sketch``, ``mashbill-read-sketch``) describe procedures
  a *consumer* runs on their own sketches. They reference plugin
  commands and consumer workflows, not Novel internals. They stay
  in ``mashbill/skills/`` where the plugin manifest exposes them.

- **Honest correction:** I added ``mashbill-entity-template`` and
  ``mashbill-domain-design`` to ``mashbill/skills/`` in v0.16.25 / v0.16.26
  without making this dev-vs-user-facing distinction. User caught
  it. The fix landed in the *same session* as the misclassification
  — D-2026-05-13-B/C are not rejected; the skills are correct
  artefacts, only their placement was wrong.

- **Lesson:** Before adding a procedure skill, classify:
  *"Does this trigger inside the plugin-consumer's project, or
  during the plugin's own development?"* If the latter, it goes in
  the monorepo's ``.claude/skills/``, never in ``plugin/skills/``.

- **Approval:** Accepted by user, 2026-05-13 (explicit ".claude/
  에 들어가야하는거 아닌가" + "네 맞아요 고고씽").

- **Spec impact:** None — internal organisation. Novel's plugin
  manifest still exposes ``mashbill/skills/`` but now only the 3
  end-user-facing skills.

- **Files in this commit:**
  - 7× ``git mv mashbill/skills/{name}/ → .claude/skills/{name}/``.
  - 7× SKILL.md path updates (sed: ``(../../X)`` → ``(../../plot/X)``).
  - ``mashbill-entity-template/SKILL.md`` feedback_no_god_object link
    converted to text reference.
  - ``mashbill/CHANGELOG.md`` — v0.16.31 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.30 → 0.16.31.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Re-classification of other plugins in this monorepo (deferred):**
  ``noory-ai/solera/skills/``, ``noory-ai/distill/skills/``,
  ``noory-ai/evonest/skills/``, ``noory-ai/flutter-cask/``,
  ``noory-ai/pencil_m3_flutter/`` may have the same misclassification.
  Audit deferred until those plugins' next session — not blocking
  Novel work.

---

### D-2026-05-13-H — v0.16.24 hands-on validation confirmed (Gate 0 pin)

- **What:** User confirmed via hands-on test in their real Chrome
  that v0.16.24 anchor visual restoration works as intended and
  the "RF 움직임 엉망" interaction complaint is no longer present.
  Verbatim user messages 2026-05-13:
  - *"근데 이제 된 거 같은데?"* (in response to a question about
    whether the 4 visible foundation edges were intended).
  - *"이제 잘 동작하는 거 같아요."* (in response to the
    diagnosis-plan offer).

- **Why:** Gate 0 trigger — confirmation pins the spec. Closing the
  "RF 움직임" NEXT_SESSION entry requires this pin or the next
  session would reopen the same diagnosis.

- **Spec impact:** None — confirms existing SPEC behaviour
  (anchor visible + RF stock interaction). No new SPEC line.

- **NEXT_SESSION impact:** ``RF 움직임`` active-queue entry
  archived to the Completed section.

- **Files in this commit:**
  - ``mashbill/docs/NEXT_SESSION.md`` — entry archive.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/CHANGELOG.md`` — v0.16.32 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.31 → 0.16.32.

- **Caveat:** Hands-on validation by spot-check; silent
  state issues found by automated page probe remain unresolved —
  see D-2026-05-13-I for the filing.

---

### D-2026-05-13-I — Silent state inconsistencies filed (lower-priority queue)

- **What:** Two data-integrity issues surfaced by automated page
  probe of ``http://localhost:5193/?project_path=.../plot-test-v010``
  on 2026-05-13, recorded so the next session can pick them up:

  1. **Console `422 Unprocessable Entity × 7`** with server
     validation error *"edges reference unknown nodes:
     ['e_mp2vvxg9_k9cq', 'e_mp2vw2a3_jwo8', 'e_mp2vw4a3_b8cd',
     'e_mp2vw78k_exi5']"*. The four ``e_``-prefixed ids are not
     present anywhere in raw storage (``grep`` 0 hits across
     ``.plot/``). Most likely cause: client → server PATCH payload
     is setting ``edge.source`` or ``edge.target`` to an edge id
     instead of a node id. Optimistic update covers the user
     experience; the user does not feel it.

  2. **``services/canvas.json`` orphan edge** ``e_mopntgek_4y74``
     with ``source_id: None, target_id: None``. Pydantic should
     reject on the next save attempt; user has not encountered it
     visibly.

- **Why low priority:** User-facing interaction confirmed working
  (D-2026-05-13-H). These do not surface in the user's session.

- **Why not zero priority:** The 422 storm is a real client-side
  bug that *would* surface if the user's session ever loses its
  optimistic state (hard reload mid-edit, browser restart, etc.).
  The None→None edge is a storage corruption that will block any
  future save touching ``services/canvas.json``.

- **Approval:** Pending — filed for next-session pickup. User
  asked to wrap session ("이제 잘 동작하는 거 같아요"); these
  issues recorded honestly without acting on them this session
  to avoid extending scope without user consent.

- **NEXT_SESSION trigger:** ``잔여 silent state`` / ``422`` /
  ``None edge`` / ``orphan edge`` / ``잔여 에러``.

- **Spec impact:** None.

- **Files in this commit:** same as D-2026-05-13-H plus the
  NEXT_SESSION entry pair.

---

### D-2026-05-13-J — JSON SSOT design vision (Phase 2 reopening — Pending detail)

- **What:** User pinned a 4-point design vision for Phase 2 of
  the deferred *"MD as derived export"* discussion
  (D-2026-05-12-A §15 #2, originally deferred 2026-05-12
  *"이 부분은 나중에 다시 다듬어 봅시다"*). User reopened the
  discussion on 2026-05-13 after Foundation hands-on testing,
  with the following verbatim statement:

  > *"json 이 원본이어야한다. 그래서 json 에 들어가는
  > 밸류값들은 md 포멧을 들어가야하고 그렇게 편집될 수 있어야한다.
  > 그리고 특정 버튼을 누르면 json 에서 md 로 추출할 수 있어야한다.
  > 근데 그걸 개별 노드로 하면 안되고 캔버스 마다 그렇게 해야한다."*

  4-point pin:

  1. **JSON = SSOT.** Current v0.13 co-equal storage model (MD
     also SoT) is abolished.
  2. **JSON value = MD-formatted string.** Typed-text fields
     (`mission.what_we_do` / `why` / `direction`, equivalents
     for `core_value` / `identity`) are stored as MD-formatted
     strings *inside* JSON. Viewer edits via an MD editor.
  3. **MD extraction = explicit button.** No automatic sync.
     User triggers JSON → MD conversion only when pressing an
     Export button.
  4. **Extraction unit = canvas.** Current v0.13 per-node MD
     files (`foundation/{kind}-{slug}.md`) are abolished. A
     single MD file per canvas (`foundation.md` or equivalent).

- **Current (v0.13 Phase 3+6) vs Vision (Phase 2) — factual diff:**

  | Aspect | Current (Phase 1) | Vision (Phase 2) |
  |---|---|---|
  | Storage | JSON + per-node MD co-equal | JSON SSOT |
  | Typed-text location | JSON (stripped on write) + MD (canonical) | Inside JSON as MD-formatted string |
  | Read merge | server-side `_merge_md_typed_text_into_nodes` | merge unnecessary (JSON read only) |
  | Write split | server-side `_split_foundation_typed_text_to_md` | MD not written (JSON written directly) |
  | MD file form | per-node (~N files per canvas) | per-canvas (1 file per canvas) |
  | MD update timing | every viewer save | user export-button press only |
  | MD purpose | co-source-of-truth | derived export (no read-back) |

- **Why now:** User hands-on testing of v0.16.32 Foundation
  canvas surfaced *"뭐지"* (=something is off) intuition.
  Investigating with the user revealed the root concern is the
  *JSON/MD relationship itself*, not any specific bug. The
  D-2026-05-12-A deferral is no longer the right state — user
  has a clear design vision and wants the discussion reopened.

- **Why pin now (today, docs-only) rather than wait for detail
  consensus:** Without a pin, the 4-point vision exists only in
  conversation history. The next session would re-elicit the
  same statement from the user. Pinning today preserves the
  user's exact words as the locked starting point; detail
  discussion next session works *from* this pin, not toward it.

- **Approval status:** **Pending — detail discussion deferred to
  next session per user direction 2026-05-13 *"이건 내일
  논의해봅시다"*.** The 4-point vision itself is locked (user
  explicit statement). Approval transitions to Accepted once
  detail open-questions (editor UX, line-break handling,
  per-canvas layout, migration path, button placement,
  idempotence, regression guard) are resolved next session.

- **Spec impact:**
  - `plot/docs/PRODUCT_SPEC.md` §15 #2 — updated 2026-05-13 with
    the 4-point vision and "in-discussion" status (replaces
    "deferred").
  - `mashbill/docs/SPEC.md` — **no change yet**; Phase 2 implementation
    will rewrite Foundation §Storage / §Typed-text sections.
    Today's ship is vision-pin only.
  - `mashbill/docs/CONCEPTS.md` — no change yet.

- **Out of scope (today):** Phase 2 implementation code
  (folder_io / models / api_endpoints / viewer editor — none
  touched). All detail decisions (open-questions list above)
  deferred to next session.

- **NEXT_SESSION trigger:** ``JSON SSOT 논의`` / ``json 원본`` /
  ``MD 추출`` / ``export 버튼`` / ``phase 2`` / ``내일 논의``.

- **Files in this commit:**
  - `mashbill/docs/DECISIONS.md` — this entry.
  - `plot/docs/PRODUCT_SPEC.md` — §15 #2 update.
  - `mashbill/docs/NEXT_SESSION.md` — `JSON SSOT 논의` queue entry.
  - `mashbill/CHANGELOG.md` — v0.16.33 section.
  - `mashbill/.claude-plugin/plugin.json` — patch bump 0.16.32 → 0.16.33.

- **Reference:** plan file
  `~/.claude/plans/sparkling-discovering-blanket.md` (user-approved
  this session) contains the 7 open detail questions for
  next-session reference.

---

### D-2026-05-13-K — Page-load refetch storm fix (anchor add-then-evict loop)

- **What:** Guard ``migrate.py::upgrade_foundation_canvas_if_needed``
  step 4 (pre-v0.13 project-anchor synthesis) on
  ``ProjectDoc.anchors[canvas_kind]``. When ``project.json`` already
  carries an anchor for foundation, step 4 short-circuits — no node
  synthesis, no canvas.json write, no watcher fire.

- **Why:** User reported 2026-05-13 *"파운데이션 볼건데요. 노드가
  보였다가 사라지네요"* on fresh page load. Server log showed the
  GET 3-call set (``/projects`` → ``/projects/{id}`` →
  ``/projects/{id}/canvases/foundation``) repeating dozens of times
  — an **infinite refetch storm**.

  The previous-day "잘 동작" confirmation (D-2026-05-13-H) was
  technically correct *for that session's state* — the user's
  optimistic in-memory state was masking the storm. Fresh page
  reload loses optimistic state → storm is visible (predicted by
  D-2026-05-13-I).

  The actual root cause is a **direct-opposing-writes loop** between
  two migration helpers that both fire on every read:

  1. ``migrate.py::upgrade_foundation_canvas_if_needed`` step 4
     (line 834) — pre-v0.13 migration that *synthesises* a
     ``kind=project`` anchor node when ``canvas.json`` has none.
     Writes the file.
  2. ``folder_io.py::_evict_legacy_project_anchor`` (line 478) —
     v0.13 Phase 0 migration that *removes* any ``kind=project``
     node and copies its placement into ``ProjectDoc.anchors``.
     Writes the file.

  For v0.13+ projects the sequence on every ``read_canvas`` is:

  ```
  upgrade.step4 adds anchor node (write 1)
    → _evict_legacy removes anchor node (writes 2 + 3 — canvas.json + project.json)
      → watcher debounce 200ms
        → broadcast 'project_changed'
          → viewer onExternalCanvas → fresh getCanvas
            → read_canvas runs again → upgrade.step4 adds anchor node …
  ```

  Loop bandwidth: roughly 3 GETs per cycle, cycles every ~200-500 ms
  (debounce + roundtrip). Each cycle replaces ``canvasCache`` in
  React state — the viewer's React Flow remounts within a race window
  that sometimes leaves nodes unrendered, producing the user-visible
  "noodes briefly appear then disappear" symptom.

- **Why this wasn't caught earlier:** Step 4 is *individually
  correct* for pre-v0.13 projects and *idempotent in isolation*
  (running it twice on a pre-v0.13 fixture produces the same
  result). The interaction with v0.13 Phase 0's
  ``_evict_legacy_project_anchor`` was the missing case. Neither
  function alone is broken; the *pair*, called in sequence on every
  read, is.

  This matches the v0.13.3-v0.13.10 cursor saga's anti-pattern: a
  migration step left in place across a major refactor without
  re-evaluating its interaction with the new state model.
  ``mashbill-design-red-team`` Attack 2 (Unstated invariants) gains a
  new calibration anchor: *"migration helpers must be re-evaluated
  against the post-migration state model; a step that was a no-op
  by chance becomes a self-loop by chance."*

- **Why the specific fix (not the others considered):**
  - **Alternative A (rejected):** delete step 4 entirely. Risk:
    breaks pre-v0.13 projects that genuinely need the synthesis
    (would lose their anchor permanently). The two regression tests
    pin both behaviours independently — kept the synthesis path
    intact via the alternate branch.
  - **Alternative B (rejected):** add origin tag to ``_write_json``
    so the watcher can skip "self-echoed" writes. Risk: scope
    expansion to the entire write surface; many helpers would need
    plumbing. Surgical fix at step 4 is enough — once step 4 stops
    writing on the idempotent path, the loop stops.
  - **Alternative C (rejected):** make ``_evict_typed_text_to_md``
    strict-idempotent. Originally suspected in the plan, but Phase
    3 code re-read showed that function is already idempotent for
    cleaned canvases. The actual write source was step 4.

- **Approval:** **Accepted** — Gate 3 hands-on verified by user
  2026-05-13 after MCP HTTP server restart with the new step-4
  guard. User verbatim: *"이제 됐습니다."* Foundation nodes appear
  and stay visible; no refetch storm in server log.

---

### D-2026-05-13-L — Auto-layout re-introduction (Foundation only, opt-in)

- **What:** Re-introduce the v0.13.9 directional-tree auto-layout
  feature as a **Foundation-only opt-in**. ``SketchCanvas`` gains
  an optional ``enableAutoLayout?: boolean`` prop (default false).
  ``FoundationCanvas`` is the *only* wrapper that passes
  ``enableAutoLayout={true}``. Other wrappers (Actors / Services /
  ServiceDetail) never opt in.

- **Why now:** User direct request 2026-05-13: *"혹시 자동 정렬을
  넣을 수 있을까요? 이걸 물어보는 이유는 자동 정렬 기능을 넣으면
  항상 캔버스 기본동작들이 망가졌기 때문입니다. ... 다른 곳에
  영향이 안 가게 만들어야합니다."* User trauma from 4 prior
  add/remove cycles (D-04-D / D-10-E / D-10-F / D-10-G) — isolation
  is the non-negotiable constraint.

- **Re-introduction policy compliance** (per D-2026-05-10-G's
  "Re-introduction policy" 4-condition gate):

  | Condition | Satisfied by |
  |---|---|
  | (a) Fresh ``D-YYYY-MM-DD-X`` entry | this entry |
  | (b) Real-user workflow demanding it | user's direct ask |
  | (c) Cost/benefit comparison vs D-10-G | the 4-layer isolation contract (below) addresses the "다른 곳에 영향" risk that D-10-G feared. Cursor flicker that originally co-occurred with auto-layout was independently caused by Tailwind preflight and fixed in D-2026-05-10-F — that risk path is permanently closed. |
  | (d) Explicit user approval before code | ExitPlanMode-approved plan, 2026-05-13 |

- **Isolation contract (4 layers of defence):**

  1. **Wrapper opt-in** — only ``FoundationCanvas`` passes
     ``enableAutoLayout={true}``. Other 3 wrappers don't pass the
     prop → default false → button never renders. Adding any other
     wrapper to the opt-in list is a breaking change that must
     update ``viewer/tests/auto-layout-isolation.test.tsx``.
  2. **Conditional render** — ``SketchCanvas`` renders the
     ``ControlButton`` only when ``enableAutoLayout === true``.
     React hooks (e.g. ``useAutoLayout``) are still called
     unconditionally (hooks rule) but the returned callback is
     wired only to a button that doesn't exist when off — dead
     code path with zero side effects.
  3. **No state mutation when disabled** — the hook's callback is
     pure with respect to ``doc.nodes`` until invoked. ``doc``
     itself is never read during the hook's identity stability,
     only inside the on-click handler. Nothing fires implicitly.
  4. **Touches positions only** — the on-click handler computes
     new ``(x, y)`` for each user node, builds ``next = {...doc,
     nodes: doc.nodes.map(...)}``, and dispatches a single
     ``onDocChange(next)``. ``kind``, ``label``, ``parent_id``,
     typed-text fields, and edges are spread through unchanged.

- **One-shot apply + Cmd+Z** (chose over the plan's preview/apply
  pattern): the explicit user-consent guarantee comes from the
  button click itself; the regular undo stack is the safety net.
  A separate preview state machine would add 15+ LOC + a separate
  visual surface for no additional isolation gain. The
  preview/apply pattern is preserved as a future option if hands-on
  shows the one-shot UX is too aggressive — convert to preview
  state pattern in a follow-up D-entry.

- **Algorithm:** Restored unchanged from v0.13.9
  (``viewer/src/canvases/sketch/autoLayout.ts``, commit
  ``75330c7``, 297 LOC, pure function — no React imports).
  Deterministic BFS from the project anchor, handle-aware
  directional placement, Reingold-Tilford-style sibling spacing.
  Tied to a fixed anchor so the layout is reproducible across
  sessions.

- **Type compatibility:** Confirmed via ``npx tsc --noEmit`` —
  the v0.13.9 algorithm reads only ``BaseFields`` (id / x / y /
  width / height) on nodes, which is the common shape of every
  member of the v0.15+ ``SketchNode`` discriminated union. No
  changes needed to the algorithm.

- **Approval:** Pending — Gate 3 hands-on verification by user in
  real Chrome.

- **Spec impact:**
  - ``mashbill/docs/SPEC.md`` §Auto-layout — full rewrite reflecting
    the new Foundation-only opt-in + 4-layer isolation contract +
    5-cycle history block.
  - ``mashbill/CLAUDE.md`` rule 6 — *"No auto-layout"* → *"Auto-layout
    is Foundation-only opt-in"* with explicit prohibition on
    adding other wrappers without a fresh D-entry.

- **Files in this commit:**
  - ``plot/viewer/src/canvases/sketch/autoLayout.ts`` (restored,
    pure function).
  - ``plot/viewer/src/canvases/sketch/useAutoLayout.ts`` (restored,
    React hook).
  - ``plot/viewer/src/canvases/SketchCanvas.tsx`` (prop + conditional
    button, 412 → 419 LOC, within 420 ceiling).
  - ``plot/viewer/src/canvases/FoundationCanvas.tsx``
    (``enableAutoLayout={true}``).
  - ``plot/viewer/tests/autoLayout.test.ts`` (restored, 13 unit
    tests).
  - ``plot/viewer/tests/auto-layout-isolation.test.tsx`` (new, 6
    isolation regression tests).
  - ``plot/viewer/tests/SketchCanvas.regression.test.tsx``
    (comment rewrite — default-off + Foundation opt-in semantics).
  - ``mashbill/docs/SPEC.md`` §Auto-layout (rewrite).
  - ``mashbill/CLAUDE.md`` rule 6 (rewrite).
  - ``mashbill/CHANGELOG.md`` v0.16.36 section.
  - ``mashbill/.claude-plugin/plugin.json`` patch bump 0.16.35 → 0.16.36.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 461 viewer tests.
  - After: 486 viewer tests (+25 — 13 autoLayout unit + 6 isolation
    + 6 follow-up from regression toggle).

---

### D-2026-05-13-M — Anchor edge 422 reject fix (D-2026-05-13-I root cause)

- **What:** Whitelist the synthetic project anchor id
  (``__project_anchor__``) in ``CanvasDoc._edges_reference_nodes``
  Pydantic validator so user-drawn edges with the anchor as
  ``source`` or ``target`` validate cleanly. Plus a compounding
  error-message bug fix — the validator now reports the actual
  *missing endpoint ids*, not the *edge ids of dangling edges*.

- **Why:** User reported 2026-05-13 *"왜 새로 고침하면 연결선이
  사라지죠?"* — user-drawn edges between the synthetic anchor and
  other nodes silently failed to persist. The viewer's optimistic
  update masked the 422 reject (edge appears on screen) until
  reload lost the optimistic state and the empty server response
  surfaced.

  Phase 1 trace (two Explore agents, file:line cited):
  - Viewer creates the edge correctly: ``useFlowHandlers.handleConnect``
    sets ``edge.source = connection.source`` (which is
    ``"__project_anchor__"`` when the user drags from the anchor's
    handle).
  - ``putCanvas`` sends the doc raw with no transform.
  - Server-side validator (``models.py:538-545``) does
    ``node_ids = {n.id for n in self.nodes}`` — the anchor lives
    in ``ProjectDoc.anchors``, not ``canvas.nodes``, so its id is
    missing from ``node_ids``. Every anchor edge gets flagged as
    "referencing unknown nodes" and 422 rejected.
  - D-2026-05-04-B SPEC mandate (*"User may draw edges from / to
    the anchor like any other node"*) is violated at the
    validator layer, even though the viewer-side rendering layer
    honours it.

  Compounding bug: the validator's error message reported the
  *edge ids of the dangling edges* (``{e.id for e in dangling}``),
  not the missing endpoint ids. The ``e_<timestamp>_<random>`` ids
  in the error text *looked like* node ids but weren't — they were
  always the edge's own id. This sent D-2026-05-13-I diagnosis
  toward a fictional "edge id is being set as source/target"
  hypothesis when the real story was much simpler: a missing
  whitelist entry.

- **Fix:**

  ```python
  PROJECT_ANCHOR_ID = "__project_anchor__"  # mirrors viewer/constants.ts

  @model_validator(mode="after")
  def _edges_reference_nodes(self) -> CanvasDoc:
      node_ids = {n.id for n in self.nodes} | {PROJECT_ANCHOR_ID}
      dangling = [...]
      if dangling:
          missing = sorted({
              ep for e in dangling
              for ep in (e.source, e.target)
              if ep not in node_ids
          })
          raise ValueError(f"edges reference unknown nodes: {missing}")
      return self
  ```

  Two changes in one validator: anchor whitelisted + error message
  reports actual missing endpoints (sorted, distinct, no edge ids).

- **Why not the alternatives:**
  - **Alt 1 (rejected):** Have the server store anchor edges in a
    separate ``ProjectDoc.anchor_edges`` field. Risk: schema fork
    between viewer (one edges list) and server (two edges lists)
    that would have to be re-merged on every read. Higher
    complexity for zero functional gain.
  - **Alt 2 (rejected):** Strip anchor edges on the client before
    PATCH. Risk: anchor edges become client-local only — exactly
    the bug we're fixing (edges sync-lost on reload). Same UX
    failure mode.
  - **Alt 3 (rejected):** Restore the v0.13 Phase 0 model where
    the anchor lives in ``canvas.nodes``. Conflicts with
    D-2026-05-13-K's storm fix and reopens a settled architectural
    question. Out of scope.

- **Approval:** Pending — Gate 3 hands-on verification by user in
  real Chrome after MCP HTTP server restart.

- **Spec impact:**
  - D-2026-05-04-B is now actually enforceable end-to-end. SPEC.md
    §Anchor "Handles visible. User may draw edges from / to the
    anchor like any other node" was the *user-visible* contract;
    the server validator now honours it.

- **Files in this commit:**
  - ``mashbill/mashbill/models.py`` — ``PROJECT_ANCHOR_ID`` constant +
    validator (anchor whitelist + error message fix).
  - ``mashbill/tests/test_canvas_doc.py`` — 5 regression tests
    (anchor edge both directions accepted, error message reports
    missing endpoints not edge ids, multi-edge case, mixed
    anchor-plus-ghost case).
  - ``mashbill/CHANGELOG.md`` — v0.16.37 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.36 → 0.16.37.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 276 server tests.
  - After: 281 server tests (+5 regression).

- **D-2026-05-13-I closure status:**
  - 422 storm + "e_-prefixed unknown node ids" — **resolved** by
    this entry (both the anchor whitelist and the error-message
    bug). The misleading e_-prefixed ids in the error text are
    gone; the underlying 422 cause is fixed.
  - ``services/canvas.json`` orphan edge ``e_mopntgek_4y74``
    (source/target both ``None``) — **remains open**. Separate
    storage-cleanup pass needed; not addressed here.

- **Lesson:** Error messages that misreport *what* is wrong send
  diagnosis down wrong paths. The ``{e.id for e in dangling}``
  expression was off by one indirection — it should have been the
  set of missing endpoint ids, not the set of edge ids whose
  endpoints were missing. ``mashbill-design-red-team`` Attack 6 (Error
  taxonomy) gains a new calibration anchor: *"the error message
  must name the thing that is missing, not the thing that
  references the missing thing."*

---

### D-2026-05-13-N — Anchor edge cleanup whitelist (v0.16.37 follow-up)

- **What:** Add ``PROJECT_ANCHOR_ID`` to the ``node_ids`` set in
  ``_evict_legacy_project_anchor``'s defensive orphan-edge cleanup
  branch (``folder_io.py:437-443``). Same one-line fix as v0.16.37
  applied to the second location that needed it.

- **Why:** User reported v0.16.37 incomplete: *"안고쳐짐.
  새로고침을 하다보면 캔버스에 노드들이 사라지는 이슈가 있네요"*.
  Investigation:
  - canvas.json showed 2 anchor edges present (the v0.16.37 fix
    made user PUT 200 OK, edges hit disk).
  - Server log showed PUT 200 OK + ongoing GETs.
  - Server-side ``_evict_legacy_project_anchor`` has a *second*
    cleanup that runs even when ``legacy_anchors`` is empty (the
    defensive branch). That cleanup also did
    ``node_ids = {n.get("id") for n in nodes}`` — the same anchor-id
    gap the Pydantic validator had.
  - Sequence: read canvas → defensive cleanup strips anchor edges
    → write empty edges → watcher fires → viewer refetches →
    fresh read → empty doc → nodes/edges disappear from viewer
    even though storage briefly recovers when the next user PUT
    races in.

  This is the *same shape* as the v0.16.34 add-then-evict loop, with
  a different pair of functions in opposing directions:

  ```
  user PUT writes anchor edges  →  storage has them briefly
  read calls _evict_legacy → defensive cleanup → strip → write 0
  → watcher → broadcast → viewer refetch (empty response)
  → next user PUT writes anchor edges again ... race race race
  ```

  v0.16.37 fixed only the validator. The cleanup was the second
  bull in the china shop.

- **Why this was missed in v0.16.37:** The Phase 1 agent's grep on
  ``__project_anchor__`` correctly found zero matches in
  ``mashbill/``, but the *risk surface* was wider than the grep
  hit count: any function with a literal ``{n.id for n in nodes}``
  *set difference against edge endpoints* needed the same fix.
  Lesson encoded for mashbill-design-red-team Attack 5 (Implicit
  invariants): *"when adding a whitelist constant for a synthetic
  id, audit every place that computes a 'known ids' set against
  edge endpoints — not just the place named in the bug report."*

- **Fix:**

  ```python
  if not legacy_anchors:
      from mashbill.models import PROJECT_ANCHOR_ID
      node_ids = {n.get("id") for n in nodes} | {PROJECT_ANCHOR_ID}
      ...
  ```

  One line of effective change (the ``| {PROJECT_ANCHOR_ID}``).

- **Why local import:** Module-level import would create a
  circular-import risk between ``folder_io`` (which imports models)
  and ``models`` (which doesn't, but might in future). The local
  import keeps the dependency edge unidirectional. Cheap pattern;
  the function is only called on cold reads, not hot paths.

- **Approval:** **Accepted** — Gate 3 hands-on verified by user
  2026-05-13 after MCP HTTP server restart. User verbatim:
  *"이제 동작하네"*. Nodes no longer disappear on reload; anchor
  edges persist across repeated hard reloads.

- **Spec impact:** None — same surface as D-2026-05-13-M, just a
  second function that needed the same whitelist.

- **Files in this commit:**
  - ``mashbill/mashbill/folder_io.py::_evict_legacy_project_anchor`` —
    defensive cleanup whitelist.
  - ``mashbill/tests/test_folder_io.py`` — 2 regression tests:
    - ``test_read_canvas_preserves_anchor_edges_across_repeated_reads``
      — anchor edges survive read + canvas.json mtime stable.
    - ``test_orphan_non_anchor_edges_still_stripped`` —
      backward-compat: non-anchor orphan edges still stripped.
  - ``mashbill/CHANGELOG.md`` — v0.16.38 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.37 → 0.16.38.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 281 server tests.
  - After: 283 server tests (+2 regression).

- **D-2026-05-13-I closure status (updated):**
  - 422 storm + e_-prefixed unknown ids: resolved in
    D-2026-05-13-M.
  - 'nodes disappear on reload' refetch loop via anchor-edge cleanup:
    resolved here in D-2026-05-13-N.
  - ``services/canvas.json`` None→None orphan edge: still open.

- **Lesson (process):** Sequential bug-fix sessions that share a
  root cause (synthetic-id gap) should audit *every* function with
  the same shape, not just the one named in the bug report.
  Adding the same whitelist twice in one day for the same constant
  is the signal.

---

### D-2026-05-13-O — JSON SSOT migration: 7 principles (Phase 0 vision pin)

- **What:** User stated 7 principles for the JSON SSOT + per-node
  MD + per-node versioning + folder-hierarchy migration during the
  2026-05-13 design discussion that continued D-2026-05-13-J's
  vision pin. This entry pins the 7 principles canonically and
  references the approved 6-phase ship sequence
  (``~/.claude/plans/sparkling-discovering-blanket.md``).

  The 7 principles:

  1. **JSON = SSOT.** v0.13's JSON+MD co-equal storage is abolished.
  2. **JSON value = MD-formatted string.** Typed-text fields are
     stored inside JSON as MD-formatted strings; viewer edits via
     an MD-aware editor.
  3. **MD extraction = "발행" (publish) button.** No automatic sync.
  4. **per-node MD file.** *Supersedes D-2026-05-13-J point #4*
     ("per-canvas single MD") — user explicit clarification:
     *"각 노드의 MD 분리해야죠"*.
  5. **Per-node versioning.** File-level git history = node history.
  6. **Version format ``vMAJOR.MINOR``:**
     - MAJOR + 1 when the node's own content is published.
     - MINOR + 1 when any descendant publishes (chain-propagated
       to all ancestors).
     - Leaf nodes (no children): MAJOR only (``v1.0`` → ``v2.0`` → …).
     - User quote: *"하위 노드가 버전이 업데이트 되면 상위 노드의
       버전도 올라가야겠죠. ... 메이저와 마이너 마이너는 하위
       버전이 올라갈 때 올라가구요"*.
  7. **MD folder hierarchy = node hierarchy 1:1.** Container nodes
     become folders; leaves become files inside (or ``index.md``
     inside its own folder). User quote: *"md 정리는요. 폴더를
     적극 활용하세요"*.

- **Why now:** D-2026-05-13-J's "이건 내일 논의해봅시다" promise
  is being kept *today* (the in-session "내일"). User reopened
  the discussion mid-session after the v0.16.37 / v0.16.38 fix
  loop closed, asked plan-mode if needed, and approved Phase 0.

- **Why Phase 0 = docs only:** small-ships per
  ``feedback_small_ships_over_big_bangs.md`` and explicit user
  trauma from the auto-layout 4 cycles (D-2026-05-04-D /
  D-2026-05-10-E / D-2026-05-10-F / D-2026-05-10-G). Pinning the
  principles in docs before any code lands gives Phase 1-6 a
  stable reference + a same-day rollback path.

- **6-phase sequence (full plan in
  ``~/.claude/plans/sparkling-discovering-blanket.md``):**

  | Phase | Scope | Ship version |
  |---:|---|:---:|
  | 0 | Vision pin docs only (this entry) | v0.16.40 |
  | 1 | MD → JSON absorption (kill MD-as-SoT) | v0.17.0 |
  | 2 | ``version: str = "v1.0"`` in BaseFields | v0.17.1 |
  | 3 | "Publish" button + per-node MD + MAJOR bump (leaf) | v0.17.2 |
  | 4 | MINOR propagation (ancestor chain) | v0.18.0 |
  | 5 | Folder hierarchy + container-publish semantics | v0.19.0 |
  | 6 | Legacy purge + final docs sync | v0.19.1 |

  Each subsequent phase opens its own plan-mode + user approval.

- **Container-publish semantics (deferred to Phase 5):** The 7
  principles do not specify container-publish behavior in singular
  form. Three alternatives flagged for Phase 5 plan-mode entry:
  - A) container = own MD + every descendant MD + 1 commit (default).
  - B) container = own MD only; children stay at their versions.
  - C) container = own MD + immediate children only.
  User decides at Phase 5; not this session.

- **isomorphic-git integration (out of scope for all 6 phases):**
  Existing ``mashbill/git_store.py`` (subprocess-native) is
  sufficient through Phase 6. isomorphic-git is a separate v0.20+
  lane (ROADMAP §"v0.17+" already lists it with 6 Major findings
  from ``mashbill-design-red-team``). Conflating it with publish would
  create a 12-issue mega-phase.

- **Approval:** **Accepted (Phase 0 only)** by user, 2026-05-13.
  Plan-mode plan approved + 7 principles confirmed verbatim
  (*"맞아요. 맞습니다."*, *"네네 맞아요"*, *"좋습니다. 가봅시다"*).
  Phases 1-6 approval queued; each phase opens its own
  approval cycle.

- **Spec impact:**
  - ``plot/docs/PRODUCT_SPEC.md`` §15 #2 — 4-point block replaced
    with 7-principle list + cross-reference to this entry.
  - ``mashbill/docs/NEXT_SESSION.md`` — ``JSON SSOT 논의`` entry
    transitions to ``Phase 1 — JSON SSOT 구현 (MD 흡수)``.
  - ``mashbill/docs/SPEC.md`` — no change yet (Phase 1+ will rewrite
    Foundation §Storage and §Typed-text sections; container-publish
    will land in §Edges or §Versioning section in Phase 5).
  - ``mashbill/docs/CONCEPTS.md`` — no change yet (Phase 2 will add
    ``version`` to BaseFields documentation).

- **D-entry supersede chain:**
  - D-2026-05-12-A §15 #2 — original deferred entry. Stays as
    historical record.
  - D-2026-05-13-J — first vision pin. Today's entry supersedes
    point #4 explicitly (per-canvas → per-node); points 1-3 carry
    forward verbatim; new points 5-7 added.
  - D-2026-05-13-O (this entry) — 7-principle vision + 6-phase
    sequence reference.
  - D-2026-05-?? × 6 — one entry per Phase 1-6 implementation.

- **Files in this commit:**
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``plot/docs/PRODUCT_SPEC.md`` §15 #2 update.
  - ``mashbill/docs/NEXT_SESSION.md`` — Active queue refresh.
  - ``mashbill/CHANGELOG.md`` — v0.16.40 section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.39 → 0.16.40.

- **Next-session trigger:** ``Phase 1`` / ``JSON SSOT 구현`` /
  ``MD 흡수``.

- **Out of scope:**
  - Services orphan edge ``e_mopntgek_4y74 | None → None`` —
    D-2026-05-13-I residual. Separate cleanup pass.

- **Spec impact:** None — internal migration helper. The user-facing
  invariant ("page load is a single GET set per canvas, then idle")
  is implicit in the design; no SPEC.md line names it. If this class
  of bug recurs, consider pinning the invariant explicitly.

- **Files in this commit:**
  - ``mashbill/mashbill/migrate.py`` — step 4 guard +
    ``_project_doc_has_anchor`` helper.
  - ``mashbill/tests/test_migrate.py`` — 2 new regression tests.
  - ``mashbill/CHANGELOG.md`` — v0.16.34 Fixed section.
  - ``mashbill/.claude-plugin/plugin.json`` — patch bump 0.16.33 → 0.16.34.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:**
  - Before: 274 server tests.
  - After: 276 server tests (+2 regression).

- **Related entries:**
  - D-2026-05-13-H — yesterday's hands-on pin ("이제 잘 동작") was
    masked by optimistic state; today's fresh page load surfaced the
    underlying loop.
  - D-2026-05-13-I — predicted the surfacing ("would surface if the
    user's session ever loses its optimistic state"). The 422 storm
    in I may also stem from the same loop (each cycle re-tries the
    PATCH that 422s) — verify after this fix lands.

- **Next-session impact:** ``잔여 silent state`` entry (D-2026-05-13-I)
  may be partially or fully resolved by this fix. Re-evaluate after
  Gate 3 hands-on confirms storm is gone.

### D-2026-05-16-A — Phase 1 JSON SSOT (MD absorbed, _legacy/ quarantine)

- **What:** Implement Phase 1 of the 6-phase JSON SSOT sequence
  pinned by D-2026-05-13-O. Foundation typed-text kinds
  (mission / core_value / identity) carry every MD-syntax string
  field (typed + new ``body``) inline in JSON; the read-side
  migrator ``_absorb_md_typed_text_into_json`` ingests pre-v0.17
  ``foundation/{kind}-{slug}.md`` files into the JSON node and
  quarantines them to ``foundation/_legacy/``. ``write_canvas`` no
  longer splits typed fields out to MD; ``details_path`` is cleared
  on these kinds unconditionally; the viewer's DetailsSection
  MD-editor surface is hidden via a new ``hideDetailsSection`` prop
  on ``BaseInspector``. Inspector typed-text textareas become
  monospace + newline-preserving so users edit raw MD-syntax
  strings. A shared ``BodyField`` component renders the new ``body``
  field in all 3 inspectors.

- **Why:** D-2026-05-13-O's principle #1 (JSON = SSOT) and #2 (JSON
  value = MD-formatted string) cannot coexist with the v0.13
  eviction-and-rehydration loop. Phase 1 retires the dual-storage
  model — a precondition for Phase 2 (per-node versioning) and
  Phase 3 (Publish button, MD becomes pure output).

- **Conflict policy (the 4 scenarios named in the plan-file):**
  - JSON empty, MD populated → MD wins; absorb.
  - JSON populated, MD missing → no-op (JSON already SSoT).
  - Both populated → JSON wins (latest); MD still quarantined.
  - Both empty → no-op.

  Plus a 5th invariant: ``details_path`` is cleared on Foundation
  typed-text kinds regardless of value (canonical or
  user-set-custom), because the v0.17 UI no longer surfaces an MD
  editor for these kinds.

- **Why per-node ``body`` is structurally just another MD-syntax
  field, not a separate "free prose" channel:** Per user
  re-confirmation 2026-05-16 (*"json 이 원천이라고 그리고 거기
  들어가는 밸류 필드의 문법이 엠디 여야한다고"*). The new ``body``
  field's value is an MD-syntax string identical in handling to
  ``what_we_do`` / ``definition`` / ``do`` / etc. Its semantic role
  ("long-form notes") is conveyed only by its i18n label
  (``inspector.field.body`` — "Notes (Markdown)" / "노트
  (Markdown)"); the storage and editing model is uniform.

- **Why ``_legacy/`` quarantine (not delete):** Data preservation.
  Phase 6 (v0.19.1) will offer a one-time user prompt to delete the
  quarantine after they confirm migration safety in real projects.
  No precedent existed in the codebase for this pattern; the
  migrator introduces it.

- **Why ``_split_foundation_typed_text_to_md`` deleted (not
  neutered):** Plan-file Phase 1 explicitly says "replace ... with
  a one-shot read-side migrator". Pydantic ``model_dump(by_alias=True)``
  already emits every field — including the new ``body`` — directly
  to the JSON output, so a no-op shim adds nothing. Deletion makes
  the disk-write code path readable end-to-end.

- **Why ``collect_foundation_md_warnings`` returns ``{}`` instead
  of being deleted:** It is called from
  ``api_endpoints.canvas_get_endpoint`` to surface MD-template
  warnings in the API response. After absorption no canonical MD
  files exist, so warnings are always empty. Kept as a stable
  callable for backward API compatibility; Phase 6 deletes the
  call site.

- **Alternatives considered and rejected:**
  - Co-equal JSON+MD storage (the v0.13 status quo) — creates two
    SSoTs; principle #1 forbids.
  - Per-canvas single MD file (D-2026-05-13-J point #4) — already
    superseded by D-2026-05-13-O point #4.
  - Drop free prose entirely on absorption — data loss; user
    explicitly chose ``body`` field for preservation.
  - Keep ``details_path`` pointing at the quarantined file — re-
    enables the DetailsSection MD editor surface, contradicting the
    user's "MD 파일 편집은 사용자가 못하게" intent.
  - WYSIWYG / MD-preview editor in Phase 1 — out of scope per
    user's "preview 없음" decision; raw monospace edit suffices.

- **Approval:** **Accepted** by user, 2026-05-16. Approved sequence:
  plan-mode plan (``~/.claude/plans/eager-fluttering-moore.md``)
  approved → 3 design questions answered (body field added; legacy
  link not kept; MD editing disabled) → mid-implementation re-anchor
  ("json 이 원천이라고") → Gate 4 confirmation ("이거 하고 게이트
  4까지 합시다") covering the implementation as a whole.

- **Spec impact:**
  - ``plot/docs/PRODUCT_SPEC.md`` §15 #2 — Phase 1 status updated
    from "queued" to "shipped 2026-05-16".
  - ``mashbill/docs/NEXT_SESSION.md`` — ``Phase 1`` active-queue entry
    archived; ``Phase 2`` becomes the next trigger.
  - ``mashbill/docs/SPEC.md`` — Foundation typed-text storage line
    inside §Storage updated to reflect JSON-SSOT.

- **Files in this commit:**
  - Server: ``mashbill/models.py``, ``mashbill/folder_io.py``.
  - Server tests: ``tests/test_folder_io.py``,
    ``tests/test_api_endpoints.py``.
  - Viewer domain: ``viewer/src/domain/{Mission,CoreValue,Identity}.ts``.
  - Viewer inspectors: ``viewer/src/canvases/inspectors/BaseInspector.tsx``,
    ``shared/BodyField.tsx`` (new),
    ``shared/DoDontFields.tsx``,
    ``{mission,core_value,identity}/index.tsx``.
  - Viewer i18n: ``viewer/src/i18n/locales/{en,ko}.json``.
  - Docs: this entry + CHANGELOG + PRODUCT_SPEC + NEXT_SESSION + SPEC.
  - Manifest: ``mashbill/.claude-plugin/plugin.json`` 0.16.40 → 0.17.0.

- **Test counts:**
  - Server: 283 → 290 (+7 ``test_absorb_md_typed_text_into_json_*``).
  - Viewer: unchanged (488 / 488 still green; schema-parity auto-
    flowed the new ``body`` field).

- **Related entries:**
  - D-2026-05-13-O — vision pin this entry implements (Phase 1 of
    the 6-phase sequence).
  - D-2026-05-13-J — earlier 4-point vision, point #4 superseded
    by D-2026-05-13-O.
  - D-2026-05-12-A — v0.13 co-equal storage being retired.

- **Next phase trigger:** ``Phase 2`` / ``BaseFields version`` /
  ``v1.0 필드`` — adds ``version: str = "v1.0"`` to
  ``BaseNodeFields`` with ``^v\\d+\\.\\d+$`` validator (server) +
  mirror in TS (viewer). No UI surface yet. The Phase 2 ship
  version is decided in its own plan-mode entry; the originally
  planned slot ``v0.17.1`` is being taken by an unrelated UX patch
  (D-2026-05-16-B); Phase 2 lands as v0.17.2 or later.

### D-2026-05-16-B — Anchor click closes Inspector

- **What:** Clicking the synthetic project anchor on any canvas
  now closes the currently-open Inspector (sets
  ``inspectorNodeId`` to ``null``). Previously
  ``useInspectorRouting.onNodeClick`` had an early-return no-op for
  the anchor — the v0.13 implementation read "anchor has no
  Inspector", which left whichever node was previously selected
  stale on screen.

- **Why:** Per-user request (2026-05-16): *"프로젝트 앵커 노드
  클릭하면 이전에 선택되었던 노드 상세 닫히게 해주세요."* In the
  user's mental model, the anchor is a content-less centre marker;
  clicking it is a "deselect everything" gesture, not a no-op.
  Anchor click now produces the same effect as clicking the empty
  pane — `setInspectorNodeId(null)`. The change is minimal and
  matches Novel's UX principle "Clear Feedback" (every click produces
  visible state change).

- **Why ship as its own commit (not bundled with v0.17.0 Phase 1):**
  Novel CLAUDE.md anti-pattern "Bundling a cross-cutting visual
  change with a feature change in one commit" — v0.13.10's
  cursor-patch-plus-auto-layout precedent shows what happens when
  visual fixes ride along with feature commits. Phase 1 ships pure
  storage migration; this UX polish ships on its own as v0.17.1.

- **Alternatives considered:**
  - Leave anchor as no-op (status quo) — rejected, user explicitly
    asked for the close-on-click behaviour.
  - Make anchor itself open an Inspector showing project metadata —
    out of scope; the anchor SSOT is ``ProjectDoc.anchors`` + the
    label is ``ProjectDoc.name``, no per-anchor typed-text exists.

- **Approval:** **Accepted** by user, 2026-05-16. Direct request
  ("프로젝트 앵커 노드 클릭하면 이전에 선택되었던 노드 상세 닫히게
  해주세요").

- **Spec impact:** Implicit. The behaviour matches the existing
  ``onPaneClick`` deselect semantic; SPEC.md §Inspector "Trigger"
  row already says "Single click on a node (any kind except — TBD
  anchor)" — the TBD now resolves to "anchor click deselects". No
  separate SPEC line needed for this small clarification; the test
  is the spec.

- **Files in this commit:**
  - ``viewer/src/canvases/sketch/useInspectorRouting.ts`` —
    onNodeClick anchor branch sets null.
  - ``viewer/tests/anchor-click-closes-inspector.test.tsx`` — new
    regression guard (2 cases).
  - ``mashbill/CHANGELOG.md`` — v0.17.1 section.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/.claude-plugin/plugin.json`` — 0.17.0 → 0.17.1.

- **Test counts:**
  - Viewer: 488 → 490 (+2). Server unchanged (290 / 290).

---

### D-2026-05-16-C — Phase 2 per-node `version` field in BaseFields

- **What:** Add a per-node ``version: str = "v1.0"`` field to
  ``mashbill/models.py::BaseNodeFields`` (server) and to both
  ``BaseFieldsJson`` (wire) and ``BaseFields`` (in-memory) interfaces
  in ``viewer/src/domain/BaseFields.ts``, plus a single
  ``version: this.version,`` line and a ``readonly version!:
  string;`` declaration on each of the 15 per-kind entity classes.
  Both layers enforce the format ``^v\d+\.\d+$`` via a regex (model
  validator on the server, ``asVersionString`` helper on the viewer).

- **Why:** The 7-principle JSON SSOT vision (D-2026-05-13-O) calls
  for explicit per-node versioning so future phases can:

  - **Phase 3** — increment a node's ``version`` on explicit
    "Publish" (MAJOR bump), emit a per-node MD export tagged with
    that version.
  - **Phase 4** — propagate the bump up the ancestor chain (MINOR
    bumps on parents).
  - **Phase 5+** — folder-hierarchy publish semantics depend on the
    field.

  Phase 1 (v0.17.0) made JSON the SSOT for typed-text content;
  Phase 2 now lays the data foundation Phases 3–5 read from and
  write to. The phase ships **with no UI surface** — no badge, no
  button, no visible difference. The visual surface lands in
  Phase 3.

- **Alternatives considered:**
  - **3-component SemVer (``v1.2.3``)** — rejected for v0.17.x.
    The publish model (Phase 3: MAJOR; Phase 4: MINOR) only needs
    two components today. A patch component would need a third
    rule and is best deferred to a fresh ``D-`` entry that names
    a concrete trigger. The regex contract fails ``"v1.0.0"``
    loudly so accidental drift can't sneak in.
  - **Per-kind optional version field** (kind opts in) — rejected,
    violates MECE. Every kind needs the field once Phase 3 can
    publish anything; lifting it to ``BaseNodeFields`` keeps it
    universal and lets the 15-kind parametric schema-parity test
    cover it automatically.
  - **Nullable version with default ``None``** — rejected. The
    publish model treats every node as carrying a version from
    creation; nullable would force every consumer to handle the
    ``None`` case and re-introduce default-fill logic.
  - **Defer until Phase 3 (UI) lands** — rejected. Phase 3 will
    need to bump the field, which means the read-side must already
    populate it on pre-Phase-2 canvases. Splitting the data layer
    from the UI layer keeps each commit atomic and the read
    contract stable across the rest of the v0.17.x sequence.

- **Approval:** **Accepted** by user, 2026-05-16. Filed as the
  active queue item in ``mashbill/docs/NEXT_SESSION.md`` with the
  exact scope ("Server: add ``version: str = "v1.0"`` to
  BaseNodeFields with ``^v\d+\.\d+$`` validator. Defaults to
  ``"v1.0"`` for backward compatibility (existing nodes auto-fill
  on read). Viewer: mirror in
  ``viewer/src/domain/BaseFields.ts``…. No UI surface yet.").

- **Spec impact:** None directly user-visible. The data layer now
  carries a new key; ``SPEC.md`` will gain its first ``version``
  mention in Phase 3 (Publish button text + per-node MD export
  format). Until then, the wire format is the spec, captured by
  ``test_schema_parity.py``.

- **Files in this commit:**
  - ``mashbill/models.py`` — ``version`` field + ``_version_is_valid``
    validator on ``BaseNodeFields``; ``import re`` added.
  - ``tests/test_schema_parity.py`` — ``_EXPECTED_BASE_FIELDS``
    grows from 14 to 15 (``"version"`` appended).
  - ``tests/test_node_models.py`` — 4 new tests (default, valid
    regex matches, invalid rejections, per-kind round-trip).
  - ``viewer/src/domain/BaseFields.ts`` — both interfaces +
    ``asVersionString`` helper.
  - ``viewer/src/domain/{Actor,ActorRef,Category,Content,CoreValue,
    Identity,IdentityRef,Metric,Mission,MissionRef,Project,Rule,
    Service,Step,ValueRef}.ts`` — 15 files × 2 line additions each
    (class body + ``toJson``).
  - ``viewer/tests/domain/base-fields.test.ts`` — 4 new tests
    (default fill, valid versions, invalid rejections, non-string
    rejection).
  - ``mashbill/CHANGELOG.md`` — v0.17.2 section.
  - ``mashbill/docs/DECISIONS.md`` — this entry.
  - ``mashbill/docs/NEXT_SESSION.md`` — Phase 2 trigger archived,
    Phase 3 trigger surfaced.
  - ``mashbill/.claude-plugin/plugin.json`` — 0.17.1 → 0.17.2.

- **Test counts:**
  - Server: 318 → 322 (+4). Viewer: 505 → 514 (+9).
  - All green; mypy + ruff + tsc all clean.

- **Cross-refs:**
  - [D-2026-05-13-J](./DECISIONS.md) — initial 4-point JSON SSOT
    vision (now superseded by O).
  - [D-2026-05-13-O](./DECISIONS.md) — 7-principle JSON SSOT
    vision (the policy that names this phase).
  - [D-2026-05-16-A](./DECISIONS.md) — Phase 1 ship (v0.17.0).
  - [D-2026-05-16-B](./DECISIONS.md) — v0.17.1 anchor-click polish.

---

### D-2026-05-16-D — AI-context architecture: "tree-in-forest" 3-layer framing

- **What:** Adopt a 3-layer mental model for the "AI implements a
  feature's spec faithfully but misses the surrounding forest
  (Identity / tone / sibling services)" problem, and queue it as
  [`ROADMAP.md` §D](./ROADMAP.md).

  - **Layer 1 — Data structural connection.** Free. Novel's typed
    user-authored graph is already a GraphRAG-quality substrate;
    the usual GraphRAG entity-extraction step is zero-cost because
    the user drew the graph.
  - **Layer 2 — Input side / call enforcement.** Small.
    Addressable with a `context_envelope` MCP tool (ancestor chain
    + Symbol resolves + N-hop neighbours), a Novel skill rule
    forcing the agent to call it before starting node-scoped work,
    and the existing interview pattern
    ([`PRODUCT_SPEC.md` §9](../../../plot/docs/PRODUCT_SPEC.md)) surfacing the
    envelope result as the interview's opening context.
  - **Layer 3 — Output side / verification loop.** Large. Cannot
    be closed by the agent alone — the agent reading the forest
    does not guarantee the forest shaping its output. Today this is
    human PR review at the merge gate
    ([`PRODUCT_SPEC.md` §11](../../../plot/docs/PRODUCT_SPEC.md)); automation
    arrives later with the Distill (crystallize transcripts → implicit
    Identity) and Evonest (LLM-as-judge consistency check) ports.

- **Why:** earlier turns in this ideation conflated retrieval (data
  exposure) with behaviour change (the AI actually internalising
  the forest). The 3-layer split makes it explicit that Novel is
  **not** blocked on retrieval infrastructure — Layer 1 is
  essentially free — and that the real cost lives in Layers 2 + 3,
  of which only Layer 2 is small enough to ship before Distill /
  Evonest are ported. The split also names where each future
  monorepo-package port (Distill, Evonest) becomes load-bearing:
  Distill → Layer 3 crystallization input; Evonest → Layer 3
  verification engine.

- **Concrete failure case — i18n / global-service:** Novel's i18n
  surface is the *most fully built-out* forest-anchoring mechanism
  in the project today — `useTranslation()` / `t()` plumbing,
  `viewer/src/i18n/locales/{en,ko}.json`, AND the static guard
  `viewer/tests/i18n-keys-parity.test.tsx` are all live (Layer 1
  fully built, Layer 3 partial — the guard catches en/ko key-count
  parity, NOT raw strings bypassing `t()`). Despite this, AI
  sessions repeatedly hardcode user-facing strings into `.tsx`
  files (per the global-service direction
  [D-2026-05-11-D](./DECISIONS.md) and the CLAUDE.md anti-pattern
  table "Hardcoding user-facing UI text in a viewer component").
  This is the sharpest available evidence that **Layer 2 (call
  enforcement at code-write time) is the actual bottleneck**:
  passive mechanisms — anti-pattern docs, memory notes, post-write
  static guards — do not stop the regression because none of them
  *announce themselves* to the AI at the moment of writing the
  offending string. The case justifies Phase 1 of §D shipping
  independently of Phases 2 / 3.

- **Alternatives:**
  - **Import a full GraphRAG library** (rejected — Novel's typed
    user-authored graph makes most GraphRAG machinery redundant;
    entity extraction is zero-cost when the user already authored
    the relationships).
  - **Bundle the three layers as one feature** (rejected —
    conflates very different difficulty levels and delays the
    deliverable Phase 1 deliverable).
  - **Defer entirely until Distill / Evonest are ported** (rejected
    — Phase 1 is small enough to ship and measure independently;
    the measurement informs how much of the problem remains for
    Phases 2 / 3).

- **Approval:** Accepted by user, 2026-05-16.

- **Spec impact:** none directly. Queues a new ROADMAP item
  ([`ROADMAP.md` §D](./ROADMAP.md)) below A / B / C. No
  [`SPEC.md`](./SPEC.md) line yet because Phase 1 implementation
  has not been scoped — when the `context_envelope` MCP tool lands,
  a fresh `D-` entry will pin its observable behaviour (envelope
  contents, when the agent must call it, what "skipping the call"
  looks like).

- **Cross-refs:**
  - [`ROADMAP.md` §D](./ROADMAP.md) — queued item that this
    framing parents.
  - [`PRODUCT_SPEC.md` §9](../../../plot/docs/PRODUCT_SPEC.md) — interview pattern
    that Layer 2 strengthens.
  - [`PRODUCT_SPEC.md` §11](../../../plot/docs/PRODUCT_SPEC.md) — PR-style merge
    gate that Layer 3 inhabits.
  - [`VISION.md`](../../../docs/VISION.md) — the essence the forest-anchoring
    serves (Retention + Execution phases).

---

### D-2026-05-16-E — Phase 3 per-node publish (button + MD export + MAJOR bump)

- **What:** Ship the visible surface of the JSON SSOT publish
  model: a **📤 publish button** in the Inspector header that on
  confirm bumps the node's ``version`` MAJOR (``v1.0 → v2.0``),
  writes a per-node MD file at
  ``<canvas_dir>/published/{kind}-{slug}-{version}.md``, and
  records a git commit with ``Publish-*:`` trailers. A **version
  badge** in the header's left cluster shows the node's current
  version. A **uniform MD template** (YAML frontmatter with 7 keys
  + one H2 section per declared typed field) renders identically
  across all 15 kinds. **Eligibility**: project anchor + ``is_root``
  + 4 ``*_ref`` alias kinds rejected (button hidden + server 409);
  remaining 10 kinds eligible.

- **Why:** Phase 2 (v0.17.2) shipped the ``BaseNodeFields.version``
  field on the per-node publish assumption fixed by
  [D-2026-05-13-O](./DECISIONS.md) #4 (which supersedes
  D-2026-05-13-J #4 with the user-quoted *"각 노드의 MD
  분리해야죠"*). Phase 3 is the explicit user surface that bumps
  that field. Subject of the git commit is for humans; the 5
  trailers (``Publish-Node-Id`` / ``Publish-Kind`` /
  ``Publish-Canvas`` / ``Publish-Version-From`` /
  ``Publish-Version-To``) are the **Phase 4 contract**.

- **Alternatives considered:**
  - **Canvas-unit publish** (D-2026-05-13-J #4) — rejected,
    superseded.
  - **Idempotent / no-op-on-unchanged publish** — rejected;
    collapses audit history; the npm/cargo mental model misleads
    because Novel publishes are *attestation* events, not registry
    uploads. Confirm dialog text names this explicitly so users
    don't carry the wrong model in.
  - **Per-publish git tag in addition to commit** — rejected; tag
    namespace would balloon; ``git log --grep "^Publish-Node-Id:"``
    + ``git interpret-trailers`` give the same queryability.
  - **Separate ``foundation/_publish_log.jsonl`` audit file** —
    rejected; would duplicate what git already records (SSOT
    violation).
  - **Bundle Phase 4 MINOR propagation into Phase 3** — rejected;
    cross-canvas ancestor walk has its own design questions; small
    ship over big bang.
  - **Auto-publish on save** — rejected; PHILOSOPHY *"user controls
    every line"*; publish is an explicit gesture.
  - **Context menu / keyboard shortcut for publish** — rejected;
    header chrome is the one canonical surface for single-node
    actions (delete / width / close already live there);
    discoverability beats hidden affordances.
  - **Always-idempotent file overwrite** (single MD per node) —
    rejected; kills the per-version file lineage that Phase 5's
    folder hierarchy + Phase 6's legacy purge depend on.
  - **Unpublish button in Phase 3** — rejected for this phase;
    manual recovery via ``git revert HEAD`` + MD cleanup
    documented in ``docs/PUBLISH.md``; automated Unpublish queued
    as v0.18.x follow-up in ``NEXT_SESSION.md``.

- **Approval:** **Accepted** by user, 2026-05-16. Plan reviewed via
  mashbill-design-red-team (8-attack pass); five Major findings
  (publish eligibility table, PSPEC §6 cross-cutting split,
  uniform MD template, undo recovery procedure, commit trailer
  contract) + two Minor (``published/`` semantics, always-bump
  framing) absorbed into the plan before code.

- **Spec impact:**
  - New ``mashbill/docs/SPEC.md`` section ``## Publish (v0.18.0)``.
  - New ``mashbill/docs/PUBLISH.md`` short doc — MD format reference +
    ``published/`` semantics + manual recovery procedure.
  - ``mashbill/docs/NEXT_SESSION.md`` updated to archive Phase 3 and
    surface Phase 4 trigger + v0.18.x Unpublish button follow-up.
  - PSPEC §6 git-event-table clarifier shipped separately in
    v0.17.4 (per design-red-team A5-1 split).

- **LOC ceiling raises (per Gate 2):**
  - ``viewer/src/canvases/SketchCanvas.tsx``: 420 → 440 (+20 for
    publish-prop threading; no-growth henceforth).
  - ``viewer/src/canvases/inspectors/BaseInspector.tsx``: 220 → 270
    (publish button + version badge + confirm-dialog handler;
    no-growth henceforth).
  - Novel CLAUDE.md Gate 2 LOC table updated to match.

- **Files in this commit:** see [`mashbill/CHANGELOG.md`](../CHANGELOG.md)
  v0.18.0 section — 25-ish files (5 server modules + 5 viewer +
  4 docs + i18n + tests).

- **Test counts:**
  - Server: 359 → 396 (+37; mypy + ruff clean).
  - Viewer: 514 → 522 (+8 new publishEligibility + auto-flow
    through existing parametric tests; tsc clean).
  - Backward-compat smoke: real-project ``plot-test-v013/banas-v013``
    mission node v1.0 → v2.0 publish flow verified end-to-end
    (server-side, ahead of viewer).

- **Cross-refs:**
  - [D-2026-05-13-J](./DECISIONS.md) — superseded canvas-unit
    publish (do not re-litigate).
  - [D-2026-05-13-O](./DECISIONS.md) — 7 principles; #4 per-node
    MD, #5 per-node version, #7 folder hierarchy (Phase 5).
  - [D-2026-05-16-A](./DECISIONS.md) — Phase 1 ship (v0.17.0).
  - [D-2026-05-16-C](./DECISIONS.md) — Phase 2 ship (v0.17.2).
  - [PSPEC §6](../../../plot/docs/PRODUCT_SPEC.md) — v0.17.4 clarifier that aligned
    the git-event spec with v0.17/v0.18 reality.

---

### D-2026-05-16-F — typed text MD 통일 + body 7 kinds + per-kind MD format

- **What:** Extend the v0.17.0 Phase 1 *"JSON value = MD-formatted
  string + monospace MD textarea + body field"* pattern from
  Foundation 3 kinds to the 7 other publish-eligible kinds
  (actor / service / category / metric / step / rule / content).
  Also lift `actor_ref`'s `gives` / `receives` textarea to
  monospace MD (ref is still publish-ineligible + no `body`).
  Document 15-kind per-kind MD section list in
  ``docs/PUBLISH.md``.

- **Why:** D-2026-05-13-O #2 (*"JSON value = MD-formatted string"*)
  + user's same-session re-confirmation: *"노드 클릭하면 상세 —
  설명·할것·하지말것·노트 — 모두 MD 문법, 노트는 extra. 발행하면
  MD."* Phase 1 cover 1/5; Phase 3 (v0.18.0) shipped publish
  before the input parity, so 7/10 publish-eligible kinds had
  plain-text input but emitted MD on publish — inconsistent.
  v0.18.2 closes the gap.

  Separately, the user defined ref's role: *"레퍼런스는 복사본
  혹은 링크. 미션/사용자 레퍼런스를 서비스 그릴 때 연결되면 매우
  훌륭. 누구를 위한 / 누가 활동하는 / 누구와 누가 관계 맺는
  서비스인가 표현."* — ref is a **relation tool** on services /
  service-detail, not an own-SSOT node. No `body` for ref; but
  `actor_ref.gives` / `actor_ref.receives` are valid *service-
  context-specific relation descriptions* and their input is
  monospace MD for consistency.

- **Alternatives considered:**
  - **`body` on ref 4** — rejected; ref is a relation, not a free
    note channel.
  - **Plain text on ref typed text** — rejected; inconsistent
    with "all typed text MD".
  - **Per-kind override** — rejected; YAGNI, intent is uniform.
  - **Bundle with Phase 4** — rejected; small ships.

- **Approval:** **Accepted** by user, 2026-05-16 (same-session
  confirmation chain).

- **Spec impact:**
  - `mashbill/docs/SPEC.md` §Publish — new "Typed text + body fields
    (v0.18.2+)" subsection.
  - `mashbill/docs/PUBLISH.md` — per-kind H2 reference (15 kinds) +
    ref-as-relation-tool note.

- **Files in this commit:** see ``mashbill/CHANGELOG.md`` v0.18.2 —
  server models.py (1) + viewer entity (7) + viewer inspectors
  (7 + 2 shared + actor_ref) + docs (5).

- **Test counts:** server 359/359, viewer 522/522 — both unchanged
  count (schema-parity + entity-roundtrip + inspectors smoke
  auto-flowed the body field through). mypy + ruff + tsc clean.

- **Cross-refs:**
  - [D-2026-05-13-O](./DECISIONS.md) #2 — the gap this closes.
  - [D-2026-05-16-A](./DECISIONS.md) — Phase 1 (v0.17.0) — the
    pattern v0.18.2 generalizes.
  - [D-2026-05-16-E](./DECISIONS.md) — Phase 3 (v0.18.0) — the
    publish flow the body field gets emitted through.

- **Follow-up filed in NEXT_SESSION.md:**
  - cross-kind ref typed-text symmetry — *왜 actor_ref 만 `gives`/
    `receives` 가 있고 mission_ref / value_ref / identity_ref 는
    없는가?* — 가치 있을 때 별도 phase 재검토.

---

### D-2026-05-17-A — Reload fit-view race fix (DOM measurement)

- **What:** Move ``fitView`` from RF's ``onInit`` callback into a
  ``useNodesInitialized`` effect inside ``SketchCanvas``. ``onInit``
  now only stores the instance ref. A ``didInitialFitRef`` gate
  ensures fit fires once per mount; ``activeCanvasKey`` remount in
  App.tsx re-triggers on tab change.

- **Why:** User reported on Foundation reload (2026-05-17):
  *"파운데이션에서 새로고침 하면 노드들 싹다 사라집니다."* Disk
  inventory confirmed all 4 nodes + 4 edges intact. Real failure
  mode: viewport pinned at (0, 0); user-placed nodes outside the
  default 1080×720 viewport rendered off-screen until manual
  fit-view click. Root cause: RF's ``onInit`` fires *before* node
  DOM measurement, so ``inst.fitView`` computed bounds from
  un-measured nodes and snapped to (0, 0).
  ``useNodesInitialized`` returns ``true`` only after every node
  carries real measured dimensions.

- **Alternatives considered:**
  - **setTimeout(0) inside onInit** — works but magic delay;
    ``useNodesInitialized`` is the explicit RF API.
  - **``fitView`` prop on ``<ReactFlow>``** — re-introduces the
    v0.16.18 (D-2026-05-12-T) regression where every render's
    fresh ``nodes`` array reference triggers re-fit, resetting
    user's manual zoom/pan.
  - **Drop fit entirely, manual only** — rejected; reproduces
    the bug being fixed.

- **Approval:** Accepted by user, 2026-05-17. Confirmed via
  chrome-devtools MCP reload (all 4 Foundation nodes + 4 edges
  visible without manual fit; console clean).

- **Spec impact:** None new. v0.16.18 (D-2026-05-12-T) "fit once
  on mount, not every render" intent preserved; only the *trigger*
  for that single fit moves from ``onInit`` to
  ``useNodesInitialized``.

- **Files in this commit:**
  - ``viewer/src/canvases/SketchCanvas.tsx`` — +~14 LOC.
  - ``mashbill/.claude-plugin/plugin.json`` — 0.18.2 → 0.18.3.
  - ``mashbill/CHANGELOG.md`` — v0.18.3 section.
  - ``mashbill/docs/DECISIONS.md`` — this entry.

- **Test counts:** viewer 522/522 green (LOC budget guard caught
  +2 over-440 first attempt → trimmed to fit). tsc clean.

- **Cross-refs:**
  - [D-2026-05-12-T](./DECISIONS.md) — v0.16.18 "fit once on
    mount" gating; intent preserved through different trigger.
  - [D-2026-05-16-E](./DECISIONS.md) — v0.18.0 LOC ceiling 440;
    this entry's +14 LOC fits within budget.

---

### D-2026-05-17-B — MD-aware Inspector editor (CodeMirror 6 stage 1)

- **What:** Replace 19 plain monospace ``<textarea>`` blocks across
  the Inspector with a single shared ``MdTextarea`` component backed
  by **CodeMirror 6** + ``@codemirror/lang-markdown``. Headings,
  lists, bold, italic, code, links, and blockquotes render with MD
  syntax highlight as the user edits. Raw MD remains the SSOT.

  Per-inspector ring color (sky / rose / violet / emerald / slate /
  lime / stone) on typed-text fields is **dropped** — single
  canonical slate→indigo focus theme. Kind colors stay on header
  chrome (color badge + KIND tag).

  Stage 1 of a 3-stage Obsidian Live Preview track:
  - **v0.19.0 (this)** — CodeMirror foundation + syntax highlight.
  - **v0.20.0** — mermaid SVG decoration widget (lazy import).
  - **v0.21.0** — heading font-size / list bullet / image embed
    decorations.

- **Why:** D-2026-05-13-O #2 (*"JSON value = MD-formatted
  string"*) + user's 2026-05-17 ask (*"노드에 있는 각 항목들 md
  잖아요. md 편집기 붙일 수 있나요?"* + *"머메이드 차트 지원해뒀으면"*
  + *"옵시디언 처럼"*). The Inspector was the natural surface — typed
  text in JSON is already MD-formatted string; only the *editor
  paint* was monospace-plain. CodeMirror + custom decoration is
  Obsidian Live Preview's actual implementation pattern; ProseMirror-
  based WYSIWYG (Milkdown / Tiptap / Lexical) round-trip risks lossy
  conversion for unusual MD syntax (callouts, custom blocks, future
  mermaid). Raw MD must remain ground truth.

- **Alternatives considered:**
  - **Milkdown / Tiptap / Lexical (WYSIWYG)** — rejected; MD ↔
    internal-state round-trip is lossy for less-common syntax.
  - **CodeMirror via ``@uiw/react-codemirror`` wrapper** —
    rejected; extra dep + version-mismatch risk against the future
    v0.20 mermaid decoration plugin. Direct CodeMirror API used.
  - **Preview pane (split / toggle)** — rejected for stage 1;
    user explicitly wanted "옵시디언 처럼" (inline render, not
    separate panes). Reserved for never-shipped if Live Preview
    fully replaces it.
  - **Per-inspector keep ring colors** — rejected for KISS; 7
    different focus colors across the Inspector tree was visual
    noise.

- **Approval:** **Accepted** by user, 2026-05-17. "1로 합시다"
  (the recommended staged option). Plan-mode walked through 4
  WYSIWYG / Live-Preview options + 3-stage ship plan.

- **Spec impact:**
  - ``mashbill/docs/SPEC.md`` §Publish "Typed text + body fields"
    subsection — label bumped to (v0.19.0+); mentions CodeMirror
    MD-aware editor.

- **Bundle size:** index 1,257 KB → 1,759 KB raw (+502 KB); gzip
  340 KB → 515 KB (**+175 KB gzip**). Within the planned
  150-180 KB gzip budget. Mermaid lazy chunks (cytoscape / katex /
  wardley) unchanged. The +175 KB gzip is approximately:
  ~110 KB CodeMirror runtime (state + view + commands + history)
  + ~65 KB markdown grammar (@codemirror/lang-markdown +
  @lezer/markdown).

- **Files in this commit:** see ``mashbill/CHANGELOG.md`` v0.19.0 —
  1 new shared component + 11 swap sites + 5 docs +
  2 dep additions (codemirror + lang-markdown).

- **Test counts:** viewer **524/524** green (522 + 2 implied
  by mirror textarea); server 359/359 unchanged. tsc + mypy +
  ruff clean. Hidden ``<textarea>`` mirror inside ``MdTextarea``
  preserves RTL ``getByDisplayValue`` queries — the original
  smoke-test pattern was an interesting wedge (CodeMirror renders
  ``<div contenteditable>``, not a form field), resolved by an
  ``sr-only`` read-only mirror that indexes for RTL without
  affecting users.

- **Cross-refs:**
  - [D-2026-05-13-O](./DECISIONS.md) #2 — *"JSON value =
    MD-formatted string"*; the MD-aware editor is the natural
    consequence.
  - [D-2026-05-16-F](./DECISIONS.md) — v0.18.2 brought monospace
    textarea + body field to 7 publish-eligible kinds; v0.19.0
    upgrades that monospace surface to CodeMirror.
  - [D-2026-05-17-A](./DECISIONS.md) — v0.18.3 fit-view race
    fix; unrelated, just adjacent in the timeline.

- **Follow-ups filed in ``NEXT_SESSION.md``:**
  - **v0.20.0** — mermaid SVG decoration widget. ``MDPreview.tsx``
    already imports mermaid + has working render path; can be
    extracted as a CodeMirror ``ViewPlugin`` decoration over
    ```` ```mermaid ```` code blocks.
  - **v0.21.0** — heading font-size + list bullet + image embed
    decorations.
  - **MCP-driven node creation via AI conversation** — user
    explicit deferral (2026-05-17 — *"MCP 로 대화하면서 만드는건
    나중으로 미루고"*). Reserved as a phase that will combine with
    tree-in-forest D-2026-05-16-D Layer 2 (``context_envelope``
    MCP tool).

---

### D-2026-05-17-C — Phase 4 MINOR propagation up ancestor chain (v0.20.0)

- **What:** When a node is published, walk its ``parent_id`` ancestor
  chain and MINOR-bump every ancestor's ``version`` field. Single git
  commit with the existing 5 base ``Publish-*:`` trailers plus one
  ``Publish-Propagated-Ancestor: <id> <from>→<to>`` trailer per
  bumped ancestor. Five sub-decisions, all approved together in
  plan-mode:

  1. **Scope of "ancestor" = ``parent_id`` chain only.** Refs
     (``actor_ref``, ``mission_ref``, ``value_ref``, ``identity_ref``,
     and ``CanvasDoc.service_ref``) are **not** walked. When the same
     id has file-presence in two canvases (ServiceDetail root service
     ↔ Services master service), they count as one logical node and
     the walk crosses via id-matching only. User direction
     (2026-05-17): *"이건 노드로 제한합니다. refs 는 링크만
     걸리는거잖아요. 그래서 페어런트와 자식 관계만"*.
  2. **No new ancestor MD files.** MINOR propagation only bumps
     ancestor JSON ``version``. The existing per-version MD files
     stay as "MAJOR publish snapshots". JSON ``version`` legitimately
     drifts past the latest on-disk MD version — the gap means
     "descendants moved since the last own-content publish".
  3. **Single commit with extra trailers**, not separate commits.
     ``git interpret-trailers`` supports duplicate keys; multi-line
     ``Publish-Propagated-Ancestor`` is the canonical shape.
  4. **Revert is automatic.** ``git revert HEAD`` undoes the publish
     commit, including all ancestor MINOR bumps and the new MD file,
     in one shot. No special handling.
  5. **No new Inspector UI** for v0.20.0. The existing version badge
     already shows ``vMAJOR.MINOR``; users see MINOR moving silently.
     A future "this node was last propagated by descendant X" badge
     can ship in v0.21+ if usage warrants.

- **Why:** D-2026-05-13-O #5 defined ``MINOR + 1 when any descendant
  publishes (chain-propagated to all ancestors)`` but Phase 3
  (v0.18.0, D-2026-05-16-E) only delivered the MAJOR half. Until
  Phase 4 lands, the ``MINOR`` axis is dead state — the AI context
  envelope ([D-2026-05-16-D](./DECISIONS.md)) cannot see "this branch
  moved recently because something below it shipped". Phase 4 makes
  the tree-in-forest mental model observable in real data.

- **Alternatives considered + rejected:**
  - *Full cross-canvas walk via refs* (publishing a step bumps
    every Actor / Mission / Identity it references). User rejected:
    refs are *links*, not parent–child; bumping the Actor when a
    service references it would create wide noisy ripples whose
    semantics ("Actor changed because something pointed at it")
    don't match how users think.
  - *Same-canvas only* (no mirror crossing). Would mean a step in
    service_detail never bumps the master service in Services. The
    Services badge wouldn't reflect detail-level activity at all,
    defeating the point of MINOR.
  - *Re-render ancestor MD files at each MINOR* (option 2(b)). The
    ancestor's content didn't change — re-rendering would just
    create a confusing pile of near-duplicate MDs with different
    version suffixes. Reserved for if the disk-MD/JSON drift
    becomes user-visible pain.
  - *Separate commits per ancestor* (option 3(a)). A leaf publish
    on a 5-level deep tree would produce 5 commits, polluting the
    log. Atomicity also degrades: partial revert leaves
    inconsistent state.
  - *Add a "Propagation history" Inspector tab now*. YAGNI — git log
    already records every propagation; UI without a felt need is
    speculative scope creep.

- **Approval:** **Accepted** by user, 2026-05-17 — plan-mode
  walkthrough with the five sub-decisions presented; user picked
  scope decision (1) explicitly via AskUserQuestion, then approved
  the bundled plan via ExitPlanMode.

- **Spec impact:**
  - [`SPEC.md` §Publish — MINOR propagation](./SPEC.md#publish—minor-propagation)
    — new subsection codifying the 5 answers.
  - [`PUBLISH.md`](./PUBLISH.md) — trailer schema extended;
    ``Publish-Propagated-Ancestor: <id> <from>→<to>`` documented.
  - [`ROADMAP.md`](./ROADMAP.md) — Phase 4 ship version corrected
    from outdated "v0.18.0" entry to "v0.20.0" (Phase 3 already
    consumed v0.18.0).

- **Cross-refs:**
  - [D-2026-05-13-O](./DECISIONS.md) #5 + #7 — defined MINOR
    semantics + reserved Phase 4 for propagation.
  - [D-2026-05-16-E](./DECISIONS.md) — Phase 3 ship (v0.18.0)
    that pre-installed the 5-trailer commit shape Phase 4 extends.
  - [D-2026-05-16-D](./DECISIONS.md) — tree-in-forest framing
    that motivates the silent propagation behaviour.

- **Follow-ups filed in ``NEXT_SESSION.md``:**
  - **Mermaid SVG inline decoration** moves from v0.20.0 →
    **v0.21.0** (Phase 4 took the v0.20.0 slot).
  - **Phase 5** — folder hierarchy + container-publish semantics
    → v0.22.0 (was v0.21.0).
  - **Phase 6** — legacy purge + final docs sync → v0.22.1.

---

### D-2026-05-17-D — Mermaid SVG inline decoration (v0.21.0, Live Preview Stage 2)

- **What:** Render ``` ```mermaid``` ``` fenced blocks inside the
  MdTextarea as inline SVG widgets *below* the closing fence. The
  raw markdown source remains visible and editable above; the SVG
  re-renders 200 ms after the last keystroke. Mermaid is loaded
  lazily — a project with no mermaid blocks pays zero mermaid
  bytes. Seven sub-decisions, all locked in plan-mode:

  1. **Lazy import trigger:** singleton ``loadMermaid()`` helper.
     First access (from either MDPreview's Preview tab or the
     MdTextarea decoration) triggers ``import("mermaid")`` once and
     caches the promise.
  2. **Invalid mermaid syntax:** reuse MDPreview's existing
     pattern — ``mermaid.render`` returns a rejected promise, the
     widget swaps to a red-border ``data-mermaid="error"`` block
     containing ``mermaid error: <msg>``. Source text never
     mutated.
  3. **Large diagrams + multi-block:** no cap; ``max-height:
     480px; overflow: auto`` on the widget container. Each fenced
     block gets its own widget. YAGNI on size caps.
  4. **Decoration position:** block widget placed *after* the
     closing ` ``` ` of the fence (``Decoration.widget({ side: 1,
     block: true })``). The Obsidian Live Preview pattern *hides*
     source unless the cursor is inside the block; Novel keeps the
     source visible because SSOT (D-2026-05-13-O #2) requires the
     authoritative markdown to remain editable + observable at all
     times. A source-toggle is deferred to a future v0.21.x if the
     always-visible source becomes pain.
  5. **Theme:** ``theme: "default"`` (mermaid's bundled theme).
     Matches the existing ``MDPreview.tsx`` config so the two
     paths render identically. Novel's slate/indigo chrome lives
     outside the SVG (border + container).
  6. **Debounce:** 200 ms on doc changes via a ``ViewPlugin`` that
     debounces dispatch of the ``setMermaidDecorations``
     ``StateEffect``. Fast enough that the SVG "feels live"
     (mermaid parse adds 50-150ms on top); slow enough that typing
     mid-fence doesn't fire ``mermaid.render`` per keystroke. Bump
     to 300ms in a v0.21.x patch if complaints arrive.
  7. **SSOT invariant test:** vitest case mounts ``<MdTextarea
     value={MERMAID_SOURCE} onChange={fn}>``, waits for the
     mocked ``mermaid.render`` to be invoked, then asserts
     ``onChange`` was never called and the hidden mirror textarea
     still holds the original value. Pins the contract that the
     decoration cannot mutate source.

- **Architectural note (CodeMirror 6 block decoration rule):**
  CodeMirror 6 disallows block-level decorations sourced directly
  from a ``ViewPlugin``'s ``decorations`` facet — they must come
  from a ``StateField`` so they participate in the layout pass.
  v0.21.0 therefore splits the plugin into:

  - ``mermaidDecoField`` — ``StateField<DecorationSet>`` holding
    the current widget set; updated only via the
    ``setMermaidDecorations`` ``StateEffect`` (otherwise just
    ``map``s through doc changes so widgets stay anchored).
  - ``mermaidDebouncer`` — ``ViewPlugin`` that watches doc
    changes, debounces 200 ms, walks the syntax tree, and
    dispatches a fresh decoration set via the effect.

  Both ship together as the composite ``mdMermaidPlugin: Extension``
  spread into the editor's extensions array.

- **Why:** v0.19.0 (D-2026-05-17-B) shipped the CodeMirror 6
  MdTextarea foundation as "stage 1 of a 3-stage Obsidian Live
  Preview track". Stage 2 brings the most-requested decoration —
  mermaid — while keeping the bundle lean (no eager mermaid load).
  Bundle delta: index chunk ``1,759 KB raw / 515 KB gzip`` (v0.19.0)
  → ``1,185 KB raw / 381 KB gzip`` (v0.21.0). The 574 KB raw / 134
  KB gzip difference is mermaid moving to its own lazy chunk.

- **Alternatives considered + rejected:**
  - *Static ``import mermaid``* — Novel has no project-wide
    requirement that mermaid be available; users without mermaid
    blocks shouldn't pay for the library. Rejected.
  - *Obsidian's replace-on-blur pattern* — would hide the source
    when the cursor leaves the fence. Novel's SSOT rule + lack of
    a source-mode toggle make the always-visible source the safer
    default. Rejected for v0.21.0; reconsiderable later.
  - *Per-keystroke render (no debounce)* — would fire
    ``mermaid.render`` 10+ times per second while the user types.
    Mermaid parse is 50-150ms; the resulting UI jank is
    unacceptable. Rejected.
  - *i18n the ``mermaid error:`` prefix.* The existing MDPreview
    ``MermaidBlock`` has had the same hardcoded prefix since
    v0.16.x. The string is technical debug output that doesn't
    surface in normal user flow (only when a user types an
    invalid diagram). Adding i18n for parity would force the
    widget (vanilla DOM, no React context) to call ``i18next.t``
    imperatively — overhead disproportionate to value. Skipped.
    If a global service review flags the inconsistency, the fix
    is a 4-line patch in v0.21.x.

- **Approval:** **Accepted** by user, 2026-05-17 — plan-mode
  walkthrough with the seven sub-decisions presented (one
  AskUserQuestion-free path; YAGNI / SSOT / KISS make every Q
  self-resolve). User approved the bundled plan via ExitPlanMode.

- **Spec impact:**
  - [`SPEC.md` §Typed text + body fields](./SPEC.md#typed-text-and-body-fields-v0190)
    — extended with a paragraph noting v0.21.0 brings mermaid
    Live Preview decoration on top of the MdTextarea foundation.
  - No new top-level SPEC section — the decoration is a visual
    enhancement of the existing MdTextarea; SSOT contract
    unchanged.

- **Cross-refs:**
  - [D-2026-05-17-B](./DECISIONS.md) — v0.19.0 stage 1
    (CodeMirror 6 foundation).
  - [D-2026-05-13-O](./DECISIONS.md) #2 — *"JSON value =
    MD-formatted string"*; the decoration must preserve this
    contract by never round-tripping through ``onChange``.

- **Follow-ups filed in ``NEXT_SESSION.md``:**
  - **Live Preview Stage 3** (heading font-size + list bullet +
    image embed decorations) — now sits at v0.22.0+ in the queue.
  - **Source-mode toggle** — Obsidian-style "edit vs preview" tab
    that hides the source when not editing; queued only if the
    always-visible-source pattern becomes UX pain.

---

### D-2026-05-17-E — MdTextarea focus redirect (v0.21.1)

**Context:** After v0.21.0 shipped, the user reported that clicking an
Inspector typed-text field (MdTextarea / CodeMirror 6) did not reliably
land keyboard focus in the editor. Browser focus event tracing revealed
the sequence:

1. Click on `.cm-content` → CM6 correctly focuses the editor.
2. Browser click processing (post-mousedown) could redirect focus to
   the adjacent sr-only mirror `<textarea>` (tabIndex -1) instead of
   keeping it on `.cm-content`.
3. The `cm-focused` class was absent; the user could not type.

Root-cause evidence: the sr-only textarea sits immediately after the
CM editor in DOM order. Browser and Playwright click semantics can
deliver the native "give focus to clicked/adjacent form element"
signal to the textarea rather than the contenteditable CM editor.

**Decision:** Add `onFocus={() => viewRef.current?.focus()}` to the
sr-only textarea. If it ever receives focus (for any reason), it
immediately delegates to the CM editor. The textarea retains its
existing role as an RTL `getByDisplayValue` test mirror; this patch
adds no new DOM elements and does not break the 529 vitest tests.

**Why `onFocus` on the textarea rather than `autoFocus` / removal:**
- `autoFocus` on the CM editor would scroll to it on Inspector mount,
  which is undesirable.
- Removing the textarea would break the vitest smoke-test suite
  (`getByDisplayValue`); refactoring all those queries is out of scope.
- `inert` attribute is supported but would also hide the textarea from
  `getByDisplayValue` in jsdom.
- The one-line redirect is self-contained and zero-risk to the SSOT
  contract (CM doc is still the canonical source; the textarea is
  read-only and is never written by this handler).

**Approval:** Self-approved bug fix; consistent with SPEC §Inspector
interaction contract (user can type in typed-text fields after
clicking them). No new SPEC line required.
**Post-ship user confirm 2026-05-17:** *"이제 되네"* — user verified
that clicking an Inspector typed-text field lands focus in the CM
editor in real Chrome.

**Spec impact:** None — the spec already implies that clicking a
typed-text field focuses it. This entry documents the implementation
fix, not a new behaviour.

**Cross-refs:**
- [D-2026-05-17-B](./DECISIONS.md) — v0.19.0 CodeMirror 6 foundation
  (MdTextarea introduced sr-only mirror).
- [D-2026-05-17-D](./DECISIONS.md) — v0.21.0 mermaid decoration
  (previous ship, same component).

---

### D-2026-05-17-F — Connection handle hit-area expansion (v0.21.2)

**Context:** User reported that connection handles "don't work
properly depending on position" — clicks 1–2 px off-center on a
handle were silently ignored. DOM probe confirmed the RF default
handle is a 10×10 px box (6 px content + 1 px border + transform).
That is below the comfortable click target for a pointer device
when the visible glyph is also the hit target.

**Decision:** Add a single CSS rule to `viewer/src/styles.css`:

```css
.react-flow__handle::after {
  content: "";
  position: absolute;
  top: -7px;
  left: -7px;
  right: -7px;
  bottom: -7px;
}
```

Result: visible handle stays exactly 10×10 (no visual change), but
the effective click target is ~30×30 (`::after` extends 7 px in
every direction; verified by `elementFromPoint` probe). Pseudo-
element clicks bubble to the parent `.react-flow__handle`, so
React Flow's `event.target.closest('.react-flow__handle')` lookup
identifies the handle correctly.

**Why pseudo-element rather than enlarging the visible dot:**
- Enlarging the visible dot would shift the canvas aesthetic and
  conflict with the existing minimal grey-on-white style.
- Pseudo-element click extension is the standard pattern used by
  Figma, Mermaid live editor, Excalidraw, etc., for icon-sized
  interactive targets that need a 24–44 px hit zone.
- Single CSS rule, no JS, no DOM additions, no React changes.

**Why hit extension is 7 px (not larger):**
- 30×30 keeps the rule well clear of adjacent handles on the same
  node (top vs. left of a 200×90 node = ~100 px center-to-center,
  no hit-area overlap).
- Larger (e.g., ±12 px → 34×34) gives diminishing returns and could
  start to overlap inter-handle gaps on very small nodes.

**Approval:** User-approved 2026-05-17: *"네 진행해주세요"* after
the proposal in the prior turn (Gate 1 satisfied per CLAUDE.md
anti-pattern *"Adding any cursor / handle / pan override on top
of RF defaults"* — the override stack is a regression engine
unless every entry has an audit trail).
**Post-ship user confirm 2026-05-17:** *"고쳐진거 같아요"* — user
verified handle drag works (indirect confirm: drag-to-connect
requires grabbing a handle reliably, and the connect verification
succeeded; see D-2026-05-17-G).

**Spec impact:** None — visible behaviour is unchanged. The spec
section on edges/handles does not need updating because the
contract ("user draws edges between handles") is preserved.

**Verification:**
- vitest 529/529 pass (the `styles-cursor-baseline.test.tsx` static
  guard only forbids `cursor:` declarations and `style.cursor =`
  JS assignments; this rule uses neither).
- DOM probe: hit area extends 15 px from visible center in each
  direction (= 30×30 total) while `handle.getBoundingClientRect()`
  remains 10×10.
- Screenshot diff: visual identical to v0.21.1.

**Cross-refs:**
- [D-2026-05-10-C](./DECISIONS.md) / [D-2026-05-10-F](./DECISIONS.md)
  — v0.13.3 → v0.13.5 stacked six rounds of cursor/handle CSS
  interventions ending in a full reset. This rule joins the
  freshly empty override stack with an explicit audit trail; future
  cursor/handle additions must follow the same pattern.
- [D-2026-05-11-A](./DECISIONS.md) — *"RF 기본으로 돌리라구요"*
  baseline that this override deliberately deviates from, with
  user sign-off recorded above.

---

### D-2026-05-17-G — Connection mode = Loose (v0.21.3)

**Context:** User reported that dragging from Core Value's top
handle to the Anchor's left handle did not form an edge. Code
audit revealed two facts:

1. `BaseNode.tsx` lines 154–157 declare the four handles with
   asymmetric types:
   - Top (id `"t"`) — `type="target"`
   - Left (id `"l"`) — `type="target"`
   - Right (id `"r"`) — `type="source"`
   - Bottom (id `"b"`) — `type="source"`
2. The `ReactFlow` component had no explicit `connectionMode`,
   which means the RF default `ConnectionMode.Strict` applied —
   only `source` → `target` drags form edges. `target` → `target`
   (and `source` → `source`) are silently rejected by RF before
   `onConnect` even fires.

**Spec evidence the strict default contradicted intent:**

[`SPEC.md §Anchor`](./SPEC.md#anchor):

> **Handles (4 sides):** Visible. User may draw edges **from / to**
> the anchor like any other node.

[`SPEC.md §Edges`](./SPEC.md#edges):

> All edges are user-drawn.

Both lines imply the user — not the framework — decides whether a
specific pair of handles connects. The strict mode silently
overruled that intent for ½ of all handle-pair combinations on
*every* node, not just the anchor.

**Decision:** Add `connectionMode={ConnectionMode.Loose}` to the
single `ReactFlow` component in `SketchCanvas.tsx`. `Loose` makes
RF accept connections between any two handles regardless of `type`;
`onConnect` then fires and `handleConnect` (which already does no
source/target validation) appends the edge to `doc.edges` as
before.

**Why a single canvas-wide flag rather than per-handle changes:**
- Per-handle: would mean adding 4 invisible "source" handles on top
  of the 4 visible "target" handles (or vice versa), doubling DOM,
  CSS-z-index gymnastics, and breaking the `id="t|l|r|b"` SSOT.
- ConnectionMode.Loose: one line, zero DOM additions, preserves
  the existing handle id convention (still useful for edge
  rendering / labelling), and matches the way Excalidraw, Mermaid
  live editor, and Obsidian Canvas behave (any-handle ↔
  any-handle).

**Side-effect surface (audited):**
- Existing edges in `canvas.json` are unchanged — the loaded
  `sourceHandle` / `targetHandle` strings still resolve.
- `useFlowHandlers.handleConnect` adds new edges with the dragged
  source/target as-is. No additional normalisation needed.
- Edge rendering uses `sourceHandle` / `targetHandle` for anchor
  positioning, unaffected by the connection-mode change.
- `viewer/tests/structural-guards.test.tsx` and the 525 other
  tests do not assert connection mode; all 529 pass.

**Approval:** Self-approved as SPEC-compliance bug fix (the prior
behaviour contradicted SPEC §Anchor / §Edges). User-reported
scenario *"코어밸류 탑핸들에서 앵커의 왼쪽핸들로 연결선을 만들려고
할 때 연결이 되지 않아요"* is the test case.
**Post-ship user confirm 2026-05-17:** *"고쳐진거 같아요"* — user
verified the Core Value top → Anchor left edge now draws in real
Chrome.

---

### D-2026-05-17-H — Publish gated by dirty (v0.22.0)

**Context:** After exercising the Publish flow shipped in v0.18.0 +
v0.20.0 + v0.21.3, the user noticed that pressing 📤 always bumped
``vMAJOR → v(MAJOR+1).0`` regardless of whether anything had actually
changed since the previous publish. SPEC §Publish §Idempotence
explicitly documented this as intentional ("release model — every
publish is a snapshot"), but the user disagreed:
*"퍼블리시 동작 보고 있는데 변경 내용이 없어도 버전이 올라가네요."*

**Decision (user-locked, AskUserQuestion):**

- **UX-level gate:** Inspector disables the publish button when the
  node is clean (user-picked from 4 options: 1️⃣ skip + alert,
  2️⃣ confirm-dialog warning, 3️⃣ keep current spec, 4️⃣ disable
  button — user picked #4).
- **"Dirty" = content change**, per user enumeration *"내용 변경
  아이덴티티 예시로 디스크립션 두 돈트 노트 그리고 연결선 정도"*:
  - typed-text fields + ``label`` + ``body``
  - **edges incident on the node** (add / remove / field edit on
    either endpoint marks both endpoints dirty)
- **NOT dirty** (silent canvas saves, no publish trigger):
  - Visual fields: ``x`` / ``y`` / ``width`` / ``height`` / ``color``
    / ``shape`` / ``icon`` / ``collapsed``
  - Structural: ``parent_id`` reparenting
  - **MINOR drift from a descendant publish** ([D-2026-05-17-C]) —
    the auto-bumped ``version`` number is bookkeeping, not new
    content; ancestor's typed-text + edges unchanged

User insight that drove this scope: *"저장이랑 버전이랑 상관이
없구나!!"* — autosave (canvas PUT) is unconditional; publish is the
separable explicit action.

**Architecture (7 locked answers):**

| # | Question | Answer |
|---|---|---|
| 1 | Baseline storage | New ``publish_baseline: dict \| None`` private field on ``BaseNodeFields``, aliased ``_publish_baseline`` in canvas.json (matches the leading-underscore server-managed pattern of ``_md_warnings``). |
| 2 | Baseline shape | ``{"node": {…content fields, visual + structural excluded}, "edges": [sorted incident edges with ephemeral edge ``id`` excluded]}``. |
| 3 | Where ``_dirty`` is computed | Server-side, at canvas GET time, on the response (same shape as ``_md_warnings``). Never persisted; recomputed per request. |
| 4 | Inspector behaviour | Button disabled when ``node._dirty === false``. Tooltip = ``t("inspector.publishDisabledHint", { version })``. Missing ``_dirty`` ⇒ treated as ``true`` (back-compat). |
| 5 | Migration for existing nodes | ``_publish_baseline`` defaults to ``None`` ⇒ dirty = true. First publish after v0.22.0 seeds the baseline. Zero schema migration; existing canvas.json files load unchanged. |
| 6 | Phase 4 MINOR drift handling | Ancestor MINOR bump deliberately does NOT touch ``_publish_baseline``. Ancestor stays clean. |
| 7 | Edge dirty propagation | Adding / removing / editing an edge ``(A → B)`` marks both ``A`` and ``B`` dirty. Edge ``id`` is excluded from the snapshot because it's server-generated. |

**Cross-server-client baseline preservation:** The Pydantic
``BaseNodeFields`` adds ``publish_baseline``; the TypeScript
``BaseFieldsJson`` mirrors it as ``publish_baseline?: unknown`` (the
schema-parity test enforces field-set equality). Per-kind entity
classes (Mission, Identity, Service, …) do NOT round-trip the
baseline through their ``toJson()`` — the field is optional in the
TS wire schema. To prevent client PUTs from clobbering the server-
managed baseline back to ``None``, ``write_canvas`` reads the
on-disk canvas first and carries any non-None baseline forward when
the incoming payload omits it.

**Spec impact:** ``SPEC.md §Publish §Idempotence`` rewritten as
``§Publish gated by dirty``. The "always-MAJOR-bump" clause under
the old §Idempotence is preserved verbatim for the case when the
user *does* press the still-enabled button.

**Verification:**
- 19 new pytest cases (``tests/test_dirty_tracking.py``) — pure
  helpers + end-to-end publish flow + Phase 4 MINOR drift
  invariant.
- 3 new pytest cases (``tests/test_api_endpoints.py``) — ``_dirty``
  decoration on canvas GET response.
- 4 new vitest cases (``tests/inspectors/publish-button-dirty.test.tsx``)
  — button enabled / disabled / back-compat / disabled-no-call.
- Schema parity test updated to include ``publish_baseline`` in
  ``_EXPECTED_BASE_FIELDS``; ``BaseFieldsJson`` updated to match.
- ``BaseInspector.tsx`` LOC ceiling 270 → 285 (audit-trail noted
  in the structural-guards test).
- Full suite: 399 pytest + 533 vitest pass.

**Approval:** User-locked via AskUserQuestion 2026-05-17 (option
"변경 없으면 publish 버튼 비활성화"). Plan approved via ExitPlanMode.
**Post-ship user confirm 2026-05-17:** *"이제 되네"* — user
verified the dirty-gate works in real Chrome after the MCP server
was restarted with v0.22.0 code (server-restart needed because
Python lacks Vite's HMR; the previous MCP process was still serving
v0.21.4 responses without ``_dirty``). Same turn surfaced a UX
follow-up *"퍼블리시 버튼이 인스펙터 창 아래로 좀 크게"* — queued
in NEXT_SESSION.md as the ``v0.22.x publish-button placement +
size`` item, deferred per user *"이런건 나중에 합시다"*.

---

### D-2026-05-17-I — Published-MD folder reorg + Inspector Published versions UI (v0.23.0)

**Context:** Two adjacent user requests during the v0.22.0 ship:
*"발행을 하면요. md 가 생기잖아요. 그거 어디서 보여줬으면 하는데
그거 어디에 생기는지도 좀 알려주고요"* and *"폴더 정리를 좀
해주셔야할 것 같은데요. 무지성하게 정리하지 마시구요."* — i.e.
the published MD library needs both a viewer surface and a deliberate
folder structure.

The pre-v0.23.0 layout was flat:
``<canvas>/published/<kind>-<slug>-v<X>.md``. With multiple kinds
× multiple nodes × N versions each, the published folder grew into
an unbrowsable list with no logical grouping.

**Decision 1 — Folder layout = ``<canvas>/published/<kind>/<slug>/v<X>.md``**

User-picked via AskUserQuestion 2026-05-17 with ASCII-tree previews
of three candidate layouts (slug-keyed / id-keyed / flat-kind).

```
.plot/<project_id>/foundation/published/
  ├── mission/mission/v2.0.md v3.0.md v4.0.md
  ├── identity/voice/v2.0.md v3.0.md v4.0.md
  └── core_value/core-value/v2.0.md v3.0.md v4.0.md
```

Rationale: one folder per logical document; all versions of the same
node grouped together; kind serves as the top-level taxonomy.
Label rename → folder rename → git tracks via rename detection.

**Decision 2 — Migration = smallest viable idempotent first-read move**

User: *"마이그레이션이 필요한가? 아직 쓰는 사람도 없는데?? 하지만
우리 테스트 프로젝트에서 마이그레이션이 필요하지. 그건 그냥 알아서
해요."*

Implemented as ``_migrate_published_flat_to_kind_slug(canvas_dir)`` in
``folder_io.py``, called from ``read_canvas`` for every canvas kind.
The helper regex-matches legacy filenames
(``^(?P<kind>[a-z_]+)-(?P<slug>.+)-v(?P<v>\d+\.\d+)\.md$``), moves
each to the new location via ``Path.rename``, and skips silently if
the destination already exists. Idempotent — once the legacy files
are gone, subsequent calls are no-ops. No special git commit for the
move (same pattern as ``_absorb_md_typed_text_into_json``).

**Decision 3 — Inspector "Published versions" section + click-to-modal**

User-picked from 4 UX options 2026-05-17: *"인스펙터에 파일 정보
보여주고요. 클릭하면 모달 팝업으로"*. Implementation:

- **Server**: new
  ``GET /api/projects/{id}/canvases/{kind}/nodes/{node_id}/published``
  reads the slug folder for the node and returns
  ``{versions: [{version, path, published_at, sha, size}, ...]}``
  sorted newest first. ``published_at`` from MD frontmatter; ``sha``
  from ``git log --diff-filter=A -1 --format=%h -- <path>``.
- **Client**:
  - ``PublishedVersionsSection`` renders inside ``BaseInspector``
    after ``DetailsSection``, gated by ``canPublish(node)``. One
    row per version (button) showing version + published_at + sha;
    click → opens ``PublishedMDModal``.
  - ``PublishedMDModal`` reuses ``MDPreview`` (GFM + Mermaid) inside
    a SketchBodyModal-style backdrop+escape scaffold. Loads the MD
    via the existing ``readFile`` (``GET /api/files``) — no new
    file-read endpoint needed.
  - List refreshes whenever ``node.version`` changes (so a
    just-clicked publish button surfaces the new ``vN.0`` row).
- **i18n**: new keys ``inspector.publishedVersions`` (section
  header), ``inspector.publishedVersionsEmpty`` ("아직 발행된 버전
  없음" / "No published versions yet").

**LOC ceiling raise:** ``BaseInspector.tsx`` 285 → 295 to absorb the
``PublishedVersionsSection`` insertion (7 LOC of props wiring inside a
``canPublish(node)`` guard). Pinned in ``structural-guards.test.tsx``
with the v0.18.0 → v0.22.0 → v0.23.0 historic note.

**Verification:**
- 10 new pytest cases in ``test_published_endpoint.py`` (path
  layout, migration idempotence, endpoint output, 404 path).
- 4 existing pytest cases updated to the new path shape
  (``test_md_publish.py`` + ``test_folder_io.py``).
- 4 new vitest cases in ``published-versions-section.test.tsx``
  (empty / non-empty / click-opens-modal / refreshKey re-fetch).
- Full suite: 409 pytest + 539 vitest pass; mypy + tsc clean.

**Approval:** User-locked via two AskUserQuestion rounds 2026-05-17
(folder layout via ASCII-tree preview, migration policy via "그냥
알아서 해요"). Plan approved via ExitPlanMode same turn. User then
said *"3 빼고 싹다 해버리지 뭐"* to ship v0.23.0 + four follow-ups
in one session.

**Spec impact:**
- ``SPEC.md §Publish §What lands on disk per publish`` path example
  rewritten to ``<kind>/<slug>/v<X>.md`` with v0.23.0 + auto-migration
  note.
- ``SPEC.md §Publish`` adds new ``§Published versions in the
  Inspector`` subsection.

**Cross-refs:**
- [D-2026-05-16-E](./DECISIONS.md) — Phase 3 publish; the
  ``published_md_path`` function lives there.
- [D-2026-05-17-H](./DECISIONS.md) — v0.22.0 dirty-gate; the
  ``PublishedVersionsSection`` refresh key is ``node.version``,
  which moves on publish (MAJOR) and on Phase 4 propagation
  (MINOR). MINOR-only drift won't add new rows but the re-fetch
  is cheap.

---

### D-2026-05-17-J — Unpublish button (v0.23.1)

**Context:** NEXT_SESSION.md had a long-standing follow-up entry
``v0.18.x follow-up — Unpublish button`` with a fully-spec'd
implementation. With v0.23.0 surfacing the published library in the
Inspector, the natural next step was to also give the user a way to
undo a misclicked publish without dropping to the shell. User
approved batch-ship 2026-05-17 (*"3 빼고 싹다 해버리지 뭐"*).

**Decision:** Implement Unpublish as **``git revert`` of the most
recent publish commit for the node**. The revert pattern preserves
git history (non-destructive) and atomically undoes:
- the canvas.json version bump,
- the new MD file,
- any Phase 4 ancestor MINOR bumps that were part of the same commit.

**Server:**
- ``git_store.py::find_latest_publish_commit(project_dir, node_id)``
  greps the log for the ``Publish-Node-Id: <node_id>`` trailer
  (extended regex, ``--format=%H``).
- ``git_store.py::revert_publish(project_dir, sha)`` runs
  ``git revert --no-edit <sha>`` and returns the new HEAD sha.
- ``git_store.py::ensure_clean_working_tree(project_dir)`` —
  **safety helper introduced for unpublish robustness.** Before a
  publish, snapshots any untracked / dirty files into a separate
  ``chore(plot): seed pre-publish state`` commit, so the subsequent
  publish commit only contains the publish-specific changes. Without
  this, the very first publish in a fresh project would bundle
  canvas.json + .gitignore + .gitattributes into one publish commit,
  and reverting it would wipe canvas.json. Called from
  ``publish_node`` (idempotent no-op when the tree is already clean).
- ``folder_io.py::unpublish_node(plot_root, project_id, canvas_kind,
  node_id, *, service_id=None)`` — resolves the node, locates the
  publish commit, runs revert, re-reads the canvas to capture the
  rolled-back version. Raises ``UnpublishNotEligibleError`` (409)
  when no publish commit exists; ``KeyError`` (404) when the node
  isn't on the canvas.
- HTTP endpoint
  ``POST /api/projects/{id}/canvases/{kind}/nodes/{node_id}/unpublish``
  returns ``{node_id, from_version, to_version, reverted_sha,
  revert_commit_sha}``.

**Client:**
- New ``api.ts::unpublishNode(...)`` mirrors ``publishNode``.
- ``BaseInspector`` adds an **↩ unpublish** button next to the
  publish button, visible only when ``canPublish(node)`` AND
  ``node.version !== "v1.0"``. Confirm dialog text describes the
  ``v(N) → v(N-1).0`` rollback and notes that history is preserved.
- ``onUnpublishNode`` prop threads through ``SketchInspectorBindings``
  → ``SketchCanvas`` → ``App.tsx``, parallel to ``onPublishNode``.
- ``useProject.unpublishNodeAction`` mirrors ``publishNodeAction``
  (re-fetch all canvases after revert so Inspector + canvas reflect
  the new version).

**i18n:** new keys ``inspector.unpublish``,
``inspector.unpublishShort`` (*"↩ unpublish"*),
``inspector.unpublishHint``, ``inspector.confirmUnpublish``.

**LOC ceiling raises (audit trail):**
- ``BaseInspector.tsx`` 295 → 340 (unpublish button + handler).
- ``SketchCanvas.tsx`` 440 → 450 (onUnpublishNode prop wiring).
- ``App.tsx`` 400 → 410 (handler wired on both canvas slots).

**Verification:**
- 8 new pytest cases in ``test_unpublish.py``: revert behaviour,
  MD-file cleanup, revert-commit subject, error paths
  (UnpublishNotEligibleError / KeyError), HTTP round-trip
  (201/404/409).
- Full suite: 417 pytest + 539 vitest pass; mypy + tsc clean.

**Approval:** User-locked via NEXT_SESSION.md spec (filed 2026-05-16);
batch-ship approved 2026-05-17 (*"3 빼고 싹다 해버리지 뭐. 플랜모드
필요합니까?"*). No plan-mode needed since the spec was already
fully-defined.

**Spec impact:** No SPEC text added in this entry — the publish
spec already implies a recovery path (PUBLISH.md documents the
manual ``git revert HEAD`` flow that this feature automates). A
future ``SPEC.md §Publish §Unpublish`` paragraph can be added if
the recovery flow grows new options (e.g. revert older commits,
not just the most recent).

**Cross-refs:**
- NEXT_SESSION.md ``v0.18.x follow-up — Unpublish button`` (now
  archived).
- [D-2026-05-16-E](./DECISIONS.md) — Phase 3 publish + the
  ``Publish-Node-Id`` trailer this implementation greps for.
- [D-2026-05-17-C](./DECISIONS.md) — Phase 4 MINOR propagation;
  ``git revert`` atomically reverses the ancestor bumps too.
- [D-2026-05-17-H](./DECISIONS.md) — v0.22.0 dirty-gate; after an
  unpublish, ``_dirty`` recomputes (the baseline disappears with
  the reverted commit, so dirty = true via the None-baseline path).
- [D-2026-05-17-I](./DECISIONS.md) — v0.23.0 folder reorg + Inspector
  Published versions section; the list will reflect the removal of
  the reverted MD file on next refresh.

---

### D-2026-05-17-K — Inspector publish footer + portal+resizable Published MD modal (v0.23.2)

**Context:** After v0.23.1 shipped (Publish + Unpublish buttons in
the Inspector header), the user surfaced two adjacent UX issues:

1. *"퍼블리시 버튼이 인스펙터 창 아래로 좀 크게"* — the publish
   button as a small icon in the cluttered header isn't a primary
   CTA. Inspector's clear action surface should be the publish.
2. *"모달 팝업이 인스펙터 영역에서만 보이네요? 저거 그냥 가운데
   보이면 좋은데 크기 조절 가능하게 해서."* — the v0.23.0 Published
   MD modal was visually trapped inside the Inspector aside rather
   than centred on the viewport, and was a fixed size.

Both are bound to the same Inspector layout pass, so they ship in
a single commit.

**Decision 1 — Publish footer (sticky, primary CTA)**

User-picked from ASCII-mockup AskUserQuestion (4 layouts):

```
┌ Inspector ──────────────┐
│ CORE VALUE  v2.0   ✕    │  ← header (publish moved out)
├─────────────────────────┤
│ Label / fields / ...    │  ← scrolling body
│ Published versions      │
│  • v2.0 ...             │
├─────────────────────────┤
│ ┌─────────────────────┐ │  ← sticky footer
│ │  📤 Publish → v3.0  │ │  ← primary CTA (emerald-600)
│ └─────────────────────┘ │
│      ↩ unpublish v2.0   │  ← secondary text link
└─────────────────────────┘
```

- Implementation: ``BaseInspector`` now ends in a ``shrink-0
  border-t bg-white p-3`` footer block (the existing ``flex
  flex-col`` aside layout makes this a natural sticky pattern —
  the scrollable body is ``flex-1 overflow-y-auto``, so the footer
  sits at the visible bottom regardless of scroll position).
- Publish button: full-width, ``bg-emerald-600 text-white shadow-sm``
  when dirty; ``bg-slate-100 text-slate-400 cursor-not-allowed``
  when clean. Label includes the next version (e.g. *"📤 publish
  → v3.0"*) so the user sees the bump magnitude before clicking.
- Unpublish: small text link below the publish button, amber colour,
  hover underline. Visible only when ``version !== "v1.0"`` (mirror
  of v0.23.1 logic).
- Footer only renders for publish-eligible kinds — for project /
  is_root / *_ref nodes the Inspector ends at the scrollable body
  (no empty footer).

**Decision 2 — PublishedMDModal via React Portal + CSS resize**

Root cause for the "trapped modal" symptom: the Inspector aside
carries ``backdrop-blur``. CSS spec — any element with
``backdrop-filter`` becomes the containing block for its
``position: fixed`` descendants (the same is true for ``transform``,
``filter``, ``perspective``, ``will-change``, ``contain``). So the
modal's ``fixed inset-0`` was resolving against the aside, not the
viewport.

- Fix: ``PublishedMDModal`` now wraps its tree in
  ``createPortal(modal, document.body)`` so it lives directly under
  ``<body>`` and the ``fixed`` positioning lands on the viewport.
- Resizable: modal container gets inline style ``resize: both;
  overflow: hidden; minWidth: 360px; minHeight: 240px; maxWidth:
  95vw; maxHeight: 95vh; width: 720px; height: 80vh``. The browser
  draws a small resize grip in the bottom-right corner; user can
  drag to any size within the min/max.

**Why not also restructure SketchBodyModal:** SketchBodyModal is
mounted in ``SketchCanvas`` (outside the Inspector aside), so it
already centres on the viewport. No portal needed there.

**Approval:** User-locked the footer layout via AskUserQuestion
ASCII-mockup 2026-05-17 (option A). Modal portal+resize was a
direct user request 2026-05-17 (*"가운데 보이면 좋은데 크기 조절
가능하게 해서"*) — implemented without further question since the
direction is unambiguous.

**LOC ceiling raises:**
- ``BaseInspector.tsx`` 340 → 380 (footer block adds ~95 LOC; net
  ~+40 after removing the header publish/unpublish IIFEs).

**Verification:**
- 539 vitest pass; tsc clean.
- Manual Gate 3: modal opens centred on viewport (verified via
  Playwright + screenshot), resizable corner grip works, Escape
  closes, backdrop click closes.

**Spec impact:** ``SPEC.md §Publish`` doesn't pin button placement
(intentionally — that's UX detail, not contract). No SPEC change
required.

**Cross-refs:**
- [D-2026-05-17-H](./DECISIONS.md) — v0.22.0 dirty-gate still drives
  the publish button enabled/disabled state.
- [D-2026-05-17-I](./DECISIONS.md) — v0.23.0 PublishedVersionsSection
  + PublishedMDModal; the modal is now portal'd.
- [D-2026-05-17-J](./DECISIONS.md) — v0.23.1 Unpublish; the unpublish
  button is now the secondary action under the footer publish CTA.

---

### D-2026-05-17-L — Live Preview Stage 3 (heading + list + image, v0.24.0)

**Context:** v0.19.0 (D-2026-05-17-B) shipped the CodeMirror 6
MdTextarea foundation with syntax highlight = Stage 1. v0.21.0
(D-2026-05-17-D) added mermaid inline SVG widgets = Stage 2. The
3-stage Obsidian Live Preview track planned **Stage 3** as
heading-font-size + list-bullet + image-embed decorations on top of
the source. User approved batch-shipping all three together
2026-05-17 (*"(A) heading + list + image 세 가지 모두 v0.24.0 에 한
번에 ship"* via AskUserQuestion).

**Decision:** Three new CodeMirror plugins (separate files for SoC),
all wired into the existing ``MdTextarea`` extensions array.

| Plugin | Decoration kind | Pattern |
|---|---|---|
| ``mdHeadingPlugin`` | Line (mark) | ATXHeading1-6 nodes → line class ``cm-md-h{N}``; CSS theme scales font-size (H1 1.5×, H2 1.3×, H3 1.15×, H4-6 just bold). |
| ``mdListPlugin`` | Mark | ``ListMark`` nodes inside ``BulletList`` (skip OrderedList) → mark class ``cm-md-bullet``; CSS hides the raw ``- / * / +`` char and paints ``•`` via ``::before``. |
| ``mdImagePlugin`` | Block widget | ``Image`` nodes with image-extension URLs → block widget placed after the image's line, holding a lazy-loaded ``<img>``. Same StateField + ViewPlugin debouncer split as mdMermaidPlugin (block widgets must come from a StateField per CM6). |

**Heading sizing rationale (reasonable defaults):**
H1 1.5× / H2 1.3× / H3 1.15× mirrors Obsidian Live Preview's
conservative scaling — enough for visual hierarchy, not so much that
short Inspector panels run out of space. H4-H6 keep base font-size +
bold so deep heading nests don't shrink past readable.

**Bullet glyph rationale:** ``•`` (U+2022) matches GitHub-flavoured
markdown, Obsidian Live Preview, and Mermaid's own list rendering
— the universal "this is an unordered list item" glyph.

**Image scope:**
- Source URLs accepted: ``http(s)://...``, ``data:image/...``, and
  project-relative paths (``./img.png`` or ``img.png``).
- Project-relative paths require a new server endpoint
  ``GET /api/files/raw`` that serves bytes (the existing
  ``/api/files`` returns JSON ``{content}`` — unusable for an
  ``<img>`` tag).
- Server-side extension allow-list:
  ``.png/.jpg/.jpeg/.gif/.webp/.avif/.svg``. Path-traversal safety
  via the existing ``resolve_safe_path``.
- Broken image → red-bordered "image not loaded: ``<url>``" block
  swap on ``img.onerror``.
- Lazy load (``loading="lazy"``) so off-screen images don't fetch.
- Sizing: ``max-width: 100%; max-height: 480px; display: block;
  margin: 0 auto``. User-resizable not needed — fits the Inspector
  width automatically.

**SSOT invariant:** all three plugins are visual-only. The doc is
never mutated; the user keeps editing the raw markdown source above
the rendered output.

**Verification:**
- 4 new pytest cases in ``test_file_raw_endpoint.py``: byte
  round-trip, 404 for missing file, 400 for disallowed extension,
  400 for path-traversal attempt.
- Full suite: 421 pytest + 545 vitest pass; mypy + tsc clean.

**Approval:** User-locked via AskUserQuestion 2026-05-17 (option
"(A) heading + list + image 세 가지 모두 v0.24.0 에 한 번에 ship"
+ ASCII-mockup preview of rendered output).

**Spec impact:** ``SPEC.md §Typed text and body fields`` mentions
Live Preview decorations; the Stage 3 paragraph is added there.

**Cross-refs:**
- [D-2026-05-17-B](./DECISIONS.md) — v0.19.0 Stage 1 (MdTextarea
  foundation).
- [D-2026-05-17-D](./DECISIONS.md) — v0.21.0 Stage 2 (mermaid
  inline SVG). The image plugin reuses the same StateField + ViewPlugin
  debouncer split.
- [D-2026-05-13-O](./DECISIONS.md) #2 — *"JSON value = MD-formatted
  string"* SSOT; preserved by all three decorations being visual-only.

---

### D-2026-05-17-M — 4-ref symmetry: notes_in_context for mission/value/identity_ref (v0.24.1)

**Context:** Long-standing NEXT_SESSION item (filed 2026-05-16,
D-2026-05-16-F follow-up) asking whether ``actor_ref``'s
``gives``/``receives`` typed-text was an intentional asymmetry vs the
other 3 ref kinds being pure pointers. User-locked direction
2026-05-17 via AskUserQuestion: **option (B) — extend**.

**Before:**

| ref kind | typed text |
|---|---|
| ActorRefNode | ``gives`` + ``receives`` (service-context value flow) |
| MissionRefNode | none (pure pointer) |
| ValueRefNode | none (pure pointer) |
| IdentityRefNode | none (pure pointer) |

**Decision:** All 3 non-actor ref kinds gain a single free-form
``notes_in_context: str = ""`` field. Service authors can capture how
the referenced Mission / CoreValue / Identity applies to **this**
service without leaving the canvas.

```
actor_ref     gives + receives     ← unchanged (richer than the others)
mission_ref   notes_in_context     ← new
value_ref     notes_in_context     ← new
identity_ref  notes_in_context     ← new
```

**Implementation:**
- ``mashbill/models.py`` — added ``notes_in_context: str = ""`` to
  ``MissionRefNode`` / ``ValueRefNode`` / ``IdentityRefNode``.
- ``viewer/src/domain/{MissionRef, ValueRef, IdentityRef}.ts`` —
  added field to interface + class + ``fromJson`` (with
  ``readNotesInContext`` helper) + ``toJson``.
- ``viewer/src/canvases/inspectors/{mission_ref,value_ref,identity_ref}/index.tsx``
  — added a single ``MdTextarea`` for the field below the existing
  ``FoundationRefBlock``.
- ``viewer/src/i18n/locales/{en,ko}.json`` — new keys
  ``inspector.field.notesInContext`` and
  ``inspector.fieldHint.notesInContext``.
- ``tests/inspectors/inspectors.smoke.test.tsx`` +
  ``publish-button-dirty.test.tsx`` — added ``notes_in_context: ""``
  to the ``makeNode`` helper so the per-kind smoke tests still
  satisfy the SketchNode type.

**Why no migration:** pre-v0.24.1 canvas.json files don't carry the
field; Pydantic's default ``""`` fills it on read. No schema bump
needed.

**Approval:** User-locked 2026-05-17 via AskUserQuestion
("(B) 확장 — mission/value/identity_ref 에도 notes_in_context").
Batch-shipped with v0.23.x + v0.24.0 in the same session.

**Verification:**
- 421 pytest pass (no regressions; schema-parity test now requires
  the new field on the TS side, which we added).
- 545 vitest pass.
- mypy + tsc clean.

**Spec impact:** None pinned in SPEC — the ``notes_in_context``
contract is "free-form typed text per-ref in service context",
identical to how the existing ``actor_ref.gives``/``receives`` work
(no SPEC pin either).

**Cross-refs:**
- D-2026-05-16-F — body field rollout (the pattern this follows for
  free-form ref-side typed text).
- NEXT_SESSION.md ``cross-kind ref typed-text symmetry`` (now
  archived).

---

### D-2026-05-18-A — Published folder name: slug → node_id (v0.24.3)

**Context:** v0.23.0 (D-2026-05-17-I) made published MD files live
in ``<canvas>/published/<kind>/<slug>/<version>.md`` where ``slug =
slugify(label)``. ``slugify`` preserves Korean / CJK characters, so
Banas's "관용 (Tolerance)" core value would land in
``published/core_value/관용-tolerance/v2.0.md``. User flagged the
non-ASCII folder name 2026-05-17: *"파일이름이 한글로 만들어지는게
좀 그러네"*. After ASCII-tree review of (A) node-id-based,
(B) Romanization, (C) keep slug, user picked **(A)** with the
follow-up *"그냥 id 로 해야겠다. 그지?"*.

**Decision:** Folder name = **``node.id``**, not ``slugify(label)``.
Novel's id policy nudges users to ASCII identifiers, so the folder
path is now reliably ASCII without any transformation. Bonus: label
rename no longer renames the folder (id is stable).

**Implementation:**

- ``mashbill/md_publish.py::published_md_path`` signature changed
  from ``(canvas_dir, *, kind, label, version)`` to
  ``(canvas_dir, *, kind, node_id, version)``. Drops the
  ``slugify`` call; uses ``node_id`` verbatim.
- ``mashbill/folder_io.py::publish_node`` updated caller.
- ``mashbill/folder_io.py`` new
  ``_migrate_published_slug_to_id(canvas_dir, raw_canvas)``: walks
  the raw canvas nodes, computes the old slug for each ``(id,
  label)`` pair, and renames ``published/<kind>/<slug>/`` →
  ``published/<kind>/<node_id>/``. Idempotent (no-op when slug ==
  node_id, or when the slug folder no longer exists). Conflicts
  (id folder already exists) leave the slug folder in place for
  audit — we never overwrite. Hooked into ``read_canvas`` alongside
  the existing v0.23.0 flat-to-kind-slug migration.
- ``mashbill/api_endpoints.py::node_published_list_endpoint``
  switched from ``slug_dir = published/<kind>/<slug>`` to
  ``node_dir = published/<kind>/<node.id>``.

**Migration coverage:**

| From layout | Migration path | Helper |
|---|---|---|
| Pre-v0.23.0 flat | flat → kind/slug → kind/id | flat-to-kind-slug (still runs) → slug-to-id |
| v0.23.0 kind/slug | kind/slug → kind/id | slug-to-id |
| v0.24.3 kind/id | (no-op) | both helpers return early |

Two-step migration for pre-v0.23.0 projects is intentional: the
flat-to-kind-slug helper still runs first to keep that v0.23.0
contract simple, then slug-to-id rewrites the result. Result is
the same regardless of which version the canvas was last written by.

**Verification:**
- 3 new pytest cases (``test_published_endpoint.py``): slug folder
  rename, no-op when id==slug, skip when destination exists.
- 3 existing pytest cases updated for new signature
  (``test_md_publish.py``).
- Full suite: 424 pytest + 545 vitest pass; mypy + tsc clean.

**Approval:** User-locked 2026-05-17 via AskUserQuestion option (A)
+ followed-up confirmation *"그냥 id 로 해야겠다. 그지?"*.

**Spec impact:**
- ``SPEC.md §Publish §What lands on disk per publish`` path example
  rewritten from ``<slug>`` to ``<node_id>``.

**Cross-refs:**
- [D-2026-05-17-I](./DECISIONS.md) — v0.23.0 folder reorg + Inspector
  "Published versions" UI. Superseded by this entry's folder choice;
  the UI surface is unchanged.
- [D-2026-05-17-J](./DECISIONS.md) — Unpublish; revert path unchanged
  (git revert on the publish commit also reverses the directory
  structure).
- [[feedback-show-dont-tell]] (memory) — ASCII-tree previews drove
  the lock for this decision.

---

### D-2026-05-17-N — Default node size + auto-layout collision fixes (v0.24.2)

**Context:** After importing the Banas workspace data into a fresh
Novel project (Foundation + Actors via one-off script), the user
reported two adjacent UX issues:

> *"정렬할 때 노드끼리 겹치면 안되는데 그리고 노드 크기가 너무 커요."*

Two AskUserQuestion locks 2026-05-17 narrowed the fixes:

- "정렬할 때 노드 겹침" → option (A) — the ➤ auto-layout button on
  Foundation produces visual overlap when nodes have large footprints
  (200+ px wide) because the 32 px sibling-padding is too small to
  separate them cleanly; isolated nodes also stack into a single
  vertical column that grows unwieldy past 5 entries.
- "노드 크기가 너무 크다" → option (B) — Novel's hardcoded default
  ``180×80`` is too big for canvases that hold 5-10 nodes per view;
  the user wants a smaller default that fits more material per
  viewport without scroll.

**Decision:**

1. **Default node size 180×80 → 140×60** in three places (server
   Pydantic, client ``parseBaseFields`` fallback, viewer
   ``DEFAULT_WIDTH``/``HEIGHT`` constants). Existing nodes keep
   their own width/height in canvas.json; only nodes created from
   this point on adopt the new default. No migration.
2. **Auto-layout padding 32 → 64**. Doubles the breathing room
   between sibling subtrees + isolated-node grid cells. With the
   smaller default node size, the resulting layout is *more*
   compact, not less.
3. **Isolated-node placement: column → square-ish grid**. Pre-v0.24.2
   stacked all isolated (not BFS-reachable from anchor) nodes into a
   single vertical column to the anchor's lower-right; this got
   unwieldy past ~5 entries and could visually overlap with the
   spanning-tree footprint. v0.24.2 packs them into a grid with
   ``cols = ceil(sqrt(count))`` rows; cell step =
   ``max(width) + padding`` × ``max(height) + padding`` so cells
   never collide.

**Implementation:**

| File | Change |
|---|---|
| ``mashbill/mashbill/models.py`` | ``BaseNodeFields.width: float = 140.0``, ``height: float = 60.0``. |
| ``plot/viewer/src/canvases/sketch/constants.ts`` | ``DEFAULT_WIDTH = 140``, ``DEFAULT_HEIGHT = 60``. |
| ``plot/viewer/src/domain/BaseFields.ts`` | ``parseBaseFields`` defaults updated to match. |
| ``plot/viewer/src/canvases/sketch/autoLayout.ts`` | ``DEFAULT_PADDING = 64``; isolated-nodes block rewritten as a grid. |

**Tests updated:**
- ``base-fields.test.ts`` — expects 140×60 defaults.
- ``round-trip.test.ts`` — expects 140 default width.
- ``autoLayout.test.ts`` — isolated-nodes test rewritten for grid
  placement (2 orphans → same y, different x).
- Full suite: 421 pytest + 545 vitest pass; mypy + tsc clean.

**Approval:** User-locked via two AskUserQuestion options
2026-05-17 (Align issue: A — auto-layout button; Node size: B —
Novel default reduction).

**Spec impact:**
- ``SPEC.md §Auto-layout`` mentions the padding; the value isn't
  pinned, so no SPEC text change required for the padding bump.
- The default node size isn't pinned in SPEC either (it's an
  implementation default, not a contract).

**Cross-refs:**
- [D-2026-05-13-L](./DECISIONS.md) — auto-layout Foundation-only
  isolation rule (unchanged; the grid rewrite is internal to the
  algorithm).
- [D-2026-05-04-A](./DECISIONS.md) — all edges user-drawn; isolated
  nodes (no edges to the anchor) are still placed but in their own
  grid quadrant.

**Cross-refs:**
- [D-2026-05-16-E](./DECISIONS.md) — Phase 3 publish. The
  "always-bump on the publish target (MAJOR)" clause under
  ``§Idempotence`` (now rewritten under ``§Publish gated by dirty``)
  is **conditioned** on the button being enabled; ``§Idempotence``
  itself no longer governs the user's intent gate.
- [D-2026-05-17-C](./DECISIONS.md) — Phase 4 MINOR propagation.
  Confirmed non-dirty per #6 above; the propagated bump is bookkeeping.

**Spec impact:** No SPEC text change required — SPEC already
implied this behaviour. This entry documents the implementation
correction, not a new behaviour.

**Cross-refs:**
- [D-2026-05-04-A](./DECISIONS.md) — *"all edges are user-drawn,
  no auto-emission"*; loose mode preserves this invariant
  (`handleConnect` is still the only edge-creation path).
- [D-2026-05-13-I](./DECISIONS.md) — silent-state issues queue
  (this was the latent example of "user action silently fails";
  scratched off the queue).

---

### D-2026-05-18-B — Auto-layout opt-in extended to Actors canvas (v0.24.5)

**Context:** Per [D-2026-05-13-L](./DECISIONS.md) the auto-layout
button is a per-wrapper opt-in. v0.16.36 wired it for
`FoundationCanvas` only. 2026-05-18, the user opened the Actors
canvas on `banas-imported` (Hero / Fan / Bana root personas
overlapping) and directly requested the same button:
*"액터 캔버스에 노드 정렬 기능 넣기"*.

The isolation contract is *honoured by extending opt-in, not by
removing it*: `ActorsCanvas` now also passes
`enableAutoLayout={true}`; `ServicesCanvas` and `ServiceDetailCanvas`
remain off. The 4-layer defence model (wrapper opt-in / conditional
render / no-mutation-when-disabled / positions-only) is unchanged —
the opt-in list grew from {Foundation} to {Foundation, Actors}.

**Decision:** `ActorsCanvas` joins `FoundationCanvas` in opting into
the `⊞` Auto-layout button. Same contract: one-shot apply via the
regular `onDocChange` pipeline, `Cmd+Z` undoes it, positions-only
mutation (kind / label / parent_id / typed-text bytewise identical).
`ServicesCanvas` and `ServiceDetailCanvas` stay off — `Services` is
hub-and-spoke around a single anchored Service node and
`ServiceDetail` is root-pinned, neither of which the v0.13.9
directional-tree algorithm has an obvious win for. Revisit when a
real overlap case arrives there.

**Implementation:**

- `viewer/src/canvases/ActorsCanvas.tsx` — add `enableAutoLayout={true}`.
- `viewer/tests/auto-layout-isolation.test.tsx`:
  - Flip "ActorsCanvas wrapper does NOT render" → "ActorsCanvas
    wrapper renders".
  - Add a new positions-only assertion for the Actors canvas
    (mirror of the Foundation positions-only test, using `actor`
    kind + `motivation` / `pain` / `side` typed fields).
  - `ServicesCanvas` and `ServiceDetailCanvas` assertions
    unchanged — they remain the negative side of the isolation
    contract.
- `docs/SPEC.md §Auto-layout` — wording / heading / isolation
  contract section / history entry updated.

**Approval:** Accepted by user, 2026-05-18 — direct request
*"액터 캔버스에 노드 정렬 기능 넣기"*. Confirmed via Gate 0 +
Gate 1 (SPEC change for a behaviour not yet pinned) before any
code edit.

**Cross-refs:**

- [D-2026-05-13-L](./DECISIONS.md) — the original Foundation-only
  opt-in; the isolation contract scaffolding this entry extends.
- [D-2026-05-04-D](./DECISIONS.md) / [D-2026-05-10-G](./DECISIONS.md)
  — prior removal cycles; resolved structurally by per-wrapper
  opt-in (so this extension does not re-introduce the original
  "auto-layout everywhere" risk that drove the removals).

---

### D-2026-05-19-A — Research subject 백데이터 기능 deferred (v0.24.6)

**Context:** 2026-05-19 actor 캔버스 4층 hierarchy (anchor → Bana →
mode → vertical) 토론 중 사용자가 추가 question:
*"바텐더 김유정 / 편의점 주인 박태식 같은 구체 인물을 5층 노드로
두면 어떨까?"*. 토론 통해 도달한 결론은 actor 캔버스 = **역할/클래스
그래프** (PHILOSOPHY P5 "Actor as class") 유지, 구체 인물은 *역할의
아래 노드* 가 아니라 *역할이 합쳐져 만들어지는 source 데이터*.

User 명시 동의: *"actor 캔버스에서는 4층까지... 백데이터처럼 할 수
있으면 좋겠다 갑자기 생각... 편의 기능이라고 생각하면 되겠죠?"*.

**Decision:** Actor 캔버스 = **4-layer max** (anchor → Bana → mode
→ vertical). Research subject (실제 인터뷰 대상자) 는 *그 사람들이
합쳐져서 추출되는* actor 의 `body` (Markdown) 필드 안 `## 인터뷰
대상자` 섹션에 적음. **새 typed 필드, 새 kind, 새 캔버스 모두 만들지
않음.** Global CLAUDE.md `design: YAGNI > others` + Novel 의 v0.13
god SketchNode 교훈 (speculative 필드 추가 = 도메인 구조 망가뜨림)
재발 방지.

**Implementation:**
- 새 코드 0줄.
- `mashbill/docs/NEXT_SESSION.md` — "Research subject 백데이터 기능"
  lower-priority queue entry 추가 (revisit trigger + 4 option
  trajectory 표 포함).
- Claude memory `project_plot_research_subjects_deferred.md` —
  결정 + future trajectory 4 옵션 보존 + revisit trigger
  ("10+ subject 가 body MD 안에 쌓여 sort/filter/search 필요해질
  때").

**Approval:** Accepted by user, 2026-05-19. 토론 시작 *"이거 토론
한판 하고 싶은데.. 다양한 의견을 좀 주세요"* → 4 관점 비교 (Cooper /
JTBD / Service Design / Pragmatic) → 사용자 *"나도 C 처럼 느껴요. ㅇㅋㅇㅋ"*
+ *"이건 편의 기능이라고 생각하면 되겠죠?"* (조건적 동의: 편의 기능
이라는 framing 으로 받아들임) → *"지금으로 충분하다. 결론이죠?"*
(최종 lock).

**Backward-compat 보장 (future trajectory 모두 가능):**
- `fromJson` boundary (D-2026-05-13-D/E) — 새 typed field 추가
  시 default 값으로 backward-compat.
- `test_schema_parity.py` — Pydantic ↔ TS 동기화 강제.
- 즉 *"지금 코드 0 줄 추가 안 해도 미래에 깨끗하게 붙음"*.

**Cross-refs:**
- `[[feedback_no_god_object]]` (memory) — speculative 새 필드 추가
  금지의 SSOT.
- `[[feedback_plot_space_vs_time]]` (memory) — research subject 도
  공간/관계 데이터 (시간 기반 ✗) — Novel 도메인 안.
- `project_plot_research_subjects_deferred.md` (memory) — 결정 +
  trajectory 보존.

---

### D-2026-05-19-B — Actor state/transitions meta-question OPEN (v0.24.7)

**Context:** 2026-05-19 토론 중 사용자가 *"로그인 같은 경우 어떻게
할 거예요?"* 질문 → 익명 방문자 (Guest) → 로그인 service → Bana 또는
Admin 으로 라우팅되는 전이가 Novel actor 모델 안 어디서 표현되는지
드러나지 않음. 즉 PHILOSOPHY P5 *"Actor as class"* 가 *상태(state) /
상태 전이(transition)* 차원을 명시적으로 다루지 못함.

**Decision (개방):** **결정하지 않음.** 현재 암묵적 입장은 *"상태는
Service / ServiceDetail flow 안에 가두고, actor 는 정적 역할/클래스
유지"*. 이 입장이 깨끗한지 / 더 명시적으로 해야 하는지 / 새 schema
field 가 필요한지 — *모두 미해결*. 사용자 직접 표현: *"이거 그냥
patch 로 풀 문제 아닙니다. 모델의 기본 가정을 건드리는 질문이에요."*

**Why pin if open:** 다음 세션에서 *"이걸 이미 결정했나?"* 를 다시
묻지 않도록 — open 상태도 SSOT 가 있어야 함. Novel v0.13 god SketchNode
saga 와 동일 교훈: 결정 안 한 항목을 *암묵* 으로 두면 다음 사람이
ad-hoc 결정함 → 일관성 깨짐.

**Implementation:**
- `mashbill/.claude-plugin/plugin.json` — v0.24.6 → v0.24.7 (docs only).
- `mashbill/CHANGELOG.md` — v0.24.7 entry.
- Claude memory `project_plot_state_transitions_open.md` — 관찰 +
  드러난 긴장 3 가지 + 가능한 해소 방향 5 가지 (현 상태 유지 / state
  typed field / new kind / docs-only 명시화 / state_via_service ref)
  + revisit trigger 보존.

**Trigger to revisit:**
- 사용자가 Novel 안에서 *상태 전이 흐름* (예: 로그인, 결제, 신청 →
  승인 → 거절) 을 그리기 시작하면서 actor 캔버스와 service flow 의
  분리가 어색해질 때.
- 또는 Novel 모델 v1.0 commitment 시점.

**Cross-refs:**
- `[[project_plot_state_transitions_open.md]]` (memory) — open
  question + 해소 방향 5 옵션.
- `docs/PHILOSOPHY.md` P5 — *"Actor as class"* 원문 (이 결정의 기반
  이지만 동시에 이 토론의 출발점).
- D-2026-05-19-A — 같은 *"actor 모델 확장 후보"* 패턴 (research
  subjects 도 deferred). 두 deferred 가 시그널: actor 모델이 추상
  level 에서 압박 받기 시작했음.

---

### D-2026-05-19-C — Actor master (is_root) now publishes directly (v0.24.10)

**Context:** Per `publishEligibility.ts` comment + v0.18.0 setup
(D-2026-05-16-E), `is_root` 노드 (actor 든 service 든) publish 가드에
막혔음 — *"Phase 5 referent flow 가 publish 를 대신 처리한다"* 라는
가정. 그러나 Phase 5 미정 + 현재 사용자가 직접 master 발행 원함:
banas-imported 의 Bana / Admin / Guest (모두 actor + is_root=true)
은 motivation / pain / body 채워져 있는데 발행 버튼 안 보임.

User 명시 (2026-05-19): *"액터 루트도 내용이 있는데 발행되어야하는데"*
+ 토론 통해 *"actor 의 is_root 는 cross-canvas master 마커일 뿐 그
자체로 발행을 막을 이유 없음"* 합의.

**Decision:** Publish 가드를 `is_root` 전반 → `is_root && kind ==
"service"` 로 좁힘. Actor master 는 다른 일반 actor 와 동일한
direct-publish 흐름으로 들어감 (per-node MD + MAJOR bump + git
commit).

- Service is_root 는 *여전히 가드 유지*: ServiceDetail 의 mirror
  관계 (Services 캔버스의 master 가 발행되면 mirror 가 자동 따라옴) 가
  내부 invariant 라 그대로 두는 게 안전. 향후 별개 D-entry 로
  재검토 가능.
- Phase 5 referent flow 가 나중에 ship 되면, master 의 publish v 를
  *referent base 로 참조* 하는 방식으로 자연 위에 얹힘. 충돌 0.

**Implementation:**

| File | 변화 |
|---|---|
| `mashbill/md_publish.py::can_publish` | `if node.is_root: return False` → `if node.is_root and node.kind == "service": return False` |
| `viewer/src/domain/publishEligibility.ts::canPublish` | 동일하게 좁힘 + JSDoc 갱신 (mirror SSOT 유지) |
| `mashbill/mcp_tools.py` (publish_node docstring) | eligibility 설명 갱신 |
| `tests/test_md_publish.py` | `test_can_publish_rejects_is_root` → `test_can_publish_rejects_is_root_service` + 새 `test_can_publish_accepts_is_root_actor` |
| `tests/test_folder_io.py` | `test_publish_node_rejects_root_actor` → `test_publish_node_accepts_root_actor` (성공 path 검증, v1.0→v2.0) |
| `tests/test_api_endpoints.py` | `test_publish_endpoint_ineligible_root_is_409` → `test_publish_endpoint_actor_root_succeeds` (200/201, to_version=v2.0) |
| `viewer/tests/domain/publishEligibility.test.ts` | `it.each(["actor","service"]) rejects is_root` → split into `rejects is_root service` + `accepts is_root actor` |
| `docs/SPEC.md §Publish eligibility` | table 갱신 — actor (is_root) 행을 **visible** 로 |

**Verification:**
- 425 server pytest + 546 viewer vitest 모두 pass.
- mypy clean (19 source files).
- ruff clean for the touched files; 1 pre-existing E501 in
  `api_endpoints.py:541` (from v0.24.3) untouched.

**Approval:** Accepted by user, 2026-05-19. Direct request *"액터
루트도 내용이 있는데 발행되어야하는데"* + 토론 통해 lock (관점
재정렬: YAGNI 잘못 적용한 첫 제안 폐기 → cross-canvas master 의미
재확인 → 가드 좁힘 합의).

**Spec impact:** `docs/SPEC.md §Publish eligibility` table updated.

**Cross-refs:**
- D-2026-05-16-E (v0.18.0 publish UX origin)
- D-2026-05-17-C / D-2026-05-17-K (publish UX 진화)
- D-2026-05-19-B — `[[project_plot_state_transitions_open]]`
  (관련: actor master 가 state 표현하는 게 적절한가의 더 큰 질문)

---

### D-2026-05-19-D — `actor.is_root` deprecated, Symbol concept formalised (v0.24.11)

**Context:** 2026-05-19 *"mark as actor root 의 의미가 대체 뭔지 몰라서
그래요"* — 사용자는 *"Mark as Actor Root (centre of its tree)"* 토글이
무엇을 의미하는지 인식 불가. UI 라벨 자체가 정보 전달 실패 (CLAUDE.md
anti-pattern *"Don't Make Me Think"*).

증거 기반 추적: 원래 의도 (origin commit `54c2f4a`, 2026-04-20) 는
*"three roots — Core, Actor root, Service root"* — singleton trunk
per tree + 각자 *"organisation-side / product-side identity"* (자기
Mission/Values/Identity 보유). v0.13 reset (D-2026-05-12-B) 가
Foundation 분리하면서 *"identity 보유"* 의미 증발. SPEC.md `*actor
(is_root): cross-canvas anchor for actor_ref*` 는 retrofit 된 설명.
v0.24.10 에서 publish 가드 풀면서 *"cross-canvas master"* 의미도
무의미해짐 (publish 측에서 구분 안 함).

사용자 명시 lock (2026-05-19): *"모든 액터는 다른 캔버스에 참조됩니다 ...
좀더 정확히는 서비스 캔버스에 참조될 수 있다고"* + *"액터 및 서브액터는
심볼이 될 수 있고, 파운데이션에 있는 미션/코어밸류/아이덴티티 다 심볼이
될 수 있어요"* + *"그래서 그 심볼을 사용하는 곳은 서비스 캔버스구요"*
+ *"아니 1이지 모든게 다 심볼이 될 수 있다니까"* (옵션 1 = actor.is_root
field 폐기 선택).

**Decision:**

1. **`actor.is_root` 사용처 모두 제거** (semantic deprecation):
   - `BaseInspector.tsx` — "Mark as Actor Root" toggle 삭제, actor
     배지에서 "액터 루트" 분기 삭제.
   - `actor/index.tsx` — `{!node.is_root && <ActorCompositionPlaceholder />}`
     분기 + placeholder 컴포넌트 자체 삭제 ("v0.3 에서 액터 구성 지원
     예정" 미정형 메시지).
   - `inspector.actorCompositionDeferred` i18n 키 stale (둘 다 locales
     에 남아있지만 더 이상 호출 안 됨; 청소는 별도).
2. **Pydantic field 보존** — `BaseNodeFields.is_root` 자체는 schema
   유지 (service 가 여전히 사용). Actor 에서만 의미 없음.
3. **Migration**: `_migrate_actor_isroot_to_false` 가 모든 actor
   `is_root=true` → `false` 로 정정 (canvas read 시 idempotent).
   banas-imported 의 Bana / Admin / Guest 모두 영향 받음 (다음 read 에
   migrated).
4. **Service.is_root 유지** — ServiceDetail mirror anchor 표시로 여전히
   load-bearing.
5. **Symbol 개념을 first-class 로 박음**: `docs/CONCEPTS.md ## Symbol`
   섹션 신설 — 5 candidate kinds (mission / core_value / identity /
   actor / sub-actor) 와 consumer (service / service_detail via *_ref)
   명시. 두 plane 비대칭 흐름 ASCII 다이어그램. Novel의 2층 구조
   (PHILOSOPHY) 와 연결.

**Implementation:**

- `viewer/src/canvases/inspectors/BaseInspector.tsx` (toggle 삭제,
  badge 분기 삭제)
- `viewer/src/canvases/inspectors/actor/index.tsx` (placeholder 삭제)
- `mashbill/folder_io.py` (`_migrate_actor_isroot_to_false`, actors
  canvas read hook)
- `viewer/tests/inspectors/inspectors.smoke.test.tsx` (placeholder
  관련 2 tests 삭제)
- `docs/SPEC.md §Publish eligibility` (table 정리)
- `docs/CONCEPTS.md` (Symbol 섹션 신설)

**Verification:**
- 544/544 viewer + 425/425 server pytest pass.
- mypy + tsc clean.
- canvas.json migration 검증: banas-imported 다음 read 시 Bana/Admin/Guest
  자동 is_root=false 로 갱신.

**Approval:** Accepted by user, 2026-05-19. 토론 6 rounds 통해
정착 — UX 버그 인식 → 원래 의도 추적 (git log) → 옵션 비교 →
사용자 *"1이지"* + Symbol 통합 개념 명시.

**Spec impact:**
- `docs/SPEC.md §Publish eligibility` table 정리.
- `docs/CONCEPTS.md ## Symbol` 섹션 신설.

**Cross-refs:**
- D-2026-05-19-C (v0.24.10 publish 가드 actor 풀린 결정 — 이 entry 가
  그 위에 한 단계 더 청소).
- D-2026-05-12-B (v0.13 god SketchNode 리셋 — 이 reset 이 `is_root`
  원래 의미를 증발시킨 변곡점).
- Origin commit `54c2f4a` (2026-04-20) — `is_root` 원래 도입 의도.
- `[[project_plot_symbol_concept]]` (memory) — Symbol 개념 + 5 candidate
  + producer/consumer 모델 보존.
- `[[feedback_no_god_object]]` — Symbol 을 새 typed field / new kind
  으로 박지 않고 *"이 kind 자체가 Symbol"* 으로 둠 (kind palette 증식
  방지).

---

### D-2026-05-21-A — Auto-save user feedback restored (v0.24.12)

**Context:** 2026-05-21 사용자 시도 *"바텐더 액터에 노트를 채웠어요"*
→ *"자동저장 안되고"* 보고. Probe 결과:

1. **자동 저장 메커니즘 자체는 동작** — 사용자가 친 모든 글자
   (body / motivation / pain) 가 `canvas.json` 에 정상 반영됨.
   ([useCanvasPersist.ts](../viewer/src/hooks/useCanvasPersist.ts)
   의 400ms 디바운스 PUT.)
2. **그러나 가시적 피드백 0 군데** — `useCanvasPersist` 가
   `saveState` ("idle"/"saving"/"saved"/"error") 를 계산하고 return
   하지만 *Header / 어느 shell 컴포넌트도 렌더링 안 함*. 사용자 입장:
   타이핑 → 무반응 → "안 됨" 결론.
3. **부수 발견: PUT 응답 `_dirty` 누락** — `canvas_put_endpoint` 가
   bare canvas 만 반환. GET 엔드포인트에만 `_dirty` 박힘
   ([api_endpoints.py:296](../mashbill/api_endpoints.py)). 결과:
   사용자가 편집해도 publish 버튼이 reload 전까지 stale (이전 GET 시점
   `_dirty=false`). v0.22.0 의 dirty-tracking UX 가 실제로 페이지
   reload 까지 작동 안 함.

**Decision (2-pronged fix, atomic):**

1. **Fix A — Header SaveIndicator (UX 갈증 해소).** `Header.tsx` 에
   `<SaveIndicator state={saveState}>` 컴포넌트 추가. socket dot 옆에
   *idle 시 숨김 / saving "💾 저장중…" / saved "✓ 저장됨" / error "⚠
   저장 실패"*. `App.tsx` 가 `useCanvasPersist().saveState` 를 Header
   prop 으로 흘림. i18n 키 `header.saveState.{saving,saved,error}` 가
   en/ko locales 둘 다 추가.
2. **Fix B — PUT response includes _dirty (정확성).**
   `canvas_put_endpoint` 가 GET 과 동일한 `_dirty` decoration 으로
   응답 본문 enrich. `useCanvasPersist` 가 응답에서 per-node `_dirty`
   추출 → cache 의 동일 노드에 머지 (사용자 in-flight edit 무관 —
   `_dirty` 필드만 갱신, 다른 필드 미변경). 결과: 편집 → 400ms 후
   publish 버튼 즉시 enable.

**Implementation:**

| File | 변화 |
|---|---|
| `mashbill/api_endpoints.py::canvas_put_endpoint` | response body 에 GET 과 동일한 `_dirty` decoration 추가 (~10 lines, lazy import 패턴 GET 과 동일) |
| `viewer/src/hooks/useCanvasPersist.ts` | `.then((res) => {...})` 안에서 `res.canvas.nodes` 의 `_dirty` 를 cache 의 해당 node 에 머지 |
| `viewer/src/shell/Header.tsx` | `SaveIndicator` 컴포넌트 신설, `saveState` prop 받음 |
| `viewer/src/App.tsx` | `useCanvasPersist` 에서 `saveState` 받아 `<Header saveState={...}>` 로 흘림 |
| `viewer/src/i18n/locales/{en,ko}.json` | `header.saveState.{saving,saved,error}` 키 추가 |
| `tests/test_api_endpoints.py` | `test_canvas_put_response_includes_dirty_decoration` 새 케이스 |

**Approval:** Accepted by user, 2026-05-21. 사용자 직접 보고
*"바텐더 액터에 노트를 채웠어요 ... 자동저장 안되고 일단"*
→ probe 통해 *"save mechanism OK, UX feedback 0"* 진단 lock
*"이건 모든 노드에 해당할 것 같은데?"* (= 일반화 가능 confirm)
→ *"네 진행합시다"* 두 fix 동시 ship 승인.

**Verification:**
- 426/426 server pytest (1 새 test 추가) + 544/544 viewer vitest.
- tsc + mypy clean.
- v0.24.11 → v0.24.12.

**Cross-refs:**
- D-2026-05-17-H (v0.22.0 — `_dirty` 컨셉 + 노드별 dirty tracking 도입.
  당시 GET 만 decoration, PUT 누락된 채로 ship 됐음; 이 entry 가 그
  미완 부분 마무리.)
- `useCanvasPersist.ts` (SSOT for save flow)
- `[[feedback_show_dont_tell]]` (memory) — *"silent success 은 버그"*
  rule 의 적용 사례.

---

### D-2026-05-21-B — 설계도 발행 (project-level semver) + blueprint framing (v0.24.13)

**Context:** 2026-05-21 사용자 *"각 캔버스들 정식 발행 개념을 잊은것
같은데요? ... 실제 작업할 때는 고정된 버전이 있어야하는데. 작업
중에 중간에 변경이 이뤄지면 안되잖아요"*. 디스커션 통해 도달:

- 사용자 의도 = *"Novel 의 산출물 = 설계도 (design blueprint), 그 전체
  의 안정된 snapshot 관리 필요"*.
- per-canvas publish 는 D-2026-05-13-J #4 에서 거부 → per-node 로
  결정 (D-2026-05-13-O). 그러나 *"전체 설계도 단위 freeze"* 는
  별개 미해결.
- 사용자 lock: *"그냥 프로젝트에 버저닝하는게 좋지 않습니까?"* +
  *"Banas v0.13 이렇게 붙이듯이"* + *"근데 프로젝트 버저닝은 메이저
  마이너 패치 이렇게 가야죠"*.

**Decision:** **프로젝트 자체에 semver 버전** 도입.

- `ProjectDoc.blueprint_version: str = "v0.1.0"` (Pydantic 기본값,
  기존 프로젝트는 first read 시 자동 backfill).
- 사용자가 `📤 설계도 발행 ▾` 버튼 (CanvasTabs 오른쪽, "세션 기록…"
  자리 대체) 으로 major/minor/patch 중 선택 → semver bump + 그 시점
  git tag (이름 = 새 버전).
- Header 에 현재 `blueprint_version` 항상 표시 (프로젝트 이름 옆 monospace
  배지).
- 기존 ad-hoc tag API (POST /tags) 는 그대로 유지 (사이드바 세션 태그
  UI 가 사용중). 새 endpoint POST /api/projects/{id}/publish 가
  semver bump 흐름 owns.

**Why per-node + per-project (not per-canvas):**
- per-node = 단일 entity 의 evolution (현행 유지).
- per-project = 전체 설계도의 release version (이 entry).
- per-canvas = 거부 (중간 단위, 의미 없는 churn 위험).

**Implementation:**

| File | 변화 |
|---|---|
| `mashbill/models.py::ProjectDoc` | `blueprint_version: str = "v0.1.0"` 필드 추가 |
| `mashbill/api_endpoints.py` | `_bump_blueprint_version()` 헬퍼 + `project_publish_endpoint()` |
| `mashbill/http_app.py` | `POST /api/projects/{project_id}/publish` route 등록 |
| `viewer/src/api.ts` | `publishProject()` + `PublishProjectResponse` + `BlueprintBump` |
| `viewer/src/types.ts::ProjectDoc` | `blueprint_version?: string` |
| `viewer/src/shell/BlueprintPublishButton.tsx` | 신규 — 버튼 + 드롭다운 + confirm |
| `viewer/src/shell/CanvasTabs.tsx` | `onMarkSession` prop 제거 → `blueprintVersion` + `onPublishBlueprint` |
| `viewer/src/shell/Header.tsx` | `blueprintVersion` prop 추가 + 배지 렌더링 |
| `viewer/src/hooks/useProject.ts` | `publishBlueprint(bump)` action |
| `viewer/src/App.tsx` | wire `handlePublishBlueprint` + Header / CanvasTabs 에 version 전달 |
| `viewer/src/i18n/locales/{en,ko}.json` | `publishProject.*` 키 6개 (label/hint/major/minor/patch/confirm/bumpHeader) |
| `tests/test_api_endpoints.py` | 3 새 케이스 (patch bump / major+minor / invalid bump 400) |

**Approval:** Accepted by user, 2026-05-21. 6 round discussion (canvas
publish 거부 추적 → "고정된 버전 필요" → "프로젝트 버저닝" → semver →
"버전들 쭉 볼 수 있게" → 위치 = CanvasTabs 우측 → "진행합시다") 통해
lock.

**Verification:**
- 429 server pytest + 544 viewer vitest pass; tsc + mypy clean.
- App.tsx 406 LOC (ceiling 410 유지).
- viewer build 성공.

**Spec impact:**
- 새 endpoint `POST /api/projects/{project_id}/publish` (Body:
  `{"bump": "major"|"minor"|"patch", "message"?: str}` → 201
  `{from_version, to_version, tag}`).
- `ProjectDoc` JSON 에 `blueprint_version` 키 추가 (back-compat 기본값).
- UI: "Mark session…" 버튼 사라짐, "📤 설계도 발행 ▾" 으로 대체.
  Header 에 blueprint version 배지 등장.

**Cross-refs:**
- D-2026-05-13-J / D-2026-05-13-O — per-canvas publish 거부 + per-node
  결정. 이 entry 가 *그 위 단위* (project) 를 추가 — 거부와 충돌 ✗,
  보완.
- D-2026-05-19-D — Symbol 개념 (cross-canvas master). 프로젝트 발행
  은 *모든 Symbol + 사용처* 의 정합 snapshot.
- `[[project_plot_blueprint_versioning]]` (memory) — 결정 + UX flow.

---

### D-2026-05-21-C — Snapshot view (read-only "view at tag") (v0.24.14)

**Context:** D-2026-05-21-B 으로 *설계도 발행* 도입 후 사용자 질문:
*"버전들 쭉 탐색하고 그 버전 볼 수 있는 기능은요?"* → grep 결과
사이드바에 *목록* 만 있고 *시점 보기* 코드 0줄임을 확인. 사용자 명시:
*"구현하고 다음 세션에서는 서비스 캔버스 작업만할거니까"* — 이번 세션
끝나기 전에 구현.

**Decision:** 사이드바 git tag 행을 *클릭* 하면 그 시점의 캔버스 상태를
read-only 로 뷰. 작업 본진 (live cache) 은 그대로, 별도 snapshot
cache 로 swap. 편집 비활성. 헤더에 amber 배너 + "✕ 나가기" 버튼.

**Implementation:**

| File | 변화 |
|---|---|
| `mashbill/git_store.py::read_file_at_tag()` | `git show <tag>:<path>` 래퍼. working tree 안 건드림. |
| `mashbill/api_endpoints.py::project_at_tag_endpoint()` | `GET /api/projects/{id}/at-tag/{tag}` — project + 모든 canvases 묶음 반환 |
| `mashbill/http_app.py` | route 등록 |
| `viewer/src/api.ts::getProjectAtTag()` | 클라이언트 |
| `viewer/src/hooks/useSnapshotView.ts` | 신규 hook — viewingTag + snapshotCache + enter/exit actions |
| `viewer/src/App.tsx` | hook 사용 + cache swap + applyEdit 가드 (`viewingTag ? noop : liveApplyEdit`) |
| `viewer/src/shell/Header.tsx` | amber 배너 + 나가기 버튼 |
| `viewer/src/canvases/SketchSidebar.tsx` | 태그 행 클릭 핸들러 + viewed 표시 (👁 + amber tint) |
| `viewer/src/i18n/locales/{en,ko}.json` | `snapshot.{viewing,exit}` + `sidebar.viewTag` |
| `tests/test_api_endpoints.py` | 2 새 테스트 (snapshot 반환 / 404 unknown tag) |
| `viewer/tests/structural-guards.test.tsx` | App.tsx 천장 410 → 425 (이 결정에 의한 cache swap + applyEdit guard 배선) |

**Why not modify useCanvasPersist directly?** Edit 가드를 App 경계에서
하는 게 더 작은 변경 — 기존 hook 의 contract 안 건드림. snapshot mode
는 *전적으로* App-level concern (= "이 화면 뭐 보여줄지" + "edit 처리
할지").

**Why `git show` not `git checkout`?** Working tree 보존. 동시에 여러
태그 볼 수 있는 길도 열어둠 (현재는 한 번에 1개만).

**Verification:**
- 431 server pytest + 544 viewer vitest pass. tsc + mypy + ruff clean.
- App.tsx 421 LOC (새 천장 425 안).
- 새 endpoint 검증: 태그 후 캔버스 mutate 해도 `/at-tag/<v>` 응답에는
  태그 시점 state 반환 (mutate 안 보임).

**Approval:** Accepted by user, 2026-05-21 — *"구현하고 다음 세션에서는
서비스 캔버스 작업만할거니까"*. 직전 5 round 토론 (직접 grep 확인 +
*"미구현한게 있다고?"* + *"발행을 안했다는거에요. 구현을 안했다는거에요?"*)
으로 명확화.

**Cross-refs:**
- D-2026-05-21-B (v0.24.13 — 발행 UX, 이 entry 가 *그 결과 보기* 를
  마저 채움)
- `git_store.py:7` 코멘트 *"future viewer UI"* 가 이 entry 로 실현됨.

---

### D-2026-05-24-A — Default node size 140×60 → 80×36 (v0.24.15)

**Context:** User opened the Services-side review in session 2026-05-24
*"이제 뭘하냐면 서비스 쪽 동작 리뷰하고 다듬을 거에요"* and immediately
flagged *"일단 노드 크기가 너무 크다"*. This is the second tightening
pass after D-2026-05-17-N (180×80 → 140×60) — Services / ServiceDetail
canvases pack more nodes into a smaller viewport than Foundation /
Actors, and 140×60 still wasted vertical space on hub-spoke layouts.

**Decision:**

1. **Default node size 140×60 → 80×36** in three places (same SSOT
   trio as D-2026-05-17-N):
   - `mashbill/models.py::BaseNodeFields.width / height` (Pydantic).
   - `viewer/src/canvases/sketch/constants.ts::DEFAULT_WIDTH / HEIGHT`.
   - `viewer/src/domain/BaseFields.ts::parseBaseFields` fallback.
2. **Auto-layout padding stays at 64** (set by D-2026-05-17-N). Padding
   is now ~1.8× the longer node dimension (was ~0.5×) — overlap risk
   strictly decreases.
3. **No migration.** Existing nodes keep their stored width / height in
   `canvas.json`; only new stencil-drop / pane-double-click / paste
   creates an 80×36 node. SSOT preserved.

**Why 80×36 specifically?** AskUserQuestion preview-compare 2026-05-24
offered 120×50 / 100×40 / 80×36. User chose 80×36 — the most aggressive
option (~66% area reduction from 140×60). Acknowledged trade-off: some
kinds (multi-word labels, long service titles) may need manual resize.
The default is what the user *starts* with; per-node resize is already
persisted (D-2026-05-17-N principle preserved).

**Files changed:**

| File | Change |
|---|---|
| `mashbill/models.py` | width / height defaults 140 / 60 → 80 / 36; comment block updated to reference D-2026-05-24-A |
| `viewer/src/canvases/sketch/constants.ts` | `DEFAULT_WIDTH = 80`, `DEFAULT_HEIGHT = 36`; comment updated |
| `viewer/src/domain/BaseFields.ts` | `parseBaseFields` fallback 140 / 60 → 80 / 36 |
| `viewer/tests/domain/base-fields.test.ts` | assertion 140 / 60 → 80 / 36 |
| `viewer/tests/domain/round-trip.test.ts` | spread width assertion 140 → 80 |

**Verification:**
- Server pytest 431 passed, mypy clean.
- Viewer vitest 544 passed, tsc clean.
- Browser: new node via stencil-drop on Foundation canvas renders at
  80×36 (per `mashbill-verifier` agent).

**Approval:** Accepted by user, 2026-05-24 — AskUserQuestion option
*"80×36"* selected directly.

**Cross-refs:**
- D-2026-05-17-N (v0.24.2 — prior reduction 180×80 → 140×60). This entry
  is its successor; both follow the same SSOT-trio update pattern.
- Phase B sibling work (Services-specific radial auto-layout) ships
  separately as v0.25.0 per plan
  `~/.claude/plans/linear-roaming-lynx.md` to keep this commit
  patch-scope and avoid the "cross-cutting bundle" anti-pattern
  ([D-2026-05-11-C](#d-2026-05-11-c)).

---

### D-2026-05-24-B — Services + ServiceDetail opt into auto-layout with new radial algorithm (v0.25.0)

**Context:** Same 2026-05-24 Services review session that filed
D-2026-05-24-A. After flagging the node-size issue, user asked
*"다른 캔버스에는 있는데 캔버스 정렬기능이 없다"* — Services /
ServiceDetail had no ⊞ button. The prior decision
[D-2026-05-18-B](#d-2026-05-18-b) had explicitly excluded those
canvases on the grounds that their hub-and-spoke topology does not
suit the directional-tree algorithm (Foundation / Actors use). User's
follow-up request was the *opposite* — give them an auto-layout button
**with an algorithm appropriate for their topology**.

**Decision:**

1. **Generalise the wrapper opt-in prop** from `enableAutoLayout:
   boolean` to `layoutAlgo: "tree" | "radial" | null`. Same default
   (null = no button); same isolation contract (per-wrapper opt-in);
   same `Cmd+Z` + positions-only invariants. Existing wrappers
   migrate:
   - `FoundationCanvas` → `layoutAlgo="tree"`
   - `ActorsCanvas` → `layoutAlgo="tree"`
   - `ServicesCanvas` → `layoutAlgo="radial"` (new)
   - `ServiceDetailCanvas` → `layoutAlgo="radial"` (new)
2. **New radial algorithm**
   ([`viewer/src/canvases/sketch/radialLayout.ts`](../viewer/src/canvases/sketch/radialLayout.ts)).
   Hub-and-spoke pattern:
   - Hub = synthetic project anchor (Services) or hidden root-service
     node (ServiceDetail). Picked by `useRadialLayout::pickHub` based
     on whether `projectAnchor` is set.
   - BFS from hub via undirected edges → ring level per node.
   - Within a ring: id-sorted, equal-angle slots, starting from the
     top (-π/2).
   - Radius accumulates: ring 1 = `hub_half + ring1_span/2 + gap`;
     ring k>1 adds `ring_k_span + gap`. Gap default 40 px (chosen to
     give an 80×36 default node its own width again between siblings
     on the inner ring per D-2026-05-24-A).
   - Orphan nodes (not reachable from hub) → grid below outermost
     ring, same shape as autoLayout.ts orphan fallback.
3. **Auto-layout-isolation test flipped** for Services / Detail. Tests
   that previously asserted `must NOT opt in` now assert `must opt in
   with radial`. Two new positions-only tests cover both radial
   wrappers (Services with anchor hub; ServiceDetail with hidden
   root-service hub).

**Why a new algorithm, not extend directional-tree?** The tree
algorithm relies on parent-side handle direction (T/R/B/L) — Services'
service-to-service relationships are bidirectional / many-to-many and
don't carry a meaningful "direction." Radial expresses centrality
(distance from hub = importance) which is the Services pattern.
ServiceDetail's category / step / rule / metric / content all hang off
*one* root service — also a clean radial fit.

**Why not Detail-only or Services-only?** AskUserQuestion 2026-05-24
preview-compare offered Services-only / Detail-only / both. User chose
both. Both canvases share the hub-and-spoke topology — splitting
adoption would be inconsistent.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/sketch/radialLayout.ts` | NEW — pure `computeRadialLayout` |
| `viewer/src/canvases/sketch/useRadialLayout.ts` | NEW — React bridge + `pickHub` |
| `viewer/src/canvases/SketchCanvas.tsx` | `enableAutoLayout: boolean` → `layoutAlgo: "tree" \| "radial" \| null`; dispatch `triggerLayout` based on algo |
| `viewer/src/canvases/{Foundation,Actors}Canvas.tsx` | `enableAutoLayout={true}` → `layoutAlgo="tree"` |
| `viewer/src/canvases/{Services,ServiceDetail}Canvas.tsx` | `layoutAlgo="radial"` added |
| `viewer/tests/radialLayout.test.ts` | NEW — 8 unit tests for the pure algo |
| `viewer/tests/auto-layout-isolation.test.tsx` | 2 "must NOT opt in" flipped to "must opt in"; 2 positions-only tests added for radial |
| `viewer/tests/SketchCanvas.regression.test.tsx` | comment / test name updated for the new prop |
| `docs/SPEC.md` | §Auto-layout rewritten — algo table + radial section |

**Verification:**
- Viewer vitest 560 passed (was 544 — +8 radial unit + 2 new radial
  positions-only tests + 6 misc adjustments).
- Server pytest 431 passed (unaffected — server has no layout code).
- tsc clean. SketchCanvas 448 LOC vs 450 ceiling.

**Approval:** Accepted by user, 2026-05-24 — AskUserQuestion option
*"Services 전용 algorithm 신규"* + *"ServicesCanvas + ServiceDetailCanvas 둘 다"*
selected directly.

**Cross-refs:**
- D-2026-05-13-L (Foundation-only opt-in, original isolation contract).
- D-2026-05-18-B (Actors opt-in extension — explicitly excluded
  Services with hub-spoke reasoning; this entry refutes that exclusion
  by supplying the missing algorithm).
- D-2026-05-24-A (Phase A sibling — default node size 80×36 — informs
  the radial `ringGap = 40` choice).

---

### D-2026-05-24-C — Services canvas reverts auto-layout opt-in; controls live in per-service modal (v0.25.1)

**Context:** Same-session immediate follow-up to D-2026-05-24-B
(shipped earlier in the same 2026-05-24 review session). After
v0.25.0 landed the radial ⊞ button on both `ServicesCanvas` and
`ServiceDetailCanvas`, user clarified the intent:

> *"서비스 상세 설계 캔버스는 모달로 따로 보여줘야해요. 컨트롤하는
> 것도 따로 보여줘야합니다. 메인 캔버스는 서비스에 대한 요약을
> 보여주는 것 뿐이에요."* + *"컨트롤하는것도 따로 해야지"*

The conceptual split:
- **Main `ServicesCanvas`** = summary view of all services. Read-y;
  no per-service editing controls live here. (Modal already exists
  for that, opened via service-node double-click — `ServiceDetailModal`
  has been around since v0.16.3.)
- **`ServiceDetailModal` + `ServiceDetailCanvas`** = per-service
  editing surface. *This* is where auto-layout and other per-service
  controls belong.

I had wired ⊞ on both in v0.25.0, which broke this split.

**Decision:**

1. **Revert** `ServicesCanvas` from `layoutAlgo="radial"` back to no
   opt-in. The ⊞ button no longer renders on the main Services canvas.
2. **Keep** `ServiceDetailCanvas` at `layoutAlgo="radial"`. The
   per-service modal continues to offer auto-layout.
3. **Retain** the `layoutAlgo` prop generalisation from
   D-2026-05-24-B — only the wrapper's *choice* changed. The radial
   algorithm code (`radialLayout.ts`, `useRadialLayout.ts`) stays
   live, used by `ServiceDetailCanvas`.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/ServicesCanvas.tsx` | removed `layoutAlgo="radial"` |
| `viewer/tests/auto-layout-isolation.test.tsx` | Services test flipped back to "must NOT opt in"; the Services positions-only test deleted (no button to click); ServiceDetail tests untouched |
| `docs/SPEC.md` | algo table updated (Services row → no opt-in); History extended with this entry |

**Why a same-day rollback?** Because the v0.25.0 wiring was
demonstrably wrong relative to the (now-explicit) Services-as-summary
intent. Honest rollback per the *"Same-day rollbacks are honest"* rule
in `mashbill/CLAUDE.md`. The radial *algorithm* is not the bug; the
*Services wrapper opting in* was.

**Why not also reconsider ServiceDetail?** User explicitly limited
the rollback to controls on the *main* canvas. The per-service modal
is exactly where these controls were said to belong.

**Verification:**
- Viewer vitest passes (Services no-button assertion + ServiceDetail
  button-present assertion both green).
- Server pytest unaffected.
- tsc clean.

**Approval:** Accepted by user, 2026-05-24 — *"컨트롤하는것도 따로
해야지"*.

**Cross-refs:**
- D-2026-05-24-B (v0.25.0 — the entry this rolls back, partially).
  That entry stays Accepted for the `ServiceDetailCanvas` half +
  `layoutAlgo` prop generalisation.
- v0.16.3 `ServiceDetailModal` extraction — the pre-existing modal
  surface this entry treats as the canonical home for per-service
  controls.

---

### D-2026-05-25-A — Directed edge model + `parent_id` removed (v0.26.0, BREAKING)

**Context:** Session 2026-05-25 Services-canvas review surfaced that
sub-nodes had no fold button. Diagnosis: fold was ``parent_id`` based,
but the user was thinking of nodes connected by an edge as "sub-nodes."
After multi-round discussion the model converged on:

- Edges carry a ``directed`` flag (two kinds: directed vs undirected).
- Drawing direction → ``from`` (source) and ``to`` (target).
- Directed edge **only** participates in hierarchy / fold derivation.

User then chose the **maximal-cleanup** path via AskUserQuestion:

1. ``parent_id`` **completely removed** (not coexistence). Directed
   edges become the sole hierarchy SSOT.
2. New edges default to **directed** (drag direction matters from the
   first stroke).
3. Ship as a **single v0.26.0** commit (no phased migration).

**Decision (executed):**

1. **Schema additions**:
   - ``SketchEdge.directed: bool = True`` (Pydantic + TS).
2. **Schema removals**:
   - ``BaseNodeFields.parent_id`` field removed from Pydantic.
   - ``BaseFieldsJson.parent_id`` / ``BaseFields.parent_id`` removed
     from TS.
   - All 15 entity classes (Actor / Service / Category / Content /
     CoreValue / Identity / IdentityRef / Metric / Mission /
     MissionRef / Project / Rule / Service / Step / ValueRef) drop
     ``parent_id`` declarations + ``toJson`` emission.
3. **Validators removed** (Pydantic):
   - ``CanvasDoc._parent_ids_are_valid`` (cycle / self-parent /
     orphan checks — obsolete).
   - ``_foundation_canvas_rules`` parent_id check for project nodes.
   - ``_services_canvas_rules`` (whole validator — was
     service-must-have-category + category-must-be-top-level).
   - ``_detail_canvas_rules`` composition-kind parent_id checks.
4. **Read-side migration**:
   - New ``folder_io._migrate_parent_id_to_directed_edges`` runs on
     every ``read_canvas``. For any node carrying a non-null
     ``parent_id``, removes the field and appends a directed edge
     ``parent → child`` (id ``e_migrated_{node_id}``). Idempotent —
     subsequent reads no-op. Also backfills ``directed=True`` on any
     pre-v0.26 edge that lacks the field (matches the new default).
5. **Edge rendering** (viewer):
   - ``edgeTransform.ts`` emits a React-Flow ``markerEnd:
     ArrowClosed`` only when ``edge.directed === true``. Colour
     matches the resolved stroke (value-flow recolouring stays
     consistent).
6. **Edge creation default** (viewer):
   - ``useFlowHandlers.handleConnect`` initialises new edges with
     ``directed: true``.
7. **Context menu** (viewer):
   - ``useContextMenus.openEdgeMenu`` gains a "Add direction" /
     "Remove direction" toggle entry as the first item.
8. **Fold refactor** (viewer):
   - ``useCollapsedTree`` signature gains ``edges: SketchEdge[]``.
     ``childIdsByParent`` is now built from directed edges instead
     of ``parent_id``. ``parentIdsByChild`` added; ancestor /
     descendant walks become BFS with visited-set cycle guard.
9. **Hierarchy helper** (viewer):
   - New pure module ``canvases/sketch/hierarchy.ts`` exposes
     ``parentIdOf`` / ``parentIdsOf`` / ``childIdsOf`` / ``hasParent``
     so consumers (Inspector, drag-and-drop, App.tsx drill context,
     etc.) express parent-child queries without reaching into Maps.
10. **Propagation walk** (server):
    - ``mashbill/propagation.py::walk_ancestors`` rewritten. Now
      walks incoming directed edges (``edge.target == current_id``)
      across all canvases; picks the lexicographically smallest
      source id for multi-parent determinism.
11. **MD publish** (server):
    - ``parent_id`` removed from the YAML frontmatter contract (was
      one of 7 keys; now 6).
12. **All viewer parent_id consumers refactored**:
    App.tsx (drill category lookup), inspectors/category /service
    (child count via outgoing directed edges), useNodesMemo (sort:
    nodes without incoming directed edge first), useNodeCreation
    (drops the field; nested drops materialise an explicit directed
    edge for *every* kind, not just actor/service), useDragAndDrop
    (sibling discovery via directed edges; coordinate system is now
    flat — no parent-local nesting), overlapNudge / SketchModals
    (parent-absolute walk simplified to identity), flow/autoLayout
    (parent_id-implicit edges removed; only explicit edges drive the
    dagre layout), ActorRefPicker (parent-chain label feature
    dropped — follow-up if missed).

**Files changed (high level):**

| Layer | Files (one-line summary) |
|---|---|
| Server schema | ``mashbill/models.py``: SketchEdge gains ``directed``; BaseNodeFields drops ``parent_id``; 4 validators removed |
| Server migration | ``mashbill/folder_io.py``: new ``_migrate_parent_id_to_directed_edges``; legacy ``_wrap_legacy_services_in_default_category`` removed |
| Server propagation | ``mashbill/propagation.py``: rewritten for directed-edge ancestor walk |
| Server md_publish | ``mashbill/md_publish.py``: ``parent_id`` removed from frontmatter |
| Server migrate.py (v0.1→v0.2) | drops parent_id arg from ``_v01_to_actor`` / ``_v01_to_service`` / ``_v01_to_composition`` |
| Client schema | ``viewer/src/types.ts``: SketchEdge gains ``directed``; ``viewer/src/domain/BaseFields.ts``: parent_id removed; 15 entity classes cleaned |
| Client domain helper | new ``viewer/src/domain/createBlankNode.ts`` drops parent_id from BlankNodeBase |
| Client edge render | ``viewer/src/canvases/sketch/edgeTransform.ts``: markerEnd for directed |
| Client edge create | ``viewer/src/canvases/sketch/useFlowHandlers.ts``: default directed=true |
| Client context menu | ``viewer/src/canvases/sketch/useContextMenus.ts``: toggle direction item |
| Client fold refactor | ``viewer/src/canvases/sketch/useCollapsedTree.ts``: edges-based |
| Client hierarchy helper | new ``viewer/src/canvases/sketch/hierarchy.ts`` |
| Client consumers | App.tsx, inspectors/{category,service}, useNodesMemo, useNodeCreation, useDragAndDrop, overlapNudge, SketchModals, ActorRefPicker, flow/autoLayout — all rewritten to use directed edges |
| Tests | test_schema_parity / test_canvas_doc / test_folder_io / test_dirty_tracking / test_propagation / test_migrate / test_md_publish + viewer base-fields / round-trip / inspectors — all updated |
| Docs | SPEC §Edges rewritten; CHANGELOG v0.26.0 + Removed/Added/Changed; this entry |
| Plugin | ``mashbill/.claude-plugin/plugin.json`` 0.25.1 → 0.26.0 |
| Structural guard | ``viewer/tests/structural-guards.test.tsx`` App.tsx ceiling 425 → 430 |

**Risk acknowledgement (kept honest):**

- ``parent_id`` was load-bearing across 152 occurrences in 32 files.
  This commit is large and rewrites domain invariants — the
  "behavior: 부분 완료 금지" rule means all of it had to land
  together. A future session may discover a missed consumer; the
  fallback is honest rollback (``git revert``) rather than partial
  patching.
- Domain enforcement that was previously schema-level (e.g. "service
  must have a category parent") now moves out of Pydantic into docs
  guidance. Users can construct technically-invalid canvases (e.g. a
  step with no incoming directed edge); they'll see no validation
  error, only a missing fold affordance. Acceptable trade-off per
  user direction (parent_id is gone; the model is intentionally
  permissive about hierarchy shape).
- ``ActorRefPicker``'s parent-chain label dropped temporarily — was
  a parent_id-only feature. Threading edges through the picker is a
  small follow-up if the omission becomes annoying.

**Verification:**
- Server pytest **433 passed**; mypy clean.
- Viewer vitest **562 passed**; tsc clean.
- Read-side migration tested via the existing folder_io / dirty
  tracking / propagation fixtures (all rebuilt to use directed
  edges directly; the migration path itself is exercised any time a
  pre-v0.26 fixture file is loaded).

**Approval:** Accepted by user, 2026-05-25 — AskUserQuestion options
*"parent_id 완전 폐기, directed edge 만 쓴다"* + *"directed (화살표
기본)"* + *"한 번에 (v0.26.0 통합 ship)"* selected directly.

**Cross-refs:**
- D-2026-05-20-… (none — last hierarchy work was the v0.15 reset
  D-2026-05-12-B which preserved ``parent_id``).
- D-2026-05-24-B (v0.25.0 radial layout — ``useRadialLayout`` already
  used directed edges; survives v0.26 unchanged).
- ``feedback_no_god_object`` memory — this entry is the dual of
  the v0.13 god-SketchNode purge: god *containment field* purge in
  favour of expressive edges.

---

### D-2026-05-25-B — Non-Symbol nodes default to rectangle shape (v0.26.1)

**Context:** Same session 2026-05-25 after v0.26.0 ship. User direction:

> *"캔버스에 앵커하고 심볼 빼고 다 사각형으로 노드를 만들죠"*

The two carve-outs reflect the v0.24.11 (D-2026-05-19-D) Symbol
concept ([[project_plot_symbol_concept]]) — Symbols are the
cross-canvas referenceable masters (mission / core_value / identity /
actor / sub-actor) whose visual identity carries domain meaning. The
project anchor is the synthetic centre node. Everything else
(category / service / actor_ref / mission_ref / value_ref /
identity_ref / metric / step / rule / content) is "consumer plane"
shape-wise — should read as a uniform rectangle so the canvas
emphasises *content* + *relationships*, not chrome.

**Decision:**

1. **Anchor stays circle.** ``ProjectNode.shape: Shape = "circle"``
   (already set, unchanged).
2. **Symbol kinds keep their current shape.** No edit to
   ``ActorNode`` (circle) / ``MissionNode`` / ``CoreValueNode`` /
   ``IdentityNode`` (rounded). These continue to inherit
   ``BaseNodeFields.shape: Shape = "rounded"``.
3. **Every other kind = rectangle** at creation time. The change
   lands in the stencil presets, not the Pydantic defaults, so:
   - New nodes from drag-and-drop / picker / preset → rectangle.
   - Existing nodes keep their stored shape (SSOT, per the
     D-2026-05-17-N pattern).
   - AI / MCP-driven node creation that omits ``shape`` still
     inherits the Pydantic default ("rounded") — acceptable since
     MCP node creation already specifies typed-field defaults; if
     it later wants rectangle parity, set ``shape="rectangle"``
     explicitly or follow up with a D entry that flips the base.

**Files changed:**

| File | Change |
|---|---|
| ``viewer/src/canvases/SketchStencil.tsx`` | 9 preset shapes: ``TOP_LEVEL_CATEGORY`` / ``SERVICE_INSIDE_CATEGORY`` / metric / ``ACTOR_REF`` / ``MISSION_REF`` / ``VALUE_REF`` / ``IDENTITY_REF`` + 4 picker-driven helpers (``actorRefPresetFor`` / ``missionRefPresetFor`` / ``valueRefPresetFor`` / ``identityRefPresetFor``) — all moved to ``shape: "rectangle"``. Step was already ``rectangle``. |
| ``mashbill/folder_io.py`` | 2 ``ActorRefNode`` auto-seeds in ``ensure_service_detail`` flipped from ``shape="ellipse"`` to ``shape="rectangle"`` for parity with the stencil. |
| ``docs/SPEC.md`` | Optional: Novel Edges section already describes user-drawn nature; no spec change for shape (preset detail). |

**Why stencil-only (not Pydantic base)?** Two reasons:
1. Stencil is the single funnel for *user-driven* creation; the
   Pydantic default fires only for raw / MCP-driven creates. Limiting
   the change to the stencil keeps the blast radius small.
2. Symbol kinds would otherwise need explicit ``shape`` defaults to
   override the new base — three more model edits. Skipping that
   keeps the change to ~10 line edits in one preset file + 2 in the
   server.

**Verification:**
- Server pytest 433 passed; mypy clean.
- Viewer vitest 562 passed; tsc clean.
- Browser verify deferred to user (Playwright MCP offline this
  session; change affects new-node visuals only — existing canvas
  unchanged).

**Approval:** Accepted by user, 2026-05-25 — direct quote
*"캔버스에 앵커하고 심볼 빼고 다 사각형으로 노드를 만들죠"*.

**Cross-refs:**
- D-2026-05-19-D ([[project_plot_symbol_concept]]) — Symbol concept
  formalised; this entry honours the producer/consumer plane split
  in visual language.
- D-2026-05-17-N — same SSOT pattern (new-node default only;
  existing stored values preserved).

---

### D-2026-05-25-C — ServicesCanvas opts back into radial auto-layout (v0.26.2, reverts D-2026-05-24-C)

**Context:** Same session 2026-05-25 next round. User direction:

> *"서비스 메인 캔버스에 정렬기능 빠져있는건 여전하고."*

This refers to the same-day rollback in
[D-2026-05-24-C](#d-2026-05-24-c--services-canvas-reverts-auto-layout-opt-in-controls-live-in-per-service-modal-v0251)
which removed the ⊞ button from `ServicesCanvas` on the grounds that
the main Services canvas was a "summary view" + controls belonged in
the per-service modal. In practice the missing affordance was felt as
a regression — the user wanted to redo the same `Services` clean-up
work flow that Foundation / Actors enjoy.

**Decision:**

1. **Revert D-2026-05-24-C.** `ServicesCanvas` regains
   `layoutAlgo="radial"` (re-uses the algorithm shipped in v0.25.0
   per D-2026-05-24-B; no new code).
2. `ServiceDetailCanvas` continues to use radial with the hidden
   root-service as hub (unchanged).
3. The "summary canvas" framing from D-2026-05-24-C is dropped from
   the spec; the main canvas now has the same auto-layout
   affordance as every other canvas.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/ServicesCanvas.tsx` | re-added `layoutAlgo="radial"` |
| `viewer/tests/auto-layout-isolation.test.tsx` | ServicesCanvas test flipped back to "must opt in"; positions-only test restored; header doc updated to record the D-2026-05-25-C revert |
| `docs/SPEC.md` | algo table — Services row back to `"radial"`; History extended with this entry |

**Why a same-session re-revert?** The D-2026-05-24-C decision was a
same-day decision based on a still-forming mental model of the
"main canvas vs modal" split. Within the same session the user
exercised the resulting UX and found the missing button was the
bigger problem. Honest re-revert per *"Same-day rollbacks are
honest"* (mashbill/CLAUDE.md). The radial algorithm code (shipped in
v0.25.0) is unchanged.

**Verification:**
- Viewer vitest 562+ passed (auto-layout-isolation 9 tests green).
- Server pytest unaffected.
- tsc clean.

**Approval:** Accepted by user, 2026-05-25 — AskUserQuestion option
*"네, 다시 추가해주세요"* selected directly after the user direction
above.

**Cross-refs:**
- D-2026-05-24-B (Services + ServiceDetail radial opt-in — original).
- D-2026-05-24-C (the same-day rollback this entry reverses).
- D-2026-05-13-L (Foundation-only opt-in, original isolation contract).

---

### D-2026-05-25-D — Radial fan-out: ring k>=2 follows parent angle (v0.26.3)

**Context:** Same session 2026-05-25, after v0.26.2 restored the
auto-layout button on Services. User exercised it on banas-imported
(category 1 + service 1 + anchor) and reported:

> *"서비스 캔버스 정렬이 제대로 안되는데요? 왜 앵커 위로 다
> 정렬해버리죠?"*

Diagnosis: the v0.25.0 radial algorithm started every ring at -π/2
(top) and spread members at 2π/N per slot. When a ring has only 1-2
members, all members land at or near the top. For a chain of
length-1 spokes (anchor → category → service), every node sits
directly above the anchor — visually "all stacked north."

**Decision:**

Two-pass placement:
1. **Ring 1** keeps the existing equal-distribution (2π/N starting
   from top). This is correct: the hub's direct neighbours have no
   parent angle to inherit, so even distribution around the circle
   is the only sensible choice.
2. **Ring k>=2** members are grouped by their BFS parent and fan
   *around the parent's angle*, not around the canvas top. Fan
   width narrows with depth: π/(k+1) — π/3 for ring 2, π/4 for
   ring 3, etc. Behaviour:
   - Single child → same angle as parent (chains follow one
     radial line outward).
   - Multiple children → evenly spread within the fan, centred on
     parent's angle.

**Why fan narrows with depth?** Without it, deeper rings inherit
the parent's spread plus their own → siblings from different
parents collide. Narrowing creates a tree-like outward spread that
reads cleanly even with branchy graphs.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/sketch/radialLayout.ts` | BFS now records ``parentOf``; placement split into two passes (angle assignment then radius accumulation); ring k>=2 fans around parent angle |
| `docs/SPEC.md` | §Auto-layout / radial algorithm section updated to describe the new two-pass placement |

**Verification:**
- Viewer vitest 563 passed; the existing 8 ``radialLayout`` unit
  tests cover distance-from-hub assertions which remain true under
  the new angle scheme; the multi-hop test (chain `hub → a → b`)
  still confirms `b` is farther than `a`. Determinism test still
  passes — same input produces same output.
- tsc clean.

**Approval:** Accepted by user, 2026-05-25 — direct request *"진행할까요?"* / *"네"* after I described the (A) option.

**Cross-refs:**
- D-2026-05-24-B (radial algorithm — original).
- D-2026-05-25-C (Services canvas opt-in restored — the change that
  made this complaint surface in the first place).

---

### D-2026-05-26-A — Services + ServiceDetail switch from radial to tree auto-layout (v0.27.0)

**Context:** Session 2026-05-26. After v0.26.3 (D-2026-05-25-D)
shipped the fan-out fix that was meant to stop length-1 spoke chains
from collapsing onto a single vertical line, the user opened the
banas-imported project and observed the same problem still present:
anchor (Banas) → category (Auth) → service (Login) still all stacked
above the anchor. User direction:

> *"정렬은 액터 캔버스 참고하쇼."*

**Diagnosis:** Even with v0.26.3's "ring k>=2 fans around the parent's
angle" change, a chain where every parent has *exactly one child*
degenerates: each child inherits its parent's single angle, and ring 1
itself starts at -π/2 (top) when there is only one member. So a chain
of length-1 spokes follows one straight line from the anchor at -π/2
outward → visually identical to the v0.26.2 bug. Fan width helps only
when a parent has multiple children. Actor / Foundation canvases use
the **tree** algorithm (`autoLayout.ts`): children fan out in the
direction (T/R/B/L) of the parent-side handle the user drew on the
edge — so user-drawn intent drives placement rather than ring-radius
math. That algorithm matches the user's preferred reading and never
exhibits the chain-collapse problem.

**Decision:**

1. `ServicesCanvas.tsx` and `ServiceDetailCanvas.tsx` both flip
   `layoutAlgo` from `"radial"` to `"tree"`. The radial code stays in
   the tree (still imported by `SketchCanvas`) but is not currently
   wired to any wrapper; it can be re-introduced for a future canvas
   that genuinely benefits from rings.
2. `useAutoLayout` hub selection extended to fall back to the
   root-service node (`kind === "service" && is_root === true`) when
   `projectAnchor` is null. ServiceDetail injects no anchor, so
   without this fallback the tree algorithm would early-return and
   the button would silently do nothing. The fallback mirrors
   `useRadialLayout.pickHub` exactly so the two algorithms share the
   same hub semantics.
3. `auto-layout-isolation.test.tsx` updated: the Services + ServiceDetail
   `must opt in` assertions remain (still render the button); the
   positions-only assertions exercise the tree algorithm now. The
   ServiceDetail positions-only test seeds a `svc-1` root-service +
   one ring-1 spoke (kept verbatim from the v0.26.2 radial test, so
   the only thing that changes is which algorithm runs against it).

**Why keep radial code instead of deleting?** Per CLAUDE.md "AHA —
avoid hasty deletion." `radialLayout.ts` is a working pure module
with 8 unit tests; if a future canvas (e.g. a per-actor capability
radar) reads as rings rather than as a directional tree, we'll want
the code back. Cost of leaving it is minimal — one extra hook call
that returns a callback that no wrapper currently invokes.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/ServicesCanvas.tsx` | `layoutAlgo="radial"` → `layoutAlgo="tree"` |
| `viewer/src/canvases/ServiceDetailCanvas.tsx` | `layoutAlgo="radial"` → `layoutAlgo="tree"` |
| `viewer/src/canvases/sketch/useAutoLayout.ts` | hub selection extended; `pickAnchor` helper falls back to root-service node when no `projectAnchor` (mirrors `useRadialLayout.pickHub`) |
| `viewer/tests/auto-layout-isolation.test.tsx` | Services + ServiceDetail positions-only tests now run against the tree algorithm; opt-in assertions updated |
| `docs/SPEC.md` | algo table — Services + ServiceDetail rows flipped to `"tree"`; tree-algorithm description extended to mention the root-service hub fallback; History extended with this entry |

**Verification:**
- Viewer vitest 563 passed (auto-layout-isolation 9 tests green).
- tsc clean.
- Browser: anchor (Banas) → Auth → Login now lays out as a clean
  left-to-right tree on the Services canvas after clicking ⊞.

**Approval:** Accepted by user, 2026-05-26 — direct request *"정렬은
액터 캔버스 참고하쇼"* selected the tree algorithm by reference.

**Cross-refs:**
- D-2026-05-24-B (radial algorithm — original opt-in for Services / ServiceDetail).
- D-2026-05-25-D (radial fan-out attempt — insufficient for length-1 chains).
- D-2026-05-13-L (Foundation-only opt-in — original tree algorithm).
- D-2026-05-18-B (Actors opt-in to tree — the reference canvas).

---

### D-2026-05-26-B — ServiceDetail modal coexists with the sidebar (v0.27.0)

**Context:** Same session 2026-05-26. User opened the Login service
modal on banas-imported and reported:

> *"서비스디테일 캔버스에서 뭘 할 수가 없어요. 여기 액터도 있고
> 해야하는데 그게 없네요? 설명도 넣고 해야하는데 말이죠?"*

**Diagnosis:** Stencil functionality is intact — `SketchStencil.tsx`'s
`service_detail` branch renders Composition (metric / step) + Actor
refs (one per master) + Mission / Value / Identity refs (one per
master). But the modal was mounted at the app root with
`fixed inset-0 z-40` + an inner panel sized at `92vw × 90vh`. That
covered the entire viewport including the left sidebar where every
draggable preset lives. Stencil labels were visible only as the
left-edge slivers that peeked past the inner panel — visually
"nothing there." User's mental model ("ServiceDetail canvas has no
controls") was a faithful reading of what was actually on screen.

**Decision:**

1. Modal mount location moves from the app root to inside the
   `<div>` that wraps the active canvas (the same container that
   already holds `<Loading>` / `<ErrorPanel>` / `<EmptyState>` /
   `<Canvas>`). That `<div>` gets `relative` so absolute positioning
   resolves to its box.
2. `ServiceDetailModal`'s root switches from `fixed inset-0` to
   `absolute inset-0`. Inner panel sizing changes from `h-[90vh]
   w-[92vw] max-w-[1600px]` (viewport-relative) to
   `h-[92%] w-[94%] max-w-[1600px]` (parent-relative), so the modal
   fills its new container instead of the viewport.
3. ESC + backdrop-click + × button close paths unchanged. The ESC
   listener stays a `window` keydown — focus is inside the modal so
   this still works.
4. Sidebar is now fully usable while the modal is open. Drag from
   sidebar onto canvas inside the modal works because the drag
   payload is JSON in the dataTransfer (not DOM-dependent), and the
   drop target (`SketchCanvas`'s root) is the modal's child.

**Why not just raise the sidebar z-index above the modal?** Would
have left the modal backdrop visually broken at the sidebar edge,
and the modal would still nominally "own" the whole viewport for
the purposes of ESC focus / accessibility tree. Moving the mount
point is the structural fix — the modal *correctly* lives inside the
canvas region because that's the only region it modifies.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/App.tsx` | modal mount block relocated from root into the canvas `<div>`; that `<div>` gets `relative` |
| `viewer/src/shell/ServiceDetailModal.tsx` | `fixed` → `absolute`; inner panel sizing from viewport units to parent percent |
| `docs/SPEC.md` | History extended with this entry |

**Verification:**
- Viewer vitest 563 passed.
- tsc clean.
- Browser: ServiceDetail modal opens with sidebar visible; COMPOSITION
  (Metric / Step), ACTORS, MISSIONS, CORE VALUES sections all
  draggable onto the modal canvas. ESC / backdrop / × all close.

**Approval:** Accepted by user, 2026-05-26 — direct approval of the
two-part patch (this + D-2026-05-26-A) via *"네 둘다 진행"*.

**Cross-refs:**
- D-2026-05-26-A (sibling fix in the same session for the same canvas).

---

### D-2026-05-26-C — ServiceDetail = user-authored interaction graph (v0.27.1)

**Context:** Same session 2026-05-26. After shipping the v0.27.0
patch (modal mount relocated; layoutAlgo flipped to tree), the user
reframed the canvas itself:

> *"아니 인터렉션 그래프인데 사용자가 만들 수 있어야해요. 이해?
> 사용자가 그릴수 있어야한다구요. 노드 추가하고 선 이어서 그리고 등등"*

This consolidates several earlier signals (memory:
project_plot_definition_of_service, project_plot_philosophy P10,
project_plot_state_transitions_open) into one decision: **ServiceDetail
is not a constrained "fill-in-the-spec" surface, it is a free
interaction graph the user authors.**

**Decision:**

1. **Identity**: ServiceDetail is the canvas where the user expresses
   "what happens inside this service" as an interaction graph — actors,
   the things they do with / to each other, what value flows, and
   what foundation (mission / value / identity) those interactions
   serve. The system *does not* prescribe a meaning model.
2. **No new kinds shipped this session.** YAGNI. The user can label
   any existing kind (`actor_ref`, `mission_ref`, `value_ref`,
   `identity_ref`, `step`, `metric`) with their own interpretation.
   `interaction` / `value_token` kinds remain **OPEN** — re-evaluate
   only after enough usage that a pattern earns dedicated chrome.
3. **SPEC.md gets a new top-level `# ServiceDetail` section** (was
   previously absent — Phase 1 Explore agent confirmed SPEC.md L4
   "Services / Service-Detail follow in later expansions"). That
   section pins this identity decision so the next session reads it
   on session-start.
4. **Edge model (`action_verb` / `value_form`)** is the load-bearing
   mechanism for "interaction" semantics. UI for editing those fields
   is a follow-up — out of scope here.

**Why no new kind?** The Novel philosophy line "the user controls
every line, every position, every colour" (PHILOSOPHY P10) and the
"패턴 2회 이상 반복 시 추상화" rule both push against premature
abstraction. Three different services authored without a felt need
for a dedicated `interaction` kind = the user is already comfortable
re-labelling. If at six services the user keeps typing the same
verbs ("publishes", "subscribes", "pays"), revisit then.

**Files changed:**

| File | Change |
|---|---|
| `docs/SPEC.md` | new top-level `# ServiceDetail` section (identity, stencil, modal structure, auto-layout, edges, open questions) |
| `docs/DECISIONS.md` | this entry + D-2026-05-26-D |

**Verification:**
- No runtime change in this entry — pure identity / SPEC pin.
- Pair-verified with D-2026-05-26-D (modal self-containment) which
  *is* the runtime change supporting this identity.

**Approval:** Accepted by user, 2026-05-26 — direct quote captured
above + plan approval via ExitPlanMode.

**Cross-refs:**
- D-2026-05-26-D (sibling decision: modal self-containment that gives
  the user the room to actually author this graph).
- D-2026-05-26-A (tree layout that makes the authored graph readable).
- PHILOSOPHY.md P10 (user controls every line).
- Open: state/transitions question (D-2026-05-19-B) — this decision
  *does not* resolve it; user-authored edges may sometimes mean
  "transition" but the model still has no explicit transition kind.

---

### D-2026-05-26-D — ServiceDetail modal is self-contained (v0.27.1)

**Context:** Same session 2026-05-26. The v0.27.0 patch relocated
the modal mount from the app root into the canvas container so the
main sidebar would remain *visible*. User exercised it and reported:

> *"동작이 자연스럽지 않음. 디테일 서비스 캔버스 컨트롤은 디테일
> 서비스 컨트롤 모달 안에서 다 이뤄져야합니다."*

**Diagnosis:** v0.27.0's structure shared one sidebar between two
contexts (main Services canvas + modal-mounted ServiceDetail
canvas) via the `stencilCanvas={... ? "service_detail" : activeTab}`
swap in App.tsx. The modal occupied the canvas region while the
sidebar continued to render service_detail-specific stencil — a
split-personality layout where neither context owns its full chrome.
User-felt verdict: "controls for the detail modal belong inside the
detail modal."

**Decision:**

1. **Modal owns its own stencil column.** New shell component
   `viewer/src/shell/ServiceDetailStencilPanel.tsx` (≤ 42 LOC)
   renders `<SketchStencil canvas="service_detail" />` inside a
   `w-56` aside. Same width / chrome as the main `SketchSidebar`'s
   stencil region so the two read as the same component family.
2. **`ServiceDetailModal` body becomes a 2-column flex row.** New
   `stencilSlot: ReactNode` prop; body =
   `<div className="flex flex-1 overflow-hidden">{stencilSlot}<div className="relative flex-1">{children}</div></div>`.
3. **App.tsx removes the stencil swap.** `stencilCanvas={activeTab}`
   always — the main sidebar never carries `service_detail` stencil.
4. **`ServiceDetailModal`'s mount location is unchanged from
   v0.27.0** (canvas container, `absolute inset-0`). The earlier
   D-2026-05-26-B is preserved; this decision is the natural
   completion of it, not a revert.

**Why a new component instead of inlining?** Two reasons:
(a) `ServiceDetailModal.tsx` would have ballooned past its
implicit shell-component LOC budget (already ~90 LOC after the
2-column layout). (b) The stencil panel has its own concern
(drag sources for the detail context) distinct from the modal
chrome (header / overlay / close handling), so SoC.

**Why keep main sidebar visible behind the backdrop?** The user
explicitly approved this in the same session ("그대로 보이는데
모달의 크기가 화면을 다 덮겠죠?"). The modal's `bg-slate-900/40`
backdrop visually mutes the main sidebar so there's no confusion
about which surface is active.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/shell/ServiceDetailStencilPanel.tsx` | new component (42 LOC) — `w-56` aside wrapping `<SketchStencil canvas="service_detail" />` |
| `viewer/src/shell/ServiceDetailModal.tsx` | new `stencilSlot: ReactNode` prop; body becomes 2-column flex |
| `viewer/src/App.tsx` | `stencilCanvas` swap removed (`activeTab` always); modal mount passes `stencilSlot={<ServiceDetailStencilPanel ... />}` |
| `docs/SPEC.md` | new `# ServiceDetail` section pins the modal structure |
| `docs/DECISIONS.md` | this entry + D-2026-05-26-C |

**Verification:**
- Viewer vitest 563 passed; tsc clean.
- Browser:
  - Services tab — main sidebar shows ONLY Services stencil (Category,
    Service); no ServiceDetail sections leak through.
  - Login double-click opens the modal — modal's left column shows
    the full service_detail stencil (COMPOSITION / ACTORS / MISSIONS
    / CORE VALUES / IDENTITY ASPECTS).
  - ESC closes the modal — Services canvas still renders Banas → Auth
    → Login intact (no v0.27.0 regression "싹다 사라짐").
- LOC: App.tsx 425 / 430 ceiling; ServiceDetailModal.tsx 92 LOC;
  ServiceDetailStencilPanel.tsx 42 LOC.

**Approval:** Accepted by user, 2026-05-26 — *"구조 제대로 잡아보세요"*
+ plan approval via ExitPlanMode + AskUserQuestion confirmations on
layout (`w-56` fixed) and main sidebar handling ("그대로 보이는데
모달의 크기가 화면을 다 덮겠죠").

**Cross-refs:**
- D-2026-05-26-C (sibling decision: the identity that makes
  self-containment the right structure).
- D-2026-05-26-B (modal mount relocation — preserved, completed by
  this entry).
- D-2026-05-26-A (tree layout enabling readable authored graphs).

---

### D-2026-05-26-E — Dynamic ref stencil items show master name (v0.27.2)

**Context:** After D-2026-05-26-D shipped the modal-internal
stencil column, the user opened the ServiceDetail modal on
banas-imported and immediately spotted:

> *"왜 심볼이 제대로 안나오는거죠?"*

Diagnosis: the ServiceDetail modal stencil rendered every actor
ref as "Actor (ref)" (7 indistinguishable rows), every core value
ref as "Core value (ref)" (5 rows), and the mission ref as just
"Mission" — the real master names (Hero / Fan / Bartender / 관용
/ 지지 / etc.) never reached the screen even though they were
present in `availableActors` / etc. on the `App.tsx` side.

Root cause: `SketchStencil.tsx::StencilItem` resolved the label
via

```js
const labelKey = preset.labelI18nKey ?? (preset.kind ? `kind.${preset.kind}` : "");
const label = labelKey ? t(labelKey, { defaultValue: preset.labelHint }) : preset.labelHint;
```

For dynamic ref presets (`actor-ref:${a.id}`, `mission-ref:${m.id}`,
…) the `labelI18nKey` is undefined and `kind` is set, so the
resolver fell through to `kind.actor_ref` → translates to "Actor
(ref)" / "액터 (참조)". The `labelHint` (which already carries
`master.label || master.id`) became unreachable. The pre-existing
comment on the resolver said *"e.g. dynamic refs that use the
master's label directly"* — the intent was correct; the
implementation was not.

**Decision:**

1. Extend `StencilPreset.labelI18nKey` from `string | undefined` to
   `string | null | undefined`. `null` is the explicit "skip i18n,
   labelHint is the SSOT" sentinel.
2. Each of the four dynamic ref preset factories
   (`actorRefPresetFor`, `missionRefPresetFor`, `valueRefPresetFor`,
   `identityRefPresetFor`) passes `labelI18nKey: null`.
3. `StencilItem` resolver becomes:
   ```js
   const labelKey =
     preset.labelI18nKey === null
       ? ""
       : (preset.labelI18nKey ?? (preset.kind ? `kind.${preset.kind}` : ""));
   ```
   `labelKey === ""` skips translation; `labelHint` wins.
4. Static presets (TOP_LEVEL_ACTOR, CORE_MISSION, CORE_VALUE, …)
   are unaffected — they have undefined `labelI18nKey` and a `kind`,
   so the existing `kind.${kind}` path still applies.

**Why a sentinel instead of, e.g., a `useMasterLabel: boolean`?**
A boolean flag would duplicate the information already implied by
"labelI18nKey explicitly says 'no i18n key'". Three-state nullable
field is the minimum surface area for the same semantics.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/SketchStencil.tsx` | `labelI18nKey` type widened to nullable; resolver branches on `=== null`; 4 dynamic ref factories pass `labelI18nKey: null` |

**Verification:**
- tsc clean; viewer vitest 563 passed.
- Browser: ServiceDetail modal stencil on banas-imported renders
  Admin / Bana / Hero / Fan / Bartender / 3rd party / 미용사 (Actors
  section), Mission, 관용 (Tolerance) / 지지 (Support) / 유머 /
  공감 / 다양성, Tone & Manner — every preset shows its master's
  real name.

**Approval:** Accepted by user, 2026-05-26 — direct bug report
*"왜 심볼이 제대로 안나오는거죠?"*; fix shipped same session.

**Cross-refs:**
- D-2026-05-26-D (modal self-containment that surfaced the bug).
- v0.14.11 (original `labelI18nKey` introduction with the comment
  that described the now-implemented behaviour).

---

### D-2026-05-26-F — ServiceDetail modal traps interaction via `inert` (v0.27.2)

**Context:** Same session 2026-05-26. User reported:

> *"서비스 디테일 모달 뜰 때 다른거 동작안되게 해야죠."*

In v0.27.1 the modal was mounted inside the canvas container
(D-2026-05-26-B) with `absolute inset-0` covering only the canvas
region. The header / tab bar / main sidebar (PROJECTS list, SESSION
TAGS, Services stencil, LanguageToggle, Help button, project
inspector, etc.) all remained click-reachable + keyboard-reachable
while the modal was up. A misclick on the sidebar could change
projects or canvas tabs *behind* the open modal.

**Decision:**

1. **Mount the modal as a sibling of the main app `<div>`, not
   inside it.** This re-locates the modal one level above where
   D-2026-05-26-B placed it (the v0.27.0 → v0.27.1 mount inside the
   canvas container was a valid stop along the way; this is the
   correction).
2. **Modal returns to `fixed inset-0`** (was `absolute inset-0`).
   The inner panel returns to `h-[92vh] w-[94vw]` (was parent-%).
3. **Root app `<div>` carries the HTML `inert` attribute whenever
   `modalOpen` is true.** `inert` is the standard a11y primitive
   for "this subtree is interaction-disabled": clicks bubble nowhere,
   focus skips the subtree, keyboard events do not reach it,
   ARIA/screen readers honour it. The modal sits OUTSIDE the inert
   subtree so it remains fully interactive.
4. **No focus-trap library, no custom keyboard handlers, no
   pointer-events CSS hack.** `inert` is one HTML attribute and
   does the entire job in one place.

**Why move the mount back up?** D-2026-05-26-B moved the modal
*into* the canvas container so the sidebar would stay visible (the
v0.26.x `fixed inset-0` covered it). With v0.27.1's self-contained
stencil column the modal no longer needs the outer sidebar for
its controls, so the v0.26.x containment motivation is moot. The
honest framing: D-2026-05-26-B / D were transitional decisions
between "no self-contained modal" and "self-contained modal with
hard interaction boundary"; this entry completes the arc.

**Why `inert` instead of pointer-events / focus-trap / custom CSS?**
- `pointer-events: none` only blocks pointer; keyboard + focus
  still leak through.
- A focus-trap library (e.g. focus-trap-react) adds a dependency
  and only handles focus, not pointer.
- `inert` has been baseline-supported across Chrome / Safari /
  Firefox since 2023 — Novel's target browsers all support it.
- The implementation is literally one conditional attribute:
  ```jsx
  <div {...(modalOpen ? { inert: "" } : {})}>
  ```

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/App.tsx` | `modalOpen` derived; root `<div>` carries `inert` when true; modal mount block moved from inside canvas container to root-sibling; wrapping fragment added |
| `viewer/src/shell/ServiceDetailModal.tsx` | `absolute` → `fixed`; inner panel size `h-[92%] w-[94%]` → `h-[92vh] w-[94vw]` (viewport-relative again) |

**Verification:**
- tsc clean; viewer vitest 563 passed.
- Browser:
  - Open Login modal — `document.querySelector('div.flex.h-screen').hasAttribute('inert')` returns `true`.
  - Try to click main sidebar item ("Banas v0.13" project switch) — no effect.
  - Try to press the Actors tab — no effect.
  - ESC closes modal — inert removed; main app fully interactive again; Services canvas (Banas → Auth → Login) intact.

**Approval:** Accepted by user, 2026-05-26 — direct demand quoted
above.

**Cross-refs:**
- D-2026-05-26-B (modal mount moved into canvas container —
  superseded by this entry).
- D-2026-05-26-D (self-contained modal stencil — load-bearing
  prerequisite; without it the modal would lose access to its
  drag sources when the outer sidebar becomes inert).
- D-2026-05-26-E (sibling bug fix in the same patch).

---

### D-2026-05-26-G — ServiceDetail root-service is the design subject, not hidden (v0.27.3)

**Context:** Same session 2026-05-26. After the seeded banas-imported
demo graph (D-2026-05-26-C / E / F session work), the user clicked
the `⊞` auto-layout button on the ServiceDetail canvas and reported:

> *"근데 내가 정렬을 누루니까 다 사라지는데?"*

Diagnosis: `useAutoLayout`'s `pickAnchor` selected the canvas's
hidden root-service node as the BFS root. Since the seeded demo
graph (15 nodes, 21 edges) did not connect any node to the
root-service, BFS reached 1 node (root only) and the other 14 fell
to the orphan grid fallback, parked off-screen to the right of the
hidden root. fitView, seeing only the lone root node, zoomed into
the modal and hid every other node out-of-frame.

User reframed the design intent:

> *"서비스를 디테일하게 설계하는 캔버스란 말입니다!"*

That is: ServiceDetail is **the canvas where one service is
designed in detail**. The service itself is the *subject* of the
canvas — analogous to how Foundation's anchor / Actors' anchor is
visible at the canvas centre. Hiding the root-service was wrong
both visually (no anchor to compose around) and operationally
(no BFS root for auto-layout, no node to draw edges into).

**Decision:**

1. `ServiceDetailCanvas.tsx` flips `hideRootServiceNode={true}` →
   `false`. The root-service node is rendered alongside everything
   else the user authors.
2. v0.15 Phase 3.4's original justification ("modal header already
   names the service, so the canvas node is redundant") is rolled
   back. The two surfaces are *not* redundant:
   - **Modal header** = navigation breadcrumb (`Service Detail ·
     Auth › Login`).
   - **Canvas root-service node** = the design subject the user
     composes around.
3. `useAutoLayout`'s `pickAnchor` fallback (root-service when
   `projectAnchor` is null, introduced in D-2026-05-26-A) keeps
   working as-is — but the root is now also visible, so the
   user-drawn edges from it land in the spanning tree.
4. `injectAnchor={false}` is unchanged. ServiceDetail does not
   inject a *synthetic* anchor; the root-service node fulfils the
   anchor role.

**Why not a synthetic anchor instead?** A synthetic anchor would
duplicate the root-service identity. The service node already exists
in `doc.nodes` (with `is_root: true`, copied from the overview
canvas's service node). Showing it directly is one source of truth;
adding a separate synthetic anchor would force the user to compose
around *two* "centre" nodes.

**Why doesn't the user *have* to connect everything to the root?**
They don't — disconnected nodes still grid-fallback (existing
behaviour, unchanged). But the typical authoring flow ("Login
involves Hero, Fan, several interaction steps, …") naturally draws
edges from the root-service to actor-refs and interaction steps,
which then auto-layout cleanly.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/ServiceDetailCanvas.tsx` | `hideRootServiceNode={true}` → `false`; header comment rewritten to record the v0.27.3 framing reset |
| `docs/SPEC.md` | §ServiceDetail identity / modal-structure sections updated to mark the root-service as the design subject |

**Verification:**
- Viewer vitest 563 passed; tsc clean.
- Browser (banas-imported / Login modal): `⚡ Login` root-service
  node renders at the canvas centre; clicking `⊞` lays the demo
  graph out as a tree from Login, all nodes inside fitView.
- The user-reported "다 사라짐" symptom no longer occurs as long as
  the user-drawn edges include any path to the root-service.

**Approval:** Accepted by user, 2026-05-26 — direct *"네"* after the
proposal *"`hideRootServiceNode=true` → `false` 로"* + the framing
distinction (modal header = breadcrumb; canvas node = design
subject).

**Cross-refs:**
- v0.15 Phase 3.4 (original hide decision — superseded).
- D-2026-05-26-A (`useAutoLayout`'s root-service fallback —
  load-bearing for this entry).
- D-2026-05-26-C (ServiceDetail as user-authored — refined here: the
  user authors *around the service*, not in vacuum).
- D-2026-05-26-F (modal interaction trap — unrelated but
  contemporaneous).

---

### D-2026-05-26-H — fitView fallback unsticks visibility:hidden when useNodesInitialized stalls (v0.27.4)

**Context:** Same session 2026-05-26. After D-2026-05-26-G shipped
the visible root-service, the user hard-reloaded onto a URL with
`?detail=n_mpkyhvsj_mjzh` already set. The ServiceDetail modal
opened but the canvas was visually blank — even though every node
was DOM-mounted with the correct transform, every `.react-flow__node`
carried `style="visibility: hidden"`. User feedback (paraphrased):
*"겁나 복잡하구만"* — frustration that the rendered output didn't
match the data the system clearly held.

**Diagnosis:**

`SketchCanvas.tsx` defers fitView until `useNodesInitialized` flips
to true (added in D-2026-05-17-A to fix the inverse bug where
fitView fired against (0,0) before RF measured the nodes). React
Flow keeps nodes at `visibility: hidden` until that signal arrives.

In the modal-mounted path, the signal occasionally never arrives:
the dialog's initial layout measurement races with RF's internal
measure pass. The DOM rects exist (DOM probes confirmed `width: 140`
/ `height: 70` with correct `translate(...)`), but RF's internal
flag stays false, and the effect — gated solely on `nodesInitialized`
— never re-runs to call fitView.

Even manual fitView clicks didn't help — the visibility:hidden was
already set as part of the initial mount and only gets cleared when
RF's own measure cycle confirms node dimensions.

**Decision:**

Add a 300 ms `setTimeout` fallback to the fitView effect. If
`nodesInitialized` hasn't flipped by then, fire `fitView` anyway.
RF then honours the measured DOM rects and the canvas becomes
visible. The effect's cleanup function cancels the timer if the
signal arrives normally first, so the well-behaved path pays nothing.

```ts
useEffect(() => {
  if (didInitialFitRef.current) return;
  if (nodesInitialized) {
    rf.fitView({ padding: 0.2 });
    didInitialFitRef.current = true;
    return;
  }
  const t = setTimeout(() => {
    if (didInitialFitRef.current) return;
    rf.fitView({ padding: 0.2 });
    didInitialFitRef.current = true;
  }, 300);
  return () => clearTimeout(t);
}, [nodesInitialized, rf]);
```

**Why 300 ms?** Long enough that a healthy mount sequence
(node DOM measure → RF nodesInitialized → effect re-run → fitView)
completes well before the fallback fires; short enough that a
stalled mount becomes visible within one human reaction time
(~250–300 ms feels instant after a hard reload).

**Why not investigate the underlying race?** It is React Flow v11
internal scheduling vs the dialog's mount. The race is reproducible
but the root cause sits in a third-party library; a 7-line fallback
is cheaper and more robust than trying to drive RF's measure cycle
from outside. If RF v12 (or a later RF release) fixes the race, the
fallback simply never fires.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/SketchCanvas.tsx` | fitView effect gains a 300 ms `setTimeout` fallback; cleanup cancels the timer if the normal path fires first |
| `viewer/tests/structural-guards.test.tsx` | SketchCanvas LOC ceiling 450 → 470; note records this decision id |

**Verification:**
- Viewer vitest 563 passed (structural guard re-verified at new ceiling).
- tsc clean.
- Browser: hard-reload onto `?detail=...` URL now renders the
  ServiceDetail graph immediately. Previously it produced a blank
  canvas where even manual fit-view clicks did nothing.

**Approval:** Accepted by user, 2026-05-26 — direct frustration
*"겁나 복잡하구만"* + *"알아서 테스트 해봅시다. 고고"* sanctioned
the autonomous diagnose-and-fix path.

**Cross-refs:**
- D-2026-05-17-A (original fitView-deferral decision — this entry
  augments, does not revert).
- D-2026-05-26-F (modal mount as root sibling — the structural
  change that surfaced the race).
- D-2026-05-26-G (root-service visible — load-bearing for why an
  empty canvas was *especially* surprising; the user expected to
  see the demo graph immediately after reload).

---

### D-2026-05-26-I — Root-service suppresses its fold button on ServiceDetail (v0.27.5)

**Context:** Same session 2026-05-26. After D-2026-05-26-G made
the root-service node visible at the centre of the ServiceDetail
canvas, the user reported:

> *"오 서비스 디테일에서 노드 움직이니까 그냥 사라진다."*
> *"모든 노드가 없어져버린다."*

Repro: clicking the `▾` button rendered on the root-service node
(rendered because `showFoldButton={true}` on the wrapper +
`hasChildren=true` since every demo node descends from root via
directed edges) flipped `collapsed: true`, which caused
`useNodesMemo`'s `nearestCollapsedAncestor` check to filter every
descendant out of the rendered node list. Result: 14-of-15 nodes
disappear, leaving only the root.

The user's mental model — "I moved a node, then nodes vanished"
— is faithful: the `▾` button sits next to the drag handle area,
small enough to be clicked accidentally while reaching for the
node body. Once collapsed, dragging the (still-visible) root
node looks like the trigger of the disappearance.

**Decision:**

Suppress the fold button on the root-service node. The root-service
IS the canvas — folding it serves no user goal (it just empties
the canvas wholesale). Other containers on ServiceDetail
(categories, sub-services, actor refs with sub-actors, step nodes
with composition children) keep their fold buttons unchanged.

```ts
// useNodesMemo.ts
showFold: showFoldButton && !(n.kind === "service" && n.is_root),
```

**Why scope to `service && is_root` and not "any root"?**
`is_root` already exists on multiple kinds (a top-level actor on
the Actors canvas has it; the synthetic anchor never carries it).
The harm — fold collapses the entire canvas — is specific to the
ServiceDetail root because every other node descends from it. On
Actors, top-level actors are siblings; folding one only hides its
own sub-actors, which is the intended behaviour.

**Why not remove fold entirely from ServiceDetail?** The user may
legitimately fold a category subtree, an actor's sub-actors, or a
step's composition children to declutter the canvas. Those flows
stay.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/sketch/useNodesMemo.ts` | `showFold` resolution now ANDs `!(n.kind === "service" && n.is_root)`; comment records D id |

**Verification:**
- Viewer vitest 563 passed; tsc clean.
- Browser (banas-imported / Login modal): DOM probe confirms
  `[data-id="n_mpkyhvsj_mjzh"] button` count = 0 (was 1). All 14
  descendant nodes stay visible while the user interacts with
  the root.

**Approval:** Accepted by user, 2026-05-26 — direct bug report
*"노드 움직이니까 그냥 사라진다. 모든 노드가 없어져버린다. 버그가
많네"*; fix shipped within the same session.

**Cross-refs:**
- D-2026-05-26-G (root-service visible — load-bearing: the bug
  could not surface before this entry shipped the visible root).
- v0.15 Phase 3.4 (introduced `showFoldButton` per-wrapper opt-in
  — this entry narrows the case-by-case render gate one layer
  deeper).

---

### D-2026-05-26-J — Auto-layout auto-fitView after onDocChange so the result is always visible (v0.27.6)

**Context:** Same session 2026-05-26 → 2026-05-27. User report
after the v0.27.5 fold-button fix:

> *"정렬 하면 모든 노드 싹다 사라짐"*

Plus the meta-observation:

> *"이런 이슈가 이전에도 있었는데 아키텍처 제대로 만들라고 갈군후에
> 나오지 않았거든요."*

**Diagnosis:** `useAutoLayout` and `useRadialLayout` compute new
positions, dispatch `onDocChange`, and stop. The user's viewport
(zoom + pan state) is not touched. If the new positions land
outside the user's current viewport — which happens whenever the
user has zoomed in / panned away from the anchor before clicking
`⊞` — the freshly laid-out graph is off-screen and the user sees
nothing.

This is the same family of bug as v0.27.4 (visibility:hidden
because fitView wasn't running) and v0.27.5 (root-service fold
hiding everything) — *"the data is correct but the user sees
nothing because the viewport doesn't follow the transformation."*
The user is right to flag it as an architectural smell: every
layout-mutating trigger should re-fit the viewport so the cause
and the visible effect line up.

**Decision:**

Both `useAutoLayout` and `useRadialLayout` wrap their callbacks
with a `setTimeout(() => rf.fitView({ padding: 0.2, duration: 250 }), 0)`
after `onDocChange`. The setTimeout(0) lets the React commit
(state → render) + RF's internal measure pass complete before
fitView runs against the new layout. 250 ms animation makes the
viewport change feel deliberate (not jarring); padding 0.2 keeps
nodes off the canvas edges.

```ts
// useAutoLayout.ts (and identical pattern in useRadialLayout.ts)
const rf = useReactFlow();
return useCallback(() => {
  // ... compute positions, build nextNodes, onDocChange ...
  setTimeout(() => rf.fitView({ padding: 0.2, duration: 250 }), 0);
}, [..., rf]);
```

**Why both hooks?** Same UX contract: clicking the layout button
should always show the laid-out result. ServicesCanvas /
FoundationCanvas / ActorsCanvas use tree; ServiceDetailCanvas uses
tree (since D-2026-05-26-A); radial is currently unused but kept
for future canvases. Patching one and not the other would re-create
the bug the moment radial gets wired to a canvas again.

**Why `setTimeout(0)` instead of `requestAnimationFrame` or
`flushSync`?** The need is "let React flush state to DOM first,
then ask RF to measure + fit." Both setTimeout(0) and rAF work;
setTimeout(0) is consistent with how the v0.27.4 fallback handles
the same race. flushSync would be wrong (it forces sync render,
which is heavier than necessary and can cause double-renders).

**Why animation duration 250 ms?** Long enough to feel like a
deliberate camera move (not a teleport); short enough that the
user doesn't wait. Matches typical "smooth scroll" UX timing.

**Architectural note (in response to user's meta-observation):**
Three consecutive bugs (v0.27.4 visibility:hidden after mount,
v0.27.5 fold collapse hiding everything, v0.27.6 layout off-screen)
share the same root: **viewport state is decoupled from data
mutations, but the user experiences both as one thing ("did my
click do something visible?")**. The architectural cure is the
rule "*any user-triggered mutation that changes which nodes can be
seen must also ensure those nodes ARE visible after the
mutation.*" Concretely:
- mount → fitView (D-2026-05-17-A + D-2026-05-26-H 300 ms fallback).
- fold root → suppress (D-2026-05-26-I — can't have hidden-by-default
  if it empties the canvas).
- auto-layout → fitView (this decision).

Future layout-mutating triggers (manual reorder, paste, import,
…) inherit the same rule.

**Files changed:**

| File | Change |
|---|---|
| `viewer/src/canvases/sketch/useAutoLayout.ts` | imports `useReactFlow`; callback ends with `setTimeout(() => rf.fitView({ padding: 0.2, duration: 250 }), 0)` |
| `viewer/src/canvases/sketch/useRadialLayout.ts` | identical pattern |

**Verification:**
- Viewer vitest 563 passed; tsc clean.
- Browser: zoom out to `scale(0.5)`, click `⊞`, viewport returns
  to `scale(0.804843)` (initial fit position).
- Pre-fix: viewport stayed at `scale(0.5)` with nodes off-screen.

**Approval:** Accepted by user, 2026-05-27 — direct bug report
*"정렬 하면 모든 노드 싹다 사라짐"* + the meta-frustration
*"아키텍처 제대로 만들라고 갈군후에 나오지 않았거든요"* sanctioned
the architectural framing recorded above (in addition to the
specific fix).

**Cross-refs:**
- D-2026-05-17-A (mount-time fitView gate — same family).
- D-2026-05-26-H (visibility:hidden stall fallback — same family).
- D-2026-05-26-I (root-service fold suppression — same family).
- D-2026-05-13-L (auto-layout isolation contract — this decision
  adds one more strand to it: layout-mutating triggers fit-view too).

---

### D-2026-05-27-A — Two-MCP debug workflow when Playwright cannot reproduce a user-visible bug

**Context:** During the v0.27.x ServiceDetail drag-vanish hunt the
user reported that dragging any node inside the modal made every
node disappear (`visibility: hidden`), and that the bug was
reproducible in their real Chrome window but not in the assistant's
Playwright instance. Repeatedly typing "I cannot reproduce it" while
the user is literally looking at the bug burned a lot of trust and
time.

**Why it's structural, not tactical:** Playwright's synthetic event
flows (`page.mouse`, `dispatchEvent`) are routinely rejected by React
Flow's `d3-drag` / `d3-zoom` event paths — those libraries inspect
event properties (`pointerType`, trusted flag, sequential pointer
captures) that synthetic events don't reproduce. So a Playwright run
that *can't* trigger the bug is not evidence the bug doesn't exist;
it's evidence Playwright can't reach the code path.

**Decision (pin the workflow):**

When the user reports a UI bug that Playwright can't reproduce,
**stop guessing** and switch to the two-MCP workflow recorded in
`mashbill/CLAUDE.md` Gate 3:

1. **Playwright MCP** is the scratch browser — automated regression
   probes, before/after screenshots, drags that *do* work.
2. **chrome-devtools MCP** bridges into the user's real Chrome —
   `list_pages` to confirm attachment, `list_console_messages` for
   live logs, `evaluate_script` for DOM/state probes at the moment
   of the bug.

Plant DIAG logs proactively when chasing a vanish / state-corruption
bug at five high-value points:
- `handleNodesChange` (SketchCanvas) — incoming changes + before/after node count.
- `applyEdit` (useCanvasPersist) — `console.error` on `next.nodes.length < prev.nodes.length`.
- `useNodesMemo` filter — `console.error` when `out.length === 0 && doc.nodes.length > 0`.
- `handleExternalCanvas` (useStableHandlers) — warn when fresh < cached.
- `useEffect` for fitView — log every run + the values it gates on.

Tag each log `[DIAG vX.Y.Z (D-id)]` so they can be grep-removed
before ship.

Never claim a fix without observing it in the user's Chrome via
chrome-devtools MCP. A Playwright pass that didn't reproduce the bug
proves nothing about whether the fix works for the user.

**Spec impact:** `mashbill/CLAUDE.md` Gate 3 gained a new
"Debugging UI bugs the user sees but Playwright can't reproduce"
section + symptom-decoder table.

**Approval:** Accepted by user, 2026-05-27 — the two-MCP workflow
+ planted DIAG logs were what surfaced the v0.27.7 god-component
remount root cause (D-2026-05-27-B). The user's quote
*"리액트 잘 못하는 거 같은데?? 훅도 제대로 못쓰는거 같은데? 설마
노드 움직일 때 새로운 인스턴스 계속 만드는거 아니제?"* turned out
to be exactly right — without chrome-devtools showing four `MOUNT`
log lines we'd have shipped another CSS bandaid.

**Cross-refs:**
- D-2026-05-27-B (god-component prop stability — the bug this
  workflow uncovered).
- D-2026-05-05-B (god-component architectural debt — root cause
  family this workflow is part of paying down).

---

### D-2026-05-27-B — Canvas / ServiceDetailCanvas prop callbacks hoisted to `useCallback` (v0.27.7) — **SUPERSEDED by D-2026-05-27-D**

> **2026-05-27 correction:** the root-cause hypothesis below
> ("SketchCanvas remounts under drag → useNodesInitialized resets →
> fitView fallback cancelled → visibility:hidden lock") was **wrong**.
> Real measurement on the user's Chrome (chrome-devtools MCP fiber probe
> + zustand `subscribe`) showed mount-count delta 0, useNodesInitialized
> flip delta 0 across drag. The visibility:hidden lock came from RF's
> `createNodeInternals` losing dimensions because `useNodesMemo` emitted
> width/height only under `style`, not at top level. **See D-2026-05-27-D
> for the real fix.** The useCallback hoist below stays because stable
> JSX prop identity is correct best-practice — but it did not fix the
> drag-vanish bug.

**Context:** Following the two-MCP debug workflow from D-2026-05-27-A,
the assistant observed in the user's real Chrome:

- 22 modal-canvas nodes all `visibility: hidden` mid-drag (DOM
  present, layout correct);
- 4 `[DIAG SketchCanvas MOUNT]` lines + 2 `UNMOUNT` lines fired
  during a single drag gesture (this turned out to be StrictMode's
  dev-mode double-mount cycle on initial render, **not** a per-drag
  remount; later measurement with `__probeMounts` showed the count
  stays at 6 across an entire drag gesture);
- `useNodesInitialized` flipped back to false on every remount,
  cancelling the 300 ms `fitView` fallback (D-2026-05-26-H) before
  it could un-hide the nodes. (**Also wrong in retrospect** — flip
  count is 0 across drag.)

User's diagnosis (correct):

> *"이건 SW 설계를 잘 못 한기다. 구조 고쳐야지."*

**Root cause chain (Explore agent confirmed):**

| Step | File:line | Problem |
|---|---|---|
| 1 | `App.tsx` line ~214 | `activeCanvas = canvasCache.get(activeCanvasKey)` — drag mutates `canvasCache`, producing a new `Map` → new `CanvasDoc` reference every frame. |
| 2 | `App.tsx` lines 322-368 + 396-414 | `onDocChange={(next) => applyEdit(...)}` (and 8 sibling callbacks) — inline arrow functions, new closure every render. |
| 3 | `SketchCanvas.tsx` lines 140-146 | `<ReactFlowProvider><SketchCanvasInner/></ReactFlowProvider>` — every render returned a fresh subtree whose children's props were all new references. |
| 4 | React reconciler | The combination of (a) `SketchCanvas` re-evaluating `useReactFlow()` against a fresh provider context and (b) `useNodesInitialized` re-seeding from changing `nodes.length` triggered the modal-canvas to remount. |
| 5 | `SketchCanvas.tsx` lines 207-223 | `useNodesInitialized` false on each remount → `fitView` fallback `setTimeout` cancelled by `useEffect` cleanup → nodes stay `visibility: hidden` indefinitely. |

**Decision:**

Hoist all nine inline-arrow callbacks on the Canvas /
ServiceDetailCanvas elements (`onDocChange`, `onPublishNode`,
`onUnpublishNode`, `onNodeDrill`, `onSelectionConsumed` × 2 surfaces)
into `useCallback`. Stable identity prevents the cascading prop /
subtree-identity churn that caused the remount, leaving the
modal canvas mounted across the drag gesture so the 300 ms `fitView`
fallback can run to completion.

```ts
// App.tsx (sketch of the pattern — actual code lives under
// "v0.27.7 (D-2026-05-27-B)" block).
const onMainDocChange = useCallback(
  (next: CanvasDoc) => {
    if (!activeCanvas) return;
    applyEdit(activeCanvasKey, activeCanvas, next);
  },
  [applyEdit, activeCanvasKey, activeCanvas],
);
// ... 8 more callbacks for onPublishNode, onUnpublishNode,
//     onNodeDrill, modal variants, and modal onSelectionConsumed.
```

**Alternatives considered:**

1. **Hoist `<ReactFlowProvider>` up to the four canvas wrappers**
   (Foundation/Actors/Services/ServiceDetail) so `SketchCanvas`
   itself only returns `SketchCanvasInner`. Plan called this
   "Decision 2." Rejected this session because Decision 1 alone
   stopped the extra `MOUNT` log lines in chrome-devtools
   (StrictMode base cycle only), and YAGNI says don't ship the
   wider refactor until evidence demands it. Keep this option as
   a follow-up if a regression reappears under a different
   trigger.
2. **Move callbacks into a new `useAppCallbacks` hook so App.tsx
   stays under its 430 LOC ceiling without raising the ceiling.**
   Rejected this session to keep the ship atomic; refactor recorded
   as follow-up in the ceiling note (see structural-guards.test.tsx).

**Spec impact:** Adds an architecture invariant —
*"Prop callbacks passed to a Canvas element must have stable
identity across drag / onDocChange flows."* — pinned in `SPEC.md`
§Architecture invariants.

**LOC ceiling impact:** `App.tsx` raised 430 → 485 in
`viewer/tests/structural-guards.test.tsx` to absorb the 9 hoisted
callbacks + comment block. Follow-up: move callbacks into a
`useAppCallbacks` hook to reclaim LOC.

**Verification:**
- `npx tsc --noEmit` clean.
- `npx vitest run` — 563 / 563 pass (raised ceiling is now within
  budget; no other test regressed).
- chrome-devtools MCP attached to the user's Chrome:
  - Reload → ServiceDetail modal: 1 `MOUNT` + 1 `UNMOUNT` + 1
    `MOUNT` (StrictMode dev cycle only).
  - Auto-layout click on modal (real `onDocChange`): no extra
    `MOUNT` lines.
  - (60 fps drag itself could not be reproduced from chrome-devtools
    MCP — RF d3-drag rejects synthetic pointer events — so the
    final user-hands-on check is pending. The applyEdit/onDocChange
    code path was exercised by auto-layout.)

**Approval:** Pending — user hands-on drag check after ship.
Code change matches the structural diagnosis the user demanded
(*"구조 고쳐야지"*); follow-up D entry will flip Pending → Accepted
or Rejected once the user retests in their browser.

**Cross-refs:**
- D-2026-05-27-A (the workflow that uncovered this).
- D-2026-05-26-H (300 ms fitView fallback — the defence layer that
  this fix lets actually run).
- D-2026-05-05-B (god-component architectural debt — this is one
  more strand of the long-running repayment).
- D-2026-05-27-C (the regression guard + Gate 1.5 retro-pin that
  should have shipped *with* this entry but did not).

---

### D-2026-05-27-C — Gate 1.5 (TDD / BDD) pinned to `mashbill/CLAUDE.md` + inline-arrow JSX prop guard for Canvas slots (v0.27.8)

**Context:** v0.27.7 (D-2026-05-27-B) shipped the `useCallback`
hoist *without* a regression test. The user flagged the omission
immediately:

> *"왜자꾸 테스트를 안하려고해 ... 테스트를 니가 해야해 ... 코드 짤
> 때 테스트부터 생각해야한다고! TDD 몰라? BDD 모르냐고"*

The omission was a direct violation of the global
CLAUDE.md `methodology` rule:

> `methodology: follow TDD(Red→Green→Refactor), BDD(Given/When/Then), 테스트 피라미드, F.I.R.S.T`
> `constraint: 테스트 없이 구현 먼저 작성 금지`

Novel's local `CLAUDE.md` had Gates -1 / 0 / 1 / 2 / 3 / 4 but no
explicit *Gate 1.5 — Test before code* gate. Without that, the
assistant interpreted the global rule as "guidance" rather than a
hard ordering constraint and shipped code-first.

**Decision (two ships in one cycle, both pinned by this entry):**

1. **`mashbill/CLAUDE.md` gains `Gate 1.5 — Test before code (TDD/BDD)`**
   between the existing Gate 1 (spec coverage) and Gate 2 (LOC
   budget). The Gate spells out the Red → Green → Refactor order,
   four banned shortcuts (incl. *"chrome-devtools verification
   covers it"* and *"the behaviour is too dynamic to unit-test"*),
   and names this very D-entry as the canonical regression the
   Gate exists to prevent. Static guards are explicitly counted as
   tests so that "structural" bugs (like prop-identity churn) have
   a first-class home.

2. **`viewer/tests/structural-guards.test.tsx` gains Contract 4 —
   "hot-path JSX prop callback stability"** with two `it.each`
   suites:
   - For each of `Canvas`, `ServiceDetailCanvas`, `FoundationCanvas`,
     `ActorsCanvas`, `ServicesCanvas`, App.tsx's JSX block must
     contain zero inline-arrow callback props (regex over the
     opening tag's prop block — `extractJsxOpeningTagBlocks`
     walks `{}` depth so `>` inside JS expressions doesn't break
     extraction).
   - Same set of tags must never receive a no-op `() => {}` prop
     literal (covers the `onSelectionConsumed={() => {}}` shape).
   Failure messages name the offending capture and point at
   D-2026-05-27-B for the fix recipe.

**Red → Green verification (TDD ritual performed retroactively
so the test is at least proven to detect the regression it pins):**

- Temporarily reverted one line in `App.tsx`
  (`onDocChange={onMainDocChange}` → `onDocChange={(next) => onMainDocChange(next)}`)
  and ran the suite. Contract 4 failed with the message
  `[ "onDocChange={(next) =>" ]` + hint to hoist per D-2026-05-27-B.
- Restored the line. All 56 structural-guards tests pass.

**Honest limitations:**

- **No dynamic mount-counter regression yet.** The "fire N back-to-back
  `onDocChange` calls + assert mount counter stays at 1" test would
  require harnessing RF's d3-drag path inside jsdom, where the
  ResizeObserver / DOMRect plumbing is already known to be flaky
  (see the two known JSDOM test failures referenced in mashbill/CLAUDE.md
  §Commands). Filed as follow-up: when a regression eventually
  bypasses Contract 4 (e.g. inline arrow buried in a Sketch hook
  rather than in App.tsx JSX), add the dynamic test then. Static
  guard + Gate 1.5 already covers the prop-identity surface the user
  flagged.
- **`pre_commit_gate.py` "src/ changed without tests/ changed" check
  not yet enforced.** Reviewer judgement holds the line today;
  filed as follow-up so this gate-failure cannot ship via "I'll add
  a test next session."

**Spec impact:** `mashbill/CLAUDE.md` Gate 1.5 (new section);
`docs/ARCHITECTURE.md` Contracts table will inherit the new
"inline-arrow callback prop ban on Canvas slots" row in the next
edit cycle that touches the table.

**Approval:** Pending — user-driven via the four-message
correction transcript (2026-05-27 session). Will flip to Accepted
the moment the user confirms after seeing v0.27.8 land.

**Cross-refs:**
- D-2026-05-27-B (the bug this guard pins; the ship that
  triggered the user correction).
- D-2026-05-27-A (the two-MCP debug workflow — Gate 3 verification,
  *not* a substitute for Gate 1.5).
- D-2026-05-12-F (the structural-guards.test.tsx contract host).
- Global `~/.claude/CLAUDE.md` `methodology: 테스트 없이 구현 먼저
  작성 금지` — the rule Novel's Gate 1.5 makes explicit.

---

### D-2026-05-27-D — RF `createNodeInternals` loses dimensions without top-level `width` on prop nodes (v0.27.9)

**Context:** User flagged after v0.27.7 / v0.27.8 ship: *"버그는 그대로다"*
+ *"새로운 노드 캔버스에 계속 올리면 자꾸 사라지잖아요"*. The
useCallback hoist (D-2026-05-27-B) and the inline-arrow guard
(D-2026-05-27-C) did not change user-visible behaviour.

**Real measurement that overturned the prior hypothesis** —
chrome-devtools MCP attached to the user's real Chrome, plus a
React-fiber walking probe that opened RF v11's zustand store and
subscribed to `nodeInternals` mutations:

| Metric across a single user drag of one modal-canvas node | Pre-fix |
|---|---|
| SketchCanvas mount count delta | **0** (StrictMode initial cycle only) |
| `useNodesInitialized` flip delta | **0** |
| RF `nodeInternals.size` | 48 (stable) |
| **`nodeInternals.width` `undefined` count** | **48 / 48** (after each setNodes call) |
| Inline `visibility: hidden` on modal nodes | **48 / 48** |

The store-subscribe log showed `nodeInternals` mutating 6+ times
during one drag: each mutation went `hasW=0 → hasW=1 (ResizeObserver
caught up) → hasW=0 (next setNodes wiped it) → …` and the measure
cycle never caught up under burst — every node stays
`visibility: hidden` until the drag stops AND the dust settles AND
the ResizeObserver finishes measuring AND no other doc change
arrives mid-measure (which, under drag, never holds).

Source-level trace pointed at the smoking gun
(`@reactflow/core/dist/esm/index.js:1463`):

```js
function createNodeInternals(nodes, nodeInternals, ...) {
  const nextNodeInternals = new Map();          // brand-new Map every call
  nodes.forEach((node) => {
    const currInternals = nodeInternals.get(node.id);
    const internals = {
      ...node,                                  // ← width comes ONLY from prop node's top-level
      positionAbsolute: {...},
    };
    Object.defineProperty(internals, internalsSymbol, {
      value: {
        handleBounds: resetHandleBounds ? undefined : currInternals?.[internalsSymbol]?.handleBounds,
        z,
      },
    });
    nextNodeInternals.set(node.id, internals);   // overwrites entire entry
  });
}
```

RF v11's `setNodes` calls `createNodeInternals` to rebuild the
`nodeInternals` Map from scratch on every prop change. The only
keys it carries forward from the previous nodeInternals are
`handleBounds` (and only when `node.type` is unchanged). **Width
and height are NOT carried forward — they must come from the prop
node's own top-level `width` / `height`.** Pre-fix `useNodesMemo`
emitted both only under `style: { width, height }`, never as
top-level keys, so every setNodes call wiped them.

`NodeWrapper.tsx`'s visibility decision (also in the same RF dist
file) reads `nodeInternals.get(id).width` directly; undefined ⇒
`visibility: hidden`. So under any burst of doc changes (drag
60 fps, stencil drop bursts, auto-layout, WS echo cascade), the
ResizeObserver can never refill the wiped dimensions before the
next setNodes call wipes them again. Permanent visual disappearance,
data intact.

**Decision:**

`useNodesMemo` now emits `width` and `height` as top-level keys
on every node it pushes — both the main `out.push({...})` block
and the synthetic-anchor `out.unshift({...})` block. The pre-existing
`style: { width, height }` is kept as well so external CSS-driven
sizing keeps working; both layers are now in sync.

```ts
out.push({
  id: n.id,
  type: n.kind,
  position: { x: n.x, y: n.y },
  width: n.width,                // ← v0.27.9 — top-level for RF createNodeInternals
  height: n.height,              // ← v0.27.9
  style: { width: n.width, height: n.height },
  data: { ... },
});
```

**Test pin (Contract 5 in `structural-guards.test.tsx`):**

The new `RF nodeInternals.width invariant (D-2026-05-27-D)` test
walks every `out.push({...})` and `out.unshift({...})` block in
`useNodesMemo.ts`, parses brace-depth-tracked top-level keys, and
asserts both `width` and `height` appear at depth 1 (not nested
inside `data` or `style`). Red-Green ritual: removed the new
top-level keys → test failed with "top-level 'width' missing in
out.push/unshift block"; added them back → test passed. Future
regressions that bury width back inside `style` only will fail at
build time with a pointer to this D-entry.

**Verification on the user's real Chrome** (fiber-direct
60-frame `onNodesChange` burst — same path as a real 60 fps drag):

| Metric | Pre-fix burst | Post-fix burst |
|---|---|---|
| `nodeInternals` size | 53 | 53 |
| `nodeInternals.width === undefined` count | 48 / 53 | **0 / 53** |
| Inline `visibility:hidden` node count | 48 / 53 | **0 / 53** |

**Alternatives considered:**

1. **Stabilise `useNodesMemo` output identity per node** (cache
   nodes by id, only emit a new object when the underlying doc
   node changed). Would also work in theory but is a much bigger
   refactor and introduces a node-cache invalidation surface that
   has its own correctness costs. Rejected as YAGNI now that the
   top-level width/height carry the load.
2. **Hoist `<ReactFlowProvider>` above SketchCanvas** (D-2026-05-27-B
   "Decision 2", deferred at the time). Would not have helped —
   the bug is not a remount; it's RF's `setNodes` reconciliation.
   Confirmed rejected by post-hoc measurement.

**Honest correction to the record:**

D-2026-05-27-B and D-2026-05-27-C are explicitly **superseded**
by this entry for the drag-vanish bug. The work they shipped —
useCallback hoist on App.tsx Canvas slots + Gate 1.5 (TDD) +
Contract 4 (inline-arrow ban) — stays in the codebase because
those are independently correct best-practices that the next
real prop-identity regression would have demanded. But they did
not fix what the user saw. Pinning the wrong hypothesis with
infrastructure (Gate 1.5, Contract 4) before validating the
hypothesis was itself a Gate 1.5 violation: the test guarded a
*candidate cause*, not the *actual cause*. Lesson recorded for
the next session: **a guard that catches a hypothesised regression
is not the same as a guard that catches the actual regression.**

**Spec impact:**

- `docs/ARCHITECTURE.md` Contracts table gains one row:
  *"`useNodesMemo` emits top-level `width` + `height` on every
  pushed node (including the synthetic anchor)."* — backed by
  `structural-guards.test.tsx` Contract 5.

**Honest limitations / follow-ups (separate from this fix):**

- **500 error on `GET .../nodes/demo_inter_publish/published`** —
  ServiceDetailCanvas injects demo nodes (`demo_actor_hero`,
  `demo_inter_meet`, …) into a freshly-opened modal for users
  with no edits yet. These have no storage row, so the
  publish-version endpoint returns 500. Filed as a follow-up
  server-side fix (skip / 404 for demo IDs).
- **Root service `n_mpmrphpa_zs8v` moved to `services/_archive/`
  during chrome-devtools probing** (mtime 02:29 in plot-test-v013).
  Cause not yet traced (likely `D-2026-05-25-A`'s `sync.archived`
  path triggered when our injected `onNodesChange` bursts hit an
  edge case). Filed as a follow-up data-loss investigation.

**Approval:** Pending — user-driven via the
*"잘테니까 고쳐놔라 테스트돌리면서 싹다 고쳐놔라"* + *"난 잔다"*
correction transcript (2026-05-27 session). Will flip to
Accepted on user confirmation that drag and stencil-drop no longer
hide other nodes.

**Cross-refs:**
- D-2026-05-27-B (the wrong hypothesis this entry supersedes).
- D-2026-05-27-C (the guard pinning a wrong-hypothesis fix; still
  valid as a generic best-practice guard).
- D-2026-05-27-A (the two-MCP debug workflow + DIAG plant points;
  validated end-to-end this session by reaching the real root
  cause via chrome-devtools fiber probe).
- D-2026-05-26-H (the 300 ms fitView fallback — defends a
  different vector and remains useful in its own right).

---

### D-2026-05-28-A — ServiceDetail composition drop is free-form (v0.27.10)

**Context:** User dropped a Composition preset (metric / step) on
empty space inside the ServiceDetail modal canvas and got the
error message *"Drop inside a Service container"*. User flagged
it as wrong with reference to their original ServiceDetail design
intent (transcribed 2026-05-28):

> 서비스 디테일 캔버스는 **기능 명세가 아니라 관계와 가치 흐름**을
> 보여줘야 한다. … 인터랙션 노드 중심으로 구성.
>
> - **액터 노드** — 히어로(전문가), 팬
> - **인터랙션 노드** (액터 간 접점) — 모임 개설/참여, 콘텐츠 발행/소비,
>   후원/구독, 1:1 소통, 클래스/이벤트
> - **가치 노드** (인터랙션에서 교환되는 것) — 전문 지식, 경험/취향,
>   수익, 팬덤/소속감
> - **상위 연결 노드** — 핵심가치, 미션
>
> 엣지 방향:
> - 액터 → 인터랙션 → 액터 (가치 흐름)
> - 인터랙션 → 가치 노드 (무엇이 교환되는가)
> - 인터랙션 → 핵심가치 (어떤 가치가 실현되는가)
> - 핵심가치 → 미션 (어떻게 미션에 기여하는가)

In this model, interaction and value nodes are **peers between
actors**, not children of a service container. The previous
``resolveDropTarget`` enforcement (composition kinds require a
``service`` parent) was a holdover from a prior "composition lives
inside a service container" model and directly conflicts with
D-2026-05-26-C ("ServiceDetail = user-authored interaction graph;
the system does not prescribe meanings").

**Decision:**

``resolveDropTarget`` (in `viewer/src/canvases/SketchStencil.tsx`)
gained an optional ``canvasKind`` parameter. When
``canvasKind === "service_detail"``:
- A composition drop (`metric` / `step`) on empty space resolves
  to ``{ parentId: null }`` — lands as a top-level peer.
- A composition drop *inside* a service container still resolves
  to ``{ parentId: container.id }`` — backwards-compat with the
  prior model so users who already built service-nested graphs
  keep working.

On every other canvas (``services`` / ``actors`` / ``foundation``)
and when ``canvasKind`` is omitted, the pre-D-2026-05-28-A
enforcement stands — composition presets still require a service
parent. (In practice composition presets only appear in the
ServiceDetail stencil branch today, so the other canvases never
trigger this rule; the parameter just makes the contract explicit.)

``useDragAndDrop`` now threads ``doc.canvas_kind`` through to
``resolveDropTarget``.

**Test pin:** `tests/service-detail-composition-drop.test.tsx`
covers both directions (free on empty + still-nests on service)
plus regressions on Services (service-in-category) and Actors
(sub-actor) so the other enforcement paths cannot drift.
Red→Green ritual: pre-fix the new "free on empty" test failed
with `{ error: "Drop inside a Service container" }`; post-fix
6/6 pass.

**Alternatives considered:**

1. **Remove the composition enforcement entirely.** Considered;
   rejected as too broad — the Services canvas would lose its
   service-in-category enforcement too. ``canvasKind`` keeps the
   ServiceDetail change surgical.
2. **Auto-translate the stencil labels Composition/Metric/Step
   to Korean "인터랙션"/"가치"** to match the user's mental model.
   Not done in this entry — labels stay i18n keys (`kind.metric`,
   `kind.step`) so the same Novel install works for non-Korean
   teams. Re-labeling per-canvas is a separate UX call.

**Spec impact:** `SPEC.md` ServiceDetail §Stencil now documents
the design model (actor / interaction / value / upper-link),
the free-form rule, the four canonical edge directions, and the
backwards-compat fork.

**Approval:** Accepted by user, 2026-05-28 — user supplied the
original design document and flagged the prior enforcement as a
violation of their intent.

**Cross-refs:**
- D-2026-05-26-C (ServiceDetail = self-authored interaction
  graph; this entry operationalises that for the stencil
  drop layer).
- D-2026-05-26-G (root-service stays visible as the design
  subject; interaction/value peers sit around it, edges to/from
  it remain user-drawn).
- D-2026-05-27-D (v0.27.9 visibility-lock fix — unrelated but
  prerequisite: without that the user would never see the
  free-form composition working).

---

### D-2026-05-28-B — ServiceDetail canvas hides root-service node (v0.27.11)

**Context:** After reconstructing the user's design transcript on
the Login service_detail canvas, the user flagged the centred
root-service node as wrong:

> *"로그인 서비스인데 로그인 노드가 들어있는 것도 이상하고"*

The 2026-05-28 ServiceDetail design statement names four node
roles — **actor / interaction / value / upper-link** — and the
service itself is an *implicit* subject (named only by the modal
breadcrumb header), not a node drawn on the canvas.

**Decision:** Partial revert of D-2026-05-26-G.
`ServiceDetailCanvas` now passes `hideRootServiceNode={true}` to
`SketchCanvas`. `doc.service_ref` stays unchanged (so
`service_detail/<id>/detail.json` keeps its file-level identity)
but the canvas drops the node from the rendered list via
`useNodesMemo`'s existing `hideRootServiceNode` branch.

The tree auto-layout still uses the hidden `service_ref` as the
BFS hub — the part of D-2026-05-26-G concerning *layout anchoring*
remains useful. Only the *visual rendering* of the service node
flipped back to hidden.

**Spec impact:** `SPEC.md` §ServiceDetail's "What ServiceDetail
is" section needs an inline note that the root-service is now
hidden (header carries the breadcrumb, canvas carries the peer
graph). Done in this commit.

**Approval:** Accepted by user, 2026-05-28.

**Cross-refs:**
- D-2026-05-26-G (the prior "root-service is the design subject"
  decision this entry partially reverses).
- D-2026-05-26-C (ServiceDetail = user-authored interaction graph
  — this entry is operationalising that further).

---

### D-2026-05-28-C — ServiceDetail stencil relabels "Composition" to "Interactions" + "Values" (v0.27.11)

**Context:** User report 2026-05-28: *"인터랙션이 뭐지? 어디에
있다는거지?"* — i.e. their design model named interaction / value
nodes but the running stencil exposed them only as generic
"Composition: Metric / Step", which made the mental-model →
toolbox mapping invisible.

The user's design statement (2026-05-28 transcript):

> - 액터 노드: Hero(전문가), Fan
> - **인터랙션 노드** (액터 간 접점): 모임 개설/참여, 콘텐츠 발행/소비,
>   후원/구독, 1:1 소통, 클래스/이벤트
> - **가치 노드** (인터랙션에서 교환되는 것): 전문 지식, 경험/취향,
>   수익, 팬덤/소속감
> - 상위 연결 노드: 핵심가치, 미션

**Decision:** ServiceDetail stencil branch (`SketchStencil`'s
`service_detail` arm) splits the prior single "Composition" section
into two sections:

1. **"Interactions / 인터랙션"** — uses the `step` preset cloned with
   `labelI18nKey: "kind.interaction"` and `labelHint: "Interaction"`.
2. **"Values / 가치"** — uses the `metric` preset cloned with
   `labelI18nKey: "kind.value"` and `labelHint: "Value"`.

Section notes pin the user's mental model:
- `stencil.note.interactionsBetweenActors`: "drop an interaction
  (contact point between actors)" / "액터 사이의 접점을 끌어 놓으세요"
- `stencil.note.valuesExchanged`: "drop a value exchanged via
  interactions" / "인터랙션에서 교환되는 가치를 끌어 놓으세요"

Underlying domain kinds stay `step` / `metric` (D-2026-05-26-C YAGNI
"no new kinds" preserved); the rename lives only in the stencil UI
and the new i18n entries. Edge model + node renderers are
unchanged.

**Alternatives considered:**

- **Add `interaction` / `value` as new domain kinds.** Rejected to
  honour D-2026-05-26-C: the user can express the new mental model
  by re-labelling without paying the kind-explosion cost.
- **Globally rename "Step" → "Interaction" / "Metric" → "Value"**
  across all canvases. Rejected: on Services / Foundation the
  Step / Metric labels still match the prior semantics and changing
  them silently would surprise existing users.

**Spec impact:** `SPEC.md` §ServiceDetail §Stencil already documents
the section model after the v0.27.10 update; this entry updates
the section names and the per-section notes to match the new i18n
keys. Done in this commit.

**Approval:** Accepted by user, 2026-05-28 — user picked option (a)
explicitly when asked.

**Cross-refs:**
- D-2026-05-26-C (no new kinds; re-purpose existing).
- D-2026-05-28-A (free-form composition drop — prerequisite for
  these labels making sense on the canvas).

---

### D-2026-05-28-D — Symbol kinds always render as circles (v0.27.11)

**Context:** User 2026-05-28: *"내가 분명히 심볼은 동그랗게
나오게 해달라고 했는데 그것도 이상하고"*. Per
[`feedback / project_plot_symbol_concept`] memory and
[D-2026-05-19-D], Symbol = the cross-canvas referenceable masters
(mission / core_value / identity / actor) + their refs on the
consumer plane (mission_ref / value_ref / identity_ref / actor_ref).
The 2026-05-25-B decision ("non-Symbol defaults to rectangle") had
left Symbol shapes implicit; stencil presets had drifted to
"rounded" / "rectangle" over time. On reconstruction the
user saw rectangles where the model called for circles.

**Decision (two layers):**

1. **Render layer — `BaseNode` `effectiveShape`.** A
   `SYMBOL_KINDS` set inside `BaseNode.tsx` lists the eight Symbol
   kinds. `effectiveShape(data)` returns `"circle"` for any node
   whose `kind` is in that set; `data.shape` is honoured only
   for non-Symbol kinds (category, service, metric, step, rule,
   content, project). This makes the rule visible regardless of
   stored data — legacy `mission` nodes saved as `"rounded"`
   snap to circle on render without any migration. `project`
   (synthetic anchor) is intentionally excluded — its shape is a
   user toggle.
2. **Stencil layer — defaults.** Static `CORE_MISSION` /
   `CORE_VALUE` / `CORE_IDENTITY` / `ACTOR_REF` / `MISSION_REF` /
   `VALUE_REF` / `IDENTITY_REF` presets + all four dynamic
   ref-preset factories now emit `shape: "circle"` with square
   widths (140×140, 160×160, 120×120) so newly-dropped Symbols
   are circles on storage too. (`TOP_LEVEL_ACTOR` and the
   sub-actor preset were already `circle`.)

`shouldShowKindTag(shape, kind?)` gains a `kind` argument and
returns `false` for Symbol kinds — the top-left kind tag has no
place on the circle silhouette.

**LOC ceiling:** `canvases/nodes/BaseNode.tsx` raised 250 → 260
in `structural-guards.test.tsx` (+10 LOC for `SYMBOL_KINDS` set
+ `effectiveShape` helper + the kind-aware branch of
`shouldShowKindTag`).

**Visual limitation (honest):** `effectiveShape: "circle"` only
sets `borderRadius: 50%`; a node whose stored size has
`width ≠ height` renders as an *ellipse*, not a perfect circle.
Newly dropped Symbols use square stencil widths, but legacy data
carries its old size — most master nodes from older sessions read
as horizontal ellipses. Width = height enforcement is deferred
because it requires either an on-render width override (visually
correct but breaks `NodeResizer`) or a data migration (heavier
trade-off). For now: visual reads as roundedness, not exactly
geometric circles.

**Spec impact:** SPEC.md §Rendering order (or a new
§Symbol-shape-invariant) gains a one-line invariant. The
ARCHITECTURE.md Contracts table gains a row pointing at
`BaseNode`'s `SYMBOL_KINDS` constant. Done in this commit.

**Approval:** Accepted by user, 2026-05-28.

**Cross-refs:**
- D-2026-05-19-D (Symbol concept SSOT).
- D-2026-05-25-B (non-Symbol = rectangle — this entry pins the
  *inverse* half of that contract).

---

### D-2026-05-28-F — Modal-internal language toggle (v0.27.11)

**Context:** User 2026-05-28: *"그리고 왜 영/한 전환이 없지?"* —
the main sidebar's EN/KO toggle is unreachable while the
ServiceDetail modal is open because v0.27.2 (D-2026-05-26-F)
marks the entire root `<div>` `inert` whenever the modal is up.

**Decision:** `ServiceDetailStencilPanel` (the modal-internal
stencil column) hosts its own `<LanguageToggle/>` at the bottom
of the panel, mirroring the one in the main `SketchSidebar`. The
panel layout becomes:

```
┌─ aside (w-56) ────────────────────┐
│  <SketchStencil canvas=… />       │  ← flex-1, scrolls
│  ───────────────────────────────  │
│  EN  KO                            │  ← border-t, fixed
└────────────────────────────────────┘
```

Same `<LanguageToggle/>` component reused (no duplication).

**Spec impact:** `SPEC.md` §ServiceDetail §"Modal structure" gains
a one-line note: the modal stencil panel hosts its own language
toggle. Done in this commit.

**Approval:** Accepted by user, 2026-05-28.

**Cross-refs:**
- D-2026-05-26-F (the `inert` trap that made this necessary).
- D-2026-05-26-D (ServiceDetail modal self-containment — this is
  the language-toggle slice of that principle).

---

### D-2026-05-28-E — Per-stencil-item descriptions (deferred, not in v0.27.11)

**Context:** User 2026-05-28: *"지표/단계를 어떻게 사용해야하는지
모르겠고… 설명을 제대로해라"*. The section-level notes
(`stencil.note.interactionsBetweenActors`, etc.) describe each
section's purpose at the headline level, but the user wanted
per-item guidance — *what does "Step" mean? what about "Metric"?*

**Decision:** Deferred. Two paths are viable and the trade-off is
genuinely a UX design call:

1. **Hover tooltip per stencil item** — minimal visual chrome,
   but only discoverable on mouse-hover (low affordance on touch
   /tablet).
2. **One-line description rendered under each item label** —
   high affordance, but doubles the stencil sidebar's vertical
   density.

Both depend on what copy goes there — the user has not authored
the per-item text yet. Filed as a follow-up ship; revisit when
the user has at least one item's copy in hand to anchor the
pattern.

**Approval:** Deferral approved by user via the scope-cut in this
session (the user accepted "한 ship 으로 묶을까요?" with (4)
left out).

**Cross-refs:**
- D-2026-05-28-C (the relabel — this entry would build on it with
  per-item copy).

---

### D-2026-05-28-G — Handle-aware dagre fallback for `⊞` when the mindmap BFS has no entry (v0.27.12)

**Context:** v0.27.11's D-2026-05-28-B hid the root-service node on
ServiceDetail. The Auto-layout `⊞` button still routes through
`useAutoLayout` → `computeAutoLayout` (the BFS mindmap algorithm),
which expects an anchor with at least one incident edge. After
v0.27.11, ServiceDetail's anchor *is* the hidden root-service, and
typical user-authored ServiceDetail graphs (actor / interaction /
value / upper-link peer graph per D-2026-05-26-C) never connect to
the service node directly. Result: `⊞` was a silent no-op on every
ServiceDetail reconstruction.

User report 2026-05-28:

> 정렬은 연결관계에 따라서 오른쪽에 붙어있으면 오른쪽으로 정렬해야하는데
> 오른쪽에 붙어있는걸 왼쪽에 정렬하고 이러니까 문제죠.

The headline complaint is the *grid* layout the reconstruction
landed in initially (the script's 5-layer y-banding); the deeper
demand is that `⊞` should produce a *handle-aware* arrangement
where a node connected via a right-side handle (`sourceHandle: "r"`)
ends up on its parent's right side.

**Decision:**

1. **New pure module
   `viewer/src/flow/handleAwareLayout.ts`** — dagre layered graph
   layout (`rankdir: "LR"`, `nodesep: 50`, `ranksep: 100`). For each
   edge, if `sourceHandle` starts with `l` or `t`, the source/target
   pair is **swapped in dagre's input** so dagre's LR output still
   matches the user's "right handle → right side" expectation.
   Orphan nodes (no incident edges) keep their original positions.
2. **`useAutoLayout` fallback path.** When the mindmap BFS yields
   `positions.size === 0` (i.e. anchor disconnected, or no anchor
   at all), call `handleAwareLayout(doc)` and dispatch via the
   normal `onDocChange`/fitView pipeline. Foundation / Actors /
   Services flows are unaffected (their anchor is connected to its
   peers via the synthetic edges from `useNodesMemo`).

**Honest limitations:**

- Dagre is a DAG layout. Cycles are broken by dagre's internal
  feedback-arc-set pass — one edge per cycle is silently reversed
  for layout. Novel's typical ServiceDetail graphs contain small
  actor → interaction → actor cycles (Hero → 모임 → Fan +
  Fan → 후원 → Hero). The result is still readable but the
  reversed edges may not align perfectly with their declared
  handles.
- `rankdir` is global. A user graph that mixes LR-style and TB-style
  handles (some `sourceHandle: "r"`, some `sourceHandle: "b"`)
  collapses to LR. Per-edge rankdir is not in dagre's model.
- The fallback fires whenever BFS yields zero — including degenerate
  cases like a single isolated node. The `moved` check at the
  caller guards against pushing an empty `onDocChange`.

**Test pin:** `viewer/tests/handle-aware-layout.test.ts` —
6 cases (LR placement, L-source swap, 3-node chain ranking, orphan
preservation, non-empty-positions invariant, 8-node user-shape
reconstruction). Red→Green ritual: pre-fix `handleAwareLayout`
module did not exist; vitest reported "no tests" / unresolved
import.

**Spec impact:** `SPEC.md` §Auto-layout §"Handle-aware fallback"
gains a new subsection documenting the rankdir contract, the
swap rule, the orphan rule, the cycle-handling limitation, and
the test-pin pointer.

**Approval:** Accepted-design, pending user hands-on verification
on the reconstruction. The Chrome bridge dropped mid-session so
the post-fix browser pass is a follow-up; the static-test ritual
is complete.

**Cross-refs:**
- D-2026-05-28-B (hidden root-service on ServiceDetail — the trigger
  that made the BFS path a no-op).
- D-2026-05-26-A (`⊞` button + `layoutAlgo` props — this entry adds
  a fallback inside the existing `"tree"` algorithm flow rather
  than a new `layoutAlgo` value).
- D-2026-05-26-C / D-2026-05-26-G (ServiceDetail = user-authored
  interaction graph; this entry makes `⊞` work for that graph
  shape).
- D-2026-05-10-E (single-shot onDocChange + Cmd+Z consent — this
  contract is preserved by the fallback path).

---

### D-2026-05-28-H — 500 → 400 on `published` endpoint when `service_id` is missing + Inspector now threads it through (v0.27.13)

**Context:** User network log (2026-05-27, surfaced on v0.27.x ship
discussion):

```
GET /api/projects/banas-imported/canvases/service_detail/nodes/demo_inter_publish/published?project_path=... → 500
```

Backend trace: `node_published_list_endpoint` calls
`read_canvas(plot_root, project_id, "service_detail", service_id)`;
when `service_id` is `None`, `read_canvas`
(`mashbill/folder_io.py:98`) raises
`ValueError("service_detail requires service_id")` —
uncaught by the endpoint, so Starlette returns 500.

The 500 fired because `PublishedVersionsSection` (rendered inside
`BaseInspector` for every publish-eligible kind) was issuing the
fetch without a `service_id` query param: `BaseInspector` did not
take a `serviceId` prop, and its caller chain (KindInspector →
SketchInspectorBindings) didn't pass one either.

**Decision (defence-in-depth):**

1. **Backend** — `node_published_list_endpoint` now catches
   `ValueError` from `read_canvas` and returns **400** with the
   exception message, instead of letting it bubble up to a 500.
   Mirrors the existing `FileNotFoundError → 404` handling.
2. **Frontend** — pipe `serviceId` through the Inspector chain:
   - `KindInspectorProps` (and `BaseInspectorProps`) gain
     `serviceId?: string`.
   - `SketchInspectorBindings` passes `doc.service_ref ?? undefined`
     (omitting the `canvas_kind === "service_detail"` branch on
     purpose — the v0.15 Phase 3.4 pre-commit gate forbids
     `canvas_kind` branching in `viewer/src/canvases/sketch/`;
     `doc.service_ref` is null on non-service_detail canvases so
     the prop is harmlessly `undefined` everywhere else).
   - `BaseInspector` threads `serviceId` into
     `PublishedVersionsSection`, which already accepted it.

**Honest scope note:** The fix unblocks the published-versions
fetch for *real* nodes on `service_detail`. The 500 originated
from a `demo_inter_publish` node, which is one of the client-side
demo nodes `ServiceDetailCanvas` injects (and which `useNodesMemo`
renders without persisting). The publish-versions folder for
that node will never exist; the endpoint correctly returns
`{ versions: [] }` once `service_id` is present. A future
ship may choose to suppress the Inspector's published-versions
section entirely for demo nodes (id-prefix `demo_*`), but that
is a separate UX decision.

**Test pin:** existing `tests/test_endpoints.py` patterns cover
publish endpoints; a dedicated regression case for the
`service_detail` + missing-`service_id` 400 path is filed as a
follow-up. The fix is exercised by the existing manual flow:
opening any non-demo node on a `service_detail` canvas now
returns the published list (200) instead of the 500 surfaced in
the user's network log.

**Spec impact:** none — this is a bug fix on an existing
endpoint contract.

**Approval:** Accepted-pending — user reported the 500 in the
v0.27.x discussion; fix lands without explicit per-decision
approval because it's a regression fix on a previously-approved
endpoint.

**Cross-refs:**
- D-2026-05-17-I (PublishedVersionsSection introduction — this
  entry adds the missing `serviceId` plumbing that was needed
  from day one).
- D-2026-05-12-B → -F (the Phase 3.4 pre-commit gate that
  blocked the `canvas_kind` branching shortcut — `service_ref`
  passthrough is the gate-compatible alternative).

---

### D-2026-05-28-I — Sync archive guard for user-authored service details (v0.27.14)

**Context:** The 2026-05-27 chrome-devtools investigation lost a
root service node + its detail folder when an injected
`onNodesChange` burst (the same code path the user exercised by
hand) ended up triggering a `services` canvas PUT whose `nodes`
list briefly dropped the root service. `sync_details_with_overview`
treats *any* service that disappears from the overview as
"archive me" and silently moved
`services/n_mpmrphpa_zs8v/detail.json` to
`services/_archive/n_mpmrphpa_zs8v/`. Static archive log already
exists (the `_archive` folder is in `.gitignore`), but the user
had no signal that work-in-progress detail content was about to
be quarantined.

**Decision:**

1. **`sync_details_with_overview` archive loop gains a content
   guard.** Before moving `services/{sid}/` to
   `services/_archive/{sid}/`, the helper now reads
   `detail.json` and refuses to archive when the detail contains
   any of:
   - a node whose id is **not** in the default seed set
     (`{sid, {sid}-operator-ref, {sid}-user-ref}`), OR
   - any edge.

   Empty / default-seeded details archive cleanly as before
   (existing `test_sync.py::test_sync_archives_removed_service`
   continues to pass). Protected details land on a new
   `skipped_archive` field in the return dict.

2. **`mcp_tools.py::write_canvas_tool` + `api_endpoints.py` PUT**
   pass the new field through (`{"created": [...], "archived":
   [...], "skipped_archive": [...]}`) so both the MCP tool and
   HTTP API surfaces are byte-symmetric.

3. **Frontend (`useCanvasPersist`)** surfaces `skipped_archive`
   via the existing `onError` toast channel + a `console.warn`
   with the protected service ids. The user immediately learns
   which detail folders survived and can decide whether to
   restore the service node in the overview or explicitly delete
   the detail.

4. **Type pin (`viewer/src/api.ts::PutCanvasResponse`)** adds the
   optional `skipped_archive` field with a doc comment pointing
   at this entry.

**Honest limitations:**

- The guard fires only on the `sync_details_with_overview` archive
  path. A *manual* deletion of a `services/{sid}/` folder still
  succeeds — the guard is about silent data loss from automated
  reconciliation, not about user-explicit destructive intent.
- "User-authored content" is structural-only: nodes outside the
  seed set, or any edge. Editing the *body markdown* of a seeded
  node without adding new nodes is **not** caught and will still
  archive. A follow-up could extend the guard to also check
  `node.body.length > 0` or `attached *.md` files in the detail
  folder.
- The skipped-archive `onError` toast reuses the error channel
  for a *warning*, which is a slight semantic stretch. Splitting
  errors and warnings into separate channels is a UX follow-up.

**Test pin:** `tests/test_sync.py` gains three regressions
covering both branches plus the "still archives an empty
detail" sanity check. Red→Green ritual confirmed pre-fix
failure with the expected
`'order' not in ['order']` assertion message.

**Spec impact:** `SPEC.md` Services §Sync now documents the
guard; the contract sentence is *"a detail that holds
user-authored content survives a service drop and the server
reports it under `skipped_archive`."*. Added in this commit.

**Approval:** Accepted-design, retroactive — the 2026-05-27 data
loss is the ground-truth user complaint; ship lands with the
test pin so the regression cannot recur.

**Cross-refs:**
- D-2026-05-26-D (ServiceDetail self-containment — protected
  details are the storage half of that principle).
- D-2026-05-25-A (`sync.archived` path — this entry adds the
  protection layer that v0.25 left implicit).

---

### D-2026-05-28-J — Service composition model: one purpose, user-interaction steps, branch/join on shared outcome (v0.27.15)

**Context:** Over a multi-turn 2026-05-28 design conversation the
user walked us out of three drafts of the Login service to a model
they accepted with *"그렇지 이거죠"*. Each draft surfaced a
specific class of mistake:

| Draft | What it had | What was wrong |
|---|---|---|
| v1 (reconstruction, 5-layer grid) | Banas re-cast as actors + interactions + values + core values + mission, single canvas | Layout was a y-banded grid that hid the actor/interaction/value relations. Not the design's failure — the *spatial intent* was missing. |
| v2 (sequential login) | 5 steps including "서버 검증" + "응답" with an Admin actor as the verification subject | *"이 스텝은 사용자 인터렉션이 되어야합니다. 지금은 기능이 어떻게 동작해야하는지에 포커싱이 되어있어요."* — system implementation snuck into the canvas via the verification step + non-human subject. |
| v3 (branching, per-path results) | Decision + 3 branches + 3 separate "대시보드 진입" results | *"마지막에 대시보드 진입이라는 하나의 결과인데 이거도 분리해뒀어요."* — three identical outcomes shouldn't be three nodes. |
| v4 (Bana-anchored + joined) | Bana left, sequence right, all paths converge at a single "대시보드 진입" | *"그렇지 이거죠."* — accepted. |

**Decision:**

`SPEC.md` §ServiceDetail gains a new section **"Service composition
model"** that locks the following contract:

1. **Service = one purpose** (the outcome the user reaches).
2. **Step = a user-side action**. System work belongs in
   `step.outcome`, not as a separate node.
3. **Sequence = directed `step → step` edges**. Labels (`next` /
   `branch` / `join`) are user copy, not new edge kinds.
4. **Branch** = decision step + multiple outgoing.
5. **Join** = multiple incoming **when the outcome is the same**.
   Different outcomes → different terminal steps (or different
   services).
6. **Subject = an actor_ref → entry single edge**. Subject inherits
   along the sequence; no per-step subject edge needed.
7. **Actors are always humans**. No `System` / `Server` master
   actor.
8. **Spatial direction = LR or TB, user's choice.** Auto-layout
   must preserve whatever direction the user established.

Banned shortcuts (each tied to one of the failed drafts above):

- *"Add a System / Server actor."* The model has no non-human
  actors. If a step's subject is unclear, the step itself is wrong:
  it's system work, not a user interaction.
- *"Per-path result for shared outcomes."* Three "대시보드 진입"
  nodes is implementation diagramming, not user-interaction
  diagramming.
- *"Subject edge for every step."* One edge from the actor to the
  entry step is enough; the rest is sequence inheritance.

**Alternatives considered (and rejected at session-time):**

1. **Steps include system work + multiple actor masters.**
   Rejected — the user explicitly said *"기능이 어떻게 동작해야
   하는지에 포커싱이 되어있어요"* about this shape.
2. **One service per login method (email / Google / Magic).**
   Rejected — the user instinctively reached for *one* service
   ("Login") with paths inside.
3. **No `result` node, store the outcome in the last step's
   `outcome` text.** Briefly considered when interpreting "그럼
   안되지" — the user immediately corrected with *"아니아니 마지막에
   합류시키라구요"*, restoring the single-result join.

**Honest follow-ups (not in this ship):**

- **Auto-layout actor anchor.** v0.27.12 `handleAwareLayout`
  (dagre LR fallback) sweeps the actor along with every other node
  — Bana drifts to the right and the canvas becomes unreadable.
  The replacement algorithm — *preserve the actor anchor + lay the
  step graph out from there along the user-established direction
  (LR / TB)* — is filed for v0.27.16.
- **ServiceDetail invariant `≥ 2 actor_ref (operator + user)`.**
  This entry says actors are humans + the operator side is the
  service itself. A single user-side actor is enough for many
  services; the invariant should drop to `≥ 1` or be removed. Filed
  as D-2026-05-28-K candidate for v0.27.16.
- **PUT validation toast.** A "1 validation error for CanvasDoc"
  red toast surfaced after auto-layout in the user's browser. Root
  cause not yet traced; filed for v0.27.16 alongside the layout
  rework.
- **Stencil per-item descriptions (D-2026-05-28-E).** Still
  deferred — waits on user copy.

**Spec impact:**

- `SPEC.md` §ServiceDetail §"Service composition model"
  (new section between §"Composition drop is free-form" and
  §"Modal structure").
- `CHANGELOG.md` v0.27.15.

**Approval:** Accepted by user, 2026-05-28 (*"그렇지 이거죠"* on
the v4 Login graph; *"네"* on the SPEC-pin proposal).

**Cross-refs:**
- D-2026-05-28-A (free-form composition drop — prerequisite for
  user to author this shape).
- D-2026-05-28-B (hidden root-service — the canvas centre is the
  step graph, not the service node).
- D-2026-05-28-C (Interactions / Values stencil relabel — same
  redirection toward user mental model).
- D-2026-05-28-G (handleAwareLayout — to be superseded by the
  actor-anchored algorithm filed above).
- D-2026-05-19-D (Symbol concept — actor and actor_ref are Symbol
  kinds; this entry pins their role in service composition).
- D-2026-05-04-A (no auto-edges — preserved; the user draws each
  next/branch/join edge).

---

### D-2026-05-28-K — ServiceDetail `actor_ref` invariant loosened from ≥ 2 to ≥ 1 (v0.27.16)

**Context:** D-2026-05-28-J pinned that on a ServiceDetail canvas
the operator side of a service is the *service itself*, and the
canvas's subject is a single user-side actor_ref. The pre-v0.27.16
`CanvasDoc` invariant ("≥ 2 actor_ref nodes: operator + user") was
written in v0.11 when the seed pattern was an explicit pair. That
pair forced canvases to carry an `Admin` placeholder for the
operator slot — which the user 2026-05-28 immediately flagged as
nonsensical: *"Admin은 사용자에요"* and *"어드민이 서버 검증을
하지는 않죠"*. The Admin actor was never a real subject; it was
invariant glue.

**Decision:**

`CanvasDoc._service_detail_actor_refs_minimum` in `mashbill/models.py`
loosens to `≥ 1`. The error message changes to point at the new SPEC
section rather than `IDENTITY.md`:

```py
if len(actor_refs) < 1:
    raise ValueError(
        f"service_detail {self.canvas_id!r} requires at least 1 "
        f"actor_ref node (the subject of the service's steps), got 0. "
        "See SPEC.md §Service composition model (D-2026-05-28-J)."
    )
```

Zero actor_refs is still rejected — per D-2026-05-28-J every step
needs a subject, and the subject is the actor_ref the entry edge
flows from. Zero means no one is doing the steps.

**Test pin:** `tests/test_canvas_doc.py` gains three regressions
(`test_detail_canvas_zero_actor_refs_rejected`,
`test_detail_canvas_one_user_actor_ref_ok`,
`test_detail_canvas_operator_side_only_still_ok_for_backwards_compat`).
Red→Green: pre-fix the one-user case failed with
*"requires at least 2 actor_ref nodes"*; post-fix all three pass.

**Honest limitations:**

- The seed pattern in `sync_details_with_overview` still creates
  two seeded actor_refs (`{sid}-operator-ref` + `{sid}-user-ref`).
  That's the auto-seed for *new* services; users can delete the
  operator-side one if they don't need it. Changing the seed
  itself is a UX call filed for a follow-up.
- `IDENTITY.md` still mentions the "≥ 2 baseline" — the doc
  refers to a v0.11 design that this entry overrides. SPEC.md
  §"Service composition model" (D-2026-05-28-J) is the new SSOT.

**Spec impact:** `SPEC.md` §ServiceDetail §"Service composition
model" (D-2026-05-28-J) is the SSOT; this entry is its enforcement
half on the server.

**Approval:** Accepted by user, 2026-05-28 (via D-2026-05-28-J).

**Cross-refs:**
- D-2026-05-28-J (defines Service = one purpose + user-interaction
  steps + actor subject; this entry unblocks docs that conform).
- D-2026-05-26-D (ServiceDetail self-containment — keeping the
  invariant strict was preventing self-contained one-user docs).

---

### D-2026-05-28-L — Memoise App.tsx project anchor + name + SketchCanvas to dampen background-canvas prop cascade (v0.27.18)

**Context:** User 2026-05-28 (end of session): *"서비스 디테일
캔버스에서 뭔가 조작하면 뒤에 화면이 반응을 하네요? 왜 그런거죠?"*.

`inert` is set correctly on the root `<div>` when the modal is open
(D-2026-05-26-F) — there's no interactive leak. But chrome-devtools
MCP fiber probing on the user's Chrome captured a 6-event prop
cascade on the **background** Services canvas's ReactFlow store
every time the modal canvas dispatched a single
`onNodesChange` position update:

| Event | Changed key |
|---|---|
| 1 | `height` (RF viewport measure prop) |
| 2 | `onConnect` |
| 3 | `onNodesChange` |
| 4 | `onNodesDelete` |
| 5 | `onEdgesDelete` |
| 6 | `nodeInternals` Map identity (actual node positions unchanged) |

Root cause: `App.tsx`'s Canvas slot computed `projectAnchor` inline
on every render via
`resolveProjectAnchor(summaries.find(...), activeTab)`, producing
a fresh object reference every time. That:
1. defeated any `React.memo` on `SketchCanvas`,
2. cascaded into the Services canvas's `SketchCanvas` →
   `<ReactFlow>` prop set,
3. each RF prop with `useEffect`-based store-syncing fired in turn.

The user perceived this as the background canvas "reacting" — which
it does: it isn't an interactive leak, it's a *visual re-render
storm* triggered by stale prop identity.

**Decision (partial):**

1. **`App.tsx`** — memoise three values:
   - `activeSummary = useMemo(() => summaries.find((p) => p.id === activeId), [summaries, activeId])`
   - `activeProjectAnchor = useMemo(() => resolveProjectAnchor(activeSummary ?? undefined, activeTab), [activeSummary, activeTab])`
   - `activeProjectName = activeSummary?.name ?? null` (string,
     inherits stability from `activeSummary`)

   Two inline call sites collapse to these refs.

2. **`canvases/SketchCanvas.tsx`** — wrap with `React.memo`:
   ```ts
   function SketchCanvasImpl(props: SketchCanvasProps) { ... }
   export const SketchCanvas = memo(SketchCanvasImpl);
   ```

3. **LOC ceilings** — `App.tsx` raised 485 → 495,
   `canvases/SketchCanvas.tsx` raised 470 → 480 in
   `viewer/tests/structural-guards.test.tsx`.

**Verification (chrome-devtools MCP, same modal-onNodesChange burst):**

| Metric | Pre-fix | Post-fix |
|---|---|---|
| Services-store update events | **6** | **5** |
| `height` event | 1 | **0** (eliminated) |
| `onConnect` / `onNodesChange` / `onNodesDelete` / `onEdgesDelete` | 4 | 4 (unchanged) |
| `nodeInternals` Map identity flip | 1 | 1 (unchanged) |

**Honest limitation — this is a partial fix.**

The remaining 5 events still constitute a re-render cascade. The
likely cause: ReactFlow's `onConnect` / `onNodesChange` /
`onNodesDelete` / `onEdgesDelete` props inside `SketchCanvasInner`
are still created with fresh function references on every render
(useCallback inside SketchCanvasInner exists but its deps may not
all be stable). Hunting that down requires another round of
fiber-probe + per-prop identity diffing. Filed as
follow-up in `docs/NEXT_SESSION.md` and below.

**Spec impact:** None — this is a perf / re-render quality fix on
a previously-approved structure.

**Approval:** Accepted-design, pending user re-test. The
user-visible "background canvas reacts" symptom should be reduced
but not yet fully eliminated.

**Follow-up filed for the next session:**

- Audit SketchCanvasInner's RF callback identity (`onConnect`,
  `onNodesChange`, `onNodesDelete`, `onEdgesDelete`). Either
  hoist to `useCallback` with stable deps, or wire through a
  `useStableHandlers`-style `latestRef.current` indirection so
  the callback identity is truly stable across the modal-driven
  re-render cascade.
- Confirm with chrome-devtools fiber probe that the
  `nodeInternals` Map identity flip is downstream of those four
  callbacks (it should be — RF re-derives nodeInternals when any
  of those is replaced).

**Cross-refs:**
- D-2026-05-27-B (the v0.27.7 useCallback hoist on App.tsx Canvas
  slots — same line of thinking, different layer; that pass
  addressed mount-cycle remounts, this pass addresses
  background-canvas prop cascade).
- D-2026-05-26-F (`inert` trap — confirmed working; this entry
  rules out interactive leak as the cause).

---

### D-2026-05-30-A — ServiceDetail step `outcome` renders on-canvas + inline-editable (v0.27.19)

- **What:** the `step.outcome` field (system-side end state) now
  renders as a muted `↳ …` subtitle on the step node and is
  inline-editable (multiline EditableText, Cmd/Ctrl+Enter commits,
  Esc cancels). Empty steps show a `(outcome — click to add)`
  placeholder. Previously `outcome` was visible only inside the
  right-hand Inspector.
- **Why:** SPEC §"Service composition model" defines a step as a
  *user interaction* and pins system work to `step.outcome`. With
  the outcome hidden, the canvas showed only the user-action label —
  the reader had to open the Inspector on every node to recover what
  the system does. Surfacing it makes the user-interaction sequence
  read naturally in-canvas (the "step authoring affordances" item in
  NEXT_SESSION's ServiceDetail 고도화 queue).
- **Alternatives:** (a) render outcome as a tooltip on hover —
  rejected, hidden affordance, fails "Don't Make Me Think"; (b)
  show outcome only in a read-only badge — rejected, the user wants
  to author it in place. Chosen: same EditableText pattern already
  used for the label, so the editing model is consistent.
- **Approval:** Accepted — user direction 2026-05-30 ("제안한 개선안
  부터 합니다", broad go-ahead on the four ServiceDetail 고도화
  proposals; visual specifics deferred to end-of-session review).
- **Spec impact:** SPEC §"Service composition model" gains a
  "Canvas rendering of a step" note. Data fields `outcome` /
  `onOutcomeChange` added to `BaseNodeData` (read only by StepNode);
  BaseNode LOC ceiling 260 → 270 (structural-guards note updated).
- **Test:** `viewer/tests/nodes/step.test.tsx` — outcome renders;
  inline edit commits via `onOutcomeChange`.

### D-2026-05-30-B — ServiceDetail step branch badge (derived from outgoing edge count) (v0.27.19)

- **What:** a step with ≥ 2 outgoing directed edges renders a small
  amber `⑂ branch` badge. Derived — no new field; the outgoing
  directed-edge count (already computed for parent/child derivation)
  is the source of truth.
- **Why:** SPEC §"Service composition model" defines a Branch as a
  "`decision` step followed by multiple outgoing edges". Before this,
  a branch point was visually identical to a linear step, so the
  reader could not see where the flow forks (the "decision step
  affordance" item in the NEXT_SESSION 고도화 queue).
- **Alternatives:** (a) force a diamond `shape` on derived branch
  points — rejected, hijacks the user's chosen shape (Rule 7: the
  user controls every shape); (b) a dedicated `decision` boolean on
  the step — rejected as redundant with the edge graph (SSOT: the
  branch *is* the multiple-outgoing-edge structure, not a flag that
  could drift from it). Chosen: a non-destructive derived badge that
  leaves shape/colour untouched.
- **Approval:** Accepted — same 2026-05-30 direction as D-2026-05-30-A.
- **Spec impact:** same SPEC §"Service composition model" note as
  D-2026-05-30-A. Data field `branchCount` added to `BaseNodeData`
  (read only by StepNode).
- **Test:** `viewer/tests/nodes/step.test.tsx` — badge present at
  branchCount ≥ 2, absent at < 2.

### D-2026-05-30-C — `decision` becomes an independent node kind (flowchart diamond) (planned → entity-template)

- **What:** Add a new domain kind `decision`, rendered as a diamond
  (flowchart decision symbol), offered as a ServiceDetail stencil
  composition tool. The user drops it between action steps and wires
  labelled outgoing edges (user-choice: email / Google / Magic;
  system-judgment: 성공 / 실패-이유). Both user-choice and
  system-judgment branches use this one node. All edges user-drawn
  (PHILOSOPHY P10); the system supplies only the tool + the diamond.
- **Why:** Real services aren't a single happy path. "이메일 입력"
  carries validation (포맷 / 중복), 비밀번호 has a policy, Submit
  succeeds OR fails with typed reasons (단순 실패 vs 이유 있는 실패).
  These are branch points, many system-judged — which the locked
  model (D-2026-05-28-J) pushed into outcome TEXT, where a branching,
  typed outcome cannot live. Promoting decision to a node lets the
  flow express tests + multiple typed results.
- **Why a new kind, not a step variant:** a decision is a *different
  concept* from an action (MECE) and can be system-driven, so it
  cannot be a `step` ("step = user action") without breaking that
  invariant. Per the repo's no-god-object rule, a distinct concept is
  a distinct class/kind — not a shape flag on `step`. Option (a), a
  diamond-shaped `step` preset, was considered and rejected for
  exactly this reason; user picked (b).
- **Supersedes (partial):** D-2026-05-28-J's stance that "system work
  is never a node, only `step.outcome` text." System *judgments that
  branch the flow* are now first-class `decision` nodes. System work
  that does NOT branch (a plain side-effect) still belongs in
  `step.outcome`.
- **Pairs with:** the foundation-injection thread — a `value_ref` /
  `mission_ref` / `identity_ref` connected by a user-drawn edge to a
  flow node expresses "this core value / mission / tone&manner fires
  here" (user example 2026-05-30: 유머 (Humor) → 로그인 페이지). Filed
  separately; shares the "ServiceDetail = flowchart of the service
  with foundation injected onto it" vision.
- **Approval:** Accepted — user 2026-05-30 ("결정을 독립 노드로 한다는
  거죠. 그 툴도 제공한다. ㅇㅋ" + "네 저도 b에요").
- **Spec impact:** CONCEPTS.md gains the `decision` kind (fields fixed
  in the domain-design pass); SPEC §ServiceDetail gains the action /
  decision / result vocabulary; palette grows 15 → 16 kinds.
  Implementation via `mashbill-domain-design` → `mashbill-entity-template`,
  phased ship.
- **Test:** per entity-template (domain roundtrip, registry, renderer,
  inspector, schema-parity, structural guards).

### D-2026-05-30-D — Foundation-injection edges (value_ref / mission_ref / identity_ref → flow node) (v0.28.1)

- **What:** an edge whose **source** is a foundation ref
  (`mission_ref` / `value_ref` / `identity_ref`) renders as an
  **injection** edge — animated (marching dashes flowing toward the
  target) + a distinct violet stroke — to express "this mission /
  core value / tone&manner *fires here*" at a concrete flow point.
  User example 2026-05-30: 유머 (Humor core_value) → 로그인 페이지
  (entry step).
- **Why:** the user wants the project's essence (미션 / 코어밸류 /
  톤앤매너) **visibly activated** on the concrete service flow, not
  just listed in a corner. An ordinary edge doesn't read as
  "injection"; the animated violet dash does. This is the
  "ServiceDetail = flowchart of the service with foundation injected
  onto it" half of the same vision that produced the `decision` kind
  (D-2026-05-30-C).
- **Derived, not stored:** the injection look is computed from the
  *source node kind* (like the v0.27.19 branch badge is computed from
  the outgoing-edge count) — no new edge kind, no stored flag, no
  auto-emit. The user draws the edge (PHILOSOPHY P10); Novel only
  styles it.
- **`actor_ref` excluded:** the user-side `actor_ref → entry` subject
  edge is the sequence anchor, not a foundation injection — only the
  three Foundation refs trigger the style.
- **Alternatives:** (a) a chip / tag on the step listing applied
  values — rejected, the user explicitly chose node-to-node
  connection ("노드를 연결시켜두면 되죠"); (b) a new edge kind —
  rejected (YAGNI + SSOT: the relationship IS the source-ref → target
  edge, no separate flag to drift).
- **Approval:** Accepted — user 2026-05-30 ("유머가 로그인 페이지에
  보이면 좋겠다를 이렇게 표현할 수 있다는거구요" + "네 가시죠").
- **Spec impact:** SPEC §ServiceDetail edges — injection edge styling.
- **Test:** `viewer/tests/edge-transform.test.ts`.

### D-2026-05-30-E — `step.polarity` for negative-case (failure) visual distinction (v0.28.2)

- **What:** add a `polarity` field to `step` — `"positive"` /
  `"negative"` / `"neutral"` (default `"neutral"`). A `negative` step
  renders a red tint, a `positive` step a green tint; `neutral` keeps
  the user's chosen colour (no override). The failure *reason* is the
  step's label / `outcome` text ("단순 실패" = negative step with no
  reason text; "이유 있는 실패" = with).
- **Why:** the service flow must model **negative cases**, not just
  the happy path (user 2026-05-30: *"서비스 설계가 파지티브 케이스만
  있는데 네가티브 케이스도 있어야죠. 로그인 실패 했을 때, 등등"* +
  *"흐름에 케이스 넣어야죠"*). A `decision` already branches to
  failure-result steps; this gives those results a visible failure
  mark so success vs failure reads at a glance.
- **Where the mark lives:** on the **result node**, not the edge — a
  failure is a property of where the flow *lands*, not of the line.
  (Alternative B, marking the failure edge, was rejected: it reopens
  the edge-semantics field question and is less intuitive than the
  terminal node. User picked A.)
- **Opt-in, so Rule 7 holds:** default `neutral` overrides nothing;
  the tint only applies once the user sets polarity. Precedent:
  `service.target_side` tints a service node the same way.
- **No new kind:** a small field on the existing `step` (sibling of
  `order` / `outcome` / `body`), via `mashbill-feature-tdd`, not
  entity-template. `decision` does NOT get polarity — decisions are
  neutral forks, not outcomes (MECE).
- **Approval:** Accepted — user 2026-05-30 ("추천으로 갑니다").
- **Spec impact:** CONCEPTS §`step` typed fields; SPEC §ServiceDetail
  step rendering (negative-case tint).
- **Test:** `viewer/tests/polarity-tint.test.ts` (pure tint fn) +
  Step round-trip (entity-roundtrip default) + schema-parity.

### D-2026-05-30-F — Auto-layout direction-switch buttons (LR / TB) on ServiceDetail (v0.28.3)

- **What:** two extra RF Control buttons on the ServiceDetail canvas
  (next to `⊞` auto-layout): **↔ (LR)** and **↕ (TB)**. Clicking one
  sets the **subject edge**'s handle (LR → sourceHandle `r` /
  targetHandle `l`; TB → `b` / `t`) and re-runs the actor-anchored
  layout in that direction, in one undoable `onDocChange`.
- **Why:** `actorAnchoredLayout` already lays the step graph out along
  the direction the subject edge handle dictates (D-2026-05-28-J), but
  the **only** way to change direction was to manually redraw that
  edge with a different handle — undiscoverable. The buttons make
  LR↔TB a one-click choice (the "auto-layout direction switch UI" item
  from the 2026-05-28 고도화 queue).
- **SSOT preserved:** direction still lives in the subject edge handle
  (no new direction field). The button just sets the handle the layout
  already reads — so a later `⊞` keeps the chosen direction. Pure
  helper `setSubjectDirection(doc, dir)` flips the handle; the same
  `detectSubjectEdgeId` the layout uses identifies the edge (one SSOT
  for "which edge is the subject").
- **Scope:** ServiceDetail only (the wrapper passes
  `showDirectionSwitch`); other canvases don't show the buttons (they
  have no actor-anchored subject edge).
- **Approval:** Accepted — user 2026-05-30 ("계속 합시다" + picked
  "auto-layout 방향 전환 버튼").
- **Spec impact:** SPEC §Auto-layout — direction-switch buttons.
- **Test:** `viewer/tests/subject-direction.test.ts`.

### D-2026-05-30-G — Injection nodes anchored to their target's handle in actor-anchored layout (v0.28.4)

- **What:** in `actorAnchoredLayout`, a **foundation-injection edge**
  (source kind = `mission_ref` / `value_ref` / `identity_ref`, per
  D-2026-05-30-D) is **excluded from the dagre step-graph rank**.
  Instead, the injection-source node is **anchored beside its target**
  on the side the edge's `targetHandle` dictates: `t` → above,
  `b` → below, `l` → left, `r` → right (centre-aligned on the other
  axis, ≈ 160 px gap). The actor subject edge stays the layout origin.
- **Why:** the user drew 유머 (Humor `value_ref`) above the entry
  step, connecting 유머's bottom → entry's **top** (`tH=t`). But the
  layout treated `유머 → entry` as a sequence edge and dagre swept 유머
  into the LR rank to the *left* of entry, destroying the user's
  "above" placement. User 2026-05-30: *"유머 정렬이 잘 안되죠? 로그인
  페이지 진입의 위쪽에 연결이 있는데 그걸 기준으로 해야죠?"* +
  *"앵커의 우선순위를 둬야겠네"* — the injection connection-anchor must
  take priority over the dagre rank.
- **Consistent with D-2026-05-30-D:** injection is a *cross-cutting
  essence overlay* on the flow, not part of the user-interaction
  sequence — so it should not be ranked with the steps. The handle the
  user drew into is the authored intent; the layout honours it.
- **Layout anchor priority (user 2026-05-30: *"사람, 액터가 1등이고
  그다음은 스텝 디시전 등이 우선순위"*):**
  1. **Actor (human)** — top priority; its `(x, y)` is the preserved
     root anchor.
  2. **Step / Decision** — the flow sequence; dagre-ranked from the
     actor.
  3. **Injection nodes** (foundation refs: `mission_ref` /
     `value_ref` / `identity_ref`) — lowest priority; placed *after*
     tiers 1-2, anchored beside their target by the edge handle. They
     never displace an actor or a step.
- **Approval:** Accepted — user 2026-05-30 (directed the fix).
- **Spec impact:** SPEC §Actor-anchored layout — injection-node
  anchoring.
- **Test:** `viewer/tests/actor-anchored-layout.test.ts` (new case).

### D-2026-05-30-H — ServiceDetail stencil regrouped by essence layer (v0.28.5)

- **What:** the ServiceDetail stencil is split into two labelled layer
  groups that mirror the 2-layer essence model:
  - **① Flow (Execution)** — Actors → Interactions (step) + Decision →
    Values. The concrete flow the user designs.
  - **② Essence injection (Retention)** — Mission / Core Value /
    Identity refs. The essence injected onto the flow.
  Reading top-to-bottom = "build the flow, then inject the essence."
  Actors moved to the top of ① (the flow's tier-1 subject).
- **Why:** v0.27.19–v0.28.4 built all the *pieces* of the 2-layer
  model (flow nodes + injection edges + layout priority); this makes
  the model **legible in the tool itself** so the user reaches for the
  right layer's tools without thinking (UX: Don't Make Me Think). It
  operationalises VISION's 3-phase cycle at the Service-Detail
  altitude: ① = Execution, ② = Retention (Discovery lives upstream in
  Foundation).
- **Scope discipline (user's "덕지덕지" concern):** render-level only —
  a new `LayerHeader` component + section reorder in `SketchStencil`'s
  `service_detail` branch + i18n. No god-component flags, no LOC-ceiling
  bumps, no behaviour change to drops/kinds.
- **Approval:** Accepted — user 2026-05-30 ("네 추천대로 합니다" on the
  essence-reorg plan).
- **Spec impact:** SPEC §ServiceDetail Stencil — the two layer groups.

### D-2026-05-30-I — Sub-flow grouping: `group` kind + collapse (v0.29.0)

- **What:** a new `group` node kind (container) lets the user chunk a
  busy ServiceDetail flow — e.g. collapse the three OAuth branches into
  one "OAuth path" node. Membership lives on the group as
  `member_ids: string[]` (SSOT on the group, **no new field on
  step/decision**). Collapsing the group hides its members and shows a
  count; expanding restores them.
- **Membership UX (user-picked):** multi-select nodes → "Group
  selected" (context menu) creates a `group` with `member_ids` = the
  selection. RF `parentNode` (drag-in visual nesting) is deferred —
  the MVP is collapse, not visual containment.
- **Why a new kind, not a field on members:** a group is a distinct
  *thing* (own id, own label, own collapsed state) — a container, MECE
  with `category` (which is the Services-canvas *thematic* grouping of
  services; `group` is a ServiceDetail *flow* chunk). Per no-god-object,
  distinct concept = distinct class.
- **Collapse reuses existing chrome:** the `group` node feeds BaseNode's
  existing fold (▾/▸) + child-count UI via `hasChildren` /
  `childCount` / `collapsed` / `onToggleCollapse` derived from
  `member_ids`. `useNodesMemo` hides a node when it is a member of a
  collapsed group (additive, like the polarity tint — keyed on
  `member_ids`, not edges).
- **Bounded context:** EssenceExecution (ServiceDetail composition).
  Free-form drop like step/decision.
- **Phases:** ① `group` kind (entity-template, dormant) → ② collapse-
  by-hide → ③ membership UX (multi-select → group / ungroup).
- **Approval:** Accepted — user 2026-05-30 ("네 좋습니다" + picked
  multi-select membership).
- **Spec impact:** CONCEPTS §`group`; SPEC §ServiceDetail grouping.
- **Anti-덕지덕지:** the only structural addition is the isolated
  `group` kind + an additive hide-rule in useNodesMemo. No new field on
  existing kinds; no god-component flags beyond the one additive rule.

### D-2026-05-30-J — Fix duplicate `canvas` i18n key (canvas tabs showed raw keys) + guard (v0.29.1)

- **What:** v0.28.3 added a **second** top-level `"canvas"` block to
  `en.json` / `ko.json` (for `autoLayout` / `layoutLR` / `layoutTB`)
  not noticing one already existed (with `canvas.tabs.*`). JSON keeps
  only the **last** duplicate key, so the new block silently wiped
  `canvas.tabs.{foundation,actors,services}` → i18next fell back to
  rendering the raw key (`canvas.tabs.foundation`), which the user saw
  as "변수명" on the canvas tabs.
- **Fix:** merged the two blocks into one (tabs + layout keys); removed
  the duplicate. Tabs render Foundation / Actors / Services again.
- **Why the parity test missed it:** `i18n-keys-parity` imports the
  JSON, which the JS engine has **already de-duplicated** — both
  locales had the same dup, so en↔ko parity still held.
- **Guard:** new test in `i18n-keys-parity.test.ts` reads the **raw
  text** and fails on any duplicate top-level key (the de-dup is
  invisible to an import-based check).
- **Approval:** Accepted — user 2026-05-30 spotted it ("캔버스 탭
  이름은 왜 변수명인가요?").
- **Spec impact:** none (bug fix). Honest note: this was a regression I
  introduced in v0.28.3.

### D-2026-05-31-H — Abstract root superclass: hide role/motive/pain on the actor-tree root

> **REFINED by [D-2026-06-15-J].** `motivation` / `pain` are no longer
> actor fields, so the abstract root now hides only `side` (`body`
> stays). `isActorBaseSuperclass` is unchanged; only the hidden field
> set shrinks.

- **What:** On the Actors canvas, the **root superclass** of an
  inheritance tree — an actor that has **no actor parent** (its only
  inheritance parent is the project anchor) **and** has at least one
  actor child — is treated as an *abstract* class (OOP framing). Its
  Inspector **hides** the `side` (역할) / `motivation` (동기) /
  `pain` (어려움) fields. The `body` (노트) field stays.
- **Why:** The user models actors as OOP class inheritance. An abstract
  root superclass carries no concrete role/motive/pain — those are
  attributes of the **concrete subclasses**. Showing them on the root
  is contradictory (every subclass overrides them anyway). A `user`
  with role `user`, motivation, pain, while `Operator` (a child) has
  role `operator`, is the canonical contradiction.
- **Scope (explicit, narrow):** Inspector field *visibility* only on
  the tree root. The inheritance computation (`effectiveActorFields`)
  is **not** changed in this entry — propagation behaviour stays as
  shipped in D-2026-05-31-G; revisit only if the user asks.
- **Not the criterion:** "has children" alone is **not** the test — an
  intermediate concrete class (e.g. `Bana` with `Hero`/`Fans` below it)
  has children yet keeps all its fields, because it has an actor parent
  (`User`). Only the tree **root** is abstract.
- **Alternatives:** (a) hide on any actor with children — rejected
  (would wrongly abstract intermediate concretes like Bana). (b) remove
  the fields from the actor model entirely — rejected (concrete actors
  need them). (c) base-as-synthesis view of children — deferred (bigger
  idea, YAGNI; no consumer yet).
- **Approval:** Accepted by user, 2026-05-31 ("OOP 상속처럼 생각하면
  된다 … 작업은 해야지").
- **Spec impact:** SPEC §Actors §Nodes — new row "Abstract root
  superclass".

### D-2026-05-31-I — Reframe actor `side` field as "Surface / 접점" (access surface)

- **What:** The actor Inspector's `side` field is relabeled from "Side /
  역할 — which side of the value exchange / 가치 교환에서 맡는 역할" to
  **"Surface / 접점"** — *which system the actor accesses*. Options keep
  the operator/user values but read as surfaces: operator → admin
  console, user → app. **i18n text only** (`inspector.field.side`,
  `inspector.fieldHint.side`, `inspector.operatorOption`,
  `inspector.userOption`); the stored enum (`operator`/`user`), the
  domain model, ServiceDetail subject detection (`side === "user"`) and
  layout are all unchanged.
- **Why:** The operator/user split exists because the participants use
  *different systems* — the Operator accesses the operations page to
  manage the service; an end user (Bana) accesses the Banas app. "Role
  in the value exchange" mislabeled that; the real distinction is the
  access surface.
- **Alternatives:** (a) model change — replace operator/user with named,
  free-form systems — rejected (YAGNI; the two surfaces map 1:1 to
  operator/user, and a model change would touch Actor/ActorRef +
  Pydantic + schema parity + ServiceDetail layout). (b) literal label
  "접속 시스템 / Access system" — rejected as clunky; "Surface" is the
  established product/UX term for the interface a participant touches.
- **Approval:** Accepted by user, 2026-05-31 ("접속 시스템으로 잡죠 …
  이쁜 말 … 추천대로합니다").
- **Spec impact:** SPEC §Actors §Nodes — `side` field semantics.

### D-2026-05-31-J — Inherited Surface caption shows the localized label, not the raw enum

- **What:** When an actor inherits `side` (Surface / 접점) from a parent,
  the greyed `↳ inherited from {parent}` caption now renders the
  **localized option label** ("사용자 — 앱" / "user — app"), not the raw
  enum value (`user`). `Inherited` gained an optional `format(raw)` prop;
  the `side` field passes a mapper (operator → admin-console label, user
  → app label). Free-text fields (motivation / pain / body) are
  unaffected.
- **Why:** The enum (`operator`/`user`) is an implementation detail the
  user never typed. Hero (own Surface unset) under Bana ("사용자 — 앱")
  should read "↳ Bana에서 상속: 사용자 — 앱", not "↳ Bana에서 상속:
  user" — surfaced during the v0.31.1 hands-on review.
- **Approval:** Accepted by user, 2026-05-31 ("고치세요").
- **Spec impact:** SPEC §Actors §Nodes — Inheritance row (caption shows
  the option label for the `side` enum).
- **Process note (honest):** during browser verification of this change,
  repeated synthetic node-selection clicks (chrome-devtools
  `evaluate_script` dispatching pointer/mouse events) mutated demo-seed
  `side` values 3× (Operator, Bana, Hero) in `plot-test-v010` (outside
  the repo; restored each time). The fix itself is verified by
  `tests/inspectors/actor-inherited-surface.test.tsx`, not by the
  flaky browser clicks. A real interaction-vs-synthetic-event mismatch
  may be worth a separate look but was not diagnosed here.

### D-2026-05-31-K — Hide the sidebar stencil when no project is active

- **What:** The left-sidebar stencil (`SketchStencil` in `SketchSidebar`)
  is now gated on `activeId` — with no project selected (empty workspace
  / "No projects yet"), the stencil is hidden. Previously it rendered the
  Foundation stencil (미션 / 코어밸류 / 아이덴티티) unconditionally, even
  when there was no project and the main panel showed the empty state.
- **Why:** Found during the hands-on empty-state walkthrough — the stencil
  chips appeared as if a Foundation canvas were open, with nothing to drop
  them onto. The session-tags block above it was already gated on
  `activeId`; the stencil simply missed the same guard.
- **Approval:** Accepted by user, 2026-05-31 ("네 고치세요").
- **Spec impact:** Empty-state behaviour — no stencil without an active
  project.

### D-2026-05-31-L — Workspace discovery + dir-tree endpoints (multi-directory projects, Phase 1)

- **What:** Two read-only server endpoints backing the upcoming
  multi-directory-projects feature (a monorepo holds many Novel projects,
  each in its own subdirectory with its own `.plot/`):
  - `GET /api/workspace/projects?project_path=<root>` → recursively
    discovers every valid project anywhere under the root, each with its
    directory relative to the root (`"."` for root-level).
    `WorkspaceDiscoveryResponse{projects:[{project,dir}], migrated}`.
  - `GET /api/workspace/tree?project_path=<root>` → nested `DirTreeNode`
    tree (`name`/`rel`/`has_plot`/`children`) for the new-project picker.
  - MCP mirror tool `discover_workspace_projects`.
- **Why:** Decided during the hands-on empty-state walkthrough — feasible
  now in the browser because the server already has filesystem access to
  the launch root (selection is constrained to subdirs under it). Off-root
  absolute paths remain a future Mac-app concern (PRODUCT_SPEC §2).
- **Design:** TWO endpoints (different shapes + cost profiles + cadence —
  discovery on launch/stale, tree only when the picker opens). Pure helpers
  in `workspace.py` (`discover_projects`, `build_dir_tree`, shared
  `enumerate_projects` — extracted from the project-scan loop that was
  duplicated in `projects_list_endpoint` + the `list_projects` MCP tool,
  AHA 3rd-use). Prune set `{.git, node_modules, .venv, __pycache__, dist,
  build, .plot, .mypy_cache, .pytest_cache, .ruff_cache}` + all dotdirs;
  `.plot` read as a marker but never descended into. Depth cap 8, project
  cap 500, tree depth 6, tree breadth 200; `followlinks=False`. Backward-
  compat: a single-root project at `<root>/.plot` surfaces as `dir="."`.
- **Parity:** the new response models are NOT node-kind classes → outside
  the 15-kind `test_schema_parity.py` harness; their TS mirrors are guarded
  by the Phase 2 viewer vitest + tsc (documented, not auto-checked).
- **Approval:** Accepted by user, 2026-05-31 (approved plan — "통합 탐색식
  + 중첩 폴더 트리").
- **Spec impact:** none yet (server-only plumbing; user-visible behaviour
  lands in Phase 2 with the unified sidebar + effective-path refactor).

### D-2026-05-31-M — Multi-directory projects: unified discovery + effective project path (Phase 2)

- **What:** The viewer now treats the launch `?project_path=` as the
  **workspace root** and lists ALL projects discovered anywhere under it in
  one sidebar (each with its dir label). Per-project I/O + the WebSocket use
  the **effective project path** (`root + project dir`), so projects in
  different subdirectories each read/write their own `.plot/`. The "New
  project" button is renamed **"Add a Project"** (en) / "프로젝트 추가" (ko).
- **Why:** A monorepo holds many Novel projects, one per package/subdir. The
  flat single-`.plot` model could only show one directory's projects.
- **Key invariants:**
  - `project_path` is no longer a page-load constant — `workspaceRoot`
    (discovery) vs `activeProjectPath` (per-project I/O), the latter derived
    from `activeId` + an id→dir map built by discovery.
  - WebSocket reconnects when the effective path (dir) changes; same-dir
    project switches do not (pinned by `ws-reconnect-on-dir-switch.test.tsx`).
- **Implementation notes (simplifications vs the plan):**
  - Discovery + the id→dir map are folded INTO `useProject` (no separate
    `useWorkspace` hook) — KISS; `useProject` already owned the project
    list, and folding avoids a cross-hook cycle. A `dirMapRef` mirrors the
    map synchronously so the initial open reads the right dir before the
    state re-render.
  - URL keeps just `?project=<id>` (no `?dir=`); the dir is resolved from
    discovery. Project ids are `proj-<base36 ts>` so cross-dir id collisions
    are astronomically unlikely; first match wins (accepted).
- **Approval:** Accepted by user, 2026-05-31 (approved plan; "Add a Project"
  label confirmed mid-build).
- **Spec impact:** SPEC §"Workspace & projects".

### D-2026-05-31-N — "Add a Project" directory-tree picker (Phase 3)

- **What:** The "Add a Project" button opens a `DirTreePickerModal` — a
  drill-down folder tree rooted at the workspace root (`/api/workspace/
  tree`), each dir flagged `has_plot`. Picking an **empty** dir creates a
  new project there (`useProject.create(targetDir)` → `createProject` at
  `root + dir`); picking a dir that **already holds** a project lands in
  its most-recently-updated one (no duplicate). The button label per dir is
  "Open" when `has_plot`, else "Create here".
- **Why:** Completes the multi-directory feature — the user chooses WHERE a
  project lives instead of every project landing at the root.
- **Scope / decisions:**
  - Tree-only (choose from existing folders); no free-text new-folder entry
    (YAGNI; also sidesteps a path-traversal entry point).
  - "Already has a project" → land in the most-recent (summaries are
    newest-first); does not create a second project in the same dir even
    though one `.plot/` can legally hold many.
  - Open-state lives in `useDirPicker` (hook) so `App.tsx` grows only by
    the import + hook call + `{dirPicker.modal}` render.
- **LOC ceiling:** `App.tsx` 495 → **497** (structural-guards) for that
  plumbing — open-state is in the hook, not App.
- **i18n:** new top-level `dirPicker.*` block (en + ko). (First authored
  nested under `sidebar.*`; moved to top-level when the browser showed raw
  keys — the parity test only checks en↔ko, not key-path resolution.)
- **Approval:** Accepted by user, 2026-05-31 (approved plan).
- **Spec impact:** SPEC §"Workspace & projects" — Add a Project.

### D-2026-05-31-O — Header shows the active project's relative dir (Phase 4)

- **What:** The header's path slot shows the **active project's directory**
  relative to the workspace root (e.g. `marketing`; `"."`/none → the
  localized "root" label) instead of the absolute workspace path. The
  absolute root is preserved as the hover `title`.
- **Why:** Closes the user's original observation that the raw absolute
  path in the header is developer clutter — the meaningful locator is which
  project (and where) is open. New `Header.projectDir` prop, fed
  `dirForId(activeId)`. Reuses the `sidebar.rootDir` i18n label.
- **LOC ceiling:** `App.tsx` 497 → 498 (structural-guards) for the one
  added prop line.
- **Approval:** Accepted by user, 2026-05-31 (approved plan; resolves the
  earlier "경로가 필요한가" header question).
- **Spec impact:** SPEC §"Workspace & projects" — URL/header note.

### D-2026-05-31-P — Workspace root → tab-bar center; socket label "MCP: live"

- **What:** (1) The workspace root absolute path moves from the header to
  the **center of the canvas tab bar**; the header left is just `PLOT ·
  {project} {version}` (the active project's dir is already shown in the
  sidebar subtitle, so it's redundant in the header). (2) The socket
  indicator is prefixed **"MCP:"** — "MCP: live" / "MCP: connecting…" /
  "MCP: reconnecting…" / "MCP: offline" — so it's clear the dot reflects the
  MCP server connection, not "the project is live".
- **Why:** User, reviewing the v0.34.1 header: the per-project dir in the
  header is "the selected one" (redundant with the sidebar); if the root is
  shown, put it centered in the tab bar. And the bare "live" was unclear
  (the user didn't know what it meant) — "MCP: live" was agreed earlier.
- **Supersedes:** D-2026-05-31-O (header relative-dir display) — that prop
  is removed; the dir lives only in the sidebar now.
- **Approval:** Accepted by user, 2026-05-31 ("필요 없고 표시한다면 탭바에
  센터에 표시하세요" + "live … MCP: live 이렇게 표시하기로 했잖아요").
- **Spec impact:** SPEC §"Workspace & projects" — Chrome.

### D-2026-05-31-Q — Swap: workspace path → header (next to PLOT); project name → tab-bar center

- **What:** The **workspace root path** is shown next to the `PLOT` logo at
  the very top (the location / "where am I"); the **active project name** is
  shown centered in the canvas tab bar (the "what am I working on"). This
  swaps the v0.34.2 layout (which had the root in the tab-bar center and the
  project name in the header).
- **Why:** User: *"PLOT 로고 옆에 나오는 프로젝트 이름에 경로를 넣고, 경로
  나오는 곳에 프로젝트 이름 넣으라구요"* — location belongs at the very top;
  the project name belongs centered in the tab bar.
- **Supersedes:** D-2026-05-31-P (placement) — root no longer in the tab
  bar; D-2026-05-31-O (header relative-dir) stays superseded. The socket
  "MCP:" prefix from P is unchanged.
- **Approval:** Accepted by user, 2026-05-31 (explicit swap instruction).
- **Spec impact:** SPEC §"Workspace & projects" — Chrome.

### D-2026-05-31-R — Foundation + Actors: all arrows converge on the anchor; symmetric connect handles

- **What:** On the Foundation + Actors canvases every directed edge's
  arrowhead points at the **anchor-ward endpoint** (nearer the project
  anchor by BFS hop-distance), however the edge was drawn. Foundation
  elements compose INTO the service (anchor); actors PARTICIPATE in it; the
  actor inheritance tree's child→parent edges point up toward the root.
- **Why:** The arrows looked inconsistent / sometimes pointed away from the
  anchor, and starting a connection from a different side of a node produced
  edges in different directions (the node's four handles were asymmetric:
  Top/Left = target, Right/Bottom = source). User: every arrow must point at
  the anchor, and starting from any connection point must produce the same
  edge.
- **How (three parts):**
  1. **Symmetric handles** — all four sides are now `source` handles
     (`BaseNode`); `ConnectionMode.Loose` lets them receive too, so a drag
     can start from any side identically. Floating edges already ignore
     handle ids for rendering.
  2. **Creation normalization** — `handleConnect` (Foundation/Actors) flips
     a new edge so its `target` is the anchor-ward endpoint, then derives
     `relation` from the post-flip source kind. Stored data is correct
     going forward (inheritance child→parent preserved).
  3. **Render enforcement** — `edgeTransform` swaps the RF source/target so
     `markerEnd` lands on the anchor-ward end for ANY stored edge (fixes
     legacy/backwards edges visually; the doc edge stays the SSOT).
  - Shared pure helper `canvases/sketch/anchorDistance.ts`
    (`anchorDistances` BFS + `sourceIsAnchorWard`).
- **Scope:** Foundation + Actors only (`canvas_kind`); Services /
  ServiceDetail keep user-chosen direction.
- **Approval:** Accepted by user, 2026-05-31 (repeated instruction:
  "모든 화살표가 앵커를 향해야" + "어느 연결점에서 시작해도 그렇게
  만들어져야" + "상하좌우 연결점 동작이 다 다르다").
- **Spec impact:** SPEC §Actors §Edges (+ applies to Foundation §Edges).

### D-2026-05-31-S — Floating edges render as bezier curves

- **What:** ``FloatingEdge`` now draws a **bezier** path (was a straight
  line). The control points leave each node perpendicular to the border
  side the floating endpoint exits (computed by the new pure
  ``floatingEdgeGeometry.borderSide``). Off-axis / diagonal edges curve
  gently; axis-aligned edges (the bezier control points stay collinear)
  still read straight — clean, not forced.
- **Why:** User: floating-edge UX is good but "선이 다 직선으로만 되는데 …
  이쁘게 좀 보이게" — straight diagonals (esp. the actor inheritance tree)
  looked harsh.
- **Approval:** Accepted by user, 2026-05-31.
- **Spec impact:** SPEC §Edges (floating edges are curved).

### D-2026-05-31-T — Round anchor uses its ellipse border (arrows stop floating off it)

- **What:** ``floatingEdgeGeometry.nodeBorderPoint`` is now shape-aware. The
  round project anchor (and any circle/ellipse node) computes the floating
  endpoint on its actual **ellipse circumference** (ray-from-centre ∩
  ellipse) instead of its bounding rectangle. ``FloatingEdge`` reads each
  node's ``data.shape`` and passes ``"ellipse"`` for circle/ellipse.
- **Why:** With the v0.34.5 bezier curve, edges approach the round anchor at
  an angle; the old rectangle approximation put the endpoint on the box edge
  (off the circle), so the arrowhead **floated** off the anchor. User caught
  it: "앵커가 네모나다고 판단해서 화살표가 붕 뜨는거죠?".
- **Approval:** Accepted by user, 2026-05-31.
- **Spec impact:** SPEC §Edges (round anchor border).

### D-2026-05-31-U — Blueprint version belongs to the project (tab-bar), not the repo path; one-line status cluster

- **What:** (1) The blueprint version badge moves from the header (next to
  the workspace path) to the **tab-bar center, next to the project name**.
  (2) The header status cluster (save / socket / error) drops its fixed
  ``w-72`` and uses ``whitespace-nowrap`` + ``shrink-0`` so "저장 중…" never
  wraps to two lines; the error is the only flexible (truncating) item.
- **Why:** User: *"프로젝트에 버전이 들어가야죠. 맨 위에 경로는 플롯
  플러그인이 설치된 리포지토리 정도라고 생각하면…"* — the top path is the
  REPO; a per-project version doesn't belong beside it. And: *"저장중 이거
  두줄로 나오죠? 한줄로 나오게 넓게 가져가세요."*
- **Approval:** Accepted by user, 2026-05-31.
- **Spec impact:** SPEC §"Workspace & projects" — Chrome (version with the
  project name in the tab bar).

### D-2026-05-31-V — Floating-canvas auto-layout: angle-preserving depth rings (option A)

- **What:** The `layoutAlgo="tree"` anchor path stops running the
  handle-based directional tree (`autoLayout.ts`) and instead calls
  `computeRadialLayout` with a new `angleMode: "preserve"`. Preserve mode:
  (1) BFS from the anchor assigns each node a **depth ring**, and the ring
  radius is its distance from the anchor — so a deeper node always sits
  farther out (no edge crossing); (2) each node keeps its **current angle**
  from the anchor centre — the side the user placed it on is preserved (no
  swap). This is the shared anchor path, so it covers Foundation + Actors
  directly and Services + ServiceDetail as their no-subject-edge fallback
  (the actor-anchored layout still claims a doc first when it has a subject
  edge).
- **Why:** Two confirmed layout bugs on the floating canvases. All edges
  are floating (D-2026-05-31-F) so their handles are nulled; the old tree
  read stale/arbitrary handles → (a) **swap**: Core value LEFT + Mission
  TOP came back swapped; (b) **crossing**: on `anchor ← user ← operator`
  the depth-2 operator landed between anchor and user. Angle-preserve +
  depth-ring fixes both by construction.
- **Alternatives considered:**
  - *Make `buildAdjacency` always use `inferDirection`* (minimal). Fixes
    both reported bugs but leaves distance to the tree's subtree packing,
    which still trusts current positions for depth. Rejected: depth-ring
    radius is the more robust, deterministic guarantee and was the recorded
    plan.
  - *Option (B): revert floating edges to handle-based rendering.* Brings
    back the asymmetric-handle awkward-loop problem (the thing floating
    fixed in v0.30.3) and loses v0.34.4–.6. Deferred to the user's review;
    `autoLayout.ts` is kept (unit-tested) as that fallback.
- **Scope note (surfaced to user):** the touched gate is the shared
  `useAutoLayout` anchor path, so the change reaches Services/ServiceDetail's
  fallback too, not only Foundation/Actors. This is consistent — floating
  edges are global, so handle-unreliability (the root cause) is global — but
  it is a slightly wider blast radius than the literal "foundation + actors"
  wording of the task.
- **Approval:** **Accepted by user, 2026-05-31** — hands-on reviewed in the
  dev browser on plot-test-v013, confirmed *"괜찮게 됐네 굿!"*. Option (A)
  kept; floating edges are NOT reverted (option B not taken). `autoLayout.ts`
  stays only as a dormant fallback.
- **Spec impact:** SPEC §Auto-layout — table + new "Angle-preserving depth
  rings" subsection; handle tree demoted to retained fallback.

### D-2026-05-31-W — In-app dialog system replaces native browser popups

- **What:** New `viewer/src/shell/dialog/` (`DialogProvider` + `useDialog()`)
  with a promise-based imperative API — `confirm()` → `Promise<boolean>`,
  `prompt()` → `Promise<string|null>`, `alert()` → `Promise<void>`. One
  styled modal renders at a time (matches DirTreePicker chrome; `danger`
  variant = rose). Mounted around `<App>` in `main.tsx`. All 13 native
  `window.confirm` / `window.alert` / `window.prompt` call sites migrated to
  it; a structural guard bans the native forms in `src/` henceforth.
- **Why:** User: *"브라우저 기본 팝업? 워닝 모달? 이거 없앱시다. 세련되지
  않아 보여요"* — the native popups are unstyled and break the app's look.
  Five call sites also carried hardcoded English strings; the migration
  routes them through i18n (en + ko), closing an i18n gap at the same time
  ([[feedback_plot_global_service]]).
- **Design choice:** promise-based imperative API (not per-component local
  modal state) so a call site reads almost exactly like the native call it
  replaces (`if (await dialog.confirm(...))`), and a single provider owns
  all styling (SSOT / consistency). Missing-provider throws only when a
  method is *called*, not at `useDialog()` — so render-only unit tests need
  no provider wrapper (kept the blast radius off ~90 existing tests).
- **Approval:** Accepted by user, 2026-05-31 (*"이쁘게 따로 다이얼로그
  만들어서 진행합시다"*). Browser-verified: delete-project confirm renders
  styled, cancel preserves the project.
- **Spec impact:** none (UI chrome, no canvas-behaviour change). Guarded by
  `structural-guards.test.tsx` "no native browser dialogs".

### D-2026-05-31-X — `has_plot` means "holds a real project", not ".plot folder exists"

- **What:** `build_dir_tree`'s `has_plot` flag (Add-a-Project directory
  picker) changes from `(path / ".plot").is_dir()` to
  `len(enumerate_projects(path / ".plot")) > 0`.
- **Why:** User: *"프로젝트가 만들어지는게 좀 이상해요."* A stray read
  creates an empty `.plot/` (`resolve_plot_root` + `watcher.start` both
  `mkdir`). With the old flag, an empty `.plot/` read as `has_plot: true`,
  so the picker labelled the dir **열기** (open). The viewer's `create()`
  is already an open-or-create fork (open if a matching project is in
  `summaries`, else create), but an empty `.plot/` has no project in
  `summaries` → the "열기" click fell through to **create**, producing a
  phantom new project. Tying `has_plot` to the validated `enumerate_projects`
  scan (the same one the sidebar lists) makes `has_plot` true ⟺ there is
  something actually openable, so the 열기/생성 fork is honest.
- **Model context:** the monorepo case ([[project_plot_project_creation_model]])
  — Banas + Banana built side by side, each app service with its own
  `.plot/` in its subdir. The picker must read each subdir's open/create
  state correctly.
- **Rejected (deferred) — option B, lazy `.plot` creation:** stop
  `resolve_plot_root` + the watcher from `mkdir`-ing `.plot` on read, so the
  empty-folder *litter* never appears. Deferred because watchdog requires
  the watched dir to exist, so the watcher needs a rework (watch the parent
  until `.plot` appears, or start lazily after first project create). Option
  A fixes the user-visible bug without that surgery.
- **Approval:** Accepted by user, 2026-05-31 (chose option A over B in an
  ASCII comparison table).
- **Spec impact:** SPEC §"Workspace & projects" — has_plot semantics (if a
  picker subsection exists; otherwise none — server-internal flag meaning).
- **Note:** pre-existing unrelated red `test_pre_commit_gate` (god-dispatch
  scan over `useFlowHandlers.ts`) is failing since before this change — not
  introduced here; tracked separately.

### D-2026-05-31-Y — Creating a project prompts for its name (web viewer)

- **What:** `useProject.create(targetDir)` now opens the in-app
  `dialog.prompt` for a name before calling `createProject`, instead of the
  hardcoded `"Untitled"`. Cancelling the prompt (`null`) aborts creation. The
  open-existing branch (the chosen dir already holds a project) is unchanged
  and does NOT prompt.
- **Why:** silently naming every new project "Untitled" was poor UX; the name
  is the first thing the user wants to set. Now that the dialog system exists
  (D-2026-05-31-W) the prompt is one line + reuses the styled modal.
- **Approval:** Accepted by user, 2026-05-31 (*"둘다 만들어두세요"* — the web
  half of the project-creation workflow). Part of
  [[project_plot_project_creation_model]].
- **Spec impact:** none (UX). Covered by `project-create-name.test.tsx`.

### D-2026-05-31-Z — `/mashbill-new-project` skill (create a project in a chosen dir)

- **What:** new user-invocable skill `skills/mashbill-new-project/SKILL.md`. It
  creates a Novel project in a directory the user picks and opens it. Steps:
  resolve the workspace (monorepo) root → pick the target subdir (ask, or use
  `discover_workspace_projects` to show what already exists; never invent a
  dir) → ask a name → build a unique `project_id` → `create_project_tool` →
  `open_canvas`. Reports the on-disk `{dir}/.plot/{id}/` location.
- **Why:** the MCP/skill front door to project creation, mirroring the web
  viewer's "+ Add a Project" picker. The user wants BOTH front doors
  (*"아 둘다 있어야하는데?"*). Built for the monorepo case — plugin installed
  once at the root, each app service (Banas + Banana) with its own `.plot/` in
  its subdir, so the "어디에 만들까?" step is explicit.
- **Distinct from `mashbill-new-sketch`:** that older skill targets the legacy
  sketch model (`create_sketch_tool`, `.plot/sketches/`); this one targets the
  v0.8+ project model (`create_project_tool`, `.plot/{id}/`).
- **Approval:** Accepted by user, 2026-05-31. Part of
  [[project_plot_project_creation_model]].
- **Spec impact:** none (tooling). No automated test (skills are markdown;
  matches `mashbill-new-sketch`).

### D-2026-05-31-AA — Restore "no canvas_kind branching in sketch hooks" via a wrapper prop

- **What:** the `doc.canvas_kind === "foundation" || "actors"` branches that
  v0.34.4 (D-2026-05-31-R) added to `useFlowHandlers` (edge normalization
  toward the anchor) and `useEdgesMemo` (`constrainArrowToAnchor`) are replaced
  by a wrapper-supplied boolean prop `convergeArrowsOnAnchor`. FoundationCanvas
  + ActorsCanvas pass `true`; SketchCanvas threads it into both hooks. The
  hooks no longer read `canvas_kind` to branch.
- **Why:** the v0.15 structural reset (D-2026-05-12-B/G) banned hooks under
  `viewer/src/canvases/sketch/` from branching on `canvas_kind` — canvas
  specificity must arrive as explicit wrapper props (the pattern already used
  by `hideRootServiceNode`, `layoutAlgo`, `showFoldButton`). The
  `pre_commit_gate` reset-check enforces this; v0.34.4 violated it and the gate
  test (`test_pre_commit_gate::test_reset_complete_against_current_repo`) had
  been red since. This restores the invariant honestly instead of weakening
  the gate.
- **Rejected — relax the gate:** allow `canvas_kind` reads in these hooks +
  update the gate. Rejected: the wrapper-prop pattern already exists and is
  cheap; weakening a guard the user deliberately built ([[feedback_no_god_object]])
  to admit a shortcut is the wrong trade.
- **`classifyEdge(canvas_kind, sourceKind)` kept:** it passes the kind as
  *data* to a pure classifier, not a behaviour branch in the hook — the gate
  regex allows it, and it is not god-dispatch.
- **Behaviour:** preserved exactly (FoundationCanvas/ActorsCanvas → true ⟺ the
  old `foundation || actors` test). Browser-confirmed the Foundation arrows
  still converge on the anchor; viewer 714/714 + server 477/477 green.
- **LOC:** SketchCanvas ceiling 490 → 500 (plumbing-only prop threading;
  `structural-guards.test.tsx` note updated).
- **Approval:** Accepted by user, 2026-05-31 (chose option A — thread a prop —
  over relaxing the gate).
- **Spec impact:** none (internal architecture; invariant restoration).

### D-2026-05-31-AB — Category nodes render with rounded corners

- **What:** `effectiveShape` (nodeShape.ts) forces `kind === "category"` to
  `"rounded"`, regardless of stored shape — alongside the existing
  master→rounded / ref→circle / decision→diamond render-time rules.
- **Why:** User: *"서비스 캔버스 보면 카테고리 모퉁이 둥그스럼하게
  만들어주세요."* Category nodes are group headers on the Services canvas;
  the sharp-cornered rectangle looked out of place next to the soft-cornered
  master kinds. Render-time policy keeps it SSOT and applies to existing +
  new categories without a data migration.
- **Approval:** Accepted by user, 2026-05-31. Extends D-2026-05-31-B
  (shape encodes producer-vs-reference).
- **Spec impact:** none (cosmetic render policy). Covered by
  `node-shape.test.ts`.

### D-2026-05-31-AC — "+ New folder" in the Add-a-Project picker

- **What:** the directory picker can create a brand-new subdirectory before
  placing a project in it. New server endpoint `POST /api/workspace/dir`
  (+ `workspace.create_workspace_dir`, path-safe via `resolve_safe_path`,
  idempotent); new client `api.createWorkspaceDir`; each `DirTreePickerModal`
  row gets a **"+ 새 폴더"** button → folder-name prompt → create → `onPick`
  the new rel (which flows into `create()` → project-name prompt).
- **Why:** User: *"폴더 새로 만들어서 추가할 수는 없는건가?"* — previously the
  picker was tree-only (existing dirs only) and `resolve_plot_root` 404'd on a
  missing dir, so a new app service's folder had to be `mkdir`'d outside Novel
  first. The monorepo flow ([[project_plot_project_creation_model]], Banas +
  Banana) needs to start a project in a folder that doesn't exist yet.
- **Two prompts, one flow:** folder name, then project name. Kept separate
  (distinct concepts) rather than one combined field; `onPick(newRel)` reuses
  the existing create-in-dir path so there's no duplicate creation logic.
- **Safety:** `resolve_safe_path` rejects `..`, absolute, and escaping paths;
  `mkdir(exist_ok=True)` is idempotent. Read paths are unaffected (this is an
  explicit create action, not the deferred lazy-`.plot` work of option B).
- **Approval:** Accepted by user, 2026-05-31.
- **Spec impact:** SPEC §"Workspace & projects" — picker can create a new dir.

### D-2026-05-31-AD — Controlled nodes array carries ``selected`` (click selection sticks)

- **What:** ``useNodesMemo`` now takes a ``selectedIds: Set<string>`` and sets
  ``selected: selectedIds.has(n.id)`` on each emitted node. SketchCanvas tracks
  selection as state (updated from RF's ``onSelectionChange``) and feeds it in.
- **Why:** User: *"노드들 클릭하면 바로 선택이 안되요 … 선택되고 해제되고
  이러네."* The ``nodes`` array is controlled (derived from ``doc``); RF resyncs
  each node's ``selected`` to the prop on every re-render. Since the derived
  array never set ``selected``, a click selected the node then the next render
  (Inspector opening) deselected it. Carrying ``selected`` in the controlled
  array is the React-Flow-correct pattern.
- **Approval:** Reported + fix accepted by user, 2026-05-31.
- **LOC:** SketchCanvas ceiling 500 → 515 (selection-state plumbing; follow-up:
  extract a ``useNodeSelection`` hook). **Spec impact:** none.

### D-2026-06-01-A — Auto-layout collision avoidance (no overlapping nodes)

- **What:** ``computeRadialLayout`` gains per-ring collision avoidance: the ring
  radius grows so ``2π·r ≥ count · (node-span + gap)`` (the circumference fits
  all nodes), and ``spreadRingAngles`` fans apart any nodes closer than one
  node-span + gap — preserving relative order, recentred on the cluster's
  middle. Applies to both preserve and distribute modes.
- **Why:** User: *"서비스 캔버스 너무 많은데 이거 정렬하면 노드들이 다
  겹쳐요 … 정렬은 노드들이 겹치지 않게 되어야죠."* The v0.34.8 angle-preserving
  depth rings had no collision avoidance; many nodes the user placed in a column
  share an angle and collapsed onto one ring slot. Measured 11 overlapping pairs
  on the BANAS Services canvas; → 0 after the fix.
- **Approval:** Reported + fix accepted by user, 2026-06-01.
- **Spec impact:** SPEC §Auto-layout — radial depth rings now guarantee
  non-overlap. Covered by ``radialLayout.test.ts``.

### D-2026-06-01-B — Nodes auto-fit content; manual resize removed

- **What:** BaseNode sizes every node to its content (rect kinds fit width
  140–340px; round shapes incl. the anchor fit as `aspect-square`). The
  manual `NodeResizer` is removed. A `ResizeObserver` persists the measured
  size back to the doc (`onResize` → `updateNode`; anchor → `onAnchorChange`)
  so `nodeInternals` (floating edges + auto-layout) and the saved blueprint
  match the visual. `useNodesMemo` no longer sets a fixed `style.width/height`.
- **Why:** User wanted nodes to fit their content always (no manual resize).
  Surfaced + fixed two follow-on regressions in the same arc: floating edges
  attached to the stale provided size (edges floated off shrunk nodes), and
  auto-layout's collision avoidance used the stale size (over-spacing) — both
  resolved by persisting the measured size. Plus the kind tag overlapped the
  label on compact nodes (top-margin fix). The anchor was initially excluded
  but the user wanted it to shrink too ("바나스 앵커는 왜 안줄이죠?").
- **Caveat (accepted):** the on-load first measurement settles each node's
  size through `onDocChange`, adding one undo entry per node until stable.
  Follow-up filed: a non-history measurement-sync path + a `useAutoFitSize`
  hook (BaseNode ceiling raised 270 → 300 meanwhile).
- **Approval:** Reported + fixes accepted by user across 2026-06-01.
- **Spec impact:** SPEC §Nodes — node size is content-driven (no manual
  resize). Structural guard ceiling updated.

### D-2026-06-01-C — Auto-layout is a tree, not radial concentric rings

- **What:** `useAutoLayout` reverts from the v0.34.8 radial depth-ring
  (`computeRadialLayout` preserve) to the Reingold-Tilford tree
  (`computeAutoLayout`). `computeAutoLayout`'s `buildAdjacency` now always
  infers child direction from current positions (handles ignored).
- **Why:** User: the radial laid hierarchy as concentric circles by depth so
  children sat far from parents on outer rings (*"원이 아니라 트리가
  되어야죠 / 상위노드에 가깝게 정렬"*). The tree places each child adjacent
  to its parent (children cluster beside parents). Inferring direction from
  position (not the floating edges' nulled handles) keeps the v0.34.8 fixes
  (no swap / no depth-crossing) without the rings.
- **Supersedes:** D-2026-05-31-V (radial preserve as the tree-canvas layout)
  and the framing of D-2026-05-31-AA's anchor path. `computeRadialLayout`
  remains for `layoutAlgo="radial"`.
- **Approval:** Reported + fix accepted by user, 2026-06-01.
- **Spec impact:** SPEC §Auto-layout — the `"tree"` canvases use the
  position-inferred Reingold-Tilford tree. Covered by `autoLayout.test.ts`.
- **Follow-up:** cross-branch crowding near the anchor can still occur (4
  cardinal directions); tighten.

### D-2026-06-03-A — Injection (essence) nodes never overlap in actor-anchored layout

- **What:** `actorAnchoredLayout` Tier-3 (injection-overlay placement) now
  checks the ≈160 px `targetHandle`-direction slot against every already-placed
  node (actor anchor, dagre steps, earlier injection refs). On collision it
  pushes the ref **further out along the same handle axis** (80 px steps,
  ≤ 24 hops) until clear. The ref stays on its target's column / row — handle
  direction preserved — only its distance grows. Deterministic.
- **Why:** Surfaced in the BANAS sim s-auth detail. Running ⊞ packed the steps
  into a tight LR layout; all three essence refs defaulted to *above* their
  target (their injection edges have no `targetHandle`), so the two refs whose
  targets shared a column piled up on top of each other and the steps. User
  saw the overlapping circles and required: *"적어도 노드가 겹치면 안되구요.
  핸들에 연결 위치로 노드 위치를 정해야해요."* (no overlap; position by the
  connection handle).
- **Scope:** `flow/actorAnchoredLayout.ts` only — the ServiceDetail layout
  path. Confirmed separate from the uncommitted handle-based mindmap work
  (`canvases/sketch/mindmapLayout.ts`, reached only for projectAnchor canvases).
- **Approval:** Approach ("핸들 축으로 밀어내기") accepted by user, 2026-06-03.
- **Spec impact:** SPEC §Auto-layout — new bullet "Injection nodes never
  overlap (v0.40.1)". Covered by `actor-anchored-layout.test.ts` (no-overlap
  pairwise assertion + handle-axis preserved).
- **Follow-up:** when a ref's target sits at the far end of its column, the
  *above* default can push the ref past unrelated steps (long injection edge).
  Setting the injection edge's `targetHandle` to the natural side (e.g. `b` for
  a bottom-branch step) avoids it — a data choice, honoured by this same code.

### D-2026-06-03-B — Actor→entry gap scales with the entry's extent

- **What:** `actorAnchoredLayout` places the entry step at a centre-to-centre
  gap from the actor of `max(ACTOR_ENTRY_GAP=220, actorHalf + entryHalf + 40)`
  along the layout axis (width for LR/RL, height for TB/BT), instead of the
  fixed 220 px. Small nodes keep 220; wide entries get pushed out so they clear
  the actor.
- **Why:** Surfaced in the BANAS sim s-onboard detail. The entry step "닉네임
  입력" auto-fit to ~307 px wide; at the fixed 220 px gap the BANA actor circle
  (168 px) overlapped it by ~18 px after ⊞. Same "no overlap" principle the
  user set in [D-2026-06-03-A], but on the tier-1/2 (actor→entry) placement
  rather than the tier-3 injection overlay.
- **Scope:** `flow/actorAnchoredLayout.ts` only.
- **Approval:** Reported during sim + fix accepted by user ("지금 수정"),
  2026-06-03.
- **Spec impact:** SPEC §Auto-layout — bullet "Actor→entry gap scales with the
  entry's extent (v0.40.2)". Covered by `actor-anchored-layout.test.ts`
  (wide-entry no-overlap assertion).

### D-2026-06-03-C — ServiceDetail direction control is one state-showing toggle

- **What:** The two separate ServiceDetail layout buttons ↔ (LR) / ↕ (TB) are
  replaced by a SINGLE toggle that (a) displays the current layout direction as
  its icon — ↔ horizontal (LR/RL), ↕ vertical (TB/BT) — and (b) flips to the
  other axis on click (horizontal → TB, vertical → LR). Current direction is
  read from the subject-edge handle via the new `detectAnchorDirection(doc)`
  (SSOT; `null` → horizontal default). `LayoutControls` takes a `doc` prop to
  derive it; `SketchCanvas` passes `doc` (+1 line, stays under the 515 ceiling).
- **Why:** User 2026-06-03 — *"정렬 버튼을 누르면 어떻게 동작이 되긴 하는데
  어떤 의미인지 잘 모르겠어요. 누를 때마다 왔다 갔다 하는데 정렬 버튼에 어떤
  상태를 표시해주면 좋을 것 같은데"*. The old two-button design rotated the
  flow LR↔TB with no indication of the current direction; the toggle makes the
  current state legible (ux: Clear Feedback) and removes a button.
- **Approval:** Approach ("방향 토글 하나로 통합") accepted by user, 2026-06-03.
- **Supersedes:** the two-button half of [D-2026-05-30-F] (the
  `setSubjectDirection` + `actorAnchoredLayout` re-run mechanism is unchanged).
- **Scope:** `LayoutControls.tsx`, `actorAnchoredLayout.ts` (new
  `detectAnchorDirection`), `SketchCanvas.tsx` (+`doc` prop), i18n
  (`layoutLR`/`layoutTB` → `layoutNowLR`/`layoutNowTB`).
- **Spec impact:** SPEC §"Direction toggle". Covered by
  `layout-controls.test.tsx` (toggle reflects current direction + flips).

### D-2026-06-03-D — Auto-layout (⊞) button icon is mode-specific

- **What:** The ⊞ auto-layout button shows a mode-specific icon + label: a
  hub-and-branches mark + "마인드맵 정렬" (`canvas.autoLayoutTree`) in tree
  mode (Foundation / Actors / Services), a left→right node-sequence mark +
  "흐름 정렬" (`canvas.autoLayoutFlow`) in flow mode (ServiceDetail). Mode is
  derived from `showDirectionSwitch` (true only on ServiceDetail). Button
  carries `data-layout-mode`. Icons are inline SVG (`TreeIcon` / `FlowIcon`
  in `LayoutControls.tsx`); i18n key `canvas.autoLayout` is replaced by the
  two mode keys.
- **Why:** ⊞ runs a *different* arrangement per canvas (mind-map tree vs
  actor-anchored flow) but one glyph hid which. User 2026-06-03: *"그니까
  봐봐 이거 뭔가 어떤 모드인지 아이콘이 같으니 알 수가 없네"*. Same
  legibility logic as the v0.40.3 direction toggle — show the mode, don't
  make the user guess (ux: Don't Make Me Think). NB: this mode is
  informational (canvas-decided), not a user choice.
- **Approval:** Approach ("모드별 아이콘") accepted by user, 2026-06-03.
- **Scope:** `LayoutControls.tsx`, i18n (`autoLayout` → `autoLayoutTree` /
  `autoLayoutFlow`), `auto-layout-isolation.test.tsx` (button-name query
  updated to `/layout/i`).
- **Spec impact:** SPEC §"Auto-layout (⊞) button icon is mode-specific".
  Covered by `layout-controls.test.tsx` (mode label + `data-layout-mode`).

### D-2026-06-04-A — Auto-layout (⊞) is one action button; mode in tooltip text only

- **What:** ⊞ shows **one mode-neutral "auto-arrange" icon** on every canvas
  (constant shape). The layout it runs still differs per canvas, but that mode
  is named only in the **tooltip text** (`autoLayoutTree` / `autoLayoutFlow`),
  never in the icon shape. Reverts the mode-shaped icons (`TreeIcon`/`FlowIcon`)
  from v0.40.4 to a single `ArrangeIcon`; keeps `data-layout-mode` + the
  mode-specific label.
- **Why:** Giving an *action* button a *mode-shaped* icon (v0.40.4) made it
  read like the direction toggle (↔/↕), whose icon flips on click to switch a
  mode. So users expected clicking ⊞ to switch the mode — but it executes the
  layout (moves nodes). User 2026-06-04: *"그걸 누르면 왜 정렬이 변하냐고"* /
  *"정보를 표시하라구요. 근데 왜 그걸 누르면 변하는거냐구요"*. An icon that
  looks like mutable state but is actually an action trigger is contradictory.
  Only the toggle shows mutable state now; ⊞ is purely an action.
- **Approval:** Approach ("액션 아이콘 하나로") accepted by user, 2026-06-04.
- **Supersedes:** the icon half of [D-2026-06-03-D] (the mode-specific *label*
  + `data-layout-mode` survive; the mode-specific *icon* does not).
- **Scope:** `LayoutControls.tsx` (`TreeIcon`/`FlowIcon` → `ArrangeIcon`).
- **Spec impact:** SPEC §"Auto-layout (⊞) is one action button…". Covered by
  `layout-controls.test.tsx` (same icon in both modes).

### D-2026-06-01-H — Mindmap arm = stored hub-side handle (position is the fallback)

- **What:** The mindmap auto-layout's top-level branch → arm assignment now
  reads, *first*, the **hub-side handle** the branch's edge is pinned to
  (`edge.sourceHandle` / `edge.targetHandle` on the hub end, `t/r/b/l` →
  `U/R/D/L`). The **connection** becomes the control surface: drag a line onto
  the hub's right handle and that branch lays out to the right, regardless of
  where the node box currently sits. When an edge carries no stored hub-side
  handle (legacy floating-era edges nulled to `None`), it **falls back** to the
  node's current side of the hub (the D-2026-06-01-F rule). Truly ambiguous
  (on the hub, no handle) → spread by subtree leaf-count, unchanged.
  `edgeTransform.resolveHandles` is updated symmetrically: a **stored** handle
  wins for edge attachment too, with the geometric facing-side used only when
  an end has no stored handle.
- **Why:** under the pure position rule (D-2026-06-01-F) the only way to move a
  branch to another arm was to physically drag the node box across the hub.
  Pinning the edge to a hub handle is a more direct, intent-carrying control —
  the user says "this branch goes right" by where they attach the line, and
  re-layout honours it even if the box drifted.
- **Alternatives:** keep position-only (D-2026-06-01-F) — rejected, no way to
  redirect an arm without moving the box; per-kind arm rule — already rejected
  in F.
- **Approval:** Design authored + tested 2026-06-01 (the prior session reserved
  this id and wrote `mindmapLayout.ts` / `edgeTransform.ts` + the
  `mindmapLayout.test.ts` cases but never committed or recorded it). Committed
  2026-06-04 at the user's explicit "커밋하고 푸시" instruction. **Supersedes**
  the arm-assignment half of [D-2026-06-01-F] (the within-arm tidy-tree shape
  and the leaf-count spread are unchanged).
- **Scope:** `viewer/src/canvases/sketch/mindmapLayout.ts` (`hubHandleDir`
  primary, `dirFromCurrent` fallback), `viewer/src/canvases/sketch/edgeTransform.ts`
  (`resolveHandles` stored-wins).
- **Spec impact:** docs/AUTO_LAYOUT.md §3 (Arm assignment) + §5 (Edge
  attachment). Covered by `viewer/tests/mindmapLayout.test.ts` (hub-handle
  override + no-handle fallback cases).

### D-2026-06-06-A — Foundation stencil: per-section concept info (ⓘ popover)

- **What:** Each Foundation stencil section header (Mission / Core values /
  Identity) gets an always-visible ⓘ icon next to the title; clicking opens a
  small popover with that concept's definition (mission = 존재의 뿌리/왜
  존재하는가; core_value = 현재의 노력/지금 어떻게 결정하는가; identity =
  쌓여가는 지향/어떤 존재가 되고 싶은가, AI 도출). Concept SSOT =
  FOUNDATION_CONCEPT.md.
- **Why:** users who don't yet know what mission/core_value/identity mean
  must be able to learn it where they place the nodes (VISION: "본질을
  *모르는* 사람이 본질을 찾는다"). User asked "거기에 미션 코어밸류
  아이덴티티가 뭔지 사용자들이 알 수 있어야 해요."
- **Alternatives:** (A) always-visible one-line note under each item —
  cleaner discoverability but more panel clutter; user chose (B) ⓘ popover.
  Caveat raised (pure ⓘ has low discoverability) → mitigated: ⓘ is
  always-visible (not hover-only) and opens on click.
- **Approval:** Accepted by user, 2026-06-06 ("네 좋아요").
- **Scope:** `viewer/src/canvases/stencil/SectionInfo.tsx` (new — ⓘ + click
  popover), `SketchStencil.tsx` `Section` gains optional `info` prop,
  i18n `stencil.info.{mission,coreValues,identity}` (en+ko). Foundation-only.
- **Spec impact:** SPEC.md §"Stencil concept info (ⓘ)". Test:
  `viewer/tests/stencil-concept-info.test.tsx`.

### D-2026-06-06-B — Remove Foundation stencil inline usage-notes (ⓘ replaces them)

- **What:** Removed the inline `note` under the Foundation stencil sections —
  "필요한 만큼 추가하세요" (Mission / Core values) and "속성별로 하나씩 —
  목소리, 에너지, 말투, …" (Identity). Deleted i18n keys
  `stencil.note.addAsManyAsYouNeed` + `stencil.note.identityOnePerAspect`.
- **Why:** with the ⓘ concept popover (D-2026-06-06-A) carrying the meaning,
  the inline note is redundant clutter. User: "옆에 필요한 만큼 추가하세요
  이런건 없어도 될 것 같은데 아이덴티티 옆에 있는 것도 없애죠."
- **Approval:** Accepted by user, 2026-06-06.
- **Scope:** `SketchStencil.tsx` (3 foundation sections drop `note`),
  `i18n/locales/{en,ko}.json` (2 keys removed). Other canvases' notes
  (drop-hints etc.) unaffected.
- **Spec impact:** SPEC.md §"Stencil concept info (ⓘ)". Test:
  `viewer/tests/stencil-concept-info.test.tsx` (no note text on foundation).

### D-2026-06-06-C — mission kind format = label + body (typed fields removed + migration)

- **What:** Implement the mission audit conclusion in code. Remove the typed
  fields `what_we_do` / `why` / `direction` from the `mission` kind; mission
  = `label` (the statement) + `body` (free markdown). Publish output follows
  (data-driven via `SECTION_LABELS` / `FOUNDATION_TYPED_TEXT_FIELDS`).
- **Migration (data-loss guard):** existing mission nodes carry values in the
  3 removed fields. Both server (`MissionNode` `model_validator(mode="before")`)
  and viewer (`Mission.fromJson`) **fold any non-empty what_we_do/why/direction
  into `body`** (appended as `## {label}` paragraphs) before dropping them, so
  no content is lost. `label` is **not** auto-rewritten (parsing risk) — the
  one-line-statement promotion is a manual content step; new nodes get
  label=statement via the inspector.
- **Why:** mission is one indivisible declaration; the 3 typed fields were
  one statement sliced by angle (over-decomposition). See
  `docs/node-format/foundation/mission.md`.
- **Approval:** Accepted by user, 2026-06-06 ("네 일단 들어가봅시다").
- **Scope:** `domain/Mission.ts`, `models.py` (MissionNode +
  FOUNDATION_TYPED_TEXT_FIELDS/FOUNDATION_MD_FIELDS), `schema_export.py`
  (SECTION_LABELS["mission"]), `inspectors/mission`, i18n (remove
  inspector.field.whatWeDo/why/direction + hints). nodes/mission renderer
  unaffected. Tests: server migration + viewer roundtrip/migration +
  test_schema_parity.
- **Spec impact:** SPEC §"Foundation typed-text storage". Follow-ups:
  core_value (do/dont cut), identity (output model) — same pattern, separate
  ships.

### D-2026-06-07-A — identity output model: `status` + `provenance` (evolution deferred)

- **What:** `identity` is an **output** kind (AI-derived from mission + core_value,
  per `docs/FOUNDATION_CONCEPT.md`), so it carries structural output-tracking
  fields the input kinds (mission / core_value) do not. Add two structural fields
  to the `identity` kind:
  - `status: "manual" | "derived" | "confirmed"` (default `"manual"`) — where the
    node sits in the derive→confirm lifecycle. `manual` = hand-authored (the
    current 14 BANAS nodes; graceful degradation). `derived` = AI draft, unconfirmed.
    `confirmed` = AI-derived then user-locked.
  - `provenance: string[]` (default `[]`) — ids of the source nodes (mission /
    core_value / service) this identity was derived from. Traceability = the core
    of "why does the AI say this is us".
  Both are **structural** (not MD prose) → they live in `canvas.json` only, NOT in
  the published `.md` typed-text split, and are NOT added to
  `FOUNDATION_TYPED_TEXT_FIELDS` / `FOUNDATION_MD_FIELDS`.
- **Evolution deferred:** the third proposed output field `evolution` (revision
  history) is **not** implemented this ship. It overlaps git history + `BaseFields.version`
  and has no writer yet (AI derivation is unimplemented). Filed for when an AI-derivation
  writer lands. See `docs/node-format/foundation/identity.md`.
- **Graceful degradation:** identity stays fully usable hand-authored
  (`label` + `description` + `body`, `status="manual"`, `provenance=[]`). The output
  fields are an enhancement layer for when AI derivation is built; they don't gate
  manual authoring. No migration needed — Pydantic / `fromJson` supply the defaults
  for pre-v0.44 nodes that lack the keys.
- **Why:** the user named "identity = output" as Novel's core foundation differentiator
  (`FOUNDATION_CONCEPT.md`, 2026-06-06); defining the target output model now is
  justified even though the AI-derivation writer is staged later.
- **Alternatives:** (a) finalize the doc only, no code (rejected — user chose to
  implement the model). (b) structured `evolution: {at, change}[]` (rejected — new
  nested-object pattern + parser for a field with no writer; YAGNI).
- **Approval:** Accepted by user, 2026-06-07 ("출력모델까지 구현" + "보류" for evolution).
- **Scope:** `domain/Identity.ts` (IdentityJson + class + fromJson/toJson),
  `models.py` (IdentityNode + 2 fields), `inspectors/identity` (status selector +
  provenance list editor), i18n (status label + 3 option labels + provenance
  label/hint). `nodes/identity` renderer unaffected (no status badge this ship —
  YAGNI until derived/confirmed nodes exist). Tests: server defaults/legacy/explicit
  + viewer roundtrip + test_schema_parity.
- **Spec impact:** SPEC §"Foundation typed-text storage" / CONCEPTS identity row.

### D-2026-06-07-B — step3: native project folder picker (Tauri desktop app)

- **Context:** Novel.app (Tauri 2) bundles viewer + mashbill sidecar. The viewer
  reads `?project_path=...` from the URL; without the param it shows a dead-end
  "add URL param" screen — unusable in a .app double-click launch where there's
  no URL bar.
- **Decision:** Extract the no-workspace screen into `shell/ProjectPicker.tsx`.
  Inside Tauri (`window.__TAURI_INTERNALS__` present), render a "Open Folder" button
  that calls `tauri-plugin-dialog` `open({ directory: true, multiple: false })`,
  then redirects to `/?project_path=<selected>`. In browser dev mode, show the
  existing URL-param hint unchanged.
- **Why:** Minimum viable flow: one click → native system dialog → app loads the
  project. No custom file-browser UI, no extra backend endpoints.
- **App.tsx LOC note:** 495 → 487. Under the live ceiling of 498
  (D-2026-05-28-L; an earlier draft of this entry mis-cited 485). Replacing the
  inline placeholder with `<ProjectPicker />` nets -8 LOC.
- **Approval:** User-directed continuation (step3); no additional confirmation needed
  per session memory ("다음 = step3 프로젝트 선택 UI").
- **Scope:** `shell/ProjectPicker.tsx` (new), `App.tsx` (+1 import, -9 inline lines),
  i18n `shell.projectPicker.*` (en + ko), `Cargo.toml` + `lib.rs` +
  `capabilities/default.json` (tauri-plugin-dialog), `@tauri-apps/plugin-dialog` npm.
  Test: `tests/project-picker.test.tsx` (5 cases, TDD Red→Green).
- **i18n namespace fix (2026-06-07):** ProjectPicker shipped with
  `useTranslation("shell")` + unprefixed keys, but the viewer loads a single
  `translation` bundle (D-2026-05-11-D) — there is no `shell` namespace, so every
  key rendered as its raw string ("projectPicker.title" shown verbatim). Fixed to
  `useTranslation()` + full-path keys (`t("shell.projectPicker.*")`). The original
  `project-picker.test.tsx` mocked `t:(k)=>k` and was blind to it; added
  `tests/project-picker-i18n.test.tsx` (real i18n bundle, asserts translated
  text) + a structural guard banning any `useTranslation(<namespace>)` arg
  viewer-wide. Verified: viewer dist rebuilt + `tauri build` .app launched (engine
  :5190 `/api/health` 200; pixel screenshot blocked by screen-recording
  permission, so confirmed via shipped-bundle key check + real-bundle test).
  758 viewer tests green.

### D-2026-06-07-C — light / dark theme via semantic CSS-variable tokens

- **What:** Add a light/dark theme to the viewer. Colour moves from hardcoded
  Tailwind palette classes (547 occurrences across 50 files — `bg-white`,
  `text-slate-*`, `border-slate-*`, plus indigo/amber/emerald/violet accents)
  to **semantic CSS-variable tokens** (`surface` / `surface-muted` /
  `surface-subtle` / `surface-inverse` / `overlay`; `text` / `text-strong` /
  `text-muted` / `text-faint` / `text-inverse`; `border-subtle` /
  `border-strong`; `accent` / `warn` / `ok` / `special`). `:root` = light,
  `.dark` = dark; Tailwind colours map to `rgb(var(--token) / <alpha-value>)`,
  `darkMode: "class"`. Default theme follows OS `prefers-color-scheme`; a
  header toggle sets an explicit `localStorage["plot:theme"]` = light | dark |
  system (mirrors `plot:lang`); the resolved theme toggles `.dark` on
  `<html>`. The dead `ink`/`paper` config colours (0 usages) are removed.
- **Why:** Novel is a global desktop product; dark mode is table-stakes UX.
  Semantic tokens give a single source of truth for colour (SSOT), keep the
  light UI pixel-identical (each token's light value = its current hex), and
  avoid `dark:`-prefix sprawl across every component.
- **Alternatives:** (a) `dark:` prefix on all ~547 spots — Tailwind-native but
  no SSOT, doubles class strings, every new component must remember the pair;
  rejected for maintainability. (b) Redefine the `slate` ramp as var-backed
  with no component edits — lowest churn but semantically fragile (white/black
  + accent special-casing, ramp ≠ clean inversion), high risk of wrong dark
  contrasts; rejected. (c) chosen: semantic tokens.
- **Approval:** Accepted by user, 2026-06-07 (strategy + OS-default picked via
  AskUserQuestion; plan approved "네 승인").
- **Spec impact:** new SPEC §"Appearance — light / dark theme".
- **Plan:** ①infra (tailwind darkMode + token vars + `useTheme` hook + header
  `ThemeToggle`, TDD) → ②migrate 547 occurrences to token classes + structural
  guard banning raw neutral colour classes → ③verify (suite + tsc + light
  regression; dark visual check needs user eyeball — screenshot blocked by
  screen-recording permission, dev-server discouraged per prior user direction).

### D-2026-06-08-A — whole-system clean-architecture migration (per ARCH_REVIEW)

- **What:** Adopt the migration plan in
  [`../../../plot/docs/ARCH_REVIEW.md`](../../../plot/docs/ARCH_REVIEW.md) across the whole system
  (viewer + engine + overhaul direction), in this order, each step keeping the
  app green: ①extract `theme/tokens.css` ②FOUC pre-paint `<head>` script +
  `color-scheme` CSS + parity/`index.html` guards ③zero-dependency `pendingWrites`
  fix (timeout + delete-on-PUT-error + echo guard) ④React-free `src/app` use-case
  ring + "no `api.ts` import outside `src/app`" guard + fix `mdImagePlugin.ts:94`
  seam bypass ⑤`useAppCallbacks` hook to bring `App.tsx` under its LOC ceiling
  ⑥TanStack Query for server state ⑦undo regression-first (project-level unified
  stack) ⑧Zustand single UI store. Overhaul track (parallel): `parseEntity` at
  the WS boundary, C4 licensing boundary, engine `folder_io.py` (1471 LOC) split.
- **Why:** State-management library choice (Zustand + TanStack Query above the
  `api.ts` seam) + a React-free use-case ring make Clean Architecture easy to
  hold as the engine moves in-process (TS, tablet); theme becomes a real
  design-token layer. The cheap Phase-0 steps (①–⑤) retire the worst live bugs
  with zero new dependencies before any library lands.
- **Alternatives:** Phase-0-only (defer the libraries) — rejected by user, who
  chose the full track including the overhaul items. Pragmatic-status-quo
  layering + Redux/RTK Query + typed-TS token SSOT — rejected in ARCH_REVIEW.
- **Adversarial corrections folded in:** `parseEntity` is dead (0 call sites);
  the `api.ts` seam already leaks (5–8 presentation imports + `mdImagePlugin:94`)
  so the use-case ring is meaningless without the import guard; `App.tsx` is
  already 487/485 (over) so new providers add LOC before relief; the WS
  `project_changed` echo to the originating client means an echo guard is still
  required; undo is a project-level unified stack and needs a regression before
  server state moves; the FOUC pre-paint literals hard-duplicate (no ESM import
  pre-paint) and must be guarded, not eliminated.
- **Approval:** Accepted by user, 2026-06-08 ("전체 + 개편 트랙", "네, 권고대로 구현").
- **Spec impact:** none yet (architecture/infra); SPEC unaffected until a
  user-visible behaviour changes.

### D-2026-06-09-A — node-card text stays dark-on-light in both themes

- **What:** A node card's on-card text (label, body, icon, fold toggle,
  untitled placeholder, kind tag), the inline `code` background, and the
  collapsed-children count-chip background no longer flip with the dark theme.
  The card root div gets a `node-card` class; `theme/tokens.css` scopes the
  on-card vars (`--fg`, `--fg-strong`, `--fg-secondary`, `--fg-muted`,
  `--fg-faint`, `--surface-subtle`, `--line`) to that class at their `:root`
  (light) values, so they resolve to the light value even under `.dark`.
- **Why:** A card's background is the user's fixed colour (`data.color`,
  usually a pastel), not a theme surface. In dark mode the text flipped to a
  light foreground and vanished on the still-light card (user: "노드 안에 글자
  색깔은 검은 색으로 그냥 가도 되는데"). Locking on-card colour to light keeps
  the text dark-on-light in both themes with zero change to the light UI.
- **Scope boundary:** only chrome *inside* the card is locked. Handles, the ⚠
  markdown-warning badge, and the selection ring sit outside the card colour
  and still follow the theme.
- **Alternatives:** (a) new explicit `node-fg-*` tokens (7 names + Tailwind map
  + 8 className edits) — more explicit but more surface area; rejected for
  churn. (b) per-component `dark:` overrides on BaseNode — reintroduces the
  raw-palette sprawl the token system removed; rejected. (c) chosen: scope the
  existing fg/bg vars to a `node-card` class — zero className churn, light stays
  1:1, parity-guarded. A prior session half-attempted the `node-fg-*` token
  route and reverted it ("아키텍처 우선"); this is the completed replacement.
- **Approval:** Accepted by user, 2026-06-09.
- **Spec impact:** SPEC §"Appearance" gains the node-card dark-on-light bullet.
- **Tests:** `tests/theme-tokens.test.ts` (`.node-card` vars = `:root` light
  values — parity + light fidelity) + `tests/nodes/base-node-dark.test.tsx`
  (card root carries `node-card`). TDD Red→Green; 816 pass, tsc clean.

### D-2026-06-09-B — hide the React Flow attribution watermark

- **What:** Hide the bottom-right "React Flow" attribution badge on the canvas
  via `proOptions={{ hideAttribution: true }}` on the `<ReactFlow>` element in
  `SketchCanvas`.
- **Why:** Novel ships as a commercial desktop app (OVERHAUL R1/R5/R6); a
  third-party watermark on the user's canvas is off-brand. User asked to remove
  it ("오른쪽 하단에 react flow 라고 나오는거 그거 없앨 수 없나요?").
- **Licence:** `reactflow` (xyflow) is MIT. xyflow *recommends* keeping the
  attribution but does not *require* it; hiding it via the official
  `hideAttribution` option is permitted. Recorded here so the OVERHAUL licence
  audit sees the call was deliberate, not an oversight.
- **Approval:** Accepted by user, 2026-06-09.
- **Spec impact:** SPEC §"Appearance" gains the no-watermark bullet.
- **LOC:** SketchCanvas ceiling 515 → 516 (one added prop); pinned in
  `structural-guards.test.tsx`.
- **Test:** `react-flow-attribution.test.tsx` asserts `.react-flow__attribution`
  is absent. TDD Red→Green; 817 viewer green, tsc clean.

### D-2026-06-09-C — git lives at the workspace (.plot/), not per project

- **What:** Replace the per-project git repo (one `.git` per
  `.plot/{project_id}`) with a single repo at the `.plot/` workspace level. All
  `git_store` operations (`ensure_repo`, `tag_snapshot`, `publish_snapshot`,
  `find_latest_publish_commit`, `revert_publish`) target `.plot/`; `git_store`'s
  `project_dir` parameter is renamed `workspace_root`. Call sites
  (`folder_io.create_project` / `publish_node` / `unpublish_node`,
  `mcp_tools.plot_tag`) now pass `plot_root`.
- **Why:** User: "워크스페이스에만 깃이 있어야 한다". A project is a unit
  *inside* a workspace, not its own VCS root; one workspace = one history = N
  projects. Per-project repos also caused a nested-git problem when the user
  wanted a workspace-level repo.
- **Workspace boundary:** the repo sits at `.plot/` (the direct parent of every
  `.plot/{project_id}`) — Novel's data root — NOT the launch folder
  (`project_path`), so the user's non-Novel files in the launch folder are never
  tracked. SPEC §"Workspace & projects" also describes multi-`.plot` roots; if
  those ever need one shared history, hoisting the repo to the launch root is a
  deferred follow-up (this change collapses per-project → per-`.plot`, the
  decisive step the user asked for).
- **Migration:** none in scope — the user had deleted all playground projects,
  so there were no legacy per-project `.git` dirs to fold in. New workspaces
  init the repo at `.plot/` from the first `create_project`.
- **Approval:** Accepted by user, 2026-06-09 (AskUserQuestion → "지금 바로 구현").
- **Tests:** `test_workspace_git.py` (repo at `.plot/`, not per project; two
  projects share one repo) + updated `test_folder_io` git-wiring tests. 500
  server tests green, ruff + mypy clean.
- **Spec impact:** SPEC §"Workspace & projects" gains the Version-control bullet.

### D-2026-06-09-D — dev-only debug channel for WKWebView introspection

- **What:** A dev-only `/api/debug` engine endpoint (GET/POST, in-memory) + a
  viewer probe (`lib/debugProbe.ts`) that collects on-screen state (theme, React
  Flow watermark presence, per-node computed colour + layout rect) and POSTs it.
  `startDebugProbe()` (wired in `main.tsx`) auto-posts on debounced DOM mutations
  when enabled (`VITE_PLOT_DEBUG=1` or `?debug`). An external agent GETs
  `/api/debug` to read what the screen actually shows.
- **Why:** CDP tools (chrome-devtools, Playwright) cannot attach to the Tauri
  **WKWebView** on macOS, and `tauri-driver` does not support macOS — so the
  assistant could not verify computed colours / layout in the .app (only the
  user's eyes could). This channel bridges that: the viewer reports
  `getComputedStyle` / `getBoundingClientRect` through the engine. (User: "플레이
  라이트나 크롬데브툴 같은 디버깅 툴 제공 안하나?")
- **Boundary:** in-memory, localhost-bound, NOT part of the product surface;
  separate `debug_endpoints.py` module (does not grow the 965-LOC god
  `api_endpoints.py`). Probe is a no-op unless explicitly enabled.
- **Approval:** Accepted by user, 2026-06-09 (AskUserQuestion → "둘 다 (채널 먼저,
  스크린샷 다음)"). A Tauri screenshot command is the next step (Phase 2).
- **Tests:** `test_debug_endpoint.py` (POST/GET roundtrip, overwrite, bad json) +
  `debugProbe.test.ts` (theme / watermark / node collection). 504 server + 820
  viewer green; ruff + mypy + tsc clean.

### D-2026-06-10-A — debug/release flavor split gates every debug surface

- **What:** All debug tooling is flavor-gated at build time, on all three
  layers. **Engine:** `/api/debug` routes register only when `PLOT_DEBUG=1`
  (release = 404). **Viewer:** the probe is enabled only when the bundle was
  built with `VITE_PLOT_DEBUG=1`; the `?debug` URL runtime escape is REMOVED
  (release bundles tree-shake the probe out entirely — verified by grepping the
  built assets). **Shell:** `tauri-plugin-screenshots` becomes an optional
  Cargo dependency behind a `debug-tools` feature; the debug flavor overlay
  `tauri.debug.conf.json` (productName "Novel Debug", identifier
  `me.noory.plot.debug`, frontendDist `dist-debug`, inline `screenshots:default`
  capability) + `-- --features debug-tools` selects it, and the shell spawns the
  sidecar with `PLOT_DEBUG=1` only under that feature.
  - Release: `npx tauri build --bundles app`
  - Debug:   `npx tauri build --bundles app --config src-tauri/tauri.debug.conf.json -- --features debug-tools`
- **Why:** User: "플레이버하고 디버그 릴리즈 모드를 제공해야 디버깅 툴 활성화를
  결정하는건데" — a commercial release binary must carry ZERO debug surface
  (code, routes, permissions), not just a disabled flag. The separate TCC
  identity also keeps the Screen Recording grant off the release app.
- **Capability note:** the debug capability is INLINE in the overlay config
  (not a `capabilities/*.json` file) so release ACL validation never sees a
  permission of the uncompiled screenshots plugin.
- **Approval:** Accepted by user, 2026-06-10 ("그거 까지 고려해서 개발하나요?" →
  구현 지시).
- **Tests:** `test_debug_endpoint.py::test_debug_routes_absent_without_flag`
  (release 404/405) + `debugProbe.test.ts` "?debug does NOT enable" + both
  cargo flavors compile (`cargo check` / `--features debug-tools`).

### D-2026-06-10-B — debug boot beacon in index.html (module-graph-independent)

- **What:** An inline `<head>` script in `index.html`, gated on the build-time
  `%VITE_PLOT_DEBUG%` HTML env replacement, that POSTs `{beacon:"boot"}` on
  page parse and wires `error` / `unhandledrejection` reporters to
  `/api/debug`. Additions to the module-graph probe in the same change: a 10s
  heartbeat (the first POST can race the sidecar's startup and POSTs are
  fire-and-forget; a static screen would otherwise never re-post) and a 1.5s
  time-box on the screenshot call (without a TCC grant the plugin call can
  stall — it must not hold the numeric probe hostage). Probe also gained
  sizing-diagnosis fields (`inline` style, computed `aspect`, parent wrapper
  box) and the on-card `classes` string.
- **Why:** During flavor bring-up the channel stayed silent and the cause was
  indistinguishable between "page never loaded", "bundle crashed at import",
  and "engine down". A beacon independent of the module graph splits those
  cases without needing eyes on the window.
- **Approval:** Accepted by user, 2026-06-10 (디버깅 툴 트랙 일괄 승인 하에).
- **Tests:** `debug-beacon.test.ts` (gated inline script present, posts boot +
  error reports) + `debugProbe.test.ts` heartbeat + hanging-capture cases.
  End-to-end verified in the debug-flavor .app: boot beacon + 10s heartbeats
  received, screenshot captured under the `me.noory.plot.debug` identity.

### D-2026-06-10-C — ARCH step 8 (Zustand UI store) retired: premise no longer holds

- **What:** Do NOT adopt Zustand. ARCH_REVIEW (D-2026-06-08-A) step 8 — "one
  UI store, last" — is closed as obsolete rather than implemented.
- **Why (measured, not guessed):** the step's premise was "UI state scattered
  across App.tsx". After steps 4–6 the audit shows App.tsx holds exactly TWO
  raw UI `useState`s — `error` (line 69) and `helpOpen` (line 200) — each
  consumed one level deep. Everything ARCH_REVIEW listed for the store
  (`activeTab` / `detailServiceId` / `selectedNodeId` / `viewingTag`) already
  lives in `useUrlSync` / `useSnapshotView` where **the URL is the SSOT**;
  mirroring URL-synced state into a store would create a second source of
  truth (SSOT violation), and a new dependency for two booleans is YAGNI.
  ARCH_REVIEW itself flagged the risk: "Two new deps under YAGNI — defer
  until tablet justifies."
- **Also closed:** step 6c (canvas PUT → `useMutation` optimistic/rollback)
  stays NOT-adopted — the debounced `putCanvas` + echoGuard + project-level
  undo stack already cover its value; revisit only if a real rollback gap
  appears.
- **Re-open trigger:** real prop-drilling pain (a leaf needing App state ≥ 3
  levels deep) or the tablet shell sharing UI state across surfaces.
- **Approval:** decided autonomously 2026-06-10 under the user's "트랙0,1,2 쭉"
  directive; recorded for explicit user review (override = reopen ARCH step 8).

### D-2026-06-10-D — folder_io god-module split (1413 → facade + 6 modules)

- **What:** `folder_io.py` (1413 lines, 3x the monorepo 500-line rule) is split
  along its own section headers into `storage.py` (paths + atomic JSON +
  ProjectDoc read/write), `canvas_migrations.py` (read-path healing: lazy
  migrations, foundation-MD absorb, legacy anchor eviction),
  `canvas_io.py` (read/write_canvas, list_service_details), `project_io.py`
  (seeds, create/rename/delete), `detail_sync.py`, `node_publish.py`
  (publish/unpublish). `folder_io.py` becomes a pure re-export facade — every
  name, including the private helpers tests/endpoints import, keeps its
  import path; zero call-site changes.
- **Why:** SoC rule (review/split at 500 lines) + ARCH_REVIEW deferred-track
  item. Dependency shape is now one-way: storage ← migrations ← canvas_io ←
  {project_io, detail_sync, node_publish}. `read_project`/`write_project`
  moved into `storage.py` to keep that acyclic (canvas healing needs them).
- **Guard:** new `tests/test_module_size.py` — every engine module ≤ 500
  lines; the facade ≤ 180 (re-exports only); pre-existing god modules
  (`models.py` 993, `api_endpoints.py` 965, `migrate.py` 916) are
  GRANDFATHERED as a ratchet (may shrink, never grow) with a companion test
  that forces removing the ratchet entry once a module is split — tracked in
  ROADMAP Track 1.4.
- **Behaviour change:** none — pure refactor; 508 server tests green
  (505 + 3 new guards), ruff + mypy clean. Sidecar rebuild not required
  (no behaviour change); the new modules ride the import graph on the next
  PyInstaller build.
- **Approval:** executed autonomously 2026-06-10 under "트랙0,1,2 쭉"
  (ROADMAP Track 1.4 item).

### D-2026-06-10-E — wire-contract snapshot: split-survivable schema parity

- **What:** The server↔viewer wire contract (base fields + full field set of
  each of the 15 kinds, Pydantic = SSOT) is exported as a diffable JSON
  snapshot, committed TWICE: `mashbill/wire_contract.json` (engine) and
  `viewer/src/schema/wire-contract.json` (viewer). Each side verifies its own
  sources against its own copy — engine: `tests/test_wire_contract.py`
  (generated == committed); viewer: `tests/wire-contract.test.ts` (TS `XxxJson`
  interfaces == committed, regex parser ported from the Python test, plus a
  drift self-check). Regenerate: `uv run python -m mashbill.schema_export
  --wire`. A monorepo-only test pins the two copies byte-identical; at repo
  split it moves to the release pipeline.
- **Why:** TECH_REVIEW separation-sequence step 1 — `test_schema_parity.py`
  reads BOTH sides from disk and silently dies when `viewer/` leaves the
  monorepo. The snapshot makes the contract survive the repo boundary. The
  old test stays alive while the monorepo lasts (belt + braces).
- **Scope note:** the edge-semantics / publish-eligibility *rule* mirrors are
  NOT in the snapshot — they are logic (pinned by each side's own behaviour
  tests, nothing dies at split). Extracting them as data tables is a separate
  follow-up if rule drift ever bites.
- **Approval:** executed autonomously 2026-06-10 under "트랙0,1,2 쭉"
  (ROADMAP Track 2.1).
- **Tests:** +3 server (snapshot match / shape / monorepo sync), +18 viewer
  (base + 15 kinds + union size + drift self-check).

### D-2026-06-10-F — R8 build guard + commercial licence audit

- **What (R8 guard):** `tests/test_r8_independence.py` AST-parses every
  `mashbill/*.py` import and fails on any root in {viewer, app, src_tauri,
  tauri, evonest, distill, solera, solera_mcp}; also bans `src-tauri` path
  literals. The one forbidden dependency direction (plugin → app, OVERHAUL R8)
  is now machine-enforced on the engine side, mirroring the viewer's
  structural-guards. `workspace.find_viewer_dist()` stays allowed — optional
  asset discovery with an API-only fallback, not a code dependency.
- **What (licence audit):** `scripts/license_audit.py` (cross-platform Python)
  runs pip-licenses (engine) + `npx license-checker --production --failOn
  GPL;AGPL;LGPL` (viewer). First execution: engine 84 deps / viewer 286
  production deps — **zero blocking copyleft**. Allowlist (verified by hand):
  docutils (tri-licensed, BSD elected), caio (metadata gap, upstream
  Apache-2.0). UNKNOWN licences fail the audit so new gaps can't slip in.
- **Why:** TECH_REVIEW steps 2 + 6 — the MIT/proprietary boundary is defended
  by build guards (file layout can't), and dependency permissiveness was
  believed but never machine-verified. Both now are.
- **Out of scope:** the single-owner CLA (blocked on D-4 법인 주체); replicating
  the R8 guard into evonest/distill/solera packages (each is an independent
  package — ROADMAP 2.2 note); CI wiring (no pipeline infra in the repo yet).
- **Approval:** executed autonomously 2026-06-10 under "트랙0,1,2 쭉"
  (ROADMAP Tracks 2.2 / 2.6).

### D-2026-06-10-G — R9: plot data root moves to `<workspace>/.noory/plot/`

- **What:** `resolve_plot_root` now resolves `{project_path}/.noory/plot/`
  (was `{project_path}/.plot/`). A legacy `.plot/` root is migrated lazily on
  first access via one `shutil.move`; if BOTH roots exist (half-migrated /
  user-restored), `.noory/plot` wins and `.plot` is left untouched — never
  merged blindly. Workspace discovery + the dir-tree `has_plot` badge check
  `.noory/plot` first and peek read-only at legacy `.plot` (a never-opened
  workspace still shows its projects; migration happens on open). `.noory` is
  pruned from discovery descent. User-facing strings (plugin description, MCP
  tool docs, monorepo CLAUDE.md) updated.
- **Why:** OVERHAUL R9 (pinned) — all plugin artifacts consolidate under ONE
  `.noory/` dotfolder per workspace so plugin mode and app mode share
  artifacts continuously. Option A (per TECH_REVIEW): resolver change + lazy
  migrate-on-read.
- **Scope:** plot engine only in this change. distill (`PROJECT_SUBDIR` ~9
  sites; global `~/.distill` tier does NOT move), evonest (8–10 leak sites),
  solera (single resolver) follow as separate per-package changes (ROADMAP
  Track 2.3).
- **Approval:** executed autonomously 2026-06-10 under "트랙0,1,2 쭉"
  (ROADMAP Track 2.3; R9 + Option A + distill-global-tier pinned earlier).
- **Tests:** `tests/test_noory_migration.py` — new root location, lazy
  migration moves (not copies), no-clobber when both exist, discovery sees
  new + legacy-only roots. 519 server green, ruff + mypy clean.

### D-2026-06-10-H — finish the workspace-git move (8 missed call sites)

- **What:** The tag list/create/delete endpoints, the at-tag reader, the
  blueprint-publish tag, and three MCP tool paths still passed
  `plot_root / project_id` to git ops after D-2026-06-09-C — and
  `tag_snapshot`'s self-heal silently re-created a per-project repo,
  re-introducing the layout the user had retired. All git operations now
  target the workspace repo; the at-tag reader prefixes paths with
  `{project_id}/` (files in the workspace repo sit under the project dir).
- **Why missed:** v0.53.0's tests only pinned `create_project`'s repo
  location; the endpoints kept passing because the self-heal made the old
  layout work. New regression tests assert the ABSENCE of a per-project
  `.git` after endpoint-driven tagging + an at-tag round-trip.
- **Approval:** bug fix under the pinned D-2026-06-09-C decision, 2026-06-10.

### D-2026-06-11-A — Round cards use flex column, not `h-full` on the inner (WebKit aspect-ratio fix)

- **What:** `BaseNode`'s round-shape sizing (`circle`/`ellipse`, incl. the
  project anchor) now puts `flex flex-col justify-center` on the card root
  itself and drops `h-full` from the inner content div. Vertical centering
  is enforced by the card's flex layout, with zero percentage-height
  dependency. Static guards in
  `viewer/tests/nodes/round-card-no-percent-height.test.tsx` pin both (card
  carries the flex classes; no descendant uses `h-full`) per shape.
- **Why:** Tauri's WKWebView resolved
  `width:fit-content + min-width + aspect-ratio + h-full child`
  into a non-square box — the anchor measured 96×132 instead of 96×96
  (`132 = 96 + 32 py-4 + 4 border-2`). Live evidence from the debug probe:
  `box-sizing: border-box` (so border-box was NOT the cause), `aspect-ratio:
  1/1`, `inner.h = 96`. The `h-full` percentage child fed content-height
  back into the aspect resolution loop. Making the card itself the flex
  container breaks the loop; aspect-ratio then resolves cleanly to 96×96.
- **Probe extensions used to confirm:** `collectProbe` now reports
  `boxSizing`, the first non-handle inner child's `{w,h}`, and the React
  Flow viewport `zoom` (parsed from the `.react-flow__viewport` transform).
  Without these the cause space could not be narrowed.
- **Scope:** viewer only; no engine changes. Persisted anchor sizes from
  prior renders (96×132) self-correct on next render via the existing
  ResizeObserver → `onAnchorChange` plumbing — no migration needed.
- **Approval:** reported by user "고쳐진거는 확인했구요", 2026-06-11.
- **Spec impact:** SPEC §Anchor — new Sizing row added pointing at this
  entry. Pinned by `round-card-no-percent-height.test.tsx`.

### D-2026-06-11-B — God-module split (models.py + api_endpoints.py + migrate.py)

- **What:** The three remaining `mashbill/` god modules (993 + 965 + 916
  LOC = 2874 lines) split along their own section headers into focused
  modules + a thin facade that re-exports every public name. Every engine
  module now sits under the 500-line monorepo SoC rule. The grandfather
  ratchet in `tests/test_module_size.py` is empty as a guard against
  regression. Per-facade tests pin each at ≤ 180 LOC. Call sites
  (`http_app.py`, `canvas_io.py`, `mcp_tools.py`, `endpoints_projects.py`,
  every test file) keep using the facade names — zero import changes.
- **Splits:**
  - `models.py` → `models_kinds.py` / `_foundation.py` / `_actors.py` /
    `_composition.py` / `_union.py` / `_canvas.py` / `_discovery.py`
    (7 modules, each cohesive around one slice of the 15-kind schema).
  - `api_endpoints.py` → `endpoints_common.py` / `_projects.py` /
    `_canvases.py` / `_tags.py` / `_publish.py` / `_files.py`
    (6 modules, one per URL group).
  - `migrate.py` → `migrate_v01_models.py` / `_builders.py` / `_v01.py` /
    `_foundation.py` (4 modules: legacy schema, builders, top-level loop,
    inline Foundation upgrade).
- **Pre-commit gate update:** `hooks/pre_commit_gate.py` previously
  searched `mashbill/models.py` for the SketchNode union body. After the
  split that body lives in `models_union.py`; the gate now scans every
  `mashbill/*.py` so the v0.15 structural reset stays enforced.
- **Why:** Folder_io's v0.56.0 split (D-2026-06-10-D) installed
  `tests/test_module_size.py` as a permanent guard but grandfathered
  these three at their then-size. ROADMAP Track 1.4 listed them as next
  to split; user chose this in tonight's session ("N-3 god 모듈 3개
  분해"). The ratchet was the existence proof — the design call had been
  made; this is execution.
- **Verification:** 524 server tests green; mypy clean (44 source files);
  ruff clean. Each module under 500 LOC; max engine module now is
  `canvas_migrations.py` (483, pre-existing, untouched).
- **Approval:** executed under the user-approved N-3 plan
  ("N-3 god 모듈 3개 분해"), 2026-06-11.

### D-2026-06-11-C — Workspace = git repo (not `.noory/plot/`)

- **What:** The **workspace is the user's opened folder**, and that folder
  IS the git repo. `.noory/plot/` lives *inside* the workspace repo (alongside
  the user's own source / docs / `.env` / whatever they keep there); Novel
  does NOT create its own `.git` under `.noory/plot/`. `ensure_repo` /
  `tag_snapshot` / `publish_snapshot` / blueprint-publish all target the
  workspace root (the path passed as `?project_path=…`), not its
  `.noory/plot/` child.
- **Why (user):** "git은 프로젝트가 아니라 워크스페이스 당 1개에요. .plot/
  에 두는게 아니라 워크스페이스 자체가 깃 레포여야한다." (2026-06-11). The
  v0.53.0 → v0.59.x design that scoped the repo to `.noory/plot/` reasoned
  from "protect non-Novel files in the launch folder"; the user's revised
  position is that workspace = git repo by definition, and tracking
  decisions (`.gitignore`) belong to the user, not to Novel.
- **Supersedes:** D-2026-06-09-C (repo at `.noory/plot/`) — partially. The
  "one repo per workspace, not per project" half stays correct; the "repo
  inside `.noory/plot/`" half flips to "repo at the workspace root."
- **Consequence — gitignore is the user's call:** Novel does NOT auto-add an
  ignore entry for its own data. If the user wants `.noory/plot/` tracked,
  it just is; if not, they add `.noory/plot/` to their workspace
  `.gitignore`. (Sibling plugin migrations — evonest v1.1.1, solera v5.2.0 —
  carry the user's prior intent forward but do not invent ignore policy for
  projects that tracked their data on purpose; the same principle applies
  here.)
- **Implementation outline (not yet shipped):** rename `workspace_root` →
  `repo_root` semantically (kept name OK, but the path it carries shifts
  from `<launch>/.noory/plot` to `<launch>`); `plot_root` (= `repo_root /
  ".noory/plot"`) still drives data I/O. `tag_snapshot` / per-node publish
  pass `repo_root` to git. Lazy migration: on first open of a workspace that
  has a `.noory/plot/.git` (the prior design), move it up to the workspace
  root *only if* no `.git` already exists at the workspace root — otherwise
  leave both alone and surface a one-time hint, since merging histories is
  the user's call.
- **Approval:** Accepted by user, 2026-06-11. Spec pinned at SPEC.md
  §Workspace & projects → "Workspace = git repo (D-2026-06-11-C)".

### D-2026-06-11-D — Git init requires explicit user consent (Novel never auto-creates `.git`)

- **What:** When the workspace folder already contains a `.git/`, Novel uses
  that repo as-is — never touches `user.name`/`user.email`, never writes
  `.gitignore` or `.gitattributes`, never silently runs `git init`. When the
  workspace folder does NOT contain a `.git/`, Novel also does NOT silently
  init one. Instead, the first tag/publish call that needs git replies with
  a structured error (`{error: "git not initialized in workspace",
  needs_git_init: true, workspace_root: "..."}`) and the viewer surfaces a
  modal **"Initialize git repo at `<workspace>`?"** with **Yes / No**.
  Only an explicit Yes triggers `POST /api/workspace/git-init`, which runs
  `git init` at the workspace root.
- **Why (user):** "근데 원래 깃일 경우도 있구요. 깃 레포가 아니면
  깃레포여야하는데 추가할거냐고 물어봐야합니다." (2026-06-11). Two
  invariants pulled from one sentence:
  1. **Existing git wins.** If the user already has a repo there, Novel must
     stay out of it. No `git config` writes, no `.gitignore` injection.
  2. **No surprise repos.** If there's no repo, Novel proposing tag/publish
     is fine, but creating the actual `.git/` requires the user clicking
     Yes — `git init` on a directory the user opened is a *visible* change
     that needs consent like any other destructive-ish action.
- **Identity (`user.name`/`user.email`) for Novel-authored commits:** instead
  of writing repo-level config, every Novel commit/tag passes its identity
  inline (`git -c user.name=Novel -c user.email=plot@noory-ai.local commit
  …`). That way Novel commits are identifiable in `git log --author`, but the
  user's repo-level `user.name` stays whatever they had before, even on a
  freshly-init-by-Novel repo (so their next non-Novel commit is authored as
  themselves, not as "Novel").
- **Path-scoped staging:** Novel's tag/publish commits stage only
  `.noory/plot/` (i.e. `git add -A -- .noory/plot/`), never the whole
  workspace. The user's working tree changes outside `.noory/plot/` are
  never folded into a Novel commit by accident. (The user can always
  `git add` other paths themselves and Novel's next `git add` won't touch
  them.)
- **Migration on first open of a workspace that has the prior `.noory/plot/.git`:**
  - if the workspace also already has its own `.git/` → leave both alone,
    log a one-line note (the user reconciles; merging histories is their
    call);
  - if the workspace has NO `.git/` → move `.noory/plot/.git/` up to the
    workspace root (one `shutil.move`, same volume). The history carries
    over with no rewrite. After the move, the workspace IS the repo.
- **Implementation outline (not yet shipped):** new endpoint
  `POST /api/workspace/git-init` (idempotent — second call on an existing
  repo is a no-op success). `git_store.ensure_repo` becomes
  `git_store.assert_repo_initialized(workspace_root)` and raises a new
  `GitNotInitializedError` instead of silently creating; tag/publish
  endpoints catch it and surface the structured 409. New
  `git_store.init_workspace_repo(workspace_root)` is the only function
  that actually runs `git init`.
- **Approval:** Accepted by user, 2026-06-11. Spec pinned at SPEC.md
  §Workspace & projects → "Git consent (D-2026-06-11-D)".

### D-2026-06-11-E — R7 in-app chat = native panel (with external-CLI subprocess)

- **What:** R7's in-app chat surface ships as a **native panel** inside
  Novel (not a thin "open Claude Code" launcher). The panel renders the
  conversation, the input box, the message history, the per-message
  status — all in Novel's own UI. The underlying *brain* is still the
  user's external CLI (Claude Code / Codex / Gemini), which Novel drives
  as a subprocess: Novel writes the user's message to the CLI's stdin,
  parses streamed output back, and shows it in the panel. The CLI owns
  API keys, model selection, billing — Novel owns the canvas + the chat
  shell.
- **Why (user choice, 2026-06-11):** Option A out of three (A = native
  panel, B = thin launcher, C = ship B first then add A). The user
  picked A directly. Native panel keeps the canvas-and-conversation
  context together (no context switching to a terminal) while staying
  inside the pinned Pencil model — Novel still doesn't host an AI, it
  just gives the user's own agent a unified surface to work through.
- **Pencil model invariants preserved:**
  - Novel never holds API keys or credentials. Auth is the CLI's job
    (`claude login`, `codex login`, etc.); Novel spawns an
    already-authenticated CLI.
  - Novel never bills the user. Token usage shows up on the user's
    Anthropic / OpenAI / Google account.
  - Novel doesn't expose model selection. The CLI uses whichever model
    is configured (its own settings file). Novel may surface a read-only
    "current model" indicator in the panel chrome.
- **Multi-provider abstraction:** one Provider interface (start
  subprocess, write message, read streamed output, kill on close) with
  per-CLI adapters: ClaudeCodeProvider, CodexProvider, GeminiProvider.
  Provider auto-detection at workspace open (which CLIs are on
  `$PATH` + which are logged in). User picks one when more than one is
  available; selection persists in `.noory/plot/chat-provider`. Per-CLI
  install/login guidance kicks in when nothing is detected.
- **Implementation outline (separate session):**
  - Track 2.5 R7 MCP registration ships first (per-CLI MCP config
    edits — `~/.claude.json` / `~/.codex/config.toml` / `~/.gemini/
    settings.json`) so the CLI knows how to call Novel's MCP server.
    *Then* the native panel can be wired up, since the canvas ↔ chat
    feedback loop relies on the CLI calling Novel's MCP tools.
  - Provider interface + ClaudeCodeProvider first (most mature MCP
    support), then CodexProvider + GeminiProvider as their MCP stories
    settle. Streamed-output parsing per provider.
  - Panel UI as a right-side dock that the user can collapse; uses
    the existing `dialog`/`shell` chrome conventions.
  - Path-scoped: Novel subprocesses the CLI inside the workspace folder
    so the CLI sees the same `?project_path=` Novel is opened on.
- **Approval:** Accepted by user, 2026-06-11. Spec pinned at SPEC.md
  §R7 chat (D-2026-06-11-E).

### D-2026-06-12-A — Workspace = monorepo, project = one service inside it

- **What:** The "why" behind the workspace-holds-many-projects shape is
  named: **a workspace is a monorepo, and each project is a distinct
  service (or app) inside that monorepo.** The user's quote:
  > "모노레포를 생각해봐요. 거기에 앱이 두 개 있어요. 서로다른 서비스죠.
  > 그래서 워크스페이스는 모노레포인거고 프로젝트는 서로다른 서비스인거에요."
  Two apps in `apps/web/` and `apps/mobile/` (or `services/api/` and
  `services/billing/`) are two **separate projects** in Novel — each with
  its own Foundation / Actors / Services / Service-Detail canvases —
  but they sit inside ONE workspace (= the monorepo) that shares ONE
  git repo (D-2026-06-11-C/D), ONE `.noory/` dotfolder (R9), and ONE
  sidebar listing them.
- **What this answers vs. what it doesn't:**
  - **Answers** "why does a workspace need to hold multiple projects?"
    → because real codebases ship more than one service in one repo;
    each service is its own bounded context with its own domain map.
  - **Does NOT change** any current code: the discovery / dir-tree
    pickers already do recursive scan, so a project at
    `apps/web/.noory/plot/{id}/` is already discoverable. The R9
    `.noory/plot/{id}/` layout already supports flat-or-nested project
    placement. This decision pins the *meaning* on top of the existing
    plumbing.
  - **Leaves open** cross-project linkage (a service that depends on
    another service's identity / actors). Not in scope for v1 — every
    project remains a self-contained graph. Future work if real
    monorepos surface this need.
- **Naming implication (UI copy):** the term **"project"** in
  user-facing strings means "one service in the monorepo" (not "the
  monorepo as a whole"). Workspace-level affordances ("open another
  workspace", "the workspace path") refer to the monorepo. Sidebar
  list = "projects in this workspace" = services in this monorepo.
- **Disk layout (unchanged):**
  - `<monorepo>/.noory/plot/{project_id}/` — one Novel project's data
    (canvases, published MD, etc.). The `{project_id}` is opaque
    (UUID-ish); the user-facing name is `ProjectDoc.name`.
  - Recursive discovery picks up nested `.noory/plot/` roots too, so
    `<monorepo>/apps/web/.noory/plot/{id}/` and
    `<monorepo>/services/api/.noory/plot/{id}/` both show in the
    sidebar. The dir-label chip tells which monorepo subfolder each
    project lives in.
- **Approval:** Accepted by user, 2026-06-12. Spec pinned at SPEC.md
  §Workspace & projects → opening paragraph rewritten to name the
  monorepo / service relationship explicitly.
- **NARROWED by D-2026-06-21-AA (2026-06-21):** "a monorepo holds N
  projects" no longer means N `project_id` folders *under one
  `.noory/plot`*. Each project gets its **own** directory with its own
  `.noory/plot` (one project per dir); the N services of a monorepo are
  **sibling directories** discovered recursively. The meaning here (a
  workspace = a monorepo of services) is unchanged — only the disk
  packing is narrowed from "stack-or-sibling" to "sibling only".

### D-2026-06-12-B — Wire-boundary domain validation via parseEntity (Track 1.4)

- **What:** Every ``CanvasDoc`` arriving across the HTTP wire is now
  validated through ``parseEntity`` before it leaks deeper into the
  viewer. ``api.ts::validateCanvas(canvas)`` iterates ``canvas.nodes``
  and runs each through the discriminated-union dispatch; any malformed
  node throws ``DomainParseError`` at the boundary instead of crashing
  the React Flow render path or the Inspector.
- **Where it's wired:** ``getCanvas``, ``getAllCanvases``, and the
  ``putCanvas`` response (server's mutating decorations — ``_md_warnings``
  + ``_dirty`` — preserved; pure validation, no clone). ``getCanvas`` is
  also what ``useProjectSocket`` calls after a WS ``project_changed``
  event, so external-write paths land in the same gate.
- **Why now:** Until v0.62, ``parseEntity`` had zero call sites — the
  dispatch table was assembled (every domain class self-registers via
  ``registerKindParser``) but never invoked outside tests. ARCH_REVIEW.md
  flagged this as Track 1.4's "parseEntity dead, 0 calls → fromJson
  activation / fail-fast" item. Wire boundary is the right place: server
  Pydantic enforces the same invariants on write, so a client-side
  ``DomainParseError`` is a contract breach (drift between server-side
  Pydantic and viewer-side per-kind classes, or a hand-edited canvas.json)
  — fail-fast surfaces it before it corrupts in-memory state.
- **Fail-fast vs fail-soft:** strict throw. The risk flagged in
  ROADMAP ("관용 데이터 거부 가능") is real for hand-edited canvas.json,
  but: (a) the server already rejects on read via Pydantic, so any
  canvas that reaches the wire is already type-valid by server schema;
  (b) tests cover all 17 kinds round-tripping through ``parseEntity``
  (``entity-roundtrip.test.tsx``); (c) the per-kind ``fromJson``
  validators are deliberately lenient on optional-empty fields (e.g.
  ``actor_ref.ref_actor_id = ""`` passes viewer-side because server
  Pydantic catches that on write).
- **What's NOT touched:** React Flow keeps working on the plain JSON
  shapes — ``validateCanvas`` returns the input ``CanvasDoc`` reference
  unchanged, and the class instances produced by ``parseEntity`` are
  deliberately discarded. The viewer never leaks class-instance prototypes
  into ``applyNodeChanges`` (which would strip them via ``{...node}``);
  the prototype-strip warning at the top of ``domain/SketchNode.ts``
  still holds.
- **Approval:** Executed under user-approved Track 1.4 plan
  ("parseEntity WS 경계"), 2026-06-12.

### D-2026-06-12-C — Semantic theme tokens SSOT (Track 1.4 final)

- **What:** `src/theme/tokens.ts` becomes the single source of truth for
  the *names* of every semantic theme token (`SEMANTIC_TOKENS` const
  array + `SemanticToken` union type + Tailwind utility-class type
  helpers). `tests/theme-tokens-ssot.test.ts` parses
  `src/theme/tokens.css` (`:root` + `.dark` blocks) and
  `tailwind.config.js` (`colors` map), then asserts each side declares
  exactly the same token name set as `SEMANTIC_TOKENS` — no
  extras, no omissions.
- **Why:** Until this commit, three artefacts had to be hand-synced when
  adding a token: the CSS var, the `.dark` override, the Tailwind
  `colors` map entry. A forgotten entry produced a silent failure
  (Tailwind class compiles but `var(--missing)` falls back to `inherit`
  / 0 / `rgba(0 0 0 / 0)`). The guard catches the drift at test time.
- **What stays the same:** No call site changes. Components still use
  Tailwind utility names (`bg-surface`, `text-fg-strong`) directly — the
  union type is available for components that want to accept a token
  through a typed prop, but it's opt-in. The light-token *value*
  fidelity guard (`tests/theme-tokens.test.ts`, D-2026-06-07-C) keeps
  guarding the actual RGB channels.
- **Sanity check now passing 3/3:** the existing token set (~30) was
  already in sync across all three artefacts.
- **Approval:** Executed under user-approved Track 1.4 plan ("테마 타입
  SSOT"), 2026-06-12. ROADMAP Track 1.4 fully closed with this.

### D-2026-06-12-D — R7 chat subprocess lives in mashbill, not Tauri

- **What:** The CLI subprocess that drives the R7 chat panel
  (`claude` / `codex` / `gemini`) is spawned, fed, and reaped by the
  **mashbill engine** (Python). The viewer reaches it through the same
  HTTP/WS transport it already uses for every other Novel operation
  (`POST /api/chat/send`, `WS /ws/chat?project_path=…`). The Tauri shell
  does *not* spawn or stream the chat CLI; its only role stays "host the
  engine sidecar".
- **Why:** Three forces, all pointing the same direction:
  1. **Dev parity.** The dev workflow is `cd mashbill && uv run mashbill-http`
     + `cd plot/viewer && npm run dev` opened in a regular browser at
     `:5193`. A browser tab has no `__TAURI__` context, so a Tauri-side
     subprocess would silently disable chat in dev. Keeping the CLI
     subprocess in the engine means dev and bundled `.app` take the same
     code path.
  2. **Transport SSOT.** `viewer/src/api.ts` already centralises every
     server call (D-2026-05-10's `EngineClient` seam preparation). Adding
     a Tauri-only IPC channel would split the transport into two paths
     and pre-empt the still-unbuilt EngineClient interface.
  3. **Existing WS plumbing.** `mashbill/broadcast.py` + the `/ws`
     endpoint already fan messages out per workspace. The chat stream
     reuses the same pattern — one new room key, no new framework.
- **What this does NOT decide:** the **PATH inheritance** problem for
  bundled-mode is a separate Tauri-side concern — `.app` launched from
  Finder gets `PATH=/usr/bin:/bin:/usr/sbin:/sbin` and won't find
  `/opt/homebrew/bin/claude` or `~/.local/bin/codex`. The fix (read the
  user's login-shell PATH and pass it down to the engine sidecar env in
  `src-tauri/src/lib.rs`) is the only Tauri-side change Phase C needs,
  and it sits below this decision rather than overturning it.
- **Implementation outline:**
  - `mashbill/chat_session.py` — `ChatProvider` ABC + `ClaudeCodeProvider`
    concrete. One session per workspace root, keyed by absolute path.
    Each user turn invokes `claude --print --output-format stream-json
    --include-partial-messages --session-id <uuid>` so the CLI emits
    chunked JSON events to stdout; the session reuses a single
    `--session-id` across turns to keep the conversation persistent in
    the CLI's own session store.
  - `mashbill/endpoints_chat.py` — `POST /api/chat/send` (workspace_root,
    message text) writes the user turn + spawns the subprocess; the
    streamed stdout flows out through `WS /ws/chat?project_path=…`
    using the same Broadcaster pattern as `/ws`. `POST /api/chat/reset`
    drops the in-memory session.
  - Viewer: `ChatMessageFrame` lights up — `submit` calls `sendChat`,
    the dock opens a chat-WS connection per workspace, messages render
    in the existing `role="log"` frame.
  - i18n: existing `chat.*` keys carry; new keys for streaming /
    error states added to en + ko in lockstep (`i18n-keys-parity` test).
- **Alternatives considered + rejected:**
  - **Tauri spawns.** Lost on dev parity (chat dead in dev mode) +
    transport split. See "Why" above.
  - **HTTP signal, Tauri spawn.** Two-process orchestration just to keep
    process tree in Rust — solves a problem that doesn't exist (the
    engine already reaps subprocesses cleanly on its own exit).
- **Approval:** User-picked option A via AskUserQuestion, 2026-06-12.
- **Spec impact:** SPEC.md §R7 chat — new "Subprocess host" row added
  to the behaviour table pointing at this decision.

### D-2026-06-12-E — R7 chat: Codex + Gemini providers land alongside Claude

- **What:** v0.64.1 adds two concrete subclasses of the
  ``_SubprocessChatProvider`` base shipped in v0.64.0:
  ``CodexProvider`` (``codex exec --json``) and ``GeminiProvider``
  (``gemini -y --output-format stream-json``). The
  ``ChatSessionRegistry`` is now keyed by ``(workspace, provider_name)``
  so switching CLIs in one session doesn't overwrite the other CLI's
  conversation, and ``/api/chat/send`` reads the workspace's persisted
  provider selection (D-2026-06-11-E Phase B step B3) to dispatch.
  Sending with no selection now returns **400** instead of silently
  spawning a default CLI the user didn't choose.
- **Per-provider quirks pinned here (so they're not buried in code
  comments — gates 1 + spec triumph over comments):**
  - **Claude Code:** Novel mints the ``--session-id`` (uuid4) on the
    first turn, then ``--resume <id>``. Novel is the only party that
    knows the id from the very first call. (Unchanged from v0.64.0.)
  - **Codex:** the CLI emits ``thread.started`` with ``thread_id`` on
    the first turn — we capture it and pass it to
    ``codex exec resume <thread_id>`` on later turns. Novel does NOT
    mint a UUID up-front (Codex doesn't accept one). If the first
    turn never emits ``thread.started`` (CLI crash, parse skip), the
    next turn falls back to a fresh ``codex exec`` so we never call
    ``resume None``. ``--skip-git-repo-check`` is always on because
    R7 must work on a freshly-opened folder before D-2026-06-11-D's
    git-init consent kicks in.
  - **Gemini:** the CLI emits ``init`` with ``session_id`` on the
    first turn — we capture it and pass ``--resume <session_id>`` on
    later turns. ``-y`` (YOLO mode) is always on because Novel is the
    canvas surface that owns user trust; the inner tool calls don't
    need a second confirmation layer (matches how IDE plugins like
    Cursor / Zed embed agentic CLIs).
- **Registry keying — why (workspace, provider) not just workspace:**
  the user's natural flow is "ask Claude to draft, switch to Codex to
  refactor, switch back to Claude to review". A single-key registry
  would either lose Claude's first session when Codex was selected, or
  require a manual "save / restore" affordance. Keying on the pair
  costs one extra tuple slot per active session and keeps both
  conversations alive.
- **No-selection → 400 (not auto-default):** v0.64.0 silently fell
  back to ClaudeCodeProvider whenever the workspace had no persisted
  selection. That contradicts D-2026-06-11-E's Pencil-model
  invariants — Novel is supposed to host the canvas, not pick a default
  AI for the user. The 400 surfaces a clean error to the dock which is
  already showing the "Pick a chat CLI above to start" empty state.
- **Module-size discipline:** v0.64.0 shipped one ~370-LOC
  ``chat_session.py``. Three providers + the base + the registry was
  going to push past the engine's 500-LOC rule (test_module_size). To
  stay legible AND under the rule, the per-CLI quirks moved into
  ``mashbill/chat_providers/{base,claude_code,codex,gemini}.py``
  and ``chat_session.py`` became a thin facade (~130 LOC) that
  re-exports the public names. Old imports keep linking.
- **Approval:** Executed under D-2026-06-11-E + D-2026-06-12-D
  ("multi-provider abstraction" was already pinned there as the goal);
  this entry documents the per-CLI implementation choices that
  shipping forced. No new user-facing surface decisions — the dock
  copy is unchanged.
- **Spec impact:** none — SPEC.md §R7 chat's "Provider selection"
  row already describes the auto-detect + persistence flow this
  endpoint dispatch reads.

### D-2026-06-12-F — Engine auth seam (Track 3.5, TABLET_ARCH §"지금 만들 것")

- **What:** Novel ships an env-gated auth seam at every engine entry
  point. ``PLOT_AUTH_TOKEN`` unset → every request passes through
  (today's dev parity). ``PLOT_AUTH_TOKEN`` set → ``/api/*`` requires
  ``Authorization: Bearer <token>`` and the ``/ws`` handshake requires
  ``?auth=<token>``. ``/api/health`` is always open so the shell can
  probe before injecting the token. Bundled Tauri builds mint a fresh
  32-byte (64-hex) token per launch, export it into the sidecar's env,
  and surface it to the viewer via the ``plot_auth_token`` invoke
  command so the viewer attaches the header on every fetch and the
  param on every WS connect.
- **Why now (TABLET_ARCH was explicit):** the pin under §"지금 만들
  것" reads — *"tokenless API에 나중에 auth 추가 = 전 엔드포인트
  breaking change; 지금 pass-through 훅 = 미들웨어 1개."* The hooks
  go in **before** any consumer locks the wire shape: when the
  bundled shell flips enforcement on, we change one env var; when
  the tablet ships, the same seam already enforces. Adding the
  middleware after a remote engine ships would require a
  coordinated client + server release with breakage on every old
  client in between.
- **Why env-gated (not always-on):** the dev loop runs the engine
  in a terminal (``uv run mashbill-http``) and the viewer in a
  browser (``npm run dev``); forcing a token there means every
  contributor juggles env vars + restarts. The pin in TABLET_ARCH is
  *"오늘은 no-op/loopback"* — env-gated keeps it no-op for dev and
  flips to enforced the moment the bundled shell sets the variable.
- **Why per-launch token, not stored secret:** the threat model on
  loopback is *another process on the same machine*. A long-lived
  on-disk secret would survive uninstall residue (Mac uninstalls
  rarely scrub user data); a per-launch token lives only in the
  shell's process memory and dies with it.
- **Why constant-time compare (``hmac.compare_digest``):** even on
  loopback, naïve string equality leaks timing information that
  same-machine attackers can use to brute-force the token byte by
  byte. ``hmac.compare_digest`` runs in O(n) regardless of where
  the mismatch starts.
- **Why open-list keeps ``/api/health`` only:** the shell's bootstrap
  needs to probe the engine before the invoke command is registered
  (Tauri's setup-hook ordering). Every other endpoint is post-boot
  and must respect enforcement. Adding more open paths inflates the
  attack surface for no operational gain.
- **What this does NOT decide:** the workspace_id seam, REST DTO
  parity, ``/api/v1`` versioning — the other three contract items
  TABLET_ARCH §"지금 만들 것" names. Those land as follow-up D
  entries; v0.65.0 is just the auth seam.
- **Implementation outline:**
  - Engine: ``mashbill/auth.py`` — env reader + ``AuthMiddleware``
    (Starlette ``BaseHTTPMiddleware`` over ``/api/*`` only) +
    ``check_ws_token`` (called from ``ws_endpoint`` inside
    ``http_app.py`` because middleware can't ride ``WebSocketRoute``).
    16 tests pin: env unset = pass-through, env set + missing → 401,
    env set + wrong → 401, env set + good → through, ``/api/health``
    always open, WS check mirrors HTTP.
  - Viewer: ``api.ts`` gains ``setEngineAuthToken`` + ``engineFetch``
    (30 ``await fetch(...)`` sites rewritten — single seam over
    every engine call). ``openProjectSocket`` appends ``?auth=...``
    when set. New ``src/app/auth.ts::initEngineAuth`` resolves the
    token: Tauri ``invoke('plot_auth_token')`` first, then
    ``import.meta.env.VITE_PLOT_AUTH_TOKEN`` for dev opt-in, then
    fall through to ``null``. Called once from ``main.tsx`` before
    render. 7 tests pin header injection on/off, ``null`` clearing,
    Tauri invoke first / dev env fallback / Tauri error swallow.
  - Tauri shell: ``mint_auth_token()`` uses ``rand::rngs::OsRng`` to
    fill 32 bytes, hex-encodes. Stored in a ``State`` so the
    ``#[tauri::command] plot_auth_token`` returns it. Sidecar
    spawned with ``.env("PLOT_AUTH_TOKEN", &token)``. 2 Rust tests
    pin hex shape + per-call uniqueness.
- **Approval:** Executed under TABLET_ARCH §"지금 만들 것" plan,
  2026-06-12. The "build now" line item literally says "auth seam …
  미리 심기."
- **Spec impact:** new SPEC.md §Engine auth section pointing at this
  entry — "env-gated, Bearer for HTTP, ?auth= for WS, /api/health
  open, dev parity preserved when env unset."

### D-2026-06-13-A — Stencil dataTransfer payload must keep `preset.id`

- **What:** `StencilItem.onDragStart` no longer strips `id` from the
  serialized drag payload. Extracted `toTransferPreset()` (exported)
  that drops only the four display-only fields (`labelHint` /
  `dropHint` / `labelI18nKey` / `dropHintI18nKey`) and keeps `id`.
- **Why:** `resolveDropTarget` keys the sub-actor / service-in-category
  *nesting* rules off `preset.id` (`id === "sub-actor"`, `id ===
  "service-in-category"`). With `id` stripped at serialization, those
  branches never fired, so a Service / sub-actor dropped anywhere fell
  through to a silent top-level node — bypassing the D-2026-05-28-A
  contract (Service nests in Category; sub-actor nests in Actor). Found
  while diagnosing a user report that nodes "won't place" on the
  Services canvas. (The headline symptom — *no node at all* in the
  bundled WKWebView `.app` — is a separate, WKWebView-only issue still
  under investigation; this fix is orthogonal correctness.)
- **Alternatives:** (a) add a dedicated `dropInto?: NodeKind` field and
  switch `resolveDropTarget` off it instead of `id` — cleaner but a
  wider design change for no extra behaviour; rejected per YAGNI/AHA.
  (b) Leave it (top-level drops) — rejected, violates the pinned
  nesting contract.
- **Approval:** Accepted by user, 2026-06-13 (chose "id-stripping 버그
  먼저").
- **Spec impact:** none — restores already-specced D-2026-05-28-A
  runtime behaviour. Pinned by `viewer/tests/stencil-transfer-preset.test.tsx`.

### D-2026-06-13-B — Debug-flavor `DEBUG` badge in the header

- **What:** a small amber `DEBUG` chip renders next to the `PLOT`
  wordmark **only** in the debug flavor (`VITE_PLOT_DEBUG=1`); the
  release flavor shows nothing. New `viewer/src/shell/FlavorBadge.tsx`
  gated by `debugEnabled()`.
- **Why:** user asked for the build flavor to be visible in the app, and
  hidden in the official release ("앱에 플레이버 표시되었으면해요" + "정식
  버전일 때는 안보이게 하고", 2026-06-12). Reuses the existing BUILD-TIME
  debug gate (D-2026-06-09-D) so the release bundle can never expose it —
  no runtime `?debug` escape hatch.
- **Alternatives:** (a) show flavor + version string — rejected per YAGNI
  (user asked for flavor only). (b) Route "DEBUG" through i18n — rejected;
  it is a build identifier, not product copy, and sits beside other
  hardcoded technical labels (`PLOT`, "MCP: live").
- **Approval:** Accepted by user, 2026-06-12 (feature request); committed
  2026-06-13.
- **Spec impact:** SPEC.md §Chrome — new "Flavor badge" bullet. Pinned by
  `viewer/tests/flavor-badge.test.tsx`.

### D-2026-06-13-C — Stencil drag uses pointer events, not HTML5 DnD

- **What:** the stencil → canvas drag is captured with pointer events
  (`pointerdown` on the stencil item → window `pointerup` over a
  registered canvas pane), replacing HTML5 `draggable` + `dataTransfer` +
  `onDrop`. New `viewer/src/canvases/sketch/StencilDragContext.tsx`
  (provider + `useStencilDrag` / `useStencilDropTarget`); `useDragAndDrop`
  exposes `placePresetAt(preset, clientX, clientY)` + registers the pane;
  `SketchStencil` items use `onPointerDown`. A ghost chip follows the
  pointer for feedback.
- **Why:** WKWebView (the bundled Tauri `.app` — Novel's only product
  surface) does **not** fire HTML5 `dragstart` / `drop`. Confirmed in-app
  via the debug channel: a top-level drop never changed `nodeCount`. So
  stencil drops created no node on ANY canvas in the desktop app, while
  Chromium dev worked. Pointer events fire identically in both.
  - WKWebView quirk handled: it implicitly captures the pointer to the
    source item, so `pointerup.target` is the SOURCE, not the drop
    element. The drop pane is resolved by `elementFromPoint(clientX,
    clientY)` OR `e.target` (jsdom has no `elementFromPoint`).
  - Supersedes the toTransferPreset mechanism of D-2026-06-13-A: the
    channel passes the full in-memory `StencilPreset` (no serialization),
    so `preset.id` can never be lost — the nesting-rule intent of A is now
    structural. `toTransferPreset` + its test were removed.
- **Root cause of the multi-hour mis-diagnosis:** the debug `.app` embeds
  `viewer/dist-debug`, but the viewer was being built to `dist`; and
  Tauri does not recompile the binary when only the frontend changes. So
  every `.app` test ran STALE (yesterday's) frontend. Fix = build
  `dist-debug` + `touch src-tauri` to force re-embed (see
  `project_debug_app_build` memory).
- **Alternatives:** (a) click-to-place — rejected, changes the drag UX.
  (b) coax HTML5 DnD to work in WKWebView — rejected, fragile and the web
  product is retired so there's no reason to keep HTML5 DnD.
- **Approval:** Accepted by user, 2026-06-13 ("포인터 드래그로 교체"); drop
  verified working in the WKWebView `.app` (placed: true via debug trace).
- **Spec impact:** SPEC.md §Drag-and-drop "Capture mechanism" bullet.
  Pinned by `viewer/tests/stencil-pointer-drag.test.tsx` (channel routing,
  WebKit-capture via elementFromPoint, pointercancel) +
  `sidebar-stencil-gating.test.tsx`.

### D-2026-06-13-D — Category is an optional grouping on the Services canvas

- **What:** `resolveDropTarget` no longer rejects a `service` dropped
  outside a `category`. Dropped on a category → nests; dropped elsewhere →
  top-level.
- **Why:** user: "카테고리는 옵셔널 할 수 있습니다" (2026-06-13). The "every
  service belongs to one category" model was a constraint, not a law, and
  did not match the user's mental model.
- **Alternatives:** keep the requirement (rejected by user); make
  sub-actor optional too (out of scope — user spoke only about category).
- **Approval:** Accepted by user, 2026-06-13.
- **Spec impact:** SPEC.md §Drag-and-drop "Optional category" bullet.
  Supersedes D-2026-05-28-A's service rule. Pinned by
  `viewer/tests/service-detail-composition-drop.test.tsx`.

### D-2026-06-13-E — Nesting edge carries no visible verb label

- **What:** the directed parent→child edge a nested drop materialises now
  uses `label: ""` / `action_verb: null` (was `"decomposes"`).
- **Why:** user: the "decomposes" label was visual clutter (2026-06-13).
  The directed edge + `relation` still carry the parent→child structure.
- **Approval:** Accepted by user, 2026-06-13.
- **Spec impact:** SPEC.md §Drag-and-drop "Hierarchy edge" bullet. Pinned
  by `viewer/tests/nested-drop-edge.test.tsx`.

### D-2026-06-13-F — Arrange icon uses a fixed dark stroke, not currentColor

- **What:** `LayoutControls` `ArrangeIcon` stroke is `#1a1a1a` (was
  `currentColor`).
- **Why:** the React Flow Controls bar has a light background in every
  theme; `currentColor` inherited the app's (light, in dark theme) text
  colour, making the arrange icon invisible. User: "정렬 아이콘이 잘 보이지
  않습니다. 아이콘 색깔을 검은 색으로 해주세요" (2026-06-13).
- **Approval:** Accepted by user, 2026-06-13.
- **Spec impact:** none (cosmetic; the controls bar is RF default chrome).

### D-2026-06-13-G — Foundation drops land at the cursor (no radial snap)

- **What:** `FoundationCanvas` no longer passes `applyAnchorRadialLayout`;
  a dropped mission / core_value / identity lands at the cursor like every
  other canvas, instead of snapping to an anchor-radial slot.
- **Why:** user: "사용자가 드롭을 한 곳에 노드가 생성되게 해주세요. 지금 자동
  정렬을 하려고 엄청 먼곳에 두는것 같아요" (2026-06-13). The drop-time radial
  snap (D-2026-05-12-O) placed nodes far from the cursor. The ⊞
  auto-layout button still arranges on demand.
- **Approval:** Accepted by user, 2026-06-13. Supersedes the drop-time
  behaviour of D-2026-05-12-O (the radial layout algorithm itself stays
  available via the auto-layout button).
- **Spec impact:** SPEC.md §Drag-and-drop "Free drop" bullet.

### D-2026-06-13-H — Chat is MCP-first; in-app chat is a Codex/Gemini-only convenience (design pinned, impl follow-up)

- **What (two coexisting paths):**
  - **Primary — MCP-only.** Novel is an MCP server; the user connects their
    OWN interactive agent (Claude Code / Codex / Gemini, already running on
    their account/subscription, as in an IDE) to it. Novel does NOT host or
    drive the AI. The R7 MCP registration (v0.62) is the keeper.
  - **Secondary — in-app chat for Codex + Gemini ONLY.** The in-app panel
    (engine spawns the CLI) stays for users who configured Codex/Gemini.
    **`claude-code` is removed from the in-app chat provider selection**
    (it remains in the MCP-registration list).
  - Chat conversations are **scoped per canvas type** (foundation / actors
    / services / service_detail) **plus one shared "project" scope** for
    cross-canvas work — the chat follows the active canvas tab; the project
    scope is always reachable. Applies to the in-app chat threads and to
    the MCP context handed to the agent.
- **Why:** the CLI agents ARE interactive chats — running `claude`
  (no `-p`) IS a chat session, on the account subscription, like the
  VSCode Claude Code extension. Novel's in-app chat uses `claude -p`
  (headless), which Anthropic bills SEPARATELY from the Claude
  subscription → a Claude user **pays twice** (subscription + `-p`). The
  user already runs their agent; Novel embedding/driving it via `-p` is
  redundant + costly. So Novel should be the MCP surface their existing
  agent connects to, not a chat host. Codex/Gemini in-app stays as a
  convenience for users who set those up (user: "둘 다 할거라고").
- **Alternatives:** (a) drive the *interactive* (subscription) CLI via a
  PTY to dodge `-p` billing — rejected for now: fragile (parsing a
  human-facing TUI the CLIs deliberately don't expose for automation) and
  billing/ToS-uncertain. Verify before ever revisiting. (b) in-app API key
  / Novel-hosted AI — both violate the pinned Pencil model + double-charge.
- **Revises:** D-2026-06-11-E ("R7 in-app chat = native panel + external
  CLI subprocess") — the subprocess in-app chat is **demoted** to a
  Codex/Gemini-only secondary; MCP-only is primary. Reframes the
  per-canvas-chat idea from "in-app threads" toward "per-canvas MCP
  context + (secondary) per-scope Codex/Gemini threads".
- **Approval:** Accepted by user, 2026-06-13 ("둘 다 할거라고"). Design
  pinned; **implementation is a follow-up** (engine: scope-keyed sessions
  + drop claude-code from chat selection; viewer: scope-aware dock +
  MCP-connect affordance; schema parity for the `scope` field). Run via
  mashbill-feature-tdd.
- **Spec impact:** SPEC §R7 chat — updated in v0.68.0 (this implementation):
  claude-code excluded from in-app chat (radio suppressed + `/api/chat/send`
  400 backstop + dock coerces legacy selection to none); per-canvas
  conversation scope (`foundation`/`actors`/`services`/`service_detail` +
  shared `project`), engine sessions keyed on `(workspace, provider, scope)`,
  viewer scope-aware dock + segmented switcher, `ChatScope` wire enum
  parity-guarded by `tests/test_chat_scope_parity.py`. Decisions:
  scope omitted → `project` (Postel); `project` scope = explicit toggle;
  `Reset` = current scope only.

