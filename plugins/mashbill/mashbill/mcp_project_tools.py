"""Draft-aware project writes without implicit draft creation."""

from __future__ import annotations

from pathlib import Path

from mashbill.draft_store import read_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.mcp_draft_tools import (
    draft_matches_write,
    draft_mismatch_warning,
)
from mashbill.mcp_write_rollback import with_draft_or_rollback
from mashbill.models_canvas import ProjectDoc
from mashbill.project_io import rename_project
from mashbill.storage import read_project


def rename_project_with_draft(
    plot_root: Path,
    project_id: str,
    name: str,
    draft_id: str | None = None,
) -> tuple[ProjectDoc, str | None]:
    """Rename a project and confirm only a matching supplied draft."""
    matches_draft = False
    if draft_id is not None:
        draft = read_draft(plot_root, project_id, draft_id)
        if draft.canvas_kind != "project":
            raise ValueError(f"draft {draft_id!r} is not a project draft")
        matches_draft = draft_matches_write(
            plot_root,
            project_id,
            draft_id,
            "project",
            [],
            written_texts=[name],
        )
    previous = read_project(plot_root, project_id)
    if previous.name == name:
        warning = (
            f"draft {draft_id} was not confirmed: this write changed no design content"
            if draft_id is not None
            else None
        )
        return previous, warning

    def confirm_supplied_draft(renamed: ProjectDoc) -> str | None:
        if matches_draft:
            assert draft_id is not None
            persist_resolution(
                plot_root,
                project_id,
                draft_id,
                "confirmed",
                [],
            )
            return None
        if draft_id is not None:
            return draft_mismatch_warning(draft_id)
        return None

    renamed, warning = with_draft_or_rollback(
        lambda: rename_project(plot_root, project_id, name),
        confirm_supplied_draft,
        lambda: rename_project(plot_root, project_id, previous.name),
    )
    return renamed, warning
