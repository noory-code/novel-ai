"""CORE-8a — one full standalone scenario: goal -> plan -> run -> gate -> retro.

This is the whole slim core in one pass, with no Plot and no published spec. The
test plays the external agent; everything else is Solera's own helpers.
"""

import shlex
import sys
from pathlib import Path

from solera.audit import audit_workspace
from solera.formats import Feedback, Progress, Retrospective
from solera.planning import add_action, create_story
from solera.supervisor import complete, start_next
from solera.workspace import Workspace


def _file_gate(name: str) -> str:
    code = f"import os, sys; sys.exit(0 if os.path.exists({name!r}) else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def test_full_standalone_scenario(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws = Workspace(project / ".noory" / "solera")
    ws.write_progress(Progress(story=None, action=None))

    # --- plan: a goal becomes a Story with two gated Actions ---
    story = create_story(ws, "Produce two greeting files.")
    add_action(ws, story.id, "Create a.txt", gate=_file_gate("a.txt"))
    add_action(ws, story.id, "Create b.txt", gate=_file_gate("b.txt"))

    # --- run: drive the loop, the test playing the agent each turn ---
    produced = {"ACT-001": "a.txt", "ACT-002": "b.txt"}
    done_order = []
    while (pair := start_next(ws)) is not None:
        story_id, action_id = pair
        (project / produced[action_id]).write_text("hi")  # the agent's work
        result = complete(ws, story_id, action_id, cwd=project)
        assert result.passed is True
        done_order.append(action_id)

    assert done_order == ["ACT-001", "ACT-002"]
    assert ws.load_story(story.id).status == "done"

    # --- retro: record what was learned; pointer cleared; workspace clean ---
    ws.write_retrospective(
        Retrospective(id=story.id, about=[], body="Two files produced; gates held.")
    )
    assert ws.load_retrospective(story.id).body.startswith("Two files")

    prog = ws.load_progress()
    assert prog.story is None and prog.action is None
    assert audit_workspace(ws) == []


def test_blocked_path_writes_feedback_and_holds(tmp_path: Path) -> None:
    """When a gate cannot pass, the agent records feedback and the Action holds."""
    project = tmp_path / "project"
    project.mkdir()
    ws = Workspace(project / ".noory" / "solera")
    ws.write_progress(Progress(story=None, action=None))

    story = create_story(ws, "Do something that gets stuck.")
    add_action(ws, story.id, "Create blocker.txt", gate=_file_gate("blocker.txt"))

    story_id, action_id = start_next(ws)  # type: ignore[misc]
    # the agent cannot produce the file; the gate fails
    assert complete(ws, story_id, action_id, cwd=project).passed is False

    # it writes a neutral feedback note and stops
    ws.write_feedback(Feedback(id="FB-001", about=[], body="Cannot create blocker.txt: no source."))
    assert ws.load_feedback("FB-001").body.startswith("Cannot")
    assert ws.list_feedback() == ["FB-001"]

    # the Action holds in doing; next re-offers it rather than skipping ahead
    assert ws.load_action(story_id, action_id).status == "doing"
    assert start_next(ws) == (story_id, action_id)
    assert audit_workspace(ws) == []
