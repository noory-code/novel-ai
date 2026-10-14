"""Compact argument shapes of the coach's most used Mashbill tools.

Read off the tool functions' signatures and, for ``propose_flow``'s list
arguments, off the draft models that validate them, so the text follows the
tools. A shape reads ``tool({arg, optional?, arg:a|b, list:[{field}]})``; the
two project arguments every project tool takes are named once in front.
"""

from __future__ import annotations

import inspect
import types
import typing
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel

from mashbill.coaching_principles import AREAS
from mashbill.design_check import set_design_check
from mashbill.flow_proposal import FlowProposal
from mashbill.mcp_canvas_tools import create_edge, create_node, update_node
from mashbill.mcp_context_tools import get_design_principles
from mashbill.mcp_draft_tools import record_draft
from mashbill.mcp_flow_tools import draw_proposed_flow, propose_flow

_PROJECT_ARGS = ("project_path", "project_id")

# (tool, model whose fields type its list-of-object arguments, values a str argument takes)
_Entry = tuple[Callable[..., Any], type[BaseModel] | None, dict[str, tuple[str, ...]]]
_TOOLS: tuple[_Entry, ...] = (
    (propose_flow, FlowProposal, {}),
    (draw_proposed_flow, None, {}),
    (create_node, None, {}),
    (create_edge, None, {}),
    (update_node, None, {}),
    (record_draft, None, {}),
    (set_design_check, None, {}),
    (get_design_principles, None, {"area": AREAS}),
)


def _type(annotation: Any) -> str:
    """``:int``, ``:a|b``, ``:[...]`` or ``:{...}`` after a name; empty for a plain string."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin in (typing.Union, types.UnionType):
        real = [a for a in args if a is not type(None)]
        if all(typing.get_origin(a) is Literal for a in real):
            return ":" + "|".join(str(v) for a in real for v in typing.get_args(a))
        return _type(real[0]) if len(real) == 1 else ""
    if origin is Literal:
        return ":" + "|".join(str(v) for v in args)
    if origin is list:
        item = args[0] if args else Any
        if isinstance(item, type) and issubclass(item, BaseModel):
            return f":[{_model(item)}]"
        inner = _type(item)
        return f":[{inner[1:] or 'str'}]"
    if origin is dict or annotation is dict:
        return ":{}"
    if annotation in (int, float):
        return f":{annotation.__name__}"
    return ""


def _model(model: type[BaseModel]) -> str:
    fields = [
        name + ("" if info.is_required() else "?") + _type(info.annotation)
        for name, info in model.model_fields.items()
    ]
    return "{" + ", ".join(fields) + "}"


def _shape(
    tool: Callable[..., Any], items: type[BaseModel] | None, values: dict[str, tuple[str, ...]]
) -> str:
    hints = typing.get_type_hints(tool)
    parts = []
    for param in inspect.signature(tool).parameters.values():
        if param.name in _PROJECT_ARGS:
            continue
        annotation = hints[param.name]
        if items is not None and param.name in items.model_fields:
            annotation = items.model_fields[param.name].annotation
        kind = ":" + "|".join(values[param.name]) if param.name in values else _type(annotation)
        optional = "" if param.default is inspect.Parameter.empty else "?"
        parts.append(f"{param.name}{optional}{kind}")
    return f"- {tool.__name__}({{{', '.join(parts)}}})"


def tool_shapes() -> str:
    """One line per tool, after a line naming the shared project arguments."""
    without = [
        tool.__name__
        for tool, _, _ in _TOOLS
        if not set(_PROJECT_ARGS) <= set(inspect.signature(tool).parameters)
    ]
    head = (
        f"Arguments (pass only these; ? = optional). Every tool but {', '.join(without)} "
        "also takes project_path, project_id:"
    )
    return "\n".join([head, *(_shape(*entry) for entry in _TOOLS)])
