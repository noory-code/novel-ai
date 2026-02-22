"""Tests for extractor: callLlm, parseExtractionResponse, wrapSamplingError."""

import json

import pytest

from distill.extractor.extractor import call_llm, parse_extraction_response
from distill.extractor.prompts import EXTRACTION_SYSTEM_PROMPT
from distill.extractor.sampling_error import SamplingNotSupportedError, wrap_sampling_error
from tests.helpers.mock_server import MockContext

VALID_RESPONSE = json.dumps([
    {
        "content": "Use ESM modules",
        "type": "preference",
        "scope": "global",
        "tags": ["typescript"],
        "confidence": 0.9,
    },
])


class TestCallLlm:
    @pytest.mark.asyncio
    async def test_sends_correct_message_structure(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        await call_llm(ctx, "test transcript", "test-model")

        assert len(ctx.calls) == 1
        assert len(ctx.calls[0].messages) == 1
        assert ctx.calls[0].messages[0]["role"] == "user"
        assert "test transcript" in ctx.calls[0].messages[0]["content"]

    @pytest.mark.asyncio
    async def test_sends_system_prompt(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        await call_llm(ctx, "transcript", "model")

        assert ctx.calls[0].system_prompt == EXTRACTION_SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_sends_model_hints(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        await call_llm(ctx, "transcript", "claude-haiku-4-5-20251001")

        assert ctx.calls[0].model_preferences["hints"] == [
            {"name": "claude-haiku-4-5-20251001"}
        ]

    @pytest.mark.asyncio
    async def test_sets_cost_and_speed_priority(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        await call_llm(ctx, "transcript", "model")

        assert ctx.calls[0].model_preferences["costPriority"] == 0.8
        assert ctx.calls[0].model_preferences["speedPriority"] == 0.8

    @pytest.mark.asyncio
    async def test_sets_max_tokens(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        await call_llm(ctx, "transcript", "model")

        assert ctx.calls[0].max_tokens == 4096

    @pytest.mark.asyncio
    async def test_returns_parsed_extractions(self) -> None:
        ctx = MockContext(response=VALID_RESPONSE)
        result = await call_llm(ctx, "transcript", "model")

        assert len(result) == 1
        assert result[0]["content"] == "Use ESM modules"
        assert result[0]["type"] == "preference"
        assert result[0]["scope"] == "global"

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_response(self) -> None:
        ctx = MockContext(response="")
        result = await call_llm(ctx, "transcript", "model")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_returns_empty_on_non_json_response(self) -> None:
        ctx = MockContext(response="No knowledge found in this transcript.")
        result = await call_llm(ctx, "transcript", "model")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_propagates_non_sampling_errors(self) -> None:
        ctx = MockContext(error=Exception("network timeout"))

        with pytest.raises(Exception, match="network timeout"):
            await call_llm(ctx, "transcript", "model")

    @pytest.mark.asyncio
    async def test_wraps_not_supported_error(self) -> None:
        ctx = MockContext(error=Exception("Method not supported"))

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            await call_llm(ctx, "transcript", "model")

    @pytest.mark.asyncio
    async def test_wraps_method_not_found_error(self) -> None:
        ctx = MockContext(error=Exception("Method not found: sampling/createMessage"))

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            await call_llm(ctx, "transcript", "model")

    @pytest.mark.asyncio
    async def test_includes_project_name_in_prompt(self) -> None:
        ctx = MockContext(response="[]")
        await call_llm(ctx, "transcript", "model", "distill")

        assert "distill" in ctx.calls[0].messages[0]["content"]

    @pytest.mark.asyncio
    async def test_includes_existing_rules_in_prompt(self) -> None:
        ctx = MockContext(response="[]")
        await call_llm(ctx, "transcript", "model", None, "### distill-style.md\n- Use strict mode")

        prompt = ctx.calls[0].messages[0]["content"]
        assert "<existing_rules>" in prompt
        assert "Use strict mode" in prompt


class TestWrapSamplingError:
    def test_wraps_not_supported_error(self) -> None:
        err = wrap_sampling_error(Exception("Method not supported"))
        assert isinstance(err, SamplingNotSupportedError)
        assert "MCP Sampling is not supported" in str(err)

    def test_wraps_method_not_found_error(self) -> None:
        err = wrap_sampling_error(Exception("Method not found: sampling/createMessage"))
        assert isinstance(err, SamplingNotSupportedError)

    def test_wraps_sampling_keyword_error(self) -> None:
        err = wrap_sampling_error(Exception("sampling request failed"))
        assert isinstance(err, SamplingNotSupportedError)

    def test_passes_through_unrelated_errors(self) -> None:
        original = Exception("network timeout")
        err = wrap_sampling_error(original)
        assert err is original

    def test_converts_non_error_to_exception(self) -> None:
        err = wrap_sampling_error("string error")
        assert isinstance(err, Exception)
        assert str(err) == "string error"


class TestParseExtractionResponse:
    def test_parses_valid_json_array(self) -> None:
        text = """Here are the extracted items:
[{"content":"Use ESM modules","type":"preference","scope":"global","tags":["typescript"],"confidence":0.9}]"""
        result = parse_extraction_response(text)
        assert len(result) == 1
        assert result[0]["content"] == "Use ESM modules"
        assert result[0]["type"] == "preference"
        assert result[0]["scope"] == "global"
        assert result[0]["tags"] == ["typescript"]
        assert result[0]["confidence"] == 0.9

    def test_parses_multiple_entries(self) -> None:
        text = """[
      {"content":"A","type":"pattern","scope":"global","tags":[],"confidence":0.8},
      {"content":"B","type":"decision","scope":"project","tags":["test"],"confidence":0.7}
    ]"""
        result = parse_extraction_response(text)
        assert len(result) == 2

    def test_accepts_all_valid_types(self) -> None:
        types = ["pattern", "preference", "decision", "mistake", "workaround", "conflict"]
        for t in types:
            text = f'[{{"content":"x","type":"{t}","scope":"global","tags":[],"confidence":0.5}}]'
            result = parse_extraction_response(text)
            assert len(result) == 1, f'type "{t}" should be accepted'

    def test_filters_invalid_type(self) -> None:
        text = '[{"content":"x","type":"invalid_type","scope":"global","tags":[],"confidence":0.5}]'
        assert parse_extraction_response(text) == []

    def test_accepts_workspace_scope(self) -> None:
        text = '[{"content":"x","type":"pattern","scope":"workspace","tags":[],"confidence":0.5}]'
        result = parse_extraction_response(text)
        assert len(result) == 1
        assert result[0]["scope"] == "workspace"

    def test_filters_invalid_scope(self) -> None:
        text = '[{"content":"x","type":"pattern","scope":"unknown","tags":[],"confidence":0.5}]'
        assert parse_extraction_response(text) == []

    def test_filters_confidence_over_1(self) -> None:
        text = '[{"content":"x","type":"pattern","scope":"global","tags":[],"confidence":1.5}]'
        assert parse_extraction_response(text) == []

    def test_filters_negative_confidence(self) -> None:
        text = '[{"content":"x","type":"pattern","scope":"global","tags":[],"confidence":-0.1}]'
        assert parse_extraction_response(text) == []

    def test_filters_missing_content(self) -> None:
        text = '[{"type":"pattern","scope":"global","tags":[],"confidence":0.5}]'
        assert parse_extraction_response(text) == []

    def test_filters_non_array_tags(self) -> None:
        text = '[{"content":"x","type":"pattern","scope":"global","tags":"not-array","confidence":0.5}]'
        assert parse_extraction_response(text) == []

    def test_returns_empty_when_no_json_found(self) -> None:
        assert parse_extraction_response("No knowledge found.") == []

    def test_returns_empty_for_malformed_json(self) -> None:
        assert parse_extraction_response("[{broken json}]") == []

    def test_keeps_valid_filters_invalid(self) -> None:
        text = """[
      {"content":"valid","type":"pattern","scope":"global","tags":[],"confidence":0.8},
      {"content":"bad type","type":"nonexistent","scope":"global","tags":[],"confidence":0.5},
      {"content":"also valid","type":"decision","scope":"project","tags":["test"],"confidence":0.6}
    ]"""
        result = parse_extraction_response(text)
        assert len(result) == 2
        assert result[0]["content"] == "valid"
        assert result[1]["content"] == "also valid"
