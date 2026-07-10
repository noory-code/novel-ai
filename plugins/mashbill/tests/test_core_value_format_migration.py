"""core_value kind format = label + body (D-2026-07-02-A).

core_value is now the value's ``label`` (its name) + ``body`` (its meaning
+ tradeoff) alone. The former typed ``definition`` field is removed — it was
the value's meaning, which now leads ``body`` — and the earlier ``do`` /
``dont`` fields stay removed. Loading old data folds any non-empty
``definition`` / ``do`` / ``dont`` into ``body`` so no content is lost:
``definition`` leads, then the prior body, then do/dont as ``## Do`` /
``## Don't`` sections. Root canon: docs/concepts/kinds.md (name + body).
"""

from __future__ import annotations

from mashbill.models import (
    FOUNDATION_MD_FIELDS,
    FOUNDATION_TYPED_TEXT_FIELDS,
    CoreValueNode,
)


def test_core_value_typed_field_maps() -> None:
    # No typed-text field beyond the free body — the value's name is ``label``.
    assert FOUNDATION_TYPED_TEXT_FIELDS["core_value"] == []
    assert FOUNDATION_MD_FIELDS["core_value"] == ["body"]


def test_core_value_node_has_no_definition_do_dont() -> None:
    n = CoreValueNode(id="cv-1", label="Tolerance", body="accept difference")
    dumped = n.model_dump()
    assert "definition" not in dumped
    assert "do" not in dumped and "dont" not in dumped


def test_old_core_value_folds_definition_into_body_lead() -> None:
    old = {
        "id": "cv-1",
        "kind": "core_value",
        "label": "Tolerance",
        "definition": "We accept difference.",
        "body": "원래 본문",
    }
    n = CoreValueNode.model_validate(old)
    # definition leads the body (it is the value's meaning), original body follows.
    assert n.body == "We accept difference.\n\n원래 본문"
    d = n.model_dump()
    assert "definition" not in d


def test_old_core_value_folds_definition_and_do_dont_into_body() -> None:
    old = {
        "id": "cv-1",
        "kind": "core_value",
        "label": "Tolerance",
        "definition": "We accept difference.",
        "do": "판단 기준: 상대를 이해하려 했는가?",
        "dont": "Judge first.",
        "body": "원래 본문",
    }
    n = CoreValueNode.model_validate(old)
    assert "We accept difference." in n.body
    assert n.body.index("We accept difference.") == 0  # definition leads
    assert "원래 본문" in n.body
    assert "판단 기준" in n.body
    assert "Judge first." in n.body
    d = n.model_dump()
    assert "definition" not in d
    assert "do" not in d and "dont" not in d


def test_empty_legacy_fields_do_not_pollute() -> None:
    old = {
        "id": "cv-1",
        "kind": "core_value",
        "label": "Tolerance",
        "definition": "",
        "do": "",
        "dont": "",
        "body": "just the body",
    }
    n = CoreValueNode.model_validate(old)
    assert n.body == "just the body"
    d = n.model_dump()
    assert "definition" not in d
