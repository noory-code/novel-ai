"""Tests for extractKnowledge integration."""

import json
import os
import tempfile

import pytest

from distill.extractor.extractor import extract_knowledge
from tests.helpers.mock_server import MockContext

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FIXTURE_BASIC = os.path.join(FIXTURES, "transcript-basic.jsonl")
FIXTURE_EMPTY = os.path.join(FIXTURES, "transcript-empty.jsonl")

VALID_LLM_RESPONSE = json.dumps([
    {
        "content": "Use ESM modules with strict mode",
        "type": "preference",
        "scope": "global",
        "tags": ["typescript"],
        "confidence": 0.9,
    },
    {
        "content": "Prefer named exports over default exports for better tree-shaking",
        "type": "decision",
        "scope": "project",
        "tags": ["typescript", "exports"],
        "confidence": 0.85,
    },
])


class TestExtractKnowledge:
    @pytest.mark.asyncio
    async def test_returns_knowledge_input_from_valid_transcript(self) -> None:
        ctx = MockContext(response=VALID_LLM_RESPONSE)
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-001",
                trigger="manual",
                project_name="test-project",
                project_root=tmp,
            )

            assert len(result) == 2
            assert result[0].content == "Use ESM modules with strict mode"
            assert result[0].type == "preference"
            assert result[0].scope == "global"
            assert result[0].tags == ["typescript"]
            assert result[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_returns_empty_for_short_transcript(self) -> None:
        ctx = MockContext(response="[]")
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_EMPTY,
                session_id="sess-002",
                trigger="manual",
                project_root=tmp,
            )

            assert len(result) == 0
            assert len(ctx.calls) == 0  # Should not call LLM at all

    @pytest.mark.asyncio
    async def test_applies_scope_override(self) -> None:
        ctx = MockContext(response=VALID_LLM_RESPONSE)
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-003",
                trigger="manual",
                scope_override="global",
                project_root=tmp,
            )

            for chunk in result:
                assert chunk.scope == "global"

    @pytest.mark.asyncio
    async def test_sets_project_name_on_project_chunks(self) -> None:
        ctx = MockContext(response=VALID_LLM_RESPONSE)
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-004",
                trigger="manual",
                project_name="my-app",
                project_root=tmp,
            )

            project_chunks = [c for c in result if c.scope == "project"]
            for chunk in project_chunks:
                assert chunk.project == "my-app"

            global_chunks = [c for c in result if c.scope == "global"]
            for chunk in global_chunks:
                # project_name is set on all chunks regardless of scope
                assert chunk.project == "my-app"

    @pytest.mark.asyncio
    async def test_sets_trigger(self) -> None:
        ctx = MockContext(response=VALID_LLM_RESPONSE)
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-005",
                trigger="manual",
                project_root=tmp,
            )

            for chunk in result:
                assert chunk.source.trigger == "manual"

    @pytest.mark.asyncio
    async def test_sets_session_id(self) -> None:
        ctx = MockContext(response=VALID_LLM_RESPONSE)
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="my-unique-session",
                trigger="manual",
                project_root=tmp,
            )

            for chunk in result:
                assert chunk.source.session_id == "my-unique-session"

    @pytest.mark.asyncio
    async def test_truncates_long_transcripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Create config with very low max_transcript_chars
            config_dir = os.path.join(tmp, ".distill")
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, "config.json"), "w") as f:
                json.dump({"max_transcript_chars": 50}, f)

            ctx = MockContext(response=VALID_LLM_RESPONSE)
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-007",
                trigger="manual",
                project_root=tmp,
            )
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handles_llm_returning_empty(self) -> None:
        ctx = MockContext(response="[]")
        with tempfile.TemporaryDirectory() as tmp:
            result = await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-008",
                trigger="manual",
                project_root=tmp,
            )

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_passes_existing_rules_to_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, "distill-style.md"), "w") as f:
                f.write("# style\n- Always use semicolons")

            ctx = MockContext(response="[]")
            await extract_knowledge(
                ctx=ctx,
                transcript_path=FIXTURE_BASIC,
                session_id="sess-009",
                trigger="manual",
                project_root=tmp,
            )

            prompt_text = ctx.calls[0].messages[0]["content"]
            assert "<existing_rules>" in prompt_text
            assert "Always use semicolons" in prompt_text
