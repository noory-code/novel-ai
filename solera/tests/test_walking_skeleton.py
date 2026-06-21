"""CORE-4 — walking skeleton: one full turn of the loop, end to end.

A hand-written Story + Action, a gate tied to real agent output, and one pass
through the supervisor: todo -> doing -> (agent works) -> gate -> done. No
planning, no retrospective, no Plot. The test plays the external agent — in real
use that is Claude Code or Codex, never Solera itself.
"""

import shlex
import sys
from pathlib import Path

import yaml

from solera.supervisor import complete, instruction, start_next
from solera.workspace import Workspace

# Hand-written workspace (CORE-4a). The gate is satisfied only by the agent's
# output, so a green gate proves the work actually happened.
STORY = """\
---
status: todo
actions:
  - ACT-001
---
Leave a greeting file for the next step.
"""


def _hello_gate() -> str:
    code = "import os, sys; sys.exit(0 if os.path.exists('hello.txt') else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _action() -> str:
    fm = yaml.safe_dump({"status": "todo", "gate": _hello_gate()}).strip()
    return f"---\n{fm}\n---\nCreate hello.txt.\n"


def _seed(root: Path) -> Workspace:
    ws = Workspace(root)
    ws.story_dir("STORY-001").mkdir(parents=True)
    ws.story_path("STORY-001").write_text(STORY)
    ws.action_path("STORY-001", "ACT-001").write_text(_action())
    ws.progress_path.write_text("---\nstory: null\naction: null\n---\n")
    return ws


def test_walking_skeleton_one_turn(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws = _seed(project / ".noory" / "solera")

    # 4b — start the next action: it becomes doing and the pointer moves to it.
    pair = start_next(ws)
    assert pair == ("STORY-001", "ACT-001")
    story_id, action_id = pair
    assert ws.load_action(story_id, action_id).status == "doing"

    # The handoff the external agent would receive.
    note = instruction(ws, story_id, action_id)
    assert "Create hello.txt." in note

    # --- simulate the external agent doing the work ---
    (project / "hello.txt").write_text("hi")

    # Gate runs at the project root and passes because the file now exists.
    result = complete(ws, story_id, action_id, cwd=project)
    assert result.passed is True

    # 4c — final state: action + story done, pointer cleared, nothing left open.
    assert ws.load_action(story_id, action_id).status == "done"
    assert ws.load_story(story_id).status == "done"
    assert start_next(ws) is None
    prog = ws.load_progress()
    assert prog.story is None and prog.action is None


def test_walking_skeleton_stops_when_agent_does_nothing(tmp_path: Path) -> None:
    """If the agent produces nothing, the gate fails and the loop stops."""
    project = tmp_path / "project"
    project.mkdir()
    ws = _seed(project / ".noory" / "solera")

    story_id, action_id = start_next(ws)  # type: ignore[misc]
    # agent does NOT create hello.txt
    result = complete(ws, story_id, action_id, cwd=project)
    assert result.passed is False
    assert ws.load_action(story_id, action_id).status == "doing"  # stuck for a human
