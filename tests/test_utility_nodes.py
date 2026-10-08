"""
[STOIQO] Unit Tests — Utility Nodes Suite
Validates:
1. StoiqoImageCompareNode (Visual Compare Slider & Zoom)
2. StoiqoTextConcatenateNode (Prompt Concatenation, Tag Deduplication & Token Counter)
3. StoiqoProImageSaverNode (Pro Image Export, Token Resolution & Sidecars)
"""

import unittest
import sys
import os
import torch
import json
import shutil

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
comfy_root = r"Y:\Project_ExCathedra\ExCathedra\engines\comfyui\ComfyUI"

for p in [root, comfy_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from nodes.image_compare_node import StoiqoImageCompareNode
    from nodes.text_concat_node import StoiqoTextConcatenateNode
    from nodes.pro_saver_node import StoiqoProImageSaverNode, _resolve_tokens
    COMFY_LOADED = True
except Exception as _e:
    COMFY_LOADED = False


class TestUtilityNodes(unittest.TestCase):

    def setUp(self):
        if not COMFY_LOADED:
            self.skipTest("ComfyUI engine environment not fully initialized in test runner.")

    # ── 1. Image Compare Node Tests ─────────────────────────────
    def test_image_compare_node(self):
        node = StoiqoImageCompareNode()
        img_a = torch.zeros((1, 256, 256, 3), dtype=torch.float32)
        img_b = torch.ones((1, 256, 256, 3), dtype=torch.float32)

        res = node.compare_images(img_a, img_b)
        self.assertIn("ui", res)
        self.assertIn("images", res["ui"])
        self.assertEqual(len(res["ui"]["images"]), 2)
        self.assertEqual(res["result"][0].shape, (1, 256, 256, 3))
        self.assertEqual(res["result"][1].shape, (1, 256, 256, 3))

    # ── 2. Text Concatenate Node Tests ──────────────────────────
    def test_text_concatenate_basic(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="masterpiece, highly detailed portrait",
            text_2="cyberpunk neon lighting, 8k resolution",
            separator=",  (Comma Space)"
        )
        self.assertIn("ui", res)
        self.assertIn("result", res)

        text, words, chars, tokens = res["result"]
        self.assertEqual(text, "masterpiece, highly detailed portrait, cyberpunk neon lighting, 8k resolution")
        self.assertGreater(words, 5)
        self.assertGreater(tokens, 5)

    def test_text_concatenate_deduplication(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="1girl, blue eyes, masterpiece",
            text_2="blue eyes, wet hair, 1GIRL, 8k",
            separator=",  (Comma Space)",
            deduplicate_tags="Case-Insensitive"
        )
        text = res["result"][0]
        self.assertEqual(text, "1girl, blue eyes, masterpiece, wet hair, 8k")

    def test_text_concatenate_syntax_cleanup(self):
        node = StoiqoTextConcatenateNode()
        res = node.concatenate(
            text_1="portrait of girl , , with blue_eyes",
            text_2="<lora:cyber_v1:0.8> , neon_city",
            separator=",  (Comma Space)",
            clean_whitespace=True,
            convert_underscores=True
        )
        text = res["result"][0]
        self.assertIn("blue eyes", text)
        self.assertIn("<lora:cyber_v1:0.8>", text)  # LoRA preserved
        self.assertIn("neon city", text)
        self.assertNotIn(" ,", text)
        self.assertNotIn(", ,", text)

    # ── 3. Pro Image Saver Tests ────────────────────────────────
    def test_pro_saver_token_resolution(self):
        meta = {
            "seed": 424242,
            "steps": 25,
            "cfg": 7.0,
            "sampler_name": "euler_ancestral",
            "model_name": "CyberRealistic_v5",
        }
        pattern = "Render_%seed%_%sampler%_%width%x%height%_%counter%"
        res = _resolve_tokens(pattern, 512, 768, meta, counter=7)
        self.assertIn("424242", res)
        self.assertIn("euler_ancestral", res)
        self.assertIn("512x768", res)
        self.assertIn("00007", res)

    def test_pro_saver_export_with_sidecars(self):
        saver = StoiqoProImageSaverNode()
        test_tensor = torch.zeros((1, 128, 128, 3), dtype=torch.float32)

        subfolder = "test_run_suite"
        result = saver.save_images_pro(
            images=test_tensor,
            filename_prefix="test_unit_%seed%",
            format="PNG (Lossless)",
            quality=90,
            subfolder=subfolder,
            sidecar_metadata="Both (.json + .txt)",
            prompt_text="A scenic sunset over mountain range",
            negative_text="blurry, low quality",
            save_workflow=False,
        )

        out_images, out_filepath, out_filename, out_folder, out_meta_json = result["result"]
        self.assertTrue(os.path.exists(out_filepath))
        self.assertTrue(out_filename.endswith(".png"))

        # Check sidecars
        base_path = os.path.splitext(out_filepath)[0]
        json_path = base_path + ".json"
        txt_path = base_path + ".txt"
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(txt_path))

        # Cleanup test files
        try:
            os.remove(out_filepath)
            os.remove(json_path)
            os.remove(txt_path)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
