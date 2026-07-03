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
    """The cross-canvas project scope gets the anti-hallucination guard alone —
    no tone, no write/propose playbook, no framing (parity with COACH_TONE)."""
    assert PROPOSE_PLAYBOOK not in build_system_prompt("project")


def test_coach_keeps_mechanics_and_field_names_out_of_sight() -> None:
    """B-6 (regression, user report + transcript 2026-07-02): the coach must not
    verbalise its internal operations — it said '저장됐어요' and exposed internal
    field names ('statement' / 'body') to the user. The system prompt must instruct
    it to never announce the save and to speak in the user's own words, not Novel's
    storage-field names."""
    p = build_system_prompt("foundation").lower()
    assert "internal field names" in p
    assert "do not announce" in p


def test_coach_leads_and_covers_full_concept() -> None:
    """B-7 (regression, user report + transcript 2026-07-02): the coach declared a
    canvas 'done' with only one identity facet and handed the wheel back ('what
    next?'), forcing the user to point out what was missing. The prompt must
    instruct it to keep leading and draw out a concept's full set of facets before
    moving on."""
    p = build_system_prompt("foundation").lower()
    assert "several facets" in p
    assert "before moving on" in p


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
    assert "don't wait for every slot" in f or "do not wait for every slot" in f


def test_services_framing_surfaces_entities_as_byproduct() -> None:
    """Benchmark finding (2026-07-02, 8-service batch): entities were 0/8 — the
    surface-the-entity instruction lived only in the entities-scope framing,
    which no design conversation ever runs under. The services framing (where
    features are born) must tell the coach to spot the data 'things' features
    handle and register confirmed ones on the entities canvas."""
    f = build_framing_preamble("services").lower()
    assert "entity" in f
    assert "entities canvas" in f


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
    assert "map the service landscape first" in f
    assert "then detail" in f


def test_services_framing_derives_the_entity_map_unprompted() -> None:
    """User directives (2026-07-02): "엔티티는 상상해서라도 만들어보세요" +
    "찾을 수 없으니 자율적 판단이 필요" — entities are the AI-maintained canvas
    (D-2026-06-17-I): the coach derives the map from the features and registers
    it AUTONOMOUSLY (no per-entity confirmation question), mentioning it in one
    light line; the user reviews/edits/deletes on the canvas."""
    f = build_framing_preamble("services").lower()
    assert "derive the entity map" in f
    assert "before leaving" in f
    assert "register them yourself" in f
    assert "등록해둘까요" not in f  # the ask-first gate is gone for entities


def test_foundation_framing_draws_values_out_until_dry() -> None:
    """Benchmark round 2 (2026-07-02): J-values was the weakest axis in every
    run — the coach lands 2–3 core values and moves on, while founders hold
    more (ground truths run 4–8). Each recurring fork is a candidate value:
    after one lands, hunt the NEXT fork and keep drawing until the user runs
    dry — never settle for the first two or three (ninth sim iteration)."""
    f = build_framing_preamble("foundation").lower()
    assert "next fork" in f
    assert "runs dry" in f
    assert "first two or three" in f


def test_services_framing_landscape_spans_exchanges_not_layers() -> None:
    """Benchmark round 2 (2026-07-02, Uber run): asked for the landscape, the
    coach mapped four internal layers of ONE marketplace (matching, safety,
    settlement) and called it the map — surfacing a single value exchange.
    A service is a value-exchange surface; the landscape spans the DIFFERENT
    exchanges the mission reaches, and layers of one exchange are not
    services (tenth sim iteration)."""
    f = build_framing_preamble("services").lower()
    assert "value-exchange surface" in f
    assert "internal layers" in f
    assert "other exchanges" in f


def test_propose_playbook_switches_to_drafts_on_thin_replies() -> None:
    """Persona round (2026-07-02, Discord × terse founder): with a
    short-answer user the coach kept widening with open questions and landed
    ONE core value (J 1/7), an unfinished identity, and half-empty reference
    slots — the worst elicitation of any run. Thin replies mean the user
    can't or won't elaborate: the coach must narrow to draft-first mode —
    one concrete candidate at a time, answerable in a word (eleventh sim
    iteration)."""
    p = build_system_prompt("foundation").lower()
    assert "thin" in p
    assert "draft-first" in p
    assert "in a word" in p


def test_propose_playbook_distills_flooding_replies() -> None:
    """Persona round (2026-07-02, YouTube × rambler founder): six actors
    registered, ZERO with body text — the coach chased the tangents and never
    landed the content. Reply weight has two poles: thin means narrow to
    drafts; FLOODING means distill — extract the usable pieces, land each in
    its node while fresh, then steer back to the thread (twelfth sim
    iteration)."""
    p = build_system_prompt("actors").lower()
    assert "flood" in p
    assert "distill" in p
    assert "back to the thread" in p


def test_foundation_framing_proposes_candidate_values_from_the_talk() -> None:
    """Round 3: values depth is founder-dependent — guarded founders volunteer
    nothing and probing stalls at 1-3 values, while the terse run proved
    drafts work (1→5 registered). The coach now also PROPOSES candidate
    values it hears in the mission talk, alternating with probing
    (fourteenth sim iteration)."""
    f = build_framing_preamble("foundation").lower()
    assert "candidate values you hear" in f
    assert "alternate" in f


def test_services_framing_registers_entities_with_each_feature_batch() -> None:
    """Round 3: entity registration was all-or-nothing (0 in 9 of 12 runs vs
    9/9/23) — the 'before leaving the canvas' checkpoint fires too late or
    never. Entities now land in the same breath as each service's feature
    batch; a service with features but zero entities is unfinished
    (fifteenth sim iteration)."""
    f = build_framing_preamble("services").lower()
    assert "same breath" in f
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
    assert "identity lands mid-phase" in f
    assert "failed session" in f
    assert "once the first values stand" in f
    assert "then return" in f
    assert "identity still empty is a failed" in f


def test_foundation_framing_resumes_value_hunt_after_identity() -> None:
    """Iteration 17 (2026-07-03): values stalled at 1-3 registered in all 11
    runs of the day, across personas AND founder model families — the
    mid-phase identity checkpoint ("once two or three values stand") reads
    as a stopping point, and the 'then return to hunting' never fires. The
    framing must name the checkpoint as a pit stop: registering the identity
    does NOT end the value hunt."""
    f = build_framing_preamble("foundation").lower()
    assert "pit stop" in f
    assert "does not end the value hunt" in f


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
    """Iteration 18 (2026-07-03): the pit-stop rule (iteration 17) did not
    unlock the values stall — registration stayed at 2-3 per run because the
    coach lands values ONE per turn and the 8-turn foundation budget caps
    that at 2-3. The framing must tell the coach to land the values the talk
    has already surfaced as a BATCH: several candidates on the table in one
    turn, one yes registers every confirmed one — no one-per-turn drip."""
    f = build_framing_preamble("foundation").lower()
    assert "batch" in f
    assert "drip" in f


def test_foundation_framing_sweeps_value_domains_without_numeric_anchor() -> None:
    """Nineteenth iteration (2026-07-03, user: 셋 다): values coverage sat
    flat at ~2/7 across five measurements while registration hit the "two or
    three" numbers the prompt itself names — the anchors became quotas, and
    the registered values all orbit the mission (customer/quality kin) while
    corpus values span operating principles the coach never fishes for. The
    framing must sweep the value TERRAIN (distinct domains, probing one the
    talk hasn't touched) and must not anchor the count: no "two or three"
    except the anti-anchor warning ("never settle for the first two or
    three")."""
    f = build_framing_preamble("foundation").lower()
    assert "sweep the value terrain" in f
    assert "hasn't touched" in f
    assert f.count("two or three") == 1  # only the anti-anchor survives


def test_system_prompt_stays_under_saturation_budget() -> None:
    """Sixteenth sim iteration (2026-07-03): the coach prompt grew with every
    rotation — the composed canvas prompt hit ~1,800–2,000 words and the
    v0.138 sample showed instruction slips (a connect habit missed, a
    'saved' announcement) that read as prompt saturation, not missing rules.
    This budget forces every future rotation to compress before it adds:
    content is pinned by the phrase guards in this file and
    ``test_chat_system_prompt.py``; this test pins the SIZE."""
    for scope in ("foundation", "actors", "services", "entities", "feature:x", "service:x"):
        words = len(build_system_prompt(scope).split())
        assert words <= 1300, f"{scope}: {words} words > 1300 budget"
