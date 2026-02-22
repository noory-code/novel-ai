"""LLM client: MCP Sampling with Anthropic API fallback."""

from __future__ import annotations

import os
from typing import Any


async def call_llm(
    *,
    messages: list[dict],
    system_prompt: str,
    model: str,
    max_tokens: int = 4096,
    ctx: Any = None,
    model_preferences: dict | None = None,
) -> str:
    """Call LLM via MCP Sampling, falling back to Anthropic API if sampling is unavailable.

    Priority:
    1. MCP Sampling via ctx.sample() — uses existing Claude subscription, no API key needed
    2. Anthropic API via ANTHROPIC_API_KEY — works in any environment

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        system_prompt: System prompt string.
        model: Model name hint (e.g. "claude-haiku-4-5-20251001").
        max_tokens: Maximum tokens for response.
        ctx: FastMCP Context object. If None, skips MCP Sampling.
        model_preferences: Full model_preferences dict for MCP Sampling.
                           Defaults to {"hints": [{"name": model}]}.

    Returns:
        LLM response text.

    Raises:
        RuntimeError: If neither MCP Sampling nor ANTHROPIC_API_KEY is available.
    """
    # 1. Try MCP Sampling
    if ctx is not None:
        try:
            result = await ctx.sample(
                messages=messages,
                system_prompt=system_prompt,
                model_preferences=model_preferences or {"hints": [{"name": model}]},
                max_tokens=max_tokens,
            )
            return result.text if hasattr(result, "text") else str(result)
        except Exception as err:
            msg = str(err)
            # Only fall through on sampling-not-supported errors
            if "not supported" not in msg and "Method not found" not in msg:
                raise

    # 2. Fallback to Anthropic API
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MCP Sampling is not supported by this client, "
            "and ANTHROPIC_API_KEY is not set. "
            "Set the ANTHROPIC_API_KEY environment variable to use Distill."
        )

    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,  # type: ignore[arg-type]
    )
    return response.content[0].text  # type: ignore[union-attr]
