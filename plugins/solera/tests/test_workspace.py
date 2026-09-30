"""Workspace layout + WorkItem io over the flat ``items/`` store."""

from pathlib import Path

import pytest

from solera.errors import FormatError
from solera.formats import Progress, WorkItem
from solera.workspace import Workspace

LEAF = WorkItem(id="ACT-001", level="action", status="todo", gate="true", goal="do step")
BOX = WorkItem(id="STORY-001", level="story", status="todo", children=["ACT-001"], goal="the box")


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_paths_compose_from_root(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    assert ws.progress_path == ws.root / "progress.md"
    assert ws.items_dir == ws.root / "items"
    assert ws.item_path("ACT-001") == ws.root / "items" / "ACT-001.md"
    assert ws.retrospective_path("STORY-001") == ws.root / "retros" / "STORY-001.md"
    assert ws.artifacts_dir("X") == ws.root / "artifacts" / "X"
    assert ws.spec_dir("auth-v1") == ws.root / "specs" / "auth-v1"


@pytest.mark.parametrize("name", ["../x", "/abs", "a/b", r"a\b", "..", ""])
@pytest.mark.parametrize(
    "path_method",
    [
        "item_path",
        "retrospective_path",
        "artifacts_dir",
        "feedback_path",
        "spec_dir",
    ],
)
def test_user_named_paths_reject_non_single_component_names(
    tmp_path: Path, name: str, path_method: str
) -> None:
    ws = _ws(tmp_path)

    with pytest.raises(FormatError, match="name"):
        getattr(ws, path_method)(name)

    assert not ws.root.exists()


def test_write_then_load_items(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.write_item(LEAF)
    ws.write_item(BOX)
    assert ws.load_item("ACT-001") == LEAF
    assert ws.load_item("STORY-001") == BOX
    assert ws.list_items() == ["ACT-001", "STORY-001"]


def test_progress_round_trip(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.write_progress(Progress(item="ACT-001"))
    assert ws.load_progress().item == "ACT-001"


def test_list_items_empty_when_no_dir(tmp_path: Path) -> None:
    assert _ws(tmp_path).list_items() == []


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _ws(tmp_path).load_progress()


def test_load_malformed_item_raises(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.items_dir.mkdir(parents=True)
    ws.item_path("ACT-001").write_text("garbage, no frontmatter\n")
    with pytest.raises(FormatError):
        ws.load_item("ACT-001")


def test_interrupted_item_write_preserves_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    ws.write_item(LEAF)
    path = ws.item_path(LEAF.id)
    original = path.read_text()
    original_write_text = Path.write_text

    def interrupt_after_partial_write(
        target: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        original_write_text(
            target,
            data[:8],
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
        raise OSError("interrupted write")

    monkeypatch.setattr(Path, "write_text", interrupt_after_partial_write)

    with pytest.raises(OSError, match="interrupted write"):
        ws.write_item(LEAF.model_copy(update={"status": "done"}))

    assert path.read_text() == original
    assert list(ws.items_dir.iterdir()) == [path]
