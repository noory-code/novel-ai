"""Wrap MCP sampling errors with user-friendly messages."""

from __future__ import annotations


class SamplingNotSupportedError(Exception):
    """MCP Sampling is not supported by the current client."""

    pass


def wrap_sampling_error(err: BaseException | str) -> Exception:
    """Detect MCP sampling unavailability and wrap with user-friendly message."""
    message = str(err) if not isinstance(err, Exception) else str(err)

    keywords = ("not supported", "Method not found", "sampling")
    if any(kw in message for kw in keywords):
        return SamplingNotSupportedError(
            "MCP Sampling is not supported by this client. "
            "Distill requires a client that supports MCP Sampling (server.createMessage). "
            "See: https://github.com/wooxist/distill#requirements"
        )

    if isinstance(err, Exception):
        return err
    return Exception(message)
