"""The supervisor — Solera's ordering (L) over a workspace.

The supervisor never builds anything itself. It finds the next open Action,
hands the agent a plain-text instruction, runs the Action's gate, and either
advances (on pass) or stops for a human (on fail). All state is the workspace
files; the supervisor holds none of its own.

The pointer in ``progress.md`` tracks the single currently-active Action:
:func:`start_next` sets it, and clears it to ``null`` when nothing is open.
A gate failure leaves the Action in ``doing`` on purpose — it is stuck until a
human intervenes, rather than being silently skipped or retried in a loop.
"""

from __future__ import annotations

from pathlib import Path

from .formats import Action, Progress, Status, Story
from .gate import DEFAULT_TIMEOUT_SECONDS, GateResult, run_action_gate
from .workspace import Workspace


def find_next_todo(ws: Workspace) -> tuple[str, str] | None:
    """First ``todo`` Action in workspace order, or ``None`` if all are done.

    Order is deterministic: stories by sorted id, Actions in the order the Story
    declares them. Done Stories are skipped entirely.
    """
    for story_id in ws.list_stories():
        story = ws.load_story(story_id)
        if story.status == "done":
            continue
        for action_id in story.actions:
            if ws.load_action(story_id, action_id).status == "todo":
                return (story_id, action_id)
    return None


def set_action_status(ws: Workspace, story_id: str, action_id: str, status: Status) -> Action:
    """Rewrite one Action's status, preserving its gate and goal."""
    updated = ws.load_action(story_id, action_id).model_copy(update={"status": status})
    ws.write_action(story_id, updated)
    return updated


def set_story_status(ws: Workspace, story_id: str, status: Status) -> Story:
    """Rewrite one Story's status, preserving its actions and goal."""
    updated = ws.load_story(story_id).model_copy(update={"status": status})
    ws.write_story(updated)
    return updated


def start_next(ws: Workspace) -> tuple[str, str] | None:
    """Pick the next ``todo`` Action, mark it ``doing``, and point at it.

    Returns the ``(story_id, action_id)`` now in progress, or ``None`` when
    nothing is open — in which case the pointer is cleared to ``null``.
    """
    pair = find_next_todo(ws)
    if pair is None:
        ws.write_progress(Progress(story=None, action=None))
        return None
    story_id, action_id = pair
    set_action_status(ws, story_id, action_id, "doing")
    ws.write_progress(Progress(story=story_id, action=action_id))
    return pair


def instruction(ws: Workspace, story_id: str, action_id: str) -> str:
    """The plain-text handoff given to the external agent for one Action."""
    action = ws.load_action(story_id, action_id)
    return (
        f"You are working on action {action_id} of story {story_id}.\n\n"
        f"Goal:\n{action.goal}\n\n"
        "When you are done, Solera verifies your work by running this gate "
        "(do not run it yourself — just make it pass):\n"
        f"  {action.gate}\n"
    )


def complete(
    ws: Workspace,
    story_id: str,
    action_id: str,
    *,
    cwd: Path,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> GateResult:
    """Run the Action's gate and branch on the verdict.

    Pass: the Action becomes ``done``; if every Action in its Story is now done,
    the Story becomes ``done`` too. Fail: the Action stays ``doing`` and the
    result is returned so the caller stops and escalates to a human.
    """
    action = ws.load_action(story_id, action_id)
    result = run_action_gate(action, cwd=cwd, timeout=timeout)
    if not result.passed:
        return result
    set_action_status(ws, story_id, action_id, "done")
    story = ws.load_story(story_id)
    if all(ws.load_action(story_id, a).status == "done" for a in story.actions):
        set_story_status(ws, story_id, "done")
    return result
