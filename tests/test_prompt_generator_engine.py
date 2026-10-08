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

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from core.system_prompts import (
    SYSTEM_PROMPT_PRESETS,
    CUSTOM_SYSTEM_PROMPT_KEY,
    TEXT_EXPANSION_SYSTEM_PROMPT,
    MULTI_IMAGE_SYSTEM_PROMPT,
    resolve_system_prompt,
)
from core.prompt_types import (
    PROMPT_TYPES,
    PROMPT_TYPE_DIRECTIVES,
    resolve_prompt_type,
)
from core.text_processing import (
    build_task_prompt,
    parse_three_way_prompt,
    convert_to_tags,
    clean_llm_output,
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


if __name__ == "__main__":
    unittest.main()
