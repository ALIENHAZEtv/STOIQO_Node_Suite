"""
[STOIQO] Layer 2: Prompt Types & Structural Formats
Re-exports dynamically loaded prompt types from loader.py for 100% backward compatibility.
"""

from .loader import (
    PROMPT_TYPES,
    PROMPT_TYPE_DIRECTIVES,
    LEGACY_PROMPT_TYPE_ALIASES,
    resolve_prompt_type,
)

# Compatibility aliases
CAPTION_STYLES = PROMPT_TYPES

__all__ = [
    "PROMPT_TYPES",
    "PROMPT_TYPE_DIRECTIVES",
    "LEGACY_PROMPT_TYPE_ALIASES",
    "resolve_prompt_type",
    "CAPTION_STYLES",
]
