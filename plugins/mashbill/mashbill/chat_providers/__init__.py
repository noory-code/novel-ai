"""R7 chat — per-CLI subprocess driver subpackage (D-2026-06-12-D + v0.64.1).

Each module here owns ONE provider's quirks (command shape, JSONL event
type names, session-id capture, resume semantics). The shared abstractions —
``ChatStreamEvent``, ``ChatProvider`` ABC, the ``_SubprocessChatProvider``
spawn-loop, and the ``_decode_jsonl`` helper — live in ``base``. ``chat_session``
imports the concrete classes from here and re-exports them so callers keep a
flat public surface.
"""
