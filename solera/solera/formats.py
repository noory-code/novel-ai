"""Parsers and models for the plain-file ``.noory/solera/`` workspace.

Each Story and Action is a Markdown file: a YAML frontmatter block holds the
machine-readable fields, the body holds the human goal. Identity is **not** in
the frontmatter — it lives in the path (the Action's filename, the Story's
directory name) and is handed to the parser explicitly. This keeps a single
source of truth for ids and avoids drift between a file's name and its contents.

The parsers fail fast: a malformed file raises :class:`FormatError` rather than
being silently coerced, so a bad workspace never reaches the supervisor or gate.
"""

from __future__ import annotations

from typing import Any, Literal, TypeVar

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .errors import FormatError

Status = Literal["todo", "doing", "done"]

_M = TypeVar("_M", bound=BaseModel)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split ``---``-fenced YAML frontmatter from the Markdown body.

    Returns the parsed frontmatter mapping and the stripped body text.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FormatError("missing frontmatter: file must start with a '---' line")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_text = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :]).strip()
            try:
                data = yaml.safe_load(fm_text)
            except yaml.YAMLError as exc:
                raise FormatError(f"invalid YAML frontmatter: {exc}") from exc
            if data is None:
                data = {}
            if not isinstance(data, dict):
                raise FormatError("frontmatter must be a mapping")
            return data, body
    raise FormatError("missing closing '---' for frontmatter")


def _require_goal(value: str) -> str:
    if not value.strip():
        raise ValueError("goal body must not be empty")
    return value


class Action(BaseModel):
    """A unit of work an AI agent can finish in one context, with a gate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    status: Status
    gate: str
    goal: str

    _check_goal = field_validator("goal")(_require_goal)


class Story(BaseModel):
    """A goal decomposed into an ordered list of Action ids."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    status: Status
    actions: list[str]
    goal: str

    _check_goal = field_validator("goal")(_require_goal)


class Progress(BaseModel):
    """The current pointer into the workspace: which Story / Action is active."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    story: str | None
    action: str | None


class WorkItem(BaseModel):
    """One rung of the altitude ladder — initiative, epic, story, or action.

    ``level`` is a free label (conventionally initiative/epic/story/action). The
    executable invariant: a **leaf** carries a ``gate`` and no children; a
    **container** carries children and no gate. An item may have neither yet (a
    container awaiting decomposition) but never both.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    level: str
    status: Status
    gate: str = ""
    children: list[str] = Field(default_factory=list)
    goal: str

    _check_goal = field_validator("goal")(_require_goal)

    @model_validator(mode="after")
    def _not_both_leaf_and_container(self) -> WorkItem:
        if self.gate and self.children:
            raise ValueError(
                "a WorkItem cannot be both a leaf (gate) and a container (children)"
            )
        return self

    @property
    def is_leaf(self) -> bool:
        return bool(self.gate)

    @property
    def is_container(self) -> bool:
        return bool(self.children)


class _Note(BaseModel):
    """A neutral ID-tagged note: a body of prose plus optional ``about`` tags.

    ``about`` is the feedback sensor of the loop — ids the note is about. It is
    optional so standalone Solera (no published spec) still produces valid notes.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    about: list[str] = Field(default_factory=list)
    body: str

    _check_body = field_validator("body")(_require_goal)


class Retrospective(_Note):
    """Written after a Story finishes: what the design lacked (post-hoc sensor)."""


class Feedback(_Note):
    """Written while blocked: a neutral note for a human to act on (escalation)."""


def _build(model: type[_M], data: dict[str, Any], **path_fields: Any) -> _M:
    try:
        return model.model_validate({**data, **path_fields})
    except ValidationError as exc:
        raise FormatError(f"invalid {model.__name__.lower()}: {exc}") from exc


def parse_action(text: str, *, action_id: str) -> Action:
    """Parse an Action file. ``action_id`` comes from the filename."""
    data, body = _split_frontmatter(text)
    return _build(Action, data, id=action_id, goal=body)


def parse_story(text: str, *, story_id: str) -> Story:
    """Parse a Story file. ``story_id`` comes from the directory name."""
    data, body = _split_frontmatter(text)
    return _build(Story, data, id=story_id, goal=body)


def parse_progress(text: str) -> Progress:
    """Parse ``progress.md`` — the pointer to the active Story / Action."""
    data, _ = _split_frontmatter(text)
    return _build(Progress, data)


def _frontmatter(fields: dict[str, Any]) -> str:
    return yaml.safe_dump(fields, sort_keys=False, default_flow_style=False).strip()


def dump_action(action: Action) -> str:
    """Serialize an Action back to file text. Inverse of :func:`parse_action`.

    ``id`` is omitted — it lives in the filename, not the frontmatter.
    """
    fm = _frontmatter({"status": action.status, "gate": action.gate})
    return f"---\n{fm}\n---\n{action.goal}\n"


def dump_story(story: Story) -> str:
    """Serialize a Story back to file text. Inverse of :func:`parse_story`."""
    fm = _frontmatter({"status": story.status, "actions": list(story.actions)})
    return f"---\n{fm}\n---\n{story.goal}\n"


def dump_progress(progress: Progress) -> str:
    """Serialize the pointer back to ``progress.md`` text."""
    fm = _frontmatter({"story": progress.story, "action": progress.action})
    return f"---\n{fm}\n---\n"


def parse_workitem(text: str, *, item_id: str) -> WorkItem:
    """Parse a WorkItem file. ``item_id`` comes from the filename."""
    data, body = _split_frontmatter(text)
    return _build(WorkItem, data, id=item_id, goal=body)


def dump_workitem(item: WorkItem) -> str:
    """Serialize a WorkItem back to file text. Inverse of :func:`parse_workitem`."""
    fm = _frontmatter(
        {
            "level": item.level,
            "status": item.status,
            "gate": item.gate,
            "children": list(item.children),
        }
    )
    return f"---\n{fm}\n---\n{item.goal}\n"


def parse_retrospective(text: str, *, story_id: str) -> Retrospective:
    """Parse a ``RETROSPECTIVE.md``. ``story_id`` comes from the directory."""
    data, body = _split_frontmatter(text)
    return _build(Retrospective, data, id=story_id, body=body)


def parse_feedback(text: str, *, feedback_id: str) -> Feedback:
    """Parse a ``feedback/{id}.md``. ``feedback_id`` comes from the filename."""
    data, body = _split_frontmatter(text)
    return _build(Feedback, data, id=feedback_id, body=body)


def dump_retrospective(retro: Retrospective) -> str:
    """Serialize a Retrospective back to file text."""
    fm = _frontmatter({"about": list(retro.about)})
    return f"---\n{fm}\n---\n{retro.body}\n"


def dump_feedback(feedback: Feedback) -> str:
    """Serialize a Feedback note back to file text."""
    fm = _frontmatter({"about": list(feedback.about)})
    return f"---\n{fm}\n---\n{feedback.body}\n"
