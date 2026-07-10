"""Service-detail canvases kept in sync with the services overview.

Split out of the folder_io god-module (D-2026-06-10-D). folder_io.py re-exports
everything, so import sites and tests are unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

from mashbill.canvas_io import list_feature_details, read_canvas, write_canvas  # noqa: F401
from mashbill.models import CanvasDoc
from mashbill.storage import (  # noqa: F401
    _canvas_file,
    _ensure_project,
    _project_dir,
    _project_file,
    _read_json,
    _write_json,
)

# ---------------------------------------------------------------------------
# Overview ↔ Detail sync
# ---------------------------------------------------------------------------


def sync_details_with_overview(plot_root: Path, project_id: str) -> dict[str, list[str]]:
    """Ensure ``services/{fid}/detail.json`` exists for every **feature** in the
    top-view ``services`` canvas.

    D-2026-06-17-D — the **feature** is the drill target (selecting a service
    shows its inspector; clicking a feature drills into its detail). So detail
    canvases seed per feature, not per service; a service with no features has
    nothing to drill into and gets no detail. The detail's wire ``canvas_kind``
    stays ``feature`` until the canvas-string rename (product-gated).

    Features that disappear from the top view have their whole folder moved
    to ``services/_archive/{fid}/`` — a destructive delete would throw away
    user work (``index.md``, attachments) on a stray click. Called
    opportunistically after writes to the services canvas.

    Returns ``{"created": [...], "archived": [...]}`` for telemetry.
    """
    _ensure_project(plot_root, project_id)
    try:
        overview = read_canvas(plot_root, project_id, "services")
    except FileNotFoundError:
        return {"created": [], "archived": []}
    overview_feature_ids = {n.id for n in overview.nodes if n.kind == "feature"}
    services_folder = _project_dir(plot_root, project_id) / "services"
    services_folder.mkdir(exist_ok=True)
    # Existing detail folders: every immediate subdir that isn't ``_archive``
    # and has its own ``detail.json``.
    existing_details: set[str] = set()
    if services_folder.is_dir():
        for child in services_folder.iterdir():
            if child.is_dir() and child.name != "_archive" and (child / "detail.json").is_file():
                existing_details.add(child.name)

    # D-2026-07-04-P — blank-canvas start: a fresh detail carries ONLY its
    # root feature node. (Supersedes D-2026-07-04-M's single user-side chip,
    # which itself replaced two fake English stubs: with no seed actors there
    # is nothing truthful to point at — the subject chip lands through
    # coaching; D-2026-05-28-J's "every step needs a subject" is coached.)
    created: list[str] = []
    for feature_id in sorted(overview_feature_ids - existing_details):
        src = next(n for n in overview.nodes if n.id == feature_id)
        detail = CanvasDoc(
            canvas_id=feature_id,
            canvas_kind="feature",
            feature_ref=feature_id,
            nodes=[
                # v0.26.0 (D-2026-05-25-A) — parent_id field removed;
                # feature root carries no structural parent
                # (is_root marks the canvas anchor).
                src.model_copy(update={"is_root": False}),
            ],
        )
        _write_json(
            _canvas_file(plot_root, project_id, "feature", service_id=feature_id),
            detail.model_dump(by_alias=True),
        )
        created.append(feature_id)

    archive_folder = services_folder / "_archive"
    archived: list[str] = []
    skipped_archive: list[str] = []
    for feature_id in sorted(existing_details - overview_feature_ids):
        src_path = services_folder / feature_id
        # v0.27.14 (D-2026-05-28-I) — data-loss guard: if the disappearing
        # detail carries user-authored content (any node outside the
        # default seed set ``{feature_id, {fid}-operator-ref,
        # {fid}-user-ref}``, OR any edges), do NOT silently archive.
        # The user's 2026-05-27 chrome-devtools session lost a root
        # node + its detail to a sync archive triggered by an
        # injected onNodesChange burst; this branch protects the
        # next instance of that pattern. Empty / default-seeded details
        # archive cleanly as before (existing test_sync coverage).
        if _detail_has_user_authored_content(src_path, feature_id):
            skipped_archive.append(feature_id)
            continue
        archive_folder.mkdir(exist_ok=True)
        dst_path = archive_folder / feature_id
        # If the archive already has a folder with the same id (rare — same
        # feature created, archived, and recreated), rename with a suffix.
        if dst_path.exists():
            n = 2
            while (archive_folder / f"{feature_id}-{n}").exists():
                n += 1
            dst_path = archive_folder / f"{feature_id}-{n}"
        src_path.replace(dst_path)
        archived.append(feature_id)

    result: dict[str, list[str]] = {"created": created, "archived": archived}
    if skipped_archive:
        result["skipped_archive"] = skipped_archive
    else:
        result["skipped_archive"] = []
    return result


def _detail_has_user_authored_content(detail_dir: Path, feature_id: str) -> bool:
    """v0.27.14 (D-2026-05-28-I) — return True iff the feature's
    ``detail.json`` contains anything beyond the auto-created shape (the
    root feature node, no edges; legacy actor_ref seed ids from the
    pre-D-2026-07-04-P shapes still count as non-user content). Used by
    ``sync_details_with_overview`` to refuse to archive details the
    user has invested work in.
    """
    detail_path = detail_dir / "detail.json"
    if not detail_path.is_file():
        return False
    try:
        doc = json.loads(detail_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # Unreadable / malformed: treat as user content to be safe.
        return True
    seeded_ids = {
        feature_id,
        f"{feature_id}-operator-ref",
        f"{feature_id}-user-ref",
    }
    nodes = doc.get("nodes") or []
    edges = doc.get("edges") or []
    if edges:
        return True
    for node in nodes:
        if not isinstance(node, dict):
            return True
        if node.get("id") not in seeded_ids:
            return True
    return False
