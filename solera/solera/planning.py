"""Planning — turn a goal into a Story, decompose it into Actions.

The *judgement* (how to split a goal, what each gate checks) belongs to the
agent and the plan skill. These helpers only own the mechanical part: allocating
ids and writing well-formed files. Because they build the validated
:class:`~solera.formats.Story` / :class:`~solera.formats.Action` models and write
through the workspace, anything they create satisfies the CORE-1 conventions —
the agent never hand-writes frontmatter.
"""

from __future__ import annotations

import re

from .formats import Action, Story
from .workspace import Workspace

_STORY_RE = re.compile(r"^STORY-(\d+)$")
_ACTION_RE = re.compile(r"^ACT-(\d+)$")


def _next_id(prefix: str, existing: list[str], pattern: re.Pattern[str]) -> str:
    highest = 0
    for name in existing:
        match = pattern.match(name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def next_story_id(ws: Workspace) -> str:
    """The next free ``STORY-NNN`` id in the workspace."""
    return _next_id("STORY", ws.list_stories(), _STORY_RE)


def next_action_id(story: Story) -> str:
    """The next free ``ACT-NNN`` id within ``story``."""
    return _next_id("ACT", list(story.actions), _ACTION_RE)


def create_story(ws: Workspace, goal: str) -> Story:
    """Create a new, empty Story for ``goal`` and write it to disk."""
    story = Story(id=next_story_id(ws), status="todo", actions=[], goal=goal)
    ws.write_story(story)
    return story


def add_action(ws: Workspace, story_id: str, goal: str, *, gate: str) -> Action:
    """Append a new Action to a Story; write the Action and the updated Story.

    One Action is a chunk an agent can finish in a single context, carrying the
    gate that verifies it.
    """
    story = ws.load_story(story_id)
    action = Action(id=next_action_id(story), status="todo", gate=gate, goal=goal)
    ws.write_action(story_id, action)
    ws.write_story(story.model_copy(update={"actions": [*story.actions, action.id]}))
    return action
