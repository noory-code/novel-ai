"""LLM client: MCP Sampling only."""

from __future__ import annotations

from typing import Any


async def call_llm(
    *,
    messages: list[dict[str, Any]],
    system_prompt: str,
    model: str,
    max_tokens: int = 4096,
    ctx: Any = None,
    model_preferences: dict[str, Any] | None = None,
) -> str:
    """Call LLM via MCP Sampling.

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        system_prompt: System prompt string.
        model: Model name hint (e.g. "claude-haiku-4-5-20251001").
        max_tokens: Maximum tokens for response.
        ctx: FastMCP Context object. Required.
        model_preferences: Full model_preferences dict for MCP Sampling.
                           Defaults to {"hints": [{"name": model}]}.

    Returns:
        LLM response text.

    Raises:
        RuntimeError: If ctx is not provided (MCP Sampling unavailable).
    """
    if ctx is None:
        raise RuntimeError(
            "MCP Sampling context (ctx) is required. "
            "When running outside MCP, use claude -p subprocess instead."
        )

    result = await ctx.sample(
        messages=messages,
        system_prompt=system_prompt,
        model_preferences=model_preferences or {"hints": [{"name": model}]},
        max_tokens=max_tokens,
    )
    return result.text if hasattr(result, "text") else str(result)
