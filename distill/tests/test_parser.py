"""Tests for transcript parser."""

import os

import pytest

from distill.extractor.parser import format_transcript, parse_transcript

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseTranscript:
    def test_parses_basic_user_assistant_messages(self) -> None:
        turns = parse_transcript(os.path.join(FIXTURES, "transcript-basic.jsonl"))
        assert len(turns) == 4
        assert turns[0].role == "user"
        assert turns[1].role == "assistant"
        assert "TypeScript" in turns[0].text

    def test_preserves_timestamps(self) -> None:
        turns = parse_transcript(os.path.join(FIXTURES, "transcript-basic.jsonl"))
        assert turns[0].timestamp == "2024-01-01T00:00:00Z"

    def test_skips_tool_use_and_thinking_keeps_text(self) -> None:
        turns = parse_transcript(os.path.join(FIXTURES, "transcript-tool-use.jsonl"))
        # user + 2 assistant messages (tool_use msg has text, thinking msg has text)
        assert len(turns) == 3
        # Assistant message with tool_use should only contain the text part
        assert "Here is your config" in turns[1].text
        assert "read_file" not in turns[1].text
        # Assistant message with thinking should only contain the text part
        assert "port 3000" in turns[2].text
        assert "Let me analyze" not in turns[2].text

    def test_skips_malformed_json_lines(self) -> None:
        turns = parse_transcript(os.path.join(FIXTURES, "transcript-malformed.jsonl"))
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[1].role == "assistant"

    def test_returns_empty_for_empty_file(self) -> None:
        turns = parse_transcript(os.path.join(FIXTURES, "transcript-empty.jsonl"))
        assert len(turns) == 0

    def test_partial_recovery_skips_only_corrupt_line(self, tmp_path: pytest.TempPathFactory) -> None:
        """부분 JSONL 복구: 손상된 줄만 건너뛰고 유효한 줄은 복구"""
        jsonl_path = tmp_path / "partial.jsonl"
        jsonl_path.write_text(
            '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"First valid"}]},"timestamp":"2024-01-01T00:00:00Z"}\n'
            '{malformed json line\n'
            '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"Second valid"}]},"timestamp":"2024-01-01T00:01:00Z"}\n',
            encoding="utf-8",
        )
        turns = parse_transcript(str(jsonl_path))
        assert len(turns) == 2
        assert turns[0].role == "user"
        assert turns[0].text == "First valid"
        assert turns[1].role == "assistant"
        assert turns[1].text == "Second valid"


class TestFormatTranscript:
    def test_formats_turns_with_role_headers(self) -> None:
        from distill.extractor.parser import ConversationTurn

        formatted = format_transcript([
            ConversationTurn(role="user", text="Hello"),
            ConversationTurn(role="assistant", text="Hi there"),
        ])
        assert "[USER]" in formatted
        assert "[ASSISTANT]" in formatted
        assert "Hello" in formatted
        assert "Hi there" in formatted
        assert "---" in formatted

    def test_returns_empty_string_for_empty_turns(self) -> None:
        formatted = format_transcript([])
        assert formatted == ""
