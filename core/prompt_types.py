"""
[STOIQO] Prompt Generator Engine — Prompt Types Facade Module
Maintains 100% backward compatibility with legacy imports while delegating
to core.image.prompt_types.
"""

try:
    from .image.prompt_types import (
        PROMPT_TYPES,
        PROMPT_TYPE_DIRECTIVES,
        resolve_prompt_type,
        CAPTION_STYLES,
        STYLE_PROMPTS,
    )
except (ImportError, ValueError):
    from core.image.prompt_types import (
        PROMPT_TYPES,
        PROMPT_TYPE_DIRECTIVES,
        resolve_prompt_type,
        CAPTION_STYLES,
        STYLE_PROMPTS,
    )

__all__ = [
    "PROMPT_TYPES",
    "PROMPT_TYPE_DIRECTIVES",
    "resolve_prompt_type",
    "CAPTION_STYLES",
    "STYLE_PROMPTS",
]
