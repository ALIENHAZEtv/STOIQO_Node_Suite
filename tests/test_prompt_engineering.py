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

from core.music_prompts import (
    build_music_task_prompt,
    YUE2_SYSTEM_PROMPT,
    GENRE_PRESETS,
    VOCAL_PRESETS,
    LANGUAGE_PRESETS,
    SONG_STRUCTURES,
    TEMPO_PRESETS,
)


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
        self.assertIn("COMPLETEZZA TOTALE", prompt_it)


if __name__ == "__main__":
    unittest.main()
