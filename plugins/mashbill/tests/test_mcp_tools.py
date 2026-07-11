"""The FastMCP tool surface — the agent's read/write interface to a project.

These tools are thin wrappers over folder_io / workspace / git_store, but they
ARE the contract Claude Code calls. Two silent-failure classes matter:
  1. a load-bearing tool quietly removed / renamed → the agent loses a verb;
  2. a wrapper delegating wrong args or reshaping the result wrong → e.g. the
     in-app coach's write lands somewhere unexpected.
A registry guard covers (1); end-to-end calls through the real functions cover (2).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mashbill import mcp_tools
from mashbill.git_store import init_workspace_repo

# Core verbs the agent (and the in-app coach) rely on. Removing/renaming any of
# these is a breaking change to the tool contract — this set makes it loud.
_CORE_TOOLS = {
    "list_projects",
    "discover_workspace_projects",
    "get_project",
    "create_project_tool",
    "rename_project",
    "delete_project_tool",
    "get_canvas",
    "update_canvas",
    "update_node",
    "create_node",
    "search_project_nodes",
    "tag_project",
    "list_project_tags",
    "delete_project_tag",
    "get_viewer_context",
    "get_design_principles",
}


async def test_registry_exposes_every_core_tool() -> None:
    tools = await mcp_tools.mcp.list_tools()
    names = {getattr(t, "name", None) or t["name"] for t in tools}
    missing = _CORE_TOOLS - names
    assert not missing, f"tool contract lost these verbs: {sorted(missing)}"


def test_create_list_get_project_roundtrip(tmp_path: Path) -> None:
    ws = str(tmp_path)
    created = mcp_tools.create_project_tool(ws, "p1", "Project One")
    assert created["id"] == "p1"

    listed = mcp_tools.list_projects(ws)
    assert "p1" in {p["id"] for p in listed}

    got = mcp_tools.get_project(ws, "p1")
    # get_project enriches the bare ProjectDoc with these two derived keys.
    assert got["id"] == "p1"
    assert "feature_details" in got and "tags" in got


def test_create_node_then_update_node_persists(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")

    created = mcp_tools.create_node(
        ws, "p1", "foundation", "mission", {"label": "Ship value weekly"}
    )
    node = created["node"]
    nid = node["id"]
    assert node["kind"] == "mission"
    assert node["label"] == "Ship value weekly"

    # update_node patches only the named content field on that one node.
    mcp_tools.update_node(ws, "p1", "foundation", nid, {"label": "Ship value daily"})

    canvas = mcp_tools.get_canvas(ws, "p1", "foundation")
    match = [n for n in canvas["nodes"] if n["id"] == nid]
    assert match and match[0]["label"] == "Ship value daily", (
        "update_node must persist the patched label to the canvas on disk"
    )


def test_create_node_rejects_structural_fields(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    # Position is server-minted, not writable through the content path.
    out = mcp_tools.create_node(ws, "p1", "foundation", "core_value", {"label": "Trust", "x": 999})
    assert "x" in out["rejected_fields"]
    assert out["node"]["label"] == "Trust"


def test_search_project_nodes_finds_by_label(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    mcp_tools.create_node(ws, "p1", "actors", "actor", {"label": "Reader"})

    hits = mcp_tools.search_project_nodes(ws, "p1", "read")  # case-insensitive
    assert any(h["label"] == "Reader" for h in hits)


def test_delete_project_tool_removes_it(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    msg = mcp_tools.delete_project_tool(ws, "p1")
    assert "p1" in msg
    assert "p1" not in {p["id"] for p in mcp_tools.list_projects(ws)}


def test_get_canvas_feature_without_service_id_is_rejected(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    # feature canvas is per-service — reading it needs a service_id.
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        mcp_tools.get_canvas(ws, "p1", "feature")


def test_update_canvas_overwrites_and_reports_sync(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    canvas = mcp_tools.get_canvas(ws, "p1", "foundation")
    out = mcp_tools.update_canvas(ws, "p1", canvas)
    # foundation is not the services overview, so nothing is reconciled.
    assert out["sync"] == {"created": [], "archived": [], "skipped_archive": []}
    assert out["canvas"]["canvas_kind"] == "foundation"


def test_rename_project_mirrors_onto_anchor_label(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "Old Name")
    renamed = mcp_tools.rename_project(ws, "p1", "New Name")
    assert renamed["name"] == "New Name"


def test_list_detail_canvases_empty_on_fresh_project(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    assert mcp_tools.list_detail_canvases(ws, "p1") == []


def test_discover_workspace_projects_finds_root_project(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    found = mcp_tools.discover_workspace_projects(ws)
    assert any(e["project"]["id"] == "p1" for e in found)


def test_migrate_v01_sketches_noop_returns_empty(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    # No legacy sketches/*.json present → nothing migrated, idempotent.
    assert mcp_tools.migrate_v01_sketches(ws) == []


def test_get_viewer_context_reports_no_live_viewer(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    ctx = mcp_tools.get_viewer_context(ws)
    # No viewer has reported, so the agent must not treat any selection as live.
    assert ctx["has_viewer"] is False
    assert ctx["active_canvas"] is None
    assert ctx["selection"] == []


def test_open_canvas_builds_url_and_opens_browser(tmp_path: Path, monkeypatch) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    opened: list[str] = []
    monkeypatch.setattr(mcp_tools.webbrowser, "open", opened.append)
    msg = mcp_tools.open_canvas(ws, "p1")
    assert opened and f"project_path={ws}" in opened[0] and "project=p1" in opened[0]
    assert "Opened" in msg


def test_tag_lifecycle_against_real_git(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    init_workspace_repo(Path(ws))  # the first tag needs an initialized repo

    tagged = mcp_tools.tag_project(ws, "p1", "session-start", message="kickoff")
    assert tagged["name"] == "session-start"

    names = {t["name"] for t in mcp_tools.list_project_tags(ws, "p1")}
    assert "session-start" in names

    msg = mcp_tools.delete_project_tag(ws, "p1", "session-start")
    assert "session-start" in msg
    assert "session-start" not in {t["name"] for t in mcp_tools.list_project_tags(ws, "p1")}


def test_tag_project_without_git_raises_actionable_error(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    # No git init → the tool must raise a guiding ValueError, not crash opaquely.
    with pytest.raises(ValueError, match="git not initialized"):
        mcp_tools.tag_project(ws, "p1", "x")


def test_design_principles_serve_discriminators_per_area() -> None:
    """D-2026-07-03-P — the coach's evaluation knowledge (distilled principles,
    D-2026-07-03-O) rides in the engine as an MCP tool, not the per-turn prompt
    (budget) and not RAG. Canon = noory-workspace docs/concepts/
    design-principles.md; this embedded copy must carry the discriminator
    questions for every area and reject unknown areas."""
    from mashbill.coaching_principles import get_principles

    for area in ("mission", "values", "services", "features"):
        text = get_principles(area)
        assert "판별" in text, area
    full = get_principles(None)
    assert "대가" in full and "교환" in full and "체감" in full
    import pytest

    with pytest.raises(ValueError):
        get_principles("nope")


def test_get_canvas_surfaces_the_synthetic_anchor(tmp_path: Path) -> None:
    """D-2026-07-03-W (user proposal: "헤드리스라도 앵커 개념을 넣어주면"):
    anchored canvases read by the AGENT include the project anchor as a
    node-like entry — before this, the coach could not see the hub every
    pillar should connect to (B-14's deeper root), and anchor knowledge
    lived only in prompt special-cases. Feature/entities canvases have no
    anchor and stay untouched."""
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "alpha", "Alpha")
    for kind in ("foundation", "actors", "services"):
        doc = mcp_tools.get_canvas(ws, "alpha", kind)
        anchors = [n for n in doc["nodes"] if n["id"] == "__project_anchor__"]
        assert len(anchors) == 1, kind
        assert anchors[0]["kind"] == "project"
    ents = mcp_tools.get_canvas(ws, "alpha", "entities")
    assert all(n["id"] != "__project_anchor__" for n in ents["nodes"])
