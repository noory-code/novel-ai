"""Cross-entity integrity checks run after every file has been read.

Per-file :mod:`solera_mcp.readers` only sees one file at a time, so refs
like ``Persona.role`` or ``Narrative.in_journey`` can only be validated
once the full id sets are known. This pass appends integrity flags on the
entities whose references don't resolve so the Actors canvas can surface
a repair prompt.
"""

from __future__ import annotations

from solera_mcp.models import Journey, Narrative, Persona, Role


def annotate_cross_ref_integrity(
    roles: list[Role],
    personas: list[Persona],
    journeys: list[Journey],
    narratives: list[Narrative],
) -> None:
    """Annotate each model's ``integrity`` list with cross-ref breaks.

    - ``Role.broken_parent_ref`` / ``inactive_parent_ref`` — ``parent``
      doesn't resolve to a Role (or resolves to a non-active one).
    - ``Persona.broken_role_ref`` / ``inactive_role_ref`` — ``role`` doesn't
      resolve to a Role.
    - ``Journey.broken_walks_ref`` / ``inactive_walks_ref`` — ``walks``
      doesn't resolve to a Role.
    - ``Narrative.broken_about_role_ref`` / ``broken_about_persona_ref`` —
      any id in ``about_roles`` / ``about_personas`` that doesn't resolve.
    - ``Narrative.broken_in_journey_ref`` — existing v4 behaviour.
    """
    roles_by_id = {r.id: r for r in roles}
    personas_by_id = {p.id: p for p in personas}
    journey_ids = {j.id for j in journeys}

    for r in roles:
        if r.parent:
            target = roles_by_id.get(r.parent)
            if target is None:
                _add(r.integrity, "broken_parent_ref")
            elif target.status != "active":
                _add(r.integrity, "inactive_parent_ref")

    for p in personas:
        if not p.role:
            continue  # missing_role was flagged at read-time
        target = roles_by_id.get(p.role)
        if target is None:
            _add(p.integrity, "broken_role_ref")
        elif target.status != "active":
            _add(p.integrity, "inactive_role_ref")

    for j in journeys:
        if not j.walks:
            continue  # missing_walks was flagged at read-time
        target = roles_by_id.get(j.walks)
        if target is None:
            _add(j.integrity, "broken_walks_ref")
        elif target.status != "active":
            _add(j.integrity, "inactive_walks_ref")

    for n in narratives:
        for role_id in n.about_roles:
            if role_id not in roles_by_id:
                _add(n.integrity, "broken_about_role_ref")
                break
        for persona_id in n.about_personas:
            if persona_id not in personas_by_id:
                _add(n.integrity, "broken_about_persona_ref")
                break
        if n.in_journey and n.in_journey not in journey_ids:
            _add(n.integrity, "broken_in_journey_ref")


def _add(flags: list[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)
