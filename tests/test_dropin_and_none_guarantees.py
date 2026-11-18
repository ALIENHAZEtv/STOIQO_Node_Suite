"""
[STOIQO] Dynamic Drop-In & 'None' Bypass Architectural Guarantee Suite
=====================================================================
Validates:
1. Full 'None' Bypass:
   - All 3 layers set to 'None' return empty prompt directives.
   - Output parsing without XML falls back cleanly to (prompt, auto-tags, default-negative).
2. Drop-in Markdown Guarantees:
   - Creating a .md file directly in main_prompts/ auto-injects _contract.md.
   - Creating a .md file directly in type_prompts/ auto-injects into Layer 2.
   - Creating a .md file directly in style_prompts/ auto-injects into Layer 3.
3. CRUD API Guarantees with new folder taxonomy (main_prompts, type_prompts, style_prompts).
"""

import os
import sys
import unittest

suite_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if suite_root not in sys.path:
    sys.path.insert(0, suite_root)

import core.image.loader as loader
from core.image.loader import (
    MAIN_PROMPTS_DIR,
    TYPE_PROMPTS_DIR,
    STYLE_PROMPTS_DIR,
    resolve_system_prompt,
    resolve_prompt_type,
    resolve_artistic_style,
    build_dynamic_system_prompt,
    reload_image_definitions,
)
from core.text_processing import parse_three_way_prompt, post_process_caption
from core.image.crud_api import save_definition, get_definition, delete_definition, list_definitions


class TestDropInAndNoneGuarantees(unittest.TestCase):

    def setUp(self):
        reload_image_definitions()

    # ── 1. TEST FULL 'NONE' BYPASS ──────────────────────────────────────────────
    def test_01_none_bypass_returns_empty_and_does_not_pollute(self):
        """Verifies that selecting 'None' across all layers bypasses injections completely."""
        sys_res = resolve_system_prompt("None (Raw / No System Prompt)")
        self.assertEqual(sys_res, "", "System prompt with None must resolve to empty string.")

        sys_res_short = resolve_system_prompt("None")
        self.assertEqual(sys_res_short, "", "System prompt with short 'None' must resolve to empty string.")

        type_res = resolve_prompt_type("None (Freeform / No Format Directive)")
        self.assertEqual(type_res, "", "Prompt type with None must resolve to empty string.")

        style_res = resolve_artistic_style("None (No Style Injection)")
        self.assertEqual(style_res, "None", "Artistic style with None must resolve to 'None'.")

        # Fusion when base system prompt is empty
        fused = build_dynamic_system_prompt(
            base_system_prompt="",
            prompt_type="None (Freeform / No Format Directive)",
            artistic_style="None (No Style Injection)",
        )
        self.assertEqual(fused, "", "Fused prompt must be empty if base system prompt is empty.")

    def test_02_parsing_raw_llm_response_without_xml(self):
        """Verifies that if the VLM outputs raw text without XML, the Python engine handles it seamlessly."""
        raw_response = (
            "A breathtaking cinematic wide-angle shot of a lone wanderer walking across "
            "an endless desert of luminescent blue sand under a starry galaxy, dramatic rim lighting, "
            "detailed fabric textures."
        )

        prompt_out, tags_out, neg_out = parse_three_way_prompt(raw_response)

        # 1. Prompt pin must receive the entire clean raw response
        self.assertEqual(prompt_out, raw_response.strip())

        # 2. Tags pin must automatically synthesize clean tags from the text
        self.assertGreater(len(tags_out), 0)
        self.assertIn("desert", tags_out.lower())
        self.assertIn("wanderer", tags_out.lower())
        self.assertLessEqual(len(tags_out.split()), 65)

        # 3. Negative pin must supply safety defaults
        self.assertGreater(len(neg_out), 0)
        self.assertIn("blurry", neg_out.lower())
        self.assertIn("distorted", neg_out.lower())

        # 4. Post-process caption pipeline must return a valid 4-tuple
        caption, tags, neg, tags_list = post_process_caption(
            raw_response,
            negative_prompt_prefix="watermark, ugly",
            prompt_type="None (Freeform / No Format Directive)",
            artistic_style="None (No Style Injection)",
        )
        self.assertEqual(caption, raw_response.strip())
        self.assertIn("watermark", neg)
        self.assertIn("ugly", neg)

    # ── 2. TEST DROP-IN MARKDOWN IN MAIN_PROMPTS ────────────────────────────────
    def test_03_drop_in_main_prompts_file_auto_fuses_contract(self):
        """Verifies that dropping a new .md into main_prompts automatically fuses _contract.md."""
        test_file = os.path.join(MAIN_PROMPTS_DIR, "test_director_unit.md")
        test_content = (
            "---\n"
            "name: \"Unit Test Vision Director\"\n"
            "aliases: [\"Test Vision Director\"]\n"
            "temperature: 0.85\n"
            "max_new_tokens: 512\n"
            "top_p: 0.95\n"
            "top_k: 45\n"
            "order: 99\n"
            "---\n"
            "# ROLE & IDENTITY\n"
            "You are a dedicated Unit Test Director specialized in testing modular drop-in architecture.\n"
        )
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            # Reload and verify discovery
            reload_image_definitions()

            self.assertIn("Unit Test Vision Director", loader.SYSTEM_PERSONAS)
            self.assertIn("Unit Test Vision Director", loader.SYSTEM_PROMPT_PRESETS)

            # INVARIANT: Contract was automatically fused to the end!
            preset = loader.SYSTEM_PROMPT_PRESETS["Unit Test Vision Director"]
            self.assertIn("Unit Test Director specialized in testing", preset)
            self.assertIn("# INVIOLABLE RULES & OUTPUT PURITY", preset)
            self.assertIn("<PROMPT>, <TAGS>, and <NEGATIVE>", preset)

            # Also accessible via alias
            self.assertIn("Test Vision Director", loader.SYSTEM_PROMPT_PRESETS)
            self.assertEqual(loader.SYSTEM_PROMPT_PRESETS["Test Vision Director"], preset)

        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)
            reload_image_definitions()

        self.assertNotIn("Unit Test Vision Director", loader.SYSTEM_PERSONAS)

    # ── 3. TEST DROP-IN MARKDOWN IN TYPE_PROMPTS ────────────────────────────────
    def test_04_drop_in_type_prompts_file(self):
        """Verifies that dropping a new .md into type_prompts is loaded as Layer 2."""
        test_file = os.path.join(TYPE_PROMPTS_DIR, "test_format_unit.md")
        test_content = (
            "---\n"
            "name: \"Unit Test Format Block\"\n"
            "order: 99\n"
            "---\n"
            "Structure the output in 3 bullet points describing perspective, action, and lighting."
        )
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            reload_image_definitions()

            self.assertIn("Unit Test Format Block", loader.PROMPT_TYPES)
            self.assertIn("Unit Test Format Block", loader.PROMPT_TYPE_DIRECTIVES)
            self.assertEqual(
                loader.PROMPT_TYPE_DIRECTIVES["Unit Test Format Block"],
                "Structure the output in 3 bullet points describing perspective, action, and lighting."
            )

            # Test fusion in Layer 2
            fused = build_dynamic_system_prompt(
                base_system_prompt="BASE SYSTEM PROMPT\n# REQUIRED OUTPUT CONTRACT\nEmit XML.",
                prompt_type="Unit Test Format Block",
                artistic_style="None (No Style Injection)",
            )
            self.assertIn("# LAYER 2 — STRUCTURAL OUTPUT FORMAT", fused)
            self.assertIn("Structure the output in 3 bullet points", fused)

        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)
            reload_image_definitions()

        self.assertNotIn("Unit Test Format Block", loader.PROMPT_TYPES)

    # ── 4. TEST DROP-IN MARKDOWN IN STYLE_PROMPTS ───────────────────────────────
    def test_05_drop_in_style_prompts_file(self):
        """Verifies that dropping a new .md into style_prompts is loaded as Layer 3."""
        test_file = os.path.join(STYLE_PROMPTS_DIR, "test_style_unit.md")
        test_content = (
            "---\n"
            "name: \"Unit Test Vaporwave Glitch\"\n"
            "medium_type: \"Retro Digital Glitch Art\"\n"
            "prohibited: \"photographic, 35mm, real world\"\n"
            "replacement: \"pixel dithering, neon scanlines, VHS tracking errors\"\n"
            "order: 99\n"
            "---\n"
            "Infuse vivid pastel pink, cyan neon gradients, and authentic VHS chromatic aberration."
        )
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            reload_image_definitions()

            self.assertIn("Unit Test Vaporwave Glitch", loader.ARTISTIC_STYLES)
            self.assertIn("Unit Test Vaporwave Glitch", loader.ARTISTIC_STYLE_DIRECTIVES)

            # Test Layer 3 aesthetic injection
            fused = build_dynamic_system_prompt(
                base_system_prompt="BASE SYSTEM PROMPT\n# REQUIRED OUTPUT CONTRACT\nEmit XML.",
                prompt_type="None (Freeform / No Format Directive)",
                artistic_style="Unit Test Vaporwave Glitch",
            )
            self.assertIn("# LAYER 3 — VISUAL AESTHETIC INJECTION", fused)
            self.assertIn("Infuse vivid pastel pink", fused)

        finally:
            if os.path.isfile(test_file):
                os.remove(test_file)
            reload_image_definitions()

        self.assertNotIn("Unit Test Vaporwave Glitch", loader.ARTISTIC_STYLES)

    # ── 5. TEST CRUD API OPERATIONS WITH NEW TAXONOMY ───────────────────────────
    def test_06_crud_api_lifecycle_with_new_taxonomy(self):
        """Verifies that CRUD API functions correctly with 'main_prompts', 'type_prompts', 'style_prompts'."""
        item_name = "CRUD Test Custom Spec"

        # 1. Save definition under kind 'main_prompts'
        res = save_definition(
            kind="main_prompts",
            name=item_name,
            body="Custom prompt instructions for CRUD validation.",
            frontmatter={"temperature": 0.55, "max_new_tokens": 768, "order": 95},
        )
        self.assertEqual(res.get("status"), "ok", f"Save failed: {res}")

        try:
            # 2. Get definition
            item = get_definition("main_prompts", item_name)
            self.assertIsNotNone(item)
            self.assertEqual(item["name"], item_name)
            self.assertEqual(item["body"], "Custom prompt instructions for CRUD validation.")
            self.assertEqual(float(item["frontmatter"]["temperature"]), 0.55)

            # 3. Verify it is registered in live memory
            self.assertIn(item_name, loader.SYSTEM_PERSONAS)

            # 4. Delete definition
            del_res = delete_definition("main_prompts", item_name)
            self.assertEqual(del_res.get("status"), "ok", f"Delete failed: {del_res}")

            # 5. Verify it is removed from live memory
            self.assertNotIn(item_name, loader.SYSTEM_PERSONAS)

        finally:
            # Safety cleanup if delete failed
            delete_definition("main_prompts", item_name)


if __name__ == "__main__":
    unittest.main()
