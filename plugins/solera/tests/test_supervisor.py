"""CORE-3 / D2-2 — supervisor over the WorkItem tree.

The supervisor never builds anything; it walks the tree to the next open leaf,
runs its gate, and rolls completion up the ancestors. A failed leaf holds in
``doing`` and is resumed, not skipped.
"""

import shlex
import sys
from pathlib import Path

from solera.formats import Progress
from solera.planning import create_item
from solera.supervisor import complete, find_next_open, instruction, start_next
from solera.workspace import Workspace


def _py(code: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _pass() -> str:
    return _py("import sys; sys.exit(0)")


def _file_gate(name: str) -> str:
    return _py(f"import os,sys; sys.exit(0 if os.path.exists({name!r}) else 1)")


def _seed_story(tmp_path: Path) -> tuple[Workspace, str, str, str]:
    """A story container with two action leaves."""
    ws = Workspace(tmp_path / ".noory" / "solera")
    story = create_item(ws, "story", "the box")
    a1 = create_item(ws, "action", "step one", gate=_pass(), parent=story.id)
    a2 = create_item(ws, "action", "step two", gate=_pass(), parent=story.id)
    ws.write_progress(Progress(item=None))
    return ws, story.id, a1.id, a2.id


# --- find next open --------------------------------------------------------


def test_find_next_open_returns_first_leaf(tmp_path: Path) -> None:
    ws, _story, a1, _a2 = _seed_story(tmp_path)
    assert find_next_open(ws) == a1


def test_find_next_open_skips_done_leaf(tmp_path: Path) -> None:
    ws, _story, a1, a2 = _seed_story(tmp_path)
    ws.write_item(ws.load_item(a1).model_copy(update={"status": "done"}))
    assert find_next_open(ws) == a2


def test_find_next_open_none_when_all_done(tmp_path: Path) -> None:
    ws, _story, a1, a2 = _seed_story(tmp_path)
    for a in (a1, a2):
        ws.write_item(ws.load_item(a).model_copy(update={"status": "done"}))
    assert find_next_open(ws) is None


def test_find_next_open_resumes_doing_before_todo(tmp_path: Path) -> None:
    ws, _story, a1, _a2 = _seed_story(tmp_path)
    ws.write_item(ws.load_item(a1).model_copy(update={"status": "doing"}))
    assert find_next_open(ws) == a1


def test_find_next_open_dives_through_deep_tree(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    init = create_item(ws, "initiative", "stand up auth")
    epic = create_item(ws, "epic", "foundation", parent=init.id)
    story = create_item(ws, "story", "wire it", parent=epic.id)
    leaf = create_item(ws, "action", "do it", gate=_pass(), parent=story.id)
    assert find_next_open(ws) == leaf.id


# --- start / complete / rollup ---------------------------------------------


def test_start_next_sets_doing_and_pointer(tmp_path: Path) -> None:
    ws, _story, a1, _a2 = _seed_story(tmp_path)
    assert start_next(ws) == a1
    assert ws.load_item(a1).status == "doing"
    assert ws.load_progress().item == a1


def test_start_next_clears_pointer_when_nothing_open(tmp_path: Path) -> None:
    ws, _story, a1, a2 = _seed_story(tmp_path)
    for a in (a1, a2):
        ws.write_item(ws.load_item(a).model_copy(update={"status": "done"}))
    assert start_next(ws) is None
    assert ws.load_progress().item is None


def test_instruction_mentions_goal_and_gate(tmp_path: Path) -> None:
    ws, _story, a1, _a2 = _seed_story(tmp_path)
    text = instruction(ws, a1)
    assert "step one" in text
    assert a1 in text
    assert _pass() in text


def test_complete_pass_marks_done(tmp_path: Path) -> None:
    ws, _story, a1, _a2 = _seed_story(tmp_path)
    start_next(ws)
    assert complete(ws, a1, cwd=tmp_path).passed is True
    assert ws.load_item(a1).status == "done"


def test_complete_fail_leaves_doing_and_next_resumes(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    story = create_item(ws, "story", "box")
    a1 = create_item(ws, "action", "make file", gate=_file_gate("missing.txt"), parent=story.id)
    a2 = create_item(ws, "action", "next", gate=_pass(), parent=story.id)
    ws.write_progress(Progress(item=None))
    start_next(ws)
    assert complete(ws, a1.id, cwd=tmp_path).passed is False
    assert ws.load_item(a1.id).status == "doing"  # stuck for a human
    assert start_next(ws) == a1.id  # resumes, does not skip to a2
    assert ws.load_item(a2.id).status == "todo"


def test_complete_rolls_up_container_when_all_children_done(tmp_path: Path) -> None:
    ws, story, a1, a2 = _seed_story(tmp_path)
    start_next(ws)
    complete(ws, a1, cwd=tmp_path)
    assert ws.load_item(story).status == "todo"  # not yet — a2 still open
    start_next(ws)
    complete(ws, a2, cwd=tmp_path)
    assert ws.load_item(story).status == "done"  # rolled up


def test_rollup_propagates_up_multiple_levels(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    init = create_item(ws, "initiative", "stand up auth")
    epic = create_item(ws, "epic", "foundation", parent=init.id)
    story = create_item(ws, "story", "wire it", parent=epic.id)
    leaf = create_item(ws, "action", "do it", gate=_pass(), parent=story.id)
    ws.write_progress(Progress(item=None))
    start_next(ws)
    complete(ws, leaf.id, cwd=tmp_path)
    assert ws.load_item(story.id).status == "done"
    assert ws.load_item(epic.id).status == "done"
    assert ws.load_item(init.id).status == "done"


def test_full_single_story_loop(tmp_path: Path) -> None:
    ws, story, a1, a2 = _seed_story(tmp_path)
    seen = []
    while (item_id := start_next(ws)) is not None:
        seen.append(item_id)
        assert complete(ws, item_id, cwd=tmp_path).passed is True
    assert seen == [a1, a2]
    assert ws.load_item(story).status == "done"
    assert ws.load_progress().item is None
