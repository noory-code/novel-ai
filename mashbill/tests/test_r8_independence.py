"""R8 build guard (D-2026-06-10-F) — the plugin never imports the app.

OVERHAUL R8 pins the ONE forbidden dependency direction: plugins (this
engine) must stay independent of the commercial app — no imports of the
viewer, the Tauri shell, the app repo, or sibling plugins. The licence
boundary (MIT plugin / proprietary app) is defended by THIS build guard,
not by file layout (TECH_REVIEW C4).

AST-parses every `mashbill/*.py` import; anything rooted at a banned name
fails. Also bans `src-tauri` path literals (a runtime reach into the shell).
NOTE: `workspace.find_viewer_dist()` locating a *built* viewer dist to serve
is allowed — that is optional asset discovery with an API-only fallback,
not a code dependency.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "mashbill"

# Code roots the plugin may NEVER import: the viewer, the app/shell, and
# sibling plugins (each is independent — R2/R8).
BANNED_ROOTS = {
    "viewer",
    "app",
    "src_tauri",
    "tauri",
    "evonest",
    "distill",
    "solera",
    "solera_mcp",
}


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_plugin_never_imports_app_or_sibling_code() -> None:
    offenders: dict[str, set[str]] = {}
    for py in sorted(PKG.glob("*.py")):
        hits = _import_roots(py) & BANNED_ROOTS
        if hits:
            offenders[py.name] = hits
    assert offenders == {}, (
        f"R8 violation — plugin imports app/sibling code: {offenders}. "
        "The dependency direction is app → plugin, NEVER the reverse."
    )


def test_plugin_never_reaches_into_the_shell_by_path() -> None:
    offenders = [
        py.name for py in sorted(PKG.glob("*.py")) if "src-tauri" in py.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"R8 violation — src-tauri path literal in: {offenders}"


def test_detector_catches_a_synthetic_violation() -> None:
    """Self-check: the AST walk actually flags a banned import."""
    sample = ast.parse("from viewer.src.api import putCanvas\nimport tauri\n")
    roots: set[str] = set()
    for node in ast.walk(sample):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots & BANNED_ROOTS == {"viewer", "tauri"}
