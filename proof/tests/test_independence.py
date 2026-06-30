"""Proof is a lower-layer substrate: it imports neither Plot nor Solera.

Plot and Solera point at decisions by id (by value); the dependency runs one way
(they depend on proof, proof depends on neither). This guard fails if any source
file imports a plot or solera module.
"""

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "proof"
FORBIDDEN_TOP_MODULES = {"plot", "plot_mcp", "solera"}


def _imported_modules(tree: ast.AST) -> list[str]:
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.append(node.module)
    return mods


def test_no_plot_or_solera_imports() -> None:
    for py in PKG.rglob("*.py"):
        tree = ast.parse(py.read_text())
        for module in _imported_modules(tree):
            assert module.split(".")[0] not in FORBIDDEN_TOP_MODULES, f"{py.name} imports {module}"
