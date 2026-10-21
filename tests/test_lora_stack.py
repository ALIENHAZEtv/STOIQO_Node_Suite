"""
[STOIQO] Unit Tests — LoRA Stack node (JSON parsing + headless apply)
"""

import importlib.util
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "stoiqo_lora_stack_node", os.path.join(root, "nodes", "lora_stack_node.py")
)
lora_mod = importlib.util.module_from_spec(_spec)
sys.modules["stoiqo_lora_stack_node"] = lora_mod
_spec.loader.exec_module(lora_mod)


class TestParseLoraStack(unittest.TestCase):
    def test_empty_and_invalid_inputs(self):
        for raw in (None, "", "   ", "[]", "not json", "{}", "123"):
            self.assertEqual(lora_mod.parse_lora_stack(raw), [])

    def test_valid_entries(self):
        raw = (
            '[{"name": "a.safetensors", "strength": 0.8, "enabled": true},'
            ' {"name": "sub/b.safetensors", "strength": "1.5", "strength_clip": 0.5, "enabled": false}]'
        )
        entries = lora_mod.parse_lora_stack(raw)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["strength_clip"], 0.8)  # defaults to model strength
        self.assertTrue(entries[0]["enabled"])
        self.assertEqual(entries[1]["strength"], 1.5)
        self.assertEqual(entries[1]["strength_clip"], 0.5)
        self.assertFalse(entries[1]["enabled"])

    def test_drops_bad_items(self):
        raw = '[{"name": ""}, {"name": "None"}, 5, {"strength": 1}, {"name": "ok.safetensors"}]'
        entries = lora_mod.parse_lora_stack(raw)
        self.assertEqual([e["name"] for e in entries], ["ok.safetensors"])
        self.assertEqual(entries[0]["strength"], 1.0)


class TestApplyHeadless(unittest.TestCase):
    def setUp(self):
        # Force headless mode: comfy may be importable in the embedded interpreter.
        self._orig_comfy = lora_mod.comfy
        lora_mod.comfy = None

    def tearDown(self):
        lora_mod.comfy = self._orig_comfy

    def test_missing_lora_file_is_reported(self):
        lora_mod.comfy = self._orig_comfy
        if lora_mod.comfy is None:
            self.skipTest("comfy not importable in this interpreter")
        node = lora_mod.StoiqoLoraStackNode()
        _, _, summary = node.apply_loras(
            "M", None, '[{"name": "definitely_missing_xyz.safetensors", "strength": 1.0}]'
        )
        self.assertIn("[MISSING] definitely_missing_xyz.safetensors", summary)

    def test_summary_reports_on_off_and_passthrough(self):
        node = lora_mod.StoiqoLoraStackNode()
        raw = (
            '[{"name": "on.safetensors", "strength": 0.7, "enabled": true},'
            ' {"name": "off.safetensors", "strength": 1.0, "enabled": false}]'
        )
        model, clip, summary = node.apply_loras("MODEL", "CLIP", raw)
        self.assertEqual(model, "MODEL")
        self.assertEqual(clip, "CLIP")
        self.assertIn("[ON] on.safetensors", summary)
        self.assertIn("[OFF] off.safetensors", summary)

    def test_empty_stack_is_passthrough(self):
        node = lora_mod.StoiqoLoraStackNode()
        model, clip, summary = node.apply_loras("M", None, "All Blocks (Standard)", "[]")
        self.assertEqual((model, clip), ("M", None))
        self.assertEqual(summary, "(no LoRAs)")

    def test_lora_block_weighting_filters(self):
        mock_state_dict = {
            "lora_te_text_model.weight": 1.0,
            "diffusion_model.input_blocks.1.weight": 2.0,
            "diffusion_model.middle_block.0.weight": 3.0,
            "diffusion_model.output_blocks.2.weight": 4.0,
        }
        # 1. Style / Texture Only (OUT Blocks)
        out_only = lora_mod.StoiqoLoraStackNode.filter_lora_state_dict(
            mock_state_dict, "Style / Texture Only (OUT Blocks)"
        )
        self.assertIn("diffusion_model.output_blocks.2.weight", out_only)
        self.assertIn("lora_te_text_model.weight", out_only)
        self.assertNotIn("diffusion_model.input_blocks.1.weight", out_only)
        self.assertNotIn("diffusion_model.middle_block.0.weight", out_only)

        # 2. Character / Structure Only (IN/MID Blocks)
        in_mid_only = lora_mod.StoiqoLoraStackNode.filter_lora_state_dict(
            mock_state_dict, "Character / Structure Only (IN/MID Blocks)"
        )
        self.assertIn("diffusion_model.input_blocks.1.weight", in_mid_only)
        self.assertIn("diffusion_model.middle_block.0.weight", in_mid_only)
        self.assertNotIn("diffusion_model.output_blocks.2.weight", in_mid_only)


if __name__ == "__main__":
    unittest.main()
