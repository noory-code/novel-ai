"""FastMCP tool surface for solera-map.

Two tools today:

- ``get_map(project_path)``: return the graph as a JSON-ready dict.
- ``open_map(project_path)``: open the browser viewer at the running HTTP
  server, validated against the workspace first so the user never lands on
  a blank error page.

The Python module ``solera_mcp.server`` composes this `mcp` object with the
HTTP stack and runs them together in :func:`solera_mcp.server.run`.
"""

from __future__ import annotations

import webbrowser
from typing import Any

from fastmcp import FastMCP

from solera_mcp.api_endpoints import graph_for
from solera_mcp.workspace import resolve_solera_root, resolved_port

mcp = FastMCP(
    "solera-map",
    instructions=(
        "solera-map exposes a Solera workspace as a typed graph of Concepts, "
        "Concept↔Concept edges, Milestones, Stories, Action Items, and Releases. "
        "Use `get_map(project_path)` to read the full graph. Future tools will "
        "propose edges and concepts before they are persisted."
    ),
)


@mcp.tool()
def get_map(project_path: str) -> dict[str, Any]:
    """Return the Solera workspace graph for ``project_path`` as a JSON-ready dict.

    Args:
        project_path: Project root containing ``.solera/`` (Solera v4) or
            ``workspace/`` (Solera v3, deprecated fallback). May also be the
            Solera root directory itself.
    """
    return graph_for(project_path).model_dump(by_alias=True)


@mcp.tool()
def open_map(project_path: str) -> str:
    """Open the Solera Map viewer in the user's default browser.

    Invoked by the ``/map`` slash command. Validates that ``project_path``
    is a readable Solera workspace before opening, so the browser never
    lands on a blank error page.
    """
    resolve_solera_root(project_path)  # raises if not a workspace
    port = resolved_port()
    url = f"http://127.0.0.1:{port}/?project_path={project_path}"
    webbrowser.open(url)
    return f"Opened {url}"
