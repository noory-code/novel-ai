"""Re-pin (INT-f) — turn format F release diffs into work-item actions.

When a service is re-published, re-pin compares its owned elements, referenced
project elements, and refs. It maps those changes onto work items that
``realizes`` affected stable IDs:

- a slug that **changed** → the item that builds it is *stale* → propose reopen.
- a slug that was **removed** → the item is orphaned → *escalate* to a human
  (not an auto-reopen — the design intent is gone, a person decides).
- a newly added service slug already realized by an item indicates a possible
  delete/re-add across releases → *escalate* rather than silently re-pin.

:func:`propose_repin` is **read-only** (deterministic proposal); a human
approves its ``proposal_id``, then :func:`apply_repin` recalculates and verifies
that ID before reopening anything. Keeping the two apart is the
human-in-the-loop gate (04-pipeline).
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from solera.intake import ImportedRelease, diff_releases
from solera.supervisor import reopen_items as reopen_work_items
from solera.workspace import Workspace, workspace_locked


def propose_repin(
    ws: Workspace,
    old: ImportedRelease,
    new: ImportedRelease,
) -> dict[str, Any]:
    """Propose which work items to reopen / escalate for a re-published release.

    Only adjacent releases of the same service are comparable. Pure read: the
    proposal contains service and shared diffs, refs changes, classifications,
    and per-item reasons, and mutates nothing.
    """
    old_service = old["service"]
    new_service = new["service"]
    if old_service["service"] != new_service["service"]:
        raise ValueError(
            "cannot re-pin different services: "
            f"{old_service['service']!r} and {new_service['service']!r}"
        )
    old_number = _service_release_number(old_service["release"])
    new_number = _service_release_number(new_service["release"])
    if new_number != old_number + 1:
        raise ValueError(
            f"service releases must be adjacent, got {old_service['release']} and "
            f"{new_service['release']}; import intervening releases and compare them "
            "one step at a time"
        )

    diff = diff_releases(old_service["elements"], new_service["elements"])
    if old_service["based_on"] == new_service["based_on"]:
        shared_diff = _empty_diff()
    else:
        shared_diff = diff_releases(old["project"]["elements"], new["project"]["elements"])

    refs_old = _ref_ids(old_service["refs"])
    refs_new = _ref_ids(new_service["refs"])
    refs_changed = refs_old != refs_new
    service_changed = set(diff["changed"])
    service_removed = set(diff["removed"])
    service_added = set(diff["added"])
    shared_changed = set(shared_diff["changed"]) & (refs_old | refs_new)
    shared_removed = set(shared_diff["removed"])
    referenced_removed = refs_old & shared_removed
    service_affected = bool(shared_changed or referenced_removed or refs_changed)
    service_element_ids = _element_ids(old_service["elements"]) | _element_ids(
        new_service["elements"]
    )

    stale: list[str] = []
    escalate: list[str] = []
    reasons: dict[str, list[str]] = {}
    for item_id in ws.list_items():
        realizes = set(ws.load_item(item_id).realizes)
        if not realizes:
            continue
        escalation_reasons = [
            *(
                f"realizes removed service element {element_id}"
                for element_id in sorted(realizes & service_removed)
            ),
            *(
                f"realizes removed shared element {element_id}"
                for element_id in sorted(realizes & shared_removed)
            ),
            *(
                f"already realizes added service element {element_id} (possible delete/re-add)"
                for element_id in sorted(realizes & service_added)
            ),
        ]
        if escalation_reasons:
            escalate.append(item_id)
            reasons[item_id] = escalation_reasons
            continue

        stale_reasons = [
            *(
                f"realizes changed service element {element_id}"
                for element_id in sorted(realizes & service_changed)
            ),
            *(
                f"realizes changed referenced shared element {element_id}"
                for element_id in sorted(realizes & shared_changed)
            ),
        ]
        realized_service = realizes & service_element_ids
        if service_affected and realized_service:
            affected_ids = ", ".join(sorted(realized_service))
            if shared_changed:
                stale_reasons.append(
                    f"service work {affected_ids} is affected by changed referenced shared "
                    f"elements: {', '.join(sorted(shared_changed))}"
                )
            if referenced_removed:
                stale_reasons.append(
                    f"service work {affected_ids} is affected by removed referenced shared "
                    f"elements: {', '.join(sorted(referenced_removed))}"
                )
            if refs_changed:
                stale_reasons.append(f"service work {affected_ids} is affected by changed refs")
        if stale_reasons:
            stale.append(item_id)
            reasons[item_id] = stale_reasons
    proposal: dict[str, Any] = {
        "stale": sorted(stale),
        "escalate": sorted(escalate),
        "diff": diff,
        "shared_diff": shared_diff,
        "refs_changed": refs_changed,
        "reasons": reasons,
    }
    proposal["proposal_id"] = _proposal_id(old, new, proposal)
    return proposal


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_json_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _proposal_id(
    old: ImportedRelease,
    new: ImportedRelease,
    proposal: dict[str, Any],
) -> str:
    reasons = proposal["reasons"]
    identity = {
        "manifests": {
            "old": {
                "service": _canonical_json_digest(old["service"]),
                "project": _canonical_json_digest(old["project"]),
            },
            "new": {
                "service": _canonical_json_digest(new["service"]),
                "project": _canonical_json_digest(new["project"]),
            },
        },
        "stale": sorted(proposal["stale"]),
        "escalate": sorted(proposal["escalate"]),
        "reasons": {item_id: sorted(reasons[item_id]) for item_id in sorted(reasons)},
    }
    return _canonical_json_digest(identity)


@workspace_locked
def apply_repin(
    ws: Workspace,
    old: ImportedRelease,
    new: ImportedRelease,
    proposal_id: str,
) -> dict[str, Any]:
    """Apply a still-current, human-approved re-pin proposal.

    The proposal is recalculated from the current manifests and work items. No
    files are written unless its identity matches the reviewed proposal.
    """
    proposal = propose_repin(ws, old, new)
    if proposal["proposal_id"] != proposal_id:
        raise ValueError("re-pin proposal changed; request a new proposal before applying")
    stale = list(proposal["stale"])
    reopen_items(ws, stale)
    return {**proposal, "reopened": stale}


def _service_release_number(release: Any) -> int:
    match = re.fullmatch(r"vS([1-9][0-9]*)", str(release))
    if match is None:
        raise ValueError(f"invalid service release: {release!r}")
    return int(match.group(1))


def _empty_diff() -> dict[str, list[str]]:
    return {"changed": [], "removed": [], "added": []}


def _ref_ids(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        ids: set[str] = set()
        for item in value:
            ids.update(_ref_ids(item))
        return ids
    if isinstance(value, dict):
        ids = set()
        for item in value.values():
            ids.update(_ref_ids(item))
        return ids
    return set()


def _element_ids(elements: list[dict[str, Any]]) -> set[str]:
    return {element["id"] for element in elements}


@workspace_locked
def reopen_items(ws: Workspace, item_ids: list[str]) -> None:
    """Reopen approved items and invalidate their completed ancestors."""
    reopen_work_items(ws, item_ids)
