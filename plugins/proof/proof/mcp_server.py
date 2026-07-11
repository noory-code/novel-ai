"""FastMCP adapter over Proof's append-only decision log."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .formats import Status
from .log import Log

mcp = FastMCP(
    "proof",
    instructions=(
        "Proof stores immutable decisions under .noory/proof. Record a new "
        "decision instead of editing an existing file. To replace a decision, "
        "record the replacement with its supersedes field set to the old id."
    ),
)


def _log(project_root: str) -> Log:
    return Log(Path(project_root).expanduser().resolve() / ".noory" / "proof")


@mcp.tool()
def record_decision(
    project_root: str,
    title: str,
    body: str,
    status: Status = "accepted",
    supersedes: str | None = None,
    about: list[str] | None = None,
) -> dict[str, Any]:
    """Append one immutable project decision and return its allocated id."""
    decision = _log(project_root).record(
        title,
        body,
        status=status,
        supersedes=supersedes,
        about=about,
    )
    return decision.model_dump()


@mcp.tool()
def list_decisions(project_root: str) -> list[dict[str, Any]]:
    """Return every decision in stable identifier order, including superseded entries."""
    return [decision.model_dump() for decision in _log(project_root).decisions()]


@mcp.tool()
def decisions_in_force(project_root: str, about: str | None = None) -> list[dict[str, Any]]:
    """Return accepted, non-superseded decisions, optionally filtered by an ``about`` id."""
    return [decision.model_dump() for decision in _log(project_root).in_force(about=about)]


@mcp.tool()
def show_decision(project_root: str, decision_id: str) -> dict[str, Any]:
    """Read one decision by its stable identifier."""
    return _log(project_root).get(decision_id).model_dump()


@mcp.tool()
def check_decision(project_root: str, about: str) -> dict[str, Any]:
    """Report whether at least one in-force decision is tagged with ``about``."""
    decisions = decisions_in_force(project_root, about=about)
    return {"satisfied": bool(decisions), "decisions": decisions}


def main() -> None:
    """Run the host-neutral stdio MCP transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
