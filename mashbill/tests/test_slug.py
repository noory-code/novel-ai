"""folder_slug — node → folder path convention (v0.7)."""

from __future__ import annotations

from mashbill.slug import folder_slug, slugify


def test_mission_label_mission() -> None:
    assert folder_slug("mission", "Mission") == "foundation/mission-mission"


def test_core_value_with_korean_and_ascii() -> None:
    assert folder_slug("core_value", "관용 (Tolerance)") == ("foundation/core-value-관용-tolerance")


def test_identity_voice() -> None:
    assert folder_slug("identity", "Voice") == "foundation/identity-voice"


def test_canvas_override() -> None:
    assert folder_slug("actor", "User", canvas="actors") == "actors/actor-user"


def test_slugify_collapses_and_trims() -> None:
    assert slugify("  Hello --  World  ") == "hello-world"
    assert slugify("A  B  C") == "a-b-c"
    assert slugify("관용") == "관용"


def test_slugify_empty_falls_back_in_folder_slug() -> None:
    """An empty label still produces a meaningful path (kind only)."""
    assert folder_slug("mission", "") == "foundation/mission"
    assert folder_slug("mission", "!!!") == "foundation/mission"
