"""Chat model selection (D-2026-06-16-C).

Every CLI provider accepts ``--model`` (verified against the installed
``claude`` / ``codex`` / ``gemini`` CLIs). The persisted selection carries an
optional ``model``; the send endpoint applies it to the cached provider via
``set_model`` before each turn, and each provider splices ``--model <value>``
into its argv when set.
"""

from __future__ import annotations

from pathlib import Path

from mashbill.chat_provider import (
    ChatProviderSelection,
    read_selection,
    write_selection,
)
from mashbill.chat_providers.claude_code import ClaudeCodeProvider
from mashbill.chat_providers.codex import CodexProvider


def test_selection_roundtrips_model(tmp_path: Path) -> None:
    write_selection(tmp_path, ChatProviderSelection(provider="codex", model="o3"))
    back = read_selection(tmp_path)
    assert back.provider == "codex"
    assert back.model == "o3"


def test_selection_model_defaults_none(tmp_path: Path) -> None:
    write_selection(tmp_path, ChatProviderSelection(provider="codex"))
    assert read_selection(tmp_path).model is None


def test_codex_command_includes_model_when_set(tmp_path: Path) -> None:
    p = CodexProvider(workspace_root=tmp_path)
    p.set_model("o3")
    cmd = p._build_command("hi")
    assert "--model" in cmd
    assert "o3" in cmd
    # message is still the last arg.
    assert cmd[-1] == "hi"


def test_codex_command_omits_model_when_unset(tmp_path: Path) -> None:
    p = CodexProvider(workspace_root=tmp_path)
    assert "--model" not in p._build_command("hi")


def test_codex_composite_model_splits_into_model_and_effort(tmp_path: Path) -> None:
    # D-2026-06-22-C: a "<slug>:<effort>" selection → --model <slug>
    # -c model_reasoning_effort=<effort>.
    p = CodexProvider(workspace_root=tmp_path)
    p.set_model("gpt-5.5:high")
    cmd = p._build_command("hi")
    assert cmd[cmd.index("--model") + 1] == "gpt-5.5"
    assert "-c" in cmd
    assert "model_reasoning_effort=high" in cmd
    assert cmd[-1] == "hi"


def test_codex_bare_model_has_no_effort_flag(tmp_path: Path) -> None:
    # A plain slug (no ":effort") stays a bare --model with no -c override.
    p = CodexProvider(workspace_root=tmp_path)
    p.set_model("gpt-5.5")
    cmd = p._build_command("hi")
    assert cmd[cmd.index("--model") + 1] == "gpt-5.5"
    assert "model_reasoning_effort" not in " ".join(cmd)


def test_codex_unknown_suffix_is_not_treated_as_effort(tmp_path: Path) -> None:
    # A colon with a non-effort suffix is passed through verbatim as the model.
    p = CodexProvider(workspace_root=tmp_path)
    p.set_model("some:thing")
    cmd = p._build_command("hi")
    assert cmd[cmd.index("--model") + 1] == "some:thing"
    assert "model_reasoning_effort" not in " ".join(cmd)


def test_claude_command_includes_model_when_set(tmp_path: Path) -> None:
    p = ClaudeCodeProvider(workspace_root=tmp_path)
    p.set_model("opus")
    cmd = p._build_command("hi")
    assert "--model" in cmd
    assert "opus" in cmd
    assert cmd[-1] == "hi"


def test_set_model_empty_string_is_treated_as_unset(tmp_path: Path) -> None:
    p = CodexProvider(workspace_root=tmp_path)
    p.set_model("")
    assert "--model" not in p._build_command("hi")
