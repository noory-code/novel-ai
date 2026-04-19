"""Markdown / frontmatter parsing primitives used by every reader.

These helpers are intentionally tolerant — real Solera workspaces contain
hand-edited files where quoting slipped or a required field was omitted.
Parsers surface under-populated nodes (and raise integrity flags upstream)
rather than hard-failing the read.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import yaml

from solera_mcp.models import STATUS_ICON_MAP, JourneyStep, WorkStatus

_log = logging.getLogger(__name__)

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)
_SECTION_RE = re.compile(r"^# (.+?)\n(.*?)(?=\n# |\Z)", re.MULTILINE | re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[[^\]]*?/?([\w.-]+?)(?:\|[^\]]*)?\]\]")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into (frontmatter dict, body).

    Malformed YAML frontmatter yields an empty dict and a warning log — real
    Solera workspaces contain hand-edited files where quoting slipped, and we
    prefer to surface them as under-populated nodes over hard-failing the read.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        _log.warning("malformed frontmatter: %s", exc)
        return {}, text[match.end() :]
    if not isinstance(fm, dict):
        return {}, text[match.end() :]
    return fm, text[match.end() :]


def parse_sections(body: str) -> dict[str, str]:
    """Split body by top-level `# Heading` blocks. Returns {heading: content}."""
    out: dict[str, str] = {}
    for m in _SECTION_RE.finditer(body):
        out[m.group(1).strip()] = m.group(2).strip()
    return out


def status_from_icon_or_text(raw: str | None) -> WorkStatus:
    """Map Time-bound status markers (icon or text) to the WorkStatus literal."""
    if not raw:
        return "pending"
    raw = raw.strip()
    for icon, status in STATUS_ICON_MAP.items():
        if icon in raw:
            return status
    lowered = raw.lower().replace("-", "_").replace(" ", "_")
    if lowered in ("pending", "in_progress", "complete", "on_hold", "cancelled"):
        return lowered  # type: ignore[return-value]
    return "pending"


def parse_bullet_list(section_text: str) -> list[str]:
    """Extract leading-`-` bullet items from a section body.

    Strips the leading `- ` and any trailing whitespace. Skips blank lines and
    HTML comment lines. Multi-line continuations of a bullet are not joined —
    a hand-edited Persona is unlikely to have them, and merging them would
    change the user's text without consent.
    """
    out: list[str] = []
    for raw in section_text.splitlines():
        line = raw.rstrip()
        if not line.lstrip().startswith("-"):
            continue
        text = line.lstrip()[1:].strip()
        if not text or text.startswith("<!--"):
            continue
        out.append(text)
    return out


_JOURNEY_STEP_ROW_RE = re.compile(
    r"^\|\s*(?P<n>\d+)\s*\|"
    r"\s*(?P<stage>[^|]*?)\s*\|"
    r"\s*(?P<step>[^|]*?)\s*\|"
    r"\s*(?P<touchpoint>[^|]*?)\s*\|"
    r"\s*(?P<emotion>[^|]*?)\s*\|"
    r"\s*(?P<pain>[^|]*?)\s*\|\s*$"
)


def parse_journey_steps_table(section_text: str) -> list[JourneyStep]:
    """Parse the Steps markdown table in a Journey file.

    Skips the header row (`| # | Stage | ...`) and the separator (`|---|---|...`).
    Tolerates malformed rows by skipping them; never raises.
    """
    steps: list[JourneyStep] = []
    for line in section_text.splitlines():
        # Filter out header / separator / non-data rows.
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "---" in stripped:
            continue
        # Skip the header row (first cell is non-numeric like "#").
        match = _JOURNEY_STEP_ROW_RE.match(stripped)
        if not match:
            continue
        try:
            n = int(match.group("n"))
        except ValueError:
            continue
        steps.append(
            JourneyStep(
                n=n,
                stage=match.group("stage"),
                step=match.group("step"),
                touchpoint=match.group("touchpoint"),
                emotion=match.group("emotion"),
                pain=match.group("pain"),
            )
        )
    return steps


def coerce_id_list(raw: Any) -> list[str]:
    """Frontmatter list fields may be a YAML list, a single string, or absent."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw if item is not None]
    return []


def extract_concept_id(bullet_line: str) -> str:
    """Pull a Concept id out of a Scope bullet.

    Accepted shapes:
        - authentication
        - [[../concepts/authentication]]
        - [[../concepts/authentication]] — annotation
        - [[../concepts/authentication|label]] — annotation
    """
    stripped = bullet_line.lstrip("- ").strip()
    wikilink = _WIKILINK_RE.search(stripped)
    if wikilink:
        return wikilink.group(1)
    # Bare id, optionally followed by em-dash annotation.
    return stripped.split("—")[0].split(" ")[0].strip()


def normalize_identity_stem(stem: str) -> str:
    """Strip Obsidian-style ``_N`` duplicate suffixes: ``vision_1`` → ``vision``."""
    return re.sub(r"_\d+$", "", stem).lower()
