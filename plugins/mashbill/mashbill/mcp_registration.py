"""Track 2.5 / D-2026-06-11-E — mashbill MCP registration in external CLI configs.

Each supported external CLI (Claude Code / Codex / Gemini) keeps its MCP
server list in a known location with a known schema. This module reads /
writes a `plot` entry in each, leaving every sibling entry alone:

  Claude Code → ``~/.claude.json`` (JSON)         ``mcpServers.plot``
  Codex       → ``~/.codex/config.toml`` (TOML)   ``[mcp_servers.mashbill]``
  Gemini      → ``~/.gemini/settings.json``       ``mcpServers.plot``

The Novel entry points the CLI at a freshly-spawned ``mashbill`` instance
via ``uv run`` so the user gets a stdio MCP server they can call from the
CLI's own tool surface. The Novel desktop app's own running sidecar is
independent — that's an HTTP server inside the app, not the stdio one the
CLI talks to.

The R7 native chat panel (D-2026-06-11-E) drives provider detection and
registration through ``/api/mcp/*`` endpoints; this module is provider-
neutral so the panel only needs one code path.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import tomli_w

# gemini (agy) chat transport temporarily removed 2026-06-23 — re-add in October
# (untestable for now, user direction). The provider impl lives in git history
# (chat_providers/gemini.py + the agy model branch); restore the literal + the
# _PROVIDERS entry + GeminiProvider wiring to bring it back.
ProviderName = Literal["claude-code", "codex"]

_MASHBILL_SERVER_NAME = "mashbill"


@dataclass(frozen=True)
class _ProviderSpec:
    """Where a provider's config lives + which CLI binary to look for."""

    name: ProviderName
    cli_command: str
    config_relative: tuple[str, ...]
    config_format: Literal["json", "toml"]
    servers_path: tuple[str, ...]
    # Extra keys to attach on the Novel entry (Claude Code wants `"type": "stdio"`).
    extra_entry_keys: dict[str, Any]


_PROVIDERS: dict[ProviderName, _ProviderSpec] = {
    "claude-code": _ProviderSpec(
        name="claude-code",
        cli_command="claude",
        config_relative=(".claude.json",),
        config_format="json",
        servers_path=("mcpServers",),
        extra_entry_keys={"type": "stdio"},
    ),
    "codex": _ProviderSpec(
        name="codex",
        cli_command="codex",
        config_relative=(".codex", "config.toml"),
        config_format="toml",
        servers_path=("mcp_servers",),
        extra_entry_keys={},
    ),
}


@dataclass(frozen=True)
class ProviderStatus:
    """Snapshot of one provider — used by the viewer's chat panel to decide
    what to render (install hint / register button / unregister button)."""

    name: ProviderName
    installed: bool
    registered: bool
    config_path: str


# ---------------------------------------------------------------------------
# spec resolution
# ---------------------------------------------------------------------------


def _spec_for(provider: ProviderName) -> _ProviderSpec:
    if provider not in _PROVIDERS:
        raise KeyError(f"unknown provider: {provider!r}")
    return _PROVIDERS[provider]


def _config_path(spec: _ProviderSpec) -> Path:
    return Path.home().joinpath(*spec.config_relative)


def _plot_entry(plugin_root: Path, spec: _ProviderSpec) -> dict[str, Any]:
    """Build the Novel mcp-server entry for one provider.

    Two shapes (D-2026-06-14-A):

    * **dev checkout** — ``uv run --directory <src> python -m mashbill``. The
      source tree is a real uv project, so this gives a stdio MCP server.
    * **frozen .app** — ``<bundled binary> --mcp-stdio``. Under PyInstaller,
      ``plugin_root`` would resolve to the ephemeral ``_MEIxxxx`` extraction
      dir (deleted on app exit, not a uv project), so ``uv run`` there times
      out. ``sys.executable`` is the stable bundled binary path inside the
      ``.app``; ``--mcp-stdio`` selects its stdio-MCP mode.
    """
    if getattr(sys, "frozen", False):
        entry: dict[str, Any] = {
            "command": sys.executable,
            "args": ["--mcp-stdio"],
            "env": {},
        }
    else:
        entry = {
            "command": "uv",
            "args": [
                "run",
                "--directory",
                str(plugin_root),
                "python",
                "-m",
                "mashbill",
                # stdio-only, like the frozen entry: a registered tool server
                # must never race the real engine for the HTTP port (B-11).
                "--mcp-stdio",
            ],
            "env": {},
        }
    entry.update(spec.extra_entry_keys)
    return entry


# ---------------------------------------------------------------------------
# config IO
# ---------------------------------------------------------------------------


def _read_config(spec: _ProviderSpec) -> dict[str, Any]:
    path = _config_path(spec)
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    if spec.config_format == "json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    else:
        try:
            data = tomllib.loads(raw)
        except tomllib.TOMLDecodeError:
            return {}
    return cast(dict[str, Any], data) if isinstance(data, dict) else {}


def _write_config(spec: _ProviderSpec, data: dict[str, Any]) -> None:
    path = _config_path(spec)
    path.parent.mkdir(parents=True, exist_ok=True)
    if spec.config_format == "json":
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    else:
        # tomli_w.dumps preserves dict key order; we pass through the same
        # structure we read so sibling entries stay where they were.
        path.write_text(tomli_w.dumps(data), encoding="utf-8")


def _servers_dict(data: dict[str, Any], spec: _ProviderSpec) -> dict[str, Any]:
    """Walk into the servers dict, creating empty containers on the way."""
    node: dict[str, Any] = data
    for key in spec.servers_path:
        sub = node.get(key)
        if not isinstance(sub, dict):
            sub = {}
            node[key] = sub
        node = sub
    return node


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


def detect_providers() -> dict[ProviderName, ProviderStatus]:
    """Inspect every provider: is the CLI on PATH? is Novel already registered?

    The result is keyed by provider name so the viewer can render one row
    per provider regardless of install state.
    """
    out: dict[ProviderName, ProviderStatus] = {}
    for name, spec in _PROVIDERS.items():
        out[name] = ProviderStatus(
            name=name,
            installed=shutil.which(spec.cli_command) is not None,
            registered=is_plot_registered(name),
            config_path=str(_config_path(spec)),
        )
    return out


def is_plot_registered(provider: ProviderName) -> bool:
    """True iff the provider's config carries a ``plot`` MCP server entry."""
    spec = _spec_for(provider)
    data = _read_config(spec)
    if not data:
        return False
    node: Any = data
    for key in spec.servers_path:
        if not isinstance(node, dict):
            return False
        node = node.get(key)
        if node is None:
            return False
    return isinstance(node, dict) and _MASHBILL_SERVER_NAME in node


def register_plot(provider: ProviderName, plugin_root: Path) -> None:
    """Add (or update) the mashbill MCP server entry in ``provider``'s config.

    Idempotent: a second call with the same ``plugin_root`` is a byte-for-byte
    no-op write. Sibling MCP server entries (e.g. ``pencil``) and unrelated
    top-level keys are preserved.
    """
    spec = _spec_for(provider)
    data = _read_config(spec)
    servers = _servers_dict(data, spec)
    servers[_MASHBILL_SERVER_NAME] = _plot_entry(plugin_root, spec)
    _write_config(spec, data)


def mashbill_config(plugin_root: Path | None = None) -> dict[str, Any]:
    """``--mcp-config`` payload that attaches the Novel stdio MCP server directly
    to an in-app CLI turn (D-2026-06-26-E).

    The in-app coach used to inherit the ``plot`` server from the user's GLOBAL
    registration (``~/.claude.json``). That pointer drifts — it can name a
    deleted / older app build, silently leaving the coach with no canvas tools
    (the "in-app chat can't write to the canvas" failure). Passing this payload
    via ``--mcp-config`` + ``--strict-mcp-config`` makes the coach always carry
    *this* engine's own Novel tools, regardless of (and ignoring) the global
    registration. Reuses the same frozen/dev command resolution as
    :func:`register_plot`, so the spawned stdio server is the running build.
    """
    root = plugin_root or plot_plugin_root()
    return {"mcpServers": {_MASHBILL_SERVER_NAME: _plot_entry(root, _spec_for("claude-code"))}}


def unregister_plot(provider: ProviderName) -> None:
    """Remove the mashbill MCP server entry from ``provider``'s config.

    No-op when the entry (or the whole config) is absent. Sibling entries
    are preserved; the surrounding container is left in place even if it
    becomes empty (so a re-register doesn't have to rebuild scaffolding).
    """
    spec = _spec_for(provider)
    data = _read_config(spec)
    if not data:
        return
    node: Any = data
    for key in spec.servers_path:
        if not isinstance(node, dict):
            return
        node = node.get(key)
        if node is None:
            return
    if isinstance(node, dict) and _MASHBILL_SERVER_NAME in node:
        del node[_MASHBILL_SERVER_NAME]
        _write_config(spec, data)


def plot_plugin_root() -> Path:
    """Return the plugin root that ``register_plot`` should default to.

    The runtime override is the ``CLAUDE_PLUGIN_ROOT`` env var (Claude Code
    sets this when invoking plugin tools). Otherwise we walk up from this
    module's directory until we find ``mashbill/``'s parent — i.e. the
    package's source root, which is what ``uv run --directory`` wants.
    """
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    # mashbill/mcp_registration.py → mashbill/ → <plugin_root>/
    return Path(__file__).resolve().parent.parent
