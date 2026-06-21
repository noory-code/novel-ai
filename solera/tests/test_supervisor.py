"""CORE-3 — supervisor: order, status transitions, instruction, gate branch.

The supervisor is the L (ordering) of the harness. It never builds anything; it
finds the next open Action, hands the agent an instruction, runs the gate, and
moves the pointer on pass or stops for a human on fail.
"""

import shlex
import sys
from pathlib import Path

import yaml

from solera.supervisor import complete, find_next_todo, instruction, start_next
from solera.workspace import Workspace


def _py(code: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _action(gate: str, status: str = "todo", goal: str = "Do it.") -> str:
    fm = yaml.safe_dump({"status": status, "gate": gate}, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n{goal}\n"


def _story(actions: list[str], status: str = "todo", goal: str = "A goal.") -> str:
    fm = yaml.safe_dump({"status": status, "actions": actions}, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n{goal}\n"


def _pass_gate() -> str:
    return _py("import sys; sys.exit(0)")


def _file_gate(name: str) -> str:
    return _py(f"import os,sys; sys.exit(0 if os.path.exists({name!r}) else 1)")


def _seed_two_actions(tmp_path: Path) -> Workspace:
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.story_dir("STORY-001").mkdir(parents=True)
    ws.story_path("STORY-001").write_text(_story(["ACT-001", "ACT-002"]))
    ws.action_path("STORY-001", "ACT-001").write_text(_action(_pass_gate()))
    ws.action_path("STORY-001", "ACT-002").write_text(_action(_pass_gate()))
    ws.progress_path.write_text("---\nstory: null\naction: null\n---\n")
    return ws


# --- 3a find next todo -----------------------------------------------------


def test_find_next_todo_returns_first_open_in_order(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    assert find_next_todo(ws) == ("STORY-001", "ACT-001")


def test_find_next_todo_skips_done(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    ws.write_action("STORY-001", ws.load_action("STORY-001", "ACT-001").model_copy(
        update={"status": "done"}))
    assert find_next_todo(ws) == ("STORY-001", "ACT-002")


def test_find_next_todo_none_when_all_done(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    for a in ("ACT-001", "ACT-002"):
        ws.write_action("STORY-001", ws.load_action("STORY-001", a).model_copy(
            update={"status": "done"}))
    assert find_next_todo(ws) is None


# --- 3b/3e start: todo->doing + pointer ------------------------------------


def test_start_next_sets_doing_and_pointer(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    assert start_next(ws) == ("STORY-001", "ACT-001")
    assert ws.load_action("STORY-001", "ACT-001").status == "doing"
    prog = ws.load_progress()
    assert (prog.story, prog.action) == ("STORY-001", "ACT-001")


def test_start_next_clears_pointer_when_nothing_open(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    for a in ("ACT-001", "ACT-002"):
        ws.write_action("STORY-001", ws.load_action("STORY-001", a).model_copy(
            update={"status": "done"}))
    assert start_next(ws) is None
    prog = ws.load_progress()
    assert prog.story is None and prog.action is None


# --- 3c instruction --------------------------------------------------------


def test_instruction_mentions_goal_and_gate(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    text = instruction(ws, "STORY-001", "ACT-001")
    assert "Do it." in text
    assert "ACT-001" in text
    assert _pass_gate() in text


# --- 3d/3e complete: gate branch -------------------------------------------


def test_complete_pass_marks_done(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    start_next(ws)
    res = complete(ws, "STORY-001", "ACT-001", cwd=tmp_path)
    assert res.passed is True
    assert ws.load_action("STORY-001", "ACT-001").status == "done"


def test_complete_fail_leaves_doing(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.story_dir("STORY-001").mkdir(parents=True)
    ws.story_path("STORY-001").write_text(_story(["ACT-001"]))
    ws.action_path("STORY-001", "ACT-001").write_text(_action(_file_gate("missing.txt")))
    ws.progress_path.write_text("---\nstory: null\naction: null\n---\n")
    start_next(ws)
    res = complete(ws, "STORY-001", "ACT-001", cwd=tmp_path)
    assert res.passed is False
    assert ws.load_action("STORY-001", "ACT-001").status == "doing"  # stuck for human


def test_complete_marks_story_done_when_all_actions_done(tmp_path: Path) -> None:
    ws = _seed_two_actions(tmp_path)
    start_next(ws)
    complete(ws, "STORY-001", "ACT-001", cwd=tmp_path)
    start_next(ws)
    complete(ws, "STORY-001", "ACT-002", cwd=tmp_path)
    assert ws.load_story("STORY-001").status == "done"


def test_full_single_story_loop(tmp_path: Path) -> None:
    """todo -> doing -> gate -> done, twice, then nothing open."""
    ws = _seed_two_actions(tmp_path)
    seen = []
    while (pair := start_next(ws)) is not None:
        story_id, action_id = pair
        seen.append(action_id)
        res = complete(ws, story_id, action_id, cwd=tmp_path)
        assert res.passed is True
    assert seen == ["ACT-001", "ACT-002"]
    assert ws.load_story("STORY-001").status == "done"
    prog = ws.load_progress()
    assert prog.story is None and prog.action is None
