"""Render one [Project] line for every coach turn (novel-workspace W-00000490).

Newcomer walk 4: the work tab's coach did not know the project id, so its tool
calls failed, and it answered "if you have not published the blueprint yet…"
after both the blueprint and a service had been published. Every scope now gets
the project id, the newest blueprint version and each service's newest release.
Unreadable publish records fall back to "not published yet" rather than breaking
the turn.
"""

from __future__ import annotations

from pathlib import Path

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


def render_project_status(plot_root: Path) -> str:
    """``[Project] id …; blueprint: …; services published: …`` or ``""`` without a project."""
    projects = enumerate_projects(plot_root)
    if not projects:
        return ""
    project_id = projects[0].id
    try:
        project_dir = _project_dir(plot_root, project_id)
        blueprint = latest_blueprint_version(project_dir)
        services = [
            f"{service} {manifest.get('release', '')}".strip()
            for service, _folder, manifest in latest_service_releases(project_dir)
        ]
    except (OSError, ValueError):
        blueprint, services = None, []
    return (
        f"[Project] id {project_id}; blueprint: {blueprint or 'not published yet'}; "
        f"services published: {', '.join(services) if services else 'none yet'}."
    )
