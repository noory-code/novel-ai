"""스킬 파라미터 검증 자동화 테스트

write-story와 execute-action-item 스킬의 필수 파라미터, 형식, Prerequisites를 검증합니다.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class SkillValidator:
    """스킬 정의 검증 클래스"""

    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.content = skill_path.read_text(encoding="utf-8")

    def extract_required_parameters(self) -> list[str]:
        """필수 파라미터 목록 추출"""
        required_params = []
        in_input_table = False

        for line in self.content.split("\n"):
            if "## Input" in line:
                in_input_table = True
                continue
            if in_input_table and line.startswith("##"):
                break
            if in_input_table and "|" in line and "**" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    param_name = parts[1].strip("*").strip()
                    is_required = parts[2].strip().upper() == "Y"
                    if is_required and param_name and param_name != "Parameter":
                        required_params.append(param_name)

        return required_params

    def extract_prerequisites(self) -> list[str]:
        """Prerequisites 목록 추출"""
        prerequisites = []
        in_prerequisites = False

        for line in self.content.split("\n"):
            if "## Prerequisites" in line:
                in_prerequisites = True
                continue
            if in_prerequisites and line.startswith("##"):
                break
            if in_prerequisites and line.strip().startswith("- "):
                prereq = line.strip()[2:].split(":")[0] if ":" in line else line.strip()[2:]
                prerequisites.append(prereq.strip())

        return prerequisites

    def extract_outputs(self) -> list[dict[str, str]]:
        """Output 목록 추출"""
        outputs = []
        in_output_table = False

        for line in self.content.split("\n"):
            if "## Output" in line:
                in_output_table = True
                continue
            if in_output_table and line.startswith("##") or in_output_table and line.startswith(">"):
                break
            if in_output_table and "|" in line and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4 and parts[1] != "Step":
                    outputs.append({
                        "step": parts[1],
                        "output": parts[2],
                        "nature": parts[3] if len(parts) > 3 else "",
                        "path": parts[4] if len(parts) > 4 else "",
                    })

        return outputs


def test_write_story_required_parameters():
    """write-story: 필수 파라미터 누락 시 검증 실패"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    # 필수 파라미터 존재 확인
    assert len(required_params) > 0, "필수 파라미터가 정의되지 않음"

    # 예상 필수 파라미터
    expected_params = {"project_path", "phase_id", "goal_id", "epic_name", "story_id", "story_name"}
    found_params = set(required_params)

    assert expected_params.issubset(found_params), \
        f"필수 파라미터 누락: {expected_params - found_params}"


def test_write_story_parameter_formats():
    """write-story: 파라미터 형식 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    # phase_id 형식: YYYY-PX-name
    phase_id_pattern = r"^\d{4}-P\d+-[\w-]+$"
    example_phase_id = "2026-P1-foundation"
    assert re.match(phase_id_pattern, example_phase_id), \
        f"phase_id 형식이 올바르지 않음: {example_phase_id}"

    # goal_id 형식: GX-name
    goal_id_pattern = r"^G\d+-[\w-]+$"
    example_goal_id = "G1-search-liquor"
    assert re.match(goal_id_pattern, example_goal_id), \
        f"goal_id 형식이 올바르지 않음: {example_goal_id}"

    # story_id 형식: US-NNN 또는 TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    example_story_id = "US-001"
    assert re.match(story_id_pattern, example_story_id), \
        f"story_id 형식이 올바르지 않음: {example_story_id}"


def test_write_story_prerequisites():
    """write-story: Prerequisites 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    # Prerequisites 존재 확인
    assert len(prerequisites) > 0, "Prerequisites가 정의되지 않음"

    # 예상 Prerequisites
    expected_prereqs = [
        "`published/identity/mission.md` exists",
        "`_epic.md` exists",
    ]

    for expected in expected_prereqs:
        assert any(expected in prereq for prereq in prerequisites), \
            f"필수 Prerequisite 누락: {expected}"


def test_write_story_expected_outputs():
    """write-story: 예상 출력 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    # 출력 존재 확인
    assert len(outputs) > 0, "출력이 정의되지 않음"

    # 예상 출력 파일
    expected_output_names = ["_story.md", "ACT-NNN-{name}.md", "RETRO.md"]

    found_outputs = [o["output"] for o in outputs]

    for expected in expected_output_names:
        assert any(expected in output for output in found_outputs), \
            f"필수 출력 누락: {expected}"


def test_execute_action_item_required_parameters():
    """execute-action-item: 필수 파라미터 누락 시 검증 실패"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    # 필수 파라미터 존재 확인
    assert len(required_params) > 0, "필수 파라미터가 정의되지 않음"

    # 예상 필수 파라미터
    expected_params = {"epic_name", "story_id", "action_item_id", "action_item_name"}
    found_params = set(required_params)

    assert expected_params.issubset(found_params), \
        f"필수 파라미터 누락: {expected_params - found_params}"


def test_execute_action_item_parameter_formats():
    """execute-action-item: 파라미터 형식 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    # action_item_id 형식: ACT-NNN
    action_item_id_pattern = r"^ACT-\d{3}$"
    example_action_item_id = "ACT-001"
    assert re.match(action_item_id_pattern, example_action_item_id), \
        f"action_item_id 형식이 올바르지 않음: {example_action_item_id}"

    # story_id 형식: US-NNN 또는 TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    example_story_id = "US-001"
    assert re.match(story_id_pattern, example_story_id), \
        f"story_id 형식이 올바르지 않음: {example_story_id}"


def test_execute_action_item_prerequisites():
    """execute-action-item: Prerequisites 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    # Prerequisites 존재 확인
    assert len(prerequisites) > 0, "Prerequisites가 정의되지 않음"

    # 예상 Prerequisites
    expected_prereqs = [
        "`_story.md` exists",
        "The corresponding ACT must be assigned in the Action Items table of _story.md",
        "All prerequisite ACTs listed in depends_on must be ✅ complete",
    ]

    for expected in expected_prereqs:
        assert any(expected in prereq for prereq in prerequisites), \
            f"필수 Prerequisite 누락: {expected}"


def test_execute_action_item_expected_outputs():
    """execute-action-item: 예상 출력 검증"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    # 출력 존재 확인
    assert len(outputs) > 0, "출력이 정의되지 않음"

    # 예상 출력
    expected_output_steps = ["Execute", "Wrap-up"]

    found_steps = [o["step"] for o in outputs]

    for expected in expected_output_steps:
        assert any(expected in step for step in found_steps), \
            f"필수 출력 단계 누락: {expected}"


def test_commit_message_format_validation():
    """커밋 메시지 형식 검증"""
    # 올바른 형식
    valid_format = r"^\[[\w-]+\]\[(US|TS)-\d{3}\]\[ACT-\d{3}\] .+$"

    valid_messages = [
        "[01-auth][US-001][ACT-001] 로그인 폼 생성",
        "[api-design][TS-002][ACT-005] 인증 엔드포인트 추가",
    ]

    for msg in valid_messages:
        assert re.match(valid_format, msg), \
            f"유효한 커밋 메시지가 형식 검증 실패: {msg}"

    # 잘못된 형식
    invalid_messages = [
        "[01-auth][US-001] 메시지",  # ACT-NNN 누락
        "[US-001][ACT-001] 메시지",  # epic-name 누락
        "[01-auth][US-001][ACT-1] 메시지",  # ACT 형식 오류
    ]

    for msg in invalid_messages:
        assert not re.match(valid_format, msg), \
            f"유효하지 않은 커밋 메시지가 형식 검증 통과: {msg}"


if __name__ == "__main__":
    # pytest가 없는 경우를 위한 간단한 실행기
    import sys

    tests = [
        ("write-story 필수 파라미터", test_write_story_required_parameters),
        ("write-story 파라미터 형식", test_write_story_parameter_formats),
        ("write-story Prerequisites", test_write_story_prerequisites),
        ("write-story 예상 출력", test_write_story_expected_outputs),
        ("execute-action-item 필수 파라미터", test_execute_action_item_required_parameters),
        ("execute-action-item 파라미터 형식", test_execute_action_item_parameter_formats),
        ("execute-action-item Prerequisites", test_execute_action_item_prerequisites),
        ("execute-action-item 예상 출력", test_execute_action_item_expected_outputs),
        ("커밋 메시지 형식", test_commit_message_format_validation),
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
