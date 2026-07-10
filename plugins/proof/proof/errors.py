"""Proof error types."""


class ProofError(Exception):
    """Base class for all Proof errors."""


class FormatError(ProofError):
    """A decision file did not match its required format.

    Raised by the parser in :mod:`proof.formats`. Proof fails fast on a malformed
    decision file rather than guessing intent.
    """
