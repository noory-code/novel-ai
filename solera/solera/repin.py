"""Re-pin (INT-f) — turn a format F ID-diff into work-item actions.

When a service is re-published, :func:`solera.intake.diff_releases` says which
slugs ``changed`` / ``removed`` / ``added``. Re-pin maps that onto the work
items that ``realizes`` those slugs:

- a slug that **changed** → the item that builds it is *stale* → propose reopen.
- a slug that was **removed** → the item is orphaned → *escalate* to a human
  (not an auto-reopen — the design intent is gone, a person decides).

:func:`propose_repin` is **read-only** (deterministic proposal); a human
approves, then :func:`reopen_items` performs the status mutation. Keeping the
two apart is the human-in-the-loop gate (04-pipeline).
"""

from __future__ import annotations

from typing import Any

from solera.intake import diff_releases
from solera.workspace import Workspace


def propose_repin(
    ws: Workspace,
    old_elements: list[dict[str, Any]],
    new_elements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Propose which work items to reopen / escalate for a re-published release.

    Pure read: returns ``{stale, escalate, diff}`` and mutates nothing.
    """
    diff = diff_releases(old_elements, new_elements)
    changed = set(diff["changed"])
    removed = set(diff["removed"])

    stale: list[str] = []
    escalate: list[str] = []
    for item_id in ws.list_items():
        realizes = ws.load_item(item_id).realizes
        if not realizes:
            continue
        if any(slug in removed for slug in realizes):
            escalate.append(item_id)
        elif any(slug in changed for slug in realizes):
            stale.append(item_id)
    return {"stale": sorted(stale), "escalate": sorted(escalate), "diff": diff}


def reopen_items(ws: Workspace, item_ids: list[str]) -> None:
    """Reopen the given items (status → ``todo``) after a human approves a
    proposal. Idempotent; only touches the listed items."""
    for item_id in item_ids:
        item = ws.load_item(item_id)
        if item.status != "todo":
            ws.write_item(item.model_copy(update={"status": "todo"}))
