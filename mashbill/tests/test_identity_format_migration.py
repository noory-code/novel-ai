"""identity kind format = description + body (D-2026-06-06-B).

The do / dont fields are removed (shared do/dont cut across the foundation
triad). identity keeps ``description`` + ``body``. Loading old data folds
any non-empty do/dont into ``body`` so no content is lost. (The output-value
model — provenance / evolution / status — is a separate future change.)
"""

from __future__ import annotations

import pytest

from mashbill.models import (
    FOUNDATION_MD_FIELDS,
    FOUNDATION_TYPED_TEXT_FIELDS,
    IdentityNode,
)


def test_identity_typed_field_maps() -> None:
    assert FOUNDATION_TYPED_TEXT_FIELDS["identity"] == ["description"]
    assert FOUNDATION_MD_FIELDS["identity"] == ["description", "body"]


def test_identity_node_has_no_do_dont() -> None:
    n = IdentityNode(id="id-1", label="Voice", description="warm", body="x")
    dumped = n.model_dump()
    assert "do" not in dumped and "dont" not in dumped


def test_old_identity_folds_do_dont_into_body() -> None:
    old = {
        "id": "id-1",
        "kind": "identity",
        "label": "Voice",
        "description": "Warm casual honorifics.",
        "do": "Greet first.",
        "dont": "Use ㅋㅋ emoji.",
        "body": "원래 본문",
    }
    n = IdentityNode.model_validate(old)
    # B-15 (D-2026-07-03-S): the folded body itself folds into description.
    assert n.description.startswith("Warm casual honorifics.")
    assert "원래 본문" in n.description
    assert "Greet first." in n.description
    assert "Use ㅋㅋ emoji." in n.description
    assert n.body == ""
    d = n.model_dump()
    assert "do" not in d and "dont" not in d


def test_empty_do_dont_do_not_pollute() -> None:
    n = IdentityNode.model_validate(
        {
            "id": "id-1",
            "kind": "identity",
            "label": "Voice",
            "description": "warm",
            "do": "",
            "dont": "",
            "body": "just the body",
        }
    )
    # B-15: body folds into description; empty do/dont add nothing.
    assert n.description == "warm\n\njust the body"
    assert n.body == ""


# ---------------------------------------------------------------------------
# Output model — status + provenance (v0.44.0, D-2026-06-07-A)
# ---------------------------------------------------------------------------


def test_identity_output_fields_default() -> None:
    """identity is an output kind; absent status/provenance default to the
    graceful-degradation values (hand-authored = manual, no lineage)."""
    n = IdentityNode(id="id-1", label="Voice", description="warm", body="x")
    assert n.status == "manual"
    assert n.provenance == []


def test_legacy_identity_without_output_fields_gets_defaults() -> None:
    """Pre-v0.44 nodes lack status/provenance keys entirely → defaults, no error."""
    n = IdentityNode.model_validate(
        {"id": "id-1", "kind": "identity", "label": "Voice", "description": "warm"}
    )
    assert n.status == "manual"
    assert n.provenance == []


def test_identity_explicit_output_fields_roundtrip() -> None:
    n = IdentityNode.model_validate(
        {
            "id": "id-1",
            "kind": "identity",
            "label": "Voice",
            "description": "warm",
            "status": "confirmed",
            "provenance": ["mission-1", "core_value-2"],
        }
    )
    assert n.status == "confirmed"
    assert n.provenance == ["mission-1", "core_value-2"]
    dumped = n.model_dump()
    assert dumped["status"] == "confirmed"
    assert dumped["provenance"] == ["mission-1", "core_value-2"]


def test_identity_status_rejects_unknown_value() -> None:
    with pytest.raises(Exception):
        IdentityNode.model_validate(
            {"id": "id-1", "kind": "identity", "label": "Voice", "status": "bogus"}
        )


def test_identity_output_fields_not_in_md_maps() -> None:
    """status/provenance are structural (canvas.json only), never MD-split."""
    assert "status" not in FOUNDATION_TYPED_TEXT_FIELDS["identity"]
    assert "status" not in FOUNDATION_MD_FIELDS["identity"]
    assert "provenance" not in FOUNDATION_TYPED_TEXT_FIELDS["identity"]
    assert "provenance" not in FOUNDATION_MD_FIELDS["identity"]


def test_identity_body_folds_into_description_on_read() -> None:
    """B-15 (user live-watch, 2026-07-03; D-2026-07-03-S): the identity
    inspector showed BOTH 설명(description) and 노트(body) — duplicative.
    Description is the surviving field; a non-empty legacy body folds into
    description on read (data-loss guard, same pattern as core_value's
    definition fold) and body empties."""
    from mashbill.models_foundation import IdentityNode

    n = IdentityNode.model_validate({
        "id": "i1", "label": "Voice", "x": 0, "y": 0,
        "description": "따뜻하고 단단한 말투", "body": "격식은 낮추고 존중은 유지",
    })
    assert "따뜻하고 단단한 말투" in n.description
    assert "격식은 낮추고 존중은 유지" in n.description
    assert n.body == ""


def test_identity_description_alone_is_untouched() -> None:
    from mashbill.models_foundation import IdentityNode

    n = IdentityNode.model_validate({
        "id": "i1", "label": "Voice", "x": 0, "y": 0, "description": "D",
    })
    assert n.description == "D" and n.body == ""
