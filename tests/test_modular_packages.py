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
)
from core.music import (
    GENRE_PRESETS,
    VOCAL_PRESETS,
    SONG_STRUCTURES,
    TEMPO_PRESETS,
    MUSIC_SYSTEM_PROMPT_PRESETS,
    build_music_task_prompt,
    parse_music_response,
)


class TestModularPackages(unittest.TestCase):

    def test_image_package_exports(self):
        self.assertIn("Generative Prompt", SYSTEM_PROMPT_PRESETS)
        self.assertIn("Krea 2 Turbo Prompt", SYSTEM_PROMPT_PRESETS)
        self.assertIn("MiniMax Video Prompt", SYSTEM_PROMPT_PRESETS)
        self.assertIn("SeedVR2 Upscale Guide", SYSTEM_PROMPT_PRESETS)
        self.assertIn("Detailed Narrative", PROMPT_TYPES)
        self.assertIn("Photorealistic (Modern Digital RAW)", ARTISTIC_STYLES)
        res_sys = resolve_system_prompt("Krea 2 Turbo Prompt", has_image=True)
        self.assertTrue(len(res_sys) > 50)

    def test_music_package_exports(self):
        self.assertIn("Pop (Contemporary, Synthpop, Indie Pop)", GENRE_PRESETS)
        self.assertIn("Warm Expressive Female Vocal", VOCAL_PRESETS)
        self.assertIn("Standard Pop/Rock (Verse 1, Chorus, Verse 2, Chorus, Bridge, Chorus, Outro)", SONG_STRUCTURES)
        self.assertIn("Upbeat Driving (115-128 BPM)", TEMPO_PRESETS)
        self.assertIn("Universal Music Architect & Lyricist (YuE2 & AI Audio)", MUSIC_SYSTEM_PROMPT_PRESETS)
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

    def test_model_manager_shared_registry(self):
        from core.model_manager import ModelManager
        mgr1 = ModelManager()
        mgr2 = ModelManager()
        self.assertIs(mgr1.model, mgr2.model)
        self.assertEqual(mgr1.current_cache_key, mgr2.current_cache_key)

        orig_model = mgr1.model
        orig_key = mgr1.current_cache_key
        try:
            mgr1.model = "sentinel_model_obj"
            mgr1.current_cache_key = "sentinel_cache_key"
            self.assertEqual(mgr2.model, "sentinel_model_obj")
            self.assertEqual(mgr2.current_cache_key, "sentinel_cache_key")
        finally:
            mgr1.model = orig_model
            mgr1.current_cache_key = orig_key


if __name__ == "__main__":
    unittest.main()
