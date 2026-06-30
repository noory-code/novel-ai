"""CORE-8b — standalone invariant: Solera never reaches into mashbill.

The hard requirement (R8 spirit): Solera and mashbill do not import or path-reference
each other. The connection, when it exists, is a neutral format and stable ids
shared *by value*, never a code dependency. This guard fails if any source file
imports a plot module or hard-codes a path into the plot tree.
"""

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "solera"
FORBIDDEN_TOP_MODULES = {"plot", "plot_mcp"}
FORBIDDEN_PATH_NEEDLES = ("noory-ai/plot", "plot_mcp", "../plot", "/plot/")


def _imported_modules(tree: ast.AST) -> list[str]:
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def test_no_plot_imports() -> None:
    for py in PKG.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for module in _imported_modules(tree):
            top = module.split(".")[0]
            assert top not in FORBIDDEN_TOP_MODULES, f"{py.name} imports {module}"


def test_no_plot_path_references() -> None:
    for py in PKG.rglob("*.py"):
        text = py.read_text()
        for needle in FORBIDDEN_PATH_NEEDLES:
            assert needle not in text, f"{py.name} references {needle!r}"
