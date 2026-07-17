"""Entity-node Proof pointer validation (D-2026-07-17-D)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mashbill.models import EntityNode


def test_entity_accepts_valid_proof_id() -> None:
    node = EntityNode(id="entity-post", label="Post", proof_id="PROOF-42")

    assert node.proof_id == "PROOF-42"


def test_entity_rejects_malformed_proof_id() -> None:
    with pytest.raises(ValidationError, match="proof_id"):
        EntityNode(id="entity-post", label="Post", proof_id="proof-42")


def test_entity_proof_id_defaults_to_none() -> None:
    node = EntityNode(id="entity-post", label="Post")

    assert node.proof_id is None
