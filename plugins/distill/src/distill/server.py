"""FastMCP server setup and tool registration."""

from typing import Any, Literal

from fastmcp import Context, FastMCP

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
    instructions="\n".join(
        [
            "Distill stores reusable knowledge for future recall.",
            "",
            "Tools:",
            "- recall(query): Search stored patterns, preferences, and decisions.",
            "- learn(transcript_path, session_id): Extract from a Claude transcript.",
            "- profile(): View knowledge and environment statistics.",
            "- digest(): Analyze duplicate and stale entries.",
            "- memory(action, id?): Manage entries or crystallize Claude rules.",
            "- manage_entry(action, id): Promote, demote, or delete without sampling.",
            "- ingest(path): Extract from text files through Claude MCP Sampling.",
            "- store(chunks, session_id): Save model-extracted chunks directly.",
            "- init(): Create config and scan the local environment.",
            "",
            "Run init once, then recall relevant knowledge before starting work.",
        ]
    ),
)


@mcp.tool()
async def recall(
    query: str,
    scope: Literal["global", "project", "workspace"] | None = None,
    knowledge_type: Literal["pattern", "preference", "decision", "mistake", "workaround"]
    | None = None,
    limit: int = 5,
    min_confidence: float = 0.0,
    caller_cwd: str | None = None,
) -> str:
    """Search accumulated knowledge by semantic similarity.

    Args:
        query: Natural language search query.
        knowledge_type: Optional pattern, preference, decision, mistake, or workaround filter.
        scope: Filter by scope — one of 'global', 'workspace', 'project', or None for all.
        limit: Maximum number of results to return (max 20).
        min_confidence: Minimum confidence threshold (0.0–1.0). Default 0.0 (all results).
        caller_cwd: Caller's working directory for scope resolution.
    """
    return await _recall(
        query=query,
        scope=scope,
        knowledge_type=knowledge_type,
        limit=limit,
        min_confidence=min_confidence,
        caller_cwd=caller_cwd,
    )


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
async def manage_entry(
    action: Literal["promote", "demote", "delete"],
    id: str,
    caller_cwd: str | None = None,
) -> str:
    """Move or delete one knowledge entry without requiring MCP Sampling."""
    return await _memory(action=action, ctx=None, id=id, caller_cwd=caller_cwd)


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
async def store(
    chunks: list[dict[str, Any]],
    session_id: str,
    trigger: str = "manual",
    scope: Literal["global", "project", "workspace"] | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Save pre-extracted knowledge chunks to the knowledge store (no LLM required).

    Used by the claude -p subprocess in hooks to persist extracted knowledge.
    """
    return await _store(
        chunks=chunks, session_id=session_id, trigger=trigger, scope=scope, caller_cwd=caller_cwd
    )


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
