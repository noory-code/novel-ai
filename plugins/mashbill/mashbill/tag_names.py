"""Shared classification rules for project git tags."""

from __future__ import annotations

import re

_BLUEPRINT_VERSION_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def is_blueprint_version_tag(name: str) -> bool:
    """Return whether ``name`` is a published blueprint version tag."""
    return _BLUEPRINT_VERSION_TAG_RE.fullmatch(name) is not None
