from __future__ import annotations

from mashbill.server import run, run_http_only


def main() -> None:
    run()


def http_only() -> None:
    """Run just the HTTP server (no MCP stdio) for browser-side development."""
    run_http_only()


if __name__ == "__main__":
    main()
