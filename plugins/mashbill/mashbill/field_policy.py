"""Which node fields a caller may set, and when — the write-policy SSOT.

Two rules live here because they are the same decision seen from both ends.

**Patching an existing node** — ``writable_node_fields`` is the allow-list
``update_node`` filters against: ``label`` plus the kind's free-text prose.
Structural, reference, and lifecycle fields stay out, so a coach cannot repoint
a service's actors or unlock an identity's lifecycle with prose
(D-2026-06-26-D).

**Creating a node** — one kind cannot be built at all under that rule.
``actor_ref`` is a pure anchor ("who starts / who can" on a Feature flow) whose
entire content is ``ref_actor_id``, and the model refuses a node without it — so
every create raised a tagged-union dump while ``create_node`` advertised the
kind as creatable, and Novel's flows carried no actor at all (novel-workspace
O-25). ``CREATE_TIME_REFS`` names that field so it can ride into the seed.

Picking the target while creating the node is not the hole the patch rule
closed: the field is still absent from ``writable_node_fields``, so a later
change is still refused. Repointing means deleting the anchor and picking again.
"""

from __future__ import annotations

from collections.abc import Iterable

from mashbill.models import CanvasKind
from mashbill.models_union import SketchNode

# Per-kind *content* fields a coach may write via ``update_node`` — the kind's
# free-text prose only. This is an **allow-list, not a deny-list** (the first cut
# was `model_fields - base_fields`, which silently let every per-kind
# structural / reference / lifecycle field through as "writable" — a coach could
# repoint a service's actor references, lock an identity's derive→confirm
# lifecycle, or rewrite a rule's permission map; D-2026-06-26-D red-team). An
# allow-list is **fail-safe**: a field absent here is NOT writable, so a new kind
# (or a new structural field on an existing kind) defaults to protected until
# someone classifies it. Deliberately ABSENT and therefore protected: ``ref_*``
# id arrays + ``actor_ref.ref_actor_id`` (cross-node references — set via the
# pick-or-create flow, not free text), ``status`` / ``provenance`` (identity
# derive→confirm lifecycle), ``polarity`` / ``order`` (step structure), ``side``
# (actor classification), ``actor_permissions`` (rule permission map). ``label``
# (the node's name) is always writable, added separately. Mirrors the existing
# per-kind content maps (``FOUNDATION_TYPED_TEXT_FIELDS``). Every union kind must
# have an entry — pinned by ``tests/test_update_node.py`` so a new kind forces
# the content-vs-structural decision instead of silently leaking.
_WRITABLE_CONTENT_FIELDS: dict[str, tuple[str, ...]] = {
    "project": (),
    "mission": ("statement", "body"),
    "core_value": ("body",),  # v0.45 (D-2026-07-02-A): definition removed → name + body
    # B-32 completion (2026-07-04): summary exposed — the prompt demanded it
    # while this list silently rejected every coach write. body left with
    # B-15 (description is THE prose field; legacy body folds on read).
    "identity": ("summary", "description"),
    "actor": ("body",),
    "actor_ref": (),
    "service": ("problem", "value_created"),
    "feature": ("proposed",),
    "category": ("theme", "body"),
    "step": ("outcome", "body"),
    "decision": ("body",),
    "note": ("body",),
    "rule": ("policy", "enforcement", "body"),
    "entity": ("summary",),
}

# Always writable on every kind: the node's name / title.
_WRITABLE_LABEL = "label"


def writable_node_fields(node: SketchNode) -> list[str]:
    """The content fields a coach may patch on ``node``: ``label`` + the kind's
    free-text prose (the per-kind allow-list :data:`_WRITABLE_CONTENT_FIELDS`).

    The SSOT for "what is writable" — used both by :func:`update_node` (to filter
    a patch) and by the chat context builder (to tell the agent which fields an
    empty selected node accepts, so it can fill a blank node). Structural /
    reference / lifecycle fields are **not** writable (set through their own
    flows, never a free-text content patch — Rule 7); the allow-list is fail-safe
    for future kinds. Deterministic order: ``label`` first, then the kind's
    content fields that actually exist on the model.
    """
    content = _WRITABLE_CONTENT_FIELDS.get(node.kind, ())
    model_fields = type(node).model_fields
    return [_WRITABLE_LABEL, *(f for f in content if f in model_fields)]


# kind -> (the field that must be picked, the canvas its target lives on).
CREATE_TIME_REFS: dict[str, tuple[str, CanvasKind]] = {
    "actor_ref": ("ref_actor_id", "actors"),
}


def validated_pick(
    kind: str,
    field: str,
    home_canvas: str,
    value: object,
    home_ids: Iterable[str],
) -> str:
    """The picked master id, or ``ValueError`` naming what is wrong (pure).

    Fail Fast on both halves the caller can get wrong: no pick at all, and a
    pick that names nothing. A dangling anchor renders as an unresolvable
    reference in the viewer, so it is refused rather than written.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"creating a {kind!r} node requires {field!r}: the id of the "
            f"{home_canvas} node it points at"
        )
    if value not in set(home_ids):
        raise ValueError(
            f"{field}={value!r} is not on the {home_canvas!r} canvas — "
            f"pick an existing one (or create it there first)"
        )
    return value
