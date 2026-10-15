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
        assert "미션에서 가치로 옮겼어요" in prompt, scope
        assert "결정할 때 쓰는 기준이에요" in prompt, scope
        assert "가치로 섭니다" in prompt, scope
        assert "가치가 무게를 받습니다" in prompt, scope
        assert "reread" in prompt, scope


# The viewer's Korean labels (`ko.json` `tabs.*` and `kind.*`), which follow
# I18N_KO_GLOSSARY.md §1. The engine cannot read the viewer bundle (R8), so these
# literals mirror it. Only the names a model would otherwise translate or leave
# in English are listed; 미션·서비스·기능 come out right unprompted.
_SCREEN_NAMES = ("파운데이션", "코어밸류", "아이덴티티", "액터", "엔티티", "인터랙션")


def test_korean_replies_use_the_names_on_the_screen() -> None:
    """O-00000151: a Korean reply said "Foundation" twice and called a core value
    "핵심 가치" while the palette says 코어밸류. The reply contract names the
    screen's Korean words, in every scope."""
    for scope in _COACH_SCOPES:
        prompt = build_system_prompt(scope)
        assert "Korean screen names" in prompt, scope
        for name in _SCREEN_NAMES:
            assert name in prompt, (scope, name)


def test_korean_principles_name_core_values_as_the_screen_does() -> None:
    """The design-principles tool payload is Korean the coach quotes, so it must
    not teach the retired spellings (I18N_KO_GLOSSARY.md §1)."""
    principles = get_principles(None)
    assert "코어밸류를 확인하는 기준" in principles
    for retired in ("핵심 가치", "정체성", "행위자", "토대"):
        assert retired not in principles, retired


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


def test_korean_service_principles_follow_the_outcome_definition() -> None:
    """The tool-provided criteria must not restore the retired exchange test."""
    principles = get_principles("services")
    assert "사람이 이루려는 결과 하나" in principles
    assert "액터를 새로 만들지 않는다" in principles
    assert "여러 액터가 반드시" in principles
    assert "서로 주고받는 두 당사자가 있나" not in principles


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
