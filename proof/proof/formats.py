"""The Decision model + parser/serializer.

A decision is a Markdown file: YAML frontmatter (title, status, supersedes) plus
a body of prose (context / decision / alternatives / consequences). Identity is
the file name, handed to the parser explicitly — never duplicated in frontmatter.
A malformed file raises :class:`FormatError` rather than being coerced.
"""

from __future__ import annotations

from typing import Any, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .errors import FormatError

Status = Literal["proposed", "accepted"]

_M = TypeVar("_M", bound=BaseModel)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FormatError("missing frontmatter: file must start with a '---' line")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            try:
                data = yaml.safe_load("\n".join(lines[1:i]))
            except yaml.YAMLError as exc:
                raise FormatError(f"invalid YAML frontmatter: {exc}") from exc
            if data is None:
                data = {}
            if not isinstance(data, dict):
                raise FormatError("frontmatter must be a mapping")
            return data, "\n".join(lines[i + 1 :]).strip()
    raise FormatError("missing closing '---' for frontmatter")


def _require_nonempty(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    return value


class Decision(BaseModel):
    """One recorded decision. Append-only — never edited once written."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    status: Status
    supersedes: str | None
    about: list[str] = Field(default_factory=list)
    body: str

    _check_title = field_validator("title")(_require_nonempty)
    _check_body = field_validator("body")(_require_nonempty)


def parse_decision(text: str, *, decision_id: str) -> Decision:
    """Parse a decision file. ``decision_id`` comes from the filename."""
    data, body = _split_frontmatter(text)
    try:
        return Decision.model_validate({**data, "id": decision_id, "body": body})
    except ValidationError as exc:
        raise FormatError(f"invalid decision: {exc}") from exc


def dump_decision(decision: Decision) -> str:
    """Serialize a decision back to file text. Inverse of :func:`parse_decision`."""
    fm = yaml.safe_dump(
        {
            "title": decision.title,
            "status": decision.status,
            "supersedes": decision.supersedes,
            "about": list(decision.about),
        },
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{fm}\n---\n{decision.body}\n"
