"""Engine version is a single source of truth (Phase D, D-2026-06-20-N).

Before this, the engine version was scattered across four stale copies:
``pyproject.toml`` (0.1.0), ``mashbill/__init__.py`` (0.1.0),
``schema_export.MASHBILL_VERSION`` (0.14.18), and ``.claude-plugin/plugin.json``
(the only one that actually moved). This pins the unification:

  - ``mashbill/__init__.py::__version__`` is THE source. ``pyproject`` derives
    it dynamically (hatchling), and ``MASHBILL_VERSION`` re-exports it.
  - the Claude Code plugin manifest is a separate artifact but must match —
    Gate 4 bumps both ``__init__`` + ``plugin.json`` in lock-step.

``SCHEMA_VERSION`` is a DIFFERENT concept (the wire-contract schema version,
the thing the runtime compat banner gates on) and is intentionally NOT tied to
the package version — this file documents that separation too.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from mashbill import __version__
from mashbill.schema_export import MASHBILL_VERSION, SCHEMA_VERSION

_MASHBILL_ROOT = Path(__file__).resolve().parent.parent


def test_plot_version_re_exports_package_version() -> None:
    assert MASHBILL_VERSION == __version__


def test_plugin_manifest_matches_package_version() -> None:
    manifest = json.loads((_MASHBILL_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))
    assert manifest["version"] == __version__, (
        "plugin.json version drifted from mashbill.__version__ — Gate 4 must "
        "bump both in lock-step."
    )


def test_pyproject_derives_version_dynamically_from_init() -> None:
    """No static ``version =`` in ``[project]``; hatchling reads ``__init__``."""
    pp = tomllib.loads((_MASHBILL_ROOT / "pyproject.toml").read_text("utf-8"))
    assert "version" not in pp["project"], "pyproject must not pin a static version"
    assert "version" in pp["project"].get("dynamic", [])
    assert pp["tool"]["hatch"]["version"]["path"] == "mashbill/__init__.py"


def test_schema_version_is_separate_from_package_version() -> None:
    """The wire schema version is an int, decoupled from the package semver."""
    assert isinstance(SCHEMA_VERSION, int)
    assert str(SCHEMA_VERSION) != __version__
