"""Draft-aware implementations for MCP project write tools."""

from __future__ import annotations

from pathlib import Path

from mashbill.chat_scope_env import effective_chat_scope
from mashbill.draft_store import list_drafts, read_draft
from mashbill.draft_store import record_applied_draft as persist_applied_draft
from mashbill.draft_store import resolve_draft as persist_resolution
from mashbill.mcp_draft_tools import AUTO_DRAFT_RATIONALE, draft_matches_write
from mashbill.mcp_write_rollback import with_draft_or_rollback
from mashbill.models_canvas import ProjectDoc
from mashbill.project_io import rename_project
from mashbill.storage import read_project


def rename_project_with_draft(
    plot_root: Path,
    project_id: str,
    name: str,
    draft_id: str | None = None,
) -> ProjectDoc:
    """Rename a project and record the successful MCP write."""
    confirmed_draft_id = draft_id
    if draft_id is not None:
        draft = read_draft(plot_root, project_id, draft_id)
        if draft.canvas_kind != "project":
            raise ValueError(f"draft {draft_id!r} is not a project draft")
    else:
        confirmed_draft_id = next(
            (
                draft.id
                for draft in list_drafts(
                    plot_root,
                    project_id,
                    status="proposed",
                    canvas_kind="project",
                )
                if draft_matches_write(
                    plot_root,
                    project_id,
                    draft.id,
                    "project",
                    [],
                    written_texts=[name],
                )
            ),
            None,
        )
    previous = read_project(plot_root, project_id)
    if previous.name == name:
        return previous

    def record_draft(renamed: ProjectDoc) -> None:
        if confirmed_draft_id is not None:
            persist_resolution(
                plot_root,
                project_id,
                confirmed_draft_id,
                "confirmed",
                [],
            )
            return
        persist_applied_draft(
            plot_root,
            project_id,
            "project",
            f"프로젝트 이름: {previous.name} → {renamed.name}",
            AUTO_DRAFT_RATIONALE,
            effective_chat_scope(""),
            [],
            None,
            None,
            [],
        )

    renamed, _ = with_draft_or_rollback(
        lambda: rename_project(plot_root, project_id, name),
        record_draft,
        lambda: rename_project(plot_root, project_id, previous.name),
    )
    return renamed
