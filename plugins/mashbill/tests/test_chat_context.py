"""Shared chat-context builders — canonical home (D-2026-06-15-D).

``build_framing_preamble`` + ``build_context_preamble`` moved out of the HTTP
endpoint module into ``mashbill.chat_context`` so the MCP path can share them
without importing the HTTP layer. These tests pin the SSOT at its new home;
``test_endpoints_chat.py`` continues to cover the in-app wiring through the
re-export.
"""

from __future__ import annotations

from mashbill.chat_context import (
    PROPOSE_PLAYBOOK,
    SCOPE_FRAMING,
    SELECTION_DETAIL_CAP,
    build_context_preamble,
    build_framing_preamble,
    build_system_prompt,
)


def test_framing_maps_each_canvas_to_its_vision_phase() -> None:
    assert "Discovery" in build_framing_preamble("foundation")
    assert "Planning" in build_framing_preamble("actors")
    assert "Planning" in build_framing_preamble("services")
    assert "Execution" in build_framing_preamble("feature:svc_1")


def test_foundation_framing_reads_a_tradeoff_answer_as_a_value() -> None:
    """CD-2026-07-25-B (W-122): the identity confirm invites the failure — the
    founder answers "이 모습이 맞나요?" with a VALUE ("복잡함보다 명확한 고객경험을
    택해야 해요") and the coach reads it only as agreement to its own proposal, so
    the value never reaches the map. Measured at the exact moment on corpus
    conversations (next-turn replay, 3 draws): without the rule the coach
    registers 7/15; with it 9/9. The framing must carry the rule at the moment it
    fails — the principles catalog cannot reach it there (0.178-0.180 saga)."""
    framing = build_framing_preamble("foundation")
    assert "identity confirmation" in framing
    assert "treat it as a VALUE rather than agreement" in framing
    assert "register that value in the same turn" in framing


def test_framing_empty_for_project_and_unknown_scope() -> None:
    assert build_framing_preamble("project") == ""
    assert build_framing_preamble("nope") == ""


def test_framing_uses_base_scope_for_parametric_feature() -> None:
    assert build_framing_preamble("feature:a") == SCOPE_FRAMING["feature"]
    assert build_framing_preamble("feature:a") == build_framing_preamble("feature:b")


def test_per_service_thread_gets_value_framing() -> None:
    """Per-service thread (D-2026-06-26-A): a ``service:<id>`` scope coaches the
    value-level big picture — the same Planning framing as the Services canvas
    (DRY, no duplicate string), parallel to ``feature:<id>``'s Execution framing."""
    assert "Planning" in build_framing_preamble("service:svc_1")
    assert build_framing_preamble("service:svc_1") == SCOPE_FRAMING["services"]
    assert build_framing_preamble("service:a") == build_framing_preamble("service:b")


def test_context_preamble_lists_selection() -> None:
    p = build_context_preamble("foundation", [{"id": "n1", "kind": "core_value", "label": "Trust"}])
    assert "foundation" in p and "core_value" in p and "Trust" in p and "n1" in p


def test_context_preamble_empty_for_project_and_empty_selection() -> None:
    assert build_context_preamble("project", [{"id": "n1", "kind": "x", "label": "y"}]) == ""
    assert build_context_preamble("foundation", []) == ""
    assert build_context_preamble("foundation", "not-a-list") == ""


def test_context_preamble_caps_detailed_nodes() -> None:
    sel = [{"id": f"n{i}", "kind": "k", "label": f"L{i}"} for i in range(SELECTION_DETAIL_CAP + 5)]
    p = build_context_preamble("services", sel)
    assert str(SELECTION_DETAIL_CAP + 5) in p  # total count surfaced
    assert f"n{SELECTION_DETAIL_CAP + 4}" in p  # overflow ids still listed


def test_canvas_system_prompt_instructs_proactive_proposing() -> None:
    """A canvas coach must PROPOSE, not only ask (ai-collaboration.md §적극 토론
    코치, D-2026-06-16-H; user report 2026-07-02). Every canvas scope carries the
    propose playbook so the agent drafts concrete candidates unprompted rather
    than passively interrogating."""
    for scope in ("foundation", "actors", "services", "feature:svc_1", "service:svc_1"):
        prompt = build_system_prompt(scope)
        assert PROPOSE_PLAYBOOK in prompt, scope
        assert "propose" in prompt.lower(), scope


def test_project_scope_has_no_propose_playbook() -> None:
    """Project gets universal rules but no tone, write/propose playbook, or framing."""
    assert PROPOSE_PLAYBOOK not in build_system_prompt("project")


def test_coach_keeps_mechanics_and_field_names_out_of_sight() -> None:
    """B-6 (regression, user report + transcript 2026-07-02): the coach must not
    verbalise its internal operations — it said '저장됐어요' and exposed internal
    field names ('statement' / 'body') to the user. The system prompt must instruct
    it to never announce the save and to speak in the user's own words, not Novel's
    storage-field names. W-62 (O-00000003 #2): the English-only 'saved'/'done'
    examples let '저장했어요' leak back through, so the ban is now language-explicit."""
    p = build_system_prompt("foundation").lower()
    assert "internal field names" in p
    assert "do not announce" in p
    assert "any language" in p
    assert "저장했어요" in build_system_prompt("foundation")


def test_coach_leads_and_covers_full_concept() -> None:
    """B-7 (regression, user report + transcript 2026-07-02): the coach declared a
    canvas 'done' after one thin identity and handed the wheel back ('what
    next?'), forcing the user to point out what was missing. The prompt must
    keep leading until each concept is clear enough to guide action, without
    imposing a fixed number of identity guidelines."""
    p = build_system_prompt("foundation").lower()
    assert "declare a canvas complete after one item" in p
    assert "check every facet before moving on" in p


def test_canvas_system_prompt_paces_the_whole_canvas() -> None:
    """Sim finding (2026-07-02, Airbnb full-flow baseline): the coach is thorough
    but slow — 8 foundation turns never reached identity, 8 services turns never
    reached features. The prompt must carry a pacing rule: keep the WHOLE canvas
    in view, land an item once it's good enough and move on, and draft the
    later items (identity) yourself from what already stands."""
    for scope in ("foundation", "services", "actors"):
        p = build_system_prompt(scope).lower()
        assert "whole canvas" in p, scope
        assert "good enough" in p, scope


def test_services_framing_pulls_features_forward() -> None:
    """Same sim finding: the services interview (five slots, then features) is so
    heavy that features never arrive. The framing must pull feature proposals
    forward — as soon as the service's problem/value stand, not after all five
    slots are filled."""
    f = build_framing_preamble("services").lower()
    assert "as soon as" in f
    assert "do not wait for every service field" in f


def test_services_framing_surfaces_entities_as_byproduct() -> None:
    """Benchmark finding (2026-07-02, 8-service batch): entities were 0/8 — the
    surface-the-entity instruction lived only in the entities-scope framing,
    which no design conversation ever runs under. The services framing (where
    features are born) must tell the coach to spot the data 'things' features
    handle and register confirmed ones on the entities canvas."""
    f = build_framing_preamble("services").lower()
    assert "entity" in f
    assert "entities canvas" in f


def test_entities_framing_defends_cross_context_intent_without_overruling_user() -> None:
    """W-85: entity removal must surface accumulated intent without taking
    the final decision away from the user."""
    f = build_framing_preamble("entities").lower()
    assert "removing, merging, or simplifying" in f
    assert "reverse references" in f
    assert "intent accumulated across" in f
    assert "steps, services, and features" in f
    assert "follow the user's final decision" in f
    assert "never decide for them" in f


def test_write_playbook_allows_entity_registration_cross_canvas() -> None:
    """Same finding: the write playbook's 'adds one bare node to the current
    canvas' line blocked the entity byproduct. Registering a confirmed entity
    on the entities canvas from a design conversation must be explicitly
    allowed (still confirmation-gated)."""
    from mashbill.chat_context import WRITE_PLAYBOOK

    p = WRITE_PLAYBOOK.lower()
    assert "entities canvas" in p


def test_pace_playbook_wraps_up_missing_items() -> None:
    """Identity landed in only 3/8 batch runs — sessions end with required
    items empty. The pace playbook must carry a wrap-up rule: when the
    conversation nears its end and a required item is still empty, draft it
    NOW and ask for one quick confirm."""
    from mashbill.chat_context import PACE_PLAYBOOK

    p = PACE_PLAYBOOK.lower()
    assert "draft it now" in p


def test_services_framing_maps_the_landscape_first() -> None:
    """Benchmark finding (2026-07-02): real products run on 5-6 value-exchange
    surfaces but the coach lands 2-3 — it dives deep into the first service
    named instead of sweeping the landscape. The framing must open with a
    canvas-level map: propose the full set of candidate services (derived from
    the mission and actors), confirm the map, THEN detail each one."""
    f = build_framing_preamble("services").lower()
    assert "identify the full set of services first" in f
    assert "then describe each service" in f


def test_services_framing_derives_the_entity_map_unprompted() -> None:
    """User directives (2026-07-02): "엔티티는 상상해서라도 만들어보세요" +
    "찾을 수 없으니 자율적 판단이 필요" — entities are the AI-maintained canvas
    (D-2026-06-17-I): the coach derives the map from the features and registers
    it AUTONOMOUSLY (no per-entity confirmation question), mentioning it in one
    light line; the user reviews/edits/deletes on the canvas."""
    f = build_framing_preamble("services").lower()
    assert "every product entity the service actually needs" in f
    assert "2–5 entities" not in f
    assert "before moving to the next service" in f
    assert "register them on the entities canvas" in f
    assert "without asking permission for each entity" in f
    assert "등록해둘까요" not in f  # the ask-first gate is gone for entities


def test_foundation_framing_does_not_force_a_value_count() -> None:
    """D-2026-08-18-D: real conflicts decide which values belong. A benchmark
    count is not a quota for a particular project."""
    f = build_framing_preamble("foundation").lower()
    assert "do not target a number" in f
    assert "real conflict" in f
    assert "two or three" not in f


def test_services_framing_maps_outcomes_not_internal_processes() -> None:
    """D-2026-08-18-B: services divide the outcomes people seek. Internal
    processes still do not become services, but a multi-actor exchange is no
    longer required."""
    f = build_framing_preamble("services").lower()
    assert "one coherent outcome" in f
    assert "one or more human actors" in f
    assert "internal processes" in f
    assert "do not invent actors" in f
    assert "exchange lines" not in f


def test_propose_playbook_switches_to_drafts_on_thin_replies() -> None:
    """Persona round (2026-07-02, Discord × terse founder): with a
    short-answer user the coach kept widening with open questions and landed
    ONE core value (J 1/7), an unfinished identity, and half-empty reference
    slots — the worst elicitation of any run. Thin replies mean the user
    can't or won't elaborate: the coach must narrow to draft-first mode —
    one concrete candidate at a time, answerable in a word (eleventh sim
    iteration)."""
    p = build_system_prompt("foundation").lower()
    assert "for a short reply" in p
    assert "offer one draft first" in p
    assert "in a word" in p


def test_propose_playbook_distills_flooding_replies() -> None:
    """Persona round (2026-07-02, YouTube × rambler founder): six actors
    registered, ZERO with body text — the coach chased the tangents and never
    landed the content. Reply weight has two poles: thin means narrow to
    drafts; FLOODING means distill — extract the usable pieces, land each in
    its node while fresh, then steer back to the thread (twelfth sim
    iteration)."""
    p = build_system_prompt("actors").lower()
    assert "for a long reply" in p
    assert "summarize the useful parts" in p
    assert "return to the current topic" in p


def test_feature_framing_says_the_coach_places_the_actor_anchor_itself() -> None:
    """Flows carried no actor in 100+ measured canvases (novel-workspace O-25).
    Two causes stacked: ``create_node`` could not build an ``actor_ref`` at all
    (fixed — the target is now picked while creating it), and this framing called
    the actor "a read-only reference", which the coach read as "not mine to
    make". It never even attempted a write during a dedicated who-does-what
    segment (W-142). Read-only forbids RE-POINTING an anchor here, not placing
    one."""
    p = build_system_prompt("feature:x")
    assert "actor_ref" in p
    assert "read-only" in p.lower()
    # The trigger is the founder settling who acts — NOT a standing task while
    # the flow is being drawn. Both attempts that pushed actors into the flow
    # talk itself shrank the flow (steps 2.81->1.50, then 4.15->2.91).
    lowered = p.lower()
    assert "when the founder" in lowered or "once the founder" in lowered


def test_foundation_framing_proposes_candidate_values_from_the_talk() -> None:
    """Round 3: values depth is founder-dependent — guarded founders volunteer
    nothing and probing stalls at 1-3 values, while the terse run proved
    drafts work (1→5 registered). The coach now also PROPOSES candidate
    values it hears in the mission talk, alternating with probing
    (fourteenth sim iteration)."""
    f = build_framing_preamble("foundation").lower()
    assert "candidate values you hear" in f
    assert "alternate" in f


def test_foundation_framing_takes_the_counter_stance_once_per_pillar() -> None:
    """W-133 (DE-00000003): the coach challenged only what it judged weak, so a
    candidate the founder stated confidently was registered untested. It now
    steelmans the case AGAINST each mission/value right before confirming and
    lets the founder defend it. Measured over 14 baseline vs 12 experiment
    plates: challenge major +2.24 against a plate-to-plate spread of 1.83, with
    founder turns getting LONGER (no defensive withdrawal). Bounded to ONE per
    pillar — the gentle-invitation tone (§0.1③) must survive the debate.
    W-00000249 moved the rule out of the foundation framing into the shared
    ASK_DIRECTION_PLAYBOOK, where it is the OPPOSITE direction and reaches every
    canvas; foundation still receives it through the composed system prompt."""
    p = build_system_prompt("foundation").lower()
    assert "opposite side once" in p
    assert "never more" in p


def test_services_framing_registers_entities_with_each_feature_batch() -> None:
    """Round 3: entity registration was all-or-nothing (0 in 9 of 12 runs vs
    9/9/23) — the 'before leaving the canvas' checkpoint fires too late or
    never. Entities now land in the same breath as each service's feature
    batch; a service with features but zero entities is unfinished
    (fifteenth sim iteration)."""
    f = build_framing_preamble("services").lower()
    assert "at the same time as the features" in f
    assert "zero entities is unfinished" in f


def test_foundation_framing_lands_identity_mid_phase() -> None:
    """Round-3 regression (2026-07-03): identity 0/12 — iteration ⑨'s
    hunt-values-until-dry ate the foundation budget and identity never came
    (round 2 was 7/8). Depth must not displace completeness: identity lands
    MID-phase (after 2-3 values stand, draft → quick confirm → back to value
    hunting); a session ending with identity empty is a failed session.

    (Merged from a same-named twin that shadowed this one — sixteenth sim
    iteration housekeeping: a duplicate ``def`` means the first body never
    runs, so its assertions live here now. Nineteenth iteration: the trigger
    lost its number — "two or three" anchored the coach to stop at 2-3, so
    the checkpoint is now "once the first values stand".)"""
    f = build_framing_preamble("foundation").lower()
    assert "start identity before the end" in f
    assert "failed session" in f
    assert "once the first values are confirmed" in f
    assert "then continue asking about values" in f
    assert "identity still empty is a failed" in f


def test_foundation_framing_returns_to_a_declined_mission() -> None:
    """W-00000254 (2026-08-23): two coupang plates run with a founder who
    declines the first draft ended with NO mission on the canvas, while three
    values and an identity landed. The coach offered a mission twice, was
    pushed back twice, dropped it to harvest the values the pushback gave, and
    only came back on the second-to-last turn — too late to confirm anything.

    A mission is what every later canvas points at, so parking it is worse than
    parking anything else. The framing must send the coach back to the mission
    right after folding in the objection, and must name an empty mission at the
    end as a failed session, the way it already does for identity."""
    f = build_framing_preamble("foundation").lower()
    assert "re-offer the mission" in f
    assert "never park it" in f
    assert "mission still empty is a failed session" in f


def test_foundation_framing_resumes_value_hunt_after_identity() -> None:
    """Iteration 17 (2026-07-03): values stalled at 1-3 registered in all 11
    runs of the day, across personas AND founder model families — the
    mid-phase identity checkpoint ("once two or three values stand") reads
    as a stopping point, and the 'then return to hunting' never fires. The
    framing must name the checkpoint as a pit stop: registering the identity
    does NOT end the value hunt."""
    f = build_framing_preamble("foundation").lower()
    assert "confirming identity does not finish the value work" in f
    assert "continue asking about values" in f


def test_write_playbook_demands_natural_korean() -> None:
    """B-10 (user report 2026-07-03): the coach registered '자유하되, 방치하지
    않는다' — a nonexistent conjugation — as a core value label, plus hangul
    typos (캐페인/리봰/숬폼) on entity labels, in both founder families.
    Canvas text is user-facing product output: the write playbook must demand
    natural, correctly-spelled Korean, reread before saving."""
    p = build_system_prompt("foundation").lower()
    assert "natural" in p
    assert "typo" in p
    assert "reread" in p


def test_foundation_framing_lands_values_in_batches() -> None:
    """RESTORED (D-2026-07-03-K reverts D-2026-07-03-I, same day): the batch
    rule looked like a dead letter — transcript audits showed strict
    one-per-turn — but removing it collapsed values registration back to 2-3
    in BOTH v0.143 confirmation runs (v0.142 12-turn arm: 5-7) while features
    and entities ballooned: dead by the letter, load-bearing in effect (it
    keeps session energy on values). Keep the rule; never judge a prompt rule
    by compliance alone."""
    f = build_framing_preamble("foundation").lower()
    assert "collect the confirmed values" in f
    assert "register all of them together" in f


def test_foundation_framing_uses_value_domains_as_prompts_not_a_quota() -> None:
    """D-2026-08-18-D: domain examples help recall conflicts but do not force
    coverage or a target number."""
    f = build_framing_preamble("foundation").lower()
    assert "prompts, not a quota" in f
    assert "only when the person needs help" in f
    assert "ask across distinct areas" not in f
    assert "two or three" not in f


def test_write_playbook_fills_placeholder_labels_too() -> None:
    """D-2026-08-18-F: only Mission is unique. Values and identities use short,
    meaningful labels so several guidelines remain distinguishable."""
    p = build_system_prompt("foundation").lower()
    assert "placeholder" in p
    assert "same update_node call" in p or "same write" in p
    assert "never the label" in p
    assert "mission is the only unique kind" in p
    assert "values and identities get a short meaningful label" in p
    assert "ask which" in p


def test_coach_consults_design_principles_when_judging() -> None:
    """D-2026-07-03-P: the coach must know WHERE its evaluation knowledge lives
    — consult get_design_principles before challenging weak content, so the
    challenge axis gets teeth without blowing the prompt budget. Since W-61 this
    lives in the mainline EVALUATE_PLAYBOOK, not buried in the propose playbook."""
    p = build_system_prompt("foundation").lower()
    assert "get_design_principles" in p


def test_evaluate_playbook_promotes_judging_to_mainline() -> None:
    """W-61 (P-00000004 ⓐ, Codex coach finding 4): evaluating a design was a
    conditional two-line side-branch inside PROPOSE_PLAYBOOK while WRITE_PLAYBOOK
    was a large block, so the coach shrank into a canvas scribe rather than a
    design critic. Evaluation is now its own mainline playbook composed into
    every canvas prompt, naming the coach's three jobs (elicit · evaluate ·
    plan) so judging is a first-class duty, not an afterthought."""
    from mashbill.chat_context import EVALUATE_PLAYBOOK

    for scope in ("foundation", "actors", "services", "feature:x", "service:x"):
        p = build_system_prompt(scope)
        assert EVALUATE_PLAYBOOK in p, scope
    # the three roles are named, evaluation among them
    low = build_system_prompt("foundation").lower()
    assert "get_design_principles" in low
    assert "evaluate" in low or "judge" in low
    # the cross-canvas project scope gets no coaching playbooks
    assert EVALUATE_PLAYBOOK not in build_system_prompt("project")


def test_write_playbook_names_the_anchor_as_foundation_parent() -> None:
    """B-14 (D-2026-07-03-T): coach-registered foundation pillars floated —
    partly the tool bug (create_edge rejected the synthetic anchor), partly
    the prompt never saying WHO a pillar's parent is. The playbook must name
    __project_anchor__ as the foundation parent so the one-yes covers the
    spoke too."""
    p = build_system_prompt("foundation")
    assert "__project_anchor__" in p


def test_services_framing_discriminates_feature_from_service() -> None:
    """A feature helps a person reach its service's outcome. A candidate that
    owns a distinct outcome belongs at service level."""
    f = build_framing_preamble("services").lower()
    assert "helps a person reach that service outcome" in f
    assert "owns a distinct outcome" in f


def test_entity_relationship_lines_carry_a_verb_label() -> None:
    """User live review (2026-07-04, coupang entities): 7 relationship lines,
    zero labels — "주문→상품" reads as nothing ("엔티티는 왜 저렇게 해놨는지
    모르겠어요"). A relationship line must carry its verb (담는다/남긴다);
    an unlabeled entity line is unfinished."""
    for scope in ("services", "entities"):
        p = build_system_prompt(scope).lower()
        assert "verb" in p, scope
        assert "unlabeled" in p or "label" in p, scope


def test_new_entities_get_a_project_anchor_spoke_in_the_same_action() -> None:
    """W-87: entity relationship edges alone leave the concept map floating.

    Entity registration can originate from Services, the Entities canvas, or a
    Feature conversation.  Every such coach must use the existing persisted
    edge tool in the same confirmed action, without replacing the separate
    ``create_node`` / ``create_edge`` contract.
    """
    expected = "create_edge source __project_anchor__ target <new entity>"
    for scope in ("services", "entities", "feature:feature_1"):
        prompt = build_system_prompt(scope)
        assert "EVERY new entity gets a stored anchor edge" in prompt, scope
        assert expected in prompt, scope


def test_services_framing_draws_entity_relationships() -> None:
    """B-18 (user live-watch): entities landed as disconnected islands — the
    user expected an ERD-like map. D-2026-06-17-I already allows AI-drawn
    relationship edges on the entities canvas; the framing must instruct the
    coach to connect related entities as it registers them."""
    f = build_framing_preamble("services").lower()
    assert "connect related entities" in f
    assert "create_edge" in f


def test_actors_framing_draws_value_flow_edges() -> None:
    """B-21 (user live-watch round, 2026-07-04): 7 actors registered, 2
    relationship edges — the interview elicits who-gives-what-to-whom but the
    coach never drew it. The actors framing must land the value-flow lines
    (create_edge, label = what flows) as actors register; an actor with no
    lines is unfinished."""
    f = build_framing_preamble("actors").lower()
    assert "create_edge" in f
    assert "without a value-flow line is unfinished" in f


def test_foundation_framing_derives_identity_as_behavior_guidelines() -> None:
    """D-2026-08-18-F: identity may contain several standing guidelines, but
    Novel must not force voice, energy, speech style, or any other fixed set."""
    f = build_framing_preamble("foundation").lower()
    for rule in (
        "one or more identity guidelines",
        "short directive",
        "one-line summary",
        "concrete actions",
        "do not target a count or force predefined facets",
    ):
        assert rule in f, rule
    assert "voice, energy, and speech style" not in f


def test_actors_framing_nests_roles_under_families() -> None:
    """B-27 (user, 2026-07-04, hand-arranged example on the live canvas):
    actors form a HIERARCHY — top-level role families connect to the anchor;
    concrete actors register UNDER their family (near= + create_edge
    family→actor); benefit-seekers split (무료/유료) into nested roles.
    Value flows stay between concrete actors. W-61: the structure stays, the
    code metaphor (inheritance/subclass) is gone."""
    f = build_framing_preamble("actors").lower()
    assert "hierarchy" in f
    assert "near=<family id>" in f
    assert "무료/유료" in f


def test_actors_framing_has_no_code_metaphor() -> None:
    """W-61 (P-00000004 ⓐ, Codex coach findings 1·2): the actors framing carried
    a code metaphor (\"like inheritance in code\", \"superclass\", \"like
    subclasses\") that collided with COACH_TONE's \"never force jargon\" guard —
    the coach was observed telling founders their actors form an \"inheritance
    tree\". The structural directive stays; the developer vocabulary is banned."""
    p = build_system_prompt("actors").lower()
    for jargon in ("inheritance", "superclass", "subclass"):
        assert jargon not in p, jargon


def test_mission_lands_as_one_line_with_detail_in_the_note() -> None:
    """B-30 (user, 2026-07-04): the mission reads best as ONE line on the
    canvas face; the reasoning moves to its note (body)."""
    f = build_framing_preamble("foundation").lower()
    assert "one line" in f
    assert "note" in f


def test_actors_families_take_domain_words_from_the_start() -> None:
    """User live-watch (2026-07-04): the coach stayed wedded to generic
    운영자/사용자 labels — coupang's buyers hung under a generic 사용자
    family ("일반 구매자와 멤버십회원은 구매자로 묶을 수 있죠"), and six
    same-nature externals (광고주, 카드사·은행…) sat as separate top-level
    families instead of one 파트너/3rd party group. Since D-2026-07-04-P the
    canvas starts EMPTY: families mint in the service's own words from the
    first registration; same-nature families nest under one parent so the
    top level stays a handful."""
    p = build_system_prompt("actors")
    assert "starts empty" in p.lower()
    assert "own word" in p.lower()
    assert "same-nature" in p.lower()
    assert "handful" in p.lower()
    # 8-service sample (2026-07-04): slack kept the generic 사용자 label and
    # baemin closed with SIX top families — the grouping must run as a
    # CLOSING sweep, and the rename example needs more than one domain.
    assert "멤버" in p
    assert "before closing" in p.lower() and "top famil" in p.lower()
    # 운영자 = internal staff ("운영자는 내부직원이라는 뜻입니다") — employed
    # operational roles (배송 기사, 물류) nest under it, not beside it.
    assert "internal staff" in p.lower()
    # …but employment decides membership, not the role name: gig riders may
    # be external ("라이더 같은 경우에는 내부자가 아닐 수도") — the coach
    # asks instead of assuming.
    assert "employment" in p.lower()


def test_actors_every_family_gets_an_anchor_spoke() -> None:
    """Coupang verification round (2026-07-04): the coach wired every family
    it created to the anchor but left one family floating — the only
    hub-less family on the canvas. Rules must bind EVERY family, whoever
    created it and whenever it landed."""
    p = build_system_prompt("actors")
    assert "every family" in p.lower()
    assert "anchor line" in p.lower()


def test_services_use_existing_human_actors_without_requiring_exchange_lines() -> None:
    """D-2026-08-18-B supersedes the exchange-line derivation rule."""
    f = build_framing_preamble("services").lower()
    assert "existing human actors" in f
    assert "exchange lines" not in f
    assert "ref_actor_ids" in f


def test_services_categories_are_optional_and_never_forced() -> None:
    """A category is useful only when several services truly share a theme or
    surface. A single service never needs a wrapper for completeness."""
    f = build_framing_preamble("services")
    low = f.lower()
    assert "categories are optional" in low
    assert "do not create a category" in low
    assert "shared theme or surface" in low


def test_feature_subjects_narrow_to_service_participants() -> None:
    f = build_framing_preamble("services").lower()
    assert "existing human actors" in f


def test_feature_doers_are_wired_not_just_narrowed() -> None:
    """Participation-chain live validation (baemin 2026-07-05 새벽): services
    and platforms got their participants wired, but features landed 0/24 —
    the framing said subjects NARROW to the service's participants without
    ever saying to SET them (the B-41 rule-without-action class). The
    framing must carry the explicit write."""
    f = build_framing_preamble("services").lower()
    assert "each feature's doer" in f


def test_foundation_every_pillar_gets_anchor_line() -> None:
    """B-41 (foundation live check 2026-07-05 — first blank-canvas run): the
    coach anchor-connected only the FIRST node of each kind; the 2nd value
    and 2nd identity floated, and after being corrected its NEXT new value
    floated again. Same lesson as the actors families: the rule must bind
    EVERY registration, in the same turn."""
    f = build_framing_preamble("foundation").lower()
    assert "anchor edge" in f
    assert "same turn" in f
    assert "every new foundation node" in f


def test_actor_is_defined_by_exchange_not_persona_card() -> None:
    """User live app session (2026-07-04): asked for "주요 액터들", the coach
    answered with persona cards — narrative person-descriptions ("서비스를
    이야기처럼 써내려가며 큰 그림을 놓치지 않으려는 사람") instead of
    exchange roles. The rule must go beyond "ask which role when an
    individual is named": an actor is DEFINED by what it gives and
    receives, never described as a persona."""
    p = build_system_prompt("actors").lower()
    assert "persona" in p
    assert "gives and receives" in p


def test_foundation_and_actors_start_from_an_empty_canvas() -> None:
    """D-2026-07-04-P — no seed nodes anywhere: the coach must know the
    canvas starts empty and that IT creates nodes as content lands
    (capability lesson of 2026-07-04: a rule without the create step fails
    silently)."""
    for scope in ("foundation", "actors"):
        p = build_system_prompt(scope).lower()
        assert "starts empty" in p, scope
        assert "create" in p, scope


def test_actors_hierarchy_arrow_points_at_the_family() -> None:
    """B-34 (user live-watch 2026-07-04): fold buttons sat on LEAF actors —
    the coach drew family → actor while the stored fold convention is
    child → family (target = parent, fold_endpoints). The framing must
    direct the arrow AT the family."""
    p = build_system_prompt("actors")
    assert "create_edge from the new actor to its family" in p


def test_actors_flows_land_with_each_registration() -> None:
    """B-21 follow-up (coupang round: hierarchy 7 lines, flows 0 — taxonomy
    ate the turn budget): each concrete actor's exchanges are drawn in the
    SAME turn it registers, never deferred until the taxonomy is done."""
    f = build_framing_preamble("actors").lower()
    assert "same turn each actor is registered" in f


def test_system_prompt_stays_under_saturation_budget() -> None:
    """Sixteenth sim iteration (2026-07-03): the coach prompt grew with every
    rotation — the composed canvas prompt hit ~1,800–2,000 words and the
    v0.138 sample showed instruction slips (a connect habit missed, a
    'saved' announcement) that read as prompt saturation, not missing rules.
    Raised 1300 -> 1350 (D-2026-07-03-U): the evaluation principles moved
    OUT to the get_design_principles tool, and the user-directed mechanics
    (anchor parent, label rules, entity edges) needed the headroom.
    Raised 1350 -> 1410 (W-61, P-00000004 ⓐ): promoting evaluation from a
    two-line branch buried in PROPOSE_PLAYBOOK to the mainline EVALUATE_PLAYBOOK
    (a design critic, not a scribe) inherently adds a titled block. The block is
    compressed to essentials and the evaluation KNOWLEDGE still stays in the
    get_design_principles tool, so the raise is minimal.
    Raised 1410 -> 1445 (CD-2026-07-25-B, W-122): the identity-confirm rule — a
    tradeoff answer is a value, not agreement — measured 7/15 -> 9/9 at the exact
    failure moment, and framing is the only surface that reaches it (the
    principles catalog demonstrably cannot — the 0.178-0.180 saga). The rule is
    compressed to 32 words; the surrounding phrasings are pinned by earlier
    measured decisions and stay.
    Raised 1445 -> 1500 (DE-00000003, W-133): the counter-stance rule — argue the
    opposite side once before confirming a pillar — measured challenge major
    +2.24 against a plate-to-plate spread of 1.83 over 14 baseline vs 12
    experiment plates, with founder turns getting LONGER (no withdrawal). It is
    compressed to 42 words and foundation had 2 words of headroom left, so no
    amount of compressing the new rule could fit it; the surrounding phrasings
    are each pinned by an earlier measured decision. NOTE: where saturation
    actually begins has never been measured — the 1,800-2,000 figure above is
    the only observation, and every raise since has been an inference from it.
    Raised 1500 -> 1560 (W-00000249): the steering rule — pick the next
    question's direction, and argue the opposite side once — is what the Novel
    design canvas draws for every canvas, and the counter-stance half moved out
    of foundation into it, so foundation barely moved while services grew by the
    whole block. The user chose the raise over compressing the services framing,
    whose phrasings are each pinned by an earlier measured decision. It stays far
    below the 1,800-2,000 words where instruction slips were actually observed.
    The budget still forces compress-before-add:
    content is pinned by the phrase guards in this file and
    ``test_chat_system_prompt.py``; this test pins the SIZE."""
    for scope in ("foundation", "actors", "services", "entities", "feature:x", "service:x"):
        words = len(build_system_prompt(scope).split())
        assert words <= 1560, f"{scope}: {words} words > 1560 budget"


def test_every_canvas_steers_the_next_question_direction() -> None:
    """W-00000249: the coach asked one thing at a time but nothing told it WHICH
    WAY to turn next, so a stalled thread got the same question again. The
    Novel design canvas draws this as a decision the coach makes every turn —
    ask deeper, ask wider, or come at it from the opposite side. It rides in
    the shared playbook, so every canvas steers, not only foundation."""
    for scope in ("foundation", "actors", "services", "entities", "feature:x"):
        p = build_system_prompt(scope).lower()
        assert "deeper" in p, scope
        assert "wider" in p, scope
        assert "opposite" in p, scope
        assert "switch" in p, scope


def test_counter_stance_reaches_every_canvas() -> None:
    """W-00000249: arguing the opposite side once before confirming used to run
    on foundation only. The canvas puts it on every canvas — a service split or
    an entity is worth one challenge too — so it moves into the shared
    playbook and foundation stops carrying its own copy."""
    for scope in ("foundation", "actors", "services", "entities", "feature:x"):
        p = build_system_prompt(scope).lower()
        assert "opposite side once" in p, scope
