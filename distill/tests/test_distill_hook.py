"""Tests for distill_hook (PreCompact/SessionEnd handler)."""

from __future__ import annotations

import json
import subprocess

import pytest

from distill.hooks.distill_hook import main


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    """Remove ANTHROPIC_API_KEY to test claude -p path by default."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


class TestClaudePPath:
    """Tests for the no-API-key path using claude -p subprocess."""

    def test_runs_claude_p_and_logs_to_stderr(self, monkeypatch):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="Stored 2 chunks.", stderr=""
        )
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return mock_result

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run)

        stdin = json.dumps({
            "session_id": "sess-abc-123",
            "transcript_path": "/tmp/test-transcript.jsonl",
            "hook_event_name": "PreCompact",
        })
        stdout, stderr, code = main(stdin)

        assert code == 0
        assert stdout == ""
        assert "auto-learn complete via claude -p" in stderr
        assert len(calls) == 1
        cmd = calls[0]
        assert "claude" in cmd[0]
        assert "-p" in cmd

    def test_claude_p_receives_transcript_path_and_session_id(self, monkeypatch):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return mock_result

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run)

        stdin = json.dumps({
            "session_id": "sess-xyz",
            "transcript_path": "/home/user/.claude/sessions/abc.jsonl",
            "hook_event_name": "SessionEnd",
        })
        main(stdin)

        prompt = calls[0][2]  # claude -p <prompt>
        assert "/home/user/.claude/sessions/abc.jsonl" in prompt
        assert "sess-xyz" in prompt

    def test_claude_p_includes_mcp_config(self, monkeypatch):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return mock_result

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run)

        stdin = json.dumps({
            "session_id": "s1",
            "transcript_path": "/tmp/t.jsonl",
        })
        main(stdin)

        cmd = calls[0]
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        mcp_json = json.loads(cmd[mcp_idx + 1])
        assert "distill" in mcp_json["mcpServers"]

    def test_claude_p_failure_logged_to_stderr(self, monkeypatch):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="claude: command not found"
        )

        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "/tmp/t.jsonl",
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)

        assert code == 0  # hook always exits 0
        assert "claude -p failed" in stderr

    def test_claude_p_timeout_logged_to_stderr(self, monkeypatch):
        def mock_run_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="claude", timeout=120)

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run_timeout)

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "/tmp/t.jsonl",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr


class TestAutoLearnPath:
    """Tests for the API-key direct extraction path."""

    def test_auto_learn_calls_extract_and_store(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        called_with = {}

        def mock_asyncio_run(coro):
            cr_frame = coro.cr_frame
            if cr_frame:
                local_vars = cr_frame.f_locals
                called_with["transcript_path"] = local_vars.get("transcript_path")
                called_with["session_id"] = local_vars.get("session_id")
                called_with["cwd"] = local_vars.get("cwd")
            coro.close()
            return "Extracted 3, stored 3."

        monkeypatch.setattr("distill.hooks.distill_hook.asyncio.run", mock_asyncio_run)

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "/tmp/t.jsonl",
            "hook_event_name": "SessionEnd",
            "cwd": "/home/user/project",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "auto-learn complete" in stderr
        assert "Extracted 3, stored 3" in stderr
        assert called_with["transcript_path"] == "/tmp/t.jsonl"
        assert called_with["session_id"] == "sess-001"
        assert called_with["cwd"] == "/home/user/project"

    def test_auto_learn_fallback_to_claude_p_on_failure(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def mock_asyncio_run_fail(coro):
            coro.close()
            raise RuntimeError("API error")

        monkeypatch.setattr("distill.hooks.distill_hook.asyncio.run", mock_asyncio_run_fail)

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-002",
            "transcript_path": "/tmp/t.jsonl",
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "auto-learn failed" in stderr
        assert "fallback claude -p complete" in stderr


class TestErrorHandling:
    def test_exits_1_on_invalid_json(self):
        _, stderr, code = main("not-json")
        assert code == 1
        assert "distill-hook" in stderr

    def test_exits_1_on_missing_session_id(self):
        stdin = json.dumps({"transcript_path": "/tmp/t.jsonl"})
        _, stderr, code = main(stdin)
        assert code == 1
        assert "distill-hook" in stderr

    def test_exits_1_on_missing_transcript_path(self):
        stdin = json.dumps({"session_id": "sess-001"})
        _, stderr, code = main(stdin)
        assert code == 1
        assert "distill-hook" in stderr

    def test_exits_1_on_empty_input(self):
        _, stderr, code = main("")
        assert code == 1
        assert "distill-hook" in stderr

    def test_writes_diagnostic_to_stderr(self, monkeypatch):
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "/tmp/t.jsonl",
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)
        assert code == 0
        assert "distill-hook:" in stderr
