"""D2-2 — one full standalone scenario over the tree: plan -> run -> gate -> retro.

The whole slim core in one pass, with no Novel. The test plays the external
agent; everything else is Solera's own helpers.
"""

import shlex
import sys
from pathlib import Path

from solera.audit import audit_workspace
from solera.formats import Feedback, Progress, Retrospective
from solera.planning import create_item
from solera.supervisor import complete, start_next
from solera.workspace import Workspace


def _file_gate(name: str) -> str:
    code = f"import os, sys; sys.exit(0 if os.path.exists({name!r}) else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def test_full_standalone_scenario(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws = Workspace(project / ".noory" / "solera")
    ws.write_progress(Progress(item=None))

    # plan: an initiative -> story -> two gated action leaves
    init = create_item(ws, "initiative", "Produce two greeting files.")
    story = create_item(ws, "story", "the greetings", parent=init.id)
    create_item(ws, "action", "Create a.txt", gate=_file_gate("a.txt"), parent=story.id)
    create_item(ws, "action", "Create b.txt", gate=_file_gate("b.txt"), parent=story.id)

    produced = {"ACT-001": "a.txt", "ACT-002": "b.txt"}
    done_order = []
    while (item_id := start_next(ws)) is not None:
        (project / produced[item_id]).write_text("hi")  # the agent's work
        assert complete(ws, item_id, cwd=project).passed is True
        done_order.append(item_id)

    assert done_order == ["ACT-001", "ACT-002"]
    # rollup reached the top
    assert ws.load_item(story.id).status == "done"
    assert ws.load_item(init.id).status == "done"

    ws.write_retrospective(
        Retrospective(id=init.id, about=[], body="Two files produced; gates held.")
    )
    assert ws.load_retrospective(init.id).body.startswith("Two files")
    assert ws.load_progress().item is None
    assert audit_workspace(ws) == []


def test_blocked_path_writes_feedback_and_holds(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    ws = Workspace(project / ".noory" / "solera")
    ws.write_progress(Progress(item=None))

    story = create_item(ws, "story", "gets stuck")
    leaf = create_item(ws, "action", "Create blocker.txt", gate=_file_gate("blocker.txt"),
                       parent=story.id)

    item_id = start_next(ws)
    assert item_id == leaf.id
    assert complete(ws, item_id, cwd=project).passed is False  # agent produced nothing

    ws.write_feedback(Feedback(id="FB-001", about=[], body="Cannot create blocker.txt."))
    assert ws.list_feedback() == ["FB-001"]
    assert ws.load_item(leaf.id).status == "doing"  # holds
    assert start_next(ws) == leaf.id  # resumes, does not skip
    assert audit_workspace(ws) == []
