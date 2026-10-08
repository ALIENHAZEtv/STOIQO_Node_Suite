"""
[STOIQO] Unit Tests — Prompt Engineering & Language Adaptation
Tests system prompt formulation, language steering, multimodal instructions,
and structure generation across diverse presets.
"""

import unittest
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

import importlib.util

spec = importlib.util.spec_from_file_location(
    "music_prompts", os.path.join(root, "core", "music_prompts.py")
)
music_prompts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(music_prompts)

build_music_task_prompt = music_prompts.build_music_task_prompt
YUE2_SYSTEM_PROMPT = music_prompts.YUE2_SYSTEM_PROMPT
GENRE_PRESETS = music_prompts.GENRE_PRESETS
VOCAL_PRESETS = music_prompts.VOCAL_PRESETS
LANGUAGE_PRESETS = music_prompts.LANGUAGE_PRESETS
SONG_STRUCTURES = music_prompts.SONG_STRUCTURES
TEMPO_PRESETS = music_prompts.TEMPO_PRESETS
MUSIC_SYSTEM_PROMPT_PRESETS = music_prompts.MUSIC_SYSTEM_PROMPT_PRESETS
MUSIC_CUSTOM_SYSTEM_PROMPT_KEY = music_prompts.MUSIC_CUSTOM_SYSTEM_PROMPT_KEY
resolve_music_system_prompt = music_prompts.resolve_music_system_prompt


class TestPromptEngineering(unittest.TestCase):

    def test_italian_prompt_adaptation(self):
        prompt = build_music_task_prompt(
            idea="Una canzone estiva sul mare e la libertà",
            genre="Pop (Contemporary, Synthpop, Indie Pop)",
            vocal="Warm Expressive Female Vocal",
            language="Italian",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[3],
            has_image=False,
        )
        self.assertIn("100% ITALIANO", prompt)
        self.assertIn("[STYLE]", prompt)
        self.assertIn("[LYRICS]", prompt)
        self.assertIn("Pop", prompt)

    def test_english_prompt_adaptation(self):
        prompt = build_music_task_prompt(
            idea="Cyberpunk futuristic chase through neon rain",
            genre="Electronic & EDM (Synthwave, House, Melodic Techno, Drum & Bass)",
            vocal="Deep Resonant Male Vocal",
            language="English",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[4],
            has_image=False,
        )
        self.assertIn("100% English", prompt)
        self.assertIn("[STYLE]", prompt)
        self.assertIn("[LYRICS]", prompt)

    def test_instrumental_directive(self):
        prompt = build_music_task_prompt(
            idea="Cinematic battle theme",
            genre="Cinematic & Epic (Orchestral, Hybrid Trailer, Ethereal Soundtrack)",
            vocal="Instrumental Only (No Vocals)",
            language="English",
            structure=SONG_STRUCTURES[5],
            tempo="Auto (Optimal for Genre)",
            has_image=False,
        )
        self.assertIn("INSTRUMENTAL", prompt)
        self.assertIn("Zero sung lyrics", prompt)

    def test_multimodal_visual_grounding(self):
        prompt_with_img = build_music_task_prompt(
            idea="Dark fantasy kingdom",
            genre="Metal (Heavy Metal, Symphonic Metal, Modern Metalcore)",
            vocal="Gritty Powerful Male Vocal",
            language="Italian",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[4],
            has_image=True,
        )
        self.assertIn("ANALISI MULTIMODALE", prompt_with_img)
        self.assertIn("VLM", prompt_with_img)

    def test_copyright_safe_system_prompt(self):
        # Guarantee system prompt contains original composition framing
        self.assertIn("100% original", YUE2_SYSTEM_PROMPT.lower())
        self.assertIn("fictional", YUE2_SYSTEM_PROMPT.lower())

    def test_completion_mandate_present(self):
        # Verify that system prompt and task prompt enforce full song completion
        self.assertIn("NEVER TRUNCATE", YUE2_SYSTEM_PROMPT)
        prompt_it = build_music_task_prompt(
            idea="Una canzone epica",
            genre="Metal",
            vocal="Gritty Powerful Male Vocal",
            language="Italian",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[3],
        )
    def test_custom_lyrics_prompt_instruction(self):
        prompt = build_music_task_prompt(
            idea="Una canzone",
            genre="Rock",
            vocal="Gritty Powerful Male Vocal",
            language="Italian",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[3],
            custom_lyrics="[Verse 1]\nParole mie scritte a mano",
        )
    def test_music_system_prompt_presets(self):
        self.assertIn("YuE2 / Suno Master Lyricist & Sound Architect", MUSIC_SYSTEM_PROMPT_PRESETS)
        self.assertIn("Pop & Radio Hitmaker", MUSIC_SYSTEM_PROMPT_PRESETS)
        self.assertIn("Rock, Metal & Alternative Producer", MUSIC_SYSTEM_PROMPT_PRESETS)
        self.assertIn("Acoustic Ballad & Folk Storyteller", MUSIC_SYSTEM_PROMPT_PRESETS)
        self.assertIn("Hip-Hop, Rap & Urban Flow", MUSIC_SYSTEM_PROMPT_PRESETS)
        self.assertIn("Cinematic & Orchestral Composer", MUSIC_SYSTEM_PROMPT_PRESETS)

        pop_prompt = resolve_music_system_prompt("Pop & Radio Hitmaker")
        self.assertIn("Billboard #1 Pop Songwriter", pop_prompt)

    def test_custom_system_prompt_override(self):
        custom_instructions = "You are a Cyberpunk Synthwave Producer specializing in dark neon dystopian lyrics."
        res = resolve_music_system_prompt(MUSIC_CUSTOM_SYSTEM_PROMPT_KEY, custom_text=custom_instructions)
        self.assertEqual(res, custom_instructions)

        # Fallback when custom_text is empty
        fallback_res = resolve_music_system_prompt(MUSIC_CUSTOM_SYSTEM_PROMPT_KEY, custom_text="")
        self.assertEqual(fallback_res, YUE2_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
