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
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

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
