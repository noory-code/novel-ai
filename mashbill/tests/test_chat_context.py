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
