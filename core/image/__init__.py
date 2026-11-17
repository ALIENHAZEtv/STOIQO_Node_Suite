"""
[STOIQO] Image Prompt Engine Package (Drop-in Modular Architecture)
Exposes dynamically loaded Layer 1 (Personas), Layer 2 (Prompt Types), and Layer 3 (Artistic Styles).
"""

from .loader import (
    reload_image_definitions,
    parse_markdown_with_frontmatter,
    SHARED_OUTPUT_CONTRACT,
    SYSTEM_PERSONAS,
    SYSTEM_PROMPT_PRESETS,
    CUSTOM_SYSTEM_PROMPT_KEY,
    SYSTEM_PROMPT_CHOICES,
    TEXT_EXPANSION_SYSTEM_PROMPT,
    MULTI_IMAGE_SYSTEM_PROMPT,
    BASE_TEXT_EXPANSION_PROMPT,
    BASE_MULTI_IMAGE_PROMPT,
    LEGACY_SYSTEM_PROMPT_ALIASES,
    PERSONA_SAMPLING_DEFAULTS,
    resolve_system_prompt,
    build_dynamic_system_prompt,
    PROMPT_TYPES,
    PROMPT_TYPE_DIRECTIVES,
    LEGACY_PROMPT_TYPE_ALIASES,
    resolve_prompt_type,
    ARTISTIC_STYLES,
    ARTISTIC_STYLE_DIRECTIVES,
    NON_PHOTOGRAPHIC_STYLES,
    LEGACY_ARTISTIC_STYLE_ALIASES,
    resolve_artistic_style,
)
from .crud_api import (
    list_definitions,
    get_definition,
    save_definition,
    delete_definition,
    CORE_PROTECTED,
)

# Compatibility aliases
CAPTION_STYLES = PROMPT_TYPES
STYLE_PROMPTS = ARTISTIC_STYLE_DIRECTIVES

__all__ = [
    "reload_image_definitions",
    "parse_markdown_with_frontmatter",
    "SHARED_OUTPUT_CONTRACT",
    "SYSTEM_PERSONAS",
    "SYSTEM_PROMPT_PRESETS",
    "CUSTOM_SYSTEM_PROMPT_KEY",
    "SYSTEM_PROMPT_CHOICES",
    "TEXT_EXPANSION_SYSTEM_PROMPT",
    "MULTI_IMAGE_SYSTEM_PROMPT",
    "BASE_TEXT_EXPANSION_PROMPT",
    "BASE_MULTI_IMAGE_PROMPT",
    "LEGACY_SYSTEM_PROMPT_ALIASES",
    "PERSONA_SAMPLING_DEFAULTS",
    "resolve_system_prompt",
    "build_dynamic_system_prompt",
    "PROMPT_TYPES",
    "PROMPT_TYPE_DIRECTIVES",
    "LEGACY_PROMPT_TYPE_ALIASES",
    "resolve_prompt_type",
    "CAPTION_STYLES",
    "STYLE_PROMPTS",
    "ARTISTIC_STYLES",
    "ARTISTIC_STYLE_DIRECTIVES",
    "NON_PHOTOGRAPHIC_STYLES",
    "resolve_artistic_style",
    "list_definitions",
    "get_definition",
    "save_definition",
    "delete_definition",
    "CORE_PROTECTED",
]
