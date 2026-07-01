"""Entity node class (D-2026-06-17-I).

The ``entity`` kind is the product data object the services act on (글 /
댓글 / 사용자) — symmetric to ``actor`` (Actors = *who* acts, Entities =
*what* is acted on). It lives on the project-level **Entities** canvas, an
AI-maintained conceptual map (NOT a physical ERD).

**Altitude guard (D-2026-06-17-I):** Novel holds only ``label`` (= the entity
name) + a one-line ``summary`` ("무엇을 담나?"). NO normalisation / FK /
cardinality / field types — those are the external AI agent's job, below
Novel's altitude. Relationships between entities are **edges** (B1 /
D-2026-06-17-J), not fields on the node.
"""

from __future__ import annotations

from typing import Literal

from mashbill.models_kinds import BaseNodeFields


class EntityNode(BaseNodeFields):
    """``entity`` kind — a product data object on the Entities canvas.

    ``label`` (from ``BaseNodeFields``) is the entity name. ``summary`` is the
    one-line "무엇을 담나?" — what the entity holds, in a sentence (rough,
    pre-normalisation; no types / FK)."""

    kind: Literal["entity"] = "entity"
    summary: str = ""
