"""Façade for the response builder.

Internal helpers live in sibling modules ``response_memory``,
``response_evidence``, ``response_teaching``, ``response_templates``,
``response_composition``. Only the two public symbols are re-exported.
"""

from __future__ import annotations

from .response_composition import build_response, render_response_markdown

__all__ = ["build_response", "render_response_markdown"]
