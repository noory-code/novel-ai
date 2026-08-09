"""Deterministic save-announcement guard (W-00000071, novel-workspace).

Three prompt passes (B-6, D-2026-07-14-B, D-2026-07-15-A) could not reliably stop
the sonnet coach from reporting the save ("미션 좋네요, 저장했어요"). Since the
reply STREAMS token-by-token, a transcript-only strip would let the user still SEE
it — so the guard runs on the live stream, buffered to sentence boundaries. This
pins the pure heart: ``strip_save_announcement`` removes the save-report clause
while preserving the coach's actual content, and never touches a sentence that
merely discusses a save FEATURE.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from mashbill.chat_output_filter import filter_save_announcements, strip_save_announcement
from mashbill.chat_providers.base import ChatStreamEvent


def test_trailing_save_clause_removed_content_kept() -> None:
    assert strip_save_announcement("미션 좋네요, 저장했어요.") == "미션 좋네요."


def test_leading_save_sentence_removed() -> None:
    assert (
        strip_save_announcement('"유연함 우선" 저장했어요. 이제 두 갈래를 나눠볼게요.')
        == "이제 두 갈래를 나눠볼게요."
    )


def test_leading_save_clause_within_sentence_removed() -> None:
    assert (
        strip_save_announcement("주체는 저장했고, 이 인사이트는 이미 미션에 담겨 있어요.")
        == "이 인사이트는 이미 미션에 담겨 있어요."
    )


def test_whole_save_only_sentence_becomes_empty() -> None:
    assert strip_save_announcement("미션이 저장됐어요.") == ""
    assert strip_save_announcement("신뢰 부분 저장할게요.") == ""


def test_multiple_sentences_only_save_dropped() -> None:
    src = "신뢰 부분 저장할게요. 그리고 지금 말씀하신 건 다른 레벨이에요."
    assert strip_save_announcement(src) == "그리고 지금 말씀하신 건 다른 레벨이에요."


def test_save_feature_discussion_is_not_a_leak() -> None:
    # A founder building a save FEATURE — the coach legitimately says 저장 without
    # the self-announce conjugation. Must stay intact (no false positive).
    for keep in (
        "자동 저장 기능을 만들까요?",
        "사용자가 초안을 저장하는 흐름이 필요해요.",
        "이제 핵심 가치를 찾아볼까요?",
    ):
        assert strip_save_announcement(keep) == keep


def test_english_save_report_removed() -> None:
    # B-6's original examples were English ('saved' / 'done').
    out = strip_save_announcement("Mission saved. Now let's find the values.")
    assert out == "Now let's find the values."


def test_paragraph_breaks_survive_cleaning() -> None:
    # W-150 (workspace O-34): the codex coach's turn holds TWO messages joined
    # by a paragraph break, and its prose carries markdown lists. The final
    # whitespace squash flattened every newline to a space, so the whole turn
    # rendered as one glued line — which is what made the two-message shape
    # read as stuttering. Cleaning must normalize spaces WITHOUT eating
    # newlines.
    two_messages = "같은 부분을 보고 결정하는 일 — 좋습니다.\n\n첫 가치는 이렇게 제안해요."
    assert strip_save_announcement(two_messages) == two_messages

    listed = "모습은 두 갈래예요.\n- 목소리: 단정하게\n- 에너지: 조용하게"
    assert strip_save_announcement(listed) == listed


def test_save_clause_is_stripped_without_flattening_paragraphs() -> None:
    src = "미션 좋네요, 저장했어요.\n\n이제 가치를 볼까요?"
    assert strip_save_announcement(src) == "미션 좋네요.\n\n이제 가치를 볼까요?"


def test_stream_chunks_concatenate_to_the_full_cleaned_text_across_paragraphs() -> None:
    # The live viewer renders deltas as they land and reconciles on
    # turn_complete. If per-chunk cleaning drops a chunk's trailing paragraph
    # break, the reconcile path falls back to resending the whole text — a
    # delta-only subscriber would see the reply twice. So piecewise cleaning
    # must concatenate to exactly the whole-text cleaning.
    full = "받아침입니다.\n\n되말하고 이어갑니다. 다음 질문이에요?"
    raw = [
        ChatStreamEvent(type="turn_start", turn_id="t2"),
        # The paragraph break arrives INSIDE the first delta's tail.
        ChatStreamEvent(type="delta", turn_id="t2", text="받아침입니다.\n\n"),
        ChatStreamEvent(type="delta", turn_id="t2", text="되말하고 이어갑니다. 다음 질문이에요?"),
        ChatStreamEvent(type="turn_complete", turn_id="t2", text=full),
    ]

    async def _run() -> list[ChatStreamEvent]:
        async def gen() -> AsyncIterator[ChatStreamEvent]:
            for e in raw:
                yield e

        return [e async for e in filter_save_announcements(gen())]

    out = asyncio.run(_run())
    deltas = "".join(e.text for e in out if e.type == "delta")
    complete = next(e for e in out if e.type == "turn_complete")
    assert complete.text == full  # nothing to strip → text unchanged
    assert deltas == complete.text  # piecewise == whole (no resend)
    assert deltas.count("받아침") == 1  # the resend fallback did not fire


def test_stream_filter_buffers_across_deltas_and_reconciles() -> None:
    # The save clause is split across two delta chunks; sentence-buffering must
    # assemble the full sentence before deciding, and turn_complete.text must equal
    # the concatenation of the cleaned deltas (so a late subscriber reconciles).
    full = "미션 좋네요, 저장했어요. 이제 가치를 볼까요?"
    raw = [
        ChatStreamEvent(type="turn_start", turn_id="t1"),
        ChatStreamEvent(type="delta", turn_id="t1", text="미션 좋네요, 저"),
        ChatStreamEvent(type="delta", turn_id="t1", text="장했어요. 이제 가치를 볼까요?"),
        ChatStreamEvent(type="turn_complete", turn_id="t1", text=full),
    ]

    async def _run() -> list[ChatStreamEvent]:
        async def gen() -> AsyncIterator[ChatStreamEvent]:
            for e in raw:
                yield e

        return [e async for e in filter_save_announcements(gen())]

    out = asyncio.run(_run())
    deltas = "".join(e.text for e in out if e.type == "delta")
    complete = next(e for e in out if e.type == "turn_complete")
    assert "저장했어요" not in deltas
    assert "미션 좋네요" in deltas and "이제 가치를 볼까요?" in deltas
    assert complete.text == deltas  # stream and reconcile text agree
