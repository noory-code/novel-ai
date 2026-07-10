#!/usr/bin/env python3
"""Validate novel-ai's marketplace and package metadata contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_URL = "https://github.com/noory-code/novel-ai"
PACKAGES = ("mashbill", "solera", "proof", "distill")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def project_version(package: str) -> str:
    if package == "mashbill":
        init_text = (ROOT / package / package / "__init__.py").read_text(encoding="utf-8")
        match = re.search(r'^__version__\s*=\s*"([^"]+)"$', init_text, re.MULTILINE)
        if match is None:
            raise AssertionError("mashbill __version__ was not found")
        return match.group(1)

    pyproject = (ROOT / package / "pyproject.toml").read_text(encoding="utf-8")
    project_section = pyproject.split("[project]", maxsplit=1)
    if len(project_section) != 2:
        raise AssertionError(f"{package}/pyproject.toml has no [project] table")
    project_text = project_section[1].split("\n[", maxsplit=1)[0]
    match = re.search(r'^version\s*=\s*"([^"]+)"$', project_text, re.MULTILINE)
    if match is None:
        raise AssertionError(f"{package}/pyproject.toml has no project.version")
    return match.group(1)


def main() -> int:
    marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    assert marketplace.get("name") == "novel-ai"

    entries = marketplace.get("plugins")
    assert isinstance(entries, list)
    names = tuple(entry.get("name") for entry in entries if isinstance(entry, dict))
    assert names == PACKAGES, f"marketplace packages differ: {names!r}"

    for package in PACKAGES:
        entry = next(
            item for item in entries if isinstance(item, dict) and item.get("name") == package
        )
        assert entry.get("source") == f"./{package}"

        manifest_path = ROOT / package / ".claude-plugin" / "plugin.json"
        manifest = load_json(manifest_path)
        assert manifest.get("name") == package
        assert manifest.get("repository") == REPOSITORY_URL
        assert manifest.get("homepage") == f"{REPOSITORY_URL}/tree/main/{package}"

        manifest_version = manifest.get("version")
        assert isinstance(manifest_version, str)
        package_version = project_version(package)
        assert manifest_version == package_version, (
            f"{package} version mismatch: manifest={manifest_version}, "
            f"package={package_version}"
        )

    print("novel-ai repository metadata: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
