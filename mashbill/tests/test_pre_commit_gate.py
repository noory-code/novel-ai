"""Tests for mashbill/hooks/pre_commit_gate.py — specifically the
``reset_complete_check`` kill-switch added in v0.16.0 (D-2026-05-12-G).

The check enforces four invariants on every commit that touches
viewer or server code:

  1. ``mashbill/models.py`` defines ``SketchNode`` as a discriminated
     union (not a god class).
  2. ``viewer/src/canvases/SketchInspector.tsx`` is absent.
  3. ``viewer/src/canvases/SketchNode.tsx`` is absent.
  4. Zero ``canvas_kind`` branching in ``viewer/src/canvases/sketch/``.

Tests:
  - Pass-case against the real repo (verifies the current tree
    satisfies all four).
  - Skip-case for docs-only commits.
  - Each invariant has an isolated failure-mode test using a tmp_path
    fixture so the negative path is exercised without mutating the
    real working tree.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the hook module from its file path — it lives outside the
# package import path so we wire it in manually.
_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_SPEC = importlib.util.spec_from_file_location(
    "plot_pre_commit_gate", _HOOKS_DIR / "pre_commit_gate.py"
)
assert _SPEC is not None
assert _SPEC.loader is not None
_GATE = importlib.util.module_from_spec(_SPEC)
sys.modules["plot_pre_commit_gate"] = _GATE
_SPEC.loader.exec_module(_GATE)


_MASHBILL_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------
# Pass case — current repo + skip case (docs-only)
# ---------------------------------------------------------------------


def test_reset_complete_against_current_repo() -> None:
    """The current tree should satisfy all four invariants."""
    staged = ["plot/viewer/src/App.tsx"]  # synthetic — any viewer file
    msg = _GATE.reset_complete_check(staged, _MASHBILL_ROOT)
    assert msg is None, f"reset_complete_check unexpectedly failed: {msg}"


def test_reset_complete_skips_docs_only_commit() -> None:
    """Docs-only commits (no viewer / server files) skip the check."""
    staged = [
        "mashbill/docs/SPEC.md",
        "mashbill/docs/DECISIONS.md",
        "mashbill/CHANGELOG.md",
    ]
    assert _GATE.reset_complete_check(staged, _MASHBILL_ROOT) is None


# ---------------------------------------------------------------------
# Failure-mode tests — tmp_path scaffold for each invariant
# ---------------------------------------------------------------------


def _make_minimal_plot_tree(tmp_path: Path) -> Path:
    """Build the minimal directory layout the gate inspects: a
    ``mashbill/`` root with ``viewer/src/canvases/sketch/``,
    ``viewer/src/`` and a ``mashbill/models.py``. All invariants pass
    in the baseline; each test mutates one piece to trigger one failure."""
    root = tmp_path / "plot"
    (root / "viewer" / "src" / "canvases" / "sketch").mkdir(parents=True)
    (root / "viewer" / "src" / "canvases" / "nodes").mkdir()
    (root / "viewer" / "src" / "canvases" / "inspectors").mkdir()
    (root / "mashbill").mkdir()
    # Server-side: union body.
    (root / "mashbill" / "models.py").write_text(
        "from typing import Annotated, Union\nfrom pydantic import Field\n"
        "SketchNode = Annotated[Union[int, str], Field(discriminator='kind')]\n",
        encoding="utf-8",
    )
    # One sketch hook with NO canvas_kind branching (the post-reset state).
    (root / "viewer" / "src" / "canvases" / "sketch" / "useNodesMemo.ts").write_text(
        "// post-reset — no canvas_kind branching here.\nexport const x = 1;\n",
        encoding="utf-8",
    )
    return root


def _staged_viewer() -> list[str]:
    """Pretend a viewer file is staged so the check actually runs."""
    return ["plot/viewer/src/canvases/FoundationCanvas.tsx"]


def test_reset_baseline_tmp_tree_passes(tmp_path: Path) -> None:
    root = _make_minimal_plot_tree(tmp_path)
    assert _GATE.reset_complete_check(_staged_viewer(), root) is None


def test_reset_fails_when_sketchnode_class_returns(tmp_path: Path) -> None:
    root = _make_minimal_plot_tree(tmp_path)
    (root / "mashbill" / "models.py").write_text(
        "class SketchNode:\n    pass\n",  # god class shape, no union
        encoding="utf-8",
    )
    msg = _GATE.reset_complete_check(_staged_viewer(), root)
    assert msg is not None and "15-way discriminated union" in msg


def test_reset_fails_when_god_sketch_inspector_returns(tmp_path: Path) -> None:
    root = _make_minimal_plot_tree(tmp_path)
    (root / "viewer" / "src" / "canvases" / "SketchInspector.tsx").write_text(
        "// re-introduced god component\n", encoding="utf-8"
    )
    msg = _GATE.reset_complete_check(_staged_viewer(), root)
    assert msg is not None and "SketchInspector.tsx" in msg


def test_reset_fails_when_god_sketch_node_returns(tmp_path: Path) -> None:
    root = _make_minimal_plot_tree(tmp_path)
    (root / "viewer" / "src" / "canvases" / "SketchNode.tsx").write_text(
        "// re-introduced god renderer\n", encoding="utf-8"
    )
    msg = _GATE.reset_complete_check(_staged_viewer(), root)
    assert msg is not None and "SketchNode.tsx" in msg


def test_reset_fails_when_canvas_kind_branching_returns(tmp_path: Path) -> None:
    root = _make_minimal_plot_tree(tmp_path)
    (root / "viewer" / "src" / "canvases" / "sketch" / "useEdgesMemo.ts").write_text(
        'if (doc.canvas_kind === "feature") { /* branch */ }\n',
        encoding="utf-8",
    )
    msg = _GATE.reset_complete_check(_staged_viewer(), root)
    assert msg is not None and "canvas_kind" in msg
    assert "useEdgesMemo.ts" in msg


def test_reset_failure_message_omits_comment_only_canvas_kind(tmp_path: Path) -> None:
    """The kill-switch must not flag canvas_kind references that live in
    comments (a comment explaining "we removed canvas_kind" should be
    a hint, not a regression signal)."""
    root = _make_minimal_plot_tree(tmp_path)
    (root / "viewer" / "src" / "canvases" / "sketch" / "useFlowHandlers.ts").write_text(
        "// v0.15 Phase 3.4 — removed all canvas_kind === switches.\nexport const y = 2;\n",
        encoding="utf-8",
    )
    assert _GATE.reset_complete_check(_staged_viewer(), root) is None


@pytest.mark.parametrize(
    "staged",
    [
        ["mashbill/.claude-plugin/plugin.json"],
        ["mashbill/hooks/hooks.json"],
        ["mashbill/skills/some-skill/SKILL.md"],
    ],
)
def test_reset_skips_non_viewer_non_server_commits(tmp_path: Path, staged: list[str]) -> None:
    """Non-viewer / non-server staged paths skip the check entirely."""
    root = _make_minimal_plot_tree(tmp_path)
    # Even if the baseline is BROKEN, the check skips when nothing
    # viewer- or server-related is staged.
    (root / "viewer" / "src" / "canvases" / "SketchInspector.tsx").write_text(
        "// would normally trigger #2\n", encoding="utf-8"
    )
    assert _GATE.reset_complete_check(staged, root) is None
