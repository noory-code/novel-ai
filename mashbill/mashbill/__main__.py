from __future__ import annotations

import sys

from mashbill.server import run, run_http_only, run_mcp_stdio


def main() -> None:
    # ``--mcp-stdio`` = tool-server mode for an external CLI (frozen builds
    # already dispatch on it in their own entrypoint). The full engine would
    # also bind the default HTTP port whenever it is free — an in-app coach
    # turn must never capture :5190 from under a real engine (B-11).
    if "--mcp-stdio" in sys.argv[1:]:
        run_mcp_stdio()
        return
    run()


def http_only() -> None:
    """Run just the HTTP server (no MCP stdio) for browser-side development."""
    run_http_only()


if __name__ == "__main__":
    main()
