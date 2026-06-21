"""Artifact homes — staging for process output, tagged not versioned.

Each kind of output has exactly one home (see ``docs/ARTIFACT_HOMES.md``):

- code -> the repository
- code-derived output (generated ERD, API docs) -> the repo's ``docs/generated``
- design intent -> Plot (folded back via retrospective / feedback); no home here
  when Plot is absent
- process artifacts (scratch output on the way) -> ``stories/{id}/artifacts/``

Process artifacts stage under a Story and carry **tags** — ``about`` (which id)
and ``from`` (where they came from) — never version numbers. The misplacement
guard is light: it flags output that landed in the wrong home, e.g. source code
staged in artifacts, where it should be committed to the repo instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .errors import FormatError
from .formats import _split_frontmatter
from .workspace import Workspace

# Source-code suffixes that belong in the repository, not in artifacts staging.
CODE_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java",
        ".rb", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".kt", ".swift", ".php",
    }
)


class ArtifactRef(BaseModel):
    """A staged artifact: a filename plus neutral tags (about / from)."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    file: str
    about: list[str] = Field(default_factory=list)
    from_: str | None = Field(default=None, alias="from")


@dataclass(frozen=True)
class Misplacement:
    """A file found in the wrong home, with the reason it does not belong."""

    path: Path
    reason: str


def parse_manifest(text: str) -> list[ArtifactRef]:
    """Parse an artifacts manifest: ``artifacts:`` is a list of tagged refs."""
    data, _ = _split_frontmatter(text)
    raw = data.get("artifacts", [])
    if not isinstance(raw, list):
        raise FormatError("artifacts manifest: 'artifacts' must be a list")
    refs: list[ArtifactRef] = []
    for entry in raw:
        try:
            refs.append(ArtifactRef.model_validate(entry))
        except ValidationError as exc:
            raise FormatError(f"invalid artifact entry: {exc}") from exc
    return refs


def dump_manifest(refs: list[ArtifactRef]) -> str:
    """Serialize an artifacts manifest. Inverse of :func:`parse_manifest`."""
    items = [r.model_dump(by_alias=True, exclude_none=True) for r in refs]
    fm = yaml.safe_dump({"artifacts": items}, sort_keys=False, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n"


def find_misplaced_artifacts(ws: Workspace) -> list[Misplacement]:
    """Warn about files staged in artifacts/ that belong in another home.

    Currently flags source code (it belongs in the repository). Returns warnings,
    not errors — the guard advises; it does not block.
    """
    out: list[Misplacement] = []
    for story_id in ws.list_stories():
        adir = ws.artifacts_dir(story_id)
        if not adir.is_dir():
            continue
        for path in sorted(adir.rglob("*")):
            if path.is_file() and path.suffix.lower() in CODE_SUFFIXES:
                out.append(
                    Misplacement(
                        path=path,
                        reason="source code belongs in the repo, not in artifacts staging",
                    )
                )
    return out
