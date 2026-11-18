"""
[STOIQO] Unit Tests for Dynamic Prompt Engine CRUD API
=====================================================
Tests Create, Read, Update, Delete for Personas, Types, and Styles,
including core protection, file persistence, and real-time SSOT reloading.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.image.crud_api import (
    list_definitions,
    get_definition,
    save_definition,
    delete_definition,
    CORE_PROTECTED,
)
from core.image.loader import (
    reload_image_definitions,
    SYSTEM_PERSONAS,
    PROMPT_TYPES,
    ARTISTIC_STYLES,
    NON_PHOTOGRAPHIC_STYLES,
    build_dynamic_system_prompt,
)


class TestPromptEngineCRUD(unittest.TestCase):
    def setUp(self):
        pass

    def test_01_list_definitions_and_krea_styles(self):
        print("Running test_01...", flush=True)
        # 1. Styles list contains foundational presets + Krea styles
        styles = list_definitions("styles")
        print(f"Loaded {len(styles)} styles.", flush=True)
        self.assertGreater(len(styles), 280)
        style_names = [s["name"] for s in styles]

        self.assertIn("Auto-Detect / Preserve Original", style_names)
        self.assertIn("Anime & Manga (2D Cel-shaded)", style_names)
        self.assertTrue(any(s.startswith("Anime //") for s in style_names))
        self.assertTrue(any(s.startswith("Photo //") for s in style_names))
        self.assertTrue(any(s.startswith("Comics //") for s in style_names))

        # 2. Personas list contains core personas
        personas = list_definitions("personas")
        self.assertGreaterEqual(len(personas), 5)
        persona_names = [p["name"] for p in personas]
        self.assertIn("Generative Vision Engine", persona_names)
        self.assertIn("Cinematic & Video Director", persona_names)
        self.assertIn("Multi-Image Synthesis Engine", persona_names)

        # 3. Types list contains structural formats
        p_types = list_definitions("types")
        self.assertGreaterEqual(len(p_types), 5)
        type_names = [t["name"] for t in p_types]
        self.assertIn("Detailed Narrative", type_names)
        self.assertIn("Short Summary", type_names)

    def test_02_get_definition(self):
        res = get_definition("styles", "Anime & Manga (2D Cel-shaded)")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["name"], "Anime & Manga (2D Cel-shaded)")
        self.assertTrue(res["is_core"])
        self.assertIn("prohibited", res["frontmatter"])
        self.assertIn("AESTHETIC INJECTION", res["body"])

        # Not found test
        res_none = get_definition("styles", "NonExistentStyle_12345")
        self.assertEqual(res_none["status"], "error")

    def test_03_crud_create_update_delete_custom_style(self):
        test_style_name = "Custom // Test Neon Synthwave 2099"
        test_body = "AESTHETIC INJECTION: Glowing neon gridlines, chromatic aberration, synthwave magenta and cyan palette."
        test_fm = {
            "category": "Custom",
            "medium_type": "Synthwave Digital Illustration",
            "prohibited": "camera lenses, realistic skin pores, RAW photo",
            "replacement": "digital vector neon glow, chromatic lines",
            "tag_injection": "synthwave, neon glow, 80s retro, digital illustration",
            "negative_injection": "photograph, photo, realistic, raw photo",
            "order": 500,
        }

        # 1. Create (Save)
        save_res = save_definition("styles", test_style_name, test_body, test_fm)
        self.assertEqual(save_res["status"], "ok")
        self.assertIn(test_style_name, save_res["choices"]["artistic_styles"])

        # Verify it can be retrieved
        get_res = get_definition("styles", test_style_name)
        self.assertEqual(get_res["status"], "ok")
        self.assertEqual(get_res["name"], test_style_name)
        self.assertFalse(get_res["is_core"])
        self.assertEqual(get_res["frontmatter"]["medium_type"], "Synthwave Digital Illustration")

        # Verify dynamic medium override in fusion engine
        fused = build_dynamic_system_prompt("Base Prompt", artistic_style=test_style_name)
        self.assertIn("Synthwave Digital Illustration", fused)
        self.assertIn("camera lenses", fused)

        # 2. Update (Edit existing)
        updated_body = test_body + "\nADDITIONAL DIRECTIVE: Intense volumetric fog."
        test_fm["order"] = 501
        update_res = save_definition("styles", test_style_name, updated_body, test_fm, original_name=test_style_name)
        self.assertEqual(update_res["status"], "ok")

        get_updated = get_definition("styles", test_style_name)
        self.assertIn("Intense volumetric fog", get_updated["body"])

        # 3. Core Protection Test: Attempt to delete core preset should be rejected
        del_core = delete_definition("styles", "Photorealistic (Modern Digital RAW)")
        self.assertEqual(del_core["status"], "error")
        self.assertIn("protected", del_core["message"].lower())

        # 4. Delete Custom Style
        del_res = delete_definition("styles", test_style_name)
        self.assertEqual(del_res["status"], "ok")
        self.assertNotIn(test_style_name, del_res["choices"]["artistic_styles"])

        # Verify it's no longer found
        get_after = get_definition("styles", test_style_name)
        self.assertEqual(get_after["status"], "error")


if __name__ == "__main__":
    unittest.main()
