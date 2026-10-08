"""
[STOIQO] Image Prompt Engine Package
Exposes Layer 1 (System Prompts), Layer 2 (Prompt Types), and Layer 3 (Artistic Styles).
"""

from .system_prompts import (
    SYSTEM_PROMPT_PRESETS,
    CUSTOM_SYSTEM_PROMPT_KEY,
    SYSTEM_PROMPT_CHOICES,
    TEXT_EXPANSION_SYSTEM_PROMPT,
    MULTI_IMAGE_SYSTEM_PROMPT,
    BASE_TEXT_EXPANSION_PROMPT,
    BASE_MULTI_IMAGE_PROMPT,
    LEGACY_SYSTEM_PROMPT_ALIASES,
    resolve_system_prompt,
)
from .prompt_types import (
    PROMPT_TYPES,
    PROMPT_TYPE_DIRECTIVES,
    resolve_prompt_type,
    CAPTION_STYLES,
    STYLE_PROMPTS,
)
from .styles import (
    ARTISTIC_STYLES,
    ARTISTIC_STYLE_DIRECTIVES,
    resolve_artistic_style,
)

__all__ = [
    "SYSTEM_PROMPT_PRESETS",
    "CUSTOM_SYSTEM_PROMPT_KEY",
    "SYSTEM_PROMPT_CHOICES",
    "TEXT_EXPANSION_SYSTEM_PROMPT",
    "MULTI_IMAGE_SYSTEM_PROMPT",
    "BASE_TEXT_EXPANSION_PROMPT",
    "BASE_MULTI_IMAGE_PROMPT",
    "LEGACY_SYSTEM_PROMPT_ALIASES",
    "resolve_system_prompt",
    "PROMPT_TYPES",
    "PROMPT_TYPE_DIRECTIVES",
    "resolve_prompt_type",
    "CAPTION_STYLES",
    "STYLE_PROMPTS",
    "ARTISTIC_STYLES",
    "ARTISTIC_STYLE_DIRECTIVES",
    "resolve_artistic_style",
]
