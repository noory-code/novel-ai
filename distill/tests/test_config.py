"""Tests for config loader."""

from __future__ import annotations

import json
from pathlib import Path

from distill.config import OutputsConfig, SourcesConfig, load_config


class TestLoadConfig:
    def test_returns_defaults_when_no_config_files_exist(self, tmp_path: Path):
        config = load_config(str(tmp_path / "nonexistent"))
        assert config.extraction_model == "claude-haiku-4-5-20251001"
        assert config.crystallize_model == "claude-sonnet-4-5-20250929"
        assert config.max_transcript_chars == 100_000
        assert config.auto_crystallize_threshold == 0

    def test_returns_defaults_when_project_root_is_none(self):
        config = load_config(None)
        assert config.extraction_model == "claude-haiku-4-5-20251001"

    def test_returns_defaults_when_project_root_is_omitted(self):
        config = load_config()
        assert config.extraction_model == "claude-haiku-4-5-20251001"

    def test_merges_project_config_over_defaults(self, tmp_path: Path):
        project_dir = tmp_path / "project1"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({"extraction_model": "custom-model"})
        )

        config = load_config(str(project_dir))
        assert config.extraction_model == "custom-model"
        assert config.crystallize_model == "claude-sonnet-4-5-20250929"
        assert config.max_transcript_chars == 100_000

    def test_handles_partial_config(self, tmp_path: Path):
        project_dir = tmp_path / "project-partial"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({"auto_crystallize_threshold": 10})
        )

        config = load_config(str(project_dir))
        assert config.auto_crystallize_threshold == 10
        assert config.extraction_model == "claude-haiku-4-5-20251001"

    def test_ignores_malformed_json_gracefully(self, tmp_path: Path):
        project_dir = tmp_path / "project-bad"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text("NOT VALID JSON {{{{")

        config = load_config(str(project_dir))
        assert config.extraction_model == "claude-haiku-4-5-20251001"

    def test_workspace_config_overrides_global(self, tmp_path: Path, monkeypatch):
        """workspace config overrides global when workspace_root is provided."""
        global_dir = tmp_path / "global"
        global_dir.mkdir()
        (global_dir / "config.json").write_text(
            json.dumps({"extraction_model": "global-model", "auto_crystallize_threshold": 5})
        )
        monkeypatch.setattr(
            "distill.config.Path.home", lambda: global_dir.parent
        )

        workspace_dir = tmp_path / "workspace"
        (workspace_dir / ".distill").mkdir(parents=True)
        (workspace_dir / ".distill" / "config.json").write_text(
            json.dumps({"extraction_model": "workspace-model"})
        )

        config = load_config(workspace_root=str(workspace_dir))
        assert config.extraction_model == "workspace-model"

    def test_project_config_overrides_workspace(self, tmp_path: Path):
        """project config takes priority over workspace config."""
        workspace_dir = tmp_path / "workspace"
        (workspace_dir / ".distill").mkdir(parents=True)
        (workspace_dir / ".distill" / "config.json").write_text(
            json.dumps({"extraction_model": "workspace-model", "auto_crystallize_threshold": 3})
        )

        project_dir = tmp_path / "app"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({"extraction_model": "project-model"})
        )

        config = load_config(project_root=str(project_dir), workspace_root=str(workspace_dir))
        assert config.extraction_model == "project-model"
        assert config.auto_crystallize_threshold == 3  # workspace value not overridden

    def test_workspace_root_none_behaves_as_before(self, tmp_path: Path):
        """Passing workspace_root=None behaves identically to old 2-arg call."""
        project_dir = tmp_path / "proj"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({"extraction_model": "proj-model"})
        )

        config_old = load_config(str(project_dir))
        config_new = load_config(str(project_dir), workspace_root=None)
        assert config_old.extraction_model == config_new.extraction_model


class TestSourcesConfig:
    def test_defaults(self):
        s = SourcesConfig()
        assert s.transcripts is True
        assert s.rules is True
        assert s.skills is True
        assert s.agents is False
        assert s.dirs == []

    def test_load_sources_from_config_file(self, tmp_path: Path):
        project_dir = tmp_path / "proj"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({
                "sources": {
                    "rules": False,
                    "dirs": ["docs/", "wiki/"]
                }
            })
        )
        config = load_config(str(project_dir))
        assert config.sources.rules is False
        assert config.sources.dirs == ["docs/", "wiki/"]
        assert config.sources.transcripts is True  # default


class TestOutputsConfig:
    def test_defaults(self):
        o = OutputsConfig()
        assert o.rules.enabled is True
        assert o.rules.budget_max_files == 5
        assert o.rules.confidence_threshold == 0.7
        assert o.rules.split_threshold_tokens == 500
        assert o.skills.enabled is True
        assert o.skills.confidence_threshold == 0.6
        assert o.agents.enabled is False
        assert o.agents.min_skills_to_merge == 3

    def test_load_outputs_from_config_file(self, tmp_path: Path):
        project_dir = tmp_path / "proj2"
        (project_dir / ".distill").mkdir(parents=True)
        (project_dir / ".distill" / "config.json").write_text(
            json.dumps({
                "outputs": {
                    "rules": {"budget_max_files": 10, "split_threshold_tokens": 800},
                    "agents": {"enabled": True, "min_skills_to_merge": 5}
                }
            })
        )
        config = load_config(str(project_dir))
        assert config.outputs.rules.budget_max_files == 10
        assert config.outputs.rules.split_threshold_tokens == 800
        assert config.outputs.agents.enabled is True
        assert config.outputs.agents.min_skills_to_merge == 5
        assert config.outputs.skills.enabled is True  # default
