"""
[STOIQO] Unit Tests — Visual Prompt Generator Engine
Validates:
1. Layer 1 System Prompts & SSOT Dispatch Logic
2. Layer 2 Prompt Type Directives & Resolvers
3. Task Prompt Builder & Three-Way Parser (<PROMPT>, <TAGS>, <NEGATIVE>)
4. Tag Conversion, Syntax Cleaning & Safety Filtering
"""

import unittest
import sys
import os
import torch

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.image import (
    SYSTEM_PROMPT_PRESETS,
    CUSTOM_SYSTEM_PROMPT_KEY,
    TEXT_EXPANSION_SYSTEM_PROMPT,
    MULTI_IMAGE_SYSTEM_PROMPT,
    resolve_system_prompt,
    PROMPT_TYPES,
    resolve_prompt_type,
)
from core.text_processing import (
    parse_three_way_prompt,
    convert_to_tags,
)


class TestPromptGeneratorEngine(unittest.TestCase):

    def test_system_prompt_presets(self):
        for name, prompt in SYSTEM_PROMPT_PRESETS.items():
            self.assertIn("# INVIOLABLE RULES & OUTPUT PURITY", prompt)
            self.assertIn("STRICT ZERO FILLER", prompt)
            self.assertIn("ABSOLUTE OUTPUT CONTRACT", prompt)
            self.assertIn("<PROMPT>", prompt)
            self.assertIn("<TAGS>", prompt)
            self.assertIn("<NEGATIVE>", prompt)

    def test_ssot_dispatch_logic(self):
        self.assertEqual(
            resolve_system_prompt("Generative Prompt", has_image=False),
            TEXT_EXPANSION_SYSTEM_PROMPT,
        )
        self.assertEqual(
            resolve_system_prompt("Generative Prompt", has_image=True, is_multi_image=False),
            SYSTEM_PROMPT_PRESETS["Generative Prompt"],
        )
        self.assertEqual(
            resolve_system_prompt("Generative Prompt", has_image=True, is_multi_image=True),
            MULTI_IMAGE_SYSTEM_PROMPT,
        )
        self.assertEqual(
            resolve_system_prompt(CUSTOM_SYSTEM_PROMPT_KEY, custom_system_prompt="Custom Prompt"),
            "Custom Prompt",
        )

    def test_prompt_type_directives(self):
        for ptype in PROMPT_TYPES:
            directive = resolve_prompt_type(ptype)
            self.assertIsNotNone(directive)
            self.assertGreater(len(directive), 10)

    def test_three_way_parsing(self):
        raw_output = """
<PROMPT>A breathtaking cinematic photograph of a majestic white tiger in a snowstorm, 8k resolution, sharp focus.</PROMPT>
<TAGS>white tiger, snowstorm, winter, cinematic, sharp focus, 8k, majestic, cold</TAGS>
<NEGATIVE>blurry, low quality, oversaturated, deformed paws</NEGATIVE>
"""
        prompt_text, tags_text, neg_prompt = parse_three_way_prompt(raw_output)
        self.assertIn("majestic white tiger", prompt_text)
        self.assertIn("white tiger", tags_text)
        self.assertIn("blurry", neg_prompt)

    def test_convert_to_tags(self):
        caption = "A beautiful girl with blue eyes and long blonde hair standing under cherry blossoms."
        tags = convert_to_tags(caption)
        self.assertIn("beautiful", tags)
        self.assertIn("blue eyes", tags)
        self.assertIn("blonde hair", tags)

    def test_artistic_medium_enforcement_and_photographic_suppression(self):
        from core.text_processing import build_task_prompt, post_process_caption
        from core.image.system_prompts import build_dynamic_system_prompt

        # 1. Test task prompt injection for Anime & Manga
        task_anime = build_task_prompt(
            prompt_type="Detailed Narrative",
            artistic_style="Anime & Manga (2D Cel-shaded)",
            input_text="a girl in a coffee shop",
        )
        self.assertIn("MANDATORY ARTISTIC MEDIUM & STYLE", task_anime)
        self.assertIn("STRICT PROHIBITION", task_anime)
        self.assertIn("Anime & Manga (2D Cel-shaded)", task_anime)
        self.assertIn("Do NOT generate a photograph", task_anime)

        # 2. Test dynamic system prompt override for Oil Painting
        sys_oil = build_dynamic_system_prompt(
            base_system_prompt="Base System Persona\n# REQUIRED OUTPUT CONTRACT",
            prompt_type="Detailed Narrative",
            artistic_style="Oil Painting & Classical Fine Art",
        )
        self.assertIn("INVIOLABLE MEDIUM OVERRIDE & PROHIBITIONS", sys_oil)
        self.assertIn("Oil Painting / Classical Canvas Fine Art", sys_oil)

        # 3. Test that image task prompt incorporates style transformation objective
        from nodes.prompt_generator_node import StoiqoPromptGeneratorNode
        gen = StoiqoPromptGeneratorNode()
        dummy_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)

        captured_task_prompt = []
        class MockTransformVLM:
            def generate_single(self, task_prompt, **kwargs):
                captured_task_prompt.append(task_prompt)
                return "<PROMPT>2D anime girl playing soccer</PROMPT><TAGS>anime, 1girl, soccer</TAGS><NEGATIVE>photorealistic</NEGATIVE>"

        gen.generate_prompt(
            prompt_style="Anime & Manga (2D Cel-shaded)",
            image_input=dummy_tensor,
            model=MockTransformVLM(),
        )
        self.assertTrue(len(captured_task_prompt) > 0)
        self.assertIn("Transform and reimagine the visual scene", captured_task_prompt[0])
        self.assertIn("Anime & Manga (2D Cel-shaded)", captured_task_prompt[0])
        self.assertIn("Do NOT describe or caption the image as a photograph", captured_task_prompt[0])

    def test_prompt_generator_caching_and_low_vram_offload(self):
        from nodes.prompt_generator_node import StoiqoPromptGeneratorNode, _PROMPT_CACHE
        gen = StoiqoPromptGeneratorNode()

        class MockVLM:
            def __init__(self):
                self.calls = 0
                self.unloaded = False
                self.keep_in_vram = False

            def generate_single(self, **kwargs):
                self.calls += 1
                return "<PROMPT>Cached cybernetic city</PROMPT><TAGS>cyberpunk, city</TAGS><NEGATIVE>low quality</NEGATIVE>"

            def unload_model(self):
                self.unloaded = True

        mock_vlm = MockVLM()
        _PROMPT_CACHE.clear()

        # Run 1: with enable_cache=True -> executes generation and unloads
        out1 = gen.generate_prompt(
            user_directives="cybernetic city",
            model=mock_vlm,
            enable_cache=True,
            seed=12345,
        )
        self.assertEqual(mock_vlm.calls, 1)
        self.assertTrue(mock_vlm.unloaded)
        self.assertIn("cybernetic city", out1["result"][0][0])

        # Reset unload flag for second run
        mock_vlm.unloaded = False

        # Run 2: identical parameters with enable_cache=True -> hits cache without calling VLM again
        out2 = gen.generate_prompt(
            user_directives="cybernetic city",
            model=mock_vlm,
            enable_cache=True,
            seed=12345,
        )
        self.assertEqual(mock_vlm.calls, 1)  # Cache hit, calls counter unchanged!
        self.assertTrue(mock_vlm.unloaded)   # Low-VRAM offloading executed in finally block
        self.assertEqual(out1["result"][0], out2["result"][0])


if __name__ == "__main__":
    unittest.main()

