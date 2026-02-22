"""Tests for scanEnvironment."""

import os
import tempfile

import pytest

from distill.scanner import scan_environment


@pytest.fixture
def scan_dir() -> str:
    with tempfile.TemporaryDirectory(prefix="distill-scanner-test-") as d:
        yield d


def _write(path: str, content: str) -> None:
    """Helper to write a file with directories created."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


class TestScanEnvironmentBasic:
    def test_returns_valid_inventory_when_project_dir_missing(self, scan_dir: str) -> None:
        result = scan_environment(os.path.join(scan_dir, "nonexistent"))
        assert isinstance(result.rules, list)
        assert isinstance(result.skills, list)
        assert isinstance(result.agents, list)
        assert isinstance(result.summary.total_rules, int)
        assert isinstance(result.summary.estimated_tokens, int)

    def test_handles_null_project_root(self) -> None:
        result = scan_environment(None)
        assert isinstance(result.rules, list)
        assert isinstance(result.skills, list)
        assert isinstance(result.agents, list)


class TestRulesScanning:
    def test_reads_distill_prefixed_rules(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-distill-rules")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-typescript.md"), "- Use strict mode")

        result = scan_environment(project_dir)
        match = next((r for r in result.rules if r.name == "distill-typescript.md"), None)
        assert match is not None
        assert match.origin == "distill"
        assert match.type == "rule"
        assert "Use strict mode" in match.content
        assert result.summary.distill_rules >= 1

    def test_reads_user_rules(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-user-rules")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "contribution.md"), "# Contribution\n- Use conventional commits")

        result = scan_environment(project_dir)
        match = next((r for r in result.rules if r.name == "contribution.md"), None)
        assert match is not None
        assert match.origin == "user"
        assert result.summary.user_rules >= 1

    def test_reads_both_distill_and_user_rules(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-mixed-rules")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-style.md"), "- Use semicolons")
        _write(os.path.join(rules_dir, "contribution.md"), "- Use conventional commits")

        result = scan_environment(project_dir)
        distill = next((r for r in result.rules if r.name == "distill-style.md"), None)
        user = next((r for r in result.rules if r.name == "contribution.md"), None)
        assert distill is not None
        assert user is not None
        assert distill.origin == "distill"
        assert user.origin == "user"
        assert result.summary.total_rules >= 2

    def test_ignores_non_md_files(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-non-md")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-style.md"), "- rule content")
        _write(os.path.join(rules_dir, "notes.txt"), "not a rule")
        _write(os.path.join(rules_dir, "data.json"), "{}")

        result = scan_environment(project_dir)
        project_rules = [r for r in result.rules if r.path.startswith(project_dir)]
        assert len(project_rules) == 1
        assert project_rules[0].name == "distill-style.md"

    def test_includes_absolute_path(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-paths")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        _write(os.path.join(rules_dir, "distill-paths.md"), "content")

        result = scan_environment(project_dir)
        match = next((r for r in result.rules if r.name == "distill-paths.md"), None)
        assert match is not None
        assert match.path.startswith("/")
        assert match.path.endswith("distill-paths.md")


class TestSkillsScanning:
    def test_reads_skill_directories(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-skills")
        skill_dir = os.path.join(project_dir, ".claude", "skills", "deploy-prod")
        _write(os.path.join(skill_dir, "SKILL.md"), "# Deploy to Production")

        result = scan_environment(project_dir)
        match = next((s for s in result.skills if s.name == "deploy-prod"), None)
        assert match is not None
        assert match.origin == "user"
        assert match.type == "skill"
        assert "Deploy to Production" in match.content

    def test_classifies_distill_prefixed_skills(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-distill-skills")
        skill_dir = os.path.join(project_dir, ".claude", "skills", "distill-build")
        _write(os.path.join(skill_dir, "SKILL.md"), "# Build procedure")

        result = scan_environment(project_dir)
        match = next((s for s in result.skills if s.name == "distill-build"), None)
        assert match is not None
        assert match.origin == "distill"
        assert result.summary.distill_skills >= 1

    def test_skips_directories_without_skill_md(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-no-skill-md")
        skill_dir = os.path.join(project_dir, ".claude", "skills", "incomplete")
        _write(os.path.join(skill_dir, "README.md"), "not a skill file")

        result = scan_environment(project_dir)
        match = next((s for s in result.skills if s.name == "incomplete"), None)
        assert match is None


class TestAgentsScanning:
    def test_reads_yaml_agent_files(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-agents")
        agents_dir = os.path.join(project_dir, ".claude", "agents")
        _write(os.path.join(agents_dir, "reviewer.yaml"), "name: reviewer")

        result = scan_environment(project_dir)
        match = next((a for a in result.agents if a.name == "reviewer.yaml"), None)
        assert match is not None
        assert match.origin == "user"
        assert match.type == "agent"
        assert result.summary.total_agents >= 1

    def test_reads_yml_agent_files(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-yml-agents")
        agents_dir = os.path.join(project_dir, ".claude", "agents")
        _write(os.path.join(agents_dir, "builder.yml"), "name: builder")

        result = scan_environment(project_dir)
        match = next((a for a in result.agents if a.name == "builder.yml"), None)
        assert match is not None


class TestSummary:
    def test_computes_estimated_tokens(self, scan_dir: str) -> None:
        project_dir = os.path.join(scan_dir, "project-tokens")
        rules_dir = os.path.join(project_dir, ".claude", "rules")
        content = "x" * 100
        _write(os.path.join(rules_dir, "distill-test.md"), content)

        result = scan_environment(project_dir)
        # Token estimate should be at least ceil(100/4) = 25 for project content
        assert result.summary.estimated_tokens >= 25
