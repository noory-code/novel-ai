"""Tests for the init tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from distill.tools.init import (
    _ensure_config,
    _format_scan_summary,
    init,
)


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


