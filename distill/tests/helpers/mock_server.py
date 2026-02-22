"""Mock MCP context for testing sampling-based code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CapturedCall:
    """Captured ctx.sample() call for assertions."""

    messages: list[dict] = field(default_factory=list)
    system_prompt: str | None = None
    model_preferences: dict | None = None
    max_tokens: int | None = None


@dataclass
class SampleResult:
    """Mock result from ctx.sample()."""

    text: str


class MockContext:
    """Duck-typed mock for FastMCP Context that only implements sample().

    Production code only uses ctx.sample(), so this is sufficient.
    """

    def __init__(
        self,
        response: str | Callable[..., str] = "[]",
        error: Exception | None = None,
    ) -> None:
        self.calls: list[CapturedCall] = []
        self._response = response
        self._error = error

    async def sample(
        self,
        messages: list[dict] | None = None,
        system_prompt: str | None = None,
        model_preferences: dict | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> SampleResult:
        call = CapturedCall(
            messages=messages or [],
            system_prompt=system_prompt,
            model_preferences=model_preferences,
            max_tokens=max_tokens,
        )
        self.calls.append(call)

        if self._error:
            raise self._error

        text = self._response(call) if callable(self._response) else self._response
        return SampleResult(text=text)
