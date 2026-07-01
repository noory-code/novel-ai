"""Track 2.5 / D-2026-06-11-E — mashbill MCP registration in external CLI configs.

Pins the contract for each provider (Claude Code / Codex / Gemini):
  - detect: which CLIs are on $PATH + which already have Novel registered
  - register: idempotent add of a Novel mcp server entry
  - unregister: drop the Novel entry, leave sibling entries alone

The test isolates ``$HOME`` via monkeypatch so the real user config files
are never touched.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from mashbill.mcp_registration import (
    ProviderName,
    detect_providers,
    is_plot_registered,
    register_plot,
    unregister_plot,
)


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    return tmp_path


@pytest.fixture
def plugin_root(tmp_path: Path) -> Path:
    """A pretend plugin root the MCP entry will point at."""
    root = tmp_path / "noory-ai" / "mashbill"
    root.mkdir(parents=True)
    return root


def _ensure_cli(home: Path, name: str) -> None:
    """Pretend the CLI exists by dropping a stub on PATH (~/.bin)."""
    bin_dir = home / ".bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / name).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (bin_dir / name).chmod(0o755)


# ---------------------------------------------------------------------------
# detection
# ---------------------------------------------------------------------------


def test_detect_reports_missing_when_cli_absent(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/nonexistent")
    statuses = detect_providers()
    for name in ("claude-code", "codex"):
        assert statuses[name].installed is False
        assert statuses[name].registered is False


def test_detect_reports_installed_when_cli_on_path(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bin_dir = fake_home / ".bin"
    bin_dir.mkdir(exist_ok=True)
    for cli in ("claude", "codex"):
        _ensure_cli(fake_home, cli)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin")
    statuses = detect_providers()
    for name in ("claude-code", "codex"):
        assert statuses[name].installed is True
        # Nothing registered yet.
        assert statuses[name].registered is False


# ---------------------------------------------------------------------------
# Claude Code (~/.claude.json)
# ---------------------------------------------------------------------------


def test_register_claude_code_creates_config_when_missing(
    fake_home: Path, plugin_root: Path
) -> None:
    register_plot("claude-code", plugin_root)
    cfg = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    plot = cfg["mcpServers"]["mashbill"]
    assert plot["command"] == "uv"
    assert "args" in plot and isinstance(plot["args"], list)
    assert str(plugin_root) in plot["args"]
    assert plot.get("type") == "stdio"


def test_register_claude_code_preserves_sibling_entries(
    fake_home: Path, plugin_root: Path
) -> None:
    (fake_home / ".claude.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "pencil": {"command": "/usr/local/bin/pencil-mcp"},
                },
                "otherTopLevel": True,
            }
        ),
        encoding="utf-8",
    )
    register_plot("claude-code", plugin_root)
    cfg = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    assert cfg["mcpServers"]["pencil"]["command"] == "/usr/local/bin/pencil-mcp"
    assert cfg["mcpServers"]["mashbill"]["command"] == "uv"
    assert cfg["otherTopLevel"] is True


def test_register_claude_code_is_idempotent(
    fake_home: Path, plugin_root: Path
) -> None:
    register_plot("claude-code", plugin_root)
    first = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    register_plot("claude-code", plugin_root)
    second = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    assert first == second


def test_unregister_claude_code_removes_plot_only(
    fake_home: Path, plugin_root: Path
) -> None:
    (fake_home / ".claude.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "pencil": {"command": "/usr/local/bin/pencil-mcp"},
                    "mashbill": {"command": "uv", "args": ["..."]},
                },
            }
        ),
        encoding="utf-8",
    )
    unregister_plot("claude-code")
    cfg = json.loads((fake_home / ".claude.json").read_text(encoding="utf-8"))
    assert "mashbill" not in cfg["mcpServers"]
    assert "pencil" in cfg["mcpServers"]


# ---------------------------------------------------------------------------
# Codex (~/.codex/config.toml)
# ---------------------------------------------------------------------------


def test_register_codex_creates_config_when_missing(
    fake_home: Path, plugin_root: Path
) -> None:
    register_plot("codex", plugin_root)
    cfg_path = fake_home / ".codex" / "config.toml"
    assert cfg_path.is_file()
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    plot = cfg["mcp_servers"]["mashbill"]
    assert plot["command"] == "uv"
    assert isinstance(plot["args"], list)
    assert str(plugin_root) in plot["args"]


def test_register_codex_preserves_sibling_server_entries(
    fake_home: Path, plugin_root: Path
) -> None:
    cfg_path = fake_home / ".codex" / "config.toml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(
        '[mcp_servers.pencil]\ncommand = "/usr/local/bin/pencil-mcp"\nargs = []\n',
        encoding="utf-8",
    )
    register_plot("codex", plugin_root)
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["mcp_servers"]["pencil"]["command"] == "/usr/local/bin/pencil-mcp"
    assert cfg["mcp_servers"]["mashbill"]["command"] == "uv"


def test_register_codex_is_idempotent(fake_home: Path, plugin_root: Path) -> None:
    register_plot("codex", plugin_root)
    first = (fake_home / ".codex" / "config.toml").read_text(encoding="utf-8")
    register_plot("codex", plugin_root)
    second = (fake_home / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert first == second


def test_unregister_codex_removes_plot_only(
    fake_home: Path, plugin_root: Path
) -> None:
    cfg_path = fake_home / ".codex" / "config.toml"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(
        '[mcp_servers.pencil]\ncommand = "/usr/local/bin/pencil-mcp"\nargs = []\n'
        '\n[mcp_servers.plot]\ncommand = "uv"\nargs = ["x"]\n',
        encoding="utf-8",
    )
    unregister_plot("codex")
    cfg = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    assert "mashbill" not in cfg.get("mcp_servers", {})
    assert "pencil" in cfg["mcp_servers"]


# ---------------------------------------------------------------------------
# is_plot_registered — used by detect
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("provider", ["claude-code", "codex"])
def test_is_plot_registered_false_when_no_config(
    fake_home: Path, provider: ProviderName
) -> None:
    assert is_plot_registered(provider) is False


@pytest.mark.parametrize("provider", ["claude-code", "codex"])
def test_is_plot_registered_true_after_register(
    fake_home: Path, plugin_root: Path, provider: ProviderName
) -> None:
    register_plot(provider, plugin_root)
    assert is_plot_registered(provider) is True


@pytest.mark.parametrize("provider", ["claude-code", "codex"])
def test_is_plot_registered_false_after_unregister(
    fake_home: Path, plugin_root: Path, provider: ProviderName
) -> None:
    register_plot(provider, plugin_root)
    unregister_plot(provider)
    assert is_plot_registered(provider) is False


def test_unknown_provider_raises(fake_home: Path, plugin_root: Path) -> None:
    with pytest.raises(KeyError):
        register_plot("notarealcli", plugin_root)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# frozen (bundled .app) registration — D-2026-06-14-A
# ---------------------------------------------------------------------------
#
# In a dev checkout the MCP entry is ``uv run --directory <src> python -m
# mashbill``. Inside the PyInstaller-frozen .app that command is broken: the
# plugin root resolves to the ephemeral ``_MEIxxxx`` extraction dir (gone once
# the app exits, and not a uv project even while alive). When frozen we must
# register a STABLE command instead — the bundled binary itself in stdio-MCP
# mode (``sys.executable --mcp-stdio``).


def test_plot_entry_uses_uv_when_not_frozen(plugin_root: Path) -> None:
    from mashbill.mcp_registration import _plot_entry, _spec_for

    entry = _plot_entry(plugin_root, _spec_for("codex"))
    assert entry["command"] == "uv"
    assert "--directory" in entry["args"]
    assert str(plugin_root) in entry["args"]


def test_plot_entry_uses_bundled_binary_when_frozen(
    plugin_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    from mashbill.mcp_registration import _plot_entry, _spec_for

    exe = "/Applications/Novel.app/Contents/MacOS/mashbill"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", exe, raising=False)

    entry = _plot_entry(plugin_root, _spec_for("codex"))
    assert entry["command"] == exe
    assert entry["args"] == ["--mcp-stdio"]
    # The ephemeral plugin root must NOT leak into the frozen command.
    assert "uv" not in entry["command"]
    assert str(plugin_root) not in entry["args"]


def test_register_codex_when_frozen_writes_stable_command(
    fake_home: Path, plugin_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    exe = "/Applications/Novel.app/Contents/MacOS/mashbill"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", exe, raising=False)

    register_plot("codex", plugin_root)
    cfg = tomllib.loads(
        (fake_home / ".codex" / "config.toml").read_text(encoding="utf-8")
    )
    plot = cfg["mcp_servers"]["mashbill"]
    assert plot["command"] == exe
    assert plot["args"] == ["--mcp-stdio"]
