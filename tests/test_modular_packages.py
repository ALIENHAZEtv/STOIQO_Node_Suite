"""
[STOIQO] Unit Tests — Modular Domain Packages (Image & Music)
Tests clean isolation and exports between core.image and core.music.
"""

import unittest
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.image import (
    SYSTEM_PROMPT_PRESETS,
    PROMPT_TYPES,
    ARTISTIC_STYLES,
    resolve_system_prompt,
    resolve_prompt_type,
    resolve_artistic_style,
)
from core.music import (
    GENRE_PRESETS,
    VOCAL_PRESETS,
    SONG_STRUCTURES,
    TEMPO_PRESETS,
    MUSIC_SYSTEM_PROMPT_PRESETS,
    resolve_music_system_prompt,
    build_music_task_prompt,
    parse_music_response,
)


class TestModularPackages(unittest.TestCase):

    def test_image_package_exports(self):
        self.assertIn("Generative Prompt", SYSTEM_PROMPT_PRESETS)
        self.assertIn("Detailed Narrative", PROMPT_TYPES)
        self.assertIn("Photorealistic (Modern Digital RAW)", ARTISTIC_STYLES)
        res_sys = resolve_system_prompt("Generative Prompt", has_image=True)
        self.assertTrue(len(res_sys) > 50)

    def test_music_package_exports(self):
        self.assertIn("Pop (Contemporary, Synthpop, Indie Pop)", GENRE_PRESETS)
        self.assertIn("Warm Expressive Female Vocal", VOCAL_PRESETS)
        self.assertIn("Standard Pop/Rock (Verse 1, Chorus, Verse 2, Chorus, Bridge, Chorus, Outro)", SONG_STRUCTURES)
        self.assertIn("Upbeat Driving (115-128 BPM)", TEMPO_PRESETS)
        self.assertIn("YuE2 / Suno Master Lyricist & Sound Architect", MUSIC_SYSTEM_PROMPT_PRESETS)

        task = build_music_task_prompt(
            idea="Canzone d'estate",
            genre="Pop",
            vocal="Warm Expressive Female Vocal",
            language="Italian",
            structure=SONG_STRUCTURES[0],
            tempo=TEMPO_PRESETS[3],
        )
        self.assertIn("[STYLE]", task)
        self.assertIn("[LYRICS]", task)

        parsed = parse_music_response(
            "[TITLE]\nNotte Serena\n\n[STYLE]\nPop, 120 BPM\n\n[LYRICS]\n[Verse 1]\nCammino solo nella sera",
            fallback_idea="pop",
            target_language="Italian",
        )
        self.assertEqual(parsed["title"], "Notte Serena")
        self.assertIn("Pop", parsed["style"])
        self.assertIn("[Verse 1]", parsed["lyrics"])


if __name__ == "__main__":
    unittest.main()
