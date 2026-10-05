"""The FastMCP tool surface — the agent's read/write interface to a project.

These tools are thin wrappers over folder_io / workspace / git_store, but they
ARE the contract Claude Code calls. Two silent-failure classes matter:
  1. a load-bearing tool quietly removed / renamed → the agent loses a verb;
  2. a wrapper delegating wrong args or reshaping the result wrong → e.g. the
     in-app coach's write lands somewhere unexpected.
A registry guard covers (1); end-to-end calls through the real functions cover (2).
"""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path

import pytest
from fastmcp import FastMCP

from mashbill import mcp_tools
from mashbill.git_store import init_workspace_repo, tag_snapshot

# Core verbs the agent (and the in-app coach) rely on. Removing/renaming any of
# these is a breaking change to the tool contract — this set makes it loud.
_CORE_TOOLS = {
    "list_projects",
    "discover_workspace_projects",
    "get_project",
    "create_project_tool",
    "rename_project",
    "get_canvas",
    "update_canvas",
    "update_node",
    "set_design_check",
    "create_node",
    "search_project_nodes",
    "tag_project",
    "list_project_tags",
    "delete_project_tag",
    "get_viewer_context",
    "get_design_principles",
    "get_canvas_framing",
    "record_draft",
    "update_draft",
    "resolve_draft",
}


async def test_set_design_check_tool_description_guards_check_truth() -> None:
    tools = {tool.name: tool for tool in await mcp_tools.mcp.list_tools()}
    description = (tools["set_design_check"].description or "").lower()
    assert "checking" in description and "starts" in description
    assert "checked" in description and "finishes" in description
    assert "never" in description and "did not run" in description


async def test_registry_exposes_every_core_tool() -> None:
    tools = await mcp_tools.mcp.list_tools()
    names = {t.name for t in tools}
    missing = _CORE_TOOLS - names
    assert not missing, f"tool contract lost these verbs: {sorted(missing)}"


def test_get_canvas_framing_returns_the_scope_system_prompt() -> None:
    # The headless coach fetches the same authoritative framing the in-app coach
    # receives via --append-system-prompt, so the free (open-engine) coach is
    # first-class. One SSOT: the tool must return build_system_prompt(scope).
    from mashbill.chat_context import build_system_prompt

    for scope in ("foundation", "actors", "services"):
        assert mcp_tools.get_canvas_framing(scope) == build_system_prompt(scope)
    # A per-service thread resolves to the services framing (DRY), not empty.
    assert mcp_tools.get_canvas_framing("service:abc123") == build_system_prompt("service:abc123")
    # A framed scope is a strict superset of the universal cross-canvas
    # ``project`` scope — proving the composed prompt carries the playbooks
    # (incl. the WRITE gate: "no silent auto-generation", VISION AICollaboration)
    # the headless coach needs to be first-class.
    guard_only = mcp_tools.get_canvas_framing("project")
    framed = mcp_tools.get_canvas_framing("foundation")
    assert guard_only in framed and len(framed) > len(guard_only)


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


async def test_registry_does_not_expose_delete_project_tool() -> None:
    tools = await mcp_tools.mcp.list_tools()
    assert "delete_project_tool" not in {tool.name for tool in tools}


def test_publish_project_snapshot_requires_bump(tmp_path: Path) -> None:
    mcp_tools.create_project_tool(str(tmp_path), "alpha", "Alpha")
    with pytest.raises(TypeError):
        mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha")  # type: ignore[call-arg]


def test_publish_project_snapshot_returns_version_and_manifest(tmp_path: Path) -> None:
    mcp_tools.create_project_tool(str(tmp_path), "alpha", "Alpha")
    init_workspace_repo(tmp_path)

    result = mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha", "patch")

    assert result["to_version"] == "v0.1.1"
    assert result["manifest"]["release"] == "vP1"
    assert result["manifest"]["blueprint_version"] == "v0.1.1"


def test_publish_project_snapshot_requires_and_accepts_english_ids(tmp_path: Path) -> None:
    from mashbill.folder_io import read_canvas, write_canvas
    from mashbill.models import ActorNode
    from mashbill.workspace import resolve_plot_root

    mcp_tools.create_project_tool(str(tmp_path), "alpha", "Alpha")
    plot_root = resolve_plot_root(str(tmp_path))
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(update={"nodes": [ActorNode(id="operator", label="운영자")]}),
    )
    init_workspace_repo(tmp_path)

    with pytest.raises(ValueError, match="operator"):
        mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha", "patch")

    result = mcp_tools.publish_project_snapshot_tool(
        str(tmp_path),
        "alpha",
        "patch",
        slugs={"operator": "operator"},
    )
    assert any(item["id"] == "actor/operator" for item in result["manifest"]["elements"])


def test_publish_project_snapshot_reports_missing_git(tmp_path: Path) -> None:
    mcp_tools.create_project_tool(str(tmp_path), "alpha", "Alpha")

    with pytest.raises(ValueError, match="git init"):
        mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha", "patch")


def test_publish_project_snapshot_reports_unchanged_blueprint(tmp_path: Path) -> None:
    mcp_tools.create_project_tool(str(tmp_path), "alpha", "Alpha")
    init_workspace_repo(tmp_path)
    mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha", "patch")

    with pytest.raises(ValueError, match=r"blueprint is unchanged since v0\.1\.1"):
        mcp_tools.publish_project_snapshot_tool(str(tmp_path), "alpha", "patch")


async def test_hide_person_only_tools_removes_only_publish_tools() -> None:
    server = FastMCP("test")

    @server.tool()
    def publish_project_snapshot_tool() -> None:
        return None

    @server.tool()
    def publish_service_tool() -> None:
        return None

    @server.tool()
    def keep_me() -> None:
        return None

    mcp_tools.hide_person_only_tools(server)

    assert {tool.name for tool in await server.list_tools()} == {"keep_me"}


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
    assert out["sync"] == {
        "created": [],
        "restored": [],
        "archived": [],
        "skipped_archive": [],
    }
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


def test_open_canvas_builds_url_and_opens_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", opened.append)
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


def test_tag_project_rejects_reserved_version_name_without_git_side_effects(
    tmp_path: Path,
) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    init_workspace_repo(Path(ws))

    with pytest.raises(ValueError, match="reserved"):
        mcp_tools.tag_project(ws, "p1", "v0.1.0")

    assert mcp_tools.list_project_tags(ws, "p1") == []
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=ws,
        check=False,
        capture_output=True,
        text=True,
    )
    assert head.returncode != 0


def test_tag_project_accepts_session_name(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    init_workspace_repo(Path(ws))

    tagged = mcp_tools.tag_project(ws, "p1", "session-2026-09-29")

    assert tagged["name"] == "session-2026-09-29"


def test_delete_project_tag_preserves_published_version_and_removes_session_tag(
    tmp_path: Path,
) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    init_workspace_repo(Path(ws))
    tag_snapshot(Path(ws), "v0.1.1")
    mcp_tools.tag_project(ws, "p1", "session-2026-09-28")

    with pytest.raises(ValueError, match="published version"):
        mcp_tools.delete_project_tag(ws, "p1", "v0.1.1")

    assert "v0.1.1" in {t["name"] for t in mcp_tools.list_project_tags(ws, "p1")}
    mcp_tools.delete_project_tag(ws, "p1", "session-2026-09-28")
    assert "session-2026-09-28" not in {t["name"] for t in mcp_tools.list_project_tags(ws, "p1")}


def test_tag_project_without_git_raises_actionable_error(tmp_path: Path) -> None:
    ws = str(tmp_path)
    mcp_tools.create_project_tool(ws, "p1", "P1")
    # No git init → the tool must raise a guiding ValueError, not crash opaquely.
    with pytest.raises(ValueError, match="git not initialized"):
        mcp_tools.tag_project(ws, "p1", "x")


def test_design_principles_call_is_recorded_when_a_log_path_is_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W-177 — the discriminators ride as a tool the coach may or may not call,
    and nothing recorded whether it did. A coach experiment that changes the
    tool's text then cannot tell "the text does not help" from "the coach never
    read it" (O-00000043). The sim points this at the run directory."""
    import json as _json

    from mashbill import mcp_tools as tools

    log = tmp_path / "tool-calls.jsonl"
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(log))
    tools.get_design_principles(area="values")
    tools.get_design_principles(area="services")

    lines = [_json.loads(x) for x in log.read_text("utf-8").splitlines() if x.strip()]
    assert [x["area"] for x in lines] == ["values", "services"]
    assert all(x["tool"] == "get_design_principles" for x in lines)
    assert all(isinstance(x.get("ts"), (int, float)) for x in lines)


def test_design_principles_works_and_writes_nothing_without_a_log_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Recording is opt-in. Outside a sim run nobody sets the variable, and the
    tool must answer exactly as before rather than fail or write somewhere."""
    from mashbill import mcp_tools as tools

    monkeypatch.delenv("MASHBILL_TOOL_LOG", raising=False)
    monkeypatch.chdir(tmp_path)
    assert "확인하는 기준" in tools.get_design_principles(area="values")
    assert list(tmp_path.iterdir()) == []


def test_design_principles_survives_an_unwritable_log_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The coach's turn must not die because a log path went bad — recording is
    for us, the answer is for the founder."""
    from mashbill import mcp_tools as tools

    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(tmp_path / "no" / "such" / "dir.jsonl"))
    assert "확인하는 기준" in tools.get_design_principles(area="values")


def test_design_principles_serve_discriminators_per_area() -> None:
    """D-2026-07-03-P — the coach's evaluation knowledge (distilled principles,
    D-2026-07-03-O) rides in the engine as an MCP tool, not the per-turn prompt
    (budget) and not RAG. Canon = noory-workspace docs/concepts/
    design-principles.md; this embedded copy must carry the discriminator
    questions for every area and reject unknown areas."""
    from mashbill.coaching_principles import get_principles

    for area in (
        "mission",
        "values",
        "identity",
        "actors",
        "entities",
        "services",
        "features",
    ):
        text = get_principles(area)
        assert "확인" in text and "기준" in text, area
    # identity (D-2026-06-16-K listed it as a foundation pillar; W-27 fills the
    # one discriminator set that was missing) must carry its own criteria, not
    # just ride the mission/values framing.
    identity = get_principles("identity")
    assert "늘 지킬 태도와 행동 방식" in identity
    assert "구체적인 행동" in identity
    # W-61 (P-00000004 ⓐ, coach finding 1): the nesting/hierarchy discriminator
    # lived only in the actors *framing* (manipulation prompt), so it never
    # reached the coach's evaluation knowledge and canvases came out flat. The
    # actors quality principles must now carry the nesting discriminator.
    actors = get_principles("actors")
    assert "역할군 아래에 구체적인 역할" in actors
    assert "AI·시스템·소프트웨어를 액터로 두지 않았나" in actors
    assert "사람의 역할만 액터다" in actors
    assert "AI·시스템을 액터로 둠" in actors
    entities = get_principles("entities")
    assert entities and "엔티티" in entities
    assert "구현 모델" in entities and "일대일" in entities
    assert mcp_tools.get_design_principles(area="entities") == entities
    services = get_principles("services")
    assert "사람이 이루려는 결과 하나" in services
    assert "액터를 새로 만들지 않는다" in services
    assert "어느 서비스도 맡지 않은 것" in services
    assert "두 서비스가 함께 맡은 것" in services
    values = get_principles("values")
    assert "대화에서 가치 후보" in values
    assert "이름은 한 단어" in values
    assert "이름만 보고 가치가 아니라고 판단하지 않는다" in values
    assert "충돌 상황" in values and "무엇을 감수" in values
    mission = get_principles("mission")
    assert "무엇이 더 나아져야 하는지" in mission
    assert "해결 방법을 계속 내놓고 고쳐 가는" in mission
    # CD-2026-07-25-A was REVERTED (W-121). Values really do get filed as identity
    # lines (novel-workspace O-00000019), but two probe passes over the corpus
    # showed the coach already spots them under the criteria above — the gap was
    # never knowledge, so the extra criterion changed no verdict and only spent
    # prompt budget. Keep it out unless a measurement shows a gain.
    assert "정체성으로 흡수했나" not in values
    assert "가치를 삼키지 마라" not in get_principles("identity")
    full = get_principles(None)
    assert "대가" in full and "교환" in full and "더 나아져야" in full
    assert "늘 지킬 태도와 행동 방식" in full  # identity is included in the all-areas join
    assert "모든 사업에서 필요한 엔티티" in full
    assert "사람이 이루려는 결과 하나" in full
    assert "대화에서 가치 후보" in full
    import pytest

    with pytest.raises(ValueError):
        get_principles("nope")


def test_design_principles_cover_feature_gaps_size_and_failures() -> None:
    """D-2026-10-05-A: the coach checks feature completeness and failure paths."""
    from mashbill.coaching_principles import get_principles

    features = " ".join(get_principles("features").split())
    for rule in (
        "누가 만들고·보고·고치고·닫는지",
        "사람이 왜 하는지",
        "짝이 없는 것과 둘인 것",
        "같은 사람·목적·결과·규칙",
        "모든 엔티티에 넷이 다 필요하지는 않다",
        "발행본은 고치지 않고 새로 만든다",
        "혼자 시작한다",
        "서비스 결과가 의미 있게 달라진다",
        "정상·실패·취소 판단이 따로 있다",
        "감추면 제공 범위를 오해한다",
        "프로젝트 이름 바꾸기는 프로젝트 관리하기의 단계",
        "위험하다고 따로 빼지 않는다",
        "AI·다른 사람에게 요청",
        "할 수 없다·하면 안 된다·하지 않겠다·이미 달라졌다",
        "비용·권한·데이터·사용자 선택이 안 바뀔 때만",
        "기대한 결과가 안 나오면 시스템이 혼자 같은 결과를 만들 수 있나",
        "결제 실패는 갈래",
        "환불은 따로 된 기능",
        "로그인 만료",
        "공통 복구 기능 하나",
        "서비스 하나의 기능을 다 그린 뒤",
        "아무 기능도 맡지 않은 목적",
        "같은 엔티티를 다르게 다룸",
    ):
        assert rule in features, rule


def test_identity_principles_match_agreed_definition() -> None:
    """D-2026-08-18-F: identity applies throughout the service's work and turns
    a short directive into concrete behavior. Conflict judgment stays with values.
    """
    from mashbill.coaching_principles import get_principles

    identity = get_principles("identity")
    for rule in (
        "늘 지킬 태도와 행동 방식",
        "설계하고 만들고 사용자에게 보여 주는 동안",
        "밝고 명쾌하게",
        "구체적인 행동",
        "미션과 코어밸류",
        "코어밸류를 따른다",
        "개수나 항목을 미리 정하지 않는다",
    ):
        assert rule in identity, rule
    assert "거절하는 게 있나" not in identity
    assert "목소리·태도" not in identity


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
