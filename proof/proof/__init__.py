"""Proof — an append-only decision log.

A proof is a stack of stones left to mark a path for those who come after. This
is the same idea for decisions: each significant choice (a tech stack, an
architecture, a convention) is recorded once and never edited. To change a
decision you record a new one that *supersedes* the old; the history stays.

Proof is a shared substrate. Plot and Solera do not own it and do not import it —
they point at decisions by stable id (by value). It runs standalone over plain
files under ``.noory/proof/``.
"""

__version__ = "0.3.0"
