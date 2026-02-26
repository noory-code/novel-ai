"""FastMCP server setup and tool registration."""

from typing import Literal

from fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

from distill.tools.digest import digest as _digest
from distill.tools.ingest import ingest as _ingest
from distill.tools.init import init as _init
from distill.tools.learn import learn as _learn
from distill.tools.memory import memory as _memory
from distill.tools.profile import profile as _profile
from distill.tools.recall import recall as _recall
from distill.tools.store import store as _store

mcp = FastMCP(
    "distill",
    instructions="\n".join([
        "Distill extracts reusable knowledge from Claude Code conversations and stores it for future recall.",
        "",
        "Tools:",
        "- recall(query): Search stored knowledge. Use at the START of a task to check for relevant patterns, preferences, or past decisions.",
        "- learn(transcript_path, session_id): Extract knowledge from a conversation transcript. Called automatically via hooks — rarely needed manually.",
        "- profile(): View knowledge statistics. Use when the user asks about their accumulated knowledge.",
        "- digest(): Analyze and deduplicate knowledge entries. Use periodically or when the user wants to clean up.",
        "- memory(action, id?): Manage entries — promote (project→global), demote (global→project), delete, or crystallize (generate rules from accumulated knowledge).",
        "- ingest(path): Extract knowledge from markdown/text files (docs/, wiki/, notes/). Skips unchanged files automatically.",
        "- init(): One-step onboarding — create config, scan environment, and ingest configured dirs. Run once when setting up Distill in a new project.",
        "",
        "Typical workflow: run init() once to set up, then recall relevant knowledge before starting work, and let hooks handle learning from completed sessions.",
    ]),
)


@mcp.tool()
async def recall(
    query: str,
    scope: Literal["global", "project", "workspace"] | None = None,
    type: Literal["pattern", "preference", "decision", "mistake", "workaround"] | None = None,
    limit: int = 5,
    caller_cwd: str | None = None,
) -> str:
    """Search accumulated knowledge by semantic similarity."""
    return await _recall(query=query, scope=scope, type=type, limit=limit, caller_cwd=caller_cwd)


@mcp.tool()
async def learn(
    transcript_path: str,
    session_id: str,
    ctx: Context,
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Extract and save knowledge from a conversation transcript."""
    return await _learn(
        transcript_path=transcript_path,
        session_id=session_id,
        ctx=ctx,
        scope=scope,
        caller_cwd=caller_cwd,
    )


@mcp.tool()
async def profile(
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """View accumulated user knowledge profile and statistics."""
    return await _profile(scope=scope, caller_cwd=caller_cwd)


@mcp.tool()
async def digest(caller_cwd: str | None = None) -> str:
    """Analyze patterns across accumulated knowledge: merge duplicates, update confidence scores."""
    return await _digest(caller_cwd=caller_cwd)


@mcp.tool()
async def memory(
    action: Literal["promote", "demote", "delete", "crystallize"],
    ctx: Context,
    id: str | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Manage knowledge: promote/demote scope, delete entries, or crystallize rules."""
    return await _memory(action=action, ctx=ctx, id=id, caller_cwd=caller_cwd)


@mcp.tool()
async def ingest(
    path: str,
    ctx: Context,
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Extract knowledge from markdown/text files into the knowledge store.

    Recursively processes .md, .mdx, .txt files. Skips unchanged files (mtime-based).
    """
    return await _ingest(path=path, ctx=ctx, scope=scope, caller_cwd=caller_cwd)


@mcp.tool()
async def test_raw_sampling(ctx: Context) -> str:
    """Test raw sampling/createMessage without capability check."""
    try:
        result = await ctx.session.create_message(
            messages=[
                SamplingMessage(
                    role="user",
                    content=TextContent(type="text", text="Reply with just: OK"),
                )
            ],
            max_tokens=10,
        )
        return f"Success: {result}"
    except Exception as e:
        return f"Failed: {type(e).__name__}: {e}"


@mcp.tool()
async def store(
    chunks: list[dict],
    session_id: str,
    trigger: str = "manual",
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Save pre-extracted knowledge chunks to the knowledge store (no LLM required).

    Used by the claude -p subprocess in hooks to persist extracted knowledge.
    """
    return await _store(chunks=chunks, session_id=session_id, trigger=trigger, scope=scope, caller_cwd=caller_cwd)


@mcp.tool()
async def init(
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """One-step Distill onboarding for a new project.

    Creates .distill/config.json (if missing), scans the current .claude/ environment,
    and reports any directories configured in sources.dirs for follow-up ingest.
    Run once when setting up Distill. Then call ingest(path) for each configured dir.
    """
    return await _init(scope=scope, caller_cwd=caller_cwd)
