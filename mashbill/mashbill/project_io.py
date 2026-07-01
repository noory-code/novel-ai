"""ProjectDoc read/write, seeds, create/rename/delete.

Split out of the folder_io god-module (D-2026-06-10-D). folder_io.py re-exports
everything, so import sites and tests are unchanged.
"""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime
from pathlib import Path

from mashbill.canvas_io import list_feature_details, read_canvas, write_canvas  # noqa: F401
from mashbill.models import (
    ActorNode,
    CanvasDoc,
    CoreValueNode,
    IdentityNode,
    MissionNode,
    ProjectDoc,
    SketchEdge,
)
from mashbill.models_foundation import PROJECT_ANCHOR_ID
from mashbill.storage import (  # noqa: F401
    _canvas_file,
    _ensure_project,
    _project_dir,
    _project_file,
    _read_json,
    _write_json,
    read_project,
    write_project,
)

# ---------------------------------------------------------------------------
# project-level IO
# ---------------------------------------------------------------------------



def rename_project(plot_root: Path, project_id: str, new_name: str) -> ProjectDoc:
    """Update ``ProjectDoc.name``. v0.13 Phase 0: there is no per-canvas
    project node any more — label is derived from ProjectDoc.name at render
    time. Touching the foundation canvas via read still triggers the
    legacy-anchor eviction migrator for old projects.
    """
    proj = read_project(plot_root, project_id)
    renamed = proj.model_copy(update={"name": new_name})
    write_project(plot_root, renamed)
    # v0.13 Phase 0: project anchors no longer carry the label as a node
    # field — label SSOT is ProjectDoc.name, derived at render. Touch the
    # foundation canvas via read so the legacy-anchor eviction migrator
    # runs if the project predates v0.13.
    try:
        read_canvas(plot_root, project_id, "foundation")
    except FileNotFoundError:
        pass
    return read_project(plot_root, project_id)


# ---------------------------------------------------------------------------
# create / delete
# ---------------------------------------------------------------------------


def _seed_foundation_canvas(project_name: str) -> CanvasDoc:  # noqa: ARG001
    """Minimum valid Foundation canvas — Mission / Core Value / Identity.

    v0.13 Phase 0: the Project anchor is no longer a node here. It lives in
    ``ProjectDoc.anchors["foundation"]`` and is rendered by the viewer at
    display time. ``project_name`` argument retained for signature stability
    but unused.
    """
    # D-2026-06-21-H — initial layout around the centre anchor (0,0): Mission on
    # top, Core Value on the left, Identity on the right, with an edge from the
    # project anchor out to each. (Revisits the v0.13.2 auto-edge rollback — now
    # explicitly user-requested, no longer YAGNI.)
    return CanvasDoc(
        canvas_id="foundation",
        canvas_kind="foundation",
        nodes=[
            MissionNode(
                id="mission",
                label="Mission",
                x=-100,
                y=-220,
                width=200,
                height=90,
                color="#fef3c7",
                shape="rounded",
            ),
            CoreValueNode(
                id="core-value-1",
                label="Core value",
                x=-340,
                y=-40,
                width=180,
                height=80,
                color="#fde68a",
                shape="rounded",
            ),
            IdentityNode(
                id="identity",
                label="Voice",
                x=140,
                y=-45,
                width=200,
                height=90,
                color="#fed7aa",
                shape="rounded",
            ),
        ],
        edges=[
            SketchEdge(
                id=f"anchor-{target}",
                source=PROJECT_ANCHOR_ID,
                target=target,
                directed=True,
                relation="flow",
            )
            for target in ("mission", "core-value-1", "identity")
        ],
    )


def _seed_actors_canvas(project_name: str) -> CanvasDoc:  # noqa: ARG001
    """v0.11 — actors canvas seeds with two placeholder classes ("Operator"
    and "User") to satisfy the IDENTITY.md "≥ 2 actor classes" minimum.

    v0.13 Phase 0: project anchor moved to ``ProjectDoc.anchors``; not seeded
    here.
    """
    return CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[
            ActorNode(
                id="operator",
                label="Operator",
                side="operator",
                x=-260,
                y=-50,
                width=140,
                height=80,
                color="#bae6fd",
                shape="rounded",
            ),
            ActorNode(
                id="user",
                label="User",
                side="user",
                x=140,
                y=-50,
                width=140,
                height=80,
                color="#fecaca",
                shape="rounded",
            ),
        ],
    )


def _seed_services_canvas(project_name: str) -> CanvasDoc:  # noqa: ARG001
    """v0.13 Phase 0: services canvas starts empty (project anchor moved to
    ``ProjectDoc.anchors``). Categories + services are added by the user.
    """
    return CanvasDoc(
        canvas_id="services",
        canvas_kind="services",
        nodes=[],
    )


def _seed_entities_canvas(project_name: str) -> CanvasDoc:  # noqa: ARG001
    """D-2026-06-17-I: entities canvas starts EMPTY (project anchor lives in
    ``ProjectDoc.anchors``). Entities are populated last — an AI-maintained,
    derived surface — never hand-authored at create time (settled: symmetric
    to services seeding).
    """
    return CanvasDoc(
        canvas_id="entities",
        canvas_kind="entities",
        nodes=[],
    )


def create_project(plot_root: Path, project_id: str, name: str) -> ProjectDoc:
    """Create a fresh project folder, seeded with Foundation / Actors /
    Services / Entities.

    v0.8 layout: one folder per project (``.plot/{project_id}/``) with a
    subfolder per canvas kind. Each canvas folder holds a ``canvas.json``.
    Service-detail canvases join the relevant service folder later via
    ``sync_details_with_overview``.

    Raises ``FileExistsError`` if ``project_id`` is taken, or — per
    one-project-per-dir (D-2026-06-21-AA, narrowing D-2026-06-12-A) — if
    ``plot_root`` already holds *any* project. A second service goes in a
    sibling directory with its own ``.noory/plot``. The HTTP create endpoint
    maps both cases to 409; this is the single chokepoint covering viewer + MCP.
    """
    from mashbill.workspace import enumerate_projects

    existing = enumerate_projects(plot_root)
    if existing:
        raise FileExistsError(
            "one project per .noory/plot dir (one-project-per-dir, "
            f"D-2026-06-21-AA): {plot_root} already holds {existing[0].id!r}. "
            "Create the new project in a sibling directory."
        )
    # S2 (D-2026-06-21-AB): flat layout — project files land directly under
    # ``plot_root`` (``_project_dir`` returns it when no nested project.json
    # exists). The one-per-dir guard above subsumes the old nested dup-id check.
    folder = _project_dir(plot_root, project_id)
    folder.mkdir(parents=True, exist_ok=True)
    # D-2026-06-11-D: Novel never silently runs ``git init``. The first
    # tag/publish on a workspace without a repo replies needs_git_init=true;
    # the user accepts via POST /api/workspace/git-init. Project creation
    # leaves git untouched.

    now = datetime.now(UTC).isoformat()
    proj = ProjectDoc(
        id=project_id,
        name=name or project_id,
        created=date.today().isoformat(),
        updated=now,
        version=3,
    )
    _write_json(_project_file(plot_root, project_id), proj.model_dump())

    _write_json(
        _canvas_file(plot_root, project_id, "foundation"),
        _seed_foundation_canvas(proj.name).model_dump(by_alias=True),
    )
    _write_json(
        _canvas_file(plot_root, project_id, "actors"),
        _seed_actors_canvas(proj.name).model_dump(by_alias=True),
    )
    _write_json(
        _canvas_file(plot_root, project_id, "services"),
        _seed_services_canvas(proj.name).model_dump(by_alias=True),
    )
    _write_json(
        _canvas_file(plot_root, project_id, "entities"),
        _seed_entities_canvas(proj.name).model_dump(by_alias=True),
    )
    # v0.13 Phase 2 — write per-kind JSON Schema + MD template files into
    # ``.plot/{proj}/schema/`` so external tools (Obsidian YAML LSP, custom
    # validators) can verify Foundation node files.
    from mashbill.schema_export import export_all_schemas

    export_all_schemas(plot_root, project_id)
    return proj


def delete_project(plot_root: Path, project_id: str) -> None:
    folder = _ensure_project(plot_root, project_id)
    if folder == plot_root:
        # S2 flat layout: the project IS the root's contents. Wipe them but
        # keep the ``.noory/plot`` dir itself, so the dir picker shows it as an
        # empty "create here" slot rather than a vanished workspace.
        for child in plot_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        shutil.rmtree(folder)


