"""Chat Layer-3 framing delivered as an authoritative system prompt (Lever 2).

The per-canvas framing used to be glued into the *user message*, where the
model reads it as "part of the conversation" rather than a binding instruction
— so it drifted and the agent invented project facts (context starvation, see
``docs/idea/chat/00-problem.md``). Lever 2 moves the framing into a real system
prompt and adds a constant hallucination guard ("ground every claim in the
provided context / read the canvas, never invent"). Providers map it per CLI:
claude has a native ``--append-system-prompt`` flag; codex (whose ``exec`` takes
the prompt as a positional arg with no system-prompt flag) falls back to
prepending it to the message.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.chat_context import (
    COACH_TONE,
    HALLUCINATION_GUARD,
    WRITE_PLAYBOOK,
    build_framing_preamble,
    build_system_prompt,
)
from mashbill.chat_providers.claude_code import ClaudeCodeProvider
from mashbill.chat_providers.codex import CodexProvider

# --- per-canvas coaching playbooks (Phase 3, sourced from ----------------
# --- docs/concepts/ai-collaboration.md §2) -------------------------------


def test_foundation_framing_runs_the_essence_interview() -> None:
    f = build_framing_preamble("foundation").lower()
    assert "discovery" in f
    for signal in ("mission", "core value", "identity", "trade-off"):
        assert signal in f, signal


def test_actors_framing_covers_role_families_and_actor_not_person() -> None:
    f = build_framing_preamble("actors").lower()
    assert "planning" in f
    assert "role" in f
    assert "not a person" in f or "not a persona" in f  # actor ≠ persona
    assert "benefit" in f  # one of the three role families


def test_services_framing_uses_five_slots_and_jtbd() -> None:
    f = build_framing_preamble("services").lower()
    assert "planning" in f
    assert "five" in f or "5" in f  # the 5 inspector slots
    assert "without it" in f  # JTBD: ask what's frustrating without it, not 'why'
    assert "promotion" in f  # the feature→service promotion test


def test_feature_framing_is_happy_path_first_with_altitude_guard() -> None:
    f = build_framing_preamble("feature:svc1").lower()
    assert "execution" in f
    assert "happy path" in f
    assert "build agent" in f  # altitude guard hands implementation to the build agent


def test_entities_framing_enforces_identity_dedup() -> None:
    f = build_framing_preamble("entities").lower()
    # match by identity, not name (글=게시물=포스트 collapse; 글≠댓글 stay)
    assert "identity" in f and "name" in f
    assert "summary" in f
    assert "never" in f  # never finalise silently / never auto-scan


def test_system_prompt_includes_coach_tone_on_canvas_scopes() -> None:
    sp = build_system_prompt("foundation")
    assert COACH_TONE in sp
    assert HALLUCINATION_GUARD in sp


def test_system_prompt_project_scope_has_guard_only_no_tone() -> None:
    sp = build_system_prompt("project")
    assert HALLUCINATION_GUARD in sp
    assert COACH_TONE not in sp  # tone is for canvas coaching, not cross-canvas


def test_write_playbook_present_on_canvas_scopes(tmp_path: Path) -> None:
    # D-2026-06-26-D: on a canvas scope the coach must know to SAVE a confirmed
    # value into the selected node (close the load-bearing gap), gated on an
    # explicit yes, and to ask when the target is ambiguous.
    sp = build_system_prompt("foundation")
    assert WRITE_PLAYBOOK in sp
    low = sp.lower()
    assert "update_node" in low  # the write tool is named
    assert "confirm" in low  # gated on explicit confirmation
    assert "ask which" in low or "several nodes" in low  # empty/multi-select → ask


def test_write_playbook_has_create_branch(tmp_path: Path) -> None:
    # D-2026-06-27-B: the coach ADDS a genuinely-new node via create_node — gated on
    # the same explicit confirmation as filling (propose first, create on the yes),
    # never by rewriting the whole canvas.
    sp = build_system_prompt("foundation")
    low = sp.lower()
    assert "create_node" in low  # the add tool is named
    assert "new" in low  # adding is scoped to something genuinely new
    # gated: propose before creating, never silently
    assert "propose" in low or "shall i add" in low or "만들까요" in sp


def test_write_playbook_absent_on_project_scope() -> None:
    # Cross-canvas project scope has no single selected target → no write playbook
    # (mirrors COACH_TONE being canvas-only).
    sp = build_system_prompt("project")
    assert WRITE_PLAYBOOK not in sp
    assert "update_node" not in sp.lower()


def test_guard_keeps_read_ask_machinery_silent() -> None:
    # Regression (D-2026-06-24-J): the in-app coach narrated its plumbing — "the
    # tool call was cancelled, I couldn't read the body, here's what I'm certain
    # of". The guard must instruct it to keep that machinery out of sight, and the
    # rule is universal (present even on the cross-canvas ``project`` scope).
    for scope in ("foundation", "project"):
        g = build_system_prompt(scope).lower()
        assert "narrate" in g, scope  # never narrate tools / a read that didn't land
        assert "fresh start" in g, scope  # empty canvas = invite, not a gap to announce


def test_coach_tone_keeps_warmth_light_not_stacked() -> None:
    # Regression (D-2026-06-24-J): the coach piled reassurance on reassurance into
    # a wall. The tone principle: warmth is one light touch led by the question,
    # not stacked caveats. Canvas scopes only (tone is absent from ``project``).
    t = build_system_prompt("foundation").lower()
    assert "warmth" in t
    assert "reassurance" in t  # "don't pile reassurance on reassurance"


# --- build_system_prompt (chat_context SSOT) -------------------------------


def test_system_prompt_includes_guard_and_framing_for_a_canvas() -> None:
    sp = build_system_prompt("foundation")
    assert HALLUCINATION_GUARD in sp
    assert build_framing_preamble("foundation") in sp


def test_system_prompt_is_guard_only_for_project_scope() -> None:
    # ``project`` is cross-canvas — no per-canvas framing — but the guard
    # (read, don't invent) is universal and must still be present.
    sp = build_system_prompt("project")
    assert HALLUCINATION_GUARD in sp
    assert build_framing_preamble("project") == ""


def test_system_prompt_uses_base_scope_for_parametric_feature() -> None:
    assert build_framing_preamble("feature:x") in build_system_prompt("feature:x")


# --- claude: native --append-system-prompt flag ----------------------------


def test_claude_command_carries_system_prompt_as_flag(tmp_path: Path) -> None:
    p = ClaudeCodeProvider(workspace_root=tmp_path)
    p.set_system_prompt("BE GROUNDED")
    cmd = p._build_command("fix this")
    assert "--append-system-prompt" in cmd
    assert cmd[cmd.index("--append-system-prompt") + 1] == "BE GROUNDED"
    # The system text must NOT leak into the user message (the last arg).
    assert cmd[-1] == "fix this"


def test_claude_command_omits_system_prompt_flag_when_unset(tmp_path: Path) -> None:
    p = ClaudeCodeProvider(workspace_root=tmp_path)
    assert "--append-system-prompt" not in p._build_command("hi")


def test_claude_attaches_own_mashbill_strictly(tmp_path: Path) -> None:
    # D-2026-06-26-E: the coach must carry THIS build's Novel tools directly, not
    # inherit a drift-prone global registration. So the command injects an
    # --mcp-config naming the mashbill server AND --strict-mcp-config to ignore all
    # other MCP sources (incl. a stale ~/.claude.json mashbill entry).
    import json

    p = ClaudeCodeProvider(workspace_root=tmp_path)
    cmd = p._build_command("hi")
    assert "--strict-mcp-config" in cmd
    assert "--mcp-config" in cmd
    cfg = json.loads(Path(cmd[cmd.index("--mcp-config") + 1]).read_text(encoding="utf-8"))
    assert "mashbill" in cfg["mcpServers"]  # the engine's own stdio Novel server
    assert cmd[-1] == "hi"  # user message still trails


# --- codex: no system-prompt flag → prepend to the message -----------------


def test_codex_prepends_system_prompt_to_message(tmp_path: Path) -> None:
    p = CodexProvider(workspace_root=tmp_path)
    p.set_system_prompt("BE GROUNDED")
    cmd = p._build_command("fix this")
    # codex exec takes the prompt as the trailing positional arg; the system
    # text rides in front of the user's message.
    assert cmd[-1].startswith("BE GROUNDED")
    assert "fix this" in cmd[-1]
    # No claude-style flag.
    assert "--append-system-prompt" not in cmd


def test_codex_message_unchanged_when_system_prompt_unset(tmp_path: Path) -> None:
    p = CodexProvider(workspace_root=tmp_path)
    assert p._build_command("hi")[-1] == "hi"
