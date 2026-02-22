"""ingest tool — Extract knowledge from markdown/text files into the knowledge store."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from distill.config import load_config
from distill.extractor.llm_client import call_llm
from distill.extractor.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from distill.extractor.rules_reader import read_all_rules
from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeInput, KnowledgeScope, KnowledgeSource
from distill.store.vector import VectorStore

INGEST_EXTENSIONS = {".md", ".mdx", ".txt", ".rst"}
_VALID_TYPES = {"pattern", "preference", "decision", "mistake", "workaround", "conflict"}
_VALID_SCOPES = {"global", "project", "workspace"}


def _file_hash(path: Path) -> str:
    """Return a hash of file path + mtime for change detection."""
    stat = path.stat()
    key = f"{path}:{stat.st_mtime}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _meta_key(path: Path) -> str:
    return f"ingest:{path}"


async def _extract_from_text(
    *,
    ctx: Any,
    content: str,
    source_path: str,
    project_root: str | None,
    config,
) -> list[KnowledgeInput]:
    """Run LLM extraction on raw text content (not a .jsonl transcript)."""
    existing_rules = read_all_rules(project_root)

    # Re-use extraction prompt, treating the doc as the "conversation"
    user_prompt = build_extraction_prompt(
        f"[Document: {source_path}]\n\n{content}",
        existing_rules=existing_rules,
    )

    text = await call_llm(
        messages=[{"role": "user", "content": user_prompt}],
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        model=config.extraction_model,
        ctx=ctx,
    )
    import re
    json_match = re.search(r"\[[\s\S]*\]", text)
    if not json_match:
        return []

    try:
        raw = json.loads(json_match.group())
    except json.JSONDecodeError:
        return []

    now = datetime.now(timezone.utc).isoformat()
    source = KnowledgeSource(
        session_id=f"ingest:{source_path}",
        timestamp=now,
        trigger="ingest",
    )

    results: list[KnowledgeInput] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        t = item.get("type", "")
        s = item.get("scope", "project")
        if t not in _VALID_TYPES or s not in _VALID_SCOPES:
            continue
        try:
            results.append(
                KnowledgeInput(
                    content=str(item.get("content", "")).strip(),
                    type=t,
                    scope=s,
                    tags=item.get("tags", []),
                    source=source,
                    confidence=float(item.get("confidence", 0.7)),
                )
            )
        except Exception:
            continue

    return results


async def ingest(
    path: str,
    ctx: Any,
    scope: KnowledgeScope | None = None,
    caller_cwd: str | None = None,
    _project_root: str | None = None,
) -> str:
    """Extract knowledge from markdown/text files into the knowledge store.

    Recursively scans a directory (or single file) for .md, .mdx, .txt files,
    runs LLM extraction on each, and saves results to the knowledge store.
    Skips files that haven't changed since last ingest (mtime-based).

    Args:
        path: File or directory path to ingest.
        ctx: MCP context for LLM sampling.
        scope: Override storage scope (global/project/workspace). Defaults to nearest scope.
        caller_cwd: Caller's working directory for project root detection.
        _project_root: Override project root (for testing).
    """
    project_root = _project_root or detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    config = load_config(project_root)

    # Default to nearest available scope
    if scope:
        effective_scope: KnowledgeScope = scope
    elif project_root:
        effective_scope = "project"
    elif workspace_root:
        effective_scope = "workspace"
    else:
        effective_scope = "global"

    ws_root = workspace_root if effective_scope == "workspace" else None

    target = Path(path).expanduser().resolve()
    if not target.exists():
        return f"Path not found: {path}"

    # Collect files
    if target.is_file():
        files = [target] if target.suffix in INGEST_EXTENSIONS else []
    else:
        files = [f for f in target.rglob("*") if f.suffix in INGEST_EXTENSIONS]

    if not files:
        return f"No supported files found in {path} (supported: {', '.join(INGEST_EXTENSIONS)})"

    skipped = 0
    processed = 0
    saved_total = 0
    errors = 0

    with (
        MetadataStore(effective_scope, project_root, ws_root) as meta,
        VectorStore(effective_scope, project_root, ws_root) as vector,
    ):
        for file in sorted(files):
            file_hash = _file_hash(file)
            meta_key = _meta_key(file)
            stored = meta.get_meta(meta_key)

            # Skip if unchanged
            if stored:
                try:
                    stored_data = json.loads(stored)
                    if stored_data.get("hash") == file_hash:
                        skipped += 1
                        continue
                    # File changed: delete old chunks
                    old_ids = stored_data.get("chunk_ids", [])
                    for old_id in old_ids:
                        meta.delete(old_id)
                        vector.remove(old_id)
                except (json.JSONDecodeError, Exception):
                    pass

            # Read file
            try:
                content = file.read_text(encoding="utf-8").strip()
            except OSError:
                errors += 1
                continue

            if not content:
                skipped += 1
                continue

            # Extract knowledge via LLM
            chunks = await _extract_from_text(
                ctx=ctx,
                content=content,
                source_path=str(file),
                project_root=project_root,
                config=config,
            )

            # Save chunks
            chunk_ids: list[str] = []
            for chunk_input in chunks:
                chunk_input.scope = effective_scope
                try:
                    inserted = meta.insert(chunk_input)
                    vector.index(inserted.id, inserted.content, inserted.tags)
                    chunk_ids.append(inserted.id)
                    saved_total += 1
                except Exception:
                    pass

            # Record processing result
            meta.set_meta(
                meta_key,
                json.dumps({"hash": file_hash, "chunk_ids": chunk_ids}),
            )
            processed += 1

    parts = [f"Ingest complete: {processed} files processed, {saved_total} chunks saved"]
    if skipped:
        parts.append(f"{skipped} unchanged files skipped")
    if errors:
        parts.append(f"{errors} files failed to read")
    return ". ".join(parts) + "."
