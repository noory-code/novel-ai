"""Automated skill parameter validation tests

Validates required parameters, formats, prerequisites, and outputs for v3 skills
(solera-write-story and solera-execute-action-item). Anchored to the v3.0.0
three-axis model: Stories contribute to Concepts (no phases/goals/epics).
"""

from __future__ import annotations

import re
from pathlib import Path


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
                prereq = line.strip()[2:]
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
            if in_output_table and (line.startswith("##") or line.startswith(">")):
                break
            if in_output_table and "|" in line and not line.startswith("|---"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4 and parts[1] != "Step":
                    outputs.append(
                        {
                            "step": parts[1],
                            "output": parts[2],
                            "path": parts[3] if len(parts) > 3 else "",
                            "nature": parts[4] if len(parts) > 4 else "",
                        }
                    )

        return outputs


# ---------------------------------------------------------------------------
# solera-write-story (v3: Story → Concepts, no phase/goal/epic)
# ---------------------------------------------------------------------------


def test_write_story_required_parameters():
    """write-story: required parameters match v3 three-axis model"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    assert len(required_params) > 0, "No required parameters defined"

    # v3 required set — Story contributes to Concepts, no phase/goal/epic
    expected_params = {"project_path", "story_id", "story_name", "contributes_to"}
    found_params = set(required_params)

    assert expected_params.issubset(found_params), (
        f"Missing required parameters: {expected_params - found_params}"
    )

    # Guard against regression to v2 schema
    forbidden_params = {"phase_id", "goal_id", "epic_name", "epic_branches"}
    leaked = forbidden_params & found_params
    assert not leaked, f"v2 parameters leaked back into write-story: {leaked}"


def test_write_story_parameter_formats():
    """write-story: parameter format validation"""
    # story_id format: US-NNN or TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    for valid in ("US-001", "TS-014"):
        assert re.match(story_id_pattern, valid), f"Valid story_id failed format check: {valid}"

    for invalid in ("US-1", "STORY-001", "us-001"):
        assert not re.match(story_id_pattern, invalid), (
            f"Invalid story_id passed format check: {invalid}"
        )

    # story_name: kebab-case
    story_name_pattern = r"^[a-z][a-z0-9-]*[a-z0-9]$"
    assert re.match(story_name_pattern, "google-login")
    assert not re.match(story_name_pattern, "GoogleLogin")


def test_write_story_prerequisites():
    """write-story: prerequisites reference v3 Concepts, not epics"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    assert len(prerequisites) > 0, "No prerequisites defined"

    joined = "\n".join(prerequisites)

    # Must mention Concept-oriented prerequisites
    assert "concepts/_index.md" in joined, "Prerequisites must reference concepts/_index.md"
    assert (
        "concepts/{id}" in joined or "concepts/{id}.md" in joined or "status: active" in joined
    ), "Prerequisites must require each contributed Concept to exist/be active"

    # Guard against v2 remnants
    assert "_epic.md" not in joined, "v2 _epic.md prerequisite must not appear in v3"
    assert "phase" not in joined.lower() or "contributes_to" in joined.lower(), (
        "v2 phase/goal language must not reappear"
    )


def test_write_story_expected_outputs():
    """write-story: expected output validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-write-story" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    assert len(outputs) > 0, "No outputs defined"

    found_outputs = [o["output"] for o in outputs]
    joined = " ".join(found_outputs)

    # Core v3 outputs
    assert "_story.md" in joined, "_story.md output must be declared"
    assert "ACT-NNN" in joined or "ACT-" in joined, "Action Item files must be declared as output"
    assert "RETROSPECTIVE.md" in joined, "RETROSPECTIVE.md output must be declared"

    # v3-specific: Concept Current Shape updates
    assert "Current Shape" in joined or "concepts/" in joined, (
        "write-story Wrap-up must declare Concept updates as output"
    )


# ---------------------------------------------------------------------------
# solera-execute-action-item (v3: no epic_name, ACT is a commit)
# ---------------------------------------------------------------------------


def test_execute_action_item_required_parameters():
    """execute-action-item: required parameters match v3 (no epic_name)"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    required_params = validator.extract_required_parameters()

    assert len(required_params) > 0, "No required parameters defined"

    expected_params = {
        "project_path",
        "story_id",
        "story_name",
        "action_item_id",
        "action_item_name",
    }
    found_params = set(required_params)

    assert expected_params.issubset(found_params), (
        f"Missing required parameters: {expected_params - found_params}"
    )

    # Guard against v2 regression
    assert "epic_name" not in found_params, (
        "v2 epic_name parameter must not reappear in execute-action-item"
    )


def test_execute_action_item_parameter_formats():
    """execute-action-item: parameter format validation"""
    # action_item_id format: ACT-NNN
    action_item_id_pattern = r"^ACT-\d{3}$"
    assert re.match(action_item_id_pattern, "ACT-001")
    assert not re.match(action_item_id_pattern, "ACT-1")

    # story_id format: US-NNN or TS-NNN
    story_id_pattern = r"^(US|TS)-\d{3}$"
    assert re.match(story_id_pattern, "US-001")
    assert re.match(story_id_pattern, "TS-014")


def test_execute_action_item_prerequisites():
    """execute-action-item: prerequisites validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    prerequisites = validator.extract_prerequisites()

    assert len(prerequisites) > 0, "No prerequisites defined"

    joined = "\n".join(prerequisites)

    assert "_story.md" in joined, "Must require parent _story.md"
    assert "Action Items table" in joined, (
        "Must require ACT to appear in Story's Action Items table"
    )
    assert "depends_on" in joined, "Must require depends_on ACTs to be complete"


def test_execute_action_item_expected_outputs():
    """execute-action-item: expected output validation"""
    skill_path = Path(__file__).parent.parent / "skills" / "solera-execute-action-item" / "SKILL.md"
    validator = SkillValidator(skill_path)

    outputs = validator.extract_outputs()

    assert len(outputs) > 0, "No outputs defined"

    found_steps = [o["step"] for o in outputs]
    joined_outputs = " ".join(o["output"] for o in outputs)

    assert any("Execute" in s for s in found_steps), "Execute step must declare outputs"
    assert any("Wrap-up" in s for s in found_steps), "Wrap-up step must declare outputs"
    assert "commit" in joined_outputs.lower(), "Wrap-up must declare a git commit as output"
    assert "Output Artifacts" in joined_outputs, (
        "Wrap-up must append Output Artifacts to parent Story (v3 invariant)"
    )


# ---------------------------------------------------------------------------
# Commit message format (v3: [primary_concept][story_id][ACT-NNN])
# ---------------------------------------------------------------------------


def test_commit_message_format_validation():
    """Commit message follows v3 three-axis scope tag: [concept_id][story_id][ACT-NNN]"""
    valid_format = r"^\[[\w-]+\]\[(US|TS)-\d{3}\]\[ACT-\d{3}\] .+$"

    # v3 valid examples — scope tag is a Concept ID (contributes_to[0])
    valid_messages = [
        "[authentication][US-001][ACT-001] Add GoogleLoginUseCase",
        "[liquor-search][TS-014][ACT-003] Write FTS5 index migration",
        "[onboarding][US-002][ACT-005] Wire welcome screen",
    ]

    for msg in valid_messages:
        assert re.match(valid_format, msg), f"Valid commit message failed format validation: {msg}"

    invalid_messages = [
        "[authentication][US-001] message",  # ACT-NNN missing
        "[US-001][ACT-001] message",  # concept tag missing
        "[authentication][US-001][ACT-1] message",  # ACT format error
        "authentication][US-001][ACT-001] message",  # malformed brackets
    ]

    for msg in invalid_messages:
        assert not re.match(valid_format, msg), (
            f"Invalid commit message passed format validation: {msg}"
        )


if __name__ == "__main__":
    import sys

    tests = [
        ("write-story required parameters", test_write_story_required_parameters),
        ("write-story parameter formats", test_write_story_parameter_formats),
        ("write-story prerequisites", test_write_story_prerequisites),
        ("write-story expected outputs", test_write_story_expected_outputs),
        ("execute-action-item required parameters", test_execute_action_item_required_parameters),
        ("execute-action-item parameter formats", test_execute_action_item_parameter_formats),
        ("execute-action-item prerequisites", test_execute_action_item_prerequisites),
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
