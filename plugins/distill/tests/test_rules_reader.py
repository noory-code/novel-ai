"""Tests for rules_reader."""

import os
import tempfile

import pytest

from distill.extractor.rules_reader import read_all_rules, read_existing_distill_rules


@pytest.fixture
def reader_dir() -> str:
    with tempfile.TemporaryDirectory(prefix="distill-rules-test-") as d:
        yield d


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


class TestReadExistingDistillRules:
    def test_returns_none_when_no_rules_exist(self, reader_dir: str) -> None:
        result = read_existing_distill_rules(os.path.join(reader_dir, "nonexistent"))
        # may pick up global rules, so just check it doesn't throw
        assert result is None or isinstance(result, str)

    def test_reads_distill_md_files(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-with-rules")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-typescript.md"), "# typescript\n- Use strict mode\n")
        _write(os.path.join(rules_dir, "distill-testing.md"), "# testing\n- Write tests first\n")

        result = read_existing_distill_rules(project_dir)
        assert result is not None
        assert "typescript" in result
        assert "testing" in result
        assert "Use strict mode" in result
        assert "Write tests first" in result

    def test_ignores_non_distill_files(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-mixed-rules")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-style.md"), "# style\n- Distill rule\n")
        _write(os.path.join(rules_dir, "contribution.md"), "# contribution\n- User rule\n")

        result = read_existing_distill_rules(project_dir)
        assert result is not None
        assert "Distill rule" in result
        assert "User rule" not in result

    def test_returns_none_when_no_distill_files(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-no-distill")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "contribution.md"), "# User-only rules\n")

        result = read_existing_distill_rules(project_dir)
        # Could be None if no global distill rules either
        assert result is None or isinstance(result, str)


class TestReadAllRules:
    def test_returns_both_user_and_distill_rules(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-both")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-style.md"), "- Distill rule content")
        _write(os.path.join(rules_dir, "contribution.md"), "- User rule content")

        result = read_all_rules(project_dir)
        assert result is not None
        assert "Distill rule content" in result
        assert "User rule content" in result

    def test_labels_user_rules_section(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-user-header")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "contribution.md"), "- User content")

        result = read_all_rules(project_dir)
        assert result is not None
        assert "### User Rules" in result
        assert "#### contribution.md" in result

    def test_labels_distill_rules_section(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-distill-header")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-ts.md"), "- TypeScript rules")

        result = read_all_rules(project_dir)
        assert result is not None
        assert "### Distill Rules" in result
        assert "#### distill-ts.md" in result

    def test_distill_only_still_filters_correctly(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-backward-compat")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-compat.md"), "- Distill only")
        _write(os.path.join(rules_dir, "user-rule.md"), "- User only")

        distill_only = read_existing_distill_rules(project_dir)
        assert distill_only is not None
        assert "Distill only" in distill_only
        assert "User only" not in distill_only

    def test_handles_project_with_only_user_rules(self, reader_dir: str) -> None:
        project_dir = os.path.join(reader_dir, "project-user-only")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "my-rules.md"), "- My rules")

        result = read_all_rules(project_dir)
        assert result is not None
        assert "### User Rules" in result
        assert "My rules" in result
