"""Deterministic save-announcement guard for the coach's streamed reply.

Three prompt passes (B-6, D-2026-07-14-B, D-2026-07-15-A) could not reliably stop
the sonnet coach from reporting the save ("미션 좋네요, 저장했어요"). The reply
STREAMS token-by-token, so a transcript-only strip would let the user still SEE
it. :func:`filter_save_announcements` buffers the stream to sentence boundaries and
runs :func:`strip_save_announcement` on each completed sentence before it is
broadcast — dropping the save-report clause while keeping the coach's content, and
making ``turn_complete.text`` exactly the concatenation of the emitted deltas so a
late subscriber reconciles to the same text.

Language scope: Korean (the coach speaks the user's language; every observed leak
was Korean) plus the English 'saved'/'done' forms B-6 first named. Novel is a
global service, so this is best-effort for KO/EN — it does not claim to catch a
save-report in every language.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

from mashbill.chat_providers.base import ChatStreamEvent

# Sentence terminators (NOT the comma — a comma bounds a *clause* inside a
# sentence, handled separately so "미션 좋네요, 저장했어요" keeps its first clause).
_SENT_SPLIT = re.compile(r"([.!?\n]+)")

# The save PREDICATE: 저장/기록 + an announcing/completive ending. "저장하는",
# "저장 기능" (present/noun) deliberately do NOT match — those are content.
_SAVE_PRED = (
    r"(?:저장|기록)(?:했어요|할게요|됐어요|했고|해뒀어요|했습니다|해요|해둘게요|했어|할게|해뒀어)"
)
# A clause that is ESSENTIALLY a save report: an optional short subject or quoted
# label, then the predicate, then nothing (anchored end). The length cap keeps a
# long content sentence that merely contains the verb from being swallowed.
_SAVE_CLAUSE_KO = re.compile(
    r"^\s*[\"'“”‘’]?[가-힣A-Za-z0-9\s·]{0,18}?[\"'“”‘’]?\s*" + _SAVE_PRED + r"\s*$"
)
_SAVE_CLAUSE_EN = re.compile(
    r"^\s*[\"']?[A-Za-z0-9\s]{0,18}?[\"']?\s*(?:saved|noted|got it saved)\s*$",
    re.IGNORECASE,
)


def _is_save_clause(segment: str) -> bool:
    s = segment.strip()
    return bool(s) and bool(_SAVE_CLAUSE_KO.match(s) or _SAVE_CLAUSE_EN.match(s))


def _strip_clauses(sentence: str) -> str:
    """Drop save-report clauses from ONE sentence, keep the rest (comma-bounded)."""
    kept = [c.strip() for c in sentence.split(",") if c.strip() and not _is_save_clause(c)]
    return ", ".join(kept)


def strip_save_announcement(text: str) -> str:
    """Remove save-report sentences/clauses, preserving the coach's content (pure)."""
    out: list[str] = []
    tokens = _SENT_SPLIT.split(text)
    for i in range(0, len(tokens), 2):
        body = tokens[i]
        term = tokens[i + 1] if i + 1 < len(tokens) else ""
        cleaned = _strip_clauses(body)
        if cleaned:
            out.append(cleaned + (term if term.strip() else ""))
    return re.sub(r"\s+", " ", " ".join(out)).strip()


async def filter_save_announcements(
    events: AsyncIterator[ChatStreamEvent],
) -> AsyncIterator[ChatStreamEvent]:
    """Sentence-buffer the coach stream and drop save-report clauses live.

    Deltas are held until a sentence terminator lands, so a clause split across
    chunks ("...저" | "장했어요.") is judged whole. ``turn_complete.text`` is the
    authoritative full cleaned reply (from the event's own text, or the accumulated
    deltas as fallback); the deltas concatenate to exactly that, so a delta-only
    subscriber and a late subscriber reconcile to identical text.
    """
    buffer = ""  # in-progress (unterminated) sentence, held back
    raw = ""  # every raw delta char seen, for fallback reconciliation
    emitted = ""  # cleaned text already sent as deltas

    def _delta(piece: str, turn_id: str) -> ChatStreamEvent:
        nonlocal emitted
        emitted += piece
        return ChatStreamEvent(type="delta", turn_id=turn_id, text=piece)

    async for ev in events:
        if ev.type == "delta":
            raw += ev.text
            buffer += ev.text
            matches = list(_SENT_SPLIT.finditer(buffer))
            if matches:
                cut = matches[-1].end()
                complete, buffer = buffer[:cut], buffer[cut:]
                cleaned = strip_save_announcement(complete)
                if cleaned:
                    sep = " " if emitted and not emitted.endswith((" ", "\n")) else ""
                    yield _delta(sep + cleaned, ev.turn_id)
            # no terminator yet → hold the buffer, emit nothing this delta
        elif ev.type == "turn_complete":
            full_cleaned = strip_save_announcement(ev.text or raw)
            # Emit whatever is not yet streamed so a delta-only subscriber lands on
            # the same full text; then reconcile turn_complete.text to it.
            if full_cleaned.startswith(emitted):
                tail = full_cleaned[len(emitted) :]
            else:  # whitespace drift — resend the authoritative text as one delta
                emitted = ""
                tail = full_cleaned
            if tail:
                yield _delta(tail, ev.turn_id)
            buffer = ""
            yield ev.model_copy(update={"text": full_cleaned})
        else:
            yield ev
