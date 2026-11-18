"""
[STOIQO] Layer 3: Style Guidelines (Artistic Styles & Medium Supremacy)
Exposes dynamically loaded aesthetic styles from loader.py.
"""

from .loader import (
    ARTISTIC_STYLES,
    ARTISTIC_STYLE_DIRECTIVES,
    NON_PHOTOGRAPHIC_STYLES,
    LEGACY_ARTISTIC_STYLE_ALIASES,
    resolve_artistic_style,
)

# Compatibility alias
STYLE_PROMPTS = ARTISTIC_STYLE_DIRECTIVES

__all__ = [
    "ARTISTIC_STYLES",
    "ARTISTIC_STYLE_DIRECTIVES",
    "NON_PHOTOGRAPHIC_STYLES",
    "LEGACY_ARTISTIC_STYLE_ALIASES",
    "resolve_artistic_style",
    "STYLE_PROMPTS",
]
