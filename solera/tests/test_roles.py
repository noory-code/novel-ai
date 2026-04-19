"""Tests for :class:`Role` parser (v5.0+)."""

from __future__ import annotations

from pathlib import Path

from solera_mcp.graph import build_graph, read_roles


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_read_roles_parses_description_and_context(tmp_path: Path) -> None:
    _write(
        tmp_path / "roles" / "admin.md",
        "---\nid: admin\nkind: role\nname: Admin\nstatus: active\n"
        "created: 2026-04-19\n---\n\n"
        "# Description\nAn operator who configures and oversees the service.\n\n"
        "# Context\nUsed by the runtime team daily.\n",
    )

    roles = read_roles(tmp_path)
    assert len(roles) == 1
    r = roles[0]
    assert r.id == "admin"
    assert r.name == "Admin"
    assert "operator" in r.description
    assert r.context and "runtime team" in r.context
    assert r.parent is None
    assert r.integrity == []


def test_read_roles_captures_parent_chain(tmp_path: Path) -> None:
    _write(
        tmp_path / "roles" / "user.md",
        "---\nid: user\nkind: role\nname: User\nstatus: active\n"
        "created: 2026-04-19\n---\n\n# Description\nA user.\n",
    )
    _write(
        tmp_path / "roles" / "vip.md",
        "---\nid: vip\nkind: role\nname: VIP\nstatus: active\n"
        "created: 2026-04-19\nparent: user\n---\n\n# Description\nA VIP user.\n",
    )

    roles = {r.id: r for r in read_roles(tmp_path)}
    assert roles["user"].parent is None
    assert roles["vip"].parent == "user"


def test_role_broken_parent_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    _write(
        tmp_path / "roles" / "orphan.md",
        "---\nid: orphan\nkind: role\nname: Orphan\nstatus: active\n"
        "created: 2026-04-19\nparent: nonexistent\n---\n\n# Description\nOrphan.\n",
    )

    graph = build_graph(tmp_path)

    r = graph.roles[0]
    assert r.parent == "nonexistent"
    assert "broken_parent_ref" in r.integrity


def test_role_inactive_parent_ref_flagged_by_build_graph(tmp_path: Path) -> None:
    _write(
        tmp_path / "roles" / "retiring.md",
        "---\nid: retiring\nkind: role\nname: Retiring\nstatus: deprecated\n"
        "created: 2026-04-19\n---\n\n# Description\nGoing away.\n",
    )
    _write(
        tmp_path / "roles" / "child.md",
        "---\nid: child\nkind: role\nname: Child\nstatus: active\n"
        "created: 2026-04-19\nparent: retiring\n---\n\n# Description\nChild.\n",
    )

    graph = build_graph(tmp_path)

    child = next(r for r in graph.roles if r.id == "child")
    assert "inactive_parent_ref" in child.integrity


def test_read_roles_skips_index_file(tmp_path: Path) -> None:
    _write(
        tmp_path / "roles" / "admin.md",
        "---\nid: admin\nkind: role\nname: Admin\nstatus: active\n"
        "created: 2026-04-19\n---\n\n# Description\nOp.\n",
    )
    _write(tmp_path / "roles" / "_index.md", "# Active Roles\n")

    assert {r.id for r in read_roles(tmp_path)} == {"admin"}


def test_read_roles_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert read_roles(tmp_path) == []
