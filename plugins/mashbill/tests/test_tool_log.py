"""Simulator tool log records successful MCP writes without their content."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mashbill import mcp_tools
from mashbill.mcp_context_tools import get_design_principles
from mashbill.mcp_draft_tools import record_draft, resolve_draft, update_draft


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_canvas_writes_append_identifiers_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = str(tmp_path)
    mcp_tools.create_project_tool(project_path, "p1", "Private project title")
    first = mcp_tools.create_node(
        project_path, "p1", "foundation", "mission", {"label": "Private mission text"}
    )["node"]["id"]
    second = mcp_tools.create_node(
        project_path, "p1", "foundation", "core_value", {"label": "Private value text"}
    )["node"]["id"]
    mcp_tools.create_edge(
        project_path, "p1", "foundation", first, second, label="Private edge text"
    )
    draft = record_draft(
        project_path,
        "p1",
        "foundation",
        "Private proposed text",
        "Private rationale text",
        target_node_ids=[first],
    )

    lines = _lines(log)
    assert [line["tool"] for line in lines] == [
        "create_node",
        "create_node",
        "create_edge",
        "record_draft",
    ]
    assert all(isinstance(line["ts"], (int, float)) for line in lines)
    assert lines[0]["project_id"] == "p1"
    assert lines[0]["canvas"] == "foundation"
    assert lines[0]["node_id"] == first
    assert lines[2]["node_ids"] == [first, second]
    assert lines[3]["node_ids"] == [first]
    assert lines[3]["draft_id"] == draft["draft_id"]
    raw = log.read_text(encoding="utf-8")
    for content in (
        "Private project title",
        "Private mission text",
        "Private value text",
        "Private edge text",
        "Private proposed text",
        "Private rationale text",
    ):
        assert content not in raw


def test_writes_without_log_env_create_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MASHBILL_TOOL_LOG", raising=False)
    project_path = str(tmp_path)
    mcp_tools.create_project_tool(project_path, "p1", "P1")
    first = mcp_tools.create_node(project_path, "p1", "foundation", "mission")["node"]["id"]
    second = mcp_tools.create_node(project_path, "p1", "foundation", "core_value")["node"]["id"]
    mcp_tools.create_edge(project_path, "p1", "foundation", first, second)
    record_draft(project_path, "p1", "foundation", "proposal", "reason")
    assert not (tmp_path / "tools.jsonl").exists()


def test_get_design_principles_still_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    get_design_principles("mission")
    assert _lines(log)[0]["tool"] == "get_design_principles"
    assert _lines(log)[0]["area"] == "mission"


def test_failed_write_does_not_append(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    mcp_tools.create_project_tool(str(tmp_path), "p1", "P1")
    with pytest.raises(ValueError):
        mcp_tools.update_node(str(tmp_path), "p1", "foundation", "missing", {"label": "secret"})
    assert not log.exists()


def test_other_writes_record_once_per_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = str(tmp_path)
    mcp_tools.create_project_tool(project_path, "p1", "P1")
    node_id = mcp_tools.create_node(
        project_path, "p1", "services", "service", {"label": "Secret service"}
    )["node"]["id"]
    mcp_tools.update_node(project_path, "p1", "services", node_id, {"label": "New secret"})
    mcp_tools.set_node_references(project_path, "p1", "services", node_id, {})
    canvas = mcp_tools.get_canvas(project_path, "p1", "services")
    mcp_tools.update_canvas(project_path, "p1", canvas)
    draft_id = record_draft(
        project_path,
        "p1",
        "services",
        "Secret proposal",
        "Secret reason",
        target_node_ids=[node_id],
    )["draft_id"]
    update_draft(project_path, "p1", draft_id, "New secret proposal", "New reason")
    resolve_draft(project_path, "p1", draft_id, "rejected")
    mcp_tools.set_design_check(project_path, "p1", node_id, "checking")
    mcp_tools.rename_project(project_path, "p1", "Secret project name")

    lines = _lines(log)
    assert [line["tool"] for line in lines] == [
        "create_node",
        "update_node",
        "set_node_references",
        "update_canvas",
        "record_draft",
        "update_draft",
        "resolve_draft",
        "set_design_check",
        "rename_project",
    ]
    assert all(line["project_id"] == "p1" for line in lines)
    assert all("Secret" not in json.dumps(line) for line in lines)
    assert lines[1]["node_id"] == node_id
    assert node_id in lines[3]["node_ids"]
    assert lines[5]["draft_id"] == draft_id


def test_rejected_draft_logs_target_node_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = str(tmp_path)
    mcp_tools.create_project_tool(project_path, "p1", "P1")
    node_id = mcp_tools.create_node(project_path, "p1", "foundation", "mission")["node"]["id"]
    draft_id = record_draft(
        project_path, "p1", "foundation", "Proposal", "Reason", target_node_ids=[node_id]
    )["draft_id"]

    resolve_draft(project_path, "p1", draft_id, "rejected")

    assert _lines(log)[-1]["node_ids"] == [node_id]


def test_rejected_draft_logs_resolved_node_ids_without_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    project_path = str(tmp_path)
    mcp_tools.create_project_tool(project_path, "p1", "P1")
    node_id = mcp_tools.create_node(project_path, "p1", "foundation", "mission")["node"]["id"]
    draft_id = record_draft(project_path, "p1", "foundation", "Proposal", "Reason")["draft_id"]
    resolve_draft(project_path, "p1", draft_id, "confirmed", [node_id])

    resolve_draft(project_path, "p1", draft_id, "rejected")

    assert _lines(log)[-1]["node_ids"] == [node_id]


def test_publication_tools_log_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "tools.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    mcp_tools.create_project_tool(str(tmp_path), "p1", "P1")
    monkeypatch.setattr(mcp_tools, "publish_blueprint_for_person", lambda *args, **kwargs: {})
    monkeypatch.setattr(mcp_tools, "publish_service", lambda *args, **kwargs: {})

    mcp_tools.publish_project_snapshot_tool(str(tmp_path), "p1", "patch")
    mcp_tools.publish_service_tool(str(tmp_path), "p1", "service-1")

    lines = _lines(log)
    assert [line["tool"] for line in lines] == [
        "publish_project_snapshot_tool",
        "publish_service_tool",
    ]
    assert lines[0]["project_id"] == "p1"
    assert lines[1]["service_id"] == "service-1"
    assert all("ts" in line for line in lines)
