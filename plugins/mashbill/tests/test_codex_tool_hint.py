"""W-00000450 — the Codex coach is told how to call the Mashbill tools.

Codex runs the coach in code mode: it calls MCP tools from a small script and
had to look up each tool's shape first (32 of 121 model round trips in the
newcomer walk, about 8 s each). Telling it the call shape up front removed
those lookups (docs/research/coach-codemode/README.md).
"""

from __future__ import annotations

import inspect
import re
import typing
from pathlib import Path

import pytest

from mashbill.chat_providers.codex import CODEX_TOOL_HINT, CODEX_TOOL_HINT_ENV, CodexProvider


def _message(tmp_path: Path) -> str:
    p = CodexProvider(workspace_root=tmp_path)
    p.set_system_prompt("SYSTEM")
    return p._build_command("미션이 뭐야?")[-1]


def test_codex_coach_turn_carries_the_tool_call_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CODEX_TOOL_HINT_ENV, raising=False)
    msg = _message(tmp_path)
    assert CODEX_TOOL_HINT in msg
    assert "await tools.mcp__mashbill__" in CODEX_TOOL_HINT
    # system prompt first, then the hint, then the person's message
    assert msg.index("SYSTEM") < msg.index(CODEX_TOOL_HINT) < msg.index("미션이 뭐야?")


def test_tool_hint_can_be_switched_off_for_experiments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(CODEX_TOOL_HINT_ENV, "0")
    assert CODEX_TOOL_HINT not in _message(tmp_path)


def test_a_turn_without_a_system_prompt_gets_no_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(CODEX_TOOL_HINT_ENV, raising=False)
    p = CodexProvider(workspace_root=tmp_path)
    assert p._build_command("hi")[-1] == "hi"


# W-00000464 — newcomer walk 2: the hint said "use the argument names shown in
# this prompt" but no turn input showed them. Five of seven propose_flow calls
# failed on shape (a ``flow`` wrapper, ``id`` for ``key``, ``from``/``to`` for
# ``source``/``target``, open items as strings or without ``at``), and
# set_design_check got ``status`` and ``canvas_kind``.
_SHAPED = (
    "propose_flow",
    "draw_proposed_flow",
    "create_node",
    "create_edge",
    "update_node",
    "record_draft",
    "set_design_check",
    "get_design_principles",
)


def _shape_line(name: str) -> str:
    lines = [line for line in CODEX_TOOL_HINT.splitlines() if line.startswith(f"- {name}(")]
    assert len(lines) == 1, f"{name} has no argument shape in the Codex hint"
    return lines[0]


def _required(fn: object) -> list[str]:
    params = inspect.signature(fn).parameters.values()  # type: ignore[arg-type]
    return [p.name for p in params if p.default is inspect.Parameter.empty]


@pytest.mark.parametrize("name", _SHAPED)
def test_hint_shows_each_tool_and_its_required_arguments(name: str) -> None:
    from mashbill import mcp_tools

    line = _shape_line(name)
    for arg in _required(getattr(mcp_tools, name)):
        if arg in ("project_path", "project_id"):
            assert "project_path" in CODEX_TOOL_HINT and "project_id" in CODEX_TOOL_HINT
            continue
        assert re.search(rf"\b{arg}\b", line), f"{name}: {arg!r} missing from {line!r}"


def test_propose_flow_shape_names_each_item_field() -> None:
    from mashbill.flow_proposal import FlowProposal

    line = _shape_line("propose_flow")
    for field in ("nodes", "edges", "open_items", "omitted", "relabels", "remove_edges", "placed"):
        annotation = FlowProposal.model_fields[field].annotation
        (item_model,) = typing.get_args(annotation)
        for name, info in item_model.model_fields.items():
            if info.is_required():
                assert re.search(rf"\b{name}\b", line), f"{field}: {name!r} missing"
    # the exact names the walk got wrong
    assert "{key, kind:step|decision|rule|note, label" in line
    assert "edges?:[{source, target, label?}]" in line
    assert "open_items?:[{at, question}]" in line
    assert "chat_scope" not in line


def test_set_design_check_shape_shows_state_values() -> None:
    line = _shape_line("set_design_check")
    assert "state:checking|checked" in line
    assert "status" not in line and "canvas_kind" not in line


def test_get_design_principles_shape_lists_the_areas() -> None:
    from mashbill.coaching_principles import AREAS

    line = _shape_line("get_design_principles")
    for area in AREAS:
        assert area in line


def test_tool_hint_stays_short() -> None:
    """It rides on every Codex turn, outside the shared prompt word budget."""
    assert len(CODEX_TOOL_HINT.split()) <= 200
