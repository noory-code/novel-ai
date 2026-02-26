"""Tests for learn tool."""

from __future__ import annotations

import json
import os

import pytest

from distill.tools.learn import learn
from tests.helpers.mock_server import MockContext


def _write_transcript(path: str, turns: list[dict]) -> None:
    """Write a simple .jsonl transcript file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for turn in turns:
            f.write(json.dumps(turn) + "\n")


def _basic_transcript(path: str) -> None:
    """Create a basic transcript with extractable content."""
    _write_transcript(
        path,
        [
            {
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Always use snake_case for Python variables"}]
                },
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Yes, PEP 8 recommends snake_case for variables and functions.",
                        }
                    ]
                },
                "timestamp": "2024-01-01T00:01:00Z",
            },
        ],
    )


@pytest.fixture
def learn_env(tmp_path, monkeypatch):
    """Set up environment for learn tests."""
    store_dir = tmp_path / ".distill" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
    monkeypatch.setattr("distill.tools.learn.detect_project_root", lambda **_: None)
    # Disable auto-crystallize for most tests
    monkeypatch.setattr(
        "distill.tools.learn.load_config",
        lambda _: type("C", (), {
            "extraction_model": "test-model",
            "crystallize_model": "test-model",
            "max_transcript_chars": 100000,
            "auto_crystallize_threshold": 0,
            "rule_budget_max_files": 5,
            "rule_confidence_threshold": 0.7,
        })(),
    )
    transcript = str(tmp_path / "test.jsonl")
    _basic_transcript(transcript)
    return {"tmp_path": tmp_path, "transcript": transcript}


class TestLearn:
    @pytest.mark.asyncio
    async def test_extracts_and_saves_knowledge(self, learn_env):
        extraction_response = json.dumps([
            {
                "content": "Use snake_case for Python variables per PEP 8",
                "type": "preference",
                "scope": "global",
                "tags": ["python", "style"],
                "confidence": 0.9,
            }
        ])
        ctx = MockContext(response=extraction_response)

        result = await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
        )

        assert "Extracted 1 knowledge chunks" in result
        assert "saved 1" in result
        assert "snake_case" in result

    @pytest.mark.asyncio
    async def test_returns_no_knowledge_message(self, learn_env):
        ctx = MockContext(response="[]")

        result = await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
        )

        assert "No extractable knowledge found" in result

    @pytest.mark.asyncio
    async def test_handles_multiple_chunks(self, learn_env):
        extraction_response = json.dumps([
            {
                "content": "Pattern 1",
                "type": "pattern",
                "scope": "global",
                "tags": ["test"],
                "confidence": 0.8,
            },
            {
                "content": "Decision 2",
                "type": "decision",
                "scope": "global",
                "tags": ["test"],
                "confidence": 0.9,
            },
        ])
        ctx = MockContext(response=extraction_response)

        result = await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
        )

        assert "Extracted 2 knowledge chunks" in result
        assert "saved 2" in result

    @pytest.mark.asyncio
    async def test_reports_conflict_warnings(self, learn_env):
        extraction_response = json.dumps([
            {
                "content": "Conflicts with existing rule X",
                "type": "conflict",
                "scope": "global",
                "tags": ["test"],
                "confidence": 0.85,
            }
        ])
        ctx = MockContext(response=extraction_response)

        result = await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
        )

        assert "Rule conflicts detected" in result
        assert "CONFLICT" in result

    @pytest.mark.asyncio
    async def test_respects_scope_override(self, learn_env, monkeypatch):
        project_dir = learn_env["tmp_path"] / "myproject"
        (project_dir / ".distill" / "knowledge").mkdir(parents=True)
        monkeypatch.setattr(
            "distill.tools.learn.detect_project_root", lambda **_: str(project_dir)
        )

        extraction_response = json.dumps([
            {
                "content": "Project-scoped rule",
                "type": "pattern",
                "scope": "project",
                "tags": ["test"],
                "confidence": 0.8,
            }
        ])
        ctx = MockContext(response=extraction_response)

        result = await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
            scope="project",
        )

        assert "Extracted 1" in result
        assert "saved 1" in result

    @pytest.mark.asyncio
    async def test_passes_ctx_to_extract_knowledge(self, learn_env):
        """Verify that ctx is forwarded to the extractor."""
        ctx = MockContext(response="[]")

        await learn(
            transcript_path=learn_env["transcript"],
            session_id="test-session",
            ctx=ctx,
        )

        # ctx.sample() should have been called at least once
        assert len(ctx.calls) >= 1
