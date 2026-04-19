"""Cross-entity integrity checks run after every file has been read.

Per-file :mod:`solera_mcp.readers` only sees one file at a time, so refs
like ``Narrative.in_journey`` can only be validated once the full set of
Journeys is known. This pass appends integrity flags on the entities whose
references don't resolve.
"""

from __future__ import annotations

from solera_mcp.models import Journey, Narrative


def annotate_cross_ref_integrity(
    journeys: list[Journey], narratives: list[Narrative]
) -> None:
    """Append ``broken_in_journey_ref`` to any Narrative pointing at a
    non-existent Journey. Refs that resolve are left alone; the Narrative's
    ``integrity`` list is mutated in place.
    """
    journey_ids = {j.id for j in journeys}
    for n in narratives:
        if n.in_journey and n.in_journey not in journey_ids:
            if "broken_in_journey_ref" not in n.integrity:
                n.integrity.append("broken_in_journey_ref")
