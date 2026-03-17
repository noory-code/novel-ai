"""Tests for distill_hook (PreCompact/SessionEnd handler)."""

from __future__ import annotations

import fcntl
import io
import json
import subprocess
import threading
from pathlib import Path

import pytest

from distill.hooks.distill_hook import main
from distill.hooks.lock import acquire_hook_lock


@pytest.fixture(autouse=True)
def _auto_mock_lock(monkeypatch):
    """Auto-mock the hook lock so existing tests are not affected.

    Individual tests that need to test lock behavior can override this
    by monkeypatching acquire_hook_lock themselves.
    """
    monkeypatch.setattr(
        "distill.hooks.distill_hook.acquire_hook_lock",
        lambda: io.StringIO(),  # always succeed
    )
    monkeypatch.setattr(
        "distill.hooks.distill_hook.write_status_started",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "distill.hooks.distill_hook.write_status_finished",
        lambda *a, **kw: None,
    )


class TestClaudePPath:
    """Tests for the claude -p subprocess path."""

    def test_runs_claude_p_and_logs_to_stderr(self, monkeypatch, tmp_path):
        transcript = tmp_path / "test-transcript.jsonl"
        transcript.write_text("")

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
            "transcript_path": str(transcript),
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

    def test_claude_p_receives_transcript_path_and_session_id(self, monkeypatch, tmp_path):
        transcript = tmp_path / "abc.jsonl"
        transcript.write_text("")

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
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        main(stdin)

        prompt = calls[0][2]  # claude -p <prompt>
        assert "abc.jsonl" in prompt
        assert "sess-xyz" in prompt

    def test_claude_p_includes_model_flag(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

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
            "transcript_path": str(transcript),
        })
        main(stdin)

        cmd = calls[0]
        assert "--model" in cmd
        model_idx = cmd.index("--model")
        assert cmd[model_idx + 1] == "claude-haiku-4-5-20251001"  # default from config

    def test_claude_p_includes_mcp_config(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

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
            "transcript_path": str(transcript),
        })
        main(stdin)

        cmd = calls[0]
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        mcp_json = json.loads(cmd[mcp_idx + 1])
        assert "distill" in mcp_json["mcpServers"]

    def test_claude_p_failure_logged_to_stderr(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="claude: command not found"
        )

        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)

        assert code == 0  # hook always exits 0
        assert "claude -p failed" in stderr

    def test_claude_p_timeout_logged_to_stderr(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        def mock_run_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="claude", timeout=120)

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run_timeout)

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr


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

    def test_writes_diagnostic_to_stderr(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)
        assert code == 0
        assert "distill-hook:" in stderr


class TestSecurityValidation:
    """Security vulnerability validation tests."""

    def test_rejects_shell_injection_in_transcript_path(self, tmp_path):
        """Verify that shell injection attempts in transcript_path are rejected."""
        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "'; rm -rf / #",
        })
        _, stderr, code = main(stdin)

        # A ValueError should be raised, causing the hook to fail
        assert code == 0  # hook always exits 0
        assert "claude -p failed" in stderr or "distill-hook" in stderr

    def test_rejects_invalid_session_id_with_special_chars(self, tmp_path, monkeypatch):
        """Verify that special characters in session_id are rejected."""
        transcript = tmp_path / "test.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess; rm -rf /",
            "transcript_path": str(transcript),
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr
        assert "Invalid session_id format" in stderr

    def test_rejects_nonexistent_transcript_path(self, monkeypatch):
        """Verify that a nonexistent transcript_path is rejected."""
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": "/nonexistent/path/to/transcript.jsonl",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr
        assert "does not exist" in stderr

    def test_rejects_directory_as_transcript_path(self, tmp_path, monkeypatch):
        """Verify that passing a directory as transcript_path is rejected."""
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(tmp_path),
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr
        assert "is not a file" in stderr

    def test_rejects_invalid_cwd(self, tmp_path, monkeypatch):
        """Verify that a nonexistent cwd is rejected."""
        transcript = tmp_path / "test.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "cwd": "/nonexistent/directory",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr

    def test_timeout_kills_process(self, tmp_path, monkeypatch):
        """Verify that the process is forcefully terminated on timeout."""
        transcript = tmp_path / "test.jsonl"
        transcript.write_text("")

        class MockProcess:
            killed = False
            waited = False

            def kill(self):
                MockProcess.killed = True

            def wait(self):
                MockProcess.waited = True

        def mock_run_timeout(*args, **kwargs):
            exc = subprocess.TimeoutExpired(cmd="claude", timeout=120)
            exc.process = MockProcess()
            raise exc

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run_timeout)

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr
        assert "timed out" in stderr
        assert MockProcess.killed
        assert MockProcess.waited

    def test_subprocess_failure_logs_to_temp_file(self, tmp_path, monkeypatch):
        """Verify that the full stderr is written to a temp file on subprocess failure."""
        transcript = tmp_path / "test.jsonl"
        transcript.write_text("")

        long_stderr = "ERROR: " + ("x" * 500)
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=long_stderr
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        stdin = json.dumps({
            "session_id": "test-session-123",
            "transcript_path": str(transcript),
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "claude -p failed" in stderr
        import tempfile
        expected_log = str(Path(tempfile.gettempdir()) / "distill-hook-test-session-123.log")
        assert expected_log in stderr

        # Verify that the log file was created
        log_path = Path(expected_log)
        if log_path.exists():
            log_content = log_path.read_text()
            assert long_stderr in log_content
            log_path.unlink()  # cleanup

    def test_valid_session_id_accepted(self, tmp_path, monkeypatch):
        """Verify that a valid session_id is processed correctly."""
        transcript = tmp_path / "test.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return mock_result

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run)

        valid_ids = [
            "sess-abc-123",
            "SESSION_001",
            "test-session",
            "a1b2c3",
        ]

        for session_id in valid_ids:
            calls.clear()
            stdin = json.dumps({
                "session_id": session_id,
                "transcript_path": str(transcript),
            })
            _, stderr, code = main(stdin)

            assert code == 0
            assert "auto-learn complete" in stderr
            assert len(calls) == 1


class TestHookLock:
    """Tests for file-lock based concurrency control."""

    def test_acquire_returns_handle_when_free(self, tmp_path, monkeypatch):
        lock_path = tmp_path / "hook.lock"
        monkeypatch.setattr("distill.hooks.lock.LOCK_PATH", lock_path)

        handle = acquire_hook_lock()
        assert handle is not None
        handle.close()

    def test_acquire_returns_none_when_locked(self, tmp_path, monkeypatch):
        lock_path = tmp_path / "hook.lock"
        monkeypatch.setattr("distill.hooks.lock.LOCK_PATH", lock_path)

        # Hold the lock in another thread
        barrier = threading.Barrier(2, timeout=5)
        release = threading.Event()

        def hold_lock():
            fh = open(lock_path, "w")
            fcntl.flock(fh, fcntl.LOCK_EX)
            barrier.wait()
            release.wait(timeout=5)
            fh.close()

        t = threading.Thread(target=hold_lock)
        t.start()
        barrier.wait()

        # Second acquire should fail
        result = acquire_hook_lock()
        assert result is None

        release.set()
        t.join()

    def test_second_hook_skipped_when_lock_held(self, monkeypatch, tmp_path):
        """When lock is already held, hook should skip with informative message."""
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        # Override auto-mock: lock fails
        monkeypatch.setattr(
            "distill.hooks.distill_hook.acquire_hook_lock",
            lambda: None,
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "skipped" in stderr
        assert "another hook instance" in stderr

    def test_lock_acquired_runs_normally(self, monkeypatch, tmp_path):
        """When lock is acquired, hook runs the claude -p subprocess."""
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return mock_result

        monkeypatch.setattr("distill.hooks.distill_hook.subprocess.run", mock_run)
        # auto-mock already provides a successful lock

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "PreCompact",
        })
        _, stderr, code = main(stdin)

        assert code == 0
        assert "auto-learn complete" in stderr
        assert len(calls) == 1


class TestHookStatusFile:
    """Tests for hook status file observability."""

    def test_status_file_written_on_success(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")
        mock_result = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="done", stderr=""
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        # Track status writes
        status_calls = []

        def mock_write_started(session_id, event):
            status_calls.append(("started", session_id, event))

        def mock_write_finished(session_id, event, result, duration, error=None):
            status_calls.append(("finished", session_id, event, result, error))

        monkeypatch.setattr(
            "distill.hooks.distill_hook.write_status_started", mock_write_started
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.write_status_finished", mock_write_finished
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        main(stdin)

        assert len(status_calls) == 2
        assert status_calls[0] == ("started", "sess-001", "SessionEnd")
        assert status_calls[1][0] == "finished"
        assert status_calls[1][3] == "success"
        assert status_calls[1][4] is None  # no error

    def test_status_file_written_on_failure(self, monkeypatch, tmp_path):
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("")

        mock_result = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="fail"
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.subprocess.run",
            lambda *a, **kw: mock_result,
        )

        status_calls = []

        def mock_write_started(session_id, event):
            status_calls.append(("started",))

        def mock_write_finished(session_id, event, result, duration, error=None):
            status_calls.append(("finished", result, error))

        monkeypatch.setattr(
            "distill.hooks.distill_hook.write_status_started", mock_write_started
        )
        monkeypatch.setattr(
            "distill.hooks.distill_hook.write_status_finished", mock_write_finished
        )

        stdin = json.dumps({
            "session_id": "sess-001",
            "transcript_path": str(transcript),
            "hook_event_name": "SessionEnd",
        })
        main(stdin)

        assert len(status_calls) == 2
        assert status_calls[1][1] == "error"
        assert status_calls[1][2] is not None  # error message present

    def test_write_status_creates_file(self, tmp_path, monkeypatch):
        """Verify actual status file I/O."""
        from distill.hooks.lock import write_status_finished, write_status_started

        monkeypatch.setattr("distill.hooks.lock.STATUS_PATH", tmp_path / "status.json")

        write_status_started("sess-x", "PreCompact")
        data = json.loads((tmp_path / "status.json").read_text())
        assert data["session_id"] == "sess-x"
        assert data["event"] == "PreCompact"
        assert "pid" in data

        write_status_finished("sess-x", "PreCompact", "success", 1.5)
        data = json.loads((tmp_path / "status.json").read_text())
        assert data["result"] == "success"
        assert data["duration_s"] == 1.5
        assert "error" not in data
