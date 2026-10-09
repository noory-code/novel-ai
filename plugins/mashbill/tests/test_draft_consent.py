"""Drafts exist only when the person explicitly chooses to keep a proposal."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.broadcast import BroadcastHub
from mashbill.chat_session import ChatProvider, ChatStreamEvent
from mashbill.chat_store import append_user
from mashbill.draft_store import list_drafts, read_draft
from mashbill.endpoints_chat import stream_chat_turn
from mashbill.folder_io import create_node as create_canvas_node
from mashbill.folder_io import read_canvas
from mashbill.mcp_draft_tools import record_draft, resolve_draft, update_draft
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


def _project(tmp_path: Path) -> Path:
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    return plot_root


def _record(
    tmp_path: Path,
    proposed_text: str,
    *,
    canvas_kind: str = "foundation",
    target_node_ids: list[str] | None = None,
) -> str:
    result = record_draft(
        str(tmp_path),
        "alpha",
        canvas_kind,  # type: ignore[arg-type]
        proposed_text,
        "A proposal the person chose to keep.",
        canvas_kind,
        target_node_ids,
    )
    return str(result["draft_id"])


@pytest.mark.parametrize(
    "tool_name",
    [
        "update_node",
        "create_node",
        "create_edge",
        "set_node_references",
        "update_canvas",
        "rename_project",
    ],
)
def test_write_without_draft_id_creates_no_draft(tmp_path: Path, tool_name: str) -> None:
    plot_root = _project(tmp_path)
    actor = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Reader"})["node"]
    other = create_canvas_node(plot_root, "alpha", "actors", "actor", {"label": "Writer"})["node"]
    service = create_canvas_node(plot_root, "alpha", "services", "service", {"label": "Reading"})[
        "node"
    ]

    if tool_name == "update_node":
        mcp_tools.update_node(
            str(tmp_path), "alpha", "actors", str(actor["id"]), {"body": "Needs clarity."}
        )
    elif tool_name == "create_node":
        mcp_tools.create_node(str(tmp_path), "alpha", "actors", "actor", {"label": "Editor"})
    elif tool_name == "create_edge":
        mcp_tools.create_edge(str(tmp_path), "alpha", "actors", str(actor["id"]), str(other["id"]))
    elif tool_name == "set_node_references":
        mcp_tools.set_node_references(
            str(tmp_path),
            "alpha",
            "services",
            str(service["id"]),
            {"ref_actor_ids": [str(actor["id"])]},
        )
    elif tool_name == "update_canvas":
        canvas = read_canvas(plot_root, "alpha", "actors").model_dump(by_alias=True)
        canvas["nodes"][0]["body"] = "Needs a clear next step."
        mcp_tools.update_canvas(str(tmp_path), "alpha", canvas)
    else:
        mcp_tools.rename_project(str(tmp_path), "alpha", "Renamed Alpha")

    assert list_drafts(plot_root, "alpha") == []


def test_matching_mismatching_and_partial_writes_never_add_drafts(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    node = create_canvas_node(
        plot_root, "alpha", "foundation", "mission", {"label": "Old", "statement": "Old"}
    )["node"]
    node_id = str(node["id"])

    matching_id = _record(tmp_path, "Shared direction", target_node_ids=[node_id])
    matching = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": "Shared direction"},
        draft_id=matching_id,
    )
    assert "draft_warning" not in matching
    assert read_draft(plot_root, "alpha", matching_id).status == "confirmed"

    mismatch_id = _record(tmp_path, "A different direction", target_node_ids=[node_id])
    mismatch = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"statement": "Unrelated wording"},
        draft_id=mismatch_id,
    )
    assert "draft_warning" in mismatch
    assert "auto draft" not in mismatch["draft_warning"]
    assert read_draft(plot_root, "alpha", mismatch_id).status == "proposed"

    partial_id = _record(tmp_path, "Final label", target_node_ids=[node_id])
    partial = mcp_tools.update_node(
        str(tmp_path),
        "alpha",
        "foundation",
        node_id,
        {"label": "Final label", "statement": "Another unrelated change"},
        draft_id=partial_id,
    )
    assert "draft_warning" in partial
    assert "auto draft" not in partial["draft_warning"]
    assert read_draft(plot_root, "alpha", partial_id).status == "confirmed"
    assert {draft.id for draft in list_drafts(plot_root, "alpha")} == {
        matching_id,
        mismatch_id,
        partial_id,
    }


def test_update_draft_accumulates_oldest_first_revisions(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    draft_id = _record(tmp_path, "First wording")
    original = read_draft(plot_root, "alpha", draft_id)

    first = update_draft(str(tmp_path), "alpha", draft_id, "Second wording", "First refinement.")
    second = update_draft(str(tmp_path), "alpha", draft_id, "Final wording", "Second refinement.")

    assert first["proposed_text"] == "Second wording"
    assert second["proposed_text"] == "Final wording"
    assert second["rationale"] == "Second refinement."
    assert second["updated"] >= original.updated
    assert second["revisions"] == [
        {
            "proposed_text": "First wording",
            "rationale": original.rationale,
            "updated": original.updated,
        },
        {
            "proposed_text": "Second wording",
            "rationale": "First refinement.",
            "updated": first["updated"],
        },
    ]


@pytest.mark.parametrize("status", ["confirmed", "rejected"])
def test_update_draft_rejects_closed_draft(tmp_path: Path, status: str) -> None:
    plot_root = _project(tmp_path)
    draft_id = _record(tmp_path, "Kept wording")
    resolve_draft(str(tmp_path), "alpha", draft_id, status)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="new draft"):
        update_draft(str(tmp_path), "alpha", draft_id, "Changed", "Changed reason")

    assert read_draft(plot_root, "alpha", draft_id).proposed_text == "Kept wording"


def test_update_project_draft_uses_the_same_revision_rule(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    draft_id = _record(tmp_path, "Project name: North Star", canvas_kind="project")

    updated = update_draft(
        str(tmp_path), "alpha", draft_id, "Project name: Compass", "Clearer name."
    )

    assert updated["canvas_kind"] == "project"
    assert len(updated["revisions"]) == 1
    assert read_draft(plot_root, "alpha", draft_id).proposed_text.endswith("Compass")


class _ConcreteProposalProvider(ChatProvider):
    async def stream_turn(self, user_message: str) -> Any:
        yield ChatStreamEvent(type="turn_complete", turn_id="turn_1", text="Concrete proposal")


class _Hub(BroadcastHub):
    async def notify_event(
        self,
        plot_root: Path,
        event_name: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        return None


async def test_stream_chat_turn_does_not_extract_or_create_drafts(tmp_path: Path) -> None:
    plot_root = _project(tmp_path)
    append_user(plot_root, "alpha", "foundation", "codex", "user_1", "hello")
    await stream_chat_turn(
        _ConcreteProposalProvider(),
        _Hub(),
        plot_root,
        "hello",
        scope="foundation",
        project_id="alpha",
        provider_name="codex",
    )
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert list_drafts(plot_root, "alpha") == []
