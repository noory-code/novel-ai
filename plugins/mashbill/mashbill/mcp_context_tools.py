"""Context and coaching-principle functions exposed through the MCP registry."""

from __future__ import annotations

from mashbill.chat_context import build_system_prompt
from mashbill.coaching_principles import get_principles
from mashbill.tool_log import record_tool_call


def get_design_principles(area: str | None = None) -> str:
    """Design-quality discriminator questions for judging content strength
    (D-2026-07-03-O/P). ``area``: mission | values | identity | actors |
    entities | services | features | omitted for all. Consult before challenging
    weak content."""
    record_tool_call("get_design_principles", area=area)
    return get_principles(area)


def get_canvas_framing(scope: str) -> str:
    """The coach's authoritative system framing for a canvas ``scope`` — the
    SAME prompt the in-app coach receives via ``--append-system-prompt``, so a
    headless coach (Claude Code / IDE, running the open engine for free) is
    first-class (D-2026-07-12-A). ``scope``: foundation | actors | services |
    ``service:<id>`` | ``feature:<id>`` | project. Call it for the canvas the
    user is designing, then follow it — it carries the hallucination guard,
    the propose/pace playbooks, and the WRITE gate (confirm before writing;
    never silently auto-generate). One SSOT: delegates to
    :func:`mashbill.chat_context.build_system_prompt`."""
    return build_system_prompt(scope)
