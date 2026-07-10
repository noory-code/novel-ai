#!/usr/bin/env python3
"""Validate novel-ai's marketplace and package metadata contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = ROOT / "plugins"
REPOSITORY_URL = "https://github.com/noory-code/novel-ai"
PACKAGES = ("mashbill", "solera", "proof", "distill")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def public_documents() -> tuple[Path, ...]:
    """Return current public contracts; historical logs are intentionally excluded."""
    documents = {
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "CLAUDE.md",
    }
    documents.update((ROOT / "docs").rglob("*.md"))
    for package in PACKAGES:
        for name in ("README.md", "CONTRIBUTOR_GUIDE.md", "PRIVACY.md"):
            path = PLUGINS_ROOT / package / name
            if path.exists():
                documents.add(path)
    documents.update(
        {
            PLUGINS_ROOT / "mashbill" / "docs" / name
            for name in (
                "CHAT_ARCH.md",
                "CONCEPTS.md",
                "DOMAIN.md",
                "I18N_KO_GLOSSARY.md",
                "NEXT_SESSION.md",
                "ROADMAP.md",
                "SPEC.md",
                "VISION.md",
            )
        }
    )
    documents.update((PLUGINS_ROOT / "mashbill" / "docs" / "node-format").rglob("*.md"))
    return tuple(sorted(documents))


def validate_local_markdown_links() -> None:
    failures: list[str] = []
    for document in public_documents():
        text = document.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            elif " " in target:
                target = target.split(" ", maxsplit=1)[0]
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            path_text = unquote(
                target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
            )
            if not path_text:
                continue
            destination = (document.parent / path_text).resolve()
            try:
                destination.relative_to(ROOT.resolve())
            except ValueError:
                failures.append(
                    f"{document.relative_to(ROOT)} -> {raw_target} (outside repository)"
                )
                continue
            if not destination.exists():
                failures.append(f"{document.relative_to(ROOT)} -> {raw_target}")
    assert not failures, "broken local Markdown links:\n" + "\n".join(failures)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def project_version(package: str) -> str:
    if package == "mashbill":
        init_text = (PLUGINS_ROOT / package / package / "__init__.py").read_text(
            encoding="utf-8"
        )
        match = re.search(r'^__version__\s*=\s*"([^"]+)"$', init_text, re.MULTILINE)
        if match is None:
            raise AssertionError("mashbill __version__ was not found")
        return match.group(1)

    pyproject = (PLUGINS_ROOT / package / "pyproject.toml").read_text(encoding="utf-8")
    project_section = pyproject.split("[project]", maxsplit=1)
    if len(project_section) != 2:
        raise AssertionError(f"{package}/pyproject.toml has no [project] table")
    project_text = project_section[1].split("\n[", maxsplit=1)[0]
    match = re.search(r'^version\s*=\s*"([^"]+)"$', project_text, re.MULTILINE)
    if match is None:
        raise AssertionError(f"{package}/pyproject.toml has no project.version")
    return match.group(1)


def _local_link_target(document: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", maxsplit=1)[0]
    if target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    path_text = unquote(target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0])
    return (document.parent / path_text).resolve() if path_text else None


def validate_installed_skill_boundaries() -> None:
    """A marketplace caches each plugin directory, so skills must stay inside it."""
    failures: list[str] = []
    for package in PACKAGES:
        plugin_root = PLUGINS_ROOT / package
        for document in (plugin_root / "skills").rglob("*.md"):
            text = document.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK_RE.findall(text):
                destination = _local_link_target(document, raw_target)
                if destination is None:
                    continue
                try:
                    destination.relative_to(plugin_root.resolve())
                except ValueError:
                    failures.append(
                        f"{document.relative_to(ROOT)} -> {raw_target} (outside plugin)"
                    )
                    continue
                if not destination.exists():
                    failures.append(f"{document.relative_to(ROOT)} -> {raw_target}")
    assert not failures, "non-portable installed skill links:\n" + "\n".join(failures)


def validate_mcp_command(
    manifest: dict[str, object], package: str, root_variable: str
) -> None:
    servers = manifest.get("mcpServers")
    assert isinstance(servers, dict), f"{package}: inline mcpServers missing"
    server = servers.get(package)
    assert isinstance(server, dict), f"{package}: MCP server entry missing"
    assert server.get("command") == "uv"
    args = server.get("args")
    assert isinstance(args, list)
    assert root_variable in args, f"{package}: MCP command does not use {root_variable}"


def validate_marketplaces() -> None:
    claude = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    assert claude.get("name") == "novel-ai"
    claude_entries = claude.get("plugins")
    assert isinstance(claude_entries, list)
    claude_names = tuple(
        entry.get("name") for entry in claude_entries if isinstance(entry, dict)
    )
    assert claude_names == PACKAGES, (
        f"Claude marketplace packages differ: {claude_names!r}"
    )

    codex = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
    assert codex.get("name") == "novel-ai"
    codex_entries = codex.get("plugins")
    assert isinstance(codex_entries, list)
    codex_names = tuple(
        entry.get("name") for entry in codex_entries if isinstance(entry, dict)
    )
    assert codex_names == PACKAGES, (
        f"Codex marketplace packages differ: {codex_names!r}"
    )

    for package in PACKAGES:
        claude_entry = next(
            item
            for item in claude_entries
            if isinstance(item, dict) and item.get("name") == package
        )
        assert claude_entry.get("source") == f"./plugins/{package}"

        codex_entry = next(
            item
            for item in codex_entries
            if isinstance(item, dict) and item.get("name") == package
        )
        source = codex_entry.get("source")
        assert source == {"source": "local", "path": f"./plugins/{package}"}


def validate_package_manifests() -> None:
    for package in PACKAGES:
        package_version = project_version(package)
        expected_homepage = f"{REPOSITORY_URL}/tree/main/plugins/{package}"
        manifests = {
            "Claude": load_json(
                PLUGINS_ROOT / package / ".claude-plugin" / "plugin.json"
            ),
            "Codex": load_json(
                PLUGINS_ROOT / package / ".codex-plugin" / "plugin.json"
            ),
        }
        for host, manifest in manifests.items():
            assert manifest.get("name") == package
            assert manifest.get("repository") == REPOSITORY_URL
            assert manifest.get("homepage") == expected_homepage
            assert manifest.get("version") == package_version, (
                f"{package} {host} version mismatch: "
                f"manifest={manifest.get('version')}, package={package_version}"
            )

        validate_mcp_command(manifests["Codex"], package, "${PLUGIN_ROOT}")
        if package != "distill":
            validate_mcp_command(manifests["Claude"], package, "${CLAUDE_PLUGIN_ROOT}")

    distill_init = (
        PLUGINS_ROOT / "distill" / "src" / "distill" / "__init__.py"
    ).read_text(encoding="utf-8")
    assert f'__version__ = "{project_version("distill")}"' in distill_init


def validate_gemini_extension() -> None:
    manifest = load_json(ROOT / "gemini-extension.json")
    assert manifest.get("name") == "novel-ai"
    assert manifest.get("contextFileName") == "GEMINI.md"
    servers = manifest.get("mcpServers")
    assert isinstance(servers, dict)
    assert tuple(servers) == PACKAGES
    for package in PACKAGES:
        server = servers.get(package)
        assert isinstance(server, dict)
        assert server.get("command") == "uv"
        args = server.get("args")
        assert isinstance(args, list)
        expected_root = f"${{extensionPath}}${{/}}plugins${{/}}{package}"
        assert expected_root in args
    distill = servers["distill"]
    assert isinstance(distill, dict)
    assert distill.get("includeTools") == [
        "recall",
        "profile",
        "digest",
        "manage_entry",
        "store",
        "init",
    ]


def main() -> int:
    validate_marketplaces()
    validate_package_manifests()
    validate_gemini_extension()

    canonical_vision = (ROOT / "docs" / "VISION.md").read_bytes()
    packaged_vision = (PLUGINS_ROOT / "mashbill" / "docs" / "VISION.md").read_bytes()
    assert packaged_vision == canonical_vision, (
        "Mashbill's packaged VISION.md mirror drifted"
    )

    validate_local_markdown_links()
    validate_installed_skill_boundaries()

    print("novel-ai repository metadata and documentation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
