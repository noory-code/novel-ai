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
    assert n.description == "Warm casual honorifics."
    assert "원래 본문" in n.body
    assert "Greet first." in n.body
    assert "Use ㅋㅋ emoji." in n.body
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
    assert n.body == "just the body"


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
