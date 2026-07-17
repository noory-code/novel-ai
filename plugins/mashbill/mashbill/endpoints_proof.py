"""Read-only Proof-by-value HTTP endpoint (D-2026-07-17-D)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from starlette.requests import Request
from starlette.responses import JSONResponse

from mashbill.endpoints_common import _ApiError, _error, _require_plot_root
from mashbill.models_entity import PROOF_ID_PATTERN


def _parse_proof_file(path: Path, proof_id: str) -> dict[str, str]:
    """Split Proof YAML frontmatter from its Markdown body."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: missing YAML frontmatter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError(f"{path.name}: missing closing frontmatter fence") from exc

    data: Any = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: frontmatter must be a mapping")
    title = data.get("title")
    status = data.get("status")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{path.name}: frontmatter title must be a non-empty string")
    if not isinstance(status, str) or not status.strip():
        raise ValueError(f"{path.name}: frontmatter status must be a non-empty string")

    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return {"id": proof_id, "title": title, "status": status, "body": body}


async def proof_get_endpoint(request: Request) -> JSONResponse:
    """Return one project-local Proof decision without importing Proof code."""
    proof_id = request.path_params["proof_id"]
    if re.fullmatch(PROOF_ID_PATTERN, proof_id) is None:
        return _error("proof_id must match ^PROOF-\\d+$", status=422)

    try:
        plot_root = _require_plot_root(request, create=False)
    except _ApiError as exc:
        return exc.response

    path = plot_root.parent / "proof" / f"{proof_id}.md"
    try:
        payload = _parse_proof_file(path, proof_id)
    except FileNotFoundError:
        return _error(f"proof not found: {proof_id}", status=404)
    except OSError as exc:
        return _error(f"could not read proof {proof_id}: {exc}", status=500)
    except (ValueError, yaml.YAMLError) as exc:
        return _error(f"malformed proof frontmatter: {exc}", status=422)
    return JSONResponse(payload)
