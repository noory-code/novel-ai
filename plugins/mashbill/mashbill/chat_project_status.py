"""Render one [Project] line for every coach turn (novel-workspace W-00000490).

Newcomer walk 4: the work tab's coach did not know the project id, so its tool
calls failed, and it answered "if you have not published the blueprint yet…"
after both the blueprint and a service had been published. Every scope now gets
the project id, the newest blueprint version, and every service on the services
canvas with its newest release or "not published yet". Unreadable publish
records fall back to "not published yet" rather than breaking the turn.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.folder_io import read_canvas
from mashbill.format_f_slugs import read_slug_store
from mashbill.storage import _project_dir
from mashbill.work_proposals import _release_dirs, latest_service_releases
from mashbill.workspace import enumerate_projects


def latest_blueprint_version(project_dir: Path) -> str | None:
    """The human version (``v0.2.0``) of the newest project snapshot, or None."""
    newest: tuple[int, str] | None = None
    for number, folder, manifest in _release_dirs(project_dir / "published"):
        version = manifest.get("blueprint_version")
        if folder.parent.name != "_project" or not isinstance(version, str):
            continue
        if newest is None or number > newest[0]:
            newest = (number, version)
    return newest[1] if newest else None


def _service_lines(plot_root: Path, project_id: str, project_dir: Path) -> list[str]:
    """``label vS2`` per service on the canvas, ``label not published yet`` for one
    never published, then any published service no longer on the canvas by slug."""
    releases = {
        service: str(manifest.get("release", ""))
        for service, _folder, manifest in latest_service_releases(project_dir)
    }
    slugs = read_slug_store(plot_root, project_id)
    lines = []
    for node in read_canvas(plot_root, project_id, "services").nodes:
        if node.kind != "service":
            continue
        release = releases.pop(slugs.get(node.id, "").removeprefix("service/"), None)
        lines.append(f"{node.label} {release or 'not published yet'}")
    return lines + [f"{service} {release}".strip() for service, release in releases.items()]


def render_project_status(plot_root: Path) -> str:
    """``[Project] id …; blueprint: …; services: …`` or ``""`` without a project."""
    projects = enumerate_projects(plot_root)
    if not projects:
        return ""
    project_id = projects[0].id
    blueprint: str | None = None
    services: list[str] = []
    try:
        project_dir = _project_dir(plot_root, project_id)
        blueprint = latest_blueprint_version(project_dir)
        services = _service_lines(plot_root, project_id, project_dir)
    except (OSError, ValueError):
        pass
    return (
        f"[Project] id {project_id}; blueprint: {blueprint or 'not published yet'}; "
        f"services: {', '.join(services) if services else 'none yet'}."
    )
