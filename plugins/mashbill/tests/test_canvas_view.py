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
from tests.conftest import _inline_canvas_fields


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


def test_inline_presentation_wins_over_stale_view_on_migration(tmp_path: Path) -> None:
    root = _project(tmp_path)
    path = _canvas_file(root, "alpha", "actors")
    raw = _stored(path)
    raw["nodes"] = [{"id": "n1", "kind": "actor", "x": 90}]
    path.write_text(json.dumps(raw), encoding="utf-8")
    view_file(path).write_text(json.dumps({"nodes": {"n1": {"x": 0, "y": 5}}, "edges": {}}))

    loaded = read_canvas_files(path)

    assert loaded is not None
    assert loaded["nodes"][0]["x"] == 90
    assert loaded["nodes"][0]["y"] == 5
    assert "x" not in _stored(path)["nodes"][0]
    assert _stored(view_file(path))["nodes"]["n1"] == {"x": 90, "y": 5}


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


_CANVAS_FILENAMES = {"canvas.json", "detail.json", ".view.json"}
_RAW_READERS = {
    # Blueprint traversal reads stored meaning to calculate a stable fingerprint.
    ("blueprint_content.py", "blueprint_content_fingerprint"),
    # Blueprint fingerprints deliberately read the stored meaning without a migration write.
    ("blueprint_content.py", "_read_canvas_json"),
    # The tag endpoint reads historical blobs without changing the working tree.
    ("endpoints_tags.py", "project_at_tag_endpoint"),
    # The tag endpoint's nested reader decodes historical blobs only.
    ("endpoints_tags.py", "_read_canvas_json"),
    # Git tag lookup reads historical bytes without touching the working tree.
    ("git_store.py", "read_file_at_tag"),
}
_RAW_READ_CALLS = {"_read_json", "_read_canvas_json", "read_file_at_tag", "open"}
_RAW_WRITE_CALLS = {"_write_json"}
_RAW_READ_METHODS = {"read_text", "read_bytes", "read", "readline", "readlines"}
_RAW_WRITE_METHODS = {
    "write_text",
    "write_bytes",
    "write",
    "writelines",
    "replace",
    "rename",
    "unlink",
}


def _raw_canvas_io_offenders(source: str, filename: str) -> list[str]:
    tree = ast.parse(source)
    offenders: set[str] = set()
    scopes = [
        tree,
        *(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ),
    ]
    for scope in scopes:
        nodes: list[ast.AST] = []
        pending = list(ast.iter_child_nodes(scope))
        while pending:
            node = pending.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            nodes.append(node)
            pending.extend(ast.iter_child_nodes(node))
        tainted: set[str] = set()
        scope_name = (
            scope.name if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)) else ""
        )
        if (
            isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef))
            and (filename, scope_name) in _RAW_READERS
        ):
            tainted.update(arg.arg for arg in scope.args.args)
        if (filename, scope_name) == ("blueprint_content.py", "blueprint_content_fingerprint"):
            tainted.add("path")

        def is_canvas_path(expr: ast.AST) -> bool:
            for node in ast.walk(expr):
                if isinstance(node, ast.Name) and node.id in tainted:
                    return True
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"_canvas_file", "view_file"}
                ):
                    return True
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and (
                        node.value.endswith(".view.json")
                        or any(
                            node.value == name or node.value.endswith("/" + name)
                            for name in _CANVAS_FILENAMES
                        )
                    )
                ):
                    return True
            return False

        assignments = [
            node for node in nodes if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
        ]
        for _ in range(len(assignments) + 1):
            before = len(tainted)
            for assignment in assignments:
                value = assignment.value
                if value is None or not is_canvas_path(value):
                    continue
                targets = (
                    assignment.targets
                    if isinstance(assignment, ast.Assign)
                    else [assignment.target]
                )
                tainted.update(
                    name.id
                    for target in targets
                    for name in ast.walk(target)
                    if isinstance(name, ast.Name)
                )
            for node in nodes:
                if isinstance(node, ast.withitem) and is_canvas_path(node.context_expr):
                    if node.optional_vars is not None:
                        tainted.update(
                            name.id
                            for name in ast.walk(node.optional_vars)
                            if isinstance(name, ast.Name)
                        )
            if len(tainted) == before:
                break

        for call in (node for node in nodes if isinstance(node, ast.Call)):
            operation: str | None = None
            target: ast.AST | None = None
            if isinstance(call.func, ast.Name):
                if call.func.id in _RAW_READ_CALLS:
                    operation = "read"
                elif call.func.id in _RAW_WRITE_CALLS:
                    operation = "write"
                if operation and call.args:
                    target = call.args[-1] if call.func.id == "read_file_at_tag" else call.args[0]
                if call.func.id == "open":
                    mode = (
                        call.args[1]
                        if len(call.args) > 1
                        else next(
                            (keyword.value for keyword in call.keywords if keyword.arg == "mode"),
                            None,
                        )
                    )
                    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                        operation = "write" if set(mode.value) & set("wax+") else "read"
            elif isinstance(call.func, ast.Attribute):
                name = call.func.attr
                if name in _RAW_READ_METHODS or name == "load":
                    operation = "read"
                elif name in _RAW_WRITE_METHODS or name == "dump":
                    operation = "write"
                elif name == "open":
                    mode = (
                        call.args[0]
                        if call.args
                        else next(
                            (keyword.value for keyword in call.keywords if keyword.arg == "mode"),
                            None,
                        )
                    )
                    operation = (
                        "write"
                        if isinstance(mode, ast.Constant)
                        and isinstance(mode.value, str)
                        and set(mode.value) & set("wax+")
                        else "read"
                    )
                if operation:
                    target = call.func.value
                    if name in {"load", "dump"} and call.args:
                        target = call.args[-1]
            if operation and target is not None and is_canvas_path(target):
                if operation == "read" and (filename, scope_name) in _RAW_READERS:
                    continue
                offenders.add(f"{filename}:{call.lineno}")
    return sorted(offenders)


def test_canvas_storage_helpers_are_the_only_raw_canvas_io() -> None:
    """Static paths only; argument paths need the runtime guard in conftest.py."""
    package = Path(__file__).resolve().parent.parent / "mashbill"
    offenders = [
        offender
        for path in package.rglob("*.py")
        if path.name not in {"canvas_view.py", "storage.py"}
        for offender in _raw_canvas_io_offenders(path.read_text(encoding="utf-8"), path.name)
    ]
    assert offenders == []


def test_raw_canvas_io_guard_detects_path_write_text() -> None:
    source = 'path = Path("canvas.json")\npath.write_text("{}")\n'
    assert _raw_canvas_io_offenders(
        "def write():\n    " + source.replace("\n", "\n    "), "new.py"
    ) == ["new.py:3"]


def test_runtime_guard_detects_argument_path_write_text(tmp_path: Path) -> None:
    def bypass(path: Path) -> None:
        path.write_text(json.dumps({"nodes": [{"id": "a", "x": 1}], "edges": []}))

    path = tmp_path / "canvas.json"
    bypass(path)
    assert _inline_canvas_fields(tmp_path) == [f"{path}:nodes[0].x"]
    path.unlink()
