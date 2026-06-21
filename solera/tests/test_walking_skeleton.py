"""D2-2 — walking skeleton: one full turn of the loop over the tree.

A hand-planned story with one gated leaf, driven through the supervisor for one
turn: todo -> doing -> (agent works) -> gate -> done. The test plays the agent.
"""

import shlex
import sys
from pathlib import Path

from solera.formats import Progress
from solera.planning import create_item
from solera.supervisor import complete, instruction, start_next
from solera.workspace import Workspace


def _hello_gate() -> str:
    code = "import os, sys; sys.exit(0 if os.path.exists('hello.txt') else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _seed(project: Path) -> tuple[Workspace, str]:
    ws = Workspace(project / ".noory" / "solera")
    story = create_item(ws, "story", "Leave a greeting.")
    leaf = create_item(ws, "action", "Create hello.txt", gate=_hello_gate(), parent=story.id)
    ws.write_progress(Progress(item=None))
    return ws, leaf.id


def test_walking_skeleton_one_turn(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws, leaf_id = _seed(project)

    assert start_next(ws) == leaf_id
    assert ws.load_item(leaf_id).status == "doing"
    assert "Create hello.txt" in instruction(ws, leaf_id)

    (project / "hello.txt").write_text("hi")  # the agent's work

    assert complete(ws, leaf_id, cwd=project).passed is True
    assert ws.load_item(leaf_id).status == "done"
    assert start_next(ws) is None
    assert ws.load_progress().item is None


def test_walking_skeleton_stops_when_agent_does_nothing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws, leaf_id = _seed(project)
    start_next(ws)
    assert complete(ws, leaf_id, cwd=project).passed is False
    assert ws.load_item(leaf_id).status == "doing"
