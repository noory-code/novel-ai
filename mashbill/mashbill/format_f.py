"""format F export (INT-2) — vP project snapshot + vS service release.

Implements the neutral published-bundle contract in ``docs/specs/format-f.md``.
format F is now the **sole** publish model (D-2026-06-22-H): the project snapshot
``vP`` (via the Header "설계도 발행" button) + a service release ``vS`` (per
service). The old per-node publish (``node_publish.py``) is retired.

Slugs are minted into a per-project registry ``_slugs.json`` (P-4 = explicit
slug field): keyed on node id, so a slug is **stable across label changes** and
decoupled from the label — the connective tissue of the mashbill↔Solera pipeline.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

from mashbill.folder_io import read_canvas, read_project
from mashbill.models import CanvasDoc
from mashbill.storage import _project_dir, _read_json, _write_json

FORMAT_F_VERSION = 1

# Kinds published as a singleton (bare slug, no ``kind/`` prefix).
_SINGLETON_KINDS = frozenset({"mission"})

# The *primary* typed field per Foundation kind — the actual statement the
# external agent reads (``body`` is secondary prose). Reading only ``body`` (the
# pre-richness behaviour) dropped the essence and left the hash blind to it.
_FOUNDATION_PRIMARY = {
    "mission": "statement",
    "core_value": "definition",
    "identity": "description",
}
# Human-readable section title per Foundation kind (grouping in foundation.md).
_FOUNDATION_SECTION = {
    "mission": "미션",
    "core_value": "코어 밸류",
    "identity": "아이덴티티",
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-") or "x"


def _slug_store_path(plot_root: Path, project_id: str) -> Path:
    return _project_dir(plot_root, project_id) / "_slugs.json"


def mint_slug(plot_root: Path, project_id: str, node: Any) -> str:
    """Return the stable slug for ``node``, minting it on first sight.

    Keyed on ``node.id``: the slug is derived from the label *once* and then
    frozen in ``_slugs.json``, so renaming the label never moves the slug
    (explicit-slug invariant, P-4). Collisions within a project get a ``-N``
    suffix.
    """
    store_path = _slug_store_path(plot_root, project_id)
    store: dict[str, str] = _read_json(store_path) if store_path.exists() else {}
    existing = store.get(node.id)
    if existing is not None:
        return existing

    if node.kind in _SINGLETON_KINDS:
        candidate = str(node.kind)
    else:
        candidate = f"{node.kind}/{_slugify(node.label or node.id)}"

    taken = set(store.values())
    slug = candidate
    suffix = 2
    while slug in taken:
        slug = f"{candidate}-{suffix}"
        suffix += 1

    store[node.id] = slug
    _write_json(store_path, store)
    return slug


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _git_sha(plot_root: Path) -> str:
    """Best-effort workspace git sha (the anchor of immutability). Empty when
    there is no repo — the walking skeleton does not require one."""
    from mashbill.workspace import workspace_root_from_plot_root

    try:
        ws = workspace_root_from_plot_root(plot_root)
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except OSError:
        return ""


def _next_release(scope_dir: Path, prefix: str) -> int:
    """Next monotonic release number under ``scope_dir`` (e.g. ``vP`` / ``vS``)."""
    if not scope_dir.is_dir():
        return 1
    seen: list[int] = []
    for child in scope_dir.iterdir():
        if child.is_dir() and child.name.startswith(prefix):
            try:
                seen.append(int(child.name[len(prefix) :]))
            except ValueError:
                continue
    return (max(seen) + 1) if seen else 1


def _latest_release(scope_dir: Path, prefix: str) -> str | None:
    n = _next_release(scope_dir, prefix) - 1
    return f"{prefix}{n}" if n >= 1 else None


def publish_project_snapshot(plot_root: Path, project_id: str) -> dict[str, Any]:
    """Freeze the project's **shared structure** (本質·Actors·Entities) into a
    ``published/_project/vP{N}/`` snapshot — the project-scope layer of the
    2-layer model (D-2026-06-21-AB). Returns the manifest.
    """
    read_project(plot_root, project_id)  # validate id (404s on mismatch)
    snap_dir = _project_dir(plot_root, project_id) / "published" / "_project"
    release = f"vP{_next_release(snap_dir, 'vP')}"
    design = snap_dir / release / "design"
    design.mkdir(parents=True, exist_ok=True)

    elements: list[dict[str, Any]] = []

    # --- Foundation (mission / core_value / identity) ---
    # Render the *primary* typed field per kind + secondary body, grouped under
    # human sections so the reading agent meets the essence first.
    foundation = read_canvas(plot_root, project_id, "foundation")
    sections: dict[str, list[str]] = {"mission": [], "core_value": [], "identity": []}
    for node in foundation.nodes:
        if node.kind not in _FOUNDATION_PRIMARY:
            continue
        slug = mint_slug(plot_root, project_id, node)
        primary = str(getattr(node, _FOUNDATION_PRIMARY[node.kind], "") or "")
        body = str(getattr(node, "body", "") or "")
        elements.append(
            {
                "id": slug,
                "kind": node.kind,
                "hash": _hash(f"{node.kind}|{node.label}|{primary}|{body}"),
            }
        )
        block = f"### {node.label} (`{slug}`)\n"
        if primary:
            block += f"\n{primary}\n"
        if body:
            block += f"\n{body}\n"
        sections[node.kind].append(block)
    f_out = [
        "# Foundation — 프로젝트의 본질\n",
        "> 이 서비스가 무엇을 위해 존재하고(미션), 무엇을 지키며(코어 밸류), 어떤 결로 "
        "말하는지(아이덴티티). 외부 에이전트는 이 본질을 깨지 않는 선에서 작업한다.\n",
    ]
    for kind in ("mission", "core_value", "identity"):
        if sections[kind]:
            f_out.append(f"## {_FOUNDATION_SECTION[kind]}\n")
            f_out.extend(sections[kind])
    (design / "foundation.md").write_text("\n".join(f_out), encoding="utf-8")

    # --- Actors (role hierarchy + relations) ---
    actors = read_canvas(plot_root, project_id, "actors")
    actor_labels = {n.id: n.label for n in actors.nodes if n.kind == "actor"}
    a_roles: list[str] = []
    for node in actors.nodes:
        if node.kind != "actor":
            continue
        slug = mint_slug(plot_root, project_id, node)
        body = str(getattr(node, "body", "") or "")
        side = str(getattr(node, "side", "") or "")
        elements.append(
            {"id": slug, "kind": "actor", "hash": _hash(f"actor|{node.label}|{side}|{body}")}
        )
        block = f"### {node.label} (`{slug}`)" + (f" — {side}" if side else "") + "\n"
        if body:
            block += f"\n{body}\n"
        a_roles.append(block)
    # Relationships (주고받음) — edges between two actor nodes carry the role-level
    # value exchange (label / action_verb). Rendered so the agent sees the
    # economy, not just the cast.
    a_rels: list[str] = []
    for e in actors.edges:
        if e.source in actor_labels and e.target in actor_labels:
            tie = e.label or e.action_verb or e.relation
            a_rels.append(f"- {actor_labels[e.source]} → {actor_labels[e.target]}: {tie}")
    a_out = ["# Actors — 역할과 주고받음\n", "## 역할\n", *a_roles]
    if a_rels:
        a_out.append("## 관계 (주고받음)\n")
        a_out.append("\n".join(a_rels) + "\n")
    (design / "actors.md").write_text("\n".join(a_out), encoding="utf-8")

    # --- Entities (concept map) ---
    entities = read_canvas(plot_root, project_id, "entities")
    for node in entities.nodes:
        if node.kind != "entity":
            continue
        slug = mint_slug(plot_root, project_id, node)
        summary = str(getattr(node, "summary", "") or "")
        elements.append(
            {"id": slug, "kind": "entity", "hash": _hash(f"entity|{node.label}|{summary}")}
        )
        ent_dir = design / "entities"
        ent_dir.mkdir(parents=True, exist_ok=True)
        (ent_dir / f"{slug.split('/')[-1]}.md").write_text(
            f"---\nid: {slug}\nkind: entity\n---\n# {node.label}\n\n**무엇을 담나:** {summary}\n",
            encoding="utf-8",
        )

    manifest: dict[str, Any] = {
        "format_f_version": FORMAT_F_VERSION,
        "scope": "project",
        "release": release,
        "git_sha": _git_sha(plot_root),
        "elements": elements,
    }
    _write_json(snap_dir / release / "manifest.json", manifest)
    return manifest


def _features_under_service(services: CanvasDoc, service_id: str) -> list[Any]:
    """Feature nodes nested under ``service_id`` — the targets of a directed
    edge from the service (the same parent→child mechanism the canvas uses,
    D-2026-06-17-D). Deterministic order (by node id) for stable manifests."""
    feature_ids = {n.id for n in services.nodes if n.kind == "feature"}
    by_id = {n.id: n for n in services.nodes}
    children = sorted(
        {e.target for e in services.edges if e.source == service_id and e.target in feature_ids}
    )
    return [by_id[fid] for fid in children]


def _render_feature_flow(detail: CanvasDoc) -> str:
    """Render a feature's UX flow (행동→분기→결과) from its detail canvas — the
    Execution-handoff content an external agent reads to realise the feature
    (format-f.md §4). Deterministic so the element hash is stable input to the
    ID-diff."""
    by_id = {n.id: n for n in detail.nodes}
    lines: list[str] = []

    subjects = [
        (n.label or "").removeprefix("→ ").strip() for n in detail.nodes if n.kind == "actor_ref"
    ]
    subjects = [s for s in subjects if s]
    if subjects:
        lines.append(f"참여자: {', '.join(subjects)}")
        lines.append("")

    steps = [n for n in detail.nodes if n.kind == "step"]
    steps.sort(key=lambda n: (n.order is None, n.order if n.order is not None else 0, n.id))
    if steps:
        lines.append("### 행동")
        for i, s in enumerate(steps, 1):
            prefix = "(실패) " if getattr(s, "polarity", "neutral") == "negative" else ""
            outcome = f" → {s.outcome}" if getattr(s, "outcome", "") else ""
            lines.append(f"{i}. {prefix}{s.label}{outcome}")
        lines.append("")

    decisions = sorted((n for n in detail.nodes if n.kind == "decision"), key=lambda n: n.id)
    if decisions:
        lines.append("### 분기")
        for d in decisions:
            lines.append(f"- {d.label}")
            for e in detail.edges:
                if e.source != d.id:
                    continue
                target = by_id.get(e.target)
                target_label = target.label if target is not None else e.target
                lines.append(f"    - {e.label or '→'}: {target_label}")
        lines.append("")

    notes = sorted((n for n in detail.nodes if n.kind == "note"), key=lambda n: n.id)
    if notes:
        lines.append("### 참고 (ambient)")
        for n in notes:
            body = getattr(n, "body", "") or ""
            lines.append(f"- {n.label}{f': {body}' if body else ''}")
        lines.append("")

    if not (steps or decisions):
        lines.append("_아직 흐름이 그려지지 않음._")

    return "\n".join(lines).rstrip() + "\n"


def publish_service(plot_root: Path, project_id: str, service_id: str) -> dict[str, Any]:
    """Freeze one **service** (5칸 + its features + each feature's UX flow) into
    a ``published/{service-slug}/vS{N}/`` release — the service-scope layer.

    Each feature nested under the service (via a directed edge, D-2026-06-17-D)
    becomes an owned element (``feature/{slug}``, ``flow: true``) with a
    ``design/features/{slug}.md`` rendering its detail-canvas UX flow — the
    Execution-handoff content an external agent reads to realise it (so a
    Solera ``realizes: feature/login`` resolves into a real flow).

    Bootstrap (format-f.md §1.5): requires a project snapshot ``vP`` to exist;
    the release pins it via ``based_on`` and references the shared elements it
    uses (actors / core_values / identity / entities) **by slug, not by copy**.
    Entity refs roll up from the features' steps (``ref_entity_ids``).
    refs-integrity gate (§1.4): every ref must resolve in that ``vP`` — else the
    publish is refused at the write boundary (before any file is written).
    """
    read_project(plot_root, project_id)  # validate id
    pdir = _project_dir(plot_root, project_id)
    snap_dir = pdir / "published" / "_project"

    vp = _latest_release(snap_dir, "vP")
    if vp is None:
        raise ValueError(
            "no project snapshot (vP) — run publish_project_snapshot first (bootstrap)"
        )
    vp_ids = {e["id"] for e in _read_json(snap_dir / vp / "manifest.json")["elements"]}

    services = read_canvas(plot_root, project_id, "services")
    svc = next((n for n in services.nodes if n.id == service_id and n.kind == "service"), None)
    if svc is None:
        raise FileNotFoundError(f"service not found: {service_id}")

    store_path = _slug_store_path(plot_root, project_id)
    store: dict[str, str] = _read_json(store_path) if store_path.exists() else {}

    def _resolve(ids: list[str]) -> tuple[list[str], list[str]]:
        ok: list[str] = []
        missing: list[str] = []
        for node_id in ids:
            slug = store.get(node_id)
            if slug is None or slug not in vp_ids:
                missing.append(node_id)
            else:
                ok.append(slug)
        return ok, missing

    # --- read phase (no writes) — gather the features + their flows so every
    # ref can be validated *before* anything lands on disk (validate-before-write).
    features = _features_under_service(services, service_id)
    feature_plan: list[tuple[Any, str]] = []  # (feature node, rendered flow text)
    entity_node_ids: set[str] = set()
    for feat in features:
        try:
            detail = read_canvas(plot_root, project_id, "feature", service_id=feat.id)
        except FileNotFoundError:
            detail = None
        flow_text = _render_feature_flow(detail) if detail is not None else "_흐름 없음._\n"
        feature_plan.append((feat, flow_text))
        if detail is not None:
            for n in detail.nodes:
                if n.kind == "step":
                    entity_node_ids.update(getattr(n, "ref_entity_ids", None) or [])

    actor_slugs, m_a = _resolve(list(svc.ref_actor_ids))
    value_slugs, m_v = _resolve(list(svc.ref_value_ids))
    identity_slugs, m_i = _resolve(list(svc.ref_identity_ids))
    entity_slugs, m_e = _resolve(sorted(entity_node_ids))
    missing = m_a + m_v + m_i + m_e
    if missing:
        raise ValueError(f"refs do not resolve in {vp} (refs-integrity): {missing}")

    # --- write phase ---
    svc_slug = mint_slug(plot_root, project_id, svc)
    out = pdir / "published" / svc_slug.split("/")[-1]
    release = f"vS{_next_release(out, 'vS')}"
    design = out / release / "design"
    design.mkdir(parents=True, exist_ok=True)

    svc_md = (
        f"# {svc.label} (`{svc_slug}`)\n\n"
        f"**왜 필요한가:** {svc.problem}\n\n"
        f"**뭐가 좋아지나:** {svc.value_created}\n"
    )
    # Surface what the service stands on in its vP (refs by slug, resolvable
    # there) so service.md reads standalone for the external agent.
    if actor_slugs or value_slugs or identity_slugs:
        svc_md += "\n## 이 서비스가 딛는 것 (vP 참조)\n\n"
        if actor_slugs:
            svc_md += f"- 참여 액터: {', '.join(actor_slugs)}\n"
        if value_slugs:
            svc_md += f"- 지키는 가치: {', '.join(value_slugs)}\n"
        if identity_slugs:
            svc_md += f"- 정체성 결: {', '.join(identity_slugs)}\n"
    (design / "service.md").write_text(svc_md, encoding="utf-8")

    elements: list[dict[str, Any]] = [
        {
            "id": svc_slug,
            "kind": "service",
            "hash": _hash(f"service|{svc.label}|{svc.problem}|{svc.value_created}"),
        }
    ]

    if feature_plan:
        (design / "features").mkdir(parents=True, exist_ok=True)
    for feat, flow_text in feature_plan:
        feat_slug = mint_slug(plot_root, project_id, feat)
        proposed = str(getattr(feat, "proposed", "") or "")
        (design / "features" / f"{feat_slug.split('/')[-1]}.md").write_text(
            f"---\nid: {feat_slug}\nkind: feature\n---\n"
            f"# {feat.label}\n\n"
            f"**무엇을 할 수 있나:** {proposed}\n\n"
            f"## UX 흐름 (action 고도)\n\n{flow_text}",
            encoding="utf-8",
        )
        elements.append(
            {
                "id": feat_slug,
                "kind": "feature",
                "hash": _hash(f"feature|{feat.label}|{proposed}|{flow_text}"),
                "flow": True,
            }
        )

    manifest: dict[str, Any] = {
        "format_f_version": FORMAT_F_VERSION,
        "scope": "service",
        "service": svc_slug,
        "release": release,
        "based_on": vp,
        "git_sha": _git_sha(plot_root),
        "elements": elements,
        "refs": {
            # Every service stands on the project's single mission — the essence
            # (VISION). Anchoring to it makes a mission change propagate to the
            # services that realize it (refs = the propagation surface, §5). The
            # foundation invariant guarantees a mission, so the guard only ever
            # falls through for a malformed vP.
            "anchors": {
                **({"mission": "mission"} if "mission" in vp_ids else {}),
                "core_values": value_slugs,
                "identity": identity_slugs,
            },
            "actors": actor_slugs,
            "entities": entity_slugs,
        },
    }
    _write_json(out / release / "manifest.json", manifest)
    return manifest
