"""mashbill MCP + HTTP server — freeform sketch canvas for Claude Code."""

# Single source of truth for the engine version (D-2026-06-20-N). pyproject
# derives this dynamically (hatchling), schema_export re-exports it as
# MASHBILL_VERSION, and .claude-plugin/plugin.json is pinned equal by
# tests/test_version_parity.py. Gate 4 bumps THIS line + plugin.json together.
__version__ = "0.158.1"
