"""Solera error types."""


class SoleraError(Exception):
    """Base class for all Solera errors."""


class FormatError(SoleraError):
    """A workspace file did not match its required format.

    Raised by the parsers in :mod:`solera.formats`. Solera fails fast on a
    malformed Action / Story / progress file rather than guessing intent.
    """
