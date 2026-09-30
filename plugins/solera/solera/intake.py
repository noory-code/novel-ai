"""format F intake — the Solera "read" half of the mashbill↔Solera contract (INT-3).

Solera reads **format F** (docs/specs/format-f.md) as a *neutral* format: it
never imports Novel and never path-references the Novel tree (R8 — guarded by
``tests/test_independence.py``). The only thing it knows is the format's own
directory convention (a service bundle ``vS`` sits next to ``_project/{vP}``).

Two pieces:
- :func:`import_release` — copy a frozen ``vS`` bundle + its ``based_on`` ``vP``
  slice into ``specs/{label}/`` (immutable → immutable). Story files then point
  at ``specs/{label}`` (their own folder), so Solera runs with or without mashbill.
- :func:`diff_releases` — the deterministic ID-diff (changed / removed / added)
  that drives re-pinning on a re-publish. A pure function over two manifests.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Literal, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from solera.workspace import Workspace

# Cross-repo contract guard (format-f.md §7): the format F version this reader
# understands. Must move in lock-step with Novel's ``format_f.FORMAT_F_VERSION``.
# A bundle stamped with any other version is refused rather than mis-read.
SUPPORTED_FORMAT_F_VERSION = 1


class _FormatFModel(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)


class _Element(_FormatFModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    hash: str = Field(pattern=r"^[0-9a-f]+$")
    label: str | None = None
    flow: bool | None = None


class _Anchors(_FormatFModel):
    core_values: list[str]
    identity: list[str]
    mission: str | None = None


class _Refs(_FormatFModel):
    anchors: _Anchors
    actors: list[str]
    entities: list[str]


def _reject_duplicate_ids(elements: list[_Element]) -> None:
    seen: set[str] = set()
    for element in elements:
        if element.id in seen:
            raise ValueError(f"duplicate element id: {element.id!r}")
        seen.add(element.id)


class _VersionedManifest(_FormatFModel):
    format_f_version: int

    @field_validator("format_f_version")
    @classmethod
    def _supported_version(cls, value: int) -> int:
        if value != SUPPORTED_FORMAT_F_VERSION:
            raise ValueError(
                f"unsupported format_f_version {value!r} "
                f"(this Solera reads {SUPPORTED_FORMAT_F_VERSION})"
            )
        return value


class _ServiceManifest(_VersionedManifest):
    scope: Literal["service"]
    service: str = Field(pattern=r"^service/")
    release: str = Field(pattern=r"^vS[1-9][0-9]*$")
    based_on: str
    git_sha: str
    category: str | None = None
    elements: list[_Element]
    refs: _Refs

    @field_validator("based_on", mode="before")
    @classmethod
    def _bare_project_release(cls, value: object) -> object:
        if isinstance(value, str) and not re.fullmatch(r"vP[1-9][0-9]*", value):
            raise ValueError(
                "based_on must be a bare release name like 'vP3'; paths such as "
                "'_project/vP3' are not allowed"
            )
        return value

    @model_validator(mode="after")
    def _validate_elements(self) -> Self:
        _reject_duplicate_ids(self.elements)
        if not any(element.id == self.service for element in self.elements):
            raise ValueError(
                f"service manifest elements must include the service id {self.service!r}"
            )
        return self


class _ProjectManifest(_VersionedManifest):
    scope: Literal["project"]
    release: str = Field(pattern=r"^vP[1-9][0-9]*$")
    git_sha: str
    elements: list[_Element]

    @model_validator(mode="after")
    def _validate_elements(self) -> Self:
        _reject_duplicate_ids(self.elements)
        return self


_ManifestT = TypeVar("_ManifestT", bound=_FormatFModel)


def _load_manifest(path: Path, model: type[_ManifestT]) -> _ManifestT:
    return model.model_validate_json(path.read_text(encoding="utf-8"))


def _validate_release_pair(service: _ServiceManifest, project: _ProjectManifest) -> None:
    if project.release != service.based_on:
        raise ValueError(
            f"project release {project.release!r} does not match "
            f"service based_on {service.based_on!r}"
        )


def _reject_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise ValueError(f"format F bundle contains a symlink: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"format F bundle contains a symlink: {path}")


def _element_hashes(elements: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, Any] = {}
    for element in elements:
        element_id = element["id"]
        if element_id in by_id:
            raise ValueError(f"duplicate element id: {element_id!r}")
        by_id[element_id] = element["hash"]
    return by_id


def _remove_temp_dir(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path)


def diff_releases(
    old_elements: list[dict[str, Any]], new_elements: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Compare two manifests' ``elements`` by stable id + content hash.

    - ``changed`` — same id, different hash → the work realizing it goes stale.
    - ``removed`` — id gone → that work is orphaned → escalate (not auto-repin).
    - ``added`` — new id → a new work candidate.

    Deterministic and pure (format-f.md §5): the harness must be able to trust
    the verdict, so this is plain code, never an LLM step.
    """
    old = _element_hashes(old_elements)
    new = _element_hashes(new_elements)
    return {
        "changed": sorted(i for i in old if i in new and old[i] != new[i]),
        "removed": sorted(i for i in old if i not in new),
        "added": sorted(i for i in new if i not in old),
    }


def load_imported_elements(ws: Workspace, label: str) -> list[dict[str, Any]]:
    """Read the ``elements`` of an already-imported service release
    (``specs/{label}/service/manifest.json``) — the input to a re-pin ID-diff.

    Stays inside Solera's own tree (the imported copy), never reaching back into
    Novel (R8). Raises :class:`FileNotFoundError` if the label was not imported.
    """
    manifest_path = ws.spec_dir(label) / "service" / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no imported release {label!r} at {manifest_path}")
    manifest = _load_manifest(manifest_path, _ServiceManifest)
    return [element.model_dump(exclude_none=True) for element in manifest.elements]


def import_release(ws: Workspace, source_vs_dir: Path, *, label: str) -> dict[str, Any]:
    """Copy a frozen service release ``vS`` (and the ``vP`` slice it is based on)
    into ``specs/{label}/`` and return the ``vS`` manifest.

    ``source_vs_dir`` is a published service bundle directory (e.g. the
    ``published/{slug}/vS{N}/`` mashbill wrote). The user wires that path in; Solera
    does not reach into Novel. The ``based_on`` ``vP`` lives at
    ``<published>/_project/{based_on}`` per the format's convention.
    """
    dest = ws.spec_dir(label)
    temp_prefix = f".{label}."
    if ws.specs_dir.is_dir():
        for old_temp in ws.specs_dir.iterdir():
            if old_temp.name.startswith(temp_prefix):
                _remove_temp_dir(old_temp)
    if dest.exists():
        raise FileExistsError(f"spec already imported: {dest}")

    _reject_symlinks(source_vs_dir)
    manifest = _load_manifest(source_vs_dir / "manifest.json", _ServiceManifest)
    project_root_path = source_vs_dir.parent.parent / "_project"
    if project_root_path.is_symlink():
        raise ValueError(f"format F bundle contains a symlink: {project_root_path}")
    project_root = project_root_path.resolve()
    vp_dir = project_root / manifest.based_on
    _reject_symlinks(vp_dir)
    resolved_vp_dir = vp_dir.resolve()
    try:
        resolved_vp_dir.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(
            f"based_on snapshot escapes the _project directory: {manifest.based_on!r}"
        ) from exc
    if not (vp_dir / "manifest.json").is_file():
        raise FileNotFoundError(f"based_on snapshot not found: {vp_dir}")

    project_manifest = _load_manifest(vp_dir / "manifest.json", _ProjectManifest)
    _validate_release_pair(manifest, project_manifest)

    ws.specs_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=temp_prefix, dir=ws.specs_dir))
    try:
        shutil.copytree(source_vs_dir, temp_dir / "service")
        shutil.copytree(vp_dir, temp_dir / "project")

        copied_service = _load_manifest(
            temp_dir / "service" / "manifest.json", _ServiceManifest
        )
        copied_project = _load_manifest(
            temp_dir / "project" / "manifest.json", _ProjectManifest
        )
        _validate_release_pair(copied_service, copied_project)

        if dest.exists():
            raise FileExistsError(f"spec already imported: {dest}")
        os.rename(temp_dir, dest)
    finally:
        if temp_dir.exists():
            _remove_temp_dir(temp_dir)

    return manifest.model_dump(exclude_none=True)
