"""mission kind format = label + statement + body (D-2026-06-06-C).

The 3 typed fields what_we_do / why / direction are replaced by a single
``statement`` field (the mission, one sentence; display label "미션") + the
free ``body``. Loading old data migrates: what_we_do -> statement, why &
direction fold into body. No content lost.
"""

from __future__ import annotations

from mashbill.models import (
    FOUNDATION_MD_FIELDS,
    FOUNDATION_TYPED_TEXT_FIELDS,
    MissionNode,
)


def test_mission_typed_field_maps() -> None:
    assert FOUNDATION_TYPED_TEXT_FIELDS["mission"] == ["statement"]
    assert FOUNDATION_MD_FIELDS["mission"] == ["statement", "body"]


def test_mission_node_fields() -> None:
    n = MissionNode(id="m-1", label="Mission", statement="We exist to X.", body="story")
    dumped = n.model_dump()
    assert dumped["statement"] == "We exist to X."
    for gone in ("what_we_do", "why", "direction"):
        assert gone not in dumped


def test_old_mission_migrates_what_we_do_to_statement_and_folds_rest() -> None:
    old = {
        "id": "m-1",
        "kind": "mission",
        "label": "Mission",
        "what_we_do": "We build X.",
        "why": "Because Y.",
        "direction": "Toward Z.",
        "body": "## Story\nonce upon a time",
    }
    n = MissionNode.model_validate(old)
    # what_we_do becomes the statement
    assert n.statement == "We build X."
    # why + direction fold into body; original body preserved
    assert "Because Y." in n.body
    assert "Toward Z." in n.body
    assert "once upon a time" in n.body
    # legacy keys gone
    d = n.model_dump()
    assert "what_we_do" not in d and "why" not in d and "direction" not in d


def test_empty_legacy_fields_do_not_pollute() -> None:
    old = {
        "id": "m-1",
        "kind": "mission",
        "label": "Mission",
        "what_we_do": "",
        "why": "",
        "direction": "",
        "body": "just the body",
    }
    n = MissionNode.model_validate(old)
    assert n.statement == ""
    assert n.body == "just the body"
