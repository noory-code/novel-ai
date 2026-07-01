"""v0.13 Phase 3: heading-section markdown templates for Foundation nodes.

A Foundation node (mission / core_value / identity) carries human-readable
typed text (``definition`` / ``do`` / ``dont`` / ``what_we_do`` / ...)
that the user wants to read and edit as plain Markdown. Storing this
text in JSON (alongside graph fields like x/y) makes the file noisy and
disconnected from how a human reads it.

v0.13's split:
- canvas.json holds graph data (id, kind, label, x/y/w/h, color, shape,
  parent_id, refs, ``details_path``).
- ``{node-slug}.md`` holds typed text as Markdown sections, separated
  from a ``---`` rule below which the user can write free prose. Novel
  parses the sections back into the kind subclass's typed fields when
  it loads the canvas.

Format (example for a core_value node):

    # Tolerance

    ## Definition
    관용. 다양한 의견 존중.

    ## Do
    - 다른 의견을 끝까지 듣는다.

    ## Don't
    - 한 사람의 발언으로 결론 내린다.

    ---

    (free prose — Novel does not parse this)

Read is **lenient**: missing sections become empty strings, unknown
sections are preserved in warnings (so the user knows we couldn't map
them). The free-prose body (everything below the ``---`` rule) is
preserved verbatim and round-tripped on write.

Write is **strict**: Novel emits exactly the kind's known headings in
the documented order, then ``---``, then the preserved free prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from mashbill.models import FOUNDATION_TYPED_TEXT_FIELDS
from mashbill.schema_export import SECTION_LABELS

# Pattern for an H2 section header on its own line. We match `## Heading`
# but reject `###` (deeper) and require the heading to be the line's whole
# textual content.
_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
# Pattern for the typed-area terminator (a horizontal rule). We accept
# `---`, `***`, or `___` per CommonMark, on a line by itself.
_HR = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedTemplate:
    """Result of parsing a Foundation node's MD file."""

    typed_fields: dict[str, str]
    """Maps the kind's typed-text field names → text. Missing fields become
    empty strings; never raises."""

    free_prose: str
    """Everything below the typed area (after the ``---`` rule). Whitespace-
    trimmed of leading/trailing blank lines but otherwise verbatim."""

    label: str
    """The H1 heading content. Returned even though canvas.json's label is
    the SSOT — write side mirrors this on save."""

    warnings: list[str]
    """Lenient-parse complaints: missing expected sections, unknown ## headers
    found in the typed area, no H1, etc."""


def _heading_to_field(kind: str, heading: str) -> str | None:
    """Reverse-map a human heading ("What we do") to its field name
    ("what_we_do"), case-insensitively. None if not a known section."""
    sections = SECTION_LABELS.get(kind, {})
    norm = heading.strip().lower()
    for field, label in sections.items():
        if label.lower() == norm:
            return field
    return None


def parse_md_template(text: str, kind: str) -> ParsedTemplate:
    """Parse a Foundation node's MD file. Lenient: never raises on a
    well-formed-as-text but schema-deviant input. Returns empty values +
    warnings for everything wrong instead."""
    warnings: list[str] = []

    # Split typed area / free prose at the first horizontal rule.
    hr = _HR.search(text)
    if hr is None:
        typed_area = text
        free_prose = ""
    else:
        typed_area = text[: hr.start()]
        tail = text[hr.end() :]
        free_prose = tail.lstrip("\n").rstrip() + "\n" if tail.strip() else ""

    # Pull the H1 label (first line starting with `# `).
    label = ""
    for line in typed_area.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            label = s[2:].strip()
            break
    if not label:
        warnings.append("missing H1 label heading (`# Title`)")

    # Walk the H2 sections.
    expected_fields = FOUNDATION_TYPED_TEXT_FIELDS.get(kind, [])
    typed_fields: dict[str, str] = {field: "" for field in expected_fields}
    h2_matches = list(_H2.finditer(typed_area))
    for i, match in enumerate(h2_matches):
        heading = match.group(1)
        field = _heading_to_field(kind, heading)
        body_start = match.end()
        body_end = h2_matches[i + 1].start() if i + 1 < len(h2_matches) else len(typed_area)
        body = typed_area[body_start:body_end].strip()
        # Strip HTML comments (the schema template embeds them as guides).
        body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
        if field is None:
            warnings.append(
                f"unknown ## section {heading!r} for kind {kind!r} — preserved in warnings, "
                f"not mapped to a typed field"
            )
            continue
        typed_fields[field] = body
    for field in expected_fields:
        if not typed_fields[field]:
            warnings.append(f"missing or empty section for typed field {field!r}")

    return ParsedTemplate(
        typed_fields=typed_fields,
        free_prose=free_prose,
        label=label,
        warnings=warnings,
    )


def render_md_template(
    kind: str,
    label: str,
    typed_fields: dict[str, str],
    free_prose: str = "",
) -> str:
    """Strict render — emit the canonical heading order for ``kind``, then
    the ``---`` rule, then the free prose. Empty typed fields render as
    blank section bodies (so the user can fill them in editor)."""
    sections = SECTION_LABELS.get(kind, {})
    lines: list[str] = []
    lines.append(f"# {label}".rstrip())
    lines.append("")
    for field, heading in sections.items():
        lines.append(f"## {heading}")
        lines.append("")
        body = (typed_fields.get(field) or "").strip()
        if body:
            lines.append(body)
            lines.append("")
        else:
            # Leave a blank line so editors put the cursor in the right place.
            lines.append("")
    lines.append("---")
    lines.append("")
    if free_prose.strip():
        lines.append(free_prose.strip())
        lines.append("")
    return "\n".join(lines)
