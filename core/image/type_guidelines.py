"""
[STOIQO] Layer 2: Type Guidelines (Structural Formats & Output Syntax)
Exposes dynamically loaded prompt formats from loader.py.
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
