"""Entry point for `python -m distill`.

Usage:
  python -m distill                                → Start MCP server
  python -m distill init [--scope=<scope>]         → Initialize Distill
  python -m distill ingest <path> [--scope=<scope>]→ Extract knowledge from files
  python -m distill recall <query> [--limit=<n>]  → Search stored knowledge
  python -m distill learn <transcript> <session_id> → Extract from transcript
  python -m distill crystallize [--scope=<scope>] → Generate rules/skills
"""

from __future__ import annotations

import asyncio
import sys


def _parse_flag(args: list[str], flag: str, default: str | None = None) -> str | None:
    """Extract --flag=value or --flag value from args list."""
    for i, arg in enumerate(args):
        if arg.startswith(f"--{flag}="):
            return arg.split("=", 1)[1]
        if arg == f"--{flag}" and i + 1 < len(args):
            return args[i + 1]
    return default


def _die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


async def _cmd_init(args: list[str]) -> None:
    from distill.tools.init import init
    scope = _parse_flag(args, "scope")
    result = await init(scope=scope)  # type: ignore[arg-type]
    print(result)


async def _cmd_ingest(args: list[str]) -> None:
    if not args or args[0].startswith("--"):
        _die("Usage: distill ingest <path> [--scope=<scope>]")
    path = args[0]
    scope = _parse_flag(args[1:], "scope")
    from distill.tools.ingest import ingest
    result = await ingest(path=path, ctx=None, scope=scope)  # type: ignore[arg-type]
    print(result)


async def _cmd_recall(args: list[str]) -> None:
    if not args or args[0].startswith("--"):
        _die("Usage: distill recall <query> [--limit=<n>]")
    query = args[0]
    limit_str = _parse_flag(args[1:], "limit", "5")
    try:
        limit = int(limit_str)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        limit = 5
    from distill.tools.recall import recall
    result = await recall(query=query, limit=limit)
    print(result)


async def _cmd_learn(args: list[str]) -> None:
    positional = [a for a in args if not a.startswith("--")]
    if len(positional) < 2:
        _die("Usage: distill learn <transcript_path> <session_id>")
    transcript_path, session_id = positional[0], positional[1]
    scope = _parse_flag(args, "scope")
    from distill.tools.learn import learn
    result = await learn(
        transcript_path=transcript_path,
        session_id=session_id,
        ctx=None,
        scope=scope,  # type: ignore[arg-type]
    )
    print(result)


async def _cmd_crystallize(args: list[str]) -> None:
    from distill.tools.memory import memory
    result = await memory(action="crystallize", ctx=None)
    print(result)


def main() -> None:
    argv = sys.argv[1:]

    if not argv or argv[0].startswith("-"):
        # No subcommand → run MCP server
        from distill.server import mcp
        mcp.run(transport="stdio")
        return

    cmd, rest = argv[0], argv[1:]

    commands = {
        "init": _cmd_init,
        "ingest": _cmd_ingest,
        "recall": _cmd_recall,
        "learn": _cmd_learn,
        "crystallize": _cmd_crystallize,
    }

    if cmd not in commands:
        _die(f"Unknown command: {cmd}. Available: {', '.join(commands)}")

    try:
        asyncio.run(commands[cmd](rest))
    except RuntimeError as e:
        _die(str(e))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
