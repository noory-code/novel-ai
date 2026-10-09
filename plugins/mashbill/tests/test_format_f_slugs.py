from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.workspace import resolve_plot_root


def _node(node_id: str, kind: str, label: str) -> SimpleNamespace:
    return SimpleNamespace(id=node_id, kind=kind, label=label)


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("결제하기", True),
        ("AI 코치", True),
        ("결제 v2", True),
        ("Café", True),
        ("🚀", True),
        ("", True),
        ("Login", False),
        ("Sign up 2", False),
        ("2024", False),
        ("Login → Home", False),
    ],
)
def test_needs_english_slug(label: str, expected: bool) -> None:
    from mashbill.format_f_slugs import needs_english_slug

    assert needs_english_slug(label) is expected


def test_plan_slugs_reserves_automatic_names_before_provided_names() -> None:
    from mashbill.format_f_slugs import InvalidSlugNamesError, plan_slugs

    nodes = [
        _node("korean", "feature", "로그인"),
        _node("english", "feature", "Login"),
    ]

    with pytest.raises(InvalidSlugNamesError) as caught:
        plan_slugs({}, nodes, {"korean": "login"})

    assert caught.value.problems == [
        {
            "node_id": "korean",
            "slug": "login",
            "reason": "taken",
        }
    ]


def test_plan_slugs_keeps_store_and_dedupes_automatic_names() -> None:
    from mashbill.format_f_slugs import plan_slugs

    nodes = [
        _node("old", "actor", "바뀐 이름"),
        _node("first", "actor", "User"),
        _node("second", "actor", "User"),
        _node("needed", "actor", "운영자"),
    ]

    plan = plan_slugs(
        {"old": "actor/x", "elsewhere": "actor/user"},
        nodes,
        {"needed": "operator"},
    )

    assert plan.slugs == {
        "old": "actor/x",
        "first": "actor/user-2",
        "second": "actor/user-3",
        "needed": "actor/operator",
    }
    assert plan.new == {
        "first": "actor/user-2",
        "second": "actor/user-3",
        "needed": "actor/operator",
    }


@pytest.mark.parametrize("slug", ["Checkout", "check_out", "-a", "a--b", "결제", ""])
def test_plan_slugs_rejects_invalid_tail(slug: str) -> None:
    from mashbill.format_f_slugs import InvalidSlugNamesError, plan_slugs

    with pytest.raises(InvalidSlugNamesError) as caught:
        plan_slugs({}, [_node("n1", "feature", "결제")], {"n1": slug})

    assert caught.value.problems[0]["reason"] == "format"


def test_plan_slugs_reports_taken_duplicate_and_not_needed() -> None:
    from mashbill.format_f_slugs import InvalidSlugNamesError, plan_slugs

    nodes = [
        _node("taken", "actor", "운영자"),
        _node("dup-a", "actor", "구매자"),
        _node("dup-b", "actor", "판매자"),
        _node("english", "actor", "Admin"),
    ]

    with pytest.raises(InvalidSlugNamesError) as caught:
        plan_slugs(
            {"other": "actor/operator"},
            nodes,
            {
                "taken": "operator",
                "dup-a": "person",
                "dup-b": "person",
                "english": "administrator",
            },
        )

    assert {problem["reason"] for problem in caught.value.problems} == {
        "taken",
        "duplicate",
        "not_needed",
    }


def test_plan_slugs_lists_missing_names_after_invalid_checks() -> None:
    from mashbill.format_f_slugs import SlugNamesNeededError, plan_slugs

    with pytest.raises(SlugNamesNeededError) as caught:
        plan_slugs(
            {},
            [
                _node("n1", "feature", "결제하기"),
                _node("n2", "actor", "운영자"),
            ],
            {"n1": "checkout"},
        )

    assert caught.value.nodes == [{"node_id": "n2", "kind": "actor", "label": "운영자"}]
    assert 'n2 (actor) "운영자"' in str(caught.value)


def test_plan_slugs_excludes_mission_from_required_names() -> None:
    from mashbill.format_f_slugs import plan_slugs

    plan = plan_slugs({}, [_node("mission-id", "mission", "우리의 미션")], None)

    assert plan.slugs == {"mission-id": "mission"}
    assert plan.new == {"mission-id": "mission"}


def test_plan_slugs_accepts_stored_mission_id_for_mission() -> None:
    from mashbill.format_f_slugs import plan_slugs

    plan = plan_slugs(
        {"mission-id": "mission"},
        [_node("mission-id", "mission", "Our mission")],
        None,
    )

    assert plan.slugs == {"mission-id": "mission"}
    assert plan.new == {}


def test_plan_slugs_rejects_mission_id_for_actor() -> None:
    from mashbill.format_f_slugs import plan_slugs

    with pytest.raises(ValueError) as caught:
        plan_slugs(
            {"actor-id": "mission"},
            [_node("actor-id", "actor", "Actor")],
            None,
        )

    assert str(caught.value) == (
        "_slugs.json has an invalid id for actor-id: 'mission' (only the mission node may use it)"
    )


def test_pending_slug_names_includes_automatic_ids_in_taken() -> None:
    from mashbill.format_f_slugs import pending_slug_names

    korean = _node("n1", "feature", "결제")
    needed, taken = pending_slug_names(
        {"old": "feature/history"},
        [korean, _node("n2", "feature", "Login")],
    )

    assert needed == [korean]
    assert taken == ["feature/history", "feature/login"]


def test_read_slug_store_accepts_legacy_ids(tmp_path: Path) -> None:
    from mashbill.format_f_slugs import read_slug_store, slug_store_path

    expected = {
        "a": "actor/x",
        "b": "actor/x-2",
        "c": "entity/tbd",
        "d": "mission",
    }
    slug_store_path(tmp_path, "alpha").write_text(json.dumps(expected), encoding="utf-8")

    assert read_slug_store(tmp_path, "alpha") == expected


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    return resolve_plot_root(str(tmp_path))


def _add_service(
    plot_root: Path,
    *,
    service_label: str = "Auth",
    feature_label: str | None = None,
) -> None:
    from mashbill.models import FeatureNode, ServiceNode, SketchEdge

    service = ServiceNode(id="svc", label=service_label)
    nodes: list[ServiceNode | FeatureNode] = [service]
    edges = []
    if feature_label is not None:
        nodes.append(FeatureNode(id="feature", label=feature_label))
        edges.append(SketchEdge(id="owns", source="svc", target="feature"))
    services = read_canvas(plot_root, "alpha", "services")
    write_canvas(
        plot_root,
        "alpha",
        services.model_copy(update={"nodes": nodes, "edges": edges}),
    )


@pytest.mark.parametrize(
    ("stored", "node_id", "value"),
    [
        ({"svc": "service/.."}, "svc", "service/.."),
        ({"svc": "service/Checkout"}, "svc", "service/Checkout"),
        ({"svc": "service/"}, "svc", "service/"),
        ({"svc": ".."}, "svc", ".."),
        ({"svc": 7}, "svc", 7),
        ({"": "actor/x"}, "", "actor/x"),
        (["service/checkout"], "<root>", ["service/checkout"]),
    ],
)
def test_invalid_slug_store_stops_publish_before_planning_or_writes(
    plot_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    stored: object,
    node_id: str,
    value: object,
) -> None:
    import mashbill.format_f as format_f
    from mashbill.format_f_slugs import slug_store_path

    create_project(plot_root, "alpha", "Alpha")
    slug_store_path(plot_root, "alpha").write_text(json.dumps(stored), encoding="utf-8")

    def unexpected_plan(*args: object, **kwargs: object) -> None:
        pytest.fail("plan_slugs must not run for an invalid slug store")

    monkeypatch.setattr(format_f, "plan_slugs", unexpected_plan)

    with pytest.raises(ValueError) as caught:
        format_f.publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    assert str(caught.value) == (
        f"_slugs.json has an invalid id for {node_id}: '{value}' "
        "(expected kind/tail with lowercase letters, digits and single hyphens)"
    )
    assert not (plot_root / "published").exists()


def test_invalid_stored_mission_id_stops_publish_before_writes(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot
    from mashbill.format_f_slugs import slug_store_path
    from mashbill.models import MissionNode

    create_project(plot_root, "alpha", "Alpha")
    foundation = read_canvas(plot_root, "alpha", "foundation")
    write_canvas(
        plot_root,
        "alpha",
        foundation.model_copy(
            update={"nodes": [MissionNode(id="mission-id", label="Our mission")]}
        ),
    )
    slug_store_path(plot_root, "alpha").write_text(
        json.dumps({"mission-id": "actor/x"}), encoding="utf-8"
    )

    with pytest.raises(ValueError) as caught:
        publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    assert str(caught.value) == (
        "_slugs.json has an invalid id for mission-id: 'actor/x' "
        "(the mission's id is always 'mission')"
    )
    assert not (plot_root / "published").exists()


def test_publish_korean_feature_uses_confirmed_file_name(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _add_service(plot_root, feature_label="결제하기")
    publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    manifest = publish_service(plot_root, "alpha", "svc", slugs={"feature": "checkout"})

    assert next(item["id"] for item in manifest["elements"] if item["kind"] == "feature") == (
        "feature/checkout"
    )
    assert (
        plot_root / "published" / "auth" / "vS1" / "design" / "features" / "checkout.md"
    ).is_file()


def test_publish_korean_service_uses_confirmed_folder_name(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot, publish_service

    create_project(plot_root, "alpha", "Alpha")
    _add_service(plot_root, service_label="결제")
    publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    manifest = publish_service(plot_root, "alpha", "svc", slugs={"svc": "payments"})

    assert manifest["service"] == "service/payments"
    assert (plot_root / "published" / "payments" / "vS1" / "manifest.json").is_file()


def test_missing_name_writes_neither_snapshot_nor_store(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot
    from mashbill.format_f_slugs import SlugNamesNeededError, slug_store_path
    from mashbill.models import ActorNode

    create_project(plot_root, "alpha", "Alpha")
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(update={"nodes": [ActorNode(id="operator", label="운영자")]}),
    )

    with pytest.raises(SlugNamesNeededError, match="operator"):
        publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    assert not (plot_root / "published" / "_project").exists()
    assert not slug_store_path(plot_root, "alpha").exists()


@pytest.mark.parametrize("tail", ["Checkout", "check_out", "-a", "a--b", "결제", ""])
def test_invalid_name_writes_nothing(plot_root: Path, tail: str) -> None:
    from mashbill.format_f import publish_project_snapshot
    from mashbill.format_f_slugs import InvalidSlugNamesError, slug_store_path
    from mashbill.models import ActorNode

    create_project(plot_root, "alpha", "Alpha")
    actors = read_canvas(plot_root, "alpha", "actors")
    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(update={"nodes": [ActorNode(id="operator", label="운영자")]}),
    )

    with pytest.raises(InvalidSlugNamesError):
        publish_project_snapshot(
            plot_root,
            "alpha",
            blueprint_version="v0.1.1",
            slugs={"operator": tail},
        )

    assert not (plot_root / "published" / "_project").exists()
    assert not slug_store_path(plot_root, "alpha").exists()


def test_existing_slug_store_round_trips_and_only_adds_new_node(plot_root: Path) -> None:
    from mashbill.format_f import publish_project_snapshot
    from mashbill.format_f_slugs import slug_store_path
    from mashbill.models import ActorNode

    create_project(plot_root, "alpha", "Alpha")
    actors = read_canvas(plot_root, "alpha", "actors")
    original_nodes = [
        ActorNode(id="n1", label="운영자"),
        ActorNode(id="n2", label="사용자"),
        ActorNode(id="n3", label="User"),
    ]
    write_canvas(plot_root, "alpha", actors.model_copy(update={"nodes": original_nodes}))
    store_path = slug_store_path(plot_root, "alpha")
    previous = b'{"n1":"actor/x","n2":"actor/x-2","n3":"actor/user"}\n'
    store_path.write_bytes(previous)

    first = publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")

    assert {item["id"] for item in first["elements"]} == {
        "actor/x",
        "actor/x-2",
        "actor/user",
    }
    assert store_path.read_bytes() == previous

    write_canvas(
        plot_root,
        "alpha",
        actors.model_copy(update={"nodes": [*original_nodes, ActorNode(id="n4", label="관리자")]}),
    )
    publish_project_snapshot(
        plot_root,
        "alpha",
        blueprint_version="v0.1.2",
        slugs={"n4": "administrator"},
    )

    assert json.loads(store_path.read_text(encoding="utf-8")) == {
        "n1": "actor/x",
        "n2": "actor/x-2",
        "n3": "actor/user",
        "n4": "actor/administrator",
    }


def test_service_write_failure_removes_release_folder_and_restores_store(
    plot_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import mashbill.format_f as format_f
    from mashbill.format_f_slugs import slug_store_path

    create_project(plot_root, "alpha", "Alpha")
    _add_service(plot_root, service_label="결제")
    format_f.publish_project_snapshot(plot_root, "alpha", blueprint_version="v0.1.1")
    from mashbill.storage import _write_json

    real_write_json = _write_json

    def fail_manifest(path: Path, payload: dict[str, object]) -> None:
        if path.name == "manifest.json" and "vS" in str(path):
            raise RuntimeError("manifest write failed")
        real_write_json(path, payload)

    monkeypatch.setattr(format_f, "_write_json", fail_manifest)

    with pytest.raises(RuntimeError, match="manifest write failed"):
        format_f.publish_service(
            plot_root,
            "alpha",
            "svc",
            slugs={"svc": "payments"},
        )

    assert not (plot_root / "published" / "payments").exists()
    assert not slug_store_path(plot_root, "alpha").exists()
