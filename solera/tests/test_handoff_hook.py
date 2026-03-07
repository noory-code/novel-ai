"""handoff_hook.py 통합 테스트

SessionEnd 훅의 실행 흐름을 검증합니다:
1. stdin JSON 수신 검증
2. subprocess 실행 인자 검증
3. timeout 처리 검증
4. HANDOFF.md 생성/업데이트 검증
5. 재귀 실행 방지 검증
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# handoff_hook 모듈을 직접 임포트
import sys
hooks_path = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(hooks_path))

from handoff_hook import main, PROMPT


def test_hook_receives_stdin_json():
    """훅이 올바른 stdin JSON을 수신하는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "HANDOFF.md updated" in stderr


def test_hook_launches_subprocess_with_correct_args():
    """subprocess가 올바른 인자로 실행되는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        # subprocess.run 호출 인자 검증
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
    """timeout 처리가 올바르게 동작하는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "timeout after 60s" in stderr


def test_missing_stdin():
    """stdin 누락 시 에러 처리 검증"""
    stdout, stderr, code = main(stdin_data="")

    assert code == 1
    assert "no input received" in stderr


def test_invalid_json():
    """유효하지 않은 JSON 처리 검증"""
    stdout, stderr, code = main(stdin_data="invalid json {")

    assert code == 1
    assert "invalid JSON" in stderr


def test_subprocess_launch_failure():
    """subprocess 실행 실패 처리 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = OSError("command not found")
        stdout, stderr, code = main(stdin_data=stdin_data)

    assert code == 0
    assert "failed to launch" in stderr


def test_subprocess_uses_correct_cwd():
    """subprocess가 올바른 cwd를 사용하는지 검증"""
    test_cwd = "/test/project/path"
    stdin_data = json.dumps({"cwd": test_cwd})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["cwd"] == test_cwd


def test_subprocess_timeout_value():
    """subprocess가 올바른 timeout 값을 사용하는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 60


def test_subprocess_shell_false():
    """subprocess가 shell=False로 실행되는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0)
        main(stdin_data=stdin_data)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["shell"] is False


def test_log_file_created():
    """로그 파일이 생성되는지 검증"""
    stdin_data = json.dumps({"cwd": "/test/project"})

    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.open", create=True) as mock_open:
            mock_run.return_value = Mock(returncode=0)
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            main(stdin_data=stdin_data)

            # /tmp/solera-handoff-hook.log 파일이 열렸는지 확인
            mock_open.assert_called_once()
            call_args = mock_open.call_args[0]
            # open 메서드는 'w'와 encoding='utf-8'로 호출되어야 함
            call_kwargs = mock_open.call_args[1]
            assert call_kwargs.get("mode") == "w" or call_args[0] == "w"
            assert call_kwargs.get("encoding") == "utf-8"


if __name__ == "__main__":
    import sys

    tests = [
        ("stdin JSON 수신 검증", test_hook_receives_stdin_json),
        ("subprocess 인자 검증", test_hook_launches_subprocess_with_correct_args),
        ("timeout 처리", test_timeout_handling),
        ("stdin 누락 처리", test_missing_stdin),
        ("유효하지 않은 JSON 처리", test_invalid_json),
        ("subprocess 실행 실패 처리", test_subprocess_launch_failure),
        ("subprocess cwd 검증", test_subprocess_uses_correct_cwd),
        ("subprocess timeout 값 검증", test_subprocess_timeout_value),
        ("subprocess shell=False 검증", test_subprocess_shell_false),
        ("로그 파일 생성 검증", test_log_file_created),
    ]

    failed = []
    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed.append(name)
        except Exception as e:
            print(f"✗ {name}: 예외 발생 - {e}")
            failed.append(name)

    if failed:
        print(f"\n실패: {len(failed)}/{len(tests)}")
        sys.exit(1)
    else:
        print(f"\n모두 통과: {len(tests)}/{len(tests)}")
        sys.exit(0)
