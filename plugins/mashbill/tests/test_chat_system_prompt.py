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

import json
from pathlib import Path

import pytest

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
    assert "helps a person reach that service outcome" in f  # feature/service boundary


def test_feature_framing_is_happy_path_first_with_altitude_guard() -> None:
    f = build_framing_preamble("feature:svc1").lower()
    assert "execution" in f
    assert "main successful sequence" in f
    assert "build agent" in f  # implementation belongs to the build agent
    # A branch must be added when the relevant step is discussed, not at the end.
    assert "add the decision and its branches there" in f
    assert "unfinished" in f


def test_entities_framing_enforces_identity_dedup() -> None:
    f = build_framing_preamble("entities").lower()
    # match by identity, not name (글=게시물=포스트 collapse; 글≠댓글 stay)
    assert "identity" in f and "name" in f
    assert "summary" in f
    assert "never" in f  # never finalise silently / never auto-scan


def test_entity_boundary_is_inlined_for_services_and_entities() -> None:
    for scope in ("services", "entities"):
        prompt = build_system_prompt(scope).lower()
        for rule in (
            "identified separately",
            "state changes independently",
            "embedded value",
            "not one-to-one",
            "build agent",
        ):
            assert rule in prompt, (scope, rule)

    services = build_framing_preamble("services").lower()
    assert "2–5 entities" not in services
    assert "every product entity the service actually needs" in services


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


def test_write_playbook_forbids_announcing_the_save_saliently() -> None:
    # D-2026-07-15-A: the no-announce rule existed but was buried mid-paragraph,
    # so the sonnet coach still opened turns with "저장했어요 / 저장할게요" in a
    # reliable 4-service round (W-67). Pin the rule saliently — the observed
    # variants are named so the coach cannot slip a synonym past it.
    wp = WRITE_PLAYBOOK
    for variant in ("저장했어요", "저장할게요", "저장됐어요", "기록했어요"):
        assert variant in wp, variant
    # The prohibition rides at the top of the playbook (right after the write
    # instruction), not buried after the label rules where it drifted.
    head = wp[:600]
    assert "저장했어요" in head, "no-announce rule must be salient (near the top)"
    # SSOT: the rule states its ONE reason once, not duplicated.
    assert wp.count("the canvas shows") <= 1


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
        assert "do not describe" in g, scope
        assert "tool use" in g and "failed reads" in g, scope
        assert "when a canvas is empty, start the interview" in g, scope


def test_coach_tone_keeps_warmth_light_not_stacked() -> None:
    # Regression (D-2026-06-24-J): the coach piled reassurance on reassurance into
    # a wall. The tone principle: warmth is one light touch led by the question,
    # not stacked caveats. Canvas scopes only (tone is absent from ``project``).
    t = build_system_prompt("foundation").lower()
    assert "ask the question directly" in t
    assert "do not add repeated reassurance" in t


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


def test_codex_attaches_own_mashbill_tools_noninteractively(tmp_path: Path) -> None:
    # D-2026-07-21-B / W-90: the headless coach must carry THIS build's
    # Mashbill stdio server without relying on ~/.codex/config.toml, and it
    # cannot wait for approval because the provider gives it stdin=DEVNULL.
    p = CodexProvider(workspace_root=tmp_path)
    cmd = p._build_command("hi")

    exec_index = cmd.index("exec")
    # ``codex exec`` has no --ask-for-approval; the verified non-interactive
    # escape is the bypass flag, placed AFTER the exec subcommand.
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert cmd.index("--dangerously-bypass-approvals-and-sandbox") > exec_index
    assert "--ignore-user-config" in cmd

    overrides = [cmd[i + 1] for i, arg in enumerate(cmd) if arg == "-c"]
    command_value = next(v for v in overrides if v.startswith("mcp_servers.mashbill.command="))
    args_value = next(v for v in overrides if v.startswith("mcp_servers.mashbill.args="))
    assert json.loads(command_value.split("=", 1)[1]) == "uv"
    mcp_args = json.loads(args_value.split("=", 1)[1])
    assert mcp_args[:3] == ["run", "--directory", str(Path(__file__).parents[1])]
    assert mcp_args[-4:] == ["python", "-m", "mashbill", "--mcp-stdio"]
    assert cmd[-1] == "hi"


def test_codex_hands_the_tool_log_path_to_the_injected_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W-177 — the coach's tool server is a grandchild process (engine → codex →
    server), and whether it inherits our environment is codex's business, not
    ours. State the path explicitly instead of trusting two spawns we do not
    control, or the recording silently covers nothing."""
    monkeypatch.setenv("MASHBILL_TOOL_LOG", str(tmp_path / "tool-calls.jsonl"))
    p = CodexProvider(workspace_root=tmp_path)
    overrides = [
        c[i + 1] for c in [p._build_command("hi")] for i, arg in enumerate(c) if arg == "-c"
    ]
    env_value = next(
        v for v in overrides if v.startswith("mcp_servers.mashbill.env.MASHBILL_TOOL_LOG=")
    )
    assert json.loads(env_value.split("=", 1)[1]) == str(tmp_path / "tool-calls.jsonl")


def test_codex_says_nothing_about_the_tool_log_when_no_run_asked_for_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Recording is a simulator concern. A user's own session must not carry a
    stray override."""
    monkeypatch.delenv("MASHBILL_TOOL_LOG", raising=False)
    p = CodexProvider(workspace_root=tmp_path)
    cmd = p._build_command("hi")
    assert not any("MASHBILL_TOOL_LOG" in str(arg) for arg in cmd)


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
