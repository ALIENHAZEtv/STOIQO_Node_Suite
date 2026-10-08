"""
[STOIQO] Prompt Generator Engine — Artistic Styles Facade Module
Maintains 100% backward compatibility with legacy imports while delegating
to core.image.styles.
"""

try:
    from .image.styles import (
        ARTISTIC_STYLES,
        ARTISTIC_STYLE_DIRECTIVES,
        resolve_artistic_style,
    )
except (ImportError, ValueError):
    from core.image.styles import (
        ARTISTIC_STYLES,
        ARTISTIC_STYLE_DIRECTIVES,
        resolve_artistic_style,
    )

__all__ = [
    "ARTISTIC_STYLES",
    "ARTISTIC_STYLE_DIRECTIVES",
    "resolve_artistic_style",
]
