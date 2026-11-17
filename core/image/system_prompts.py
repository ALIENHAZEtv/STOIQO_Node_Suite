"""
[STOIQO] Layer 1: Cognitive Personas & System Prompts
Re-exports dynamically loaded personas from loader.py for 100% backward compatibility.
"""

from .loader import (
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
    _compose_prompt,
)

__all__ = [
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
    "_compose_prompt",
]
