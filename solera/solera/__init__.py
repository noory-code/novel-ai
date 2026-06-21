"""Solera — a slim harness over a plain-file ``.noory/solera/`` workspace.

Solera plans work into a tree of WorkItems (initiative / epic / story / action),
runs deterministic gates on the leaves, and orders the steps an external AI agent
executes. It does not run the agent loop itself and it works standalone, with or
without Plot.
"""

__version__ = "7.1.0"
