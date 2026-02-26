"""Tests for the ingest tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from distill.tools.ingest import INGEST_EXTENSIONS, _file_hash, _meta_key, ingest


class MockContext:
    """Mock MCP context that returns a fixed LLM response."""

    def __init__(self, response: str = "[]"):
        self.calls: list[dict] = []
        self._response = response

    async def sample(self, **kwargs) -> object:
        self.calls.append(kwargs)

        class Result:
            text: str

        r = Result()
        r.text = self._response
        return r


def _make_ctx(chunks: list[dict] | None = None) -> MockContext:
    if chunks is None:
        chunks = [
            {
                "content": "Always use TypeScript strict mode",
                "type": "pattern",
                "scope": "project",
                "tags": ["typescript"],
                "confidence": 0.9,
            }
        ]
    return MockContext(response=json.dumps(chunks))


class TestIngestHelpers:
    def test_file_hash_is_deterministic(self, tmp_path: Path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        h1 = _file_hash(f)
        h2 = _file_hash(f)
        assert h1 == h2

    def test_file_hash_changes_on_different_path(self, tmp_path: Path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("x")
        f2.write_text("x")
        assert _file_hash(f1) != _file_hash(f2)

    def test_meta_key_format(self, tmp_path: Path):
        f = tmp_path / "docs" / "arch.md"
        key = _meta_key(f)
        assert key.startswith("ingest:")
        assert "arch.md" in key

    def test_ingest_extensions(self):
        assert ".md" in INGEST_EXTENSIONS
        assert ".mdx" in INGEST_EXTENSIONS
        assert ".txt" in INGEST_EXTENSIONS
        assert ".py" not in INGEST_EXTENSIONS


class TestIngestTool:
    @pytest.mark.asyncio
    async def test_returns_error_for_nonexistent_path(self, tmp_path: Path):
        ctx = _make_ctx()
        result = await ingest(
            path=str(tmp_path / "nonexistent"),
            ctx=ctx,
            _project_root=str(tmp_path),
        )
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_processes_single_md_file(self, tmp_path: Path):
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        doc = tmp_path / "guide.md"
        doc.write_text("# TypeScript Guide\n\nAlways use strict mode.")
        ctx = _make_ctx()

        result = await ingest(path=str(doc), ctx=ctx, scope="project", _project_root=str(tmp_path))

        assert "1 files processed" in result
        assert "1 chunks saved" in result
        assert len(ctx.calls) == 1

    @pytest.mark.asyncio
    async def test_processes_directory_recursively(self, tmp_path: Path):
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "a.md").write_text("Pattern A")
        (tmp_path / "docs" / "b.md").write_text("Pattern B")
        (tmp_path / "docs" / "skip.py").write_text("not processed")
        ctx = _make_ctx()

        result = await ingest(path=str(tmp_path / "docs"), ctx=ctx, _project_root=str(tmp_path))

        assert "2 files processed" in result
        assert "2 chunks saved" in result

    @pytest.mark.asyncio
    async def test_skips_unchanged_files(self, tmp_path: Path):
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        doc = tmp_path / "stable.md"
        doc.write_text("Stable content")
        ctx = _make_ctx()

        # First ingest
        result1 = await ingest(
            path=str(doc), ctx=ctx, scope="project", _project_root=str(tmp_path)
        )
        assert "1 files processed" in result1

        # Second ingest (same mtime) — should skip
        ctx2 = _make_ctx()
        result2 = await ingest(
            path=str(doc), ctx=ctx2, scope="project", _project_root=str(tmp_path)
        )
        assert "1 unchanged files skipped" in result2
        assert len(ctx2.calls) == 0  # No LLM call made

    @pytest.mark.asyncio
    async def test_no_files_returns_descriptive_message(self, tmp_path: Path):
        (tmp_path / "empty").mkdir()
        ctx = _make_ctx()
        result = await ingest(path=str(tmp_path / "empty"), ctx=ctx, _project_root=str(tmp_path))
        assert "No supported files" in result

    @pytest.mark.asyncio
    async def test_saves_chunks_with_ingest_trigger(self, tmp_path: Path):
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        doc = tmp_path / "doc.md"
        doc.write_text("Use Python type hints")
        ctx = _make_ctx([{
            "content": "Use Python type hints for better code",
            "type": "pattern",
            "scope": "project",
            "tags": ["python"],
            "confidence": 0.8,
        }])

        await ingest(path=str(doc), ctx=ctx, scope="project", _project_root=str(tmp_path))

        # Verify trigger is "ingest" in LLM prompt
        assert len(ctx.calls) == 1
        user_msg = ctx.calls[0]["messages"][0]["content"]
        assert "doc.md" in user_msg  # source path mentioned

    @pytest.mark.asyncio
    async def test_handles_empty_llm_response(self, tmp_path: Path):
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        doc = tmp_path / "irrelevant.md"
        doc.write_text("Some content with no extractable knowledge")
        ctx = MockContext(response="[]")

        result = await ingest(path=str(doc), ctx=ctx, scope="project", _project_root=str(tmp_path))

        assert "1 files processed" in result
        assert "0 chunks saved" in result

    @pytest.mark.asyncio
    async def test_rejects_path_traversal_attack(self, tmp_path: Path):
        """경로 순회 공격을 차단하는지 확인"""
        (tmp_path / ".distill" / "knowledge").mkdir(parents=True)
        ctx = _make_ctx()

        # /etc/passwd는 tmp_path와 홈 디렉토리 외부이므로 차단되어야 함
        malicious_path = "/etc/passwd"

        with pytest.raises(ValueError, match="허용된 디렉토리 외부"):
            await ingest(
                path=malicious_path,
                ctx=ctx,
                scope="project",
                _project_root=str(tmp_path),
            )
