# Per-canvas behavior

> **Canon (shared behaviour RULES, `D-2026-06-28-B`).** The single source of the canvas behaviour rules both
> products follow — what does what. **Detailed implementation·edge cases·code-mechanism** (render detail·layout
> algorithm·cursor·dagre) = engine [`SPEC.md`](../../plugins/mashbill/docs/SPEC.md) +
> `AUTO_LAYOUT`/`CURSOR`/`ARCHITECTURE`. Meaning = [`../concepts/`](../concepts/).

## Common — project anchor

- The primary canvases (Foundation/Actors/Services/Entities) float a **synthetic project anchor** at the
  center. Label = `ProjectDoc.name` mirror (SSOT = `ProjectDoc.anchors`, outside `canvas.json`).
- Exactly 1·non-deletable (synthetic id `__project_anchor__`, delete events ignored).
- Drag·resize persist via **`PATCH /api/projects/:id/anchor`** (not `onDocChange`).
- Visual: 2px slate-600 **border** (no outline — triggers cursor flicker). Square auto-fit.
- 4-side handles visible, the user can draw edges to the anchor. Holds **the name only** (not a content container).
- `anchorArrowMode` (arrow direction at render time, the document edge stays the SSOT): Foundation=`converge`
  (converge toward the anchor), Actors=`diverge-structure` (structure lines — anchor spokes and inheritance — point out
  from the anchor; value-exchange lines keep their giver→receiver direction, `D-2026-07-04-K`), Services=`diverge`
  (out from the anchor), Feature=`none`.
- On every engine canvas write, a root-capable node with neither an anchor edge nor a hierarchy parent edge receives
  one persisted `__project_anchor__→node` spoke. Root-capable kinds are Foundation=`mission/core_value/identity`,
  Actors=`actor`, Services=`category/service`, and Entities=`entity`; Feature canvases are excluded because they have
  no project anchor. Existing anchor and parent edges are preserved, so nested nodes are not re-rooted and repeated
  saves are idempotent. `create_node` remains bare; this is write-time normalization, never read-time repair.
- **Blank-canvas start (`D-2026-07-04-P`).** `create_project` writes the four primary canvases empty: no seed
  nodes and no seed edges, only the project anchor. An auto-created feature detail canvas holds only its root
  feature node. The old content minimums (Foundation ≥1 mission / ≥1 identity, Actors ≥2 actors, Feature ≥1
  `actor_ref`) are gone with the seeds, so **any partial state is saveable** — deleting the last node of a kind
  must never make the write fail. The coach leads the design to completion, not the schema.

---

## Foundation — Discovery

- **Nodes:** `project` (anchor) · `mission` · `core_value` · `identity`. No essence node (emergent).
- **Drill:** none.
- **Edges:** drawn by the user, or by the coach after the user confirms; the coach gives every pillar its anchor
  line in the same turn (`D-2026-07-05-C`). The common save-time orphan→anchor normalization above adds any spoke
  still missing. There is still **no edge emission inside node creation**; the stored spoke is added only when the
  complete canvas is written.
- **Inspector:** selecting a node fills the sidebar panel with its inspector, covering the palette; deselecting
  returns the palette (`D-2026-06-21-Q`). Sections = header (kind·delete·close) → label → per-kind typed form. There
  is no width toggle; the user resizes the panel. (Typed-text kinds hide the legacy details-MD section.)
- **Layout:** auto-layout ON (`layoutAlgo="tree"` = anchor BFS angle-preserving depth ring; ⊞ button,
  touches position only, Cmd+Z undo). Drag-dropped nodes settle **where dropped** (no snap);
  pressing ⊞ aligns them. (The old anchor-radial forced placement is retired for drop only.)
- **Later expansion/TBD:** anchor click→inspector behavior (TBD), connection rules (which kinds), multi-select bulk.

## Actors — Planning

- **Nodes:** `actor` only (rounded). Color is per-node user-selected.
- **Hierarchy = inheritance tree** (anchor root). A hierarchy edge is stored as `relation:"inheritance"`
  (child→parent, toward the anchor); value-exchange edges are the other kind below. Inheritance fields = `[body]` (US-303: side removed). (self→nearest ancestor→blank, computed
  at render time, not stored; grey `↳ inherited from {parent}` caption). An **abstract root** (actor with no
  actor parent and actor children ≥1) shows body only.
- **2 edge kinds:** hierarchy (inheritance, valueless quiet edge) + value exchange (a labeled `flow` edge from giver to
  receiver). [`../concepts/canvases.md`](../concepts/canvases.md) Actors.
- **Value-exchange visual convention:** dashed, in its own amber colour with a matching arrowhead
  (`D-2026-07-04-I`, `D-2026-07-05-A`), so it reads apart from the slate solid structure lines (anchor spokes,
  hierarchy). Value-exchange lines rank below structure lines in auto-layout (`D-2026-07-04-I`). When two or more
  lines join the same node pair — a two-way exchange, for example — they separate into symmetric arcs
  (`D-2026-07-05-B`, [`edges.md`](./edges.md) Render · edit), so overlapping dashes never fill each other's gaps and
  read as one solid line.
- **Hand connect (`D-2026-07-05-D`):** a node-to-node line drawn by hand on the Actors canvas first asks
  "이 선은 무엇을 뜻하나요?" (what does this line mean?): "소속" (belongs to — groups the child under a family as a
  child→family inheritance line) or "가치 교환" (value exchange — asks who gives and what moves, then stores a labeled
  giver→receiver `flow`). Cancel creates nothing. The prompts use domain words, not technical terms. A line to or
  from the anchor has one meaning and is created at once. Handle storage follows [`edges.md`](./edges.md) payload
  fields.
- **Root safety:** a top-level actor family with no actor parent receives the common save-time anchor spoke; an actor
  with an `inheritance` parent remains nested and receives no spoke.
- **Drill:** none.
- **Inspector (identity-only):** `body`. (US-303: side field/editing/schema removal complete; old motivation/pain removed earlier)
- **Layout:** `tree` (angle-preserving depth ring). Edges are floating bezier, circle nodes attach to the circumference.

## Services (overview) — Planning

- **Nodes:** `category` (optional grouping, low-friction/dumb) · `service` (5-field inspector) · `feature` (capability). `category` is shown in the app as **Group** (Korean 묶음); the stored kind stays `category` (`D-2026-10-02-C`).
  Hierarchy category → service → feature. Services are **optional** under a category (not forced). All three kinds
  show their kind tag on the node face and have their own colour — category violet, service sky, feature green
  (`D-2026-07-05-G`, `D-2026-07-05-H`).
- **Participants per layer (`D-2026-07-05-E`):** each layer can name who takes part (`ref_actor_ids`), narrowing
  category ⊇ service ⊇ feature. A child's participant picker offers only its parent's participants. The narrowing
  is **soft**: when the parent names no one, the picker offers the whole actor roster, and no validator enforces it.
- **Drill:** **Selecting a service = 5-field inspector, no drill. Clicking a feature = drill into the Feature canvas**
  (the sole drill target). [The old "single-click on service = drill" is retired.]
- **Edges:** user-drawn/coach-confirmed hierarchy plus the common save-time orphan normalization. **No first-class
  service↔service edge** (user-journey retired). `anchor→category→service` outward direction (diverge). A top-level
  service is valid and receives an anchor spoke; a service already parented by a category does not.
- **Inspector (service 5 question-style fields):** ① `"누가 참여하나?"` (who participates?) (actor reference chips,
  multiple) ② `"왜 필요한가?"` (why is it needed?) (typed) ③ `"뭐가 좋아지나?"` (what improves?) (typed) ④ `"뭘 양보 못 하나?"`
  (what can't be conceded?) (core_value chips, multiple) ⑤ `"어떤 결로 다가가나?"` (in what manner does it approach?) (identity
  chips, multiple). The title is itself the interview question. References = pick from Foundation/Actors
  (if absent, create new, [`../concepts/ai-collaboration.md`](../concepts/ai-collaboration.md) §0.2). The old 9 fields are deleted.
- **Design-check state** *(user, `D-2026-10-05-A` (6))*: each service shows its feature-split check ("기능 나눔") and each
  feature its failure check ("실패 점검") as unchecked, checking, checked or needs re-check, in text, beside the node; when a
  checked or re-check state has problems remaining, the count follows ("남은 문제 2"). The person does not edit it: the
  coach records it, and the engine turns checking or checked back to needs re-check when the service's content or feature set
  changes (service) or the feature's content or flow changes (the feature and its service). The feature canvas shows the
  feature's failure-check state above the canvas. The publish confirmation shows how many checks are not finished ("점검이
  끝나지 않은 곳 N곳 — 기능 나눔 a, 실패 점검 b") and does not block publishing. *(Claude:)* the marker floats outside the node's
  measured size at the top right, so the work badge keeps the bottom right; a missing state reads as unchecked.
- **Layout:** `tree`. **Later expansion:** Services overview full behavior spec (model pinned only).

## Feature canvas — Execution (formerly Service-Detail)

A **UX flowchart** opened by clicking a feature (action → branch → outcome, action altitude). Opens as a dynamic
canvas tab (`{feature/service name}` label). Not a modal.

- **Anchor:** **none.** A hidden root-service node is the layout-hub fallback.
- **Nodes:** `step` (action) · `decision` (branch ◇) · flow edge · `note` (global context with no edges) ·
  `rule` (per-feature operating constraint) · `actor_ref` (read-only actor anchor). [Retired: mission_ref/value_ref/
  identity_ref/metric/content/group.]
- **`actor_ref` = read-only anchor (the crux this session):** displays "who starts/who can". Not edited here.
  The old `gives`/`receives`/`motivation`/`pain` are **retired** (value lives in Actors + the service
  5 fields). See `kinds-fields.md`.
- **Altitude guard:** up to user action → branch → outcome. Implementation logic (storage·query·render) is outside Novel
  (external agent). This line is the in-app coach → external-agent handoff.
- **Drill:** this canvas is the drill target. `actor_ref` click (single/double) = inspector only, no jump to Actors.
- **Edges:** governed by definition. Flow edge = `flow` (step→step). [The old injection edge was from when a foundation ref was a
  node — those refs moved out as chips, so the Feature canvas has no injection source.]
- **Inspector:** like every other canvas — the sidebar shows the palette until a node is selected, then that node's
  inspector; clicking empty space returns the palette. The always-on read-only subject-service inspector is retired
  (`D-2026-06-21-Q`).
- **Node render:** `step` = STEP tag + label (user action) + `⑂` badge (outgoing edges ≥2, derived) +
  `outcome` subtitle (inline edit) + `polarity` tint (positive=green/negative=red/neutral=user color).
  `decision` = diamond forced (no tag). Shape=meaning (master=rounded rectangle, `*_ref`=circle, decision=◇).
- **Layout:** actor-anchor layout (when there are subject edges): preserve actor positions → step/decision get dagre
  rank → direction from the subject edge handles (↔/↕ toggle). Code detail = Mashbill
  [`AUTO_LAYOUT.md`](../../plugins/mashbill/docs/AUTO_LAYOUT.md).
- **Later expansion:** full body re-description (drill·layout), action↔entity reference mechanism.

## Entities — Planning (derived, AI-maintained)

- **Status:** model pinned, **on-canvas interaction detail unwritten (later expansion).**
- **Nodes:** `entity` (+ project anchor). Symmetric with Actors (who/what).
- **Authorship:** two paths (user decision 2026-09-29). (1) The AI synthesizes·proposes them as a by-product of
  feature/service design → a human confirms. (2) The user drags an `entity` from the canvas toolbar and names it,
  so the design can be finished without AI like the other canvases. The coach's dedup check applies to path (1);
  on path (2) the user is responsible for not creating a second entity for the same thing. When two entities already
  on the canvas look like the same object, the coach points to both and asks whether to merge them; the user decides
  (user decision 2026-09-30).
- **Form:** concept map (name + one-line `"무엇을 담나"` (what does it hold) + rough relationship). Not a physical ERD.
- **Behavior:** strong dedup (identity matching, ask when ambiguous, quiet merge·no duplicates❌) · back-reference (read-only) ·
  proposed during chat (no auto-scan❌) · lean inspector. Integrity = [`../concepts/ai-collaboration.md`](../concepts/ai-collaboration.md) §3.
- **Edges:** the coach requests a project-anchor→entity spoke in the same confirmed action, and the common save-time
  normalization guarantees any still-unanchored entity receives that same canonical spoke. This only anchors the
  concept map visually; it does not implement the deeper service-target connectedness invariant. Being AI-maintained,
  the AI can also propose·draw entity↔entity rough relationship edges; those relationship edges remain independently
  editable·deletable.

## Work tab — Execution (Solera work-item graph)

Decisions: placement `D-2026-10-02-B`, data path `D-2026-10-02-A`, connectedness `D-2026-10-01-G`. Items marked
*(user)* were set by the user on 2026-09-29/30 (novel-workspace P-00000005); items marked *(Claude)* are Claude's
choices made while building it on 2026-10-02 and still open to the user's review.

- **Placement:** a tab of its own after the four design tabs, labelled 일감 / Work. It is not drawn on a design
  canvas *(user)*.
- **Source:** the Solera engine is the only owner of work items. The app reads and writes them only through that engine
  and redraws when the engine reports `work_changed`. If the engine cannot be reached, the tab says so and offers a
  retry; the design tabs keep working.
- **What is drawn:** the work-item tree, plus the published design nodes that work items realize (nodes that have a
  slug, labelled as on their design canvas). Unpublished nodes are not drawn: work attaches only to published nodes.
- **Edges:** two kinds that differ in shape, never in colour alone. *Membership* — parent work item → child, and work
  item → the design node it realizes — is a solid line without an arrowhead. *Order* — "this must be done before that",
  predecessor → successor — is a dashed line with an arrowhead *(Claude: the exact styles)*.
- **Work item face:** goal text; for an item with children, the completion percent the engine computed *(user)*;
  status (todo · doing · done); when it cannot start, the engine's reasons as text (waiting for another item, or names no
  design node). Every item without children has a checkbox (see "Checking items off"). Design nodes show no percent
  *(user)*.
- **Layout:** automatic top-down tree. Positions are not saved in this version *(Claude; the screen-data split,
  novel-workspace W-00000317, is still open)*.
- **Keyboard on the graph** *(user: MindNode style)*: with a work item selected, Tab creates a child and Return
  creates a sibling right after it; the new item opens for typing its goal. Double-click edits a goal; Return commits,
  Esc cancels and removes a new item left empty *(Claude: the editing keys)*. A child under an item that has a check
  command is refused with a message that says why (such an item is a leaf). At the root level Return creates a new root,
  and roots keep the engine's order (by id) *(Claude)*.
- **Choosing the node a new item serves:** when a new root has no design node, the app asks which published node it
  serves and offers every published node (every node that has a slug), not only those
  already drawn on the tab. The person may skip; the item is still created, but it cannot start
  until it or an ancestor names a node (`D-2026-10-01-G`).
- **Order links:** drag from one work item to another to add "this before that"; select an order edge and press
  Delete or Backspace to remove it. A link the engine rejects (for example, a cycle) is not drawn and the engine's
  reason is shown.
- **List beside the graph** *(user)*: a toggle shows the same tree as an indented list next to the graph, sharing the
  selection. In the list, Tab indents an item under the item above it, Shift+Tab outdents it, Return adds a sibling, and
  dragging moves an item to another parent or position; every change is a move in the engine and the graph follows.
  Roots cannot be reordered, because the engine orders roots by id *(Claude)*.
- **Folding and focus** *(user)*: any item with children can be folded; a folded item shows only its accepted fraction. Focus
  mode keeps the selected branch and dims everything else. *(Claude:)* fold with the item's toggle or `[` / `]` on the
  selected item, in the graph or the list; the fold state lasts for the session and is not saved; folding keeps the
  viewport; Esc leaves focus mode.
- **Badge on design canvases** *(user, `D-2026-10-04-A` (3))*: a published design node that work items realize shows
  counts per state on the bottom-right corner of its frame, never one total and never a percent: uphill ("오르막 N",
  what to do is not yet known), downhill ("내리막 N", the work is known and being done), and awaiting judgment
  ("판단 N"). Only non-zero states appear. Awaiting judgment is always shown; uphill and downhill appear only while the
  design canvas's work-progress toggle is on. Clicking the badge opens the Work tab focused on those items. Unpublished
  nodes show no badge. *(Claude:)* an unfinished item (`todo`, `doing`, `rework`) counts as downhill when its phase is
  executing and as uphill otherwise, since an empty phase means nobody has recorded that the work is known; finished
  and cancelled items are not counted. The toggle is off by default and lasts for the session; while it is off, a node
  with work and nothing awaiting judgment shows a plain "일감" / "work" marker so it still opens its work. "focused"
  means the first of those items is selected and focus mode lights the branches of all of them, until the person
  selects another item; returning to the Work tab later does not refocus. The badge floats outside the node's measured
  size, so a change in Solera never rewrites the design file.
  "확인 필요 N" / "Needs check N" counts active work items with no movement for at least 7 days and is always shown when nonzero, independent of the work-progress toggle (`D-2026-10-08-A`). The Work tab asks the person which stage each such item is in.
- **Checking items off** *(user; D-2026-10-02-D)*: every item without children has a checkbox, on the graph node and in
  the list. On an item without a check command, the checkbox finishes it, and pressing it again reopens it. On an item
  with a check command, the checkbox runs that command: a pass checks it, and a failure leaves it unchecked and shows
  the command's output on request; a passed check cannot be undone by hand. An item that waits for other work or names
  no design node cannot be checked, and its checkbox says why. Containers have no checkbox. *(Claude:)* Space checks
  the selected item in the graph or the list, and a check command shows "running the check" while it runs.
- **Accepted fraction** *(user, `D-2026-10-04-B` (1))*: an item with children, and a folded item, shows "accepted /
  currently known lowest items" ("받아들임 9/10"), never a percent. The numbers come from the engine; lowest items
  exclude cancelled ones. When the denominator changes, the reason appears beside it: "새로 N" (new lowest items),
  "N 빠짐" (lowest items left), or "나뉨" (a lowest item was split). *(Claude:)* the reason is computed in the app
  from the lowest items it last saw during the session and stays until the next change; when a split and other
  changes happen together, "나뉨" is shown.
  *Decided, not yet built (`D-2026-10-04-B` (2)–(6)):* finished items leave the progress view but stay reachable
  from their design node; a new publish re-checks only related in-progress items.
  *(user, `D-2026-10-04-A` (1)–(2)):* work items have no fixed level names. An item whose result was promised to the
  person is not finished when all its children are; it waits for judgment until the person tries the result and accepts
  it, and that acceptance can be reopened. *Decided, not yet built:* the person confirms pass conditions in plain words,
  not check code.
- **Judgment inbox** *(user, `D-2026-10-04-A` (2), `D-2026-10-04-B` (5))*: while any result promised to the person awaits
  judgment, the Work tab shows "판단 대기 N" / "N awaiting judgment"; it opens an inbox of those results and of results
  already accepted. Selecting one shows its goal, the design nodes it realizes, its children and their state, and its past
  judgments (action, reason, time), with the actions its state allows: awaiting judgment → accept, send back, cancel;
  accepted → reopen; otherwise → cancel. Send back and cancel require a reason. Reopen asks when the problem started:
  if the result never met its conditions, the acceptance is reopened; if it worked and broke later, the acceptance stays
  and a new item is made under the same parent for the same design nodes, awaiting the person's acceptance. Clicking a
  design-node badge whose items await judgment opens the inbox. *(Claude:)* with nothing awaiting judgment the count
  button is hidden and a "일감 상세" / "Work details" button keeps accepted results reachable; the inbox lists the newest
  items first (items carry no time they entered judgment).
- **AI proposals** *(user, `D-2026-10-09-A` (1): Mashbill proposes once, the app writes to Solera only what the person
  confirms; the rest Claude, from the self-design features "설계에서 일감 만들기" and "AI가 나눈 일 확정하기")*:
  - *Making one work item from the design.* "AI로 일감 만들기" asks which published nodes the work serves (the same
    picker as for a new root) and what result the person wants, in their own words. The app sends
    `POST /api/projects/{id}/work-proposals/item` to Mashbill with `{"slugs": [slug...], "outcome": str}`; Mashbill reads
    those nodes from its latest published releases, asks the workspace's chosen provider once (`complete_once`, 120 s),
    and returns `{"proposal": PlanNode}` with `goal`, `conditions`, `pass_examples`, `fail_examples`, `risks`, `accept`
    (`person` or `children`), `realizes` (the slugs) and `basis` (`<slug>@vS<N>` per slug). A slug that was never
    published is refused (`unknown_slug`, 404).
  - *Splitting a confirmed item.* On an item that is not accepted, protected or cancelled, "AI로 나누기" sends
    `POST /api/projects/{id}/work-proposals/split` with `{"item": {"goal", "conditions", "pass_examples",
    "fail_examples", "risks", "realizes", "basis"}, "existing_children": [goal...]}` — the app copies these from Solera,
    since Mashbill never reads Solera. Mashbill returns `{"proposal": {"items": [PlanNode...]}}`: child results as
    children, work that only has to finish first as `after_keys`, and nothing that repeats an existing child's goal.
    Several results may wait for one release item, and a finished release item does not finish them.
  - *Failure.* No chosen provider (`no_chat_provider`, 409), a failed or timed-out call, or a reply that is not a valid
    proposal — including one that carries a `gate` — returns `proposal_failed` (502) with the reason. The app keeps the
    person's input, shows the reason, and offers try again, write it by hand, or cancel; it never retries on its own.
    Nothing is written either way.
  - *Showing and confirming.* *(Claude)* A proposal is drawn on the Work tab where it would go — a new root, or under
    the item being split — with a dashed outline and a "제안" / "Proposal" tag, never by colour alone; its fields can be
    edited in place, and in a split the person can delete proposed items, move them, or turn a child into an order link
    before confirming, which is how part of a proposal is taken. The proposal lives only in the app until confirmed or
    discarded; it is not a draft (`D-2026-10-01-A`), and leaving the tab discards it after a confirmation prompt.
    Discarding writes nothing and leaves the item being split as it was.
  - *Before writing.* *(Claude)* The app asks Mashbill for the current release of each slug
    (`POST /api/projects/{id}/work-proposals/basis`, `{"slugs": [...]}` → `{"basis": [...]}`). If a release changed since
    the proposal, it shows what changed and offers: propose again on the new design, confirm against the old basis, or
    discard. It then sends one `POST /api/work/plans` to Solera with a `request_id` made once per proposal. If the
    result is unknown (no response), it shows "확인 필요" / "Needs check" and sends the same request again, which
    creates nothing twice.
- **Linking work to the design** *(user, `D-2026-10-01-G` (2)–(3) and W-00000320 decision 1 ⓐ; the mechanics Claude,
  `D-2026-10-09-B`)*:
  - *Importing.* Right after a service publish is confirmed, the app imports that release into Solera
    (`POST /api/work/imports`). Before any write on the Work tab (create, plan, check), it asks Mashbill for the latest
    release of every published service (`GET /api/projects/{id}/published-releases` → `{"releases": [{"service":
    slug, "release": "vS<N>", "source": path}]}`) and imports any not imported yet. Opening the tab writes nothing. An
    import failure is shown with its reason and does not block reading or creating. While an import has failed and
    no release is imported, the app does not send a check for an item that neither it nor an ancestor links to a
    published node — the engine could not enforce the rule — and says why; other checks proceed. When no service is
    published, nothing is imported and checks proceed as in Solera on its own: the workspace is not linked to a design
    (D-2026-10-01-G "Applied in Solera").
  - *Blocked items.* With a design imported, an item without children that neither it nor an ancestor links to a
    published node cannot be checked; its checkbox says so, and the item offers "노드 고르기" / "Choose a node" (the
    published-node chooser used for a new root) and "AI로 노드 찾기" / "Find a node with AI". The latter sends
    `POST /api/projects/{id}/work-proposals/nodes` with `{"goal", "conditions", "ancestors": [goal...]}`; Mashbill
    asks the chosen provider once (`complete_once`, 60 s) with the published nodes it knows and returns
    `{"candidates": [{"slug", "label", "reason"}]}` (at most three; a slug that is not published is dropped as invalid,
    and a reply with none valid is `proposal_failed`). Errors as in "AI proposals → Failure". Picking a candidate sets
    the item's `realizes` (PATCH). *(Claude)* When no candidate fits, "설계에 먼저 그리기" / "Draw it in the design
    first" opens the Services tab; drawing the node is left to the person and the coach there.
- **Not in this version:** deleting items.
