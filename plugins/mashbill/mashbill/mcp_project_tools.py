"""Draft-aware implementations for MCP project write tools."""

from __future__ import annotations

import logging
from pathlib import Path

from mashbill.chat_scope_env import effective_chat_scope
from mashbill.draft_store import record_applied_draft as persist_applied_draft
from mashbill.mcp_draft_tools import AUTO_DRAFT_RATIONALE
from mashbill.models_canvas import ProjectDoc
from mashbill.project_io import rename_project
from mashbill.storage import read_project

_log = logging.getLogger(__name__)


def rename_project_with_draft(plot_root: Path, project_id: str, name: str) -> ProjectDoc:
    """Rename a project and best-effort record the successful MCP write."""
    previous = read_project(plot_root, project_id)
    renamed = rename_project(plot_root, project_id, name)
    if previous.name == renamed.name:
        return renamed
    try:
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
    except Exception:  # noqa: BLE001 — draft failure must not undo a successful rename
        _log.exception("automatic project rename draft failed for %s", project_id)
    return renamed
