"""The coach replies in the user's language without copying prompt metaphors."""

from __future__ import annotations

from pathlib import Path

from mashbill.chat_context import build_system_prompt
from mashbill.chat_store import append_assistant, append_user, read_recent_transcript
from mashbill.coaching_principles import get_principles
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root

_COACH_SCOPES = (
    "project",
    "foundation",
    "actors",
    "services",
    "service:service_1",
    "entities",
    "feature:feature_1",
)


def test_every_coach_scope_carries_the_response_language_rules() -> None:
    """The reply contract is universal, including project and parametric scopes."""
    for scope in _COACH_SCOPES:
        prompt = build_system_prompt(scope)
        assert "Reply in the language the user uses" in prompt, scope
        assert "For Korean replies" in prompt, scope
        assert "Korean particles" in prompt, scope
        assert "spacing" in prompt, scope
        assert "standard technical terms" in prompt, scope
        assert "Do not translate figurative wording" in prompt, scope
        assert "do not invent metaphors" in prompt, scope
        assert "Do not describe abstract ideas as physical objects" in prompt, scope
        assert "미션에서 가치로 옮겼습니다" in prompt, scope
        assert "결정할 때 쓰는 기준입니다" in prompt, scope
        assert "가치로 섭니다" in prompt, scope
        assert "가치가 무게를 받습니다" in prompt, scope
        assert "reread" in prompt, scope


def test_coach_instructions_do_not_model_figurative_shorthand() -> None:
    """Known English metaphors must not remain as wording for the coach to copy."""
    prompts = "\n".join(build_system_prompt(scope) for scope in _COACH_SCOPES).lower()
    for phrase in (
        "pillar floats",
        "value terrain",
        "pit stop",
        "wobbler",
        "service landscape",
        "happy path as its spine",
        "land values",
        "land an item",
        "same breath",
        "batch, not a drip",
    ):
        assert phrase not in prompts, phrase


def test_korean_principles_use_direct_wording() -> None:
    """Tool-provided Korean criteria must not teach the coach coined metaphors."""
    principles = get_principles(None)
    for phrase in (
        "미션의 메아리",
        "가치 지도가 절반만 선다",
        "이 면의 양쪽에",
        "신뢰 제조면",
        "틀린 분해의 표본",
        "틀린 뭉침의 표본",
        "그 면이 굴리는",
    ):
        assert phrase not in principles, phrase


def test_replayed_history_preserves_facts_but_rejects_earlier_style(tmp_path: Path) -> None:
    """A fresh session keeps settled content without treating old prose as a model."""
    plot_root = resolve_plot_root(str(tmp_path))
    create_project(plot_root, "alpha", "Alpha")
    append_user(plot_root, "alpha", "foundation", "claude-code", "u1", "가치는 명확함입니다")
    awkward = "자를 빌려 쓰던 가치가 자를 갖게 됐네요."
    append_assistant(plot_root, "alpha", "foundation", "claude-code", "a1", awkward)

    transcript = read_recent_transcript(plot_root, "alpha", "foundation")

    assert "가치는 명확함입니다" in transcript
    assert awkward in transcript  # history is not rewritten or deleted
    assert "facts and decisions" in transcript
    assert "do not imitate" in transcript
