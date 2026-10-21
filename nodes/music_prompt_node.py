"""
[STOIQO] Music Prompt & Lyrics Engine (YuE2 / Suno)
Generates production-grade musical style descriptors and rhymed, structured lyrics
directly feedable into YuE2, Suno, and AI music workflows.
Supports optional multimodal visual grounding from cover art or video frames.
"""


try:
    from ..core.music import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        MUSIC_SYSTEM_PROMPT_CHOICES,
        resolve_music_system_prompt,
        build_music_task_prompt,
        parse_music_response,
        clean_user_custom_lyrics,
        clean_user_custom_directives,
    )
    from ..core import tensor_to_pil, ModelManager
except (ImportError, ValueError):
    from core.music import (
        GENRE_PRESETS,
        VOCAL_PRESETS,
        LANGUAGE_PRESETS,
        SONG_STRUCTURES,
        TEMPO_PRESETS,
        MUSIC_SYSTEM_PROMPT_CHOICES,
        resolve_music_system_prompt,
        build_music_task_prompt,
        parse_music_response,
        clean_user_custom_lyrics,
        clean_user_custom_directives,
    )
    from core import tensor_to_pil, ModelManager


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
                "system_prompt": (
                    MUSIC_SYSTEM_PROMPT_CHOICES,
                    {
                        "default": MUSIC_SYSTEM_PROMPT_CHOICES[0],
                        "tooltip": "AI Producer Persona & System Prompt: Select a specialized music director persona, or select 'Custom (Manual Override)' to write your own custom system instructions below.",
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
                "custom_system_prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Active only when system_prompt = 'Custom'. Write your custom AI music producer system instructions here...",
                        "tooltip": "Custom system instructions for the music engine. Revealed dynamically on canvas when system_prompt is set to 'Custom'.",
                    },
                ),
                "custom_lyrics": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional: Write or paste your own lyrics. Leave blank for AI lyric generation...",
                        "tooltip": "Optional: Write or paste your own lyrics. When provided, the node preserves your lyrics 100% exactly as written, while the AI analyzes them to formulate the matching YuE2 Style prompt, BPM, Duration, and Mode.",
                    },
                ),
                "custom_directives": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "Optional constraints (e.g. 'incorporate acoustic cello', 'no drums in verse 1')...",
                        "tooltip": "Specific constraints, e.g. 'incorporate acoustic cello', 'mention character name Alex', 'no drums in verse 1'.",
                    },
                ),
                "cover_image": (
                    "IMAGE",
                    {
                        "tooltip": "Optional visual inspiration (album cover, concept art). The model analyzes its mood and aesthetic.",
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
                        "default": 0.55,
                        "min": 0.1,
                        "max": 1.5,
                        "step": 0.05,
                        "tooltip": "Creativity and lyrical variation (0.50-0.60 recommended for tight rhyming & zero CJK drift).",
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
                        "default": 3072,
                        "min": 256,
                        "max": 8192,
                        "step": 64,
                        "tooltip": "Token limit for full lyrics and style generation (2560-4096 recommended for complete songs).",
                    },
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = (
        "STRING",
        "STRING",
        "STRING",
        "BOOLEAN",
        "STRING",
        "FLOAT",
        "INT",
        "STRING",
        "STRING",
        "STRING",
        "STRING",
        "INT",
    )
    RETURN_NAMES = (
        "style",
        "lyrics",
        "title",
        "abc_planning",
        "mode",
        "max_duration",
        "bpm",
        "musical_key",
        "time_signature",
        "genre_tags",
        "vocal_description",
        "seed",
    )
    FUNCTION = "generate_music_prompt"
    OUTPUT_NODE = True
    CATEGORY = "STOIQO"

    def generate_music_prompt(
        self,
        idea,
        system_prompt=MUSIC_SYSTEM_PROMPT_CHOICES[0],
        genre=GENRE_PRESETS[0],
        vocal_type=VOCAL_PRESETS[0],
        language=LANGUAGE_PRESETS[0],
        structure=SONG_STRUCTURES[0],
        tempo=TEMPO_PRESETS[0],
        custom_system_prompt="",
        custom_lyrics="",
        cover_image=None,
        custom_directives="",
        stoiqo_model=None,
        seed=0,
        temperature=0.55,
        repetition_penalty=1.02,
        max_new_tokens=3072,
        unique_id=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        clean_idea = (idea or "").strip()
        if not clean_idea:
            clean_idea = f"An original {genre} song featuring {vocal_type} in {language} with {tempo} tempo."

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

        # Sanitize any shifted widget values from LiteGraph deserialization (e.g. 'randomize', numbers)
        clean_lyrics_in = clean_user_custom_lyrics(custom_lyrics)
        clean_directives_in = clean_user_custom_directives(custom_directives)

        # Resolve active system prompt (preset or custom manual override)
        active_system_prompt = resolve_music_system_prompt(system_prompt, custom_system_prompt)

        # Build task prompt with multimodal grounding awareness and custom lyrics
        task_prompt = build_music_task_prompt(
            idea=clean_idea,
            genre=genre,
            vocal=vocal_type,
            language=language,
            structure=structure,
            tempo=tempo,
            custom_directives=clean_directives_in,
            has_image=(img_pil is not None),
            custom_lyrics=clean_lyrics_in,
        )

        # Clamp temperature for structured lyrical generation:
        # LLMs (especially Qwen2.5-VL-7B) at temp > 0.65 suffer token entropy collapse
        # and start hallucinating numbers, guitar gauges, and corrupted tokens.
        eff_temperature = min(max(float(temperature), 0.1), 0.60)
        if abs(eff_temperature - float(temperature)) > 0.01:
            print(f"[STOIQO Music] Notice: Clamping temperature from {temperature:.2f} to {eff_temperature:.2f} to ensure coherent, rhyming singable lyrics.")

        print(f"[STOIQO Music] Generating music style & lyrics for: '{clean_idea[:60]}'...")

        # Discover target node IDs for live WebSocket streaming
        stream_ids = []
        if unique_id is not None:
            stream_ids.append(str(unique_id))
            if prompt and isinstance(prompt, dict):
                uid_str = str(unique_id)
                for nid, ninfo in prompt.items():
                    if isinstance(ninfo, dict) and "inputs" in ninfo:
                        inputs_dict = ninfo["inputs"]
                        for inval in inputs_dict.values():
                            if isinstance(inval, list) and len(inval) > 0 and str(inval[0]) == uid_str:
                                stream_ids.append(str(nid))

        raw_output = active_mgr.generate_single(
            img_pil,
            task_prompt,
            active_system_prompt,
            max_new_tokens=max_new_tokens,
            temperature=eff_temperature,
            top_p=0.85,
            repetition_penalty=repetition_penalty,
            is_multi_image=False,
            seed=seed,
            node_id=stream_ids,
        )

        print(f"[STOIQO Music] Raw LLM output: {len(raw_output)} chars generated.")
        if len(raw_output) < 200:
            print(f"[STOIQO Music Debug] Short raw output: {repr(raw_output)}")

        parsed = parse_music_response(
            raw_output,
            fallback_idea=clean_idea,
            target_language=language,
            genre=genre,
            vocal=vocal_type,
            tempo=tempo,
            structure=structure,
            custom_lyrics=clean_lyrics_in,
        )

        # Word & char counts
        words = len(parsed["lyrics"].split())
        chars = len(parsed["lyrics"])

        print(f"[STOIQO Music] Generated Song: '{parsed['title']}' | {words} words in lyrics.")
        print(f"[STOIQO Music] Style: {parsed['style'][:80]}...")

        bpm_val = int(parsed.get("bpm", 120))
        key_val = str(parsed.get("musical_key", "C Minor"))
        time_sig_val = str(parsed.get("time_signature", "4/4"))
        gtags_val = str(parsed.get("genre_tags", ""))
        vdesc_val = str(parsed.get("vocal_description", ""))

        ui_info = [{
            "title": parsed["title"],
            "style": parsed["style"],
            "lyrics": parsed["lyrics"],
            "words": words,
            "chars": chars,
            "mode": parsed["mode"],
            "abc_planning": parsed["abc_planning"],
            "max_duration": parsed["max_duration"],
            "bpm": bpm_val,
            "musical_key": key_val,
            "time_signature": time_sig_val,
            "genre_tags": gtags_val,
            "vocal_description": vdesc_val,
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
                bpm_val,
                key_val,
                time_sig_val,
                gtags_val,
                vdesc_val,
                int(seed),
            ),
        }
