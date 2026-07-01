"""core_value kind format = definition + body (D-2026-06-06-B/C).

The do / dont fields are removed (do = a restatement of definition; dont
was unused). core_value keeps ``definition`` + ``body``. Loading old data
folds any non-empty do/dont into ``body`` so no content is lost.
"""

from __future__ import annotations

from mashbill.models import (
    FOUNDATION_MD_FIELDS,
    FOUNDATION_TYPED_TEXT_FIELDS,
    CoreValueNode,
)


def test_core_value_typed_field_maps() -> None:
    assert FOUNDATION_TYPED_TEXT_FIELDS["core_value"] == ["definition"]
    assert FOUNDATION_MD_FIELDS["core_value"] == ["definition", "body"]


def test_core_value_node_has_no_do_dont() -> None:
    n = CoreValueNode(id="cv-1", label="Tolerance", definition="accept difference", body="x")
    dumped = n.model_dump()
    assert "do" not in dumped and "dont" not in dumped


def test_old_core_value_folds_do_dont_into_body() -> None:
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
    assert n.definition == "We accept difference."
    assert "원래 본문" in n.body
    assert "판단 기준" in n.body
    assert "Judge first." in n.body
    d = n.model_dump()
    assert "do" not in d and "dont" not in d


def test_empty_do_dont_do_not_pollute() -> None:
    old = {
        "id": "cv-1",
        "kind": "core_value",
        "label": "Tolerance",
        "definition": "We accept difference.",
        "do": "",
        "dont": "",
        "body": "just the body",
    }
    n = CoreValueNode.model_validate(old)
    assert n.body == "just the body"
