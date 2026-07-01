"""Workspace directory-tree picker model — v0.32.0 (D-2026-05-31-L).

`build_dir_tree(workspace_root)` returns a nested `DirTreeNode` for the
new-project picker: each node carries `rel` (POSIX-relative, "." for root)
and `has_plot`. Heavy / dot dirs are pruned; depth + breadth capped.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.file_io import resolve_safe_path
from mashbill.models import DirTreeNode
from mashbill.workspace import MAX_TREE_DEPTH, build_dir_tree


def _flatten(node: DirTreeNode) -> list[DirTreeNode]:
    out = [node]
    for c in node.children:
        out.extend(_flatten(c))
    return out


def _child_names(node: DirTreeNode) -> set[str]:
    return {c.name for c in node.children}


def test_tree_has_plot_requires_a_real_project(tmp_path: Path) -> None:
    # v0.35.1 (D-2026-05-31-X) — ``has_plot`` means "this dir holds a real
    # project", not merely "a ``.plot`` folder exists". An empty ``.plot``
    # (e.g. one a stray read created) must read False, otherwise the picker
    # labels it "열기" and clicking it lands in create() with nothing to
    # open → a phantom new project.
    from mashbill.folder_io import create_project

    create_project(tmp_path / "a" / ".plot", "proj-real", "A")  # real project
    (tmp_path / "b" / ".plot").mkdir(parents=True)  # empty .plot
    (tmp_path / "c").mkdir()  # no .plot
    tree = build_dir_tree(tmp_path)
    by_name = {c.name: c for c in tree.children}
    assert by_name["a"].has_plot is True
    assert by_name["b"].has_plot is False
    assert by_name["c"].has_plot is False


def test_tree_root_rel_is_dot(tmp_path: Path) -> None:
    tree = build_dir_tree(tmp_path)
    assert tree.rel == "."


def test_tree_prunes_heavy_dirs(tmp_path: Path) -> None:
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    tree = build_dir_tree(tmp_path)
    assert _child_names(tree) == {"src"}


def test_tree_depth_cap(tmp_path: Path) -> None:
    deep = tmp_path
    for _ in range(MAX_TREE_DEPTH + 3):
        deep = deep / "d"
    deep.mkdir(parents=True)
    rels = {n.rel for n in _flatten(build_dir_tree(tmp_path))}
    # nothing deeper than MAX_TREE_DEPTH levels appears
    assert all(r == "." or len(r.split("/")) <= MAX_TREE_DEPTH for r in rels)


def test_tree_rels_are_relative_and_safe(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "c").mkdir()
    for node in _flatten(build_dir_tree(tmp_path)):
        assert ".." not in node.rel.split("/")
        if node.rel != ".":
            # round-trips the path-traversal guard without raising
            resolve_safe_path(tmp_path, node.rel)
