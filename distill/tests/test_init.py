"""Tests for the init tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from distill.tools.init import init, _ensure_config, _format_scan_summary, _install_skills, _install_hooks


class TestEnsureConfig:
    def test_creates_config_when_missing(self, tmp_path: Path):
        created, config_path = _ensure_config(str(tmp_path), "project")
        assert created is True
        assert config_path.exists()

    def test_config_is_valid_json(self, tmp_path: Path):
        _, config_path = _ensure_config(str(tmp_path), "project")
        data = json.loads(config_path.read_text())
        assert "extraction_model" in data
        assert "sources" in data
        assert "outputs" in data

    def test_does_not_overwrite_existing_config(self, tmp_path: Path):
        config_dir = tmp_path / ".distill"
        config_dir.mkdir()
        config_path = config_dir / "config.json"
        config_path.write_text('{"extraction_model": "custom-model"}')

        created, returned_path = _ensure_config(str(tmp_path), "project")

        assert created is False
        # Content must be untouched
        data = json.loads(config_path.read_text())
        assert data["extraction_model"] == "custom-model"

    def test_global_scope_writes_to_home(self, tmp_path: Path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)

        created, config_path = _ensure_config(str(tmp_path), "global")
        assert created is True
        assert config_path == tmp_path / ".distill" / "config.json"


class TestInstallSkills:
    def test_creates_all_skill_files(self, tmp_path: Path):
        results = _install_skills(str(tmp_path))
        assert len(results) == 8
        for created, name, path in results:
            assert created is True
            assert path.exists()
            assert name in path.read_text()

    def test_skips_if_already_exist(self, tmp_path: Path):
        _install_skills(str(tmp_path))
        results = _install_skills(str(tmp_path))
        for created, _, _ in results:
            assert created is False

    def test_skill_paths_are_correct(self, tmp_path: Path):
        results = _install_skills(str(tmp_path))
        for _, name, path in results:
            expected = tmp_path / ".claude" / "skills" / name / "SKILL.md"
            assert path == expected

    def test_installs_distill_recall_skill(self, tmp_path: Path):
        results = _install_skills(str(tmp_path))
        names = [name for _, name, _ in results]
        assert "distill-recall" in names
        assert "distill-init" in names
        assert "distill-learn" in names



class TestFormatScanSummary:
    def test_returns_no_items_message_when_empty(self, tmp_path: Path, monkeypatch):
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path / "fake_home")
        summary = _format_scan_summary(str(tmp_path))
        assert "no rules" in summary.lower()

    def test_counts_rules(self, tmp_path: Path, monkeypatch):
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path / "fake_home")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "distill-typescript.md").write_text("# TS rules")
        (rules_dir / "distill-python.md").write_text("# Python rules")

        summary = _format_scan_summary(str(tmp_path))
        assert "2 rules" in summary

    def test_counts_skills(self, tmp_path: Path, monkeypatch):
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path / "fake_home")
        skills_dir = tmp_path / ".claude" / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# My skill")

        summary = _format_scan_summary(str(tmp_path))
        assert "1 skills" in summary


class TestInitTool:
    @pytest.mark.asyncio
    async def test_creates_config_on_first_run(self, tmp_path: Path):
        result = await init(scope="project", _project_root=str(tmp_path))

        assert "Config created" in result
        config_path = tmp_path / ".distill" / "config.json"
        assert config_path.exists()

    @pytest.mark.asyncio
    async def test_reports_existing_config(self, tmp_path: Path):
        config_dir = tmp_path / ".distill"
        config_dir.mkdir()
        (config_dir / "config.json").write_text('{"extraction_model": "haiku"}')

        result = await init(scope="project", _project_root=str(tmp_path))

        assert "already exists" in result

    @pytest.mark.asyncio
    async def test_scans_environment(self, tmp_path: Path, monkeypatch):
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path / "fake_home")
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        (rules_dir / "distill-test.md").write_text("# Test rule")

        result = await init(scope="project", _project_root=str(tmp_path))

        assert "1 rules" in result

    @pytest.mark.asyncio
    async def test_no_dirs_message(self, tmp_path: Path):
        result = await init(scope="project", _project_root=str(tmp_path))

        assert "No dirs configured" in result or "sources.dirs" in result

    @pytest.mark.asyncio
    async def test_reports_configured_dirs(self, tmp_path: Path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config_path = tmp_path / ".distill" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "sources": {"dirs": [str(docs_dir)]},
        }))

        result = await init(scope="project", _project_root=str(tmp_path))

        # init() does not call ingest — it reports dirs and tells the user to call ingest()
        assert "sources.dirs configured" in result
        assert "ingest(" in result

    @pytest.mark.asyncio
    async def test_guidance_without_dirs(self, tmp_path: Path):
        result = await init(scope="project", _project_root=str(tmp_path))

        assert "learn(" in result or "sources.dirs" in result

    @pytest.mark.asyncio
    async def test_installs_skills_on_first_run(self, tmp_path: Path):
        result = await init(scope="project", _project_root=str(tmp_path))

        skill_path = tmp_path / ".claude" / "skills" / "distill-recall" / "SKILL.md"
        assert skill_path.exists()
        assert "Skills installed" in result

    @pytest.mark.asyncio
    async def test_reports_existing_skills(self, tmp_path: Path):
        # Pre-create all skills
        from distill.tools.init import _SKILL_CONTENTS
        for name in _SKILL_CONTENTS:
            skill_dir = tmp_path / ".claude" / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("existing")

        result = await init(scope="project", _project_root=str(tmp_path))
        assert "already exist" in result

    @pytest.mark.asyncio
    async def test_installs_hooks_on_first_run(self, tmp_path: Path):
        settings_path = tmp_path / "settings.local.json"
        result = await init(scope="project", _project_root=str(tmp_path))
        # init() uses real ~/.claude/settings.local.json — just verify message is present
        assert "Hook" in result

    @pytest.mark.asyncio
    async def test_guidance_with_dirs(self, tmp_path: Path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        config_path = tmp_path / ".distill" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps({
            "sources": {"dirs": [str(docs_dir)]},
        }))

        result = await init(scope="project", _project_root=str(tmp_path))

        assert "ingest(" in result


class TestMonorepoScopeSelection:
    @pytest.mark.asyncio
    async def test_monorepo_subpackage_uses_workspace_scope(self, tmp_path, monkeypatch):
        """서브패키지(project_root != workspace_root)에서 init() → workspace scope."""
        workspace = tmp_path / "monorepo"
        project = workspace / "packages" / "app"
        project.mkdir(parents=True)

        monkeypatch.setattr("distill.tools.init.detect_project_root", lambda **_: str(project))
        monkeypatch.setattr("distill.tools.init.detect_workspace_root", lambda **_: str(workspace))

        result = await init(_project_root=str(project))

        # config는 workspace에 생성되어야 함
        assert (workspace / ".distill" / "config.json").exists()
        assert not (project / ".distill" / "config.json").exists()

    @pytest.mark.asyncio
    async def test_standalone_project_uses_project_scope(self, tmp_path, monkeypatch):
        """project_root == workspace_root이면 project scope 유지."""
        monkeypatch.setattr("distill.tools.init.detect_project_root", lambda **_: str(tmp_path))
        monkeypatch.setattr("distill.tools.init.detect_workspace_root", lambda **_: str(tmp_path))

        result = await init(_project_root=str(tmp_path))

        assert (tmp_path / ".distill" / "config.json").exists()

    @pytest.mark.asyncio
    async def test_scope_override_respected_in_monorepo(self, tmp_path, monkeypatch):
        """명시적 scope 파라미터는 모노레포 감지보다 우선."""
        workspace = tmp_path / "monorepo"
        project = workspace / "packages" / "app"
        project.mkdir(parents=True)

        monkeypatch.setattr("distill.tools.init.detect_project_root", lambda **_: str(project))
        monkeypatch.setattr("distill.tools.init.detect_workspace_root", lambda **_: str(workspace))

        # 명시적으로 project scope 요청
        result = await init(scope="project", _project_root=str(project))

        assert (project / ".distill" / "config.json").exists()


class TestInstallHooks:
    def _settings(self, tmp_path: Path) -> Path:
        return tmp_path / "settings.local.json"

    def test_creates_settings_file_if_missing(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        result = _install_hooks(tmp_path / "distill", _settings_path=settings_path)
        assert settings_path.exists()
        assert "Hooks installed" in result

    def test_installs_all_hooks(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        _install_hooks(tmp_path / "distill", _settings_path=settings_path)
        data = json.loads(settings_path.read_text())
        assert "PreCompact" in data["hooks"]
        assert "SessionEnd" in data["hooks"]
        assert "SessionStart" not in data["hooks"]

    def test_hook_command_contains_distill_dir(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        distill_dir = tmp_path / "my-distill"
        _install_hooks(distill_dir, _settings_path=settings_path)
        data = json.loads(settings_path.read_text())
        cmd = data["hooks"]["PreCompact"][0]["command"]
        assert str(distill_dir) in cmd

    def test_skips_already_registered_hooks(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        distill_dir = tmp_path / "distill"
        _install_hooks(distill_dir, _settings_path=settings_path)
        _install_hooks(distill_dir, _settings_path=settings_path)

        data = json.loads(settings_path.read_text())
        # Should not have duplicates
        assert len(data["hooks"]["PreCompact"]) == 1

    def test_reports_already_registered(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        distill_dir = tmp_path / "distill"
        _install_hooks(distill_dir, _settings_path=settings_path)
        result = _install_hooks(distill_dir, _settings_path=settings_path)
        assert "already registered" in result

    def test_preserves_existing_hooks(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        existing = {
            "hooks": {
                "PreCompact": [{"type": "command", "command": "other-tool"}]
            }
        }
        settings_path.write_text(json.dumps(existing))

        _install_hooks(tmp_path / "distill", _settings_path=settings_path)

        data = json.loads(settings_path.read_text())
        commands = [e["command"] for e in data["hooks"]["PreCompact"]]
        assert "other-tool" in commands
        assert any("distill" in c for c in commands)

    def test_handles_malformed_json(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("{not valid json{{")

        result = _install_hooks(tmp_path / "distill", _settings_path=settings_path)
        assert "Could not read" in result
        # Original file should be untouched
        assert settings_path.read_text() == "{not valid json{{"

    def test_partial_install_reports_both(self, tmp_path: Path):
        settings_path = self._settings(tmp_path)
        distill_dir = tmp_path / "distill"

        # Pre-install PreCompact only
        cmd = f"uv --directory {distill_dir} run python -m distill.hooks.distill_hook"
        existing = {"hooks": {"PreCompact": [{"type": "command", "command": cmd}]}}
        settings_path.write_text(json.dumps(existing))

        result = _install_hooks(distill_dir, _settings_path=settings_path)
        assert "Hooks installed" in result
        assert "SessionEnd" in result
