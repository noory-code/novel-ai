"""Solera error types."""


class SoleraError(Exception):
    """Base class for all Solera errors."""


class FormatError(SoleraError):
    """A workspace file did not match its required format.

    Raised by the parsers in :mod:`solera.formats`. Solera fails fast on a
    malformed WorkItem / progress file rather than guessing intent.
    """


class OrderError(SoleraError):
    """Work-item order links are invalid or leave every open leaf blocked."""


class PlanningError(SoleraError):
    """A requested WorkItem edit would violate the planning tree."""


class GateError(SoleraError):
    """A gate could not be run at all (e.g. empty command, missing gate).

    Distinct from a gate that *ran and failed*: that is reported as a
    :class:`~solera.gate.GateResult` with ``passed=False``, not raised.
    """
