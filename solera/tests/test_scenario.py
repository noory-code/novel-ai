"""CORE-8a — one full standalone scenario: goal -> plan -> run -> gate -> retro.

This is the whole slim core in one pass, with no Plot and no published spec. The
test plays the external agent; everything else is Solera's own helpers.
"""

import shlex
import sys
from pathlib import Path

from solera.audit import audit_workspace
from solera.formats import Progress, Retrospective
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
