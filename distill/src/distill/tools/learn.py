"""learn tool — Extract and save knowledge from a conversation transcript."""

from __future__ import annotations

from datetime import datetime, timezone

from distill.config import load_config
from distill.extractor.crystallize import crystallize
from distill.extractor.extractor import extract_knowledge
from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeChunk, KnowledgeInput, KnowledgeScope
from distill.store.vector import VectorStore
from distill.tools.helpers import for_each_scope


async def learn(
    transcript_path: str,
    session_id: str,
    ctx,
    scope: KnowledgeScope | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Extract and save knowledge from a conversation transcript."""
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None
    project_name = project_root.split("/")[-1] if project_root else None
    config = load_config(project_root)

    # Extract knowledge from transcript via MCP sampling
    chunks = await extract_knowledge(
        ctx=ctx,
        transcript_path=transcript_path,
        session_id=session_id,
        trigger="manual",
        project_name=project_name,
        scope_override=scope,
        project_root=project_root,
    )

    if not chunks:
        return "No extractable knowledge found in this transcript."

    # scope별로 청크를 그룹화
    chunks_by_scope: dict[str, list[KnowledgeInput]] = {}
    for chunk in chunks:
        scope_key = f"{chunk.scope}:{workspace_root if chunk.scope == 'workspace' else project_root}"
        if scope_key not in chunks_by_scope:
            chunks_by_scope[scope_key] = []
        chunks_by_scope[scope_key].append(chunk)

    # 각 scope별로 배치 저장
    saved = 0
    conflict_warnings: list[str] = []

    for scope_key, scope_chunks in chunks_by_scope.items():
        try:
            first_chunk = scope_chunks[0]
            ws_root = workspace_root if first_chunk.scope == "workspace" else None

            with (
                MetadataStore(first_chunk.scope, project_root, ws_root) as meta,
                VectorStore(first_chunk.scope, project_root, ws_root) as vector,
            ):
                # 모든 청크를 메타데이터 스토어에 삽입
                entry_ids = [meta.insert(chunk).id for chunk in scope_chunks]

                # 배치 벡터 인덱싱
                vector.index_many(
                    ids=entry_ids,
                    contents=[c.content for c in scope_chunks],
                    tags_list=[c.tags for c in scope_chunks],
                )

                # conflict 타입 체크
                for chunk in scope_chunks:
                    if chunk.type == "conflict":
                        conflict_warnings.append(f"  ⚠ CONFLICT: {chunk.content[:100]}")
                    saved += 1
        except Exception:
            pass

    summary = "\n".join(f"- [{c.type}] {c.content[:80]}..." for c in chunks)

    lines = [f"Extracted {len(chunks)} knowledge chunks, saved {saved}."]

    if conflict_warnings:
        lines.append("")
        lines.append("Rule conflicts detected:")
        lines.extend(conflict_warnings)

    lines.append("")
    lines.append(summary)

    # Check auto-crystallize threshold
    auto_msg = ""
    if config.auto_crystallize_threshold > 0:
        try:
            with MetadataStore("global") as global_meta:
                last_crystallize = global_meta.get_meta("last_crystallize") or "1970-01-01T00:00:00.000Z"
                new_count = global_meta.count_since(last_crystallize)

            if new_count >= config.auto_crystallize_threshold:
                # Collect all chunks for crystallize
                all_chunks: list[KnowledgeChunk] = []
                await for_each_scope(
                    None, project_root, lambda c: all_chunks.extend(c.meta.get_all()),
                    workspace_root=workspace_root,
                )

                report = await crystallize(
                    ctx=ctx,
                    chunks=all_chunks,
                    model=config.crystallize_model,
                    project_root=project_root,
                )

                with MetadataStore("global") as gm2:
                    gm2.set_meta("last_crystallize", datetime.now(timezone.utc).isoformat())

                parts = []
                if report.created:
                    parts.append(f"created: {', '.join(report.created)}")
                if report.updated:
                    parts.append(f"updated: {', '.join(report.updated)}")
                if report.removed:
                    parts.append(f"removed: {', '.join(report.removed)}")
                if report.downgraded:
                    parts.append(f"downgraded: {', '.join(report.downgraded)}")
                if report.skills_created:
                    parts.append(f"skills: {', '.join(report.skills_created)}")
                auto_msg = (
                    f"\n\n🔮 Auto-crystallize triggered ({new_count} chunks since last run): "
                    f"{'; '.join(parts) or 'no changes'}"
                )
                if report.user_conflicts:
                    conflict_lines = [
                        f"  - {c.user_rule_file}: {c.conflicting_content} → {c.suggestion}"
                        for c in report.user_conflicts
                    ]
                    auto_msg += f"\n\n⚠ User rule conflicts:\n" + "\n".join(conflict_lines)
        except Exception as err:
            auto_msg = f"\n\n⚠ Auto-crystallize failed: {err}"

    return "\n".join(lines) + auto_msg
