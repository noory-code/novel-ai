"""R8 build guard — this plugin never imports the app or sibling plugins.

OVERHAUL R8 (see `repos-plot/plot/docs/OVERHAUL.md`) pins the ONE forbidden
dependency direction: a plugin must stay independent of the commercial Novel
app — no imports of the viewer, the Tauri shell, or the app repo — and, per
R2, independent of every sibling plugin. The MIT-plugin / proprietary-app
licence boundary is defended by THIS build guard, not by file layout.

Mirrors `plot/tests/test_r8_independence.py`. AST-parses every module under
`src/distill/`; anything rooted at a banned name fails. Also bans `src-tauri`
path literals (a runtime reach into the shell).
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "src" / "distill"

# Code roots this plugin may NEVER import: the Novel viewer / app / shell, and
# every sibling plugin (each is independent — R2/R8).
BANNED_ROOTS = {
    "viewer",
    "app",
    "src_tauri",
    "tauri",
    "plot",
    "plot_mcp",
    "evonest",
    "solera",
    "solera_mcp",
}


def _modules() -> list[Path]:
    return sorted(
        p for p in PKG.rglob("*.py") if "__pycache__" not in p.parts
    )


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
    for py in _modules():
        hits = _import_roots(py) & BANNED_ROOTS
        if hits:
            offenders[str(py.relative_to(PKG))] = hits
    assert offenders == {}, (
        f"R8 violation — plugin imports app/sibling code: {offenders}. "
        "The dependency direction is app → plugin, NEVER the reverse."
    )


def test_plugin_never_reaches_into_the_shell_by_path() -> None:
    offenders = [
        str(py.relative_to(PKG))
        for py in _modules()
        if "src-tauri" in py.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"R8 violation — src-tauri path literal in: {offenders}"


def test_detector_catches_a_synthetic_violation() -> None:
    """Self-check: the AST walk actually flags a banned import."""
    sample = ast.parse("from viewer.src.api import putCanvas\nimport plot_mcp\n")
    roots: set[str] = set()
    for node in ast.walk(sample):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    assert roots & BANNED_ROOTS == {"viewer", "plot_mcp"}
