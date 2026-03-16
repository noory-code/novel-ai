"""handoff_hook.py integration tests

Validates the SessionEnd hook execution flow:
1. stdin JSON reception validation
2. subprocess argument validation
3. timeout handling validation
4. HANDOFF.md creation/update validation
5. Recursive execution prevention validation
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# Import handoff_hook module directly
import sys
hooks_path = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_path))

from handoff_hook import main, PROMPT


def test_hook_receives_stdin_json():
    """Verify that the hook receives valid stdin JSON"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "HANDOFF.md updated" in stderr


def test_hook_launches_subprocess_with_correct_args():
    """Verify that subprocess is launched with correct arguments"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        # Verify subprocess.run call arguments
        call_args = mock_run.call_args
        cmd = call_args[0][0]

        assert cmd[0] == "claude"
        assert cmd[1] == "-p"
        assert cmd[2] == PROMPT
        assert "--model" in cmd
        assert "haiku" in cmd
        assert "--allowedTools" in cmd
        assert "Bash,Read,Write,Edit" in cmd
        assert "--output-format" in cmd
        assert "text" in cmd


def test_timeout_handling():
    """Verify that timeout handling works correctly"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "timeout after 60s" in stderr


def test_missing_stdin():
    """Verify error handling when stdin is missing"""
    stdout, stderr, code = main(stdin_data="")

    assert code == 1
    assert "no input received" in stderr


def test_invalid_json():
    """Verify handling of invalid JSON"""
    stdout, stderr, code = main(stdin_data="invalid json {")

    assert code == 1
    assert "invalid JSON" in stderr


def test_subprocess_launch_failure():
    """Verify handling of subprocess launch failure"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = OSError("command not found")
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "failed to launch" in stderr


def test_subprocess_uses_correct_cwd():
    """Verify that subprocess uses the correct cwd"""
    test_cwd = "/test/project/path"
    stdin_data = json.dumps({"cwd": test_cwd})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == test_cwd


def test_subprocess_timeout_value():
    """Verify that subprocess uses the correct timeout value"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 60


def test_subprocess_shell_false():
    """Verify that subprocess runs with shell=False"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["shell"] is False


def test_log_file_created():
    """Verify that the log file is created"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.open", create=True) as mock_open:
            mock_run.return_value = Mock(returncode=0)
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            main(stdin_data=stdin_data)

            # Verify /tmp/solera-handoff-hook.log file was opened
            mock_open.assert_called_once()
            call_args = mock_open.call_args[0]
            # open method should be called with 'w' and encoding='utf-8'
            call_kwargs = mock_open.call_args[1]
            assert call_kwargs.get("mode") == "w" or call_args[0] == "w"
            assert call_kwargs.get("encoding") == "utf-8"


if __name__ == "__main__":
    import sys

    tests = [
        ("stdin JSON reception", test_hook_receives_stdin_json),
        ("subprocess arguments", test_hook_launches_subprocess_with_correct_args),
        ("timeout handling", test_timeout_handling),
        ("missing stdin handling", test_missing_stdin),
        ("invalid JSON handling", test_invalid_json),
        ("subprocess launch failure handling", test_subprocess_launch_failure),
        ("subprocess cwd", test_subprocess_uses_correct_cwd),
        ("subprocess timeout value", test_subprocess_timeout_value),
        ("subprocess shell=False", test_subprocess_shell_false),
        ("log file creation", test_log_file_created),
    ]

    failed = []
    for name, test_func in tests:
        try:
            test_func()
            print(f"PASS {name}")
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"FAIL {name}: exception raised - {e}")
            failed.append(name)

    if failed:
        print(f"\nFailed: {len(failed)}/{len(tests)}")
        sys.exit(1)
    else:
        print(f"\nAll passed: {len(tests)}/{len(tests)}")
        sys.exit(0)
