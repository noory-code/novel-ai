"""Tests for crystallize: parseCrystallizeResponse and crystallize pipeline."""

import json
import os
import tempfile

import pytest

from distill.extractor.crystallize import (
    AgentMetadata,
    CrystallizeReport,
    crystallize,
    parse_crystallize_response,
)
from distill.extractor.prompts import CRYSTALLIZE_SYSTEM_PROMPT
from tests.helpers.factories import make_knowledge_chunk
from tests.helpers.mock_server import MockContext


class TestParseCrystallizeResponse:
    def test_parses_valid_create_action(self) -> None:
        text = json.dumps([{
            "topic": "typescript-style",
            "action": "create",
            "delivery": "rule",
            "rules": ["Use strict mode", "Prefer named exports"],
            "source_ids": ["id1", "id2"],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].topic == "typescript-style"
        assert result[0].action == "create"
        assert result[0].delivery == "rule"
        assert result[0].rules == ["Use strict mode", "Prefer named exports"]
        assert result[0].source_ids == ["id1", "id2"]

    def test_parses_all_valid_actions(self) -> None:
        for action in ("create", "update", "remove", "downgrade"):
            text = json.dumps([{
                "topic": "t", "action": action, "delivery": "rule",
                "rules": ["r"], "source_ids": ["s"],
            }])
            result, _ = parse_crystallize_response(text)
            assert len(result) == 1, f'action "{action}" should be accepted'

    def test_parses_update_with_existing_file(self) -> None:
        text = json.dumps([{
            "topic": "error-handling",
            "action": "update",
            "delivery": "rule",
            "rules": ["Updated rule"],
            "source_ids": ["id3"],
            "existing_file": "distill-error-handling.md",
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].existing_file == "distill-error-handling.md"

    def test_parses_multiple_results(self) -> None:
        text = json.dumps([
            {"topic": "a", "action": "create", "delivery": "rule", "rules": ["r1"], "source_ids": ["s1"]},
            {"topic": "b", "action": "update", "delivery": "rule", "rules": ["r2"], "source_ids": ["s2"]},
            {"topic": "c", "action": "remove", "delivery": "rule", "rules": [], "source_ids": ["s3"]},
        ])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 3

    def test_filters_invalid_action(self) -> None:
        text = '[{"topic":"t","action":"invalid","delivery":"rule","rules":["r"],"source_ids":["s"]}]'
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_missing_topic(self) -> None:
        text = '[{"action":"create","delivery":"rule","rules":["r"],"source_ids":["s"]}]'
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_non_array_rules(self) -> None:
        text = '[{"topic":"t","action":"create","delivery":"rule","rules":"not-array","source_ids":["s"]}]'
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_non_array_source_ids(self) -> None:
        text = '[{"topic":"t","action":"create","delivery":"rule","rules":["r"],"source_ids":"not-array"}]'
        assert parse_crystallize_response(text) == ([], [])

    def test_returns_empty_when_no_json(self) -> None:
        assert parse_crystallize_response("No patterns detected.") == ([], [])

    def test_returns_empty_for_malformed_json(self) -> None:
        assert parse_crystallize_response("[{bad}]") == ([], [])

    def test_handles_json_embedded_in_text(self) -> None:
        text = (
            'Here are the results:\n\n'
            '[{"topic":"embedded","action":"create","delivery":"rule",'
            '"rules":["found it"],"source_ids":["e1"]}]\n\n'
            "That's all."
        )
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].topic == "embedded"

    def test_parses_downgrade_action(self) -> None:
        text = json.dumps([{
            "topic": "low-confidence",
            "action": "downgrade",
            "delivery": "store",
            "rules": ["Old rule"],
            "source_ids": ["id1"],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].action == "downgrade"

    def test_parses_delivery_rule(self) -> None:
        text = json.dumps([{
            "topic": "high-confidence",
            "action": "create",
            "delivery": "rule",
            "rules": ["Always use this"],
            "source_ids": ["id1"],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].delivery == "rule"

    def test_parses_delivery_skill_with_metadata(self) -> None:
        text = json.dumps([{
            "topic": "deploy-workflow",
            "action": "create",
            "delivery": "skill",
            "rules": ["Deployment procedure"],
            "source_ids": ["id1"],
            "skill_metadata": {
                "description": "Deploy app to production",
                "when_to_use": "When deploying",
                "procedure": ["Step 1", "Step 2"],
                "examples": ["deploy api"],
            },
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].delivery == "skill"
        assert result[0].skill_metadata is not None
        assert result[0].skill_metadata.description == "Deploy app to production"
        assert result[0].skill_metadata.when_to_use == "When deploying"
        assert result[0].skill_metadata.procedure == ["Step 1", "Step 2"]
        assert result[0].skill_metadata.examples == ["deploy api"]

    def test_parses_delivery_store(self) -> None:
        text = json.dumps([{
            "topic": "niche-case",
            "action": "create",
            "delivery": "store",
            "rules": ["Rarely used"],
            "source_ids": ["id1"],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].delivery == "store"

    def test_filters_invalid_delivery(self) -> None:
        text = json.dumps([{
            "topic": "test", "action": "create", "delivery": "invalid",
            "rules": ["rule"], "source_ids": ["id1"],
        }])
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_skill_without_metadata(self) -> None:
        text = json.dumps([{
            "topic": "test", "action": "create", "delivery": "skill",
            "rules": ["rule"], "source_ids": ["id1"],
        }])
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_skill_with_incomplete_metadata(self) -> None:
        text = json.dumps([{
            "topic": "test", "action": "create", "delivery": "skill",
            "rules": ["rule"], "source_ids": ["id1"],
            "skill_metadata": {"description": "Missing procedure and when_to_use"},
        }])
        assert parse_crystallize_response(text) == ([], [])

    def test_accepts_skill_without_examples(self) -> None:
        text = json.dumps([{
            "topic": "test", "action": "create", "delivery": "skill",
            "rules": ["rule"], "source_ids": ["id1"],
            "skill_metadata": {
                "description": "Test skill",
                "when_to_use": "When testing",
                "procedure": ["Do this"],
            },
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].skill_metadata is not None
        assert result[0].skill_metadata.examples is None

    def test_parses_user_conflicts(self) -> None:
        text = json.dumps([{
            "topic": "style",
            "action": "create",
            "delivery": "rule",
            "rules": ["Use tabs"],
            "source_ids": ["id1"],
            "user_conflicts": [{
                "user_rule_file": "contribution.md",
                "conflicting_content": "Use spaces for indentation",
                "suggestion": "Consider aligning tab vs space preference",
            }],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].user_conflicts is not None
        assert len(result[0].user_conflicts) == 1
        assert result[0].user_conflicts[0].user_rule_file == "contribution.md"
        assert result[0].user_conflicts[0].conflicting_content == "Use spaces for indentation"

    def test_returns_none_user_conflicts_when_absent(self) -> None:
        text = json.dumps([{
            "topic": "style", "action": "create", "delivery": "rule",
            "rules": ["Use tabs"], "source_ids": ["id1"],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].user_conflicts is None

    def test_filters_invalid_user_conflicts(self) -> None:
        text = json.dumps([{
            "topic": "style", "action": "create", "delivery": "rule",
            "rules": ["Use tabs"], "source_ids": ["id1"],
            "user_conflicts": [
                {"user_rule_file": "valid.md", "conflicting_content": "content", "suggestion": "fix it"},
                {"user_rule_file": "missing-fields"},
                "not-an-object",
                None,
            ],
        }])
        result, _ = parse_crystallize_response(text)
        assert len(result) == 1
        assert result[0].user_conflicts is not None
        assert len(result[0].user_conflicts) == 1
        assert result[0].user_conflicts[0].user_rule_file == "valid.md"

    def test_parses_multiple_user_conflicts(self) -> None:
        text = json.dumps([{
            "topic": "style", "action": "create", "delivery": "rule",
            "rules": ["Use tabs"], "source_ids": ["id1"],
            "user_conflicts": [
                {"user_rule_file": "a.md", "conflicting_content": "c1", "suggestion": "s1"},
                {"user_rule_file": "b.md", "conflicting_content": "c2", "suggestion": "s2"},
            ],
        }])
        result, _ = parse_crystallize_response(text)
        assert result[0].user_conflicts is not None
        assert len(result[0].user_conflicts) == 2


class TestCrystallize:
    CREATE_RESPONSE = json.dumps([{
        "topic": "typescript-style",
        "action": "create",
        "delivery": "rule",
        "rules": ["Use strict mode", "Prefer named exports"],
        "source_ids": ["id1", "id2"],
    }])

    @pytest.mark.asyncio
    async def test_returns_empty_report_for_empty_chunks(self) -> None:
        ctx = MockContext()
        report = await crystallize(ctx=ctx, chunks=[], model="test-model", project_root="/tmp/test")
        assert report == CrystallizeReport()
        assert len(ctx.calls) == 0

    @pytest.mark.asyncio
    async def test_sends_correct_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.CREATE_RESPONSE)
            chunks = [make_knowledge_chunk(id="c1", content="Test rule")]

            await crystallize(ctx=ctx, chunks=chunks, model="claude-sonnet-4-5-20250929", project_root=tmp)

            assert len(ctx.calls) == 1
            assert ctx.calls[0].system_prompt == CRYSTALLIZE_SYSTEM_PROMPT
            assert ctx.calls[0].model_preferences["hints"] == [
                {"name": "claude-sonnet-4-5-20250929"}
            ]
            assert ctx.calls[0].model_preferences["intelligencePriority"] == 0.9
            assert ctx.calls[0].max_tokens == 4096

    @pytest.mark.asyncio
    async def test_creates_rule_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.CREATE_RESPONSE)
            chunks = [make_knowledge_chunk(id="c1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.created == ["distill-typescript-style.md"]
            assert report.total_rules == 2

            file_path = os.path.join(tmp, ".claude", "rules", "distill-typescript-style.md")
            assert os.path.exists(file_path)
            with open(file_path) as f:
                content = f.read()
            assert "# typescript-style" in content
            assert "Use strict mode" in content
            assert "Prefer named exports" in content

    @pytest.mark.asyncio
    async def test_updates_rule_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, "distill-style.md"), "w") as f:
                f.write("# style\n- Old rule")

            update_response = json.dumps([{
                "topic": "style", "action": "update", "delivery": "rule",
                "rules": ["Updated rule"], "source_ids": ["u1"],
                "existing_file": "distill-style.md",
            }])

            ctx = MockContext(response=update_response)
            chunks = [make_knowledge_chunk(id="u1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.updated == ["distill-style.md"]
            with open(os.path.join(rules_dir, "distill-style.md")) as f:
                content = f.read()
            assert "Updated rule" in content
            assert "Old rule" not in content

    @pytest.mark.asyncio
    async def test_removes_rule_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            file_path = os.path.join(rules_dir, "distill-obsolete.md")
            with open(file_path, "w") as f:
                f.write("# obsolete\n- Old rule")
            assert os.path.exists(file_path)

            remove_response = json.dumps([{
                "topic": "obsolete", "action": "remove", "delivery": "rule",
                "rules": [], "source_ids": ["r1"],
                "existing_file": "distill-obsolete.md",
            }])

            ctx = MockContext(response=remove_response)
            chunks = [make_knowledge_chunk(id="r1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.removed == ["distill-obsolete.md"]
            assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_reports_mixed_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, "distill-old.md"), "w") as f:
                f.write("# old\n- Rule")
            with open(os.path.join(rules_dir, "distill-dead.md"), "w") as f:
                f.write("# dead\n- Rule")

            mixed_response = json.dumps([
                {"topic": "new-topic", "action": "create", "delivery": "rule", "rules": ["New rule"], "source_ids": ["n1"]},
                {"topic": "old", "action": "update", "delivery": "rule", "rules": ["Better rule"], "source_ids": ["o1"], "existing_file": "distill-old.md"},
                {"topic": "dead", "action": "remove", "delivery": "rule", "rules": [], "source_ids": ["d1"], "existing_file": "distill-dead.md"},
            ])

            ctx = MockContext(response=mixed_response)
            chunks = [make_knowledge_chunk(id="n1"), make_knowledge_chunk(id="o1"), make_knowledge_chunk(id="d1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.created == ["distill-new-topic.md"]
            assert report.updated == ["distill-old.md"]
            assert report.removed == ["distill-dead.md"]
            assert report.total_rules == 2  # 1 from create + 1 from update

    @pytest.mark.asyncio
    async def test_handles_multiple_creates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            mixed_response = json.dumps([
                {"topic": "a", "action": "create", "delivery": "rule", "rules": ["r1", "r2"], "source_ids": ["s1"]},
                {"topic": "b", "action": "create", "delivery": "rule", "rules": ["r3"], "source_ids": ["s2"]},
            ])

            ctx = MockContext(response=mixed_response)
            chunks = [make_knowledge_chunk()]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert len(report.created) == 2
            assert report.total_rules == 3

    @pytest.mark.asyncio
    async def test_uses_project_rules_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.CREATE_RESPONSE)
            chunks = [make_knowledge_chunk()]

            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            file_path = os.path.join(tmp, ".claude", "rules", "distill-typescript-style.md")
            assert os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_reads_existing_rules_into_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, "distill-existing.md"), "w") as f:
                f.write("# existing\n- Pre-existing rule")

            ctx = MockContext(response="[]")
            chunks = [make_knowledge_chunk()]

            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            prompt_text = ctx.calls[0].messages[0]["content"]
            assert "Pre-existing rule" in prompt_text

    @pytest.mark.asyncio
    async def test_returns_empty_report_when_llm_returns_no_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response="[]")
            chunks = [make_knowledge_chunk()]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report == CrystallizeReport()

    @pytest.mark.asyncio
    async def test_propagates_non_sampling_errors(self) -> None:
        ctx = MockContext(error=Exception("network timeout"))
        chunks = [make_knowledge_chunk()]

        with pytest.raises(Exception, match="network timeout"):
            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root="/tmp/test")

    @pytest.mark.asyncio
    async def test_wraps_sampling_not_supported_error(self) -> None:
        ctx = MockContext(error=Exception("Method not found: sampling/createMessage"))
        chunks = [make_knowledge_chunk()]

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root="/tmp/test")

    @pytest.mark.asyncio
    async def test_collects_user_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            response = json.dumps([{
                "topic": "indent-style",
                "action": "create",
                "delivery": "rule",
                "rules": ["Use tabs for indentation"],
                "source_ids": ["c1"],
                "user_conflicts": [{
                    "user_rule_file": "contribution.md",
                    "conflicting_content": "Use 2-space indentation",
                    "suggestion": "Align indentation preference",
                }],
            }])

            ctx = MockContext(response=response)
            chunks = [make_knowledge_chunk(id="c1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert len(report.user_conflicts) == 1
            assert report.user_conflicts[0].user_rule_file == "contribution.md"
            assert "distill-indent-style.md" in report.created

    @pytest.mark.asyncio
    async def test_returns_empty_user_conflicts_when_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.CREATE_RESPONSE)
            chunks = [make_knowledge_chunk(id="c1")]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.user_conflicts == []

    @pytest.mark.asyncio
    async def test_includes_user_rules_in_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rules_dir = os.path.join(tmp, ".claude", "rules")
            os.makedirs(rules_dir, exist_ok=True)
            with open(os.path.join(rules_dir, "contribution.md"), "w") as f:
                f.write("# Contribution\n- Use conventional commits")

            ctx = MockContext(response="[]")
            chunks = [make_knowledge_chunk()]

            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            prompt_text = ctx.calls[0].messages[0]["content"]
            assert "User Rules" in prompt_text
            assert "contribution.md" in prompt_text
            assert "conventional commits" in prompt_text

    @pytest.mark.asyncio
    async def test_rule_file_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.CREATE_RESPONSE)
            chunks = [make_knowledge_chunk()]

            await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            with open(os.path.join(tmp, ".claude", "rules", "distill-typescript-style.md")) as f:
                content = f.read()

            assert content.startswith("# typescript-style\n")
            assert "> Auto-generated by Distill" in content
            assert "- Use strict mode" in content
            assert "- Prefer named exports" in content
            assert "## Sources" in content
            assert "- id1" in content
            assert "- id2" in content


class TestParseCrystallizeResponseAgent:
    """Tests for agent delivery parsing."""

    AGENT_RESPONSE = json.dumps([{
        "topic": "deploy-workflow",
        "action": "create",
        "delivery": "agent",
        "rules": [],
        "source_ids": ["s1", "s2"],
        "agent_metadata": {
            "description": "Orchestrates the full deploy workflow",
            "skills": ["distill-pre-deploy-checks", "distill-deploy-to-prod", "distill-post-verify"],
            "tools": ["Bash", "Read"],
        }
    }])

    def test_parses_agent_delivery(self) -> None:
        results, _ = parse_crystallize_response(self.AGENT_RESPONSE)
        assert len(results) == 1
        r = results[0]
        assert r.delivery == "agent"
        assert r.agent_metadata is not None
        assert r.agent_metadata.description == "Orchestrates the full deploy workflow"
        assert r.agent_metadata.skills == [
            "distill-pre-deploy-checks",
            "distill-deploy-to-prod",
            "distill-post-verify",
        ]
        assert r.agent_metadata.tools == ["Bash", "Read"]

    def test_filters_agent_without_agent_metadata(self) -> None:
        text = json.dumps([{
            "topic": "workflow",
            "action": "create",
            "delivery": "agent",
            "rules": [],
            "source_ids": ["s1"],
        }])
        assert parse_crystallize_response(text) == ([], [])

    def test_filters_agent_with_incomplete_metadata(self) -> None:
        text = json.dumps([{
            "topic": "workflow",
            "action": "create",
            "delivery": "agent",
            "rules": [],
            "source_ids": ["s1"],
            "agent_metadata": {"description": "missing skills field"},
        }])
        assert parse_crystallize_response(text) == ([], [])

    def test_agent_tools_defaults_when_omitted(self) -> None:
        text = json.dumps([{
            "topic": "workflow",
            "action": "create",
            "delivery": "agent",
            "rules": [],
            "source_ids": ["s1"],
            "agent_metadata": {
                "description": "Test",
                "skills": ["distill-skill-a"],
            },
        }])
        results, _ = parse_crystallize_response(text)
        assert len(results) == 1
        assert results[0].agent_metadata.tools == ["Bash", "Read", "Write"]


class TestParseRelations:
    def test_parses_relations_from_object_format(self) -> None:
        text = json.dumps({
            "results": [{
                "topic": "style",
                "action": "create",
                "delivery": "rule",
                "rules": ["Use tabs"],
                "source_ids": ["id1"],
            }],
            "relations": [{
                "from_id": "chunk-a",
                "to_id": "chunk-b",
                "relation_type": "refines",
                "confidence": 0.85,
            }],
        })
        results, relations = parse_crystallize_response(text)
        assert len(results) == 1
        assert len(relations) == 1
        assert relations[0].from_id == "chunk-a"
        assert relations[0].to_id == "chunk-b"
        assert relations[0].relation_type == "refines"
        assert relations[0].confidence == 0.85

    def test_plain_array_format_returns_empty_relations(self) -> None:
        text = json.dumps([{
            "topic": "style",
            "action": "create",
            "delivery": "rule",
            "rules": ["r"],
            "source_ids": ["s"],
        }])
        results, relations = parse_crystallize_response(text)
        assert len(results) == 1
        assert relations == []

    def test_filters_invalid_relation_types(self) -> None:
        text = json.dumps({
            "results": [{
                "topic": "t",
                "action": "create",
                "delivery": "rule",
                "rules": ["r"],
                "source_ids": ["s"],
            }],
            "relations": [
                {"from_id": "a", "to_id": "b", "relation_type": "refines"},
                {"from_id": "c", "to_id": "d", "relation_type": "invalid_type"},
            ],
        })
        _, relations = parse_crystallize_response(text)
        assert len(relations) == 1
        assert relations[0].relation_type == "refines"

    def test_all_valid_relation_types(self) -> None:
        for rel_type in ("refines", "contradicts", "depends_on", "supersedes"):
            text = json.dumps({
                "results": [{"topic": "t", "action": "create", "delivery": "rule", "rules": ["r"], "source_ids": ["s"]}],
                "relations": [{"from_id": "a", "to_id": "b", "relation_type": rel_type}],
            })
            _, relations = parse_crystallize_response(text)
            assert len(relations) == 1, f"relation type '{rel_type}' should be valid"


class TestCrystallizeAgentOutput:
    """Tests for agent file writing via crystallize pipeline."""

    AGENT_RESPONSE = json.dumps([{
        "topic": "deploy-workflow",
        "action": "create",
        "delivery": "agent",
        "rules": [],
        "source_ids": ["s1"],
        "agent_metadata": {
            "description": "Full deploy workflow",
            "skills": ["distill-deploy-to-prod"],
            "tools": ["Bash"],
        },
    }])

    @pytest.mark.asyncio
    async def test_does_not_create_agent_when_disabled(self) -> None:
        """agents.enabled=False (default) → no agent file created."""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            ctx = MockContext(response=self.AGENT_RESPONSE)
            chunks = [make_knowledge_chunk()]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert report.agents_created == []
            assert not os.path.exists(os.path.join(tmp, ".claude", "agents"))

    @pytest.mark.asyncio
    async def test_creates_agent_file_when_enabled(self) -> None:
        """agents.enabled=True → writes distill-{topic}.md to .claude/agents/."""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, ".claude", "rules"), exist_ok=True)
            # Write config with agents enabled
            os.makedirs(os.path.join(tmp, ".distill"), exist_ok=True)
            with open(os.path.join(tmp, ".distill", "config.json"), "w") as f:
                json.dump({"outputs": {"agents": {"enabled": True}}}, f)

            ctx = MockContext(response=self.AGENT_RESPONSE)
            chunks = [make_knowledge_chunk()]

            report = await crystallize(ctx=ctx, chunks=chunks, model="test-model", project_root=tmp)

            assert "distill-deploy-workflow.md" in report.agents_created
            agent_path = os.path.join(tmp, ".claude", "agents", "distill-deploy-workflow.md")
            assert os.path.exists(agent_path)

            with open(agent_path) as f:
                content = f.read()
            assert "name: distill-deploy-workflow" in content
            assert "Full deploy workflow" in content
            assert "distill-deploy-to-prod" in content
