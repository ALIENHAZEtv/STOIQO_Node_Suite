"""
[STOIQO] Music Prompt & Lyrics Engine Package
Exposes presets, personas, task builders, and parsers for YuE2 & Suno.
"""

from .presets import (
    GENRE_PRESETS,
    VOCAL_PRESETS,
    LANGUAGE_PRESETS,
    SONG_STRUCTURES,
    TEMPO_PRESETS,
)
from .system_prompts import (
    MUSIC_SYSTEM_PROMPT_PRESETS,
    MUSIC_CUSTOM_SYSTEM_PROMPT_KEY,
    MUSIC_SYSTEM_PROMPT_CHOICES,
    YUE2_SYSTEM_PROMPT,
    resolve_music_system_prompt,
)
from .builder import (
    clean_user_custom_lyrics,
    clean_user_custom_directives,
    detect_existing_lyrics,
    build_music_task_prompt,
)
from .parser import (
    generate_fallback_song_lyrics,
    clean_repetition_artifacts,
    normalize_lyrics_sections,
    parse_music_response,
)

__all__ = [
    "GENRE_PRESETS",
    "VOCAL_PRESETS",
    "LANGUAGE_PRESETS",
    "SONG_STRUCTURES",
    "TEMPO_PRESETS",
    "MUSIC_SYSTEM_PROMPT_PRESETS",
    "MUSIC_CUSTOM_SYSTEM_PROMPT_KEY",
    "MUSIC_SYSTEM_PROMPT_CHOICES",
    "YUE2_SYSTEM_PROMPT",
    "resolve_music_system_prompt",
    "clean_user_custom_lyrics",
    "clean_user_custom_directives",
    "detect_existing_lyrics",
    "build_music_task_prompt",
    "generate_fallback_song_lyrics",
    "clean_repetition_artifacts",
    "normalize_lyrics_sections",
    "parse_music_response",
]
