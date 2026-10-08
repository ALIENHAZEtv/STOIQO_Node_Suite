"""
[STOIQO] Music Prompt & Lyrics Engine — Facade Module
Maintains 100% backward compatibility with legacy imports while delegating
to the modular core.music package (presets, system_prompts, builder, parser).
"""

try:
    from .music import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        MUSIC_SYSTEM_PROMPT_PRESETS,
        MUSIC_CUSTOM_SYSTEM_PROMPT_KEY,
        MUSIC_SYSTEM_PROMPT_CHOICES,
        YUE2_SYSTEM_PROMPT,
        resolve_music_system_prompt,
        clean_user_custom_lyrics,
        clean_user_custom_directives,
        detect_existing_lyrics,
        build_music_task_prompt,
        generate_fallback_song_lyrics,
        clean_repetition_artifacts,
        normalize_lyrics_sections,
        parse_music_response,
    )
except (ImportError, ValueError):
    from core.music import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        MUSIC_SYSTEM_PROMPT_PRESETS,
        MUSIC_CUSTOM_SYSTEM_PROMPT_KEY,
        MUSIC_SYSTEM_PROMPT_CHOICES,
        YUE2_SYSTEM_PROMPT,
        resolve_music_system_prompt,
        clean_user_custom_lyrics,
        clean_user_custom_directives,
        detect_existing_lyrics,
        build_music_task_prompt,
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
