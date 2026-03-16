"""Automated skill parameter validation tests

Validates required parameters, formats, and prerequisites for write-story and execute-action-item skills.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class SkillValidator:
    """Skill definition validator"""

    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.content = skill_path.read_text(encoding="utf-8")

    def extract_required_parameters(self) -> list[str]:
        """Extract list of required parameters"""
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
        """Extract list of prerequisites"""
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
        """Extract list of outputs"""
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
    """write-story: validation fails when required parameters are missing"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    # Verify required parameters exist
    assert len(required_params) > 0, "No required parameters defined"

    # Expected required parameters
    expected_params = {"project_path", "phase_id", "goal_id", "epic_name", "story_id", "story_name"}
    found_params = set(required_params)

    assert expected_params.issubset(found_params), \
        f"Missing required parameters: {expected_params - found_params}"


def test_write_story_parameter_formats():
    """write-story: parameter format validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    # phase_id format: YYYY-PX-name
    phase_id_pattern = r"^\d{4}-P\d+-[\w-]+$"
    example_phase_id = "2026-P1-foundation"
    assert re.match(phase_id_pattern, example_phase_id), \
        f"Invalid phase_id format: {example_phase_id}"

    # goal_id format: GX-name
    goal_id_pattern = r"^G\d+-[\w-]+$"
    example_goal_id = "G1-search-liquor"
    assert re.match(goal_id_pattern, example_goal_id), \
        f"Invalid goal_id format: {example_goal_id}"

    # story_id format: US-NNN or TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    example_story_id = "US-001"
    assert re.match(story_id_pattern, example_story_id), \
        f"Invalid story_id format: {example_story_id}"


def test_write_story_prerequisites():
    """write-story: prerequisites validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    # Verify prerequisites exist
    assert len(prerequisites) > 0, "No prerequisites defined"

    # Expected prerequisites
    expected_prereqs = [
        "`published/identity/mission.md` exists",
        "`_epic.md` exists",
    ]

    for expected in expected_prereqs:
        assert any(expected in prereq for prereq in prerequisites), \
            f"Missing required prerequisite: {expected}"


def test_write_story_expected_outputs():
    """write-story: expected output validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    # Verify outputs exist
    assert len(outputs) > 0, "No outputs defined"

    # Expected output files
    expected_output_names = ["_story.md", "ACT-NNN-{name}.md", "RETRO.md"]

    found_outputs = [o["output"] for o in outputs]

    for expected in expected_output_names:
        assert any(expected in output for output in found_outputs), \
            f"Missing required output: {expected}"


def test_execute_action_item_required_parameters():
    """execute-action-item: validation fails when required parameters are missing"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    # Verify required parameters exist
    assert len(required_params) > 0, "No required parameters defined"

    # Expected required parameters
    expected_params = {"epic_name", "story_id", "action_item_id", "action_item_name"}
    found_params = set(required_params)

    assert expected_params.issubset(found_params), \
        f"Missing required parameters: {expected_params - found_params}"


def test_execute_action_item_parameter_formats():
    """execute-action-item: parameter format validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    # action_item_id format: ACT-NNN
    action_item_id_pattern = r"^ACT-\d{3}$"
    example_action_item_id = "ACT-001"
    assert re.match(action_item_id_pattern, example_action_item_id), \
        f"Invalid action_item_id format: {example_action_item_id}"

    # story_id format: US-NNN or TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    example_story_id = "US-001"
    assert re.match(story_id_pattern, example_story_id), \
        f"Invalid story_id format: {example_story_id}"


def test_execute_action_item_prerequisites():
    """execute-action-item: prerequisites validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    # Verify prerequisites exist
    assert len(prerequisites) > 0, "No prerequisites defined"

    # Expected prerequisites
    expected_prereqs = [
        "`_story.md` exists",
        "The corresponding ACT must be assigned in the Action Items table of _story.md",
        "All prerequisite ACTs listed in depends_on must be ✅ complete",
    ]

    for expected in expected_prereqs:
        assert any(expected in prereq for prereq in prerequisites), \
            f"Missing required prerequisite: {expected}"


def test_execute_action_item_expected_outputs():
    """execute-action-item: expected output validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    # Verify outputs exist
    assert len(outputs) > 0, "No outputs defined"

    # Expected outputs
    expected_output_steps = ["Execute", "Wrap-up"]

    found_steps = [o["step"] for o in outputs]

    for expected in expected_output_steps:
        assert any(expected in step for step in found_steps), \
            f"Missing required output step: {expected}"


def test_commit_message_format_validation():
    """Commit message format validation"""
    # Valid format
    valid_format = r"^\[[\w-]+\]\[(US|TS)-\d{3}\]\[ACT-\d{3}\] .+$"

    valid_messages = [
        "[01-auth][US-001][ACT-001] Create login form",
        "[api-design][TS-002][ACT-005] Add auth endpoint",
    ]

    for msg in valid_messages:
        assert re.match(valid_format, msg), \
            f"Valid commit message failed format validation: {msg}"

    # Invalid format
    invalid_messages = [
        "[01-auth][US-001] message",  # ACT-NNN missing
        "[US-001][ACT-001] message",  # epic-name missing
        "[01-auth][US-001][ACT-1] message",  # ACT format error
    ]

    for msg in invalid_messages:
        assert not re.match(valid_format, msg), \
            f"Invalid commit message passed format validation: {msg}"


if __name__ == "__main__":
    # Simple runner for when pytest is not available
    import sys

    tests = [
        ("write-story required parameters", test_write_story_required_parameters),
        ("write-story parameter formats", test_write_story_parameter_formats),
        ("write-story Prerequisites", test_write_story_prerequisites),
        ("write-story expected outputs", test_write_story_expected_outputs),
        ("execute-action-item required parameters", test_execute_action_item_required_parameters),
        ("execute-action-item parameter formats", test_execute_action_item_parameter_formats),
        ("execute-action-item Prerequisites", test_execute_action_item_prerequisites),
        ("execute-action-item expected outputs", test_execute_action_item_expected_outputs),
        ("commit message format", test_commit_message_format_validation),
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
