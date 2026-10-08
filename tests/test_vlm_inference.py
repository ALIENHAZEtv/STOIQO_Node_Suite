"""
[STOIQO] Hardware Integration Test — VLM Inference on Qwen2.5-VL
Executes full model inference to verify:
1. Absence of addCriterion loop (left padding verified).
2. Proper lyrics generation with musical section headers.
3. Zero placeholder phrases in output.
"""

import unittest
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.model_manager import ModelManager
from core.music_prompts import (
    YUE2_SYSTEM_PROMPT,
    build_music_task_prompt,
    parse_music_response,
)


class TestVLMInference(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mgr = ModelManager()
        target_repo = cls.mgr.resolve_model_repo(model_preset=None, local_model_path="", model_mode=None)
        cls.mgr.load_model(target_repo, "4bit - NF4 (Recommended - Low VRAM)")

    @classmethod
    def tearDownClass(cls):
        cls.mgr.unload_model()

    def test_e2e_song_generation_italian(self):
        idea = "La rinascita dell'amore tra le fiamme e la distruzione"
        task_prompt = build_music_task_prompt(
            idea=idea,
            genre="Metal (Heavy Metal, Symphonic Metal, Modern Metalcore)",
            vocal="Gritty Powerful Male Vocal",
            language="Italian",
            structure="Short & Punchy (Verse 1, Chorus, Verse 2, Chorus, Outro)",
            tempo="High Energy Fast (132-150 BPM)",
            has_image=False,
        )

        output = self.mgr.generate_single(
            pil_images=None,
            task_prompt=task_prompt,
            system_prompt=YUE2_SYSTEM_PROMPT,
            max_new_tokens=600,
            temperature=0.65,
            top_p=0.90,
            repetition_penalty=1.02,
            seed=42,
        )

        self.assertNotIn("addCriterion", output)
        parsed = parse_music_response(output, fallback_idea=idea, target_language="Italian")
        self.assertTrue(len(parsed["title"]) > 2)
        self.assertTrue(len(parsed["style"]) > 10)
        self.assertIn("[Verse 1]", parsed["lyrics"])
        self.assertNotIn("Parole che nascono dall'idea", parsed["lyrics"])
        self.assertNotIn("Incredibile Bellezza", parsed["lyrics"])


if __name__ == "__main__":
    unittest.main()
