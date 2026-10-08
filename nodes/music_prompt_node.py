"""
[STOIQO] Music Prompt & Lyrics Engine (YuE2 / Suno)
Generates production-grade musical style descriptors and rhymed, structured lyrics
directly feedable into YuE2, Suno, and AI music workflows.
Supports optional multimodal visual grounding from cover art or video frames.
"""

import os
import random
import numpy as np
import torch
from PIL import Image

try:
    from ..core import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        YUE2_SYSTEM_PROMPT,
        build_music_task_prompt,
        parse_music_response,
        tensor_to_pil,
        ModelManager,
    )
except (ImportError, ValueError):
    from core import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        YUE2_SYSTEM_PROMPT,
        build_music_task_prompt,
        parse_music_response,
        tensor_to_pil,
        ModelManager,
    )


class StoiqoMusicPromptEngineNode:
    """
    [STOIQO] Music Prompt & Lyrics Engine
    Turns ideas, themes, and optional visual artwork into structured YuE2 styles & lyrics.
    """

    def __init__(self):
        self.model_mgr = ModelManager()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "idea": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "An upbeat summer indie pop song about a nostalgic coastal road trip with driving rhythms and melodic guitars.",
                        "tooltip": "The core musical idea, mood, narrative, or concept for the song.",
                    },
                ),
                "genre": (
                    GENRE_PRESETS,
                    {
                        "default": GENRE_PRESETS[0],
                        "tooltip": "Musical genre and acoustic characteristics.",
                    },
                ),
                "vocal_type": (
                    VOCAL_PRESETS,
                    {
                        "default": VOCAL_PRESETS[0],
                        "tooltip": "Singing voice style, gender, and timbre.",
                    },
                ),
                "language": (
                    LANGUAGE_PRESETS,
                    {
                        "default": LANGUAGE_PRESETS[0],
                        "tooltip": "Language of the lyrics and vocal delivery.",
                    },
                ),
                "structure": (
                    SONG_STRUCTURES,
                    {
                        "default": SONG_STRUCTURES[0],
                        "tooltip": "Song arrangement and verse/chorus structure.",
                    },
                ),
                "tempo": (
                    TEMPO_PRESETS,
                    {
                        "default": TEMPO_PRESETS[0],
                        "tooltip": "BPM tempo range and rhythm drive.",
                    },
                ),
            },
            "optional": {
                "cover_image": (
                    "IMAGE",
                    {
                        "tooltip": "Optional visual inspiration (album cover, concept art). The model analyzes its mood and aesthetic.",
                    },
                ),
                "custom_directives": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Specific constraints, e.g. 'incorporate acoustic cello', 'mention character name Alex', 'no drums in verse 1'.",
                    },
                ),
                "stoiqo_model": (
                    "STOIQO_MODEL",
                    {
                        "tooltip": "Shared VLM model loaded via [STOIQO] VLM Model Loader to save VRAM.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Seed for deterministic lyrics & style generation.",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.65,
                        "min": 0.1,
                        "max": 1.5,
                        "step": 0.05,
                        "tooltip": "Creativity and lyrical variation (0.60-0.70 recommended for lyrical coherence).",
                    },
                ),
                "repetition_penalty": (
                    "FLOAT",
                    {
                        "default": 1.02,
                        "min": 1.0,
                        "max": 1.5,
                        "step": 0.01,
                        "tooltip": "Penalizes repetitive loops without degrading poetic vocabulary (1.01-1.04 recommended).",
                    },
                ),
                "max_new_tokens": (
                    "INT",
                    {
                        "default": 1536,
                        "min": 512,
                        "max": 3072,
                        "step": 64,
                        "tooltip": "Token limit for full lyrics and style generation (1536 recommended for complete songs).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "BOOLEAN", "STRING", "FLOAT")
    RETURN_NAMES = ("style", "lyrics", "title", "abc_planning", "mode", "max_duration")
    FUNCTION = "generate_music_prompt"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO/Audio & Music"

    def generate_music_prompt(
        self,
        idea,
        genre,
        vocal_type,
        language,
        structure,
        tempo,
        cover_image=None,
        custom_directives="",
        stoiqo_model=None,
        seed=0,
        temperature=0.65,
        repetition_penalty=1.02,
        max_new_tokens=1536,
    ):
        clean_idea = (idea or "").strip()
        if not clean_idea:
            clean_idea = "A melodic and uplifting contemporary song with warm instruments and evocative lyrics."

        active_mgr = stoiqo_model if stoiqo_model is not None else self.model_mgr
        if active_mgr.model is None:
            if getattr(active_mgr, "last_load_params", None) is not None:
                active_mgr.load_model(**active_mgr.last_load_params)
            else:
                target_repo = active_mgr.resolve_model_repo(model_preset=None, local_model_path="", model_mode=None)
                active_mgr.load_model(target_repo, "4bit - NF4 (Recommended - Low VRAM)")

        # Convert image tensor to PIL if provided
        img_pil = None
        if cover_image is not None:
            try:
                img_pil = tensor_to_pil(cover_image[0:1])
                print("[STOIQO Music] Multimodal mode enabled: analyzing visual cover artwork...")
            except Exception as e:
                print(f"[STOIQO Music] Warning converting cover image: {e}")

        # Build task prompt with multimodal grounding awareness
        task_prompt = build_music_task_prompt(
            idea=clean_idea,
            genre=genre,
            vocal=vocal_type,
            language=language,
            structure=structure,
            tempo=tempo,
            custom_directives=custom_directives,
            has_image=(img_pil is not None),
        )

        print(f"[STOIQO Music] Generating music style & lyrics for: '{clean_idea[:60]}'...")

        raw_output = active_mgr.generate_single(
            img_pil,
            task_prompt,
            YUE2_SYSTEM_PROMPT,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=0.90,
            repetition_penalty=repetition_penalty,
            is_multi_image=False,
            seed=seed,
        )

        print(f"[STOIQO Music] Raw LLM output: {len(raw_output)} chars generated.")
        if len(raw_output) < 200:
            print(f"[STOIQO Music Debug] Short raw output: {repr(raw_output)}")

        parsed = parse_music_response(raw_output, fallback_idea=clean_idea, target_language=language)

        # Word & char counts
        words = len(parsed["lyrics"].split())
        chars = len(parsed["lyrics"])

        print(f"[STOIQO Music] Generated Song: '{parsed['title']}' | {words} words in lyrics.")
        print(f"[STOIQO Music] Style: {parsed['style'][:80]}...")

        ui_info = [{
            "title": parsed["title"],
            "style": parsed["style"],
            "lyrics": parsed["lyrics"],
            "words": words,
            "chars": chars,
            "mode": parsed["mode"],
            "abc_planning": parsed["abc_planning"],
            "max_duration": parsed["max_duration"],
        }]

        return {
            "ui": {
                "music_info": ui_info,
            },
            "result": (
                parsed["style"],
                parsed["lyrics"],
                parsed["title"],
                parsed["abc_planning"],
                parsed["mode"],
                float(parsed["max_duration"]),
            ),
        }
