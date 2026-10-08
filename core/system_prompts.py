"""
[STOIQO] Prompt Generator Engine — System Prompts Facade Module
Maintains 100% backward compatibility with legacy imports while delegating
to core.image.system_prompts.
"""

try:
    from .image.system_prompts import (
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
except (ImportError, ValueError):
    from core.image.system_prompts import (
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
]
