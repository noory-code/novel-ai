"""Tests for profile tool."""

from __future__ import annotations

import json

import pytest

from distill.store.metadata import MetadataStore
from distill.tools.profile import profile
from tests.helpers.factories import make_knowledge_input


@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    """Set up environment with some knowledge for profile tests."""
    store_dir = tmp_path / ".distill" / "knowledge"
    store_dir.mkdir(parents=True)
    monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
    monkeypatch.setattr("distill.tools.profile.detect_project_root", lambda **_: None)
    # Mock scanner to avoid filesystem issues
    monkeypatch.setattr(
        "distill.tools.profile.scan_environment",
        lambda _: type("Inv", (), {
            "summary": type("S", (), {
                "total_rules": 2,
                "distill_rules": 1,
                "user_rules": 1,
                "estimated_tokens": 500,
                "total_skills": 0,
                "distill_skills": 0,
                "user_skills": 0,
                "total_agents": 0,
            })(),
        })(),
    )
    monkeypatch.setattr(
        "distill.tools.profile.load_config",
        lambda _: type("C", (), {"rule_budget_max_files": 5})(),
    )

    meta = MetadataStore("global")
    meta.insert(
        make_knowledge_input(
            content="Pattern A", type="pattern", scope="global", confidence=0.9
        )
    )
    meta.insert(
        make_knowledge_input(
            content="Decision B", type="decision", scope="global", confidence=0.8
        )
    )
    meta.insert(
        make_knowledge_input(
            content="Preference C", type="preference", scope="global", confidence=0.7
        )
    )

    yield meta
    meta.close()


class TestProfile:
    @pytest.mark.asyncio
    async def test_shows_total_count(self, profile_env):
        result = await profile()
        assert "Total: 3" in result

    @pytest.mark.asyncio
    async def test_shows_type_breakdown(self, profile_env):
        result = await profile()
        assert "pattern: 1" in result
        assert "decision: 1" in result
        assert "preference: 1" in result

    @pytest.mark.asyncio
    async def test_shows_environment_section(self, profile_env):
        result = await profile()
        assert "ENVIRONMENT" in result
        assert "Rules: 2 files" in result
        assert "Budget:" in result

    @pytest.mark.asyncio
    async def test_shows_scope_header(self, profile_env):
        result = await profile()
        assert "GLOBAL scope" in result

    @pytest.mark.asyncio
    async def test_empty_store(self, tmp_path, monkeypatch):
        store_dir = tmp_path / "empty" / ".distill" / "knowledge"
        store_dir.mkdir(parents=True)
        monkeypatch.setattr("distill.store.scope.GLOBAL_DIR", store_dir)
        monkeypatch.setattr("distill.tools.profile.detect_project_root", lambda **_: None)
        monkeypatch.setattr(
            "distill.tools.profile.scan_environment",
            lambda _: type("Inv", (), {
                "summary": type("S", (), {
                    "total_rules": 0, "distill_rules": 0, "user_rules": 0,
                    "estimated_tokens": 0, "total_skills": 0, "distill_skills": 0,
                    "user_skills": 0, "total_agents": 0,
                })(),
            })(),
        )
        monkeypatch.setattr(
            "distill.tools.profile.load_config",
            lambda _: type("C", (), {"rule_budget_max_files": 5})(),
        )

        result = await profile()
        assert "Total: 0" in result

    @pytest.mark.asyncio
    async def test_respects_scope_filter(self, profile_env):
        result = await profile(scope="global")
        assert "GLOBAL scope" in result

    @pytest.mark.asyncio
    async def test_shows_hook_status_finished(self, profile_env, tmp_path, monkeypatch):
        status_path = tmp_path / "hook-status.json"
        status_path.write_text(json.dumps({
            "last_run": "2026-03-17T10:00:00Z",
            "session_id": "sess-abc",
            "event": "SessionEnd",
            "result": "success",
            "duration_s": 12.5,
        }))
        monkeypatch.setattr("distill.tools.profile.STATUS_PATH", status_path)

        result = await profile()
        assert "LAST HOOK" in result
        assert "SessionEnd" in result
        assert "success" in result
        assert "12.5s" in result

    @pytest.mark.asyncio
    async def test_shows_hook_status_running(self, profile_env, tmp_path, monkeypatch):
        status_path = tmp_path / "hook-status.json"
        status_path.write_text(json.dumps({
            "pid": 12345,
            "started_at": "2026-03-17T10:00:00Z",
            "session_id": "sess-abc",
            "event": "PreCompact",
        }))
        monkeypatch.setattr("distill.tools.profile.STATUS_PATH", status_path)

        result = await profile()
        assert "LAST HOOK" in result
        assert "Currently running" in result
        assert "12345" in result

    @pytest.mark.asyncio
    async def test_shows_hook_error(self, profile_env, tmp_path, monkeypatch):
        status_path = tmp_path / "hook-status.json"
        status_path.write_text(json.dumps({
            "last_run": "2026-03-17T10:00:00Z",
            "session_id": "sess-abc",
            "event": "SessionEnd",
            "result": "error",
            "duration_s": 120.0,
            "error": "Hook timed out after 120s",
        }))
        monkeypatch.setattr("distill.tools.profile.STATUS_PATH", status_path)

        result = await profile()
        assert "error" in result.lower()
        assert "timed out" in result

    @pytest.mark.asyncio
    async def test_no_hook_status_file(self, profile_env, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "distill.tools.profile.STATUS_PATH",
            tmp_path / "nonexistent.json",
        )
        result = await profile()
        assert "LAST HOOK" not in result
