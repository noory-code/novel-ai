"""Slug-index graph query."""

from solera.formats import WorkItem
from solera.graph import items_by_slugs


def _item(item_id: str, realizes: list[str]) -> WorkItem:
    return WorkItem(
        id=item_id,
        level="story",
        status="todo",
        realizes=realizes,
        goal=item_id,
    )


def test_items_by_slugs_preserves_requested_keys_and_item_order() -> None:
    items = {
        "STORY-002": _item("STORY-002", ["feature/login", "entity/account"]),
        "STORY-001": _item("STORY-001", ["feature/login"]),
    }

    assert items_by_slugs(items, ["feature/login", "missing", "feature/login"]) == {
        "feature/login": ["STORY-002", "STORY-001"],
        "missing": [],
    }
