"""format F intake (INT-3) — the Solera "read" half of the mashbill↔Solera contract.

Solera reads format F as a **neutral format** (docs/specs/format-f.md): it does
not import Novel or know the bundle came from Novel. These tests build synthetic
bundles by hand to prove exactly that independence — no plot_mcp anywhere.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pytest

from solera.errors import FormatError
from solera.intake import (
    diff_releases,
    import_release,
    load_imported_elements,
    load_imported_release,
)
from solera.workspace import Workspace


def test_diff_releases_changed_removed_added() -> None:
    old = [
        {"id": "feature/login", "kind": "feature", "hash": "aaa"},
        {"id": "service/auth", "kind": "service", "hash": "bbb"},
        {"id": "entity/session", "kind": "entity", "hash": "ccc"},
    ]
    new = [
        {"id": "feature/login", "kind": "feature", "hash": "AAA"},  # changed
        {"id": "service/auth", "kind": "service", "hash": "bbb"},  # same
        {"id": "feature/signup", "kind": "feature", "hash": "ddd"},  # added
        # entity/session removed
    ]
    d = diff_releases(old, new)
    assert d == {
        "changed": ["feature/login"],
        "removed": ["entity/session"],
        "added": ["feature/signup"],
    }


def _write_bundle(root: Path, rel: str, manifest: dict[str, object]) -> Path:
    d = root / rel
    (d / "design").mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (d / "design" / "service.md").write_text("# Auth\n", encoding="utf-8")
    return d


def _project_manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "format_f_version": 1,
        "scope": "project",
        "release": "vP1",
        "git_sha": "",
        "elements": [
            {"id": "actor/user", "kind": "actor", "hash": "0123456789abcdef"},
        ],
    }
    manifest.update(overrides)
    return manifest


def _service_manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "format_f_version": 1,
        "scope": "service",
        "service": "service/auth",
        "release": "vS1",
        "based_on": "vP1",
        "git_sha": "",
        "elements": [
            {"id": "service/auth", "kind": "service", "hash": "fedcba9876543210"},
        ],
        "refs": {
            "anchors": {"core_values": [], "identity": []},
            "actors": ["actor/user"],
            "entities": [],
        },
    }
    manifest.update(overrides)
    return manifest


def _write_valid_published(root: Path) -> tuple[Path, Path]:
    vp_dir = _write_bundle(root, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(root, "auth/vS1", _service_manifest())
    return vs_dir, vp_dir


@pytest.mark.parametrize("label", ["../x", "/abs", "a/b", "..", ""])
def test_import_rejects_path_like_labels_without_writing(tmp_path: Path, label: str) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / ".noory" / "solera")

    with pytest.raises(FormatError, match="name"):
        import_release(ws, vs_dir, label=label)

    assert not ws.specs_dir.exists()
    assert ws.lock_path.is_file()


@pytest.mark.parametrize("based_on", ["../../private", "_project/vP1"])
def test_import_rejects_non_bare_based_on(tmp_path: Path, based_on: str) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest(based_on=based_on))

    with pytest.raises(ValueError, match="based_on.*bare release"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize("tree", ["service", "project"])
def test_import_rejects_symlinks_in_source_trees(tmp_path: Path, tree: str) -> None:
    vs_dir, vp_dir = _write_valid_published(tmp_path / "published")
    source_tree = vs_dir if tree == "service" else vp_dir
    (source_tree / "design" / "linked.md").symlink_to(source_tree / "design" / "service.md")

    with pytest.raises(ValueError, match="symlink"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


def test_import_rejects_symlinked_project_bundle_directory(tmp_path: Path) -> None:
    vs_dir, vp_dir = _write_valid_published(tmp_path / "published")
    real_vp_dir = tmp_path / "real-vp1"
    vp_dir.rename(real_vp_dir)
    vp_dir.symlink_to(real_vp_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize(
    "elements",
    [
        None,
        {"id": "service/auth", "kind": "service", "hash": "a"},
        [],
    ],
)
def test_import_requires_service_elements_list_with_service_id(
    tmp_path: Path, elements: object
) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    manifest = _service_manifest()
    if elements is None:
        manifest.pop("elements")
    else:
        manifest["elements"] = elements
    vs_dir = _write_bundle(published, "auth/vS1", manifest)

    with pytest.raises(ValueError, match="elements|service"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize(
    ("field", "element"),
    [
        ("id", {"id": "", "kind": "service", "hash": "a"}),
        ("kind", {"id": "service/auth", "kind": "", "hash": "a"}),
        ("hash", {"id": "service/auth", "kind": "service", "hash": ""}),
        ("hash", {"id": "service/auth", "kind": "service", "hash": "ABC123"}),
    ],
)
def test_import_rejects_invalid_element_fields(
    tmp_path: Path, field: str, element: dict[str, str]
) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest(elements=[element]))

    with pytest.raises(ValueError, match=field):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize(
    "overrides",
    [
        {"service": "auth"},
        {"git_sha": 123},
        {"refs": {"anchors": {}, "actors": [], "entities": []}},
        {"refs": {"anchors": {"core_values": [], "identity": []}, "actors": "user"}},
    ],
)
def test_import_rejects_invalid_service_identity_and_refs(
    tmp_path: Path, overrides: dict[str, object]
) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest(**overrides))

    with pytest.raises(ValueError):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scope", "project"),
        ("release", "vS0"),
        ("release", "vP1"),
        ("based_on", "vP0"),
        ("based_on", "project-vP1"),
    ],
)
def test_import_rejects_invalid_service_scope_and_release_fields(
    tmp_path: Path, field: str, value: str
) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest(**{field: value}))

    with pytest.raises(ValueError, match=field):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


def test_import_rejects_project_release_different_from_based_on(tmp_path: Path) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest(release="vP2"))
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest())

    with pytest.raises(ValueError, match="release.*based_on"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize(
    ("field", "value"),
    [("scope", "service"), ("release", "vP0"), ("release", "vS1")],
)
def test_import_rejects_invalid_project_scope_and_release_fields(
    tmp_path: Path, field: str, value: str
) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest(**{field: value}))
    vs_dir = _write_bundle(published, "auth/vS1", _service_manifest())

    with pytest.raises(ValueError, match=field):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize("scope", ["service", "project"])
def test_import_rejects_duplicate_element_ids(tmp_path: Path, scope: str) -> None:
    published = tmp_path / "published"
    project = _project_manifest()
    service = _service_manifest()
    target = service if scope == "service" else project
    elements = list(cast(list[dict[str, object]], target["elements"]))
    elements.append(dict(elements[0]))
    target["elements"] = elements
    _write_bundle(published, "_project/vP1", project)
    vs_dir = _write_bundle(published, "auth/vS1", service)

    with pytest.raises(ValueError, match="duplicate element id"):
        import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")


@pytest.mark.parametrize("side", ["old", "new"])
def test_diff_releases_rejects_duplicate_ids(side: str) -> None:
    duplicate = [{"id": "feature/x", "hash": "a"}, {"id": "feature/x", "hash": "b"}]
    old = duplicate if side == "old" else []
    new = duplicate if side == "new" else []

    with pytest.raises(ValueError, match="duplicate element id"):
        diff_releases(old, new)


def test_failed_second_copy_is_cleaned_up_and_retry_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    real_copytree = shutil.copytree
    calls = 0

    def fail_second_copy(*args: Any, **kwargs: Any) -> Path:
        nonlocal calls
        source = Path(args[0])
        if source in {vs_dir, vs_dir.parent.parent / "_project" / "vP1"}:
            calls += 1
            if calls == 2:
                raise OSError("simulated project copy failure")
        return Path(real_copytree(*args, **kwargs))

    monkeypatch.setattr("solera.intake.shutil.copytree", fail_second_copy)

    with pytest.raises(OSError, match="simulated"):
        import_release(ws, vs_dir, label="auth")

    assert not ws.spec_dir("auth").exists()
    assert not any(path.name.startswith(".auth.") for path in ws.specs_dir.iterdir())

    import_release(ws, vs_dir, label="auth")
    assert (ws.spec_dir("auth") / "service" / "manifest.json").is_file()
    assert (ws.spec_dir("auth") / "project" / "manifest.json").is_file()


def test_import_removes_stale_temp_directory_for_same_label(tmp_path: Path) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    stale = ws.specs_dir / ".auth.abandoned"
    stale.mkdir(parents=True)
    (stale / "partial").write_text("incomplete")

    import_release(ws, vs_dir, label="auth")

    assert not stale.exists()


def test_duplicate_import_still_removes_stale_temp_directory(tmp_path: Path) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    import_release(ws, vs_dir, label="auth")
    stale = ws.specs_dir / ".auth.abandoned"
    stale.mkdir()

    with pytest.raises(FileExistsError, match="already imported"):
        import_release(ws, vs_dir, label="auth")

    assert not stale.exists()


def test_import_revalidates_copied_manifests_before_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    real_copytree = shutil.copytree

    def corrupt_service_copy(*args: Any, **kwargs: Any) -> Path:
        result = Path(real_copytree(*args, **kwargs))
        if Path(args[0]) == vs_dir:
            manifest_path = result / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest.pop("elements")
            manifest_path.write_text(json.dumps(manifest))
        return result

    monkeypatch.setattr("solera.intake.shutil.copytree", corrupt_service_copy)

    with pytest.raises(ValueError, match="elements"):
        import_release(ws, vs_dir, label="auth")

    assert not ws.spec_dir("auth").exists()
    assert not any(path.name.startswith(".auth.") for path in ws.specs_dir.iterdir())


def test_import_accepts_legacy_unlabelled_elements_and_future_fields(tmp_path: Path) -> None:
    published = tmp_path / "published"
    project = _project_manifest(blueprint_version="v9.9.9", future_project_field=True)
    service = _service_manifest(future_service_field={"anything": "goes"})
    _write_bundle(published, "_project/vP1", project)
    vs_dir = _write_bundle(published, "auth/vS1", service)

    manifest = import_release(Workspace(tmp_path / "ws"), vs_dir, label="auth")

    assert manifest["elements"][0]["hash"] == "fedcba9876543210"


def test_load_imported_elements_uses_full_service_manifest_validation(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / "ws")
    manifest_dir = ws.specs_dir / "broken" / "service"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "manifest.json").write_text(
        json.dumps({"format_f_version": 1, "scope": "service"}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="elements"):
        load_imported_elements(ws, "broken")


def test_import_rejects_unsupported_format_f_version(tmp_path: Path) -> None:
    """Cross-repo contract guard (INT-1c): the reader pins the format version it
    understands, so a mashbill that bumps format_f_version without Solera following
    fails loudly here instead of silently mis-reading the contract."""
    from solera.intake import SUPPORTED_FORMAT_F_VERSION

    published = tmp_path / "published"
    _write_bundle(
        published,
        "_project/vP1",
        _project_manifest(),
    )
    vs_dir = _write_bundle(
        published,
        "auth/vS1",
        _service_manifest(format_f_version=SUPPORTED_FORMAT_F_VERSION + 999),
    )
    ws = Workspace(tmp_path / ".noory" / "solera")
    with pytest.raises(ValueError, match="format_f_version"):
        import_release(ws, vs_dir, label="vS1")


def test_import_release_copies_service_and_its_project_slice(tmp_path: Path) -> None:
    # Synthetic published tree (as Novel would write it) — NO plot import.
    published = tmp_path / "published"
    vs_dir, _ = _write_valid_published(published)

    ws = Workspace(tmp_path / ".noory" / "solera")
    manifest = import_release(ws, vs_dir, label="vS1")

    assert manifest["service"] == "service/auth"
    spec = ws.specs_dir / "vS1"
    assert (spec / "service" / "manifest.json").is_file()  # the vS bundle
    assert (spec / "project" / "manifest.json").is_file()  # its based_on vP slice
    # import is a copy — the source is untouched (immutable→immutable)
    assert (vs_dir / "manifest.json").is_file()


def test_import_release_keeps_service_category_in_copy_and_loaded_manifest(tmp_path: Path) -> None:
    published = tmp_path / "published"
    _write_bundle(published, "_project/vP1", _project_manifest())
    vs_dir = _write_bundle(
        published, "auth/vS1", _service_manifest(category="category/identity")
    )
    ws = Workspace(tmp_path / "ws")

    imported = import_release(ws, vs_dir, label="auth")
    copied = json.loads((ws.spec_dir("auth") / "service" / "manifest.json").read_text())
    loaded = load_imported_release(ws, "auth")

    assert imported["category"] == "category/identity"
    assert copied["category"] == "category/identity"
    assert loaded["service"]["category"] == "category/identity"


def test_load_imported_release_validates_and_returns_both_manifests(
    tmp_path: Path,
) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    import_release(ws, vs_dir, label="auth")

    release = load_imported_release(ws, "auth")

    assert release["service"]["release"] == "vS1"
    assert release["project"]["release"] == "vP1"


def test_import_rejects_conflicting_manifest_for_same_service_release(
    tmp_path: Path,
) -> None:
    published = tmp_path / "published"
    first = _write_bundle(published, "auth/vS1", _service_manifest())
    _write_bundle(published, "_project/vP1", _project_manifest())
    ws = Workspace(tmp_path / "ws")
    import_release(ws, first, label="first")

    conflicting_root = tmp_path / "conflicting"
    _write_bundle(conflicting_root, "_project/vP1", _project_manifest())
    second = _write_bundle(
        conflicting_root,
        "auth/vS1",
        _service_manifest(
            elements=[{"id": "service/auth", "kind": "service", "hash": "aaaaaaaaaaaaaaaa"}]
        ),
    )

    with pytest.raises(ValueError, match="service/auth.*vS1.*different manifest"):
        import_release(ws, second, label="second")

    assert not ws.spec_dir("second").exists()


def test_import_rejects_conflicting_project_manifest_for_same_based_on(
    tmp_path: Path,
) -> None:
    first, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")
    import_release(ws, first, label="first")

    conflicting_root = tmp_path / "conflicting"
    _write_bundle(
        conflicting_root,
        "_project/vP1",
        _project_manifest(
            elements=[{"id": "actor/user", "kind": "actor", "hash": "aaaaaaaaaaaaaaaa"}]
        ),
    )
    second = _write_bundle(
        conflicting_root,
        "billing/vS1",
        _service_manifest(
            service="service/billing",
            elements=[{"id": "service/billing", "kind": "service", "hash": "bbbbbbbbbbbbbbbb"}],
        ),
    )

    with pytest.raises(ValueError, match="vP1.*different manifest"):
        import_release(ws, second, label="second")


def test_import_allows_same_manifests_under_another_label(tmp_path: Path) -> None:
    vs_dir, _ = _write_valid_published(tmp_path / "published")
    ws = Workspace(tmp_path / "ws")

    import_release(ws, vs_dir, label="first")
    import_release(ws, vs_dir, label="second")

    assert load_imported_release(ws, "first") == load_imported_release(ws, "second")
