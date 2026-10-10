"""Storage contract for D-2026-10-10-B."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, cast

from mashbill.canvas_view import read_canvas_files, view_file, write_canvas_files
from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.models import ActorNode, CanvasDoc, SketchEdge
from mashbill.storage import _canvas_file


def _project(tmp_path: Path) -> Path:
    root = tmp_path / ".noory" / "novel"
    create_project(root, "alpha", "Alpha")
    return root


def _stored(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_round_trip_splits_positions_colors_and_handles(tmp_path: Path) -> None:
    root = _project(tmp_path)
    canvas = CanvasDoc(
        canvas_id="actors",
        canvas_kind="actors",
        nodes=[ActorNode(id="a", label="A", x=123, y=456, color="#123456"), ActorNode(id="b")],
        edges=[SketchEdge(id="e", source="a", target="b", sourceHandle="right")],
    )
    saved = write_canvas(root, "alpha", canvas)
    path = _canvas_file(root, "alpha", "actors")
    semantic = _stored(path)
    view = _stored(view_file(path))
    assert all("x" not in node and "color" not in node for node in semantic["nodes"])
    assert "sourceHandle" not in semantic["edges"][0]
    assert view["nodes"]["a"]["x"] == 123
    assert view["nodes"]["a"]["color"] == "#123456"
    assert view["edges"]["e"]["sourceHandle"] == "right"
    assert read_canvas(root, "alpha", "actors") == saved


def test_legacy_inline_is_migrated_once(tmp_path: Path) -> None:
    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    original = _stored(path)
    original["nodes"] = [ActorNode(id="a", x=90, y=25).model_dump(by_alias=True)]
    path.write_text(json.dumps(original), encoding="utf-8")
    first = read_canvas(root, "alpha", "actors").model_dump(by_alias=True)
    assert first == CanvasDoc.model_validate(original).model_dump(by_alias=True)
    assert "x" not in _stored(path)["nodes"][0]
    assert _stored(view_file(path))["nodes"]["a"]["x"] == 90
    before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in (path, view_file(path))]
    assert read_canvas(root, "alpha", "actors").model_dump(by_alias=True) == first
    assert [(p.read_bytes(), p.stat().st_mtime_ns) for p in (path, view_file(path))] == before


def test_view_tolerates_missing_and_stale_entries(tmp_path: Path) -> None:
    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    doc = CanvasDoc(canvas_id="actors", canvas_kind="actors", nodes=[ActorNode(id="a")])
    write_canvas_files(path, doc.model_dump(by_alias=True))
    view_file(path).write_text(json.dumps({"nodes": {"deleted": {"x": 400}}, "edges": {}}))
    loaded = read_canvas(root, "alpha", "actors")
    assert loaded.nodes[0].x == ActorNode(id="a").x
    write_canvas_files(path, loaded.model_dump(by_alias=True))
    assert "deleted" not in _stored(view_file(path))["nodes"]


def test_unchanged_side_keeps_bytes_and_mtime(tmp_path: Path) -> None:
    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    doc = CanvasDoc(canvas_id="actors", canvas_kind="actors", nodes=[ActorNode(id="a", label="A")])
    write_canvas_files(path, doc.model_dump(by_alias=True))
    semantic_before = (path.read_bytes(), path.stat().st_mtime_ns)
    moved = doc.model_dump(by_alias=True)
    moved["nodes"][0]["x"] = 300
    write_canvas_files(path, moved)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == semantic_before
    view_path = view_file(path)
    view_before = (view_path.read_bytes(), view_path.stat().st_mtime_ns)
    moved["nodes"][0]["label"] = "B"
    write_canvas_files(path, moved)
    assert (view_path.read_bytes(), view_path.stat().st_mtime_ns) == view_before
    assert read_canvas_files(path) == moved


def test_blank_canvas_creation_writes_view_file(tmp_path: Path) -> None:
    root = _project(tmp_path)
    for kind in ("foundation", "actors", "services", "entities"):
        path = _canvas_file(root, "alpha", kind)
        assert _stored(view_file(path)) == {"nodes": {}, "edges": {}}


def test_canvas_migration_writes_semantics_only(tmp_path: Path) -> None:
    from mashbill.canvas_migrations import _migrate_parent_id_to_directed_edges

    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    raw = {
        "canvas_id": "actors",
        "canvas_kind": "actors",
        "nodes": [
            {"id": "a", "kind": "actor", "x": 42},
            {"id": "b", "kind": "actor", "parent_id": "a", "x": 75},
        ],
        "edges": [],
    }
    _migrate_parent_id_to_directed_edges(root, "alpha", "actors", None, raw)
    assert all("x" not in node for node in _stored(path)["nodes"])
    assert _stored(view_file(path))["nodes"]["b"]["x"] == 75


def test_foundation_migration_writes_semantics_only(tmp_path: Path) -> None:
    from mashbill.migrate_foundation import upgrade_foundation_canvas_if_needed

    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "foundation")
    raw = _stored(path)
    raw["canvas_kind"] = "core"
    raw["nodes"] = [{"id": "core", "kind": "core", "label": "Old", "x": 47}]
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert upgrade_foundation_canvas_if_needed(root, "alpha")
    assert "x" not in _stored(path)["nodes"][0]
    assert _stored(view_file(path))["nodes"]["core"]["x"] == 47


def test_v01_migration_writes_semantics_only(tmp_path: Path) -> None:
    from mashbill.migrate_v01 import migrate_v01_to_v02

    root = tmp_path / ".noory" / "novel"
    sketches = root / "sketches"
    sketches.mkdir(parents=True)
    (sketches / "alpha.json").write_text(
        json.dumps(
            {
                "id": "alpha",
                "name": "Alpha",
                "nodes": [
                    {"id": "core", "kind": "core", "x": 61},
                    {"id": "actor", "kind": "actor", "is_root": True, "x": 92},
                ],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    assert migrate_v01_to_v02(root) == ["alpha"]
    path = _canvas_file(root, "alpha", "actors")
    assert all("x" not in node for node in _stored(path)["nodes"])
    assert _stored(view_file(path))["nodes"]


def test_detail_sync_writes_semantics_only(tmp_path: Path) -> None:
    from mashbill.detail_sync import sync_details_with_overview
    from mashbill.models import FeatureNode

    root = _project(tmp_path)
    write_canvas(
        root,
        "alpha",
        CanvasDoc(
            canvas_id="services",
            canvas_kind="services",
            nodes=[FeatureNode(id="feature", label="Feature", x=71)],
        ),
    )
    assert sync_details_with_overview(root, "alpha")["created"] == ["feature"]
    path = _canvas_file(root, "alpha", "feature", "feature")
    assert "x" not in _stored(path)["nodes"][0]
    assert _stored(view_file(path))["nodes"]["feature"]["x"] == 71


def test_design_check_related_write_keeps_view_separate(tmp_path: Path) -> None:
    from mashbill.design_check import write_related

    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    raw = CanvasDoc(
        canvas_id="actors", canvas_kind="actors", nodes=[ActorNode(id="a", x=48)]
    ).model_dump(by_alias=True)
    write_related([(path, raw)])
    assert "x" not in _stored(path)["nodes"][0]
    assert _stored(view_file(path))["nodes"]["a"]["x"] == 48


def test_canvas_storage_helpers_are_the_only_raw_canvas_io() -> None:
    package = Path(__file__).resolve().parent.parent / "mashbill"
    offenders: list[str] = []
    for path in package.glob("*.py"):
        if path.name == "canvas_view.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        canvas_paths = {
            target.id
            for assignment in (node for node in ast.walk(tree) if isinstance(node, ast.Assign))
            for target in assignment.targets
            if isinstance(target, ast.Name)
            and isinstance(assignment.value, ast.Call)
            and isinstance(assignment.value.func, ast.Name)
            and assignment.value.func.id == "_canvas_file"
        }
        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            if not isinstance(call.func, ast.Name) or call.func.id not in {
                "_write_json",
                "_read_json",
            }:
                continue
            if call.args and (
                isinstance(call.args[0], ast.Name)
                and call.args[0].id in canvas_paths
                or any(
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "_canvas_file"
                    for node in ast.walk(call.args[0])
                )
            ):
                offenders.append(f"{path.name}:{call.lineno}")
    assert offenders == []
