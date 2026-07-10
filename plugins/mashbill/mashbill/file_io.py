"""Safe read/write for project-relative text files (v0.7).

The viewer's new MD editor reads and writes Markdown files that live inside
a project's ``workspace/`` tree (or anywhere else under ``project_path``).
This module enforces the path-safety rules so a malicious relative path
can't escape the project root, and keeps the atomic-write contract used
elsewhere in ``folder_io``.
"""

from __future__ import annotations

from pathlib import Path

# Only text-like extensions may be read/written via this module. Keeps binary
# upload attempts out of the write path.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt"})

# v0.24.0 (D-2026-05-17-L) — image extensions served raw via the
# /api/files/raw endpoint for Live Preview image embeds. Same
# path-traversal safety as text reads (resolve_safe_path); extension
# allow-list is the only auth.
ALLOWED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg"}
)

# Reject pathological payloads early.
MAX_FILE_BYTES: int = 1 * 1024 * 1024  # 1 MiB


class UnsafePathError(ValueError):
    """Raised when a user-supplied relative path escapes the project root."""


class ExtensionNotAllowedError(ValueError):
    """Raised when a path targets an extension outside the allow-list."""


def resolve_safe_path(project_path: Path, rel_path: str) -> Path:
    """Join ``rel_path`` onto ``project_path`` and verify the result stays
    inside the project root.

    Rejects absolute paths, ``..`` segments, empty components, and any
    symlink chains that escape via ``realpath``.
    """
    if rel_path is None:
        raise UnsafePathError("rel_path is required")
    normalised = rel_path.strip().replace("\\", "/")
    if not normalised or normalised == ".":
        raise UnsafePathError("rel_path must not be blank")
    if normalised.startswith("/"):
        raise UnsafePathError(f"rel_path must be relative: {rel_path!r}")
    # Allow ``./foo`` at the head but reject ``..`` anywhere and any empty
    # segment (catches ``foo//bar``).
    raw_parts = normalised.split("/")
    parts = [p for p in raw_parts if p != "."]
    if any(p == ".." or p == "" for p in parts):
        raise UnsafePathError(f"rel_path contains '..' or empty segments: {rel_path!r}")

    root = project_path.resolve()
    target = (root / Path(*parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise UnsafePathError(f"rel_path escapes project root: {rel_path!r}") from exc
    return target


def _ensure_allowed_extension(target: Path) -> None:
    if target.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ExtensionNotAllowedError(
            f"extension {target.suffix!r} not allowed (allowed: {sorted(ALLOWED_EXTENSIONS)})"
        )


def read_text_file(project_path: Path, rel_path: str) -> str:
    """Read a text file. Returns ``""`` when the file does not yet exist
    — useful for "open node" flows where the folder was just created."""
    target = resolve_safe_path(project_path, rel_path)
    _ensure_allowed_extension(target)
    if not target.exists():
        return ""
    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"file {rel_path!r} exceeds {MAX_FILE_BYTES} bytes; refusing to read")
    return target.read_text(encoding="utf-8")


def write_text_file(project_path: Path, rel_path: str, content: str) -> None:
    """Atomic text write (tmp → rename, same pattern as folder_io._write_json)."""
    target = resolve_safe_path(project_path, rel_path)
    _ensure_allowed_extension(target)
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError(f"content exceeds {MAX_FILE_BYTES} bytes; refusing to write {rel_path!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(target)


def _resolve_safe_dir(project_path: Path, rel_folder: str) -> tuple[Path, Path]:
    """Shared folder-path normalisation for ensure_folder / uniquify. Returns
    (absolute_resolved, relative_path_object)."""
    if rel_folder is None:
        raise UnsafePathError("rel_folder is required")
    normalised = rel_folder.strip().replace("\\", "/")
    if not normalised or normalised == ".":
        raise UnsafePathError("rel_folder must not be blank")
    if normalised.startswith("/"):
        raise UnsafePathError(f"rel_folder must be relative: {rel_folder!r}")
    raw_parts = normalised.split("/")
    parts = [p for p in raw_parts if p != "."]
    if not parts or any(p == ".." or p == "" for p in parts):
        raise UnsafePathError(f"rel_folder contains '..' or empty segments: {rel_folder!r}")
    root = project_path.resolve()
    rel_obj = Path(*parts)
    target = (root / rel_obj).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise UnsafePathError(f"rel_folder escapes project root: {rel_folder!r}") from exc
    return target, rel_obj


def ensure_folder(project_path: Path, rel_folder: str) -> Path:
    """Create ``rel_folder`` (inside the project root) and seed an empty
    ``index.md`` if the folder is fresh. Returns the resolved folder path.
    Idempotent — existing contents stay untouched.
    """
    target, _ = _resolve_safe_dir(project_path, rel_folder)
    target.mkdir(parents=True, exist_ok=True)
    index_md = target / "index.md"
    if not index_md.exists():
        index_md.write_text("", encoding="utf-8")
    return target


def uniquify_folder(project_path: Path, desired_rel_folder: str) -> str:
    """Return a relative path that does not yet exist, appending ``-2``,
    ``-3``, … when the desired name is taken. Caller typically passes the
    result to ``ensure_folder`` to create it.
    """
    candidate, base = _resolve_safe_dir(project_path, desired_rel_folder)
    if not candidate.exists():
        return str(base).replace("\\", "/")

    root = project_path.resolve()
    parent = base.parent
    stem = base.name
    n = 2
    while True:
        next_rel = parent / f"{stem}-{n}"
        next_abs = (root / next_rel).resolve()
        if not next_abs.exists():
            return str(next_rel).replace("\\", "/")
        n += 1
