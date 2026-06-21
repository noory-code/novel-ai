"""The gate-runner — Solera's deterministic verification (V) step.

A gate is a single command. It is tokenised with :func:`shlex.split` and run
with ``shell=False`` so the verdict is deterministic and never depends on a
shell being present or on shell expansion. The rule is exactly: exit code 0
passes, anything else fails. A gate that cannot be *started* (empty command,
binary not found) is a :class:`GateResult` with ``passed=False`` and no exit
code — never a silent pass.

This is intentionally not an LLM step. The harness must be able to trust the
verdict, so it is a plain subprocess with a fixed pass rule.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import GateError
from .formats import Action

DEFAULT_TIMEOUT_SECONDS = 120.0


def _as_text(value: object) -> str:
    """Coerce captured stream output (str | bytes | None) to text."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


@dataclass(frozen=True)
class GateResult:
    """The outcome of running one gate, with evidence."""

    command: str
    passed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool


def run_gate(
    command: str,
    *,
    cwd: Path,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> GateResult:
    """Run ``command`` in ``cwd`` and return a :class:`GateResult`.

    Raises :class:`GateError` only when the command string is empty — there is
    nothing to run. Every other failure mode (non-zero exit, timeout, binary
    not found) is reported as ``passed=False`` so the supervisor can branch on
    it without handling exceptions.
    """
    argv = shlex.split(command)
    if not argv:
        raise GateError("empty gate command: nothing to run")

    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return GateResult(
            command=command,
            passed=False,
            exit_code=None,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr) + f"\ngate timed out after {timeout}s",
            timed_out=True,
        )
    except (FileNotFoundError, OSError) as exc:
        return GateResult(
            command=command,
            passed=False,
            exit_code=None,
            stdout="",
            stderr=f"could not run gate: {exc}",
            timed_out=False,
        )

    return GateResult(
        command=command,
        passed=proc.returncode == 0,
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        timed_out=False,
    )


def run_action_gate(
    action: Action,
    *,
    cwd: Path,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> GateResult:
    """Run the gate declared on ``action``.

    An Action with no gate cannot be auto-verified, so this raises
    :class:`GateError` rather than passing it silently — the caller must escalate
    such an Action to a human.
    """
    if not action.gate.strip():
        raise GateError(f"action {action.id} has no gate to run")
    return run_gate(action.gate, cwd=cwd, timeout=timeout)
